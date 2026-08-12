# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
#  O4_Pays_Utils.py  —  déduction du PAYS d'une tuile (pour ranger le relief)
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  RÔLE — À partir de (lat, lon) d'une tuile, déduire le NOM DE PAYS afin de
#    ranger automatiquement les .hgt Sonny dans  hgt/<Pays>/  (comme le fait
#    Sonny, qui classe ses fichiers par pays). Zéro question à l'utilisateur.
#
#  Les emprises sont des rectangles englobants (lat_min, lat_max, lon_min,
#  lon_max), volontairement LARGES. En cas de chevauchement (zones
#  frontalières), le pays dont le CENTRE de tuile est le plus proche du
#  centre d'emprise l'emporte — ça suffit pour ranger le fichier, car Sonny
#  remplit chaque .hgt « cross-country » (données voisines incluses).
#
#  Aucune dépendance externe. Ne lève jamais : si aucun pays ne correspond,
#  retourne "Autre" (le fichier est alors rangé dans hgt/Autre/).
#
#  Table centrée sur les pays réellement proposés par Sonny (Europe +
#  pourtour). Elle peut être complétée sans risque : simples rectangles.
# ----------------------------------------------------------------------------

import math

PAYS_DEFAUT = "Autre"

# nom -> (lat_min, lat_max, lon_min, lon_max)
# Rectangles englobants larges. L'ordre n'importe pas : on choisit par
# proximité du centre en cas de recouvrement.
_PAYS = {
    "France":       (41.3, 51.1, -5.2, 9.6),
    "Allemagne":    (47.2, 55.1, 5.8, 15.1),
    "Suisse":       (45.7, 47.9, 5.9, 10.6),
    "Belgique":     (49.4, 51.6, 2.5, 6.4),
    "Luxembourg":   (49.4, 50.2, 5.7, 6.6),
    "Pays-Bas":     (50.7, 53.7, 3.3, 7.3),
    "Italie":       (36.6, 47.1, 6.6, 18.6),
    "Espagne":      (35.9, 43.9, -9.4, 3.4),
    "Portugal":     (36.9, 42.2, -9.6, -6.1),
    "Royaume-Uni":  (49.8, 61.0, -8.7, 1.8),
    "Irlande":      (51.4, 55.5, -10.7, -5.9),
    "Autriche":     (46.3, 49.1, 9.5, 17.2),
    "Pologne":      (49.0, 54.9, 14.1, 24.2),
    "Rep_Tcheque":  (48.5, 51.1, 12.0, 18.9),
    "Slovaquie":    (47.7, 49.7, 16.8, 22.6),
    "Hongrie":      (45.7, 48.6, 16.1, 22.9),
    "Danemark":     (54.5, 57.8, 8.0, 15.2),
    "Norvege":      (57.9, 71.2, 4.5, 31.1),
    "Suede":        (55.3, 69.1, 11.0, 24.2),
    "Finlande":     (59.7, 70.1, 20.5, 31.6),
    "Islande":      (63.2, 66.6, -24.6, -13.4),
    "Grece":        (34.8, 41.8, 19.3, 28.3),
    "Croatie":      (42.3, 46.6, 13.4, 19.5),
    "Slovenie":     (45.4, 46.9, 13.3, 16.6),
    "Roumanie":     (43.6, 48.3, 20.2, 29.7),
    "Bulgarie":     (41.2, 44.3, 22.3, 28.7),
    "Estonie":      (57.5, 59.7, 21.7, 28.2),
    "Lettonie":     (55.6, 58.1, 20.9, 28.3),
    "Lituanie":     (53.8, 56.5, 20.9, 26.9),
    "Chypre":       (34.5, 35.8, 32.2, 34.6),
}


def _centre(emprise):
    a0, a1, o0, o1 = emprise
    return ((a0 + a1) / 2.0, (o0 + o1) / 2.0)


def _dans(emprise, lat, lon):
    a0, a1, o0, o1 = emprise
    # On teste le CENTRE de la tuile (lat+0.5, lon+0.5).
    cl, cn = lat + 0.5, lon + 0.5
    return (a0 <= cl <= a1) and (o0 <= cn <= o1)


# Priorité en cas de zone frontalière : un pays de cette liste l'emporte
# sur ses voisins (ex. l'Alsace touche DE/CH/LU mais est 100 % française).
_PRIORITE = ("France",)


def pays_pour_tuile(lat, lon):
    """Nom de pays pour la tuile (coin SO = lat, lon).
    Retourne PAYS_DEFAUT ("Autre") si rien ne correspond. Ne lève jamais."""
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return PAYS_DEFAUT

    candidats = []
    for nom, emp in _PAYS.items():
        if _dans(emp, lat, lon):
            candidats.append((nom, emp))

    if not candidats:
        return PAYS_DEFAUT
    if len(candidats) == 1:
        return candidats[0][0]

    # 1) Priorité frontalière : si un pays prioritaire est candidat, il gagne.
    noms = [n for n, _e in candidats]
    for prio in _PRIORITE:
        if prio in noms:
            return prio

    # 2) Sinon, pays dont le centre d'emprise est le plus proche du centre
    #    de la tuile.
    cl, cn = lat + 0.5, lon + 0.5
    meilleur = None
    meilleure_dist = None
    for nom, emp in candidats:
        el, en = _centre(emp)
        d = math.hypot(cl - el, cn - en)
        if meilleure_dist is None or d < meilleure_dist:
            meilleure_dist = d
            meilleur = nom
    return meilleur or PAYS_DEFAUT


def pays_connus():
    """Liste triée des pays de la table (pour une liste déroulante éventuelle)."""
    return sorted(_PAYS.keys())
