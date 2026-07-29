
#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland Lehmann (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland Lehmann (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================

# ============================================================
#  O4_Correction_Utils.py  —  ORTHO4XP V3
#  Module autonome « Correction imagerie et traitement de zone »
#
#  RÔLE (cible finale) :
#    - Fenêtre de correction imagerie (sélection éditeur GIMP + ouverture),
#      rapatriée ici depuis O4_Tile_Utils pour centraliser et sécuriser
#      toute la logique de correction dans un seul fichier isolé.
#    - « Visualiser la tuile » : preview des DDS (mosaïque, un carré par
#      DDS) — ajouté à l'étape suivante.
#    - JOSM : traité dans la fenêtre « Avancé (JOSM) »,
#      module autonome O4_Avance_Utils.
#
#  ÉTAT ACTUEL (transfert fidèle — comportement identique) :
#    La fenêtre _open_correction_window ci-dessous est la COPIE FIDÈLE de
#    celle qui vivait dans O4_Tile_Utils. Elle est désormais hébergée ici,
#    et le module l'ouvre lui-même (plus de dépendance à O4_Tile_Utils
#    pour cette fenêtre). L'original dans O4_Tile_Utils reste en place
#    (dormant) : rien n'est supprimé du pipeline validé.
#
#  RÈGLE : fichier autonome. Aucun fichier du pipeline (build, DSF,
#  textures, Sea) n'est modifié. En cas de problème, le bouton du GUI se
#  replie automatiquement sur l'ancienne fenêtre (voir
#  open_correction_module dans O4_GUI_Utils).
# ============================================================

import os


def _open_correction_window(parent_win, patch_dir, existing_files,
                             BG, FG, FG2, PREV_BG, FONT, FONT_T, _tr,
                             textures_dir=None, preview_corr_dir=None,
                             avert_patch=""):
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
             font=FONT, bg=BG, fg="#888888").pack(pady=(0, 2))

    # Avertissement non bloquant : la fenêtre s'ouvre même sans patch,
    # pour laisser l'accès à « Visualiser la tuile » et aux autres outils.
    if avert_patch:
        tk.Label(corr, text="⚠ " + avert_patch, font=FONT, bg=BG,
                 fg="#ffaa00", wraplength=760,
                 justify="center").pack(pady=(0, 6))
    else:
        tk.Frame(corr, bg=BG, height=6).pack()

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
    _nav_coche = [None]    # patch coché AUTOMATIQUEMENT par la navigation
                           # (permet de le décocher en quittant, sans toucher
                           #  aux coches manuelles — option douce)
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

    def _rebuild_list():
        for widget in inner.winfo_children():
            widget.destroy()
        _lignes.clear()
        _all = sorted(check_vars.keys())
        # Rubrique « à fabriquer » retirée : la détection des défauts se fait
        # désormais visuellement dans le preview de la tuile. Tous les patches
        # sont présentés dans une liste unique.
        _norm = _all

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
                     lambda e, f=fname: _naviguer(f))
            cb.config(command=lambda f=fname: _show_preview(f))
            _lignes[fname] = (row, cb, lbl)

        def _ajout_titre(texte):
            tk.Label(inner, text=texte, font=("TkFixedFont", 10, "bold"),
                     bg=BG, fg=FG, anchor="w").pack(fill=tk.X, pady=(6, 2))

        _ordre_affiche = []  # ordre visuel pour la navigation clavier
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

    def _naviguer(fname):
        # Option douce : naviguer/cliquer sur une ligne la COCHE et la
        # surligne ; on décoche UNIQUEMENT la ligne précédemment cochée par
        # la navigation (les coches manuelles faites via les cases restent
        # intactes → multi-sélection manuelle toujours possible).
        _prec = _nav_coche[0]
        if _prec is not None and _prec != fname and _prec in check_vars:
            try:
                check_vars[_prec].set(False)
            except Exception:
                pass
        if fname in check_vars:
            try:
                check_vars[fname].set(True)
            except Exception:
                pass
        _nav_coche[0] = fname
        _show_preview(fname)

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
            _naviguer(_nav_ordre[_i])
            return "break"
        _i = max(0, min(len(_nav_ordre) - 1, _i + delta))
        _naviguer(_nav_ordre[_i])
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

    def _visualiser_tuile():
        # ── Étape 2b1 : mosaïque des DDS de la tuile ─────────────────────
        # Lit les DDS de textures/ avec Pillow, fabrique une vignette par
        # DDS et les affiche en mosaïque. Les vignettes sont mises en cache
        # dans Preview_Correction/ (à l'intérieur du dossier de la tuile) et
        # ne sont régénérées que si le DDS a changé (comparaison des dates).
        # AUCUN fichier du pipeline n'est modifié ; lecture seule des DDS.
        # (Zoom et réglages fins d'affichage : étape 2b2.)
        viz = tk.Toplevel(corr)
        viz.title(_tr("Visualiser la tuile — Ortho4XP V3"))
        viz.configure(bg=BG)
        viz.transient(corr)
        viz.lift()
        viz.focus_force()

        tk.Label(viz, text=_tr("Visualiser la tuile"),
                 font=FONT_T, bg=BG, fg=FG).pack(pady=(12, 2))

        def _fin_simple(message):
            # Fenêtre minimale (message + Fermer) pour les cas sans DDS.
            tk.Label(viz, text=message, font=FONT, bg=BG,
                     fg="#888888").pack(pady=(0, 16), padx=24)
            ttk.Button(viz, text=_tr("Fermer"),
                       command=viz.destroy).pack(pady=(0, 16), ipadx=12, ipady=4)
            viz.update_idletasks()
            vw = max(480, viz.winfo_reqwidth())
            vh = max(200, viz.winfo_reqheight())
            viz.geometry(f"{vw}x{vh}+{(sw - vw) // 2}+{(sh - vh) // 2}")
            viz.minsize(vw, vh)

        if not textures_dir or not os.path.isdir(textures_dir):
            _fin_simple(_tr("Dossier textures introuvable pour cette tuile."))
            return

        dds_list = sorted(f for f in os.listdir(textures_dir)
                          if f.lower().endswith(".dds"))
        if not dds_list:
            _fin_simple(_tr("Aucun DDS dans le dossier textures de la tuile."))
            return

        lbl_info = tk.Label(viz, text=_tr("Préparation des vignettes…"),
                            font=FONT, bg=BG, fg="#888888")
        lbl_info.pack(pady=(0, 6))

        # Zone défilante (ascenseur vertical simple ; zoom en 2b2).
        frm_moz = tk.Frame(viz, bg=PREV_BG)
        frm_moz.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        sb = tk.Scrollbar(frm_moz, bg=BG, troughcolor=BG)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        cnv = tk.Canvas(frm_moz, bg=PREV_BG, highlightthickness=0,
                        yscrollcommand=sb.set)
        cnv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=cnv.yview)
        grid = tk.Frame(cnv, bg=PREV_BG)
        cnv.create_window((0, 0), window=grid, anchor="nw")

        # Cases à cocher de la mosaïque : dds_name -> BooleanVar
        _viz_checks = {}

        frm_viz_bot = tk.Frame(viz, bg=BG)
        frm_viz_bot.pack(pady=(4, 10))
        # Pas de bouton « Transférer » : c'est la CASE sous la vignette qui
        # transfère (voir _cocher_vignette). Un bouton en plus ferait
        # doublon et retransférerait ce qui est déjà dans la liste.
        ttk.Button(frm_viz_bot,
                   text=_tr("Effacer JPG source et relancer étape 3"),
                   command=lambda: _effacer_et_relancer()).pack(
                       side=tk.LEFT, padx=6, ipadx=8, ipady=4)
        ttk.Button(frm_viz_bot, text=_tr("Fermer"),
                   command=viz.destroy).pack(side=tk.LEFT, padx=6,
                                             ipadx=12, ipady=4)

        # Taille d'affichage des vignettes. Chaque vignette est placée dans la
        # grille ; le nombre de colonnes s'ajuste à la largeur de la fenêtre et
        # se recalcule quand on la redimensionne (voir _reflow plus bas), pour
        # que les vignettes passent à la ligne au lieu d'être coupées.
        THUMB = 192       # taille d'une vignette en pixels
        GAP = 12          # espacement entre vignettes
        MARGIN = 40       # marge intérieure gauche/droite de la mosaïque

        # Largeur d'ouverture de la fenêtre (bornée à l'écran) et nombre de
        # colonnes qui tiennent dans cette largeur.
        vw = min(sw - 80, max(760, 12 * (THUMB + GAP) + MARGIN))
        vh = min(sh - 120, 800)
        COLS = max(1, int((vw - MARGIN - 30) // (THUMB + GAP)))

        # Cache des vignettes DANS le dossier de la tuile (validé avec Roland).
        if preview_corr_dir:
            try:
                os.makedirs(preview_corr_dir, exist_ok=True)
            except Exception:
                pass

        _photos = []   # conserver les références (sinon Tkinter efface l'image)

        def _vignette(dds_name):
            # Vignette PNG en cache, (re)fabriquée seulement si nécessaire :
            # si le cache existe et est au moins aussi récent que le DDS, on
            # le réutilise. La taille est incluse dans le nom du cache :
            # changer THUMB régénère proprement, sans réutiliser une ancienne
            # taille (et prépare le zoom de l'étape 2b2).
            dds_path = os.path.join(textures_dir, dds_name)
            if not preview_corr_dir:
                return None
            cache_path = os.path.join(preview_corr_dir,
                                      dds_name + f".{THUMB}.png")
            try:
                if (os.path.isfile(cache_path) and
                        os.path.getmtime(cache_path) >= os.path.getmtime(dds_path)):
                    return cache_path
            except Exception:
                pass
            try:
                im = Image.open(dds_path).convert("RGB")
                im.thumbnail((THUMB, THUMB), Image.LANCZOS)
                im.save(cache_path, "PNG")
                return cache_path
            except Exception:
                return None

        # ── Duplication du JPG source (RÈGLE VALIDÉE) ────────────────────
        # On ne duplique JAMAIS le DDS (déjà compressé → perte de qualité) :
        # on copie le JPG source correspondant. Le ZL est LU dans le nom du
        # DDS (jamais figé). Si un patch existe déjà → on le garde. Sinon →
        # on copie UNIQUEMENT le JPG du provider ACTIF : sa cible est le nom
        # exact dérivé du DDS (col_row + provider + ZL), donc aucun provider
        # n'est codé en dur et les JPG des autres providers sont ignorés.
        # Les JPG source ne sont jamais modifiés (copie seule).
        def _dest_cible_zl(dds_name):
            import re as _re
            m = _re.search(r'(\d+)\.(?:dds|DDS)$', dds_name)
            parts = dds_name.split("_")
            if not m or len(parts) < 2:
                return (None, None, None)
            zl = m.group(1)
            # Même nom que le DDS, extension .jpg → JPG du provider actif.
            cible = os.path.splitext(dds_name)[0] + ".jpg"
            dest = os.path.join(os.path.dirname(patch_dir), "PATCH_" + zl)
            return (dest, cible, zl)

        def _patches_existants(dds_name):
            dest, cible, _zl = _dest_cible_zl(dds_name)
            if not dest or not cible:
                return []
            try:
                return [cible] if os.path.isfile(
                    os.path.join(dest, cible)) else []
            except Exception:
                return []

        def _dupliquer_jpg_source(dds_name):
            import shutil as _sh
            import O4_File_Names as _FN
            dest, cible, _zl = _dest_cible_zl(dds_name)
            if not dest or not cible:
                return ("erreur", [], None)
            try:
                os.makedirs(dest, exist_ok=True)
            except Exception:
                pass
            deja = _patches_existants(dds_name)
            if deja:
                return ("existe", deja, dest)
            # Recherche du SEUL JPG portant le nom exact (donc le provider
            # actif du DDS). Les JPG des autres providers sont ignorés.
            src = None
            try:
                for _r, _d, _files in os.walk(_FN.Imagery_dir):
                    if cible in _files:
                        src = os.path.join(_r, cible)
                        break
            except Exception:
                pass
            if not src:
                return ("aucune", [], dest)
            try:
                _sh.copy2(src, os.path.join(dest, cible))
            except Exception:
                return ("aucune", [], dest)
            return ("copie", [cible], dest)

        def _rafraichir_liste(copied, dest):
            # N'ajoute à la liste principale que les patches tombés dans le
            # dossier affiché (même ZL) ; les autres ZL restent corrects sur
            # disque mais hors de cette liste (mono-ZL, comportement existant).
            if not dest:
                return
            if os.path.normpath(dest) != os.path.normpath(patch_dir):
                return
            changed = False
            for f in copied:
                if f not in check_vars:
                    check_vars[f] = tk.BooleanVar(value=False)
                    changed = True
            if changed:
                try:
                    _rebuild_list()
                except Exception:
                    pass

        def _cocher_vignette(dds_name):
            """Case cochée sous une vignette → transfert immédiat vers la
            liste « JPG à corriger » de la fenêtre « Correction patches ».

            On copie le JPG SOURCE du provider actif (nom exact déduit du
            DDS, ZL lu dans le nom) dans PATCH_<ZL>/, puis on ajoute le
            fichier à la liste de gauche. Aucun DDS n'est modifié, aucun JPG
            source n'est modifié (copie seule) et un patch déjà présent est
            conservé tel quel. Décocher ne supprime rien (sécurité) : la
            suppression se fait avec « Supprimer patches sélectionnés »
            dans la fenêtre « Correction patches ».
            """
            var = _viz_checks.get(dds_name)
            court = "_".join(dds_name.split("_")[:2])
            if var is None or not var.get():
                return          # décocher ne supprime rien
            st, copied, dest = _dupliquer_jpg_source(dds_name)
            if st == "copie":
                _rafraichir_liste(copied, dest)
                lbl_info.config(
                    text=court + " — "
                    + _tr("transféré dans « JPG à corriger »"))
            elif st == "existe":
                _rafraichir_liste(copied, dest)
                lbl_info.config(
                    text=court + " — "
                    + _tr("déjà présent dans « JPG à corriger »"))
            else:
                var.set(False)
                lbl_info.config(
                    text=court + " — "
                    + _tr("aucun JPG source trouvé pour cette tuile"))

        def _jpg_source_path(dds_name):
            """Chemin du JPG source du provider ACTIF (nom exact déduit du
            DDS : col_row + provider + ZL). Aucun provider codé en dur."""
            import O4_File_Names as _FN
            _d, cible, _z = _dest_cible_zl(dds_name)
            if not cible:
                return None
            try:
                for _r, _sd, _files in os.walk(_FN.Imagery_dir):
                    if cible in _files:
                        return os.path.join(_r, cible)
            except Exception:
                pass
            return None

        def _effacer_et_relancer():
            """Supprime les JPG source cochés (provider actif) puis relance
            l'étape 3, qui les retéléchargera. Sert quand un téléchargement
            s'est mal déroulé : on repart d'une image saine au lieu de
            corriger inutilement à la main."""
            coches = [n for n, v in _viz_checks.items() if v.get()]
            if not coches:
                messagebox.showinfo(
                    _tr("Visualiser la tuile"),
                    _tr("Aucune vignette cochée."), parent=viz)
                return
            trouves = []
            for n in coches:
                p = _jpg_source_path(n)
                if p:
                    trouves.append((n, p))
            if not trouves:
                messagebox.showinfo(
                    _tr("Visualiser la tuile"),
                    _tr("Aucun JPG source trouvé pour cette tuile"),
                    parent=viz)
                return
            # Suppression définitive → confirmation explicite.
            if not messagebox.askyesno(
                    _tr("Effacer JPG source et relancer étape 3"),
                    _tr("Supprimer {n} JPG source puis relancer "
                        "l'étape 3 ?").format(n=len(trouves)),
                    parent=viz):
                return
            supprimes = 0
            for n, p in trouves:
                try:
                    os.remove(p)
                    supprimes += 1
                except Exception:
                    pass
            _relancer_etape3(supprimes)

        def _relancer_etape3(nb_supprimes):
            """Relance l'étape 3 (Build Imagery/DSF) : c'est elle qui
            retélécharge les JPG source supprimés. On s'appuie sur la méthode
            build_tile() de la fenêtre principale d'Ortho4XP (parent_win),
            qui est exactement le bouton « Build Imagery/DSF »."""
            lanceur = getattr(parent_win, "build_tile", None)
            if not callable(lanceur):
                messagebox.showinfo(
                    _tr("Effacer JPG source et relancer étape 3"),
                    _tr("Relancez l'étape 3 dans la fenêtre principale."),
                    parent=viz)
                return
            try:
                viz.destroy()
            except Exception:
                pass
            try:
                lanceur()
                messagebox.showinfo(
                    _tr("Effacer JPG source et relancer étape 3"),
                    _tr("{n} JPG source supprimé(s). Étape 3 relancée.").format(
                        n=nb_supprimes), parent=parent_win)
            except Exception:
                messagebox.showinfo(
                    _tr("Effacer JPG source et relancer étape 3"),
                    _tr("Relancez l'étape 3 dans la fenêtre principale."),
                    parent=parent_win)
        def _ouvrir_detail(start_idx):
            det = tk.Toplevel(viz)
            det.title(_tr("Détail de la tuile"))
            det.configure(bg=BG)
            _cur = [start_idx]

            # Dimensionnement borné à l'écran : on RÉSERVE la place des
            # libellés et des boutons du bas (CHROME) et une marge pour la
            # barre de menus / le dock macOS, sinon les boutons passent sous
            # le bord de l'écran.
            avail_w = max(400, sw - 120)
            avail_h = max(400, sh - 200)
            CHROME = 180
            side = int(min(avail_w, avail_h - CHROME, 1000))
            if side < 300:
                side = 300
            win_w = min(avail_w, side + 40)
            win_h = min(avail_h, side + CHROME)

            # Haut : titre + compteur.
            top = tk.Label(det, bg=BG, fg=FG,
                           font=("TkDefaultFont", 13, "bold"))
            info = tk.Label(det, bg=BG, fg=FG2)

            # Bas : case + statut + boutons (ancrés en bas → toujours visibles).
            _chk_var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(
                det, variable=_chk_var,
                text=_tr("À corriger (copier le JPG source)"),
                bg=BG, fg=FG, selectcolor=PREV_BG,
                activebackground=BG, activeforeground=FG,
                command=lambda: _on_check())
            status = tk.Label(det, bg=BG, fg=FG2)
            nav = tk.Frame(det, bg=BG)

            # Milieu : image.
            img_lbl = tk.Label(det, bg=PREV_BG, bd=1, relief="solid")

            def _charger(i):
                dds_name = dds_list[i]
                top.config(text="_".join(dds_name.split("_")[:2]))
                info.config(text=f"{i + 1} / {len(dds_list)}")
                try:
                    im = Image.open(
                        os.path.join(textures_dir, dds_name)).convert("RGB")
                    im = im.resize((side, side), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(im)
                    img_lbl.config(image=ph, text="")
                    img_lbl.image = ph        # anti-GC (widget)
                    det._detail_img = ph      # anti-GC (fenêtre)
                except Exception:
                    img_lbl.config(image="", text="?")
                if _patches_existants(dds_name):
                    status.config(
                        text=_tr("Un patch existe déjà pour cette tuile"))
                else:
                    status.config(text="")
                _chk_var.set(False)
                chk.config(state="normal")

            def _on_check():
                if not _chk_var.get():
                    return   # décocher ne supprime rien (sécurité)
                dds_name = dds_list[_cur[0]]
                st, copied, dest = _dupliquer_jpg_source(dds_name)
                if st == "copie":
                    status.config(
                        text=_tr("JPG source copié dans les patches"))
                    _rafraichir_liste(copied, dest)
                elif st == "existe":
                    status.config(
                        text=_tr("Un patch existe déjà pour cette tuile"))
                else:
                    status.config(
                        text=_tr("Aucun JPG source trouvé pour cette tuile"))
                    _chk_var.set(False)

            def _go(delta):
                n = len(dds_list)
                if n:
                    _cur[0] = (_cur[0] + delta) % n
                    _charger(_cur[0])

            ttk.Button(nav, text="< " + _tr("Précédent"),
                       command=lambda: _go(-1)).pack(side=tk.LEFT, padx=6)
            ttk.Button(nav, text=_tr("Suivant") + " >",
                       command=lambda: _go(1)).pack(side=tk.LEFT, padx=6)
            ttk.Button(nav, text=_tr("Fermer"),
                       command=det.destroy).pack(side=tk.LEFT, padx=6)

            # Ordre d'empilage : on réserve d'abord le HAUT puis le BAS, et
            # l'image prend la place restante. Ainsi les boutons du bas restent
            # visibles même si l'image est grande ou la fenêtre réduite.
            top.pack(side=tk.TOP, pady=(10, 2))
            info.pack(side=tk.TOP, pady=(0, 4))
            nav.pack(side=tk.BOTTOM, pady=(4, 10))
            status.pack(side=tk.BOTTOM, pady=(0, 2))
            chk.pack(side=tk.BOTTOM, pady=(2, 0))
            img_lbl.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                         padx=10, pady=6)

            det.bind("<Left>", lambda e: _go(-1))
            det.bind("<Right>", lambda e: _go(1))
            det.bind("<Escape>", lambda e: det.destroy())

            _charger(_cur[0])
            x = max(10, (sw - win_w) // 2)
            y = max(30, (sh - win_h) // 2)
            det.geometry(f"{win_w}x{win_h}+{x}+{y}")
            try:
                det.minsize(360, 360)
                det.resizable(True, True)
                det.transient(viz)
                det.focus_set()
            except Exception:
                pass

        def _bind_click_rec(w, i):
            # Clic sur la vignette (ou son cadre/numéro) → fenêtre de détail.
            try:
                w.bind("<Button-1>", lambda e, ii=i: _ouvrir_detail(ii))
                w.config(cursor="hand2")
            except Exception:
                pass
            for c in w.winfo_children():
                _bind_click_rec(c, i)

        total = len(dds_list)
        _cells = []            # cellules gardées pour les repositionner
        for idx, dds_name in enumerate(dds_list):
            cache_path = _vignette(dds_name)
            cell = tk.Frame(grid, bg=PREV_BG)
            cell.grid(row=idx // COLS, column=idx % COLS,
                      padx=GAP // 2, pady=GAP // 2)
            _cells.append(cell)
            drawn = False
            if cache_path:
                try:
                    ph = ImageTk.PhotoImage(Image.open(cache_path))
                    _photos.append(ph)
                    _lbl_img = tk.Label(cell, image=ph, bg=PREV_BG,
                                        bd=1, relief="solid")
                    # IMPORTANT (Tkinter) : garder une référence de l'image
                    # SUR le widget lui-même. Sans cela, l'image est effacée
                    # de la mémoire dès la fin de la fonction et le carré
                    # devient vide (seuls le cadre et le numéro restent).
                    _lbl_img.image = ph
                    _lbl_img.pack()
                    drawn = True
                except Exception:
                    drawn = False
            if not drawn:
                tk.Label(cell, text="?", width=12, height=6,
                         bg=PREV_BG, fg="#ff4444",
                         bd=1, relief="solid").pack()
            # Libellé court : préfixe col_row (seule partie stable du nom).
            _short = "_".join(dds_name.split("_")[:2])
            tk.Label(cell, text=_short, font=("TkFixedFont", 8),
                     bg=PREV_BG, fg=FG2).pack()
            # Vignette cliquable → fenêtre de détail (image en grand).
            _bind_click_rec(cell, idx)
            # Case à cocher AJOUTÉE APRÈS le binding : cliquer la case ne doit
            # pas ouvrir la fenêtre de détail.
            _v = tk.BooleanVar(value=False)
            _viz_checks[dds_name] = _v
            tk.Checkbutton(cell, variable=_v, bg=PREV_BG, fg=FG,
                           selectcolor=BG, activebackground=PREV_BG,
                           activeforeground=FG,
                           highlightthickness=0, bd=0,
                           command=lambda d=dds_name: _cocher_vignette(d)
                           ).pack()
            # Garder l'interface réactive pendant la 1re génération du cache.
            if idx % 8 == 0:
                lbl_info.config(
                    text=_tr("Préparation des vignettes…")
                    + f"  {idx + 1}/{total}")
                try:
                    viz.update()
                except Exception:
                    pass

        lbl_info.config(text=f"{total} DDS")
        # Conserver les images sur la fenêtre elle-même : elles doivent
        # survivre à la fin de _visualiser_tuile(), sinon Tkinter les efface.
        viz._vignette_photos = _photos
        grid.update_idletasks()
        try:
            cnv.config(scrollregion=cnv.bbox("all"))
        except Exception:
            pass

        # ── Réagencement responsive ──────────────────────────────────────
        # Quand la fenêtre est rétrécie, on recalcule le nombre de colonnes
        # d'après la largeur DISPONIBLE et on REPOSITIONNE les cellules
        # existantes (jamais de destruction → aucune image perdue). Les
        # vignettes qui ne tiennent plus passent à la ligne et deviennent
        # accessibles via l'ascenseur vertical.
        _last_cols = [COLS]

        def _reflow(event=None):
            avail = cnv.winfo_width()
            if avail < 50:
                return
            cols = max(1, int((avail - MARGIN) // (THUMB + GAP)))
            if cols == _last_cols[0]:
                return
            _last_cols[0] = cols
            for i, c in enumerate(_cells):
                try:
                    c.grid_configure(row=i // cols, column=i % cols)
                except Exception:
                    pass
            grid.update_idletasks()
            try:
                cnv.config(scrollregion=cnv.bbox("all"))
            except Exception:
                pass

        _reflow_after = [None]

        def _on_configure(event=None):
            # Regroupe les nombreux évènements émis pendant le glissement.
            if _reflow_after[0] is not None:
                try:
                    viz.after_cancel(_reflow_after[0])
                except Exception:
                    pass
            _reflow_after[0] = viz.after(120, _reflow)

        cnv.bind("<Configure>", _on_configure)

        viz.geometry(f"{int(vw)}x{int(vh)}"
                     f"+{(sw - int(vw)) // 2}+{(sh - int(vh)) // 2}")
        # Taille mini : en-tête + une partie de la mosaïque + barre de boutons
        # (Effacer / Fermer) restent toujours visibles quand on réduit ;
        # la mosaïque se réagence (reflow) et l'agrandissement reste libre.
        viz.minsize(800, 460)

    def _supprimer_preview():
        """Supprime le dossier Preview_Correction de la tuile. Ce cache de
        vignettes ne sert qu'à l'affichage dans Ortho4XP : il est inutile
        pour X-Plane et alourdit le dossier de la tuile (une grande tuile de
        plus de 1000 DDS produit autant de vignettes). Il est régénéré
        automatiquement au prochain « Visualiser la tuile »."""
        import shutil as _sh
        if not preview_corr_dir or not os.path.isdir(preview_corr_dir):
            messagebox.showinfo(
                _tr("Suppression dossier Preview"),
                _tr("Aucun dossier Preview à supprimer."), parent=corr)
            return
        try:
            _nb = sum(len(f) for _r, _d, f in os.walk(preview_corr_dir))
        except Exception:
            _nb = 0
        if not messagebox.askyesno(
                _tr("Suppression dossier Preview"),
                _tr("Supprimer le dossier Preview ({n} fichiers) ?").format(
                    n=_nb), parent=corr):
            return
        try:
            _sh.rmtree(preview_corr_dir)
            messagebox.showinfo(
                _tr("Suppression dossier Preview"),
                _tr("Dossier Preview supprimé ({n} fichiers).").format(n=_nb),
                parent=corr)
        except Exception as _e:
            messagebox.showerror(
                _tr("Suppression dossier Preview"), str(_e), parent=corr)

    # ── Ligne 1 : actions génériques ─────────────────────────────────
    ttk.Button(frm_bot, text=_tr("Visualiser la tuile"),
               command=_visualiser_tuile).grid(row=0, column=0, padx=6,
                                               ipadx=10, ipady=4)
    ttk.Button(frm_bot, text=_tr("Supprimer patches sélectionnés"),
               command=_delete_selected).grid(row=0, column=1, padx=6,
                                              ipadx=10, ipady=4)
    ttk.Button(frm_bot, text=_tr("Fermer"),
               command=corr.destroy).grid(row=0, column=2, padx=6,
                                          ipadx=10, ipady=4)

    # ── Ligne 2 : sélection ──────────────────────────────────────────
    ttk.Button(frm_bot, text=_tr("Tout cocher"),
               command=_sel_all).grid(row=1, column=0, padx=6, pady=(8, 0),
                                      ipadx=8, ipady=4)
    ttk.Button(frm_bot, text=_tr("Tout décocher"),
               command=_sel_none).grid(row=1, column=1, padx=6, pady=(8, 0),
                                       ipadx=8, ipady=4)
    ttk.Button(frm_bot, text=_tr("Suppression dossier Preview"),
               command=_supprimer_preview).grid(row=1, column=2, padx=6,
                                                pady=(8, 0), ipadx=8, ipady=4)

    # ── Ligne 3 : GIMP ───────────────────────────────────────────────
    # Le cadre QGIS a été retiré : QGIS est désormais géré dans la
    # fenêtre « Altimétrie / DEM » (choix de l'application + ouverture
    # du .tif assemblé). Un seul endroit pour QGIS, pas deux.
    # Le cadre JOSM « à venir » a lui aussi été retiré : les couches JOSM
    # sont désormais regroupées dans la fenêtre « Avancé (JOSM) »
    # (module O4_Avance_Utils). Un seul endroit pour JOSM, pas deux.
    frm_tools = tk.Frame(frm_bot, bg=BG)
    frm_tools.grid(row=2, column=0, columnspan=3, pady=(12, 0), sticky="ew")

    gimp_lf = tk.LabelFrame(frm_tools, text=_tr("GIMP"),
                            bg=BG, fg=FG, font=FONT)
    gimp_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ttk.Button(gimp_lf, text=_tr("Correction (choisir application)"),
               command=_choose_editor).pack(fill=tk.X, padx=8, pady=(6, 3),
                                            ipady=3)
    ttk.Button(gimp_lf, text=_tr("Ouvrir dans l'éditeur"),
               command=_open_in_editor).pack(fill=tk.X, padx=8, pady=(3, 8),
                                             ipady=3)

    corr.update_idletasks()
    ww = max(960, corr.winfo_reqwidth())
    wh = max(640, corr.winfo_reqheight())
    corr.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
    corr.minsize(700, 500)


def open_correction_window(gui):
    """Point d'entrée du module, appelé par le bouton « Correction imagerie/zone ».

    Prépare le contexte (tuile, ZL, dossier PATCH, thème) exactement comme
    le faisait le GUI, puis ouvre la fenêtre de correction hébergée dans ce
    module. Autonome : ne dépend plus de O4_Tile_Utils pour cette fenêtre.
    """
    from tkinter import messagebox
    try:
        from O4_Lang import tr
    except Exception:
        def tr(k): return k
    import O4_File_Names as FNAMES

    try:
        lat = int(gui.lat.get() or 0)
        lon = int(gui.lon.get() or 0)
        sign_lat = "+" if lat >= 0 else "-"
        sign_lon = "+" if lon >= 0 else "-"
        tile_key = f"{sign_lat}{abs(lat):02d}{sign_lon}{abs(lon):03d}"
        try:
            zl = int(gui.default_zl.get())
        except Exception:
            zl = 17
        patch_dir = os.path.join(FNAMES.Patch_dir, tile_key, f"PATCH_{zl}")
        # L'absence de patches n'est PLUS bloquante : la fenêtre s'ouvre
        # quand même, car « Visualiser la tuile » et les autres outils ne
        # dépendent pas des patches. On se contente d'informer.
        # (La liste de gauche « JPG à corriger » sera simplement vide.)
        _avert_patch = ""
        if not os.path.isdir(patch_dir):
            _avert_patch = tr("Aucun dossier PATCH pour cette tuile "
                              "(Step 2.1 non lancé).")
            existing = []
        else:
            existing = sorted(f for f in os.listdir(patch_dir)
                              if f.endswith(".jpg"))
            if not existing:
                _avert_patch = tr("Aucun patch JPG dans :") + " " + patch_dir
        # Couleurs thème (identique au GUI historique)
        try:
            import O4_Theme_Manager as _TM
            _t = _TM.get_theme()
            BG      = _t.get("patch_bg",      _t.get("bg",          "#0a1a0a"))
            FG      = _t.get("patch_fg",      _t.get("fg",          "#00cc44"))
            FG2     = _t.get("patch_fg2",     _t.get("fg_secondary","#88ffaa"))
            PREV_BG = _t.get("patch_prev_bg", _t.get("canvas_bg",   "#050f05"))
        except Exception:
            BG, FG, FG2, PREV_BG = "#0a1a0a", "#00cc44", "#88ffaa", "#050f05"
        FONT   = ("TkFixedFont", 11)
        FONT_T = ("TkFixedFont", 13)
        try:
            from O4_Lang import tr as _tr
        except Exception:
            def _tr(k): return k
        # Dossier textures/ de la tuile — obtenu EXACTEMENT comme le GUI le
        # fait lui-même (O4_GUI_Utils : build_dir + "textures"). Le cache des
        # vignettes vit dans Preview_Correction/ À L'INTÉRIEUR de la tuile
        # (validé avec Roland) : aucune collision entre tuiles, et il part
        # avec la tuile si elle est supprimée/reconstruite.
        try:
            custom = gui.custom_build_dir.get() or ""
        except Exception:
            custom = ""
        try:
            build_dir = FNAMES.build_dir(lat, lon, custom)
            textures_dir = os.path.join(build_dir, "textures")
            preview_corr_dir = os.path.join(build_dir, "Preview_Correction")
        except Exception:
            textures_dir = None
            preview_corr_dir = None
        _open_correction_window(
            gui, patch_dir, existing,
            BG, FG, FG2, PREV_BG, FONT, FONT_T, _tr,
            textures_dir=textures_dir, preview_corr_dir=preview_corr_dir,
            avert_patch=_avert_patch)
    except Exception as _e:
        messagebox.showerror(tr("Correction imagerie/zone"), str(_e))
