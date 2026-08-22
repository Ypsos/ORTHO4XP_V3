# ============================================================
#  O4_Lang.py  —  ORTHO4XP V2  —  Moteur de traduction
#
#  La langue est sauvegardée dans Ortho4XP.cfg (racine)
#  sous la clé :  language=EN   ou   language=FR
#
#  Usage dans les autres fichiers :
#      from O4_Lang import tr
#      button = ttk.Button(frame, text=tr("Assemble Vector data"))
#
#  Au 1er lancement (clé absente de Ortho4XP.cfg) → dialogue de choix.
#  Depuis l'interface → bouton dans Outils : "🌐 Changer la langue…"
# ============================================================

import os
import re
import locale
import tkinter as tk
from tkinter import ttk

# ── Chemin du fichier de config global ────────────────────────────
try:
    import O4_File_Names as FNAMES
    _cfg_path = os.path.join(FNAMES.Ortho4XP_dir, "Ortho4XP.cfg")
except Exception:
    # O4_Lang.py est dans src/ — remonter d'un niveau pour trouver Ortho4XP.cfg
    _src_dir  = os.path.dirname(os.path.abspath(__file__))
    _root_dir = os.path.dirname(_src_dir)
    _cfg_path = os.path.join(_root_dir, "Ortho4XP.cfg")

# ── Langues disponibles ────────────────────────────────────────────
#  La liste n'est PLUS ecrite en dur : elle est construite en scannant
#  le dossier src/ a la recherche de tous les fichiers  O4_Lang_XX.py
#  presents. Ajouter demain un fichier  O4_Lang_DE.py  (allemand) ou
#  O4_Lang_ES.py  (espagnol) suffit : aucune modification de code.
#  EN et FR restent garantis comme base de secours.

_LANG_FILE_RE = re.compile(r"^O4_Lang_([A-Za-z]{2,3})\.py$")

def _scan_available_langs():
    """
    Scanne le dossier de ce module et retourne un dict
       { 'EN': 'O4_Lang_EN', 'FR': 'O4_Lang_FR', ... }
    a partir des fichiers  O4_Lang_XX.py  reellement presents.
    EN et FR sont toujours garantis (base de secours).
    """
    langs = {}
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        for name in os.listdir(here):
            m = _LANG_FILE_RE.match(name)
            if m:
                code = m.group(1).upper()
                langs[code] = "O4_Lang_" + code
    except Exception as e:
        print("[O4_Lang] Cannot scan language files: {}".format(e))
    # Garantie de la base minimale
    langs.setdefault("EN", "O4_Lang_EN")
    langs.setdefault("FR", "O4_Lang_FR")
    return langs

AVAILABLE_LANGS = _scan_available_langs()

# Noms natifs des langues, affiches dans le selecteur QUELLE QUE SOIT la
# langue active (un nom de langue se montre toujours dans sa propre langue).
# Une langue absente d'ici retombe sur tr("language_btn_xx") puis sur le code.
_LANG_NATIVE = {
    "EN": "🇬🇧  English",   "FR": "🇫🇷  Français",  "DE": "🇩🇪  Deutsch",
    "ES": "🇪🇸  Español",   "IT": "🇮🇹  Italiano",  "PT": "🇵🇹  Português",
    "NL": "🇳🇱  Nederlands", "IS": "🇮🇸  Íslenska",  "NO": "🇳🇴  Norsk",
    "SV": "🇸🇪  Svenska",   "FI": "🇫🇮  Suomi",     "GD": "🏴  Gàidhlig",
}

# ── État interne ───────────────────────────────────────────────────
_current_lang = "EN"
_translations  = {}


# ──────────────────────────────────────────────────────────────────
#  LECTURE / ÉCRITURE dans Ortho4XP.cfg
# ──────────────────────────────────────────────────────────────────

def _read_lang_from_cfg():
    """
    Lit la valeur de la clé 'language' dans Ortho4XP.cfg.
    Retourne le code ('EN' ou 'FR') ou None si absent / illisible.
    Format du fichier : une variable par ligne  ->  language=FR
    """
    if not os.path.isfile(_cfg_path):
        return None
    try:
        with open(_cfg_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("language="):
                    code = line.split("=", 1)[1].strip().upper()
                    if code in AVAILABLE_LANGS:
                        return code
    except Exception as e:
        print("[O4_Lang] Cannot read {}: {}".format(_cfg_path, e))
    return None


def _write_lang_to_cfg(code):
    """
    Ecrit (ou met a jour) la cle 'language=XX' dans Ortho4XP.cfg.
    Si le fichier existe, remplace la ligne language= existante
    ou ajoute la ligne en fin de fichier. Conserve tout le reste intact.
    """
    code = code.upper().strip()
    try:
        lines = []
        found = False
        if os.path.isfile(_cfg_path):
            with open(_cfg_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("language="):
                    lines[i] = "language={}\n".format(code)
                    found = True
                    break
        if not found:
            lines.append("language={}\n".format(code))
        with open(_cfg_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print("[O4_Lang] Cannot write language to {}: {}".format(_cfg_path, e))


# ──────────────────────────────────────────────────────────────────
#  DETECTION DE LA LANGUE DU SYSTEME  (Windows / macOS / Linux)
# ──────────────────────────────────────────────────────────────────

_LANG_VERBOSE = {"FRENCH": "FR", "ENGLISH": "EN", "GERMAN": "DE",
                 "SPANISH": "ES", "ITALIAN": "IT", "DUTCH": "NL",
                 "PORTUGUESE": "PT"}

def _normalize_lang_code(raw):
    """
    Transforme une valeur brute de locale en code langue 2 lettres.
    'fr_FR.UTF-8' / 'fr-FR' / 'French_France' -> 'FR'
    Renvoie None si la valeur est inutilisable (vide, 'C', 'POSIX'...).
    """
    if not raw:
        return None
    code = raw.replace("-", "_").split("_")[0].split(".")[0].strip().upper()
    if not code or code in ("C", "POSIX"):
        return None
    code = _LANG_VERBOSE.get(code, code)
    if len(code) < 2:
        return None
    return code[:2]


def _detect_system_lang():
    """
    Retourne le code langue de l'OS en 2 lettres majuscules (ex: 'FR',
    'EN', 'DE', 'ES') ou None si indeterminable.

    Multi-plateforme (Windows / macOS / Linux). On lit PLUSIEURS sources
    par ordre de fiabilite et on garde la premiere reellement exploitable
    (les valeurs 'C' / 'POSIX' sont ignorees) :
      1. variables d'environnement (vraie langue utilisateur sur macOS/Linux)
      2. locale.getdefaultlocale() (fiable sur Windows)
      3. locale.getlocale() (dernier recours)
    Aucun setlocale() n'est appele : pas d'effet de bord sur le parsing
    des nombres. Aucune exception ne remonte : en cas de doute -> None.
    """
    candidates = []
    # 1) variables d'environnement
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var)
        if val:
            candidates.append(val)
    # 2) locale par defaut
    try:
        candidates.append(locale.getdefaultlocale()[0])
    except Exception:
        pass
    # 3) locale courant
    try:
        candidates.append(locale.getlocale()[0])
    except Exception:
        pass
    for raw in candidates:
        code = _normalize_lang_code(raw)
        if code:
            return code
    return None


def _resolve_startup_lang():
    """
    Determine la langue a charger au 1er lancement (aucune langue encore
    enregistree dans Ortho4XP.cfg) :
      - langue de l'OS si son fichier O4_Lang_XX.py est present ;
      - sinon repli : FR si l'OS est francophone, EN dans tous les autres cas.
    """
    sys_code = _detect_system_lang()
    if sys_code and sys_code in AVAILABLE_LANGS:
        return sys_code
    if sys_code == "FR" and "FR" in AVAILABLE_LANGS:
        return "FR"
    if "EN" in AVAILABLE_LANGS:
        return "EN"
    # Ultime secours : n'importe quelle langue disponible
    return next(iter(AVAILABLE_LANGS), "EN")


# ──────────────────────────────────────────────────────────────────
#  CHARGEMENT DU DICTIONNAIRE
# ──────────────────────────────────────────────────────────────────

def _load_lang(code):
    """Charge le fichier O4_Lang_XX.py correspondant au code."""
    global _current_lang, _translations
    code = code.upper().strip()
    if code not in AVAILABLE_LANGS:
        code = "EN"
    module_name = AVAILABLE_LANGS[code]
    try:
        import importlib
        mod = importlib.import_module(module_name)
        _translations = mod.T
        _current_lang = code
    except Exception as e:
        print("[O4_Lang] Cannot load {}: {}".format(module_name, e))
        _translations = {}
        _current_lang = "EN"


# ──────────────────────────────────────────────────────────────────
#  FONCTION DE TRADUCTION
# ──────────────────────────────────────────────────────────────────

def tr(key):
    """
    Retourne la traduction de `key` dans la langue active.
    Si la cle est absente du dictionnaire, retourne `key` tel quel
    (aucun crash, l'interface reste lisible).
    """
    return _translations.get(key, key)


def current_lang():
    """Retourne le code de langue actif ('EN' ou 'FR')."""
    return _current_lang


# ──────────────────────────────────────────────────────────────────
#  COULEURS DU THEME  (aucune couleur ecrite en dur)
# ──────────────────────────────────────────────────────────────────

def _theme_colors():
    """
    Lit le theme courant via O4_Theme_Manager (comme le lanceur et la
    fenetre principale) et retourne un dict de couleurs. La fenetre de
    choix de langue suit ainsi le theme comme toutes les autres fenetres.
    Un repli neutre n'est utilise QUE si le gestionnaire de theme est
    totalement absent (meme logique que le lanceur).
    """
    t = {}
    try:
        import O4_Theme_Manager as _TM
        t = _TM.get_theme() or {}
    except Exception:
        t = {}
    btn_bg = t.get("btn_bg") or "#4a6b59"
    btn_fg = t.get("btn_fg") or "white"
    return {
        "bg":     t.get("bg")           or "#3b5b49",
        "fg":     t.get("fg")           or "#a6e3a1",
        "fg_dim": t.get("fg_secondary") or t.get("fg") or "#c0c0c0",
        "btn_bg": btn_bg,
        "btn_fg": btn_fg,
        "accent": t.get("accent") or t.get("btn_hover") or "#5a7b69",
    }


class _CanvasButton(tk.Canvas):
    """
    Bouton dessine sur un canvas (comme le HoverButton du lanceur), aux
    couleurs du theme. Contrairement a tk.Button, il s'affiche correctement
    sur macOS (le theme Aqua ignore la couleur de face des tk.Button).
    """
    def __init__(self, parent, text, command, colors,
                 width=190, height=48, font_size=14):
        super().__init__(parent, width=width, height=height,
                         bg=colors["bg"], highlightthickness=0, cursor="hand2")
        self._command = command
        self._btn = colors["btn_bg"]
        self._acc = colors["accent"]
        self._rect = self._rounded(2, 2, width - 2, height - 2, 12,
                                   fill=self._btn)
        self.create_text(width // 2, height // 2, text=text,
                         fill=colors["btn_fg"],
                         font=("Helvetica", font_size, "bold"))
        self.bind("<Button-1>", lambda e: self._command())
        self.bind("<Enter>", lambda e: self.itemconfig(self._rect, fill=self._acc))
        self.bind("<Leave>", lambda e: self.itemconfig(self._rect, fill=self._btn))

    def _rounded(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
               x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
               x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.create_polygon(pts, **kw, smooth=True)


def _themed_button(parent, text, command, colors,
                   width=190, height=48, font_size=14):
    """Bouton canvas aux couleurs du theme, lisible sur les 3 OS."""
    return _CanvasButton(parent, text, command, colors,
                         width=width, height=height, font_size=font_size)


# ──────────────────────────────────────────────────────────────────
#  DIALOGUE DE CHOIX DE LANGUE
# ──────────────────────────────────────────────────────────────────

def show_language_dialog(parent=None, on_change=None):
    """
    Affiche une fenetre modale pour choisir la langue.
    Sauvegarde le choix dans Ortho4XP.cfg (cle language=).
    - parent    : fenetre Tk parente (optionnel)
    - on_change : callable() appele apres le changement
    """
    C = _theme_colors()
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title(tr("language_dialog_title"))
    win.resizable(False, False)
    win.configure(bg=C["bg"])
    if parent:
        win.grab_set()

    # Langues : EN et FR restent des boutons visibles (base garantie) ;
    # toutes les AUTRES langues vont dans un menu deroulant, pour que la
    # fenetre reste compacte quel que soit leur nombre.
    _bases = [c for c in ("EN", "FR") if c in AVAILABLE_LANGS]
    _others = sorted(c for c in AVAILABLE_LANGS if c not in ("EN", "FR"))

    # Centrage + taille (stable : 2 boutons + 1 menu deroulant)
    win.update_idletasks()
    w = 470
    h = 210 + (48 if _others else 0)
    try:
        px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    except Exception:
        px, py = 300, 200
    win.geometry("{}x{}+{}+{}".format(w, h, px, py))

    tk.Label(
        win,
        text="  " + tr("language_dialog_message"),
        bg=C["bg"], fg=C["fg"],
        font=("TkFixedFont", 13, "bold"),
        pady=18,
    ).pack(fill=tk.X)

    btn_frame = tk.Frame(win, bg=C["bg"])
    btn_frame.pack(pady=4)

    def _choose(code):
        _load_lang(code)
        _write_lang_to_cfg(code)   # <- sauvegarde dans Ortho4XP.cfg
        win.destroy()
        # Message informatif — relancement requis
        msg_win = tk.Toplevel(parent) if parent else tk.Tk()
        msg_win.title("Ortho4XP")
        msg_win.configure(bg=C["bg"])
        msg_win.resizable(False, False)
        try:
            px2 = parent.winfo_rootx() + (parent.winfo_width()  - 480) // 2
            py2 = parent.winfo_rooty() + (parent.winfo_height() - 200) // 2
            msg_win.geometry("480x200+{}+{}".format(px2, py2))
        except Exception:
            msg_win.geometry("480x200")
        lbl_text = (
            "Language saved / Langue sauvegardée.\n\n"
            "Relancez Ortho4XP pour appliquer.\n"
            "Restart Ortho4XP to apply."
        )
        tk.Label(msg_win, text=lbl_text,
                 bg=C["bg"], fg=C["fg"],
                 font=("TkFixedFont", 11),
                 justify="center", pady=10).pack(expand=True)
        btn_txt = "  ✅  OK  — Click here to close  " if _current_lang == "EN" else "  ✅  OK  — Cliquez ici pour fermer  "
        _themed_button(msg_win, btn_txt, msg_win.destroy, C,
                       width=440, height=46, font_size=13).pack(pady=(0, 16))
        if callable(on_change):
            on_change()

    # Libelle natif d'une langue (nom dans sa propre langue), sinon libelle
    # traduit, sinon le code.
    def _btn_label(code):
        native = _LANG_NATIVE.get(code.upper())
        if native:
            return native
        lbl = tr("language_btn_" + code.lower())
        return code if lbl == "language_btn_" + code.lower() else lbl

    # Boutons EN / FR (base garantie), aux couleurs du theme.
    for _code in _bases:
        _themed_button(
            btn_frame, _btn_label(_code),
            (lambda c=_code: _choose(c)), C,
            width=190, height=50, font_size=14,
        ).pack(side=tk.LEFT, padx=12)

    # Menu deroulant pour toutes les autres langues.
    if _others:
        _prompt = "Autres langues…" if _current_lang != "EN" else "Other languages…"
        _labels, _lbl2code = [], {}
        for _c in _others:
            _l = _btn_label(_c)
            _labels.append(_l)
            _lbl2code[_l] = _c
        _sel = tk.StringVar(win)
        _sel.set(_prompt)
        # Menu déroulant Mac-safe : ttk.Combobox stylé (même recette que
        # O4_comb_generator.py). tk.OptionMenu restait blanc/gris sur macOS
        # et masquait son texte d'invite ; le Combobox l'affiche correctement.
        _style = ttk.Style(win)
        try:
            _style.theme_use("alt")
        except Exception:
            pass
        _COMBO_BG = "#f0f4f2"   # fond clair (recette O4_comb_generator, lisible sur Mac)
        _COMBO_FG = "#1e3028"   # texte vert foncé, lisible sur fond clair
        _style.configure("O4Lang.TCombobox",
                         fieldbackground=_COMBO_BG,
                         background=_COMBO_BG,
                         foreground=_COMBO_FG)
        _om = ttk.Combobox(win, textvariable=_sel, values=_labels,
                           state="readonly", style="O4Lang.TCombobox",
                           font=("Helvetica", 12, "bold"))

        def _on_lang_select(_evt=None):
            _s = _sel.get()
            if _s in _lbl2code:
                _choose(_lbl2code[_s])

        _om.bind("<<ComboboxSelected>>", _on_lang_select)
        _om.pack(pady=(12, 0), ipadx=8, ipady=3)

    # Indicateur langue courante + nom du fichier cfg
    cfg_short = os.path.basename(_cfg_path)
    tk.Label(
        win,
        text="(current: {}  -  saved in {})".format(_current_lang, cfg_short),
        bg=C["bg"], fg=C["fg_dim"],
        font=("TkFixedFont", 9),
    ).pack(pady=(10, 0))

    if parent:
        parent.wait_window(win)
    else:
        win.mainloop()


# ──────────────────────────────────────────────────────────────────
#  BOUTON REUTILISABLE
# ──────────────────────────────────────────────────────────────────

def make_language_button(parent, on_change=None):
    """
    Cree et retourne un bouton pret a etre place dans un frame.

    Utilise la fabrique maison _themed_button (Canvas arrondi aux couleurs
    du theme, lisible sur les 3 OS) — meme look que les boutons de la fenetre
    de choix de langue. Repli ttk.Button si la fabrique echoue.

    Exemple :
        from O4_Lang import make_language_button
        make_language_button(frame_tools, on_change=rebuild_cb).pack(
            side=tk.LEFT, padx=8, pady=4)
    """
    _cmd = lambda: show_language_dialog(parent, on_change=on_change)
    try:
        return _themed_button(
            parent,
            "  " + tr("language_menu_change_lang"),
            _cmd,
            _theme_colors(),
            width=210, height=40, font_size=12,
        )
    except Exception:
        return ttk.Button(
            parent,
            text="  " + tr("language_menu_change_lang"),
            style="TButton",
            command=_cmd,
        )


# ──────────────────────────────────────────────────────────────────
#  INITIALISATION AU DEMARRAGE
# ──────────────────────────────────────────────────────────────────

def init(parent=None, on_change=None):
    """
    A appeler UNE SEULE FOIS au demarrage (avant root.mainloop()).

    Comportement :
    - Lit la cle 'language=' dans Ortho4XP.cfg
    - Si presente -> charge silencieusement la langue sauvegardee
                     (comportement V2 strictement inchange)
    - Si absente  -> detecte la langue de l'OS, la charge si son fichier
                     existe, sinon repli FR (OS francophone) ou EN,
                     puis enregistre ce choix dans Ortho4XP.cfg.
                     Aucune fenetre : le bouton "Changer la langue"
                     de l'onglet Outils reste disponible a tout moment.
    """
    saved = _read_lang_from_cfg()
    if saved:
        _load_lang(saved)
    else:
        # Premier lancement : detection automatique + repli
        code = _resolve_startup_lang()
        _load_lang(code)
        _write_lang_to_cfg(code)   # fixe le choix pour les lancements suivants
        if callable(on_change):
            on_change()


# ──────────────────────────────────────────────────────────────────
#  AUTO-INIT silencieux (si importe sans appel a init())
# ──────────────────────────────────────────────────────────────────
_saved = _read_lang_from_cfg()
if _saved:
    _load_lang(_saved)
else:
    # Import sans appel a init() : on charge la langue detectee (repli EN/FR)
    # sans ecrire dans le cfg (init() reste l'endroit qui persiste le choix).
    _load_lang(_resolve_startup_lang())


# ──────────────────────────────────────────────────────────────────
#  GUIDE D'INTEGRATION
# ──────────────────────────────────────────────────────────────────
#
#  1. DEMARRAGE (script principal ou O4_GUI_Utils.py)
#  ---------------------------------------------------
#     import O4_Lang
#     O4_Lang.init(parent=root)   # AVANT root.mainloop()
#
#
#  2. TRADUCTION D'UN TEXTE
#  -------------------------
#     from O4_Lang import tr
#     ttk.Button(frame, text=tr("Assemble Vector data"), ...)
#     tk.Label(frame,   text=tr("Latitude:"), ...)
#
#
#  3. BOUTON "CHANGER LA LANGUE" DANS L'ONGLET OUTILS
#  ----------------------------------------------------
#     from O4_Lang import make_language_button
#     make_language_button(frame_outils).pack(side=tk.LEFT, padx=8)
#
#
#  4. FORMAT DANS Ortho4XP.cfg
#  ----------------------------
#     language=FR      <- ajoute automatiquement par O4_Lang
#     (ligne unique, mise a jour a chaque changement de langue)
#     Les autres variables du cfg ne sont jamais touchees.
#
# ──────────────────────────────────────────────────────────────────
