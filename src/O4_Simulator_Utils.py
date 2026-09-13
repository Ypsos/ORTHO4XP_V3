# -*- coding: utf-8 -*-
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — Mars 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CREDIT — AUTHOR: Roland (Ypsos) — March 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================
"""
O4_Simulator_Utils.py — Simulateur visuel Ortho4XP V3 (module autonome)
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, HORIZONTAL, LEFT, RIGHT, CENTER, N, S, E, W, NW, NE, SW, SE, END, ALL, RIDGE
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    ctk = None
    _HAS_CTK = False

from PIL import Image, ImageTk
import O4_File_Names as FNAMES
import O4_Config_Utils as CFG
from O4_Lang import tr

_BG     = "#3b5b49"
_FG     = "#e8f0ec"
_FG2    = "#a6e3a1"
_BTN_BG = "#4a6b59"
_BTN_FG = "#ffffff"
_CON_BG = "#0f0f1a"
_CON_FG = "#50fa7b"
_ACCENT = "#a6e3a1"

def _reload_theme():
    global _BG, _FG, _FG2, _BTN_BG, _BTN_FG, _CON_BG, _CON_FG, _ACCENT
    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
        _BG     = _t.get("bg", _BG)
        _FG     = _t.get("fg", _FG)
        _FG2    = _t.get("fg_secondary", _FG2)
        _BTN_BG = _t.get("btn_bg", _BTN_BG)
        _BTN_FG = _t.get("btn_fg", _BTN_FG)
        _CON_BG = _t.get("console_bg", _CON_BG)
        _CON_FG = _t.get("console_fg", _CON_FG)
        _ACCENT = _t.get("accent", _ACCENT)
    except Exception:
        pass

_reload_theme()

def _lighten(hexcol, factor=1.30):
    try:
        h = hexcol.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hexcol

def _ctk_button(parent, text=None, command=None, width=None, corner_radius=8, **ttk_kw):
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
            fg_color=base, hover_color=_lighten(base, 1.30),
            border_color=_t.get("border", base),
            text_color=_t.get("btn_fg", "#ffffff"))
        if width:
            b.configure(width=width)
        b.after_idle(lambda btn=b, c=base: btn.winfo_exists() and btn.configure(fg_color=c))
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

# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATEUR VISUEL — Ortho4XP V3  (Étape 1 : tous paramètres cfg)
# ═══════════════════════════════════════════════════════════════════════════════




def _sim_images_roots():
    """Dossiers 'images' a la racine Ortho4XP (PAS dans src)."""
    roots = []
    candidates = []

    # A) FNAMES.Ortho4XP_dir
    try:
        base = getattr(FNAMES, "Ortho4XP_dir", None)
        if base:
            candidates.append(os.path.abspath(base))
    except Exception:
        pass

    # B) Remonter depuis le .py jusqu'a trouver un dossier "images"
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        cur = here
        for _ in range(6):
            candidates.append(cur)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    except Exception:
        pass

    # C) CWD
    try:
        candidates.append(os.path.abspath(os.getcwd()))
    except Exception:
        pass

    # D) Chemin Mac connu (fallback)
    candidates.append("/Users/rolandlehmann/Applications/ORTHO4XP_V3")

    seen = set()
    for c in candidates:
        if not c:
            continue
        try:
            img = os.path.normpath(os.path.join(c, "images"))
        except Exception:
            continue
        if img not in seen and os.path.isdir(img):
            seen.add(img)
            roots.append(img)
        elif img not in seen:
            # garder meme si pas encore cree, pour le message diagnostic
            seen.add(img)
            roots.append(img)
    return roots



# ── Images canvas simulateur Côte & Masques ──────────────────────
# Chargées depuis images/Mer_Cotes/ (PNG) — noir = transparent.
# Tous les PNG sont au même format (plein cadre) et se superposent.
# Noms attendus (tolérants) :
#   terre.png | fond marin.png | Merxplane.png | Lac.png | degrade jointure.png

_SIM_PNG_NAMES = {
    "terre":   ["terre.png", "Terre.png", "TERRE.png"],
    "fond":    ["fond marin.png", "fond_marin.png", "fondmarin.png", "Fond marin.png"],
    "mer":     ["Merxplane.png", "merxplane.png", "MerXplane.png", "mer.png", "Mer.png"],
    "lac":     ["Lac.png", "lac.png", "LAC.png"],
    "degrade": ["degrade jointure.png", "degrade_jointure.png", "degrade.png", "Degrade jointure.png"],
}

def _sim_find_png(key):
    """Retourne le chemin absolu du PNG Mer_Cotes pour la clé, ou None."""
    names = _SIM_PNG_NAMES.get(key, [])
    subdirs = ["Mer_Cotes", "Mer_Cotes".lower(), "mer_cotes", ""]
    for root in _sim_images_roots():
        for sub in subdirs:
            d = os.path.join(root, sub) if sub else root
            if not os.path.isdir(d):
                continue
            try:
                existing = {f.lower(): os.path.join(d, f) for f in os.listdir(d)}
            except Exception:
                continue
            for n in names:
                p = existing.get(n.lower())
                if p and os.path.isfile(p):
                    return p
            for low, full in existing.items():
                if key in low and low.endswith(".png"):
                    return full
    return None

def _sim_black_to_alpha(img, thresh=28):
    """Convertit les pixels quasi-noirs en transparent — version rapide.

    Le test porte sur max(R,G,B) : un pixel n'est rendu transparent que si
    TOUS ses canaux sont sombres (vrai fond noir). Sinon, les routes vertes
    (0,255,0) ou bleues (0,0,255), qui ont un rouge quasi nul, étaient
    effacées par erreur (ancienne version qui ne testait que le rouge).
    """
    from PIL import Image as _P, ImageChops as _C
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    # Luminance « max » par pixel : max(R, G, B)
    mx = _C.lighter(_C.lighter(r, g), b)

    def _mk(t=thresh):
        def fn(p):
            return 0 if p <= t else 255
        return fn

    # Masque : 0 (transparent) uniquement là où max(R,G,B) <= seuil = vrai noir
    mask = mx.point(_mk())
    # alpha final = min(alpha original, mask)
    a = _P.composite(a, _P.new("L", img.size, 0), mask)
    img.putalpha(a)
    return img

def _sim_load_full(key, w, h, cache, make_black_transparent=True):
    """
    Charge un PNG plein cadre, redimensionné à (w,h).
    Cache par (key, w, h, transparent).
    """
    ck = (key, w, h, make_black_transparent)
    if ck in cache:
        return cache[ck].copy()
    from PIL import Image as _P
    path = _sim_find_png(key)
    if not path:
        colors = {
            "terre":   (90, 140, 70, 255),
            "fond":    (40, 90, 130, 255),
            "mer":     (30, 120, 180, 220),
            "lac":     (40, 100, 160, 0),
            "degrade": (255, 230, 120, 180),
        }
        img = _P.new("RGBA", (max(1, w), max(1, h)), colors.get(key, (80, 80, 80, 255)))
        cache[ck] = img
        return img.copy()
    img = _P.open(path).convert("RGBA")
    if make_black_transparent:
        img = _sim_black_to_alpha(img)
    if img.size != (w, h):
        img = img.resize((max(1, w), max(1, h)), _P.LANCZOS)
    cache[ck] = img
    return img.copy()


# ── Images canvas simulateur Imagerie & Aéroports ────────────────
# Chargées depuis images/Imagerie/ (PNG/JPG) — noir = transparent pour les calques routes.
_SIM_IMG_NAMES = {
    "aeroport":  [
        "Aeroport.jpg", "aeroport.jpg", "Aeroport.png", "Aeroport.jpeg",
        "Aeroport", "aeroport", "airport.jpg", "Aéroport.jpg", "Aéroport.png",
    ],
    "autoroute": [
        "Autoroute.png", "autoroute.png", "AUTO.png", "Autoroute.jpg",
    ],
    "route1": [
        "Route1.png", "route1.png", "R1.png", "Route1.jpg",
    ],
    "route2": [
        "Route2.png", "route2.png", "R2.png", "Route2.jpg",
        "Route 2.png", "route 2.png",
    ],
    "jointure": [
        "Jointure.png", "jointure.png",
        "Jointure zone aeroport.png", "Jointure zone aéroport.png",
        "Jointure zone aeroport.jpg", "jointure zone aeroport.png",
    ],
}

def _sim_find_imagerie(key):
    """Cherche dans images/Aeroports, images/Imagerie, puis images/ (racine)."""
    names = _SIM_IMG_NAMES.get(key, [])
    # sous-dossiers possibles sous images/
    subdirs = ["Aeroports", "aeroports", "Imagerie", "imagerie", ""]
    for root in _sim_images_roots():
        for sub in subdirs:
            d = os.path.join(root, sub) if sub else root
            if not os.path.isdir(d):
                continue
            try:
                files = os.listdir(d)
            except Exception:
                continue
            # map lower -> real path (avec et sans extension)
            existing = {}
            for f in files:
                full = os.path.join(d, f)
                if not os.path.isfile(full):
                    continue
                existing[f.lower()] = full
                # aussi sans extension
                base, ext = os.path.splitext(f)
                if ext:
                    existing[base.lower()] = full
            for n in names:
                p = existing.get(n.lower())
                if p:
                    return p
    return None


def _sim_load_imagerie(key, w, h, cache, blur_r=0.0, black_transparent=False,
                       res_factor=1.0):
    """Charge et redimensionne une image Imagerie. Cache par (key,w,h,blur,bt,res)."""
    ck = (key, w, h, round(blur_r, 2), black_transparent, round(res_factor, 3))
    if ck in cache:
        return cache[ck]
    from PIL import Image as _P, ImageFilter as _F
    path = _sim_find_imagerie(key)
    if not path:
        # fallback : transparent si overlay, uni sombre si fond
        if black_transparent:
            img = _P.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
        else:
            img = _P.new("RGB", (max(1, w), max(1, h)), (30, 50, 40))
        cache[ck] = img
        return img
    img = _P.open(path)
    if black_transparent:
        img = _sim_black_to_alpha(img, thresh=25)
    else:
        img = img.convert("RGB")
    if img.size != (w, h):
        img = img.resize((max(1, w), max(1, h)), _P.LANCZOS)
    # Simulation d'un ZL plus bas = image BASSE RÉSOLUTION : on réduit fortement
    # l'image puis on la ré-agrandit → TOUTE l'image (pas seulement les détails
    # fins) devient moins nette, comme une vraie imagerie basse définition.
    if res_factor < 0.98:
        lw = max(1, int(w * res_factor))
        lh = max(1, int(h * res_factor))
        img = img.resize((lw, lh), _P.LANCZOS).resize(
            (max(1, w), max(1, h)), _P.BILINEAR)
    if blur_r > 0.3:
        img = img.filter(_F.GaussianBlur(radius=blur_r))
    cache[ck] = img
    return img


class Ortho4XP_Simulator(tk.Toplevel):
    """
    Fenêtre simulateur visuel.
    Affiche l'effet de chaque paramètre du cfg avec curseurs et canvas animé.
    Organisée en onglets thématiques. Lecture/écriture cfg via boutons.
    """

    BG       = "#1a2a20"
    BG2      = "#22342a"
    BG3      = _BG
    FG       = _FG
    FG2      = _FG2
    FG3      = "#607d6b"
    TROUGH   = "#0d1f17"
    ACC      = "#4fc3f7"

    def __init__(self, parent, lat, lon, custom_build_dir=""):
        tk.Toplevel.__init__(self, parent)
        self.configure(bg=_BG)
        self.parent = parent
        self.lat = lat
        self.lon = lon
        self.custom_build_dir = custom_build_dir
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title(tr("🎚  Simulateur Ortho4XP — tuile ") + f"{lat:+d}/{lon:+d}")
        self.configure(bg=self.BG)
        self.resizable(True, True)
        self._anim_running = True
        self._t = 0
        self._vars = {}
        self._canvases = {}
        self._tile = CFG.Tile(lat, lon, custom_build_dir)
        self._tile.read_from_config()
        self._build_ui()
        self._load_values()
        # Taille adaptée à l'écran : la fenêtre doit toujours laisser les
        # boutons du bas accessibles, même sur un moniteur de faible hauteur.
        # On ne prend PAS la hauteur naturelle de tous les onglets comme
        # minsize : certains onglets contiennent volontairement beaucoup de
        # réglages et pourraient pousser les boutons hors de l'écran.
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            # Plus large (vignettes à droite), hauteur limitée à l'écran
            # pour garder les boutons du bas accessibles (réf. onglet Mer).
            win_w = min(1280, max(1000, sw - 40))
            win_h = min(int(sh * 0.88), max(520, sh - 80))
            x = max(0, (sw - win_w) // 2)
            y = max(10, (sh - win_h) // 2)
            self.geometry(f"{win_w}x{win_h}+{x}+{y}")
            self.minsize(960, 520)
            self.maxsize(sw - 10, sh - 30)
        except Exception:
            self.geometry("1200x640")
            self.minsize(960, 520)
        self._anim_loop()

    def _on_close(self):
        self._anim_running = False
        self.destroy()

    # ── Construction UI ────────────────────────────────────────────────
    def _build_ui(self):
        s = 1.0
        try:
            if self.winfo_fpixels("1i") > 120:
                s = 1.2
        except Exception:
            pass
        fs = lambda x: int(x * s)

        self.configure(bg=self.BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        hdr = tk.Frame(self, bg=self.BG)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        tk.Label(hdr, text="Simulateur visuel — Ortho4XP V2",
            bg=self.BG, fg=self.FG2,
            font=("TkFixedFont", fs(13), "bold")).pack(side="left")
        tk.Label(hdr,
            text=tr("tuile ") + f"{self.lat:+d}/{self.lon:+d}",
            bg=self.BG, fg=self.FG3,
            font=("TkFixedFont", fs(10))).pack(side="left", padx=12)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)

        try:
            self._tab_mer_cote(nb, fs)
            self._tab_terrain(nb, fs)
            self._tab_mesh(nb, fs)
            self._tab_imagerie(nb, fs)
        except Exception as e:
            err = tk.Frame(nb, bg=self.BG2)
            nb.add(err, text="Erreur")
            tk.Label(err, text=tr("Erreur construction onglets : ") + str(e),
                bg=self.BG2, fg="#ff6b6b",
                font=("TkFixedFont", 11), justify="left").pack(anchor="w", padx=12, pady=12)

        status_fr = tk.Frame(self, bg=self.BG)
        status_fr.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        self._status = tk.Label(status_fr, text="", bg=self.BG,
            fg=self.FG2, font=("TkFixedFont", fs(10)))
        self._status.pack(side="left")

        btn_fr = tk.Frame(self, bg=self.BG)
        btn_fr.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        _ctk_button(btn_fr, text=tr("↺  Recharger depuis cfg"),
            command=self._load_values).pack(side="left", padx=4)
        _ctk_button(btn_fr, text=tr("✅  Écrire cfg tuile"),
            command=self._write_tile).pack(side="left", padx=4)
        _ctk_button(btn_fr, text=tr("🌍  Écrire cfg app"),
            command=self._write_app).pack(side="left", padx=4)
        _ctk_button(btn_fr, text=tr("✖  Fermer"),
            command=self._on_close).pack(side="right", padx=4)

        # La géométrie est calculée après construction de l'UI dans __init__
        # afin de tenir compte de la hauteur réelle du moniteur.

    def _make_scrollable(self, parent, row=0):
        """Zone défilante verticale (ascenseur à droite) pour les curseurs."""
        wrap = tk.Frame(parent, bg=self.BG2)
        wrap.grid(row=row, column=0, sticky="nsew", padx=4, pady=(0, 2))
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(0, weight=1)

        canvas = tk.Canvas(wrap, bg=self.BG2, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=self.BG2)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfigure(win, width=e.width)
        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            # macOS: e.delta ; Linux: Button-4/5
            if getattr(e, "delta", 0):
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            elif getattr(e, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(e, "num", None) == 5:
                canvas.yview_scroll(1, "units")

        def _bind_wheel(_e=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        def _unbind_wheel(_e=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        inner.bind("<Enter>", _bind_wheel)
        inner.bind("<Leave>", _unbind_wheel)

        inner.columnconfigure(0, weight=1)
        return inner


    def _bind_mousewheel_tree(self, widget, scroll_canvas):
        """Propage la molette vers le canvas de défilement (petit moniteur)."""
        def _on_mw(e, _c=scroll_canvas):
            try:
                if getattr(e, "delta", 0):
                    d = e.delta
                    _c.yview_scroll(int(-1 * (d / 120 if abs(d) >= 120 else d)), "units")
                elif getattr(e, "num", None) == 4:
                    _c.yview_scroll(-1, "units")
                elif getattr(e, "num", None) == 5:
                    _c.yview_scroll(1, "units")
            except Exception:
                pass
        def _bind(w):
            try:
                w.bind("<MouseWheel>", _on_mw, add="+")
                w.bind("<Button-4>", _on_mw, add="+")
                w.bind("<Button-5>", _on_mw, add="+")
            except Exception:
                pass
            try:
                for ch in w.winfo_children():
                    _bind(ch)
            except Exception:
                pass
        _bind(widget)

    def _make_tab(self, nb, title, canvas_height=170, inline=False):
        """
        inline=False (défaut) : comportement historique — une seule zone
            d'explication sous le canvas, alimentée au survol des curseurs.
            (Utilisé par l'onglet Terrain & Relief, inchangé.)
        inline=True : plus d'espace entre le canvas (montage) et les réglages
            (séparateur), et l'explication s'affiche en permanence sous chaque
            curseur (exp_lbl renvoyé = None ; passer inline_hint=True à
            _add_group).
        """
        frame = tk.Frame(nb, bg=self.BG2)
        nb.add(frame, text=title)
        frame.columnconfigure(0, weight=1)

        # Canvas en haut — pleine largeur
        # sticky nsew + padx=0 : évite la bande claire (fond notebook)
        # visible à droite du canvas sur macOS
        frame.rowconfigure(0, weight=0)
        frame.columnconfigure(0, weight=1)
        cv_frame = tk.Frame(frame, bg=_CON_BG, relief="flat", bd=0,
                            highlightthickness=0, highlightbackground=_CON_BG)
        cv_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(4, 2))
        cv = tk.Canvas(cv_frame, bg=_CON_BG,
            highlightthickness=0, borderwidth=0, height=canvas_height)
        cv.pack(fill="both", expand=True)
        # Forcer redraw quand le canvas est redimensionné
        cv.bind("<Configure>", lambda e: self.after(10, self._redraw_all))

        if inline:
            # Canvas fixe en haut ; zone curseurs défilante + ascenseur à droite
            # (indispensable sur petit moniteur pour atteindre les curseurs du bas)
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=0)
            frame.rowconfigure(2, weight=1)
            frame.columnconfigure(0, weight=1)

            sep_fr = tk.Frame(frame, bg=self.BG2)
            sep_fr.grid(row=1, column=0, sticky="ew", padx=6, pady=(2, 2))
            tk.Frame(sep_fr, bg=self.BG3, height=1).pack(fill="x")

            scroll_host = tk.Frame(frame, bg=self.BG2)
            scroll_host.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, 1))
            scroll_host.columnconfigure(0, weight=1)
            scroll_host.rowconfigure(0, weight=1)

            sc_canvas = tk.Canvas(scroll_host, bg=self.BG2,
                highlightthickness=0, borderwidth=0)
            vbar = ttk.Scrollbar(scroll_host, orient="vertical",
                command=sc_canvas.yview)
            sc_canvas.configure(yscrollcommand=vbar.set)
            sc_canvas.grid(row=0, column=0, sticky="nsew")
            vbar.grid(row=0, column=1, sticky="ns")

            inner = tk.Frame(sc_canvas, bg=self.BG2)
            inner.columnconfigure(0, weight=1)
            inner_id = sc_canvas.create_window((0, 0), window=inner, anchor="nw")

            def _on_inner_configure(_e=None, _c=sc_canvas, _i=inner):
                try:
                    _c.configure(scrollregion=_c.bbox("all"))
                    # largeur = canvas visible
                    _c.itemconfigure(inner_id, width=_c.winfo_width())
                except Exception:
                    pass

            def _on_sc_configure(e, _c=sc_canvas):
                try:
                    _c.itemconfigure(inner_id, width=e.width)
                except Exception:
                    pass

            def _on_mousewheel(e, _c=sc_canvas):
                # macOS: delta en unités, Windows: multiple de 120
                try:
                    if getattr(e, "delta", 0):
                        _c.yview_scroll(int(-1 * (e.delta / 120 if abs(e.delta) >= 120 else e.delta)), "units")
                    elif getattr(e, "num", None) == 4:
                        _c.yview_scroll(-1, "units")
                    elif getattr(e, "num", None) == 5:
                        _c.yview_scroll(1, "units")
                except Exception:
                    pass

            inner.bind("<Configure>", _on_inner_configure)
            sc_canvas.bind("<Configure>", _on_sc_configure)
            # Molette : lier au canvas de scroll et à l'inner
            for w in (sc_canvas, inner):
                w.bind("<MouseWheel>", _on_mousewheel)
                w.bind("<Button-4>", _on_mousewheel)
                w.bind("<Button-5>", _on_mousewheel)

            # Mémoriser pour rebind molette sur les enfants plus tard
            frame._scroll_canvas = sc_canvas
            frame._scroll_inner = inner

            return cv, inner, None

        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)

        inner = tk.Frame(frame, bg=self.BG2)
        inner.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 1))
        inner.columnconfigure(0, weight=1)

        # Explication dynamique — sous le canvas
        exp_fr = tk.Frame(frame, bg=self.BG)
        exp_fr.grid(row=2, column=0, sticky="ew", padx=8, pady=(0,2))
        exp_fr.pack_propagate(False)
        exp_fr.configure(height=38)
        exp_lbl = tk.Label(exp_fr, text=tr("Survolez un curseur."),
            bg=self.BG, fg=self.FG3, font=("TkFixedFont", 9),
            wraplength=860, justify="left", anchor="w")
        exp_lbl.pack(fill="both", expand=True, padx=4, pady=3)

        return cv, inner, exp_lbl

    # ── Helper : ajouter un groupe + curseurs ─────────────────────────
    def _add_group(self, parent, title, sliders, exp_lbl, fs=lambda x:x,
                   inline_hint=False, row_hints=None):
        """
        Chaque ligne = [bloc gauche: curseur + explication collée] | [vignette]
        L'explication est DANS le bloc gauche, juste sous le curseur,
        pour ne pas être poussée par la hauteur de la vignette.
        """
        if row_hints is None:
            row_hints = {}
        grp = tk.LabelFrame(parent, text=title,
            bg=self.BG3, fg=self.FG2,
            font=("TkFixedFont", fs(10), "bold"),
            padx=3, pady=1)
        grp.pack(fill="x", padx=3, pady=(1, 0))
        grp.columnconfigure(0, weight=1)
        grp.columnconfigure(1, weight=0)

        for row_i, (key, label, vmin, vmax, step, typ, hint, values) \
                in enumerate(sliders):

            # Bloc gauche : label + contrôle + valeur + explication collée
            left = tk.Frame(grp, bg=self.BG3)
            left.grid(row=row_i, column=0, sticky="ew", padx=(0, 4), pady=(2, 2))
            left.columnconfigure(1, weight=1)

            tk.Label(left, text=label, bg=self.BG3, fg=self.FG,
                font=("TkFixedFont", fs(10)), width=16,
                anchor="e").grid(row=0, column=0, padx=(2, 4), sticky="e")

            val_lbl = tk.Label(left, text="—", bg=self.BG3,
                fg=self.ACC, font=("TkFixedFont", fs(10), "bold"),
                width=7)
            val_lbl.grid(row=0, column=2, padx=2, sticky="w")

            if values:
                var = tk.StringVar()
                self._vars[key] = var
                cb = ttk.Combobox(left, values=values,
                    textvariable=var, state="readonly", width=12)
                cb.grid(row=0, column=1, padx=2, sticky="ew")
                val_lbl.config(textvariable=var)
                if exp_lbl is not None:
                    def _cb_hint(e, h=hint, lbl=exp_lbl):
                        lbl.config(text=h)
                    cb.bind("<<ComboboxSelected>>", _cb_hint)
                    cb.bind("<Enter>",
                        lambda e, h=hint, lbl=exp_lbl: lbl.config(text=h))
                def _cb_redraw(_e=None):
                    try:
                        self.after_idle(self._redraw_all)
                    except Exception:
                        pass
                cb.bind("<<ComboboxSelected>>", _cb_redraw, add="+")
            else:
                if typ == int:
                    var = tk.IntVar()
                else:
                    var = tk.DoubleVar()
                self._vars[key] = var

                def _make_cb(lbl, k, t):
                    def cb(*_):
                        v = self._vars[k].get()
                        lbl.config(text=str(v) if t == int
                            else f"{v:.3f}".rstrip('0').rstrip('.'))
                    return cb

                var.trace_add("write", _make_cb(val_lbl, key, typ))
                def _redraw_hint(*_a, _k=key):
                    try:
                        self.after_idle(self._redraw_all)
                    except Exception:
                        pass
                try:
                    var.trace_add("write", _redraw_hint)
                except Exception:
                    pass

                sl = tk.Scale(left,
                    from_=vmin, to=vmax, resolution=step,
                    orient=HORIZONTAL, variable=var,
                    bg=self.BG3, fg=self.FG,
                    troughcolor=self.TROUGH,
                    highlightthickness=0, showvalue=False,
                    length=320)
                sl.grid(row=0, column=1, padx=2, sticky="ew")
                if exp_lbl is not None:
                    sl.bind("<Enter>",
                        lambda e, h=hint, lbl=exp_lbl: lbl.config(text=h))

            # Explication collée sous le curseur + ligne vide avant le suivant
            # (même aération que l'onglet Mesh 3D, tous onglets)
            if inline_hint:
                one = " ".join(str(hint).split())
                tk.Label(left, text=one, bg=self.BG3, fg=self.FG,
                    font=("TkFixedFont", fs(9)),
                    justify="left", anchor="w"
                    ).grid(row=1, column=0, columnspan=3,
                    padx=(4, 2), pady=(1, 0), sticky="w")
                # Ligne vierge sous l'explication
                tk.Frame(left, bg=self.BG3, height=8).grid(
                    row=2, column=0, columnspan=3, sticky="ew")

            # Vignette à droite
            if key in row_hints:
                ck = row_hints[key]
                cnv = tk.Canvas(grp, bg="#0a140a", highlightthickness=1,
                    highlightbackground="#3a5a40", width=190, height=84)
                cnv.grid(row=row_i, column=1, padx=(20, 4), pady=2, sticky="ne")
                self._canvases[ck] = cnv

    # ══════════════════════════════════════════════════════════════════
    # ONGLET 1 — MER, CÔTE & MASQUES (fusionné)
    # ══════════════════════════════════════════════════════════════════
        # Molette active aussi sur les curseurs (petit moniteur)
        try:
            top = parent
            while top is not None:
                sc = getattr(top, "_scroll_canvas", None)
                if sc is not None:
                    self._bind_mousewheel_tree(grp, sc)
                    break
                top = getattr(top, "master", None)
        except Exception:
            pass

    def _tab_mer_cote(self, nb, fs):
        cv, inner, exp_lbl = self._make_tab(nb, tr("🌊 Mer & Côte"), inline=True)
        self._canvases["mer"] = cv
        self._canvases["cote"] = cv  # même canvas partagé

        # ── Groupe 1 : Eau & Transparence ──────────────────────────
        sliders_eau = [
            ("ratio_water",    "ratio_water",    0, 1,    0.01, float,
             tr('ratio_water : 0 = JPG satellite opaque sur mer. 1 = eau XP12 entièrement visible (vagues, reflets, bathymétrie). Recommandé : 0.10 pour Vendée/Atlantique.'), None),
            ("ratio_bathy",    "ratio_bathy",    0, 1,    0.05, float,
             tr('ratio_bathy : dégradé de profondeur XP12. 0 = mer uniforme. 1 = eau profonde sombre → turquoise côtier (recommandé).'), None),
            ("water_tech",     "water_tech",     0, 0,    1,    str,
             tr('water_tech : XP12 = eau dynamique (vagues, reflets, bathymétrie). ⚠ XP11+bathy = ancien mode, incompatible avec imprint_masks_to_dds=True.'),
             ["XP12", "XP11+bathy"]),
            ("overlay_lod",    "overlay_lod (m)",5000,50000,1000,float,
             tr("overlay_lod : distance en mètres jusqu'où XPlane affiche l'imagerie sur la mer. 30000 = recommandé."), None),
            ("water_smoothing","water_smoothing",0, 5,    1,    int,
             tr('water_smoothing : lissage du maillage eau intérieure. 2 = recommandé.'), None),
        ]
        self._add_group(inner, tr("Eau & Transparence"), sliders_eau, exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "ratio_bathy": "mer_hint_bathy",
                            "overlay_lod": "mer_hint_lod",
                            "water_smoothing": "mer_hint_smooth",
                        })

        # ── Groupe 2 : Masques côtiers ──────────────────────────────
        sliders_cote = [
            ("masks_width",    "masks_width (m)", 50,8000,50,  int,
             tr('masks_width : largeur en mètres de la zone de dégradé côtier. 100m = transition nette (recommandé). 500m = dégradé naturel. ⚠ Valeurs > 500m peuvent produire des jointures visibles.'), None),
            ("mask_zl",        "mask_zl",        14,20,   1,    int,
             tr('mask_zl : résolution des masques côtiers. 17 = bon équilibre (recommandé). 19-20 = très précis, fichiers lourds.'), None),
            ("masking_mode",   "masking_mode",   0, 0,    1,    str,
             tr('masking_mode : algorithme masque. sand = dégradé naturel (recommandé). rocks = transition abrupte (falaises). 3steps = 3 étapes personnalisées.'),
             ["sand","rocks","3steps"]),
            ("imprint_masks_to_dds","imprint DDS",0,0,   1,    str,
             tr('imprint_masks_to_dds : grave le canal alpha dans le DDS (BC3). True = nécessaire pour transparence XP12 (recommandé). ⚠ False + water_tech=XP12 = jointures visibles.'),
             ["True","False"]),
        ]
        self._add_group(inner, tr("Masques côtiers"), sliders_cote, exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "masks_width": "mer_hint_maskwz",
                        })

        sliders_inland = [
            ("use_masks_for_inland","use_inland", 0, 0, 1, str,
             tr('use_masks_for_inland : applique les masques côtiers sur lacs et rivières. False = recommandé (économise VRAM). True = masque lac visible dans le canvas ci-dessus.'),
             ["False","True"]),
        ]
        self._add_group(inner, tr("Lacs & Rivières"), sliders_inland, exp_lbl, fs,
                        inline_hint=True)

        # ── Compatibilité XP12 : bloquer options incompatibles ──────
        self._setup_xp12_compatibility()

    # ══════════════════════════════════════════════════════════════════
    # ONGLET 3 — TERRAIN & RELIEF
    # ══════════════════════════════════════════════════════════════════
    def _tab_terrain(self, nb, fs):
        """
        Canvas principal + bande d'animations :
          normal_map_strength | terrain_casts_shadows | fill_nodata
        puis curseurs.
        """
        frame = tk.Frame(nb, bg=self.BG2)
        nb.add(frame, text=tr("⛰ Terrain & Relief"))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=0)

        cv_frame = tk.Frame(frame, bg=_CON_BG, relief="flat", bd=1)
        cv_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 2))
        cv = tk.Canvas(cv_frame, bg=_CON_BG, highlightthickness=0, height=220)
        cv.pack(fill="both", expand=True)
        cv.bind("<Configure>", lambda e: self.after(10, self._redraw_all))
        self._canvases["terrain"] = cv

        inner = tk.Frame(frame, bg=self.BG2)
        inner.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 1))
        inner.columnconfigure(0, weight=1)

        exp_fr = tk.Frame(frame, bg=self.BG)
        exp_fr.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 2))
        exp_lbl = tk.Label(exp_fr, text=tr("Survolez un curseur."),
            bg=self.BG, fg=self.FG3, font=("TkFixedFont", 9),
            wraplength=900, justify="left", anchor="w")
        exp_lbl.pack(fill="both", expand=True, padx=4, pady=3)

        sliders = [
            ("normal_map_strength","normal_map",  0, 2,   0.1,  float,
             tr("normal_map_strength : intensité de l'ombrage terrain. 0 = terrain plat visuellement. 1.0 = ombrage exact (recommandé). 2.0 = ombrage très marqué."), None),
            ("terrain_casts_shadows","ombres terrain",0,0,1,str,
             tr('terrain_casts_shadows : le terrain projette des ombres. True = ombres réalistes (recommandé). False = gain perfs, moins réaliste.'),
             ["True","False"]),
            ("use_decal_on_terrain",tr('décals terrain'),0,0,1,str,
             tr('use_decal_on_terrain : décals herbe/roche au sol. True = recommandé.'),
             ["True","False"]),
            ("fill_nodata",    "fill_nodata",    0, 0,    1,    str,
             tr('fill_nodata : comble les trous du DEM par interpolation. True = recommandé si le DEM a des trous.'),
             ["True","False"]),
            ("min_area",       "min_area (°²)",  0.00001,0.01,0.00001,float,
             tr("min_area : surface mini d'un polygone vectoriel. 0.0001 = recommandé."), None),
            ("max_area",       "max_area (°²)",  1,200,  5,    float,
             tr("max_area : surface max d'un polygone. 100 = recommandé."), None),
            ("water_simplification","water_simpl",0,1,  0.05, float,
             tr('water_simplification : 0 (gauche) = rive simplifiée, 1 (droite) = rive très détaillée.'), None),
        ]
        self._add_group(inner, tr("Terrain & Ombrage"), sliders[:3], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "normal_map_strength": "terrain_hint_nm",
                            "terrain_casts_shadows": "terrain_hint_shadow",
                        })
        self._add_group(inner, tr("Altimétrie & Vecteurs"), sliders[3:], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "fill_nodata": "terrain_hint_nodata",
                            "min_area": "terrain_hint_minarea",
                            "max_area": "terrain_hint_maxarea",
                            "water_simplification": "terrain_hint_wsimpl",
                        })

    # ══════════════════════════════════════════════════════════════════
    # ONGLET 4 — MESH 3D
    # ══════════════════════════════════════════════════════════════════
    def _tab_mesh(self, nb, fs):
        """Canvas + curseurs avec mini-animations à droite de chaque option."""
        frame = tk.Frame(nb, bg=self.BG2)
        nb.add(frame, text=tr("🗺 Mesh 3D"))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)

        cv_frame = tk.Frame(frame, bg=_CON_BG, relief="flat", bd=1)
        cv_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 2))
        cv = tk.Canvas(cv_frame, bg=_CON_BG, highlightthickness=0, height=240)
        cv.pack(fill="both", expand=True)
        cv.bind("<Configure>", lambda e: self.after(10, self._redraw_all))
        self._canvases["mesh"] = cv

        inner = tk.Frame(frame, bg=self.BG2)
        inner.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 1))
        inner.columnconfigure(0, weight=1)
        exp_lbl = None

        sliders = [
            ("mesh_zl",        "mesh_zl",        14,20,  1,    int,
             tr('mesh_zl : zoom level du maillage 3D. 14-16 = mesh grossier, relief approximatif. 19 = mesh très précis, côtes et falaises détaillées (recommandé). 20 = très lourd, rarement nécessaire.'), None),
            ("curvature_tol",  "curvature_tol",  30,1,   0.5,  float,
             tr('curvature_tol : à GAUCHE (30) = pentes simplifiées, relief grossier. À DROITE (1) = le mesh épouse mieux les courbes du relief (plus détaillé, plus lourd). 16 = recommandé.'), None),
            ("limit_tris",     "limit_tris (M)", 1,50,   1,    float,
             tr('limit_tris : plafond du nombre de triangles (millions). Gauche = peu de triangles autorisés, maillage incomplet. Droite = assez de triangles pour tout le relief. 15 = recommandé.'), None),
            ("min_angle",      "min_angle (°)",  0.1,2,  0.1,  float,
             tr('min_angle : angle mini des triangles. GAUCHE (0.1°) = triangles très étroits autorisés. DROITE (2°) = triangles plus réguliers seulement. 0.5 = recommandé.'), None),
            ("iterate",        "iterate",        0, 3,   1,    int,
             tr("iterate : passes de raffinement. 0 = une seule passe (rapide). 1-2 = affine côtes/relief. 3 = très long. Chaque cran = une passe de plus."), None),
            ("clean_bad_geometries","clean_geom",0,0,   1,    str,
             tr('clean_bad_geometries : supprime les géométries vectorielles invalides avant la triangulation. True = recommandé.'),
             ["True","False"]),
        ]
        self._add_group(inner, tr("Paramètres Mesh"), sliders[:4], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "curvature_tol": "mesh_hint_curv",
                            "min_angle": "mesh_hint_angle",
                        })
        self._add_group(inner, tr("Qualité & Nettoyage"), sliders[4:], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "iterate": "mesh_hint_iter",
                        })

    # ══════════════════════════════════════════════════════════════════
    # ONGLET 5 — IMAGERIE & AÉROPORTS
    # ══════════════════════════════════════════════════════════════════
    def _tab_imagerie(self, nb, fs):
        cv, inner, exp_lbl = self._make_tab(nb, tr("📷 Imagerie & Aéroports"), canvas_height=280, inline=True)
        self._canvases["imagerie"] = cv

        sliders = [
            ("default_zl",     "default_zl",     14,20,  1,    int,
             tr("default_zl : niveau de zoom de l'imagerie principale. 14-15 = faible résolution, flou. 17 = résolution standard, recommandé. 19-20 = très haute résolution, très lourd en VRAM."), None),
            ("cover_zl",       "cover_zl airports",14,20,1,   int,
             tr('cover_zl : zoom level haute résolution autour des aéroports. 18 = recommandé pour voir les marquages et taxiways.'), None),
            ("cover_extent",   "cover_extent (km)",0,5, 0.5,  float,
             tr('cover_extent : rayon en km autour des aéroports pour la haute résolution. 1.0 = recommandé. 3.0 = large zone haute résolution.'), None),
            ("cover_airports_with_highres","HiRes airports",0,0,1,str,
             tr('cover_airports_with_highres (high_zl_airports) : upgrade le ZL des textures au-dessus des aéroports. False = désactivé. True = tous les aéroports OSM (y compris petits/privés). ICAO = uniquement ceux avec code ICAO (recommandé si beaucoup d’aéroports). Existing = dériver les zones ZL depuis le dossier textures d’une tuile déjà construite. cover_zl / cover_extent s’appliquent quand actif.'),
             ["False","True","ICAO","Existing"]),
            ("apt_smoothing_pix","apt_smooth (px)",0,30, 1,   int,
             tr('apt_smoothing_pix : lissage de la piste dans le mesh. 0 = bosses possibles. 8 = piste plate (recommandé). 30 = très lissé.'), None),
            ("apt_curv_tol",   "apt_curv_tol",   0.5,5, 0.5,  float,
             tr('apt_curv_tol : précision du contour aéroport. Bas = suit bien les virages de piste. Haut = contour simplifié.'), None),
            ("apt_curv_ext",   "apt_curv_ext (km)",0.5,3,0.5, float,
             tr('apt_curv_ext : extension de la zone de précision autour des aéroports. 1.0 = recommandé.'), None),
            ("road_level",     "road_level",     0, 4,   1,    int,
             tr('road_level : densité des routes intégrées dans le mesh. 0 = aucune route. 4 = toutes les routes (recommandé).'), None),
            ("max_levelled_segs","levelled_segs",0,500000,10000,int,
             tr('max_levelled_segs : combien de segments de route peuvent être aplatis. Bas = peu de routes plates. Haut = beaucoup de routes nivelées.'), None),
        ]
        self._add_group(inner, tr("Imagerie"), sliders[:4], exp_lbl, fs,
                        inline_hint=True)
        self._add_group(inner, tr("Aéroports"), sliders[4:7], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "apt_smoothing_pix": "img_hint_smooth",
                            "apt_curv_tol": "img_hint_curv",
                        })
        self._add_group(inner, tr("Routes"), sliders[7:], exp_lbl, fs,
                        inline_hint=True, row_hints={
                            "max_levelled_segs": "img_hint_segs",
                        })


    # ── Forcer redraw de tous les canvas ────────────────────────────
    def _redraw_all(self):
        # Vues procédurales : immédiat
        for fn in (self._draw_mer, self._draw_terrain, self._draw_mesh):
            try:
                fn()
            except Exception:
                pass
        # Vignettes Imagerie (levelled_segs, smooth, curv) : immédiat
        # (sinon le cache de _draw_imagerie bloque l'animation du curseur)
        for fn in (self._draw_img_smooth_hint, self._draw_img_curv_hint,
                   self._draw_img_segs_hint):
            try:
                fn()
            except Exception:
                pass
        # PNG lourds : debounce 60 ms
        if getattr(self, "_png_redraw_after", None):
            try:
                self.after_cancel(self._png_redraw_after)
            except Exception:
                pass
        self._png_redraw_after = self.after(60, self._redraw_png_tabs)

    def _redraw_png_tabs(self):
        self._png_redraw_after = None
        for fn in (self._draw_cote, self._draw_imagerie):
            try:
                fn()
            except Exception:
                pass

    def _anim_loop(self):
        if not self._anim_running:
            return
        self._t += 1
        # Vues procédurales animées + canvas PNG (cote via _draw_mer, imagerie).
        # _draw_cote et _draw_imagerie ont un « early-return » (ne recalculent
        # que si un curseur change) : les mettre ici garantit que TOUT curseur
        # (dont default_zl) est pris en compte en 120 ms, sans clignotement.
        for fn in (self._draw_mer, self._draw_terrain, self._draw_mesh,
                   self._draw_imagerie):
            try:
                fn()
            except Exception:
                pass
        self.after(120, self._anim_loop)  # 120ms au lieu de 80 → plus fluide CPU

    def _cv_size(self, key):
        cv = self._canvases.get(key)
        if not cv:
            return 400, 220
        return max(200, cv.winfo_width()), max(100, cv.winfo_height())

    def _get(self, key, default=0):
        v = self._vars.get(key)
        if v is None:
            return default
        try:
            val = v.get()
            if isinstance(val, str):
                try:
                    return float(val)
                except Exception:
                    return val
            return val
        except Exception:
            return default

    # ── Noyau isométrique partagé ──────────────────────────────────
    def _iso_terrain(self, W, H, params):
        """
        Génère une liste de polygones isométriques représentant le terrain.
        params = dict avec les valeurs des curseurs de l'onglet actif.
        Retourne une liste de (polygon_pts, fill_color, outline_color, outline_w).
        """
        import math, random
        polys = []

        ratio_w  = params.get("ratio_water",  0.1)
        ratio_b  = params.get("ratio_bathy",  1.0)
        mw       = params.get("masks_width",  6144)
        mzl      = params.get("mask_zl",      17)
        ctol     = params.get("curvature_tol",16)
        msh_zl   = params.get("mesh_zl",      19)
        limit_t  = params.get("limit_tris",   15)
        nm       = params.get("normal_map_strength", 1.0)
        shad     = params.get("terrain_casts_shadows", "True")
        dzl      = params.get("default_zl",   17)
        wt       = params.get("water_tech",   "XP12")
        coast_ct = params.get("coast_curv_tol", 1.0)
        wire_on  = params.get("_wire",        False)

        # ── Projection isométrique ────────────────────────────────
        # Grille NX x NY cases, chaque case → quadrilatère projeté
        NX, NY = 22, 14
        ox = W * 0.50   # origine projection
        oy = H * 0.18
        sx = W / (NX + NY) * 1.05   # taille cellule horizontale
        sy = H / (NX + NY) * 0.52   # taille cellule verticale

        def iso(gx, gy, gz=0):
            px = ox + (gx - gy) * sx
            py = oy + (gx + gy) * sy - gz * (H * 0.012)
            return px, py

        # ── Heightmap : montagnes nord + vallée + lac + plaine + mer ─
        rng = random.Random(42)

        def height(gx, gy):
            # Montagnes au nord-ouest
            mx = gx / NX; my = gy / NY
            mtn  = math.exp(-((mx-0.15)**2 + (my-0.20)**2)*18) * 9.5
            mtn += math.exp(-((mx-0.30)**2 + (my-0.10)**2)*22) * 7.0
            mtn += math.exp(-((mx-0.10)**2 + (my-0.35)**2)*14) * 6.0
            # Vallée centrale vers le lac
            valley = -3.5 * math.exp(-((mx-0.48)**2)*8 - ((my-0.55)**2)*6)
            # Lac (dépression)
            lake_d = math.sqrt((mx-0.52)**2 + (my-0.52)**2)
            lake = -4.0 if lake_d < 0.13 else 0.0
            # Plaine côtière → descente vers mer
            plain = -2.5 * max(0, mx - 0.68)
            # Mer (bord droit)
            sea = -5.5 * max(0, mx - 0.80)
            # Crête entre montagnes : relief escarpé
            ridge = math.exp(-((mx-0.22)**2)*30 - ((my-0.30)**2)*50) * 5.0
            # Bruit micro
            noise = (rng.random()-0.5)*0.4
            raw = mtn + valley + lake + plain + sea + ridge + noise
            return raw

        # Influence curvature_tol sur le bruit de la heightmap
        def height_final(gx, gy):
            h = height(gx, gy)
            # curvature_tol haut = terrain lissé, bas = pics acérés
            smooth = max(0.3, 1.0 - (30 - ctol) / 30.0 * 0.6)
            return h * smooth

        # ── Couleur par biome + paramètres ───────────────────────
        def cell_color(gx, gy, h):
            mx = gx / NX; my = gy / NY
            # Lac
            lake_d = math.sqrt((mx-0.52)**2 + (my-0.52)**2)
            if lake_d < 0.13 or h < -3.2:
                # Couleur eau lac = influence ratio_water + ratio_bathy
                r = int(15  + ratio_b*15)
                g = int(90  + ratio_b*60 + ratio_w*30)
                b = int(160 + ratio_b*40 + ratio_w*20)
                return f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"
            # Mer (gx élevé, h très bas)
            if h < -4.0 or mx > 0.84:
                depth = min(1.0, max(0, (-h-4.0)/2.0 + (mx-0.82)/0.2))
                if "XP12" in str(wt):
                    r = int(8  + depth*10 + ratio_b*12)
                    g = int(50 + depth*30 + ratio_b*70)
                    b = int(120+ depth*40 + ratio_b*40)
                else:
                    r = int(40 + depth*10)
                    g = int(70 + depth*20)
                    b = int(110+ depth*30)
                return f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"
            # Plage
            if mx > 0.76 and h > -4.0 and h < 0.5:
                return "#d4b882"
            # Neige sommet (lié à normal_map_strength pour la brillance)
            snow_thr = 7.5 - nm * 1.5
            if h > snow_thr:
                bright = min(255, int(220 + nm*25))
                return f"#{bright:02x}{bright:02x}{min(255,bright+5):02x}"
            # Roche haute
            if h > 5.5:
                return "#8a8070"
            # Forêt (versants)
            if h > 1.5 and my < 0.55:
                g = int(70 + h*8)
                return f"#3a{min(255,g):02x}28"
            # Prairie (plaine)
            if h > 0.2:
                return "#5a8a38"
            # Bocage bas
            return "#4a7228"

        def shadow_factor(gx, gy, h):
            if shad != "True":
                return 1.0
            # Ombrage directionnel depuis nord-ouest
            dh = height_final(max(0,gx-1), max(0,gy-1)) - h
            return max(0.55, 1.0 - max(0, dh)*0.09)

        # ── Génération des polygones (arrière → avant) ────────────
        for gy in range(NY-1, -1, -1):
            for gx in range(NX-1, -1, -1):
                h00 = height_final(gx,   gy  )
                h10 = height_final(gx+1, gy  )
                h01 = height_final(gx,   gy+1)
                h11 = height_final(gx+1, gy+1)
                hm  = (h00+h10+h01+h11)/4

                p00 = iso(gx,   gy,   h00)
                p10 = iso(gx+1, gy,   h10)
                p11 = iso(gx+1, gy+1, h11)
                p01 = iso(gx,   gy+1, h01)

                fill = cell_color(gx+0.5, gy+0.5, hm)
                sf   = shadow_factor(gx, gy, hm)

                # Assombrir selon shadow
                if sf < 0.99:
                    r = int(int(fill[1:3],16)*sf)
                    g = int(int(fill[3:5],16)*sf)
                    b = int(int(fill[5:7],16)*sf)
                    fill = f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"

                pts = [p00[0],p00[1], p10[0],p10[1],
                       p11[0],p11[1], p01[0],p01[1]]

                # Maillage visible si wire_on
                if wire_on:
                    ow = 0.5; oc = "#00ff88"
                else:
                    ow = 0; oc = ""

                polys.append((pts, fill, oc, ow))

        return polys

    def _iso_draw(self, cv, W, H, params, t=0, extra_fn=None):
        """Dessine les polygones isométriques sur le canvas."""
        polys = self._iso_terrain(W, H, params)
        for pts, fill, oc, ow in polys:
            if ow > 0:
                cv.create_polygon(pts, fill=fill, outline=oc, width=ow)
            else:
                cv.create_polygon(pts, fill=fill, outline="")
        if extra_fn:
            extra_fn(cv, W, H, params, t)

    # ── Canvas MER ────────────────────────────────────────────────
    def _draw_mer(self):
        cv = self._canvases.get("mer")
        if not cv or not cv.winfo_exists():
            return
        W, H = self._cv_size("mer")
        if W < 10 or H < 10:
            return
        # Le canvas Mer & Côte affiche la VRAIE photo satellite (PNG terre/mer)
        # via _draw_cote — plus de dôme dessiné par le code. _draw_cote est mis
        # en cache (ne recalcule que si un curseur change) : léger dans la boucle.
        try:
            self._draw_cote()
        except Exception:
            pass

        # Vignettes animées de l'onglet Mer (chacune protégée)
        for _hfn in (self._draw_bathy_hint, self._draw_lod_hint,
                     self._draw_smooth_hint, self._draw_maskwz_hint):
            try:
                _hfn()
            except Exception:
                pass

    # ── Canvas CÔTE ────────────────────────────────────────────────
    def _draw_cote(self):
        """
        Canvas Côte & Masques — superposition PNG Mer_Cotes (noir=transparent).
        Cache final PhotoImage : ne recalcule que si curseurs/taille changent.
        """
        cv = self._canvases.get("cote")
        if not cv or not cv.winfo_exists():
            return
        W, H = self._cv_size("cote")
        if W < 10 or H < 10:
            return

        try:
            from PIL import Image as _PIL, ImageTk as _ITK

            rw  = float(self._get("ratio_water",         0.1))
            mw  = float(self._get("masks_width",         100))
            mzl = int(self._get("mask_zl",               17))
            mm  = str(self._get("masking_mode",          "sand"))
            uml = str(self._get("use_masks_for_inland",  "False"))
            imp = str(self._get("imprint_masks_to_dds",  "True"))
            wt  = str(self._get("water_tech",            "XP12"))

            # Clé de cache final (paramètres + taille)
            ck = (W, H, round(rw, 3), int(mw), mzl, mm, uml, imp, wt)
            if not hasattr(self, "_cote_final"):
                self._cote_final = {}
            if not hasattr(self, "_cote_cache"):
                self._cote_cache = {}
            if not hasattr(self, "_cote_last_ck"):
                self._cote_last_ck = None

            # Si rien n'a changé → ne rien faire (garde le canvas)
            if self._cote_last_ck == ck and cv.find_all():
                return

            if ck in self._cote_final:
                photo, meta = self._cote_final[ck]
                cv.delete("all")
                cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._pk_cote = photo
                self._cote_draw_overlays(cv, W, H, mw, imp, wt, meta)
                self._cote_last_ck = ck
                return

            # ── Composition (une seule fois par jeu de params) ──
            base = _PIL.new("RGBA", (W, H), (20, 40, 50, 255))

            img_f = _sim_load_full("fond", W, H, self._cote_cache)
            base = _PIL.alpha_composite(base, img_f)

            if rw > 0.01:
                img_m = _sim_load_full("mer", W, H, self._cote_cache)
                if rw < 0.99:
                    # Ne pas modifier le cache : travailler sur une copie
                    img_m = img_m.copy()
                    a = img_m.split()[3]
                    a = a.point(lambda p, r=rw: int(p * max(0.0, min(1.0, r))))
                    img_m.putalpha(a)
                base = _PIL.alpha_composite(base, img_m)

            img_t = _sim_load_full("terre", W, H, self._cote_cache)
            base = _PIL.alpha_composite(base, img_t)

            if uml == "True":
                img_l = _sim_load_full("lac", W, H, self._cote_cache)
                base = _PIL.alpha_composite(base, img_l)

            # Dégradé jointure — étirement vertical selon masks_width
            # mw 50→ band fine, mw 8000→ band large
            band_frac = max(0.04, min(0.55, (mw / 8000.0) * 0.50 + 0.04))
            band_h = max(4, int(H * band_frac))
            # Zone côte ~ 55% hauteur (comme l'ancien split)
            coast_y = int(H * 0.48)
            y0 = max(0, coast_y - band_h // 2)
            y1 = min(H, y0 + band_h)

            deg = _sim_load_full("degrade", W, max(8, band_h), self._cote_cache)
            # Coller le dégradé dans une couche pleine taille
            layer = _PIL.new("RGBA", (W, H), (0, 0, 0, 0))
            # Centrer verticalement sur coast_y
            paste_y = max(0, coast_y - deg.size[1] // 2)
            layer.paste(deg, (0, paste_y), deg)
            base = _PIL.alpha_composite(base, layer)

            rgb = base.convert("RGB")
            photo = _ITK.PhotoImage(rgb)
            meta = {"band_h": band_h, "coast_y": coast_y, "y0": y0, "y1": y1}

            # Limiter le cache final (max 12 entrées)
            if len(self._cote_final) > 12:
                self._cote_final.clear()
            self._cote_final[ck] = (photo, meta)

            cv.delete("all")
            cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")
            cv.create_image(0, 0, anchor="nw", image=photo)
            cv._pk_cote = photo
            self._cote_draw_overlays(cv, W, H, mw, imp, wt, meta)
            self._cote_last_ck = ck

        except Exception:
            try:
                cv.delete("all")
                cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
                cv.create_text(W // 2, H // 2,
                    text=tr("Images Mer_Cotes introuvables\nPlacez les PNG dans images/Mer_Cotes/"),
                    fill="#ffaa66", font=("TkFixedFont", 10), justify="center")
            except Exception:
                pass

    def _cote_draw_overlays(self, cv, W, H, mw, imp, wt, meta):
        """Textes, flèches, lignes — légers, redessinés à chaque affichage cache."""
        SPLIT = meta.get("coast_y", int(H * 0.48))
        y_top = meta.get("y0", SPLIT - 10)
        y_bot = meta.get("y1", SPLIT + 10)

        cv.create_line(0, y_top, W, y_top, fill="#ffe066", width=1, dash=(4, 3))
        cv.create_line(0, y_bot, W, y_bot, fill="#ffe066", width=1, dash=(4, 3))
        cv.create_line(0, SPLIT, W, SPLIT, fill="#ffffff", width=1)

        ax = W - 28
        cv.create_line(ax, y_top, ax, y_bot, fill="#ffe066", width=2)
        cv.create_line(ax - 5, y_top, ax + 5, y_top, fill="#ffe066", width=2)
        cv.create_line(ax - 5, y_bot, ax + 5, y_bot, fill="#ffe066", width=2)
        mid_y = (y_top + y_bot) // 2
        cv.create_rectangle(ax - 52, mid_y - 10, ax - 4, mid_y + 10,
            fill="#0a140a", outline="#ffe066")
        cv.create_text(ax - 28, mid_y,
            text=f"{int(mw)} m", fill="#ffe066",
            font=("TkFixedFont", 9, "bold"))

        cv.create_text(W // 2, max(14, int(H * 0.22)),
                       text=tr("TERRE"),
                       fill="#ccffcc", font=("TkFixedFont", 9, "bold"))
        cv.create_text(W // 2, min(H - 22, int(H * 0.72)),
                       text=(tr("MER (BC3)") if imp == "True" else tr("MER (BC1)")),
                       fill="#88ddff", font=("TkFixedFont", 9, "bold"))
        cv.create_text(12, max(y_top + 2, SPLIT - 8),
                       text=tr("zone masque / dégradé"),
                       fill="#ffe066", font=("TkFixedFont", 8), anchor="sw")

        warn = []
        if imp != "True" and wt == "XP12":
            warn.append(tr("imprint=False + XP12 → jointures possibles"))
        if mw > 800:
            warn.append(tr("masque très large — jointures parfois visibles"))
        if "XP11" in wt:
            warn.append(tr("XP11+bathy : vagues XP12 désactivées"))
        if warn:
            msg = "  ·  ".join(warn)
            cv.create_text(W // 2, H - 8, text=msg,
                           fill="#ffaa66", font=("TkFixedFont", 8))


    def _draw_bathy_hint(self):
        """
        ratio_bathy — coupe de plage qui descend sous l'eau :
        le sable forme une pente ; la couleur de l'eau suit cette pente
        (clair près de la plage → sombre au large si ratio élevé).
        """
        cv = self._canvases.get("mer_hint_bathy")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        rb = float(self._get("ratio_bathy", 1.0))
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")

        # Surface libre de l'eau (ligne horizontale)
        y_water = int(H * 0.32)
        y_bottom = H - 16

        # Pente de plage : haut à gauche → bas à droite (sous l'eau)
        # Point haut (hors eau / laisse)
        x0, y0 = 4, int(H * 0.22)
        # Point bas (sous l'eau, vers le large)
        x1, y1 = int(W * 0.55), int(H * 0.78)
        # Fin du fond à droite
        x2, y2 = W - 4, y_bottom

        def beach_y_at(x):
            """Altitude du fond (sable) à l'abscisse x."""
            if x <= x0:
                return y0
            if x >= x1:
                # après la plage : fond plus plat / profond
                t = (x - x1) / max(1, x2 - x1)
                return int(y1 + (y2 - y1) * t)
            t = (x - x0) / max(1, x1 - x0)
            return int(y0 + (y1 - y0) * t)

        # Eau : bandes verticales sous la surface, au-dessus du fond
        n = 28
        shallow = (40, 210, 190)   # turquoise côtier
        deep = (8, 35, 85)         # bleu profond
        for i in range(n):
            f = i / max(1, n - 1)          # 0 côte → 1 large
            x_a = int(4 + f * (W - 8))
            x_b = int(4 + (i + 1) / n * (W - 8))
            y_bed = beach_y_at((x_a + x_b) // 2)
            # Couleur selon distance côte × ratio_bathy
            d = f * rb
            r = int(shallow[0] + (deep[0] - shallow[0]) * d)
            g = int(shallow[1] + (deep[1] - shallow[1]) * d)
            b = int(shallow[2] + (deep[2] - shallow[2]) * d)
            # Colonne d'eau : de la surface jusqu'au fond (pente)
            top = max(y_water, 2)
            bot = max(top + 1, y_bed)
            cv.create_rectangle(x_a, top, x_b + 1, bot,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

        # Polygone sable : pente qui plonge sous l'eau
        sand_pts = [
            0, y_bottom,
            0, y0,
            x0, y0,
        ]
        steps = 16
        for i in range(steps + 1):
            t = i / steps
            x = int(x0 + (x1 - x0) * t)
            sand_pts.extend([x, beach_y_at(x)])
        sand_pts.extend([x2, y2, W, y_bottom])
        cv.create_polygon(sand_pts, fill="#c2b280", outline="")
        # Ligne de pente bien visible
        slope_line = []
        for i in range(20):
            t = i / 19
            x = int(x0 + (x1 - x0) * t)
            slope_line.extend([x, beach_y_at(x)])
        cv.create_line(slope_line, fill="#8a7340", width=2)

        # Surface de l'eau
        cv.create_line(0, y_water, W, y_water, fill="#bfffe8", width=1, dash=(3, 2))
        cv.create_text(W - 6, y_water - 2, text=tr("surface"),
            fill="#a6e3a1", font=("TkFixedFont", 7), anchor="se")
        cv.create_text(8, y0 - 2, text=tr("plage"),
            fill="#e8d8a0", font=("TkFixedFont", 7), anchor="sw")

        # Flèche
        cv.create_line(int(W * 0.35), 10, W - 12, 10, fill="#a6e3a1",
            width=1, arrow="last")
        cv.create_text(W // 2, 10, text=tr("côte → large"),
            fill="#a6e3a1", font=("TkFixedFont", 7), anchor="n")

        if rb < 0.2:
            msg, col = tr("même couleur partout"), "#ffe066"
        elif rb < 0.6:
            msg, col = tr("un peu plus sombre au large"), "#88ccff"
        else:
            msg, col = tr("profond sombre / côte claire"), "#66ff99"
        cv.create_rectangle(0, H - 15, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 8, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))

    def _draw_lod_hint(self):
        """
        overlay_lod — fondu PLEIN CADRE photo satellite ↔ mer XP.

        GAUCHE : photo (fond marin.png) couvre TOUTE la vignette.
        CENTRE : fondu progressif photo ↔ mer XP sur toute la surface.
        DROITE : uniquement mer XP (plus de photo), plein cadre.

        Chemin universel : images/Mer_Cotes/fond marin.png
        """
        cv = self._canvases.get("mer_hint_lod")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        lod = float(self._get("overlay_lod", 30000))
        # 0 = gauche, 1 = droite
        fr = max(0.0, min(1.0, (lod - 5000.0) / 45000.0))
        # photo pleine à gauche → invisible à droite
        photo_a = 1.0 - fr

        cv.delete("all")

        try:
            from PIL import Image as _PIL, ImageTk as _ITK, ImageDraw as _ID
            import math

            if not hasattr(self, "_lod_cache"):
                self._lod_cache = {}

            ck = (W, H, round(photo_a, 2))
            if getattr(self, "_lod_photo_ck", None) == ck and getattr(cv, "_pk_lod", None):
                pass  # réutilise cv._pk_lod
            else:
                # ── Mer XP plein cadre (bleu) ──
                xp = _PIL.new("RGBA", (W, H), (0, 0, 0, 255))
                dr = _ID.Draw(xp)
                for y in range(H):
                    k = y / max(1, H - 1)
                    rr = int(15 + 25 * k)
                    gg = int(55 + 60 * k)
                    bb = int(110 + 100 * k)
                    dr.line([(0, y), (W, y)], fill=(rr, gg, bb, 255))
                for i in range(0, W, 7):
                    yy = int(H * 0.45 + 6 * math.sin(i * 0.2))
                    dr.ellipse([i, yy, i + 5, yy + 3],
                               fill=(170, 215, 255, 140))

                # ── Photo satellite : crop de la zone NON noire, étirée plein cadre ──
                raw = _sim_load_full("fond", 400, 300, self._lod_cache,
                                     make_black_transparent=False)
                if raw.mode != "RGBA":
                    raw = raw.convert("RGBA")
                # Trouver la bande utile (pas le noir du haut)
                px = raw.load()
                w0, h0 = raw.size
                y0 = 0
                for y in range(h0):
                    # ligne non noire si assez de pixels clairs
                    n_lit = 0
                    for x in range(0, w0, 4):
                        r, g, b, a = px[x, y]
                        if r + g + b > 40:
                            n_lit += 1
                    if n_lit > w0 // 20:
                        y0 = y
                        break
                cropped = raw.crop((0, y0, w0, h0))
                photo = cropped.resize((W, H), _PIL.LANCZOS).convert("RGBA")
                # Opacité globale selon curseur
                alpha = photo.split()[3].point(
                    lambda p, r=photo_a: int(p * max(0.0, min(1.0, r))))
                photo.putalpha(alpha)

                # Composite : XP en dessous, photo par-dessus
                base = _PIL.alpha_composite(xp, photo)
                cv._pk_lod = _ITK.PhotoImage(base.convert("RGB"))
                self._lod_photo_ck = ck

            cv.create_image(0, 0, anchor="nw", image=cv._pk_lod)

        except Exception:
            # Fallback rectangles
            cv.create_rectangle(0, 0, W, H, fill="#0d2b5c", outline="")
            if photo_a > 0.05:
                # approximation verte/grise de la photo
                shade = int(40 + 50 * photo_a)
                cv.create_rectangle(0, 0, W, H,
                    fill=f"#{shade:02x}{shade+20:02x}{shade+10:02x}", outline="")

        cv.create_text(8, 10, text=tr("photo sat."),
                       fill="#c8ffc8", font=("TkFixedFont", 7), anchor="nw")
        cv.create_text(W - 8, 10, text=tr("mer XP"),
                       fill="#aaccff", font=("TkFixedFont", 7), anchor="ne")
        cv.create_text(W // 2, 10, text=f"{lod / 1000:.0f} km",
                       fill="#ffdd44", font=("TkFixedFont", 9, "bold"))

        if fr < 0.33:
            msg, col = tr("photo recouvre toute la mer XP"), "#88ff88"
        elif fr < 0.66:
            msg, col = tr("fondu photo ↔ mer XP"), "#ffe066"
        else:
            msg, col = tr("mer XP seule — plus de photo"), "#88ccff"
        cv.create_rectangle(0, H - 16, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 8, text=msg, fill=col,
                       font=("TkFixedFont", 8, "bold"))


    def _draw_smooth_hint(self):
        """
        water_smoothing — bord d'un lac :
        0 = dents de scie ; élevé = rivage arrondi.
        """
        import math, random
        cv = self._canvases.get("mer_hint_smooth")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        sm = int(float(self._get("water_smoothing", 2)))
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")

        pad = 8
        x0, y0 = pad, 14
        bw, bh = W - 2 * pad, H - 28
        midy = y0 + bh // 2
        frac = max(0.0, min(1.0, sm / 5.0))

        rnd = random.Random(1234)
        npts = 20
        jag = [rnd.uniform(-1, 1) for _ in range(npts)]
        pts = []
        for i in range(npts):
            f = i / (npts - 1)
            x = x0 + int(f * bw)
            jagged = jag[i] * bh * 0.32
            smoothv = math.sin(f * math.pi * 1.2) * bh * 0.08
            yy = midy + jagged * (1 - frac) + smoothv * frac
            pts.extend([x, yy])

        # Terre au-dessus, eau en dessous
        cv.create_polygon([x0, y0] + pts + [x0 + bw, y0],
            fill="#2a5a32", outline="")
        cv.create_polygon([x0, y0 + bh] + pts + [x0 + bw, y0 + bh],
            fill="#1a5080", outline="")
        cv.create_line(pts, fill="#ffe066", width=2, smooth=(frac > 0.35))

        cv.create_text(x0 + 4, y0 + 6, text=tr("terre"),
            fill="#c8e8c8", font=("TkFixedFont", 7), anchor="w")
        cv.create_text(x0 + 4, y0 + bh - 6, text=tr("lac"),
            fill="#c8d8ff", font=("TkFixedFont", 7), anchor="w")

        if sm == 0:
            msg, col = tr("rivage en dents de scie"), "#ff8866"
        elif sm <= 2:
            msg, col = tr("rivage naturel (reco)"), "#66ff99"
        else:
            msg, col = tr("rivage très arrondi"), "#88ccff"
        cv.create_text(W // 2, H - 8, text=f"×{sm} — " + msg, fill=col,
            font=("TkFixedFont", 8, "bold"))

    def _draw_maskwz_hint(self):
        """
        masks_width × mask_zl — coupe côte :
        bande jaune = largeur du masque ; cases = finesse (mask_zl).
        """
        import math
        cv = self._canvases.get("mer_hint_maskwz")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        mw = float(self._get("masks_width", 100))
        mzl = int(float(self._get("mask_zl", 17)))
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")

        pad = 6
        x0, y0 = pad, 16
        bw, bh = W - 2 * pad, H - 28

        # Largeur bande (masks_width)
        bwf = max(0.10, min(0.70, (mw - 50) / 2500.0 * 0.60 + 0.10))
        band_h = max(8, int(bh * bwf))
        land_h = max(6, int((bh - band_h) * 0.4))
        sea_h = bh - land_h - band_h
        sea_y0 = y0 + land_h + band_h

        # Terre / mer
        cv.create_rectangle(x0, y0, x0 + bw, y0 + land_h,
            fill="#2a5a32", outline="")
        cv.create_rectangle(x0, sea_y0, x0 + bw, y0 + bh,
            fill="#123a5c", outline="")
        cv.create_text(x0 + 4, y0 + 2, text=tr("terre"),
            fill="#c8e8c8", font=("TkFixedFont", 7), anchor="nw")
        cv.create_text(x0 + 4, y0 + bh - 2, text=tr("mer"),
            fill="#c8d8ff", font=("TkFixedFont", 7), anchor="sw")

        # Bande masque en cases (mask_zl = taille des pixels)
        cell = max(3, int(18 - (mzl - 14) * 2.2))
        ncols = max(1, bw // cell)
        nrows = max(1, band_h // max(1, cell))
        for r in range(nrows + 1):
            for c in range(ncols + 1):
                cx = x0 + c * cell
                cy = y0 + land_h + r * cell
                f = r / max(1, nrows)
                # dégradé jaune → bleu dans la bande
                rr = int(255 - 180 * f)
                gg = int(220 - 100 * f)
                bb = int(80 + 80 * f)
                cv.create_rectangle(cx, cy,
                    min(cx + cell - 1, x0 + bw),
                    min(cy + cell - 1, sea_y0),
                    fill=f"#{rr:02x}{gg:02x}{bb:02x}", outline="#0a140a")

        # Flèche épaisseur
        ax = x0 + bw - 10
        cv.create_line(ax, y0 + land_h, ax, sea_y0, fill="#ffe066", width=1,
            arrow="both")
        cv.create_text(W // 2, 8,
            text=tr("largeur masque") + f" {int(mw)} m · ZL{mzl}",
            fill="#ffdd44", font=("TkFixedFont", 8, "bold"))

        if mw > 1200:
            msg, col = tr("transition très large"), "#ff8866"
        elif cell >= 12:
            msg, col = tr("pixels masque gros"), "#ffe066"
        else:
            msg, col = tr("transition fine"), "#66ff99"
        cv.create_text(W // 2, H - 8, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))

    def _setup_xp12_compatibility(self):
        """Bloque les options incompatibles avec XP12 en temps réel."""
        def _check(*_):
            wt  = str(self._get("water_tech", "XP12"))
            imp = str(self._get("imprint_masks_to_dds", "True"))
            # XP11+bathy + imprint=True → incompatible
            if "XP11" in wt and imp == "True":
                if "imprint_masks_to_dds" in self._vars:
                    self._vars["imprint_masks_to_dds"].set("False")
            # Mettre à jour le canvas côte
            if hasattr(self, "_draw_cote"):
                self._draw_cote()
        # Surveiller water_tech et imprint_masks_to_dds
        for key in ["water_tech", "imprint_masks_to_dds", "masks_width", "mask_zl", "masking_mode"]:
            if key in self._vars:
                self._vars[key].trace_add("write", _check)

        # ── Canvas TERRAIN ─────────────────────────────────────────────
    def _terrain_photo_base(self, W, H):
        """Paysage réaliste (même images que Mesh 3D), redimensionné."""
        sharp = self._mesh_pil("mesh_sharp.png", (W, H)) if hasattr(self, "_mesh_pil") else None
        soft = self._mesh_pil("mesh_soft.png", (W, H)) if hasattr(self, "_mesh_pil") else None
        img = sharp or soft
        if img is None:
            return None
        return img.copy()

    def _draw_nm_hint(self):
        """
        normal_map_strength sur photo réelle :
        bas = image délavée / plat ; haut = contraste d'ombres marqué.
        """
        cv = self._canvases.get("terrain_hint_nm")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        nm = float(self._get("normal_map_strength", 1.0))
        t = max(0.0, min(1.0, nm / 2.0))
        cv.delete("all")

        base = self._terrain_photo_base(W, H)
        if base is not None:
            try:
                from PIL import ImageEnhance, ImageTk, ImageDraw
                # Contraste / luminosité liés à normal_map
                # t=0 → plat (faible contraste) ; t=1 → relief marqué
                contrast = 0.45 + 1.35 * t
                img = ImageEnhance.Contrast(base.convert("RGB")).enhance(contrast)
                # Assombrir légèrement les zones déjà sombres si t haut
                if t > 0.3:
                    img = ImageEnhance.Sharpness(img).enhance(0.8 + t)
                # Petit soleil en overlay
                draw = ImageDraw.Draw(img, "RGBA") if False else None
                photo = ImageTk.PhotoImage(img)
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._nm_photo = photo
                # Soleil (canvas)
                cv.create_oval(10, 8, 28, 26, fill="#ffe066", outline="#fff8aa")
                cv.create_text(32, 16, text="☀", fill="#ffe066",
                    font=("TkFixedFont", 10), anchor="w")
            except Exception:
                base = None
        if base is None:
            cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
            cv.create_text(W//2, H//2, text=tr("image paysage absente"),
                fill="#a6e3a1", font=("TkFixedFont", 9))

        if t < 0.25:
            msg, col = tr("plat — peu d'ombrage"), "#ffe066"
        elif t < 0.6:
            msg, col = tr("ombrage normal"), "#88ccff"
        else:
            msg, col = tr("relief marqué — ombres fortes"), "#66ff99"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))

    def _draw_shadow_hint(self):
        """
        terrain_casts_shadows (True/False) sur photo :
        True  = ombres allongées bien visibles sous les reliefs
        False = aucune ombre, image « plate »
        """
        cv = self._canvases.get("terrain_hint_shadow")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        on = str(self._get("terrain_casts_shadows", "True")) == "True"
        cv.delete("all")

        base = self._terrain_photo_base(W, H)
        if base is not None:
            try:
                from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageEnhance
                img = base.convert("RGBA")
                if on:
                    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    dr = ImageDraw.Draw(shadow)
                    for cx, cy, rw, rh in (
                        (int(W * 0.50), int(H * 0.58), int(W * 0.28), int(H * 0.10)),
                        (int(W * 0.28), int(H * 0.65), int(W * 0.20), int(H * 0.07)),
                        (int(W * 0.72), int(H * 0.50), int(W * 0.18), int(H * 0.06)),
                        (int(W * 0.40), int(H * 0.42), int(W * 0.12), int(H * 0.05)),
                    ):
                        dr.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                                   fill=(0, 0, 0, 130))
                    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
                    img = Image.alpha_composite(img, shadow)
                    # Assombrir un peu le versant
                    img = ImageEnhance.Contrast(img.convert("RGB")).enhance(1.15)
                    img = img.convert("RGBA")
                else:
                    # Aplatir : moins de contraste = « pas d'ombre »
                    img = ImageEnhance.Contrast(img.convert("RGB")).enhance(0.7)
                    img = img.convert("RGBA")
                photo = ImageTk.PhotoImage(img.convert("RGB"))
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._sh_photo = photo
            except Exception:
                base = None
        if base is None:
            cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")

        # Badge True / False bien visible
        if on:
            badge, bcol = "True — " + tr("ombres ON"), "#66ff99"
        else:
            badge, bcol = "False — " + tr("ombres OFF"), "#ff8866"
        cv.create_rectangle(0, H - 20, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 10, text=badge, fill=bcol,
            font=("TkFixedFont", 9, "bold"))
        cv.create_oval(W - 22, 6, W - 8, 20, fill="#ffe066", outline="")

    def _draw_nodata_hint(self):
        """fill_nodata : False = trous sombres dans le relief ; True = comblé."""
        cv = self._canvases.get("terrain_hint_nodata")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        Hc = max(20, H - 18)
        fill = str(self._get("fill_nodata", "True")) == "True"
        ck = (W, H, fill)
        if getattr(self, "_nd_ck", None) == ck and cv.find_all():
            return
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")
        drawn = False
        try:
            from PIL import ImageDraw as _ID, ImageTk as _ITK
            import random as _r, math as _m
            base = self._terrain_photo_base(W, Hc)
            if base is not None:
                img = base.convert("RGB")
                if not fill:
                    # Trous sombres organiques dans le relief (partie basse)
                    dr = _ID.Draw(img, "RGBA")
                    _r.seed(5)
                    for (fx, fy) in [(0.22, 0.55), (0.55, 0.62),
                                     (0.78, 0.50), (0.40, 0.78)]:
                        cx = int(fx * W); cy = int(fy * Hc)
                        rad = _r.randint(max(4, int(W * 0.05)),
                                         max(6, int(W * 0.09)))
                        pts = []
                        for i in range(12):
                            a = 2 * _m.pi * i / 12
                            rr = rad * (1 + _r.uniform(-0.3, 0.3))
                            pts.append((cx + _m.cos(a) * rr,
                                        cy + _m.sin(a) * rr * 0.7))
                        dr.polygon(pts, fill=(8, 8, 10, 235))
                photo = _ITK.PhotoImage(img)
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._nd_photo = photo
                drawn = True
        except Exception:
            drawn = False
        if not drawn:
            cv.create_rectangle(0, 0, W, Hc, fill="#1a2a20", outline="#3a5a40")

        if fill:
            badge, bcol = "True — " + tr("trous comblés"), "#66ff99"
        else:
            badge, bcol = "False — " + tr("trous dans le relief"), "#ff8866"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=badge, fill=bcol,
            font=("TkFixedFont", 8, "bold"))
        self._nd_ck = ck

    def _draw_minarea_hint(self):
        """min_area — fondu entre deux photos :
        gauche = LacNodetaille (peu détaillé) ; droite = Lac (détaillé).
        Fondu bidirectionnel au déplacement du curseur."""
        import math
        cv = self._canvases.get("terrain_hint_minarea")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        Hc = max(20, H - 18)
        try:
            v = float(self._get("min_area", 0.0001))
        except Exception:
            v = 0.0001
        t = max(0.0, min(1.0, (math.log10(max(v, 1e-6)) + 5) / 3.0))
        ck = (W, H, round(t, 2))
        if getattr(self, "_mn_ck", None) == ck and cv.find_all():
            return
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")
        drawn = False
        try:
            from PIL import Image as _P, ImageTk as _ITK
            cache = self.__dict__.setdefault("_vig_cache", {})
            # Deux photos étirées à la même taille (pour le fondu)
            k1 = ("nodet", W, Hc)
            k2 = ("lacdet", W, Hc)
            if k1 in cache:
                nod = cache[k1]
            else:
                # Recherche robuste : n'importe quel fichier contenant
                # « nodetail » (.png ou .jpg) dans Mesh 3D ou Mer_Cotes.
                _p = None
                for _r0 in _sim_images_roots():
                    for _sub in ("Mesh 3D", "Mesh3D", "Mesh_3D", "Mer_Cotes", ""):
                        _d = os.path.join(_r0, _sub) if _sub else _r0
                        if not os.path.isdir(_d):
                            continue
                        try:
                            for _f in os.listdir(_d):
                                _lo = _f.lower()
                                if ("nodetail" in _lo or "nodetaille" in _lo) and \
                                        _lo.endswith((".png", ".jpg", ".jpeg")):
                                    _p = os.path.join(_d, _f)
                                    break
                        except Exception:
                            pass
                        if _p:
                            break
                    if _p:
                        break
                nod = (_P.open(_p).convert("RGB").resize((W, Hc), _P.LANCZOS)
                       if _p else None)
                cache[k1] = nod
            if k2 in cache:
                det = cache[k2]
            else:
                _p = self._mesh_image_path("Lac.png") or _sim_find_png("lac")
                det = (_P.open(_p).convert("RGB").resize((W, Hc), _P.LANCZOS)
                       if _p else None)
                cache[k2] = det

            if nod is not None and det is not None:
                img = _P.blend(nod, det, t)     # t=0 → Nodetaille ; t=1 → Lac
            else:
                img = det or nod
            if img is not None:
                photo = _ITK.PhotoImage(img)
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._mn_photo = photo
                drawn = True
        except Exception:
            drawn = False
        if not drawn:
            cv.create_rectangle(0, 0, W, Hc, fill="#244a32", outline="#3a5a40")

        if t < 0.35:
            msg, col = tr("berge peu détaillée"), "#ff8866"
        elif t > 0.65:
            msg, col = tr("belle berge détaillée"), "#66ff99"
        else:
            msg, col = tr("détail moyen"), "#ffe066"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))
        self._mn_ck = ck

    def _draw_maxarea_hint(self):
        """max_area : un grand lac (vraie photo Lac.png).
        Droite (valeur haute) = lac d'un seul tenant.
        Gauche (valeur basse) = lac cassé en morceaux."""
        cv = self._canvases.get("terrain_hint_maxarea")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        Hc = max(20, H - 18)
        try:
            v = float(self._get("max_area", 100))
        except Exception:
            v = 100
        # t = fragmentation : max_area bas (gauche) → cassé ; haut (droite) → entier
        t = max(0.0, min(1.0, (200 - v) / 199.0))
        ck = (W, H, round(t, 2))
        if getattr(self, "_ma_ck", None) == ck and cv.find_all():
            return  # rien changé → on garde l'affichage (pas de clignotement)

        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")
        drawn = False
        try:
            from PIL import Image as _P, ImageTk as _ITK
            cache = self.__dict__.setdefault("_vig_cache", {})
            # Fond = lac étiré à la taille vignette (pour caler le calque dessus)
            lck = ("lac_stretch", W, Hc)
            lake = cache.get(lck)
            if lake is None:
                _lp = self._mesh_image_path("Lac.png") or _sim_find_png("lac")
                lake = (_P.open(_lp).convert("RGB").resize((W, Hc), _P.LANCZOS)
                        if _lp else _P.new("RGB", (W, Hc), (40, 100, 160)))
                cache[lck] = lake
            img = lake.copy()
            if t >= 0.04:
                # Calque de fissures = LE PNG LacCalque_casse.png, calé sur le
                # lac ; opacité pilotée par le curseur (dissolution).
                cck = ("calque_casse", W, Hc)
                if cck in cache:
                    calque = cache[cck]
                else:
                    _cp = (self._mesh_image_path("LacCalque_casse.png")
                           or _sim_find_png("calque") or _sim_find_png("casse"))
                    calque = (_P.open(_cp).convert("RGBA").resize((W, Hc), _P.LANCZOS)
                              if _cp else None)
                    cache[cck] = calque
                if calque is not None:
                    _r0, _g0, _b0, _al = calque.split()
                    _al = _al.point(lambda p: int(p * t))
                    ov = _P.merge("RGBA", (_r0, _g0, _b0, _al))
                    img = _P.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
                else:
                    # Repli : fissures générées sur l'eau si le PNG est absent
                    import numpy as _np
                    from PIL import ImageDraw as _ID
                    import random as _r
                    ba = _np.asarray(lake).astype(_np.int16)
                    water = ((ba[:, :, 2] > ba[:, :, 0] + 6)
                             & (ba[:, :, 2] > ba[:, :, 1] + 6))
                    ck2 = lake.copy()
                    dr = _ID.Draw(ck2, "RGBA")
                    _r.seed(11)
                    aa = int(70 + 170 * t)
                    for _k in range(6):
                        x = int(W * (0.1 + 0.8 * _r.random())); y = 0
                        pts = [(x, y)]
                        while y < Hc:
                            y += _r.randint(5, 12); x += _r.randint(-11, 11)
                            pts.append((max(0, min(W, x)), min(Hc, y)))
                        dr.line(pts, fill=(6, 8, 12, aa), width=2)
                    out = _np.where(water[:, :, None], _np.asarray(ck2),
                                    _np.asarray(lake))
                    img = _P.fromarray(out.astype("uint8"), "RGB")
            photo = _ITK.PhotoImage(img)
            cv.create_image(0, 0, anchor="nw", image=photo)
            cv._ma_photo = photo
            drawn = True
        except Exception:
            drawn = False
        if not drawn:
            cv.create_rectangle(0, 0, W, Hc, fill="#1a3020", outline="#3a5a40")

        if t < 0.04:
            msg, col = tr("un seul lac, d'un seul tenant"), "#ffe066"
        else:
            msg, col = tr("lac coupé en morceaux"), "#ff8866"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))
        self._ma_ck = ck

    def _draw_wsimpl_hint(self):
        """
        water_simplification — sens demandé :
          gauche (0) = rive simplifiée
          droite (1) = rive très détaillée
        """
        import math
        cv = self._canvases.get("terrain_hint_wsimpl")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        try:
            ws = float(self._get("water_simplification", 0))
        except Exception:
            ws = 0.0
        detail = max(0.0, min(1.0, ws))  # 0 = simple, 1 = détaillé
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a140a", outline="")

        npts = int(4 + detail * 24)
        npts = max(3, npts)
        midy = H // 2 - 2
        pts = []
        for i in range(npts):
            f = i / max(1, npts - 1)
            x = 8 + int(f * (W - 16))
            jag = (math.sin(f * math.pi * 7) * 11 +
                   math.sin(f * math.pi * 15) * 5) * detail
            pts.extend([x, int(midy + jag)])

        cv.create_polygon([8, H - 18] + pts + [W - 8, H - 18],
            fill="#1a5080", outline="")
        cv.create_polygon([8, 8] + pts + [W - 8, 8],
            fill="#2a5a32", outline="")
        cv.create_line(pts, fill="#ffe066", width=2, smooth=(detail > 0.5))

        cv.create_text(10, 10, text=tr("terre"), fill="#c8e8c8",
            font=("TkFixedFont", 7), anchor="nw")
        cv.create_text(10, H - 28, text=tr("eau"), fill="#c8d8ff",
            font=("TkFixedFont", 7), anchor="sw")

        if detail < 0.25:
            msg, col = "0 — " + tr("rive simplifiée"), "#ff8866"
        elif detail < 0.7:
            msg, col = tr("rive intermédiaire"), "#ffe066"
        else:
            msg, col = "1 — " + tr("rive très détaillée"), "#66ff99"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=msg, fill=col,
            font=("TkFixedFont", 8, "bold"))

    def _draw_terrain(self):
        cv = self._canvases.get("terrain")
        if not cv or not cv.winfo_exists():
            return
        W, H = self._cv_size("terrain")
        if W < 10 or H < 10:
            return

        nm   = float(self._get("normal_map_strength", 1.0))
        shad = str(self._get("terrain_casts_shadows", "True"))
        dcl  = str(self._get("use_decal_on_terrain", "True"))

        # ── Fond = VRAIE photo de montagne (images/Mesh 3D/) ──
        # Plus de « dôme » dessiné par le code : on affiche le beau panorama
        # réel. Le détail de chaque réglage reste montré dans les vignettes.
        drawn = False
        base = self._terrain_photo_base(W, H)
        if base is not None:
            try:
                from PIL import ImageTk as _ITK
                ck = (W, H)
                if (getattr(self, "_terrain_last_ck", None) != ck
                        or getattr(self, "_pk_terrain", None) is None):
                    self._pk_terrain = _ITK.PhotoImage(base.convert("RGB"))
                    self._terrain_last_ck = ck
                cv.delete("all")
                cv.create_image(0, 0, anchor="nw", image=self._pk_terrain)
                drawn = True
            except Exception:
                drawn = False

        if not drawn:
            # Repli : ancien rendu procédural si les PNG sont introuvables
            cv.delete("all")
            params = {
                "normal_map_strength": nm, "terrain_casts_shadows": shad,
                "use_decal_on_terrain": dcl, "curvature_tol": 16,
                "ratio_water": float(self._get("ratio_water", 0.1)),
            }
            try:
                self._iso_draw(cv, W, H, params, self._t)
            except Exception:
                cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
                cv.create_text(W // 2, H // 2,
                    text=tr("Images Mesh 3D introuvables\nPlacez les PNG dans images/Mesh 3D/"),
                    fill="#ffaa66", font=("TkFixedFont", 10), justify="center")

        # Bandeau texte bas (état des réglages terrain)
        cv.create_rectangle(0, H - 20, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 10,
            text=(f"normal_map {int(nm*100)}%  "
                  + tr("ombres=") + f"{'✓' if shad=='True' else '✗'}  "
                  + tr("décals=") + f"{'✓' if dcl=='True' else '✗'}"),
            fill="#e0d8a0", font=("TkFixedFont", 9))

        self._draw_nm_hint()
        self._draw_shadow_hint()
        self._draw_nodata_hint()
        self._draw_minarea_hint()
        self._draw_maxarea_hint()
        self._draw_wsimpl_hint()

    # ── Canvas MESH ────────────────────────────────────────────────
    def _mesh_image_path(self, name):
        """Cherche une image mesh dans images/Mesh 3D/ (à la racine Ortho4XP).

        Tolérant aux variantes de noms de fichiers : casse, accents
        (découpe/découpé), espaces vs underscores, transparent/transparente.
        Repli sur d'anciens emplacements pour compatibilité.
        """
        import unicodedata

        def _norm(s):
            s = unicodedata.normalize("NFKD", s)
            s = "".join(c for c in s if not unicodedata.combining(c))
            s = s.lower()
            for ch in ("_", "-", "."):
                s = s.replace(ch, " ")
            return " ".join(s.split())

        # Noms exacts connus (repli) — tolérés via _norm
        exact = {
            "mesh_soft.png": [
                "mesh_soft.png",
                "Montagne arrondis pas de relief grand triangle.png",
            ],
            "mesh_sharp.png": [
                "mesh_sharp.png",
                "Plus de triangle et plus petit pics et relief mieux découpe.png",
                "Plus de triangle et plus petit pics et relief mieux découpé.png",
            ],
            "mesh_grid_large.png": [
                "mesh_grid_large.png",
                "grille_GRAND_TRIANGLES_transparent.png",
                "grille_GRAND_TRIANGLES_transparente.png",
            ],
            "mesh_grid_small.png": [
                "mesh_grid_small.png",
                "grille_PETITS_TRIANGLES_transparent.png",
                "grille_PETITS_TRIANGLES_transparente.png",
            ],
        }

        def _match_keywords(low, key):
            is_grille = "grille" in low
            if key == "mesh_grid_large.png":
                return is_grille and "grand" in low
            if key == "mesh_grid_small.png":
                return is_grille and "petit" in low
            if key == "mesh_soft.png":
                return (not is_grille) and ("arrondi" in low or "montagne" in low)
            if key == "mesh_sharp.png":
                return (not is_grille) and (
                    "decoup" in low or "mieux" in low
                    or ("plus" in low and "petit" in low and "relief" in low))
            return False

        # Dossiers à explorer : images/Mesh 3D/ (+ variantes) via _sim_images_roots()
        dirs = []
        for r in _sim_images_roots():
            for sub in ("Mesh 3D", "Mesh3D", "Mesh_3D", "mesh 3d", "mesh3d", ""):
                dirs.append(os.path.join(r, sub) if sub else r)
        # Repli : anciens emplacements
        root = getattr(FNAMES, "Ortho4XP_dir", "") or ""
        src = os.path.dirname(os.path.abspath(__file__))
        dirs += [
            os.path.join(root, "Simulator_images"),
            os.path.join(src, "Simulator_images"),
            src, root,
        ]

        cands_norm = {_norm(c) for c in exact.get(name, [name])}
        for d in dirs:
            if not d or not os.path.isdir(d):
                continue
            try:
                files = [f for f in os.listdir(d)
                         if os.path.isfile(os.path.join(d, f))]
            except Exception:
                continue
            # 1) correspondance exacte (tolérante)
            for f in files:
                if _norm(f) in cands_norm:
                    return os.path.join(d, f)
            # 2) correspondance par mots-clés (robuste aux renommages)
            for f in files:
                low = _norm(f)
                if not (low.endswith("png") or low.endswith("jpg")
                        or low.endswith("jpeg")):
                    continue
                if _match_keywords(low, name):
                    return os.path.join(d, f)
        return None

    def _mesh_pil(self, name, size):
        key = (name, size)
        cache = getattr(self, "_mesh_pil_cache", None)
        if cache is None:
            self._mesh_pil_cache = {}
            cache = self._mesh_pil_cache
        if key in cache:
            return cache[key]
        path = self._mesh_image_path(name)
        if not path:
            cache[key] = None
            return None
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.LANCZOS)
            cache[key] = img
            return img
        except Exception:
            cache[key] = None
            return None

    def _mesh_mask_grid_to_terrain(self, grid, landscape):
        """Retire les traits sur ciel (au-dessus des crêtes) et sur l'eau."""
        if grid is None or landscape is None:
            return grid
        try:
            import numpy as np
            land = np.asarray(landscape.convert("RGBA"))
            gr = np.asarray(grid.convert("RGBA")).copy()
            h, w = land.shape[:2]
            lr = land[:, :, 0].astype(np.int16)
            lg = land[:, :, 1].astype(np.int16)
            lb = land[:, :, 2].astype(np.int16)
            lum = (lr + lg + lb) / 3.0
            is_sky = (lum > 145) & (lb >= lr - 8) & (lb >= lg - 8)
            is_water = (lb > lg + 10) & (lb > lr + 10) & (lum > 35) & (lum < 210)
            ridgeline = np.full(w, h, dtype=np.int32)
            for x in range(w):
                nz = np.where(~is_sky[:, x])[0]
                if len(nz):
                    ridgeline[x] = int(nz[0])
            yy = np.arange(h)[:, None]
            above_ridge = yy < ridgeline[None, :]
            remove = above_ridge | is_water | is_sky
            gr[:, :, 3] = np.where(remove, 0, gr[:, :, 3])
            return Image.fromarray(gr, "RGBA")
        except Exception:
            g = grid.load()
            L = landscape.load()
            w, h = grid.size
            out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            o = out.load()
            for x in range(w):
                ridge = h
                for y in range(h):
                    lr, lg, lb, _ = L[x, y]
                    lum = (lr + lg + lb) / 3.0
                    if not (lum > 145 and lb >= lr - 8 and lb >= lg - 8):
                        ridge = y
                        break
                for y in range(h):
                    gr_, gg, gb, ga = g[x, y]
                    if ga < 8 or y < ridge:
                        continue
                    lr, lg, lb, _ = L[x, y]
                    lum = (lr + lg + lb) / 3.0
                    if lb > lg + 10 and lb > lr + 10 and 35 < lum < 210:
                        continue
                    if lum > 145 and lb >= lr - 8 and lb >= lg - 8:
                        continue
                    o[x, y] = (gr_, gg, gb, ga)
            return out

    def _mesh_scores(self):
        """
        mesh_zl       → taille triangles + relief (ronds/pics) liés
        curvature_tol → alignement montagne / grille
        limit_tris    → « budget » de triangles : grille partielle → complète
        """
        mzl  = float(self._get("mesh_zl", 19))
        ctol = float(self._get("curvature_tol", 16))
        lt   = float(self._get("limit_tris", 15))

        mesh_q = max(0.0, min(1.0, (mzl - 14.0) / 6.0))
        grid_q = mesh_q
        land_q = mesh_q
        misalign = max(0.0, min(1.0, (ctol - 1.0) / 29.0))
        # 1M → quasi vide, 15M → moyen, 50M → plein
        fill_q = max(0.0, min(1.0, (lt - 1.0) / 49.0))

        return grid_q, land_q, misalign, fill_q, mzl, ctol, lt

    def _mesh_blended_photo(self, W, H, grid_q, land_q, misalign, fill_q):
        """
        Paysage + grille (mesh_zl), décalage (curvature),
        couverture partielle de la grille (limit_tris).
        """
        grid_q = max(0.0, min(1.0, float(grid_q)))
        land_q = max(0.0, min(1.0, float(land_q)))
        misalign = max(0.0, min(1.0, float(misalign)))
        fill_q = max(0.0, min(1.0, float(fill_q)))
        q_land = round(land_q * 20) / 20.0
        mis_step = round(misalign * 12) / 12.0
        fill_step = round(fill_q * 12) / 12.0

        if grid_q < 0.42:
            grid_mode, grid_alpha = "large", 1.0
        elif grid_q > 0.58:
            grid_mode, grid_alpha = "small", 1.0
        else:
            t = (grid_q - 0.42) / (0.58 - 0.42)
            grid_mode, grid_alpha = "cross", t

        key = ("v7fill", W, H, q_land, grid_mode, round(grid_alpha, 2),
               mis_step, fill_step)
        cache = getattr(self, "_mesh_blend_cache", None)
        if cache is None:
            self._mesh_blend_cache = {}
            cache = self._mesh_blend_cache
        if key in cache:
            return cache[key]

        soft = self._mesh_pil("mesh_soft.png", (W, H))
        sharp = self._mesh_pil("mesh_sharp.png", (W, H))
        g_large = self._mesh_pil("mesh_grid_large.png", (W, H))
        g_small = self._mesh_pil("mesh_grid_small.png", (W, H))

        if soft and sharp:
            land = Image.blend(soft, sharp, q_land)
        else:
            land = sharp or soft
            if land is None:
                cache[key] = None
                return None
            land = land.copy()

        base = Image.new("RGBA", (W, H), (15, 25, 20, 255))

        ox = int(mis_step * W * 0.035)
        oy = int(mis_step * H * 0.045)
        if mis_step > 0.05:
            z = 1.0 + mis_step * 0.06
            nw, nh = int(W * z), int(H * z)
            land_s = land.resize((nw, nh), Image.LANCZOS)
            px = -ox - (nw - W) // 2
            py = -oy - (nh - H) // 2
            base.paste(land_s, (px, py))
        else:
            base.paste(land, (0, 0))

        land_for_mask = base.copy()
        if g_large is not None:
            g_large = self._mesh_mask_grid_to_terrain(g_large, land_for_mask)
        if g_small is not None:
            g_small = self._mesh_mask_grid_to_terrain(g_small, land_for_mask)

        def _with_opacity(img, alpha):
            if img is None or alpha <= 0:
                return None
            if alpha >= 0.99:
                return img
            r, g, b, a = img.split()
            a = a.point(lambda p: int(p * alpha))
            return Image.merge("RGBA", (r, g, b, a))

        def _apply_fill_budget(grid_img, fq):
            """
            limit_tris bas → grille seulement en bas (budget épuisé).
            limit_tris haut → grille sur tout le relief.
            """
            if grid_img is None:
                return None
            # Toujours un peu de grille en bas (15%), jusqu'à 100%
            cover = 0.15 + 0.85 * fq
            y_cut = int(H * (1.0 - cover))
            g = grid_img.copy()
            # Efface les traits au-dessus de y_cut (alpha = 0)
            if y_cut > 0:
                top = Image.new("RGBA", (W, y_cut), (0, 0, 0, 0))
                g.paste(top, (0, 0))
            return g, y_cut

        grid_final = None
        y_cut = 0
        if grid_mode == "large" and g_large is not None:
            grid_final, y_cut = _apply_fill_budget(g_large, fill_step)
        elif grid_mode == "small" and g_small is not None:
            grid_final, y_cut = _apply_fill_budget(g_small, fill_step)
        elif grid_mode == "cross":
            gl = _with_opacity(g_large, 1.0 - grid_alpha)
            gs = _with_opacity(g_small, grid_alpha)
            if gl is not None and gs is not None:
                merged = Image.alpha_composite(
                    Image.new("RGBA", (W, H), (0, 0, 0, 0)), gl)
                merged = Image.alpha_composite(merged, gs)
                grid_final, y_cut = _apply_fill_budget(merged, fill_step)
            elif gl is not None:
                grid_final, y_cut = _apply_fill_budget(gl, fill_step)
            elif gs is not None:
                grid_final, y_cut = _apply_fill_budget(gs, fill_step)

        if grid_final is not None:
            base = Image.alpha_composite(base.convert("RGBA"), grid_final)

        photo = ImageTk.PhotoImage(base.convert("RGBA"))
        # Stocker y_cut pour le dessin de la ligne budget (attribut temporaire)
        photo._limit_y_cut = y_cut
        photo._limit_fill = fill_step
        if len(cache) > 40:
            cache.clear()
        cache[key] = photo
        return photo

    def _draw_mesh_curve_hint(self, cv=None, W=None, H=None, ctol=None):
        """curvature_tol — le maillage (jaune) doit épouser le relief (vert).
        Curseur vers la DROITE (valeur basse) = plus de segments = le jaune
        colle au vert. Les traits ROUGES = relief perdu (écart maillage/relief).
        Un curseur blanc balaie la scène pour montrer l'écart local."""
        import math
        cv = self._canvases.get("mesh_hint_curv")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        if ctol is None:
            ctol = float(self._get("curvature_tol", 16))
        cv.delete("all")
        tphase = getattr(self, "_t", 0)

        nseg = int(3 + (30.0 - max(1.0, min(30.0, ctol))) / 29.0 * 11)
        nseg = max(3, min(14, nseg))

        pad = 8
        x0, y0 = pad, pad
        bw = W - 2 * pad
        bh = H - 2 * pad - 16

        def hill(t):
            t = max(0.0, min(1.0, t))
            p1 = math.exp(-((t - 0.32) ** 2) / (2 * 0.018))
            p2 = math.exp(-((t - 0.72) ** 2) / (2 * 0.022))
            base = 0.12 * math.sin(math.pi * t)
            h = base + 0.95 * max(p1, p2 * 0.92)
            return y0 + bh - int(bh * min(1.0, h))

        # Noeuds du maillage (ligne jaune)
        nodes = [(x0 + float(k) / nseg * bw, hill(float(k) / nseg))
                 for k in range(nseg + 1)]

        def approx_y(x):
            for i in range(len(nodes) - 1):
                x1, y1 = nodes[i]
                x2, y2 = nodes[i + 1]
                if x1 <= x <= x2 and x2 > x1:
                    f = (x - x1) / (x2 - x1)
                    return y1 + (y2 - y1) * f
            return nodes[-1][1]

        # 1) Zones d'erreur (relief perdu) — traits rouges
        gap_sum = 0.0
        gap_n = 0
        for i in range(0, int(bw), 5):
            x = x0 + i
            gy = hill(i / bw)
            ay = approx_y(x)
            d = abs(gy - ay)
            gap_sum += d
            gap_n += 1
            if d > 3:
                cv.create_line(x, gy, x, ay, fill="#c0392b", width=2)
        mean_gap = gap_sum / max(1, gap_n)

        # 2) Relief réel (courbe verte lisse)
        pts = []
        for i in range(57):
            t = i / 56.0
            pts.extend([x0 + int(t * bw), hill(t)])
        cv.create_line(pts, fill="#3d8f5a", width=3, smooth=True)

        # 3) Maillage (ligne jaune) + noeuds
        apts = []
        for (nx, ny) in nodes:
            apts.extend([nx, ny])
        cv.create_line(apts, fill="#ffe066", width=2)
        for (nx, ny) in nodes:
            cv.create_oval(nx - 2, ny - 2, nx + 2, ny + 2,
                           fill="#ffe066", outline="")

        # 4) Curseur de balayage animé + repères de l'écart local
        sx = x0 + int((tphase % 40) / 39.0 * bw)
        gy = hill((sx - x0) / bw)
        ay = approx_y(sx)
        cv.create_line(sx, y0, sx, y0 + bh, fill="#ffffff", width=1, dash=(2, 3))
        cv.create_oval(sx - 3, gy - 3, sx + 3, gy + 3,
                       fill="#a6e3a1", outline="")
        cv.create_oval(sx - 3, ay - 3, sx + 3, ay + 3,
                       fill="#ffe066", outline="")

        # 5) Verdict dynamique
        if mean_gap > 10:
            msg, col = tr("relief perdu"), "#ff8866"
        elif mean_gap > 4:
            msg, col = tr("relief partiel"), "#ffe066"
        else:
            msg, col = tr("relief suivi"), "#66ff99"
        cv.create_text(W // 2, H - 8,
            text=tr("maillage / relief : ") + msg,
            fill=col, font=("TkFixedFont", 8, "bold"))

    def _draw_min_angle_hint(self, cv=None, W=None, H=None, min_angle=None):
        """min_angle — effet visible sur la montagne (design validé).

        Gauche (min_angle bas) = relief ABÎMÉ : des pics/aiguilles sombres
        (mailles déformées) déforment la montagne. En glissant vers la DROITE,
        ces défauts s'effacent → relief PROPRE. Le curseur pilote l'opacité du
        calque de défauts (méthode « calque qui se dissout »).
        """
        if cv is None:
            cv = self._canvases.get("mesh_hint_angle")
        if not cv or not cv.winfo_exists():
            return
        if W is None:
            W = max(120, cv.winfo_width())
        if H is None:
            H = max(60, cv.winfo_height())
        if min_angle is None:
            min_angle = float(self._get("min_angle", 0.5))
        # t : 0 (0.1°, gauche, abîmé) → 1 (2.0°, droite, propre)
        t = max(0.0, min(1.0, (min_angle - 0.1) / 1.9))
        op = 1.0 - t   # opacité des défauts : forte à gauche, nulle à droite

        Hc = max(20, H - 18)
        ck = (W, H, round(op, 2))
        if getattr(self, "_ma_angle_ck", None) == ck and cv.find_all():
            return

        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")
        drawn = False
        try:
            from PIL import Image as _P, ImageDraw as _ID, ImageTk as _ITK
            import random as _r
            cache = self.__dict__.setdefault("_vig_cache", {})

            # Montagne réelle (même chargeur que les autres vignettes)
            mk = ("mont_angle", W, Hc)
            mont = cache.get(mk)
            if mont is None:
                base = self._terrain_photo_base(W, Hc)
                mont = base.convert("RGBA") if base is not None else None
                cache[mk] = mont

            # Calque de défauts (pics sombres + éclats clairs) — construit 1×
            dk = ("defs_angle", W, Hc)
            defs = cache.get(dk)
            if defs is None and mont is not None:
                defs = _P.new("RGBA", (W, Hc), (0, 0, 0, 0))
                dd = _ID.Draw(defs)
                _r.seed(6)
                n = max(10, int(W / 20))
                for k in range(n):
                    bx = _r.uniform(0.07 * W, 0.93 * W)
                    by = _r.uniform(0.55 * Hc, 0.90 * Hc)
                    hgt = _r.uniform(0.16 * Hc, 0.42 * Hc)
                    wdt = _r.uniform(0.006 * W, 0.020 * W)
                    lean = _r.uniform(-0.02 * W, 0.02 * W)
                    if k % 2:
                        col = (10, 12, 14, 210)      # pics sombres
                    else:
                        col = (200, 200, 205, 150)   # éclats clairs
                    dd.polygon([(bx - wdt, by), (bx + wdt, by),
                                (bx + lean, by - hgt)], fill=col)
                cache[dk] = defs

            if mont is not None and defs is not None:
                defA = defs.split()[3]
                ov = defs.copy()
                ov.putalpha(defA.point(lambda v, o=op: int(v * o)))
                comp = _P.alpha_composite(mont, ov).convert("RGB")
                photo = _ITK.PhotoImage(comp)
                cv.create_image(0, 0, anchor="nw", image=photo)
                cv._ma_angle_photo = photo
                drawn = True
        except Exception:
            drawn = False
        if not drawn:
            cv.create_rectangle(0, 0, W, Hc, fill="#1a2a20", outline="#3a5a40")

        if op > 0.6:
            lbl, col = tr("relief abîmé (mailles déformées)"), "#ff8866"
        elif op < 0.12:
            lbl, col = tr("relief propre"), "#a6e3a1"
        else:
            lbl, col = tr("les défauts s'effacent…"), "#e0c080"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=f"{min_angle:.1f}° — {lbl}", fill=col,
                       font=("TkFixedFont", 8, "bold"))
        self._ma_angle_ck = ck


    def _draw_iterate_hint(self, cv=None, W=None, H=None, iterate=None):
        """iterate : surface 3D de plus en plus raffinée."""
        if cv is None:
            cv = self._canvases.get("mesh_hint_iter")
        if not cv or not cv.winfo_exists():
            return
        if W is None:
            W = max(120, cv.winfo_width())
        if H is None:
            H = max(60, cv.winfo_height())
        if iterate is None:
            iterate = int(float(self._get("iterate", 0)))
        iterate = max(0, min(3, iterate))
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")

        import math
        # Grille perspective : plus de subdivisions si iterate haut
        cols = 2 + iterate * 2  # 2,4,6,8
        rows = 1 + iterate      # 1,2,3,4
        y0, y1 = int(H * 0.25), H - 22
        for r in range(rows + 1):
            fy = r / rows
            y = y0 + int((y1 - y0) * fy)
            # largeur perspective
            margin = int(W * (0.28 - 0.18 * fy))
            cv.create_line(margin, y, W - margin, y, fill="#4a7a5a", width=1)
        for c in range(cols + 1):
            fx = c / cols
            # ligne de fuite
            x_near = int(W * 0.08 + fx * W * 0.84)
            x_far = int(W * 0.30 + fx * W * 0.40)
            cv.create_line(x_far, y0, x_near, y1, fill="#4a7a5a", width=1)

        # relief ondulé sur la surface
        pts = []
        for c in range(cols + 1):
            fx = c / cols
            x = int(W * 0.08 + fx * W * 0.84)
            y = y1 - int(8 * math.sin(fx * math.pi * (1 + iterate)))
            pts.append((x, y))
        for i in range(len(pts) - 1):
            cv.create_line(*pts[i], *pts[i + 1], fill="#a6e3a1", width=2)

        labels = [
            tr("1 passe — rapide"),
            tr("2 passes — côtes affinées"),
            tr("3 passes — relief fin"),
            tr("4 passes — très long"),
        ]
        lbl = labels[iterate]
        col = ["#e0c080", "#a6e3a1", "#66ccff", "#ffaa66"][iterate]
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=f"{iterate} — {lbl}", fill=col,
                       font=("TkFixedFont", 8, "bold"))


    def _draw_mesh(self):
        cv = self._canvases.get("mesh")
        if not cv or not cv.winfo_exists():
            return
        W, H = self._cv_size("mesh")
        if W < 40 or H < 40:
            return
        cv.delete("all")

        grid_q, land_q, misalign, fill_q, mzl, ctol, lt = self._mesh_scores()

        photo = self._mesh_blended_photo(
            W, H, grid_q, land_q, misalign, fill_q)
        if photo is not None:
            cv.create_image(0, 0, anchor="nw", image=photo)
            cv._mesh_bg = photo
            y_cut = getattr(photo, "_limit_y_cut", 0)
            if fill_q < 0.95 and y_cut > 8:
                cv.create_line(0, y_cut, W, y_cut,
                    fill="#ff8866", width=1, dash=(6, 4))
                cv.create_text(W - 8, y_cut - 8,
                    text=tr("limit_tris") + f" → {lt:g}M",
                    fill="#ff8866", font=("TkFixedFont", 9, "bold"),
                    anchor="e")
        else:
            cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
            cv.create_text(W//2, H//2,
                text=tr("Placez les 4 images dans Simulator_images/"),
                fill="#a6e3a1", font=("TkFixedFont", 11), justify="center")

        # Compteur limit_tris
        cv.create_rectangle(W - 118, 8, W - 8, 36,
            fill="#0a140a", outline="#5a7a50")
        cv.create_text(W - 63, 22,
            text=f"{lt:g}M",
            fill="#ffe066" if fill_q < 0.5 else "#66ff99",
            font=("TkFixedFont", 14, "bold"))

        if misalign > 0.66:
            c_lbl, c_col = tr("curvature → ne suit pas"), "#ffaa66"
        elif misalign > 0.33:
            c_lbl, c_col = tr("curvature → partiel"), "#ffe066"
        else:
            c_lbl, c_col = tr("curvature → calé"), "#66ff99"

        if grid_q < 0.33:
            g_lbl = tr("mesh_zl → grands △")
        elif grid_q < 0.66:
            g_lbl = tr("mesh_zl → moyen")
        else:
            g_lbl = tr("mesh_zl → petits △")

        if fill_q < 0.33:
            f_lbl = tr("limit → peu de △")
        elif fill_q < 0.7:
            f_lbl = tr("limit → △ moyen")
        else:
            f_lbl = tr("limit → assez de △")

        cv.create_rectangle(0, H - 28, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 14,
            text=f"{g_lbl}  |  {c_lbl}  |  {f_lbl}",
            fill=c_col, font=("TkFixedFont", 9, "bold"))

        # Animations dans leurs cadres (sous l'image)
        self._draw_mesh_curve_hint()
        self._draw_min_angle_hint()
        self._draw_iterate_hint()

    def _draw_img_smooth_hint(self):
        """apt_smooth : piste vue en perspective (bosses → plate)."""
        cv = self._canvases.get("img_hint_smooth")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        sm = float(self._get("apt_smoothing_pix", 8))
        t = max(0.0, min(1.0, sm / 30.0))  # 0 = bosses, 1 = lisse
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")

        # Ciel + horizon
        cv.create_rectangle(0, 0, W, int(H * 0.35), fill="#2a3a48", outline="")
        # Sol perspective (trapèze)
        y0, y1 = int(H * 0.38), H - 4
        pts_ground = [2, y1, W - 2, y1, int(W * 0.62), y0, int(W * 0.38), y0]
        cv.create_polygon(pts_ground, fill="#3a4a30", outline="")

        # Piste en perspective : large devant, étroite au loin
        def runway_y(f):
            return y0 + int((y1 - y0) * f)

        def runway_half_w(f):
            # f=0 loin, f=1 près
            return int((W * 0.04) + (W * 0.22) * f)

        # Profil vertical de la piste (bosses selon t)
        n = 14
        left, right, center = [], [], []
        for i in range(n + 1):
            f = i / n  # 0 loin → 1 près
            y = runway_y(f)
            hw = runway_half_w(f)
            # bosses : plus fortes quand t bas, amorties avec f (loin = moins visibles)
            bump = (1.0 - t) * 7.0 * (0.4 + 0.6 * f)
            import math
            dy = int(bump * math.sin(i * 1.7) * math.sin(i * 0.9))
            cx = W // 2
            left.append((cx - hw, y + dy))
            right.append((cx + hw, y + dy))
            center.append((cx, y + dy))

        # Surface piste
        poly = left + list(reversed(right))
        flat = [c for p in poly for c in p]
        cv.create_polygon(flat, fill="#5a5a55", outline="#888")
        # Ligne centrale
        for i in range(len(center) - 1):
            if i % 2 == 0:
                cv.create_line(*center[i], *center[i + 1], fill="#e8e070", width=2)
        # Bords
        for i in range(len(left) - 1):
            cv.create_line(*left[i], *left[i + 1], fill="#c0c0b0", width=1)
            cv.create_line(*right[i], *right[i + 1], fill="#c0c0b0", width=1)

        if t < 0.25:
            lbl, col = tr("piste bosselée"), "#ff8866"
        elif t < 0.55:
            lbl, col = tr("piste correcte (reco)"), "#a6e3a1"
        else:
            lbl, col = tr("piste très lissée"), "#66ccff"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=f"{int(sm)}px — {lbl}", fill=col,
                       font=("TkFixedFont", 8, "bold"))


    def _draw_img_curv_hint(self):
        """apt_curv_tol : virage taxiway en perspective (suit / simplifie)."""
        cv = self._canvases.get("img_hint_curv")
        if not cv or not cv.winfo_exists():
            return
        W = max(120, cv.winfo_width())
        H = max(60, cv.winfo_height())
        act = float(self._get("apt_curv_tol", 1.5))
        # bas = précis (suit), haut = simplifié
        t = max(0.0, min(1.0, (act - 0.5) / 5.0))
        cv.delete("all")
        cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")
        # Sol
        cv.create_rectangle(0, int(H * 0.45), W, H, fill="#2a3a28", outline="")

        import math
        # Courbe réelle (vert) — S en perspective
        real = []
        for i in range(24):
            u = i / 23.0
            x = int(W * 0.12 + u * W * 0.76)
            y = int(H * 0.78 - 18 * math.sin(u * math.pi * 1.5)
                    - u * H * 0.25)
            real.append((x, y))
        for i in range(len(real) - 1):
            cv.create_line(*real[i], *real[i + 1], fill="#55aa66", width=2)

        # Mesh (jaune) : moins de points si t haut
        n_pts = max(3, int(12 - t * 9))
        mesh = []
        for i in range(n_pts):
            u = i / max(1, n_pts - 1)
            x = int(W * 0.12 + u * W * 0.76)
            # suit moins bien si simplifié
            amp = 18 * (1.0 - 0.65 * t)
            y = int(H * 0.78 - amp * math.sin(u * math.pi * 1.5)
                    - u * H * 0.25)
            mesh.append((x, y))
        for i in range(len(mesh) - 1):
            cv.create_line(*mesh[i], *mesh[i + 1], fill="#ffe066", width=2)
        for x, y in mesh:
            cv.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#ffe066", outline="")

        if t < 0.35:
            lbl, col = tr("suit les virages"), "#a6e3a1"
        elif t < 0.7:
            lbl, col = tr("assez précis"), "#e0c080"
        else:
            lbl, col = tr("contour simplifié"), "#ff8866"
        cv.create_rectangle(0, H - 18, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 9, text=f"tol {act:.1f} — {lbl}", fill=col,
                       font=("TkFixedFont", 8, "bold"))


    def _draw_img_segs_hint(self):
        """levelled_segs — vignette validée, lisible :
        GAUCHE : route montagne russe, bosses ROUGES au-dessus, cuvettes VERT CLAIR en dessous.
        DROITE : route épaisse et plate, vert collé à la route, plus de bosses/cuvettes.
        """
        import math
        cv = self._canvases.get("img_hint_segs")
        if not cv or not cv.winfo_exists():
            return
        W = max(140, cv.winfo_width())
        H = max(70, cv.winfo_height())
        segs = float(self._get("max_levelled_segs", 200000))
        t = max(0.0, min(1.0, segs / 500000.0))  # 0=gauche, 1=droite
        cv.delete("all")

        top, bot = 6, H - 18
        x0, x1 = 6, W - 6
        Hd = max(12, bot - top)
        cy = top + 0.50 * Hd
        amp0 = 0.40 * Hd
        amp = amp0 * (1.0 - t)

        def wave(px):
            u = (px - x0) / max(1.0, float(x1 - x0))
            return (0.75 * math.sin(u * math.pi * 2.5)
                    + 0.25 * math.sin(u * math.pi * 5.0 + 0.6))

        def profile(px):
            return cy - amp * wave(px)

        step = 2
        xs = list(range(x0, x1 + 1, step))
        if xs[-1] != x1:
            xs.append(x1)

        # Fond
        cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")
        cv.create_rectangle(0, 0, W, bot, fill="#1a3048", outline="")

        # ── Cuvettes VERT CLAIR (sous le niveau moyen cy) ──
        if amp > 2.0:
            run, runs = [], []
            for px in xs:
                if profile(px) > cy + 1.0:
                    run.append(px)
                else:
                    if len(run) >= 2:
                        runs.append(run)
                    run = []
            if len(run) >= 2:
                runs.append(run)
            for r in runs:
                pts = []
                for px in r:
                    pts.extend([px, profile(px)])
                for px in reversed(r):
                    pts.extend([px, cy])
                cv.create_polygon(pts, fill="#9ee87a", outline="#6bc04a")

        # ── Terrain de base (vert) ──
        gpts = [x0, bot]
        for px in xs:
            gpts.extend([px, profile(px)])
        gpts.extend([x1, bot])
        # À droite (t→1) le vert se colle à la route (profil plat)
        cv.create_polygon(gpts, fill="#4a9a3a", outline="#2e6e28")

        # ── Bosses ROUGES (au-dessus de cy) ──
        if amp > 2.0:
            run, runs = [], []
            for px in xs:
                if profile(px) < cy - 1.0:
                    run.append(px)
                else:
                    if len(run) >= 2:
                        runs.append(run)
                    run = []
            if len(run) >= 2:
                runs.append(run)
            for r in runs:
                pts = []
                for px in r:
                    pts.extend([px, profile(px)])
                for px in reversed(r):
                    pts.extend([px, cy])
                cv.create_polygon(pts, fill="#e84840", outline="#c03028")

        # ── Route : montagne russe → plate et plus ÉPAISSE à droite ──
        # Épaisseur : 3 px à gauche → 6 px à droite
        half = 3.0 + 3.0 * t
        band = []
        mid = []
        for px in xs:
            ry = profile(px) * (1.0 - t) + cy * t
            band.extend([px, ry - half])
            mid.extend([px, ry])
        for px in reversed(xs):
            ry = profile(px) * (1.0 - t) + cy * t
            band.extend([px, ry + half])
        cv.create_polygon(band, fill="#4a4f56", outline="#2a2e34")
        cv.create_line(mid, fill="#f2d75a", width=max(1, int(1 + t)), dash=(6, 3))

        # Croix sur bosses (gauche seulement)
        if amp > 3.0:
            for bxf in (0.18, 0.82):
                bx = x0 + bxf * (x1 - x0)
                ty = profile(bx)
                if ty < cy - 4:
                    by = ty - 6
                    s = 5
                    cv.create_line(bx - s, by - s, bx + s, by + s,
                                   fill="#ff6048", width=2)
                    cv.create_line(bx + s, by - s, bx - s, by + s,
                                   fill="#ff6048", width=2)

        k = int(segs / 1000)
        if t < 0.25:
            lbl, col = tr("montagne russe — bosses + cuvettes"), "#ff8866"
        elif t < 0.7:
            lbl, col = tr("en partie nivelé"), "#e0c080"
        else:
            lbl, col = tr("route plate — vert collé"), "#a6e3a1"
        cv.create_rectangle(0, H - 16, W, H, fill="#060e06", outline="")
        cv.create_text(W // 2, H - 8, text=f"{k}k — {lbl}", fill=col,
                       font=("TkFixedFont", 8, "bold"))


    def _draw_imagerie(self):
        """
        Canvas Imagerie & Aéroports — PNG depuis images/Aeroports/.
        Cache final : ne recalcule que si curseurs / taille changent.
        """
        cv = self._canvases.get("imagerie")
        if not cv or not cv.winfo_exists():
            return
        W, H = self._cv_size("imagerie")
        if W < 40 or H < 40:
            return

        dzl  = int(self._get("default_zl", 17))
        czl  = int(self._get("cover_zl", 18))
        cext = float(self._get("cover_extent", 1.0))
        apt  = str(self._get("cover_airports_with_highres", "False"))
        rl   = int(self._get("road_level", 4))
        asmp = int(self._get("apt_smoothing_pix", 8))
        act  = float(self._get("apt_curv_tol", 1.5))
        ace  = float(self._get("apt_curv_ext", 1.0))

        if not hasattr(self, "_img_cache"):
            self._img_cache = {}
        if not hasattr(self, "_img_final"):
            self._img_final = {}
        if not hasattr(self, "_img_last_ck"):
            self._img_last_ck = None

        # Clé : params qui affectent la photo composée (pas les cercles)
        ck_photo = (W, H, dzl, rl, 1 if dzl >= 17 else 0)
        ck_full  = (W, H, dzl, czl, round(cext, 2), apt, rl, asmp, round(act, 2), round(ace, 2))

        # Skip total si rien n'a changé
        if self._img_last_ck == ck_full and cv.find_all():
            return

        try:
            from PIL import Image as _PIL, ImageTk as _ITK

            apt_path = _sim_find_imagerie("aeroport")
            if not apt_path:
                cv.delete("all")
                cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
                roots = _sim_images_roots()
                lines = [
                    "Images Aeroports introuvables",
                    "",
                    "Placez les fichiers dans :",
                    "  Ortho4XP/images/Aeroports/",
                    "Fichiers : Aeroport.jpg, Autoroute.png,",
                    "  Route1.png, Route2.png,",
                    "  Jointure zone aeroport.png",
                    "",
                    "Dossiers cherches :",
                ]
                for r in roots[:4]:
                    lines.append("  " + os.path.join(r, "Aeroports"))
                cv.create_text(W // 2, H // 2, text="\\n".join(lines),
                    fill="#ffaa66", font=("TkFixedFont", 9), justify="center")
                return

            # Photo composée (satellite + routes) — cachee
            if ck_photo in self._img_final:
                photo = self._img_final[ck_photo]
            else:
                # default_zl = résolution de TOUTE l'image (fond + routes).
                # On compose d'abord en PLEINE résolution, puis on applique la
                # basse résolution à l'ensemble (plus bas) — sinon les calques
                # routes nets recouvrent le fond et masquent l'effet de
                # default_zl (road_level n'a rien à voir avec le flou).
                res_factor = min(1.0, max(0.12, (dzl - 13) / 7.0))
                pil = _sim_load_imagerie("aeroport", W, H, self._img_cache)
                if pil.mode != "RGBA":
                    base = pil.convert("RGBA")
                else:
                    base = pil.copy()

                # Routes selon road_level (curseur à droite = 4 → tous les calques)
                #   1 = Autoroute (vert)
                #   2 = + Route1 (rouge)
                #   3 = + Route2 (réseau complet vert/rouge/bleu)
                #   4 = idem Route2 (max)
                road_keys = []
                if rl >= 1:
                    road_keys.append("autoroute")
                if rl >= 2:
                    road_keys.append("route1")
                if rl >= 3:  # 3 et 4 → Route2.png
                    road_keys.append("route2")

                for rk in road_keys:
                    ov = _sim_load_imagerie(rk, W, H, self._img_cache, black_transparent=True)
                    if ov is None:
                        continue
                    if ov.mode != "RGBA":
                        ov = ov.convert("RGBA")
                    base = _PIL.alpha_composite(base, ov)

                # Jointure si ZL >= 17
                if dzl >= 17:
                    jn = _sim_load_imagerie("jointure", W, H, self._img_cache, black_transparent=True)
                    if jn.mode != "RGBA":
                        jn = jn.convert("RGBA")
                    base = _PIL.alpha_composite(base, jn)

                # ── Basse résolution pilotée UNIQUEMENT par default_zl ──
                # Appliquée à TOUTE l'image composée (fond + routes) : réduction
                # puis ré-agrandissement. Ainsi le flou ne dépend jamais de
                # road_level (les routes ne recouvrent plus un fond net).
                if res_factor < 0.98:
                    lw = max(1, int(W * res_factor))
                    lh = max(1, int(H * res_factor))
                    base = base.resize((lw, lh), _PIL.LANCZOS).resize(
                        (W, H), _PIL.BILINEAR)

                photo = _ITK.PhotoImage(base.convert("RGB"))
                if len(self._img_final) > 10:
                    self._img_final.clear()
                self._img_final[ck_photo] = photo

            cv.delete("all")
            cv.create_rectangle(0, 0, W, H, fill="#0a120a", outline="")
            cv.create_image(0, 0, anchor="nw", image=photo)
            cv._pk_apt = photo

            # Cercles HiRes — comme dans l'animation d'origine
            # Anneaux concentriques qui grossissent avec cover_extent / curv_ext
            import math
            apt_on = str(apt) not in ("False", "0", "", "None", "false", "none")
            cx, cy = W // 2, int(H * 0.48)

            # Échelle : 1 km ≈ scale pixels (cadre ~ 12-20 km visible)
            scale = min(W, H) / 14.0
            # Rayons (minimum visibles même à 0 pour feedback)
            r0 = max(10, int(0.4 * scale))                    # noyau aéroport
            r_ext = max(r0 + 4, int(max(cext, 0.15) * scale)) # cover_extent
            r_curv = max(r_ext + 6, int((max(cext, 0.15) + max(ace, 0.3)) * scale))
            r_tol = max(r0 + 2, int(r_ext * (0.55 + 0.15 * min(act, 4.0))))

            # Couleurs selon cover_zl
            if czl >= 19:
                col_ext = "#88ff44"
            elif czl >= 17:
                col_ext = "#66dd88"
            else:
                col_ext = "#88aa66"
            col_curv = "#ff8844"
            col_tol  = "#44aaff"
            col_core = "#ffe066"

            if apt_on:
                # Anneau cover_extent (plein)
                cv.create_oval(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext,
                    outline=col_ext, width=2)
                # Anneau intérieur (trait pointillé)
                cv.create_oval(cx - r_ext + 3, cy - r_ext + 3,
                               cx + r_ext - 3, cy + r_ext - 3,
                    outline=col_ext, width=1, dash=(6, 4))
                # Anneau curv_ext (orange, tirets)
                cv.create_oval(cx - r_curv, cy - r_curv, cx + r_curv, cy + r_curv,
                    outline=col_curv, width=2, dash=(5, 3))
                # Anneau curv_tol (bleu, fin)
                cv.create_oval(cx - r_tol, cy - r_tol, cx + r_tol, cy + r_tol,
                    outline=col_tol, width=1, dash=(2, 3))
                # Noyau
                cv.create_oval(cx - r0, cy - r0, cx + r0, cy + r0,
                    outline=col_core, width=2)
                cv.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                    fill=col_core, outline="")

                # Labels
                cv.create_text(cx, cy - r_curv - 14,
                    text=f"HiRes ON  ZL{czl}", fill=col_ext,
                    font=("TkFixedFont", 10, "bold"))
                cv.create_text(cx + r_ext + 6, cy - 8,
                    text=f"{cext:.1f} km", fill=col_ext,
                    font=("TkFixedFont", 9, "bold"), anchor="w")
                cv.create_text(cx + r_curv + 6, cy + 10,
                    text=f"+{ace:.1f} km curv", fill=col_curv,
                    font=("TkFixedFont", 8), anchor="w")
            else:
                # HiRes OFF : petit cercle gris + indication
                cv.create_oval(cx - r0, cy - r0, cx + r0, cy + r0,
                    outline="#556655", width=2, dash=(4, 3))
                cv.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                    fill="#556655", outline="")
                cv.create_text(cx, cy - r0 - 14,
                    text=f"HiRes OFF  ZL{dzl}", fill="#889988",
                    font=("TkFixedFont", 10, "bold"))
                cv.create_text(cx, cy + r0 + 14,
                    text=tr("activer cover_airports_with_highres"),
                    fill="#667766", font=("TkFixedFont", 8))

            # Légende
            legend = [
                ("#88ff44" if apt_on else "#556655",
                 tr("HiRes") + (" ON" if apt_on else " OFF")),
                ("#88ff44", f"cover_extent {cext:.1f} km"),
                ("#66ccff", f"cover_zl ZL{czl}"),
                ("#ff8844", f"curv_ext +{ace:.1f} km"),
                ("#44aaff", f"curv_tol {act:.1f}"),
                ("#aaaaaa", tr("routes") + f" niv.{rl}"),
            ]
            lx, ly = W - 176, 4
            cv.create_rectangle(lx - 2, ly, W - 2, ly + len(legend) * 16 + 6,
                fill="#081008", outline="")
            for j, (col, lbl) in enumerate(legend):
                y_ = ly + 10 + j * 16
                cv.create_rectangle(lx + 4, y_ - 4, lx + 16, y_ + 4,
                    fill=col, outline="")
                cv.create_text(lx + 22, y_, text=lbl, fill=col,
                    anchor="w", font=("TkFixedFont", 8))

            qual_lbl = (
                "HD ZL20" if dzl >= 20 else
                f"ZL{dzl} — {'HD' if dzl >= 19 else 'SD' if dzl >= 17 else 'LD'}")
            if apt_on:
                mode = apt if apt in ("ICAO", "Existing") else "HiRes"
                apt_lbl = tr("aéroport") + f" {mode} ZL{czl} ±{cext:.1f}km"
            else:
                apt_lbl = tr("aéroport: même ZL que le reste (HiRes OFF)")
            cv.create_rectangle(0, H - 22, W, H, fill="#061006", outline="")
            cv.create_text(W // 2, H - 11,
                text=f"{qual_lbl}  |  {apt_lbl}  |  " + tr("routes") + f" {rl}",
                fill="#e0c080", font=("TkFixedFont", 9))

            self._img_last_ck = ck_full
            try:
                self._draw_img_smooth_hint()
                self._draw_img_curv_hint()
                self._draw_img_segs_hint()
            except Exception:
                pass

        except Exception:
            try:
                cv.delete("all")
                cv.create_rectangle(0, 0, W, H, fill="#1a2a20", outline="")
                cv.create_text(W // 2, H // 2,
                    text=tr("Images Aeroports introuvables\\nPlacez les fichiers dans images/Aeroports/"),
                    fill="#ffaa66", font=("TkFixedFont", 10), justify="center")
            except Exception:
                pass



    # ── Ouverture fenêtre Vue Tuile ───────────────────────────────
    def _open_tile_view(self):
        if hasattr(self, "_tile_view_win") and self._tile_view_win and                 self._tile_view_win.winfo_exists():
            self._tile_view_win.lift()
            self._tile_view_win.focus_force()
            return
        self._tile_view_win = Ortho4XP_TileView(
            self, self.lat, self.lon,
            self.custom_build_dir, self._vars)

    # ── Chargement valeurs depuis cfg ──────────────────────────────
    def _load_values(self):
        self._tile = CFG.Tile(self.lat, self.lon, self.custom_build_dir)
        self._tile.read_from_config()
        bool_map = {True:"True", False:"False"}
        for key, var in self._vars.items():
            try:
                val = getattr(self._tile, key, None)
                if val is None:
                    continue
                if isinstance(var, tk.StringVar):
                    if isinstance(val, bool):
                        var.set(bool_map[val])
                    else:
                        var.set(str(val))
                else:
                    var.set(val)
            except Exception:
                pass
        self._status.config(
            text=tr("✓ Valeurs chargées depuis le cfg."), fg=self.FG2)

    # ── Écriture cfg tuile ─────────────────────────────────────────
    def _write_tile(self):
        try:
            self._apply_to_tile()
            self._tile.write_to_config()
            self._status.config(
                text=tr("✅ Sauvegardé dans cfg tuile."), fg=self.FG2)
        except Exception as e:
            self._status.config(text=f"❌ {e}", fg="#ff6b6b")

    # ── Écriture cfg app global ────────────────────────────────────
    def _write_app(self):
        try:
            self._apply_to_tile()
            # Écrire le cfg global Ortho4XP
            import O4_Config_Utils as _CFG
            cfg_path = os.path.join(
                FNAMES.Ortho4XP_dir, "Ortho4XP.cfg")
            self._tile.write_to_config(cfg_path)
            self._status.config(
                text=tr("✅ Sauvegardé dans cfg global."), fg=self.FG2)
        except Exception as e:
            self._status.config(text=f"❌ {e}", fg="#ff6b6b")

    def _apply_to_tile(self):
        bool_keys = {
            "use_masks_for_inland","imprint_masks_to_dds",
            "distance_masks_too","masks_use_DEM_too",
            "terrain_casts_shadows",
            "use_decal_on_terrain","fill_nodata","clean_bad_geometries"
        }
        for key, var in self._vars.items():
            try:
                raw = var.get()
                if key in bool_keys:
                    setattr(self._tile, key, raw == "True")
                elif isinstance(raw, str):
                    try:
                        setattr(self._tile, key, float(raw)
                            if '.' in raw else int(raw))
                    except Exception:
                        setattr(self._tile, key, raw)
                else:
                    setattr(self._tile, key, raw)
            except Exception:
                pass
