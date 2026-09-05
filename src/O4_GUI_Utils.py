import os
from math import floor, cos, pi
import sys
import queue
import threading
import tkinter as tk
from tkinter import RIDGE, N, S, E, W, NW, NE, SW, SE, LEFT, RIGHT, CENTER, HORIZONTAL, END, ALL, filedialog, messagebox
import tkinter.ttk as ttk
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    ctk = None
    _HAS_CTK = False
from PIL import Image, ImageTk
import O4_Version
import O4_Imagery_Utils as IMG
import O4_File_Names as FNAMES
import O4_Geo_Utils as GEO
import O4_Vector_Utils as VECT
import O4_Vector_Map as VMAP
import O4_Mesh_Utils as MESH
import O4_Mask_Utils as MASK
import O4_Tile_Utils as TILE
import O4_UI_Utils as UI
import O4_Config_Utils as CFG
import O4_Color_Normalize as CNORM
import O4_Color_Check as CC
from O4_Lang import tr
import O4_UI_Dialogs as DIALOGS

# ── Module de correction imagerie/zone (non bloquant) ────────────────────
#  Fichier autonome hébergeant, à terme, le preview des DDS, la correction
#  GIMP et la gestion des couches JOSM. Import non bloquant : si le module
#  est absent ou défaillant, le GUI démarre normalement et le bouton se
#  replie sur l'ancienne fenêtre de correction (open_patch_correction).
try:
    import O4_Correction_Utils as _CORRMOD
    _corrmod_enabled = True
except Exception:
    _CORRMOD = None
    _corrmod_enabled = False

# ── Module Altimétrie / DEM (non bloquant) ───────────────────────────────
#  Fichier autonome : assemblage des altimétries d'une tuile (remplace la
#  procédure QGIS manuelle). Import non bloquant : si le module est absent
#  ou défaillant, le GUI démarre normalement et le bouton le signale.
#  AUCUN fichier du pipeline n'est concerné par ce module.
try:
    import O4_Altimetrie_Utils as _ALTIMOD
    _altimod_enabled = True
except Exception:
    _ALTIMOD = None
    _altimod_enabled = False

# ── Module Bathymétrie / fonds marins (non bloquant) ─────────────────────
#  Fichier autonome : même structure automatisée que l'Altimétrie, mais
#  pour les relevés de fonds. Renseigne custom_bathy_dem (jamais custom_dem).
#  S'appuie sur le moteur validé de O4_Altimetrie_Utils. Import non bloquant :
#  si le module est absent, le GUI démarre et le bouton le signale.
#  AUCUN fichier du pipeline n'est concerné par ce module.
try:
    import O4_Bathymetrie_Utils as _BATHYMOD
    _bathymod_enabled = True
except Exception:
    _BATHYMOD = None
    _bathymod_enabled = False

# ── Module Avancé / JOSM (non bloquant) ──────────────────────────────────
#  Fichier autonome : fenêtre « Avancé » regroupant les couches JOSM
#  (Extents/, Patches/, OSM_data/). Import non bloquant : si le module est
#  absent ou défaillant, le GUI démarre normalement et le bouton le signale.
#  AUCUN fichier du pipeline n'est concerné par ce module.
try:
    import O4_Avance_Utils as _AVANCEMOD
    _avancemod_enabled = True
except Exception:
    _AVANCEMOD = None
    _avancemod_enabled = False

# ── Module Cache OSM local .pbf (non bloquant) ───────────────────────────
#  Fichier autonome : remplit OSM_data/ a partir d'un extrait .pbf local,
#  de sorte que le Step 1 recycle les donnees au lieu de les telecharger.
#  Import non bloquant : si le module est absent ou defaillant, le GUI
#  demarre normalement et le bouton le signale.
#  AUCUN fichier du pipeline n'est concerne par ce module.
try:
    import O4_PBF_Utils as _PBFMOD
    _pbfmod_enabled = True
except Exception:
    _PBFMOD = None
    _pbfmod_enabled = False

# ── Module Provider Score / Analyse Fournisseurs (non bloquant) ────
try:
    import O4_Provider_Score as _SCOREMOD
    _scoremod_enabled = True
except Exception:
    _SCOREMOD = None
    _scoremod_enabled = False

# ── Module Simulateur visuel / Visualisation réglages (non bloquant) ──
#  Fichier autonome : fenêtre Simulateur Ortho4XP V2 (onglets, canvas
#  animés, curseurs cfg). Import non bloquant : si le module est absent
#  ou défaillant, le GUI démarre normalement et le bouton le signale.
#  AUCUN fichier du pipeline n'est concerné par ce module.
try:
    import O4_Simulator_Utils as _SIMMOD
    _simmod_enabled = True
except Exception as _sim_imp_err:
    _SIMMOD = None
    _simmod_enabled = False
    print(f"[GUI] O4_Simulator_Utils non chargé: {_sim_imp_err}")

# Alias TOUJOURS défini (menus / scripts font O4_GUI_Utils.Ortho4XP_Simulator)
# Si le module simulateur est OK → vraie classe ; sinon → None
try:
    Ortho4XP_Simulator = _SIMMOD.Ortho4XP_Simulator if _simmod_enabled else None
except Exception:
    Ortho4XP_Simulator = None


# ── Nouveaux modules Phase 3 (non bloquants) ─────────────────────────────
try:
    from O4_Benchmark import Timeline as _Timeline
    _timeline_enabled = True
except Exception:
    _timeline_enabled = False
    class _Timeline:
        def start(self, *a): pass
        def end(self, *a):   pass
        def report(self):    pass

try:
    from O4_Score_Logger import ScoreLogger as _ScoreLogger
    _score_logger_gui = _ScoreLogger(auto_persist=False)
    _score_logger_enabled = True
except Exception:
    _score_logger_enabled = False
    _score_logger_gui = None

try:
    from O4_Memory_Manager import memory_stats as _memory_stats
    _mem_enabled = True
except Exception:
    _mem_enabled = False
    def _memory_stats(): return {}

# Instance Timeline globale partagée pour toute la session GUI
_build_timeline = _Timeline()
# ─────────────────────────────────────────────────────────────────────────

# --- THEME ---
_BG     = "#3b5b49"
_FG     = "#e8f0ec"
_FG2    = "#a6e3a1"
_BTN_BG = "#4a6b59"
_BTN_FG = "#ffffff"
_CON_BG = "#0f0f1a"
_CON_FG = "#50fa7b"
_ACCENT = "#a6e3a1"

def _reload_theme():
    """Recharge les couleurs depuis le thème actif — appelé à chaque ouverture de fenêtre."""
    global _BG, _FG, _FG2, _BTN_BG, _BTN_FG, _CON_BG, _CON_FG, _ACCENT
    try:
        import O4_Theme_Manager as _TM
        _t      = _TM.get_theme()
        _BG     = _t.get("bg",           _BG)
        _FG     = _t.get("fg",           _FG)
        _FG2    = _t.get("fg_secondary", _FG2)
        _BTN_BG = _t.get("btn_bg",       _BTN_BG)
        _BTN_FG = _t.get("btn_fg",       _BTN_FG)
        _CON_BG = _t.get("console_bg",   _CON_BG)
        _CON_FG = _t.get("console_fg",   _CON_FG)
        _ACCENT = _t.get("accent",       _ACCENT)
    except Exception:
        pass

_reload_theme()
# -------------

OsX = "dar" in sys.platform


class Ortho4XP_GUI(tk.Tk):

    zl_list = ["12", "13", "14", "15", "16", "17", "18"]

    def __init__(self):
        tk.Tk.__init__(self)
        _reload_theme()

        # ── Détection 4K ──────────────────────────────────────────────
        dpi = self.winfo_fpixels('1i')
        self._ui_scale = 1.3  # +30% pour lisibilité 4K macOS
        s = self._ui_scale
        fs = lambda x: int(x * s)

        # ── Styles ttk ────────────────────────────────────────────────
        O4 = ttk.Style()
        # macOS : "alt" préserve mieux les couleurs de texte que "default"
        # Sur macOS sombre le thème natif écrase les couleurs → on force tout
        O4.theme_use("alt")
        # TButton — foreground forcé pour macOS (texte visible sur fond foncé)
        O4.configure("TButton",
            background=_BTN_BG, foreground=_BTN_FG,
            relief="raised", borderwidth=1)
        O4.map("TButton",
            background=[("active",   _ACCENT),
                        ("pressed",  _BG),
                        ("disabled", _BG)],
            foreground=[("active",   "#1e3028"),
                        ("pressed",  _BTN_FG),
                        ("disabled", "#888888")])
        O4.configure("Flat.TButton",
            background=_BG, foreground=_BTN_FG,
            highlightbackground=_BG,
            selectbackground=_BG, highlightcolor=_BG,
            highlightthickness=0, relief="flat")
        O4.map("Flat.TButton",
            background=[("disabled","pressed","!focus","active",_BG)],
            foreground=[("disabled", "#888888"),
                        ("active",   _BTN_FG),
                        ("pressed",  _BTN_FG)])
        O4.configure("O4.TCombobox",
            selectbackground="white", selectforeground="#1e3028",
            fieldbackground="white", foreground="#1e3028", background="white")
        O4.map("O4.TCombobox",
            fieldbackground=[("disabled","!focus","focus","active","white")])
        # ── Barres de progression au thème ────────────────────────────
        #    Creux foncé, remplissage à la couleur d'accent, plus épaisses.
        #    ttk ne gère pas de vrais coins arrondis (limite native).
        _TROUGH = "#2f4a3b"   # creux : un ton sous le fond général
        O4.configure("O4.Horizontal.TProgressbar",
            troughcolor=_TROUGH, background=_ACCENT,
            bordercolor=_TROUGH, lightcolor=_ACCENT, darkcolor=_ACCENT,
            borderwidth=0, thickness=12)
        # Barre d'activité : vert secondaire pour la distinguer des %
        O4.configure("O4Act.Horizontal.TProgressbar",
            troughcolor="#2a4235", background="#63a978",
            bordercolor="#2a4235", lightcolor="#63a978", darkcolor="#63a978",
            borderwidth=0, thickness=12)
        # macOS : forcer couleur texte globale pour tous les widgets tk natifs
        if OsX:
            self.option_add("*Button.foreground",   _BTN_FG)
            self.option_add("*Button.background",   _BTN_BG)
            self.option_add("*Button.activeforeground", "#1e3028")
            self.option_add("*Button.activebackground", _ACCENT)
            self.option_add("*Label.foreground",    _FG)
            self.option_add("*Label.background",    _BG)
        self.option_add("*Font", f"TkFixedFont {fs(11)}")

        # ── UI global ─────────────────────────────────────────────────
        UI.gui = self

        # ── Initialisation providers ──────────────────────────────────
        try:
            IMG.initialize_providers_dict()
            IMG.initialize_combined_providers_dict()
            IMG.initialize_extents_dict()
            IMG.initialize_color_filters_dict()
        except Exception as e:
            print(f"[GUI] initialize_providers: {e}")
        try:
            def _in_gui(p):
                if isinstance(p, dict): return p.get("in_GUI", True)
                return getattr(p, "in_GUI", True)
            full = sorted([
                c for c in set(IMG.providers_dict)
                if _in_gui(IMG.providers_dict[c])
            ] + sorted(set(IMG.combined_providers_dict)))
            for rm in ("OSM", "SEA"):
                try: full.remove(rm)
                except: pass
            self.map_list = full if full else ["BI","GO2","ARC","IGN","SWISSTOPO","ZonePhoto"]
        except:
            self.map_list = ["BI","GO2","ARC","IGN","SWISSTOPO","ZonePhoto"]

        # ── Fenêtre ───────────────────────────────────────────────────
        self.title("Ortho4XP V3.0 - sRGB Roland Edition (Mars 2026)")
        self.geometry(f"{int(1320*s)}x{int(860*s)}")
        self.minsize(1320, 860)
        self.protocol("WM_DELETE_WINDOW", self.exit_prg)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)   # console extensible

        # ── Barre de menus native (module externe O4_Menu_Bar) ─────────
        #  Ajout pur : double l'accès aux fonctions existantes, ne retire
        #  aucun bouton. Non bloquant : si le module est absent ou en
        #  erreur, l'interface démarre normalement (comme les autres
        #  modules optionnels ci-dessus).
        try:
            import O4_Menu_Bar
            O4_Menu_Bar.install_menubar(self)
        except Exception as _e:
            print(f"[GUI] menubar: {_e}")

        # ── Icônes (GIF natifs Ortho4XP) ─────────────────────────────
        def _load_icon(name):
            try:
                path = os.path.join(FNAMES.Utils_dir, name)
                img = tk.PhotoImage(file=path)
                # Zoom ×2 sur 4K
                if s >= 2.0:
                    img = img.zoom(2, 2)
                return img
            except:
                return None

        self.folder_icon = _load_icon("Folder.gif")
        self.earth_icon  = _load_icon("Earth.gif")
        self.loupe_icon  = _load_icon("Loupe.gif")
        self.config_icon = _load_icon("Config.gif")
        self.stop_icon   = _load_icon("Stop.gif")
        self.exit_icon   = _load_icon("Exit.gif")

        # ── FRAME TOP (toutes les rubriques empilées) ─────────────────
        self.frame_top = tk.Frame(self, border=4, relief=RIDGE, bg=_BG)
        self.frame_top.grid(row=0, column=0, sticky=N+S+W+E)
        self.frame_top.columnconfigure(0, weight=1)

        # ── Fabricant de CADRE de rubrique (chapitrage encadré) ───────
        #  Chaque groupe est enfermé dans un cadre titré bordé, pour bien
        #  isoler visuellement les rubriques les unes des autres.
        #  Purement visuel : aucune fonction ni aucun bouton n'est modifié.
        def _section(title, r):
            sec = tk.LabelFrame(self.frame_top,
                text="  " + title + "  ",
                bg=_BG, fg=_FG2,
                border=2, relief=RIDGE,
                font=("TkFixedFont", fs(12), "bold"),
                padx=6, pady=4)
            sec.grid(row=r, column=0, sticky=N+S+W+E, padx=6, pady=(6, 2))
            sec.columnconfigure(0, weight=1)
            return sec

        # ══ RUBRIQUE 1 : Coordonnées et dossier de la tuile ═══════════
        sec_coord = _section(tr('Coordonnées et dossier de la tuile'), 0)

        # ── Ligne coordonnées : lat/lon/imagery/zl + icônes ───────────
        self.frame_tile = tk.Frame(sec_coord, border=0, padx=5, pady=5, bg=_BG)
        self.frame_tile.grid(row=0, column=0, sticky=N+S+W+E)
        self.frame_tile.columnconfigure(5, weight=1)   # imagery s'étire

        self.lat = tk.StringVar()
        self.lat.trace_add("write", self.tile_change)
        tk.Label(self.frame_tile, text=tr("Latitude:"),  bg=_BG, fg=_FG, font=("TkFixedFont", fs(11))).grid(row=0, column=0, padx=5, pady=5, sticky=E+W)
        self.lat_entry = tk.Entry(self.frame_tile, width=5, bg="#f0f4f2", fg="#1e3028", textvariable=self.lat)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)

        self.lon = tk.StringVar()
        self.lon.trace_add("write", self.tile_change)
        tk.Label(self.frame_tile, text=tr("Longitude:"), bg=_BG, fg=_FG, font=("TkFixedFont", fs(11))).grid(row=0, column=2, padx=5, pady=5, sticky=E+W)
        self.lon_entry = tk.Entry(self.frame_tile, width=5, bg="#f0f4f2", fg="#1e3028", textvariable=self.lon)
        self.lon_entry.grid(row=0, column=3, padx=5, pady=5, sticky=W)

        tk.Label(self.frame_tile, text=tr("Imagery:"), bg=_BG, fg=_FG, font=("TkFixedFont", fs(11))).grid(row=0, column=4, padx=5, pady=5, sticky=E+W)
        self.default_website = tk.StringVar()
        self.default_website.trace_add("write", self._on_imagery_change)
        # "Personnel" toujours présent en fin de liste
        self._full_map_list = self.map_list + [tr("Personnel")]
        self.img_combo = ttk.Combobox(self.frame_tile, values=self._full_map_list,
            textvariable=self.default_website, state="readonly", width=40)
        self.img_combo.grid(row=0, column=5, padx=5, pady=5, sticky=W)

        tk.Label(self.frame_tile, text=tr("Zoomlevel:"), bg=_BG, fg=_FG, font=("TkFixedFont", fs(11))).grid(row=0, column=6, padx=5, pady=5, sticky=E+W)
        self.default_zl = tk.StringVar()
        self.default_zl.trace_add("write", self.update_cfg)
        self.zl_combo = ttk.Combobox(self.frame_tile, values=self.zl_list,
            textvariable=self.default_zl, state="readonly", width=5)
        self.zl_combo.grid(row=0, column=7, padx=5, pady=5, sticky=W)

        # Icônes grandes à droite — avec fallback texte si GIF absent
        def _icon_btn(parent, icon, text_fallback, cmd, col):
            kw = dict(takefocus=False, command=cmd)
            if icon:
                kw["image"] = icon
            else:
                kw["text"] = text_fallback
                kw["width"] = 4
            ttk.Button(parent, **kw).grid(row=0, column=col, rowspan=2, padx=4, pady=2)

        _icon_btn(self.frame_tile, self.config_icon, "⚙",  self.open_config_window,   9)
        _icon_btn(self.frame_tile, self.loupe_icon,  "🔍", self.open_custom_zl_window, 10)
        _icon_btn(self.frame_tile, self.earth_icon,  "🌍", self.open_earth_window,     11)
        _icon_btn(self.frame_tile, self.stop_icon,   "🛑", self.set_red_flag,          12)
        _icon_btn(self.frame_tile, self.exit_icon,   "⏻",  self.exit_prg,             13)

        # Bouton de sélection de langue : déplacé dans la fenêtre du lanceur
        # (Ortho4XP_Launcher.py). Retiré ici pour éviter le doublon.

        # ── Ligne dossier racine ──────────────────────────────────────
        self.frame_folder = tk.Frame(sec_coord, border=0, padx=5, pady=0, bg=_BG)
        self.frame_folder.grid(row=1, column=0, sticky=N+S+W+E)
        self.frame_folder.columnconfigure(1, weight=1)

        tk.Label(self.frame_folder, text=tr("Base Folder:"), bg=_BG, fg=_FG).grid(row=0, column=0, padx=5, pady=5, sticky=E+W)
        self.custom_build_dir = tk.StringVar()
        self.custom_build_dir_entry = tk.Entry(self.frame_folder, bg="#f0f4f2", fg="#1e3028",
            textvariable=self.custom_build_dir)
        self.custom_build_dir_entry.grid(row=0, column=1, padx=0, pady=0, sticky=E+W)
        kw_folder = dict(takefocus=False, command=self.choose_custom_build_dir)
        if self.folder_icon:
            kw_folder["image"] = self.folder_icon
        else:
            kw_folder["text"] = "📁"; kw_folder["width"] = 4
        ttk.Button(self.frame_folder, **kw_folder).grid(row=0, column=2, padx=0, pady=0, sticky=N+S+E+W)

        # ══ RUBRIQUE 2 « Gestion des Données » : SUPPRIMÉE ════════════
        #  Ses boutons (Altimétrie, Bathymétrie, provider .lay, Cache OSM,
        #  Analyse Fournisseurs) sont désormais dans la barre de menus
        #  (Outils). Les méthodes correspondantes restent intactes.
        #  Timeline (Chronologie) : bouton ET méthode d'affichage _show_timeline
        #  supprimés (plus aucun appel). Le chronomètre du build lui-même
        #  (_build_timeline) reste actif et mesure la durée de chaque étape.
        #  Le label RAM est déplacé plus bas, au bout de la ligne des barres
        #  de progression (rubrique Fabrication Tuile).


        # ══ RUBRIQUE 3 : Gestion des Couleurs automatisée ═════════════
        sec_color = _section(tr('Gestion des Couleurs automatisée'), 2)
        self.frame_cnorm = tk.Frame(sec_color, border=0, padx=2, pady=2, bg=_BG)
        self.frame_cnorm.grid(row=0, column=0, sticky=N+S+W+E)
        self.frame_cnorm.columnconfigure(0, weight=1)
        self.frame_cnorm.columnconfigure(1, weight=1)

        # ── Cadre gauche : Normalisation couleur ──────────────────────
        lf_norm = tk.LabelFrame(self.frame_cnorm, text=" " + tr("Color Normalize") + " ",
            bg=_BG, fg=_FG2, border=2, relief=RIDGE,
            font=("TkFixedFont", fs(11), "bold"), padx=8, pady=4)
        lf_norm.grid(row=0, column=0, padx=(0, 6), pady=2, sticky=N+S+W+E)
        lf_norm.columnconfigure(1, weight=1)
        self._lf_norm = lf_norm

        self.cnorm_enabled = tk.IntVar(value=1)
        self.cnorm_checkbox = tk.Checkbutton(lf_norm, text=tr("Enable"),
            fg=_FG, selectcolor=_BG,
            activeforeground="#ffffff", activebackground=_BG,
            variable=self.cnorm_enabled, command=self.toggle_cnorm,
            font=("TkFixedFont", fs(11), "bold"), bg=_BG)
        self.cnorm_checkbox.grid(row=0, column=0, columnspan=2, padx=2, sticky=W)

        self._cnorm_desc_label = tk.Label(lf_norm, text=tr('Intensité de la correction'), bg=_BG, fg="#cbdcc9",
                 font=("TkFixedFont", fs(10)))
        self._cnorm_desc_label.grid(row=1, column=0, columnspan=2, padx=2, sticky=W)

        self.cnorm_strength = tk.IntVar(value=100)
        self.cnorm_slider = self._themed_slider(
            lf_norm, 0, 100, self.cnorm_strength,
            self.update_cnorm_strength, width=int(180*s))
        self.cnorm_slider.grid(row=2, column=0, padx=2, sticky=W+E)

        self.cnorm_pct_label = tk.Label(lf_norm, text="100%",
            bg=_BG, fg=_FG2, font=("TkFixedFont", fs(12), "bold"))
        self.cnorm_pct_label.grid(row=2, column=1, padx=6, sticky=W)

        self.cnorm_ref_label = tk.Label(lf_norm,
            text=tr("Réf: Calibré_48753_JPG_Europe"),
            bg=_BG, fg=_FG2,
            font=("TkFixedFont", fs(11), "bold"))
        self.cnorm_ref_label.grid(row=3, column=0, columnspan=2, padx=2, pady=(2, 0), sticky=W)

        # ── Cadre droit : Saturation ──────────────────────────────────
        lf_sat = tk.LabelFrame(self.frame_cnorm, text=" Saturation ",
            bg=_BG, fg=_FG2, border=2, relief=RIDGE,
            font=("TkFixedFont", fs(11), "bold"), padx=8, pady=4)
        lf_sat.grid(row=0, column=1, padx=(6, 0), pady=2, sticky=N+S+W+E)
        lf_sat.columnconfigure(1, weight=1)
        self._lf_sat = lf_sat

        self.cnorm_sat_enabled = tk.IntVar(value=0)
        self.cnorm_sat_checkbox = tk.Checkbutton(lf_sat, text=tr("Enable"),
            fg=_FG, selectcolor=_BG,
            activeforeground="#ffffff", activebackground=_BG,
            variable=self.cnorm_sat_enabled, command=self.toggle_cnorm_sat,
            font=("TkFixedFont", fs(11), "bold"), bg=_BG)
        self.cnorm_sat_checkbox.grid(row=0, column=0, columnspan=2, padx=2, sticky=W)

        self._cnorm_sat_desc_label = tk.Label(lf_sat, text=tr('Boost — intensité de la saturation'), bg=_BG, fg="#cbdcc9",
                 font=("TkFixedFont", fs(10)))
        self._cnorm_sat_desc_label.grid(row=1, column=0, columnspan=2, padx=2, sticky=W)

        self.cnorm_sat_value = tk.IntVar(value=100)
        self.cnorm_sat_slider = self._themed_slider(
            lf_sat, 0, 200, self.cnorm_sat_value,
            self.update_cnorm_sat, width=int(180*s))
        self.cnorm_sat_slider.grid(row=2, column=0, padx=2, sticky=W+E)

        self.cnorm_sat_label = tk.Label(lf_sat, text=tr('100%  (réf.)'),
            bg=_BG, fg=_FG2, font=("TkFixedFont", fs(11), "bold"),
            width=14, anchor=W)
        self.cnorm_sat_label.grid(row=2, column=1, padx=6, sticky=W)

        self._cnorm_sat_legend = tk.Label(lf_sat,
            text=tr("0%=gris  100%=réf.48753JPG  200%=×2"),
            bg=_BG, fg=_FG2, font=("TkFixedFont", fs(10)))
        self._cnorm_sat_legend.grid(
            row=3, column=0, columnspan=2, padx=2, pady=(2, 0), sticky=W)

        # État initial des curseurs selon les cases (grisé si décoché)
        self._sync_cnorm_slider_state()
        self._sync_cnorm_sat_slider_state()

        # ══ RUBRIQUE 4 : Fabrication Tuile ════════════════════════════
        sec_build = _section(tr('Fabrication Tuile'), 3)
        self.frame_steps = tk.Frame(sec_build, border=0, padx=5, pady=5, bg=_BG)
        self.frame_steps.grid(row=0, column=0, sticky=N+S+W+E)
        for i in range(6): self.frame_steps.columnconfigure(i, weight=1)

        self._themed_button(self.frame_steps, tr("Assemble Vector data"),
            self.build_poly_file).grid(row=0, column=0, padx=5, pady=0, sticky=N+S+E+W)

        build_mesh_button = self._themed_button(self.frame_steps, tr("Triangulate 3D Mesh"))
        build_mesh_button.grid(row=0, column=1, padx=5, pady=0, sticky=N+S+E+W)
        self._bind_clicks(build_mesh_button, self._on_mesh_click)

        self._themed_button(self.frame_steps, tr("Sea Patches (2.1)"),
            self.build_sea_patches).grid(row=0, column=2, padx=5, pady=0, sticky=N+S+E+W)

        build_masks_button = self._themed_button(self.frame_steps, tr(" Draw Water Masks  "))
        build_masks_button.grid(row=0, column=3, padx=5, pady=0, sticky=N+S+E+W)
        self._bind_clicks(build_masks_button, self._on_masks_click)

        self._themed_button(self.frame_steps, tr(" Build Imagery/DSF "),
            self.build_tile).grid(row=0, column=4, padx=5, pady=0, sticky=N+S+E+W)

        self._themed_button(self.frame_steps, tr("    All in one     "),
            self.build_all).grid(row=0, column=5, padx=5, pady=0, sticky=N+S+E+W)

        # ── Barres de progression ─────────────────────────────────────
        self.frame_bars = tk.Frame(sec_build, border=0, padx=5, pady=5, bg=_BG)
        self.frame_bars.grid(row=1, column=0, sticky=N+S+W+E)

        self.pgrb1v = tk.IntVar()
        self.pgrb2v = tk.IntVar()
        self.pgrb3v = tk.IntVar()
        if _HAS_CTK:
            # ── Visualiseurs d'avancement en CustomTkinter ─────────────
            try:
                import O4_Theme_Manager as _TM
                _t = _TM.get_theme()
            except Exception:
                _t = {}
            _trough = _t.get("bg_secondary", "#2a4235")
            _fill   = _t.get("accent",       "#a6e3a1")
            _actcol = _t.get("btn_bg",       "#4a6b59")

            def _mkbar(col, activity=False):
                b = ctk.CTkProgressBar(
                    self.frame_bars, width=120, height=14,
                    mode="indeterminate" if activity else "determinate",
                    fg_color=_trough,
                    progress_color=_actcol if activity else _fill)
                if activity:
                    b.configure(indeterminate_speed=1)
                b.grid(row=0, column=col, padx=5, pady=6)
                return b

            self.pgrb1 = _mkbar(0)
            self.pgrb2 = _mkbar(1)
            self.pgrb3 = _mkbar(2)
            for _b in (self.pgrb1, self.pgrb2, self.pgrb3):
                _b.set(0)
            self.pgrbv = {1: self.pgrb1, 2: self.pgrb2, 3: self.pgrb3}
            self.pgrb_activity = _mkbar(3, activity=True)
            self._pgrb_ctk = True
        else:
            self.pgrbv = {1: self.pgrb1v, 2: self.pgrb2v, 3: self.pgrb3v}
            self.pgrb1 = ttk.Progressbar(self.frame_bars, mode="determinate", orient=HORIZONTAL, variable=self.pgrb1v, style="O4.Horizontal.TProgressbar")
            self.pgrb1.grid(row=0, column=0, padx=5, pady=0)
            self.pgrb2 = ttk.Progressbar(self.frame_bars, mode="determinate", orient=HORIZONTAL, variable=self.pgrb2v, style="O4.Horizontal.TProgressbar")
            self.pgrb2.grid(row=0, column=1, padx=5, pady=0)
            self.pgrb3 = ttk.Progressbar(self.frame_bars, mode="determinate", orient=HORIZONTAL, variable=self.pgrb3v, style="O4.Horizontal.TProgressbar")
            self.pgrb3.grid(row=0, column=2, padx=5, pady=0)
            # ── Barre d'activité (indéterminée) : signe de vie pendant les
            #    phases longues où le pourcentage ne bouge pas ───────────────
            self.pgrb_activity = ttk.Progressbar(self.frame_bars, mode="indeterminate", orient=HORIZONTAL, style="O4Act.Horizontal.TProgressbar")
            self.pgrb_activity.grid(row=0, column=3, padx=5, pady=0)
            self._pgrb_ctk = False

        # ── Label RAM live : déplacé ici, au bout de la ligne des barres de
        #    progression. Même objet et même mise à jour périodique
        #    (_update_ram_label) qu'avant — seul son emplacement change. ──
        self.frame_bars.columnconfigure(5, weight=1)
        self._ram_label = tk.Label(self.frame_bars,
            text="RAM: --",
            bg=_BG, fg=_FG2,
            font=("TkFixedFont", fs(10)))
        self._ram_label.grid(row=0, column=5, padx=12, sticky=E)
        self._update_ram_label()

        # ══ RUBRIQUE « Corrections avancées » RETIRÉE de l'écran principal ══
        # Le cadre et ses deux boutons — « Corrections R.G.B., Netteté,
        # saturation » (open_color_check) et « Correction imagerie/zone »
        # (open_correction_module) — sont désormais accessibles depuis la
        # barre de menus (menu Outils). Les méthodes moteur sont CONSERVÉES
        # (dormantes) plus bas dans ce fichier : retirer un bouton ne
        # supprime jamais sa fonction.

        # ── CONSOLE (row=1 principal — extensible) ─────────────────────
        self.frame_console = tk.Frame(self, border=4, relief=RIDGE, bg=_BG)
        self.frame_console.grid(row=1, column=0, sticky=N+S+W+E, padx=4, pady=4)
        self.frame_console.rowconfigure(0, weight=1)
        self.frame_console.columnconfigure(0, weight=1)
        self.console = tk.Text(self.frame_console, bd=0, font=("Courier", fs(13)))
        self.console.grid(row=0, column=0, sticky=N+S+E+W)
        # ── Barre de défilement verticale (droite) ─────────────────────
        self.console_scrollbar = tk.Scrollbar(self.frame_console, orient="vertical",
                                              command=self.console.yview)
        self.console_scrollbar.grid(row=0, column=1, sticky=N+S)
        self.console.config(yscrollcommand=self.console_scrollbar.set)
        # Lecture seule multi-OS : bloque saisie/suppression, autorise sélection et copie
        def _console_key(e):
            # Touches de navigation autorisées (déplacement/défilement seul, aucune édition)
            if e.keysym in ("Up", "Down", "Left", "Right",
                            "Prior", "Next", "Home", "End"):
                return None   # Flèches haut/bas, Page préc./suiv., Début/Fin
            # Ctrl (Win/Linux) = state & 0x4 / Cmd (Mac) = state & 0x8
            mod = e.state & 0x4 or e.state & 0x8
            if mod and e.keysym.lower() in ("c", "a"):
                return None   # Autoriser Ctrl+C / Ctrl+A / Cmd+C / Cmd+A
            return "break"    # Bloquer tout le reste
        self.console.bind("<Key>",       _console_key)
        self.console.bind("<BackSpace>", lambda e: "break")
        self.console.bind("<Delete>",    lambda e: "break")

        # ── Queues & redirection ───────────────────────────────────────
        self.console_queue = queue.Queue()
        self.console_update()
        self.pgrb_queue = queue.Queue()
        self.pgrb_update()
        self.stdout_orig = sys.stdout
        sys.stdout = self

        # ── Application du thème couleurs ─────────────────────────────
        try:
            import O4_Theme_Manager as _TM
            _TM.apply_to_root(self)
        except Exception:
            pass  # si O4_Theme_Manager absent → couleurs par défaut conservées

        # ── Restauration dernière session ──────────────────────────────
        try:
            f = open(os.path.join(FNAMES.Ortho4XP_dir, ".last_gui_params.txt"), "r")
            (lat, lon, default_website, default_zl) = f.readline().split()
            custom_build_dir = f.readline().strip()
            self.lat.set(lat); self.lon.set(lon)
            self.default_website.set(default_website); self.default_zl.set(default_zl)
            self.custom_build_dir.set(custom_build_dir)
            f.close()
        except:
            self.lat.set(48); self.lon.set(-6)
            self.default_website.set("BI"); self.default_zl.set(16)
            self.custom_build_dir.set("")

    # ── Callbacks tile_change / update_cfg (requis par .trace) ────────
    def tile_change(self, *args):
        try:
            CNORM.check_tile_change(int(self.lat.get()), int(self.lon.get()))
            self.cnorm_ref_label.config(
                text=tr('Réf: ') + (CNORM.REFERENCE_TEMP_NAME or CNORM.REFERENCE_DEFAULT_NAME),
                fg="darkorange" if CNORM.REFERENCE_TEMP else _FG)
        except:
            pass

    def update_cfg(self, *args):
        try:
            CFG.update_tile_cfg(self)
        except:
            pass

    def _on_imagery_change(self, *args):
        """Intercepte la sélection 'Personnel' pour ouvrir la fenêtre de gestion.
        Pour tout autre provider, délègue simplement à update_cfg."""
        val = self.default_website.get()
        if val == tr("Personnel"):
            # Empêche "Personnel" d'être écrit dans le cfg comme provider réel
            self.after(0, self.open_personal_provider_window)
        else:
            self.update_cfg()

    # ── Color Normalize ────────────────────────────────────────────────
    #  Couleur "grisée" appliquée aux titres/textes d'un cadre décoché.
    _CNORM_INACTIVE_FG = "#6f8579"

    def _set_widget_fg(self, widget, color):
        """Recolore un widget si présent (silencieux si absent/détruit)."""
        try:
            if widget is not None:
                widget.config(fg=color)
        except Exception:
            pass

    def _sync_cnorm_slider_state(self):
        """Cadre Normalisation : curseur + titres/textes actifs seulement si la case est cochée."""
        on = bool(self.cnorm_enabled.get())
        try:
            self.cnorm_slider.configure(state=("normal" if on else "disabled"))
        except Exception:
            pass
        grey = self._CNORM_INACTIVE_FG
        self._set_widget_fg(getattr(self, "_lf_norm", None),          _FG2      if on else grey)
        self._set_widget_fg(getattr(self, "_cnorm_desc_label", None), "#cbdcc9" if on else grey)
        self._set_widget_fg(getattr(self, "cnorm_pct_label", None),   _FG2      if on else grey)
        self._set_widget_fg(getattr(self, "cnorm_ref_label", None),   _FG2      if on else grey)

    def _sync_cnorm_sat_slider_state(self):
        """Cadre Saturation : curseur + titres/textes actifs seulement si la case est cochée."""
        on = bool(self.cnorm_sat_enabled.get())
        try:
            self.cnorm_sat_slider.configure(state=("normal" if on else "disabled"))
        except Exception:
            pass
        grey = self._CNORM_INACTIVE_FG
        self._set_widget_fg(getattr(self, "_lf_sat", None),               _FG2      if on else grey)
        self._set_widget_fg(getattr(self, "_cnorm_sat_desc_label", None), "#cbdcc9" if on else grey)
        self._set_widget_fg(getattr(self, "cnorm_sat_label", None),       _FG2      if on else grey)
        self._set_widget_fg(getattr(self, "_cnorm_sat_legend", None),     _FG2      if on else grey)

    def toggle_cnorm(self):
        CNORM.color_normalization_enabled = bool(self.cnorm_enabled.get())
        self._sync_cnorm_slider_state()

    def update_cnorm_strength(self, value):
        CNORM.CORRECTION_STRENGTH = int(value) / 100.0
        self.cnorm_pct_label.config(text=str(value) + "%")

    def toggle_cnorm_sat(self):
        CNORM.saturation_enabled = bool(self.cnorm_sat_enabled.get())
        self._sync_cnorm_sat_slider_state()

    def update_cnorm_sat(self, value):
        v = int(value)
        CNORM.saturation_strength = v / 100.0
        if v == 100:
            self.cnorm_sat_label.config(text=tr('100%  (réf.)'))
        elif v < 100:
            self.cnorm_sat_label.config(text=f"{v}%  (−sat.)")
        else:
            self.cnorm_sat_label.config(text=f"{v}%  (+sat.)")

    def _update_ram_label(self):
        """
        Met à jour le label RAM toutes les 10 secondes.
        psutil est appelé dans un thread séparé pour ne jamais
        bloquer le thread tkinter principal (évite le gel de l'UI).
        """
        def _fetch():
            try:
                if _mem_enabled:
                    stats = _memory_stats()
                    pct   = stats.get("ram_percent", 0)
                    avail = stats.get("ram_available_gb", 0)
                    color = "#ff5555" if pct > 80 else "#50fa7b" if pct < 60 else "#ffb86c"
                    # Retour dans le thread tkinter via after(0)
                    self.after(0, lambda: self._apply_ram_label(
                        f"RAM: {pct:.0f}%  ({avail:.1f}Go)", color))
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()
        self.after(10000, self._update_ram_label)

    def _apply_ram_label(self, text, color):
        """Applique le texte RAM dans le thread tkinter — non bloquant."""
        try:
            self._ram_label.config(text=text, fg=color)
        except Exception:
            pass

    def open_color_check(self):
        # Désactive Color Normalize et décoche la case avant d'ouvrir
        self.cnorm_enabled.set(0)
        CNORM.color_normalization_enabled = False
        self._sync_cnorm_slider_state()

        lat = int(self.lat.get() or 0)
        lon = int(self.lon.get() or 0)
        custom = self.custom_build_dir.get() or ""
        build_dir = FNAMES.build_dir(lat, lon, custom)
        CC.open_color_check(self, os.path.join(build_dir, "textures"), {"lat": lat, "lon": lon})

    def open_altimetrie_module(self):
        """Point d'entrée du bouton « Altimétrie / DEM ».

        Délègue au module autonome O4_Altimetrie_Utils, qui assemble les
        fichiers altimétriques de la tuile (reprojection EPSG:4326,
        découpe avec débord de chevauchement, fusion) et renseigne
        custom_dem. Aucun fichier du pipeline n'est modifié.

        Si le module est absent ou lève une erreur, le GUI reste
        parfaitement fonctionnel : on se contente d'informer.
        """
        from tkinter import messagebox
        if not (_altimod_enabled and _ALTIMOD is not None):
            messagebox.showinfo(
                tr("Altimétrie / DEM"),
                tr("Le module O4_Altimetrie_Utils.py est introuvable "
                   "dans le dossier src/."))
            return
        try:
            _ALTIMOD.open_altimetrie_window(self)
        except Exception as _e:
            try:
                UI.vprint(1, "[Altimetrie] " + str(_e))
            except Exception:
                pass
            messagebox.showerror(tr("Altimétrie / DEM"), str(_e))

    def open_bathymetrie_module(self):
        """Point d'entrée du bouton « Bathymétrie ».

        Délègue au module autonome O4_Bathymetrie_Utils, jumeau de
        l'Altimétrie : même structure automatisée et même moteur
        d'assemblage (reprojection EPSG:4326, découpe avec débord,
        fusion), mais pour les relevés de FONDS. Renseigne
        custom_bathy_dem sans jamais toucher custom_dem. Aucun fichier
        du pipeline n'est modifié.

        Si le module est absent ou lève une erreur, le GUI reste
        parfaitement fonctionnel : on se contente d'informer.
        """
        from tkinter import messagebox
        if not (_bathymod_enabled and _BATHYMOD is not None):
            messagebox.showinfo(
                tr("Bathymétrie"),
                tr("Le module O4_Bathymetrie_Utils.py est introuvable "
                   "dans le dossier src/."))
            return
        try:
            _BATHYMOD.open_bathymetrie_window(self)
        except Exception as _e:
            try:
                UI.vprint(1, "[Bathymetrie] " + str(_e))
            except Exception:
                pass
            messagebox.showerror(tr("Bathymétrie"), str(_e))

    def open_lay_generator_module(self):
        import O4_lay_generator
        O4_lay_generator.run_lay_generator(parent=self)

    def open_pbf_module(self):
        """Point d'entrée du bouton « Cache OSM local (.pbf) ».

        Délègue au module autonome O4_PBF_Utils, qui remplit OSM_data/ à
        partir d'un extrait .pbf local (Geofabrik ou équivalent). Le Step 1
        recycle ensuite ces fichiers au lieu d'interroger Overpass.
        Aucun fichier du pipeline n'est modifié par ce bouton.

        Si le module est absent ou lève une erreur, le GUI reste
        parfaitement fonctionnel : on se contente d'informer.
        """
        from tkinter import messagebox
        if not (_pbfmod_enabled and _PBFMOD is not None):
            messagebox.showinfo(
                tr("Cache OSM local (.pbf)"),
                tr("Le module O4_PBF_Utils.py est introuvable "
                   "dans le dossier src/."))
            return
        try:
            _PBFMOD.open_pbf_window(self)
        except Exception as _e:
            try:
                UI.vprint(1, "[PBF] " + str(_e))
            except Exception:
                pass
            messagebox.showerror(tr("Cache OSM local (.pbf)"), str(_e))
    def open_provider_score_module(self):
        """Fenêtre Analyse Fournisseurs avec validation préalable et exclusion de ZonePhoto."""
        from tkinter import messagebox
        import O4_UI_Dialogs as DIALOGS

        if not (_scoremod_enabled and _SCOREMOD is not None):
            messagebox.showinfo(
                tr("Analyse Fournisseurs"),
                tr("Le module O4_Provider_Score.py est introuvable dans le dossier src/."))
            return

        # 1. On lance d'abord la fenêtre d'avertissement d'usage personnel
        # On passe 'self' (la fenêtre principale) et la fonction de création réelle
        def afficher_analyse_apres_validation():
            self._creer_fenetre_analyse_fournisseurs()

        # Ouvre la boîte de dialogue (Je valide / Je quitte)
        DIALOGS.valider_usage_personnel_callback(self, action_valider=afficher_analyse_apres_validation)

    def _creer_fenetre_analyse_fournisseurs(self):
        """Création de la fenêtre Analyse Fournisseurs (exclut automatique de ZonePhoto.comb)."""
        import os
        from tkinter import messagebox

        try:
            report_raw = _SCOREMOD.report_all()
            data       = _SCOREMOD._load_all_scores()

            # --- 1. CHARGEMENT AUTOMATIQUE DE ZONEPHOTO.COMB ---
            zonephoto_providers = {"zonephoto"}  # Inclut le nom principal par défaut

            # Emplacements possibles pour trouver ZonePhoto.comb
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "Providers", "ZonePhoto.comb"),
                os.path.join(os.path.dirname(__file__), "Providers", "ZonePhoto.comb"),
                "ZonePhoto.comb",
                "Providers/ZonePhoto.comb"
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                parts = line.split()
                                if parts:
                                    # Ajoute le nom du provider en minuscules
                                    zonephoto_providers.add(parts[0].lower())
                    break

            # Helper pour vérifier si un nom appartient à la liste ZonePhoto
            def est_zonephoto(nom):
                if not nom:
                    return False
                nom_low = nom.lower().strip()
                return any(nom_low.startswith(zp) for zp in zonephoto_providers)

            # --- 2. FILTRAGE DU TEXTE DU RAPPORT ---
            lines = report_raw.splitlines() if report_raw else []
            filtered_lines = []
            for l in lines:
                l_strip = l.strip()
                if not l_strip:
                    continue
                # Extrait le premier mot de la ligne (nom du provider dans le rapport)
                first_word = l_strip.split()[0]
                if not est_zonephoto(first_word):
                    filtered_lines.append(l)

            report = "\n".join(filtered_lines)

            # --- 3. EXCLUSION POUR LE CALCUL DU MEILLEUR PROVIDER ---
            best_code  = None
            best_score = -1.0
            for key, s in data.items():
                p_code = s.get("provider_code", "")
                
                # On ignore tout ce qui vient de ZonePhoto / ZonePhoto.comb
                if est_zonephoto(p_code):
                    continue

                g = s.get("global_score", 0)
                if g > best_score:
                    best_score = g
                    best_code  = p_code

            # --- 4. CRÉATION DE LA FENÊTRE ---
            win = tk.Toplevel(self)
            win.title(tr("Analyse Fournisseurs"))
            win.configure(bg=_BG)
            win.geometry("780x520")
            win.minsize(600, 400)

            # Zone de texte (rapport)
            txt = tk.Text(win, bg=_CON_BG, fg=_CON_FG,
                          font=("TkFixedFont", 10), wrap="none")
            txt.pack(fill="both", expand=True, padx=8, pady=(8, 4))
            txt.insert("1.0", report if data else tr(
                "Aucun score enregistré.\n\nLancez d'abord un Build Imagery/DSF\npour générer des scores."))
            txt.config(state="disabled")

            # Cadre boutons
            frame_btn = tk.Frame(win, bg=_BG)
            frame_btn.pack(fill="x", padx=8, pady=8)

            info_label = tk.Label(frame_btn, bg=_BG, fg=_FG2,
                                  font=("TkFixedFont", 10))
            info_label.pack(side="left", padx=5)

            if best_code:
                info_label.config(
                    text=f"{tr('Meilleur provider détecté :')} {best_code}  ({best_score:.1f}/100)")
            else:
                info_label.config(text=tr("Aucun score disponible pour cette tuile."))

            def apply_best():
                if not best_code:
                    messagebox.showinfo(tr("Analyse Fournisseurs"),
                                        tr("Aucun score disponible pour cette tuile."))
                    return
                # Applique le provider dans la liste déroulante principale
                self.default_website.set(best_code)
                messagebox.showinfo(
                    tr("Analyse Fournisseurs"),
                    f"{tr('Provider appliqué :')} {best_code}")
                win.destroy()

            # 3. Boutons avec gestion Mac / highlightbackground pour éviter les carrés blancs
            import sys
            btn_apply = _ctk_button(
                frame_btn,
                text=tr("Utiliser le meilleur provider pour la tuile active"),
                command=apply_best)
            btn_close = _ctk_button(
                frame_btn, text=tr("Fermer"), command=win.destroy)

            btn_apply.pack(side="right", padx=5)
            btn_close.pack(side="right", padx=5)

        except Exception as _e:
            try:
                UI.vprint(1, "[ProviderScore] " + str(_e))
            except Exception:
                pass
            messagebox.showerror(tr("Analyse Fournisseurs"), str(_e))

    def open_correction_module(self):
        """Point d'entrée du bouton « Correction imagerie/zone ».

        Étape 1 (architecture) : délègue au nouveau module autonome
        O4_Correction_Utils s'il est disponible. Pour l'instant ce module
        se contente de rouvrir la fenêtre de correction existante, afin de
        NE RIEN CASSER : le workflow validé reste identique. Le preview
        enrichi (tous les DDS, terre comprise) y sera ajouté à l'étape 2.

        Repli de sécurité : si le module est absent ou lève une erreur,
        on rouvre directement l'ancienne fenêtre (open_patch_correction).
        """
        if _corrmod_enabled and _CORRMOD is not None:
            try:
                _CORRMOD.open_correction_window(self)
                return
            except Exception as _e:
                try:
                    UI.vprint(1, tr("[CorrMod] Repli sur l'ancienne fenêtre : ")
                                 + str(_e))
                except Exception:
                    pass
        # Repli : comportement historique inchangé
        self.open_patch_correction()

    def open_patch_correction(self):
        """Ouvre directement la fenêtre Correction patches sans lancer de build."""
        try:
            lat = int(self.lat.get() or 0)
            lon = int(self.lon.get() or 0)
            # Construire tile_key au format +46-003
            sign_lat = "+" if lat >= 0 else "-"
            sign_lon = "+" if lon >= 0 else "-"
            tile_key = f"{sign_lat}{abs(lat):02d}{sign_lon}{abs(lon):03d}"
            # Trouver le ZL depuis l'interface
            try:
                zl = int(self.default_zl.get())
            except Exception:
                zl = 17
            patch_dir = os.path.join(FNAMES.Patch_dir, tile_key, f"PATCH_{zl}")
            if not os.path.isdir(patch_dir):
                from tkinter import messagebox
                messagebox.showinfo(
                    tr("Correction Patches"),
                    tr("Aucun dossier PATCH trouvé pour cette tuile.\n"
                       "Lancer d'abord le Step 2.1 — Sea Patches."))
                return
            existing = sorted(f for f in os.listdir(patch_dir) if f.endswith(".jpg"))
            if not existing:
                from tkinter import messagebox
                messagebox.showinfo(
                    tr("Correction Patches"),
                    tr("Aucun patch JPG trouvé dans :\n") + patch_dir)
                return
            # Couleurs thème
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
            import O4_Tile_Utils as _TILE
            _TILE._open_correction_window(
                self, patch_dir, existing,
                BG, FG, FG2, PREV_BG, FONT, FONT_T, _tr)
        except Exception as _e:
            from tkinter import messagebox
            messagebox.showerror(tr("Correction Patches"), str(_e))

    # ── Icônes & navigation ────────────────────────────────────────────
    def choose_custom_build_dir(self):
        d = filedialog.askdirectory()
        if d: self.custom_build_dir.set(d + "/")

    def open_simulator_window(self):
        """Ouvre le Simulateur visuel (module O4_Simulator_Utils, non bloquant)."""
        from tkinter import messagebox
        # Recharge au cas où le module a été ajouté après le démarrage
        global _SIMMOD, _simmod_enabled, Ortho4XP_Simulator
        if not (_simmod_enabled and _SIMMOD is not None):
            try:
                import O4_Simulator_Utils as _SIMMOD
                _simmod_enabled = True
                Ortho4XP_Simulator = _SIMMOD.Ortho4XP_Simulator
            except Exception as e:
                messagebox.showinfo(
                    tr("Simulateur"),
                    tr("Le module O4_Simulator_Utils.py est introuvable ou en erreur dans src/.\n")
                    + str(e))
                return
        if hasattr(self, "_sim_win") and self._sim_win and \
                self._sim_win.winfo_exists():
            self._sim_win.lift()
            self._sim_win.focus_force()
            return
        try:
            lat = int(self.lat.get() or 46)
            lon = int(self.lon.get() or -3)
            custom = self.custom_build_dir.get() or ""
            cls = getattr(_SIMMOD, "Ortho4XP_Simulator", None) or Ortho4XP_Simulator
            if cls is None:
                raise RuntimeError("Ortho4XP_Simulator introuvable dans O4_Simulator_Utils")
            self._sim_win = cls(self, lat, lon, custom)
        except Exception as e:
            messagebox.showinfo("Simulateur", tr("Erreur : ") + str(e))

    def _reload_personal_providers(self):
        """Recharge les providers depuis le disque et met à jour img_combo."""
        try:
            IMG.initialize_providers_dict()
            IMG.initialize_combined_providers_dict()
        except Exception:
            pass
        try:
            def _in_gui(p):
                if isinstance(p, dict): return p.get("in_GUI", True)
                return getattr(p, "in_GUI", True)
            full = sorted([
                c for c in set(IMG.providers_dict)
                if _in_gui(IMG.providers_dict[c])
            ] + sorted(set(IMG.combined_providers_dict)))
            for rm in ("OSM", "SEA"):
                try: full.remove(rm)
                except: pass
            self.map_list = full if full else ["BI","GO2","ARC","IGN","SWISSTOPO","ZonePhoto"]
        except:
            pass
        self._full_map_list = self.map_list + [tr("Personnel")]
        self.img_combo.config(values=self._full_map_list)

    def open_personal_provider_window(self):
        """Ouvre la fenêtre de gestion des providers personnels."""
        # Ne pas ouvrir plusieurs instances
        if hasattr(self, "_personal_win") and self._personal_win and                 self._personal_win.winfo_exists():
            self._personal_win.lift()
            self._personal_win.focus_force()
            return
        self._personal_win = Ortho4XP_PersonalProvider(self)

    def open_config_window(self):
        # Ne pas ouvrir plusieurs fois la même fenêtre
        if hasattr(self, "_config_win") and self._config_win and                 self._config_win.winfo_exists():
            self._config_win.lift()
            self._config_win.focus_force()
            return
        try:
            self._config_win = CFG.Ortho4XP_Config(self)
        except Exception as e:
            messagebox.showinfo("Config", tr("Fenêtre de configuration\n(") + str(e) + ")")

    def open_custom_zl_window(self):
        try:
            if hasattr(self, 'custom_zl_window') and self.custom_zl_window.winfo_exists():
                self.custom_zl_window.lift()
                return
            lat = int(self.lat.get() or 48); lon = int(self.lon.get() or 6)
            self.custom_zl_window = Ortho4XP_Custom_ZL(self, lat, lon)
        except Exception as e: messagebox.showinfo("Custom ZL", tr("Erreur : ") + str(e))

    def open_earth_window(self):
        try:
            if hasattr(self, 'earth_window') and self.earth_window.winfo_exists():
                self.earth_window.lift()
                return
            lat = int(self.lat.get() or 48); lon = int(self.lon.get() or 6)
            self.earth_window = Ortho4XP_Earth_Preview(self, lat, lon)
        except Exception as e: messagebox.showinfo("Earth", tr("Erreur : ") + str(e))

    def set_red_flag(self):
        UI.red_flag = True
        messagebox.showinfo("Red Flag", tr('Red flag activé'))

    def exit_prg(self):
        try:
            f = open(os.path.join(FNAMES.Ortho4XP_dir, ".last_gui_params.txt"), "w")
            website = self.default_website.get() or "BI"
            f.write(f"{self.lat.get()} {self.lon.get()} {website} {self.default_zl.get()}\n")
            f.write(self.custom_build_dir.get() + "\n")
            f.close()
        except: pass
        # Supprimer les .pyc en cache pour éviter les conflits au prochain démarrage
        try:
            import pathlib
            for pyc in pathlib.Path(os.path.join(FNAMES.Ortho4XP_dir, "src")).rglob("*.pyc"):
                pyc.unlink()
        except: pass
        self.destroy()

    # ── Build ──────────────────────────────────────────────────────────
    def build_poly_file(self):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Step 1 — Vectors"))
        self._activity_start()
        def _run():
            VMAP.build_poly_file(tile)
            _build_timeline.end(tr("Step 1 — Vectors"))
            self._activity_stop()
        threading.Thread(target=_run).start()

    def build_mesh(self, event=None):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Step 2 — Mesh"))
        self._activity_start()
        def _run():
            MESH.build_mesh(tile)
            _build_timeline.end(tr("Step 2 — Mesh"))
            self._activity_stop()
        threading.Thread(target=_run).start()

    def sort_mesh(self, event=None):
        try: threading.Thread(target=MESH.sort_mesh, args=[self.tile_from_interface()]).start()
        except: pass

    def community_mesh(self, event=None):
        try: threading.Thread(target=MESH.community_mesh, args=[self.tile_from_interface()]).start()
        except: pass

    def build_masks(self, event=None):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Step 2.5 — Masks"))
        self._activity_start()
        def _run():
            MASK.build_masks(tile)
            _build_timeline.end(tr("Step 2.5 — Masks"))
            self._activity_stop()
        threading.Thread(target=_run).start()

    def build_sea_patches(self):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Step 2.1 — Sea Patches"))
        self._activity_start()
        def _run():
            TILE.build_sea_patches(tile)
            _build_timeline.end(tr("Step 2.1 — Sea Patches"))
            self._activity_stop()
            _build_timeline.report()
        threading.Thread(target=_run).start()

    def build_tile(self):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Step 3 — DSF/Imagery"))
        self._activity_start()
        def _run():
            TILE.build_tile(tile)
            _build_timeline.end(tr("Step 3 — DSF/Imagery"))
            self._activity_stop()
            _build_timeline.report()
        threading.Thread(target=_run).start()

    def build_all(self):
        tile = self.tile_from_interface()
        _build_timeline.start(tr("Build All"))
        self._activity_start()
        def _run():
            TILE.build_all(tile)
            _build_timeline.end(tr("Build All"))
            self._activity_stop()
            _build_timeline.report()
        threading.Thread(target=_run).start()

    def get_lat_lon(self):
        lat = int(self.lat.get() or 48)
        lon = int(self.lon.get() or -6)
        return (lat, lon)

    def tile_from_interface(self):
        lat = int(self.lat.get() or 48)
        lon = int(self.lon.get() or -6)
        tile = CFG.Tile(lat, lon, self.custom_build_dir.get() or "")
        tile.default_website = self.default_website.get() or "BI"
        tile.default_zl = int(self.default_zl.get() or 16)
        return tile

    # ── Console & progress ─────────────────────────────────────────────
    def write(self, line):
        self.console_queue.put(line)

    def console_update(self):
        try:
            while True:
                line = self.console_queue.get_nowait()
                self.console.insert(END, str(line))
                self.console.see(END)
        except queue.Empty:
            pass
        self.after(100, self.console_update)

    def pgrb_update(self):
        try:
            while True:
                (bar_id, value) = self.pgrb_queue.get_nowait()
                if bar_id in self.pgrbv:
                    if getattr(self, "_pgrb_ctk", False):
                        self.pgrbv[bar_id].set(
                            max(0.0, min(1.0, float(value) / 100.0)))
                    else:
                        self.pgrbv[bar_id].set(value)
        except queue.Empty:
            pass
        self.after(100, self.pgrb_update)

    def _activity_start(self):
        # Lance l'animation de la barre d'activité (appel thread-safe via after)
        try:
            if getattr(self, "_pgrb_ctk", False):
                self.after(0, self.pgrb_activity.start)
            else:
                self.after(0, lambda: self.pgrb_activity.start(15))
        except Exception:
            pass

    def _activity_stop(self):
        # Arrête l'animation de la barre d'activité (appel thread-safe via after)
        try:
            self.after(0, self.pgrb_activity.stop)
        except Exception:
            pass

    @staticmethod
    def _lighten(hexcol, factor):
        # Teinte plus claire (facteur > 1) pour l'éclat au survol.
        try:
            h = hexcol.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hexcol

    def _themed_button(self, parent, text, command=None, width=None,
                       corner_radius=8):
        # Bouton au look moderne (CustomTkinter) si disponible, sinon repli
        # ttk. Les couleurs suivent O4_Theme_Manager ; survol « vivant ».
        if _HAS_CTK:
            try:
                import O4_Theme_Manager as _TM
                _t = _TM.get_theme()
            except Exception:
                _t = {}
            base = _t.get("btn_bg", "#4a6b59")
            b = ctk.CTkButton(
                parent, text=text, command=command,
                corner_radius=corner_radius, border_width=1, height=30,
                fg_color=base, hover_color=self._lighten(base, 1.30),
                border_color=_t.get("border", base),
                text_color=_t.get("btn_fg", "#ffffff"))
            if width:
                b.configure(width=width)
            # macOS : le remplissage arrondi du CTkButton n'est dessine
            # qu'une fois le bouton dimensionne. On force un redessin apres
            # la mise en page pour eviter le rectangle sombre derriere le
            # texte au repos (qui ne disparaissait qu'au survol).
            b.after_idle(
                lambda btn=b, c=base: btn.winfo_exists()
                and btn.configure(fg_color=c))
            return b
        kw = {"text": text}
        if command is not None:
            kw["command"] = command
        if width:
            kw["width"] = max(1, int(width / 8))
        return ttk.Button(parent, **kw)

    def _bind_clicks(self, btn, handler):
        # Lie un gestionnaire de clic à un bouton, qu'il soit CTkButton
        # (surfaces internes _canvas/_text_label) ou ttk/tk (widget seul).
        # Le gestionnaire lit event.state pour Shift/Ctrl → fire une seule
        # fois (return "break" stoppe la propagation).
        targets = []
        for attr in ("_canvas", "_text_label"):
            w = getattr(btn, attr, None)
            if w is not None:
                targets.append(w)
        if not targets:
            targets = [btn]
        for w in targets:
            w.bind("<ButtonPress-1>", handler, add="+")

    def _on_mesh_click(self, event):
        # Triangulate 3D Mesh : clic = build_mesh, Shift+clic = sort_mesh,
        # Ctrl+clic = community_mesh (comportement d'origine préservé).
        try:
            if event.state & 0x0001:        # Shift
                self.sort_mesh(event)
            elif event.state & 0x0004:      # Control
                self.community_mesh(event)
            else:
                self.build_mesh(event)
        except Exception as e:
            print(f"[GUI] clic mesh: {e}")
        return "break"

    def _on_masks_click(self, event):
        # Draw Water Masks : clic (avec ou sans Shift) = build_masks.
        try:
            self.build_masks(event)
        except Exception as e:
            print(f"[GUI] clic masks: {e}")
        return "break"

    def _themed_slider(self, parent, frm, to, variable, callback, width=180):
        # Curseur moderne (CTkSlider) si dispo, sinon repli tk.Scale.
        # CTkSlider envoie un flottant → on passe un entier au callback,
        # qui attend int(value) comme avec tk.Scale.
        if _HAS_CTK:
            try:
                import O4_Theme_Manager as _TM
                _t = _TM.get_theme()
            except Exception:
                _t = {}
            acc = _t.get("accent", "#a6e3a1")
            return ctk.CTkSlider(
                parent, from_=frm, to=to, number_of_steps=int(to - frm),
                variable=variable, width=width, height=18,
                command=lambda v: callback(int(float(v))),
                fg_color=_t.get("bg_secondary", "#2a4235"),
                progress_color=acc, button_color=acc,
                button_hover_color=self._lighten(acc, 1.15))
        return tk.Scale(parent, from_=frm, to=to, orient=HORIZONTAL,
            variable=variable, command=callback,
            bg=_BG, fg=_FG, troughcolor="#1a2e25",
            length=width, showvalue=True)

if __name__ == "__main__":
    Ortho4XP_GUI().mainloop()

# ═══════════════════════════════════════════════════════════════════════════════
def _ctk_button(parent, text=None, command=None, width=None,
                corner_radius=8, **ttk_kw):
    """Bouton texte au look CustomTkinter (meme style que la fenetre
    principale) ; repli automatique sur ttk.Button si CustomTkinter absent.
    Les kwargs ttk (style, takefocus...) ne s'appliquent qu'au repli ttk.
    """
    if _HAS_CTK:
        try:
            import O4_Theme_Manager as _TM
            _t = _TM.get_theme()
        except Exception:
            _t = {}
        base = _t.get("btn_bg", "#4a6b59")
        b = ctk.CTkButton(
            parent, text=text, command=command,
            corner_radius=corner_radius, border_width=1, height=30,
            fg_color=base, hover_color=Ortho4XP_GUI._lighten(base, 1.30),
            border_color=_t.get("border", base),
            text_color=_t.get("btn_fg", "#ffffff"))
        if width:
            b.configure(width=width)
        # Meme correctif macOS que _themed_button : redessin force apres
        # mise en page pour supprimer le rectangle sombre au repos.
        b.after_idle(
            lambda btn=b, c=base: btn.winfo_exists()
            and btn.configure(fg_color=c))
        return b
    kw = {}
    if text is not None:
        kw["text"] = text
    if command is not None:
        kw["command"] = command
    if width:
        kw["width"] = max(1, int(width / 8))
    kw.update(ttk_kw)
    return ttk.Button(parent, **kw)


class Ortho4XP_PersonalProvider(tk.Toplevel):
    """Fenêtre de gestion des providers personnels (TMS).
    Crée / modifie / supprime des fichiers .lay dans Providers/Personnel/.
    Après chaque opération, recharge la liste img_combo de la fenêtre parent.
    """

    # Noms réservés — ne peuvent pas être utilisés comme code provider
    _RESERVED = {"OSM", "SEA", "PATCH", "ZonePhoto", "Personnel", "Custom"}

    def __init__(self, parent):
        _reload_theme()
        self.parent_gui = parent
        tk.Toplevel.__init__(self, parent)
        self.configure(bg=_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title(tr("personal_provider_window_title"))
        # Largeur fixe, hauteur extensible — update_idletasks force le rendu
        self.resizable(False, True)
        self.geometry("760x500")
        self.update_idletasks()
        self.minsize(760, 460)

        # ── Dossier de stockage ──────────────────────────────────
        self._provider_dir = os.path.join(FNAMES.Provider_dir, "Personnel")
        os.makedirs(self._provider_dir, exist_ok=True)

        self._build_ui()
        self._refresh_list()

        # ── Application du thème (après _build_ui pour couvrir tous les widgets)
        try:
            import O4_Theme_Manager as _TM
            _TM.apply_to_root(self)
        except Exception:
            pass  # thème absent → couleurs par défaut conservées

    # ── Construction UI ──────────────────────────────────────────
    def _build_ui(self):
        """Layout pack — labels en largeur fixe, champs extensibles."""
        PAD  = dict(padx=10, pady=4)
        LPAD = dict(padx=10, pady=2)
        # Largeur fixe des labels colonne gauche (en pixels)
        LBL_W = 200

        # ── Titre liste ───────────────────────────────────────────
        tk.Label(self, text=tr("personal_provider_list_label"),
                 bg=_BG, fg=_FG, font=("TkFixedFont", 11, "bold"),
                 anchor="w").pack(fill="x", **LPAD)

        # ── Listbox + scrollbar ──────────────────────────────────
        frm_list = tk.Frame(self, bg=_BG)
        frm_list.pack(fill="x", padx=10, pady=2)
        sb = tk.Scrollbar(frm_list, orient="vertical")
        self._listbox = tk.Listbox(frm_list, bg="#1a2e25", fg=_FG,
                                   selectbackground=_ACCENT,
                                   selectforeground="#1e3028",
                                   font=("TkFixedFont", 11),
                                   height=4, activestyle="none",
                                   yscrollcommand=sb.set)
        sb.config(command=self._listbox.yview)
        self._listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        # ── Hint sélection ───────────────────────────────────────
        self._hint_lbl = tk.Label(self,
                                  text=tr("personal_provider_select_hint"),
                                  bg=_BG, fg="#888888",
                                  font=("TkFixedFont", 10, "italic"),
                                  anchor="w")
        self._hint_lbl.pack(fill="x", padx=12, pady=2)

        # ── Séparateur visuel ────────────────────────────────────
        tk.Frame(self, bg=_BTN_BG, height=1).pack(
            fill="x", padx=10, pady=4)

        # ── Ligne Nom provider ───────────────────────────────────
        frm_name = tk.Frame(self, bg=_BG)
        frm_name.pack(fill="x", **PAD)
        tk.Label(frm_name, text=tr("personal_provider_name_label"),
                 bg=_BG, fg=_FG, font=("TkFixedFont", 11),
                 width=26, anchor="e").pack(side="left")
        self._name_var = tk.StringVar()
        self._name_entry = tk.Entry(frm_name, textvariable=self._name_var,
                                    bg="#f0f4f2", fg="#1e3028",
                                    font=("TkFixedFont", 11))
        self._name_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # ── Ligne URL jpg ────────────────────────────────────────
        frm_url_row = tk.Frame(self, bg=_BG)
        frm_url_row.pack(fill="x", **PAD)
        tk.Label(frm_url_row, text=tr("personal_provider_url_label"),
                 bg=_BG, fg=_FG, font=("TkFixedFont", 11),
                 width=26, anchor="ne").pack(side="left")
        frm_url_right = tk.Frame(frm_url_row, bg=_BG)
        frm_url_right.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._url_entry = tk.Text(frm_url_right, height=3,
                                  bg="#f0f4f2", fg="#1e3028",
                                  font=("TkFixedFont", 10), wrap="word")
        self._url_entry.pack(fill="x")
        tk.Label(frm_url_right, text=tr("personal_provider_url_hint"),
                 bg=_BG, fg="#888888",
                 font=("TkFixedFont", 9, "italic"),
                 anchor="w").pack(fill="x")

        # ── Statut ───────────────────────────────────────────────
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(self, textvariable=self._status_var,
                                    bg=_BG, fg=_FG2,
                                    font=("TkFixedFont", 10, "italic"),
                                    wraplength=720, anchor="w")
        self._status_lbl.pack(fill="x", padx=12, pady=(6, 2))

        # ── Boutons ───────────────────────────────────────────────
        frm_btn = tk.Frame(self, bg=_BG)
        frm_btn.pack(fill="x", padx=10, pady=8)
        for i in range(4):
            frm_btn.columnconfigure(i, weight=1)
        _ctk_button(frm_btn, text=tr("personal_provider_save_btn"),
                   command=self._save).grid(
                   row=0, column=0, sticky="ew", padx=4)
        _ctk_button(frm_btn, text=tr("personal_provider_modify_btn"),
                   command=self._modify).grid(
                   row=0, column=1, sticky="ew", padx=4)
        _ctk_button(frm_btn, text=tr("personal_provider_delete_btn"),
                   command=self._delete).grid(
                   row=0, column=2, sticky="ew", padx=4)
        _ctk_button(frm_btn, text=tr("personal_provider_cancel_btn"),
                   command=self._on_close).grid(
                   row=0, column=3, sticky="ew", padx=4)

    # ── Helpers internes ─────────────────────────────────────────
    def _lay_path(self, code):
        return os.path.join(self._provider_dir, code + ".lay")

    def _list_personal_providers(self):
        """Retourne la liste triée des codes providers présents dans Personnel/."""
        try:
            return sorted(
                f[:-4] for f in os.listdir(self._provider_dir)
                if f.endswith(".lay")
            )
        except Exception:
            return []

    def _refresh_list(self):
        """Recharge la Listbox depuis le dossier Personnel/."""
        self._listbox.delete(0, "end")
        for code in self._list_personal_providers():
            self._listbox.insert("end", code)

    def _get_url_from_entry(self):
        return self._url_entry.get("1.0", "end").strip()

    def _set_url_entry(self, url):
        self._url_entry.delete("1.0", "end")
        self._url_entry.insert("1.0", url)

    def _read_url_from_lay(self, code):
        """Lit l'url_template d'un fichier .lay existant."""
        try:
            path = self._lay_path(code)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("url_template"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        except Exception:
            pass
        return ""

    def _write_lay(self, code, url):
        """Ecrit le fichier .lay TMS pour le provider personnel."""
        path = self._lay_path(code)
        content = (
            "request_type = tms\n"
            "grid_type = webmercator\n"
            "url_template = " + url + "\n"
            "in_GUI = True\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _validate_inputs(self, code, url):
        """Valide le code et l'URL. Retourne (True, "") ou (False, message)."""
        if not code:
            return False, tr("personal_provider_err_name")
        if not code.replace("_", "").replace("-", "").isalnum():
            return False, tr("personal_provider_err_name_invalid")
        if code.upper() in {r.upper() for r in self._RESERVED}:
            return False, tr("personal_provider_err_reserved")
        if not url:
            return False, tr("personal_provider_err_url")
        return True, ""

    def _set_status(self, msg, ok=True):
        self._status_var.set(msg)
        self._status_lbl.config(fg=_FG2 if ok else "#ff6b6b")

    # ── Actions boutons ──────────────────────────────────────────
    def _on_select(self, event=None):
        """Pré-remplit le formulaire avec le provider sélectionné."""
        sel = self._listbox.curselection()
        if not sel:
            return
        code = self._listbox.get(sel[0])
        url  = self._read_url_from_lay(code)
        self._name_var.set(code)
        self._set_url_entry(url)
        self._status_var.set("")

    def _save(self):
        """Crée un nouveau provider (nom non existant) ou confirme la sauvegarde."""
        code = self._name_var.get().strip()
        url  = self._get_url_from_entry()
        ok, msg = self._validate_inputs(code, url)
        if not ok:
            self._set_status(msg, ok=False)
            return
        self._write_lay(code, url)
        self._refresh_list()
        self.parent_gui.after(0, self._apply_and_select, code)
        self._set_status(tr("personal_provider_saved_ok"), ok=True)

    def _modify(self):
        """Modifie le provider sélectionné dans la liste (url ou nom = identique)."""
        sel = self._listbox.curselection()
        if not sel:
            self._set_status(tr("personal_provider_select_hint"), ok=False)
            return
        old_code = self._listbox.get(sel[0])
        new_code = self._name_var.get().strip()
        url = self._get_url_from_entry()
        ok, msg = self._validate_inputs(new_code, url)
        if not ok:
            self._set_status(msg, ok=False)
            return
        # Supprimer l'ancien fichier si le code a changé
        if old_code != new_code:
            try:
                os.remove(self._lay_path(old_code))
            except Exception:
                pass
        self._write_lay(new_code, url)
        self._refresh_list()
        self.parent_gui.after(0, self._apply_and_select, new_code)
        self._set_status(tr("personal_provider_saved_ok"), ok=True)

    def _delete(self):
        """Supprime le provider sélectionné dans la liste."""
        sel = self._listbox.curselection()
        if not sel:
            self._set_status(tr("personal_provider_select_hint"), ok=False)
            return
        code = self._listbox.get(sel[0])
        try:
            os.remove(self._lay_path(code))
        except Exception:
            pass
        self._name_var.set("")
        self._set_url_entry("")
        self._refresh_list()
        self.parent_gui.after(0, self._apply_reload_only)
        self._set_status(tr("personal_provider_deleted_ok"), ok=True)

    def _apply_and_select(self, code):
        """Recharge les providers et sélectionne le nouveau code dans img_combo."""
        self.parent_gui._reload_personal_providers()
        # Sélectionne le provider dans le combobox principal
        current = self.parent_gui.default_website.get()
        if code in self.parent_gui._full_map_list:
            # Bloque temporairement _on_imagery_change pour éviter la boucle
            self.parent_gui.default_website.set(code)
        # Sinon on laisse l'ancienne sélection

    def _apply_reload_only(self):
        """Recharge uniquement la liste sans changer la sélection courante."""
        current = self.parent_gui.default_website.get()
        self.parent_gui._reload_personal_providers()
        # Rétablit la sélection si elle existe encore
        if current in self.parent_gui._full_map_list:
            self.parent_gui.default_website.set(current)
        elif self.parent_gui._full_map_list:
            self.parent_gui.default_website.set(
                self.parent_gui._full_map_list[0])

    def _on_close(self):
        """Ferme la fenêtre et restaure une sélection valide dans img_combo."""
        current = self.parent_gui.default_website.get()
        # Si "Personnel" est encore sélectionné, revenir au dernier provider réel
        if current == tr("Personnel"):
            lst = [x for x in self.parent_gui._full_map_list
                   if x != tr("Personnel")]
            if lst:
                self.parent_gui.default_website.set(lst[0])
        self.destroy()


class Ortho4XP_Custom_ZL(tk.Toplevel):

    dico_color = {
        15: "#4a9e8e",   # bleu-vert Roland foncé
        16: "#5ab88a",   # vert Roland moyen
        17: "#7eca7e",   # vert Roland
        18: "#a6d96a",   # vert Roland clair
        19: "#c8e65a",   # vert-jaune Roland très clair
    }
    zl_list = ["10", "11", "12", "13"]
    points = []
    coords = []
    polygon_list = []
    polyobj_list = []

    def __init__(self, parent, lat, lon):
        _reload_theme()
        self.parent = parent
        self.lat = lat
        self.lon = lon
        def _in_gui(p):
            if isinstance(p, dict): return p.get("in_GUI", True)
            return getattr(p, "in_GUI", True)
        self.map_list = sorted(
            [
                provider_code
                for provider_code in set(IMG.providers_dict)
                if _in_gui(IMG.providers_dict[provider_code])
            ]
            + sorted(set(IMG.combined_providers_dict))
        )
        self.map_list = [
            provider_code
            for provider_code in self.map_list
            if provider_code != "SEA"
        ]
        self.reduced_map_list = [
            provider_code
            for provider_code in self.map_list
            if provider_code != "OSM"
        ]
        self.points = []
        self.coords = []
        self.polygon_list = []
        self.polyobj_list = []

        # Init valeurs par défaut — seront recalculées à chaque preview_tile
        self.xmin = 0
        self.ymin = 0
        self.xmax = 256
        self.ymax = 256
        self.zoomlevel = 11
        self.poly_curr = None

        tk.Toplevel.__init__(self)
        self.configure(bg=_BG)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.title(tr("Preview / Custom zoomlevels"))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Constants

        self.map_choice = tk.StringVar()
        self.map_choice.set("OSM")
        self.zl_choice = tk.StringVar()
        self.zl_choice.set("11")
        self.progress_preview = tk.IntVar()
        self.progress_preview.set(0)
        self.zmap_choice = tk.StringVar()
        self.zmap_choice.set(self.parent.default_website.get())

        self.zlpol = tk.IntVar()
        try:  # default_zl might still be empty
            self.zlpol.set(
                max(min(int(self.parent.default_zl.get()) + 1, 19), 15)
            )
        except:
            self.zlpol.set(17)
        # Memoire du ZL de la zone actuellement en cours de trace. Sert a
        # l'auto-sauvegarde : quand l'utilisateur clique un NOUVEAU bouton ZL
        # alors qu'une zone est en cours, on sauve cette zone avec SON ZL
        # d'origine avant de passer au suivant (voir on_zl_change).
        self._prev_zlpol = self.zlpol.get()
        self.gb = tk.StringVar()
        self.gb.set("0Gb")

        # Frames
        self.frame_left = tk.Frame(
            self, border=4, relief=RIDGE, bg=_BG
        )
        self.frame_left.grid(row=0, column=0, sticky=N + S + W + E)

        self.frame_right = tk.Frame(
            self, border=4, relief=RIDGE, bg=_BG
        )
        self.frame_right.grid(row=0, column=1, sticky=N + S + W + E)
        self.frame_right.rowconfigure(0, weight=1)
        self.frame_right.columnconfigure(0, weight=1)

        # Widgets
        row = 0
        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Preview params "),
            fg=_FG2,
            bg=_BG,
            font="Helvetica 16 bold italic",
        ).grid(row=row, column=0, sticky=W + E)
        row += 1

        tk.Label(
            self.frame_left, anchor=W, text=tr("Source : "), bg=_BG, fg=_FG)
        self.map_combo = ttk.Combobox(
            self.frame_left,
            textvariable=self.map_choice,
            values=self.map_list,
            width=40,
            state="readonly",
        )
        self.map_combo.grid(row=row, column=0, padx=5, pady=3, sticky=E)
        row += 1

        tk.Label(
            self.frame_left, anchor=W, text=tr("Zoomlevel : "), bg=_BG, fg=_FG)
        self.zl_combo = ttk.Combobox(
            self.frame_left,
            textvariable=self.zl_choice,
            values=self.zl_list,
            width=3,
            state="readonly",
        )
        self.zl_combo.grid(row=2, column=0, padx=5, pady=3, sticky=E)
        row += 1

        _ctk_button(
            self.frame_left,
            text=tr("Preview"),
            command=lambda: self.preview_tile(lat, lon),
        ).grid(row=row, padx=5, column=0, sticky=N + S + E + W)
        row += 1
        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Zone params "),
            fg=_FG2,
            bg=_BG,
            font="Helvetica 16 bold italic",
        ).grid(row=row, column=0, pady=10, sticky=W + E)
        row += 1

        tk.Label(
            self.frame_left, anchor=W, text=tr("Source : "), bg=_BG, fg=_FG)
        self.zmap_combo = ttk.Combobox(
            self.frame_left,
            textvariable=self.zmap_choice,
            values=self.reduced_map_list,
            width=40,
            state="readonly",
        )
        self.zmap_combo.grid(row=row, column=0, padx=5, pady=10, sticky=E)
        row += 1

        self.frame_zlbtn = tk.Frame(self.frame_left, border=0, bg=_BG)
        for i in range(5):
            self.frame_zlbtn.columnconfigure(i, weight=1)
        self.frame_zlbtn.grid(
            row=row, column=0, columnspan=1, sticky=N + S + W + E
        )
        row += 1
        for zl in range(15, 20):
            col = zl - 15
            tk.Radiobutton(
                self.frame_zlbtn,
                bd=2,
                bg=self.dico_color[zl],
                activebackground=self.dico_color[zl],
                selectcolor=self.dico_color[zl],
                fg="#ffffff",
                activeforeground="#ffffff",
                font=("Arial", 11, "bold"),
                relief="flat",
                height=2,
                indicatoron=0,
                text="ZL" + str(zl),
                variable=self.zlpol,
                value=zl,
                command=self.on_zl_change,
            ).grid(row=0, column=col, padx=1, pady=1, sticky=N + S + E + W)

        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Approx. Add. Size : "),
            bg=_BG, fg=_FG).grid(row=row, column=0, padx=5, pady=10, sticky=W)
        tk.Entry(
            self.frame_left,
            width=7,
            justify=RIGHT,
            bg=_BG,
            fg=_FG2,
            textvariable=self.gb,
        ).grid(row=row, column=0, padx=5, pady=10, sticky=E)
        row += 1

        _ctk_button(
            self.frame_left, text=tr("  Save zone  "), command=self.save_zone_cmd
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left, text=tr("Delete ZL zone"), command=self.delete_zone_cmd
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left,
            text=tr("Make GeoTiffs"),
            command=self.build_geotiffs_ifc,
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left, text=tr("Extract Mesh "), command=self.extract_mesh_ifc
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        tk.Label(
            self.frame_left,
            text=(
                tr('── Navigation ──\nClic + glisser\n   Déplacer la carte\nMolette\n   Zoom avant / arrière\n\n── Tracer une zone ──\nShift + clic\n   Ajouter un point\nCtrl+Shift + clic\n   Point aligné grille\n Sauvegarder la zone\nBackspace  Annuler dernier pt\n\n── Rectangle ZL ──\nCtrl + clic (vide)\n   Créer rectangle\nCtrl + clic (zone)\n   Supprimer rectangle\nd  Supprimer dernière zone')
            ),
            bg=_BG, fg=_FG2,
            justify=LEFT,
            font=("Helvetica", 10),
        ).grid(row=row, column=0, padx=5, pady=10, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left, text=tr("    Apply    "), command=self.save_zone_list
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left, text=tr("    Reset    "), command=self.delAll
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        _ctk_button(
            self.frame_left, text=tr("    Exit     "), command=self.destroy
        ).grid(row=row, column=0, padx=5, pady=3, sticky=N + S + E + W)
        row += 1
        self.canvas = tk.Canvas(self.frame_right, bd=0, height=750, width=750)
        self.canvas.grid(row=0, column=0, sticky=N + S + E + W)
        # Taille minimale = taille naturelle du contenu une fois l'UI construite.
        # Les boutons (Apply / Reset / Exit) restent toujours visibles même si
        # la fenêtre est réduite ; l'agrandissement reste libre.
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def preview_tile(self, lat, lon):
        # Recharger les zones depuis le .cfg de la tuile
        try:
            _tile = CFG.Tile(lat, lon,
                             self.parent.custom_build_dir.get()
                             if hasattr(self.parent, "custom_build_dir") else "")
            _tile.read_from_config()
            CFG.zone_list = _tile.zone_list
        except Exception:
            pass
        self.zoomlevel = int(self.zl_combo.get())
        zoomlevel = self.zoomlevel
        provider_code = self.map_combo.get()
        (tilxleft, tilytop) = GEO.wgs84_to_gtile(lat + 1, lon, zoomlevel)
        (self.latmax, self.lonmin) = GEO.gtile_to_wgs84(
            tilxleft, tilytop, zoomlevel
        )
        (self.xmin, self.ymin) = GEO.wgs84_to_pix(
            self.latmax, self.lonmin, zoomlevel
        )
        (tilxright, tilybot) = GEO.wgs84_to_gtile(lat, lon + 1, zoomlevel)
        (self.latmin, self.lonmax) = GEO.gtile_to_wgs84(
            tilxright + 1, tilybot + 1, zoomlevel
        )
        (self.xmax, self.ymax) = GEO.wgs84_to_pix(
            self.latmin, self.lonmax, zoomlevel
        )
        filepreview = FNAMES.preview(lat, lon, zoomlevel, provider_code)
        if os.path.isfile(filepreview) != True:
            fargs_ctp = [lat, lon, zoomlevel, provider_code]
            self.ctp_thread = threading.Thread(
                target=IMG.create_tile_preview, args=fargs_ctp
            )
            self.ctp_thread.start()
            fargs_dispp = [filepreview, lat, lon]
            dispp_thread = threading.Thread(
                target=self.show_tile_preview, args=fargs_dispp
            )
            dispp_thread.start()
        else:
            # Fond de carte en cache : lancer show_tile_preview en thread
            # pour que tag_raise() des aéroports OACI fonctionne correctement
            threading.Thread(
                target=self.show_tile_preview,
                args=(filepreview, lat, lon),
                daemon=True
            ).start()
        return

    def show_tile_preview(self, filepreview, lat, lon):
        for item in self.polyobj_list:
            try:
                self.canvas.delete(item)
            except:
                pass
        try:
            self.canvas.delete(self.img_map)
        except:
            pass
        try:
            self.canvas.delete(self.boundary)
        except:
            pass
        try:
            self.ctp_thread.join()
        except:
            pass
        # Attendre que le fichier existe (max 30s)
        import time
        for _ in range(60):
            if os.path.isfile(filepreview):
                break
            time.sleep(0.5)
        if not os.path.isfile(filepreview):
            UI.vprint(0, tr("Preview non générée :"), filepreview)
            return
        self.image = Image.open(filepreview)
        self._image_orig = self.image.copy()
        self._zoom_scale = 1.0
        self.photo = ImageTk.PhotoImage(self.image)
        self.map_x_res = self.photo.width()
        self.map_y_res = self.photo.height()
        self.img_map = self.canvas.create_image(
            0, 0, anchor=NW, image=self.photo
        )
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))
        if "dar" in sys.platform:
            self.canvas.bind("<ButtonPress-2>", self.scroll_start)
            self.canvas.bind("<B2-Motion>", self.scroll_move)
            self.canvas.bind("<Control-ButtonPress-2>", self.delPol)
        else:
            self.canvas.bind("<ButtonPress-3>", self.scroll_start)
            self.canvas.bind("<B3-Motion>", self.scroll_move)
            self.canvas.bind("<Control-ButtonPress-3>", self.delPol)
        self.canvas.bind("<ButtonPress-1>",   self._on_left_press)
        self.canvas.bind("<B1-Motion>",        self._on_left_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_left_release)
        self.canvas.bind("<Motion>",           self._on_hover)
        # Etat pour l'edition d'un sommet (attraper / deplacer un point de la
        # zone EN COURS de trace). Reinitialise a chaque preview.
        self._drag_pt_idx = None
        self._hover_idx   = None
        self._hover_obj   = None
        self.canvas.bind("<Shift-ButtonPress-1>",         self.newPoint)
        self.canvas.bind("<Control-Shift-ButtonPress-1>", self.newPointGrid)
        self.canvas.bind("<Control-ButtonPress-1>",       self._ctrl_click)
        self.canvas.focus_set()
        self.canvas.bind("p", self.newPoint)
        self.canvas.bind("d", self.delete_zone_cmd)
        self.canvas.bind("n", self.save_zone_cmd)
        self.canvas.bind("<BackSpace>", self.delLast)
        # Zoom molette — multi-OS
        self.canvas.bind("<MouseWheel>",  self._zoom)
        self.canvas.bind("<Button-4>",    self._zoom)
        self.canvas.bind("<Button-5>",    self._zoom)
        self._preview_lat = lat
        self._preview_lon = lon
        if not hasattr(self, 'polygon_list') or not self.polygon_list:
            self.polygon_list = []
            self.polyobj_list = []
        self.poly_curr = []
        bdpoints = []
        for [latp, lonp] in [
            [lat, lon],
            [lat, lon + 1],
            [lat + 1, lon + 1],
            [lat + 1, lon],
        ]:
            [x, y] = self.latlon_to_xy(latp, lonp, self.zoomlevel)
            bdpoints += [int(x), int(y)]
        self.boundary = self.canvas.create_polygon(
            bdpoints, outline="black", fill="", width=2
        )
        for zone in CFG.zone_list:
            self.coords = zone[0][0:-2]
            self.zlpol.set(zone[1])
            self.zmap_combo.set(zone[2])
            self.points = []
            for idxll in range(0, len(self.coords) // 2):
                latp = self.coords[2 * idxll]
                lonp = self.coords[2 * idxll + 1]
                [x, y] = self.latlon_to_xy(latp, lonp, self.zoomlevel)
                self.points += [int(x), int(y)]
            self.redraw_poly()
            self.save_zone_cmd()
        # ── Overlay aeroports via Overpass ────────────────────────────────
        self._airports_pending = []
        self._airports_drawn   = False
        self._airports_retry   = 0
        threading.Thread(
            target=self._fetch_airports_overpass,
            args=(lat, lon),
            daemon=True
        ).start()
        self.canvas.after(500, self._draw_airports_when_ready)
        # ──────────────────────────────────────────────────────────────────
        return

    def _fetch_airports_overpass(self, lat, lon):
        import urllib.request, json
        q = (
            "[out:json][timeout:25];("
            + 'node["aeroway"="aerodrome"](%d,%d,%d,%d);' % (lat, lon, lat+1, lon+1)
            + 'way["aeroway"="aerodrome"](%d,%d,%d,%d);'  % (lat, lon, lat+1, lon+1)
            + 'rel["aeroway"="aerodrome"](%d,%d,%d,%d);'  % (lat, lon, lat+1, lon+1)
            + ");out center;"
        )
        servers = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        ]
        data = None
        for server in servers:
            try:
                req = urllib.request.Request(
                    server,
                    data=q.encode("utf-8"),
                    headers={"User-Agent": "Ortho4XP/2.0 airport-preview"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                break
            except Exception:
                continue
        if not data:
            print(tr("[OACI] Serveurs Overpass indisponibles — cercles aéroports non affichés."))
            return
        result = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            if el["type"] == "node":
                alat, alon = el["lat"], el["lon"]
            else:
                c = el.get("center", {})
                if not c:
                    continue
                alat, alon = c["lat"], c["lon"]
            icao  = tags.get("icao") or tags.get("iata") or tags.get("ref") or ""
            name  = tags.get("name", "")
            label = icao if icao else (name[:14] if name else "APT")
            result.append((alat, alon, label))
        self._airports_pending = result

    def _draw_airports_when_ready(self):
        """Appelé depuis canvas.after() → thread principal tkinter.
        Attend que les données Overpass soient disponibles puis dessine.
        Sécurisé même si show_tile_preview tourne dans un thread secondaire.
        """
        if self._airports_drawn:
            return
        if not self._airports_pending:
            self._airports_retry += 1
            if self._airports_retry < 120:  # 60s max (120 × 500ms)
                self.canvas.after(500, self._draw_airports_when_ready)
            return
        self._airports_drawn = True
        new_items = []
        for (alat, alon, label) in self._airports_pending:
            try:
                px, py = self.latlon_to_xy(alat, alon, self.zoomlevel)
                r = 13
                new_items.append(self.canvas.create_oval(
                    px-r, py-r, px+r, py+r,
                    outline="#FFD700", fill="#333333", width=2))
                new_items.append(self.canvas.create_text(
                    px, py, text="✈",
                    fill="#FFD700", font=("Arial", 11, "bold"), anchor="center"))
                new_items.append(self.canvas.create_text(
                    px+1, py+r+4, text=label,
                    fill="#000000", font=("Arial", 8, "bold"), anchor="n"))
                new_items.append(self.canvas.create_text(
                    px, py+r+3, text=label,
                    fill="#FFD700", font=("Arial", 8, "bold"), anchor="n"))
            except Exception as e:
                print(f"Draw error {label}: {e}")
                continue
        # tag_raise via after(0) pour thread-safety tkinter
        def _raise_all():
            for item in new_items:
                try:
                    self.canvas.tag_raise(item)
                except Exception:
                    pass
        self.canvas.after(0, _raise_all)
        self.polyobj_list += new_items

    def scroll_start(self, event):
        self.canvas.focus_set()
        self.canvas.scan_mark(event.x, event.y)
        return

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        return

    def on_zl_change(self):
        """Appelee quand l'utilisateur clique un bouton ZL.

        Si une zone est en cours de trace (au moins 3 points poses mais pas
        encore sauvegardee) ET que le ZL choisi est different du precedent,
        on sauvegarde AUTOMATIQUEMENT la zone en cours avec son ZL d'origine
        avant de passer au nouveau ZL. Cela evite que les points de la zone
        suivante se rattachent a la precedente (zones reliees par un trait).

        Le workflow "anneaux" devient : tracer l'anneau -> cliquer le ZL
        suivant (la zone precedente se range toute seule) -> tracer le
        suivant, etc.
        """
        new_zl = self.zlpol.get()
        prev_zl = getattr(self, "_prev_zlpol", None)
        # len(self.points) est en nombre de valeurs (2 par point) : >= 6 = au
        # moins 3 points = un polygone valide (meme critere que save_zone_cmd).
        if len(self.points) >= 6 and prev_zl is not None and new_zl != prev_zl:
            # On sauve la zone en cours avec SON ZL (prev_zl), pas le nouveau.
            self.zlpol.set(prev_zl)
            self.save_zone_cmd()        # remet points/coords a zero
            self.zlpol.set(new_zl)      # retablit la selection utilisateur
        self._prev_zlpol = new_zl
        self.redraw_poly()

    def redraw_poly(self):
        try:
            self.canvas.delete(self.poly_curr)
        except:
            pass
        try:
            color = self.dico_color[self.zlpol.get()]
            if len(self.points) >= 4:
                self.poly_curr = self.canvas.create_polygon(
                    self.points, outline="#742374", fill="", width=2
                )
            else:
                self.poly_curr = self.canvas.create_polygon(
                    self.points, outline=color, fill="", width=5
                )
        except:
            pass
        return

    def _find_near_point(self, event, threshold=12):
        """Index (numero de sommet) du point de la zone EN COURS le plus proche
        du curseur si distance <= threshold px, sinon None. Ne concerne QUE la
        zone en cours de trace (self.points), pas les zones deja sauvegardees."""
        if not self.points:
            return None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        best_idx = None
        best_d2 = float(threshold * threshold)
        for i in range(len(self.points) // 2):
            dx = self.points[2 * i] - x
            dy = self.points[2 * i + 1] - y
            d2 = dx * dx + dy * dy
            if d2 <= best_d2:
                best_d2 = d2
                best_idx = i
        return best_idx

    def _draw_hover_marker(self, idx):
        """Affiche (ou retire) le petit rond de surbrillance sur le point
        survole, pour montrer qu'il est attrapable."""
        try:
            if self._hover_obj is not None:
                self.canvas.delete(self._hover_obj)
        except Exception:
            pass
        self._hover_obj = None
        if idx is None or not self.points:
            return
        try:
            x = self.points[2 * idx]
            y = self.points[2 * idx + 1]
            r = 6
            self._hover_obj = self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                outline="#742374", fill="#c8e65a", width=2
            )
        except Exception:
            self._hover_obj = None

    def _on_hover(self, event):
        """Souris sans bouton : surligne le point survole s'il est assez proche,
        pour indiquer qu'on peut l'attraper."""
        if getattr(self, "_drag_pt_idx", None) is not None:
            return
        idx = self._find_near_point(event)
        if idx == getattr(self, "_hover_idx", None):
            return
        self._hover_idx = idx
        self._draw_hover_marker(idx)

    def _on_left_press(self, event):
        """Bouton gauche enfonce. Si un point de la zone en cours est juste sous
        le curseur -> on l'attrape (edition). Sinon -> deplacement de la carte
        (comportement historique). Les clics Shift/Ctrl gardent leurs propres
        liaisons (ajout de point / rectangle)."""
        if event.state & 0x1 or event.state & 0x4:
            return
        idx = self._find_near_point(event)
        if idx is not None:
            self._drag_pt_idx = idx
            return
        self._drag_pt_idx = None
        self.scroll_start(event)

    def _on_left_drag(self, event):
        """Glisser bouton gauche. Point attrape -> on le deplace ; sinon ->
        deplacement de la carte (comportement historique)."""
        if event.state & 0x1 or event.state & 0x4:
            return
        if getattr(self, "_drag_pt_idx", None) is not None:
            self._move_point(self._drag_pt_idx, event)
            return
        self.scroll_move(event)

    def _on_left_release(self, event):
        """Relacher bouton gauche : on lache le point eventuellement attrape."""
        self._drag_pt_idx = None

    def _move_point(self, idx, event):
        """Deplace le sommet idx de la zone en cours vers le curseur. Met a jour
        la coordonnee geographique (coords) ET le point ecran (points) de facon
        coherente, comme newPointGrid / _redraw_all."""
        if idx is None or 2 * idx + 1 >= len(self.points):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        [latp, lonp] = self.xy_to_latlon(x, y, self.zoomlevel)
        self.coords[2 * idx] = latp
        self.coords[2 * idx + 1] = lonp
        [px, py] = self.latlon_to_xy(latp, lonp, self.zoomlevel)
        self.points[2 * idx] = int(px)
        self.points[2 * idx + 1] = int(py)
        self.redraw_poly()
        self._draw_hover_marker(idx)

    def newPoint(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.points += [x, y]
        [latp, lonp] = self.xy_to_latlon(x, y, self.zoomlevel)
        self.coords += [latp, lonp]
        self.redraw_poly()
        return

    def newPointGrid(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        [latp, lonp] = self.xy_to_latlon(x, y, self.zoomlevel)
        [a, b] = GEO.wgs84_to_orthogrid(latp, lonp, self.zlpol.get())
        [aa, bb] = GEO.wgs84_to_gtile(latp, lonp, self.zlpol.get())
        a = a + 16 if aa - a >= 8 else a
        b = b + 16 if bb - b >= 8 else b
        [latp, lonp] = GEO.gtile_to_wgs84(a, b, self.zlpol.get())
        self.coords += [latp, lonp]
        [x, y] = self.latlon_to_xy(latp, lonp, self.zoomlevel)
        self.points += [int(x), int(y)]
        self.redraw_poly()
        return

    def newPol(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        [latp, lonp] = self.xy_to_latlon(x, y, self.zoomlevel)
        [a, b] = GEO.wgs84_to_orthogrid(latp, lonp, self.zlpol.get())
        [latmax, lonmin] = GEO.gtile_to_wgs84(a, b, self.zlpol.get())
        [latmin, lonmax] = GEO.gtile_to_wgs84(a + 16, b + 16, self.zlpol.get())
        self.coords = [
            latmin,
            lonmin,
            latmin,
            lonmax,
            latmax,
            lonmax,
            latmax,
            lonmin,
        ]
        self.points = []
        for i in range(4):
            [x, y] = self.latlon_to_xy(
                self.coords[2 * i], self.coords[2 * i + 1], self.zoomlevel
            )
            self.points += [int(x), int(y)]
        self.redraw_poly()
        self.save_zone_cmd()
        return

    def _zoom(self, event):
        """Zoom molette progressif centré sur le curseur — multi-OS.
        Facteur 1.25 par cran (doux). ZL logique min=10, max=14.
        Le point sous le curseur reste fixe après le zoom."""
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            factor = 1.25
        else:
            factor = 1.0 / 1.25
        if not hasattr(self, 'image') or self.image is None:
            return
        # Limiter le zoom total via _zoom_scale
        if not hasattr(self, '_zoom_scale'):
            self._zoom_scale = 1.0
        new_scale = self._zoom_scale * factor
        # Limite : 0.25x (zoom arrière max) à 8x (zoom avant max)
        if new_scale < 0.25 or new_scale > 8.0:
            return
        self._zoom_scale = new_scale
        # Position du curseur dans le canvas (avant zoom)
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        # Nouvelle taille image
        orig = getattr(self, '_image_orig', None)
        if orig is None:
            self._image_orig = self.image.copy()
            orig = self._image_orig
        new_w = max(1, int(orig.width  * self._zoom_scale))
        new_h = max(1, int(orig.height * self._zoom_scale))
        self.image = orig.resize((new_w, new_h), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)
        self.map_x_res = new_w
        self.map_y_res = new_h
        # Recalculer coordonnées géo au zoomlevel logique
        lat = getattr(self, '_preview_lat', None)
        lon = getattr(self, '_preview_lon', None)
        if lat is not None:
            zl = self.zoomlevel
            (tilxleft, tilytop) = GEO.wgs84_to_gtile(lat + 1, lon, zl)
            (self.latmax, self.lonmin) = GEO.gtile_to_wgs84(tilxleft, tilytop, zl)
            (self.xmin, self.ymin) = GEO.wgs84_to_pix(self.latmax, self.lonmin, zl)
            (tilxright, tilybot) = GEO.wgs84_to_gtile(lat, lon + 1, zl)
            (self.latmin, self.lonmax) = GEO.gtile_to_wgs84(tilxright+1, tilybot+1, zl)
            (self.xmax, self.ymax) = GEO.wgs84_to_pix(self.latmin, self.lonmax, zl)
        # Mettre à jour l'image dans le canvas
        self.canvas.itemconfig(self.img_map, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))
        # Recentrer sur le curseur : déplacer la vue pour que cx/cy reste fixe
        self.canvas.xview_moveto((cx * factor - event.x) / new_w)
        self.canvas.yview_moveto((cy * factor - event.y) / new_h)
        # Redessiner zones et bordures
        self._redraw_all(lat, lon)

    def _redraw_all(self, lat, lon):
        """Redessine les bordures et zones après un zoom."""
        if lat is None or lon is None:
            return
        # Supprimer ancienne bordure
        try:
            self.canvas.delete(self.boundary)
        except:
            pass
        # Redessiner bordure
        bdpoints = []
        for [latp, lonp] in [[lat, lon],[lat, lon+1],[lat+1, lon+1],[lat+1, lon]]:
            [x, y] = self.latlon_to_xy(latp, lonp, self.zoomlevel)
            bdpoints += [int(x), int(y)]
        self.boundary = self.canvas.create_polygon(
            bdpoints, outline="black", fill="", width=2)
        # Redessiner les zones sauvegardées
        old_poly_list = list(self.polygon_list)
        old_points_list = [p[0] for p in old_poly_list]
        old_coords_list = [p[1] for p in old_poly_list]
        old_zl_list     = [p[2] for p in old_poly_list]
        old_src_list    = [p[3] for p in old_poly_list]
        for obj in self.polyobj_list:
            try: self.canvas.delete(obj)
            except: pass
        self.polygon_list = []
        self.polyobj_list = []
        for coords, zl, src in zip(old_coords_list, old_zl_list, old_src_list):
            self.coords = list(coords)
            self.points = []
            self.zlpol.set(zl)
            self.zmap_combo.set(src)
            for i in range(len(coords) // 2):
                [x, y] = self.latlon_to_xy(coords[2*i], coords[2*i+1], self.zoomlevel)
                self.points += [int(x), int(y)]
            self.redraw_poly()
            self.save_zone_cmd()
        self.points = []
        self.coords = []

    def _ctrl_click(self, event):
        """Ctrl+clic gauche : supprime la zone si le clic est dedans, sinon crée un rectangle."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for poly in self.polygon_list:
            closed = poly[0] + poly[0][0:2]
            if VECT.point_in_polygon([x, y], closed):
                self.delPol(event)
                return
        self.newPol(event)

    def delPol(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        copy = self.polygon_list[:]
        for poly in copy:
            if poly[2] != self.zlpol.get():
                continue
            # point_in_polygon exige polygone fermé (dernier point = premier)
            closed = poly[0] + poly[0][0:2]
            if VECT.point_in_polygon([x, y], closed):
                idx = self.polygon_list.index(poly)
                self.polygon_list.pop(idx)
                self.canvas.delete(self.polyobj_list[idx])
                self.polyobj_list.pop(idx)
                self.compute_size()
                return
        return

    def delAll(self):
        copy = self.polygon_list[:]
        for poly in copy:
            idx = self.polygon_list.index(poly)
            self.polygon_list.pop(idx)
            self.canvas.delete(self.polyobj_list[idx])
            self.polyobj_list.pop(idx)
        try:
            self.canvas.delete(self.poly_curr)
        except:
            pass
        self.compute_size()
        return

    def xy_to_latlon(self, x, y, zoomlevel):
        # Corriger les coords canvas par le facteur de zoom PIL
        scale = getattr(self, '_zoom_scale', 1.0)
        pix_x = x / scale + self.xmin
        pix_y = y / scale + self.ymin
        return GEO.pix_to_wgs84(pix_x, pix_y, zoomlevel)

    def latlon_to_xy(self, lat, lon, zoomlevel):
        scale = getattr(self, '_zoom_scale', 1.0)
        [pix_x, pix_y] = GEO.wgs84_to_pix(lat, lon, zoomlevel)
        return [(pix_x - self.xmin) * scale, (pix_y - self.ymin) * scale]

    def delLast(self, event):
        self.points = self.points[0:-2]
        self.coords = self.coords[0:-2]
        self.redraw_poly()
        return

    def compute_size(self):
        total_size = 0
        for polygon in self.polygon_list:
            polyp = polygon[0] + polygon[0][0:2]
            area = 0
            x1 = polyp[0]
            y1 = polyp[1]
            for j in range(1, len(polyp) // 2):
                x2 = polyp[2 * j]
                y2 = polyp[2 * j + 1]
                area += (x2 - x1) * (y2 + y1)
                x1 = x2
                y1 = y2
            total_size += (
                abs(area)
                / 2
                * (
                    (
                        40000
                        * cos(pi / 180 * polygon[1][0])
                        / 2 ** (int(self.zl_combo.get()) + 8)
                    )
                    ** 2
                )
                * 2 ** (2 * (int(polygon[2]) - 17))
                / 1024
            )
        self.gb.set("{:.1f}".format(total_size) + "Gb")
        return

    def save_zone_cmd(self):
        if len(self.points) < 6:
            return
        self.polyobj_list.append(self.poly_curr)
        self.polygon_list.append(
            [self.points, self.coords, self.zlpol.get(), self.zmap_combo.get()]
        )
        self.compute_size()
        self.poly_curr = []
        self.points = []
        self.coords = []
        return

    def build_geotiffs_ifc(self):
        texture_attributes_list = []
        fake_zone_list = []
        for polygon in self.polygon_list:
            lat_bar = (polygon[1][0] + polygon[1][4]) / 2
            lon_bar = (polygon[1][1] + polygon[1][3]) / 2
            zoomlevel = int(polygon[2])
            provider_code = polygon[3]
            til_x_left, til_y_top = GEO.wgs84_to_orthogrid(
                lat_bar, lon_bar, zoomlevel
            )
            texture_attributes_list.append(
                (til_x_left, til_y_top, zoomlevel, provider_code)
            )
            fake_zone_list.append(("", "", provider_code))
        UI.vprint(1, "\nBuilding geotiffs.\n------------------\n")
        tile = CFG.Tile(self.lat, self.lon, "")
        tile.zone_list = fake_zone_list
        IMG.initialize_local_combined_providers_dict(tile)
        fargs_build_geotiffs = [tile, texture_attributes_list]
        build_geotiffs_thread = threading.Thread(
            target=IMG.build_geotiffs, args=fargs_build_geotiffs
        )
        build_geotiffs_thread.start()
        return

    def extract_mesh_ifc(self):
        polygon = self.polygon_list[0]
        lat_bar = (polygon[1][0] + polygon[1][4]) / 2
        lon_bar = (polygon[1][1] + polygon[1][3]) / 2
        zoomlevel = int(polygon[2])
        provider_code = polygon[3]
        til_x_left, til_y_top = GEO.wgs84_to_orthogrid(
            lat_bar, lon_bar, zoomlevel
        )
        build_dir = FNAMES.build_dir(
            self.lat, self.lon, self.parent.custom_build_dir.get()
        )
        mesh_file = FNAMES.mesh_file(build_dir, self.lat, self.lon)
        UI.vprint(
            1,
            "Extracting part of ",
            mesh_file,
            "to",
            FNAMES.obj_file(til_x_left, til_y_top, zoomlevel, provider_code),
            "(Wavefront)",
        )
        fargs_extract_mesh = [
            mesh_file,
            til_x_left,
            til_y_top,
            zoomlevel,
            provider_code,
        ]
        extract_mesh_thread = threading.Thread(
            target=MESH.extract_mesh_to_obj, args=fargs_extract_mesh
        )
        extract_mesh_thread.start()
        return

    def delete_zone_cmd(self, event=None):
        try:
            if not self.polygon_list:
                return
            self.canvas.delete(self.polyobj_list[-1])
            self.polygon_list.pop(-1)
            self.polyobj_list.pop(-1)
            try:
                self.canvas.delete(self.poly_curr)
            except:
                pass
            self.poly_curr = None
            self.points = []
            self.coords = []
            self.compute_size()
        except:
            self.points = []
            self.coords = []
        return

    def save_zone_list(self):
        ordered_list = sorted(
            self.polygon_list, key=lambda item: item[2], reverse=True
        )
        zone_list = []
        for item in ordered_list:
            tmp = []
            for pt in item[1]:
                tmp.append(pt)
            for pt in item[1][
                0:2
            ]:  # repeat first point for point_in_polygon algo
                tmp.append(pt)
            zone_list.append([tmp, item[2], item[3]])
        CFG.zone_list = zone_list
        # Sauvegarde dans le fichier .cfg de la tuile
        # → les zones sont rechargées au prochain démarrage
        # → makedirs garantit que le dossier existe même avant le premier build
        try:
            tile = CFG.Tile(self.lat, self.lon,
                            self.parent.custom_build_dir.get()
                            if hasattr(self.parent, "custom_build_dir") else "")
            tile.zone_list = zone_list
            # Créer le dossier build_dir si nécessaire avant d'écrire le cfg
            import os as _os
            _os.makedirs(tile.build_dir, exist_ok=True)
            tile.write_to_config()
            UI.vprint(1, tr("Zones sauvegardées dans cfg tuile ") + f"{self.lat},{self.lon}")
        except Exception as e:
            UI.vprint(0, tr("Avertissement save_zone_list: ") + str(e))
        return

################################################################################
class Ortho4XP_Earth_Preview(tk.Toplevel):

    earthzl = 6
    resolution = 2 ** earthzl * 256

    list_del_ckbtn = [
        "OSM data",
        "Mask data",
        "Jpeg imagery",
        "Tile (whole)",
        "Tile (textures)",
    ]
    list_do_ckbtn = [
        "Assemble vector data",
        "Triangulate 3D mesh",
        "Draw water masks",
        "Build imagery/DSF",
        "Extract overlays",
        "Read per tile cfg",
    ]

    canvas_min_x = 900
    canvas_min_y = 700

    def __init__(self, parent, lat, lon):
        tk.Toplevel.__init__(self)
        self.configure(bg=_BG)
        self.title(tr("Tiles collection and management"))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Parent derived data
        self.parent = parent
        self.set_working_dir()

        # Constants/Variable
        self.dico_tiles_todo = {}
        self.dico_tiles_done = {}
        self.v_ = {}
        for item in self.list_del_ckbtn + self.list_do_ckbtn:
            self.v_[item] = tk.IntVar()
        self.latlon = tk.StringVar()

        # Frames
        self.frame_left = tk.Frame(
            self, border=4, relief=RIDGE, bg=_BG
        )
        self.frame_left.grid(row=0, column=0, sticky=N + S + W + E)
        self.frame_right = tk.Frame(
            self, border=4, relief=RIDGE, bg=_BG
        )
        self.frame_right.grid(row=0, rowspan=60, column=1, sticky=N + S + W + E)
        self.frame_right.rowconfigure(0, weight=1, minsize=self.canvas_min_y)
        self.frame_right.columnconfigure(0, weight=1, minsize=self.canvas_min_x)

        # Widgets
        row = 0
        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Active tile"),
            fg=_FG2,
            bg=_BG,
            font="Helvetica 16 bold italic",
        ).grid(row=row, column=0, sticky=W + E)
        row += 1
        self.latlon_entry = tk.Entry(
            self.frame_left,
            width=8,
            bg=_BG,
            fg=_FG2,
            textvariable=self.latlon,
        )
        self.latlon_entry.grid(row=row, column=0, padx=5, pady=5, sticky=N + S)
        row += 1
        # Trash
        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Erase cached data"),
            fg=_FG2,
            bg=_BG,
            font="Helvetica 16 bold italic",
        ).grid(row=row, column=0, sticky=W + E)
        row += 1
        for item in self.list_del_ckbtn:
            tk.Checkbutton(
                self.frame_left,
                text=tr(item),
                anchor=W,
                variable=self.v_[item],
                bg=_BG,
                fg=_FG,
                selectcolor=_BG,
                activebackground=_BG,
                activeforeground="#ffffff",
                highlightthickness=0,
            ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
            row += 1
        _ctk_button(
            self.frame_left, text=tr("  Delete    "), command=self.trash
        ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
        row += 1
        # Batch build
        tk.Label(
            self.frame_left,
            anchor=W,
            text=tr("Batch build tiles"),
            fg=_FG2,
            bg=_BG,
            font="Helvetica 16 bold italic",
        ).grid(row=row, column=0, sticky=W + E)
        row += 1
        for item in self.list_do_ckbtn:
            tk.Checkbutton(
                self.frame_left,
                text=tr(item),
                anchor=W,
                variable=self.v_[item],
                bg=_BG,
                fg=_FG,
                selectcolor=_BG,
                activebackground=_BG,
                activeforeground="#ffffff",
                highlightthickness=0,
            ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
            row += 1
        _ctk_button(
            self.frame_left, text=tr("  Batch Build   "), command=self.batch_build
        ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
        row += 1
        # Refresh window
        _ctk_button(
            self.frame_left, text=tr("    Refresh     "), command=self.refresh
        ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
        row += 1
        # Exit
        _ctk_button(
            self.frame_left, text=tr("      Exit      "), command=self.exit
        ).grid(row=row, column=0, padx=5, pady=5, sticky=N + S + E + W)
        row += 1
        tk.Label(
            self.frame_left,
            text=(tr("Shortcuts :") + "\n-----------------\n"
                  + tr("B2-press+hold=move map") + "\n"
                  + "B1-double-click=select active\n"
                  + "Shift+B1=add to batch build\nCtrl+B1=link in Custom Scenery"),
            bg=_BG, fg=_FG).grid(row=row, column=0, padx=0, pady=5, sticky=N + S + E + W)
        row += 1

        self.canvas = tk.Canvas(self.frame_right, bd=0)
        self.canvas.grid(row=0, column=0, sticky=N + S + E + W)

        self.canvas.config(
            scrollregion=(
                1,
                1,
                2 ** self.earthzl * 256 - 1,
                2 ** self.earthzl * 256 - 1,
            )
        )  # self.canvas.bbox(ALL))
        (x0, y0) = GEO.wgs84_to_pix(lat + 0.5, lon + 0.5, self.earthzl)
        x0 = max(1, x0 - self.canvas_min_x / 2)
        y0 = max(1, y0 - self.canvas_min_y / 2)
        self.canvas.xview_moveto(x0 / self.resolution)
        self.canvas.yview_moveto(y0 / self.resolution)
        self.nx0 = int((8 * x0) // self.resolution)
        self.ny0 = int((8 * y0) // self.resolution)
        if "dar" in sys.platform:
            self.canvas.bind("<ButtonPress-2>", self.scroll_start)
            self.canvas.bind("<B2-Motion>", self.scroll_move)
        else:
            self.canvas.bind("<ButtonPress-3>", self.scroll_start)
            self.canvas.bind("<B3-Motion>", self.scroll_move)
        self.canvas.bind("<Double-Button-1>", self.select_tile)
        self.canvas.bind("<Shift-ButtonPress-1>", self.add_tile)
        self.canvas.bind("<Control-ButtonPress-1>", self.toggle_to_custom)
        # Refocus automatique au survol — ne pas binder ButtonPress-1
        # car il interfère avec Double-Button-1 sur macOS
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        self.canvas.focus_set()
        self.draw_canvas(self.nx0, self.ny0)
        self.active_lat = lat
        self.active_lon = lon
        self.latlon.set(FNAMES.short_latlon(self.active_lat, self.active_lon))
        [x0, y0] = GEO.wgs84_to_pix(
            self.active_lat + 1, self.active_lon, self.earthzl
        )
        [x1, y1] = GEO.wgs84_to_pix(
            self.active_lat, self.active_lon + 1, self.earthzl
        )
        self.active_tile = self.canvas.create_rectangle(
            x0, y0, x1, y1, fill="", outline="yellow", width=3
        )
        # Taille minimale = taille naturelle du contenu une fois l'UI construite.
        # Empêche de masquer les boutons en réduisant la fenêtre ;
        # l'agrandissement reste libre.
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.threaded_preview()
        return

    def set_working_dir(self):
        self.custom_build_dir = self.parent.custom_build_dir.get()
        self.grouped = (
            self.custom_build_dir and self.custom_build_dir[-1] != "/"
        )
        self.working_dir = (
            self.custom_build_dir if self.custom_build_dir else FNAMES.Tile_dir
        )

    def refresh(self):
        self.set_working_dir()
        self.threaded_preview()
        return

    def threaded_preview(self):
        threading.Thread(target=self.preview_existing_tiles).start()

    def preview_existing_tiles(self):
        dico_color = {
            11: "#1e3028",
            12: "#1e3028",
            13: "#1e3028",
            14: "#1e3028",
            15: "cyan",
            16: _CON_FG,
            17: "yellow",
            18: "orange",
            19: "red",
        }
        if self.dico_tiles_done:
            for tile in self.dico_tiles_done:
                for objid in self.dico_tiles_done[tile][:2]:
                    self.canvas.delete(objid)
            self.dico_tiles_done = {}
        if not self.grouped:
            for dir_name in os.listdir(self.working_dir):
                if "XP_" in dir_name:
                    try:
                        lat = int(dir_name.split("XP_")[1][:3])
                        lon = int(dir_name.split("XP_")[1][3:7])
                    except:
                        continue
                    # With the enlarged accepetance rule for directory name 
                    # there might be more than one tile for the same (lat,lon),
                    # we skip all but the first encountered.
                    if (lat, lon) in self.dico_tiles_done:
                        continue
                    [x0, y0] = GEO.wgs84_to_pix(lat + 1, lon, self.earthzl)
                    [x1, y1] = GEO.wgs84_to_pix(lat, lon + 1, self.earthzl)
                    if os.path.isfile(
                        os.path.join(
                            self.working_dir,
                            dir_name,
                            "Earth nav data",
                            FNAMES.long_latlon(lat, lon) + ".dsf",
                        )
                    ):
                        color = "#1e3028"
                        content = ""
                        try:
                            tmpf = open(
                                os.path.join(
                                    self.working_dir,
                                    dir_name,
                                    "Ortho4XP_"
                                    + FNAMES.short_latlon(lat, lon)
                                    + ".cfg",
                                ),
                                "r",
                                encoding="latin-1",
                            )
                            found_config = True
                        except:
                            try:
                                tmpf = open(
                                    os.path.join(
                                        self.working_dir,
                                        dir_name,
                                        "Ortho4XP.cfg",
                                    ),
                                    "r",
                                    encoding="latin-1",
                                )
                                found_config = True
                            except:
                                found_config = False
                        if found_config:
                            prov = zl = ""
                            for line in tmpf.readlines():
                                if line[:15] == "default_website":
                                    prov = line.strip().split("=")[1][:4]
                                elif line[:10] == "default_zl":
                                    zl = int(line.strip().split("=")[1])
                                    break
                            tmpf.close()
                            if not prov:
                                prov = "?"
                            if zl:
                                color = dico_color[zl]
                            else:
                                zl = "?"
                            content = prov + "\n" + str(zl)
                        else:
                            content = "?"
                        self.dico_tiles_done[(lat, lon)] = (
                            self.canvas.create_rectangle(
                                x0, y0, x1, y1, fill=color, stipple="gray12"
                            )
                            if not OsX
                            else self.canvas.create_rectangle(
                                x0, y0, x1, y1, outline="black"
                            ),
                            self.canvas.create_text(
                                (x0 + x1) // 2,
                                (y0 + y1) // 2,
                                justify=CENTER,
                                text=content,
                                fill="black",
                                font=("Helvetica", "12", "normal"),
                            ),
                            dir_name,
                        )
                        link = os.path.join(
                            CFG.custom_scenery_dir,
                            "zOrtho4XP_" + FNAMES.short_latlon(lat, lon),
                        )
                        if os.path.isdir(link):
                            if os.path.samefile(
                                os.path.realpath(link),
                                os.path.realpath(
                                    os.path.join(self.working_dir, dir_name)
                                ),
                            ):
                                if not OsX:
                                    self.canvas.itemconfig(
                                        self.dico_tiles_done[(lat, lon)][0],
                                        stipple="gray50",
                                    )
                                else:
                                    self.canvas.itemconfig(
                                        self.dico_tiles_done[(lat, lon)][1],
                                        font=(
                                            "Helvetica",
                                            "12",
                                            "bold underline",
                                        ),
                                    )
        elif self.grouped and os.path.isdir(
            os.path.join(self.working_dir, "Earth nav data")
        ):
            for dir_name in os.listdir(
                os.path.join(self.working_dir, "Earth nav data")
            ):
                for file_name in os.listdir(
                    os.path.join(self.working_dir, "Earth nav data", dir_name)
                ):
                    try:
                        lat = int(file_name[0:3])
                        lon = int(file_name[3:7])
                    except:
                        continue
                    [x0, y0] = GEO.wgs84_to_pix(lat + 1, lon, self.earthzl)
                    [x1, y1] = GEO.wgs84_to_pix(lat, lon + 1, self.earthzl)
                    color = "#1e3028"
                    content = ""
                    try:
                        tmpf = open(
                            os.path.join(
                                self.working_dir,
                                "Ortho4XP_"
                                + FNAMES.short_latlon(lat, lon)
                                + ".cfg",
                            ),
                            "r",
                            encoding="latin-1",
                        )
                        found_config = True
                    except:
                        found_config = False
                    if found_config:
                        prov = zl = ""
                        for line in tmpf.readlines():
                            if line[:15] == "default_website":
                                prov = line.strip().split("=")[1][:4]
                            elif line[:10] == "default_zl":
                                zl = int(line.strip().split("=")[1])
                                break
                        tmpf.close()
                        if not prov:
                            prov = "?"
                        if zl:
                            color = dico_color[zl]
                        else:
                            zl = "?"
                        content = prov + "\n" + str(zl)
                    else:
                        content = "?"
                    self.dico_tiles_done[(lat, lon)] = (
                        self.canvas.create_rectangle(
                            x0, y0, x1, y1, fill=color, stipple="gray12"
                        )
                        if not OsX
                        else self.canvas.create_rectangle(
                            x0, y0, x1, y1, outline="black"
                        ),
                        self.canvas.create_text(
                            (x0 + x1) // 2,
                            (y0 + y1) // 2,
                            justify=CENTER,
                            text=content,
                            fill="black",
                            font=("Helvetica", "12", "normal"),
                        ),
                        dir_name,
                    )
            link = os.path.join(
                CFG.custom_scenery_dir,
                "zOrtho4XP_" + os.path.basename(self.working_dir),
            )
            if os.path.isdir(link):
                if os.path.samefile(
                    os.path.realpath(link), os.path.realpath(self.working_dir)
                ):
                    for (lat0, lon0) in self.dico_tiles_done:
                        if "dar" not in sys.platform:
                            self.canvas.itemconfig(
                                self.dico_tiles_done[(lat, lon)][0],
                                stipple="gray50",
                            )
                        else:
                            self.canvas.itemconfig(
                                self.dico_tiles_done[(lat, lon)][1],
                                font=("Helvetica", "12", "bold underline"),
                            )
        for (lat, lon) in self.dico_tiles_todo:
            [x0, y0] = GEO.wgs84_to_pix(lat + 1, lon, self.earthzl)
            [x1, y1] = GEO.wgs84_to_pix(lat, lon + 1, self.earthzl)
            self.canvas.delete(self.dico_tiles_todo[(lat, lon)])
            self.dico_tiles_todo[(lat, lon)] = (
                self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill="red", stipple="gray12"
                )
                if not OsX
                else self.canvas.create_rectangle(
                    x0, y0, x1, y1, outline="red", width=2
                )
            )
        return

    def trash(self):
        if self.v_["OSM data"].get():
            try:
                shutil.rmtree(FNAMES.osm_dir(self.active_lat, self.active_lon))
            except Exception as e:
                UI.vprint(3, e)
        if self.v_["Mask data"].get():
            try:
                shutil.rmtree(FNAMES.mask_dir(self.active_lat, self.active_lon))
            except Exception as e:
                UI.vprint(3, e)
        if self.v_["Jpeg imagery"].get():
            try:
                shutil.rmtree(
                    os.path.join(
                        FNAMES.Imagery_dir,
                        FNAMES.long_latlon(self.active_lat, self.active_lon),
                    )
                )
            except Exception as e:
                UI.vprint(3, e)
        if self.v_["Tile (whole)"].get() and not self.grouped:
            try:
                shutil.rmtree(
                    FNAMES.build_dir(
                        self.active_lat, self.active_lon, self.custom_build_dir
                    )
                )
            except Exception as e:
                UI.vprint(3, e)
            if (self.active_lat, self.active_lon) in self.dico_tiles_done:
                for objid in self.dico_tiles_done[
                    (self.active_lat, self.active_lon)
                ][:2]:
                    self.canvas.delete(objid)
                del self.dico_tiles_done[(self.active_lat, self.active_lon)]
        if self.v_["Tile (textures)"].get() and not self.grouped:
            try:
                shutil.rmtree(
                    os.path.join(
                        FNAMES.build_dir(
                            self.active_lat,
                            self.active_lon,
                            self.custom_build_dir,
                        ),
                        "textures",
                    )
                )
            except Exception as e:
                UI.vprint(3, e)
        return

    def select_tile(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        (lat, lon) = [floor(t) for t in GEO.pix_to_wgs84(x, y, self.earthzl)]
        self.active_lat = lat
        self.active_lon = lon
        self.latlon.set(FNAMES.short_latlon(lat, lon))
        try:
            self.canvas.delete(self.active_tile)
        except:
            pass
        [x0, y0] = GEO.wgs84_to_pix(lat + 1, lon, self.earthzl)
        [x1, y1] = GEO.wgs84_to_pix(lat, lon + 1, self.earthzl)
        self.active_tile = self.canvas.create_rectangle(
            x0, y0, x1, y1, fill="", outline="yellow", width=3
        )
        self.parent.lat.set(lat)
        self.parent.lon.set(lon)
        return

    def toggle_to_custom(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        (lat, lon) = [floor(t) for t in GEO.pix_to_wgs84(x, y, self.earthzl)]
        if (lat, lon) not in self.dico_tiles_done:
            return
        if not self.grouped:
            link = os.path.join(
                CFG.custom_scenery_dir,
                "zOrtho4XP_" + FNAMES.short_latlon(lat, lon),
            )
            # target=os.path.realpath(os.path.join(self.working_dir,
            # 'zOrtho4XP_'+FNAMES.short_latlon(lat,lon)))
            target = os.path.realpath(
                os.path.join(
                    self.working_dir, self.dico_tiles_done[(lat, lon)][-1]
                )
            )
            if os.path.isdir(link) and os.path.samefile(
                os.path.realpath(link), target
            ):
                os.remove(link)
                if not OsX:
                    self.canvas.itemconfig(
                        self.dico_tiles_done[(lat, lon)][0], stipple="gray12"
                    )
                else:
                    self.canvas.itemconfig(
                        self.dico_tiles_done[(lat, lon)][1],
                        font=("Helvetica", "12", "normal"),
                    )
                return
        elif self.grouped:
            link = os.path.join(
                CFG.custom_scenery_dir,
                "zOrtho4XP_" + os.path.basename(self.working_dir),
            )
            target = os.path.realpath(self.working_dir)
            if os.path.isdir(link) and os.path.samefile(
                os.path.realpath(link), os.path.realpath(self.working_dir)
            ):
                os.remove(link)
                for (lat0, lon0) in self.dico_tiles_done:
                    if not OsX:
                        self.canvas.itemconfig(
                            self.dico_tiles_done[(lat, lon)][0],
                            stipple="gray12",
                        )
                    else:
                        self.canvas.itemconfig(
                            self.dico_tiles_done[(lat, lon)][1],
                            font=("Helvetica", "12", "normal"),
                        )
                return
        # in case this was a broken link
        try:
            os.remove(link)
        except:
            pass
        if ("dar" in sys.platform) or (
            "win" not in sys.platform
        ):  # Mac and Linux
            os.system("ln -s " + ' "' + target + '" "' + link + '"')
        else:
            os.system('MKLINK /J "' + link + '" "' + target + '"')
        if not self.grouped:
            if not OsX:
                self.canvas.itemconfig(
                    self.dico_tiles_done[(lat, lon)][0], stipple="gray50"
                )
            else:
                self.canvas.itemconfig(
                    self.dico_tiles_done[(lat, lon)][1],
                    font=("Helvetica", "12", "bold underline"),
                )
        else:
            for (lat0, lon0) in self.dico_tiles_done:
                if not OsX:
                    self.canvas.itemconfig(
                        self.dico_tiles_done[(lat0, lon0)][0], stipple="gray50"
                    )
                else:
                    self.canvas.itemconfig(
                        self.dico_tiles_done[(lat, lon)][1],
                        font=("Helvetica", "12", "bold underline"),
                    )
        return

    def add_tile(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        (lat, lon) = [floor(t) for t in GEO.pix_to_wgs84(x, y, self.earthzl)]
        # V3.2 — Mettre à jour active_lat/active_lon pour que Delete fonctionne
        # sur la tuile visible, même sans double-clic préalable
        self.active_lat = lat
        self.active_lon = lon
        self.latlon.set(FNAMES.short_latlon(lat, lon))
        if (lat, lon) not in self.dico_tiles_todo:
            [x0, y0] = GEO.wgs84_to_pix(lat + 1, lon, self.earthzl)
            [x1, y1] = GEO.wgs84_to_pix(lat, lon + 1, self.earthzl)
            if not OsX:
                self.dico_tiles_todo[(lat, lon)] = self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill="red", stipple="gray12"
                )
            else:
                self.dico_tiles_todo[(lat, lon)] = self.canvas.create_rectangle(
                    x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline="red", width=1
                )
        else:
            self.canvas.delete(self.dico_tiles_todo[(lat, lon)])
            self.dico_tiles_todo.pop((lat, lon), None)
        return

    def batch_build(self):
        list_lat_lon = sorted(self.dico_tiles_todo.keys())
        if not list_lat_lon:
            return
        (lat, lon) = list_lat_lon[0]
        try:
            tile = CFG.Tile(lat, lon, self.custom_build_dir)
        except:
            return 0
        args = [
            tile,
            list_lat_lon,
            self.v_["Assemble vector data"].get(),
            self.v_["Triangulate 3D mesh"].get(),
            self.v_["Draw water masks"].get(),
            self.v_["Build imagery/DSF"].get(),
            self.v_["Extract overlays"].get(),
            self.v_["Read per tile cfg"].get(),
        ]
        threading.Thread(target=TILE.build_tile_list, args=args).start()
        return

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        return

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.redraw_canvas()
        return

    def redraw_canvas(self):
        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        if x0 < 0:
            x0 = 0
        if y0 < 0:
            y0 = 0
        nx0 = int((8 * x0) // self.resolution)
        ny0 = int((8 * y0) // self.resolution)
        if nx0 == self.nx0 and ny0 == self.ny0:
            return
        else:
            self.nx0 = nx0
            self.ny0 = ny0
            try:
                self.canvas.delete(self.canv_imgNW)
            except:
                pass
            try:
                self.canvas.delete(self.canv_imgNE)
            except:
                pass
            try:
                self.canvas.delete(self.canv_imgSW)
            except:
                pass
            try:
                self.canvas.delete(self.canv_imgSE)
            except:
                pass
            fargs_rc = [nx0, ny0]
            self.rc_thread = threading.Thread(
                target=self.draw_canvas, args=fargs_rc
            )
            self.rc_thread.start()
            return

    def draw_canvas(self, nx0, ny0):
        fileprefix = os.path.join(
            FNAMES.Utils_dir, "Earth", "Earth2_ZL" + str(self.earthzl) + "_"
        )
        filepreviewNW = fileprefix + str(nx0) + "_" + str(ny0) + ".jpg"
        try:
            self.imageNW = Image.open(filepreviewNW)
            self.photoNW = ImageTk.PhotoImage(self.imageNW)
            self.canv_imgNW = self.canvas.create_image(
                nx0 * 2 ** self.earthzl * 256 / 8,
                ny0 * 2 ** self.earthzl * 256 / 8,
                anchor=NW,
                image=self.photoNW,
            )
            self.canvas.tag_lower(self.canv_imgNW)
        except:
            UI.lvprint(
                0,
                "Could not find Earth preview file",
                filepreviewNW,
                ", please update your installation from a fresh copy.",
            )
            # Fond gris couvrant TOUTE la scrollregion — indispensable pour
            # que canvasx/canvasy retournent des coords correctes même sans carte
            res = 2 ** self.earthzl * 256
            self.canvas.create_rectangle(
                0, 0, res, res,
                fill="#3a3a3a", outline="", tags="background"
            )
            # Message centré sur la zone visible
            cx = nx0 * res // 8 + self.canvas_min_x // 2
            cy = ny0 * res // 8 + self.canvas_min_y // 2
            self.canvas.create_text(
                cx, cy,
                text=tr("Carte Earth non disponible\\n") +
                     tr('Copiez Utils/Earth/ depuis Ortho4XP 2.00\n\nDouble-clic = sélectionner tuile\nShift+clic = ajouter au batch'),
                fill="white", font=("TkFixedFont", 13),
                justify="center"
            )
        if nx0 < 2 ** (self.earthzl - 3) - 1:
            filepreviewNE = fileprefix + str(nx0 + 1) + "_" + str(ny0) + ".jpg"
            self.imageNE = Image.open(filepreviewNE)
            self.photoNE = ImageTk.PhotoImage(self.imageNE)
            self.canv_imgNE = self.canvas.create_image(
                (nx0 + 1) * 2 ** self.earthzl * 256 / 8,
                ny0 * 2 ** self.earthzl * 256 / 8,
                anchor=NW,
                image=self.photoNE,
            )
            self.canvas.tag_lower(self.canv_imgNE)
        if ny0 < 2 ** (self.earthzl - 3) - 1:
            filepreviewSW = fileprefix + str(nx0) + "_" + str(ny0 + 1) + ".jpg"
            self.imageSW = Image.open(filepreviewSW)
            self.photoSW = ImageTk.PhotoImage(self.imageSW)
            self.canv_imgSW = self.canvas.create_image(
                nx0 * 2 ** self.earthzl * 256 / 8,
                (ny0 + 1) * 2 ** self.earthzl * 256 / 8,
                anchor=NW,
                image=self.photoSW,
            )
            self.canvas.tag_lower(self.canv_imgSW)
        if (
            nx0 < 2 ** (self.earthzl - 3) - 1
            and ny0 < 2 ** (self.earthzl - 3) - 1
        ):
            filepreviewSE = (
                fileprefix + str(nx0 + 1) + "_" + str(ny0 + 1) + ".jpg"
            )
            self.imageSE = Image.open(filepreviewSE)
            self.photoSE = ImageTk.PhotoImage(self.imageSE)
            self.canv_imgSE = self.canvas.create_image(
                (nx0 + 1) * 2 ** self.earthzl * 256 / 8,
                (ny0 + 1) * 2 ** self.earthzl * 256 / 8,
                anchor=NW,
                image=self.photoSE,
            )
            self.canvas.tag_lower(self.canv_imgSE)
        return

    def exit(self):
        self.destroy()



# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATEUR VISUEL — déplacé dans O4_Simulator_Utils.py (module non bloquant)
# Le bouton « Visualisation réglages » appelle open_simulator_window() → _SIMMOD
# ═══════════════════════════════════════════════════════════════════════════════
