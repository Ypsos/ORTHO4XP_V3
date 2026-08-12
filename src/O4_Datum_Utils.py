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
#  O4_Datum_Utils.py
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  RÔLE — Garde-fou « datum vertical ».
#
#    Les altimétries HR (IGN RGE ALTI / LiDAR HD, swissALTI3D, Sonny, USGS
#    3DEP…) sont fournies en altitude ORTHOMÉTRIQUE (au-dessus du niveau de
#    la mer) : NGF-IGN69 pour l'IGN, LN02 pour swisstopo, EGM2008 pour Sonny
#    en Europe, NAVD88 pour 3DEP. Elles sont donc mutuellement compatibles à
#    quelques dizaines de centimètres près.
#
#    Le DANGER n'apparaît QUE si une dalle en hauteur ELLIPSOÏDALE (WGS84
#    ellipsoïde, ex. certains produits satellites bruts) se glisse dans le
#    lot : elle est alors ~30 à ~50 m plus haute que les autres, et le
#    mélange décale tout le relief sans le moindre message d'erreur.
#
#  CE QUE FAIT CE MODULE :
#    - PAR DÉFAUT : passe-plat TOTAL. Aucune altitude n'est modifiée, aucun
#      fichier n'est écrit ou touché. La chaîne Altimétrie/Bathymétrie reste
#      identique au bit près.
#    - GARDE-FOU : avant la fusion, il inspecte le CRS vertical de chaque
#      dalle. Si l'une déclare une hauteur ELLIPSOÏDALE, il écrit un
#      AVERTISSEMENT dans le journal — il n'assemble pas en silence.
#
#  CE QUE CE MODULE NE FAIT PAS :
#    - aucun accès réseau ;
#    - aucune écriture disque ;
#    - aucune modification des tableaux d'altitude ;
#    - il ne lève JAMAIS d'exception vers l'appelant (un garde-fou ne doit
#      jamais casser un build) : tout est capturé, au pire il se tait.
#
#  DÉPENDANCES : uniquement ce qui est déjà présent dans le venv du projet
#    (rasterio fournit les objets ouverts ; pyproj est utilisé si présent
#    pour une détection plus fine, sinon repli sur l'analyse du WKT).
# ----------------------------------------------------------------------------

# Résultats possibles de la classification d'une dalle.
ORTHOMETRIQUE = "orthometrique"   # au-dessus du niveau de la mer (cas normal)
ELLIPSOIDAL   = "ellipsoidal"     # hauteur ellipsoïdale (cas DANGEREUX)
INCONNU       = "inconnu"         # composante verticale présente mais ambiguë
ABSENT        = "absent"          # aucune composante verticale déclarée (2D)

# Marqueurs textuels recherchés dans le WKT (analyse de repli, en minuscules).
_MARQUEURS_VERTICAL = (
    "vert_cs", "vertcrs", "verticalcrs", "vertical crs",
)
_MARQUEURS_ELLIPSOIDAL = (
    "ellipsoidal height", "hauteur ellipsoidale", "hauteur ellipsoïdale",
)
_MARQUEURS_ORTHOMETRIQUE = (
    "gravity-related height", "geoid", "géoïde", "geoide",
    "egm2008", "egm96", "egm 2008", "egm 96",
    "ngf", "ign69", "ign 69", "ngf-ign69",
    "navd88", "navd 88",
    "ln02", "lhn95", "orthometric",
)


def _wkt_de(crs):
    """Retourne le WKT (minuscules) d'un CRS, ou None si indisponible.
    Ne lève jamais : toute erreur -> None."""
    if crs is None:
        return None
    try:
        wkt = crs.to_wkt()
    except Exception:
        try:
            wkt = str(crs)
        except Exception:
            return None
    if not wkt:
        return None
    return wkt.lower()


def _classer_via_pyproj(crs):
    """Classification fine via pyproj, si disponible. Retourne l'un des
    constantes, ou None si pyproj est absent / n'aboutit pas."""
    try:
        from pyproj import CRS as _PPCRS
    except Exception:
        return None
    try:
        try:
            wkt = crs.to_wkt()
        except Exception:
            wkt = str(crs)
        pc = _PPCRS.from_wkt(wkt)
    except Exception:
        return None
    try:
        # Cas 1 : CRS composé (2D horizontal + 1D vertical).
        if getattr(pc, "is_compound", False):
            for sous in pc.sub_crs_list:
                if getattr(sous, "is_vertical", False):
                    nom = (getattr(sous, "name", "") or "").lower()
                    for m in _MARQUEURS_ELLIPSOIDAL:
                        if m in nom:
                            return ELLIPSOIDAL
                    for m in _MARQUEURS_ORTHOMETRIQUE:
                        if m in nom:
                            return ORTHOMETRIQUE
                    return INCONNU
            return ABSENT
        # Cas 2 : CRS géographique 3D (le 3e axe est une hauteur).
        axes = getattr(pc, "axis_info", None) or []
        if getattr(pc, "is_geographic", False) and len(axes) >= 3:
            troisieme = axes[2]
            nom_axe = (getattr(troisieme, "name", "") or "").lower()
            abbr = (getattr(troisieme, "abbrev", "") or "").lower()
            if "ellipsoidal" in nom_axe or abbr == "h":
                return ELLIPSOIDAL
            if "gravity" in nom_axe or abbr == "h ":  # 'H' -> orthométrique
                return ORTHOMETRIQUE
            return INCONNU
        # Cas 3 : purement 2D -> aucune info verticale.
        return ABSENT
    except Exception:
        return None


def _classer_via_wkt(crs):
    """Classification de repli par simple lecture du texte WKT.
    Retourne toujours une des constantes (jamais None)."""
    wkt = _wkt_de(crs)
    if not wkt:
        return INCONNU
    # Hauteur ellipsoïdale explicite (y compris CRS géographique 3D).
    for m in _MARQUEURS_ELLIPSOIDAL:
        if m in wkt:
            return ELLIPSOIDAL
    # Composante verticale présente ?
    a_vertical = any(m in wkt for m in _MARQUEURS_VERTICAL)
    if not a_vertical:
        return ABSENT
    # Vertical présent : orthométrique ou ambigu.
    for m in _MARQUEURS_ORTHOMETRIQUE:
        if m in wkt:
            return ORTHOMETRIQUE
    if "ellipsoid" in wkt:
        return ELLIPSOIDAL
    return INCONNU


def classer_datum_vertical(crs):
    """Classe le référentiel vertical d'un CRS.
    Renvoie ORTHOMETRIQUE / ELLIPSOIDAL / INCONNU / ABSENT.
    Ne lève jamais."""
    try:
        r = _classer_via_pyproj(crs)
        if r is not None:
            return r
        return _classer_via_wkt(crs)
    except Exception:
        return INCONNU


def _nom_dalle(raster, defaut):
    """Nom lisible d'une dalle ouverte (attribut .name si présent)."""
    try:
        n = getattr(raster, "name", None)
        if n:
            import os
            return os.path.basename(str(n))
    except Exception:
        pass
    return defaut


def verifier_datum_vertical(rasters, log=None):
    """Inspecte une liste de rasters DÉJÀ OUVERTS (objets rasterio) et
    retourne un récapitulatif. N'écrit rien, ne modifie rien.

    Retour : dict {
        'total'          : int,
        'ellipsoidal'    : [noms de dalles suspectes],
        'inconnu'        : [noms de dalles ambiguës],
        'orthometrique'  : nb,
        'absent'         : nb,
        'suspect'        : bool,   # True si au moins une dalle ellipsoïdale
    }

    Ne lève jamais : en cas de souci, renvoie un récap neutre.
    """
    recap = {
        "total": 0, "ellipsoidal": [], "inconnu": [],
        "orthometrique": 0, "absent": 0, "suspect": False,
    }
    if not rasters:
        return recap
    for i, r in enumerate(rasters):
        recap["total"] += 1
        try:
            crs = getattr(r, "crs", None)
        except Exception:
            crs = None
        cls = classer_datum_vertical(crs)
        nom = _nom_dalle(r, "dalle #%d" % i)
        if cls == ELLIPSOIDAL:
            recap["ellipsoidal"].append(nom)
        elif cls == INCONNU:
            recap["inconnu"].append(nom)
        elif cls == ORTHOMETRIQUE:
            recap["orthometrique"] += 1
        else:  # ABSENT
            recap["absent"] += 1
    recap["suspect"] = bool(recap["ellipsoidal"])
    return recap


def _emettre(log, message):
    """Écrit une ligne de journal via le callable fourni, sinon print.
    Ne lève jamais."""
    try:
        if callable(log):
            log(message)
        else:
            print(message)
    except Exception:
        pass


def avertir_si_datum_suspect(rasters, log=None):
    """POINT D'ENTRÉE pour la chaîne Altimétrie/Bathymétrie.

    À appeler AVANT la fusion (merge), tant que les dalles sont encore
    ouvertes. Passe-plat : ne modifie aucune altitude, n'écrit aucun
    fichier. Émet seulement un AVERTISSEMENT dans le journal si une dalle
    déclare une hauteur ellipsoïdale (mélange dangereux).

    Renvoie le récapitulatif (utile pour les tests). Ne lève jamais.
    """
    try:
        recap = verifier_datum_vertical(rasters, log=log)
    except Exception:
        return None

    if recap["suspect"]:
        noms = ", ".join(recap["ellipsoidal"])
        _emettre(log, "   [DATUM] ATTENTION : hauteur ellipsoïdale détectée "
                      "sur %d dalle(s) : %s" % (len(recap["ellipsoidal"]), noms))
        _emettre(log, "   [DATUM] Ces altitudes sont ~30 à 50 m plus hautes "
                      "que des altitudes orthométriques (au-dessus du niveau "
                      "de la mer).")
        _emettre(log, "   [DATUM] Mélanger ces dalles avec des sources IGN / "
                      "swiss / Sonny décalera le relief. Vérifiez la source "
                      "de ces dalles avant d'assembler.")
    elif recap["inconnu"]:
        noms = ", ".join(recap["inconnu"])
        _emettre(log, "   [DATUM] Note : référentiel vertical ambigu sur "
                      "%d dalle(s) : %s (assemblage poursuivi tel quel)."
                      % (len(recap["inconnu"]), noms))
    # Cas normal (tout orthométrique ou 2D) : silence total, aucun bruit.
    return recap
