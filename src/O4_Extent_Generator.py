# -*- coding: utf-8 -*-
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CREDIT — AUTHOR: Roland (Ypsos) — 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================
# O4_Extent_Generator.py — ORTHO4XP V3
#
#   Générateur d'Extents grand public.
#
#   Objectif : permettre à n'importe quel utilisateur (sans connaître OSM ni
#   la ligne de commande) de fabriquer un « extent » — le trio de fichiers
#   .ext + .png + .osm.bz2 qui délimite où un provider régional s'applique.
#
#   Principe (validé avec Roland), STRICTEMENT additif :
#     - Ce module n'altère AUCUN fichier existant du moteur.
#     - Il ne recrée RIEN : pour fabriquer le trio, il lance l'outil existant
#       O4_Mask_Utils.py exactement comme un utilisateur expert le ferait au
#       Terminal (subprocess), puis range le résultat. Zéro logique dupliquée.
#     - Le réseau (Overpass), la triangulation et l'écriture du .ext/.png sont
#       entièrement pris en charge par O4_Mask_Utils.py, non modifié.
#
#   Mécanisme (prouvé sur de vrais fichiers d'extents) :
#     O4_Mask_Utils.py  <extent_code>  <pixel>  <buffer>  <blur>  <requête OSM>
#     ex. : ValleAosta 10 0 500 rel[admin_level=4][name:de=Aostatal]
#     La requête est assemblée à partir de choix simples (niveau + nom).
#     Mask écrit ses fichiers dans le RÉPERTOIRE COURANT : on lance donc depuis
#     Extents/<pays>/ pour que le trio se range tout seul au bon endroit.
#
#   Style : calqué sur O4_lay_generator.py / O4_Menu_Avance.py
#     - thème via O4_Theme_Manager (utilisé, jamais modifié) ;
#     - boutons Mac-safe = Frame+Label (jamais tk.Button à cause d'Aqua) ;
#     - bilingue FR/EN résolu ICI via _L(), sans toucher aux fichiers O4_Lang_*.
# ============================================================

import sys
import os

# --- détection OS (même logique que lay_generator / menu_avance) -------------
if "dar" in sys.platform:
    _OS = "mac"
elif "win" in sys.platform:
    _OS = "windows"
else:
    _OS = "linux"

# --- thème : importé si présent, sinon couleurs de repli ---------------------
try:
    import O4_Theme_Manager as _TM
    _HAS_THEME = True
except Exception:
    _TM = None
    _HAS_THEME = False

# --- langue active : import protégé, repli EN (comme menu_avance) ------------
try:
    from O4_Lang import current_lang as _current_lang
except Exception:
    def _current_lang():
        return "EN"


def _lang_code():
    """Retourne 'FR' si la langue active est le français, sinon 'EN'.
    Toute langue autre que FR retombe volontairement sur EN."""
    try:
        code = (_current_lang() or "EN").upper()
    except Exception:
        code = "EN"
    return "FR" if code == "FR" else "EN"


def _L(fr, en):
    """Libellé bilingue résolu ICI (sans toucher aux fichiers O4_Lang_*).
    FR si langue active = français, EN sinon."""
    return fr if _lang_code() == "FR" else en


def _c(key, fallback):
    """Couleur du thème actif, ou fallback si Theme Manager absent."""
    if _HAS_THEME:
        try:
            return _TM.get_theme().get(key, fallback)
        except Exception:
            return fallback
    return fallback


# ── Chemins projet ────────────────────────────────────────────────────────────
# Ce fichier vit dans src/. La racine du projet est un niveau au-dessus.
# Extents/ est à la racine ; O4_Mask_Utils.py est dans src/ (à côté de nous).
def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))   # …/src
    return os.path.dirname(here)                          # …/ (racine)


def _extents_dir():
    return os.path.join(_project_root(), "Extents")


def _mask_utils_path():
    return os.path.join(_project_root(), "src", "O4_Mask_Utils.py")


# ── Niveaux administratifs OSM ────────────────────────────────────────────────
# Valeurs standard OSM (boundary=administrative). Prouvé : Suisse=2, Val d'Aoste=4.
# (code, libellé_fr, libellé_en)
_ADMIN_LEVELS = [
    ("2", "Pays entier",           "Whole country"),
    ("4", "Région / Land / Canton", "Region / Land / Canton"),
    ("6", "Département / Province", "Department / Province"),
]

# Clés de nom OSM essayées AUTOMATIQUEMENT, dans cet ordre, jusqu'à trouver la
# zone. L'utilisateur ne choisit RIEN : il tape juste un nom, le module teste
# ces clés une à une. Prouvé : Suisse=name:fr, Val d'Aoste=name:de.
# 'name' (nom local) en premier car c'est le cas le plus fréquent.
_NAME_KEYS = ["name", "name:fr", "name:en", "name:de", "name:it",
              "name:es", "name:nl", "name:pt", "int_name"]

# Réglages fins par défaut (valeurs standard, prouvées sur de vrais extents).
_DEFAULT_PIXEL = "10"
_DEFAULT_BUFFER = "0"
_DEFAULT_BLUR = "0"

# Résolution (pixel_size) recommandée SELON LE NIVEAU. Valeurs conseillées par
# un utilisateur expérimenté sur le forum : 10 pour un département est bien,
# mais trop lourd pour une région, et ingérable pour un pays (masque énorme).
#   - Département (6) : 10    (fin, zone petite)
#   - Région (4)     : 30    (« 20 ou 30 » selon l'expert → on prend 30)
#   - Pays (2)       : 1000  (« très basse, ex. 1000 si le pays est grand »)
# L'utilisateur garde la main : ces valeurs ne sont que des DÉFAUTS, modifiables
# dans les Réglages avancés (l'expert affine selon son cas).
_PIXEL_PAR_NIVEAU = {
    "6": "10",     # Département / Province
    "4": "30",     # Région / Land / Canton
    "2": "1000",   # Pays entier
}


# ── Bouton Mac-safe : Frame + Label (JAMAIS tk.Button) ────────────────────────
# Patron identique à _make_themed_button d'O4_lay_generator / O4_Menu_Avance.
def _make_themed_button(tk, parent, text, command):
    bg = _c("btn_bg", "#4a6b59")
    fg = _c("btn_fg", "#ffffff")
    hover = _c("accent", "#5a7b69")
    active = _c("fg_secondary", "#a6e3a1")
    border = _c("btn_bg", "#4a6b59")

    frame = tk.Frame(parent, bg=bg, highlightthickness=1,
                     highlightbackground=border, highlightcolor=active, bd=0)
    label = tk.Label(frame, text=text, bg=bg, fg=fg, padx=10, pady=5,
                     font=("Helvetica", 12) if _OS == "mac" else ("Segoe UI", 10),
                     cursor="hand2")
    label.pack(fill="both", expand=True)

    state = {"enabled": True}

    def on_enter(e=None):
        if state["enabled"]:
            frame.configure(bg=hover); label.configure(bg=hover)

    def on_leave(e=None):
        if state["enabled"]:
            frame.configure(bg=bg); label.configure(bg=bg)

    def on_click(e=None):
        if state["enabled"]:
            frame.configure(bg=active); label.configure(bg=active)

    def on_release(e=None):
        if state["enabled"]:
            frame.configure(bg=hover); label.configure(bg=hover)
            if callable(command):
                command()

    for w in (frame, label):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)
        w.bind("<ButtonRelease-1>", on_release)

    # petits utilitaires pour griser / réactiver le bouton (ex. « Créer »)
    def set_enabled(flag):
        state["enabled"] = bool(flag)
        if flag:
            frame.configure(bg=bg); label.configure(bg=bg, fg=fg)
        else:
            grey_bg = _c("bg_secondary", "#2a4235")
            grey_fg = _c("fg_secondary", "#a6e3a1")
            frame.configure(bg=grey_bg); label.configure(bg=grey_bg, fg=grey_fg)

    frame.set_enabled = set_enabled  # type: ignore[attr-defined]
    return frame


# ── Scan des dossiers pays existants dans Extents/ ────────────────────────────
def _scan_country_dirs():
    """Liste les sous-dossiers de Extents/ (pays/régions déjà présents).
    Scan EN DIRECT : s'adapte à n'importe quelle installation (5 dossiers de
    base chez un nouvel utilisateur, davantage chez un utilisateur avancé).
    Renvoie une liste triée de noms de dossiers."""
    root = _extents_dir()
    resultat = []
    try:
        for nom in os.listdir(root):
            chemin = os.path.join(root, nom)
            if os.path.isdir(chemin) and not nom.startswith("."):
                resultat.append(nom)
    except Exception:
        pass
    resultat.sort(key=lambda s: s.lower())
    return resultat


# ── Construction de la requête OSM ────────────────────────────────────────────
def _build_osm_query(admin_level, name_key, name_value):
    """Assemble la requête OSM au format prouvé sur de vrais extents :
        rel[admin_level=X][<clé_nom>=<valeur>]
    ex. rel[admin_level=4][name:de=Aostatal]."""
    return "rel[admin_level={}][{}={}]".format(
        admin_level, name_key, name_value
    )


# ── MODE PAR TUILE : numéro de tuile → liste des zones qu'elle contient ───────
import re as _re


def _parse_tile(tile):
    """'+48+007' ou '+46-003' → (lat, lon) entiers signés, ou None si invalide.
    Convention Ortho : nom de tuile = coin sud-ouest, signe + 2 chiffres lat,
    signe + 3 chiffres lon."""
    if not tile:
        return None
    m = _re.match(r'^\s*([+-]\d{2})([+-]\d{3})\s*$', str(tile).strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def _tile_to_bbox(tile):
    """Renvoie (south, west, north, east) pour Overpass, ou None.
    La tuile fait 1°×1° : bbox = (lat, lon, lat+1, lon+1)."""
    p = _parse_tile(tile)
    if p is None:
        return None
    lat, lon = p
    return (lat, lon, lat + 1, lon + 1)


def _active_tile_from_parent(parent):
    """Récupère le numéro de la tuile active depuis la fenêtre principale
    d'Ortho (parent.lat / parent.lon), au format '+48+007'. Renvoie une chaîne
    vide si indisponible. Même source que le générateur .lay (parent.lat.get()).
    Toujours protégé : jamais de plantage si parent absent ou champs vides."""
    if parent is None:
        return ""
    try:
        lat = int(parent.lat.get())
        lon = int(parent.lon.get())
        return "{:+03d}{:+04d}".format(lat, lon)
    except Exception:
        return ""


def _reload_extents_hot():
    """Recharge « à chaud » la liste des extents connus d'Ortho, pour qu'un
    extent tout juste créé soit pris en compte SANS relancer l'application.

    Prudence maximale :
      - on ne RÉ-IMPORTE PAS O4_Imagery_Utils (module lourd) : on réutilise
        l'instance déjà chargée en mémoire (sys.modules) ;
      - tout est enveloppé : au moindre souci, on renvoie False et l'appelant
        affiche simplement « pensez à relancer ». Aucun plantage possible.
    Renvoie True si le rechargement a réussi, False sinon."""
    try:
        import sys as _sys
        IMG = _sys.modules.get("O4_Imagery_Utils")
        if IMG is None:
            return False  # moteur pas encore chargé (ex. test isolé)
        fn = getattr(IMG, "initialize_extents_dict", None)
        if not callable(fn):
            return False
        fn()  # ré-scanne Extents/ et complète extents_dict (affectation par clé)
        return True
    except Exception:
        return False


def _osm_list_zones(tile, admin_level, timeout=25):
    """Interroge Overpass : quelles zones de niveau <admin_level> touchent la
    tuile ? Renvoie :
      - une liste triée de dicts {name, admin_level, kind} (peut être vide),
      - "bad_tile" si le numéro de tuile est invalide,
      - None en cas d'échec réseau (tous serveurs KO).
    Réutilise serveurs + User-Agent d'O4_OSM_Utils. Un essai par serveur."""
    bbox = _tile_to_bbox(tile)
    if bbox is None:
        return "bad_tile"
    try:
        import requests
    except Exception:
        return None
    import json as _json
    servers, ua = _osm_servers_and_ua()
    s_lat, w_lon, n_lat, e_lon = bbox
    data = ("[out:json];relation[boundary=administrative]"
            "[admin_level={}]({},{},{},{});out tags;").format(
                admin_level, s_lat, w_lon, n_lat, e_lon)
    for code, base in servers.items():
        url = base + "?data=" + data
        try:
            sess = requests.Session()
            sess.headers.update({"User-Agent": ua})
            r = sess.get(url, timeout=timeout)
            if "200" not in str(r):
                continue
            payload = _json.loads(r.text)
            zones = []
            seen = set()
            for el in payload.get("elements", []):
                tags = el.get("tags", {})
                name = (tags.get("name", "") or "").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                zones.append({
                    "name": name,
                    "admin_level": tags.get("admin_level", str(admin_level)),
                    "kind": tags.get("border_type",
                                     tags.get("admin_title", "")),
                })
            zones.sort(key=lambda z: z["name"].lower())
            return zones
        except Exception:
            continue  # serveur suivant, pas de retente infinie
    return None


# ── Test réseau léger : la zone existe-t-elle sous cette clé de nom ? ──────────
# NOTE : ce test est DISTINCT du téléchargement d'O4_OSM_Utils.get_overpass_data
# (qui, lui, retente indéfiniment — parfait pour un vrai download, inadapté à un
# test). Ici : une requête « out count » (réponse instantanée : combien
# d'objets ?), UN essai par serveur, timeout court, pas de boucle infinie.
# On réutilise la MÊME liste de serveurs et le MÊME User-Agent qu'O4_OSM_Utils
# (cohérence, aucune divergence), lus dynamiquement si le module est présent.
def _osm_servers_and_ua():
    """Récupère serveurs + User-Agent depuis O4_OSM_Utils si présent, sinon
    valeurs de repli identiques à celles du moteur (V3.2)."""
    servers = {
        "KU": "https://overpass.kumi.systems/api/interpreter",
        "DE": "http://overpass-api.de/api/interpreter",
        "RU": "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    }
    ua = ("Ortho4XP/3.2 (https://github.com/oscar-broman/Ortho4XP; "
          "contact: ortho4xp@github.com)")
    try:
        import O4_OSM_Utils as _OSM
        s = getattr(_OSM, "overpass_servers", None)
        if isinstance(s, dict) and s:
            servers = dict(s)
    except Exception:
        pass
    return servers, ua


def _osm_count(admin_level, name_key, name_value, timeout=15):
    """Combien de relations correspondent ? Retourne :
        >=0 : nombre d'objets trouvés (0 = aucune)
        -1  : impossible de tester (réseau/serveurs KO ou requests absent).
    UN essai par serveur, pas de retente infinie."""
    try:
        import requests
    except Exception:
        return -1
    import re
    servers, ua = _osm_servers_and_ua()
    # Requête de comptage : réponse quasi instantanée.
    q = 'relation[admin_level={}]["{}"="{}"];out count;'.format(
        admin_level, name_key, name_value)
    for code, base in servers.items():
        url = base + "?data=" + q
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": ua})
            r = s.get(url, timeout=timeout)
            if "200" not in str(r):
                continue
            txt = r.text
            # Overpass renvoie le total dans une balise <count>…total…</count>
            m = re.search(r'total["\s:=v>]+.*?(\d+)', txt, re.S)
            if not m:
                m = re.search(r'"total"\s*:\s*"?(\d+)', txt)
            if m:
                return int(m.group(1))
            continue
        except Exception:
            continue  # serveur suivant, PAS de retente infinie
    return -1


def _cascade_find_key(admin_level, name_value, log):
    """Essaie chaque clé de _NAME_KEYS jusqu'à en trouver une qui matche.
    Renvoie (clé_gagnante, statut) :
      statut = "found"    → clé trouvée, name_value est bon
      statut = "none"     → testé partout, aucune clé ne matche (nom à revoir)
      statut = "no_net"   → impossible de tester (réseau) → on ne bloque pas,
                            on laissera Mask tenter avec 'name' par défaut.
    """
    net_ok = False
    for key in _NAME_KEYS:
        n = _osm_count(admin_level, key, name_value)
        if n == -1:
            # Erreur réseau sur cette tentative ; on note et on continue,
            # mais si TOUT échoue en réseau on le signalera.
            log("  " + key + " : " + _L("réseau indisponible",
                                        "network unavailable"))
            continue
        net_ok = True
        log("  " + key + " : " + str(n) + " " +
            _L("objet(s)", "object(s)"))
        if n > 0:
            log(_L("  → trouvé avec « %s »", "  → found with “%s”") % key)
            return key, "found"
    if not net_ok:
        return None, "no_net"
    return None, "none"


# ── Vérification du trio produit ──────────────────────────────────────────────
def _trio_status(country_dir, extent_code):
    """Retourne (present, manquants) pour le trio .ext/.png/.osm.bz2."""
    base = os.path.join(country_dir, extent_code)
    attendus = {
        ".ext": base + ".ext",
        ".png": base + ".png",
        ".osm.bz2": base + ".osm.bz2",
    }
    manquants = [ext for ext, chemin in attendus.items()
                 if not os.path.isfile(chemin)]
    return (len(manquants) == 0, manquants)


# ── Lancement de la création (via O4_Mask_Utils.py, non modifié) ──────────────
def _run_creation(country_name, extent_code, admin_level,
                  name_value, pixel_size, buffer_size, blur_size, log,
                  known_key=None):
    """Crée le trio d'extent en lançant l'outil O4_Mask_Utils.py existant.

    - Si known_key est fourni (mode « par tuile » : le nom vient déjà d'OSM),
      on l'utilise directement, sans cascade.
    - Sinon (mode « par nom » : saisie experte), on trouve AUTOMATIQUEMENT la
      bonne clé de nom OSM par cascade (name / name:fr / name:de…).
    - Se place dans Extents/<country_name>/ (créé si besoin) pour que le trio
      s'y range automatiquement (Mask écrit dans le répertoire courant).
    - N'écrit RIEN lui-même : tout le travail est fait par Mask.
    - Vérifie ensuite la présence du trio et rapporte proprement.
    Renvoie True si le trio complet a été créé, False sinon."""
    import subprocess

    mask = _mask_utils_path()
    if not os.path.isfile(mask):
        log(_L("Introuvable : O4_Mask_Utils.py (dans src/).",
               "Not found: O4_Mask_Utils.py (in src/)."))
        return False

    # Dossier de destination (créé s'il n'existe pas encore).
    country_dir = os.path.join(_extents_dir(), country_name)
    try:
        os.makedirs(country_dir, exist_ok=True)
    except Exception as ex:
        log(_L("Impossible de créer le dossier : %s",
               "Could not create the folder: %s") % ex)
        return False

    if known_key:
        # Mode « par tuile » : le nom vient directement d'OSM, clé connue.
        name_key = known_key
    else:
        # Mode « par nom » : cascade automatique pour trouver la bonne clé.
        log(_L("Recherche de la zone dans OpenStreetMap…",
               "Looking up the area in OpenStreetMap…"))
        name_key, statut = _cascade_find_key(admin_level, name_value, log)

        if statut == "none":
            log(_L("⚠️ Zone introuvable sous ce nom, quelle que soit la langue.",
                   "⚠️ Area not found under this name, in any language."))
            log(_L("Vérifiez l'orthographe exacte (accents, tirets) telle "
                   "qu'elle apparaît sur openstreetmap.org.",
                   "Check the exact spelling (accents, hyphens) as shown "
                   "on openstreetmap.org."))
            return False

        if statut == "no_net":
            # Pas de réseau pour tester : on ne bloque pas, on tente 'name'.
            name_key = "name"
            log(_L("Test réseau indisponible — tentative avec « name » par défaut.",
                   "Network test unavailable — trying with “name” by default."))

    query = _build_osm_query(admin_level, name_key, name_value)

    # Commande calquée EXACTEMENT sur l'usage prouvé (format version actuelle) :
    #   python O4_Mask_Utils.py <code> <pixel> <buffer> <blur> <requête>
    cmd = [
        sys.executable or "python3", mask, extent_code,
        str(pixel_size), str(buffer_size), str(blur_size), query,
    ]

    log(_L("Création de l'extent en cours…",
           "Creating the extent, please wait…"))
    log("→ " + extent_code + "  (" + query + ")")

    try:
        # cwd = Extents/<pays>/  → le trio se range tout seul ici.
        proc = subprocess.run(
            cmd, cwd=country_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except Exception as ex:
        log(_L("Erreur au lancement : %s", "Launch error: %s") % ex)
        return False

    # On vérifie le résultat par la présence du trio (pas par le code retour,
    # car Mask sort proprement même quand la frontière est introuvable).
    complet, manquants = _trio_status(country_dir, extent_code)
    if complet:
        log(_L("✅ Extent créé : les 3 fichiers sont présents dans %s/",
               "✅ Extent created: all 3 files present in %s/") % country_name)
        # Rechargement à chaud : l'extent devient connu sans relancer Ortho.
        if _reload_extents_hot():
            log(_L("↻ Extent rechargé — disponible sans relancer Ortho.",
                   "↻ Extent reloaded — available without restarting Ortho."))
        else:
            log(_L("Pensez à relancer Ortho pour qu'il soit pris en compte.",
                   "Remember to restart Ortho so it is taken into account."))
        return True
    else:
        # Cas le plus fréquent : nom OSM incorrect → réponse vide → rien créé.
        log(_L("⚠️ Aucun extent complet créé (manque : %s).",
               "⚠️ No complete extent created (missing: %s).")
            % ", ".join(manquants))
        log(_L("Vérifiez l'orthographe du nom OSM et la clé de nom "
               "(name, name:fr, name:de…), puis réessayez.",
               "Check the OSM name spelling and the name key "
               "(name, name:fr, name:de…), then try again."))
        return False


def _run_creation_from_osm(country_name, extent_code, osm_bz2_path,
                           pixel_size, buffer_size, blur_size, log):
    """Crée un extent à partir d'un fichier .osm.bz2 DÉJÀ CONSTRUIT (typiquement
    tracé à la main dans JOSM). Reproduit ce que l'expert fait en console :
      1. copie le .osm.bz2 fourni dans Extents/<pays>/<code>.osm.bz2 ;
      2. lance O4_Mask_Utils.py avec 5 arguments (SANS requête OSM) ;
         → Mask détecte le fichier présent et le RECYCLE (pas de téléchargement).
    Renvoie True si le trio complet est créé, False sinon."""
    import subprocess
    import shutil

    mask = _mask_utils_path()
    if not os.path.isfile(mask):
        log(_L("Introuvable : O4_Mask_Utils.py (dans src/).",
               "Not found: O4_Mask_Utils.py (in src/)."))
        return False

    if not osm_bz2_path or not os.path.isfile(osm_bz2_path):
        log(_L("Fichier .osm.bz2 introuvable : %s",
               "The .osm.bz2 file was not found: %s") % osm_bz2_path)
        return False

    # Dossier de destination (créé si besoin).
    country_dir = os.path.join(_extents_dir(), country_name)
    try:
        os.makedirs(country_dir, exist_ok=True)
    except Exception as ex:
        log(_L("Impossible de créer le dossier : %s",
               "Could not create the folder: %s") % ex)
        return False

    # Mask attend le fichier nommé <code>.osm.bz2 dans le répertoire courant.
    cible = os.path.join(country_dir, extent_code + ".osm.bz2")
    try:
        # Ne pas se copier sur soi-même si la source est déjà la cible.
        if os.path.abspath(osm_bz2_path) != os.path.abspath(cible):
            shutil.copy2(osm_bz2_path, cible)
    except Exception as ex:
        log(_L("Copie du .osm.bz2 impossible : %s",
               "Could not copy the .osm.bz2: %s") % ex)
        return False

    # Commande à 5 arguments (SANS requête) → Mask recycle le .osm.bz2 présent.
    cmd = [
        sys.executable or "python3", mask, extent_code,
        str(pixel_size), str(buffer_size), str(blur_size),
    ]
    log(_L("Construction de l'extent depuis le .osm.bz2 fourni…",
           "Building the extent from the provided .osm.bz2…"))
    log("→ " + extent_code + "  (.osm.bz2 recyclé)")

    try:
        proc = subprocess.run(
            cmd, cwd=country_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except Exception as ex:
        log(_L("Erreur au lancement : %s", "Launch error: %s") % ex)
        return False

    complet, manquants = _trio_status(country_dir, extent_code)
    if complet:
        log(_L("✅ Extent créé depuis le .osm.bz2 : 3 fichiers présents dans %s/",
               "✅ Extent created from the .osm.bz2: 3 files present in %s/")
            % country_name)
        if _reload_extents_hot():
            log(_L("↻ Extent rechargé — disponible sans relancer Ortho.",
                   "↻ Extent reloaded — available without restarting Ortho."))
        else:
            log(_L("Pensez à relancer Ortho pour qu'il soit pris en compte.",
                   "Remember to restart Ortho so it is taken into account."))
        return True
    else:
        log(_L("⚠️ Extent incomplet (manque : %s). Le .osm.bz2 est-il valide ?",
               "⚠️ Incomplete extent (missing: %s). Is the .osm.bz2 valid?")
            % ", ".join(manquants))
        return False


# ── Fenêtre principale (deux modes : Par tuile / Par nom) ─────────────────────
def run_extent_generator(parent=None):
    """Ouvre la fenêtre « Générateur d'Extents ».
    Deux modes :
      • Par tuile (grand public) : on saisit un numéro de tuile, le module liste
        les zones réelles qu'elle contient, l'utilisateur coche → un extent par
        case cochée (nom OSM utilisé tel quel).
      • Par nom (expert) : on saisit directement un nom de zone (cascade de clés).
    Import tkinter LOCAL (au clic). parent = fenêtre principale ou None (test)."""
    import tkinter as tk
    from tkinter import ttk

    BG = _c("bg", "#3b5b49")
    FG = _c("fg", "#e8f0ec")
    FG2 = _c("fg_secondary", "#a6e3a1")
    ENTRY_BG = _c("bg_secondary", "#2a4235")

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_L("Ortho4XP — Générateur d'Extents",
                 "Ortho4XP — Extent Generator"))
    win.configure(bg=BG)
    win.resizable(True, True)

    def _fixer_taille_min(w):
        """Ouvre la fenêtre à la taille de son contenu et EMPÊCHE de la réduire
        en dessous : rien n'est jamais masqué, ni en largeur ni en hauteur. On
        ne fige PAS la taille (position seule), donc la fenêtre grandit d'elle-
        même quand le contenu grandit (changement de mode) ; minsize interdit
        de la rétrécir sous le contenu courant."""
        try:
            w.update_idletasks()
            rw, rh = w.winfo_reqwidth(), w.winfo_reqheight()
            sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
            x = max(0, (sw - rw) // 2)
            y = max(0, (sh - rh) // 3)
            w.minsize(rw, rh)
            w.geometry("+%d+%d" % (x, y))
            w.resizable(True, True)
            w.lift()
        except Exception:
            pass

    # Style pour la liste déroulante de destination. Sur macOS, tk.OptionMenu
    # n'affiche pas sa valeur (case vide) ; une ttk.Combobox readonly l'affiche
    # de façon fiable sur les 3 OS. On configure un style nommé SANS changer le
    # thème global (pas d'effet de bord sur les autres fenêtres ttk).
    _style = ttk.Style(win)
    _style.configure("O4Dest.TCombobox", fieldbackground=ENTRY_BG,
                     background=_c("btn_bg", "#4a6b59"), foreground=FG,
                     arrowcolor=FG)
    try:
        _style.map("O4Dest.TCombobox",
                   fieldbackground=[("readonly", ENTRY_BG)],
                   foreground=[("readonly", FG)],
                   selectbackground=[("readonly", ENTRY_BG)],
                   selectforeground=[("readonly", FG)])
    except Exception:
        pass

    def _font(sz, bold=False):
        fam = "Helvetica" if _OS == "mac" else "Segoe UI"
        return (fam, sz, "bold") if bold else (fam, sz)

    # Titre
    tk.Label(win, text=_L("Générateur d'Extents", "Extent Generator"),
             bg=BG, fg=FG, font=_font(15 if _OS == "mac" else 12, True),
             pady=6).pack(fill="x", padx=14, pady=(10, 0))

    # ── Sélecteur de mode ──
    mode_var = tk.StringVar(value="tuile")  # grand public par défaut
    mode_row = tk.Frame(win, bg=BG)
    mode_row.pack(fill="x", padx=14, pady=(4, 6))
    tk.Label(mode_row, text=_L("Mode :", "Mode:"), bg=BG, fg=FG,
             font=_font(11 if _OS == "mac" else 9)).pack(side="left", padx=(0, 8))
    tk.Radiobutton(mode_row,
                   text=_L("Par tuile (simple)", "By tile (simple)"),
                   variable=mode_var, value="tuile",
                   bg=BG, fg=FG, selectcolor=ENTRY_BG, activebackground=BG,
                   activeforeground=FG, highlightthickness=0,
                   font=_font(10 if _OS == "mac" else 9)).pack(side="left", padx=(0, 10))
    tk.Radiobutton(mode_row,
                   text=_L("Par nom (expert)", "By name (expert)"),
                   variable=mode_var, value="nom",
                   bg=BG, fg=FG, selectcolor=ENTRY_BG, activebackground=BG,
                   activeforeground=FG, highlightthickness=0,
                   font=_font(10 if _OS == "mac" else 9)).pack(side="left")

    # ── Ligne commune : dossier de destination ──
    dest_frame = tk.Frame(win, bg=BG)
    dest_frame.pack(fill="x", padx=14, pady=(2, 2))
    tk.Label(dest_frame, text=_L("Dossier de destination :", "Destination folder:"),
             bg=BG, fg=FG, font=_font(11 if _OS == "mac" else 9)
             ).pack(side="left", padx=(0, 6))
    pays_existants = _scan_country_dirs()
    NOUVEAU = _L("＋ Nouveau…", "＋ New…")
    dest_choices = pays_existants + [NOUVEAU]
    dest_var = tk.StringVar(value=dest_choices[0] if dest_choices else NOUVEAU)
    dest_menu = ttk.Combobox(dest_frame, textvariable=dest_var,
                             values=dest_choices, state="readonly",
                             style="O4Dest.TCombobox",
                             font=_font(11 if _OS == "mac" else 9))
    dest_menu.pack(side="left", fill="x", expand=True)

    # Ligne dédiée pour le nom du nouveau dossier (apparaît si « Nouveau… »).
    new_dir_frame = tk.Frame(win, bg=BG)
    new_dir_var = tk.StringVar(value="")
    tk.Label(new_dir_frame, text=_L("Nom du nouveau dossier :",
                                    "New folder name:"),
             bg=BG, fg=FG, font=_font(11 if _OS == "mac" else 9)
             ).pack(side="left", padx=(0, 6))
    new_dir_entry = tk.Entry(new_dir_frame, textvariable=new_dir_var,
                             bg=ENTRY_BG, fg=FG, insertbackground=FG,
                             font=_font(11 if _OS == "mac" else 9))
    new_dir_entry.pack(side="left", fill="x", expand=True)

    def _on_dest_change(*_a):
        if dest_var.get() == NOUVEAU:
            # placée juste après la ligne du menu de destination
            new_dir_frame.pack(fill="x", padx=14, pady=(0, 4), after=dest_frame)
            new_dir_entry.focus_set()
        else:
            new_dir_frame.pack_forget()
    dest_var.trace_add("write", _on_dest_change)

    def _resolve_dest(log):
        dest = dest_var.get()
        if dest == NOUVEAU:
            dest = new_dir_var.get().strip()
            if not dest:
                log(_L("Indiquez un nom de dossier de destination.",
                       "Please enter a destination folder name."))
                return None
        return dest

    # ── Ligne commune : niveau administratif ──
    level_frame = tk.Frame(win, bg=BG)
    level_frame.pack(fill="x", padx=14, pady=(2, 2))
    tk.Label(level_frame, text=_L("Niveau :", "Level:"), bg=BG, fg=FG,
             font=_font(11 if _OS == "mac" else 9)).pack(side="left", padx=(0, 8))
    level_var = tk.StringVar(value="6")  # Département par défaut (mode tuile)
    for code, fr, en in _ADMIN_LEVELS:
        tk.Radiobutton(level_frame, text=_L(fr, en), variable=level_var, value=code,
                       bg=BG, fg=FG, selectcolor=ENTRY_BG, activebackground=BG,
                       activeforeground=FG, highlightthickness=0,
                       font=_font(10 if _OS == "mac" else 9)).pack(side="left", padx=(0, 8))

    # ── Panneau MODE TUILE ──
    tuile_frame = tk.Frame(win, bg=BG)
    trow = tk.Frame(tuile_frame, bg=BG)
    trow.pack(fill="x", pady=(4, 2))
    tk.Label(trow, text=_L("Numéro de tuile :", "Tile number:"), bg=BG, fg=FG,
             font=_font(11 if _OS == "mac" else 9)).pack(side="left", padx=(0, 6))
    tile_var = tk.StringVar(value=_active_tile_from_parent(parent))
    tile_entry = tk.Entry(trow, textvariable=tile_var, bg=ENTRY_BG, fg=FG,
                          insertbackground=FG, width=12,
                          font=_font(11 if _OS == "mac" else 9))
    tile_entry.pack(side="left")
    tk.Label(trow, text=_L("  (ex : +48+007)", "  (e.g. +48+007)"), bg=BG, fg=FG2,
             font=_font(10 if _OS == "mac" else 8)).pack(side="left")

    # Zone scrollable des cases à cocher
    check_outer = tk.Frame(tuile_frame, bg=ENTRY_BG, highlightthickness=1,
                           highlightbackground=_c("btn_bg", "#4a6b59"))
    check_outer.pack(fill="both", expand=True, pady=(4, 2))
    check_canvas = tk.Canvas(check_outer, bg=ENTRY_BG, height=140,
                             highlightthickness=0)
    check_scroll = tk.Scrollbar(check_outer, orient="vertical",
                                command=check_canvas.yview)
    check_inner = tk.Frame(check_canvas, bg=ENTRY_BG)
    check_inner.bind("<Configure>",
                     lambda e: check_canvas.configure(
                         scrollregion=check_canvas.bbox("all")))
    check_canvas.create_window((0, 0), window=check_inner, anchor="nw")
    check_canvas.configure(yscrollcommand=check_scroll.set)
    check_canvas.pack(side="left", fill="both", expand=True)
    check_scroll.pack(side="right", fill="y")

    zone_vars = []  # liste de (BooleanVar, dict_zone)

    def _clear_checks():
        for w in check_inner.winfo_children():
            w.destroy()
        zone_vars.clear()

    def _lister_zones():
        _clear_checks()
        tile = tile_var.get().strip()
        log(_L("Recherche des zones dans la tuile %s…",
               "Looking up areas in tile %s…") % tile)
        res = _osm_list_zones(tile, level_var.get())
        if res == "bad_tile":
            log(_L("Numéro de tuile invalide (format attendu : +48+007).",
                   "Invalid tile number (expected format: +48+007)."))
            return
        if res is None:
            log(_L("Réseau indisponible ou serveurs OSM occupés. Réessayez.",
                   "Network unavailable or OSM servers busy. Please retry."))
            return
        if not res:
            log(_L("Aucune zone de ce niveau dans cette tuile.",
                   "No area of this level in this tile."))
            return
        log(_L("%d zone(s) trouvée(s). Cochez celles à créer.",
               "%d area(s) found. Tick the ones to create.") % len(res))
        for z in res:
            var = tk.BooleanVar(value=False)
            label = z["name"]
            if z.get("kind"):
                label += "   (" + z["kind"] + ")"
            cb = tk.Checkbutton(check_inner, text=label, variable=var,
                                bg=ENTRY_BG, fg=FG, selectcolor=BG,
                                activebackground=ENTRY_BG, activeforeground=FG,
                                highlightthickness=0, anchor="w",
                                font=_font(10 if _OS == "mac" else 9))
            cb.pack(fill="x", anchor="w")
            zone_vars.append((var, z))

    def _check_all(flag):
        for var, _z in zone_vars:
            var.set(flag)

    lister_btn = _make_themed_button(
        tk, tuile_frame, _L("🔍  Lister les zones de la tuile",
                            "🔍  List the tile's areas"), _lister_zones)
    lister_btn.pack(fill="x", pady=(2, 2))

    # Boutons de sélection groupée (pratique quand la tuile a beaucoup de zones)
    sel_row = tk.Frame(tuile_frame, bg=BG)
    sel_row.pack(fill="x", pady=(0, 2))
    _make_themed_button(tk, sel_row,
                        _L("☑ Tout cocher", "☑ Select all"),
                        lambda: _check_all(True)
                        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
    _make_themed_button(tk, sel_row,
                        _L("☐ Tout décocher", "☐ Clear all"),
                        lambda: _check_all(False)
                        ).pack(side="left", fill="x", expand=True)

    # ── Panneau MODE NOM (expert) ──
    nom_frame = tk.Frame(win, bg=BG)
    nrow = tk.Frame(nom_frame, bg=BG)
    nrow.pack(fill="x", pady=(4, 2))
    tk.Label(nrow, text=_L("Nom de la zone :", "Area name:"), bg=BG, fg=FG,
             font=_font(11 if _OS == "mac" else 9)).pack(side="left", padx=(0, 6))
    name_var = tk.StringVar(value="")
    name_entry = tk.Entry(nrow, textvariable=name_var, bg=ENTRY_BG, fg=FG,
                          insertbackground=FG, font=_font(11 if _OS == "mac" else 9))
    name_entry.pack(side="left", fill="x", expand=True)
    nrow2 = tk.Frame(nom_frame, bg=BG)
    nrow2.pack(fill="x", pady=(4, 2))
    tk.Label(nrow2, text=_L("Nom du fichier extent :", "Extent file name:"),
             bg=BG, fg=FG, font=_font(11 if _OS == "mac" else 9)
             ).pack(side="left", padx=(0, 6))
    code_var = tk.StringVar(value="")
    code_entry = tk.Entry(nrow2, textvariable=code_var, bg=ENTRY_BG, fg=FG,
                          insertbackground=FG, font=_font(11 if _OS == "mac" else 9))
    code_entry.pack(side="left", fill="x", expand=True)
    code_edited = {"by_user": False}

    def _sync_code(*_a):
        if code_edited["by_user"]:
            return
        code_var.set(name_var.get().strip().replace(" ", "_"))
    name_var.trace_add("write", _sync_code)
    code_entry.bind("<Key>", lambda e: code_edited.__setitem__("by_user", True))

    # ── Option EXPERT : utiliser un .osm.bz2 déjà construit (JOSM) ──
    osm_use_var = tk.BooleanVar(value=False)
    osm_path_var = tk.StringVar(value="")
    osm_row = tk.Frame(nom_frame, bg=BG)
    osm_row.pack(fill="x", pady=(6, 2))
    tk.Checkbutton(
        osm_row,
        text=_L("J'ai déjà un fichier .osm.bz2 (tracé JOSM)",
                "I already have a .osm.bz2 file (JOSM-drawn)"),
        variable=osm_use_var, bg=BG, fg=FG, selectcolor=ENTRY_BG,
        activebackground=BG, activeforeground=FG, highlightthickness=0,
        font=_font(10 if _OS == "mac" else 9)
    ).pack(side="left")

    osm_pick_row = tk.Frame(nom_frame, bg=BG)  # affiché seulement si coché
    # Nom du fichier choisi, affiché clairement (le chemin complet reste dans
    # osm_path_var, utilisé par la construction). Avant : chemin complet en
    # petite police secondaire, difficile à voir → on montre « ✓ nom.osm.bz2 ».
    osm_disp_var = tk.StringVar(value="")
    _osm_dernier_dir = {"d": ""}  # mémoire de session du dernier dossier ouvert

    def _choisir_osm():
        try:
            from tkinter import filedialog
            chemin = filedialog.askopenfilename(
                title=_L("Choisir un fichier .osm.bz2",
                         "Choose a .osm.bz2 file"),
                initialdir=(_osm_dernier_dir["d"]
                            if _osm_dernier_dir["d"] else ""),
                filetypes=[("OSM bz2", "*.osm.bz2"), ("Tous", "*.*")])
            if chemin:
                osm_path_var.set(chemin)
                osm_disp_var.set("✓ " + os.path.basename(chemin))
                _osm_dernier_dir["d"] = os.path.dirname(chemin)
        except Exception:
            pass

    _make_themed_button(
        tk, osm_pick_row,
        _L("📂 Choisir le .osm.bz2", "📂 Choose the .osm.bz2"),
        _choisir_osm).pack(side="left", padx=(0, 6))
    tk.Label(osm_pick_row, textvariable=osm_disp_var, bg=BG,
             fg=FG, font=_font(11 if _OS == "mac" else 9),
             anchor="w").pack(side="left", fill="x", expand=True)

    def _on_osm_toggle(*_a):
        if osm_use_var.get():
            osm_pick_row.pack(fill="x", pady=(0, 2), after=osm_row)
        else:
            osm_pick_row.pack_forget()
    osm_use_var.trace_add("write", _on_osm_toggle)

    # ── Bascule d'affichage selon le mode ──
    def _on_mode_change(*_a):
        if mode_var.get() == "tuile":
            nom_frame.pack_forget()
            tuile_frame.pack(fill="both", expand=True, padx=14, pady=(2, 2),
                             after=level_frame)
        else:
            tuile_frame.pack_forget()
            nom_frame.pack(fill="x", padx=14, pady=(2, 2), after=level_frame)
        # Le contenu change de hauteur selon le mode : on ré-ajuste pour que
        # rien ne soit masqué et que la fenêtre ne puisse pas être réduite en
        # dessous du contenu courant.
        _fixer_taille_min(win)
    mode_var.trace_add("write", _on_mode_change)

    # ── Réglages avancés (repliés) ──
    px_var = tk.StringVar(value=_PIXEL_PAR_NIVEAU.get(level_var.get(),
                                                      _DEFAULT_PIXEL))
    bf_var = tk.StringVar(value=_DEFAULT_BUFFER)
    bl_var = tk.StringVar(value=_DEFAULT_BLUR)

    # La finesse par défaut suit le niveau (département=10, région=30, pays=200)
    # tant que l'utilisateur n'a pas saisi sa propre valeur. Dès qu'il modifie
    # le champ à la main, on respecte son choix et on ne l'écrase plus.
    _px_touche_par_user = {"on": False}

    def _on_level_change_px(*_a):
        if _px_touche_par_user["on"]:
            return  # l'utilisateur a fixé sa valeur : on n'y touche pas
        px_var.set(_PIXEL_PAR_NIVEAU.get(level_var.get(), _DEFAULT_PIXEL))
    level_var.trace_add("write", _on_level_change_px)

    adv_frame = tk.Frame(win, bg=BG)
    for i, (lab_fr, lab_en, var) in enumerate([
        ("Finesse (pixel_size)", "Fineness (pixel_size)", px_var),
        ("Marge (buffer)", "Buffer", bf_var),
        ("Adoucissement (blur)", "Blur", bl_var),
    ]):
        tk.Label(adv_frame, text=_L(lab_fr, lab_en), bg=BG, fg=FG2,
                 font=_font(10 if _OS == "mac" else 9)
                 ).grid(row=i, column=0, sticky="w", padx=(4, 6), pady=1)
        ent = tk.Entry(adv_frame, textvariable=var, bg=ENTRY_BG, fg=FG,
                       insertbackground=FG, width=10,
                       font=_font(10 if _OS == "mac" else 9))
        ent.grid(row=i, column=1, sticky="w", pady=1)
        if var is px_var:
            # Marquer que l'utilisateur a pris la main dès qu'il tape dans px.
            ent.bind("<Key>",
                     lambda e: _px_touche_par_user.__setitem__("on", True))
    # Guide de résolution (conseils Oscar Pilote / tests extents).
    tk.Label(adv_frame,
             text=_L(
                 "Finesse = précision du masque.\n"
                 "Marge = 0 de préférence (négatif = rentrer la frontière).\n"
                 "Dégradé = 0 de préférence (n’augmenter que si le provider d’en face déborde).",
                 "Fineness = mask precision.\n"
                 "Buffer = 0 preferred (negative = pull border inward).\n"
                 "Blur = 0 preferred (increase only if the opposite provider overlaps)."
             ),
             bg=BG, fg=FG2, font=_font(9 if _OS == "mac" else 8),
             wraplength=440, justify="left"
             ).grid(row=3, column=0, columnspan=2, sticky="w", padx=(4, 6),
                    pady=(4, 1))
    adv_shown = {"on": False}

    def _toggle_adv():
        adv_shown["on"] = not adv_shown["on"]
        if adv_shown["on"]:
            adv_frame.pack(fill="x", padx=18, pady=(2, 4))
        else:
            adv_frame.pack_forget()
    _make_themed_button(tk, win, _L("⚙ Réglages avancés", "⚙ Advanced settings"),
                        _toggle_adv).pack(fill="x", padx=14, pady=(6, 2))

    # ── Console ──
    console = tk.Text(win, height=6, bg=_c("console_bg", "#0f0f1a"),
                      fg=_c("console_fg", "#50fa7b"), insertbackground=FG,
                      font=("Courier", 10), wrap="word", relief="flat")
    console.pack(fill="both", expand=True, padx=14, pady=(6, 4))

    def log(msg):
        try:
            console.insert("end", msg + "\n")
            console.see("end")
            console.update_idletasks()
        except Exception:
            pass

    def _adv_values():
        def _num(v, d):
            v = (v or "").strip()
            try:
                float(v); return v
            except Exception:
                return d
        return (_num(px_var.get(), _DEFAULT_PIXEL),
                _num(bf_var.get(), _DEFAULT_BUFFER),
                _num(bl_var.get(), _DEFAULT_BLUR))

    # ── Bouton Créer ──
    def _creer():
        dest = _resolve_dest(log)
        if not dest:
            return
        px, bf, bl = _adv_values()

        if mode_var.get() == "tuile":
            coches = [(v.get(), z) for (v, z) in zone_vars if v.get()]
            if not coches:
                log(_L("Cochez au moins une zone à créer.",
                       "Tick at least one area to create."))
                return
            n_ok = 0
            for _flag, z in coches:
                nom = z["name"]
                code = nom.strip().replace(" ", "_")
                log(_L("── Création : %s ──", "── Creating: %s ──") % nom)
                ok = _run_creation(
                    country_name=dest, extent_code=code,
                    admin_level=z.get("admin_level", level_var.get()),
                    name_value=nom, pixel_size=px, buffer_size=bf,
                    blur_size=bl, log=log, known_key="name")
                if ok:
                    n_ok += 1
            log(_L("Terminé : %d extent(s) créé(s).",
                   "Done: %d extent(s) created.") % n_ok)
        else:
            # Mode « Par nom » (expert).
            # Cas A : l'utilisateur fournit un .osm.bz2 déjà construit (JOSM).
            if osm_use_var.get():
                osm_path = osm_path_var.get().strip()
                if not osm_path:
                    log(_L("Cochez la case puis choisissez votre fichier .osm.bz2.",
                           "Tick the box then choose your .osm.bz2 file."))
                    return
                code = code_var.get().strip()
                if not code:
                    base = os.path.basename(osm_path)
                    code = base.replace(".osm.bz2", "").replace(" ", "_")
                _run_creation_from_osm(
                    country_name=dest, extent_code=code,
                    osm_bz2_path=osm_path,
                    pixel_size=px, buffer_size=bf, blur_size=bl, log=log)
                return
            # Cas B : création classique par nom OSM (téléchargement).
            name_value = name_var.get().strip()
            if not name_value:
                log(_L("Indiquez le nom de la zone.",
                       "Please enter the area name."))
                return
            code = code_var.get().strip() or name_value.replace(" ", "_")
            _run_creation(
                country_name=dest, extent_code=code,
                admin_level=level_var.get(), name_value=name_value,
                pixel_size=px, buffer_size=bf, blur_size=bl, log=log)

    btn_row = tk.Frame(win, bg=BG)
    btn_row.pack(fill="x", padx=14, pady=(2, 12))
    _make_themed_button(tk, btn_row,
                        _L("💾  Créer l'extent", "💾  Create the extent"),
                        _creer).pack(side="left", fill="x", expand=True, padx=(0, 6))
    _make_themed_button(tk, btn_row, _L("Fermer", "Close"),
                        win.destroy).pack(side="left")

    # Affichage initial du bon panneau
    _on_mode_change()
    _tuile_pre = _active_tile_from_parent(parent)
    if _tuile_pre:
        log(_L("Prêt. Tuile active « %s » détectée. Cliquez « Lister les zones ».",
               "Ready. Active tile “%s” detected. Click “List the areas”.")
            % _tuile_pre)
    else:
        log(_L("Prêt. Mode « Par tuile » : saisissez un numéro (+48+007) puis "
               "« Lister les zones ».",
               "Ready. “By tile” mode: enter a number (+48+007) then "
               "“List the areas”."))

    _fixer_taille_min(win)
    return win


# Exécution autonome (test headless hors Ortho)
if __name__ == "__main__":
    run_extent_generator(None)
    try:
        import tkinter as _tk
        _tk._default_root.mainloop()  # type: ignore[attr-defined]
    except Exception:
        pass
