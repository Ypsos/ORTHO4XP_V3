# ============================================================
#  O4_Bathymetrie_Utils.py  —  ORTHO4XP V3
#  Module autonome « Bathymétrie / relevés de fonds »
#
#  RÔLE :
#    Jumeau du module Altimétrie, mais pour les RELEVÉS DE FONDS MARINS
#    (bathymétrie). Un seul bouton lit les fichiers bathymétriques d'un
#    dossier, les reprojette en EPSG:4326, les découpe à l'emprise de la
#    tuile élargie du débord, les fusionne, écrit <tuile>.tif à côté, et
#    renseigne « custom_bathy_dem » dans le cfg de la tuile (et NON
#    custom_dem, qui reste le relief terrestre).
#
#  POURQUOI UN MODULE SÉPARÉ :
#    Le relief terrestre (custom_dem) et les fonds marins
#    (custom_bathy_dem) sont deux sources DISTINCTES qui ne doivent
#    jamais se mélanger : la terre peut venir de l'IGN / Sonny, les fonds
#    du SHOM. C'est exactement la séparation ajoutée dans O4_Bathymetry.py
#    et O4_Config_Utils.py ; ce module en est l'outil de préparation.
#
#  RÉUTILISATION (aucune duplication) :
#    Tout le MOTEUR raster (reprojection, assainissement des valeurs
#    aberrantes, fusion, préparation/réduction, auto-test) est celui,
#    déjà validé, de O4_Altimetrie_Utils.py : il est purement géométrique
#    et se moque de savoir si les altitudes sont positives (relief) ou
#    négatives (profondeurs). Il est donc IMPORTÉ tel quel. Seuls
#    changent ici : les noms de dossiers, les clés de configuration, la
#    clé écrite dans le cfg de tuile (custom_bathy_dem) et les libellés.
#
#  RÈGLES RESPECTÉES :
#    - Fichier NEUF. Aucun fichier du pipeline n'est modifié.
#    - Aucune commande Terminal ; tout passe par rasterio.
#    - Le CRS source n'est jamais codé en dur (lu dans le fichier).
#    - Les fichiers sources ne sont jamais modifiés (lecture seule).
#    - custom_bathy_dem est écrit SANS toucher custom_dem : les deux
#      altimétries coexistent dans le même cfg de tuile.
# ============================================================

import os

# ── Moteur raster + logique pure, réutilisés depuis le module Altimétrie
#    (déjà validés, purement géométriques : négatifs = profondeurs). ──
from O4_Altimetrie_Utils import (
    tile_key,
    tile_bounds,
    intersecte,
    assainir_altitudes,
    lister_sources,
    sources_depuis_dossier,
    assembler_tuile,
    preparer_pays,
    resolution_metres,
    rasterio_disponible,
    auto_test,
    _lire_cfg_valeur,
    DEBORD_DEFAUT,
    _EXT_RASTER,
    _CRS_REPLI,
)

# ── Structure imposée propre à la bathymétrie (créée au 1er lancement) ─
#   <racine choisie>/Bathymétrie/
#       ├── Bathymétrie TIFF/<Pays>/      ← relevés déposés (EPSG:4326)
#       └── Bathymétrie assemble/
#             └── Assemble <Pays>/<tuile>/<tuile>.tif
DOSSIER_RACINE = "Bathymétrie"
DOSSIER_STOCK = "Bathymétrie TIFF"
DOSSIER_ASSEMBLE = "Bathymétrie assemble"
PREFIXE_PAYS_ASSEMBLE = "Assemble "

CFG_RACINE = "bathy_root_dir"      # ANCIEN — conservé pour la reprise
CFG_PAYS = "bathy_last_country"    # ANCIEN — conservé pour la reprise
CFG_STOCK = "bathy_stock_dir"      # dossier des relevés, choisi par l'utilisateur
CFG_SORTIE = "bathy_output_dir"    # dossier du résultat assemblé
CFG_QGIS = "qgis_app"              # application QGIS (partagée avec Altimétrie)


def chemins_structure(racine):
    """Retourne (stock, assemble) pour une racine <...>/Bathymétrie."""
    return (os.path.join(racine, DOSSIER_STOCK),
            os.path.join(racine, DOSSIER_ASSEMBLE))


def creer_structure(base, pays):
    """Crée la structure complète. Idempotent : ne détruit jamais rien.
    Retourne (racine, stock_pays, assemble_pays)."""
    racine = os.path.join(base, DOSSIER_RACINE) \
        if os.path.basename(os.path.normpath(base)) != DOSSIER_RACINE \
        else base
    stock, assemble = chemins_structure(racine)
    stock_pays = os.path.join(stock, pays)
    assemble_pays = os.path.join(assemble, PREFIXE_PAYS_ASSEMBLE + pays)
    for d in (racine, stock, assemble, stock_pays, assemble_pays):
        os.makedirs(d, exist_ok=True)
    return racine, stock_pays, assemble_pays


def creer_pays_dans(racine, pays, cible):
    """Crée le dossier d'un pays dans UN SEUL des deux dossiers, jamais
    dans les deux :
      cible="stock"  → <racine>/Bathymétrie TIFF/<pays>
      cible="sortie" → <racine>/Bathymétrie assemble/Assemble <pays>
    Retourne le chemin du dossier créé."""
    stock, assemble = chemins_structure(racine)
    if cible == "stock":
        pays_dir = os.path.join(stock, pays)
    else:
        pays_dir = os.path.join(assemble, PREFIXE_PAYS_ASSEMBLE + pays)
    os.makedirs(pays_dir, exist_ok=True)
    return pays_dir


def lister_pays(racine):
    """Pays présents dans le stock."""
    stock, _a = chemins_structure(racine)
    if not os.path.isdir(stock):
        return []
    return sorted(d for d in os.listdir(stock)
                  if not d.startswith(".")
                  and os.path.isdir(os.path.join(stock, d)))


def maj_cfg_lignes(lignes, chemin):
    """Remplace (ou ajoute) custom_bathy_dem SANS toucher aux autres
    lignes — en particulier custom_dem (le relief) reste intact."""
    out = []
    trouve = False
    for l in lignes:
        if l.startswith("custom_bathy_dem="):
            out.append("custom_bathy_dem=%s\n" % chemin)
            trouve = True
        else:
            out.append(l)
    if not trouve:
        out.append("custom_bathy_dem=%s\n" % chemin)
    return out


def ecrire_custom_bathy_dem(cfg_path, chemin_tif):
    """Écrit custom_bathy_dem dans le cfg de la tuile. Le cfg est créé
    s'il n'existe pas. Aucune autre clé n'est touchée (custom_dem inclus)."""
    lignes = []
    if os.path.isfile(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            lignes = f.readlines()
    lignes = maj_cfg_lignes(lignes, chemin_tif)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(lignes)


def open_bathymetrie_window(gui):
    """Point d'entrée du module, appelé par le bouton « Bathymétrie ».

    Au premier lancement, un assistant crée la structure imposée. Ensuite,
    le module trouve seul les sources qui recouvrent la tuile.
    """
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import subprocess
    import sys

    try:
        from O4_Lang import tr as _tr
    except Exception:
        def _tr(k):
            return k

    import O4_File_Names as FNAMES

    def _app_cfg():
        return os.path.join(FNAMES.Ortho4XP_dir, "Ortho4XP.cfg")

    def _cfg_get(cle):
        return _lire_cfg_valeur(_app_cfg(), cle)

    def _cfg_set(cle, valeur):
        try:
            p = _app_cfg()
            lignes = []
            trouve = False
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.startswith(cle + "="):
                            lignes.append("%s=%s\n" % (cle, valeur))
                            trouve = True
                        else:
                            lignes.append(l)
            if not trouve:
                lignes.append("%s=%s\n" % (cle, valeur))
            with open(p, "w", encoding="utf-8") as f:
                f.writelines(lignes)
        except Exception:
            pass

    try:
        lat = int(gui.lat.get() or 0)
        lon = int(gui.lon.get() or 0)
    except Exception:
        messagebox.showerror(_tr("Bathymétrie"),
                             _tr("Latitude / longitude invalides."))
        return

    cle = tile_key(lat, lon)

    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
        BG = _t.get("patch_bg", _t.get("bg", "#0a1a0a"))
        FG = _t.get("patch_fg", _t.get("fg", "#00cc44"))
        FG2 = _t.get("patch_fg2", _t.get("fg_secondary", "#88ffaa"))
        PREV_BG = _t.get("patch_prev_bg", _t.get("canvas_bg", "#050f05"))
    except Exception:
        BG, FG, FG2, PREV_BG = "#0a1a0a", "#00cc44", "#88ffaa", "#050f05"
    FONT = ("TkFixedFont", 11)
    FONT_T = ("TkFixedFont", 13)

    root_ref = None
    try:
        root_ref = tk._default_root
    except Exception:
        pass
    win = tk.Toplevel(root_ref) if root_ref else tk.Toplevel(gui)
    win.title(_tr("Bathymétrie — Ortho4XP V3"))
    win.configure(bg=BG)
    # Rattachée au GUI : elle ne se perd jamais derrière la fenêtre
    # principale après une boîte de dialogue.
    try:
        win.transient(gui)
    except Exception:
        pass
    win.lift()
    win.focus_force()

    def _remonter():
        """Ramène la fenêtre au premier plan. Appelée après chaque boîte
        de dialogue : sous macOS, la fenêtre repasse sinon derrière le
        GUI et donne l'impression de s'être fermée."""
        try:
            win.deiconify()
            win.lift()
            win.focus_force()
            win.attributes("-topmost", True)
            win.after(300, lambda: win.attributes("-topmost", False))
        except Exception:
            pass
    def _saisie(titre, message, parent=None, initialvalue=""):
        """Saisie de texte au thème du projet.

        Remplace tkinter.simpledialog.askstring : ce dernier n'hérite pas
        du thème sombre et affichait un bouton « Cancel » blanc sur fond
        blanc, donc illisible. Même signature que askstring, retourne la
        chaîne saisie ou None si l'utilisateur annule.
        """
        res = {"v": None}
        par = parent if parent is not None else win

        dlg = tk.Toplevel(par)
        dlg.title(titre)
        dlg.configure(bg=BG)
        try:
            dlg.transient(par)
        except Exception:
            pass
        dlg.resizable(False, False)
        dlg.columnconfigure(0, weight=1)

        tk.Label(dlg, text=message, bg=BG, fg=FG, font=FONT,
                 justify="left", anchor="w").grid(
            row=0, column=0, padx=14, pady=(14, 6), sticky="w")

        var = tk.StringVar(value=initialvalue or "")
        ent = tk.Entry(dlg, textvariable=var, width=46, bg=PREV_BG, fg=FG2,
                       bd=0, insertbackground=FG, highlightthickness=1,
                       highlightbackground=FG, highlightcolor=FG,
                       font=("TkFixedFont", 12))
        ent.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

        bar = tk.Frame(dlg, bg=BG)
        bar.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")

        def _ok(_e=None):
            res["v"] = var.get()
            dlg.destroy()

        def _annuler(_e=None):
            res["v"] = None
            dlg.destroy()

        ttk.Button(bar, text=_tr("Valider"), command=_ok).pack(side="left")
        ttk.Button(bar, text=_tr("Annuler"),
                   command=_annuler).pack(side="right")

        dlg.bind("<Return>", _ok)
        dlg.bind("<Escape>", _annuler)
        dlg.protocol("WM_DELETE_WINDOW", _annuler)
        ent.focus_set()
        try:
            ent.selection_range(0, "end")
        except Exception:
            pass
        try:
            dlg.update_idletasks()
            _x = par.winfo_rootx() + max(
                0, (par.winfo_width() - dlg.winfo_reqwidth()) // 2)
            _y = par.winfo_rooty() + 120
            dlg.geometry("+%d+%d" % (_x, _y))
        except Exception:
            pass
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.wait_window()
        return res["v"]

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()

    tk.Label(win, text=_tr("Bathymétrie") + "  —  " + cle,
             font=FONT_T, bg=BG, fg=FG).pack(pady=(12, 2))
    tk.Label(win,
             text=_tr("Structure  →  Préparer les données (une fois par "
                      "pays)  →  Assembler la tuile"),
             font=FONT, bg=BG, fg="#888888").pack(pady=(0, 2))
    lbl_etat = tk.Label(win, text="", font=FONT, bg=BG, fg="#888888")
    lbl_etat.pack(pady=(0, 6))

    # ── Journal ──────────────────────────────────────────────────────
    frm_log = tk.Frame(win, bg=BG)
    frm_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 4))
    sb = tk.Scrollbar(frm_log, bg=BG, troughcolor=BG)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    txt = tk.Text(frm_log, bg=PREV_BG, fg=FG2, font=("TkFixedFont", 10),
                  height=18, width=92, yscrollcommand=sb.set,
                  highlightthickness=1, highlightbackground="#1a4a1a")
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.config(command=txt.yview)

    import queue as _queue
    import threading as _threading
    _fil = _queue.Queue()

    def _log(m=""):
        """Journalise. Appelable depuis n'importe quel thread : si on
        n'est pas dans le thread de l'interface, le message passe par une
        file d'attente vidée par _pomper()."""
        if _threading.current_thread() is _threading.main_thread():
            try:
                txt.insert(tk.END, m + "\n")
                txt.see(tk.END)
                win.update()
            except Exception:
                pass
        else:
            _fil.put(m)

    def _pomper():
        """Vide la file d'attente dans le journal. Rappelée toutes les
        100 ms tant qu'un travail de fond est en cours : l'interface
        reste vivante et l'utilisateur voit l'avancement."""
        try:
            while True:
                txt.insert(tk.END, _fil.get_nowait() + "\n")
                txt.see(tk.END)
        except Exception:
            pass

    def _etat(m, couleur="#888888"):
        # L'utilisateur n'est JAMAIS laissé sans information : chaque
        # opération annonce son début et sa fin.
        try:
            lbl_etat.config(text=m, fg=couleur)
            win.update()
        except Exception:
            pass

    _boutons = []
    _travail = [False]
    _anim = [0]

    def _animer(message):
        """Indicateur d'activité : l'utilisateur n'a jamais l'impression
        que l'application est figée."""
        if not _travail[0]:
            return
        _anim[0] = (_anim[0] + 1) % 4
        _etat(message + " " + ("." * _anim[0]).ljust(3), FG)
        _pomper()
        win.after(400, lambda: _animer(message))

    # ── Les deux seuls chemins du module ─────────────────────────────
    # AUCUN nom de dossier n'est imposé : l'utilisateur désigne son
    # dossier de sources et son dossier de sortie, tels qu'ils existent
    # chez lui. Les deux sont mémorisés dans Ortho4XP.cfg.
    _stock = [_cfg_get(CFG_STOCK)]
    _sortie = [_cfg_get(CFG_SORTIE)]
    _dossier_tuile = [""]
    _src_var = tk.StringVar()
    _out_var = tk.StringVar()

    def _maj_bandeaux():
        """Rappel permanent des deux dossiers, en bas de la fenêtre."""
        _src_var.set(_stock[0] or _tr("(non configuré)"))
        _out_var.set(os.path.join(_sortie[0], cle) if _sortie[0]
                     else _tr("(non configurée)"))

    # Reprise d'une configuration faite avec l'ancienne structure
    # imposée : on retrouve les dossiers réels sans rien redemander.
    if not _stock[0]:
        _anc_r = _cfg_get(CFG_RACINE)
        _anc_p = _cfg_get(CFG_PAYS)
        if _anc_r and os.path.isdir(_anc_r):
            _s_anc, _a_anc = chemins_structure(_anc_r)
            _cand_s = os.path.join(_s_anc, _anc_p) if _anc_p else _s_anc
            _cand_a = os.path.join(_a_anc, PREFIXE_PAYS_ASSEMBLE + _anc_p) \
                if _anc_p else _a_anc
            _stock[0] = _cand_s if os.path.isdir(_cand_s) else _s_anc
            _sortie[0] = _cand_a if os.path.isdir(_cand_a) else _a_anc
            _cfg_set(CFG_STOCK, _stock[0])
            _cfg_set(CFG_SORTIE, _sortie[0])

    # ── Assistant : désignation des deux dossiers ────────────────────
    def _choisir_stock():
        """Dossier où l'utilisateur dépose ses bathymétries sources."""
        d = filedialog.askdirectory(
            parent=win, initialdir=_stock[0] or os.path.expanduser("~"),
            title=_tr("Dossier de vos bathymétries sources (.tif, .asc…)"))
        _remonter()
        if not d:
            return False
        _stock[0] = d
        _cfg_set(CFG_STOCK, d)
        _maj_bandeaux()
        return True

    def _choisir_sortie():
        """Dossier où sera écrit le fichier assemblé de la tuile."""
        d = filedialog.askdirectory(
            parent=win,
            initialdir=_sortie[0] or _stock[0] or os.path.expanduser("~"),
            title=_tr("Dossier de destination des bathymétries assemblées"))
        _remonter()
        if not d:
            return False
        _sortie[0] = d
        _cfg_set(CFG_SORTIE, d)
        _maj_bandeaux()
        return True

    def _creer_structure():
        """Premier usage sans organisation existante : crée l'arborescence
        par défaut et renseigne les deux dossiers. Personne n'est obligé
        de s'en servir : ceux qui ont déjà leurs dossiers utilisent les
        boutons « Dossier des sources » et « Dossier de sortie »."""
        messagebox.showinfo(
            _tr("Bathymétrie"),
            _tr("Choisissez le disque ou le dossier où créer votre "
                "organisation des bathymétries (un disque externe "
                "convient)."), parent=win)
        _remonter()
        base = filedialog.askdirectory(
            parent=win,
            title=_tr("Où créer l'organisation des bathymétries"))
        _remonter()
        if not base:
            return False
        # Garde-fou : si le dossier choisi est DÉJÀ dans une structure
        # existante, on remonte à sa racine au lieu d'en empiler une
        # seconde (c'est ce qui produisait des chemins en doublon).
        _parts = os.path.normpath(base).split(os.sep)
        if DOSSIER_RACINE in _parts:
            base = os.sep.join(_parts[:_parts.index(DOSSIER_RACINE)]) or os.sep
        pays = _saisie(
            _tr("Bathymétrie"),
            _tr("Nom du pays (ex. : France, Suisse, Allemagne) :"),
            parent=win, initialvalue="France")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        _etat(_tr("Création de la structure…"), FG)
        try:
            racine, stock_pays, assemble_pays = creer_structure(base, pays)
        except Exception as e:
            _etat("")
            messagebox.showerror(_tr("Bathymétrie"), str(e), parent=win)
            _remonter()
            return False
        _stock[0] = stock_pays
        _sortie[0] = assemble_pays
        _cfg_set(CFG_STOCK, stock_pays)
        _cfg_set(CFG_SORTIE, assemble_pays)
        _maj_bandeaux()
        _etat(_tr("Structure créée."), FG)
        txt.delete("1.0", tk.END)
        _log(_tr("Structure créée :"))
        _log("   " + racine)
        _log()
        _log(_tr("Dossier des sources :"))
        _log("   " + stock_pays)
        _log(_tr("Dossier de sortie :"))
        _log("   " + assemble_pays)
        _log()
        _log(_tr("Les sources doivent être en EPSG:4326 — X-Plane ne lit"))
        _log(_tr("aucune autre projection. Ortho4XP convertira au besoin,"))
        _log(_tr("mais préparez-les de préférence en 4326."))
        _log()
        _log(_tr("Le résultat assemblé sera écrit dans :"))
        _log("   " + os.path.join(assemble_pays, cle, cle + ".tif"))
        messagebox.showinfo(
            _tr("Bathymétrie"),
            _tr("Structure créée.\n\nDéposez vos bathymétries dans :\n{d}"
                "\n\nFormat requis : EPSG:4326.").format(d=stock_pays),
            parent=win)
        _remonter()
        return True

    def _racine_structure():
        """Déduit la racine <...>/Bathymétrie d'une structure DÉJÀ créée,
        à partir du dossier des sources courant. Retourne la racine si
        le dossier courant appartient bien à la structure imposée
        (<racine>/Bathymétrie TIFF/…), sinon None (dossiers personnels ou
        aucune structure en place)."""
        s = _stock[0]
        if not s:
            return None
        parts = os.path.normpath(s).split(os.sep)
        if DOSSIER_STOCK in parts:
            i = parts.index(DOSSIER_STOCK)
            racine = os.sep.join(parts[:i]) or os.sep
            if os.path.isdir(os.path.join(racine, DOSSIER_STOCK)):
                return racine
        return None

    def _resoudre_racine():
        """Retrouve la racine <...>/Bathymétrie de la structure existante
        sans jamais la recréer : d'abord depuis le dossier des sources,
        sinon depuis le dossier de sortie, sinon en demandant à
        l'utilisateur d'ouvrir son dossier « Bathymétrie ». Retourne la
        racine ou None si l'utilisateur annule."""
        r = _racine_structure()
        if r:
            return r
        if _sortie[0]:
            parts = os.path.normpath(_sortie[0]).split(os.sep)
            if DOSSIER_ASSEMBLE in parts:
                i = parts.index(DOSSIER_ASSEMBLE)
                rr = os.sep.join(parts[:i]) or os.sep
                if os.path.isdir(os.path.join(rr, DOSSIER_ASSEMBLE)):
                    return rr
        messagebox.showinfo(
            _tr("Bathymétrie"),
            _tr("Ouvrez le dossier « Bathymétrie » de votre structure."),
            parent=win)
        _remonter()
        base = filedialog.askdirectory(
            parent=win,
            initialdir=_stock[0] or os.path.expanduser("~"),
            title=_tr("Ouvrir la racine Bathymétrie"))
        _remonter()
        if not base:
            return None
        parts = os.path.normpath(base).split(os.sep)
        if DOSSIER_RACINE in parts:
            return os.sep.join(parts[:parts.index(DOSSIER_RACINE) + 1])
        if os.path.basename(os.path.normpath(base)) == DOSSIER_RACINE:
            return base
        return os.path.join(base, DOSSIER_RACINE)

    def _ajouter_pays():
        """Bouton « Ajouter un pays ».
        1) Une fenêtre demande le dossier de destination : Bathymétrie TIFF
           OU Bathymétrie assemble.
        2) Une seconde fenêtre demande le nom du pays.
        3) À la validation, le dossier est créé UNIQUEMENT dans le dossier
           choisi — jamais dans les deux — et devient le dossier courant
           correspondant. L'autre chemin n'est pas modifié.
        La structure de base (« Créer la structure ») n'est jamais recréée
        ici."""
        racine = _resoudre_racine()
        if not racine:
            return False
        # 1) Choix du dossier de destination : TIFF (sources) ou assemble.
        choix = _choix_tiff_assemble(racine)
        _remonter()
        if not choix:
            return False
        cible_txt = DOSSIER_STOCK if choix == "stock" else DOSSIER_ASSEMBLE
        # 2) Saisie du nom du pays.
        pays = _saisie(
            _tr("Bathymétrie"),
            _tr("Nom du pays (ex. : France, Suisse, Allemagne) :")
            + "\n→ " + cible_txt,
            parent=win, initialvalue="")
        _remonter()
        if not pays:
            return False
        pays = pays.strip().replace("/", "-").replace("\\", "-")
        if not pays:
            return False
        # 3) Création dans le SEUL dossier choisi.
        _etat(_tr("Création de la structure…"), FG)
        try:
            pays_dir = creer_pays_dans(racine, pays, choix)
        except Exception as e:
            _etat("")
            messagebox.showerror(_tr("Bathymétrie"), str(e), parent=win)
            _remonter()
            return False
        # 4) Le dossier créé devient le dossier courant correspondant ;
        #    l'AUTRE chemin reste inchangé.
        if choix == "stock":
            _stock[0] = pays_dir
            _cfg_set(CFG_STOCK, pays_dir)
        else:
            _sortie[0] = pays_dir
            _cfg_set(CFG_SORTIE, pays_dir)
        _maj_bandeaux()
        _etat(_tr("Structure créée."), FG)
        txt.delete("1.0", tk.END)
        _log(_tr("Pays ajouté :") + " " + pays)
        _log()
        if choix == "stock":
            _log(_tr("Dossier des sources :"))
        else:
            _log(_tr("Dossier de sortie :"))
        _log("   " + pays_dir)
        _remonter()
        return True

    def _choix_tiff_assemble(racine):
        """Ouvre la racine Bathymétrie et demande dans lequel des deux
        dossiers de la structure l'utilisateur veut travailler.
        Retourne "stock" (Bathymétrie TIFF), "sortie" (Bathymétrie assemble)
        ou None si annulation."""
        res = {"v": None}
        dlg = tk.Toplevel(win)
        dlg.title(_tr("Bathymétrie"))
        dlg.configure(bg=BG)
        try:
            dlg.transient(win)
        except Exception:
            pass
        dlg.resizable(False, False)
        dlg.columnconfigure(0, weight=1)
        dlg.columnconfigure(1, weight=1)

        tk.Label(dlg,
                 text=_tr("Dans quel dossier de la structure Bathymétrie "
                          "voulez-vous travailler ?"),
                 bg=BG, fg=FG, font=FONT, justify="left",
                 anchor="w", wraplength=520).grid(
            row=0, column=0, columnspan=2, padx=14, pady=(14, 2), sticky="w")
        tk.Label(dlg, text=_tr("Racine :") + " " + racine,
                 bg=BG, fg=FG2, font=("TkFixedFont", 10), justify="left",
                 anchor="w", wraplength=520).grid(
            row=1, column=0, columnspan=2, padx=14, pady=(0, 12), sticky="w")

        def _pick(val):
            res["v"] = val
            try:
                dlg.destroy()
            except Exception:
                pass

        ttk.Button(dlg, text=DOSSIER_STOCK,
                   command=lambda: _pick("stock")).grid(
            row=2, column=0, padx=(14, 7), pady=(0, 6), sticky="ew", ipady=4)
        ttk.Button(dlg, text=DOSSIER_ASSEMBLE,
                   command=lambda: _pick("sortie")).grid(
            row=2, column=1, padx=(7, 14), pady=(0, 6), sticky="ew", ipady=4)
        ttk.Button(dlg, text=_tr("Annuler"),
                   command=lambda: _pick(None)).grid(
            row=3, column=0, columnspan=2, padx=14, pady=(0, 14))

        dlg.bind("<Escape>", lambda e: _pick(None))
        dlg.protocol("WM_DELETE_WINDOW", lambda: _pick(None))
        try:
            dlg.update_idletasks()
            _x = win.winfo_rootx() + max(
                0, (win.winfo_width() - dlg.winfo_reqwidth()) // 2)
            _y = win.winfo_rooty() + 120
            dlg.geometry("+%d+%d" % (_x, _y))
        except Exception:
            pass
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.wait_window()
        return res["v"]

    def _choisir_dans_structure():
        """Bouton « Emplacement TIFF / assemble » : ouvre la racine
        Bathymétrie de la structure existante, demande à l'utilisateur s'il
        veut travailler dans Bathymétrie TIFF (sources) ou Bathymétrie
        assemble (sortie), puis lui laisse désigner le dossier exact
        (un pays, par exemple). Ne redemande PAS le disque si la structure
        est déjà connue. Ne modifie QUE le chemin correspondant au choix,
        jamais l'autre."""
        # 1) Retrouver la racine <...>/Bathymétrie sans rien redemander.
        racine = _racine_structure()
        if not racine and _sortie[0]:
            parts = os.path.normpath(_sortie[0]).split(os.sep)
            if DOSSIER_ASSEMBLE in parts:
                i = parts.index(DOSSIER_ASSEMBLE)
                r = os.sep.join(parts[:i]) or os.sep
                if os.path.isdir(os.path.join(r, DOSSIER_ASSEMBLE)):
                    racine = r
        # 2) Structure inconnue : demander d'ouvrir la racine Bathymétrie.
        if not racine:
            messagebox.showinfo(
                _tr("Bathymétrie"),
                _tr("Ouvrez le dossier « Bathymétrie » de votre structure."),
                parent=win)
            _remonter()
            base = filedialog.askdirectory(
                parent=win,
                initialdir=_stock[0] or os.path.expanduser("~"),
                title=_tr("Ouvrir la racine Bathymétrie"))
            _remonter()
            if not base:
                return False
            parts = os.path.normpath(base).split(os.sep)
            if DOSSIER_RACINE in parts:
                racine = os.sep.join(parts[:parts.index(DOSSIER_RACINE) + 1])
            elif os.path.basename(os.path.normpath(base)) == DOSSIER_RACINE:
                racine = base
            else:
                racine = os.path.join(base, DOSSIER_RACINE)
            # Création seulement des dossiers manquants ; aucun fichier
            # existant n'est touché.
            for d in (racine, os.path.join(racine, DOSSIER_STOCK),
                      os.path.join(racine, DOSSIER_ASSEMBLE)):
                os.makedirs(d, exist_ok=True)
        # 3) Demander TIFF ou assemble.
        choix = _choix_tiff_assemble(racine)
        _remonter()
        if not choix:
            return False
        if choix == "stock":
            depart = os.path.join(racine, DOSSIER_STOCK)
            titre = _tr("Dossier de vos bathymétries sources (.tif, .asc…)")
        else:
            depart = os.path.join(racine, DOSSIER_ASSEMBLE)
            titre = _tr("Dossier de destination des bathymétries assemblées")
        os.makedirs(depart, exist_ok=True)
        # 4) Laisser désigner le dossier exact, ouvert directement dans le
        #    dossier choisi (l'utilisateur peut entrer dans un pays).
        d = filedialog.askdirectory(parent=win, initialdir=depart,
                                    title=titre)
        _remonter()
        if not d:
            return False
        if choix == "stock":
            _stock[0] = d
            _cfg_set(CFG_STOCK, d)
        else:
            _sortie[0] = d
            _cfg_set(CFG_SORTIE, d)
        _maj_bandeaux()
        _etat(_tr("Dossier enregistré."), FG)
        return True

    def _assistant(force=False):
        """Première utilisation : demande les deux dossiers, sans jamais
        imposer de nom ni créer d'arborescence. L'organisation existante
        de l'utilisateur est reprise telle quelle."""
        if _stock[0] and os.path.isdir(_stock[0]) and _sortie[0] \
                and not force:
            return True
        # Deux profils d'utilisateurs : celui qui a déjà ses dossiers et
        # celui qui part de zéro. On lui demande lequel il est plutôt que
        # d'imposer une organisation à tout le monde.
        _neuf = messagebox.askyesno(
            _tr("Bathymétrie"),
            _tr("Deux dossiers sont nécessaires :\n\n"
                "1) celui où se trouvent vos bathymétries sources ;\n"
                "2) celui où écrire les bathymétries assemblées.\n\n"
                "Voulez-vous qu'Ortho4XP crée cette organisation pour "
                "vous ?\n\n"
                "OUI  →  la structure est créée automatiquement.\n"
                "NON  →  vous désignez vos propres dossiers, qui sont "
                "utilisés tels quels."), parent=win)
        _remonter()
        if _neuf:
            return _creer_structure()
        if not _choisir_stock():
            return False
        if not _choisir_sortie():
            return False
        txt.delete("1.0", tk.END)
        _etat(_tr("Dossiers enregistrés."), FG)
        _log(_tr("Dossier des sources :"))
        _log("   " + _stock[0])
        _log(_tr("Dossier de sortie :"))
        _log("   " + _sortie[0])
        _log()
        _log(_tr("Les sources doivent être en EPSG:4326 — X-Plane ne lit"))
        _log(_tr("aucune autre projection. Ortho4XP convertira au besoin,"))
        _log(_tr("mais préparez-les de préférence en 4326."))
        _log()
        _log(_tr("Le résultat assemblé sera écrit dans :"))
        _log("   " + os.path.join(_sortie[0], cle, cle + ".tif"))
        messagebox.showinfo(
            _tr("Bathymétrie"),
            _tr("Dossiers enregistrés.\n\nSources :\n{s}\n\n"
                "Sortie :\n{d}").format(s=_stock[0], d=_sortie[0]),
            parent=win)
        _remonter()
        return True

    # ── Dossier de sortie de la tuile ────────────────────────────────
    # Le cfg de la tuile doit être EXACTEMENT celui que lit Ortho4XP,
    # c'est-à-dire FNAMES.build_dir(lat, lon, custom_build_dir) +
    # "Ortho4XP_<short_latlon>.cfg" — même calcul que
    # O4_Config_Utils.load_tile_cfg(). L'ancien chemin
    # (Tile_dir/<tuile>/…) désignait un fichier que personne ne lit :
    # custom_bathy_dem y était écrit sans jamais apparaître dans le champ
    # « custom_bathy_dem » du GUI, qui restait sur une autre bathymétrie.
    def _custom_build_dir():
        for _att in ("custom_build_dir_entry", "custom_build_dir"):
            try:
                _v = getattr(gui, _att).get()
                if _v:
                    return _v
            except Exception:
                pass
        return ""

    try:
        _bdir = FNAMES.build_dir(lat, lon, _custom_build_dir())
        tile_cfg = os.path.join(
            _bdir, "Ortho4XP_%s.cfg" % FNAMES.short_latlon(lat, lon))
        # Repli sur le nom générique quand c'est celui qui existe déjà :
        # load_tile_cfg() applique le même repli.
        if not os.path.isfile(tile_cfg) and \
                os.path.isfile(os.path.join(_bdir, "Ortho4XP.cfg")):
            tile_cfg = os.path.join(_bdir, "Ortho4XP.cfg")
    except Exception:
        try:
            tile_cfg = os.path.join(FNAMES.Tile_dir, cle,
                                    "Ortho4XP_%s.cfg" % cle)
        except Exception:
            tile_cfg = ""

    def _dossier_sortie():
        """Dossier où écrire le fichier assemblé de la tuile.

        Le dossier de sortie CHOISI par l'utilisateur est prioritaire :
        le module y crée le sous-dossier au nom de la tuile (+49-002),
        puis y écrit +49-002.tif. Un custom_bathy_dem déjà présent dans le cfg
        n'est qu'un repli, pour les tuiles configurées avant que les
        dossiers ne soient désignés — sinon la sortie repartirait vers
        l'bathymétrie d'une autre tuile.
        """
        if _sortie[0]:
            return os.path.join(_sortie[0], cle)
        dem = _lire_cfg_valeur(tile_cfg, "custom_bathy_dem") if tile_cfg else ""
        if dem and os.path.isdir(os.path.dirname(dem)):
            return os.path.dirname(dem)
        return ""

    _deb_var = None

    def _debord():
        try:
            v = float(_deb_var.get().replace(",", "."))
            if 0 <= v <= 1:
                return v
        except Exception:
            pass
        return DEBORD_DEFAUT

    def _sources():
        """Sources retenues, avec repli sur le dossier de la tuile.
        1) stock imposé (aucun lien à créer)
        2) sinon dossier de sortie s'il contient déjà des fichiers
           (compatibilité avec les tuiles préparées à la main)"""
        srcs = []
        origine = ""
        if _stock[0] and os.path.isdir(_stock[0]):
            srcs = sources_depuis_dossier(_stock[0], lat, lon, _debord())
            origine = _tr("dossier des sources")
        if not srcs:
            d = _dossier_sortie()
            srcs = lister_sources(d, sortie_exclue=cle + ".tif")
            origine = _tr("dossier de la tuile")
        return srcs, origine

    def _rafraichir():
        txt.delete("1.0", tk.END)
        _maj_bandeaux()
        if not _stock[0] or not os.path.isdir(_stock[0]):
            _etat(_tr("Dossiers non configurés."), "#ffaa00")
            _log(_tr("Aucun dossier de bathymétries n'est configuré."))
            _log(_tr("Cliquez sur « Dossier des sources »."))
            if _stock[0]:
                _log()
                _log(_tr("Chemin mémorisé introuvable :"))
                _log("   " + _stock[0])
                _log(_tr("Si vos bathymétries sont sur un disque externe,"))
                _log(_tr("vérifiez qu'il est branché."))
            return
        b = tile_bounds(lat, lon, _debord())
        _log(_tr("Tuile") + " %s — %s %.3f %.3f %.3f %.3f"
             % (cle, _tr("emprise"), b[0], b[1], b[2], b[3]))
        _log(_tr("Sources :") + " " + _stock[0])
        _log(_tr("Sortie :") + " "
             + (_sortie[0] or _tr("(non configurée)")))
        _log()
        _etat(_tr("Recherche des sources…"), FG)
        srcs, origine = _sources()
        _etat("")
        if not srcs:
            _etat(_tr("Aucune source pour cette tuile."), "#ffaa00")
            _log(_tr("Aucun fichier bathymétrique ne recouvre cette tuile."))
            _log(_tr("Déposez vos données dans le dossier des sources, "
                     "en EPSG:4326."))
            return
        _log(_tr("{n} source(s) trouvée(s) — origine : {o}").format(
            n=len(srcs), o=origine))
        for s in srcs:
            marque = " (lien)" if os.path.islink(s) else ""
            _log("   • " + os.path.basename(s) + marque)
        _log()
        _log(_tr("Cliquer sur « Assembler » pour lancer."))
        _etat(_tr("Prêt."), FG)

    # ── Actions ──────────────────────────────────────────────────────
    def _assembler():
        if not rasterio_disponible():
            messagebox.showerror(
                _tr("Bathymétrie"),
                _tr("rasterio est introuvable dans l'installation "
                    "d'Ortho4XP."), parent=win)
            _remonter()
            return
        srcs, _o = _sources()
        if not srcs:
            messagebox.showinfo(_tr("Bathymétrie"),
                                _tr("Aucune source pour cette tuile."),
                                parent=win)
            _remonter()
            return
        dest = _dossier_sortie()
        if not dest:
            messagebox.showinfo(_tr("Bathymétrie"),
                                _tr("Dossiers non configurés."), parent=win)
            _remonter()
            return
        try:
            os.makedirs(dest, exist_ok=True)
        except Exception as e:
            messagebox.showerror(_tr("Bathymétrie"), str(e), parent=win)
            _remonter()
            return
        sortie = os.path.join(dest, cle + ".tif")
        # Confirmation de la DESTINATION avant de travailler : un dossier
        # de sortie mémorisé mais devenu faux ferait écrire le fichier
        # ailleurs, et on ne s'en apercevrait qu'à la fin.
        if not messagebox.askyesno(
                _tr("Bathymétrie"),
                _tr("Le fichier assemblé sera écrit ici :\n\n{f}\n\n"
                    "Est-ce le bon emplacement ?\n\n"
                    "NON  →  utilisez le bouton « Dossier de sortie ».")
                .format(f=sortie), parent=win):
            _remonter()
            return
        _remonter()
        if os.path.isfile(sortie):
            if not messagebox.askyesno(
                    _tr("Bathymétrie"),
                    _tr("{f} existe déjà. Le remplacer ?").format(
                        f=cle + ".tif"), parent=win):
                _remonter()
                return
        txt.delete("1.0", tk.END)
        _travail[0] = True
        for b in _boutons:
            try:
                b.state(["disabled"])
            except Exception:
                pass
        _animer(_tr("Assemblage en cours… ne fermez pas la fenêtre"))
        _res = {}

        def _tache():
            # Le travail lourd (reprojection, fusion, écriture) tourne
            # ICI, hors du thread de l'interface : plus de gel, plus de
            # curseur d'attente. Le journal remonte par la file.
            try:
                _res["ok"] = assembler_tuile(lat, lon, dest,
                                             debord=_debord(), log=_log,
                                             sources=srcs)
            except Exception as _e:
                _res["err"] = str(_e)

        th = _threading.Thread(target=_tache, daemon=True)
        th.start()

        def _fin():
            if th.is_alive():
                _pomper()
                win.after(150, _fin)
                return
            _travail[0] = False
            _pomper()
            for b in _boutons:
                try:
                    b.state(["!disabled"])
                except Exception:
                    pass
            if "err" in _res:
                _etat(_tr("Échec."), "#ff4444")
                _log()
                _log(_tr("ÉCHEC :") + " " + _res["err"])
                messagebox.showerror(_tr("Bathymétrie"), _res["err"],
                                     parent=win)
                _remonter()
                return
            chemin, ignorees = _res["ok"]
            if tile_cfg:
                try:
                    os.makedirs(os.path.dirname(tile_cfg), exist_ok=True)
                    ecrire_custom_bathy_dem(tile_cfg, chemin)
                    _log()
                    _log(_tr("custom_bathy_dem renseigné dans le cfg de la tuile."))
                    _log(tile_cfg)
                except Exception as _e:
                    _log(_tr("custom_bathy_dem non écrit :") + " " + str(_e))
            # Le fichier ne suffit pas : si la fenêtre de configuration est
            # déjà ouverte, son champ « custom_bathy_dem » garde en mémoire la
            # valeur chargée au départ (une autre bathymétrie). On la met
            # à jour directement pour que l'affichage corresponde au cfg.
            try:
                _cw = getattr(gui, "_config_win", None)
                if _cw is not None and _cw.winfo_exists():
                    _cw.v_["custom_bathy_dem"].set(chemin)
            except Exception:
                pass
            _etat(_tr("Terminé."), FG)
            _log()
            _log(_tr("TERMINÉ."))
            messagebox.showinfo(
                _tr("Bathymétrie"),
                _tr("Assemblage terminé.\n\n{f}\n\n"
                    "custom_bathy_dem est renseigné : la tuile est prête pour "
                    "l'étape mesh.").format(f=chemin), parent=win)
            _remonter()

        win.after(150, _fin)

    def _auto_test():
        txt.delete("1.0", tk.END)
        _etat(_tr("Auto-test en cours…"), FG)
        _log(_tr("Auto-test du moteur d'assemblage"))
        _log(_tr("(aucun de vos fichiers n'est touché)"))
        _log()
        ok, _rap = auto_test(log=_log)
        _log()
        _log("=> " + (_tr("SUCCÈS") if ok else _tr("ÉCHEC")))
        _etat(_tr("Auto-test terminé.") + " "
              + (_tr("SUCCÈS") if ok else _tr("ÉCHEC")),
              FG if ok else "#ff4444")
        messagebox.showinfo(
            _tr("Bathymétrie"),
            (_tr("Auto-test réussi : le moteur d'assemblage fonctionne.")
             if ok else
             _tr("Auto-test en échec — voir le détail dans la fenêtre.")),
            parent=win)
        _remonter()

    # ── QGIS (mémorisé comme GIMP dans la fenêtre Correction) ────────
    def _choisir_qgis():
        if sys.platform == "darwin":
            init_dir, ft = "/Applications", [(_tr("Applications macOS"),
                                              "*.app"),
                                             (_tr("Tous les fichiers"), "*")]
        elif sys.platform.startswith("win"):
            init_dir, ft = "C:\\Program Files", \
                [(_tr("Exécutables Windows"), "*.exe"),
                 (_tr("Tous les fichiers"), "*")]
        else:
            init_dir, ft = "/usr/bin", [(_tr("Tous les fichiers"), "*")]
        p = filedialog.askopenfilename(
            parent=win, title=_tr("Choisir l'application QGIS"),
            initialdir=init_dir, filetypes=ft)
        _remonter()
        if p:
            _cfg_set(CFG_QGIS, p)
            _qgis_var.set(p)
            messagebox.showinfo(_tr("Bathymétrie"),
                                _tr("Application QGIS enregistrée."),
                                parent=win)
            _remonter()

    def _ouvrir_qgis():
        app = _qgis_var.get().strip()
        if not app:
            messagebox.showinfo(
                _tr("Bathymétrie"),
                _tr("Aucune application QGIS définie.\n"
                    "Cliquez d'abord sur « Choisir QGIS »."), parent=win)
            _remonter()
            return
        cible = os.path.join(_dossier_sortie(), cle + ".tif")
        args = [cible] if os.path.isfile(cible) else []
        try:
            if sys.platform == "darwin" and app.endswith(".app"):
                subprocess.Popen(["open", "-a", app] + args)
            else:
                subprocess.Popen([app] + args)
            _etat(_tr("QGIS lancé."), FG)
        except Exception as e:
            messagebox.showerror(_tr("Bathymétrie"), str(e), parent=win)
            _remonter()

    # ── Préparer un pays (chaîne A : brut → EPSG:4326 → réduit) ──────
    def _preparer():
        if not rasterio_disponible():
            messagebox.showerror(
                _tr("Bathymétrie"),
                _tr("rasterio est introuvable dans l'installation "
                    "d'Ortho4XP."), parent=win)
            _remonter()
            return
        if not _stock[0] or not os.path.isdir(_stock[0]):
            messagebox.showinfo(_tr("Bathymétrie"),
                                _tr("Dossiers non configurés."), parent=win)
            _remonter()
            return
        src = filedialog.askdirectory(
            parent=win,
            title=_tr("Dossier des données brutes (.asc, .tif…)"))
        _remonter()
        if not src:
            return
        # Résolution réelle de la source : évite de « réduire » du Sonny
        # (~20 m) en dessous de sa résolution native.
        res_m = None
        try:
            for rep, _d, fs in os.walk(src, followlinks=True):
                for f in sorted(fs):
                    if not f.startswith(".") and \
                            f.lower().endswith(_EXT_RASTER):
                        res_m = resolution_metres(os.path.join(rep, f))
                        break
                if res_m:
                    break
        except Exception:
            res_m = None
        if res_m is None:
            messagebox.showerror(
                _tr("Bathymétrie"),
                _tr("Aucun fichier bathymétrique lisible dans ce dossier."),
                parent=win)
            _remonter()
            return

        # Ratio proposé : 25 % pour du 1 m (procédure IGN), 100 % si la
        # source est déjà grossière.
        defaut = "25" if res_m <= 2.0 else "100"
        rep_ratio = _saisie(
            _tr("Bathymétrie"),
            _tr("Résolution source détectée : {r} m\n\n"
                "Ratio de réduction en % (25 = diviser par 4) :\n"
                "100 = aucune réduction.").format(r=("%.1f" % res_m)),
            parent=win, initialvalue=defaut)
        _remonter()
        if not rep_ratio:
            return
        try:
            ratio = float(rep_ratio.replace(",", ".").replace("%", "")) / 100.0
        except Exception:
            messagebox.showerror(_tr("Bathymétrie"),
                                 _tr("Ratio invalide."), parent=win)
            _remonter()
            return
        ratio = max(0.01, min(1.0, ratio))
        res_finale = res_m / ratio
        if ratio < 1.0 and res_m > 5.0:
            if not messagebox.askyesno(
                    _tr("Bathymétrie"),
                    _tr("La source est déjà à {a} m. Réduire encore "
                        "donnerait {b} m et ferait perdre du relief.\n\n"
                        "Continuer quand même ?").format(
                            a=("%.1f" % res_m), b=("%.1f" % res_finale)),
                    parent=win):
                _remonter()
                return
            _remonter()

        suffixe = "%dM" % int(round(res_finale)) if res_finale >= 1 else "1M"
        nom_def = "%s-%s-reduit.tif" % (os.path.basename(
            os.path.normpath(src)), suffixe)
        nom = _saisie(
            _tr("Bathymétrie"),
            _tr("Nom du fichier produit :"),
            parent=win, initialvalue=nom_def)
        _remonter()
        if not nom:
            return
        if not nom.lower().endswith(".tif"):
            nom += ".tif"

        # Le fichier réduit est écrit dans le dossier des sources choisi
        # par l'utilisateur : aucun sous-dossier n'est créé.
        dest = os.path.join(_stock[0], nom)
        if os.path.isfile(dest):
            if not messagebox.askyesno(
                    _tr("Bathymétrie"),
                    _tr("{f} existe déjà. Le remplacer ?").format(f=nom),
                    parent=win):
                _remonter()
                return
            _remonter()

        txt.delete("1.0", tk.END)
        _log(_tr("Préparation :") + " " + src)
        _log(_tr("Résolution source :") + " %.1f m" % res_m)
        _log(_tr("Ratio :") + " %.0f %%  →  %.1f m" % (ratio * 100,
                                                       res_finale))
        _log(_tr("Destination :") + " " + dest)
        _log()
        _travail[0] = True
        for b in _boutons:
            try:
                b.state(["disabled"])
            except Exception:
                pass
        _animer(_tr("Préparation en cours… ne fermez pas la fenêtre"))
        _res = {}

        def _tache():
            try:
                _res["ok"] = preparer_pays(src, dest, ratio=ratio, log=_log)
            except Exception as _e:
                _res["err"] = str(_e)

        th = _threading.Thread(target=_tache, daemon=True)
        th.start()

        def _fin():
            if th.is_alive():
                _pomper()
                win.after(150, _fin)
                return
            _travail[0] = False
            _pomper()
            for b in _boutons:
                try:
                    b.state(["!disabled"])
                except Exception:
                    pass
            if "err" in _res:
                _etat(_tr("Échec."), "#ff4444")
                _log()
                _log(_tr("ÉCHEC :") + " " + _res["err"])
                messagebox.showerror(_tr("Bathymétrie"), _res["err"],
                                     parent=win)
                _remonter()
                return
            _etat(_tr("Terminé."), FG)
            _log()
            _log(_tr("TERMINÉ."))
            messagebox.showinfo(
                _tr("Bathymétrie"),
                _tr("Fichier préparé :\n\n{f}\n\n"
                    "Il est maintenant dans le stock et sera utilisé "
                    "automatiquement pour les tuiles qu'il "
                    "recouvre.").format(f=_res["ok"][0]), parent=win)
            _remonter()
            _rafraichir()

        win.after(150, _fin)

    # ── Barre du bas ─────────────────────────────────────────────────
    frm_deb = tk.Frame(win, bg=BG)
    frm_deb.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_deb, text=_tr("Débord de chevauchement (°) :"),
             font=FONT, bg=BG, fg=FG).pack(side=tk.LEFT)
    _deb_var = tk.StringVar(value=str(DEBORD_DEFAUT))
    tk.Entry(frm_deb, textvariable=_deb_var, width=8, bg=PREV_BG, fg=FG2,
             insertbackground=FG).pack(side=tk.LEFT, padx=(8, 0))
    tk.Label(frm_deb, text=_tr("(0.1 = 10 % de la tuile sur les 4 côtés)"),
             font=FONT, bg=BG, fg="#888888").pack(side=tk.LEFT, padx=(8, 0))

    _qgis_var = tk.StringVar(value=_cfg_get(CFG_QGIS))
    frm_q = tk.Frame(win, bg=BG)
    frm_q.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_q, text=_tr("QGIS :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_q, textvariable=_qgis_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    # ── Rappel permanent des deux dossiers ───────────────────────────
    # La destination doit être visible AVANT d'assembler, pas découverte
    # après coup dans le message de fin.
    frm_src = tk.Frame(win, bg=BG)
    frm_src.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_src, text=_tr("Sources :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_src, textvariable=_src_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    frm_out = tk.Frame(win, bg=BG)
    frm_out.pack(fill=tk.X, padx=14, pady=(0, 4))
    tk.Label(frm_out, text=_tr("Sortie :"), font=FONT, bg=BG,
             fg=FG).pack(side=tk.LEFT)
    tk.Label(frm_out, textvariable=_out_var, font=("TkFixedFont", 10),
             bg=BG, fg=FG2, anchor="w", wraplength=560,
             justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True,
                                  padx=(8, 0))

    frm_bot = tk.Frame(win, bg=BG)
    frm_bot.pack(pady=(6, 12))
    # Ordre des boutons = ordre réel du travail :
    #   structure  →  préparation des données  →  assemblage de la tuile
    # Ligne 1 : les trois étapes, dans l'ordre.
    # Ligne 2 : outils et configuration.
    _defs = [
        (_tr("Créer la structure"),
         lambda: (_creer_structure(), _rafraichir()), 0, 0),
        (_tr("Préparer les données (EPSG → réduit)"), _preparer, 0, 1),
        (_tr("Assembler"), _assembler, 0, 2),
        (_tr("Rafraîchir"), _rafraichir, 0, 3),
        (_tr("Dossier des sources"),
         lambda: (_choisir_stock(), _rafraichir()), 1, 0),
        (_tr("Vérifier (auto-test)"), _auto_test, 1, 1),
        (_tr("Choisir QGIS"), _choisir_qgis, 1, 2),
        (_tr("Ouvrir dans QGIS"), _ouvrir_qgis, 1, 3),
        (_tr("Dossier de sortie"),
         lambda: (_choisir_sortie(), _rafraichir()), 2, 0),
        (_tr("Ajouter un pays"),
         lambda: (_ajouter_pays(), _rafraichir()), 2, 1),
        (_tr("Emplacement TIFF / assemble"),
         lambda: (_choisir_dans_structure(), _rafraichir()), 2, 2),
        (_tr("Fermer"), win.destroy, 2, 3),
    ]
    for _txt, _cmd, _r, _c in _defs:
        _b = ttk.Button(frm_bot, text=_txt, command=_cmd)
        _b.grid(row=_r, column=_c, padx=5, pady=(8, 0) if _r else 0,
                ipadx=6, ipady=4)
        # Le bouton Fermer reste actif même pendant un assemblage.
        if _cmd is not win.destroy:
            _boutons.append(_b)

    if not _stock[0] or not _sortie[0]:
        win.after(150, lambda: (_assistant(), _rafraichir()))
    else:
        _rafraichir()

    # ── Ancrage des barres du bas ────────────────────────────────────
    # Le journal est packé avant les barres du bas et occupe tout
    # l'espace disponible (expand=True) : si la fenêtre est réduite,
    # c'est lui qui garde la place et les barres du bas (dont les
    # boutons) sortent du cadre. On repacke donc les barres du bas
    # EN PREMIER, ancrées en bas, puis le journal : Tk sert les barres
    # avant le journal, qui se comprime seul. Les boutons restent
    # toujours visibles.
    try:
        for _f in (frm_log, frm_deb, frm_q, frm_src, frm_out, frm_bot):
            _f.pack_forget()
        frm_bot.pack(side=tk.BOTTOM, pady=(6, 12))
        frm_out.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_src.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_q.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_deb.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 4))
        frm_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 4))
    except Exception:
        pass

    win.update_idletasks()
    ww = max(880, win.winfo_reqwidth())
    wh = max(620, win.winfo_reqheight())
    win.geometry("%dx%d+%d+%d" % (ww, wh, (sw - ww) // 2, (sh - wh) // 2))

    # ── Taille minimale réelle ───────────────────────────────────────
    # La taille minimale doit être celle dont l'interface a réellement
    # besoin (largeur des 4 colonnes de boutons + hauteur des libellés,
    # des deux barres et des trois lignes de boutons), avec juste un
    # reste de journal. Sinon l'utilisateur peut réduire la fenêtre
    # jusqu'à masquer les boutons. Bornée à l'écran pour rester
    # utilisable sur les petits écrans.
    try:
        _min_w = min(win.winfo_reqwidth(), sw - 40)
        # hauteur requise moins la place « en trop » du journal :
        # on garde au minimum 120 px de journal.
        _log_h = max(0, frm_log.winfo_reqheight() - 120)
        _min_h = min(max(480, win.winfo_reqheight() - _log_h), sh - 80)
        win.minsize(int(_min_w), int(_min_h))
    except Exception:
        win.minsize(880, 560)
