#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland  (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland  (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================
"""
O4_Inland_Water_Utils.py - Module EAU INTERIEURE (rivieres, fleuves, lacs)
==========================================================================
Concu et specifie par Roland (Ypsos) pour Ortho4XP V3.

Ce module regroupe le traitement PROPRE de l'eau interieure, separe de la mer :
  1) inland_width_shape_filter : garde les cours d'eau larges (fleuves,
     rivieres) et les vrais lacs (>= seuil ha), jette les ruisseaux fins et
     petits etangs isoles. Une riviere allongee n'est jamais coupee ; un etang
     relie a une eau large en fait partie.
  2) narrow_inland_blur : bord ETROIT (~15 px) + effet GRAIN DE SABLE /
     diffusion dans la zone de transition (rive "sablee" au lieu d'un lisere
     lisse). Ne touche JAMAIS la mer (qui garde son flou large dans blur_mask).

O4_Mask_Utils.py importe et appelle ce module ; la mer n'est jamais concernee.
"""

import numpy
from PIL import Image, ImageDraw, ImageFilter
import O4_UI_Utils as UI

# --------------------------------------------------------------------------
# Seuils EN DUR (l'utilisateur n'y touche pas ; aucun reglage Ortho ajoute).
# Le seul levier utilisateur reste le bouton existant use_masks_for_inland.
# --------------------------------------------------------------------------
MASK_INLAND_MIN_WIDTH = 50.0    # metres : largeur mini d'un cours d'eau masque
MASK_POND_MIN_AREA_HA = 50.0    # ha : lac/etang compact garde si surface >= ceci
MASK_FILTER_MPP = 16.0          # m/px du calcul interne de largeur

# Bord ETROIT de l'eau interieure. La mer garde son flou large (masks_width).
INLAND_EDGE_BLUR_PX = 11.0      # rayon gaussien => transition ~22 px (fondu naturel)
INLAND_GRAIN_SMOOTH_PX = 1.0    # micro-lissage du grain de sable (0 = brut)
INLAND_GRAIN_STRENGTH = 0.6     # force du grain 0..1 (1=plein, 0.6=adouci "sable", 0=lisse)
# Repartition du grain facon "poignee de sable jetee" : dense contre la TERRE,
# dispersion rapide vers l'EAU (ou il se dissout). Plus GAMMA est grand, plus la
# chute vers l'eau est rapide. 1 = reparti uniformement ; 2.5 = dense puis chute.
INLAND_GRAIN_GAMMA = 2.5


def inland_width_shape_filter(inland_tris, min_width_m, pond_min_area_ha, mpp):
    # Determine, parmi des triangles d'EAU INTERIEURE, lesquels retirer.
    # inland_tris : liste de tuples (lat1,lon1,lat2,lon2,lat3,lon3) - meme
    #               format que dico_sea.
    # Retour : un set d'INDICES (dans inland_tris) a retirer. En cas de souci
    #          quelconque, retourne un set vide -> aucun retrait -> comportement
    #          d'origine conserve (rien n'est casse).
    try:
        from scipy import ndimage
    except Exception:
        UI.lvprint(
            1,
            "-> Filtre largeur/forme : module de calcul absent, filtre ignore"
            " (masques construits normalement).",
        )
        return set()
    if not inland_tris:
        return set()
    try:
        arr = numpy.asarray(inland_tris, dtype=float)   # (N,6)
        lats = arr[:, 0::2]                              # colonnes 0,2,4
        lons = arr[:, 1::2]                              # colonnes 1,3,5
        lo0, lo1 = float(lons.min()), float(lons.max())
        la0, la1 = float(lats.min()), float(lats.max())
        m_lat = 111320.0
        m_lon = 111320.0 * numpy.cos(numpy.radians((la0 + la1) / 2.0))
        span_x = (lo1 - lo0) * m_lon
        span_y = (la1 - la0) * m_lat
        # Si le raster serait trop grand pour la memoire, on AUGMENTE le pas
        # (calcul plus grossier) au lieu d'abandonner. Une largeur de 50 m
        # reste detectable tant que le pas <= 25 m/px. On borne le pas a 25.
        px_limit = 120000000
        need = (span_x / mpp + 2) * (span_y / mpp + 2)
        if need > px_limit:
            mpp = mpp * (need / px_limit) ** 0.5
            if mpp > 25.0:
                mpp = 25.0
        W = int(span_x / mpp) + 2
        H = int(span_y / mpp) + 2
        if W < 2 or H < 2 or (W * H) > 300000000:
            UI.lvprint(
                1,
                "-> Filtre largeur/forme : emprise trop grande, filtre ignore"
                " (masques construits normalement).",
            )
            return set()
        px = (lons - lo0) * m_lon / mpp
        py = (la1 - lats) * m_lat / mpp
        img = Image.new("1", (W, H), 0)
        draw = ImageDraw.Draw(img)
        for k in range(arr.shape[0]):
            draw.polygon(
                [
                    (px[k, 0], py[k, 0]),
                    (px[k, 1], py[k, 1]),
                    (px[k, 2], py[k, 2]),
                ],
                fill=1,
            )
        water = numpy.array(img, dtype=bool)
        del img, draw
        edt = ndimage.distance_transform_edt(water) * mpp
        lbl, nlab = ndimage.label(water)
        # composantes assez larges (au moins un point a >= min_width_m de large)
        wide_ids = numpy.unique(lbl[edt >= (min_width_m / 2.0)])
        wide_ids = wide_ids[wide_ids > 0]
        if len(wide_ids) == 0:
            keep_mask = numpy.zeros_like(water)
        else:
            area = ndimage.sum(
                numpy.ones_like(lbl), lbl, index=wide_ids
            ) * (mpp * mpp)
            maxw = ndimage.maximum(edt, lbl, index=wide_ids) * 2.0
            slices = ndimage.find_objects(lbl)
            keep_ids = []
            for j, i in enumerate(wide_ids):
                sl = slices[i - 1]
                hh = (sl[0].stop - sl[0].start) * mpp
                ww = (sl[1].stop - sl[1].start) * mpp
                elong = max(hh, ww) / max(float(maxw[j]), 1e-6)
                is_linear = elong >= 3.0     # riviere/fleuve allonge
                if is_linear or area[j] >= (pond_min_area_ha * 10000.0):
                    keep_ids.append(i)
            if keep_ids:
                keep_mask = numpy.isin(
                    lbl, numpy.array(keep_ids, dtype=lbl.dtype)
                )
            else:
                keep_mask = numpy.zeros_like(water)
        # decision par triangle : jete si son centre n'est pas dans une eau gardee
        cx = px.mean(axis=1).astype(int)
        cy = py.mean(axis=1).astype(int)
        numpy.clip(cx, 0, W - 1, out=cx)
        numpy.clip(cy, 0, H - 1, out=cy)
        kept_tri = keep_mask[cy, cx]
        drop = set(int(k) for k in numpy.nonzero(~kept_tri)[0])
        return drop
    except Exception as e:
        UI.lvprint(
            1,
            "-> Filtre largeur/forme ignore (",
            str(e),
            "), masques construits normalement.",
        )
        return set()


def narrow_inland_blur(img_array):
    # Flou + GRAIN DE SABLE pour l'eau INTERIEURE (rivieres, fleuves, lacs).
    # N'appelle PAS blur_mask (maths de flou de la mer non touchees).
    # 1) flou gaussien (bord ~22 px) => l'eau se fond en nappe ;
    # 2) semis de points (terre/eau) dans la zone de transition -> rive "sablee" ;
    # 3) micro-lissage du grain, puis MELANGE avec le degrade lisse selon
    #    INLAND_GRAIN_STRENGTH (grain adouci, pas d'effet "plastique colle").
    # En cas de souci : tableau valide, aucune exception ne remonte.
    try:
        smooth = numpy.array(
            Image.fromarray(img_array)
            .convert("L")
            .filter(ImageFilter.GaussianBlur(INLAND_EDGE_BLUR_PX)),
            dtype=numpy.uint8,
        )
        band = (smooth > 5) & (smooth < 250)
        if not band.any():
            return smooth
        noise = numpy.random.randint(
            0, 256, size=smooth.shape, dtype=numpy.uint8
        ).astype(numpy.float32) / 255.0
        # densite "poignee de sable" : proba = (proximite terre)^GAMMA -> dense
        # contre la terre, se dissout vers l'eau.
        t = smooth.astype(numpy.float32) / 255.0
        proba = t ** float(INLAND_GRAIN_GAMMA)
        grained = numpy.where(
            band,
            numpy.where(noise < proba, numpy.uint8(255), numpy.uint8(0)),
            smooth,
        ).astype(numpy.uint8)
        if INLAND_GRAIN_SMOOTH_PX > 0:
            grained = numpy.array(
                Image.fromarray(grained).filter(
                    ImageFilter.GaussianBlur(INLAND_GRAIN_SMOOTH_PX)
                ),
                dtype=numpy.uint8,
            )
        s = float(INLAND_GRAIN_STRENGTH)
        if s >= 1.0:
            return grained
        if s <= 0.0:
            return smooth
        out = (
            s * grained.astype(numpy.float32)
            + (1.0 - s) * smooth.astype(numpy.float32)
        )
        return numpy.clip(out, 0, 255).astype(numpy.uint8)
    except Exception:
        return numpy.array(img_array, dtype=numpy.uint8)
