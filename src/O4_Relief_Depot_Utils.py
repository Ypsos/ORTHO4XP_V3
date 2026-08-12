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
#  O4_Relief_Depot_Utils.py  —  DÉPÔT & STRUCTURE du relief Sonny
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  RÔLE — Gérer l'HÉBERGEMENT des données Sonny sur le disque choisi par
#    l'utilisateur, avec une STRUCTURE À NOM FIXE pour qu'Ortho4XP retrouve
#    toujours ses fichiers, quel que soit le disque désigné.
#
#    L'utilisateur ne choisit QUE le disque/dossier racine. Ortho crée
#    dedans, avec un nom IMPOSÉ (en dur), la structure :
#
#        <racine choisie>/Ortho4XP_Relief_Sonny/
#              ├── _downloads/   ← ZIP téléchargés (temporaire)
#              └── hgt/          ← .hgt rangés et vérifiés (lu par Ortho)
#
#    Ortho mémorise la racine (via le cfg) ; le sous-dossier étant fixe, il
#    recompose toujours le bon chemin. L'utilisateur ne peut pas se tromper
#    de nom : il ne le choisit jamais.
#
#  CE MODULE (100 % hors-ligne, aucune dépendance réseau) :
#    - NOM_STRUCTURE / dossier_hgt() / dossier_downloads() : chemins fixes.
#    - creer_structure()      : crée l'arborescence sous la racine choisie.
#    - espace_libre_go()      : espace disponible sur le disque (sécurité).
#    - assez_d_espace()       : compare à un minimum requis.
#    - decompresser_zip()     : extrait un .zip Sonny vers un dossier temp,
#                               en se protégeant des chemins malveillants
#                               (zip slip) et sans jamais lever.
#    - trouver_zips_sonny()   : repère les .zip plausibles dans un dossier
#                               (ex. Téléchargements) pour récupération auto.
#
#  Le RANGEMENT effectif des .hgt (copie vérifiée) reste assuré par
#  O4_Relief_Sonny_Utils.importer_dossier() : ce module prépare et alimente,
#  il ne duplique pas la logique d'import.
# ----------------------------------------------------------------------------

import os
import shutil
import zipfile
import tempfile

# Nom de structure IMPOSÉ (en dur). Ne jamais rendre configurable.
NOM_STRUCTURE = "Ortho4XP_Relief_Sonny"
_SOUS_HGT = "hgt"
_SOUS_DL = "_downloads"

# Pays traités par Sonny (source : sonny.4lima.de, page DOWNLOADS).
# Les dossiers correspondants sont créés vides dès la mise en place de la
# structure, pour que l'utilisateur voie où ranger et qu'Ortho retrouve tout.
PAYS_SONNY = (
    "Autriche", "Belgique", "Croatie", "Chypre", "Rep_Tcheque",
    "Danemark", "Estonie", "Finlande", "France", "Allemagne",
    "Grece", "Hongrie", "Islande", "Irlande", "Italie",
    "Lettonie", "Lituanie", "Luxembourg", "Pays-Bas", "Norvege",
    "Pologne", "Portugal", "Roumanie", "Slovaquie", "Slovenie",
    "Espagne", "Suede", "Suisse", "Royaume-Uni",
    "Autre",
)

# Marge de sécurité : espace minimal conseillé sur le disque cible (Go).
# Un pays Sonny 1" pèse jusqu'à ~1-2 Go zippé + décompressé ; l'Europe 4,8 Go.
ESPACE_MIN_GO_DEFAUT = 6.0

# Taille plancher d'un .hgt (identique au chapitre 2) pour cohérence.
_TAILLE_MIN_HGT = 1201 * 1201 * 2


# --------------------------------------------------------------------------
#  Chemins de la structure à nom fixe
# --------------------------------------------------------------------------
def racine_structure(disque_choisi):
    """<disque choisi>/Ortho4XP_Relief_Sonny  (nom fixe, non modifiable)."""
    return os.path.join(disque_choisi, NOM_STRUCTURE)


def dossier_hgt(disque_choisi):
    """Dossier lu par Ortho pour les .hgt rangés."""
    return os.path.join(racine_structure(disque_choisi), _SOUS_HGT)


def dossier_downloads(disque_choisi):
    """Dossier temporaire où atterrissent/déplacent les ZIP."""
    return os.path.join(racine_structure(disque_choisi), _SOUS_DL)


def emplacement_verrouille(hgtdir_memorise, log=None):
    """PROTECTION anti-multiples. À partir du chemin hgt mémorisé dans le cfg
    (relief_sonny_dir), détermine l'état de l'emplacement UNIQUE :

      ('ok', hgtdir)        : la structure existe -> à réutiliser telle quelle.
      ('introuvable', None) : un emplacement était défini mais a disparu
                              (disque débranché/déplacé) -> prévenir, ne PAS
                              en recréer un ailleurs sans l'accord explicite.
      ('absent', None)      : aucun emplacement défini -> première création
                              autorisée.

    Ne crée rien, ne lève jamais. C'est le garde-fou qui empêche un second
    Ortho4XP_Relief_Sonny de proliférer n'importe où.
    """
    def _l(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass
    if not hgtdir_memorise:
        return ("absent", None)
    try:
        if os.path.isdir(hgtdir_memorise):
            return ("ok", hgtdir_memorise)
        # Peut-être la racine existe mais pas le sous-dossier hgt : on tolère.
        racine = os.path.dirname(hgtdir_memorise)
        if os.path.isdir(racine):
            return ("ok", hgtdir_memorise)
    except Exception:
        pass
    _l("   [DEPOT] Emplacement relief mémorisé introuvable : %s"
       % hgtdir_memorise)
    return ("introuvable", None)


def creer_structure(disque_choisi, log=None):
    """Crée <racine>/Ortho4XP_Relief_Sonny/{hgt,_downloads}.
    Retourne le dossier hgt (celui qu'Ortho lira), ou None si échec.

    PROTECTION : si le disque choisi est DÉJÀ à l'intérieur d'une structure
    Ortho4XP_Relief_Sonny existante, on ne recrée pas une structure imbriquée
    — on renvoie le hgt de la structure parente. Empêche les poupées russes.
    Ne lève jamais."""
    """Crée <racine>/Ortho4XP_Relief_Sonny/{hgt,_downloads}.
    Retourne le dossier hgt (celui qu'Ortho lira), ou None si échec.
    Ne lève jamais."""
    def _l(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass
    try:
        # PROTECTION poupées russes : si le disque choisi est déjà DANS une
        # structure Ortho4XP_Relief_Sonny, on réutilise la structure parente
        # au lieu d'en imbriquer une seconde.
        _chemin = os.path.abspath(disque_choisi)
        _parties = _chemin.split(os.sep)
        if NOM_STRUCTURE in _parties:
            _idx = _parties.index(NOM_STRUCTURE)
            _racine_parente = os.sep.join(_parties[:_idx + 1])
            hgt = os.path.join(_racine_parente, _SOUS_HGT)
            os.makedirs(hgt, exist_ok=True)
            for _pays in PAYS_SONNY:
                try:
                    os.makedirs(os.path.join(hgt, _pays), exist_ok=True)
                except Exception:
                    pass
            _l("   [DEPOT] Structure existante réutilisée (pas d'imbrication) : %s"
               % _racine_parente)
            return hgt

        hgt = dossier_hgt(disque_choisi)
        os.makedirs(hgt, exist_ok=True)
        # Crée d'avance TOUS les dossiers pays Sonny (vides). L'utilisateur
        # voit où ranger, et Ortho retrouve toujours le bon dossier.
        # (Le dossier _downloads n'est pas créé : le navigateur télécharge
        #  dans ~/Downloads, et l'import lit directement là-bas.)
        for _pays in PAYS_SONNY:
            try:
                os.makedirs(os.path.join(hgt, _pays), exist_ok=True)
            except Exception:
                pass
        _l("   [DEPOT] Structure prête (%d dossiers pays) : %s"
           % (len(PAYS_SONNY), racine_structure(disque_choisi)))
        return hgt
    except Exception as e:
        _l("   [DEPOT] Création impossible (%s)." % type(e).__name__)
        return None


# --------------------------------------------------------------------------
#  Sécurité espace disque
# --------------------------------------------------------------------------
def espace_libre_go(chemin):
    """Espace libre (Go) sur le disque contenant `chemin`. -1 si inconnu.
    Ne lève jamais."""
    try:
        cible = chemin
        # Remonte au premier dossier existant (le disque peut être vide).
        while cible and not os.path.exists(cible):
            parent = os.path.dirname(cible)
            if parent == cible:
                break
            cible = parent
        if not cible or not os.path.exists(cible):
            return -1.0
        st = shutil.disk_usage(cible)
        return st.free / (1024.0 ** 3)
    except Exception:
        return -1.0


def assez_d_espace(chemin, minimum_go=ESPACE_MIN_GO_DEFAUT):
    """Retourne (ok, libre_go). ok=True si libre >= minimum.
    Si l'espace est inconnu (-1), on renvoie ok=True (on ne bloque pas à tort)
    mais libre_go=-1 pour que l'appelant puisse prévenir."""
    libre = espace_libre_go(chemin)
    if libre < 0:
        return True, -1.0
    return (libre >= minimum_go), libre


# --------------------------------------------------------------------------
#  Décompression ZIP sécurisée (anti zip-slip)
# --------------------------------------------------------------------------
def _dest_sure(base, membre):
    """Chemin de destination sûr : empêche l'extraction hors de `base`
    (attaque zip-slip via des noms comme ../../etc)."""
    dest = os.path.realpath(os.path.join(base, membre))
    base_real = os.path.realpath(base)
    if dest == base_real or dest.startswith(base_real + os.sep):
        return dest
    return None


def decompresser_zip(chemin_zip, dossier_cible=None, log=None):
    """Décompresse un .zip Sonny. Extrait uniquement les .hgt (les autres
    fichiers du zip sont ignorés). Retourne le dossier contenant les .hgt
    extraits, ou None. Protégé contre zip-slip. Ne lève jamais.
    """
    def _l(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass

    if not chemin_zip or not os.path.isfile(chemin_zip):
        _l("   [DEPOT] ZIP introuvable.")
        return None
    if not zipfile.is_zipfile(chemin_zip):
        _l("   [DEPOT] Fichier non-ZIP ignoré.")
        return None

    cible = dossier_cible or tempfile.mkdtemp(prefix="sonny_unzip_")
    try:
        os.makedirs(cible, exist_ok=True)
    except Exception:
        return None

    n = 0
    try:
        with zipfile.ZipFile(chemin_zip) as z:
            for membre in z.namelist():
                if not membre.lower().endswith(".hgt"):
                    continue
                dest = _dest_sure(cible, os.path.basename(membre))
                if dest is None:
                    _l("   [DEPOT] Entrée ZIP suspecte ignorée : %s" % membre)
                    continue
                try:
                    with z.open(membre) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    if os.path.getsize(dest) >= _TAILLE_MIN_HGT:
                        n += 1
                    else:
                        os.remove(dest)
                except Exception:
                    continue
    except Exception as e:
        _l("   [DEPOT] Décompression interrompue (%s)." % type(e).__name__)
        return None

    _l("   [DEPOT] %d fichier(s) .hgt extrait(s)." % n)
    return cible if n > 0 else None


# --------------------------------------------------------------------------
#  Repérage des ZIP Sonny (récupération auto depuis Téléchargements)
# --------------------------------------------------------------------------
def dossier_telechargements():
    """Dossier Téléchargements de l'utilisateur (best effort, multi-OS)."""
    for cand in (os.path.join(os.path.expanduser("~"), "Downloads"),
                 os.path.join(os.path.expanduser("~"), "Téléchargements")):
        if os.path.isdir(cand):
            return cand
    return os.path.expanduser("~")


def trouver_zips_sonny(dossier=None, apres_horodatage=None):
    """Liste les .zip plausiblement Sonny dans `dossier` (défaut :
    Téléchargements), triés du plus récent au plus ancien. Si
    `apres_horodatage` est fourni, ne garde que les zip modifiés après.
    Ne lève jamais."""
    d = dossier or dossier_telechargements()
    trouves = []
    try:
        for f in os.listdir(d):
            if not f.lower().endswith(".zip"):
                continue
            chemin = os.path.join(d, f)
            try:
                mtime = os.path.getmtime(chemin)
            except Exception:
                continue
            if apres_horodatage is not None and mtime < apres_horodatage:
                continue
            # Filtre léger : nom contenant un indice Sonny/DTM/pays fréquent.
            nom = f.lower()
            indice = ("dtm" in nom or "sonny" in nom or "1sec" in nom
                      or "1s" in nom or "3sec" in nom or "hgt" in nom)
            trouves.append((mtime, chemin, indice))
    except Exception:
        return []
    # Récents d'abord ; ceux qui "sentent" Sonny remontent à mtime égal.
    trouves.sort(key=lambda t: (t[0], t[2]), reverse=True)
    return [c for _m, c, _i in trouves]
