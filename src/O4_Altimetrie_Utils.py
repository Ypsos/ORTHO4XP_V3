
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
#  O4_Altimetrie_Utils.py  —  ORTHO4XP V3
#  Module autonome « Altimétrie / DEM »
#
#  RÔLE :
#    Remplacer la procédure QGIS manuelle (41 étapes + tableur .ods) par
#    un seul bouton. Le module lit les fichiers altimétriques présents
#    dans le dossier de la tuile (fichiers réels OU liens symboliques
#    relatifs), les reprojette en EPSG:4326, les découpe à l'emprise de
#    la tuile élargie du débord de chevauchement, les fusionne, écrit
#    <tuile>.tif à côté, et renseigne custom_dem dans le cfg de la tuile.
#
#  ÉQUIVALENCE AVEC LA PROCÉDURE MANUELLE (validée avec Roland) :
#    Raster/Projections/Warp  -> reprojection EPSG:4326
#    NoData -32767 -> -99999  -> _NODATA
#    Emprise du tableur .ods  -> gdalwarp -te (lon-0.1) (lat-0.1)
#                                          (lon+1.1) (lat+1.1)
#    Raster/Divers/Fusion     -> rasterio.merge
#    Export + champ DEM       -> écriture <tuile>.tif + custom_dem
#
#  RÈGLES RESPECTÉES :
#    - Fichier NEUF. Aucun fichier du pipeline n'est modifié :
#      ni O4_DSF_Utils.py, ni les fichiers Sea, ni le mécanisme Extents/.
#    - Aucune commande Terminal. Tout passe par rasterio (déjà installé
#      dans le venv, avec gdal_data/ et proj_data/ embarqués : l'erreur
#      « Cannot find proj.db » ne peut donc pas se produire).
#    - Le CRS source n'est JAMAIS codé en dur : il est lu dans le
#      fichier. EPSG:2154 (Lambert-93) n'est proposé qu'en repli pour les
#      fichiers qui ne déclarent aucun CRS (cas des .asc IGN bruts).
#    - L'arborescence de Roland n'est ni interprétée ni réorganisée.
#    - Les fichiers sources ne sont jamais modifiés (lecture seule).
# ============================================================

import os

# Débord de chevauchement : 10 % d'une tuile de 1° = 0,1° sur les 4 côtés.
# Sert à ce que les bords fusionnent sans couture avec la tuile voisine.
DEBORD_DEFAUT = 0.1

# Valeur NoData de sortie (identique à la procédure manuelle).
_NODATA = -99999.0

# CRS de repli, utilisé UNIQUEMENT si le fichier ne déclare aucun CRS.
_CRS_REPLI = "EPSG:2154"

_EXT_RASTER = (".tif", ".tiff", ".vrt", ".asc", ".img", ".hgt", ".dt2")


def _est_fichier_raster(chemin):
    """Vrai si le fichier porte une extension raster — OU si c'est un lien
    symbolique dont la CIBLE réelle porte une extension raster.

    Indispensable : un utilisateur crée souvent un lien vers son gros
    fichier (plusieurs dizaines de Go) et l'outil macOS nomme parfois ce
    lien « ....tif symlink » (le nom ne finit donc PAS en .tif). Sans ce
    contrôle sur la cible, ce lien serait ignoré et le fichier — pourtant
    valide — ne serait jamais assemblé."""
    nom = os.path.basename(chemin)
    if nom.lower().endswith(_EXT_RASTER):
        return True
    try:
        if os.path.islink(chemin):
            cible = os.path.realpath(chemin)
            if os.path.basename(cible).lower().endswith(_EXT_RASTER):
                return True
    except Exception:
        pass
    return False


# Plafond de sur-échantillonnage : on autorise une sortie plus fine que la
# source (ex. Sonny 27 m → 4 m, comme dans QGIS = interpolation, grille
# uniforme), mais on borne le facteur pour éviter une explosion mémoire sur
# une saisie extrême (16 couvre largement 27 m → ~1,7 m).
_RATIO_MAX = 16.0

# Bornes d'altitude physiquement possibles sur Terre, avec une marge
# large (Everest 8 849 m, fosse des Mariannes -10 984 m). Toute valeur
# en dehors n'est pas une altitude : c'est une valeur de remplissage
# (-32767, -9999, -3.4e38 laissé par un warp GDAL…) que le fichier a
# oublié de déclarer en NoData. Fusionnée telle quelle, elle écrase le
# relief réel et produit un mesh plat ou aberrant SANS message d'erreur.
_ALT_MIN = -12000.0
_ALT_MAX = 9500.0

# Hauteur des bandes lues d'un coup lors de l'assainissement. Travailler
# par bandes garde la mémoire constante : un département réduit peut
# faire plusieurs Go, il ne doit jamais être chargé en entier.
_BANDE_LIGNES = 512

# ── Structure imposée (créée au premier lancement) ──────────────────
#   <racine choisie>/Altimétrie/
#       ├── Altimétrie TIFF/<Pays>/      ← sources déposées (EPSG:4326)
#       └── Altimétrie assemble/
#             └── Assemble <Pays>/<tuile>/<tuile>.tif
# Imposer la structure supprime toute la classe d'erreurs « chemin
# introuvable » chez les utilisateurs qui n'ont pas d'organisation.
DOSSIER_RACINE = "Altimétrie"
DOSSIER_STOCK = "Altimétrie TIFF"
DOSSIER_ASSEMBLE = "Altimétrie assemble"
PREFIXE_PAYS_ASSEMBLE = "Assemble "

CFG_RACINE = "dem_root_dir"      # ANCIEN — conservé pour la reprise
CFG_PAYS = "dem_last_country"    # ANCIEN — conservé pour la reprise
CFG_STOCK = "dem_stock_dir"      # ANCIEN dossier des sources (reprise)
CFG_SORTIE = "dem_output_dir"    # ANCIEN dossier du résultat (reprise)
CFG_QGIS = "qgis_app"            # application QGIS (comme patch_editor_app)
CFG_PREP_SRC = "dem_prepare_src_dir"  # dernier dossier source ouvert (Préparer)

# ── NOUVELLE STRUCTURE À 4 DOSSIERS (validée avec Roland) ────────────
#   <racine>/Altimétrie/
#       ├── Données Sonny/<Pays>/     ← Sonny isolé (licence), va direct à l'assemblage
#       ├── ASC brut/<Pays>/<Dépt>/   ← brut IGN + étranger, temporaire (vidé à la main)
#       ├── EPSG réduit/<Pays>/       ← sorties de « Préparer », toutes résolutions
#       └── Assemblage tuile/<tuile>/ ← tuile finale (+46-003.tif) → custom_dem
# Chaque dossier a son propre bouton qui pointe droit dessus.
DOSSIER_SONNY = "Données Sonny"
DOSSIER_ASC = "ASC brut"
DOSSIER_EPSG = "EPSG réduit"
DOSSIER_TUILE = "Assemblage tuile"

CFG_SONNY = "dem_sonny_dir"      # dossier Données Sonny (courant, par pays)
CFG_ASC = "dem_asc_dir"          # dossier ASC brut (courant, par pays)
CFG_EPSG = "dem_epsg_dir"        # dossier EPSG réduit (courant, par pays)
CFG_TILEOUT = "dem_tile_out_dir"  # dossier Assemblage tuile (racine, rangé par tuile)


def chemins_structure(racine):
    """Retourne (stock, assemble) pour une racine <...>/Altimétrie."""
    return (os.path.join(racine, DOSSIER_STOCK),
            os.path.join(racine, DOSSIER_ASSEMBLE))


def creer_structure(base, pays):
    """Crée la structure complète. Idempotent : ne détruit jamais rien,
    se contente de créer ce qui manque. Retourne (racine, stock_pays,
    assemble_pays)."""
    racine = os.path.join(base, DOSSIER_RACINE) \
        if os.path.basename(os.path.normpath(base)) != DOSSIER_RACINE \
        else base
    stock, assemble = chemins_structure(racine)
    stock_pays = os.path.join(stock, pays)
    assemble_pays = os.path.join(assemble, PREFIXE_PAYS_ASSEMBLE + pays)
    for d in (racine, stock, assemble, stock_pays, assemble_pays):
        os.makedirs(d, exist_ok=True)
    return racine, stock_pays, assemble_pays


def creer_pays_dans(racine, pays, cible):
    """Crée le dossier d'un pays dans UN SEUL des deux dossiers de la
    structure, jamais dans les deux :
      cible="stock"  → <racine>/Altimétrie TIFF/<pays>
      cible="sortie" → <racine>/Altimétrie assemble/Assemble <pays>
    L'autre dossier n'est jamais référencé ni touché. La racine et le
    dossier parent choisi ne sont créés que s'ils manquent (idempotent).
    Retourne le chemin du dossier créé."""
    stock, assemble = chemins_structure(racine)
    if cible == "stock":
        pays_dir = os.path.join(stock, pays)
    else:
        pays_dir = os.path.join(assemble, PREFIXE_PAYS_ASSEMBLE + pays)
    os.makedirs(pays_dir, exist_ok=True)
    return pays_dir


def lister_pays(racine):
    """Pays présents dans le stock."""
    stock, _a = chemins_structure(racine)
    if not os.path.isdir(stock):
        return []
    return sorted(d for d in os.listdir(stock)
                  if not d.startswith(".")
                  and os.path.isdir(os.path.join(stock, d)))


# ── NOUVELLE STRUCTURE À 4 DOSSIERS — logique pure, testée headless ──
#   Ces fonctions ne touchent JAMAIS aux données existantes (création
#   idempotente uniquement) et sont entièrement simulables sans rasterio.

def chemins_structure4(racine):
    """Retourne (sonny, asc, epsg, assemblage_tuile) sous <...>/Altimétrie."""
    return (os.path.join(racine, DOSSIER_SONNY),
            os.path.join(racine, DOSSIER_ASC),
            os.path.join(racine, DOSSIER_EPSG),
            os.path.join(racine, DOSSIER_TUILE))


def creer_structure4(base, pays=None):
    """Crée les 4 dossiers de la structure. Idempotent : ne détruit jamais
    rien, crée seulement ce qui manque. Si pays est fourni, crée aussi le
    sous-dossier <pays> dans Données Sonny, ASC brut et EPSG réduit — PAS
    dans Assemblage tuile (rangé par numéro de tuile, jamais par pays).
    Retourne (racine, sonny, asc, epsg, assemblage)."""
    racine = base if os.path.basename(os.path.normpath(base)) == DOSSIER_RACINE \
        else os.path.join(base, DOSSIER_RACINE)
    sonny, asc, epsg, assemble = chemins_structure4(racine)
    for d in (racine, sonny, asc, epsg, assemble):
        os.makedirs(d, exist_ok=True)
    if pays:
        for base_dir in (sonny, asc, epsg):
            os.makedirs(os.path.join(base_dir, pays), exist_ok=True)
    return racine, sonny, asc, epsg, assemble


def racine_depuis_dossier4(dossier):
    """Déduit la racine <...>/Altimétrie à partir d'un des 4 sous-dossiers
    (ou d'un sous-dossier pays à l'intérieur). Retourne la racine si le
    chemin appartient bien à la structure, sinon None."""
    if not dossier:
        return None
    parts = os.path.normpath(dossier).split(os.sep)
    for marqueur in (DOSSIER_SONNY, DOSSIER_ASC, DOSSIER_EPSG, DOSSIER_TUILE):
        if marqueur in parts:
            i = parts.index(marqueur)
            racine = os.sep.join(parts[:i]) or os.sep
            return racine
    if DOSSIER_RACINE in parts:
        i = parts.index(DOSSIER_RACINE)
        return os.sep.join(parts[:i + 1]) or os.sep
    return None


def _norm_nom(s):
    """Normalise un nom pour comparaison souple : minuscule, sans accents,
    sans séparateurs (espace, tiret, souligné)."""
    import unicodedata
    import re
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[\s_\-]+", "", s.lower())


def departements_asc(asc_dir):
    """Liste les sous-dossiers de département présents sous ASC brut, en
    descendant récursivement (gère ASC brut/<Pays>/<Département>). Un dossier
    est retenu s'il contient au moins un fichier raster (.asc, .tif…) ; on ne
    descend pas sous un dossier déjà retenu. Le dossier ASC brut lui-même et
    les dossiers vides ne sont jamais listés.
    Retourne une liste de (nom_affiché, chemin_absolu), triée."""
    res = []
    if not asc_dir or not os.path.isdir(asc_dir):
        return res
    racine_reelle = os.path.realpath(asc_dir)
    for rep, sous, fichiers in os.walk(asc_dir):
        if os.path.realpath(rep) == racine_reelle:
            continue
        a_du_raster = any(not f.startswith(".")
                          and f.lower().endswith(_EXT_RASTER)
                          for f in fichiers)
        if a_du_raster:
            res.append((os.path.basename(rep), rep))
            sous[:] = []  # département feuille : ne pas descendre plus bas
    return sorted(res, key=lambda t: t[0].lower())


def dept_est_reduit(dept_nom, epsg_dir):
    """Vrai si un fichier réduit correspondant au département existe déjà
    sous EPSG réduit (recherche récursive, comparaison souple sur le nom).
    Sert d'indicateur ✅ déjà réduit (sûr à supprimer) / ⚠️ pas encore."""
    if not epsg_dir or not os.path.isdir(epsg_dir):
        return False
    cible = _norm_nom(dept_nom)
    if not cible:
        return False
    for rep, _s, fichiers in os.walk(epsg_dir):
        for f in fichiers:
            if f.startswith(".") or not f.lower().endswith((".tif", ".tiff")):
                continue
            if cible in _norm_nom(f):
                return True
    return False


# ────────────────────────────────────────────────────────────────────
#  Partie 1 — logique pure (sans rasterio, entièrement simulable)
# ────────────────────────────────────────────────────────────────────

def tile_key(lat, lon):
    """Nom canonique de la tuile : +46-003, +49+007, -34+151…"""
    return "%s%02d%s%03d" % ("+" if lat >= 0 else "-", abs(int(lat)),
                             "+" if lon >= 0 else "-", abs(int(lon)))


def tile_bounds(lat, lon, debord=DEBORD_DEFAUT):
    """Emprise (ouest, sud, est, nord) de la tuile élargie du débord.
    Reproduit exactement la formule du tableur FormuleBord :
      gdalwarp -te (lon-0.1) (lat-0.1) (lon+1.1) (lat+1.1)"""
    return (lon - debord, lat - debord,
            lon + 1 + debord, lat + 1 + debord)


def intersecte(src, tgt):
    """Vrai si les deux emprises se touchent, ne serait-ce que d'un pixel.
    Un contact strictement tangent n'apporte aucun pixel → exclu."""
    return (src[0] < tgt[2] and src[2] > tgt[0] and
            src[1] < tgt[3] and src[3] > tgt[1])


def assainir_altitudes(arr, nodata=None):
    """Remplace par _NODATA toute valeur qui n'est pas une altitude.

    Fonction PURE (numpy seulement) : entièrement simulable sans
    rasterio. Retourne (tableau float32 assaini, nombre de valeurs
    remplacées). Le tableau reçu n'est jamais modifié.

    Sont considérées comme inexploitables :
      - NaN et infinis ;
      - toute valeur hors [_ALT_MIN, _ALT_MAX] : -32767, -9999,
        -3.4e38, 32767… ;
      - la valeur NoData déclarée par le fichier, si elle est dans les
        bornes (certains DEM déclarent 0 ou -1).

    Après passage, fill_nodata / merge peuvent faire leur travail :
    un trou reste un trou au lieu de devenir une fausse altitude.
    """
    import numpy as np
    a = np.array(arr, dtype="float32", copy=True)
    fini = np.isfinite(a)
    mauvais = ~fini
    mauvais |= fini & ((a < _ALT_MIN) | (a > _ALT_MAX))
    if nodata is not None:
        try:
            nd = float(nodata)
            if np.isfinite(nd) and _ALT_MIN <= nd <= _ALT_MAX:
                # Tolérance : le NoData déclaré peut ne pas être
                # représentable exactement en float32.
                mauvais |= fini & (np.abs(a - np.float32(nd)) <= 1e-3)
        except (TypeError, ValueError):
            pass
    nb = int(mauvais.sum())
    if nb:
        a[mauvais] = _NODATA
    return a, nb


def maj_cfg_lignes(lignes, chemin):
    """Remplace (ou ajoute) custom_dem sans toucher aux autres lignes."""
    out = []
    trouve = False
    for l in lignes:
        if l.startswith("custom_dem="):
            out.append("custom_dem=%s\n" % chemin)
            trouve = True
        else:
            out.append(l)
    if not trouve:
        out.append("custom_dem=%s\n" % chemin)
    return out


def ecrire_custom_dem(cfg_path, chemin_tif):
    """Écrit custom_dem dans le cfg de la tuile. Le cfg est créé s'il
    n'existe pas. Aucune autre clé n'est touchée."""
    lignes = []
    if os.path.isfile(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            lignes = f.readlines()
    lignes = maj_cfg_lignes(lignes, chemin_tif)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(lignes)


def lister_sources(dossier, sortie_exclue=None):
    """Fichiers raster du dossier de la tuile, liens relatifs compris.
    Le fichier de sortie déjà présent est exclu (pas d'auto-fusion)."""
    res = []
    if not dossier or not os.path.isdir(dossier):
        return res
    for f in sorted(os.listdir(dossier)):
        if f.startswith("."):
            continue
        if sortie_exclue and f == sortie_exclue:
            continue
        p = os.path.join(dossier, f)
        # os.path.isfile suit les liens symboliques relatifs.
        if os.path.isfile(p) and _est_fichier_raster(p):
            res.append(p)
    return res


def sources_depuis_stock(racine, lat, lon, debord=DEBORD_DEFAUT):
    """Compatibilité : ancienne structure imposée <racine>/Altimétrie TIFF.
    Se contente de désigner le dossier de stock puis délègue."""
    stock, _a = chemins_structure(racine)
    return sources_depuis_dossier(stock, lat, lon, debord)


def sources_depuis_dossier(stock, lat, lon, debord=DEBORD_DEFAUT, log=None):
    """Étape B — parcourt le dossier des sources DÉSIGNÉ PAR L'UTILISATEUR
    (sous-dossiers compris) et retourne les fichiers dont l'emprise
    intersecte la tuile élargie. Aucun nom de dossier n'est imposé.

    Nécessite rasterio pour lire les emprises. Les fichiers dont
    l'emprise n'est pas lisible en degrés sont retournés quand même :
    assembler_tuile() refera le test après reprojection.

    log (optionnel) : si fourni, explique pour CHAQUE fichier raster
    pourquoi il est gardé ou écarté — indispensable pour diagnostiquer
    un fichier qui « disparaît » (illisible, CRS, hors emprise…)."""
    def _l(m):
        if log:
            try:
                log(m)
            except Exception:
                pass
    res = []
    if not os.path.isdir(stock):
        return res
    try:
        rasterio = _import_rasterio()[0]
    except Exception:
        return res
    bornes = tile_bounds(lat, lon, debord)
    # followlinks=True : indispensable. L'utilisateur place souvent un
    # LIEN vers son stock réel (plusieurs dizaines de Go) au lieu de
    # dupliquer les données. Sans cette option, os.walk ne descendrait
    # pas dans le lien et ne trouverait aucun fichier.
    vus = set()
    for rep, sous, fichiers in os.walk(stock, followlinks=True):
        # Garde-fou : un lien qui pointerait sur un parent créerait une
        # boucle infinie. On ne visite jamais deux fois le même dossier.
        reel = os.path.realpath(rep)
        if reel in vus:
            sous[:] = []
            continue
        vus.add(reel)
        for f in sorted(fichiers):
            if f.startswith("."):
                continue
            p = os.path.join(rep, f)
            if not _est_fichier_raster(p):
                continue
            try:
                with rasterio.open(p) as ds:
                    b = ds.bounds
                    crs = ds.crs
                if crs is not None and crs.to_epsg() == 4326:
                    if not intersecte((b.left, b.bottom, b.right, b.top),
                                      bornes):
                        _l("      écarté (hors emprise) : %s "
                           "[fichier %.2f %.2f %.2f %.2f]"
                           % (f, b.left, b.bottom, b.right, b.top))
                        continue
                # CRS non 4326 → emprise non comparable ici : on garde,
                # le test définitif est fait après reprojection.
                res.append(p)
                _l("      gardé : %s" % f)
            except Exception as e:
                # NE PLUS ignorer en silence : c'est exactement ce qui
                # cachait pourquoi un gros fichier ne remontait pas.
                _l("      ÉCARTÉ (illisible : %s) : %s" % (e, f))
                continue
                continue
    return res


# ────────────────────────────────────────────────────────────────────
#  Partie 2 — moteur raster (rasterio)
# ────────────────────────────────────────────────────────────────────

def _import_rasterio():
    """Import différé : le module reste chargeable même sans rasterio,
    et la fenêtre affiche alors un message clair au lieu de planter."""
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.merge import merge
    from rasterio.crs import CRS
    return rasterio, calculate_default_transform, reproject, Resampling, merge, CRS


def rasterio_disponible():
    try:
        _import_rasterio()
        return True
    except Exception:
        return False


def _bandes(ds, lignes=_BANDE_LIGNES):
    """Découpe le fichier en bandes horizontales. Mémoire constante."""
    from rasterio.windows import Window
    i = 0
    while i < ds.height:
        h = min(lignes, ds.height - i)
        yield Window(0, i, ds.width, h)
        i += h


def _fichier_sain(src_path):
    """Vrai si le fichier ne contient AUCUNE valeur aberrante.
    Simple lecture, aucune écriture : dans le cas normal (la grande
    majorité des fichiers) rien n'est copié sur le disque."""
    rasterio = _import_rasterio()[0]
    with rasterio.open(src_path) as ds:
        nd = ds.nodata
        for w in _bandes(ds):
            _a, n = assainir_altitudes(ds.read(1, window=w), nd)
            if n:
                return False
    return True


def _assainir_fichier(src_path, dst_path, log=None):
    """Réécrit le fichier bande par bande en remplaçant les valeurs
    aberrantes par _NODATA. La géométrie (emprise, résolution, CRS)
    est conservée à l'identique : seule la valeur des pixels change.
    Le fichier source n'est jamais modifié."""
    rasterio = _import_rasterio()[0]
    total = 0
    with rasterio.open(src_path) as src:
        profil = src.profile.copy()
        profil.update(driver="GTiff", count=1, dtype="float32",
                      nodata=_NODATA, compress="DEFLATE")
        profil.pop("blockxsize", None)
        profil.pop("blockysize", None)
        profil["tiled"] = False
        with rasterio.open(dst_path, "w", **profil) as dst:
            for w in _bandes(src):
                a, n = assainir_altitudes(src.read(1, window=w), src.nodata)
                total += n
                dst.write(a, 1, window=w)
    if log and total:
        log("      %d valeur(s) aberrante(s) neutralisée(s) : %s"
            % (total, os.path.basename(src_path)))
    return dst_path, total


def _source_assainie(src_path, tmp_dir, marque, log=None):
    """Retourne le chemin à utiliser réellement pour la reprojection :
    le fichier d'origine s'il est sain, sinon une copie assainie écrite
    dans tmp_dir. Retourne (chemin, chemin_temporaire_ou_None)."""
    try:
        if _fichier_sain(src_path):
            return src_path, None
    except Exception as e:
        # Un fichier illisible sera de toute façon signalé par la
        # reprojection : on ne bloque pas ici.
        if log:
            log("      Contrôle des valeurs impossible : %s" % e)
        return src_path, None
    tmp_path = os.path.join(tmp_dir, "sain_%s.tif" % marque)
    try:
        _assainir_fichier(src_path, tmp_path, log=log)
    except Exception as e:
        if log:
            log("      Note : assainissement non nécessaire (%s) — on continue." % e)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return src_path, None
    return tmp_path, tmp_path


def _reprojeter(src_path, dst_path, log=None):
    """Reprojette en EPSG:4326 et impose le NoData de sortie.
    Équivaut à : gdalwarp -t_srs EPSG:4326 -dstnodata -99999"""
    (rasterio, calculate_default_transform, reproject,
     Resampling, merge, CRS) = _import_rasterio()

    with rasterio.open(src_path) as src:
        src_crs = src.crs
        if src_crs is None:
            # Aucun CRS déclaré (cas des .asc IGN bruts) → repli Lambert-93.
            src_crs = CRS.from_string(_CRS_REPLI)
            if log:
                log("      CRS absent — repli %s : %s"
                    % (_CRS_REPLI, os.path.basename(src_path)))

        dst_crs = CRS.from_epsg(4326)
        transform, width, height = calculate_default_transform(
            src_crs, dst_crs, src.width, src.height, *src.bounds)

        profil = src.profile.copy()
        profil.update(driver="GTiff", crs=dst_crs, transform=transform,
                      width=width, height=height, nodata=_NODATA,
                      dtype="float32", count=1, compress="DEFLATE")
        profil.pop("blockxsize", None)
        profil.pop("blockysize", None)
        if width >= 256 and height >= 256:
            profil["tiled"] = True
        else:
            profil["tiled"] = False

        with rasterio.open(dst_path, "w", **profil) as dst:
            reproject(source=rasterio.band(src, 1),
                      destination=rasterio.band(dst, 1),
                      src_transform=src.transform, src_crs=src_crs,
                      src_nodata=src.nodata,
                      dst_transform=transform, dst_crs=dst_crs,
                      dst_nodata=_NODATA,
                      resampling=Resampling.bilinear)
    return dst_path


def _fenetre_pixels(bornes, left, top, px_x, px_y, width, height):
    """Calcule la fenêtre de pixels (col_off, row_off, ncols, nrows) d'un
    raster 4326 (nord en haut) correspondant à l'emprise géographique
    `bornes` = (ouest, sud, est, nord).

    left/top = coin haut-gauche du fichier (degrés) ; px_x/px_y = taille
    d'un pixel en degrés (valeurs positives) ; width/height = dimensions
    du fichier en pixels.

    Retourne None si l'emprise ne recouvre pas le fichier. Fonction PURE
    (aucune dépendance rasterio) : c'est le calcul décisif du découpage,
    donc il est testé à part avec de vrais chiffres. Une erreur ici lirait
    les mauvais pixels — d'où le test dédié."""
    import math
    w, s, e, n = bornes
    right = left + width * px_x
    bottom = top - height * px_y
    # Intersection géographique fichier ∩ emprise demandée.
    iw = max(w, left)
    ie = min(e, right)
    isn = max(s, bottom)
    inn = min(n, top)
    if ie <= iw or inn <= isn:
        return None
    col_off = int((iw - left) / px_x)
    row_off = int((top - inn) / px_y)
    col_end = int(math.ceil((ie - left) / px_x))
    row_end = int(math.ceil((top - isn) / px_y))
    col_off = max(0, min(col_off, width))
    row_off = max(0, min(row_off, height))
    col_end = max(0, min(col_end, width))
    row_end = max(0, min(row_end, height))
    ncols = col_end - col_off
    nrows = row_end - row_off
    if ncols <= 0 or nrows <= 0:
        return None
    return (col_off, row_off, ncols, nrows)


def _decouper_fenetre_4326(src_path, dst_path, bornes, log=None):
    """Découpe un fichier DÉJÀ en EPSG:4326 (nord en haut) à l'emprise
    `bornes`, en ne lisant QUE la fenêtre de pixels correspondante, par
    blocs de lignes (mémoire constante). AUCUNE reprojection : le fichier
    est déjà en 4326.

    Indispensable pour les très gros fichiers pays (plusieurs dizaines de
    Go, ex. Allemagne/Suisse Sonny) : on ne peut pas les charger en entier.
    Reproduit le `gdalwarp -te` de la procédure QGIS. Les valeurs aberrantes
    sont neutralisées au passage (comme à la reprojection). Retourne
    dst_path, ou None si aucun recouvrement."""
    rasterio = _import_rasterio()[0]
    from rasterio.windows import Window
    with rasterio.open(src_path) as src:
        t = src.transform
        left, top = t.c, t.f
        px_x, px_y = abs(t.a), abs(t.e)
        fen = _fenetre_pixels(bornes, left, top, px_x, px_y,
                              src.width, src.height)
        if fen is None:
            return None
        col_off, row_off, ncols, nrows = fen
        window = Window(col_off, row_off, ncols, nrows)
        win_transform = src.window_transform(window)
        profil = src.profile.copy()
        profil.update(driver="GTiff", height=nrows, width=ncols,
                      transform=win_transform, count=1, dtype="float32",
                      nodata=_NODATA, compress="DEFLATE")
        profil.pop("blockxsize", None)
        profil.pop("blockysize", None)
        profil["tiled"] = (ncols >= 256 and nrows >= 256)
        src_nodata = src.nodata
        with rasterio.open(dst_path, "w", **profil) as dst:
            # Lecture/écriture par blocs de lignes : la mémoire reste
            # constante quelle que soit la taille du fichier source.
            r = 0
            while r < nrows:
                h = min(_BANDE_LIGNES, nrows - r)
                sub = Window(col_off, row_off + r, ncols, h)
                arr = src.read(1, window=sub)
                arr, _n = assainir_altitudes(arr, src_nodata)
                dst.write(arr, 1, window=Window(0, r, ncols, h))
                r += h
    if log:
        log("      découpe fenêtre 4326 : %d x %d px" % (ncols, nrows))
    return dst_path


def assembler_tuile(lat, lon, dossier_tuile, debord=DEBORD_DEFAUT,
                    log=None, sources=None):
    """Assemble le DEM de la tuile. Retourne le chemin du .tif produit.

    Enchaînement, identique à la procédure manuelle :
      1) sélection des sources qui intersectent la tuile élargie
      2) reprojection EPSG:4326 + NoData -99999
      3) fusion (merge) bornée à l'emprise élargie
      4) écriture de <tuile>.tif dans le dossier de la tuile
    """
    import tempfile
    import shutil

    (rasterio, calculate_default_transform, reproject,
     Resampling, merge, CRS) = _import_rasterio()

    def _log(m):
        if log:
            log(m)

    cle = tile_key(lat, lon)
    nom_sortie = cle + ".tif"
    sortie = os.path.join(dossier_tuile, nom_sortie)
    bornes = tile_bounds(lat, lon, debord)

    _log("   [DEM] Tuile %s — emprise %.3f %.3f %.3f %.3f (débord %.3f°)"
         % (cle, bornes[0], bornes[1], bornes[2], bornes[3], debord))

    if sources is None:
        sources = lister_sources(dossier_tuile, sortie_exclue=nom_sortie)
    if not sources:
        raise RuntimeError("Aucun fichier altimétrique dans le dossier "
                           "de la tuile.")

    tmp = tempfile.mkdtemp(prefix="o4_dem_")
    reprojetes = []
    ignorees = []
    try:
        # ── 1 + 2 : lecture, test d'intersection, reprojection ────────
        for i, s in enumerate(sources):
            nom = os.path.basename(s)
            try:
                with rasterio.open(s) as ds:
                    b = ds.bounds
                    crs = ds.crs
                    if crs is not None and crs.to_epsg() == 4326:
                        emprise = (b.left, b.bottom, b.right, b.top)
                    else:
                        # Emprise inconnue en degrés avant reprojection :
                        # on ne peut pas trancher ici → on reprojette puis
                        # on teste. Marqué par emprise=None.
                        emprise = None
            except Exception as e:
                ignorees.append((nom, "illisible : %s" % e))
                _log("      IGNORÉ (illisible) : %s" % nom)
                continue

            if emprise is not None and not intersecte(emprise, bornes):
                ignorees.append((nom, "hors emprise %.3f %.3f %.3f %.3f"
                                 % emprise))
                _log("      IGNORÉ (hors emprise) : %s" % nom)
                continue

            dst = os.path.join(tmp, "r%03d.tif" % i)
            if emprise is not None:
                # Source DÉJÀ en 4326 (Sonny, gros fichiers pays…) : on
                # DÉCOUPE seulement la fenêtre de la tuile, sans reprojeter
                # ni lire le fichier entier. Indispensable pour les fichiers
                # de dizaines de Go. Le découpage neutralise aussi les
                # valeurs aberrantes, donc pas de _source_assainie ici
                # (qui lirait tout le fichier).
                try:
                    res = _decouper_fenetre_4326(s, dst, bornes, log=_log)
                except Exception as e:
                    ignorees.append((nom, "découpe : %s" % e))
                    _log("      IGNORÉ (découpe) : %s" % nom)
                    continue
                if res is None:
                    ignorees.append((nom, "hors emprise (découpe)"))
                    _log("      IGNORÉ (hors emprise) : %s" % nom)
                    continue
            else:
                # Source NON 4326 (IGN .asc en Lambert-93…) : assainissement
                # complet + reprojection, comme avant (fichiers de taille
                # raisonnable, un département).
                src_reel, a_effacer = _source_assainie(s, tmp, "a%03d" % i,
                                                       log=_log)
                try:
                    _reprojeter(src_reel, dst, log=_log)
                except Exception as e:
                    ignorees.append((nom, "reprojection : %s" % e))
                    _log("      IGNORÉ (reprojection) : %s" % nom)
                    continue
                finally:
                    if a_effacer:
                        try:
                            os.remove(a_effacer)
                        except Exception:
                            pass

            # Second test après reprojection (cas emprise inconnue).
            with rasterio.open(dst) as ds:
                b = ds.bounds
                if not intersecte((b.left, b.bottom, b.right, b.top),
                                  bornes):
                    ignorees.append(
                        (nom, "hors emprise après reprojection "
                              "%.3f %.3f %.3f %.3f"
                              % (b.left, b.bottom, b.right, b.top)))
                    _log("      IGNORÉ (hors emprise) : %s" % nom)
                    continue

            reprojetes.append(dst)
            _log("      RETENU : %s" % nom)

        if not reprojetes:
            detail = "\n".join("   • %s : %s" % (n, r) for n, r in ignorees)
            raise RuntimeError(
                "Aucune source ne recouvre cette tuile.\n"
                "Emprise cherchée : %.3f %.3f %.3f %.3f\n"
                "%d fichier(s) écarté(s) :\n%s"
                % (bornes[0], bornes[1], bornes[2], bornes[3],
                   len(ignorees), detail or "   (aucun)"))

        # ── 3 : fusion bornée à l'emprise élargie ─────────────────────
        _log("   [DEM] Fusion de %d source(s)…" % len(reprojetes))
        ouverts = [rasterio.open(p) for p in reprojetes]
        try:
            mosaic, out_transform = merge(ouverts, bounds=bornes,
                                          nodata=_NODATA)
            profil = ouverts[0].profile.copy()
        finally:
            for o in ouverts:
                try:
                    o.close()
                except Exception:
                    pass

        profil.update(driver="GTiff", height=mosaic.shape[1],
                      width=mosaic.shape[2], transform=out_transform,
                      count=1, dtype="float32", nodata=_NODATA,
                      compress="DEFLATE")
        profil.pop("blockxsize", None)
        profil.pop("blockysize", None)
        profil["tiled"] = (mosaic.shape[1] >= 256 and mosaic.shape[2] >= 256)

        # ── 4 : écriture ─────────────────────────────────────────────
        tmp_out = os.path.join(tmp, "final.tif")
        with rasterio.open(tmp_out, "w", **profil) as dst:
            dst.write(mosaic[0].astype("float32"), 1)

        # Écriture finale seulement si tout a réussi : un assemblage
        # interrompu ne laisse jamais un .tif partiel à la place du bon.
        shutil.move(tmp_out, sortie)
        _log("   [DEM] Écrit : %s" % sortie)
        return sortie, ignorees
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


def resolution_metres(src_path):
    """Résolution approximative du fichier, en mètres.
    Sert à afficher ce que donnera un ratio de réduction et à empêcher
    de « réduire » une source déjà grossière (Sonny ≈ 20 m) en dessous
    de sa résolution native, ce qui n'apporterait aucune information."""
    rasterio = _import_rasterio()[0]
    with rasterio.open(src_path) as ds:
        rx, ry = abs(ds.res[0]), abs(ds.res[1])
        crs = ds.crs
        lat = (ds.bounds.bottom + ds.bounds.top) / 2.0
        if crs is not None and crs.to_epsg() == 4326:
            # Degrés → mètres, à la latitude médiane du fichier.
            import math
            mx = rx * 111320.0 * max(0.05, math.cos(math.radians(lat)))
            my = ry * 110540.0
            return (mx + my) / 2.0
        # CRS projeté (Lambert-93, UTM…) : l'unité est déjà le mètre.
        return (rx + ry) / 2.0


def preparer_pays(dossier_source, fichier_sortie, ratio=0.25,
                  crs_repli=_CRS_REPLI, log=None, stop=None):
    """Chaîne A — prépare le fichier réduit d'un département / pays.

    Équivaut à la procédure Terminal :
        gdalbuildvrt X.vrt *.asc
        gdalwarp -s_srs <CRS> -t_srs EPSG:4326 X.vrt XEPSG.tif
        gdal_translate -outsize <ratio>% <ratio>% XEPSG.tif X-reduit.tif

    DIFFÉRENCE ASSUMÉE : l'ordre est inversé (reprojection + réduction
    dalle par dalle, PUIS assemblage). Le résultat est identique, mais la
    mémoire reste constante : un département IGN en 1 m représente des
    dizaines de Go et ne peut pas être assemblé en mémoire.

    Le CRS source est LU dans chaque fichier ; crs_repli ne sert que pour
    les fichiers qui n'en déclarent aucun (cas des .asc IGN bruts, d'où
    le -s_srs EPSG:2154 de la procédure manuelle).
    """
    import tempfile
    import shutil

    (rasterio, calculate_default_transform, reproject,
     Resampling, merge, CRS) = _import_rasterio()
    from rasterio.transform import Affine

    def _log(m=""):
        if log:
            log(m)

    if not os.path.isdir(dossier_source):
        raise RuntimeError("Dossier source introuvable : %s" % dossier_source)
    ratio = max(0.01, min(_RATIO_MAX, float(ratio)))

    sources = []
    for rep, _d, fichiers in os.walk(dossier_source, followlinks=True):
        for f in sorted(fichiers):
            if not f.startswith(".") and f.lower().endswith(_EXT_RASTER):
                sources.append(os.path.join(rep, f))
    if not sources:
        raise RuntimeError("Aucun fichier altimétrique dans :\n%s"
                           % dossier_source)

    _log("   [PREP] %d fichier(s) source(s), ratio %.0f %%"
         % (len(sources), ratio * 100))

    tmp = tempfile.mkdtemp(prefix="o4_prep_")
    reduits = []
    ignorees = []
    try:
        dst_crs = CRS.from_epsg(4326)
        for i, src_path in enumerate(sources):
            if stop is not None and stop():
                raise RuntimeError("Préparation interrompue par "
                                   "l'utilisateur.")
            nom = os.path.basename(src_path)
            # Même garde-fou qu'à l'assemblage : une dalle qui contient
            # une valeur de remplissage non déclarée contaminerait, via
            # le rééchantillonnage « average », tous les pixels réduits
            # de son voisinage.
            src_reel, a_effacer = _source_assainie(src_path, tmp,
                                                   "b%05d" % i, log=_log)
            try:
                with rasterio.open(src_reel) as src:
                    src_crs = src.crs
                    if src_crs is None:
                        src_crs = CRS.from_string(crs_repli)
                    transform, width, height = calculate_default_transform(
                        src_crs, dst_crs, src.width, src.height,
                        *src.bounds)
                    # Réduction : on applique le ratio à la grille de
                    # sortie, exactement comme gdal_translate -outsize.
                    w2 = max(1, int(round(width * ratio)))
                    h2 = max(1, int(round(height * ratio)))
                    t2 = transform * Affine.scale(width / float(w2),
                                                  height / float(h2))
                    profil = src.profile.copy()
                    profil.update(driver="GTiff", crs=dst_crs,
                                  transform=t2, width=w2, height=h2,
                                  count=1, dtype="float32",
                                  nodata=_NODATA, compress="DEFLATE")
                    profil.pop("blockxsize", None)
                    profil.pop("blockysize", None)
                    profil["tiled"] = (w2 >= 256 and h2 >= 256)
                    dst_path = os.path.join(tmp, "p%05d.tif" % i)
                    with rasterio.open(dst_path, "w", **profil) as dst:
                        reproject(
                            source=rasterio.band(src, 1),
                            destination=rasterio.band(dst, 1),
                            src_transform=src.transform, src_crs=src_crs,
                            src_nodata=src.nodata,
                            dst_transform=t2, dst_crs=dst_crs,
                            dst_nodata=_NODATA,
                            # average : moyenne des pixels regroupés.
                            # Sur un MNT c'est nettement meilleur que le
                            # plus proche voisin, qui crée des marches.
                            resampling=(Resampling.average if ratio < 1.0
                                        else Resampling.bilinear))
                reduits.append(dst_path)
            except Exception as e:
                ignorees.append((nom, str(e)))
                _log("      IGNORÉ : %s (%s)" % (nom, e))
                continue
            finally:
                if a_effacer:
                    try:
                        os.remove(a_effacer)
                    except Exception:
                        pass
            if (i + 1) % 10 == 0 or i + 1 == len(sources):
                _log("      %d / %d traité(s)" % (i + 1, len(sources)))

        if not reduits:
            detail = "\n".join("   • %s : %s" % (n, r) for n, r in ignorees)
            raise RuntimeError("Aucun fichier exploitable.\n%s" % detail)

        _log("   [PREP] Assemblage de %d dalle(s) réduite(s)…"
             % len(reduits))
        ouverts = [rasterio.open(p) for p in reduits]
        try:
            mosaic, out_transform = merge(ouverts, nodata=_NODATA)
            profil = ouverts[0].profile.copy()
        finally:
            for o in ouverts:
                try:
                    o.close()
                except Exception:
                    pass

        profil.update(driver="GTiff", height=mosaic.shape[1],
                      width=mosaic.shape[2], transform=out_transform,
                      count=1, dtype="float32", nodata=_NODATA,
                      compress="DEFLATE")
        profil.pop("blockxsize", None)
        profil.pop("blockysize", None)
        profil["tiled"] = (mosaic.shape[1] >= 256 and mosaic.shape[2] >= 256)

        tmp_out = os.path.join(tmp, "final.tif")
        with rasterio.open(tmp_out, "w", **profil) as dst:
            dst.write(mosaic[0].astype("float32"), 1)
        os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)
        # Écriture atomique : jamais de fichier partiel dans le stock.
        shutil.move(tmp_out, fichier_sortie)
        _log("   [PREP] Écrit : %s" % fichier_sortie)
        return fichier_sortie, ignorees
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ────────────────────────────────────────────────────────────────────
#  Partie 3 — auto-test (validation du moteur sans toucher aux données)
# ────────────────────────────────────────────────────────────────────

def auto_test(log=None):
    """Fabrique des GeoTIFF de test dans un dossier temporaire, exécute
    la chaîne complète et vérifie le résultat. Ne touche à AUCUN fichier
    de Roland. Retourne (ok, rapport)."""
    import tempfile
    import shutil

    lignes = []

    def _l(m):
        lignes.append(m)
        if log:
            log(m)

    # ── Tests de logique pure (toujours exécutables) ─────────────────
    try:
        assert tile_key(46, -3) == "+46-003"
        assert tile_key(49, 7) == "+49+007"
        assert tile_key(-34, 151) == "-34+151"
        _l("[1/7] Nommage des tuiles ................ OK")

        assert tile_bounds(45, 1) == (0.9, 44.9, 2.1, 46.1)
        b = [round(x, 6) for x in tile_bounds(49, 7)]
        assert b == [6.9, 48.9, 8.1, 50.1]
        _l("[2/7] Emprise + débord (formule .ods) ... OK")

        t = tile_bounds(49, 7)
        assert intersecte((5.0, 48.0, 6.9001, 50.0), t)
        assert not intersecte((5.0, 48.0, 6.9, 50.0), t)
        assert not intersecte((10, 49, 11, 50), t)
        _l("[3/7] Règle du pixel de contact ......... OK")

        r = maj_cfg_lignes(["default_zl=17\n", "custom_dem=/vieux.tif\n"],
                           "/neuf.tif")
        assert r[1] == "custom_dem=/neuf.tif\n" and len(r) == 2
        r = maj_cfg_lignes(["default_zl=17\n"], "/neuf.tif")
        assert r[-1] == "custom_dem=/neuf.tif\n"
        _l("[4/7] Écriture custom_dem ............... OK")

        import numpy as _np
        _a = _np.array([[100.0, -32767.0, _np.nan],
                        [-3.4e38, 8000.0, 1e30]], dtype="float32")
        _r, _n = assainir_altitudes(_a, -32767.0)
        assert _n == 4, "valeurs aberrantes mal comptees : %d" % _n
        assert _r[0][0] == 100.0 and _r[1][1] == 8000.0, \
            "une altitude valide a ete detruite"
        assert (_r[0][1] == _NODATA and _r[1][0] == _NODATA
                and _r[1][2] == _NODATA), "remplissage non neutralise"
        assert _np.isnan(_a[0][2]), "le tableau source a ete modifie"
        _r2, _n2 = assainir_altitudes(
            _np.array([[0.0, 50.0]], dtype="float32"), 0.0)
        assert _n2 == 1 and _r2[0][1] == 50.0
        _r3, _n3 = assainir_altitudes(
            _np.array([[0.0, 50.0]], dtype="float32"), None)
        assert _n3 == 0
        _l("[5/7] Neutralisation des DEM douteux .... OK")
    except Exception as e:
        _l("ÉCHEC logique : %s" % e)
        return False, "\n".join(lignes)

    # ── Tests raster (nécessitent rasterio) ──────────────────────────
    if not rasterio_disponible():
        _l("[6/7] rasterio .......................... ABSENT")
        _l("")
        _l("rasterio est introuvable dans le venv d'Ortho4XP.")
        _l("Le moteur d'assemblage ne peut pas fonctionner.")
        return False, "\n".join(lignes)

    (rasterio, calculate_default_transform, reproject,
     Resampling, merge, CRS) = _import_rasterio()
    import numpy as np
    from rasterio.transform import from_origin

    tmp = tempfile.mkdtemp(prefix="o4_dem_test_")
    try:
        # Deux dalles voisines en 4326, NoData -32767, qui se chevauchent
        # et couvrent ensemble la tuile +45+001.
        chemins = []
        for k, (x0, y0) in enumerate([(0.5, 46.5), (1.4, 46.5)]):
            p = os.path.join(tmp, "src%d.tif" % k)
            data = np.full((120, 120), 100.0 + k, dtype="float32")
            data[0, 0] = -32767.0
            prof = dict(driver="GTiff", height=120, width=120, count=1,
                        dtype="float32", crs=CRS.from_epsg(4326),
                        transform=from_origin(x0, y0, 0.01, 0.01),
                        nodata=-32767.0)
            with rasterio.open(p, "w", **prof) as d:
                d.write(data, 1)
            chemins.append(p)

        # Une dalle volontairement hors emprise : doit être ignorée.
        p = os.path.join(tmp, "hors.tif")
        prof = dict(driver="GTiff", height=20, width=20, count=1,
                    dtype="float32", crs=CRS.from_epsg(4326),
                    transform=from_origin(20.0, 60.0, 0.01, 0.01),
                    nodata=-32767.0)
        with rasterio.open(p, "w", **prof) as d:
            d.write(np.full((20, 20), 5.0, dtype="float32"), 1)
        chemins.append(p)

        _l("[6/7] Lecture / reprojection ............ OK")

        sortie, ignorees = assembler_tuile(45, 1, tmp, log=_l,
                                           sources=chemins)
        assert os.path.isfile(sortie), "fichier de sortie absent"
        assert os.path.basename(sortie) == "+45+001.tif"
        assert any(n == "hors.tif" for n, _r in ignorees), \
            "la dalle hors emprise aurait dû être ignorée"

        with rasterio.open(sortie) as d:
            assert d.crs.to_epsg() == 4326, "CRS de sortie incorrect"
            assert abs(d.nodata - _NODATA) < 1e-6, "NoData incorrect"
            bb = d.bounds
            for got, want in ((bb.left, 0.9), (bb.bottom, 44.9),
                              (bb.right, 2.1), (bb.top, 46.1)):
                assert abs(got - want) < 0.02, \
                    "emprise %.4f attendue %.4f" % (got, want)
            arr = d.read(1)
            assert float(arr.max()) > 99.0, "aucune donnée utile fusionnée"
        _l("[7/7] Fusion + écriture + NoData ........ OK")
        _l("")
        _l("Moteur d'assemblage opérationnel.")
        return True, "\n".join(lignes)
    except Exception as e:
        _l("ÉCHEC raster : %s" % e)
        return False, "\n".join(lignes)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ────────────────────────────────────────────────────────────────────
#  Partie 4 — fenêtre
# ────────────────────────────────────────────────────────────────────

def _lire_cfg_valeur(cfg_path, cle):
    try:
        if not os.path.isfile(cfg_path):
            return ""
        with open(cfg_path, "r", encoding="utf-8") as f:
            for l in f:
                if l.startswith(cle + "="):
                    return l.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def open_altimetrie_window(gui):
    """Point d'entrée du module, appelé par le bouton « Altimétrie / DEM ».

    Au premier lancement, un assistant crée la structure imposée. Ensuite,
    le module trouve seul les sources qui recouvrent la tuile.
    """
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import subprocess
    import sys

    # ── Boutons look CustomTkinter (repli ttk conservé) ──────────────────
    #  Convertit les boutons TEXTE au style de la fenêtre principale validée.
    #  Si CustomTkinter est absent, on retombe sur ttk.Button : la fenêtre
    #  marche exactement comme avant. Le CTkButton renvoyé porte une méthode
    #  .state() compatible ttk pour que les appels b.state(["disabled"]) /
    #  b.state(["!disabled"]) déjà en place (Assembler / Préparer)
    #  continuent de fonctionner sans être modifiés.
    try:
        import customtkinter as ctk
        _HAS_CTK = True
    except Exception:
        _HAS_CTK = False

    def _lighten_hex(hexcol, factor):
        try:
            h = hexcol.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
            return "#%02x%02x%02x" % (r, g, b)
        except Exception:
            return hexcol

    def _ctk_button(parent, text=None, command=None, **ttk_kw):
        """Bouton texte look CTk ; repli ttk.Button si CTk absent."""
        if _HAS_CTK:
            try:
                try:
                    import O4_Theme_Manager as _TM2
                    _t2 = _TM2.get_theme()
                except Exception:
                    _t2 = {}
                base = _t2.get("btn_bg", "#4a6b59")
                b = ctk.CTkButton(
                    parent, text=text, command=command,
                    corner_radius=8, border_width=1, height=30,
                    fg_color=base, hover_color=_lighten_hex(base, 1.30),
                    border_color=_t2.get("border", base),
                    text_color=_t2.get("btn_fg", "#ffffff"))

                # .state() compatible ttk : traduit ["disabled"] /
                # ["!disabled"] en configure(state=...). Les appels
                # existants restent inchangés.
                def _state(spec=None, _b=b):
                    if spec is None:
                        return ()
                    try:
                        if "disabled" in spec and "!disabled" not in spec:
                            _b.configure(state="disabled")
                        elif "!disabled" in spec:
                            _b.configure(state="normal")
                    except Exception:
                        pass
                    return ()
                b.state = _state  # type: ignore[attr-defined]

                if "state" in ttk_kw:
                    try:
                        b.configure(state=ttk_kw["state"])
                    except Exception:
                        pass
                # CORRECTIF macOS OBLIGATOIRE : redessin après mise en page.
                b.after_idle(
                    lambda btn=b, c=base: btn.winfo_exists()
                    and btn.configure(fg_color=c))
                return b
            except Exception:
                pass  # échec CTk → repli ttk
        kw = {}
        if text is not None:
            kw["text"] = text
        if command is not None:
            kw["command"] = command
        kw.update(ttk_kw)
        return ttk.Button(parent, **kw)

    try:
        from O4_Lang import tr as _tr
    except Exception:
        def _tr(k):
            return k

    # ── Bilingue FR/EN résolu ICI (recette maison identique à
    #    O4_Menu_Avance.py / O4_Extent_Generator.py). Sert aux libellés
    #    des NOUVEAUX dossiers et boutons. Toute langue autre que FR
    #    retombe volontairement sur EN. Français = repli garanti :
    #    si O4_Lang est absent, on affiche le français. Aucun fichier
    #    O4_Lang_* n'est touché.
    try:
        from O4_Lang import current_lang as _current_lang
    except Exception:
        def _current_lang():
            return "FR"

    def _lang_code():
        try:
            code = (_current_lang() or "FR").upper()
        except Exception:
            code = "FR"
        return "EN" if code == "EN" else "FR"

    def _L(fr, en):
        """Libellé bilingue : EN si langue active = anglais, FR sinon."""
        return en if _lang_code() == "EN" else fr

    import O4_File_Names as FNAMES

    def _app_cfg():
        return os.path.join(FNAMES.Ortho4XP_dir, "Ortho4XP.cfg")

    def _cfg_get(cle):
        return _lire_cfg_valeur(_app_cfg(), cle)

    def _cfg_set(cle, valeur):
        try:
            p = _app_cfg()
            lignes = []
            trouve = False
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.startswith(cle + "="):
                            lignes.append("%s=%s\n" % (cle, valeur))
                            trouve = True
                        else:
                            lignes.append(l)
            if not trouve:
                lignes.append("%s=%s\n" % (cle, valeur))
            with open(p, "w", encoding="utf-8") as f:
                f.writelines(lignes)
        except Exception:
            pass

    try:
        lat = int(gui.lat.get() or 0)
        lon = int(gui.lon.get() or 0)
    except Exception:
        messagebox.showerror(_tr("Altimétrie / DEM"),
                             _tr("Latitude / longitude invalides."))
        return

    cle = tile_key(lat, lon)

    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
        BG = _t.get("patch_bg", _t.get("bg", "#0a1a0a"))
        FG = _t.get("patch_fg", _t.get("fg", "#00cc44"))
        FG2 = _t.get("patch_fg2", _t.get("fg_secondary", "#88ffaa"))
        PREV_BG = _t.get("patch_prev_bg", _t.get("canvas_bg", "#050f05"))
    except Exception:
        BG, FG, FG2, PREV_BG = "#0a1a0a", "#00cc44", "#88ffaa", "#050f05"
    FONT = ("TkFixedFont", 11)
    FONT_T = ("TkFixedFont", 13)

    root_ref = None
    try:
        root_ref = tk._default_root
    except Exception:
        pass
    win = tk.Toplevel(root_ref) if root_ref else tk.Toplevel(gui)
    win.title(_tr("Altimétrie / DEM — Ortho4XP V3"))
    win.configure(bg=BG)
    # Rattachée au GUI : elle ne se perd jamais derrière la fenêtre
    # principale après une boîte de dialogue.
    try:
        win.transient(gui)
    except Exception:
        pass
    win.lift()
    win.focus_force()

    def _remonter():
        """Ramène la fenêtre au premier plan. Appelée après chaque boîte
        de dialogue : sous macOS, la fenêtre repasse sinon derrière le
        GUI et donne l'impression de s'être fermée."""
        try:
            win.deiconify()
            win.lift()
            win.focus_force()
            win.attributes("-topmost", True)
            win.after(300, lambda: win.attributes("-topmost", False))
        except Exception:
            pass
    def _saisie(titre, message, parent=None, initialvalue=""):
        """Saisie de texte au thème du projet.

        Remplace tkinter.simpledialog.askstring : ce dernier n'hérite pas
        du thème sombre et affichait un bouton « Cancel » blanc sur fond
        blanc, donc illisible. Même signature que askstring, retourne la
        chaîne saisie ou None si l'utilisateur annule.
        """
        res = {"v": None}
        par = parent if parent is not None else win

        dlg = tk.Toplevel(par)
        dlg.title(titre)
        dlg.configure(bg=BG)
        try:
            dlg.transient(par)
        except Exception:
            pass
        dlg.resizable(False, False)
        dlg.columnconfigure(0, weight=1)

        tk.Label(dlg, text=message, bg=BG, fg=FG, font=FONT,
                 justify="left", anchor="w").grid(
            row=0, column=0, padx=14, pady=(14, 6), sticky="w")

        var = tk.StringVar(value=initialvalue or "")
        ent = tk.Entry(dlg, textvariable=var, width=46, bg=PREV_BG, fg=FG2,
                       bd=0, insertbackground=FG, highlightthickness=1,
                       highlightbackground=FG, highlightcolor=FG,
                       font=("TkFixedFont", 12))
        ent.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

        bar = tk.Frame(dlg, bg=BG)
        bar.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")

        def _ok(_e=None):
            res["v"] = var.get()
            dlg.destroy()

        def _annuler(_e=None):
            res["v"] = None
            dlg.destroy()

        _ctk_button(bar, text=_tr("Valider"), command=_ok).pack(side="left")
        _ctk_button(bar, text=_tr("Annuler"),
                   command=_annuler).pack(side="right")

        dlg.bind("<Return>", _ok)
        dlg.bind("<Escape>", _annuler)
        dlg.protocol("WM_DELETE_WINDOW", _annuler)
        ent.focus_set()
        try:
            ent.selection_range(0, "end")
        except Exception:
            pass
        try:
            dlg.update_idletasks()
            _x = par.winfo_rootx() + max(
                0, (par.winfo_width() - dlg.winfo_reqwidth()) // 2)
            _y = par.winfo_rooty() + 120
            dlg.geometry("+%d+%d" % (_x, _y))
        except Exception:
            pass
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.wait_window()
        return res["v"]

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()

    tk.Label(win, text=_tr("Altimétrie / DEM") + "  —  " + cle,
             font=FONT_T, bg=BG, fg=FG).pack(pady=(12, 2))
    tk.Label(win,
             text=_tr("Structure  →  Préparer les données (une fois par "
                      "pays)  →  Assembler la tuile"),
             font=FONT, bg=BG, fg="#888888").pack(pady=(0, 2))
    lbl_etat = tk.Label(win, text="", font=FONT, bg=BG, fg="#888888")
    lbl_etat.pack(pady=(0, 6))

    # ── Journal ──────────────────────────────────────────────────────
    frm_log = tk.Frame(win, bg=BG)
    frm_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 4))
    sb = tk.Scrollbar(frm_log, bg=BG, troughcolor=BG)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    txt = tk.Text(frm_log, bg=PREV_BG, fg=FG2, font=("TkFixedFont", 10),
                  height=18, width=92, yscrollcommand=sb.set,
                  highlightthickness=1, highlightbackground="#1a4a1a")
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.config(command=txt.yview)

    import queue as _queue
    import threading as _threading
    _fil = _queue.Queue()

    def _log(m=""):
        """Journalise. Appelable depuis n'importe quel thread : si on
        n'est pas dans le thread de l'interface, le message passe par une
        file d'attente vidée par _pomper()."""
        if _threading.current_thread() is _threading.main_thread():
            try:
                txt.insert(tk.END, m + "\n")
                txt.see(tk.END)
                win.update()
            except Exception:
                pass
        else:
            _fil.put(m)

    def _pomper():
        """Vide la file d'attente dans le journal. Rappelée toutes les
        100 ms tant qu'un travail de fond est en cours : l'interface
        reste vivante et l'utilisateur voit l'avancement."""
        try:
            while True:
                txt.insert(tk.END, _fil.get_nowait() + "\n")
                txt.see(tk.END)
        except Exception:
            pass

    def _etat(m, couleur="#888888"):
        # L'utilisateur n'est JAMAIS laissé sans information : chaque
        # opération annonce son début et sa fin.
        try:
            lbl_etat.config(text=m, fg=couleur)
            win.update()
        except Exception:
            pass

    _boutons = []
    _travail = [False]
    _anim = [0]

    def _animer(message):
        """Indicateur d'activité : l'utilisateur n'a jamais l'impression
        que l'application est figée."""
        if not _travail[0]:
            return
        _anim[0] = (_anim[0] + 1) % 4
        _etat(message + " " + ("." * _anim[0]).ljust(3), FG)
        _pomper()
        win.after(400, lambda: _animer(message))

    # ── STRUCTURE À 4 DOSSIERS ───────────────────────────────────────
    # Chaque dossier a sa variable et son bouton. Tous mémorisés dans
    # Ortho4XP.cfg. Aucun nom n'est imposé : l'utilisateur peut pointer
    # ses propres dossiers, mais les boutons créent/ouvrent par défaut la
    # structure Altimétrie/ standard.
    #   _sonny  = Données Sonny/<Pays>   (Sonny isolé, va direct à l'assemblage)
    #   _asc    = ASC brut/<Pays>        (brut IGN + étranger, temporaire)
    #   _epsg   = EPSG réduit/<Pays>     (sorties de « Préparer »)
    #   _sortie = Assemblage tuile       (sortie de « Assembler », rangée par tuile)
    _sonny = [_cfg_get(CFG_SONNY)]
    _asc = [_cfg_get(CFG_ASC)]
    _epsg = [_cfg_get(CFG_EPSG)]
    _sortie = [_cfg_get(CFG_TILEOUT) or _cfg_get(CFG_SORTIE)]
    # _stock conservé UNIQUEMENT pour compatibilité interne (repli) : il
    # pointe sur EPSG réduit, le dossier des sources préparées.
    _stock = [_epsg[0]]
    _dossier_tuile = [""]
    _src_var = tk.StringVar()
    _out_var = tk.StringVar()
    _sonny_var = tk.StringVar()
    _asc_var = tk.StringVar()

    def _maj_bandeaux():
        """Rappel permanent des dossiers, en bas de la fenêtre."""
        _sonny_var.set(_sonny[0] or _L("(non configuré)", "(not set)"))
        _asc_var.set(_asc[0] or _L("(non configuré)", "(not set)"))
        _src_var.set(_epsg[0] or _L("(non configuré)", "(not set)"))
        _out_var.set(os.path.join(_sortie[0], cle) if _sortie[0]
                     else _L("(non configurée)", "(not set)"))
        _stock[0] = _epsg[0]  # garde le repli interne synchronisé

    # Reprise d'une ancienne configuration (2 dossiers) : on ne perd rien.
    # L'ancien « stock » devient EPSG réduit, l'ancienne « sortie » devient
    # Assemblage tuile. L'utilisateur pourra repointer proprement ensuite.
    if not _epsg[0] and _cfg_get(CFG_STOCK):
        _epsg[0] = _cfg_get(CFG_STOCK)
        _stock[0] = _epsg[0]
    if not _sortie[0]:
        _anc_r = _cfg_get(CFG_RACINE)
        _anc_p = _cfg_get(CFG_PAYS)
        if _anc_r and os.path.isdir(_anc_r):
            _s_anc, _a_anc = chemins_structure(_anc_r)
            _cand_a = os.path.join(_a_anc, PREFIXE_PAYS_ASSEMBLE + _anc_p) \
                if _anc_p else _a_anc
            _sortie[0] = _cand_a if os.path.isdir(_cand_a) else _a_anc
            _cfg_set(CFG_TILEOUT, _sortie[0])

    # ════════════════════════════════════════════════════════════════
    #  NOUVELLE STRUCTURE À 4 DOSSIERS — fonctions des boutons
    # ════════════════════════════════════════════════════════════════

    def _racine4():
        """Déduit la racine <...>/Altimétrie à partir de n'importe lequel
        des 4 dossiers déjà connus. Retourne la racine ou None."""
        for v in (_epsg[0], _asc[0], _sonny[0], _sortie[0]):
            r = racine_depuis_dossier4(v)
            if r and os.path.isdir(os.path.join(r, DOSSIER_RACINE)) \
                    or (r and os.path.basename(os.path.normpath(r))
                        == DOSSIER_RACINE):
                return r
            if r:
                return r
        return None

    def _appliquer_pays(racine, pays):
        """Pointe _sonny/_asc/_epsg sur <racine>/<dossier>/<pays> et _sortie
        sur <racine>/Assemblage tuile. Mémorise dans le cfg."""
        sonny, asc, epsg, assemble = chemins_structure4(racine)
        _sonny[0] = os.path.join(sonny, pays) if pays else sonny
        _asc[0] = os.path.join(asc, pays) if pays else asc
        _epsg[0] = os.path.join(epsg, pays) if pays else epsg
        _sortie[0] = assemble
        _cfg_set(CFG_SONNY, _sonny[0])
        _cfg_set(CFG_ASC, _asc[0])
        _cfg_set(CFG_EPSG, _epsg[0])
        _cfg_set(CFG_TILEOUT, _sortie[0])
        _maj_bandeaux()

    def _creer_structure4_gui():
        """Bouton « Créer la structure » : crée les 4 dossiers Altimétrie/
        sur le disque choisi, avec un premier pays, et pointe tout dessus."""
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            _L("Choisissez le disque ou le dossier où créer votre "
               "organisation Altimétrie (un disque externe convient).",
               "Choose the disk or folder where your Altimetry structure "
               "will be created (an external disk is fine)."), parent=win)
        _remonter()
        base = filedialog.askdirectory(
            parent=win,
            title=_L("Où créer l'organisation Altimétrie",
                     "Where to create the Altimetry structure"))
        _remonter()
        if not base:
            return False
        # Éviter d'empiler deux racines : si on est déjà dedans, remonter.
        _parts = os.path.normpath(base).split(os.sep)
        if DOSSIER_RACINE in _parts:
            base = os.sep.join(_parts[:_parts.index(DOSSIER_RACINE)]) or os.sep
        pays = _saisie(
            _tr("Altimétrie / DEM"),
            _L("Nom du pays (ex. : France, Suisse, Allemagne) :",
               "Country name (e.g. France, Switzerland, Germany):"),
            parent=win, initialvalue="France")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        _etat(_L("Création de la structure…", "Creating structure…"), FG)
        try:
            racine, sonny, asc, epsg, assemble = creer_structure4(base, pays)
        except Exception as e:
            _etat("")
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()
            return False
        _appliquer_pays(racine, pays)
        _etat(_L("Structure créée.", "Structure created."), FG)
        txt.delete("1.0", tk.END)
        _log(_L("Structure Altimétrie créée :", "Altimetry structure created:"))
        _log("   " + racine)
        _log()
        _log("   • " + DOSSIER_SONNY + "/" + pays + "   "
             + _L("(déposez ici vos .hgt Sonny)", "(put your Sonny .hgt here)"))
        _log("   • " + DOSSIER_ASC + "/" + pays + "   "
             + _L("(déposez ici vos .asc bruts IGN)", "(put your raw IGN .asc here)"))
        _log("   • " + DOSSIER_EPSG + "/" + pays + "   "
             + _L("(fichiers réduits, générés par « Préparer »)",
                  "(reduced files, produced by « Prepare »)"))
        _log("   • " + DOSSIER_TUILE + "/<" + _L("tuile", "tile") + ">   "
             + _L("(tuile finale → custom_dem)", "(final tile → custom_dem)"))
        _remonter()
        return True

    def _ajouter_pays4():
        """Bouton « Ajouter un pays » : crée <pays> dans Données Sonny,
        ASC brut et EPSG réduit (jamais dans Assemblage tuile), et pointe
        les 3 dossiers courants dessus."""
        racine = _racine4()
        if not racine:
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _L("Créez d'abord la structure (bouton « Créer la structure »).",
                   "Create the structure first (« Create structure » button)."),
                parent=win)
            _remonter()
            return False
        pays = _saisie(
            _tr("Altimétrie / DEM"),
            _L("Nom du pays (ex. : France, Suisse, Allemagne) :",
               "Country name (e.g. France, Switzerland, Germany):"),
            parent=win, initialvalue="")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        try:
            creer_structure4(racine, pays)
        except Exception as e:
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()
            return False
        _appliquer_pays(racine, pays)
        _etat(_L("Pays ajouté : ", "Country added: ") + pays, FG)
        _log(_L("Pays ajouté : ", "Country added: ") + pays)
        _remonter()
        return True

    def _pointer_dossier(kind):
        """Boutons-dossiers : OUVRE le dossier concerné DANS la structure
        existante et le mémorise. kind ∈ {'sonny','asc','epsg','tuile'}.
        NE CRÉE JAMAIS l'arborescence : seul « Créer la structure » le fait.
        Si aucune structure n'existe encore, renvoie vers ce bouton."""
        racine = _racine4()
        if not racine or not os.path.isdir(racine):
            # Pas de structure Altimétrie réellement présente sur le disque :
            # on ne crée rien ici (seul « Créer la structure » le fait).
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _L("Aucune structure « Altimétrie » n'existe encore.\n\n"
                   "Cliquez d'abord sur « Créer la structure » : elle crée "
                   "les 4 dossiers d'un coup. Ce bouton sert seulement à "
                   "OUVRIR un dossier déjà créé, jamais à en créer un.",
                   "No « Altimetry » structure exists yet.\n\n"
                   "Click « Create structure » first: it creates the 4 "
                   "folders at once. This button only OPENS an existing "
                   "folder, it never creates one."),
                parent=win)
            _remonter()
            return False
        sonny, asc, epsg, assemble = chemins_structure4(racine)
        depart = {"sonny": sonny, "asc": asc, "epsg": epsg,
                  "tuile": assemble}.get(kind, "")
        # Le dossier de la structure existe déjà (créé par « Créer la
        # structure ») : on l'ouvre, sans jamais en fabriquer un ailleurs.
        if not os.path.isdir(depart):
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _L("Ce dossier de la structure est manquant. Relancez "
                   "« Créer la structure » pour compléter l'arborescence.",
                   "This structure folder is missing. Run « Create "
                   "structure » again to complete the tree."),
                parent=win)
            _remonter()
            return False
        cur = {"sonny": _sonny[0], "asc": _asc[0], "epsg": _epsg[0],
               "tuile": _sortie[0]}.get(kind, "")
        titre = {
            "sonny": _L("Dossier Données Sonny", "Sonny data folder"),
            "asc": _L("Dossier ASC brut", "Raw ASC folder"),
            "epsg": _L("Dossier EPSG réduit", "Reduced EPSG folder"),
            "tuile": _L("Dossier Assemblage tuile", "Tile assembly folder"),
        }.get(kind, "")
        d = filedialog.askdirectory(
            parent=win, title=titre,
            initialdir=(cur if cur and os.path.isdir(cur) else depart))
        _remonter()
        if not d:
            return False
        if kind == "sonny":
            _sonny[0] = d
            _cfg_set(CFG_SONNY, d)
        elif kind == "asc":
            _asc[0] = d
            _cfg_set(CFG_ASC, d)
        elif kind == "epsg":
            _epsg[0] = d
            _cfg_set(CFG_EPSG, d)
        else:
            _sortie[0] = d
            _cfg_set(CFG_TILEOUT, d)
        _maj_bandeaux()
        _etat(_L("Dossier enregistré.", "Folder saved."), FG)
        return True

    def _vider_asc():
        """Bouton « Vider ASC brut » : liste à cocher des départements
        présents dans ASC brut, avec indicateur ✅ déjà réduit / ⚠️ pas
        encore. Suppression UNIQUEMENT des départements cochés, après
        confirmation. Jamais automatique, jamais en bloc."""
        import shutil
        asc_dir = _asc[0]
        if not asc_dir or not os.path.isdir(asc_dir):
            # repli : proposer la racine ASC brut de la structure
            racine = _racine4()
            if racine:
                asc_dir = chemins_structure4(racine)[1]
        if not asc_dir or not os.path.isdir(asc_dir):
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _L("Aucun dossier ASC brut configuré.",
                   "No raw ASC folder configured."), parent=win)
            _remonter()
            return
        deps = departements_asc(asc_dir)
        if not deps:
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _L("Aucun département à vider dans ASC brut.",
                   "No department to clear in raw ASC."), parent=win)
            _remonter()
            return

        dlg = tk.Toplevel(win)
        dlg.title(_L("Vider ASC brut", "Clear raw ASC"))
        dlg.configure(bg=BG)
        try:
            dlg.transient(win)
        except Exception:
            pass
        dlg.columnconfigure(0, weight=1)
        dlg.rowconfigure(1, weight=1)

        tk.Label(dlg,
                 text=_L("Cochez les départements à SUPPRIMER de ASC brut.\n"
                         "✅ = déjà réduit (sûr).   ⚠️ = pas encore réduit "
                         "(à garder).",
                         "Tick the departments to DELETE from raw ASC.\n"
                         "✅ = already reduced (safe).   ⚠️ = not reduced yet "
                         "(keep)."),
                 bg=BG, fg=FG, font=FONT, justify="left", anchor="w",
                 wraplength=560).grid(row=0, column=0, padx=14,
                                      pady=(14, 6), sticky="w")

        cadre = tk.Frame(dlg, bg=PREV_BG, highlightthickness=1,
                         highlightbackground=FG)
        cadre.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="nsew")
        cvs = tk.Canvas(cadre, bg=PREV_BG, highlightthickness=0, height=260)
        sbv = tk.Scrollbar(cadre, orient="vertical", command=cvs.yview)
        inner = tk.Frame(cvs, bg=PREV_BG)
        inner.bind("<Configure>",
                   lambda e: cvs.configure(scrollregion=cvs.bbox("all")))
        cvs.create_window((0, 0), window=inner, anchor="nw")
        cvs.configure(yscrollcommand=sbv.set)
        cvs.pack(side="left", fill="both", expand=True)
        sbv.pack(side="right", fill="y")

        etats = []  # (BooleanVar, nom, chemin, deja_reduit)
        for nom, chemin in deps:
            deja = dept_est_reduit(nom, _epsg[0])
            var = tk.BooleanVar(value=False)
            ligne = tk.Frame(inner, bg=PREV_BG)
            ligne.pack(fill="x", padx=6, pady=1)
            tk.Checkbutton(ligne, variable=var, bg=PREV_BG,
                           activebackground=PREV_BG,
                           selectcolor=PREV_BG).pack(side="left")
            tag = ("✅ " + _L("déjà réduit", "already reduced")) if deja \
                else ("⚠️ " + _L("pas encore réduit", "not reduced yet"))
            coul = FG2 if deja else "#ffaa00"
            tk.Label(ligne, text=nom, bg=PREV_BG, fg=FG,
                     font=("TkFixedFont", 11), anchor="w", width=28,
                     justify="left").pack(side="left")
            tk.Label(ligne, text=tag, bg=PREV_BG, fg=coul,
                     font=("TkFixedFont", 10), anchor="w").pack(side="left")
            etats.append((var, nom, chemin, deja))

        bar = tk.Frame(dlg, bg=BG)
        bar.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")

        def _fermer():
            try:
                dlg.destroy()
            except Exception:
                pass
            _remonter()

        def _supprimer():
            choisis = [(n, c, d) for (v, n, c, d) in etats if v.get()]
            if not choisis:
                messagebox.showinfo(
                    _tr("Altimétrie / DEM"),
                    _L("Aucun département coché.", "No department ticked."),
                    parent=dlg)
                return
            # Double alerte si un département NON réduit est coché.
            non_reduits = [n for (n, c, d) in choisis if not d]
            if non_reduits:
                if not messagebox.askyesno(
                        _L("Attention", "Warning"),
                        _L("Ces départements ne sont PAS encore réduits :\n\n"
                           "{d}\n\nLes supprimer vous obligera à les "
                           "retélécharger. Continuer quand même ?",
                           "These departments are NOT reduced yet:\n\n{d}\n\n"
                           "Deleting them will force you to download them "
                           "again. Continue anyway?").format(
                               d=", ".join(non_reduits)), parent=dlg):
                    return
            if not messagebox.askyesno(
                    _L("Confirmer la suppression", "Confirm deletion"),
                    _L("Supprimer définitivement {n} dossier(s) ?",
                       "Permanently delete {n} folder(s)?").format(
                           n=len(choisis)), parent=dlg):
                return
            n_ok = 0
            for (nom, chemin, _d) in choisis:
                try:
                    shutil.rmtree(chemin)
                    n_ok += 1
                    _log(_L("Supprimé : ", "Deleted: ") + nom)
                except Exception as e:
                    _log(_L("Échec suppression ", "Delete failed ")
                         + nom + " : " + str(e))
            _fermer()
            _etat(_L("{n} dossier(s) supprimé(s).",
                     "{n} folder(s) deleted.").format(n=n_ok), FG)

        _ctk_button(bar, text=_L("Supprimer la sélection", "Delete selection"),
                    command=_supprimer).pack(side="left")
        _ctk_button(bar, text=_tr("Annuler"),
                    command=_fermer).pack(side="right")

        dlg.bind("<Escape>", lambda e: _fermer())
        dlg.protocol("WM_DELETE_WINDOW", _fermer)
        try:
            dlg.update_idletasks()
            _x = win.winfo_rootx() + max(
                0, (win.winfo_width() - dlg.winfo_reqwidth()) // 2)
            _y = win.winfo_rooty() + 100
            dlg.geometry("+%d+%d" % (_x, _y))
            dlg.grab_set()
        except Exception:
            pass

    # ── Assistant : désignation des deux dossiers ────────────────────
    def _choisir_stock():
        """Dossier où l'utilisateur dépose ses altimétries sources."""
        d = filedialog.askdirectory(
            parent=win, initialdir=_stock[0] or os.path.expanduser("~"),
            title=_tr("Dossier de vos altimétries sources (.tif, .asc…)"))
        _remonter()
        if not d:
            return False
        _stock[0] = d
        _cfg_set(CFG_STOCK, d)
        _maj_bandeaux()
        return True

    def _choisir_sortie():
        """Dossier où sera écrit le fichier assemblé de la tuile."""
        d = filedialog.askdirectory(
            parent=win,
            initialdir=_sortie[0] or _stock[0] or os.path.expanduser("~"),
            title=_tr("Dossier de destination des altimétries assemblées"))
        _remonter()
        if not d:
            return False
        _sortie[0] = d
        _cfg_set(CFG_SORTIE, d)
        _maj_bandeaux()
        return True

    def _creer_structure():
        """Premier usage sans organisation existante : crée l'arborescence
        par défaut et renseigne les deux dossiers. Personne n'est obligé
        de s'en servir : ceux qui ont déjà leurs dossiers utilisent les
        boutons « Dossier des sources » et « Dossier de sortie »."""
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            _tr("Choisissez le disque ou le dossier où créer votre "
                "organisation des altimétries (un disque externe "
                "convient)."), parent=win)
        _remonter()
        base = filedialog.askdirectory(
            parent=win,
            title=_tr("Où créer l'organisation des altimétries"))
        _remonter()
        if not base:
            return False
        # Garde-fou : si le dossier choisi est DÉJÀ dans une structure
        # existante, on remonte à sa racine au lieu d'en empiler une
        # seconde (c'est ce qui produisait des chemins en doublon).
        _parts = os.path.normpath(base).split(os.sep)
        if DOSSIER_RACINE in _parts:
            base = os.sep.join(_parts[:_parts.index(DOSSIER_RACINE)]) or os.sep
        pays = _saisie(
            _tr("Altimétrie / DEM"),
            _tr("Nom du pays (ex. : France, Suisse, Allemagne) :"),
            parent=win, initialvalue="France")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        _etat(_tr("Création de la structure…"), FG)
        try:
            racine, stock_pays, assemble_pays = creer_structure(base, pays)
        except Exception as e:
            _etat("")
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()
            return False
        _stock[0] = stock_pays
        _sortie[0] = assemble_pays
        _cfg_set(CFG_STOCK, stock_pays)
        _cfg_set(CFG_SORTIE, assemble_pays)
        _maj_bandeaux()
        _etat(_tr("Structure créée."), FG)
        txt.delete("1.0", tk.END)
        _log(_tr("Structure créée :"))
        _log("   " + racine)
        _log()
        _log(_tr("Dossier des sources :"))
        _log("   " + stock_pays)
        _log(_tr("Dossier de sortie :"))
        _log("   " + assemble_pays)
        _log()
        _log(_tr("Les sources doivent être en EPSG:4326 — X-Plane ne lit"))
        _log(_tr("aucune autre projection. Ortho4XP convertira au besoin,"))
        _log(_tr("mais préparez-les de préférence en 4326."))
        _log()
        _log(_tr("Le résultat assemblé sera écrit dans :"))
        _log("   " + os.path.join(assemble_pays, cle, cle + ".tif"))
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            _tr("Structure créée.\n\nDéposez vos altimétries dans :\n{d}"
                "\n\nFormat requis : EPSG:4326.").format(d=stock_pays),
            parent=win)
        _remonter()
        return True

    def _racine_structure():
        """Déduit la racine <...>/Altimétrie d'une structure DÉJÀ créée,
        à partir du dossier des sources courant. Retourne la racine si
        le dossier courant appartient bien à la structure imposée
        (<racine>/Altimétrie TIFF/…), sinon None (dossiers personnels ou
        aucune structure en place)."""
        s = _stock[0]
        if not s:
            return None
        parts = os.path.normpath(s).split(os.sep)
        if DOSSIER_STOCK in parts:
            i = parts.index(DOSSIER_STOCK)
            racine = os.sep.join(parts[:i]) or os.sep
            if os.path.isdir(os.path.join(racine, DOSSIER_STOCK)):
                return racine
        return None

    def _resoudre_racine():
        """Retrouve la racine <...>/Altimétrie de la structure existante
        sans jamais la recréer : d'abord depuis le dossier des sources,
        sinon depuis le dossier de sortie, sinon en demandant à
        l'utilisateur d'ouvrir son dossier « Altimétrie ». Retourne la
        racine ou None si l'utilisateur annule."""
        r = _racine_structure()
        if r:
            return r
        if _sortie[0]:
            parts = os.path.normpath(_sortie[0]).split(os.sep)
            if DOSSIER_ASSEMBLE in parts:
                i = parts.index(DOSSIER_ASSEMBLE)
                rr = os.sep.join(parts[:i]) or os.sep
                if os.path.isdir(os.path.join(rr, DOSSIER_ASSEMBLE)):
                    return rr
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            _tr("Ouvrez le dossier « Altimétrie » de votre structure."),
            parent=win)
        _remonter()
        base = filedialog.askdirectory(
            parent=win,
            initialdir=_stock[0] or os.path.expanduser("~"),
            title=_tr("Ouvrir la racine Altimétrie"))
        _remonter()
        if not base:
            return None
        parts = os.path.normpath(base).split(os.sep)
        if DOSSIER_RACINE in parts:
            return os.sep.join(parts[:parts.index(DOSSIER_RACINE) + 1])
        if os.path.basename(os.path.normpath(base)) == DOSSIER_RACINE:
            return base
        return os.path.join(base, DOSSIER_RACINE)

    def _ajouter_pays():
        """Bouton « Ajouter un pays ».
        1) Une fenêtre demande le dossier de destination : Altimétrie TIFF
           OU Altimétrie assemble.
        2) Une seconde fenêtre demande le nom du pays.
        3) À la validation, le dossier est créé UNIQUEMENT dans le dossier
           choisi — jamais dans les deux — et devient le dossier courant
           correspondant. L'autre chemin n'est pas modifié.
        La structure de base (« Créer la structure ») n'est jamais recréée
        ici."""
        racine = _resoudre_racine()
        if not racine:
            return False
        # 1) Choix du dossier de destination : TIFF (sources) ou assemble.
        choix = _choix_tiff_assemble(racine)
        _remonter()
        if not choix:
            return False
        cible_txt = DOSSIER_STOCK if choix == "stock" else DOSSIER_ASSEMBLE
        # 2) Saisie du nom du pays.
        pays = _saisie(
            _tr("Altimétrie / DEM"),
            _tr("Nom du pays (ex. : France, Suisse, Allemagne) :")
            + "\n→ " + cible_txt,
            parent=win, initialvalue="")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        # 3) Création dans le SEUL dossier choisi.
        _etat(_tr("Création de la structure…"), FG)
        try:
            pays_dir = creer_pays_dans(racine, pays, choix)
        except Exception as e:
            _etat("")
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()
            return False
        # 4) Le dossier créé devient le dossier courant correspondant ;
        #    l'AUTRE chemin reste inchangé.
        if choix == "stock":
            _stock[0] = pays_dir
            _cfg_set(CFG_STOCK, pays_dir)
        else:
            _sortie[0] = pays_dir
            _cfg_set(CFG_SORTIE, pays_dir)
        _maj_bandeaux()
        _etat(_tr("Structure créée."), FG)
        txt.delete("1.0", tk.END)
        _log(_tr("Pays ajouté :") + " " + pays)
        _log()
        if choix == "stock":
            _log(_tr("Dossier des sources :"))
        else:
            _log(_tr("Dossier de sortie :"))
        _log("   " + pays_dir)
        _remonter()
        return True

    def _choix_tiff_assemble(racine):
        """Ouvre la racine Altimétrie et demande dans lequel des deux
        dossiers de la structure l'utilisateur veut travailler.
        Retourne "stock" (Altimétrie TIFF), "sortie" (Altimétrie assemble)
        ou None si annulation."""
        res = {"v": None}
        dlg = tk.Toplevel(win)
        dlg.title(_tr("Altimétrie / DEM"))
        dlg.configure(bg=BG)
        try:
            dlg.transient(win)
        except Exception:
            pass
        dlg.resizable(False, False)
        dlg.columnconfigure(0, weight=1)
        dlg.columnconfigure(1, weight=1)

        tk.Label(dlg,
                 text=_tr("Dans quel dossier de la structure Altimétrie "
                          "voulez-vous travailler ?"),
                 bg=BG, fg=FG, font=FONT, justify="left",
                 anchor="w", wraplength=520).grid(
            row=0, column=0, columnspan=2, padx=14, pady=(14, 2), sticky="w")
        tk.Label(dlg, text=_tr("Racine :") + " " + racine,
                 bg=BG, fg=FG2, font=("TkFixedFont", 10), justify="left",
                 anchor="w", wraplength=520).grid(
            row=1, column=0, columnspan=2, padx=14, pady=(0, 12), sticky="w")

        def _pick(val):
            res["v"] = val
            try:
                dlg.destroy()
            except Exception:
                pass

        _ctk_button(dlg, text=DOSSIER_STOCK,
                   command=lambda: _pick("stock")).grid(
            row=2, column=0, padx=(14, 7), pady=(0, 6), sticky="ew", ipady=4)
        _ctk_button(dlg, text=DOSSIER_ASSEMBLE,
                   command=lambda: _pick("sortie")).grid(
            row=2, column=1, padx=(7, 14), pady=(0, 6), sticky="ew", ipady=4)
        _ctk_button(dlg, text=_tr("Annuler"),
                   command=lambda: _pick(None)).grid(
            row=3, column=0, columnspan=2, padx=14, pady=(0, 14))

        dlg.bind("<Escape>", lambda e: _pick(None))
        dlg.protocol("WM_DELETE_WINDOW", lambda: _pick(None))
        try:
            dlg.update_idletasks()
            _x = win.winfo_rootx() + max(
                0, (win.winfo_width() - dlg.winfo_reqwidth()) // 2)
            _y = win.winfo_rooty() + 120
            dlg.geometry("+%d+%d" % (_x, _y))
        except Exception:
            pass
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.wait_window()
        return res["v"]

    def _choisir_dans_structure():
        """Bouton « Emplacement TIFF / assemble » : ouvre la racine
        Altimétrie de la structure existante, demande à l'utilisateur s'il
        veut travailler dans Altimétrie TIFF (sources) ou Altimétrie
        assemble (sortie), puis lui laisse désigner le dossier exact
        (un pays, par exemple). Ne redemande PAS le disque si la structure
        est déjà connue. Ne modifie QUE le chemin correspondant au choix,
        jamais l'autre."""
        # 1) Retrouver la racine <...>/Altimétrie sans rien redemander.
        racine = _racine_structure()
        if not racine and _sortie[0]:
            parts = os.path.normpath(_sortie[0]).split(os.sep)
            if DOSSIER_ASSEMBLE in parts:
                i = parts.index(DOSSIER_ASSEMBLE)
                r = os.sep.join(parts[:i]) or os.sep
                if os.path.isdir(os.path.join(r, DOSSIER_ASSEMBLE)):
                    racine = r
        # 2) Structure inconnue : demander d'ouvrir la racine Altimétrie.
        if not racine:
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _tr("Ouvrez le dossier « Altimétrie » de votre structure."),
                parent=win)
            _remonter()
            base = filedialog.askdirectory(
                parent=win,
                initialdir=_stock[0] or os.path.expanduser("~"),
                title=_tr("Ouvrir la racine Altimétrie"))
            _remonter()
            if not base:
                return False
            parts = os.path.normpath(base).split(os.sep)
            if DOSSIER_RACINE in parts:
                racine = os.sep.join(parts[:parts.index(DOSSIER_RACINE) + 1])
            elif os.path.basename(os.path.normpath(base)) == DOSSIER_RACINE:
                racine = base
            else:
                racine = os.path.join(base, DOSSIER_RACINE)
            # Création seulement des dossiers manquants ; aucun fichier
            # existant n'est touché.
            for d in (racine, os.path.join(racine, DOSSIER_STOCK),
                      os.path.join(racine, DOSSIER_ASSEMBLE)):
                os.makedirs(d, exist_ok=True)
        # 3) Demander TIFF ou assemble.
        choix = _choix_tiff_assemble(racine)
        _remonter()
        if not choix:
            return False
        if choix == "stock":
            depart = os.path.join(racine, DOSSIER_STOCK)
            titre = _tr("Dossier de vos altimétries sources (.tif, .asc…)")
        else:
            depart = os.path.join(racine, DOSSIER_ASSEMBLE)
            titre = _tr("Dossier de destination des altimétries assemblées")
        os.makedirs(depart, exist_ok=True)
        # 4) Laisser désigner le dossier exact, ouvert directement dans le
        #    dossier choisi (l'utilisateur peut entrer dans un pays).
        d = filedialog.askdirectory(parent=win, initialdir=depart,
                                    title=titre)
        _remonter()
        if not d:
            return False
        if choix == "stock":
            _stock[0] = d
            _cfg_set(CFG_STOCK, d)
        else:
            _sortie[0] = d
            _cfg_set(CFG_SORTIE, d)
        _maj_bandeaux()
        _etat(_tr("Dossier enregistré."), FG)
        return True

    def _assistant(force=False):
        """Première utilisation : propose de créer la structure à 4
        dossiers. Si l'utilisateur refuse, il pourra pointer ses propres
        dossiers avec les 4 boutons-dossiers."""
        if _un_dossier_source_pret() and _sortie[0] and not force:
            return True
        _neuf = messagebox.askyesno(
            _tr("Altimétrie / DEM"),
            _L("Ortho4XP peut créer pour vous une organisation "
               "« Altimétrie » à 4 dossiers :\n\n"
               "• Données Sonny   (relief Sonny, par pays)\n"
               "• ASC brut        (données IGN/étranger à préparer)\n"
               "• EPSG réduit     (fichiers préparés)\n"
               "• Assemblage tuile (tuiles finales)\n\n"
               "OUI  →  la structure est créée automatiquement.\n"
               "NON  →  vous pointerez vos propres dossiers avec les "
               "boutons.",
               "Ortho4XP can create an « Altimetry » structure with 4 "
               "folders for you:\n\n"
               "• Sonny data     (Sonny relief, per country)\n"
               "• Raw ASC        (IGN/foreign data to prepare)\n"
               "• Reduced EPSG   (prepared files)\n"
               "• Tile assembly  (final tiles)\n\n"
               "YES  →  the structure is created automatically.\n"
               "NO   →  point your own folders with the buttons."),
            parent=win)
        _remonter()
        if _neuf:
            return _creer_structure4_gui()
        # Refus : l'utilisateur pointe au moins un dossier source + la sortie.
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            _L("Utilisez les 4 boutons-dossiers pour pointer vos dossiers "
               "(Données Sonny, ASC brut, EPSG réduit, Assemblage tuile).",
               "Use the 4 folder buttons to point your folders (Sonny data, "
               "Raw ASC, Reduced EPSG, Tile assembly)."), parent=win)
        _remonter()
        return True

    # ── Dossier de sortie de la tuile ────────────────────────────────
    # Le cfg de la tuile doit être EXACTEMENT celui que lit Ortho4XP,
    # c'est-à-dire FNAMES.build_dir(lat, lon, custom_build_dir) +
    # "Ortho4XP_<short_latlon>.cfg" — même calcul que
    # O4_Config_Utils.load_tile_cfg(). L'ancien chemin
    # (Tile_dir/<tuile>/…) désignait un fichier que personne ne lit :
    # custom_dem y était écrit sans jamais apparaître dans le champ
    # « custom_dem » du GUI, qui restait sur une autre altimétrie.
    def _custom_build_dir():
        for _att in ("custom_build_dir_entry", "custom_build_dir"):
            try:
                _v = getattr(gui, _att).get()
                if _v:
                    return _v
            except Exception:
                pass
        return ""

    try:
        _bdir = FNAMES.build_dir(lat, lon, _custom_build_dir())
        tile_cfg = os.path.join(
            _bdir, "Ortho4XP_%s.cfg" % FNAMES.short_latlon(lat, lon))
        # Repli sur le nom générique quand c'est celui qui existe déjà :
        # load_tile_cfg() applique le même repli.
        if not os.path.isfile(tile_cfg) and \
                os.path.isfile(os.path.join(_bdir, "Ortho4XP.cfg")):
            tile_cfg = os.path.join(_bdir, "Ortho4XP.cfg")
    except Exception:
        try:
            tile_cfg = os.path.join(FNAMES.Tile_dir, cle,
                                    "Ortho4XP_%s.cfg" % cle)
        except Exception:
            tile_cfg = ""

    def _dossier_sortie():
        """Dossier où écrire le fichier assemblé de la tuile.

        Le dossier de sortie CHOISI par l'utilisateur est prioritaire :
        le module y crée le sous-dossier au nom de la tuile (+49-002),
        puis y écrit +49-002.tif. Un custom_dem déjà présent dans le cfg
        n'est qu'un repli, pour les tuiles configurées avant que les
        dossiers ne soient désignés — sinon la sortie repartirait vers
        l'altimétrie d'une autre tuile.
        """
        if _sortie[0]:
            return os.path.join(_sortie[0], cle)
        dem = _lire_cfg_valeur(tile_cfg, "custom_dem") if tile_cfg else ""
        if dem and os.path.isdir(os.path.dirname(dem)):
            return os.path.dirname(dem)
        return ""

    _deb_var = None

    def _debord():
        try:
            v = float(_deb_var.get().replace(",", "."))
            if 0 <= v <= 1:
                return v
        except Exception:
            pass
        return DEBORD_DEFAUT

    def _sources():
        """Sources de l'ASSEMBLAGE : tous les fichiers déjà convertis qui
        recouvrent la tuile. On balaie la STRUCTURE entière — tout le
        dossier « EPSG réduit » (tous les pays) ET tout le dossier
        « Données Sonny » (tous les pays) — puis on ne garde que ce qui
        recouvre la tuile élargie. Ainsi une tuile frontalière (Alsace =
        France + Allemagne + Suisse) prend automatiquement les bons
        fichiers, sans dépendre du « pays courant » pointé. Repli : les
        dossiers pointés à la main, puis le dossier de sortie de la tuile."""
        dossiers = []
        racine = _racine4()
        if racine and os.path.isdir(racine):
            _sy, _ac, _ep, _asm = chemins_structure4(racine)
            # EPSG réduit + Données Sonny, à leur RACINE (tous pays) :
            # sources_depuis_dossier descend récursivement dans les
            # sous-dossiers pays et filtre par emprise.
            dossiers = [_ep, _sy]
        else:
            # Pas de structure : on retombe sur les dossiers pointés.
            dossiers = [_epsg[0], _sonny[0]]
        srcs = []
        for dossier in dossiers:
            if dossier and os.path.isdir(dossier):
                srcs += sources_depuis_dossier(dossier, lat, lon, _debord(),
                                               log=_log)
        # Dédoublonnage (un même fichier accessible par deux chemins).
        vus, uniq = set(), []
        for s in srcs:
            rp = os.path.realpath(s)
            if rp not in vus:
                vus.add(rp)
                uniq.append(s)
        srcs = uniq
        origine = _L("EPSG réduit + Données Sonny (toute la structure)",
                     "Reduced EPSG + Sonny data (whole structure)")
        if not srcs:
            d = _dossier_sortie()
            srcs = lister_sources(d, sortie_exclue=cle + ".tif")
            origine = _L("dossier de la tuile", "tile folder")
        return srcs, origine

    def _un_dossier_source_pret():
        """Vrai si des sources d'assemblage sont disponibles : soit la
        structure existe (EPSG réduit / Données Sonny), soit un dossier
        a été pointé à la main."""
        racine = _racine4()
        if racine and os.path.isdir(racine):
            _sy, _ac, _ep, _asm = chemins_structure4(racine)
            if os.path.isdir(_ep) or os.path.isdir(_sy):
                return True
        return bool((_epsg[0] and os.path.isdir(_epsg[0]))
                    or (_sonny[0] and os.path.isdir(_sonny[0])))

    def _rafraichir():
        txt.delete("1.0", tk.END)
        _maj_bandeaux()
        if not _un_dossier_source_pret():
            _etat(_L("Dossiers non configurés.", "Folders not configured."),
                  "#ffaa00")
            _log(_L("Aucun dossier de données n'est configuré.",
                    "No data folder is configured."))
            _log(_L("Cliquez sur « Créer la structure » pour démarrer.",
                    "Click « Create structure » to begin."))
            return
        b = tile_bounds(lat, lon, _debord())
        _log(_L("Tuile", "Tile") + " %s — %s %.3f %.3f %.3f %.3f"
             % (cle, _L("emprise", "extent"), b[0], b[1], b[2], b[3]))
        _log(DOSSIER_SONNY + " : " + (_sonny[0] or _L("(non configuré)",
                                                      "(not set)")))
        _log(DOSSIER_EPSG + " : " + (_epsg[0] or _L("(non configuré)",
                                                    "(not set)")))
        _log(DOSSIER_TUILE + " : " + (_sortie[0] or _L("(non configurée)",
                                                       "(not set)")))
        _log()
        _etat(_L("Recherche des sources…", "Searching sources…"), FG)
        srcs, origine = _sources()
        _etat("")
        if not srcs:
            _etat(_L("Aucune source pour cette tuile.",
                     "No source for this tile."), "#ffaa00")
            _log(_L("Aucun fichier ne recouvre cette tuile.",
                    "No file covers this tile."))
            _log(_L("Préparez vos départements, ou déposez du Sonny, en "
                    "EPSG:4326.",
                    "Prepare your departments, or add Sonny data, in "
                    "EPSG:4326."))
            return
        _log(_L("{n} source(s) trouvée(s) — origine : {o}",
                "{n} source(s) found — from: {o}").format(
                    n=len(srcs), o=origine))
        for s in srcs:
            marque = " (lien)" if os.path.islink(s) else ""
            _log("   • " + os.path.basename(s) + marque)
        _log()
        _log(_L("Cliquer sur « Assembler » pour lancer.",
                "Click « Assemble » to run."))
        _etat(_L("Prêt.", "Ready."), FG)

    # ── Actions ──────────────────────────────────────────────────────
    def _assembler():
        if not rasterio_disponible():
            messagebox.showerror(
                _tr("Altimétrie / DEM"),
                _tr("rasterio est introuvable dans l'installation "
                    "d'Ortho4XP."), parent=win)
            _remonter()
            return
        srcs, _o = _sources()
        if not srcs:
            messagebox.showinfo(_tr("Altimétrie / DEM"),
                                _tr("Aucune source pour cette tuile."),
                                parent=win)
            _remonter()
            return
        dest = _dossier_sortie()
        if not dest:
            messagebox.showinfo(_tr("Altimétrie / DEM"),
                                _tr("Dossiers non configurés."), parent=win)
            _remonter()
            return
        try:
            os.makedirs(dest, exist_ok=True)
        except Exception as e:
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()
            return
        sortie = os.path.join(dest, cle + ".tif")
        # Confirmation de la DESTINATION avant de travailler : un dossier
        # de sortie mémorisé mais devenu faux ferait écrire le fichier
        # ailleurs, et on ne s'en apercevrait qu'à la fin.
        if not messagebox.askyesno(
                _tr("Altimétrie / DEM"),
                _tr("Le fichier assemblé sera écrit ici :\n\n{f}\n\n"
                    "Est-ce le bon emplacement ?\n\n"
                    "NON  →  utilisez le bouton « Dossier de sortie ».")
                .format(f=sortie), parent=win):
            _remonter()
            return
        _remonter()
        if os.path.isfile(sortie):
            if not messagebox.askyesno(
                    _tr("Altimétrie / DEM"),
                    _tr("{f} existe déjà. Le remplacer ?").format(
                        f=cle + ".tif"), parent=win):
                _remonter()
                return
        txt.delete("1.0", tk.END)
        _travail[0] = True
        for b in _boutons:
            try:
                b.state(["disabled"])
            except Exception:
                pass
        _animer(_tr("Assemblage en cours… ne fermez pas la fenêtre"))
        _res = {}

        def _tache():
            # Le travail lourd (reprojection, fusion, écriture) tourne
            # ICI, hors du thread de l'interface : plus de gel, plus de
            # curseur d'attente. Le journal remonte par la file.
            try:
                _res["ok"] = assembler_tuile(lat, lon, dest,
                                             debord=_debord(), log=_log,
                                             sources=srcs)
            except Exception as _e:
                _res["err"] = str(_e)

        th = _threading.Thread(target=_tache, daemon=True)
        th.start()

        def _fin():
            if th.is_alive():
                _pomper()
                win.after(150, _fin)
                return
            _travail[0] = False
            _pomper()
            for b in _boutons:
                try:
                    b.state(["!disabled"])
                except Exception:
                    pass
            if "err" in _res:
                _etat(_tr("Échec."), "#ff4444")
                _log()
                _log(_tr("ÉCHEC :") + " " + _res["err"])
                messagebox.showerror(_tr("Altimétrie / DEM"), _res["err"],
                                     parent=win)
                _remonter()
                return
            chemin, ignorees = _res["ok"]
            if tile_cfg:
                try:
                    os.makedirs(os.path.dirname(tile_cfg), exist_ok=True)
                    ecrire_custom_dem(tile_cfg, chemin)
                    _log()
                    _log(_tr("custom_dem renseigné dans le cfg de la tuile."))
                    _log(tile_cfg)
                except Exception as _e:
                    _log(_tr("custom_dem non écrit :") + " " + str(_e))
            # Le fichier ne suffit pas : si la fenêtre de configuration est
            # déjà ouverte, son champ « custom_dem » garde en mémoire la
            # valeur chargée au départ (une autre altimétrie). On la met
            # à jour directement pour que l'affichage corresponde au cfg.
            try:
                _cw = getattr(gui, "_config_win", None)
                if _cw is not None and _cw.winfo_exists():
                    _cw.v_["custom_dem"].set(chemin)
            except Exception:
                pass
            _etat(_tr("Terminé."), FG)
            _log()
            _log(_tr("TERMINÉ."))
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _tr("Assemblage terminé.\n\n{f}\n\n"
                    "custom_dem est renseigné : la tuile est prête pour "
                    "l'étape mesh.").format(f=chemin), parent=win)
            _remonter()

        win.after(150, _fin)

    def _auto_test():
        txt.delete("1.0", tk.END)
        _etat(_tr("Auto-test en cours…"), FG)
        _log(_tr("Auto-test du moteur d'assemblage"))
        _log(_tr("(aucun de vos fichiers n'est touché)"))
        _log()
        ok, _rap = auto_test(log=_log)
        _log()
        _log("=> " + (_tr("SUCCÈS") if ok else _tr("ÉCHEC")))
        _etat(_tr("Auto-test terminé.") + " "
              + (_tr("SUCCÈS") if ok else _tr("ÉCHEC")),
              FG if ok else "#ff4444")
        messagebox.showinfo(
            _tr("Altimétrie / DEM"),
            (_tr("Auto-test réussi : le moteur d'assemblage fonctionne.")
             if ok else
             _tr("Auto-test en échec — voir le détail dans la fenêtre.")),
            parent=win)
        _remonter()

    # ── QGIS (mémorisé comme GIMP dans la fenêtre Correction) ────────
    def _choisir_qgis():
        if sys.platform == "darwin":
            init_dir, ft = "/Applications", [(_tr("Applications macOS"),
                                              "*.app"),
                                             (_tr("Tous les fichiers"), "*")]
        elif sys.platform.startswith("win"):
            init_dir, ft = "C:\\Program Files", \
                [(_tr("Exécutables Windows"), "*.exe"),
                 (_tr("Tous les fichiers"), "*")]
        else:
            init_dir, ft = "/usr/bin", [(_tr("Tous les fichiers"), "*")]
        p = filedialog.askopenfilename(
            parent=win, title=_tr("Choisir l'application QGIS"),
            initialdir=init_dir, filetypes=ft)
        _remonter()
        if p:
            _cfg_set(CFG_QGIS, p)
            _qgis_var.set(p)
            messagebox.showinfo(_tr("Altimétrie / DEM"),
                                _tr("Application QGIS enregistrée."),
                                parent=win)
            _remonter()

    def _ouvrir_qgis():
        app = _qgis_var.get().strip()
        if not app:
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _tr("Aucune application QGIS définie.\n"
                    "Cliquez d'abord sur « Choisir QGIS »."), parent=win)
            _remonter()
            return
        cible = os.path.join(_dossier_sortie(), cle + ".tif")
        args = [cible] if os.path.isfile(cible) else []
        try:
            if sys.platform == "darwin" and app.endswith(".app"):
                subprocess.Popen(["open", "-a", app] + args)
            else:
                subprocess.Popen([app] + args)
            _etat(_tr("QGIS lancé."), FG)
        except Exception as e:
            messagebox.showerror(_tr("Altimétrie / DEM"), str(e), parent=win)
            _remonter()

    # ── Préparer un pays (chaîne A : brut → EPSG:4326 → réduit) ──────
    def _preparer():
        if not rasterio_disponible():
            messagebox.showerror(
                _tr("Altimétrie / DEM"),
                _tr("rasterio est introuvable dans l'installation "
                    "d'Ortho4XP."), parent=win)
            _remonter()
            return
        # « Préparer » lit dans ASC brut. On ouvre directement ce dossier.
        _memo_src = _cfg_get(CFG_PREP_SRC) or _asc[0] or ""
        if not (_memo_src and os.path.isdir(_memo_src)):
            _memo_src = _asc[0] if (_asc[0] and os.path.isdir(_asc[0])) else ""
        src = filedialog.askdirectory(
            parent=win,
            title=_L("Dossier ASC brut à préparer (.asc, .tif…)",
                     "Raw ASC folder to prepare (.asc, .tif…)"),
            initialdir=_memo_src)
        _remonter()
        if not src:
            return
        _cfg_set(CFG_PREP_SRC, src)
        # Résolution réelle de la source : évite de « réduire » du Sonny
        # (~20 m) en dessous de sa résolution native.
        res_m = None
        try:
            for rep, _d, fs in os.walk(src, followlinks=True):
                for f in sorted(fs):
                    if not f.startswith(".") and \
                            f.lower().endswith(_EXT_RASTER):
                        res_m = resolution_metres(os.path.join(rep, f))
                        break
                if res_m:
                    break
        except Exception:
            res_m = None
        if res_m is None:
            messagebox.showerror(
                _tr("Altimétrie / DEM"),
                _tr("Aucun fichier altimétrique lisible dans ce dossier."),
                parent=win)
            _remonter()
            return

        # L'utilisateur choisit la RÉSOLUTION VOULUE en sortie (en mètres),
        # PAS un pourcentage : une source 1 m, 3 m, 27 m… donne toujours la
        # même sortie (ex. 4 m). Le ratio se calcule tout seul :
        #     ratio = résolution source / résolution voulue.
        # Cible PLUS FINE que la source (ex. Sonny 27 m → 4 m) : autorisé,
        # comme dans QGIS (interpolation bilinéaire). Ça ne crée pas de détail
        # réel — c'est un lissage sur grille plus fine — mais ça donne une
        # grille uniforme (mosaïquable avec du LiDAR déjà en 4 m). Rien codé
        # en dur.
        cible_def = "4"
        rep_cible = _saisie(
            _tr("Altimétrie / DEM"),
            _tr("Résolution source détectée : {r} m\n\n"
                "Résolution VOULUE en sortie, en mètres (ex. 4).\n"
                "Plus GRAND que la source = allègement (moins de points).\n"
                "Plus PETIT que la source = grille plus fine par "
                "interpolation\n(lissage, sans détail supplémentaire — "
                "utile pour une grille uniforme)."
                ).format(r=("%.1f" % res_m)),
            parent=win, initialvalue=cible_def)
        _remonter()
        if not rep_cible:
            return
        try:
            cible_m = float(rep_cible.replace(",", ".")
                            .replace("m", "").replace("M", "").strip())
        except Exception:
            messagebox.showerror(_tr("Altimétrie / DEM"),
                                 _tr("Valeur invalide."), parent=win)
            _remonter()
            return
        if cible_m <= 0:
            messagebox.showerror(_tr("Altimétrie / DEM"),
                                 _tr("Valeur invalide."), parent=win)
            _remonter()
            return
        # ratio = source / voulue. Peut être > 1 (sur-échantillonnage) ; borné
        # par _RATIO_MAX pour la mémoire.
        ratio = max(0.01, min(_RATIO_MAX, res_m / cible_m))
        res_finale = res_m / ratio

        suffixe = "%dM" % int(round(res_finale)) if res_finale >= 1 else "1M"
        nom_def = "%s-%s-reduit.tif" % (os.path.basename(
            os.path.normpath(src)), suffixe)

        # « ENREGISTRER SOUS » — l'utilisateur choisit LUI-MÊME le dossier ET
        # le nom du fichier réduit, exactement comme l'« Exporter → Enregistrer
        # sous » de QGIS. Le dossier proposé par défaut est le dossier de
        # SORTIE configuré (_sortie[0]), plus le dossier source : le fichier
        # réduit ne se retrouve donc plus posé à côté de l'original, ce qui
        # pouvait les faire se mélanger au moment du build. asksaveasfilename
        # gère lui-même la confirmation d'écrasement du système : inutile de la
        # redemander.
        # Sortie de « Préparer » = EPSG réduit (et non Assemblage tuile).
        _dossier_def = _epsg[0] if (_epsg[0]
                                    and os.path.isdir(_epsg[0])) else src
        dest = filedialog.asksaveasfilename(
            parent=win,
            title=_L("Enregistrer le fichier réduit dans EPSG réduit…",
                     "Save the reduced file into Reduced EPSG…"),
            initialdir=_dossier_def,
            initialfile=nom_def,
            defaultextension=".tif",
            filetypes=[("GeoTIFF", "*.tif"),
                       (_tr("Tous les fichiers"), "*")])
        _remonter()
        if not dest:
            return
        if not dest.lower().endswith(".tif"):
            dest += ".tif"
        nom = os.path.basename(dest)

        txt.delete("1.0", tk.END)
        _log(_tr("Préparation :") + " " + src)
        _log(_tr("Résolution source :") + " %.1f m" % res_m)
        _log(_tr("Résolution voulue :") + " %.1f m" % res_finale)
        _log(_tr("Facteur de grille :") + " %.0f %% " % (ratio * 100)
             + (_tr("(interpolation)") if ratio > 1.0
                else _tr("(allègement)") if ratio < 1.0
                else _tr("(identique)")))
        _log(_tr("Destination :") + " " + dest)
        _log()
        _travail[0] = True
        for b in _boutons:
            try:
                b.state(["disabled"])
            except Exception:
                pass
        _animer(_tr("Préparation en cours… ne fermez pas la fenêtre"))
        _res = {}

        def _tache():
            try:
                _res["ok"] = preparer_pays(src, dest, ratio=ratio, log=_log)
            except Exception as _e:
                _res["err"] = str(_e)

        th = _threading.Thread(target=_tache, daemon=True)
        th.start()

        def _fin():
            if th.is_alive():
                _pomper()
                win.after(150, _fin)
                return
            _travail[0] = False
            _pomper()
            for b in _boutons:
                try:
                    b.state(["!disabled"])
                except Exception:
                    pass
            if "err" in _res:
                _etat(_tr("Échec."), "#ff4444")
                _log()
                _log(_tr("ÉCHEC :") + " " + _res["err"])
                messagebox.showerror(_tr("Altimétrie / DEM"), _res["err"],
                                     parent=win)
                _remonter()
                return
            _etat(_tr("Terminé."), FG)
            _log()
            _log(_tr("TERMINÉ."))
            messagebox.showinfo(
                _tr("Altimétrie / DEM"),
                _tr("Fichier préparé :\n\n{f}\n\n"
                    "Il est maintenant dans le stock et sera utilisé "
                    "automatiquement pour les tuiles qu'il "
                    "recouvre.").format(f=_res["ok"][0]), parent=win)
            _remonter()
            _rafraichir()

        win.after(150, _fin)

    # ── Barre du bas ─────────────────────────────────────────────────
    frm_deb = tk.Frame(win, bg=BG)
    frm_deb.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_deb, text=_tr("Débord de chevauchement (°) :"),
             font=FONT, bg=BG, fg=FG).pack(side=tk.LEFT)
    _deb_var = tk.StringVar(value=str(DEBORD_DEFAUT))
    tk.Entry(frm_deb, textvariable=_deb_var, width=8, bg=PREV_BG, fg=FG2,
             insertbackground=FG).pack(side=tk.LEFT, padx=(8, 0))
    tk.Label(frm_deb, text=_tr("(0.1 = 10 % de la tuile sur les 4 côtés)"),
             font=FONT, bg=BG, fg="#888888").pack(side=tk.LEFT, padx=(8, 0))

    _qgis_var = tk.StringVar(value=_cfg_get(CFG_QGIS))
    frm_q = tk.Frame(win, bg=BG)
    frm_q.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_q, text=_tr("QGIS :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_q, textvariable=_qgis_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    # ── Rappel permanent des deux dossiers ───────────────────────────
    # La destination doit être visible AVANT d'assembler, pas découverte
    # après coup dans le message de fin.
    frm_src = tk.Frame(win, bg=BG)
    frm_src.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_src, text=_tr("Sources :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_src, textvariable=_src_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    frm_out = tk.Frame(win, bg=BG)
    frm_out.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_out, text=_tr("Sortie :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_out, textvariable=_out_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    frm_bot = tk.Frame(win, bg=BG)
    def _importer_relief_sonny():
        """Décompresse le ZIP Sonny téléchargé dans hgt/<Pays>/ et renseigne
        custom_dem automatiquement avec le .hgt. Pas d'assemblage TIFF :
        Ortho4XP lit le .hgt directement (comme un DEM pointé à la main)."""
        try:
            import O4_Relief_Sonny_Utils as _RS
            import O4_Relief_Depot_Utils as _DEP
            import O4_Pays_Utils as _PA
        except Exception as _e:
            _log(_tr("Import Sonny : modules absents (%s).") % _e)
            return
        # Emplacement de rangement du .hgt : PRIORITÉ à « Données Sonny » de
        # la structure Altimétrie (cohérent avec « Créer la structure » et le
        # bouton « Données Sonny »). Repli sur l'ancien système UNIQUEMENT si
        # aucune structure n'existe encore.
        _rac_imp = _racine4()
        if _rac_imp:
            _hgtdir = chemins_structure4(_rac_imp)[0]   # Données Sonny
        else:
            _memo = _cfg_get("relief_sonny_dir")
            _etatdep, _hgtdir = _DEP.emplacement_verrouille(_memo, log=_log)
            if _etatdep != "ok" or not _hgtdir:
                messagebox.showinfo(
                    _tr("Import du relief"),
                    _L("Créez d'abord votre structure (bouton « Créer la "
                       "structure ») ou cliquez « Données Sonny » : le relief "
                       "y sera rangé.",
                       "First create your structure (« Create structure ») or "
                       "click « Sonny data »: the relief will be stored "
                       "there."),
                    parent=win)
                _remonter()
                return
        try:
            _lat = int(gui.lat.get() or 0)
            _lon = int(gui.lon.get() or 0)
        except Exception:
            _log(_tr("Import Sonny : tuile courante illisible."))
            return

        _nom = _RS.nom_hgt(_lat, _lon)                 # ex. N46W003
        _pays = _PA.pays_pour_tuile(_lat, _lon)        # ex. France
        # NOUVEAU : le .hgt Sonny est rangé dans « Données Sonny/<Pays> » de
        # la structure Altimétrie (Sonny isolé pour respecter sa licence).
        # Repli sur l'ancien emplacement du dépôt si la structure n'existe
        # pas encore.
        _rac4 = _racine4()
        if _rac4:
            _sonny_root = chemins_structure4(_rac4)[0]
            _dossier_pays = os.path.join(_sonny_root, _pays)
        else:
            _dossier_pays = os.path.join(_hgtdir, _pays)
        try:
            os.makedirs(_dossier_pays, exist_ok=True)
        except Exception as _e:
            _log(_tr("Impossible de créer le dossier pays (%s).") % _e)
            return

        # 1) Repérer le ZIP dans Téléchargements (le bon nom en priorité).
        _zips = _DEP.trouver_zips_sonny()
        _zip = None
        for _z in _zips:
            if _nom.lower() in os.path.basename(_z).lower():
                _zip = _z
                break
        if not _zip and _zips:
            _zip = _zips[0]
        if not _zip:
            _zip = filedialog.askopenfilename(
                parent=win,
                title=_tr("Sélectionnez le fichier ZIP Sonny (%s.zip)") % _nom,
                filetypes=[("ZIP", "*.zip"), ("Tous", "*.*")])
        if not _zip:
            _log(_tr("Import annulé : aucun ZIP trouvé."))
            return

        # 2) Décompresser DIRECTEMENT dans hgt/<Pays>/.
        _log(_tr("Décompression dans %s…") % _dossier_pays)
        _extrait = _DEP.decompresser_zip(_zip, dossier_cible=_dossier_pays,
                                         log=_log)
        if not _extrait:
            _log(_tr("Aucun .hgt valide dans ce ZIP."))
            return

        # 3) Chemin du .hgt final -> custom_dem.
        _hgt_final = os.path.join(_dossier_pays, _nom + ".hgt")
        if not os.path.isfile(_hgt_final):
            _hgts = [f for f in os.listdir(_dossier_pays)
                     if f.lower().endswith(".hgt")]
            if _hgts:
                _hgt_final = os.path.join(_dossier_pays, sorted(_hgts)[0])
            else:
                _log(_tr("Aucun .hgt en place après décompression."))
                return

        # 3bis) Le .hgt est vérifié en place → proposer de supprimer le ZIP.
        #       JAMAIS automatique : on demande, et seulement après avoir
        #       confirmé que le .hgt existe bien (sinon on garderait le ZIP
        #       pour permettre une nouvelle tentative).
        try:
            if _zip and os.path.isfile(_zip) and os.path.isfile(_hgt_final):
                if messagebox.askyesno(
                        _L("Supprimer le ZIP ?", "Delete the ZIP?"),
                        _L("Le relief est en place et vérifié :\n%s\n\n"
                           "Supprimer le fichier ZIP téléchargé ?\n%s",
                           "The relief is in place and verified:\n%s\n\n"
                           "Delete the downloaded ZIP file?\n%s")
                        % (_hgt_final, _zip), parent=win):
                    os.remove(_zip)
                    _log(_L("ZIP supprimé : ", "ZIP deleted: ") + _zip)
                else:
                    _log(_L("ZIP conservé.", "ZIP kept."))
        except Exception as _e:
            _log(_L("ZIP non supprimé : ", "ZIP not deleted: ") + str(_e))

        # 4) Renseigner custom_dem dans le cfg de la tuile (mécanisme identique
        #    à Assembler : même calcul de tile_cfg avec repli Ortho4XP.cfg).
        _cle = tile_key(_lat, _lon)
        try:
            _bdir = FNAMES.build_dir(_lat, _lon, _custom_build_dir())
            _tile_cfg = os.path.join(
                _bdir, "Ortho4XP_%s.cfg" % FNAMES.short_latlon(_lat, _lon))
            if not os.path.isfile(_tile_cfg) and \
                    os.path.isfile(os.path.join(_bdir, "Ortho4XP.cfg")):
                _tile_cfg = os.path.join(_bdir, "Ortho4XP.cfg")
        except Exception:
            try:
                _tile_cfg = os.path.join(FNAMES.Tile_dir, _cle,
                                         "Ortho4XP_%s.cfg" % _cle)
            except Exception:
                _tile_cfg = ""

        if _tile_cfg:
            try:
                os.makedirs(os.path.dirname(_tile_cfg), exist_ok=True)
                ecrire_custom_dem(_tile_cfg, _hgt_final)
                _log(_tr("custom_dem renseigné dans le cfg de la tuile."))
                _log(_tile_cfg)
            except Exception as _e:
                _log(_tr("custom_dem non écrit : ") + str(_e))
                
        # 4bis) Écrire AUSSI custom_dem dans le cfg APP (Ortho4XP.cfg), pour
        #       que « Recharger CFG app » ne restaure pas un ancien relief.
        try:
            _app_cfg_path = os.path.join(FNAMES.Ortho4XP_dir, "Ortho4XP.cfg")
            if os.path.isfile(_app_cfg_path):
                ecrire_custom_dem(_app_cfg_path, _hgt_final)
                _log(_tr("custom_dem renseigné aussi dans le cfg application."))
        except Exception as _e:
            _log(_tr("cfg application non mis à jour : ") + str(_e))

        # 5) Met à jour le champ « custom_dem » du GUI s'il est ouvert
        #    (même mécanisme que Assembler : gui._config_win).
        try:
            _cw = getattr(gui, "_config_win", None)
            if _cw is not None and _cw.winfo_exists():
                _cw.v_["custom_dem"].set(_hgt_final)
        except Exception:
            pass

        messagebox.showinfo(
            _tr("Relief installé"),
            _tr("Relief rangé dans :\n%s\n\n"
                "custom_dem a été renseigné dans les fichiers de "
                "configuration.\n\n"
                "⚠️  IMPORTANT — Pour voir le chemin du relief dans le champ "
                "« custom_dem » :\n"
                "cliquez sur « Charger CFG tuile » (ou « Recharger CFG app »).\n\n"
                "Sans cette action, le champ affichera encore l'ancien relief.\n\n"
                "Vous pourrez ensuite lancer la construction de la tuile.")
            % _dossier_pays,
            parent=win)
        _etat(_tr("Relief Sonny prêt."), FG)
    def _relief_sonny_auto():
        """Mode débutant : relief HD Sonny automatique pour la tuile courante.
        - dalles présentes -> assemblage + custom_dem (silence) ;
        - absentes -> propose l'installation (Oui = guide, Non = relief standard).
        Ne casse jamais : au moindre souci, relief standard."""
        try:
            import O4_Relief_Sonny_Utils as _RS
            import O4_Relief_Orchestrateur_Utils as _ORCH
        except Exception as _e:
            _log(_tr("Relief Sonny : modules absents (%s).") % _e)
            return
        try:
            _lat = int(gui.lat.get() or 0)
            _lon = int(gui.lon.get() or 0)
        except Exception:
            _log(_tr("Relief Sonny : tuile courante illisible."))
            return

        # PROBLÈME 2 — Si le .hgt de cette tuile est DÉJÀ installé, on ne
        # relance pas toute la procédure : on renseigne custom_dem et on sort.
        try:
            import O4_Relief_Depot_Utils as _DEP0
            import O4_Pays_Utils as _PA0
            _nom0 = _RS.nom_hgt(_lat, _lon)
            _pays0 = _PA0.pays_pour_tuile(_lat, _lon)
            # Cherche le .hgt d'abord dans « Données Sonny/<Pays> » de la
            # structure (nouvel emplacement), puis dans l'ancien dépôt.
            _candidats = []
            _rac0 = _racine4()
            if _rac0:
                _candidats.append(os.path.join(
                    chemins_structure4(_rac0)[0], _pays0, _nom0 + ".hgt"))
            _memo0 = _cfg_get("relief_sonny_dir")
            _et0, _hgt0 = _DEP0.emplacement_verrouille(_memo0)
            if _et0 == "ok" and _hgt0:
                _candidats.append(os.path.join(_hgt0, _pays0, _nom0 + ".hgt"))
            for _deja in _candidats:
                if os.path.isfile(_deja):
                    _log(_tr("Relief Sonny déjà installé pour cette tuile : %s")
                         % _deja)
                    _importer_relief_sonny()
                    return
        except Exception:
            pass
        
        # cfg de la tuile (même calcul que le reste du module).
        try:
            _bdir = FNAMES.build_dir(_lat, _lon, _custom_build_dir())
            _cfg = os.path.join(
                _bdir, "Ortho4XP_%s.cfg" % FNAMES.short_latlon(_lat, _lon))
        except Exception:
            _cfg = None

        # Où Sonny cherche/range les .hgt : « Données Sonny » de la structure
        # Altimétrie si elle existe (passé en chemin_choisi à emplacement_gere),
        # sinon l'emplacement par défaut. Cohérent avec « Créer la structure »
        # et le bouton « Données Sonny ».
        _rac_auto = _racine4()
        _sonny_root = chemins_structure4(_rac_auto)[0] if _rac_auto else None
        _dossier = _RS.emplacement_gere(getattr(FNAMES, "Ortho4XP_dir", "."),
                                        chemin_choisi=_sonny_root)
        _tuiledir = _sortie[0] or _dossier

        _res = _ORCH.generer_relief_tuile(
            _lat, _lon, _tuiledir, _cfg, _dossier,
            debord=_debord(),
            assembler=assembler_tuile,
            ecrire_cfg=ecrire_custom_dem,
            log=_log)

        _statut = _res.get("statut")
        if _statut == _ORCH.FAIT:
            _log(_tr("Relief Sonny intégré : %d dalle(s).") % _res.get("dalles", 0))
            _etat(_tr("Relief HD intégré."), FG)
        elif _statut == _ORCH.A_INSTALLER:
            try:
                import O4_Relief_Sonny_Utils as _RS2
                _zipnom = _RS2.nom_hgt(_lat, _lon) + ".zip"
            except Exception:
                _zipnom = "(le fichier de votre zone)"
            _rep = messagebox.askyesno(
                _tr("Relief haute définition"),
                _tr("Un relief haute définition (Sonny) est disponible pour "
                    "cette zone.\n\nSouhaitez-vous l'installer maintenant ?\n\n"
                    "Oui : définir où stocker, puis télécharger le fichier.\n"
                    "Non : continuer avec le relief standard."),
                parent=win)
            if not _rep:
                _log(_tr("Relief standard conservé."))
            else:
                # NOUVEAU : le relief Sonny se range dans « Données Sonny » de
                # la structure Altimétrie. Plus AUCUN disque séparé à définir,
                # plus de clé relief_sonny_dir : on vérifie juste que la
                # structure existe, puis on ouvre le site de téléchargement.
                _rac_inst = _racine4()
                if not _rac_inst:
                    messagebox.showinfo(
                        _tr("Altimétrie / DEM"),
                        _L("Créez d'abord votre structure (bouton « Créer la "
                           "structure ») : le relief Sonny sera rangé dans "
                           "« Données Sonny ».",
                           "First create your structure (« Create structure » "
                           "button): Sonny relief will be stored in "
                           "« Sonny data »."),
                        parent=win)
                    _remonter()
                    return
                messagebox.showinfo(
                    _L("Téléchargement", "Download"),
                    _L("Le site Sonny va s'ouvrir.\n\n"
                       "Sélectionnez votre pays puis téléchargez le fichier :"
                       "\n\n        %s\n\n"
                       "Une fois téléchargé, cliquez « Installer le ZIP "
                       "téléchargé » : il sera rangé dans « Données Sonny ».",
                       "The Sonny site will open.\n\n"
                       "Select your country then download the file:\n\n"
                       "        %s\n\n"
                       "Once downloaded, click « Install downloaded ZIP »: it "
                       "will be stored in « Sonny data ».") % _zipnom,
                    parent=win)
                _remonter()
                try:
                    import webbrowser
                    webbrowser.open("https://sonny.4lima.de")
                except Exception:
                    pass
                _log(_L("Téléchargez %s puis « Installer le ZIP téléchargé ».",
                        "Download %s then « Install downloaded ZIP ».")
                     % _zipnom)
        elif _statut == _ORCH.HORS_ZONE:
            _log(_tr("Hors zone Sonny : relief standard."))
        else:
            _log(_tr("Relief Sonny indisponible : relief standard."))
    frm_bot.pack(pady=(6, 12))
    # Ordre des boutons = ordre réel du travail :
    #   structure  →  préparation des données  →  assemblage de la tuile
    # Ligne 1 : les trois étapes, dans l'ordre.
    # Ligne 2 : outils et configuration.
    # Grille de boutons — organisée par lignes de travail :
    #  Ligne 0 : les 3 étapes, dans l'ordre  (Préparer → Assembler)
    #  Ligne 1 : les 4 dossiers de la structure (un bouton = un dossier)
    #  Ligne 2 : gestion (structure, pays, vider ASC, rafraîchir)
    #  Ligne 3 : Sonny + QGIS + outils
    #  Ligne 4 : fermer
    _defs = [
        # Ligne 0 — étapes principales
        (_L("Préparer les données", "Prepare data"), _preparer, 0, 0),
        (_L("Assembler la tuile", "Assemble tile"), _assembler, 0, 1),
        (_L("Vider ASC brut", "Clear raw ASC"),
         lambda: (_vider_asc(), _rafraichir()), 0, 2),
        (_L("Rafraîchir", "Refresh"), _rafraichir, 0, 3),
        # Ligne 1 — les 4 dossiers (même nom que le dossier)
        (DOSSIER_SONNY,
         lambda: (_pointer_dossier("sonny"), _rafraichir()), 1, 0),
        (DOSSIER_ASC,
         lambda: (_pointer_dossier("asc"), _rafraichir()), 1, 1),
        # Libellé plus parlant que le nom brut du dossier : il dit ce que
        # le dossier CONTIENT (un DEM/altitudes, réduit à la résolution
        # choisie). Le dossier réel sur le disque reste « EPSG réduit ».
        ("EPSG 4326 · DEM-Alt (4/6/10 m)",
         lambda: (_pointer_dossier("epsg"), _rafraichir()), 1, 2),
        (DOSSIER_TUILE,
         lambda: (_pointer_dossier("tuile"), _rafraichir()), 1, 3),
        # Ligne 2 — gestion de la structure
        (_L("Créer la structure", "Create structure"),
         lambda: (_creer_structure4_gui(), _rafraichir()), 2, 0),
        (_L("Ajouter un pays", "Add a country"),
         lambda: (_ajouter_pays4(), _rafraichir()), 2, 1),
        (_L("Vérifier (auto-test)", "Check (self-test)"), _auto_test, 2, 2),
        (_L("Fermer", "Close"), win.destroy, 2, 3),
        # Ligne 3 — Sonny + QGIS
        (_L("Relief Sonny automatique", "Automatic Sonny relief"),
         lambda: _relief_sonny_auto(), 3, 0),
        (_L("Installer le ZIP téléchargé", "Install downloaded ZIP"),
         lambda: _importer_relief_sonny(), 3, 1),
        (_L("Choisir QGIS", "Choose QGIS"), _choisir_qgis, 3, 2),
        (_L("Ouvrir dans QGIS", "Open in QGIS"), _ouvrir_qgis, 3, 3),
    ]
    for _txt, _cmd, _r, _c in _defs:
        _b = _ctk_button(frm_bot, text=_txt, command=_cmd)
        _b.grid(row=_r, column=_c, padx=5, pady=(8, 0) if _r else 0,
                ipadx=6, ipady=4)
        # Le bouton Fermer reste actif même pendant un assemblage.
        if _cmd is not win.destroy:
            _boutons.append(_b)

    if not _un_dossier_source_pret() or not _sortie[0]:
        win.after(150, lambda: (_assistant(), _rafraichir()))
    else:
        _rafraichir()

    # ── Ancrage des barres du bas ────────────────────────────────────
    # Le journal est packé avant les barres du bas et occupe tout
    # l'espace disponible (expand=True) : si la fenêtre est réduite,
    # c'est lui qui garde la place et les barres du bas (dont les
    # boutons) sortent du cadre. On repacke donc les barres du bas
    # EN PREMIER, ancrées en bas, puis le journal : Tk sert les barres
    # avant le journal, qui se comprime seul. Les boutons restent
    # toujours visibles.
    try:
        for _f in (frm_log, frm_deb, frm_q, frm_src, frm_out, frm_bot):
            _f.pack_forget()
        frm_bot.pack(side=tk.BOTTOM, pady=(6, 12))
        frm_out.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_src.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_q.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_deb.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 4))
    except Exception:
        pass

    win.update_idletasks()
    ww = max(880, win.winfo_reqwidth())
    wh = max(620, win.winfo_reqheight())
    win.geometry("%dx%d+%d+%d" % (ww, wh, (sw - ww) // 2, (sh - wh) // 2))

    # ── Taille minimale réelle ───────────────────────────────────────
    # La taille minimale doit être celle dont l'interface a réellement
    # besoin (largeur des 4 colonnes de boutons + hauteur des libellés,
    # des deux barres et des trois lignes de boutons), avec juste un
    # reste de journal. Sinon l'utilisateur peut réduire la fenêtre
    # jusqu'à masquer les boutons. Bornée à l'écran pour rester
    # utilisable sur les petits écrans.
    try:
        _min_w = min(win.winfo_reqwidth(), sw - 40)
        # hauteur requise moins la place « en trop » du journal :
        # on garde au minimum 120 px de journal.
        _log_h = max(0, frm_log.winfo_reqheight() - 120)
        _min_h = min(max(480, win.winfo_reqheight() - _log_h), sh - 80)
        win.minsize(int(_min_w), int(_min_h))
    except Exception:
        win.minsize(880, 560)
