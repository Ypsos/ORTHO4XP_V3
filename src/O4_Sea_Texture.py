#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================
"""
O4_Sea_Texture.py — Fond marin local via JPG-Patch
===================================================
Ortho4XP V3.2 — Mai 2026
Auteur : Roland (Ypsos) — Codage : Claude (Anthropic AI)

PRINCIPE :
  Corriger les zones nodata (blanc/noir) dans les JPG existants.
  dans Orthophotos/JPG-Patch/+46-003/PATCH_{zl}/
  Le provider PATCH injecté par O4_Imagery_Utils les récupère comme source.
  Zéro téléchargement réseau — zéro dossier SEA.

PIPELINE :
  1. JPG-Patch sauvegardé dans JPG-Patch/+46-003/PATCH_17/
  2. Provider PATCH lu par combine_textures() via _get_sea_tile_for_tile()
  3. PNG → DDS normalement

Corrections v43 (02 juin 2026) :
  - Import O4_Mesh_Utils ajouté (manquant → NameError sur MESH.read_mesh_file)
  - Fallback couleur : sea_mask 512x512 vs _nb_arr 4096x4096 corrigé
    (redimensionner _nb_arr à 512x512 avant indexation par sea_mask)

v73 (05 juillet 2026) — Cas 1 : remplissage au TAMPON ALIGNÉ (geste GIMP
réel de Roland, doc officielle vérifiée) — décalage constant par trait, la
source suit le pinceau, tranches locales à bords ondulés prolongeant la mer
adjacente à leur hauteur (N tranches automatiques) ; puis BARBOUILLAGE
directionnel (doc GIMP) uniquement sur les jointures (frontière côté zone +
coutures entre traits). Détection VALIDÉE inchangée (verrou anti-faux-
positifs 5/5 sur tuiles réelles 4096 : aucun pixel touché hors zones
synthétiques) ; expansion de zone relative à la résolution (halo ~1.4%).

Optimisation v46 (08 juin 2026) :
  - fill_sea_nodata : pré-test rapide (.any()) avant label → return None immédiat
    si aucun pixel blanc ni noir → zéro label, zéro filtre sur JPG propres
  - fill_sea_nodata : uniform_filter et gaussian_filter opèrent uniquement sur
    le crop bounding-box de la zone nodata (+ marge 150px) → réinjection dans
    le tableau complet → gain ~3× sur JPG avec nodata partiel
  - Pixels valides strictement inchangés (diff=0.0 garanti, validé par simulation)

"""

import os
import math
from PIL import Image
import numpy
from scipy.ndimage import distance_transform_edt as _dte

import O4_UI_Utils as UI
import O4_File_Names as FNAMES
import O4_Imagery_Utils as IMG
import O4_Mesh_Utils as MESH
from O4_Lang import tr


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRE DOSSIER jpg
# ─────────────────────────────────────────────────────────────────────────────

def _tile_folder(tile):
    """Retourne le nom de dossier standard Ortho4XP : ex. +46-003 ou +46+002"""
    sign_lat = "+" if tile.lat >= 0 else "-"
    sign_lon = "+" if tile.lon >= 0 else "-"
    return f"{sign_lat}{abs(int(tile.lat)):02d}{sign_lon}{abs(int(tile.lon)):03d}"


# ─────────────────────────────────────────────────────────────────────────────
# FILL SEA NODATA — Correction zones noires des JPG marin (v46)
# Algorithme : inpainting pixels mer clairs + HDR cross blend jointure
# ─────────────────────────────────────────────────────────────────────────────

def fill_sea_nodata(jpg_path, sea_mask=None):
    """
    Remplit la zone nodata (hors couverture provider) d'un JPG marin.
    Cas 1 uniquement — v73 (05 juillet 2026), geste GIMP réel de Roland,
    vérifié sur la documentation officielle GIMP (clonage + barbouillage).

    ÉTAPE 1 — Détection : INCHANGÉE (version validée, confirmée sûre par le
    verrou anti-faux-positifs sur 5 tuiles réelles 4096 : aucun déclenchement
    sur la mer sombre calme réelle). Seule l'EXPANSION de la zone devient
    relative à la résolution : le halo sombre de mélange provider mesure
    ~1.4% de la largeur d'image (≈15 px à 1092, ≈55 px à 4096) — les 10 px
    fixes laissaient un trait rectiligne sombre à la frontière sur les
    vraies tuiles 4096.

    ÉTAPE 2 — TAMPON ALIGNÉ (doc GIMP clonage, mode Aligné) : par trait,
    un DÉCALAGE source→destination CONSTANT — la source suit le pinceau.
    Chaque trait est un balayage serpentin de pinceau rond sur une tranche
    de la zone (l'union des disques d'un serpentin dense = la tranche à
    bords ondulés organiques, jamais un carré). L'ancre source est prise
    dans la mer à la MÊME position le long de l'axe de la zone (même eau
    que la mer adjacente) → chaque tranche PROLONGE le bord marin local ;
    N tranches automatiques selon la taille de la zone, jamais codé en dur.
    Copie brute pixel à pixel (zéro moyennage) ; recalage de ton par trait
    vers la mer adjacente de la tranche. Garde-fou : la copie n'a lieu que
    si le pixel SOURCE est de la mer (pool adaptatif) — jamais de terre ou
    de plage prolongée en mer.

    ÉTAPE 3 — BARBOUILLAGE (doc GIMP Barbouiller) sur les jointures
    UNIQUEMENT (ligne de frontière côté zone + coutures entre traits) :
    l'outil prélève la couleur au passage et la mélange aux couleurs qu'il
    rencontre, en étirant la matière — implémenté par tirage directionnel :
    chaque pixel de la bande reçoit la matière prélevée de part et d'autre
    de la ligne (amplitude décroissante avec la distance, bruit lisse),
    puis très léger lissage de la bande. Les pixels de la mer valide sont
    LUS mais jamais modifiés.

    Filets : pixels non couvrables → couleur de la mer adjacente locale +
    bruit léger (jamais de plus-proche-voisin — source d'artefacts
    triangulaires constatés). Pixels valides strictement inchangés.

    Retourne Image PIL corrigée, ou None si pas de nodata.
    """
    from scipy.ndimage import (uniform_filter, binary_dilation,
                               binary_erosion, label, gaussian_filter)
    from scipy.ndimage import distance_transform_edt as _dte_l
    from scipy.ndimage import zoom as _zoom
    try:
        img  = Image.open(jpg_path).convert('RGB')
        arr  = numpy.array(img, dtype=numpy.float32)
        H, W = arr.shape[:2]
        R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # ── ÉTAPE 1 : détection (inchangée, validée) ───────────────────────────
        raw_dark  = (R < 70) & (G < 70) & (B < 70)
        raw_white = (R > 240) & (G > 240) & (B > 240)
        if not raw_dark.any() and not raw_white.any():
            return None

        gray = arr.mean(axis=2)
        _m1 = uniform_filter(gray, size=9)
        _m2 = uniform_filter(gray**2, size=9)
        local_std = numpy.sqrt(numpy.clip(_m2 - _m1**2, 0, None))
        flat = local_std < 1.5
        del gray, _m1, _m2, local_std  # hygiène mémoire (tuiles 4096)

        MIN_SIZE = max(5000, int(0.02 * H * W))

        def big_components(mask):
            result = numpy.zeros(mask.shape, dtype=bool)
            if not mask.any():
                return result
            lbl, n = label(mask)
            if n == 0:
                return result
            sizes = numpy.bincount(lbl.ravel())
            for i in range(1, n + 1):
                if sizes[i] >= MIN_SIZE:
                    result |= (lbl == i)
            return result

        no_data = big_components((raw_dark | raw_white) & flat)
        if no_data.sum() == 0:
            return None

        # Expansion RELATIVE à la résolution (halo mesuré ~1.4%, marge 1.6%)
        _halo_px = max(12, int(0.016 * max(H, W)))
        dist_to_nd = _dte_l(no_data == False)
        no_data = dist_to_nd <= _halo_px
        valid   = ~no_data
        dist_to_nd = _dte_l(no_data == False)

        # ── Pool de mer adaptatif (médiane/MAD de l'anneau autour de la zone) ──
        luma = 0.299 * R + 0.587 * G + 0.114 * B
        _ring_w = max(25, int(0.01 * max(H, W)))
        ring = valid & (dist_to_nd < 2 * _ring_w) & (luma < 190)
        if ring.sum() < 200:
            ring = valid & (luma < 190)
        med = numpy.array([numpy.median(arr[:, :, c][ring]) for c in range(3)],
                          dtype=numpy.float32)
        sig = numpy.array(
            [max(6.0, 1.4826 * float(numpy.median(
                numpy.abs(arr[:, :, c][ring] - med[c])))) for c in range(3)],
            dtype=numpy.float32)
        dev = numpy.max(
            numpy.abs(arr - med[None, None, :]) / sig[None, None, :], axis=2)
        pool = valid & (dev < 4.0) & (luma < 190)
        pool = binary_erosion(pool, iterations=2)
        if pool.sum() < 5000:
            pool = valid & (dev < 6.0) & (luma < 190)
        del dev

        ys_pool, xs_pool = numpy.where(pool)
        if len(ys_pool) < 50:
            return None

        rng = numpy.random.RandomState(hash(os.path.basename(jpg_path)) & 0xFFFFFFFF)

        # ── ÉTAPE 2 : traits de tampon aligné par tranches locales ────────────
        filled    = arr.copy()
        remaining = no_data.copy()
        stroke_id = numpy.zeros((H, W), dtype=numpy.int32)
        sid = 0

        _ys0, _xs0 = numpy.where(no_data)
        _ymin, _ymax = int(_ys0.min()), int(_ys0.max())
        _xmin, _xmax = int(_xs0.min()), int(_xs0.max())
        _along_y = (_ymax - _ymin) >= (_xmax - _xmin)
        _extent = (_ymax - _ymin + 1) if _along_y else (_xmax - _xmin + 1)
        _slab = max(int(0.10 * max(H, W)), 80)
        _n_slabs = max(1, int(numpy.ceil(_extent / _slab)))
        _perp_len = W if _along_y else H
        _waves = []
        for _i in range(_n_slabs + 1):
            _g = rng.rand(9) - 0.5
            _w = _zoom(_g, _perp_len / 9.0, order=3)[:_perp_len]
            _waves.append((_w * 0.5 * _slab).astype(numpy.int32))
        _II = numpy.arange(H)[:, None] if _along_y else numpy.arange(W)[None, :]
        _loc_win = max(40, int(0.05 * max(H, W)))
        _adj_win = max(60, int(0.08 * max(H, W)))

        def _stroke_fill(ys_s, xs_s, anchors, min_cov):
            """Un trait de tampon aligné : cherche un décalage constant dont
            la région translatée tombe majoritairement dans le pool de mer,
            copie brute + recalage de ton vers la mer adjacente locale.
            Retourne le nombre de pixels copiés."""
            nonlocal sid
            _lys, _lxs = anchors
            if not len(_lys):
                return 0
            _n_s2 = min(2500, len(ys_s))
            _sel2 = rng.choice(len(ys_s), _n_s2, replace=False)
            _py2, _px2 = ys_s[_sel2], xs_s[_sel2]
            best_cov, best_off = 0.0, None
            for _try in range(40):
                idx = rng.randint(len(_lys))
                sy, sx = int(_lys[idx]), int(_lxs[idx])
                k = rng.randint(len(ys_s))
                dyo, dxo = sy - int(ys_s[k]), sx - int(xs_s[k])
                ty, tx = _py2 + dyo, _px2 + dxo
                ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
                if not ok.any():
                    continue
                cov = float(pool[ty[ok], tx[ok]].sum()) / _n_s2
                if cov > best_cov:
                    best_cov, best_off = cov, (dyo, dxo)
                if cov > 0.92:
                    break
            if best_off is None or best_cov < min_cov:
                return 0
            (dyo, dxo) = best_off
            ty, tx = ys_s + dyo, xs_s + dxo
            ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
            oky, okx = ys_s[ok], xs_s[ok]
            tyy, txx = ty[ok], tx[ok]
            oksea = pool[tyy, txx]
            if not oksea.any():
                return 0
            oky, okx = oky[oksea], okx[oksea]
            tyy, txx = tyy[oksea], txx[oksea]
            # recalage de ton du trait vers la mer adjacente locale (même
            # gamme de positions le long de l'axe que la tranche)
            if _along_y:
                _r0 = max(0, int(oky.min()) - _adj_win)
                _r1 = min(H, int(oky.max()) + _adj_win + 1)
                adj = pool[_r0:_r1, :] & (dist_to_nd[_r0:_r1, :] < _adj_win)
                adj_px = arr[_r0:_r1, :][adj]
            else:
                _c0 = max(0, int(okx.min()) - _adj_win)
                _c1 = min(W, int(okx.max()) + _adj_win + 1)
                adj = pool[:, _c0:_c1] & (dist_to_nd[:, _c0:_c1] < _adj_win)
                adj_px = arr[:, _c0:_c1][adj]
            src_px = arr[tyy, txx]
            if len(adj_px) > 100:
                delta = numpy.clip(adj_px.mean(axis=0) - src_px.mean(axis=0),
                                   -40, 40)
            else:
                delta = numpy.zeros(3, dtype=numpy.float32)
            sid += 1
            filled[oky, okx] = src_px + delta[None, :]
            stroke_id[oky, okx] = sid
            remaining[oky, okx] = False
            return len(oky)

        for _i in range(_n_slabs):
            _b0 = (_ymin if _along_y else _xmin) + _i * _slab
            _b1 = _b0 + _slab
            if _along_y:
                _lo = _b0 + _waves[_i][None, :]
                _hi = _b1 + _waves[_i + 1][None, :]
            else:
                _lo = _b0 + _waves[_i][:, None]
                _hi = _b1 + _waves[_i + 1][:, None]
            slab_mask = remaining & (_II >= _lo) & (_II < _hi)
            if _i == 0:
                slab_mask |= remaining & (_II < _lo)
            if _i == _n_slabs - 1:
                slab_mask |= remaining & (_II >= _hi)
            if not slab_mask.any():
                continue
            ys_s, xs_s = numpy.where(slab_mask)
            # ancres = même position le long de l'axe, toute distance
            # perpendiculaire (prolongation du bord marin adjacent)
            anchors = (numpy.array([]), numpy.array([]))
            for _grow in (1, 2, 4):
                if _along_y:
                    _wy0 = max(0, int(ys_s.min()) - _loc_win * _grow)
                    _wy1 = min(H, int(ys_s.max()) + _loc_win * _grow + 1)
                    _sub = pool[_wy0:_wy1, :]
                    _ly, _lx = numpy.where(_sub)
                    if len(_ly) > 2000:
                        anchors = (_ly + _wy0, _lx)
                        break
                else:
                    _wx0 = max(0, int(xs_s.min()) - _loc_win * _grow)
                    _wx1 = min(W, int(xs_s.max()) + _loc_win * _grow + 1)
                    _sub = pool[:, _wx0:_wx1]
                    _ly, _lx = numpy.where(_sub)
                    if len(_ly) > 2000:
                        anchors = (_ly, _lx + _wx0)
                        break
            _stroke_fill(ys_s, xs_s, anchors, 0.5)

        # rattrapage : traits globaux (ancre libre) pour les pixels restants
        _tries = 0
        while remaining.any() and _tries < 10:
            _tries += 1
            ys_r, xs_r = numpy.where(remaining)
            if _stroke_fill(ys_r, xs_r, (ys_pool, xs_pool), 0.15) == 0:
                break

        # dernier filet : mer adjacente locale + bruit léger (zéro NN/Voronoï)
        if remaining.any():
            ys_r, xs_r = numpy.where(remaining)
            base_col = numpy.array(
                [float(numpy.median(arr[:, :, c][ring])) for c in range(3)],
                dtype=numpy.float32)
            noise = rng.randn(len(ys_r), 3).astype(numpy.float32) * 1.5
            filled[ys_r, xs_r] = base_col[None, :] + noise
            remaining[:] = False

        # ── ÉTAPE 3 : barbouillage directionnel sur les jointures ─────────────
        pmax = numpy.zeros((H, W), dtype=numpy.int32)
        pmin = numpy.full((H, W), 2**30, dtype=numpy.int32)
        for _sy in (-1, 0, 1):
            for _sx in (-1, 0, 1):
                sh = numpy.roll(numpy.roll(stroke_id, _sy, axis=0), _sx, axis=1)
                pmax = numpy.maximum(pmax, sh)
                _vs = sh > 0
                pmin = numpy.where(_vs, numpy.minimum(pmin, sh), pmin)
        seam_lines = no_data & (stroke_id > 0) & (pmax != pmin) & (pmin < 2**30)
        del pmax, pmin
        _depth_in = _dte_l(no_data)
        seam_lines |= no_data & (_depth_in <= 1.5)   # ligne de frontière, côté zone

        if seam_lines.any():
            _dline = _dte_l(~seam_lines).astype(numpy.float32)
            _wb = max(8.0, 0.004 * max(H, W))
            band = no_data & (_dline < _wb)
            if band.any():
                # direction perpendiculaire à la ligne (gradient de distance)
                gy, gx = numpy.gradient(_dline)
                gn = numpy.sqrt(gy * gy + gx * gx)
                gn = numpy.maximum(gn, 1e-3)
                gy /= gn; gx /= gn
                # amplitude : maximale sur la ligne, nulle au bord de bande,
                # signée par un bruit lisse → tire la matière des DEUX côtés
                _gnz = rng.rand(17, 17) - 0.5
                nz = _zoom(_gnz, (H / 17.0, W / 17.0), order=3)[:H, :W]
                amp = (numpy.clip(1.0 - _dline / _wb, 0, 1)
                       * _wb * 1.6 * nz.astype(numpy.float32))
                ys_b, xs_b = numpy.where(band)
                syb = numpy.clip((ys_b + gy[ys_b, xs_b] * amp[ys_b, xs_b])
                                 .round().astype(numpy.int64), 0, H - 1)
                sxb = numpy.clip((xs_b + gx[ys_b, xs_b] * amp[ys_b, xs_b])
                                 .round().astype(numpy.int64), 0, W - 1)
                filled[ys_b, xs_b] = filled[syb, sxb]
                del gy, gx, gn, nz, amp
                # très léger lissage de la bande (fondu du barbouillage)
                _aw = numpy.clip(1.0 - _dline / _wb, 0.0, 1.0)**1.5
                _aw = numpy.where(no_data, _aw, 0.0).astype(numpy.float32)
                for ch in range(3):
                    blurred = gaussian_filter(filled[:, :, ch], sigma=1.5)
                    filled[:, :, ch] = (_aw * blurred
                                        + (1.0 - _aw) * filled[:, :, ch])

        # pixels valides strictement inchangés
        filled[valid] = arr[valid]

        # ── Garantie finale : zéro pixel nodata résiduel dans la zone ─────────
        R2, G2, B2 = filled[:, :, 0], filled[:, :, 1], filled[:, :, 2]
        still_bad = no_data & (
            ((R2 < 70) & (G2 < 70) & (B2 < 70) & (numpy.abs(R2 - med[0]) > 3 * sig[0]))
            | ((R2 > 240) & (G2 > 240) & (B2 > 240)))
        if still_bad.any():
            ys_b, xs_b = numpy.where(still_bad)
            base_col = numpy.array(
                [float(numpy.median(arr[:, :, c][ring])) for c in range(3)],
                dtype=numpy.float32)
            noise = rng.randn(len(ys_b), 3).astype(numpy.float32) * 1.5
            filled[ys_b, xs_b] = base_col[None, :] + noise

        return Image.fromarray(numpy.clip(filled, 0, 255).astype(numpy.uint8))

    except Exception as e:
        UI.vprint(2, f"   [SeaTex] fill_sea_nodata erreur : {e}")
        return None


def generate_sea_jpg(tile, til_x_left, til_y_top, zoomlevel, provider_code,
                     neighbor_colors=None, jpeg_dir=None, dico_customzl=None,
                     existing_jpg_paths=None, provider_dict=None):
    """
    Correction nodata dans JPG existants.
    Trouve le JPG exact (distance=0), appelle fill_sea_nodata.
    Si nodata >= 1000px → patch corrigé sauvegardé.
    Si 100% valide → return None.
    Si JPG absent → return None.
    """
    try:
        patch_dir = os.path.join(
            FNAMES.Patch_dir,
            _tile_folder(tile), f"PATCH_{int(zoomlevel)}")
        os.makedirs(patch_dir, exist_ok=True)
        # Nom patch = nom JPG source (résolu après scan)
        _patch_name_pending = True
        jpg_name = None
        jpg_path = None

        # Trouver le JPG exact (distance=0) du provider
        neighbor_jpg = None
        _best_dist   = float('inf')
        try:
            _src_dirs = []
            if provider_dict is not None:
                _src_dirs = [FNAMES.jpeg_file_dir_from_attributes(
                    tile.lat, tile.lon, int(zoomlevel), provider_dict)]
            else:
                # CORRECTION (validé Roland) : scan STRICTEMENT exclusif au
                # provider actif (celui sélectionné dans Imagery pour cette
                # tuile) — jamais de repli vers un autre dossier provider.
                # Si le provider actif n'a pas de JPG à cette position,
                # aucun patch n'est généré pour cette tuile (pas de secours).
                _src_dirs = []
                for _rl in IMG.local_combined_providers_dict.get(provider_code, []):
                    _lc = _rl.get("layer_code", "")
                    if _lc != provider_code:
                        continue  # exclut tout layer de secours
                    if _lc == "PATCH":
                        continue  # PATCH n'a pas de JPG source — ignorer
                    _lpd = IMG.providers_dict.get(_lc)
                    if _lpd is None:
                        continue
                    _src_dirs.append(FNAMES.jpeg_file_dir_from_attributes(
                        tile.lat, tile.lon, int(zoomlevel), _lpd))
            _zl_str = str(int(zoomlevel))
            for _src_dir in _src_dirs:
                if not os.path.isdir(_src_dir):
                    continue
                for _fname in os.listdir(_src_dir):
                    if not _fname.lower().endswith(".jpg"):
                        continue
                    if _zl_str not in _fname:
                        continue
                    _fparts = _fname.split("_")
                    if len(_fparts) < 2:
                        continue
                    try:
                        _fy = int(_fparts[0])
                        _fx = int(_fparts[1])
                    except ValueError:
                        continue
                    _d = abs(int(til_x_left) - _fx) + abs(int(til_y_top) - _fy)
                    if _d < _best_dist:
                        _best_dist  = _d
                        neighbor_jpg = os.path.join(_src_dir, _fname)
                    if _d == 0:
                        break
                if _best_dist == 0:
                    break
        except Exception as _se:
            UI.vprint(2, f"   [SeaTex] Scan erreur : {_se}")

        # Fallback : provider simple non dans local_combined → providers_dict direct
        if not _src_dirs and provider_code in IMG.providers_dict:
            try:
                _lpd = IMG.providers_dict[provider_code]
                _src_dir = FNAMES.jpeg_file_dir_from_attributes(
                    tile.lat, tile.lon, int(zoomlevel), _lpd)
                if os.path.isdir(_src_dir):
                    _zl_str2 = str(int(zoomlevel))
                    for _fname in os.listdir(_src_dir):
                        if not _fname.lower().endswith(".jpg"):
                            continue
                        if _zl_str2 not in _fname:
                            continue
                        _fparts = _fname.split("_")
                        if len(_fparts) < 2:
                            continue
                        try:
                            _fy = int(_fparts[0])
                            _fx = int(_fparts[1])
                        except ValueError:
                            continue
                        _d = abs(int(til_x_left) - _fx) + abs(int(til_y_top) - _fy)
                        if _d < _best_dist:
                            _best_dist  = _d
                            neighbor_jpg = os.path.join(_src_dir, _fname)
                        if _d == 0:
                            break
            except Exception as _fb:
                UI.vprint(2, f"   [SeaTex] Scan fallback erreur : {_fb}")

        if _best_dist != 0 or neighbor_jpg is None:
            return None  # JPG absent

        # Nom patch avec provider_code réel → correspond au DDS attendu
        jpg_name = f"{int(til_y_top)}_{int(til_x_left)}_{provider_code}{int(zoomlevel)}.jpg"
        jpg_path = os.path.join(patch_dir, jpg_name)
        if os.path.isfile(jpg_path):
            return jpg_path  # patch déjà généré — skip

        filled_img = fill_sea_nodata(neighbor_jpg)
        if filled_img is None:
            # Fabrication automatique des patches « à fabriquer » SUPPRIMÉE :
            # les zones no-data de couleur (gris/vert/bleu/marron) qui
            # échappent au Cas 1 (noir/blanc) ne sont plus dupliquées ni
            # marquées automatiquement. L'utilisateur les traite désormais à
            # la main via le visualiseur (« Visualiser la tuile »).
            # Le Cas 1 (fill_sea_nodata, noir/blanc) reste strictement intact.
            UI.vprint(2, f"   [SeaTex] Pas de nodata noir/blanc — pas de patch : {jpg_name}")
            return None

        filled_img.save(jpg_path, quality=85)
        UI.vprint(1, tr("   [SeaTex] JPG-Patch généré : {jpg_name}").format(jpg_name=jpg_name))
        return jpg_path

    except Exception as e:
        import traceback
        UI.vprint(0, f"   [SeaTex] generate_sea_jpg ERREUR : {e} | {traceback.format_exc()}")
        return None


def _get_sea_tile_for_tile(tile, til_x_left, til_y_top, zoomlevel):
    """
    Retourne Image PIL depuis JPG-Patch si disponible.
    Appelé par combine_textures() dans O4_Imagery_Utils.py.
    Nom fichier : {ty}_{tx}_{provider}{zl}.jpg
    """
    patch_dir = os.path.join(
        FNAMES.Patch_dir,
        _tile_folder(tile),
        f"PATCH_{int(zoomlevel)}"
    )
    # Chercher le fichier patch : {ty}_{tx}_{provider}{zl}.jpg
    # ty en position 0, tx en position 1 (split sur "_")
    _ty_str = str(int(til_y_top))
    _tx_str = str(int(til_x_left))
    for _fn in os.listdir(patch_dir) if os.path.isdir(patch_dir) else []:
        if not _fn.endswith(".jpg"):
            continue
        _parts = _fn.split("_")
        if len(_parts) >= 2 and _parts[0] == _ty_str and _parts[1] == _tx_str:
            try:
                return Image.open(os.path.join(patch_dir, _fn)).convert("RGB")
            except Exception:
                return None
    return None


def download_sea_neighbor_row(tile, til_x_left, til_y_top, zoomlevel,
                               provider_code):
    """
    Stub compatible avec l'appel existant dans combine_textures().
    Les jpg voisins sont gérés par le pipeline — zéro réseau.
    """
    pass


# ─────────────────────────────────────────────────────────────────────────────
# BUILD SEA TEXTURE SET — Identifie les tuiles mer côtières via mesh
# ─────────────────────────────────────────────────────────────────────────────

def build_sea_texture_set(tile, dico_customzl):
    """
    Identifie les tuiles texture mer côtières via adjacence mesh.

    Filtre adjacence arêtes — V3.2 Mai 2026 :
      - Un triangle mer est inclus uniquement si au moins une de ses 3 arêtes
        est partagée avec un triangle de type != 2 (terre ou eau intérieure).
      - Les triangles mer entourés uniquement d'autres triangles mer (pleine mer)
        sont exclus → zéro patch inutile en pleine mer.
      - Le JPG source doit être absent (sinon le pipeline standard s'en charge).

    Appelé dans build_tile() avant les threads — zéro deadlock.
    """
    sea_set = set()
    try:
        import O4_Geo_Utils as GEO
        mesh_file = FNAMES.mesh_file(tile.build_dir, tile.lat, tile.lon)
        if not os.path.isfile(mesh_file):
            return sea_set

        (mesh_version, nbr_nodes, node_coords, nbr_tris,
         tri_idx, tri_types) = MESH.read_mesh_file(mesh_file)

        has_water = 7 if (mesh_version >= 1.3) else 3

        # ── Étape 1 : construire dict arêtes → indices triangles ─────────────
        UI.vprint(1, tr("   [SeaTex] Construction arêtes mesh..."))
        edge_to_tris = {}
        for i in range(nbr_tris):
            n1 = int(tri_idx[3 * i])
            n2 = int(tri_idx[3 * i + 1])
            n3 = int(tri_idx[3 * i + 2])
            for e in (frozenset((n1, n2)),
                      frozenset((n2, n3)),
                      frozenset((n1, n3))):
                edge_to_tris.setdefault(e, []).append(i)

        # ── Étape 2 : identifier les triangles mer adjacents à un non-mer ────
        # Track 2 (validé Roland, en doublon avec Track 1 Étape 3) :
        # dico_attributes (O4_Vector_Utils.py) : WATER=1, SEA=2, SEA_EQUIV=4.
        # La logique collapse existante (t and (2*(t>1) or 1)) fusionnait
        # WATER(1) et SEA(2)/SEA_EQUIV(4) en une seule valeur "2" — un canal
        # ou une rivière (WATER pur) était donc indiscernable de la vraie mer.
        # On exige ici explicitement le bit SEA ou SEA_EQUIV sur le triangle
        # candidat lui-même (le test d'adjacence au voisin non-mer, lui,
        # reste inchangé — il ne sert qu'à détecter un voisin non-aquatique).
        _BIT_SEA = 2
        _BIT_SEA_EQUIV = 4
        sea_adjacent_tris = set()
        for i in range(nbr_tris):
            # CORRECTION (mesh réel Data_46-003.mesh, session suivante) :
            # tri_types[i] contient DEJA la valeur brute dico_attributes
            # (0=DUMMY/terre, 1=WATER, 2=SEA, 4=SEA_EQUIV...) — voir
            # write_mesh_file() qui copie l'attribut Triangle tel quel, et
            # read_mesh_file() qui le restitue via tri_types[i]=t+1 après
            # avoir fait t=attr-1 (donc tri_types[i]==attr brut). Le "-1"
            # ici était erroné : il transformait la terre (0) en -1, qui en
            # complément à deux (numpy uint32→python int) active TOUS les
            # bits — d'où ~50% de "SEA" détecté à tort sur des tuiles 100%
            # terre (vérifié sur le vrai mesh : 46096_64704/64800,
            # 46144_64784, toutes tombées à 0-0.16% une fois corrigé).
            _raw_attr = int(tri_types[i])
            is_open_sea = bool(_raw_attr & _BIT_SEA) or (
                mesh_version >= 1.3 and bool(_raw_attr & _BIT_SEA_EQUIV))
            if not is_open_sea:
                continue
            n1 = int(tri_idx[3 * i])
            n2 = int(tri_idx[3 * i + 1])
            n3 = int(tri_idx[3 * i + 2])
            adj = False
            for e in (frozenset((n1, n2)),
                      frozenset((n2, n3)),
                      frozenset((n1, n3))):
                for j in edge_to_tris.get(e, []):
                    if j == i:
                        continue
                    tj = int(tri_types[j]) & has_water
                    tj = tj and (2 * (tj > 1) or 1)
                    if tj != 2:
                        adj = True
                        break
                if adj:
                    break
            if adj:
                sea_adjacent_tris.add(i)

        UI.vprint(1, tr("   [SeaTex] {n} triangle(s) mer côtier(s) détecté(s).").format(n=len(sea_adjacent_tris)))

        if not sea_adjacent_tris:
            return sea_set

        # ── Étape 2bis : classification SEA/SEA_EQUIV globale par tuile ──────
        # Déplacé avant l'Étape 3 (était après, "Étape 3bis") : validé sur
        # 5 JPG réels avec photo à l'appui (session suivante) — le ratio
        # SEA/total classe correctement 5/5 tuiles connues par photo :
        # 46096_64720 (côte réelle, 9.18%→inclus), 46112_64752 (eau
        # dominante, 100%→inclus), 46096_64704/46096_64800/46144_64784
        # (marais salin confirmé par photo, 0-0.16%→exclus). Ce garde-fou
        # doit donc protéger AUSSI les tuiles JPG existantes (sea_set, Étape
        # 3) — un comptage brut d'adjacence (MIN_TRIS_PER_TILE) ne suffit pas
        # seul : un vrai chenal de marée isolé (marais salin) peut dépasser
        # 15 triangles adjacents tout en restant une tuile à 100% terre en
        # photo (confirmé sur 46096_64704 : 29 triangles adjacents malgré
        # 100% terre visuel).
        # RATIO : triangles_SEA / triangles_TOTAUX de la tuile. Seuil 2%
        # avec minimum absolu de 5 triangles SEA (évite le bruit
        # statistique sur les tuiles à peu de triangles).
        MIN_SEA_RATIO = 0.02
        MIN_SEA_TRIS_ABS = 5
        _tile_sea_tri_count = {}
        _tile_total_tri_count = {}
        for i in range(nbr_tris):
            # tri_types[i] est déjà la valeur brute dico_attributes — pas
            # de -1 (voir correction Étape 2 ci-dessus).
            _ra = int(tri_types[i])
            _is_sea = bool(_ra & _BIT_SEA) or (
                mesh_version >= 1.3 and bool(_ra & _BIT_SEA_EQUIV))
            n1s = int(tri_idx[3 * i]); n2s = int(tri_idx[3 * i + 1]); n3s = int(tri_idx[3 * i + 2])
            blon = (node_coords[5*n1s] + node_coords[5*n2s] + node_coords[5*n3s]) / 3
            blat = (node_coords[5*n1s+1] + node_coords[5*n2s+1] + node_coords[5*n3s+1]) / 3
            k = GEO.wgs84_to_orthogrid(blat, blon, tile.mesh_zl)
            if k not in dico_customzl:
                continue
            ta = dico_customzl[k]
            _tile_total_tri_count[ta] = _tile_total_tri_count.get(ta, 0) + 1
            if _is_sea:
                _tile_sea_tri_count[ta] = _tile_sea_tri_count.get(ta, 0) + 1

        def _is_genuine_sea_tile(ta):
            _s = _tile_sea_tri_count.get(ta, 0)
            if _s < MIN_SEA_TRIS_ABS:
                return False
            _t = _tile_total_tri_count.get(ta, 0)
            if _t == 0:
                return False
            return (_s / _t) >= MIN_SEA_RATIO

        # ── Étape 3 : convertir tri_idx → tex_attr, filtrer JPG absents ─────
        # Track 1 (validé Roland) : un seul triangle mer-adjacent isolé
        # (ex. canal/rivière traversant une tuile à 95-100% terre) ne doit
        # PAS suffire à classer toute la tuile "côtière". On compte d'abord
        # le nombre de triangles mer-adjacents par tuile, puis on n'inclut
        # que les tuiles dépassant un seuil minimum (vraie façade maritime).
        # Garde-fou renforcé (validé photo, session suivante) :
        # _is_genuine_sea_tile() (ratio SEA/total ≥ 2%) appliqué ICI aussi.
        MIN_TRIS_PER_TILE = 15  # seuil à calibrer avec tests réels Roland

        _tri_count_by_attr = {}
        _tri_list_by_attr = {}
        for i in sea_adjacent_tris:
            n1 = int(tri_idx[3 * i])
            n2 = int(tri_idx[3 * i + 1])
            n3 = int(tri_idx[3 * i + 2])
            bary_lon = (
                node_coords[5*n1] + node_coords[5*n2] + node_coords[5*n3]
            ) / 3
            bary_lat = (
                node_coords[5*n1+1] + node_coords[5*n2+1] + node_coords[5*n3+1]
            ) / 3

            key = GEO.wgs84_to_orthogrid(bary_lat, bary_lon, tile.mesh_zl)
            if key not in dico_customzl:
                continue

            tex_attr = dico_customzl[key]
            _tri_count_by_attr[tex_attr] = _tri_count_by_attr.get(tex_attr, 0) + 1
            _tri_list_by_attr.setdefault(tex_attr, []).append(i)

        _excluded_land = 0
        for tex_attr, _count in _tri_count_by_attr.items():
            if _count < MIN_TRIS_PER_TILE:
                _excluded_land += 1
                continue
            if not _is_genuine_sea_tile(tex_attr):
                _excluded_land += 1
                continue
            if tex_attr in sea_set:
                continue

            (til_x, til_y, zl, provider_code) = tex_attr

            jpg_exists = False
            for rlayer in IMG.local_combined_providers_dict.get(provider_code, []):
                lc = rlayer.get("layer_code", "")
                if lc not in IMG.providers_dict:
                    continue
                true_x, true_y, true_zl = til_x, til_y, zl
                if "max_zl" in IMG.providers_dict[lc]:
                    mzl = int(IMG.providers_dict[lc]["max_zl"])
                    if mzl < zl:
                        import O4_Geo_Utils as _GEO2
                        (latm, lonm) = _GEO2.gtile_to_wgs84(til_x+8, til_y+8, zl)
                        (true_x, true_y) = _GEO2.wgs84_to_orthogrid(latm, lonm, mzl)
                        true_zl = mzl
                fdir = FNAMES.jpeg_file_dir_from_attributes(
                    tile.lat, tile.lon, true_zl, IMG.providers_dict[lc])
                fname = FNAMES.jpeg_file_name_from_attributes(
                    true_x, true_y, true_zl, lc)
                if os.path.isfile(os.path.join(fdir, fname)):
                    jpg_exists = True
                    break

            # JPG présent ou absent → sea_set dans les deux cas
            sea_set.add(tex_attr)

        UI.vprint(
            1, f"   [SeaTex] {len(sea_set)} jpg(s) mer côtière(s) "
               f"identifiée(s) via adjacence mesh (zéro patch pleine mer)."
        )
        if _excluded_land:
            UI.vprint(
                1, f"   [SeaTex] {_excluded_land} tuile(s) exclue(s) "
                   f"(< {MIN_TRIS_PER_TILE} triangles mer-adjacents — "
                   f"probable terre avec canal/rivière isolé(e))."
            )



    except Exception as e:
        import traceback
        UI.vprint(2, f"   [SeaTex] build_sea_texture_set erreur : {e}\n"
                     f"{traceback.format_exc()}")
    return sea_set
