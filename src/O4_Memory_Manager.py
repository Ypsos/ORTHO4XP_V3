"""
O4_Memory_Manager.py
Ortho4XP V3 — Lot A / Livrable A3
Auteur : Roland (Ypsos) — Codage : Claude (Anthropic AI)
Version : 2.0 — Juillet 2026

Rôle :
    - Surveiller l'utilisation RAM en temps réel (via psutil)
    - Nettoyer automatiquement la mémoire quand le seuil est dépassé
    - Exposer check_and_cleanup_memory() à appeler dans les boucles lourdes
      (O4_DEM_Utils, O4_Imagery_Utils, O4_DSF_Utils, etc.)
    - Zéro cassure V2 : module autonome, rien n'est modifié dans les fichiers existants

Paramètres configurables :
    max_ram_percent   : seuil RAM système (défaut 80%)
    max_cache_size_gb : taille max du cache interne (défaut 8 Go)

Utilisation depuis un autre module :
    from O4_Memory_Manager import check_and_cleanup_memory, memory_stats

---------------------------------------------------------------------------
CORRECTIONS APPORTÉES EN 2.0
L'API publique de la 1.0 est intégralement conservée : mêmes fonctions,
mêmes signatures (deux paramètres optionnels ajoutés, avec valeur par
défaut), mêmes clés retournées par memory_stats().
---------------------------------------------------------------------------

1. MESURE RÉELLE DES BUFFERS
   La 1.0 estimait la taille du cache avec sys.getsizeof(). Mesuré : une
   image Pillow 4096x4096 RGB (48 Mo de pixels) est comptée 48 octets, une
   vue numpy 144 octets, une liste de dix images 136 octets. Le plafond
   max_cache_size_gb ne pouvait donc jamais se déclencher — cette moitié du
   module ne fonctionnait pas.
   La 2.0 mesure la mémoire réellement occupée : numpy .nbytes, Pillow
   largeur x hauteur x octets par pixel, bytes/bytearray/memoryview, et
   récursion bornée sur les conteneurs.

2. TAILLE DU CACHE SUIVIE EN INCRÉMENTAL
   La 1.0 reparcourait tout le cache, verrou tenu, à chaque cache_set et à
   chaque check_and_cleanup_memory. Avec des threads concurrents, tous se
   bloquaient sur ce verrou. La 2.0 tient un compteur d'octets mis à jour à
   l'écriture et à la suppression : coût constant, plus aucun parcours sous
   verrou.

3. gc.collect() SOUS CONTRÔLE EXPLICITE DE L'APPELANT
   gc.collect() est une pause globale : il fige TOUS les threads, y compris
   celui qui écrit un DSF. Il ne peut pas libérer un objet encore référencé
   (le ramasse-miettes de Python ne touche jamais aux objets atteignables),
   donc aucun risque de corruption d'image ; mais un gel de plusieurs
   secondes déclenché pendant que les threads de travail tournent est
   inacceptable.

   Le critère n'est PAS « suis-je dans le thread principal ». Dans Ortho4XP,
   AUCUN build ne tourne dans le thread principal : build_tile, build_all et
   build_tile_list sont chacun lancés dans un thread pour que Tkinter reste
   réactif. Le seul critère valable est « des threads de travail tournent-ils
   en ce moment », et seul l'appelant le sait.

   D'où le paramètre allow_gc :
       allow_gc=False (défaut) : éviction du cache seulement — toujours sûr,
                                 appelable depuis n'importe où.
       allow_gc=True           : éviction + gc.collect(). À ne passer que
                                 depuis un point du code où TOUS les threads
                                 de travail ont été joints.
   Le défaut est le comportement sûr : un appel écrit sans précaution ne peut
   pas figer un build.

4. COMPTEURS PROTÉGÉS
   _last_cleanup et _cleanup_count étaient modifiés hors verrou depuis
   plusieurs threads. Ils sont désormais sous _state_lock, et la réservation
   du créneau anti-rafale est atomique.

5. LECTURE RAM AMORTIE
   psutil.virtual_memory() est un appel système. Appelé à chaque itération
   d'une boucle lourde, il coûte cher pour rien. La 2.0 met la valeur en
   cache pendant _RAM_POLL_INTERVAL (0,5 s).

---------------------------------------------------------------------------
VOCABULAIRE
    « tuile » désigne exclusivement une tuile 1°x1° X-Plane (ex : +46-003).
    Les fichiers d'imagerie sont appelés image, JPG, texture ou DDS.
---------------------------------------------------------------------------
"""

import gc
import sys
import time
import threading

# ---------------------------------------------------------------------------
# Import psutil (requis pour la surveillance RAM)
# ---------------------------------------------------------------------------
try:
    import psutil
    _has_psutil = True
except ImportError:
    _has_psutil = False

# ---------------------------------------------------------------------------
# Import du système de logs Ortho4XP existant (O4_UI_Utils)
# Si indisponible (tests standalone), on bascule sur print simple
# ---------------------------------------------------------------------------
try:
    import O4_UI_Utils as UI
    def _log(msg):
        UI.lvprint(1, "[MEMORY] " + msg)
    def _logwarn(msg):
        UI.lvprint(1, "[MEMORY] ATTENTION : " + msg)
except ImportError:
    def _log(msg):
        print(time.strftime("%Y-%m-%d %H:%M:%S") + " [MEMORY] " + msg)
    def _logwarn(msg):
        print(time.strftime("%Y-%m-%d %H:%M:%S") + " [MEMORY] ATTENTION : " + msg)


# ---------------------------------------------------------------------------
# Configuration — modifiable sans toucher au reste du code
# ---------------------------------------------------------------------------

# Seuil d'utilisation RAM système (%) au-delà duquel on nettoie
max_ram_percent    = 80.0

# Taille maximale du cache interne en Go
max_cache_size_gb  = 8.0

# Intervalle minimum entre deux nettoyages forcés (secondes)
# Évite de spammer gc.collect() dans les boucles très rapides
_MIN_CLEANUP_INTERVAL = 5.0

# Durée de validité de la mesure RAM mise en cache (secondes)
_RAM_POLL_INTERVAL = 0.5

# Profondeur maximale de récursion pour mesurer un conteneur imbriqué
_SIZEOF_MAX_DEPTH = 3

# Nombre maximum d'éléments inspectés dans un conteneur (borne le coût)
_SIZEOF_MAX_ITEMS = 64

# ---------------------------------------------------------------------------
# Cache interne géré par ce module
# Dictionnaire simple : clé → valeur (ex: images, masques en mémoire)
# Les modules externes peuvent enregistrer/lire des objets via l'API ci-dessous
# ---------------------------------------------------------------------------
_cache         = {}
_cache_sizes   = {}        # clé → octets mesurés à l'insertion
_cache_bytes   = 0         # somme courante, tenue à jour en incrémental
_cache_lock    = threading.RLock()

# Verrou dédié aux compteurs d'état, séparé de celui du cache : un log ou une
# lecture de statistiques ne doit pas bloquer un thread qui écrit dans le cache
_state_lock    = threading.Lock()
_last_cleanup  = 0.0       # timestamp du dernier nettoyage
_cleanup_count = 0         # nombre total de nettoyages effectués

# Mesure RAM amortie
_ram_cached_pct   = 0.0
_ram_cached_avail = 999.0
_ram_cached_at    = 0.0
_ram_poll_lock    = threading.Lock()


# ---------------------------------------------------------------------------
# Fonctions internes
# ---------------------------------------------------------------------------

def _poll_ram():
    """
    Rafraîchit la mesure RAM si elle date de plus de _RAM_POLL_INTERVAL.
    psutil.virtual_memory() est un appel système : l'appeler à chaque
    itération d'une boucle lourde coûte cher pour rien.
    """
    global _ram_cached_pct, _ram_cached_avail, _ram_cached_at

    if not _has_psutil:
        return

    if time.time() - _ram_cached_at < _RAM_POLL_INTERVAL:
        return

    with _ram_poll_lock:
        # Re-test après acquisition : un autre thread a pu rafraîchir entre-temps
        now = time.time()
        if now - _ram_cached_at < _RAM_POLL_INTERVAL:
            return
        try:
            vm = psutil.virtual_memory()
            _ram_cached_pct   = vm.percent
            _ram_cached_avail = vm.available / (1024 ** 3)
        except Exception:
            _ram_cached_pct   = 0.0
            _ram_cached_avail = 999.0
        _ram_cached_at = now


def _ram_usage_percent():
    """
    Retourne le pourcentage d'utilisation RAM système.
    Retourne 0.0 si psutil n'est pas disponible.
    """
    if not _has_psutil:
        return 0.0
    _poll_ram()
    return _ram_cached_pct


def _ram_available_gb():
    """
    Retourne la RAM disponible en Go.
    Retourne 999.0 si psutil n'est pas disponible (mode dégradé sans blocage).
    """
    if not _has_psutil:
        return 999.0
    _poll_ram()
    return _ram_cached_avail


def _sizeof_bytes(obj, _depth=0):
    """
    Estime la mémoire RÉELLEMENT occupée par un objet, en octets.

    sys.getsizeof() ne convient pas ici : mesuré, une image Pillow 4096x4096
    RGB (48 Mo de pixels) est comptée 48 octets, une vue numpy 144 octets,
    une liste de dix images 136 octets. Le plafond de cache de la 1.0 ne
    pouvait donc jamais se déclencher.

    Cette fonction traite explicitement les types réellement mis en cache par
    Ortho4XP (numpy, Pillow, tampons binaires) et récursionne de façon bornée
    sur les conteneurs. Elle n'est appelée qu'à l'insertion, jamais dans une
    boucle de traitement.
    """
    if obj is None:
        return 0

    # --- numpy : couvre aussi les vues, dont getsizeof ne voit que l'en-tête
    nbytes = getattr(obj, "nbytes", None)
    if isinstance(nbytes, int) and nbytes >= 0:
        return nbytes

    # --- Pillow : largeur x hauteur x octets par pixel.
    #     Détection par attributs, sans importer PIL : le module reste autonome.
    size = getattr(obj, "size", None)
    mode = getattr(obj, "mode", None)
    if isinstance(mode, str) and isinstance(size, tuple) and len(size) == 2:
        try:
            w, h = int(size[0]), int(size[1])
            bytes_per_px = {
                "1": 1, "L": 1, "P": 1, "LA": 2, "La": 2,
                "RGB": 3, "YCbCr": 3, "LAB": 3, "HSV": 3,
                "RGBA": 4, "RGBa": 4, "CMYK": 4,
                "I": 4, "F": 4, "I;16": 2, "I;16B": 2, "I;16L": 2,
            }.get(mode, 4)
            return max(0, w * h * bytes_per_px)
        except Exception:
            pass

    # --- tampons binaires bruts
    if isinstance(obj, (bytes, bytearray, memoryview)):
        try:
            return len(obj)
        except Exception:
            return 0

    # --- conteneurs : récursion bornée en profondeur et en nombre d'éléments
    if _depth < _SIZEOF_MAX_DEPTH:
        try:
            if isinstance(obj, dict):
                total = sys.getsizeof(obj)
                for i, (k, v) in enumerate(obj.items()):
                    if i >= _SIZEOF_MAX_ITEMS:
                        break
                    total += _sizeof_bytes(k, _depth + 1)
                    total += _sizeof_bytes(v, _depth + 1)
                return total
            if isinstance(obj, (list, tuple, set, frozenset)):
                total = sys.getsizeof(obj)
                for i, v in enumerate(obj):
                    if i >= _SIZEOF_MAX_ITEMS:
                        break
                    total += _sizeof_bytes(v, _depth + 1)
                return total
        except Exception:
            pass

    # --- repli : au moins la taille de l'objet Python lui-même
    try:
        return sys.getsizeof(obj)
    except Exception:
        return 0


def _cache_size_gb():
    """
    Retourne la taille du cache interne en Go.

    Lecture d'un compteur tenu à jour en incrémental : coût constant, aucun
    parcours du cache. La 1.0 reparcourait tout le dictionnaire verrou tenu,
    à chaque écriture — source de contention entre threads concurrents.
    """
    with _cache_lock:
        return _cache_bytes / (1024 ** 3)


def _evict_cache():
    """
    Vide le cache interne et remet le compteur d'octets à zéro.

    Opération instantanée et sûre depuis n'importe quel thread : elle ne fait
    que retirer des références. Tout objet encore utilisé ailleurs reste
    vivant grâce au comptage de références de Python.

    Retourne (nombre d'entrées supprimées, octets libérés).
    """
    global _cache_bytes
    with _cache_lock:
        n     = len(_cache)
        freed = _cache_bytes
        _cache.clear()
        _cache_sizes.clear()
        _cache_bytes = 0
    return n, freed


def _do_cleanup(reason="seuil dépassé", allow_gc=False):
    """
    Effectue le nettoyage mémoire :
    1. Vide le cache interne si sa taille dépasse max_cache_size_gb
    2. Appelle gc.collect(), uniquement si allow_gc est vrai
    3. Log le résultat

    Voir le point 3 de l'en-tête du module pour le sens exact de allow_gc.
    """
    global _last_cleanup, _cleanup_count

    # Test de l'intervalle minimum ET réservation du créneau sous verrou :
    # sans cela, plusieurs threads franchissent le test simultanément et
    # nettoient en rafale.
    with _state_lock:
        now = time.time()
        if now - _last_cleanup < _MIN_CLEANUP_INTERVAL:
            return
        _last_cleanup   = now
        _cleanup_count += 1
        count = _cleanup_count

    ram_before = _ram_usage_percent()
    cache_gb   = _cache_size_gb()

    # Vider le cache interne si trop grand
    if cache_gb > max_cache_size_gb:
        cleared_keys, _ = _evict_cache()
        _logwarn(f"Cache interne vidé ({cache_gb:.2f} Go > {max_cache_size_gb} Go) "
                 f"— {cleared_keys} entrée(s) supprimée(s)")

    # Nettoyage Python, sur autorisation explicite de l'appelant seulement
    if allow_gc:
        collected = gc.collect()
        gc_txt = f"Objets GC collectés : {collected}"
    else:
        gc_txt = "gc.collect() non autorisé par l'appelant"

    # Le nettoyage a pu durer : on redate pour que l'intervalle parte de la fin
    with _state_lock:
        _last_cleanup = time.time()

    ram_after = _ram_usage_percent()
    _log(f"Nettoyage #{count} [{reason}] — "
         f"RAM : {ram_before:.1f}% → {ram_after:.1f}% — {gc_txt}")


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def check_and_cleanup_memory(context="", allow_gc=False):
    """
    Fonction principale à appeler dans les boucles lourdes.

    Vérifie si les seuils RAM ou cache sont dépassés.
    Si oui, déclenche un nettoyage automatique.

    Paramètres :
        context  : texte libre affiché dans les logs pour identifier l'appelant
                   ex: "boucle DEM", "conversion imagerie ZL17", etc.
        allow_gc : autorise gc.collect() en plus de l'éviction du cache.
                   Défaut False = toujours sûr, appelable depuis n'importe où.
                   Ne passer True que depuis un point du code où TOUS les
                   threads de travail ont été joints : gc.collect() est une
                   pause globale qui figerait sinon les traitements en cours.

    Sûre depuis n'importe quel thread. Le critère n'est pas le thread appelant
    mais la présence ou non de threads de travail actifs — voir le point 3 de
    l'en-tête du module.

    Exemple d'utilisation dans O4_DEM_Utils.py :
        from O4_Memory_Manager import check_and_cleanup_memory
        for lat in range(...):
            check_and_cleanup_memory(context="build_dem")
            # ... traitement lourd ...
    """
    global _last_cleanup, _cleanup_count

    if not _has_psutil:
        # Mode dégradé : pas de surveillance RAM possible.
        # gc.collect() seulement si l'appelant l'a explicitement autorisé.
        if not allow_gc:
            return
        with _state_lock:
            now = time.time()
            if now - _last_cleanup < _MIN_CLEANUP_INTERVAL:
                return
            _last_cleanup   = now
            _cleanup_count += 1
        gc.collect()
        with _state_lock:
            _last_cleanup = time.time()
        return

    ram_pct  = _ram_usage_percent()
    cache_gb = _cache_size_gb()

    needs_cleanup = (
        ram_pct  > max_ram_percent   or
        cache_gb > max_cache_size_gb
    )

    if needs_cleanup:
        reason = []
        if ram_pct  > max_ram_percent:
            reason.append(f"RAM {ram_pct:.1f}% > {max_ram_percent}%")
        if cache_gb > max_cache_size_gb:
            reason.append(f"cache {cache_gb:.2f} Go > {max_cache_size_gb} Go")
        label = " | ".join(reason)
        if context:
            label = f"{context} — {label}"
        _do_cleanup(reason=label, allow_gc=allow_gc)


def memory_stats():
    """
    Retourne un dictionnaire avec l'état courant de la mémoire.

    Retourne :
        dict avec les clés :
            ram_percent      : % RAM système utilisée
            ram_available_gb : Go RAM disponible
            cache_size_gb    : taille du cache interne
            cache_entries    : nombre d'entrées dans le cache
            cleanup_count    : nombre de nettoyages effectués depuis le démarrage
            psutil_available : True si psutil est installé

    Ne déclenche jamais gc.collect() : appelable sans risque depuis un thread
    d'affichage, y compris pendant un build.
    """
    with _cache_lock:
        n_entries = len(_cache)
        size_gb   = _cache_bytes / (1024 ** 3)

    with _state_lock:
        n_cleanups = _cleanup_count

    return {
        "ram_percent"      : _ram_usage_percent(),
        "ram_available_gb" : _ram_available_gb(),
        "cache_size_gb"    : size_gb,
        "cache_entries"    : n_entries,
        "cleanup_count"    : n_cleanups,
        "psutil_available" : _has_psutil,
    }


def cache_set(key, value):
    """
    Stocke une valeur dans le cache interne géré par ce module.

    Paramètres :
        key   : clé string unique (ex: "dem_48_2", "jpg_ZL17_x123_y456")
        value : objet Python à mettre en cache

    Note : après chaque écriture, check_and_cleanup_memory() est appelé
           automatiquement pour éviter un dépassement silencieux.

    La taille de l'objet est mesurée une seule fois, à l'insertion, et HORS
    du verrou. Le compteur global est ensuite mis à jour en temps constant.
    """
    global _cache_bytes

    # Mesure hors verrou : ne bloque aucun autre thread pendant le calcul
    size = _sizeof_bytes(value)

    with _cache_lock:
        old = _cache_sizes.get(key)
        if old is not None:
            _cache_bytes -= old
        _cache[key]       = value
        _cache_sizes[key] = size
        _cache_bytes     += size
        if _cache_bytes < 0:      # garde-fou, ne devrait jamais arriver
            _cache_bytes = 0

    check_and_cleanup_memory(context=f"cache_set:{key}")


def cache_get(key, default=None):
    """
    Récupère une valeur du cache interne.

    Paramètres :
        key     : clé à chercher
        default : valeur retournée si la clé est absente (défaut : None)

    Retourne :
        La valeur mise en cache, ou default si absente.
    """
    with _cache_lock:
        return _cache.get(key, default)


def cache_delete(key):
    """
    Supprime une entrée du cache interne.

    Paramètres :
        key : clé à supprimer

    Retourne :
        True si la clé existait, False sinon.
    """
    global _cache_bytes
    with _cache_lock:
        if key in _cache:
            del _cache[key]
            _cache_bytes -= _cache_sizes.pop(key, 0)
            if _cache_bytes < 0:
                _cache_bytes = 0
            return True
    return False


def cache_clear(allow_gc=True):
    """
    Vide entièrement le cache interne et force un gc.collect().
    À utiliser après une opération lourde (ex: fin de build d'une tuile
    1°x1°, au sens Ortho4XP du terme).

    Paramètres :
        allow_gc : défaut True — cache_clear() est un appel délibéré, fait à
                   un moment choisi par le développeur, contrairement à
                   check_and_cleanup_memory() qui se déclenche tout seul.
                   Passer False pour vider le cache sans figer les threads
                   si des traitements parallèles sont encore en cours.
    """
    global _cleanup_count

    n, freed = _evict_cache()

    with _state_lock:
        _cleanup_count += 1

    if allow_gc:
        collected = gc.collect()
        _log(f"Cache vidé manuellement — {n} entrée(s) supprimée(s), "
             f"{freed / (1024 ** 2):.1f} Mo libérés, "
             f"{collected} objets GC collectés")
    else:
        _log(f"Cache vidé manuellement — {n} entrée(s) supprimée(s), "
             f"{freed / (1024 ** 2):.1f} Mo libérés, "
             f"gc.collect() non demandé")


def set_limits(ram_percent=None, cache_size_gb=None):
    """
    Modifie les seuils à chaud, sans redémarrage.

    Paramètres :
        ram_percent   : nouveau seuil RAM (ex: 75.0)
        cache_size_gb : nouvelle taille max cache (ex: 6.0)
    """
    global max_ram_percent, max_cache_size_gb
    if ram_percent is not None:
        if 10.0 <= ram_percent <= 95.0:
            max_ram_percent = float(ram_percent)
            _log(f"Seuil RAM mis à jour : {max_ram_percent}%")
        else:
            _logwarn(f"Seuil RAM invalide ({ram_percent}) — doit être entre 10 et 95")
    if cache_size_gb is not None:
        if 0.1 <= cache_size_gb <= 64.0:
            max_cache_size_gb = float(cache_size_gb)
            _log(f"Taille max cache mise à jour : {max_cache_size_gb} Go")
        else:
            _logwarn(f"Taille cache invalide ({cache_size_gb}) — doit être entre 0.1 et 64")


# ---------------------------------------------------------------------------
# Test standalone (python O4_Memory_Manager.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test O4_Memory_Manager 2.0 ===\n")

    # ---- Tests hérités de la 1.0, inchangés -------------------------------

    # Test 1 : memory_stats
    stats = memory_stats()
    print(f"[OK] memory_stats() : {stats}")
    assert "ram_percent"      in stats
    assert "cache_entries"    in stats
    assert "cleanup_count"    in stats
    assert "psutil_available" in stats
    print(f"     psutil disponible : {stats['psutil_available']}")
    if stats["psutil_available"]:
        print(f"     RAM utilisée      : {stats['ram_percent']:.1f}%")
        print(f"     RAM disponible    : {stats['ram_available_gb']:.2f} Go")

    # Test 2 : cache_set / cache_get
    cache_set("test_key", [1, 2, 3, 4, 5])
    val = cache_get("test_key")
    assert val == [1, 2, 3, 4, 5], "ERREUR : cache_get ne retrouve pas la valeur"
    print("[OK] cache_set / cache_get")

    # Test 3 : cache_delete
    ok = cache_delete("test_key")
    assert ok, "ERREUR : cache_delete a retourné False"
    assert cache_get("test_key") is None
    print("[OK] cache_delete")

    # Test 4 : check_and_cleanup_memory (ne doit pas planter)
    check_and_cleanup_memory(context="test unitaire")
    print("[OK] check_and_cleanup_memory")

    # Test 5 : set_limits
    set_limits(ram_percent=75.0, cache_size_gb=6.0)
    assert max_ram_percent   == 75.0
    assert max_cache_size_gb == 6.0
    print("[OK] set_limits")

    # Test 6 : cache_clear
    cache_set("a", "valeur_a")
    cache_set("b", "valeur_b")
    cache_clear()
    assert cache_get("a") is None
    assert cache_get("b") is None
    print("[OK] cache_clear")

    # Test 7 : set_limits avec valeurs invalides (ne doit pas planter)
    set_limits(ram_percent=5.0)    # trop bas → ignoré
    set_limits(cache_size_gb=100)  # trop haut → ignoré
    print("[OK] set_limits valeurs invalides correctement ignorées")

    # ---- Tests ajoutés en 2.0 ---------------------------------------------

    # Test 8 : mesure réelle d'un tampon binaire
    cache_clear()
    set_limits(cache_size_gb=64.0)
    cache_set("buf", bytes(10 * 1024 * 1024))          # 10 Mo
    mesure_mo = memory_stats()["cache_size_gb"] * 1024
    assert 9.0 < mesure_mo < 11.0, f"ERREUR : 10 Mo mesurés {mesure_mo:.2f} Mo"
    print(f"[OK] mesure réelle des tampons : 10 Mo → {mesure_mo:.2f} Mo mesurés")

    # Test 9 : le compteur redescend à la suppression
    cache_delete("buf")
    assert memory_stats()["cache_size_gb"] < 0.001
    print("[OK] compteur d'octets décrémenté à la suppression")

    # Test 10 : écraser une clé ne double pas le compteur
    cache_set("k", bytes(5 * 1024 * 1024))
    cache_set("k", bytes(5 * 1024 * 1024))
    mo = memory_stats()["cache_size_gb"] * 1024
    assert 4.0 < mo < 6.0, f"ERREUR : écrasement mal compté ({mo:.2f} Mo)"
    print(f"[OK] écrasement de clé correctement compté ({mo:.2f} Mo)")
    cache_clear()

    # Test 11 : mesure d'une image Pillow, si disponible
    try:
        from PIL import Image
        im = Image.new("RGB", (2048, 2048))
        im.load()
        attendu_mo = 2048 * 2048 * 3 / (1024 ** 2)
        mesure     = _sizeof_bytes(im) / (1024 ** 2)
        assert abs(mesure - attendu_mo) < 1.0
        print(f"[OK] image Pillow 2048x2048 RGB : {mesure:.1f} Mo mesurés "
              f"(sys.getsizeof en aurait rapporté {sys.getsizeof(im)} octets)")
    except ImportError:
        print("[--] Pillow absent — test image ignoré")

    # Test 12 : mesure d'un tableau numpy et de ses vues, si disponible
    try:
        import numpy as np
        arr = np.zeros((1024, 1024, 3), dtype=np.uint8)
        vue = arr[100:900]
        assert _sizeof_bytes(arr) == arr.nbytes
        assert _sizeof_bytes(vue) == vue.nbytes
        print(f"[OK] numpy : tableau {arr.nbytes / 1024**2:.1f} Mo et vue "
              f"{vue.nbytes / 1024**2:.1f} Mo correctement mesurés")
    except ImportError:
        print("[--] numpy absent — test tableau ignoré")

    # Outillage commun aux tests 13 à 15 : espion sur gc.collect()
    _gc_calls    = {"n": 0}
    _vrai_gc     = gc.collect

    def _gc_espion(*a, **kw):
        _gc_calls["n"] += 1
        return _vrai_gc(*a, **kw)

    # Test 13 : par défaut (allow_gc absent), AUCUN gc.collect(),
    #           y compris sous forte concurrence, et sans blocage
    cache_clear()
    set_limits(cache_size_gb=0.1)     # 100 Mo, franchi dès les 1res écritures
    _MIN_CLEANUP_INTERVAL = 0.0       # neutralise l'anti-rafale pour le test
    _gc_calls["n"] = 0
    gc.collect = _gc_espion
    try:
        erreurs = []

        def worker(i):
            try:
                for j in range(200):
                    cache_set(f"w{i}_{j}", bytes(1024 * 1024))   # 1 Mo
                    check_and_cleanup_memory(context=f"worker{i}")
            except Exception as e:
                erreurs.append(e)

        ths = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        t0 = time.time()
        for t in ths:
            t.start()
        for t in ths:
            t.join(timeout=60)
        duree = time.time() - t0

        assert not erreurs, f"ERREUR dans un thread : {erreurs[0]}"
        assert all(not t.is_alive() for t in ths), "ERREUR : thread bloqué"
        assert _gc_calls["n"] == 0, \
            f"ERREUR : {_gc_calls['n']} gc.collect() alors que allow_gc=False"
        n_nettoyages = memory_stats()["cleanup_count"]
        assert n_nettoyages > 0, \
            "ERREUR : aucun nettoyage déclenché — le test ne vérifierait rien"
        print(f"[OK] 8 threads x 200 Mo en {duree:.2f}s — "
              f"{n_nettoyages} nettoyage(s), 0 gc.collect() par défaut, "
              f"aucun blocage")
    finally:
        gc.collect = _vrai_gc

    # Test 14 : allow_gc=True déclenche bien gc.collect(), depuis un thread
    #           quelconque (le thread principal n'est PAS le critère)
    _gc_calls["n"] = 0
    gc.collect = _gc_espion
    try:
        cache_clear()
        set_limits(cache_size_gb=64.0)     # large : cache_set n'évince pas
        _last_cleanup  = 0.0
        _gc_calls["n"] = 0
        resultat = {}

        def appel_autorise():
            try:
                cache_set("gros", bytes(200 * 1024 * 1024))     # 200 Mo
                # Seuil abaissé APRÈS remplissage : sinon cache_set aurait
                # déjà évincé, et l'appel testé ne verrait plus rien à faire.
                set_limits(cache_size_gb=0.1)
                check_and_cleanup_memory(context="fin de tuile", allow_gc=True)
                resultat["ok"] = True
            except Exception as e:
                resultat["err"] = e

        t = threading.Thread(target=appel_autorise)
        t.start()
        t.join(timeout=60)
        assert not t.is_alive(),        "ERREUR : thread bloqué"
        assert "err" not in resultat,   f"ERREUR : {resultat.get('err')}"
        assert _gc_calls["n"] >= 1, \
            "ERREUR : allow_gc=True n'a pas déclenché gc.collect()"
        print(f"[OK] allow_gc=True depuis un thread non principal : "
              f"gc.collect() déclenché ({_gc_calls['n']} appel)")
    finally:
        gc.collect = _vrai_gc
        _MIN_CLEANUP_INTERVAL = 5.0

    # Test 15 : cache_clear(allow_gc=False) ne déclenche pas gc.collect()
    _gc_calls["n"] = 0
    gc.collect = _gc_espion
    try:
        cache_set("x", bytes(1024))
        cache_clear(allow_gc=False)
        assert _gc_calls["n"] == 0, "ERREUR : cache_clear(False) a appelé gc"
        cache_set("y", bytes(1024))
        cache_clear()                      # défaut = True
        assert _gc_calls["n"] >= 1, "ERREUR : cache_clear() n'a pas appelé gc"
        print("[OK] cache_clear : allow_gc respecté dans les deux sens")
    finally:
        gc.collect = _vrai_gc

    # Test 16 : cohérence finale du compteur d'octets
    cache_clear()
    set_limits(ram_percent=80.0, cache_size_gb=8.0)
    for i in range(50):
        cache_set(f"c{i}", bytes(1024 * 100))
    attendu = 50 * 1024 * 100
    reel    = memory_stats()["cache_size_gb"] * (1024 ** 3)
    assert abs(reel - attendu) < attendu * 0.02, \
        f"ERREUR : compteur dérivé ({reel:.0f} vs {attendu})"
    print("[OK] compteur d'octets cohérent après 50 écritures")
    cache_clear()

    print("\n✅ Tous les tests O4_Memory_Manager 2.0 passés.")
