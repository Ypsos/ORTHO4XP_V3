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
  2. Provider PATCH lu par combine_textures() via _get_sea_tile()
  3. PNG → DDS normalement

Corrections v43 (02 juin 2026) :
  - Import O4_Mesh_Utils ajouté (manquant → NameError sur MESH.read_mesh_file)
  - Fallback couleur : sea_mask 512x512 vs _nb_arr 4096x4096 corrigé
    (redimensionner _nb_arr à 512x512 avant indexation par sea_mask)

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
    Algorithme v46 (08 juin 2026) :
      1. Pré-test rapide : si aucun pixel blanc ni noir → return None immédiat
         (zéro label, zéro filtre — gain majeur sur JPG sans nodata)
      2. Nodata = blanc (R>240 G>240 B>240) OU noir (R<15 G<15 B<15) uniforme
         (variance < 3) — détection sur pleine résolution 4096x4096
      3. Source profonde = pixels valides à distance > 20px du bord nodata,
         excluant les pixels lumineux de transition JPEG (luma>180, ±8px)
         → évite le trait blanc visible à la jointure nodata/valide
      4. Pré-lissage H+V (uniform_filter) UNIQUEMENT sur crop bbox nodata+150px
         → atténue les stries Voronoï — gain ~140× vs plein 4096x4096
      5. Tampon duplicateur : nodata + pixels transition ← source profonde lissée
         la plus proche (inpainting natif — zéro upscale LANCZOS)
      6. Pixels valides profonds strictement inchangés (diff=0.0 garanti)
      7. Gaussian anti-strie UNIQUEMENT sur crop bbox nodata
         → casse les frontières Voronoï droites — gain ~57× vs plein 4096x4096
    Retourne Image PIL corrigée, ou None si pas de nodata.
    """
    from scipy.ndimage import uniform_filter, binary_dilation
    try:
        img  = Image.open(jpg_path).convert('RGB')
        arr  = numpy.array(img, dtype=numpy.float32)

        # ── Pré-test rapide : candidats blanc/noir sur image entière ─────────
        # Si aucun pixel blanc ni aucun pixel noir → return None immédiat
        # Économise ~2× label sur 4096x4096 pour tous les JPG propres
        raw_white = (arr[:,:,0] > 240) & (arr[:,:,1] > 240) & (arr[:,:,2] > 240)
        raw_black = (arr[:,:,0] <  15) & (arr[:,:,1] <  15) & (arr[:,:,2] <  15)
        if not raw_white.any() and not raw_black.any():
            return None

        # ── Passage 1b : test linéarité frontière nodata ──────────────────────
        # Une zone nodata satellite est toujours géométrique (carré, rectangle,
        # triangle, oblique) → frontière compacte → ratio surface/périmètre² élevé.
        # Des artefacts JPEG éparpillés ont un périmètre énorme vs leur surface
        # → ratio très faible → rejet immédiat avant _filter_uniform.
        # Seuil 0.5 validé sur 5 JPG réels (vrais nodata : 4.7–14.7 / faux : <0.02).
        try:
            from scipy.ndimage import binary_dilation as _bd_p1b
            _raw_nd_p1b = raw_white | raw_black
            _surface_p1b = int(_raw_nd_p1b.sum())
            _front_p1b = _bd_p1b(_raw_nd_p1b, iterations=1) & ~_raw_nd_p1b
            _perim_p1b = int(_front_p1b.sum())
            _ratio_p1b = (_surface_p1b / (_perim_p1b ** 2) * 1000
                          ) if _perim_p1b > 0 else 0.0
            if _ratio_p1b < 0.5:
                return None   # artefacts JPEG éparpillés — pas de nodata réel
        except Exception:
            pass  # en cas d'erreur inattendue : continuer vers _filter_uniform

        # Nodata = blanc OU noir UNIFORME (variance < 3 sur pixels de la composante)
        # Détection sur pleine résolution 4096x4096 — correct et universel
        # Élimine mer profonde texturée (variance > 3) et artefacts JPEG isolés
        from scipy.ndimage import label as _lbl_fn2
        def _filter_uniform(raw_mask, min_size=100, max_var=3.0):
            """Détecte composantes uniformes — variance centrée max par canal."""
            result = numpy.zeros_like(raw_mask, dtype=bool)
            if not raw_mask.any():
                return result
            _lbl, _n = _lbl_fn2(raw_mask)
            if _n == 0:
                return result
            _sizes = numpy.bincount(_lbl.ravel())
            lut = numpy.zeros(_lbl.max() + 1, dtype=bool)
            for _i in range(1, _n + 1):
                if _sizes[_i] < min_size:
                    continue
                _ys, _xs = numpy.where(_lbl == _i)
                _pixels = arr[_ys, _xs]
                # Variance centrée par canal : soustrait la moyenne canal par canal
                # → détecte blanc pur (241-255) ET noir pur (0-14) uniformément
                _centered = _pixels - _pixels.mean(axis=0)
                var_max_ch = float(numpy.max(numpy.var(_centered, axis=0)))
                if var_max_ch < max_var:
                    lut[_i] = True
            return lut[_lbl]

        _is_white = _filter_uniform(raw_white, min_size=100, max_var=3.0)
        _is_black = _filter_uniform(raw_black, min_size=100, max_var=3.0)
        no_data   = _is_white | _is_black
        if no_data.sum() == 0:
            return None

        valid      = ~no_data
        dist_valid = _dte(~no_data)

        # Pixels lumineux de transition JPEG à la frontière nodata/valide
        # = artefacts de compression qui forment le trait blanc visible
        luma = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        bright_border = valid & binary_dilation(no_data, iterations=8) & (luma > 180)

        # Source profonde : pixels valides loin du bord, excluant bright_border
        deep_source = valid & (dist_valid > 20) & ~bright_border
        if deep_source.sum() < 10000:
            deep_source = valid & (dist_valid > 5) & ~bright_border
        if deep_source.sum() < 1000:
            return None

        # ── Bounding-box de no_data + marge 150px ────────────────────────────
        # uniform_filter et gaussian_filter opèrent uniquement sur ce crop
        # puis réinjectés dans le tableau complet → gain ~3× sur JPG côtiers
        H, W = arr.shape[:2]
        MARGIN = 150
        ys_nd, xs_nd = numpy.where(no_data)
        y0c = max(0,   int(ys_nd.min()) - MARGIN)
        y1c = min(H,   int(ys_nd.max()) + MARGIN)
        x0c = max(0,   int(xs_nd.min()) - MARGIN)
        x1c = min(W,   int(xs_nd.max()) + MARGIN)

        # Pré-lissage H+V sur les pixels sources profonds — crop seulement
        arr_smooth = arr.copy()
        crop       = arr[y0c:y1c, x0c:x1c]
        deep_crop  = deep_source[y0c:y1c, x0c:x1c]
        for ch in range(3):
            s1 = uniform_filter(crop[:,:,ch], size=40)
            s2 = uniform_filter(crop[:,:,ch].T, size=40).T
            arr_smooth[y0c:y1c, x0c:x1c, ch] = numpy.where(
                deep_crop, (s1 + s2) / 2.0, crop[:,:,ch])

        # Inpainting : nodata + pixels transition ← source profonde lissée
        inpaint_mask = no_data | bright_border
        _, idx = _dte(~deep_source, return_indices=True)
        rows_ip, cols_ip = numpy.where(inpaint_mask)
        filled = arr.copy()
        for ch in range(3):
            filled[rows_ip, cols_ip, ch] = arr_smooth[
                idx[0][rows_ip, cols_ip],
                idx[1][rows_ip, cols_ip], ch]

        # Pixels valides profonds strictement inchangés
        filled[valid & ~bright_border] = arr[valid & ~bright_border]

        # ── Anti-strie : gaussian UNIQUEMENT sur zone nodata (crop) ──────────
        # Casse les frontières Voronoï droites (horizontal/vertical) sans
        # toucher aux pixels valides — couleur et netteté inchangées
        from scipy.ndimage import gaussian_filter as _gf
        filled_crop  = filled[y0c:y1c, x0c:x1c].copy()
        no_data_crop = no_data[y0c:y1c, x0c:x1c]
        for ch in range(3):
            blurred = _gf(filled_crop[:,:,ch], sigma=12)
            filled[y0c:y1c, x0c:x1c, ch] = numpy.where(
                no_data_crop, blurred, filled_crop[:,:,ch])
        # Pixels valides strictement inchangés — garanti
        filled[valid & ~bright_border] = arr[valid & ~bright_border]

        # ── [v47] Sigma=40 sur nodata PROFOND uniquement (dist > 15px) ───────
        # Les pixels nodata proches de la jointure (≤15px) conservent sigma=12
        # → jointure non accentuée. Les pixels profonds reçoivent sigma=40
        # → stries Voronoï droites cassées plus efficacement.
        # Pixels valides strictement inchangés — garanti.
        dist_from_border = _dte(no_data)
        nodata_profond_crop = (no_data & (dist_from_border > 15))[y0c:y1c, x0c:x1c]
        if nodata_profond_crop.any():
            fc_v47 = filled[y0c:y1c, x0c:x1c].copy()
            for ch in range(3):
                blurred_40 = _gf(fc_v47[:,:,ch], sigma=40)
                filled[y0c:y1c, x0c:x1c, ch] = numpy.where(
                    nodata_profond_crop, blurred_40, fc_v47[:,:,ch])
        # Garantie absolue — tous pixels valides inchangés
        filled[valid] = arr[valid]

        # ── [v52] Barbouillage frontière nodata/valide ────────────────────────
        # Bande 15px côté nodata + 15px côté valide dans filled rempli.
        # Barbouillage rayon 20px : copie depuis pixel rempli aléatoire →
        # mélange couleurs remplissage + satellite → ligne droite invisible.
        # Gaussian sigma=2 final pour adoucir.
        # Pixels valides hors bande : inchangés (diff=0.0 garanti).
        try:
            _dist_nd_v52 = _dte(no_data)
            _dist_v_v52  = _dte(valid)
            _bande_nd = no_data & (_dist_nd_v52 >= 1) & (_dist_nd_v52 <= 15)
            _bande_v  = valid   & (_dist_v_v52  >= 1) & (_dist_v_v52  <= 15)
            _bande    = _bande_nd | _bande_v
            if _bande.any():
                _rows_b, _cols_b = numpy.where(_bande)
                _rng52 = numpy.random.default_rng(
                    seed=int(_rows_b[0]) ^ int(_cols_b[0]))
                RAYON = 20
                _dy52 = _rng52.integers(-RAYON, RAYON + 1, size=len(_rows_b))
                _dx52 = _rng52.integers(-RAYON, RAYON + 1, size=len(_rows_b))
                _nr52 = numpy.clip(_rows_b + _dy52, 0, H - 1)
                _nc52 = numpy.clip(_cols_b + _dx52, 0, W - 1)
                for ch in range(3):
                    filled[_rows_b, _cols_b, ch] = filled[_nr52, _nc52, ch]
                # Gaussian sigma=2
                for ch in range(3):
                    _bl2 = _gf(filled[:,:,ch], sigma=2)
                    filled[:,:,ch] = numpy.where(_bande, _bl2, filled[:,:,ch])
                # Pixels valides hors bande : inchangés
                filled[valid & ~_bande_v] = arr[valid & ~_bande_v]
        except Exception as _e52:
            UI.vprint(2, f"   [SeaTex] v52 jointure ignoree : {_e52}")

        return Image.fromarray(numpy.clip(filled, 0, 255).astype(numpy.uint8))

    except Exception as e:
        UI.vprint(2, f"   [SeaTex] fill_sea_nodata erreur : {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# JPG-PATCH — Génération locale fond marin (zéro réseau)
# Appelé par build_tile() dans O4_Tile_Utils.py AVANT les threads
# ─────────────────────────────────────────────────────────────────────────────

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
        jpg_name = f"{int(til_y_top)}_{int(til_x_left)}_PATCH{int(zoomlevel)}.jpg"
        jpg_path = os.path.join(patch_dir, jpg_name)
        if os.path.isfile(jpg_path):
            return jpg_path  # patch déjà généré — skip

        # Trouver le JPG exact (distance=0) du provider
        neighbor_jpg = None
        _best_dist   = float('inf')
        try:
            _src_dirs = []
            if provider_dict is not None:
                _src_dirs = [FNAMES.jpeg_file_dir_from_attributes(
                    tile.lat, tile.lon, int(zoomlevel), provider_dict)]
            else:
                for _rl in IMG.local_combined_providers_dict.get(provider_code, []):
                    _lc  = _rl.get("layer_code", "")
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

        if _best_dist != 0 or neighbor_jpg is None:
            return None  # JPG absent

        filled_img = fill_sea_nodata(neighbor_jpg)
        if filled_img is None:
            UI.vprint(2, f"   [SeaTex] JPG valide — pas de patch : {jpg_name}")
            return None

        filled_img.save(jpg_path, quality=85)
        UI.vprint(1, f"   [SeaTex] JPG-Patch généré : {jpg_name}")
        return jpg_path

    except Exception as e:
        import traceback
        UI.vprint(0, f"   [SeaTex] generate_sea_jpg ERREUR : {e} | {traceback.format_exc()}")
        return None


def _get_sea_tile_for_tile(tile, til_x_left, til_y_top, zoomlevel):
    """
    Retourne Image PIL depuis JPG-Patch si disponible.
    Appelé par combine_textures() dans O4_Imagery_Utils.py.
    Nom fichier : {ty}_{tx}_PATCH{zl}.jpg
    """
    patch_dir = os.path.join(
        FNAMES.Patch_dir,
        _tile_folder(tile),
        f"PATCH_{int(zoomlevel)}"
    )
    jpg_name = f"{int(til_y_top)}_{int(til_x_left)}_PATCH{int(zoomlevel)}.jpg"
    jpg_path = os.path.join(patch_dir, jpg_name)
    if os.path.isfile(jpg_path):
        try:
            return Image.open(jpg_path).convert("RGB")
        except Exception:
            return None
    return None


def _get_sea_tile(til_x_left, til_y_top, zoomlevel):
    """
    Version sans tile — parcourt les dossiers JPG-Patch existants.
    Compatibilité avec les appels existants dans O4_Imagery_Utils.py.
    Nom fichier : {ty}_{tx}_PATCH{zl}.jpg
    """
    try:
        base_dir = FNAMES.Patch_dir
    except Exception:
        return None
    if not os.path.isdir(base_dir):
        return None
    jpg_name = f"{int(til_y_top)}_{int(til_x_left)}_PATCH{int(zoomlevel)}.jpg"
    for tile_folder in sorted(os.listdir(base_dir)):
        if not os.path.isdir(os.path.join(base_dir, tile_folder)):
            continue
        patch_dir = os.path.join(base_dir, tile_folder, f"PATCH_{int(zoomlevel)}")
        jpg_path  = os.path.join(patch_dir, jpg_name)
        if os.path.isfile(jpg_path):
            try:
                return Image.open(jpg_path).convert("RGB")
            except Exception:
                return None
    return None


def generate_sea_jpg_missing(tile, til_x_left, til_y_top, zoomlevel,
                              source_paths):
    """
    Cas 2 — JPG absent en pleine mer.
    Génère un patch texture mer depuis les JPG côtiers sources (1 ou 2).
    Extraction zone mer uniquement (pixels non-blancs, non-noirs, non-terre)
    via filtre colorimétrique mer (teinte bleu-vert dominante).
    Moyenne des zones mer des sources → patch 4096×4096 avec texture réelle.
    Le patch porte le numéro (til_x_left, til_y_top) du JPG absent.
    """
    try:
        patch_dir = os.path.join(
            FNAMES.Patch_dir,
            _tile_folder(tile), f"PATCH_{int(zoomlevel)}")
        os.makedirs(patch_dir, exist_ok=True)
        jpg_name = f"{int(til_y_top)}_{int(til_x_left)}_PATCH{int(zoomlevel)}.jpg"
        jpg_path = os.path.join(patch_dir, jpg_name)
        if os.path.isfile(jpg_path):
            return jpg_path  # déjà généré — skip

        if isinstance(source_paths, str):
            source_paths = [source_paths]

        # Extraire la zone mer de chaque source
        # Filtre mer : pixels où le bleu+vert domine sur le rouge
        # et pas trop clairs (pas de ciel/nuage) ni trop sombres (nodata)
        _sea_arrays = []
        for _sp in source_paths[:2]:
            try:
                _arr = numpy.array(Image.open(_sp).convert("RGB"), dtype=numpy.float32)
                _R, _G, _B = _arr[:,:,0], _arr[:,:,1], _arr[:,:,2]
                # Masque mer : bleu+vert dominants, luminosité correcte
                _lum = (_R * 0.299 + _G * 0.587 + _B * 0.114)
                _sea_mask = (
                    (_B + _G > _R * 1.3) &  # bleu-vert dominant
                    (_lum > 20) &            # pas nodata noir
                    (_lum < 230)             # pas surexposé
                )
                if _sea_mask.sum() > 1000:
                    _sea_arrays.append((_arr, _sea_mask))
            except Exception:
                pass

        if not _sea_arrays:
            # Fallback : médiane globale du premier source
            _arr0 = numpy.array(Image.open(source_paths[0]).convert("RGB"), dtype=numpy.uint8)
            _med = tuple(int(numpy.median(_arr0[:,:,ch])) for ch in range(3))
            out_arr = numpy.full((4096, 4096, 3), _med, dtype=numpy.uint8)
            Image.fromarray(out_arr).save(jpg_path, quality=85)
            UI.vprint(1, f"   [SeaTex] Patch mer créé (fallback) : {jpg_name} RGB{_med}")
            return jpg_path

        # Calculer la texture mer moyenne depuis les sources
        # Redimensionner chaque zone mer extraite à 4096×4096
        _out_float = numpy.zeros((4096, 4096, 3), dtype=numpy.float64)
        _weight_total = numpy.zeros((4096, 4096), dtype=numpy.float64)

        for (_arr, _mask) in _sea_arrays:
            # Inpainting simple : remplir pixels non-mer avec la médiane mer
            _arr_filled = _arr.copy()
            for ch in range(3):
                _med_ch = float(numpy.median(_arr[_mask, ch]))
                _arr_filled[~_mask, ch] = _med_ch
            # Redimensionner à 4096×4096
            _img_resized = numpy.array(
                Image.fromarray(_arr_filled.astype(numpy.uint8)).resize(
                    (4096, 4096), Image.BILINEAR), dtype=numpy.float64)
            _mask_resized = numpy.array(
                Image.fromarray(_mask.astype(numpy.uint8) * 255).resize(
                    (4096, 4096), Image.NEAREST), dtype=numpy.float64) / 255.0
            for ch in range(3):
                _out_float[:,:,ch] += _img_resized[:,:,ch] * _mask_resized
            _weight_total += _mask_resized

        # Normaliser
        _weight_safe = numpy.maximum(_weight_total, 1.0)
        for ch in range(3):
            _out_float[:,:,ch] /= _weight_safe

        # Zones sans poids → médiane globale
        _no_weight = (_weight_total < 0.01)
        if _no_weight.any():
            _arr0 = numpy.array(Image.open(source_paths[0]).convert("RGB"), dtype=numpy.uint8)
            for ch in range(3):
                _out_float[_no_weight, ch] = float(numpy.median(_arr0[:,:,ch]))

        out_arr = numpy.clip(_out_float, 0, 255).astype(numpy.uint8)
        Image.fromarray(out_arr).save(jpg_path, quality=85)
        UI.vprint(1, f"   [SeaTex] Patch mer créé : {jpg_name} "
                     f"({len(_sea_arrays)} source(s))")
        return jpg_path

    except Exception as e:
        import traceback
        UI.vprint(2, f"   [SeaTex] generate_sea_jpg_missing erreur : {e} "
                     f"| {traceback.format_exc()}")
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
    sea_set_missing = set()
    try:
        import O4_Geo_Utils as GEO
        mesh_file = FNAMES.mesh_file(tile.build_dir, tile.lat, tile.lon)
        if not os.path.isfile(mesh_file):
            return sea_set

        (mesh_version, nbr_nodes, node_coords, nbr_tris,
         tri_idx, tri_types) = MESH.read_mesh_file(mesh_file)

        has_water = 7 if (mesh_version >= 1.3) else 3

        # ── Étape 1 : construire dict arêtes → indices triangles ─────────────
        UI.vprint(1, "   [SeaTex] Construction arêtes mesh...")
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
        sea_adjacent_tris = set()
        for i in range(nbr_tris):
            t = int(tri_types[i]) & has_water
            # NE PAS utiliser tile.use_masks_for_inland ici —
            # on veut uniquement la VRAIE mer (type&7 > 1),
            # pas les zones inland reclassifiées type=2 par use_masks_for_inland.
            t = t and (2 * (t > 1) or 1)
            if t != 2:
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

        UI.vprint(1, f"   [SeaTex] {len(sea_adjacent_tris)} triangle(s) mer côtier(s) détecté(s).")

        if not sea_adjacent_tris:
            return sea_set

        # ── Étape 3 : convertir tri_idx → tex_attr, filtrer JPG absents ─────
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

        # ── Étape 4 : BFS vague 1 uniquement ────────────────────────────────
        # Uniquement les positions directement adjacentes (±16px) aux JPG côtiers.
        # Une seule rangée de patches suffit pour éliminer la jointure visible.
        # XP12 gère le reste en eau native.
        INC = 16
        for (tx_c, ty_c, zl_c, prov_c) in sea_set:
            for (dy, dx) in [(-INC,0),(INC,0),(0,-INC),(0,INC)]:
                _key_v = GEO.wgs84_to_orthogrid(
                    *GEO.gtile_to_wgs84(tx_c + dx//2 + 8 + dx,
                                        ty_c + dy//2 + 8 + dy, zl_c), zl_c)
                # Construire tex_attr voisin directement
                _tx_v = tx_c + dx
                _ty_v = ty_c + dy
                _ta_v = (_tx_v, _ty_v, zl_c, prov_c)
                if _ta_v in sea_set or _ta_v in sea_set_missing:
                    continue
                sea_set_missing.add(_ta_v)

        UI.vprint(1, f"   [SeaTex] {len(sea_set_missing)} jpg(s) manquant(s) "
                     f"en pleine mer identifié(s) (vague 1 BFS).")

    except Exception as e:
        import traceback
        UI.vprint(2, f"   [SeaTex] build_sea_texture_set erreur : {e}\n"
                     f"{traceback.format_exc()}")
    return sea_set, sea_set_missing
