# -*- coding: utf-8 -*-
#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================
#  O4_Avance_Utils.py  —  ORTHO4XP V3  —  Fenêtre « Avancé » (JOSM)
# ----------------------------------------------------------------------------
#  Module AUTONOME. Aucun fichier du pipeline n'est importé ni modifié.
#  Le GUI ne reçoit qu'un import non bloquant, un bouton et une méthode.
#
#  ÉTAPE 1 (cette livraison) :
#     Bouton « Données OSM de la tuile » — pleinement fonctionnel.
#       * liste les fichiers *.osm.bz2 du dossier OSM_data de la tuile active
#       * SAUVEGARDE HORODATÉE SYSTÉMATIQUE avant toute ouverture
#       * ouverture dans JOSM via le Remote Control (port 8111), avec repli
#         sur le lancement de l'application si le port ne répond pas
#       * rappel : relancer l'étape 1 après fermeture de JOSM
#
#  Les trois autres boutons (Provider & Emprises / Nivellement & Terrain /
#  Aéroport & Runways) sont présents et signalés « à venir » : ils créeront
#  des modèles pré-tagués dans Extents/ et Patches/. Ils seront activés aux
#  étapes suivantes, une fois tranchée la contrainte de nommage OACI.
#
#  RAPPELS DE CONCEPTION (issus de l'analyse validée) :
#     - Extents/            → quel provider s'applique où      (.ext + _osm.bz2)
#     - Patches/+xx-yyy/    → altitude du mesh                 (.patch.osm)
#     - OSM_data/+xx-yyy/   → géométrie source téléchargée     (*.osm.bz2)
#       C'est le SEUL des quatre mécanismes où le fichier existe déjà :
#       on ouvre l'existant, on ne crée jamais de modèle, et on sauvegarde
#       avant, car ce dossier est un cache qu'Ortho4XP peut réécrire.
# ============================================================================

import os
import re
import sys
import shutil
import platform
import threading
import subprocess

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, N, S, E, W, RIDGE, END

# ── Traduction : non bloquante ──────────────────────────────────────────────
#  Si O4_Lang est absent ou si la clé n'existe pas encore, le texte français
#  écrit dans le code est renvoyé tel quel. Les clés seront ajoutées aux
#  fichiers O4_Lang_FR.py / O4_Lang_EN.py en une seule passe en fin de
#  chantier, afin de ne pas réécrire deux fichiers de 670 lignes à chaque
#  étape.
try:
    from O4_Lang import tr as _tr_real
except Exception:
    _tr_real = None


def tr(s):
    if _tr_real is None:
        return s
    try:
        out = _tr_real(s)
        return out if out else s
    except Exception:
        return s


# ── Journalisation : non bloquante ──────────────────────────────────────────
try:
    import O4_UI_Utils as UI
except Exception:
    UI = None


def _log(msg):
    try:
        if UI is not None:
            UI.vprint(1, "[Avance] " + str(msg))
        else:
            print("[Avance] " + str(msg))
    except Exception:
        pass


# ── Noms de fichiers : non bloquant ─────────────────────────────────────────
try:
    import O4_File_Names as FNAMES
except Exception:
    FNAMES = None


# ============================================================================
#  Utilitaires de chemins
# ============================================================================

_RE_TUILE = re.compile(r"^([+-]\d{2})([+-]\d{3})$")


def _tile_de_fichier(filepath):
    """Tuile à laquelle appartient RÉELLEMENT un fichier de données OSM.

    Déduite du chemin — dossier « +46-003 », ou nom de fichier
    « +46-003_water_osm.bz2 » — et jamais des champs de la fenêtre
    principale.

    POURQUOI : la fenêtre suit la tuile active avec quelques secondes
    de décalage. Pendant ce laps de temps, les boutons de couches
    montrent encore l'ancienne tuile alors que les champs affichent
    déjà la nouvelle. Se fier aux champs rangerait la copie de sécurité
    d'un fichier de +46-003 sous +47+008 — et la protection deviendrait
    introuvable le jour où elle sert. Le chemin, lui, ne ment jamais.

    Retourne (lat, lon), ou (None, None) si le nom ne suit pas la
    convention Ortho4XP.
    """
    candidats = [os.path.basename(os.path.dirname(filepath))]
    base = os.path.basename(filepath)
    candidats.append(base[:7])
    for c in candidats:
        m = _RE_TUILE.match(c)
        if m:
            try:
                return int(m.group(1)), int(m.group(2))
            except ValueError:
                pass
    return None, None


def _short_latlon(lat, lon):
    """Nom de tuile Ortho4XP, ex. (46, -3) -> '+46-003'."""
    return "{:+03d}{:+04d}".format(int(lat), int(lon))


def _ortho4xp_dir():
    """Racine Ortho4XP, déduite de FNAMES si possible, sinon du module."""
    if FNAMES is not None:
        d = getattr(FNAMES, "Ortho4XP_dir", None)
        if d and os.path.isdir(d):
            return d
    # Repli : le module vit dans src/, la racine est le dossier parent.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _round10(v):
    """Arrondi vers le bas au multiple de 10 (46 -> 40, -3 -> -10)."""
    import math
    return int(math.floor(int(v) / 10.0) * 10)


def _osm_data_dir(lat, lon):
    """Dossier OSM_data de la tuile.

    Structure réelle vérifiée sur l'installation de Roland (capture Finder) :

        Ortho4XP/OSM_data/+40-010/+46-003/+46-003_water.osm.bz2

    Il y a donc un niveau intermédiaire de 10 degrés (+40-010) entre
    OSM_data et le dossier de tuile. On passe par FNAMES.osm_dir quand il
    est disponible ; le repli reconstruit la même structure à deux niveaux.
    """
    if FNAMES is not None and hasattr(FNAMES, "osm_dir"):
        try:
            d = FNAMES.osm_dir(int(lat), int(lon))
            if d:
                return d
        except Exception:
            pass
    base = os.path.join(_ortho4xp_dir(), "OSM_data")
    tile = _short_latlon(lat, lon)
    parent = _short_latlon(_round10(lat), _round10(lon))
    d2 = os.path.join(base, parent, tile)
    if os.path.isdir(d2):
        return d2
    # Tolérance : certaines installations anciennes sont à plat.
    d1 = os.path.join(base, tile)
    if os.path.isdir(d1):
        return d1
    return d2


_SAUV_DIR = "Sauvegarde fichier source"


def _original_dir(lat, lon):
    """Dossier des copies de sécurité des données OSM.

        OSM_data/Sauvegarde fichier source/+40-010/+46-003/

    POURQUOI PAS DANS LE DOSSIER DE LA TUILE : le nettoyage du GUI, case
    « OSM data » cochée, exécute un shutil.rmtree sur le dossier de la
    tuile. Un sous-dossier placé à l'intérieur serait emporté avec le
    reste, et le filet de sécurité disparaîtrait en même temps que ce
    qu'il protège. Placé un cran au-dessus, il survit au nettoyage tout
    en restant immédiatement visible à côté des tuiles.
    """
    return os.path.join(_ortho4xp_dir(), "OSM_data", _SAUV_DIR,
                        _short_latlon(_round10(lat), _round10(lon)),
                        _short_latlon(lat, lon))


def _original_path(filepath, lat, lon):
    """Chemin de la copie de sécurité d'un fichier de données OSM.

        +46-003_water.osm.bz2
          -> …/Sauvegarde fichier source/+40-010/+46-003/
             +46-003_water.osm.bz2.original
    """
    return os.path.join(_original_dir(lat, lon),
                        os.path.basename(filepath) + ".original")


def _modified_path(filepath, lat, lon):
    """Chemin de la copie de MES modifications.

        …/Sauvegarde fichier source/+40-010/+46-003/
           +46-003_water.osm.bz2.modifie

    C'est la copie la plus précieuse des deux : l'original est
    régénérable — Ortho4XP le retélécharge à l'étape 1 s'il est absent —
    alors que le travail fait dans JOSM ne se régénère pas. Elle survit
    donc, elle aussi, à la suppression de la tuile, et peut être
    réappliquée sur une tuile reconstruite de zéro.
    """
    return os.path.join(_original_dir(lat, lon),
                        os.path.basename(filepath) + ".modifie")


def _snapshot_modified(filepath, lat, lon):
    """Enregistre l'état courant du fichier comme « mes modifications ».

    Contrairement à l'original, cette copie est REMPLACÉE à chaque fois :
    on veut toujours le dernier état du travail, pas un historique.
    Retourne le chemin, ou None si le fichier est encore identique à
    l'original (rien à sauvegarder).
    """
    def _identique(a, b):
        try:
            if not os.path.isfile(a):
                return False
            if os.path.getsize(a) != os.path.getsize(b):
                return False
            return open(a, "rb").read() == open(b, "rb").read()
        except Exception:
            return False

    # Sans original de référence, la couche n'a jamais été ouverte ici :
    # rien ne prouve qu'elle a été modifiée, et l'enregistrer comme
    # « mes modifications » serait faux. On ne fait rien.
    orig = _original_path(filepath, lat, lon)
    if not os.path.isfile(orig):
        return None
    # Rien à sauvegarder non plus si le fichier est encore tel
    # qu'Ortho4XP l'avait téléchargé…
    if _identique(orig, filepath):
        return None
    dest = _modified_path(filepath, lat, lon)
    # …ni s'il est déjà identique au dernier instantané : inutile de
    # réécrire le même contenu à chaque fermeture de la fenêtre.
    if _identique(dest, filepath):
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(filepath, dest)
    return dest


def _ensure_original(filepath, lat, lon):
    """Crée la copie de sécurité si elle n'existe pas déjà.

    Créée UNE SEULE FOIS : la toute première version saine est préservée,
    même après de nombreuses séances d'édition. Retourne (créée, chemin).
    """
    dest = _original_path(filepath, lat, lon)
    if os.path.exists(dest):
        return (False, dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(filepath, dest)
    return (True, dest)


# ============================================================================
#  Détection et pilotage de JOSM
# ============================================================================

_JOSM_PORT = 8111
_JOSM_HOST = "127.0.0.1"


def _josm_remote_alive(timeout=1.5):
    """Vrai si une instance de JOSM répond sur le Remote Control."""
    try:
        import urllib.request
        url = "http://{}:{}/version".format(_JOSM_HOST, _JOSM_PORT)
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _josm_remote_open(filepath, timeout=8.0):
    """Demande à JOSM d'ouvrir un fichier via le Remote Control."""
    try:
        import urllib.request
        import urllib.parse
        url = "http://{}:{}/open_file?filename={}".format(
            _JOSM_HOST, _JOSM_PORT,
            urllib.parse.quote(os.path.abspath(filepath)))
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception as e:
        _log("Remote Control : " + str(e))
        return False


_CFG_KEY = "josm_app"


def _cfg_path():
    return os.path.join(_ortho4xp_dir(), "Ortho4XP.cfg")


def _read_cfg(key=_CFG_KEY):
    """Lit une clé d'Ortho4XP.cfg. Même format que patch_editor_app."""
    try:
        c = _cfg_path()
        if not os.path.isfile(c):
            return ""
        with open(c, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def _save_cfg(value, key=_CFG_KEY):
    """Écrit une clé dans Ortho4XP.cfg sans toucher aux autres lignes."""
    c = _cfg_path()
    lines = []
    found = False
    if os.path.isfile(c):
        with open(c, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(key + "="):
                    lines.append("{}={}\n".format(key, value))
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append("{}={}\n".format(key, value))
    with open(c, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _find_josm():
    """Retourne un chemin plausible vers JOSM, ou None.

    Aucune commande n'est demandée à l'utilisateur : la recherche est faite
    par le programme, aux emplacements standards de chaque système.
    """
    # 1) Application choisie par l'utilisateur, mémorisée dans Ortho4XP.cfg
    chosen = _read_cfg()
    if chosen and os.path.exists(chosen):
        return chosen

    syst = platform.system()
    candidates = []
    if syst == "Darwin":
        candidates = ["/Applications/JOSM.app",
                      os.path.expanduser("~/Applications/JOSM.app")]
    elif syst == "Windows":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                     os.environ.get("LOCALAPPDATA", "")):
            if base:
                candidates.append(os.path.join(base, "JOSM", "josm.exe"))
                candidates.append(os.path.join(base, "JOSM", "JOSM.exe"))
    else:
        w = shutil.which("josm")
        if w:
            candidates.append(w)
        candidates += ["/usr/bin/josm", "/usr/local/bin/josm",
                       "/snap/bin/josm"]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    # Repli universel : un josm-tested.jar posé dans la racine Ortho4XP.
    jar = os.path.join(_ortho4xp_dir(), "josm-tested.jar")
    if os.path.isfile(jar):
        return jar
    return None


def _macos_binary(app_path):
    """Exécutable réel contenu dans un bundle .app macOS.

    POURQUOI : « open -a JOSM.app fichier.osm.bz2 » passe par
    LaunchServices, qui refuse le fichier avec « aucun gestionnaire adapté
    n'est disponible » parce que JOSM ne déclare pas l'extension .bz2
    parmi ses types de documents. Le fichier existe pourtant. En appelant
    directement le binaire du bundle, on contourne LaunchServices et JOSM
    reçoit son argument normalement.
    """
    mac = os.path.join(app_path, "Contents", "MacOS")
    if not os.path.isdir(mac):
        return None
    noms = sorted(os.listdir(mac))
    for n in noms:
        if n.lower().startswith("josm"):
            c = os.path.join(mac, n)
            if os.access(c, os.X_OK):
                return c
    for n in noms:
        c = os.path.join(mac, n)
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def _launch_josm(josm_path, filepath=None):
    """Lance JOSM, avec le fichier en argument si fourni.

    Retourne (ok, message).
    """
    try:
        args = None
        if josm_path.endswith(".app"):
            b = _macos_binary(josm_path)
            if b:
                args = [b]
            else:
                # Repli : ouverture du bundle sans document. Le fichier
                # sera transmis ensuite par le Remote Control.
                if filepath:
                    subprocess.Popen(["open", "-a", josm_path])
                    return (True, "")
                subprocess.Popen(["open", "-a", josm_path])
                return (True, "")
        elif josm_path.endswith(".jar"):
            java = shutil.which("java")
            if not java:
                return (False, tr("Java est introuvable : JOSM ne peut pas "
                                  "être lancé depuis le fichier .jar."))
            args = [java, "-jar", josm_path]
        else:
            args = [josm_path]
        if filepath:
            args.append(os.path.abspath(filepath))
        subprocess.Popen(args)
        return (True, "")
    except Exception as e:
        return (False, str(e))


def _wait_remote(timeout=90.0, pas=2.0):
    """Attend que le Remote Control de JOSM réponde, après lancement."""
    import time
    fin = time.time() + timeout
    while time.time() < fin:
        if _josm_remote_alive(timeout=1.0):
            return True
        time.sleep(pas)
    return False


_JOSM_HELP = (
    "JOSM n'a pas été trouvé sur cet ordinateur.\n\n"
    "JOSM est l'éditeur OpenStreetMap officiel, gratuit et multiplateforme.\n"
    "Il se télécharge sur le site officiel : josm.openstreetmap.de\n\n"
    "Installation :\n"
    "  • macOS : télécharger la version macOS et glisser JOSM dans le "
    "dossier Applications.\n"
    "  • Windows : télécharger l'installeur et l'exécuter.\n"
    "  • Linux : installer le paquet josm de la distribution.\n\n"
    "Une fois JOSM installé, activez le Remote Control :\n"
    "  Menu Édition → Préférences → Remote Control → cocher "
    "« Activer le Remote Control ».\n"
    "Ortho4XP pourra alors ouvrir les fichiers directement dans la fenêtre "
    "JOSM déjà lancée, sans en relancer une seconde."
)


# ============================================================================
#  Libellés des couches OSM d'une tuile
# ============================================================================
#  Fichiers réellement produits par Ortho4XP à l'étape 1, vérifiés sur la
#  tuile +46-003 :
#     +46-003_water_osm.bz2        lacs, étangs, rivières  (le plus gros)
#     +46-003_coastline_osm.bz2    trait de côte
#     +46-003_airports_osm.bz2     emprises aéroportuaires
#     +46-003_big_roads_osm.bz2    routes principales
#     +46-003_small_roads_osm.bz2  routes secondaires
#  Le générateur annoncé dans le XML est « Ortho4XP » ; après édition, JOSM
#  réécrit le fichier avec son propre générateur, ce qui est sans effet sur
#  la relecture par Ortho4XP.

_LAYER_LABELS = (
    ("_water",       "bords de lac, étangs, rivières"),
    ("_coastline",   "trait de côte"),
    ("_airports",    "emprises aéroportuaires"),
    ("_big_roads",   "routes principales"),
    ("_small_roads", "routes secondaires"),
    ("_buildings",   "bâtiments"),
    ("_patches",     "patches"),
)


def _layer_label(fname):
    low = fname.lower()
    for key, lab in _LAYER_LABELS:
        if key in low:
            return tr(lab)
    return ""


# ============================================================================
#  Consigne d'enregistrement, adaptée au système
# ============================================================================
#  JOSM ouvre le fichier depuis son emplacement réel et retient ce chemin.
#  « Enregistrer » réécrit donc directement au bon endroit, sans fenêtre ni
#  navigation. Le seul vrai piège est « Enregistrer sous », qui demande un
#  dossier — et c'est là que les fichiers finissent sur le Bureau.

def _raccourci_enregistrer():
    """Raccourci clavier d'enregistrement du système courant."""
    if sys.platform == "darwin":
        return "Cmd+S"
    return "Ctrl+S"


def _consigne_enregistrement():
    """Message d'enregistrement, avec le raccourci du système courant."""
    if sys.platform == "darwin":
        syst = tr("sur macOS")
    elif sys.platform.startswith("win"):
        syst = tr("sur Windows")
    else:
        syst = tr("sur Linux")
    return (tr("POUR ENREGISTRER dans JOSM : ") + _raccourci_enregistrer()
            + " (" + syst + ")"
            + tr(", ou menu Fichier puis Enregistrer.\n\n"
                 "Le fichier repart directement au bon endroit : JOSM a "
                 "retenu son emplacement, il n'y a aucun dossier à choisir."
                 "\n\nÉvitez « Enregistrer sous » et « Enregistrer la "
                 "session » : ce sont les deux commandes qui font atterrir "
                 "le fichier au mauvais endroit. Raccourcis équivalents : "
                 "Cmd+S sur macOS, Ctrl+S sur Windows et Linux."))


# ============================================================================
#  Fabrication des modèles JOSM pré-tagués
# ============================================================================
#  Les échecs relevés sur les forums ne viennent pas de JOSM mais des tags
#  manquants ou faux. Les modèles ci-dessous sont donc livrés déjà tagués :
#  l'utilisateur n'a plus qu'à déplacer les nœuds du rectangle.
#
#  Format vérifié sur un extent réel (OrthoLittoV3) et sur les patches du
#  dépôt Ortho4XP :
#     - nœuds à identifiants NÉGATIFS, action='modify'
#     - une way FERMÉE (le premier nœud est répété en dernier)
#     - extent  : way référencée par une relation, rôle 'outer', admin_level
#     - patch   : tags altitude / altitude_low + altitude_high / profile

# upload='never' est ESSENTIEL. Sans cet attribut, JOSM considère la
# couche comme publiable et propose « Envoyer » coché par défaut dans la
# boîte de fermeture. Or « Envoyer » ne sauvegarde pas sur le disque : il
# TÉLÉVERSE vers les serveurs publics d'OpenStreetMap. Un rectangle tagué
# admin_level deviendrait une fausse limite administrative visible par
# tous, avec un risque de blocage du compte OSM. Avec upload='never',
# JOSM désactive purement et simplement l'envoi pour cette couche et ne
# propose plus que « Enregistrer ».
_OSM_HEAD = ("<?xml version='1.0' encoding='UTF-8'?>\n"
             "<osm version='0.6' upload='never' generator='Ortho4XP'>\n")
_OSM_FOOT = "</osm>\n"


def _rectangle(lat, lon, marge=0.25):
    """Rectangle centré dans la tuile (lat, lon), en degrés.

    marge=0.25 donne un rectangle occupant la moitié centrale de la tuile :
    assez grand pour être visible dans JOSM, assez petit pour ne pas donner
    l'illusion d'une emprise déjà correcte.
    """
    la0, la1 = lat + marge, lat + 1 - marge
    lo0, lo1 = lon + marge, lon + 1 - marge
    return [(la0, lo0), (la0, lo1), (la1, lo1), (la1, lo0)]


def _osm_polygon(points, tags, relation_tags=None):
    """Construit un document OSM : nœuds + way fermée (+ relation)."""
    out = [_OSM_HEAD]
    nid = -1
    ids = []
    for la, lo in points:
        out.append("  <node id='{}' action='modify' visible='true' "
                   "lat='{:.8f}' lon='{:.8f}' />\n".format(nid, la, lo))
        ids.append(nid)
        nid -= 1
    wid = -1000
    out.append("  <way id='{}' action='modify' visible='true'>\n".format(wid))
    for i in ids + [ids[0]]:
        out.append("    <nd ref='{}' />\n".format(i))
    for k, v in tags:
        out.append("    <tag k='{}' v='{}' />\n".format(k, v))
    out.append("  </way>\n")
    if relation_tags is not None:
        out.append("  <relation id='-2000' action='modify' visible='true'>\n")
        out.append("    <member type='way' ref='{}' role='outer' />\n".format(wid))
        for k, v in relation_tags:
            out.append("    <tag k='{}' v='{}' />\n".format(k, v))
        out.append("  </relation>\n")
    out.append(_OSM_FOOT)
    return "".join(out)


def _read_osm_bounds(path):
    """Enveloppe (lon_min, lat_min, lon_max, lat_max) des nœuds d'un .osm.

    Sert à recalculer mask_bounds APRÈS édition dans JOSM. Sans ce
    recalcul, une emprise agrandie dans JOSM mais laissée avec l'ancien
    mask_bounds provoque le fameux « Could not test coverage of… ».
    Accepte le fichier compressé (.bz2) comme le fichier clair.
    """
    import re
    if path.lower().endswith(".bz2"):
        import bz2
        data = bz2.open(path, "rt", encoding="utf-8", errors="replace").read()
    else:
        data = open(path, "r", encoding="utf-8", errors="replace").read()
    lats, lons = [], []
    # ATTENTION : un fichier JOSM issu d'un téléchargement OSM contient des
    # milliers de nœuds action='delete', vestiges de la donnée effacée par
    # l'auteur (vérifié sur OrthoLittoV3 : 18 000 lignes de rebut couvrant
    # toute la France). Les inclure fausserait complètement l'emprise.
    # On ne retient donc QUE les nœuds réellement conservés.
    for m in re.finditer(r"<node\b[^>]*/?>", data):
        bal = m.group(0)
        if "action='delete'" in bal or 'action="delete"' in bal:
            continue
        a = re.search(r"lat=['\"]([-0-9.]+)['\"]", bal)
        b = re.search(r"lon=['\"]([-0-9.]+)['\"]", bal)
        if not (a and b):
            continue
        try:
            lats.append(float(a.group(1)))
            lons.append(float(b.group(1)))
        except Exception:
            pass
    if not lats:
        return None
    # Légère marge extérieure : sur l'extent réel OrthoLittoV3, l'auteur
    # avait lui-même élargi son mask_bounds d'environ 0,03° par rapport au
    # tracé. Une enveloppe calculée au plus juste risque de rogner la
    # couverture en bordure — d'où la même marge ici.
    m = 0.03
    return (min(lons) - m, min(lats) - m, max(lons) + m, max(lats) + m)


def _write_ext(ext_path, bounds):
    """Écrit le fichier .ext qui accompagne l'emprise."""
    with open(ext_path, "w", encoding="utf-8") as f:
        f.write("# Créé par Ortho4XP — fenêtre Avancé (JOSM)\n")
        f.write("mask_bounds={:.6f},{:.6f},{:.6f},{:.6f}\n".format(*bounds))


def _memes_octets(a, b):
    """Vrai si les deux fichiers ont exactement le même contenu."""
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()
    except Exception:
        return False


def _search_dirs():
    """Endroits où un utilisateur enregistre un fichier par mégarde.

    Les plaintes récurrentes sur les forums ne portent pas sur JOSM mais
    sur le rangement : le fichier finit sur le Bureau ou dans
    Téléchargements, Ortho4XP ne le voit jamais, et l'utilisateur conclut
    que « ça ne marche pas ». On va donc le chercher à sa place.
    """
    h = os.path.expanduser("~")
    d = [os.path.join(h, x) for x in
         ("Desktop", "Bureau", "Downloads", "Téléchargements",
          "Documents", "Documenti", "Escritorio", "Descargas")]
    d.append(h)
    d.append(_ortho4xp_dir())
    return [x for x in d if os.path.isdir(x)]


def _scan_stray_osm(extents_dir, profondeur=2):
    """Recense les .osm d'emprise égarés, SANS rien modifier.

    Un fichier n'est retenu que si son nom correspond à une emprise
    connue — un .ext ou un _osm.bz2 déjà présent dans Extents/ — ou s'il
    porte le préfixe CUSTOM_ des modèles créés par cette fenêtre. On ne
    regarde donc jamais un .osm sans rapport avec Ortho4XP.

    Retourne une liste de (source, destination, action, raison) où action
    vaut « deplacer » ou « supprimer ». Rien n'est appliqué ici : c'est
    l'utilisateur qui décide, dans la fenêtre de confirmation.
    """
    connus = set()
    try:
        for f in os.listdir(extents_dir):
            if f.lower().endswith(".ext"):
                connus.add(f[:-len(".ext")])
            elif f.endswith("_osm.bz2"):
                connus.add(f[:-len("_osm.bz2")])
    except Exception:
        pass

    trouves = []
    vus = set()
    for base in _search_dirs():
        for racine, dossiers, fichiers in os.walk(base):
            if racine[len(base):].count(os.sep) >= profondeur:
                dossiers[:] = []
                continue
            dossiers[:] = [x for x in dossiers if not x.startswith(".")]
            if os.path.abspath(racine) == os.path.abspath(extents_dir):
                continue
            for f in fichiers:
                if not f.lower().endswith(".osm"):
                    continue
                nom = f[:-len(".osm")]
                if nom not in connus and not nom.startswith("CUSTOM_"):
                    continue
                src = os.path.join(racine, f)
                if src in vus:
                    continue
                vus.add(src)
                dst = os.path.join(extents_dir, f)
                try:
                    if not os.path.isfile(dst):
                        trouves.append((src, dst, "deplacer",
                                        tr("absent de Extents/")))
                    elif _memes_octets(src, dst):
                        trouves.append((src, dst, "supprimer",
                                        tr("identique à celui de Extents/")))
                    elif os.path.getmtime(src) > os.path.getmtime(dst):
                        trouves.append((src, dst, "deplacer",
                                        tr("plus récent que celui de "
                                           "Extents/")))
                    else:
                        trouves.append((src, dst, "supprimer",
                                        tr("plus ancien que celui de "
                                           "Extents/")))
                except Exception:
                    pass
    return trouves


def _apply_stray(trouves):
    """Applique les actions décidées. Aucun doublon ne doit subsister."""
    deplaces, supprimes, erreurs = [], [], []
    for src, dst, action, _raison in trouves:
        try:
            if action == "deplacer":
                if os.path.isfile(dst):
                    os.remove(dst)
                shutil.move(src, dst)
                deplaces.append(os.path.basename(dst))
            else:
                os.remove(src)
                supprimes.append(os.path.basename(src))
        except Exception as e:
            erreurs.append("{} : {}".format(os.path.basename(src), e))
    return deplaces, supprimes, erreurs


def _publier_emprise(extents_dir, nom):
    """Écrit les deux fichiers attendus par Ortho4XP à partir du .osm.

        NOM.osm  (édité dans JOSM)
           ->  NOM_osm.bz2   le dessin, compressé, au nom exigé
           ->  NOM.ext       les limites réelles du dessin

    Le .ext est le point critique : si le dessin est agrandi dans JOSM
    mais que les limites restent celles du rectangle d'origine, Ortho4XP
    cherche l'imagerie hors des limites déclarées et échoue avec
    « Could not test coverage of… ».

    Retourne les limites écrites, ou None si rien n'était à faire.
    """
    travail = os.path.join(extents_dir, nom + ".osm")
    publie = os.path.join(extents_dir, nom + "_osm.bz2")
    ext = os.path.join(extents_dir, nom + ".ext")
    if not os.path.isfile(travail):
        return None
    b = _read_osm_bounds(travail)
    if not b:
        return None
    import bz2
    with open(travail, "rb") as fin:
        data = fin.read()
    with bz2.open(publie, "wb") as fout:
        fout.write(data)
    _write_ext(ext, b)
    return b


def _a_publier(extents_dir, stable=3.0):
    """Noms dont le .osm est plus récent que sa publication.

    « stable » évite de publier un fichier en cours d'écriture par JOSM :
    on attend qu'il n'ait plus bougé depuis quelques secondes.
    """
    import time
    out = []
    try:
        fichiers = os.listdir(extents_dir)
    except Exception:
        return out
    maintenant = time.time()
    for f in fichiers:
        if not f.lower().endswith(".osm"):
            continue
        nom = f[:-len(".osm")]
        travail = os.path.join(extents_dir, f)
        publie = os.path.join(extents_dir, nom + "_osm.bz2")
        try:
            # Fichier encore en cours d'écriture par JOSM : on attend.
            if maintenant - os.path.getmtime(travail) < stable:
                continue
            # Comparaison par CONTENU et non par date : les dates
            # d'écriture peuvent se croiser (copie, restauration, horloge
            # système), et une emprise non republiée passerait inaperçue.
            if os.path.isfile(publie):
                import bz2
                with open(travail, "rb") as f1:
                    a = f1.read()
                with bz2.open(publie, "rb") as f2:
                    b = f2.read()
                if a == b:
                    continue
        except Exception:
            continue
        out.append(nom)
    return out


def _airports_of_tile(osm_dir, tile):
    """Codes OACI présents dans le fichier _airports de la tuile.

    Vérifié sur +46-003 : le fichier contient bien des tags icao
    (LFEY, LFFO) accompagnés de tags name. Retourne [(code, nom), …].
    """
    import re
    import bz2
    path = None
    try:
        for f in os.listdir(osm_dir):
            if "_airports" in f and f.lower().endswith("osm.bz2"):
                path = os.path.join(osm_dir, f)
                break
    except Exception:
        return []
    if not path:
        return []
    try:
        data = bz2.open(path, "rt", encoding="utf-8", errors="replace").read()
    except Exception:
        return []
    # On associe chaque icao au name le plus proche dans le même bloc.
    out = {}
    for bloc in re.split(r"</(?:way|node|relation)>", data):
        icao = re.search(
            r"k=['\"]icao['\"]\s+v=(['\"])([A-Za-z0-9]{4})\1", bloc)
        if not icao:
            continue
        # Le nom contient souvent une apostrophe (« Aérodrome de l'Île-d'Yeu »)
        # alors que l'attribut est délimité par des guillemets doubles. Le
        # délimiteur est donc capturé, et la fin de valeur cherchée sur CE
        # délimiteur uniquement.
        nom = re.search(r"k=['\"]name['\"]\s+v=(['\"])(.*?)\1", bloc)
        libelle = nom.group(2) if nom else ""
        for ent, car in (("&apos;", "'"), ("&quot;", '"'), ("&amp;", "&"),
                         ("&lt;", "<"), ("&gt;", ">")):
            libelle = libelle.replace(ent, car)
        out[icao.group(2).upper()] = libelle
    return sorted(out.items())


# ============================================================================
#  Thème — identique aux autres fenêtres du projet
# ============================================================================
#  Mêmes clés et mêmes valeurs de repli que O4_Correction_Utils, afin que la
#  fenêtre « Avancé » ne détonne pas : fond sombre, texte vert.

def _theme():
    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
        BG      = _t.get("patch_bg",      _t.get("bg",           "#0a1a0a"))
        FG      = _t.get("patch_fg",      _t.get("fg",           "#00cc44"))
        FG2     = _t.get("patch_fg2",     _t.get("fg_secondary", "#88ffaa"))
        PREV_BG = _t.get("patch_prev_bg", _t.get("canvas_bg",    "#050f05"))
    except Exception:
        BG, FG, FG2, PREV_BG = "#0a1a0a", "#00cc44", "#88ffaa", "#050f05"
    return BG, FG, FG2, PREV_BG


# ============================================================================
#  Fenêtre « Avancé »
# ============================================================================

class AvanceWindow(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title(tr("Avancé — Couches JOSM"))
        self.BG, self.FG, self.FG2, self.PREV_BG = _theme()
        self._osm_buttons = []
        # Couches ouvertes pendant la séance, toutes tuiles confondues.
        self._couches_ouvertes = set()
        self.configure(bg=self.BG)
        # macOS : sans transient, la fenêtre repasse derrière le GUI après
        # chaque boîte de dialogue et paraît s'être fermée.
        try:
            self.transient(parent)
        except Exception:
            pass
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── En-tête : tuile active ─────────────────────────────────────
        head = tk.Frame(self, border=2, relief=RIDGE, bg=self.BG)
        head.grid(row=0, column=0, sticky=N+S+E+W, padx=6, pady=6)
        head.columnconfigure(1, weight=1)

        tk.Label(head, text=tr("Tuile active :"), bg=self.BG, fg=self.FG,
                 font=("TkFixedFont", 12, "bold")).grid(
            row=0, column=0, padx=6, pady=6, sticky=W)
        self._lbl_tile = tk.Label(head, text="--", bg=self.BG, fg=self.FG2,
                                  font=("TkFixedFont", 12))
        self._lbl_tile.grid(row=0, column=1, padx=6, pady=6, sticky=W)

        tk.Label(head, text=tr("JOSM :"), bg=self.BG, fg=self.FG,
                 font=("TkFixedFont", 12, "bold")).grid(
            row=1, column=0, padx=6, pady=(0, 6), sticky=W)
        self._lbl_josm = tk.Label(head, text=tr("recherche…"), bg=self.BG,
                                  fg=self.FG2, font=("TkFixedFont", 11))
        self._lbl_josm.grid(row=1, column=1, padx=6, pady=(0, 6), sticky=W)

        # ── Les quatre mécanismes ──────────────────────────────────────
        body = tk.Frame(self, bg=self.BG)
        body.grid(row=1, column=0, sticky=N+S+E+W, padx=6)
        for c in range(2):
            body.columnconfigure(c, weight=1)

        self._make_card(
            body, 0, 0,
            tr("Provider & Emprises"),
            tr("Extents/  —  définit où s'applique tel ou tel provider,\n"
               "en bord de mer, de lac, ou en pleine terre.\n"
               "Produit une paire .ext + _osm.bz2."),
            self._btn_extent)

        self._make_card(
            body, 0, 1,
            tr("Nivellement & Terrain"),
            tr("Patches/  —  altitude du mesh : aplanir un plateau,\n"
               "creuser une vallée, corriger une bosse du DEM.\n"
               "Produit un fichier .patch.osm."),
            self._btn_terrain)

        self._make_card(
            body, 1, 0,
            tr("Aéroport & Runways"),
            tr("Patches/  —  profil de piste et abords.\n"
               "Le nom du fichier doit commencer par le code OACI,\n"
               "faute de quoi le patch reste sans effet."),
            self._btn_airport)

        self._card_osm = self._make_card(
            body, 1, 1,
            tr("Données OSM de la tuile"),
            tr("OSM_data/  —  bords de lac, trait de côte, aéroports.\n"
               "On ouvre le fichier existant ; une copie est rangée dans\n"
               "« Sauvegarde fichier source » pour revenir en arrière."),
            None, bouton=False)
        self._fill_osm_buttons()

        # ── Journal ────────────────────────────────────────────────────
        logf = tk.Frame(self, border=2, relief=RIDGE, bg=self.BG)
        logf.grid(row=2, column=0, sticky=N+S+E+W, padx=6, pady=6)
        logf.columnconfigure(0, weight=1)
        logf.rowconfigure(0, weight=1)
        self._txt = tk.Text(logf, height=8, width=88, bd=0,
                            bg=self.PREV_BG, fg=self.FG2,
                            insertbackground=self.FG,
                            highlightthickness=0,
                            font=("Courier", 11))
        self._txt.grid(row=0, column=0, sticky=N+S+E+W)
        sb = tk.Scrollbar(logf, orient="vertical", bg=self.BG,
                          troughcolor=self.BG, command=self._txt.yview)
        sb.grid(row=0, column=1, sticky=N+S)
        self._txt.config(yscrollcommand=sb.set)

        # ── Pied ───────────────────────────────────────────────────────
        foot = tk.Frame(self, bg=self.BG)
        foot.grid(row=3, column=0, sticky=E+W, padx=6, pady=(0, 8))
        ttk.Button(foot, text=tr("Aide JOSM"),
                   command=self._show_help).pack(side="left", padx=4)
        ttk.Button(foot, text=tr("Choisir l'application JOSM"),
                   command=self._choose_josm).pack(side="left", padx=4)
        ttk.Button(foot, text=tr("Sauvegardes…"),
                   command=self._open_backups).pack(side="left", padx=4)
        ttk.Button(foot, text=tr("Fermer"),
                   command=self._on_close).pack(side="right", padx=4)

        self.bind("<Escape>", lambda e: self._on_close())

        # Taille mini = taille naturelle du contenu une fois l'UI construite :
        # les cartes de mécanismes et les boutons de pied de page restent
        # toujours visibles quand on réduit ; l'agrandissement reste libre.
        # Recalculée à chaque changement de tuile : le nombre de boutons de
        # couches varie de 1 à 7 selon les données présentes.
        self._ui_prete = True
        self._verrouiller_minsize()

        self._refresh_tile()
        # Tuile affichée à l'instant : sert de référence à la
        # surveillance, qui ne rafraîchira que si elle change vraiment.
        self._tuile_vue = self._tile_latlon()
        self._tuile_stable = self._tuile_vue
        self._refresh_josm_async()

        # Rangement des fichiers égarés, puis publication automatique.
        try:
            self._propose_stray(os.path.join(_ortho4xp_dir(), "Extents"))
        except Exception as e:
            _log("detection fichiers egares : " + str(e))
        self._watch_id = None
        self._surveiller()

    # ── Construction d'une carte de mécanisme ──────────────────────────
    def _make_card(self, parent, row, col, title, desc, command,
                   bouton=True):
        f = tk.Frame(parent, border=2, relief=RIDGE, bg=self.BG)
        f.grid(row=row, column=col, sticky=N+S+E+W, padx=4, pady=4)
        f.columnconfigure(0, weight=1)
        tk.Label(f, text=title, bg=self.BG, fg=self.FG,
                 font=("TkFixedFont", 12, "bold")).grid(
            row=0, column=0, padx=6, pady=(6, 2), sticky=W)
        tk.Label(f, text=desc, justify="left", bg=self.BG, fg=self.FG2,
                 font=("TkFixedFont", 10)).grid(
            row=1, column=0, padx=6, pady=(0, 4), sticky=W)
        if bouton:
            if command is None:
                b = ttk.Button(f, text=tr("à venir"), state="disabled")
            else:
                b = ttk.Button(f, text=tr("Ouvrir dans JOSM"),
                               command=command)
            b.grid(row=2, column=0, padx=6, pady=(0, 8), sticky=E+W)
        return f

    # ── Un bouton par fichier réellement présent ───────────────────────
    # ── Taille minimale, recalculable ──────────────────────────────────
    def _verrouiller_minsize(self):
        """Réajuste la taille mini au contenu réellement présent.

        Appelée à la construction, puis après chaque reconstruction des
        boutons de couches : selon la tuile, Ortho4XP produit de 3 à 7
        fichiers OSM, donc de 3 à 7 boutons. Une taille mini figée à la
        construction laisserait le dernier bouton coupé sur une tuile
        plus fournie que celle affichée au départ.
        """
        # Pendant la construction, l'interface est incomplète : mesurer
        # à ce moment donnerait une taille mini trop petite.
        if not getattr(self, "_ui_prete", False):
            return
        try:
            self.update_idletasks()
            besoin_l = self.winfo_reqwidth()
            besoin_h = self.winfo_reqheight()
            self.minsize(besoin_l, besoin_h)
            # La fenêtre a pu être réduite par l'utilisateur avant le
            # changement de tuile : on l'agrandit du strict nécessaire,
            # jamais davantage, et on ne la rétrécit jamais.
            actuel_l = self.winfo_width()
            actuel_h = self.winfo_height()
            if actuel_l < besoin_l or actuel_h < besoin_h:
                self.geometry("%dx%d" % (max(besoin_l, actuel_l),
                                         max(besoin_h, actuel_h)))
        except Exception:
            pass

    # ── Un bouton par fichier réellement présent ───────────────────────
    def _fill_osm_buttons(self):
        """Construit un bouton par couche OSM trouvée dans la tuile.

        Les boutons ne sont PAS figés dans le code : selon la tuile et les
        options de build, Ortho4XP produit 3, 5 ou 6 fichiers (il peut y
        avoir buildings, il peut n'y avoir ni côte ni aéroport). Des
        boutons en dur pointeraient alors vers des fichiers inexistants.
        On lit donc le dossier au moment de l'ouverture de la fenêtre.
        """
        f = self._card_osm
        # Nettoyage : la fenêtre peut être reconstruite après changement
        # de tuile, il ne doit jamais rester de bouton d'une tuile
        # précédente.
        for w in self.__dict__.get("_osm_buttons", []):
            try:
                w.destroy()
            except Exception:
                pass
        self._osm_buttons = []

        lat, lon = self._tile_latlon()
        fichiers = []
        d = None
        if lat is not None and lon is not None:
            d = _osm_data_dir(lat, lon)
            if os.path.isdir(d):
                try:
                    fichiers = sorted(x for x in os.listdir(d)
                                      if x.lower().endswith("osm.bz2"))
                except Exception:
                    fichiers = []

        if not fichiers:
            b = ttk.Button(f, text=tr("Aucune donnée — lancer l'étape 1"),
                           command=self._open_osm_data)
            b.grid(row=2, column=0, padx=6, pady=(0, 8), sticky=E+W)
            self._osm_buttons.append(b)
            self._verrouiller_minsize()
            return

        r = 2
        for nom in fichiers:
            lab = _layer_label(nom)
            texte = lab if lab else nom
            chemin = os.path.join(d, nom)
            b = ttk.Button(
                f, text=texte,
                command=lambda c=chemin: self._protect_and_open(c))
            b.grid(row=r, column=0, padx=6, pady=(0, 3), sticky=E+W)
            self._osm_buttons.append(b)
            r += 1
        # Petite marge sous le dernier bouton.
        f.grid_rowconfigure(r - 1, pad=5)
        self._verrouiller_minsize()

    # ── Journal de la fenêtre ──────────────────────────────────────────
    def _say(self, msg):
        try:
            self._txt.insert(END, str(msg) + "\n")
            self._txt.see(END)
        except Exception:
            pass
        _log(msg)

    # ── Tuile active ───────────────────────────────────────────────────
    def _tile_latlon(self):
        """Latitude/longitude de la tuile active, lues sur le GUI parent."""
        lat = lon = None
        for attr, target in (("lat", "lat"), ("lon", "lon")):
            try:
                v = getattr(self.parent, attr).get()
                v = int(str(v).strip() or 0)
            except Exception:
                v = None
            if target == "lat":
                lat = v
            else:
                lon = v
        if lat is None or lon is None:
            # Repli : certains écrans exposent active_lat / active_lon.
            lat = getattr(self.parent, "active_lat", lat)
            lon = getattr(self.parent, "active_lon", lon)
        return lat, lon

    def _refresh_tile(self):
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            self._lbl_tile.config(text=tr("indéterminée"))
            return
        self._lbl_tile.config(text=_short_latlon(lat, lon))
        # Les boutons de couches suivent la tuile active.
        if hasattr(self, "_card_osm"):
            self._fill_osm_buttons()

    # ── État de JOSM (en tâche de fond : ne gèle pas l'interface) ───────
    def _refresh_josm_async(self):
        def _work():
            alive = _josm_remote_alive()
            path = _find_josm()
            if alive:
                txt = tr("en cours d'exécution (Remote Control actif)")
            elif path:
                txt = tr("installé, non lancé") + "  —  " + path
            else:
                # Message d'action plutôt que constat d'échec : JOSM peut
                # être installé ailleurs qu'aux emplacements standards,
                # le sélecteur est alors la bonne réponse.
                txt = tr("non sélectionné — cliquez sur "
                         "« Choisir l'application JOSM »")
            try:
                self.after(0, lambda: self._lbl_josm.config(text=txt))
            except Exception:
                pass
        threading.Thread(target=_work, daemon=True).start()

    def _show_help(self):
        messagebox.showinfo(tr("Aide JOSM"), tr(_JOSM_HELP), parent=self)

    # ══════════════════════════════════════════════════════════════════
    #  Bouton « Données OSM de la tuile »
    # ══════════════════════════════════════════════════════════════════
    def _open_osm_data(self):
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            messagebox.showwarning(
                tr("Données OSM de la tuile"),
                tr("La tuile active n'est pas déterminée : renseignez la "
                   "latitude et la longitude dans la fenêtre principale."),
                parent=self)
            return

        d = _osm_data_dir(lat, lon)
        if not os.path.isdir(d):
            messagebox.showwarning(
                tr("Données OSM de la tuile"),
                tr("Aucun dossier de données OSM pour cette tuile.\n\n"
                   "Lancez d'abord l'étape 1 (Assemble Vector data) : "
                   "Ortho4XP téléchargera les données OpenStreetMap, "
                   "qui pourront ensuite être retouchées ici."),
                parent=self)
            self._say(tr("Dossier absent : ") + d)
            return

        try:
            # Suffixe réel des fichiers Ortho4XP : « +46-003_water_osm.bz2 ».
            # C'est bien « _osm.bz2 » (souligné) et non « .osm.bz2 ».
            # On accepte les deux écritures par prudence.
            files = sorted(f for f in os.listdir(d)
                           if f.lower().endswith("osm.bz2"))
        except Exception as e:
            messagebox.showerror(tr("Données OSM de la tuile"), str(e),
                                 parent=self)
            return

        if not files:
            messagebox.showwarning(
                tr("Données OSM de la tuile"),
                tr("Le dossier existe mais ne contient aucun fichier "
                   ".osm.bz2. Lancez d'abord l'étape 1."),
                parent=self)
            return

        self._choose_file(d, files)

    # ── Sélection du fichier à ouvrir ──────────────────────────────────
    def _choose_file(self, d, files):
        win = tk.Toplevel(self)
        win.title(tr("Quel fichier ouvrir ?"))
        win.configure(bg=self.BG)
        try:
            win.transient(self)
        except Exception:
            pass
        win.columnconfigure(0, weight=1)
        win.rowconfigure(1, weight=1)

        tk.Label(win, justify="left", bg=self.BG, fg=self.FG2,
                 text=tr("Une copie d'origine sera rangée dans « Sauvegarde "
                         "fichier source »\nsi elle n'existe pas encore, puis "
                         "le fichier sera ouvert dans JOSM.\nC'est bien le "
                         "fichier réel que vous modifiez : Ortho4XP le "
                         "reprendra tel quel."),
                 font=("TkFixedFont", 11)).grid(
            row=0, column=0, padx=8, pady=8, sticky=W)

        lb = tk.Listbox(win, width=60, height=min(12, max(4, len(files))),
                        bg=self.PREV_BG, fg=self.FG2, bd=0,
                        selectbackground=self.FG, selectforeground=self.BG,
                        highlightthickness=0,
                        font=("Courier", 11), exportselection=False)
        lb.grid(row=1, column=0, padx=8, sticky=N+S+E+W)
        for f in files:
            try:
                ko = os.path.getsize(os.path.join(d, f)) // 1024
            except Exception:
                ko = 0
            lb.insert(END, "{}   ({} ko)   {}".format(
                f, ko, _layer_label(f)))
        lb.selection_set(0)

        bar = tk.Frame(win, bg=self.BG)
        bar.grid(row=2, column=0, sticky=E+W, padx=8, pady=8)

        def _go(_e=None):
            sel = lb.curselection()
            if not sel:
                return
            fname = files[sel[0]]
            win.destroy()
            self._protect_and_open(os.path.join(d, fname))

        ttk.Button(bar, text=tr("Ouvrir dans JOSM"),
                   command=_go).pack(side="left", padx=4)
        ttk.Button(bar, text=tr("Annuler"),
                   command=win.destroy).pack(side="right", padx=4)
        lb.bind("<Double-Button-1>", _go)
        lb.bind("<Return>", _go)
        win.bind("<Escape>", lambda e: win.destroy())
        lb.focus_set()
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

    # ── Sauvegarde puis ouverture ──────────────────────────────────────
    def _protect_and_open(self, filepath):
        """Protège l'original, puis ouvre le VRAI fichier dans JOSM.

        C'est bien le fichier d'origine qui est ouvert et modifié : la
        version éditée est donc prise en compte par Ortho4XP sans aucune
        intervention dans le pipeline. La copie « .original » sert
        uniquement de retour arrière.

        La tuile est déduite DU FICHIER, pas des champs de la fenêtre
        principale : une copie de sécurité doit toujours être rangée
        sous la tuile à laquelle le fichier appartient réellement.
        """
        lat, lon = _tile_de_fichier(filepath)
        if lat is None or lon is None:
            lat, lon = self._tile_latlon()
        try:
            created, dest = _ensure_original(filepath, lat, lon)
            if created:
                self._say(tr("Copie de sécurité créée : ")
                          + os.path.basename(dest))
            else:
                self._say(tr("Copie de sécurité déjà présente, conservée : ")
                          + os.path.basename(dest))
        except Exception as e:
            if not messagebox.askyesno(
                    tr("Copie de sécurité impossible"),
                    tr("La copie de sécurité n'a pas pu être créée :\n")
                    + str(e)
                    + tr("\n\nOuvrir quand même le fichier dans JOSM ?"),
                    parent=self):
                return

        # Instantané du travail de la séance précédente, avant de rouvrir.
        try:
            m = _snapshot_modified(filepath, lat, lon)
            if m:
                self._say(tr("Modifications sauvegardées : ")
                          + os.path.basename(m))
        except Exception as e:
            _log("snapshot : " + str(e))

        self._say(tr("Ouverture : ") + os.path.basename(filepath))
        # Mémorisé pour la sauvegarde de fermeture : c'est la liste des
        # couches réellement ouvertes pendant la séance, toutes tuiles
        # confondues. Balayer le dossier de la tuile affichée ne suffit
        # pas — on peut avoir changé de tuile depuis.
        try:
            self._couches_ouvertes.add(os.path.abspath(filepath))
        except Exception:
            pass
        self._open_in_josm(filepath)

    # ══════════════════════════════════════════════════════════════════
    #  Choix manuel de l'application JOSM
    # ══════════════════════════════════════════════════════════════════
    def _choose_josm(self):
        """Sélecteur d'application, sur le modèle de celui de GIMP.

        Le chemin est mémorisé dans Ortho4XP.cfg (clé josm_app) et devient
        prioritaire sur la détection automatique.
        """
        from tkinter import filedialog
        if sys.platform == "darwin":
            init_dir = "/Applications"
            ft = [(tr("Applications macOS"), "*.app"),
                  (tr("Tous les fichiers"), "*")]
        elif sys.platform.startswith("win"):
            init_dir = "C:\\Program Files"
            ft = [(tr("Exécutables Windows"), "*.exe"),
                  (tr("Archives Java"), "*.jar"),
                  (tr("Tous les fichiers"), "*")]
        else:
            init_dir = "/usr/bin"
            ft = [(tr("Tous les fichiers"), "*")]
        path = filedialog.askopenfilename(
            parent=self, title=tr("Choisir l'application JOSM"),
            initialdir=init_dir, filetypes=ft)
        if not path:
            return
        try:
            _save_cfg(path)
            self._say(tr("Application JOSM enregistrée : ") + path)
        except Exception as e:
            messagebox.showerror(tr("Choisir l'application JOSM"), str(e),
                                 parent=self)
            return
        self._refresh_josm_async()

    # ══════════════════════════════════════════════════════════════════
    #  Création d'un modèle puis ouverture
    # ══════════════════════════════════════════════════════════════════
    def _create_and_open(self, path, contenu, compresse=False):
        """Écrit le modèle s'il n'existe pas, puis l'ouvre dans JOSM.

        RÈGLE : un fichier déjà présent n'est JAMAIS écrasé — on ouvre
        l'existant. C'est la seule façon de ne pas perdre un travail
        antérieur par une fausse manœuvre.
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.exists(path):
                self._say(tr("Fichier déjà présent, ouverture de "
                             "l'existant : ") + os.path.basename(path))
            else:
                if compresse:
                    import bz2
                    with bz2.open(path, "wt", encoding="utf-8") as f:
                        f.write(contenu)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(contenu)
                self._say(tr("Modèle créé : ") + os.path.basename(path))
        except Exception as e:
            messagebox.showerror(tr("Avancé — Couches JOSM"), str(e),
                                 parent=self)
            return
        self._open_in_josm(path)

    def _ask_name(self, titre, defaut):
        """Saisie de nom, avec valeur pré-remplie.

        Boîte maison plutôt que tkinter.simpledialog : ce dernier n'hérite
        pas du thème du projet et affichait un bouton « Cancel » blanc sur
        blanc, donc illisible.
        """
        res = {"v": None}

        win = tk.Toplevel(self)
        win.title(titre)
        win.configure(bg=self.BG)
        try:
            win.transient(self)
        except Exception:
            pass
        win.resizable(False, False)
        win.columnconfigure(0, weight=1)

        tk.Label(win, text=tr("Nom du fichier :"), bg=self.BG, fg=self.FG,
                 font=("TkFixedFont", 12, "bold")).grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky=W)

        var = tk.StringVar(value=defaut)
        ent = tk.Entry(win, textvariable=var, width=42,
                       bg=self.PREV_BG, fg=self.FG2, bd=0,
                       insertbackground=self.FG, highlightthickness=1,
                       highlightbackground=self.FG, highlightcolor=self.FG,
                       font=("Courier", 12))
        ent.grid(row=1, column=0, padx=12, pady=(0, 10), sticky=E+W)

        bar = tk.Frame(win, bg=self.BG)
        bar.grid(row=2, column=0, padx=12, pady=(0, 12), sticky=E+W)

        def _ok(_e=None):
            v = var.get().strip()
            # Caractères interdits dans un nom de fichier, tous systèmes.
            for c in '\\/:*?"<>|':
                v = v.replace(c, "_")
            res["v"] = v or defaut
            win.destroy()

        def _annuler(_e=None):
            res["v"] = None
            win.destroy()

        ttk.Button(bar, text=tr("Valider"), command=_ok).pack(side="left")
        ttk.Button(bar, text=tr("Annuler"),
                   command=_annuler).pack(side="right")

        win.bind("<Return>", _ok)
        win.bind("<Escape>", _annuler)
        win.protocol("WM_DELETE_WINDOW", _annuler)
        ent.focus_set()
        ent.selection_range(0, END)
        try:
            win.grab_set()
        except Exception:
            pass
        self.wait_window(win)
        return res["v"]

    # ── Bouton « Provider & Emprises » ─────────────────────────────────
    def _btn_extent(self):
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            messagebox.showwarning(
                tr("Provider & Emprises"),
                tr("La tuile active n'est pas déterminée : renseignez la "
                   "latitude et la longitude dans la fenêtre principale."),
                parent=self)
            return
        tile = _short_latlon(lat, lon)
        nom = self._ask_name(tr("Provider & Emprises"),
                             "CUSTOM_{}_zone1".format(tile))
        if not nom:
            return
        d = os.path.join(_ortho4xp_dir(), "Extents")
        # FICHIER DE TRAVAIL en clair, extension .osm.
        # POURQUOI PAS DIRECTEMENT « NOM_osm.bz2 » : JOSM reconnaît
        # « …​.osm.bz2 » (avec un point) mais PAS « …_osm.bz2 » (avec un
        # souligné), et affiche « aucun gestionnaire adapté n'est
        # disponible ». Or Ortho4XP, lui, exige la forme au souligné.
        # Les deux conventions étant incompatibles, on édite un .osm clair
        # et la publication automatique écrit ensuite le _osm.bz2
        # attendu par Ortho4XP, dès que l'enregistrement est détecté.
        osm = os.path.join(d, nom + ".osm")
        ext = os.path.join(d, nom + ".ext")
        pts = _rectangle(lat, lon)
        contenu = _osm_polygon(pts,
                               tags=[],
                               relation_tags=[("admin_level", "6")])
        try:
            os.makedirs(d, exist_ok=True)
            if not os.path.exists(ext):
                _write_ext(ext, (min(p[1] for p in pts),
                                 min(p[0] for p in pts),
                                 max(p[1] for p in pts),
                                 max(p[0] for p in pts)))
                self._say(tr("Fichier .ext créé : ") + os.path.basename(ext))
        except Exception as e:
            messagebox.showerror(tr("Provider & Emprises"), str(e),
                                 parent=self)
            return
        messagebox.showinfo(
            tr("Provider & Emprises"),
            tr("Dans JOSM, utilisez toujours ENREGISTRER, jamais "
               "ENVOYER : « Envoyer » téléverse vers les serveurs publics "
               "d'OpenStreetMap.\n\nUn rectangle pré-tagué va s'ouvrir dans "
               "JOSM : déplacez ses nœuds pour épouser la zone "
               "souhaitée.\n\nDès que vous enregistrerez dans JOSM, "
               "Ortho4XP recevra automatiquement votre tracé : vous n'avez "
               "aucune autre manipulation à faire.\n\n")
            + _consigne_enregistrement(),
            parent=self)
        self._create_and_open(osm, contenu)

    # ── Bouton « Nivellement & Terrain » ───────────────────────────────
    def _btn_terrain(self):
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            messagebox.showwarning(
                tr("Nivellement & Terrain"),
                tr("La tuile active n'est pas déterminée : renseignez la "
                   "latitude et la longitude dans la fenêtre principale."),
                parent=self)
            return
        tile = _short_latlon(lat, lon)
        nom = self._ask_name(tr("Nivellement & Terrain"),
                             "{}_terrain".format(tile))
        if not nom:
            return
        if nom.endswith(".patch.osm"):
            nom = nom[:-len(".patch.osm")]
        path = os.path.join(_ortho4xp_dir(), "Patches", tile,
                            nom + ".patch.osm")
        contenu = _osm_polygon(_rectangle(lat, lon),
                               tags=[("altitude", "0")])
        messagebox.showinfo(
            tr("Nivellement & Terrain"),
            tr("Un rectangle pré-tagué « altitude=0 » va s'ouvrir dans "
               "JOSM.\n\nDéplacez ses nœuds sur la zone à corriger, puis "
               "remplacez la valeur d'altitude par l'altitude voulue, en "
               "MÈTRES.\n\nPour une pente, remplacez le tag altitude par "
               "altitude_low et altitude_high, et ajoutez si besoin "
               "profile=spline.\n\n") + _consigne_enregistrement(),
            parent=self)
        self._create_and_open(path, contenu)

    # ── Bouton « Aéroport & Runways » ──────────────────────────────────
    def _btn_airport(self):
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            messagebox.showwarning(
                tr("Aéroport & Runways"),
                tr("La tuile active n'est pas déterminée : renseignez la "
                   "latitude et la longitude dans la fenêtre principale."),
                parent=self)
            return
        tile = _short_latlon(lat, lon)
        aeros = _airports_of_tile(_osm_data_dir(lat, lon), tile)
        self._choose_airport(lat, lon, tile, aeros)

    def _choose_airport(self, lat, lon, tile, aeros):
        """Liste des aérodromes de la tuile, avec repli ZZZZ.

        Le code OACI n'est pas décoratif : Ortho4XP lit les 4 premiers
        caractères du nom de fichier pour désactiver l'aplanissement
        automatique de l'aéroport correspondant. Un nom fantaisiste rend
        le patch silencieusement sans effet — d'où le choix dans une liste
        plutôt qu'une saisie libre.
        """
        win = tk.Toplevel(self)
        win.title(tr("Aéroport & Runways"))
        win.configure(bg=self.BG)
        try:
            win.transient(self)
        except Exception:
            pass
        win.columnconfigure(0, weight=1)
        win.rowconfigure(1, weight=1)

        if aeros:
            txt = tr("Aérodromes trouvés dans les données OSM de la tuile.\n"
                     "Le nom du fichier reprend le code OACI : c'est lui qui "
                     "désactive l'aplanissement automatique.")
        else:
            txt = tr("Aucun aérodrome n'a été trouvé dans les données OSM de "
                     "la tuile.\nZZZZ est le code officiel des aérodromes "
                     "non répertoriés : le patch s'appliquera normalement, "
                     "mais l'aplanissement automatique ne sera pas désactivé.")
        tk.Label(win, text=txt, justify="left", bg=self.BG, fg=self.FG2,
                 font=("TkFixedFont", 11)).grid(row=0, column=0,
                                                padx=8, pady=8, sticky=W)

        entries = [(c, n) for c, n in aeros]
        entries.append(("ZZZZ", tr("aérodrome non répertorié")))

        lb = tk.Listbox(win, width=56, height=min(10, max(3, len(entries))),
                        bg=self.PREV_BG, fg=self.FG2, bd=0,
                        selectbackground=self.FG, selectforeground=self.BG,
                        highlightthickness=0,
                        font=("Courier", 11), exportselection=False)
        lb.grid(row=1, column=0, padx=8, sticky=N+S+E+W)
        for c, n in entries:
            lb.insert(END, "{}   {}".format(c, n))
        lb.selection_set(0)

        bar = tk.Frame(win, bg=self.BG)
        bar.grid(row=2, column=0, sticky=E+W, padx=8, pady=8)

        def _go(_e=None):
            sel = lb.curselection()
            if not sel:
                return
            code = entries[sel[0]][0]
            win.destroy()
            suffixe = self._ask_name(
                tr("Aéroport & Runways"), code)
            if not suffixe:
                return
            if not suffixe.upper().startswith(code):
                suffixe = code
            if suffixe.endswith(".patch.osm"):
                suffixe = suffixe[:-len(".patch.osm")]
            path = os.path.join(_ortho4xp_dir(), "Patches", tile,
                                suffixe + ".patch.osm")
            contenu = _osm_polygon(
                _rectangle(lat, lon, marge=0.45),
                tags=[("altitude_low", "0"), ("altitude_high", "0"),
                      ("profile", "spline")])
            messagebox.showinfo(
                tr("Aéroport & Runways"),
                tr("Un rectangle pré-tagué va s'ouvrir dans JOSM.\n\n"
                   "Placez-le sur la piste, puis renseignez altitude_low "
                   "et altitude_high en MÈTRES aux deux extrémités. Pour "
                   "une piste plate, mettez la même valeur des deux côtés, "
                   "ou remplacez les deux tags par un seul tag "
                   "altitude.\n\n") + _consigne_enregistrement(),
                parent=self)
            self._create_and_open(path, contenu)

        ttk.Button(bar, text=tr("Créer et ouvrir"),
                   command=_go).pack(side="left", padx=4)
        ttk.Button(bar, text=tr("Annuler"),
                   command=win.destroy).pack(side="right", padx=4)
        lb.bind("<Double-Button-1>", _go)
        lb.bind("<Return>", _go)
        win.bind("<Escape>", lambda e: win.destroy())
        lb.focus_set()
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

    # ── Fichiers d'emprise enregistrés au mauvais endroit ──────────────
    def _propose_stray(self, extents_dir):
        """Signale les fichiers égarés et propose de les ranger.

        L'utilisateur voit ce qui a été trouvé, où, et ce qui va être fait
        pour chacun. Il décide. Après application, aucun doublon ne reste :
        soit le fichier a rejoint Extents/, soit il a été supprimé parce
        qu'il faisait doublon avec une version identique ou plus récente.
        """
        trouves = _scan_stray_osm(extents_dir)
        if not trouves:
            return

        lignes = []
        for src, _dst, action, raison in trouves:
            verbe = (tr("DÉPLACER vers Extents/") if action == "deplacer"
                     else tr("SUPPRIMER"))
            lignes.append("• {}\n    {}\n    → {}  ({})".format(
                os.path.basename(src), src, verbe, raison))

        txt = (tr("Des fichiers d'emprise ont été enregistrés ailleurs que "
                  "dans Extents/.\nOrtho4XP ne les voit pas à cet "
                  "endroit.\n\n")
               + "\n\n".join(lignes)
               + tr("\n\nRanger maintenant ? Aucun doublon ne subsistera : "
                    "chaque fichier rejoint Extents/ ou disparaît s'il y "
                    "fait doublon."))

        if not messagebox.askyesno(tr("Fichiers enregistrés au mauvais "
                                      "endroit"), txt, parent=self):
            self._say(tr("Rangement refusé : ") + str(len(trouves))
                      + tr(" fichier(s) laissé(s) en place."))
            return

        dep, sup, err = _apply_stray(trouves)
        for x in dep:
            self._say(tr("Déplacé dans Extents/ : ") + x)
        for x in sup:
            self._say(tr("Doublon supprimé : ") + x)
        for x in err:
            self._say(tr("Échec : ") + x)
        if err:
            messagebox.showwarning(
                tr("Fichiers enregistrés au mauvais endroit"),
                "\n".join(err), parent=self)

    # ══════════════════════════════════════════════════════════════════
    #  Publication automatique des emprises
    # ══════════════════════════════════════════════════════════════════
    #  L'utilisateur n'a RIEN à faire : il dessine dans JOSM, il
    #  enregistre, et les fichiers attendus par Ortho4XP sont écrits tout
    #  seuls. Trois moments : à l'ouverture de la fenêtre, en continu tant
    #  qu'elle est ouverte, et à sa fermeture.

    def _publier_auto(self, signaler=True):
        """Publie toute emprise dont le dessin a changé."""
        d = os.path.join(_ortho4xp_dir(), "Extents")
        if not os.path.isdir(d):
            return 0
        n = 0
        for nom in _a_publier(d):
            try:
                b = _publier_emprise(d, nom)
                if b:
                    n += 1
                    if signaler:
                        self._say(tr("Emprise publiée : ") + nom
                                  + "  mask_bounds="
                                  + ",".join("{:.6f}".format(x) for x in b))
            except Exception as e:
                _log("publication " + nom + " : " + str(e))
        return n

    def _suivre_tuile(self):
        """Rafraîchit l'en-tête et les boutons si la tuile a changé.

        La tuile active est saisie dans la fenêtre principale, qui ne
        prévient personne. Sans cette vérification, il faut fermer et
        rouvrir la fenêtre pour la voir suivre — et les boutons de
        couches continuent d'afficher ceux de l'ancienne tuile.

        Rien n'est reconstruit tant que la tuile ne change pas : le coût
        est une simple lecture de deux champs toutes les 4 secondes.
        """
        try:
            courant = self._tile_latlon()
        except Exception:
            return
        if courant[0] is None or courant[1] is None:
            return
        # Anti-saisie en cours : la valeur doit être la même qu'au
        # passage précédent avant d'être prise en compte. Sans cela,
        # taper « 46 » déclencherait un rafraîchissement dès le « 4 »,
        # sur une tuile qui n'existe pas.
        stable = getattr(self, "_tuile_stable", None)
        self._tuile_stable = courant
        if courant != stable:
            return
        if courant == getattr(self, "_tuile_vue", None):
            return
        self._tuile_vue = courant
        try:
            self._say(tr("Tuile active : ") + _short_latlon(*courant))
            self._refresh_tile()
        except Exception as e:
            _log("suivi de tuile : " + str(e))

    def _surveiller(self):
        """Vérifie périodiquement si une emprise vient d'être enregistrée."""
        try:
            self._suivre_tuile()
        except Exception as e:
            _log("suivi de tuile : " + str(e))
        try:
            self._publier_auto()
        except Exception as e:
            _log("surveillance : " + str(e))
        try:
            self._watch_id = self.after(4000, self._surveiller)
        except Exception:
            pass

    # ── Restauration ───────────────────────────────────────────────────
    # ── Fermeture : filet de sécurité ──────────────────────────────────
    def _on_close(self):
        """Sauvegarde silencieuse, dernière publication, puis fermeture.

        Troisième déclencheur de sauvegarde, après l'instantané à
        l'ouverture d'une couche et le bouton manuel. Il supprime la
        dernière zone de risque : éditer dans JOSM, enregistrer, puis
        supprimer la tuile sans avoir pensé à sauvegarder.

        Ce sont les couches RÉELLEMENT OUVERTES pendant la séance qui
        sont sauvegardées, chacune sous la tuile à laquelle elle
        appartient. L'ancien balayage du dossier de la tuile affichée
        laissait tomber le travail dès qu'on avait changé de tuile
        entre-temps — et relisait au passage des couches jamais
        ouvertes.

        Silencieuse et sans condition d'échec : la fermeture ne doit
        JAMAIS être empêchée par un problème de sauvegarde.
        """
        try:
            n = 0
            for chemin in sorted(getattr(self, "_couches_ouvertes", ())):
                if not os.path.isfile(chemin):
                    continue
                lat, lon = _tile_de_fichier(chemin)
                if lat is None or lon is None:
                    lat, lon = self._tile_latlon()
                if lat is None or lon is None:
                    continue
                # Sans original de référence, il n'y a rien à comparer :
                # _snapshot_modified le vérifie déjà et retourne None.
                if _snapshot_modified(chemin, lat, lon):
                    n += 1
            if n:
                _log(tr("Modifications sauvegardées à la fermeture : ")
                     + str(n))
        except Exception as e:
            _log("fermeture : " + str(e))
        try:
            if self.__dict__.get("_watch_id"):
                self.after_cancel(self._watch_id)
        except Exception:
            pass
        try:
            # Dernier passage : une emprise enregistrée juste avant la
            # fermeture ne doit pas rester non publiée.
            self._publier_auto(signaler=False)
        except Exception as e:
            _log("publication a la fermeture : " + str(e))
        try:
            self.destroy()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════
    #  Sauvegardes : mes modifications / l'original
    # ══════════════════════════════════════════════════════════════════
    def _open_backups(self):
        """Regroupe les trois actions de sécurité en un seul endroit."""
        win = tk.Toplevel(self)
        win.title(tr("Sauvegardes"))
        win.configure(bg=self.BG)
        try:
            win.transient(self)
        except Exception:
            pass
        win.columnconfigure(0, weight=1)

        tk.Label(win, justify="left", bg=self.BG, fg=self.FG2,
                 font=("TkFixedFont", 11),
                 text=tr("Deux copies vivent dans « Sauvegarde fichier "
                         "source », hors\ndu dossier de la tuile : elles "
                         "survivent donc à sa suppression.\n\n"
                         "• l'original, tel qu'Ortho4XP l'avait téléchargé\n"
                         "• vos modifications, à réappliquer sur une tuile "
                         "reconstruite")).grid(
            row=0, column=0, padx=10, pady=10, sticky=W)

        ttk.Button(win, text=tr("Sauvegarder mes modifications maintenant"),
                   command=lambda: (win.destroy(), self._save_modified())
                   ).grid(row=1, column=0, padx=10, pady=3, sticky=E+W)
        ttk.Button(win, text=tr("Réappliquer mes modifications"),
                   command=lambda: (win.destroy(), self._reapply_modified())
                   ).grid(row=2, column=0, padx=10, pady=3, sticky=E+W)
        ttk.Button(win, text=tr("Restaurer l'original"),
                   command=lambda: (win.destroy(), self._restore_original())
                   ).grid(row=3, column=0, padx=10, pady=3, sticky=E+W)
        ttk.Button(win, text=tr("Fermer"), command=win.destroy).grid(
            row=4, column=0, padx=10, pady=(10, 10), sticky=E)
        win.bind("<Escape>", lambda e: win.destroy())
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

    def _save_modified(self):
        """Enregistre l'état courant de toutes les couches de la tuile."""
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            return
        d = _osm_data_dir(lat, lon)
        if not os.path.isdir(d):
            messagebox.showwarning(
                tr("Sauvegarder mes modifications"),
                tr("Aucun dossier de données OSM pour cette tuile."),
                parent=self)
            return
        n = 0
        try:
            for f in sorted(os.listdir(d)):
                if not f.lower().endswith("osm.bz2"):
                    continue
                m = _snapshot_modified(os.path.join(d, f), lat, lon)
                if m:
                    self._say(tr("Modifications sauvegardées : ") + f)
                    n += 1
        except Exception as e:
            messagebox.showerror(tr("Sauvegarder mes modifications"), str(e),
                                 parent=self)
            return
        if n:
            messagebox.showinfo(
                tr("Sauvegarder mes modifications"),
                tr("Fichiers sauvegardés : ") + str(n), parent=self)
        else:
            messagebox.showinfo(
                tr("Sauvegarder mes modifications"),
                tr("Aucune modification à sauvegarder : les fichiers sont "
                   "identiques à l'original."), parent=self)

    def _reapply_modified(self):
        """Réinjecte mes modifications dans la tuile (même reconstruite)."""
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            return
        d = _original_dir(lat, lon)
        cible = _osm_data_dir(lat, lon)
        try:
            mods = sorted(f for f in os.listdir(d)
                          if f.lower().endswith(".modifie"))
        except Exception:
            mods = []
        if not mods:
            messagebox.showinfo(
                tr("Réappliquer mes modifications"),
                tr("Aucune modification sauvegardée pour cette tuile."),
                parent=self)
            return
        if not messagebox.askyesno(
                tr("Réappliquer mes modifications"),
                tr("Remplacer les données OSM de la tuile par vos "
                   "modifications sauvegardées ?\n\nFichiers concernés : ")
                + str(len(mods))
                + tr("\n\nRelancez ensuite l'étape 1."), parent=self):
            return
        try:
            os.makedirs(cible, exist_ok=True)
            for f in mods:
                shutil.copy2(os.path.join(d, f),
                             os.path.join(cible, f[:-len(".modifie")]))
                self._say(tr("Modifications réappliquées : ")
                          + f[:-len(".modifie")])
        except Exception as e:
            messagebox.showerror(tr("Réappliquer mes modifications"), str(e),
                                 parent=self)
            return
        self._fill_osm_buttons()
        messagebox.showinfo(
            tr("Réappliquer mes modifications"),
            tr("Modifications réappliquées. Relancez l'étape 1 pour que la "
               "tuile les prenne en compte."), parent=self)

    # ── Restauration ───────────────────────────────────────────────────
    def _restore_original(self):
        """Remet en place la copie « .original » d'un fichier."""
        lat, lon = self._tile_latlon()
        if lat is None or lon is None:
            return
        d = _original_dir(lat, lon)
        cible = _osm_data_dir(lat, lon)
        if not os.path.isdir(d):
            messagebox.showinfo(
                tr("Restaurer l'original"),
                tr("Aucune copie d'origine pour cette tuile : aucun fichier "
                   "n'a encore été ouvert dans JOSM."),
                parent=self)
            return
        try:
            origs = sorted(f for f in os.listdir(d)
                           if f.lower().endswith(".original"))
        except Exception as e:
            messagebox.showerror(tr("Restaurer l'original"), str(e),
                                 parent=self)
            return
        if not origs:
            messagebox.showinfo(
                tr("Restaurer l'original"),
                tr("Aucune copie d'origine pour cette tuile : aucun fichier "
                   "n'a encore été ouvert dans JOSM."),
                parent=self)
            return

        win = tk.Toplevel(self)
        win.title(tr("Restaurer l'original"))
        win.configure(bg=self.BG)
        try:
            win.transient(self)
        except Exception:
            pass
        win.columnconfigure(0, weight=1)
        win.rowconfigure(1, weight=1)
        tk.Label(win, justify="left", bg=self.BG, fg=self.FG2,
                 font=("TkFixedFont", 11),
                 text=tr("Le fichier choisi sera remplacé par sa copie "
                         "d'origine.\nLes modifications faites dans JOSM "
                         "seront perdues.")).grid(
            row=0, column=0, padx=8, pady=8, sticky=W)
        lb = tk.Listbox(win, width=60, height=min(10, max(3, len(origs))),
                        bg=self.PREV_BG, fg=self.FG2, bd=0,
                        selectbackground=self.FG, selectforeground=self.BG,
                        highlightthickness=0,
                        font=("Courier", 11), exportselection=False)
        lb.grid(row=1, column=0, padx=8, sticky=N+S+E+W)
        for f in origs:
            lb.insert(END, f[:-len(".original")])
        lb.selection_set(0)
        bar = tk.Frame(win, bg=self.BG)
        bar.grid(row=2, column=0, sticky=E+W, padx=8, pady=8)

        def _go(_e=None):
            sel = lb.curselection()
            if not sel:
                return
            src = os.path.join(d, origs[sel[0]])
            dst = os.path.join(cible, origs[sel[0]][:-len(".original")])
            if not messagebox.askyesno(
                    tr("Restaurer l'original"),
                    tr("Remplacer définitivement :\n")
                    + os.path.basename(dst)
                    + tr("\n\npar sa copie d'origine ?"), parent=win):
                return
            win.destroy()
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                self._say(tr("Original restauré : ") + os.path.basename(dst))
                messagebox.showinfo(
                    tr("Restaurer l'original"),
                    tr("Fichier restauré. Relancez l'étape 1 pour que la "
                       "tuile reparte de la donnée d'origine."), parent=self)
            except Exception as e:
                messagebox.showerror(tr("Restaurer l'original"), str(e),
                                     parent=self)

        ttk.Button(bar, text=tr("Restaurer"),
                   command=_go).pack(side="left", padx=4)
        ttk.Button(bar, text=tr("Annuler"),
                   command=win.destroy).pack(side="right", padx=4)
        lb.bind("<Double-Button-1>", _go)
        lb.bind("<Return>", _go)
        win.bind("<Escape>", lambda e: win.destroy())
        lb.focus_set()
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

    def _open_in_josm(self, filepath):
        """Remote Control d'abord, lancement de l'application ensuite."""
        def _work():
            ok = False
            msg = ""
            if _josm_remote_alive():
                ok = _josm_remote_open(filepath)
                msg = (tr("Fichier envoyé à la fenêtre JOSM déjà ouverte.")
                       if ok else
                       tr("JOSM répond mais a refusé le fichier."))
            if not ok:
                path = _find_josm()
                if not path:
                    self.after(0, lambda: messagebox.showwarning(
                        tr("JOSM introuvable"), tr(_JOSM_HELP), parent=self))
                    self.after(0, lambda: self._say(tr("JOSM introuvable.")))
                    return
                ok, err = _launch_josm(path, filepath)
                if not ok:
                    self.after(0, lambda: self._say(
                        tr("Échec du lancement : ") + err))
                    return
                msg = tr("JOSM lancé avec le fichier.")
                # Filet : si JOSM a démarré sans charger le fichier (bundle
                # macOS ouvert sans document, ou argument ignoré), on le lui
                # transmet dès que son Remote Control répond.
                self.after(0, lambda: self._say(
                    tr("Démarrage de JOSM, veuillez patienter…")))
                if _wait_remote():
                    if _josm_remote_open(filepath):
                        msg = tr("Fichier transmis à JOSM.")
                else:
                    msg = tr("JOSM a été lancé. Si le fichier ne s'ouvre "
                             "pas, activez le Remote Control dans les "
                             "préférences de JOSM (voir « Aide JOSM »).")
            self.after(0, lambda: self._say(msg))
            if ok:
                self.after(0, self._remind_step1)
            self.after(0, self._refresh_josm_async)

        threading.Thread(target=_work, daemon=True).start()

    def _remind_step1(self):
        messagebox.showinfo(
            tr("Après l'édition dans JOSM"),
            tr("Enregistrez régulièrement votre travail dans JOSM "
               "(une copie d'origine a été rangée dans « Sauvegarde fichier "
               "source » avant ouverture : le bouton « Restaurer l'original » "
               "permet de revenir en arrière à tout moment).\n\n"
               "Quand votre édition sera terminée et enregistrée, cliquez "
               "sur « Sauvegardes… » puis « Sauvegarder mes modifications » "
               ": votre travail sera alors protégé même si la tuile est "
               "supprimée ou reconstruite.\n\n"
               "Une fois l'édition terminée et enregistrée, relancez "
               "l'étape 1 (Assemble Vector data) dans Ortho4XP : les "
               "données modifiées seront reprises telles quelles, sans "
               "nouveau téléchargement.\n\n") + _consigne_enregistrement(),
            parent=self)


# ============================================================================
#  Point d'entrée appelé par le GUI
# ============================================================================

def open_avance_window(parent):
    """Ouvre la fenêtre « Avancé ». Ne lève jamais : le GUI reste sain."""
    try:
        w = AvanceWindow(parent)
        try:
            w.lift()
            w.focus_force()
        except Exception:
            pass
        return w
    except Exception as e:
        _log("open_avance_window : " + str(e))
        try:
            messagebox.showerror(tr("Avancé — Couches JOSM"), str(e))
        except Exception:
            pass
        return None


# ============================================================================
#  Auto-test hors GUI
# ============================================================================

if __name__ == "__main__":
    print("O4_Avance_Utils — auto-test")
    print("  racine Ortho4XP :", _ortho4xp_dir())
    print("  tuile +46-003   :", _short_latlon(46, -3))
    print("  parent 10°      :", _short_latlon(_round10(46), _round10(-3)))
    print("  OSM_data        :", _osm_data_dir(46, -3))
    print("  copies securite :", _original_dir(46, -3))
    print("  JOSM détecté    :", _find_josm())
    print("  Remote Control  :", _josm_remote_alive())
    for _f in ("+46-003_water_osm.bz2", "+46-003_coastline_osm.bz2",
               "+46-003_big_roads_osm.bz2", "+46-003_airports_osm.bz2",
               "+46-003_small_roads_osm.bz2"):
        print("  filtre  {:<30} retenu={}  {}".format(
            _f, _f.lower().endswith("osm.bz2"), _layer_label(_f)))
