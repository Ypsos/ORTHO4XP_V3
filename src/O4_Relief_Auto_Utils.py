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
#  O4_Relief_Auto_Utils.py   —   ÉTAPE 1 : couverture (calcul pur, offline)
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  RÔLE (étape 1 uniquement) — Décider, pour une tuile (lat, lon), quelle
#    source de relief HAUTE DÉFINITION s'applique, SANS aucun réseau et SANS
#    écrire quoi que ce soit :
#
#        swissALTI3D  -> uniquement en Suisse (le plus précis)
#        Sonny        -> Europe (et pourtour couvert par Sonny)
#        (aucune)     -> ailleurs : Ortho4XP reprendra son DEM classique
#                        (View / SRTM / ALOS), qui est mondial.
#
#  C'EST UNE BRIQUE DE DÉCISION. Elle ne télécharge rien, n'assemble rien,
#  n'écrit pas custom_dem. Les étapes suivantes (download, puis branchement
#  custom_dem) viendront APRÈS validation de celle-ci.
#
#  Une tuile Ortho4XP est notée par le coin SUD-OUEST entier (lat, lon).
#  Sa couverture réelle est le carré [lat, lat+1] x [lon, lon+1]. On teste
#  donc l'INTERSECTION de ce carré avec les emprises, pas seulement le coin.
#
#  Rien ici n'est figé : les emprises sont de simples rectangles éditables.
#  Aucune dépendance externe (ni rasterio, ni pyproj, ni réseau).
# ----------------------------------------------------------------------------

# Identifiants de source (chaînes stables, réutilisées par les étapes 2 et 3).
SWISS = "swissALTI3D"
SONNY = "Sonny"
AUCUNE = None            # -> repli DEM classique Ortho4XP


# Emprise de la Suisse (rectangle englobant large, marge de sécurité incluse).
# lat_min, lat_max, lon_min, lon_max
_EMPRISE_SUISSE = (45.7, 47.9, 5.9, 10.6)

# Emprise Sonny (Europe + pourtour réellement couvert par les DTM Sonny :
# de l'Atlantique/Islande à l'ouest jusqu'à l'est européen, Afrique du Nord
# et Proche-Orient inclus dans la zone publiée). Rectangle englobant large.
_EMPRISE_SONNY = (26.0, 72.0, -32.0, 45.0)


def _carre_tuile(lat, lon):
    """Carré géographique couvert par la tuile (coin SO = lat, lon)."""
    return (float(lat), float(lat) + 1.0, float(lon), float(lon) + 1.0)


def _intersecte(carre, emprise):
    """True si le carré de la tuile recoupe le rectangle d'emprise."""
    la0, la1, lo0, lo1 = carre
    ea0, ea1, eo0, eo1 = emprise
    # Pas d'intersection si l'un est entièrement à côté de l'autre.
    if la1 <= ea0 or la0 >= ea1:
        return False
    if lo1 <= eo0 or lo0 >= eo1:
        return False
    return True


def source_pour_tuile(lat, lon):
    """Retourne la source HR à utiliser pour la tuile (lat, lon).

    Priorité : Suisse (swissALTI3D) > Europe (Sonny) > aucune (repli).
    Ne lève jamais ; entrée invalide -> AUCUNE (repli sûr).
    """
    try:
        carre = _carre_tuile(lat, lon)
    except Exception:
        return AUCUNE
    # 1) Suisse d'abord : la plus précise là où elle s'applique.
    if _intersecte(carre, _EMPRISE_SUISSE):
        return SWISS
    # 2) Europe / pourtour Sonny.
    if _intersecte(carre, _EMPRISE_SONNY):
        return SONNY
    # 3) Ailleurs : repli DEM classique Ortho4XP (mondial).
    return AUCUNE


def message_utilisateur(source):
    """Message clair et rassurant à afficher à l'utilisateur débutant,
    selon la source retenue. Aucune jargon technique."""
    if source == SWISS:
        return ("Relief haute définition suisse (swissALTI3D) disponible "
                "pour cette tuile.")
    if source == SONNY:
        return ("Relief haute définition (Sonny LiDAR) disponible pour "
                "cette tuile.")
    return ("Pas de relief haute définition pour cette zone : le relief "
            "standard sera utilisé. Votre tuile sera générée normalement.")


def message_indisponible(source):
    """Message si la source HR existe pour la zone mais est injoignable
    (réseau coupé, serveur down). Le build continue en relief standard."""
    nom = source if source else "haute définition"
    return ("Relief %s temporairement indisponible : utilisation du relief "
            "standard. Votre tuile sera générée normalement." % nom)
