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
from O4_Lang import tr

# Lot A — Memory Manager (non bloquant)
# Appelé UNIQUEMENT en fin de build_tile() (étape 3), après la jointure de
# tous les threads : build_dsf_thread.join(), download_thread.join() et
# parallel_join() des workers de conversion. Aucun traitement parallèle n'est
# alors en cours, gc.collect() ne peut figer personne — d'où allow_gc=True.
# Ce point est traversé par tous les chemins : étape 3 seule, « All in one »
# (build_all) et build_tile_list.
# Ne JAMAIS appeler depuis download_textures(), convert_texture() ni aucun
# worker parallèle.
try:
    from O4_Memory_Manager import check_and_cleanup_memory as _check_mem
except Exception:
    def _check_mem(context="", allow_gc=False):
        pass



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
        ttk.Button(frm_btn, text=_tr("🖊  Correction patches"), command=lambda: _open_correction_window(win, patch_dir, existing_files, BG, FG, FG2, PREV_BG, FONT, FONT_T, _tr)).grid(row=0, column=3, padx=12, pady=8, ipadx=10, ipady=6)

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

        # ── Rubriques dédiées (validé 14/07/2026) ────────────────────────────
        # « Patchs à fabriquer » = marqueur .afabriquer présent (orange),
        # « JPG à corriger » = les autres, rubrique toujours affichée.
        def _est_a_fabriquer(fname):
            return os.path.isfile(os.path.join(patch_dir, fname + ".afabriquer"))

        _afab = [f for f in sorted_files if _est_a_fabriquer(f)]
        _norm = [f for f in sorted_files if f not in _afab]
        _nav_ordre = []
        _nav_courant = [None]
        _lignes = {}   # fname -> (row, cb, lbl) pour le surlignage
        SURL = "#1a4a1a"  # couleur de surlignage de la ligne sélectionnée

        def _surligne(fname):
            # Retirer le surlignage précédent, poser le nouveau
            _prec = _nav_courant[0]
            if _prec in _lignes:
                for w in _lignes[_prec]:
                    try:
                        w.config(bg=BG)
                    except Exception:
                        pass
            if fname in _lignes:
                for w in _lignes[fname]:
                    try:
                        w.config(bg=SURL)
                    except Exception:
                        pass

        def _ajout_titre_sel(texte):
            tk.Label(inner, text=texte, font=("TkFixedFont", 10, "bold"),
                     bg=BG, fg=FG, anchor="w").pack(fill=tk.X, pady=(6, 2))

        def _ajout_ligne_sel(fname, couleur):
            var = tk.BooleanVar(value=False)
            check_vars[fname] = var
            row = tk.Frame(inner, bg=BG, cursor="hand2")
            row.pack(fill=tk.X, pady=1)
            cb = tk.Checkbutton(row, variable=var, bg=BG,
                                fg=FG, selectcolor="#1a4a1a",
                                activebackground=BG, activeforeground=FG,
                                takefocus=0)
            cb.pack(side=tk.LEFT)
            lbl = tk.Label(row, text=fname, font=("TkFixedFont", 10),
                           bg=BG, fg=couleur, anchor="w", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X)
            lbl.bind("<Button-1>", lambda e, f=fname, v=var: (v.set(not v.get()), _show_preview(f)))
            cb.config(command=lambda f=fname: _show_preview(f))
            _nav_ordre.append(fname)
            _lignes[fname] = (row, cb, lbl)

        if _afab:
            _ajout_titre_sel(_tr("── Patchs à fabriquer ──") + f" ({len(_afab)})")
            for fname in _afab:
                _ajout_ligne_sel(fname, "#ffaa33")
        _ajout_titre_sel(_tr("── JPG à corriger ──") + f" ({len(_norm)})")
        for fname in _norm:
            _ajout_ligne_sel(fname, FG2)

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
            _surligne(fname)
            _nav_courant[0] = fname
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

        # ── Navigation clavier ↑/↓ (validé 14/07/2026) ──────────────────────
        # bind_all : fiable même si le focus est sur un widget enfant (macOS).
        # Nettoyé à la fermeture pour ne pas polluer les autres fenêtres.
        def _nav_fleche_sel(delta):
            if not _nav_ordre:
                return "break"
            try:
                _i = _nav_ordre.index(_nav_courant[0])
                _i = max(0, min(len(_nav_ordre) - 1, _i + delta))
            except ValueError:
                _i = 0 if delta > 0 else len(_nav_ordre) - 1
            _show_preview(_nav_ordre[_i])
            try:
                canvas_list.yview_moveto(_i / max(1, len(_nav_ordre)))
            except Exception:
                pass
            return "break"

        sel.bind_all("<Up>", lambda e: _nav_fleche_sel(-1))
        sel.bind_all("<Down>", lambda e: _nav_fleche_sel(1))

        def _nettoie_binds_sel(_e=None):
            try:
                sel.unbind_all("<Up>")
                sel.unbind_all("<Down>")
            except Exception:
                pass
        sel.bind("<Destroy>", _nettoie_binds_sel)

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

        # Afficher le premier patch au démarrage (ordre affiché, rubriques comprises)
        if _nav_ordre:
            sel.after(100, lambda: _show_preview(_nav_ordre[0]))

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

# ─────────────────────────────────────────────────────────────────────────────
# FENÊTRE CORRECTION PATCHES — V3.2
# Ouverte depuis le bouton "Correction patches" de _ask_patch_management.
# Permet de supprimer des patches sélectionnés ET d'ouvrir un patch dans
# une application externe (GIMP, Photoshop, etc.) dont le chemin est
# sauvegardé dans Ortho4XP.cfg sous la clé patch_editor_app.
# ─────────────────────────────────────────────────────────────────────────────

def _open_correction_window(parent_win, patch_dir, existing_files,
                             BG, FG, FG2, PREV_BG, FONT, FONT_T, _tr):
    """
    Fenêtre "Correction patches" :
      - Liste des patches avec cases à cocher
      - Bouton "Supprimer patches sélectionnés" → supprime les cochés
      - Bouton "Correction" → sélecteur d'application (Finder/Explorer)
        → chemin sauvegardé dans Ortho4XP.cfg (clé patch_editor_app)
        → ouvre le(s) patch(es) coché(s) dans l'application choisie
    """
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from PIL import Image, ImageTk
    import subprocess
    import sys

    _cfg_key = "patch_editor_app"

    def _read_editor_path():
        try:
            import O4_File_Names as _FN
            cfg_path = os.path.join(_FN.Ortho4XP_dir, "Ortho4XP.cfg")
            if not os.path.isfile(cfg_path):
                return ""
            with open(cfg_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(_cfg_key + "="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
        return ""

    def _save_editor_path(path):
        try:
            import O4_File_Names as _FN
            cfg_path = os.path.join(_FN.Ortho4XP_dir, "Ortho4XP.cfg")
            lines = []
            found = False
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith(_cfg_key + "="):
                            lines.append(f"{_cfg_key}={path}\n")
                            found = True
                        else:
                            lines.append(line)
            if not found:
                lines.append(f"{_cfg_key}={path}\n")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as _se:
            messagebox.showerror(
                _tr("Erreur"),
                f"{_tr('Impossible de sauvegarder le chemin éditeur')} :\n{_se}")

    root_ref = None
    try:
        root_ref = tk._default_root
    except Exception:
        pass

    corr = tk.Toplevel(root_ref) if root_ref else tk.Toplevel(parent_win)
    corr.title(_tr("Correction patches — Ortho4XP V3"))
    corr.configure(bg=BG)
    corr.resizable(True, True)
    corr.lift()
    corr.focus_force()

    sw = corr.winfo_screenwidth()
    sh = corr.winfo_screenheight()

    tk.Label(corr, text=_tr("Correction patches"),
             font=FONT_T, bg=BG, fg=FG).pack(pady=(12, 2))
    tk.Label(corr, text=_tr("Cocher les patches à traiter"),
             font=FONT, bg=BG, fg="#888888").pack(pady=(0, 8))

    frm_main = tk.Frame(corr, bg=BG)
    frm_main.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

    frm_list = tk.Frame(frm_main, bg=BG)
    frm_list.pack(side=tk.LEFT, fill=tk.BOTH)

    scrollbar = tk.Scrollbar(frm_list, bg=BG, troughcolor=BG)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas_list = tk.Canvas(frm_list, bg=BG, width=320,
                            yscrollcommand=scrollbar.set,
                            highlightthickness=0)
    canvas_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=canvas_list.yview)

    inner = tk.Frame(canvas_list, bg=BG)
    canvas_list.create_window((0, 0), window=inner, anchor="nw")

    check_vars = {}
    _nav_ordre = []   # ordre visuel des patches pour la navigation clavier
    _nav_courant = [None]  # patch actuellement affiché dans l'aperçu
    _lignes = {}      # fname -> (row, cb, lbl) pour le surlignage
    SURL = "#1a4a1a"  # couleur de surlignage de la ligne sélectionnée

    def _surligne(fname):
        _prec = _nav_courant[0]
        if _prec in _lignes:
            for w in _lignes[_prec]:
                try:
                    w.config(bg=BG)
                except Exception:
                    pass
        if fname in _lignes:
            for w in _lignes[fname]:
                try:
                    w.config(bg=SURL)
                except Exception:
                    pass

    sorted_files = sorted(f for f in existing_files
                          if os.path.isfile(os.path.join(patch_dir, f)))

    def _est_a_fabriquer(fname):
        # Rubrique dédiée (validé 14/07/2026) : un patch est « à fabriquer »
        # tant que son marqueur .afabriquer existe dans PATCH_{zl}.
        return os.path.isfile(os.path.join(patch_dir, fname + ".afabriquer"))

    def _rebuild_list():
        for widget in inner.winfo_children():
            widget.destroy()
        _lignes.clear()
        _all = sorted(check_vars.keys())
        _afab = [f for f in _all if _est_a_fabriquer(f)]
        _norm = [f for f in _all if f not in _afab]

        def _ajout_ligne(fname, couleur):
            var = check_vars[fname]
            row = tk.Frame(inner, bg=BG, cursor="hand2")
            row.pack(fill=tk.X, pady=1)
            cb = tk.Checkbutton(row, variable=var, bg=BG,
                                fg=FG, selectcolor="#1a4a1a",
                                activebackground=BG, activeforeground=FG,
                                takefocus=0)
            cb.pack(side=tk.LEFT)
            lbl = tk.Label(row, text=fname, font=("TkFixedFont", 10),
                           bg=BG, fg=couleur, anchor="w", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X)
            lbl.bind("<Button-1>",
                     lambda e, v=var, f=fname: (v.set(not v.get()), _show_preview(f)))
            cb.config(command=lambda f=fname: _show_preview(f))
            _lignes[fname] = (row, cb, lbl)

        def _ajout_titre(texte):
            tk.Label(inner, text=texte, font=("TkFixedFont", 10, "bold"),
                     bg=BG, fg=FG, anchor="w").pack(fill=tk.X, pady=(6, 2))

        _ordre_affiche = []  # ordre visuel pour la navigation clavier
        if _afab:
            _ajout_titre(_tr("── Patchs à fabriquer ──") + f" ({len(_afab)})")
            for fname in _afab:
                _ajout_ligne(fname, "#ffaa33")
                _ordre_affiche.append(fname)
        _ajout_titre(_tr("── JPG à corriger ──") + f" ({len(_norm)})")
        for fname in _norm:
            _ajout_ligne(fname, FG2)
            _ordre_affiche.append(fname)
        _nav_ordre[:] = _ordre_affiche
        inner.update_idletasks()
        canvas_list.config(scrollregion=canvas_list.bbox("all"))

    for fname in sorted_files:
        check_vars[fname] = tk.BooleanVar(value=False)
    _rebuild_list()

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
        _surligne(fname)
        _nav_courant[0] = fname
        lbl_preview_name.config(text=fname, fg=FG)
        fpath = os.path.join(patch_dir, fname)
        try:
            img = Image.open(fpath).convert("RGB")
            img.thumbnail((PREV_W, PREV_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            _current_photo[0] = photo
            canvas_prev.delete("all")
            ox = (PREV_W - img.width) // 2
            oy = (PREV_H - img.height) // 2
            canvas_prev.create_image(ox, oy, anchor=tk.NW, image=photo)
        except Exception as _pe:
            canvas_prev.delete("all")
            canvas_prev.create_text(PREV_W // 2, PREV_H // 2,
                text=f"Erreur : {_pe}", fill="#ff4444", font=FONT)

    # ── Navigation clavier ↑/↓ dans la liste de gauche (validé 14/07/2026) ──
    # Les flèches parcourent la liste dans l'ordre affiché (rubriques
    # comprises) et mettent l'aperçu à jour ; la liste défile pour suivre.
    def _nav_fleche(delta):
        if not _nav_ordre:
            return "break"
        try:
            _i = _nav_ordre.index(_nav_courant[0])
        except ValueError:
            _i = 0 if delta > 0 else len(_nav_ordre) - 1
            _show_preview(_nav_ordre[_i])
            return "break"
        _i = max(0, min(len(_nav_ordre) - 1, _i + delta))
        _show_preview(_nav_ordre[_i])
        try:
            canvas_list.yview_moveto(_i / max(1, len(_nav_ordre)))
        except Exception:
            pass
        return "break"

    corr.bind_all("<Up>", lambda e: _nav_fleche(-1))
    corr.bind_all("<Down>", lambda e: _nav_fleche(1))

    def _nettoie_binds_corr(_e=None):
        try:
            corr.unbind_all("<Up>")
            corr.unbind_all("<Down>")
        except Exception:
            pass
    corr.bind("<Destroy>", _nettoie_binds_corr)

    if sorted_files:
        corr.after(100, lambda: _show_preview(
            _nav_ordre[0] if _nav_ordre else sorted_files[0]))

    # Barre chemin éditeur
    _editor_var = tk.StringVar(value=_read_editor_path())
    frm_editor = tk.Frame(corr, bg=BG)
    frm_editor.pack(fill=tk.X, padx=12, pady=(4, 0))
    tk.Label(frm_editor, text=_tr("Application :"), font=FONT,
             bg=BG, fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_editor, textvariable=_editor_var,
             font=("TkFixedFont", 10), bg=BG, fg=FG2,
             anchor="w", wraplength=600, justify="left").pack(
             side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    frm_bot = tk.Frame(corr, bg=BG)
    frm_bot.pack(pady=10)

    def _sel_all():
        for v in check_vars.values(): v.set(True)

    def _sel_none():
        for v in check_vars.values(): v.set(False)

    def _delete_selected():
        to_del = [f for f, v in check_vars.items() if v.get()]
        if not to_del:
            messagebox.showinfo(_tr("Correction patches"),
                                _tr("Aucun patch sélectionné."))
            return
        if not messagebox.askyesno(
                _tr("Confirmation"),
                _tr("Supprimer {n} patch(es) sélectionné(s) ?").format(n=len(to_del))):
            return
        for fname in to_del:
            try:
                os.remove(os.path.join(patch_dir, fname))
                # Supprimer aussi le marqueur .afabriquer associé (orphelin)
                _mk = os.path.join(patch_dir, fname + ".afabriquer")
                if os.path.isfile(_mk):
                    os.remove(_mk)
            except Exception as _re:
                messagebox.showerror(_tr("Erreur"),
                    f"{_tr('Impossible de supprimer')} {fname} :\n{_re}")
            check_vars.pop(fname, None)
        _rebuild_list()
        canvas_prev.delete("all")
        lbl_preview_name.config(text=_tr("← Cliquer sur un patch"), fg="#888888")

    def _choose_editor():
        if sys.platform == "darwin":
            init_dir = "/Applications"
            filetypes = [(_tr("Applications macOS"), "*.app"),
                         (_tr("Tous les fichiers"), "*")]
        elif sys.platform.startswith("win"):
            init_dir = "C:\\Program Files"
            filetypes = [(_tr("Exécutables Windows"), "*.exe"),
                         (_tr("Tous les fichiers"), "*")]
        else:
            init_dir = "/usr/bin"
            filetypes = [(_tr("Tous les fichiers"), "*")]
        path = filedialog.askopenfilename(
            parent=corr,
            title=_tr("Choisir l'application de correction (GIMP, Photoshop…)"),
            initialdir=init_dir,
            filetypes=filetypes)
        if path:
            _editor_var.set(path)
            _save_editor_path(path)

    def _open_in_editor():
        editor = _editor_var.get().strip()
        if not editor:
            messagebox.showinfo(
                _tr("Correction patches"),
                _tr("Aucune application définie.\n"
                    "Cliquer d'abord sur 'Correction' pour choisir l'application."))
            return
        selected = [f for f, v in check_vars.items() if v.get()]
        if not selected:
            messagebox.showinfo(_tr("Correction patches"),
                                _tr("Aucun patch sélectionné."))
            return
        paths = [os.path.join(patch_dir, f) for f in selected]
        try:
            if sys.platform == "darwin" and editor.endswith(".app"):
                subprocess.Popen(["open", "-a", editor] + paths)
            elif sys.platform.startswith("win"):
                subprocess.Popen([editor] + paths)
            else:
                subprocess.Popen([editor] + paths)
        except Exception as _oe:
            messagebox.showerror(
                _tr("Erreur ouverture"),
                _tr("Impossible d'ouvrir l'application") + f" :\n{_oe}")

    ttk.Button(frm_bot, text=_tr("Tout cocher"),
               command=_sel_all).grid(row=0, column=0, padx=6, ipadx=8, ipady=4)
    ttk.Button(frm_bot, text=_tr("Tout décocher"),
               command=_sel_none).grid(row=0, column=1, padx=6, ipadx=8, ipady=4)
    ttk.Button(frm_bot, text=_tr("🗑  Supprimer patches sélectionnés"),
               command=_delete_selected).grid(row=0, column=2, padx=12,
                                              ipadx=12, ipady=4)
    ttk.Button(frm_bot, text=_tr("🖊  Correction (choisir application)"),
               command=_choose_editor).grid(row=1, column=0, columnspan=2,
                                            padx=6, pady=(8, 0),
                                            ipadx=10, ipady=5)
    ttk.Button(frm_bot, text=_tr("▶  Ouvrir dans l'éditeur"),
               command=_open_in_editor).grid(row=1, column=2, padx=12,
                                             pady=(8, 0), ipadx=10, ipady=5)

    corr.update_idletasks()
    ww = max(960, corr.winfo_reqwidth())
    wh = max(640, corr.winfo_reqheight())
    corr.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
    corr.minsize(700, 500)


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

        UI.vprint(1, tr("   [SeaTex] {n} triangle(s) mer côtier(s) détecté(s).").format(n=len(sea_adjacent_tris)))

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
                    # Supprimer aussi le marqueur .afabriquer associé
                    _mk_d = os.path.join(_patch_dir, _f + ".afabriquer")
                    if os.path.isfile(_mk_d):
                        os.remove(_mk_d)
                except Exception:
                    pass
        UI.vprint(1, f"   [SeaTex] Dossier JPG-Patch : {_patch_dir}")
    except Exception as _pe:
        UI.vprint(2, f"   [SeaTex] Dossier JPG-Patch erreur : {_pe}")

    # ── Initialiser providers ─────────────────────────────────────────────────
    if not IMG.initialize_local_combined_providers_dict(tile):
        UI.vprint(0, tr("   [SeaTex] ERREUR : initialisation providers échouée."))
        return 0

    # ── Identifier tuiles mer côtières via mesh ───────────────────────────────
    try:
        dico_customzl = _DSF.zone_list_to_ortho_dico(tile)
        sea_texture_set = _SEA.build_sea_texture_set(tile, dico_customzl)
    except Exception as _ste:
        import traceback
        UI.vprint(0, f"   [SeaTex] build_sea_texture_set ERREUR : {_ste}\n"
                     f"{traceback.format_exc()}")
        return 0

    if not sea_texture_set:
        UI.vprint(1, tr("   [SeaTex] Aucune tuile mer côtière détectée — rien à générer."))
        return 1

    UI.vprint(1, f"   [SeaTex] Correction nodata pour "
                 f"{len(sea_texture_set)} jpg(s) mer côtière(s)...")

    # ── Cas 1 : corriger nodata (blanc/noir) dans les JPG existants ──────────
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
        # Règle Bible : ZonePhoto avec extent réel → PAS de patch côtier
        try:
            import O4_Color_Normalize as _CNORM
            if _CNORM.load_zonephoto():
                _layers_cas1 = IMG.local_combined_providers_dict.get(prov, [])
                _has_extent = any(
                    rl.get("extent_code", "global") != "global"
                    for rl in _layers_cas1
                    if rl.get("layer_code") != "PATCH"
                )
                if _has_extent:
                    continue  # ZonePhoto avec extent → skip
        except Exception:
            pass
        _jpg = _SEA.generate_sea_jpg(tile, tx, ty, zl, prov,
                                     provider_dict=None)
        if _jpg:
            generated += 1
            _patches_done.add((ty, tx, zl))
    UI.progress_bar(2, 100)

    UI.vprint(1, tr("   [SeaTex] Cas 1 terminé — {n} patch(es) nodata corrigés.").format(n=generated))


    UI.vprint(1, tr("   [SeaTex] Step 2.1 terminé."))
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

    # Le cache aéroports (.apt) est relu pendant l'étape 3. Son format exécute
    # du code au moment de l'ouverture : la vérification a donc lieu ici, dans
    # le thread principal, AVANT que le moindre traitement ne démarre. Un cache
    # non authentique est effacé et l'étape 3 se poursuit sans lui, exactement
    # comme lorsqu'il a été supprimé par le nettoyage.
    # Voir O4_File_Names.check_apt_file().
    FNAMES.check_apt_file(tile)

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
        _sign_lat = "+" if tile.lat >= 0 else "-"
        _sign_lon = "+" if tile.lon >= 0 else "-"
        _tile_key = f"{_sign_lat}{abs(int(tile.lat)):02d}{_sign_lon}{abs(int(tile.lon)):03d}"
        _zl_st = getattr(tile, "default_zl", 17)
        _patch_dir_st = os.path.join(FNAMES.Patch_dir,
                                     _tile_key, f"PATCH_{_zl_st}")
        if os.path.isdir(_patch_dir_st):
            _prov_st = getattr(tile, "default_website", "")
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
    except Exception as _e_pre:
        UI.vprint(2, "   [SeaTex] Erreur pré-DSF ter : " + str(_e_pre))
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

            # ── Passage 2 : conversion directe PATCH_{zl}/ → textures/ ──
            _patch_dir_p2 = os.path.join(
                FNAMES.Patch_dir,
                FNAMES.short_latlon(tile.lat, tile.lon),
                f"PATCH_{getattr(tile, 'default_zl', 17)}"
            )
            _textures_dir_p2 = os.path.join(tile.build_dir, "textures")
            if os.path.isdir(_patch_dir_p2) and not UI.red_flag and not skip_converts:
                _patches_p2 = [f for f in os.listdir(_patch_dir_p2) if f.endswith(".jpg")]
                if _patches_p2:
                    UI.vprint(1, f"   [SeaTex] Passage 2 : {len(_patches_p2)} patch(es)...")
                    import subprocess as _sp
                    _terrain_dir_p2 = os.path.join(tile.build_dir, 'terrain')
                    os.makedirs(_terrain_dir_p2, exist_ok=True)
                    _done_p2 = 0
                    for _fn_p2 in _patches_p2:
                        try:
                            _jpg_p2 = os.path.join(_patch_dir_p2, _fn_p2)
                            # ── Patch « à fabriquer » (validé 14/07/2026) ──
                            # Tant que le marqueur .afabriquer existe et que
                            # le JPG n'a pas été retouché depuis (mtime JPG
                            # <= mtime marqueur), le duplicata brut défectueux
                            # ne doit PAS remplacer le DDS propre du pipeline.
                            # Dès que le JPG est retouché (mtime > marqueur),
                            # le marqueur est supprimé et la conversion a lieu.
                            _mk_p2 = _jpg_p2 + ".afabriquer"
                            if os.path.isfile(_mk_p2):
                                if os.path.getmtime(_jpg_p2) <= os.path.getmtime(_mk_p2):
                                    UI.vprint(2, "   [SeaTex] Passage 2 : patch à fabriquer non retouché, DDS conservé : " + _fn_p2)
                                    continue
                                try:
                                    os.remove(_mk_p2)
                                except Exception:
                                    pass
                            # Cas 1 : nom DDS identique au JPG
                            _dds_name_p2 = _fn_p2.replace('.jpg', '.dds')
                            _dds_p2 = os.path.join(_textures_dir_p2, _dds_name_p2)
                            _sp.call([IMG.dds_convert_cmd, '-bc1', '-fast',
                                      _jpg_p2, _dds_p2],
                                     stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
                            _done_p2 += 1
                        except Exception as _ep2:
                            UI.vprint(2, '   [SeaTex] Passage 2 erreur : ' + str(_ep2))
                    if _done_p2 >= 1:
                        UI.vprint(1, tr("   [SeaTex] Passage 2 terminé — {n} DDS générés.").format(n=_done_p2))
    UI.vprint(1, " *Activating DSF file.")
    dsf_file_name = os.path.join(
        tile.build_dir,
        "Earth nav data",
        FNAMES.long_latlon(tile.lat, tile.lon) + ".dsf",
    )
    try:
        os.replace(dsf_file_name + ".tmp", dsf_file_name)
    except:
        UI.vprint(0, "ERROR : could not rename DSF file, tile is not actived.")
    # Nettoyage des PNG masques côtiers après DSF et DDS terminés (Option 1) :
    # - uniquement en mode imprint (masques cuits dans les DDS) ; en mode
    #   non-imprint les .ter référencent ces PNG via BORDER_TEX et XP12
    #   plante s'ils sont supprimés.
    # - chaque PNG n'est supprimé qu'après vérification que le DDS
    #   correspondant (même préfixe ty_tx_) a bien été créé.
    # - le seul PNG conservé est water_transition.png.
    if getattr(tile, "imprint_masks_to_dds", False):
        _tex_dir = os.path.join(tile.build_dir, "textures")
        _dds_prefixes = set()
        for _f in os.listdir(_tex_dir):
            if _f.endswith(".dds"):
                _p = _f.split("_")
                if len(_p) >= 2:
                    _dds_prefixes.add((_p[0], _p[1]))
        for _f in os.listdir(_tex_dir):
            if _f.endswith(".png") and _f != "water_transition.png":
                _p = _f.split("_")
                if len(_p) >= 2 and (_p[0], _p[1]) in _dds_prefixes:
                    try:
                        os.remove(os.path.join(_tex_dir, _f))
                    except:
                        pass
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
        # La signature suit le sort de son cache : la laisser seule n'aurait
        # aucun effet, mais autant garder le dossier propre.
        try:
            os.remove(FNAMES.apt_sig_file(tile))
        except:
            pass
    if UI.cleaning_level > 1 and not tile.grouped:
        remove_unwanted_textures(tile)
    # Lot A — surveillance mémoire en fin d'étape 3.
    # Tous les threads sont joints à ce point (build_dsf_thread.join,
    # download_thread.join, parallel_join des workers de conversion), donc
    # aucun traitement parallèle n'est en cours et gc.collect() ne peut figer
    # personne — d'où allow_gc=True. C'est le moment où la RAM est la plus
    # haute du build, et le seul point traversé par TOUS les chemins :
    # étape 3 seule, « All in one » (build_all) et build_tile_list.
    _check_mem(
        context=f"fin étape 3 tuile {FNAMES.short_latlon(tile.lat, tile.lon)}",
        allow_gc=True,
    )
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
            UI.vprint(1, tr("   [Batch] DSF .tmp corrompu supprimé : {name}").format(name=os.path.basename(dsf_tmp)))
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
                UI.vprint(0, tr("   [Batch] Tuile {tile} ignorée (erreur OSM) — batch continue.").format(tile=FNAMES.short_latlon(lat, lon)))
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_mesh:
            MESH.build_mesh(tile)
            if UI.red_flag:
                UI.vprint(0, tr("   [Batch] Tuile {tile} ignorée (erreur mesh) — batch continue.").format(tile=FNAMES.short_latlon(lat, lon)))
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_mask:
            MASK.build_masks(tile)
            if UI.red_flag:
                UI.vprint(0, tr("   [Batch] Tuile {tile} ignorée (erreur masque) — batch continue.").format(tile=FNAMES.short_latlon(lat, lon)))
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_dsf:
            build_tile(tile)
            if UI.red_flag:
                UI.vprint(0, tr("   [Batch] Tuile {tile} ignorée (erreur DSF/imagery) — batch continue.").format(tile=FNAMES.short_latlon(lat, lon)))
                _cleanup_corrupt_dsf(tile)  # Nettoyer le .tmp de cette tuile
                skipped.append((lat, lon))
                UI.red_flag = False
                continue
        if do_ovl:
            OVL.build_overlay(lat, lon)
            if UI.red_flag:
                UI.vprint(0, tr("   [Batch] Tuile {tile} ignorée (erreur overlay) — batch continue.").format(tile=FNAMES.short_latlon(lat, lon)))
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
    # Correctif shred86 1.40.13 : les .ter mer/eau portent les suffixes
    # _water, _sea, _overlay (et combinaisons _sea_overlay, _water_overlay)
    # alors que le DDS correspondant n'a pas de suffixe. L'ancien code en
    # déduisait un nom de DDS inexistant (ex: ..._sea.dds), et le vrai DDS
    # (couvert uniquement par des triangles mer, comme les patches mer)
    # était alors supprimé comme "obsolète" quand cleaning_level > 1.
    texture_list = []
    for f in os.listdir(os.path.join(tile.build_dir, "terrain")):
        if f[-4:] != ".ter":
            continue
        base = f[:-4]
        for _suffix in ("_overlay", "_sea", "_water"):
            if base.endswith(_suffix):
                base = base[: -len(_suffix)]
        texture_list.append(base + ".dds")
    for f in os.listdir(os.path.join(tile.build_dir, "textures")):
        if f[-4:] != ".dds":
            continue
        if f not in texture_list:
            print("Removing obsolete texture", f)
            try:
                os.remove(os.path.join(tile.build_dir, "textures", f))
            except:
                pass
