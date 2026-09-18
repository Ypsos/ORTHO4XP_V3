# -*- coding: utf-8 -*-
##############################################################################
# O4_Mount_Check_Utils.py
## ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)  — CDC V3.6, Point 5
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — Mars 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)  — CDC V3.6, Point 5
#
# CREDIT — AUTHOR: Roland (Ypsos) — March 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================

# GPLv3
#
# Garde-fou "chemins accessibles" AVANT build. 100 % ADDITIF, autonome.
#
# Objectif : l'utilisateur choisit deja, dans les fenetres existantes, ou vont
# ses donnees (par ex. custom_dem sur un SSD externe /Volumes/SSD, ou sur un
# serveur). Si ce disque / serveur n'est PAS branche au moment du build, le
# chemin devient introuvable et le moteur lit du vide -> le fameux piege
# "mesh a altitude zero" (tuile plate, build gaspille).
#
# Ce module verifie, tout au debut de l'Etape 1, que les chemins DEJA choisis
# par l'utilisateur sont bien accessibles. Si un chemin externe manque, on
# REFUSE de demarrer le build avec un message clair disant lequel manque.
#
# Regles :
#   - On ne CREE rien, on ne DEPLACE rien : lecture seule (os.path.exists).
#   - On ne verifie QUE de vrais chemins (avec separateur). Les mots-cles de
#     source DEM internes (View/SRTM/ALOS...) ne sont PAS des chemins : ils
#     sont ignores, sinon on bloquerait un build parfaitement sain.
#   - Aucun reseau, aucun tkinter, aucune dependance lourde.
#   - FAIL-OPEN : la moindre erreur interne -> on autorise le build. Ce
#     garde-fou ne doit JAMAIS bloquer un build sain.
##############################################################################

import os

# Mots-cles de source DEM internes (telecharges par Ortho) : ce ne sont PAS
# des chemins fichiers, donc on ne les controle jamais.
_DEM_SOURCE_KEYWORDS = {
    "", "view", "srtm", "alos", "ned1/3", "ned1", "srtmv3",
}


def _B(fr, en):
    """Bilingue SYSTEMATIQUE : renvoie le francais ET l'anglais ensemble, quelle
    que soit la langue active de l'interface (message de securite important)."""
    return fr + " / " + en


def _looks_like_path(value):
    """Un vrai chemin contient un separateur ; un mot-cle DEM n'en a pas."""
    return ("/" in value) or ("\\" in value)


def _iter_configured_paths(tile):
    """Genere (label, chemin, is_output) pour chaque chemin externe a verifier.

    is_output=True -> c'est un dossier de SORTIE (peut ne pas exister encore :
    on verifiera son emplacement parent). is_output=False -> c'est une ENTREE
    (DEM/bathy) qui doit etre lisible telle quelle.
    """
    # custom_dem : peut contenir plusieurs chemins separes par ';'
    cdem = getattr(tile, "custom_dem", "") or ""
    for part in str(cdem).split(";"):
        part = part.strip()
        if (
            part
            and part.lower() not in _DEM_SOURCE_KEYWORDS
            and _looks_like_path(part)
        ):
            yield (_B("Altimétrie (custom_dem)", "Elevation (custom_dem)"),
                   part, False)

    # custom_bathy_dem : un chemin fichier ou dossier
    cbat = str(getattr(tile, "custom_bathy_dem", "") or "").strip()
    if cbat and _looks_like_path(cbat):
        yield (_B("Bathymétrie (custom_bathy_dem)",
                  "Bathymetry (custom_bathy_dem)"),
               cbat, False)

    # custom_build_dir : dossier de sortie de la tuile
    cbld = str(getattr(tile, "custom_build_dir", "") or "").strip()
    if cbld and _looks_like_path(cbld):
        yield (_B("Dossier de sortie de la tuile",
                  "Tile output folder"),
               cbld, True)


def check_paths_before_build(tile):
    """Retourne (ok, message).

    ok=True  -> le build peut demarrer (rien a signaler).
    ok=False -> un ou plusieurs chemins externes sont inaccessibles ; le
                message (bilingue) liste lesquels.

    FAIL-OPEN : toute erreur interne renvoie (True, "").
    """
    try:
        missing = []
        for (label, path, is_output) in _iter_configured_paths(tile):
            if is_output:
                # Le dossier de sortie peut ne pas exister encore : on verifie
                # que son emplacement PARENT (le disque) est bien present.
                target = path.rstrip("/\\")
                parent = os.path.dirname(target)
                present = os.path.isdir(target) or (
                    bool(parent) and os.path.isdir(parent)
                )
            else:
                # Entree (DEM/bathy) : le fichier ou dossier doit etre lisible.
                present = os.path.exists(path)
            if not present:
                missing.append((label, path))

        if not missing:
            return (True, "")

        lines = [
            "",
            "*** CHEMIN(S) INACCESSIBLE(S) / PATH(S) NOT REACHABLE ***",
            _B("Un disque externe ou un serveur n'est peut-etre pas branche"
               " / monte.",
               "An external disk or server may not be plugged in / mounted."),
            _B("Build refuse pour ne pas fabriquer une tuile plate"
               " (altitude zero).",
               "Build refused to avoid building a flat tile (zero altitude)."),
            "",
        ]
        for (label, path) in missing:
            lines.append("  - " + label + " : " + path)
        lines.append("")
        lines.append(_B(
            "Branche le disque / monte le serveur, puis relance le build.",
            "Plug the disk / mount the server, then start the build again.",
        ))
        lines.append("")
        return (False, "\n".join(lines))
    except Exception:
        # Ne JAMAIS bloquer un build sain a cause du garde-fou lui-meme.
        return (True, "")
