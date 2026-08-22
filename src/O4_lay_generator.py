#============================================================
# CRÉDIT — AUTEUR : Roland (Ypsos). — 2026
# Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE,
# quelle que soit l'évolution ultérieure du fichier.
#============================================================
# CREDIT — AUTHOR: Roland (Ypsos). — 2026
# This module was designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship notice MUST NEVER BE REMOVED,
# regardless of any subsequent evolution of the file.
#============================================================
# CONTRIBUTEURS / CONTRIBUTORS :
#   - Preset IGN Ortho France (WMTS, France + DOM-TOM) :
#     domisilasol (Dominique) — X-Plane.fr, août 2026.
#============================================================
# -*- coding: utf-8 -*-
"""
O4_lay_generator.py
Générateur de fichiers .lay (définitions de providers) pour Ortho4XP.
Module autonome, additif : n'altère AUCUN fichier existant du moteur.
Fenêtre thématisée (couleurs Ortho), boutons lisibles macOS/Windows/Linux.
Écrit un .lay dans Providers/<tuile active>/.
"""

from __future__ import annotations
import os
import sys

# --- détection OS ----------------------------------------------------------
if "dar" in sys.platform:
    _OS = "mac"
elif "win" in sys.platform:
    _OS = "windows"
else:
    _OS = "linux"

# --- traduction (réutilise le tr() d'Ortho ; fallback = texte tel quel) ---
try:
    from O4_Lang import tr as _tr
    def tr(k, default=""):
        v = _tr(k)
        return v if v != k else (default or k)
except Exception:
    def tr(k, default=""):
        return default or k

# --- thème (réutilise O4_Theme_Manager comme le GUI principal) -------------
try:
    import O4_Theme_Manager as _TM
    _HAS_THEME = True
except Exception:
    _TM = None
    _HAS_THEME = False

def _c(key, fallback):
    """Couleur du thème actif, ou fallback si Theme Manager absent."""
    if _HAS_THEME:
        try:
            return _TM.get_theme().get(key, fallback)
        except Exception:
            return fallback
    return fallback

# --- CustomTkinter (boutons look fenêtre principale) -----------------------
# Repli TOUJOURS conservé : si CTk absent, on garde la fabrique Frame+Label
# Mac-safe existante (voir _make_themed_button).
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    _HAS_CTK = False

def _lighten_hex(hexcol, factor):
    """Éclaircit une couleur hex (#rrggbb) d'un facteur. Utilisé pour le
    survol des boutons CTk, comme dans la fenêtre principale validée."""
    try:
        h = hexcol.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hexcol

# ===========================================================================
# PARTIE LOGIQUE (sans interface) — testable seule
# ===========================================================================

def _providers_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "Providers")

def _tile_name(lat, lon):
    """Réutilise la fonction officielle d'Ortho ; sinon recopie son format."""
    try:
        import O4_File_Names as FNAMES
        return FNAMES.short_latlon(int(lat), int(lon))
    except Exception:
        return "{:+03d}{:+04d}".format(int(lat), int(lon))

def build_lay_text(fields: dict) -> str:
    """Fabrique le contenu .lay. Ne garde que les clés lues par le moteur."""
    order = [
        "request_type", "grid_type", "url_prefix", "url_template",
        "layers", "epsg_code", "wms_size", "wms_version",
        "image_type", "imagery_dir", "in_GUI",
    ]
    lines = []
    for key in order:
        if key not in fields:
            continue
        val = str(fields[key]).strip()
        # Si l'utilisateur a collé la LIGNE complète « clé=valeur », on retire
        # le préfixe « clé= » en trop (sinon on obtenait « url_prefix=url_prefix=… »
        # ou « layers=layers=… »).
        if val.lower().startswith(key.lower() + "="):
            val = val[len(key) + 1:].strip()
        if val != "":
            lines.append("{}={}".format(key, val))
    return "\n".join(lines) + "\n"

def _safe_lay_name(provider_name):
    """Nom de fichier .lay SÛR, SANS extension. Retire un « .lay » final
    éventuel (sinon « Aoste_2012.lay » donnait « Aoste_2012lay.lay », le point
    étant supprimé par le filtrage des caractères)."""
    name = (provider_name or "").strip()
    if name.lower().endswith(".lay"):
        name = name[:-4]
    safe = "".join(c for c in name if c.isalnum() or c in "-_ ").strip()
    return safe or "provider"

def target_path(lat, lon, provider_name: str) -> str:
    tile = _tile_name(lat, lon)
    return os.path.join(_providers_dir(), tile, _safe_lay_name(provider_name) + ".lay")

def target_path_in_dir(dest_dir, provider_name: str) -> str:
    """Chemin .lay dans un dossier provider CHOISI par l'utilisateur (pour
    réutiliser un .lay sur d'autres tuiles)."""
    return os.path.join(dest_dir, _safe_lay_name(provider_name) + ".lay")

def write_lay(lat, lon, provider_name: str, fields: dict, overwrite=False,
              dest_dir=None):
    # dest_dir fourni → on écrit LÀ (dossier provider choisi) ; sinon dans
    # Providers/<tuile active>/ (comportement par défaut conservé).
    if dest_dir:
        path = target_path_in_dir(dest_dir, provider_name)
    else:
        path = target_path(lat, lon, provider_name)
    if os.path.exists(path) and not overwrite:
        return (False, path, "EXISTS")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_lay_text(fields))
    return (True, path, "OK")

def validate_fields(fields: dict) -> list:
    problems = []
    rtype = fields.get("request_type", "").strip().lower()
    if rtype not in ("wms", "tms", "wmts"):
        problems.append("Type de requête invalide (attendu wms/tms/wmts).")
    if rtype == "tms":
        if not fields.get("url_template", "").strip():
            problems.append("url_template obligatoire pour un provider TMS.")
    else:
        if not fields.get("url_prefix", "").strip():
            problems.append("url_prefix obligatoire pour un provider WMS/WMTS.")
        if not fields.get("layers", "").strip():
            problems.append("layers obligatoire pour un provider WMS/WMTS.")
    return problems

def parse_lay_text(text: str) -> dict:
    """Relit un .lay existant en dictionnaire clé->valeur."""
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data

def scan_existing_lays():
    """Scanne Providers/ et retourne la liste des .lay trouvés.
    Retourne une liste de tuples (dossier, nom_fichier, chemin_complet),
    triée par dossier puis par nom. Lue en direct du disque = toujours à jour."""
    base = _providers_dir()
    found = []
    if not os.path.isdir(base):
        return found
    for root, dirs, files in os.walk(base):
        for fn in files:
            if fn.lower().endswith(".lay"):
                full = os.path.join(root, fn)
                # dossier relatif à Providers/ (ex. "Suisse", "France Pays de la Loire")
                rel = os.path.relpath(root, base)
                folder = "" if rel == "." else rel
                found.append((folder, fn[:-4], full))
    found.sort(key=lambda t: (t[0].lower(), t[1].lower()))
    return found

# ===========================================================================
# BOUTON THÉMATISÉ (fiable macOS : tk.Button ignore souvent bg/fg en Aqua)
# ===========================================================================
def _make_themed_button(tk, parent, text, command):
    bg     = _c("btn_bg", "#4a6b59")
    fg     = _c("btn_fg", "#ffffff")
    hover  = _c("accent", "#5a7b69")
    active = _c("fg_secondary", "#a6e3a1")
    border = _c("btn_bg", "#4a6b59")

    # --- Branche CustomTkinter : bouton look fenêtre principale ------------
    # Si CTk présent, on retourne un CTkButton (mêmes couleurs de thème).
    # .pack() reste disponible → les appelants sont inchangés.
    if _HAS_CTK:
        try:
            b = ctk.CTkButton(
                parent, text=text, command=command,
                corner_radius=8, border_width=1, height=30,
                fg_color=bg, hover_color=_lighten_hex(bg, 1.30),
                border_color=border, text_color=fg,
                font=("Helvetica", 12) if _OS == "mac" else ("Segoe UI", 10))
            # CORRECTIF macOS OBLIGATOIRE : le remplissage arrondi n'est
            # dessiné qu'une fois le bouton dimensionné → sinon rectangle
            # sombre derrière le texte au repos. On force un redessin.
            b.after_idle(
                lambda btn=b, c=bg: btn.winfo_exists()
                and btn.configure(fg_color=c))
            return b
        except Exception:
            pass  # échec CTk → on retombe sur la fabrique Frame+Label

    # --- Repli Mac-safe conservé (Frame+Label) : CTk absent ---------------
    frame = tk.Frame(parent, bg=bg, highlightthickness=1,
                     highlightbackground=border, highlightcolor=active, bd=0)
    label = tk.Label(frame, text=text, bg=bg, fg=fg, padx=10, pady=5,
                     font=("Helvetica", 12) if _OS == "mac" else ("Segoe UI", 10),
                     cursor="hand2")
    label.pack(fill="both", expand=True)

    def on_enter(e=None):
        frame.configure(bg=hover); label.configure(bg=hover)
    def on_leave(e=None):
        frame.configure(bg=bg); label.configure(bg=bg)
    def on_click(e=None):
        frame.configure(bg=active); label.configure(bg=active)
    def on_release(e=None):
        frame.configure(bg=hover); label.configure(bg=hover)
        if command:
            command()
    for w in (frame, label):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)
        w.bind("<ButtonRelease-1>", on_release)
    return frame

# ===========================================================================
# FENÊTRE (chargée seulement au clic sur le bouton)
# ===========================================================================
def run_lay_generator(parent=None):
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    BG     = _c("bg", "#3b5b49")
    FG     = _c("fg", "#e8f0ec")
    FG2    = _c("fg_secondary", "#a6e3a1")
    CON_BG = _c("console_bg", "#0f0f1a")
    CON_FG = _c("console_fg", "#50fa7b")
    ENTRY_BG = "#f0f4f2"
    ENTRY_FG = "#1e3028"

    try:
        cur_lat = int(parent.lat.get() or 48)
        cur_lon = int(parent.lon.get() or -6)
    except Exception:
        cur_lat, cur_lon = 48, -6

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(tr("lay_win_title", "Générateur de provider (.lay)"))
    win.configure(bg=BG)
    win.resizable(True, True)
    if parent is not None:
        try:
            win.transient(parent)
        except Exception:
            pass

    # Dossier où sera écrit le .lay. Par défaut : Providers/<tuile active>/
    # (comportement conservé). L'utilisateur peut en choisir un autre pour
    # réutiliser le même .lay sur d'autres tuiles.
    v_dest_dir = tk.StringVar(
        value=os.path.join(_providers_dir(), _tile_name(cur_lat, cur_lon)))
    v_dest_disp = tk.StringVar(value="")

    def _maj_dest_disp(*_):
        p = v_dest_dir.get()
        try:
            court = os.path.join(os.path.basename(os.path.dirname(p)),
                                 os.path.basename(p))
        except Exception:
            court = p
        v_dest_disp.set("→ " + court)
    v_dest_dir.trace_add("write", _maj_dest_disp)
    _maj_dest_disp()

    def _fixer_taille_min(w):
        """Ouvre la fenêtre à la taille de son contenu et EMPÊCHE de la réduire
        en dessous : rien n'est jamais masqué, ni en largeur ni en hauteur.
        La fenêtre reste agrandissable et est centrée à l'écran. On ne fige PAS
        la taille (on ne pose que la position) : ainsi elle grandit d'elle-même
        si le contenu grandit, et minsize interdit de la rétrécir sous le
        contenu."""
        try:
            w.update_idletasks()
            rw, rh = w.winfo_reqwidth(), w.winfo_reqheight()
            sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
            x = max(0, (sw - rw) // 2)
            y = max(0, (sh - rh) // 3)
            w.minsize(rw, rh)
            w.geometry("+%d+%d" % (x, y))
            w.resizable(True, True)
            w.lift()
        except Exception:
            pass

    # ttk style pour les combobox aux couleurs du thème + fix macOS
    style = ttk.Style(win)
    try:
        style.theme_use("alt")
    except Exception:
        pass
    style.configure("O4Lay.TCombobox", fieldbackground=ENTRY_BG,
                    background=ENTRY_BG, foreground=ENTRY_FG)

    def lbl(r, text):
        tk.Label(win, text=text, bg=FG2, fg="#14241c",
                 font=("", 11, "bold"), anchor="w", padx=6).grid(
                 row=r, column=0, sticky="ew", padx=(8, 4), pady=3)

    def entry(r, default=""):
        var = tk.StringVar(value=default)
        tk.Entry(win, textvariable=var, width=44,
                 bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG).grid(
                 row=r, column=1, sticky="ew", padx=(4, 8), pady=3)
        return var

    def combo(r, values, default):
        var = tk.StringVar(value=default)
        ttk.Combobox(win, textvariable=var, values=values, state="readonly",
                     width=41, style="O4Lay.TCombobox").grid(
                     row=r, column=1, sticky="ew", padx=(4, 8), pady=3)
        return var

    tk.Label(win, text=tr("lay_active_tile", "Tuile active :") + " " + _tile_name(cur_lat, cur_lon),
             bg=FG2, fg="#14241c", font=("", 13, "bold")).grid(
             row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(10, 8))

    lbl(1, tr("lay_provider_name", "Nom du provider"));   v_name = entry(1)
    lbl(2, tr("lay_request_type", "Type de requête"));   v_type = combo(2, ["wms", "tms", "wmts"], "wms")
    lbl(3, tr("lay_url_prefix", "url_prefix (WMS)"));  v_prefix = entry(3)
    lbl(4, tr("lay_url_template", "url_template (TMS)"));v_template = entry(4)
    lbl(5, tr("lay_layers", "layers (WMS)"));      v_layers = entry(5)
    lbl(6, "epsg_code");         v_epsg = entry(6, "3857")
    lbl(7, "wms_size");          v_size = entry(7, "512")
    lbl(8, "wms_version");       v_ver = entry(8, "1.3.0")
    lbl(9, "image_type");        v_img = combo(9, ["jpeg", "png"], "jpeg")
    lbl(10, "imagery_dir");      v_dir = combo(10, ["grouped", "code"], "grouped")

    lbl(11, "in_GUI");           v_gui = combo(11, ["True", "False"], "True")

    status = tk.Label(win, text="", bg=BG, fg=FG2, anchor="w")
    status.grid(row=12, column=0, columnspan=2, sticky="ew", padx=8)

    def collect():
        fields = {
            "request_type": v_type.get().strip(),
            "url_prefix": v_prefix.get().strip(),
            "url_template": v_template.get().strip(),
            "layers": v_layers.get().strip(),
            "epsg_code": v_epsg.get().strip(),
            "wms_size": v_size.get().strip(),
            "wms_version": v_ver.get().strip(),
            "image_type": v_img.get().strip(),
            "imagery_dir": v_dir.get().strip(),
            "in_GUI": "True" if v_gui.get() == "True" else "False",
        }
        if fields["request_type"] == "tms":
            fields["grid_type"] = "webmercator"
        return fields

    def refresh_preview(*_):
        try:
            name = _safe_lay_name(v_name.get()) or "provider"
            txt = build_lay_text(collect())
            preview.configure(state="normal")
            preview.delete("1.0", "end")
            preview.insert("1.0", "# " + name + ".lay\n" + txt)
            preview.configure(state="disabled")
        except Exception:
            pass

    def _fill_from_data(data, name=""):
        """Remplit le formulaire à partir d'un dict de champs .lay."""
        v_type.set(data.get("request_type", "wms"))
        v_prefix.set(data.get("url_prefix", ""))
        v_template.set(data.get("url_template", ""))
        v_layers.set(data.get("layers", ""))
        v_epsg.set(data.get("epsg_code", "3857"))
        v_size.set(data.get("wms_size", data.get("tile_size", "512")))
        v_ver.set(data.get("wms_version", data.get("wmts_version", "1.3.0")))
        v_img.set(data.get("image_type", "jpeg"))
        v_dir.set(data.get("imagery_dir", "grouped"))
        v_gui.set("True" if str(data.get("in_GUI", "True")).lower() in ("true", "1", "yes") else "False")
        if name:
            v_name.set(name)

    def do_browse_providers():
        """Ouvre une fenêtre listant TOUS les .lay présents dans Providers/,
        lus en direct du disque (toujours à jour). Filtre + double-clic pour
        charger dans le formulaire. AUCUN preset codé en dur."""
        lays = scan_existing_lays()
        win2 = tk.Toplevel(win)
        win2.title(tr("lay_browse_title", "Providers existants"))
        win2.configure(bg=BG)

        tk.Label(win2, text=tr("lay_browse_filter", "🔍 Filtrer :"),
                 bg=BG, fg=FG).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        v_filter = tk.StringVar()
        tk.Entry(win2, textvariable=v_filter, width=40,
                 bg=ENTRY_BG, fg=ENTRY_FG).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        lst = tk.Listbox(win2, width=70, height=20, bg=CON_BG, fg=CON_FG,
                         selectbackground=FG2, selectforeground="#14241c",
                         highlightbackground=BG, highlightcolor=FG2,
                         relief="flat", bd=6, activestyle="none")
        lst.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 6))
        sb = tk.Scrollbar(win2, command=lst.yview, bg=BG,
                          troughcolor=CON_BG, activebackground=FG2)
        sb.grid(row=1, column=2, sticky="ns", pady=(0, 6))
        lst.config(yscrollcommand=sb.set)

        info = tk.Label(win2, text="", bg=BG, fg=FG2, anchor="w")
        info.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))

        # index courant : liste des tuples affichés (folder, name, path)
        shown = []

        def refresh_list(*_):
            flt = v_filter.get().strip().lower()
            # On tolère que l'utilisateur tape « Swisstopo.lay » : le nom stocké
            # est sans extension, donc on retire un « .lay » final du filtre.
            if flt.endswith(".lay"):
                flt = flt[:-4]
            lst.delete(0, "end")
            shown.clear()
            for folder, name, path in lays:
                label = ("[{}] {}".format(folder, name) if folder else name)
                if flt and flt not in label.lower():
                    continue
                shown.append((folder, name, path))
                lst.insert("end", label)
            info.config(text=tr("lay_browse_count", "Providers trouvés :")
                        + " {}".format(len(shown)))

        def load_selected(*_):
            sel = lst.curselection()
            if not sel:
                return
            folder, name, path = shown[sel[0]]
            try:
                data = parse_lay_text(open(path, encoding="utf-8").read())
            except Exception as e:
                messagebox.showerror("Provider (.lay)",
                        tr("lay_msg_read_err", "Lecture impossible :") + "\n{}".format(e))
                return
            _fill_from_data(data, name)
            status.config(text=tr("lay_browse_loaded", "Chargé depuis Providers :")
                          + " {}".format(name))
            win2.destroy()

        v_filter.trace_add("write", refresh_list)
        lst.bind("<Double-Button-1>", load_selected)

        btnrow = tk.Frame(win2, bg=BG)
        btnrow.grid(row=3, column=0, columnspan=3, pady=8)
        _make_themed_button(tk, btnrow, tr("lay_browse_load", "📥 Charger"),
                            load_selected).pack(side="left", padx=5)
        _make_themed_button(tk, btnrow, tr("lay_browse_close", "Fermer"),
                            win2.destroy).pack(side="left", padx=5)

        win2.grid_columnconfigure(1, weight=1)
        win2.grid_rowconfigure(1, weight=1)
        try:
            win2.transient(win)
        except Exception:
            pass
        _fixer_taille_min(win2)
        refresh_list()
        if not lays:
            info.config(text=tr("lay_browse_empty",
                    "Aucun .lay dans Providers/ pour l'instant. "
                    "Créez-en un avec ce générateur."))

        # Thème : utiliser la fonction officielle d'Ortho (récursive sur la
        # fenêtre), PUIS forcer la Listbox car apply_to_root ne la gère pas.
        if _HAS_THEME:
            try:
                _TM.apply_to_root(win2)
            except Exception:
                pass
            try:
                lst.configure(bg=CON_BG, fg=CON_FG, selectbackground=FG2,
                              selectforeground="#14241c")
                info.configure(bg=BG, fg=FG2)
            except Exception:
                pass

    def do_clear():
        for v in (v_name, v_prefix, v_template, v_layers):
            v.set("")
        v_type.set("wms"); v_epsg.set("3857"); v_size.set("512")
        v_ver.set("1.3.0"); v_img.set("jpeg"); v_dir.set("grouped"); v_gui.set("True")
        status.config(text="Formulaire effacé.")

    def do_load():
        # Ouvre le sélecteur dans Providers/ (ou Providers/<tuile active>/ si présent),
        # là où les .lay sont rangés — l'utilisateur n'a pas à chercher ailleurs.
        base = _providers_dir()
        tile_dir = os.path.join(base, _tile_name(cur_lat, cur_lon))
        initial = tile_dir if os.path.isdir(tile_dir) else base
        if not os.path.isdir(initial):
            initial = None
        path = filedialog.askopenfilename(
            title="Charger un .lay existant",
            initialdir=initial,
            filetypes=[("Fichiers LAY", "*.lay"), ("Tous", "*.*")])
        if not path:
            return
        try:
            data = parse_lay_text(open(path, encoding="utf-8").read())
        except Exception as e:
            messagebox.showerror("Provider (.lay)", "Lecture impossible :\n{}".format(e))
            return
        v_type.set(data.get("request_type", "wms"))
        v_prefix.set(data.get("url_prefix", ""))
        v_template.set(data.get("url_template", ""))
        v_layers.set(data.get("layers", ""))
        v_epsg.set(data.get("epsg_code", "3857"))
        v_size.set(data.get("wms_size", data.get("tile_size", "512")))
        v_ver.set(data.get("wms_version", data.get("wmts_version", "1.3.0")))
        v_img.set(data.get("image_type", "jpeg"))
        v_dir.set(data.get("imagery_dir", "grouped"))
        v_gui.set("True" if str(data.get("in_GUI", "True")).lower() in ("true", "1", "yes") else "False")
        v_name.set(os.path.splitext(os.path.basename(path))[0])
        status.config(text="Chargé : {}".format(os.path.basename(path)))

    def _choisir_dossier():
        d = filedialog.askdirectory(
            title=tr("lay_dest_pick", "Choisir un dossier provider"),
            initialdir=_providers_dir())
        if d:
            v_dest_dir.set(d)

    def do_create():
        name = v_name.get().strip()
        if not name:
            messagebox.showerror("Provider (.lay)",
                    tr("lay_msg_name_req", "Le nom du provider est obligatoire."))
            return
        fields = collect()
        problems = validate_fields(fields)
        if problems:
            messagebox.showerror("Provider (.lay)", "\n".join(problems))
            return
        ok, path, msg = write_lay(cur_lat, cur_lon, name, fields,
                                  overwrite=False, dest_dir=v_dest_dir.get())
        if not ok and msg == "EXISTS":
            if messagebox.askyesno("Provider (.lay)",
                    "Un fichier existe déjà :\n{}\n\nÉcraser ?".format(path)):
                ok, path, msg = write_lay(cur_lat, cur_lon, name, fields,
                                          overwrite=True, dest_dir=v_dest_dir.get())
            else:
                return
        if ok:
            messagebox.showinfo(
                "Provider (.lay)",
                tr("lay_msg_created", "Fichier créé :") + "\n" + path + "\n\n"
                + "⚠️ " + tr("lay_msg_restart",
                    "Fermez puis relancez Ortho4XP pour que la nouvelle "
                    "imagerie apparaisse dans le menu Imagery."))
            status.config(text=tr("lay_msg_created", "Fichier créé :") + " " + path)

    bar = tk.Frame(win, bg=BG)
    bar.grid(row=13, column=0, columnspan=2, pady=12)

    # Rangée : dossier de destination du .lay (défaut = tuile active) + choix.
    row_folder = tk.Frame(bar, bg=BG)
    row_folder.pack(side="top", pady=(0, 6))
    tk.Label(row_folder, text=tr("lay_dest_label", "Dossier provider :"),
             bg=BG, fg=FG2).pack(side="left", padx=(0, 4))
    tk.Label(row_folder, textvariable=v_dest_disp, bg=BG, fg=FG,
             font=("", 11, "bold")).pack(side="left", padx=(0, 8))
    _make_themed_button(tk, row_folder,
                        tr("lay_dest_btn", "📁 Autre dossier…"),
                        _choisir_dossier).pack(side="left")

    row_presets = tk.Frame(bar, bg=BG)
    row_presets.pack(side="top", pady=(0, 4))
    row_actions = tk.Frame(bar, bg=BG)
    row_actions.pack(side="top")
    _make_themed_button(tk, row_presets, tr("lay_btn_browse", "📋 Providers existants"), do_browse_providers).pack(side="left", padx=5)
    _make_themed_button(tk, row_actions, tr("lay_btn_load", "📂 Charger un .lay"), do_load).pack(side="left", padx=5)
    _make_themed_button(tk, row_actions, tr("lay_btn_clear", "🧹 Effacer"), do_clear).pack(side="left", padx=5)
    _make_themed_button(tk, row_actions, tr("lay_btn_create", "💾 Créer le .lay"), do_create).pack(side="left", padx=5)

    tk.Label(win, text=tr("lay_preview_label", "Aperçu du fichier .lay qui sera généré"),
             bg=BG, fg=FG2, anchor="w").grid(row=14, column=0, columnspan=2,
             sticky="ew", padx=8, pady=(6, 0))
    preview = tk.Text(win, height=10, width=54, bg=CON_BG, fg=CON_FG,
                      insertbackground=CON_FG, relief="flat", bd=6,
                      font=("Menlo", 11) if _OS == "mac" else ("Consolas", 10))
    preview.grid(row=15, column=0, columnspan=2, sticky="ew", padx=8, pady=(2, 10))
    for _v in (v_name, v_type, v_prefix, v_template, v_layers, v_epsg,
               v_size, v_ver, v_img, v_dir, v_gui):
        _v.trace_add("write", refresh_preview)
    refresh_preview()

    win.grid_columnconfigure(1, weight=1)
    _fixer_taille_min(win)
    if parent is None:
        win.mainloop()
