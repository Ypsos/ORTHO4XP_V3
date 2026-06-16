import os
import time
import shutil
import queue
import threading
from PIL import Image
import O4_UI_Utils as UI
import O4_File_Names as FNAMES
import O4_Imagery_Utils as IMG
import O4_Vector_Map as VMAP
import O4_Mesh_Utils as MESH
import O4_Mask_Utils as MASK
import O4_DSF_Utils as DSF
import O4_Overlay_Utils as OVL
from O4_Parallel_Utils import parallel_launch, parallel_join



# ─────────────────────────────────────────────────────────────────────────────
# DIALOGUE GESTION JPG-PATCH — V3.2
# Affiché au lancement du build si des patches existent déjà dans PATCH_{zl}/
# Permet de conserver les patches corrigés manuellement dans GIMP.
# ─────────────────────────────────────────────────────────────────────────────

def _ask_patch_management(patch_dir, existing_files):
    """
    Affiche une fenêtre modale de gestion des JPG-Patch existants.
    Retourne la liste des fichiers à supprimer.

    3 options :
      • Tout supprimer  → retourne tous les fichiers
      • Tout conserver  → retourne liste vide
      • Sélection       → fenêtre avec liste + aperçu → retourne les non cochés
    """
    try:
        import tkinter as tk
        from tkinter import ttk
        from PIL import Image, ImageTk
        try:
            from O4_Lang import tr as _tr
        except Exception:
            def _tr(k): return k

        # ── Couleurs depuis O4_Theme_Manager (thème actif) ──────────────────
        # Fallback = valeurs sombre par défaut si theme manager absent
        try:
            import O4_Theme_Manager as _TM_P
            _t = _TM_P.get_theme()
            BG      = _t.get("patch_bg",      _t.get("bg",          "#0a1a0a"))
            FG      = _t.get("patch_fg",      _t.get("fg",          "#00cc44"))
            FG2     = _t.get("patch_fg2",     _t.get("fg_secondary","#88ffaa"))
            BTN_BG  = _t.get("patch_btn_bg",  _t.get("btn_bg",      "#0d2e0d"))
            SEL_BG  = _t.get("patch_sel_bg",  _t.get("btn_active",  "#1a4a1a"))
            PREV_BG = _t.get("patch_prev_bg", _t.get("canvas_bg",   "#050f05"))
        except Exception:
            BG      = "#0a1a0a"
            FG      = "#00cc44"
            FG2     = "#88ffaa"
            BTN_BG  = "#0d2e0d"
            SEL_BG  = "#1a4a1a"
            PREV_BG = "#050f05"
        # ────────────────────────────────────────────────────────────────────
        FONT    = ("TkFixedFont", 11)
        FONT_T  = ("TkFixedFont", 13)

        result = {"action": None}  # "all" | "none" | list_to_delete

        # ── Fenêtre principale ───────────────────────────────────────────────
        root_ref = None
        try:
            root_ref = tk._default_root
        except Exception:
            pass

        win = tk.Toplevel(root_ref) if root_ref else tk.Tk()
        win.title(_tr("Gestion JPG-Patch — Ortho4XP V3"))
        win.configure(bg=BG)
        win.resizable(False, False)
        win.lift()
        win.focus_force()

        # Centrer la fenêtre
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()

        # ── Titre ────────────────────────────────────────────────────────────
        tk.Label(win, text=_tr("Gestion des JPG-Patch existants"),
                 font=FONT_T, bg=BG, fg=FG).pack(pady=(14, 2))
        tk.Label(win,
                 text=f"{len(existing_files)} {_tr('patch(es) trouvé(s) dans')} PATCH_{patch_dir.split('PATCH_')[-1]}",
                 font=FONT, bg=BG, fg=FG2).pack(pady=(0, 10))

        # ── 3 boutons principaux ─────────────────────────────────────────────
        frm_btn = tk.Frame(win, bg=BG)
        frm_btn.pack(pady=6, padx=20)

        def _do_all():
            result["action"] = "all"
            win.destroy()

        def _do_none():
            result["action"] = "none"
            win.destroy()

        def _do_select():
            result["action"] = "select"
            win.destroy()

        # ttk.Button : texte toujours lisible sur macOS/Windows/Linux
        # (Color Check utilise le même pattern)
        ttk.Button(frm_btn, text=_tr("🗑  Tout supprimer"),  command=_do_all).grid(row=0, column=0, padx=12, pady=8, ipadx=10, ipady=6)
        ttk.Button(frm_btn, text=_tr("✅  Tout conserver"),  command=_do_none).grid(row=0, column=1, padx=12, pady=8, ipadx=10, ipady=6)
        ttk.Button(frm_btn, text=_tr("🔍  Sélection patches"), command=_do_select).grid(row=0, column=2, padx=12, pady=8, ipadx=10, ipady=6)

        # Centrer après création
        win.update_idletasks()
        ww = win.winfo_reqwidth()
        wh = win.winfo_reqheight()
        win.geometry(f"+{(sw-ww)//2}+{(sh-wh)//2}")

        win.wait_window()

        # ── Action = tout supprimer ──────────────────────────────────────────
        if result["action"] == "all":
            return list(existing_files)

        # ── Action = tout conserver ──────────────────────────────────────────
        if result["action"] == "none":
            return []

        # ── Action = sélection ───────────────────────────────────────────────
        if result["action"] != "select":
            return []

        # Fenêtre de sélection avec liste + aperçu
        sel_result = {"to_delete": list(existing_files)}  # par défaut tout supprimer

        sel = tk.Toplevel(root_ref) if root_ref else tk.Tk()
        sel.title(_tr("Sélection patches à conserver — Ortho4XP V3"))
        sel.configure(bg=BG)
        sel.resizable(True, True)
        sel.lift()
        sel.focus_force()

        tk.Label(sel, text=_tr("Cocher les patches à CONSERVER"),
                 font=FONT_T, bg=BG, fg=FG).pack(pady=(12, 4))
        tk.Label(sel, text=_tr("(Les patches non cochés seront supprimés)"),
                 font=FONT, bg=BG, fg="#888888").pack(pady=(0, 8))

        frm_main = tk.Frame(sel, bg=BG)
        frm_main.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # ── Liste gauche avec cases à cocher ─────────────────────────────────
        frm_list = tk.Frame(frm_main, bg=BG)
        frm_list.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar = tk.Scrollbar(frm_list, bg=BG, troughcolor=BG)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox_frame = tk.Frame(frm_list, bg=BG)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        check_vars = {}
        thumb_photos = {}

        canvas_list = tk.Canvas(listbox_frame, bg=BG, width=320,
                                yscrollcommand=scrollbar.set,
                                highlightthickness=0)
        canvas_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas_list.yview)

        inner = tk.Frame(canvas_list, bg=BG)
        canvas_list.create_window((0, 0), window=inner, anchor="nw")

        sorted_files = sorted(existing_files)
        for fname in sorted_files:
            var = tk.BooleanVar(value=False)
            check_vars[fname] = var
            row = tk.Frame(inner, bg=BG, cursor="hand2")
            row.pack(fill=tk.X, pady=1)
            cb = tk.Checkbutton(row, variable=var, bg=BG,
                                fg=FG, selectcolor="#1a4a1a",
                                activebackground=BG, activeforeground=FG)
            cb.pack(side=tk.LEFT)
            lbl = tk.Label(row, text=fname, font=("TkFixedFont", 10),
                           bg=BG, fg=FG2, anchor="w", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X)

            # Clic sur le label → sélectionner + afficher aperçu
            def _on_click(f=fname, v=var, r=row):
                v.set(not v.get())
                _show_preview(f)
            lbl.bind("<Button-1>", lambda e, f=fname, v=var: (v.set(not v.get()), _show_preview(f)))
            cb.config(command=lambda f=fname: _show_preview(f))

        inner.update_idletasks()
        canvas_list.config(scrollregion=canvas_list.bbox("all"))

        # ── Canvas aperçu à droite ────────────────────────────────────────────
        frm_preview = tk.Frame(frm_main, bg=PREV_BG)
        frm_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        lbl_preview_name = tk.Label(frm_preview, text=_tr("← Cliquer sur un patch"),
                                    font=FONT, bg=PREV_BG, fg="#888888")
        lbl_preview_name.pack(pady=(4, 2))

        PREV_W, PREV_H = 512, 512
        canvas_prev = tk.Canvas(frm_preview, width=PREV_W, height=PREV_H,
                                bg=PREV_BG, highlightthickness=1,
                                highlightbackground="#1a4a1a")
        canvas_prev.pack(padx=8, pady=4)

        _current_photo = [None]

        def _show_preview(fname):
            lbl_preview_name.config(text=fname, fg=FG)
            fpath = os.path.join(patch_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB")
                img.thumbnail((PREV_W, PREV_H), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                _current_photo[0] = photo
                canvas_prev.delete("all")
                # Centrer dans le canvas
                ox = (PREV_W - img.width)  // 2
                oy = (PREV_H - img.height) // 2
                canvas_prev.create_image(ox, oy, anchor=tk.NW, image=photo)
            except Exception as _pe:
                canvas_prev.delete("all")
                canvas_prev.create_text(PREV_W//2, PREV_H//2,
                    text=f"Erreur : {_pe}", fill="#ff4444", font=FONT)

        # ── Boutons bas ───────────────────────────────────────────────────────
        frm_bot = tk.Frame(sel, bg=BG)
        frm_bot.pack(pady=10)

        def _sel_all():
            for v in check_vars.values(): v.set(True)
        def _sel_none():
            for v in check_vars.values(): v.set(False)

        ttk.Button(frm_bot, text=_tr("Tout cocher"),   command=_sel_all).grid(row=0, column=0, padx=6, ipadx=8, ipady=4)
        ttk.Button(frm_bot, text=_tr("Tout décocher"), command=_sel_none).grid(row=0, column=1, padx=6, ipadx=8, ipady=4)

        def _validate():
            # Conserver = coché → supprimer = non coché
            to_delete = [f for f, v in check_vars.items() if not v.get()]
            sel_result["to_delete"] = to_delete
            sel.destroy()

        ttk.Button(frm_bot, text="✅  Valider",
                   command=_validate).grid(row=0, column=2, padx=12, ipadx=16, ipady=6)

        # Afficher le premier patch au démarrage
        if sorted_files:
            sel.after(100, lambda: _show_preview(sorted_files[0]))

        sel.update_idletasks()
        ww2 = max(900, sel.winfo_reqwidth())
        wh2 = max(600, sel.winfo_reqheight())
        sel.geometry(f"{ww2}x{wh2}+{(sw-ww2)//2}+{(sh-wh2)//2}")
        sel.minsize(700, 500)

        sel.wait_window()
        return sel_result["to_delete"]

    except Exception as _dlg_e:
        # Fallback silencieux : si Tkinter indisponible → supprimer tout
        try:
            import O4_UI_Utils as _UI
            _UI.vprint(1, f"   [SeaTex] Dialogue patches non disponible ({_dlg_e}) — suppression auto")
        except Exception:
            pass
        return list(existing_files)

max_convert_slots = 4
skip_downloads = False
skip_converts = False


################################################################################
def build_sea_texture_set(tile, dico_customzl):
    """
    Lit le mesh et retourne un set de texture_attributes correspondant à des
    triangles tri_type=2 (mer) DIRECTEMENT ADJACENTS (arête partagée) à un
    triangle non-mer (terre / eau intérieure) ayant un JPG source disponible.

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
        # Chaque arête est un frozenset de 2 indices nœuds (unique par paire).
        # Permet de trouver en O(1) les triangles voisins partageant une arête.
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
        # Un triangle est "côtier" si au moins une arête est partagée avec
        # un triangle de type != 2 (terre, eau intérieure, etc.)
        sea_adjacent_tris = set()  # indices triangles mer côtiers
        for i in range(nbr_tris):
            t = int(tri_types[i]) & has_water
            # NE PAS utiliser tile.use_masks_for_inland ici —
            # on veut uniquement la VRAIE mer (type&7 > 1),
            # pas les zones inland reclassifiées type=2 par use_masks_for_inland.
            # Sinon marais/vasières vendéens → patches bleus inutiles.
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
                continue  # déjà ajouté via un autre triangle de la même texture

            (til_x, til_y, zl, provider_code) = tex_attr

            # Vérifier que le JPG est absent — même logique que build_jpeg_ortho
            jpg_exists = False
            for rlayer in IMG.local_combined_providers_dict.get(provider_code, []):
                lc = rlayer.get("layer_code", "")
                if lc not in IMG.providers_dict:
                    continue
                true_x, true_y, true_zl = til_x, til_y, zl
                if "max_zl" in IMG.providers_dict[lc]:
                    mzl = int(IMG.providers_dict[lc]["max_zl"])
                    if mzl < zl:
                        (latm, lonm) = GEO.gtile_to_wgs84(til_x+8, til_y+8, zl)
                        (true_x, true_y) = GEO.wgs84_to_orthogrid(latm, lonm, mzl)
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
    except Exception as e:
        import traceback
        UI.vprint(2, f"   [SeaTex] build_sea_texture_set erreur : {e}\n"
                     f"{traceback.format_exc()}")
    return sea_set


################################################################################
def build_sea_patches(tile):
    """
    Step 2.1 — Génération patches bord marin.

    Appelé APRÈS Step 2 (mesh présent) et AVANT Step 3 (build DDS).
    Peut être lancé depuis un bouton UI ou depuis build_all().

    Pipeline :
      1. Scan TOUS les dossiers Orthophotos/ (sauf JPG-Patch/) tous ZL
         → index {(ty,tx): [chemins JPG]} multi-provider multi-ZL
      2. build_sea_texture_set() → triangles mer côtiers via mesh
      3. Pour chaque tuile mer : fill_sea_nodata depuis meilleur voisin IGN
         Si aucun voisin → fallback dégradé couleur mer
      4. Dialogue gestion patches si patches existants

    Avantages vs Passe 1/2 dans build_tile() :
      - Tous JPG sources disponibles (Step 1 terminé)
      - Multi-provider multi-ZL → vraie texture IGN garantie
      - Patches générés une seule fois, propres, stables
      - Step 3 les utilise directement — zéro Passe 1/Passe 2
    """
    import O4_Sea_Texture as _SEA
    import O4_DSF_Utils as _DSF
    import time as _time
    _timer_21 = _time.time()

    UI.vprint(0,
        "\nStep 2.1 : Génération patches bord marin pour "
        + FNAMES.short_latlon(tile.lat, tile.lon)
        + " :\n--------\n"
    )

    # Vérifier mesh présent
    if not os.path.isfile(FNAMES.mesh_file(tile.build_dir, tile.lat, tile.lon)):
        UI.vprint(0, "   [SeaTex] ERREUR : mesh absent — lancer Step 2 d'abord.")
        return 0

    # ── Créer dossier JPG-Patch + dialogue gestion patches ───────────────────
    try:
        _sign_lat = "+" if tile.lat >= 0 else "-"
        _sign_lon = "+" if tile.lon >= 0 else "-"
        _tile_key = f"{_sign_lat}{abs(int(tile.lat)):02d}{_sign_lon}{abs(int(tile.lon)):03d}"
        _zl = getattr(tile, "default_zl", 17)
        _patch_dir = os.path.join(FNAMES.Patch_dir,
                                  _tile_key, f"PATCH_{_zl}")
        os.makedirs(_patch_dir, exist_ok=True)
        _existing = [f for f in os.listdir(_patch_dir) if f.endswith(".jpg")]
        if _existing:
            _to_delete = _ask_patch_management(_patch_dir, _existing)
            for _f in _to_delete:
                try:
                    os.remove(os.path.join(_patch_dir, _f))
                except Exception:
                    pass
        UI.vprint(1, f"   [SeaTex] Dossier JPG-Patch : {_patch_dir}")
    except Exception as _pe:
        UI.vprint(2, f"   [SeaTex] Dossier JPG-Patch erreur : {_pe}")

    # ── Initialiser providers ─────────────────────────────────────────────────
    if not IMG.initialize_local_combined_providers_dict(tile):
        UI.vprint(0, "   [SeaTex] ERREUR : initialisation providers échouée.")
        return 0

    # ── Identifier tuiles mer côtières via mesh ───────────────────────────────
    try:
        dico_customzl = _DSF.zone_list_to_ortho_dico(tile)
        sea_texture_set, sea_set_missing = _SEA.build_sea_texture_set(tile, dico_customzl)
    except Exception as _ste:
        import traceback
        UI.vprint(0, f"   [SeaTex] build_sea_texture_set ERREUR : {_ste}\n"
                     f"{traceback.format_exc()}")
        return 0

    if not sea_texture_set:
        UI.vprint(1, "   [SeaTex] Aucune tuile mer côtière détectée — rien à générer.")
        return 1

    UI.vprint(1, f"   [SeaTex] Correction nodata pour "
                 f"{len(sea_texture_set)} jpg(s) mer côtière(s)...")

    # ── Cas 2 : corriger nodata (blanc/noir) dans les JPG existants ──────────
    # Pour chaque tuile mer côtière dont le JPG existe et contient des zones
    # nodata (blanc R>240 ou noir R<15) → fill_sea_nodata → patch corrigé
    # sauvegardé dans JPG-Patch/. Les JPG 100% valides sont ignorés (return None).
    generated = 0
    _patches_done = set()
    _total_sea = len(sea_texture_set)
    UI.progress_bar(2, 0)
    for _k, _ta in enumerate(sea_texture_set, 1):
        (tx, ty, zl, prov) = _ta
        UI.vprint(1, f"   [SeaTex] Analyse nodata {_k}/{_total_sea}...")
        UI.progress_bar(2, int(100 * (_k - 1) / _total_sea))
        if (ty, tx, zl) in _patches_done:
            continue
        _prov_dict = IMG.providers_dict.get(prov)
        if _prov_dict is None:
            _layers = IMG.local_combined_providers_dict.get(prov, [])
            _lc = next((rl.get("layer_code", "") for rl in _layers
                        if rl.get("layer_code", "") in IMG.providers_dict), None)
            _prov_dict = IMG.providers_dict.get(_lc) if _lc else None
        _jpg = _SEA.generate_sea_jpg(tile, tx, ty, zl, prov,
                                     provider_dict=_prov_dict)
        if _jpg:
            generated += 1
            _patches_done.add((ty, tx, zl))
    UI.progress_bar(2, 100)

    UI.vprint(1, f"   [SeaTex] Cas 1 terminé — {generated} patch(es) nodata corrigés.")

    # ── Cas 2 : JPG absents en pleine mer → patch couleur mer depuis patch côtier ──
    # Pour chaque position pleine mer sans JPG provider :
    # Trouver le patch côtier existant le plus proche → extraire couleur mer
    # → générer patch uniforme portant le numéro du JPG manquant
    if sea_set_missing:
        UI.vprint(1, f"   [SeaTex] Cas 2 : {len(sea_set_missing)} JPG manquants vers le large...")
        _gen2 = 0
        _total2 = len(sea_set_missing)

        # Construire index des JPG provider côtiers existants sur disque
        # Même logique que Cas 1 pour trouver _prov_dict et le chemin JPG
        # Trouver les JPG côtiers sur disque et calculer couleur mer globale
        _coastal_jpgs = []
        for _ta_c in sea_texture_set:
            (tx_c, ty_c, zl_c, prov_c) = _ta_c
            _layers_c = IMG.local_combined_providers_dict.get(prov_c, [])
            _lc_c = next((rl.get("layer_code", "") for rl in _layers_c
                          if rl.get("layer_code", "") in IMG.providers_dict
                          and rl.get("layer_code", "") != "PATCH"), None)
            if _lc_c is None:
                continue
            _prov_dict_c = IMG.providers_dict.get(_lc_c)
            if _prov_dict_c is None:
                continue
            _fd_c = FNAMES.jpeg_file_dir_from_attributes(
                tile.lat, tile.lon, zl_c, _prov_dict_c)
            _fn_c = FNAMES.jpeg_file_name_from_attributes(tx_c, ty_c, zl_c, _lc_c)
            _fp_c = os.path.join(_fd_c, _fn_c)
            if os.path.isfile(_fp_c):
                _coastal_jpgs.append(_fp_c)

        if not _coastal_jpgs:
            UI.vprint(1, "   [SeaTex] Cas 2 : aucun JPG côtier source — ignoré.")
        else:
            # Couleur mer globale — médiane sur tous les JPG côtiers
            import numpy as _np2
            from PIL import Image as _IMG2
            _all_px2 = []
            for _fp2 in _coastal_jpgs:
                try:
                    _a2 = _np2.array(_IMG2.open(_fp2).convert("RGB"), dtype=_np2.uint8)
                    _all_px2.append(_a2.reshape(-1, 3))
                except Exception:
                    pass
            if not _all_px2:
                UI.vprint(1, "   [SeaTex] Cas 2 : impossible d'extraire couleur mer.")
            else:
                _combined2 = _np2.concatenate(_all_px2, axis=0)
                _global_color = tuple(int(_np2.median(_combined2[:, ch])) for ch in range(3))
                UI.vprint(1, f"   [SeaTex] Couleur mer globale : RGB{_global_color}")

                # Source = premier JPG côtier (chemin fichier attendu par generate_sea_jpg_missing)
                _src_path = _coastal_jpgs[0]
                for _k2, _ta2 in enumerate(sea_set_missing, 1):
                    (tx2, ty2, zl2, prov2) = _ta2
                    UI.vprint(1, f"   [SeaTex] Patch manquant {_k2}/{_total2} : {ty2}_{tx2}_PATCH{zl2}...")
                    if (ty2, tx2, zl2) in _patches_done:
                        continue
                    _jpg2 = _SEA.generate_sea_jpg_missing(
                        tile, tx2, ty2, zl2, _src_path)
                    if _jpg2:
                        _gen2 += 1
                        _patches_done.add((ty2, tx2, zl2))
        UI.vprint(1, f"   [SeaTex] Cas 2 terminé — {_gen2} patch(es) pleine mer générés.")

    UI.vprint(1, f"   [SeaTex] Step 2.1 terminé.")
    UI.timings_and_bottom_line(_timer_21)
    return 1


################################################################################
################################################################################
def download_textures(tile, download_queue, convert_queue, sea_texture_set=None):
    UI.vprint(1, "-> Opening download queue.")
    done = 0
    while True:
        texture_attributes = download_queue.get()
        if isinstance(texture_attributes, str) and texture_attributes == "quit":
            UI.progress_bar(2, 100)
            break
        if IMG.build_jpeg_ortho(tile, *texture_attributes):
            # JPG source présent — pipeline original inchangé
            done += 1
            UI.progress_bar(
                2, int(100 * done / (done + download_queue.qsize()))
            )
            convert_queue.put((tile, *texture_attributes))
        else:
            # JPG absent — si tuile mer, JPG-Patch déjà généré → convert quand même
            is_sea_tile = (sea_texture_set is not None and
                           texture_attributes in sea_texture_set)
            if is_sea_tile:
                done += 1
                UI.progress_bar(
                    2, int(100 * done / (done + download_queue.qsize()))
                )
                convert_queue.put((tile, *texture_attributes))

        if UI.red_flag:
            UI.vprint(1, "Download process interrupted.")
            return 0
    if done:
        UI.vprint(1, " *Download of textures completed.")
    return 1

################################################################################
def build_tile(tile):
    if UI.is_working:
        return 0
    UI.is_working = 1
    UI.red_flag = False
    UI.logprint(
        "Step 3 for tile lat=", tile.lat, ", lon=", tile.lon, ": starting."
    )
    UI.vprint(
        0,
        "\nStep 3 : Building DSF/Imagery for tile "
        + FNAMES.short_latlon(tile.lat, tile.lon)
        + " : \n--------\n",
    )

    if not os.path.isfile(FNAMES.mesh_file(tile.build_dir, tile.lat, tile.lon)):
        UI.lvprint(
            0, "ERROR: A mesh file must first be constructed for the tile!"
        )
        UI.exit_message_and_bottom_line("")
        return 0

    timer = time.time()

    tile.write_to_config()

    if not IMG.initialize_local_combined_providers_dict(tile):
        UI.exit_message_and_bottom_line("")
        return 0

    try:
        if not os.path.exists(
            os.path.join(
                tile.build_dir,
                "Earth nav data",
                FNAMES.round_latlon(tile.lat, tile.lon),
            )
        ):
            os.makedirs(
                os.path.join(
                    tile.build_dir,
                    "Earth nav data",
                    FNAMES.round_latlon(tile.lat, tile.lon),
                )
            )
        if not os.path.isdir(os.path.join(tile.build_dir, "textures")):
            os.makedirs(os.path.join(tile.build_dir, "textures"))
        if UI.cleaning_level > 1 and not tile.grouped:
            for f in os.listdir(os.path.join(tile.build_dir, "textures")):
                if f[-4:] != ".png":
                    continue
                try:
                    os.remove(os.path.join(tile.build_dir, "textures", f))
                except:
                    pass
        if not tile.grouped:
            try:
                shutil.rmtree(os.path.join(tile.build_dir, "terrain"))
            except:
                pass
        if not os.path.isdir(os.path.join(tile.build_dir, "terrain")):
            os.makedirs(os.path.join(tile.build_dir, "terrain"))
    except Exception as e:
        UI.lvprint(0, "ERROR: Cannot create tile subdirectories.")
        UI.vprint(3, e)
        UI.exit_message_and_bottom_line("")
        return 0

    # Construire sea_texture_set depuis les patches déjà sur disque (Step 2.1)
    # Pas de parcours mesh — silencieux — juste lire les JPG-Patch présents
    sea_texture_set = set()
    try:
        import O4_Geo_Utils as _GEO_st
        _sign_lat = "+" if tile.lat >= 0 else "-"
        _sign_lon = "+" if tile.lon >= 0 else "-"
        _tile_key = f"{_sign_lat}{abs(int(tile.lat)):02d}{_sign_lon}{abs(int(tile.lon)):03d}"
        _zl_st = getattr(tile, "default_zl", 17)
        _patch_dir_st = os.path.join(FNAMES.Patch_dir,
                                     _tile_key, f"PATCH_{_zl_st}")
        if os.path.isdir(_patch_dir_st):
            _prov_st = getattr(tile, "default_website", "ZonePhoto")
            for _fn_st in os.listdir(_patch_dir_st):
                if not _fn_st.endswith(".jpg"):
                    continue
                _p_st = _fn_st.replace(".jpg", "").split("_")
                if len(_p_st) < 2:
                    continue
                try:
                    _ty_st = int(_p_st[0])
                    _tx_st = int(_p_st[1])
                    sea_texture_set.add((_tx_st, _ty_st, _zl_st, _prov_st))
                except ValueError:
                    continue
    except Exception:
        sea_texture_set = None

    download_queue = queue.Queue()
    convert_queue = queue.Queue()

    download_launched = False
    convert_launched = False

    build_dsf_thread = threading.Thread(
        target=DSF.build_dsf, args=[tile, download_queue]
    )
    download_thread = threading.Thread(
        target=download_textures,
        args=[tile, download_queue, convert_queue, sea_texture_set]
    )
    build_dsf_thread.start()
    if not skip_downloads:
        download_thread.start()
        download_launched = True
        if not skip_converts:
            UI.vprint(
                1,
                "-> Opening convert queue and",
                max_convert_slots,
                "conversion workers.",
            )
            dico_conv_progress = {"done": 0, "bar": 3}
            convert_workers = parallel_launch(
                IMG.convert_texture,
                convert_queue,
                max_convert_slots,
                progress=dico_conv_progress,
            )
            convert_launched = True
    build_dsf_thread.join()
    if download_launched:
        download_queue.put("quit")
        download_thread.join()


        if convert_launched:
            for _ in range(max_convert_slots):
                convert_queue.put("quit")
            parallel_join(convert_workers)
            if UI.red_flag:
                UI.vprint(1, "DDS conversion process interrupted.")
            elif dico_conv_progress["done"] >= 1:
                UI.vprint(1, " *DDS conversion of textures completed.")
    UI.vprint(1, " *Activating DSF file.")
    # Supprimer les PNG masques côtiers après DSF et DDS terminés
    for _f in os.listdir(os.path.join(tile.build_dir, "textures")):
        if _f.endswith(".png") and _f != "water_transition.png" and "_ZL" not in _f:
            try:
                os.remove(os.path.join(tile.build_dir, "textures", _f))
            except:
                pass
    dsf_file_name = os.path.join(
        tile.build_dir,
        "Earth nav data",
        FNAMES.long_latlon(tile.lat, tile.lon) + ".dsf",
    )
    try:
        os.replace(dsf_file_name + ".tmp", dsf_file_name)
    except:
        UI.vprint(0, "ERROR : could not rename DSF file, tile is not actived.")
    if UI.red_flag:
        UI.exit_message_and_bottom_line()
        return 0
    if UI.cleaning_level > 1:
        try:
            os.remove(FNAMES.alt_file(tile))
        except:
            pass
        try:
            os.remove(FNAMES.input_node_file(tile))
        except:
            pass
        try:
            os.remove(FNAMES.input_poly_file(tile))
        except:
            pass
    if UI.cleaning_level > 2:
        try:
            os.remove(FNAMES.mesh_file(tile.build_dir, tile.lat, tile.lon))
        except:
            pass
        try:
            os.remove(FNAMES.apt_file(tile))
        except:
            pass
    if UI.cleaning_level > 1 and not tile.grouped:
        remove_unwanted_textures(tile)
    UI.timings_and_bottom_line(timer)
    UI.logprint(
        "Step 3 for tile lat=", tile.lat, ", lon=", tile.lon, ": normal exit."
    )
    return 1

################################################################################
def build_all(tile):
    VMAP.build_poly_file(tile)
    if UI.red_flag:
        UI.exit_message_and_bottom_line("")
        return 0
    MESH.build_mesh(tile)
    if UI.red_flag:
        UI.exit_message_and_bottom_line("")
        return 0
    build_sea_patches(tile)
    if UI.red_flag:
        UI.exit_message_and_bottom_line("")
        return 0
    MASK.build_masks(tile)
    if UI.red_flag:
        UI.exit_message_and_bottom_line("")
        return 0
    build_tile(tile)
    if UI.red_flag:
        UI.exit_message_and_bottom_line("")
        return 0
    UI.is_working = 0
    return 1

################################################################################
def _cleanup_corrupt_dsf(tile):
    """
    Supprime le fichier DSF .tmp corrompu si présent.
    Appelé automatiquement avant chaque tuile batch pour éviter le blocage
    du validateur DSF au relancement. Modification minimale V3.2.
    """
    dsf_tmp = os.path.join(
        tile.build_dir,
        "Earth nav data",
        FNAMES.long_latlon(tile.lat, tile.lon) + ".dsf.tmp",
    )
    if os.path.isfile(dsf_tmp):
        try:
            os.remove(dsf_tmp)
            UI.vprint(1, f"   [Batch] DSF .tmp corrompu supprimé : {os.path.basename(dsf_tmp)}")
        except Exception as e:
            UI.vprint(2, f"   [Batch] Impossible de supprimer DSF .tmp : {e}")


################################################################################
def build_tile_list(
    tile, list_lat_lon, do_osm, do_mesh, do_mask, do_dsf, do_ovl, do_ptc
):
    if UI.is_working:
        return 0
    UI.red_flag = 0
    timer = time.time()
    skipped = []  # V3.2 — tuiles ignorées après erreur
    UI.lvprint(
        0, "Batch build launched for a number of", len(list_lat_lon), "tiles."
    )
    k = 0
    for (lat, lon) in list_lat_lon:
        k += 1
        UI.vprint(
            1,
            "Dealing with tile ",
            k,
            "/",
            len(list_lat_lon),
            ":",
            FNAMES.short_latlon(lat, lon),
        )
        (tile.lat, tile.lon) = (lat, lon)
        tile.build_dir = FNAMES.build_dir(
            tile.lat, tile.lon, tile.custom_build_dir
        )
        tile.dem = None
        if do_ptc:
            tile.read_from_config()
        if do_osm or do_mesh or do_dsf:
            tile.make_dirs()
        # V3.2 — Nettoyer DSF .tmp corrompu avant chaque tuile
        if do_dsf:
            _cleanup_corrupt_dsf(tile)
        if do_osm:
            VMAP.build_poly_file(tile)
            if UI.red_flag:
                # V3.2 — Skip cette tuile, continuer le batch
                UI.vprint(0, f"   [Batch] Tuile {FNAMES.short_latlon(lat, lon)} ignorée (erreur OSM) — batch continue.")
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_mesh:
            MESH.build_mesh(tile)
            if UI.red_flag:
                UI.vprint(0, f"   [Batch] Tuile {FNAMES.short_latlon(lat, lon)} ignorée (erreur mesh) — batch continue.")
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_mask:
            MASK.build_masks(tile)
            if UI.red_flag:
                UI.vprint(0, f"   [Batch] Tuile {FNAMES.short_latlon(lat, lon)} ignorée (erreur masque) — batch continue.")
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_dsf:
            build_tile(tile)
            if UI.red_flag:
                UI.vprint(0, f"   [Batch] Tuile {FNAMES.short_latlon(lat, lon)} ignorée (erreur DSF/imagery) — batch continue.")
                _cleanup_corrupt_dsf(tile)  # Nettoyer le .tmp de cette tuile
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_ovl:
            OVL.build_overlay(lat, lon)
            if UI.red_flag:
                UI.vprint(0, f"   [Batch] Tuile {FNAMES.short_latlon(lat, lon)} ignorée (erreur overlay) — batch continue.")
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        try:
            UI.gui.earth_window.canvas.delete(
                UI.gui.earth_window.dico_tiles_todo[(lat, lon)]
            )
            UI.gui.earth_window.dico_tiles_todo.pop((lat, lon), None)
        except:
            pass
    # V3.2 — Rapport final batch
    if skipped:
        UI.lvprint(0, f"Batch terminé avec {len(skipped)} tuile(s) ignorée(s) :")
        for (slat, slon) in skipped:
            UI.lvprint(0, f"  ⚠ {FNAMES.short_latlon(slat, slon)}")
    UI.lvprint(
        0, "Batch process completed in", UI.nicer_timer(time.time() - timer)
    )
    return 1

################################################################################
def remove_unwanted_textures(tile):
    texture_list = []
    for f in os.listdir(os.path.join(tile.build_dir, "terrain")):
        if f[-4:] != ".ter":
            continue
        if f[-5] != "y":  # overlay
            texture_list.append(f.replace(".ter", ".dds"))
        else:
            texture_list.append("_".join(f[:-4].split("_")[:-2]) + ".dds")
    for f in os.listdir(os.path.join(tile.build_dir, "textures")):
        if f[-4:] != ".dds":
            continue
        if f not in texture_list:
            print("Removing obsolete texture", f)
            try:
                os.remove(os.path.join(tile.build_dir, "textures", f))
            except:
                pass
