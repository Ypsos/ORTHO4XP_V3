# -*- coding: utf-8 -*-
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — Mars 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CREDIT — AUTHOR: Roland (Ypsos) — March 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================
#  O4_Relief_Sonny_Utils.py  —  ÉTAPE 2 : gestion LOCALE des dalles Sonny
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  CONTEXTE (décidé avec Roland) — Sonny (sonny.4lima.de) ne distribue PAS
#    de dalle par URL : ses modèles 1"/3" sont des .hgt (format SRTM, 1°×1°)
#    fournis en archives .zip PAR PAYS, via Google Drive. On ne télécharge
#    donc rien automatiquement. L'utilisateur récupère et décompresse le(s)
#    pays qui l'intéressent ; Ortho4XP se charge de RANGER puis d'EXPLOITER
#    ces .hgt tout seul, pour qu'un débutant n'ait jamais à savoir « où
#    mettre les fichiers ».
#
#  CE QUE FAIT CE MODULE (100 % hors-ligne, aucune dépendance réseau) :
#    - emplacement_gere()   : où Ortho4XP range le relief Sonny. Par défaut
#                             <racine>/Elevation_data/Sonny/, redirigeable
#                             vers un autre disque (ex. SSD dédié).
#    - importer_dossier()   : COPIE vérifiée des .hgt d'un dossier extrait
#                             vers l'emplacement géré (copie atomique + garde
#                             anti-corruption). La source n'est jamais touchée
#                             tant que la copie n'est pas validée intègre.
#    - supprimer_source()   : nettoyage OPTIONNEL du dossier d'origine, à
#                             n'appeler qu'APRÈS un import vérifié.
#    - dalles_pour_tuile()  : liste les .hgt de l'emplacement géré couvrant
#                             une tuile (avec débord ; gère les tuiles à
#                             cheval sur plusieurs pays, ex. Alsace).
#
#  Ce module ne modifie AUCUN moteur, n'écrit pas custom_dem, ne lève jamais
#  vers l'appelant. L'assemblage en TIFF et l'écriture custom_dem seront le
#  chapitre suivant, en réutilisant assembler_tuile() de l'Altimétrie.
#
#  RÈGLE Sonny : les modèles 0.5"/1"/3" sont « cross-country entirely filled »
#    — chaque .hgt d'un pays est déjà rempli jusqu'aux bords avec les données
#    voisines. Une tuile frontalière (Alsace : FR/DE/CH/LU) est donc couverte
#    dès que l'utilisateur possède le pays principal ; inutile de croiser les
#    pays. On raisonne uniquement en coordonnées .hgt, pas en frontières.
# ----------------------------------------------------------------------------

import os
import math
import shutil
import tempfile

# Côtés de grille .hgt admis (Sonny 1"=3601, 3"=1201 ; 1801 = variante SRTM).
_COTES_HGT = (1201, 1801, 3601)
_TAILLE_MIN_HGT = 1201 * 1201 * 2          # ~2,88 Mo : plancher de plausibilité

# Sous-dossier par défaut, sous la racine Ortho4XP.
_SOUS_DOSSIER_DEFAUT = os.path.join("Elevation_data", "Sonny")


# --------------------------------------------------------------------------
#  Nommage / analyse des dalles
# --------------------------------------------------------------------------
def nom_hgt(lat, lon):
    """Nom SRTM d'une cellule 1°×1° depuis son coin sud-ouest ENTIER.
    (48, 7) -> 'N48E007'   ;   (46, -3) -> 'N46W003'."""
    la = int(math.floor(lat))
    lo = int(math.floor(lon))
    ns = "N" if la >= 0 else "S"
    ew = "E" if lo >= 0 else "W"
    return "%s%02d%s%03d" % (ns, abs(la), ew, abs(lo))


def parse_nom_hgt(nom):
    """'N48E007(.hgt)' -> (48, 7). Retourne None si non conforme.
    Tolère la casse et l'extension."""
    try:
        base = os.path.basename(str(nom))
        if base.lower().endswith(".hgt"):
            base = base[:-4]
        base = base.strip().upper()
        if len(base) < 7:
            return None
        if base[0] not in ("N", "S") or base[3] not in ("E", "W"):
            return None
        lat = int(base[1:3])
        lon = int(base[4:7])
        if base[0] == "S":
            lat = -lat
        if base[3] == "W":
            lon = -lon
        return (lat, lon)
    except Exception:
        return None


# --------------------------------------------------------------------------
#  Emplacement géré
# --------------------------------------------------------------------------
def emplacement_gere(racine_ortho, chemin_choisi=None):
    """Retourne le dossier où ranger/lire le relief Sonny.

    - chemin_choisi renseigné (ex. SSD dédié) -> il est utilisé tel quel ;
    - sinon -> <racine_ortho>/Elevation_data/Sonny/.

    Ne crée PAS le dossier ici (création au moment de l'import). Ne lève pas.
    """
    try:
        if chemin_choisi:
            return os.path.abspath(os.path.expanduser(str(chemin_choisi)))
        return os.path.join(racine_ortho, _SOUS_DOSSIER_DEFAUT)
    except Exception:
        return os.path.join(racine_ortho or ".", _SOUS_DOSSIER_DEFAUT)


# --------------------------------------------------------------------------
#  Validation d'un .hgt (taille / grille), sans rien lire de lourd
# --------------------------------------------------------------------------
def hgt_valide(chemin):
    """True si le fichier a une taille cohérente avec une grille .hgt carrée
    admise. Ne lit pas le contenu (juste la taille). Ne lève jamais."""
    try:
        taille = os.path.getsize(chemin)
    except Exception:
        return False
    if taille < _TAILLE_MIN_HGT or taille % 2 != 0:
        return False
    n2 = taille // 2
    cote = int(round(math.sqrt(n2)))
    return cote * cote == n2 and cote in _COTES_HGT


# --------------------------------------------------------------------------
#  Indexation de l'emplacement géré
# --------------------------------------------------------------------------
def indexer(dossier):
    """Parcourt le dossier (récursif) et retourne un index
    { (lat, lon) : chemin } des .hgt valides. Doublons : le premier gagne.
    Ne lève jamais ; dossier absent -> index vide."""
    index = {}
    if not dossier or not os.path.isdir(dossier):
        return index
    for rep, _sous, fichiers in os.walk(dossier):
        for f in fichiers:
            if not f.lower().endswith(".hgt"):
                continue
            coord = parse_nom_hgt(f)
            if coord is None:
                continue
            chemin = os.path.join(rep, f)
            if not hgt_valide(chemin):
                continue
            if coord not in index:
                index[coord] = chemin
    return index


# --------------------------------------------------------------------------
#  Import : COPIE vérifiée vers l'emplacement géré
# --------------------------------------------------------------------------
def _copie_atomique_verifiee(src, dest):
    """Copie src -> dest via un fichier temporaire, puis vérifie que la
    taille copiée == taille source et que le résultat reste un .hgt valide.
    Retourne True si OK. Nettoie le temporaire en cas d'échec."""
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        taille_src = os.path.getsize(src)
        fd, tmp = tempfile.mkstemp(suffix=".part", dir=os.path.dirname(dest))
        os.close(fd)
        shutil.copyfile(src, tmp)
        if os.path.getsize(tmp) != taille_src or not hgt_valide(tmp):
            os.remove(tmp)
            return False
        os.replace(tmp, dest)
        return True
    except Exception:
        try:
            if 'tmp' in locals() and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


def importer_dossier(dossier_source, dossier_gere, log=None):
    """Copie tous les .hgt valides de `dossier_source` (récursif) vers
    `dossier_gere` (rangement à plat, un .hgt par coordonnée).

    La source n'est JAMAIS supprimée ici (voir supprimer_source()).

    Retour : dict {
        'copiees'      : [noms rangés],
        'deja'         : [noms déjà présents, ignorés],
        'rejetees'     : [noms invalides/corrompus],
        'total_source' : nb de .hgt vus dans la source,
        'ok'           : bool  # True si au moins une dalle exploitable en place
    }
    Ne lève jamais.
    """
    def _log(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass

    res = {"copiees": [], "deja": [], "rejetees": [],
           "total_source": 0, "ok": False}

    if not dossier_source or not os.path.isdir(dossier_source):
        _log("   [SONNY] Dossier source introuvable → rien à importer.")
        return res

    for rep, _sous, fichiers in os.walk(dossier_source):
        for f in fichiers:
            if not f.lower().endswith(".hgt"):
                continue
            res["total_source"] += 1
            src = os.path.join(rep, f)
            coord = parse_nom_hgt(f)
            if coord is None or not hgt_valide(src):
                res["rejetees"].append(f)
                continue
            nom = "%s.hgt" % nom_hgt(*coord)
            dest = os.path.join(dossier_gere, nom)
            # Déjà présent et valide → on ne recopie pas.
            if os.path.isfile(dest) and hgt_valide(dest):
                res["deja"].append(nom)
                continue
            if _copie_atomique_verifiee(src, dest):
                res["copiees"].append(nom)
            else:
                res["rejetees"].append(f)

    n_ok = len(res["copiees"]) + len(res["deja"])
    res["ok"] = n_ok > 0
    _log("   [SONNY] Import : %d rangée(s), %d déjà présente(s), %d rejetée(s) "
         "(sur %d vue(s))." % (len(res["copiees"]), len(res["deja"]),
                               len(res["rejetees"]), res["total_source"]))
    return res


def supprimer_source(dossier_source, log=None):
    """Supprime le dossier d'origine (extraction). À n'appeler qu'APRÈS un
    import vérifié, sur décision explicite de l'utilisateur. Ne lève jamais.
    Retourne True si supprimé."""
    def _log(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass
    try:
        if dossier_source and os.path.isdir(dossier_source):
            shutil.rmtree(dossier_source)
            _log("   [SONNY] Dossier d'origine supprimé.")
            return True
    except Exception as e:
        _log("   [SONNY] Suppression impossible (%s)." % type(e).__name__)
    return False


# --------------------------------------------------------------------------
#  Recherche des dalles couvrant une tuile
# --------------------------------------------------------------------------
def _cellules_couvrantes(lat, lon, debord=0.0):
    """Coins SO entiers (la, lo) des cellules 1° recouvrant la tuile
    [lat, lat+1] × [lon, lon+1] élargie du débord."""
    la_min = int(math.floor(lat - debord))
    la_max = int(math.floor(lat + 1 + debord - 1e-9))
    lo_min = int(math.floor(lon - debord))
    lo_max = int(math.floor(lon + 1 + debord - 1e-9))
    cellules = []
    for la in range(la_min, la_max + 1):
        for lo in range(lo_min, lo_max + 1):
            cellules.append((la, lo))
    return cellules


def dalles_pour_tuile(dossier_gere, lat, lon, debord=0.0, index=None,
                      log=None):
    """Retourne les chemins des .hgt de l'emplacement géré couvrant la
    tuile (lat, lon), débord inclus.

    Retour : dict {
        'fichiers'   : [chemins présents],
        'manquantes' : [(la, lo) attendues mais absentes],
        'ok'         : bool  # True si la cellule centrale est présente
    }
    `ok=False` → l'appelant NE doit PAS écrire custom_dem (repli DEM classique).
    Ne lève jamais.
    """
    def _log(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass

    res = {"fichiers": [], "manquantes": [], "ok": False}
    if index is None:
        index = indexer(dossier_gere)

    for (la, lo) in _cellules_couvrantes(lat, lon, debord):
        chemin = index.get((la, lo))
        if chemin and os.path.isfile(chemin):
            res["fichiers"].append(chemin)
        else:
            res["manquantes"].append((la, lo))

    centrale = (int(math.floor(lat)), int(math.floor(lon)))
    res["ok"] = (centrale in index) and bool(res["fichiers"])

    if res["ok"]:
        _log("   [SONNY] Tuile couverte : %d dalle(s) trouvée(s)."
             % len(res["fichiers"]))
    else:
        _log("   [SONNY] Couverture insuffisante → relief standard.")
    return res
