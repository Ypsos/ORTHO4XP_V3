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
        if key in fields and str(fields[key]).strip() != "":
            lines.append("{}={}".format(key, fields[key]))
    return "\n".join(lines) + "\n"

def target_path(lat, lon, provider_name: str) -> str:
    tile = _tile_name(lat, lon)
    safe = "".join(c for c in provider_name if c.isalnum() or c in "-_ ").strip()
    if not safe:
        safe = "provider"
    return os.path.join(_providers_dir(), tile, safe + ".lay")

def write_lay(lat, lon, provider_name: str, fields: dict, overwrite=False):
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

# ===========================================================================
# BOUTON THÉMATISÉ (fiable macOS : tk.Button ignore souvent bg/fg en Aqua)
# ===========================================================================
def _make_themed_button(tk, parent, text, command):
    bg     = _c("btn_bg", "#4a6b59")
    fg     = _c("btn_fg", "#ffffff")
    hover  = _c("accent", "#5a7b69")
    active = _c("fg_secondary", "#a6e3a1")
    border = _c("btn_bg", "#4a6b59")

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
    win.resizable(False, False)

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

    v_gui = tk.BooleanVar(value=True)
    tk.Checkbutton(win, text=tr("lay_in_gui", "Afficher dans le menu (in_GUI)"), variable=v_gui,
                   bg=BG, fg=FG, selectcolor=BG, activebackground=BG,
                   activeforeground=FG, highlightthickness=0).grid(
                   row=11, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 2))

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
            "in_GUI": "True" if v_gui.get() else "False",
        }
        if fields["request_type"] == "tms":
            fields["grid_type"] = "webmercator"
        return fields

    def refresh_preview(*_):
        try:
            name = v_name.get().strip() or "provider"
            txt = build_lay_text(collect())
            preview.configure(state="normal")
            preview.delete("1.0", "end")
            preview.insert("1.0", "# " + name + ".lay\n" + txt)
            preview.configure(state="disabled")
        except Exception:
            pass

    def do_preset_pcrs():
        v_name.set("PCRS_IGN"); v_type.set("wms")
        v_prefix.set("custom"); v_layers.set("PCRS.LAMB93")
        v_epsg.set("3857"); v_size.set("512"); v_ver.set("1.3.0")
        v_img.set("png"); v_dir.set("code"); v_gui.set(True)
        status.config(text="Preset PCRS_IGN chargé (PCRS nécessite O4_Custom_URL.py).")

    def do_preset_ign_ortho():
        # Ortho IGN France entière + DOM-TOM (WMTS tuilé, TMS webmercator).
        # Source directe : aucun O4_Custom_URL.py nécessaire.
        # Contributeur : domisilasol (Dominique) — X-Plane.fr, 08/2026.
        v_name.set("IGN_Ortho_France"); v_type.set("tms")
        v_template.set(
            "https://data.geopf.fr/wmts?&SERVICE=WMTS&VERSION=1.0.0"
            "&REQUEST=GetTile&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal"
            "&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={zoom}"
            "&TILEROW={y}&TILECOL={x}")
        v_prefix.set(""); v_layers.set("")
        v_epsg.set("3857"); v_size.set("512"); v_ver.set("1.3.0")
        v_img.set("jpeg"); v_dir.set("grouped"); v_gui.set(True)
        status.config(text="Preset IGN Ortho France chargé (France + DOM-TOM) "
                            "— contributeur : domisilasol.")

    def do_clear():
        for v in (v_name, v_prefix, v_template, v_layers):
            v.set("")
        v_type.set("wms"); v_epsg.set("3857"); v_size.set("512")
        v_ver.set("1.3.0"); v_img.set("jpeg"); v_dir.set("grouped"); v_gui.set(True)
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
        v_gui.set(str(data.get("in_GUI", "True")).lower() in ("true", "1", "yes"))
        v_name.set(os.path.splitext(os.path.basename(path))[0])
        status.config(text="Chargé : {}".format(os.path.basename(path)))

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
        ok, path, msg = write_lay(cur_lat, cur_lon, name, fields, overwrite=False)
        if not ok and msg == "EXISTS":
            if messagebox.askyesno("Provider (.lay)",
                    "Un fichier existe déjà :\n{}\n\nÉcraser ?".format(path)):
                ok, path, msg = write_lay(cur_lat, cur_lon, name, fields, overwrite=True)
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
    _make_themed_button(tk, bar, tr("lay_btn_pcrs", "🛰 Preset PCRS_IGN"), do_preset_pcrs).pack(side="left", padx=5)
    _make_themed_button(tk, bar, tr("lay_btn_ign", "🇫🇷 Preset IGN Ortho"), do_preset_ign_ortho).pack(side="left", padx=5)
    _make_themed_button(tk, bar, tr("lay_btn_load", "📂 Charger un .lay"), do_load).pack(side="left", padx=5)
    _make_themed_button(tk, bar, tr("lay_btn_clear", "🧹 Effacer"), do_clear).pack(side="left", padx=5)
    _make_themed_button(tk, bar, tr("lay_btn_create", "💾 Créer le .lay"), do_create).pack(side="left", padx=5)

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
    if parent is None:
        win.mainloop()
