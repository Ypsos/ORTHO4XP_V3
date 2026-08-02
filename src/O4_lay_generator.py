#============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland  (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland  (Ypsos) for # Ortho4XP
#============================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O4_lay_generator.py
Ortho4XP V3 - Générateur de fichiers .lay (format custom / O4_Custom_URL)
Contribution Grok pour Ypsos
Lancement possible depuis Ortho4XP ou en autonome.
Utilise O4_Theme_Manager pour les couleurs + gestion spécifique boutons macOS.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys

# ------------------------------------------------------------------
# Thème Ortho4XP V3 (avec fallback si module absent)
# ------------------------------------------------------------------
try:
    import O4_Theme_Manager as THEME
    _HAS_THEME = True
except ImportError:
    _HAS_THEME = False

# Détection OS (même logique que O4_Theme_Manager)
if "dar" in sys.platform:
    _OS = "mac"
elif "win" in sys.platform:
    _OS = "windows"
else:
    _OS = "linux"


def _c(key, fallback="#ffffff"):
    """Couleur du thème actif, ou fallback si Theme Manager absent."""
    if _HAS_THEME:
        return THEME.get_color(key, fallback)
    return fallback


def _guess_providers_dir():
    """Essaie de trouver le dossier Providers à côté de ce script ou dans Ortho4XP_Data."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Providers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Providers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "_internal", "Ortho4XP_Data", "Providers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ortho4XP_Data", "Providers"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return None


# ------------------------------------------------------------------
# Bouton compatible multiplateforme (surtout macOS)
# Sur macOS, tk.Button ignore souvent bg/fg (Aqua natif).
# On utilise donc un Frame + Label cliquable sur Mac, et un vrai Button ailleurs.
# ------------------------------------------------------------------
class ThemedButton(tk.Frame):
    """Bouton thématisé, fiable sur macOS / Windows / Linux."""

    def __init__(self, parent, text="", command=None, width=None, **kwargs):
        bg = _c("btn_bg", "#4a6b59")
        fg = _c("btn_fg", "#ffffff")
        hover = _c("btn_hover", "#5a7b69")
        active = _c("btn_active", "#a6e3a1")
        border = _c("border", "#4a6b59")

        super().__init__(parent, bg=bg, highlightthickness=1,
                         highlightbackground=border, highlightcolor=active, bd=0)

        self._command = command
        self._bg = bg
        self._hover = hover
        self._active = active
        self._fg = fg

        self._label = tk.Label(
            self, text=text, bg=bg, fg=fg,
            padx=10, pady=4,
            font=("Segoe UI", 10) if _OS != "mac" else ("Helvetica", 12),
            cursor="hand2"
        )
        if width:
            self._label.configure(width=width)
        self._label.pack(fill=tk.BOTH, expand=True)

        # Bindings
        for w in (self, self._label):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event=None):
        self.configure(bg=self._hover)
        self._label.configure(bg=self._hover)

    def _on_leave(self, event=None):
        self.configure(bg=self._bg)
        self._label.configure(bg=self._bg)

    def _on_click(self, event=None):
        self.configure(bg=self._active)
        self._label.configure(bg=self._active)

    def _on_release(self, event=None):
        self.configure(bg=self._hover)
        self._label.configure(bg=self._hover)
        if self._command:
            self._command()

    def configure_text(self, text):
        self._label.configure(text=text)


class LayGeneratorApp:
    def __init__(self, root, providers_dir=None):
        self.root = root
        self.root.title("Ortho4XP V3 — Générateur de fichiers .lay")
        self.root.geometry("840x800")
        self.root.minsize(740, 660)

        self.providers_dir = providers_dir or _guess_providers_dir()

        # Couleurs thème
        bg = _c("bg", "#3b5b49")
        bg2 = _c("bg_secondary", "#2a4235")
        fg = _c("fg", "#e8f0ec")
        fg2 = _c("fg_secondary", "#a6e3a1")
        console_bg = _c("console_bg", "#0f0f1a")
        console_fg = _c("console_fg", "#50fa7b")
        border = _c("border", "#4a6b59")
        accent = _c("accent", "#a6e3a1")

        self.root.configure(bg=bg)

        # Style ttk (pour Combobox, etc.)
        style = ttk.Style()
        # Sur Mac, 'clam' se comporte mieux que 'aqua' pour les couleurs
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg2)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TRadiobutton", background=bg, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TEntry", fieldbackground=bg2, foreground=fg)
        style.configure("TCombobox", fieldbackground=bg2, foreground=fg, background=bg2)
        style.map("TCombobox", fieldbackground=[("readonly", bg2)])
        style.configure("Status.TLabel", background=bg2, foreground=fg2, relief="sunken")

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # === Titre ===
        title = ttk.Label(main, text="Générateur de provider .lay (format custom / O4_Custom_URL)",
                          font=("Segoe UI", 13, "bold") if _OS != "mac" else ("Helvetica", 14, "bold"))
        title.pack(pady=(0, 8))

        # === Formulaire ===
        form = ttk.LabelFrame(main, text="Paramètres du fichier .lay", padding=10)
        form.pack(fill=tk.X, pady=5)

        row = 0
        ttk.Label(form, text="Nom du provider (fichier) :").grid(row=row, column=0, sticky="w", pady=4)
        self.code_var = tk.StringVar(value="PCRS_IGN")
        e = ttk.Entry(form, textvariable=self.code_var, width=45)
        e.grid(row=row, column=1, sticky="ew", pady=4, padx=5)
        ttk.Label(form, text="→ génère PCRS_IGN.lay").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(form, text="request_type :").grid(row=row, column=0, sticky="w", pady=4)
        self.request_type = tk.StringVar(value="wms")
        type_frame = ttk.Frame(form)
        type_frame.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        ttk.Radiobutton(type_frame, text="wms", variable=self.request_type, value="wms",
                        command=self.update_preview).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="tms", variable=self.request_type, value="tms",
                        command=self.update_preview).pack(side=tk.LEFT, padx=12)

        row += 1
        ttk.Label(form, text="url_prefix :").grid(row=row, column=0, sticky="w", pady=4)
        self.url_prefix = tk.StringVar(value="custom")
        ttk.Entry(form, textvariable=self.url_prefix, width=45).grid(row=row, column=1, sticky="ew", pady=4, padx=5)
        ttk.Label(form, text="(custom = passe par O4_Custom_URL.py)").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(form, text="wms_size :").grid(row=row, column=0, sticky="w", pady=4)
        self.wms_size = tk.StringVar(value="512")
        ttk.Entry(form, textvariable=self.wms_size, width=12).grid(row=row, column=1, sticky="w", pady=4, padx=5)

        row += 1
        ttk.Label(form, text="wms_version :").grid(row=row, column=0, sticky="w", pady=4)
        self.wms_version = tk.StringVar(value="1.3.0")
        ttk.Combobox(form, textvariable=self.wms_version, values=["1.3.0", "1.1.1", "1.1.0"],
                     width=12, state="readonly").grid(row=row, column=1, sticky="w", pady=4, padx=5)

        row += 1
        ttk.Label(form, text="epsg_code :").grid(row=row, column=0, sticky="w", pady=4)
        self.epsg_code = tk.StringVar(value="3857")
        ttk.Entry(form, textvariable=self.epsg_code, width=12).grid(row=row, column=1, sticky="w", pady=4, padx=5)
        ttk.Label(form, text="(3857 = Web Mercator)").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(form, text="layers :").grid(row=row, column=0, sticky="w", pady=4)
        self.layers = tk.StringVar(value="PCRS.LAMB93")
        ttk.Entry(form, textvariable=self.layers, width=45).grid(row=row, column=1, sticky="ew", pady=4, padx=5)

        row += 1
        ttk.Label(form, text="imagery_dir :").grid(row=row, column=0, sticky="w", pady=4)
        self.imagery_dir = tk.StringVar(value="code")
        ttk.Combobox(form, textvariable=self.imagery_dir, values=["code", "grouped", ""],
                     width=42, state="readonly").grid(row=row, column=1, sticky="w", pady=4, padx=5)
        ttk.Label(form, text="(code = dossier au nom du provider)").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(form, text="max_threads :").grid(row=row, column=0, sticky="w", pady=4)
        self.max_threads = tk.StringVar(value="8")
        ttk.Entry(form, textvariable=self.max_threads, width=12).grid(row=row, column=1, sticky="w", pady=4, padx=5)

        row += 1
        self.in_gui = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="in_GUI = True (afficher dans la liste Ortho4XP)",
                        variable=self.in_gui).grid(row=row, column=1, sticky="w", pady=4, padx=5)

        form.columnconfigure(1, weight=1)

        # === Boutons (ThemedButton = fiable sur Mac) ===
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=12)

        buttons = [
            ("Mettre à jour l'aperçu", self.update_preview),
            ("Enregistrer sous…", self.save_as),
            ("Enregistrer dans Providers", self.save_to_providers),
            ("Charger un .lay", self.load_lay),
            ("Preset PCRS_IGN", self.load_preset_pcrs),
            ("Effacer", self.clear_form),
        ]
        for text, cmd in buttons:
            b = ThemedButton(btn_frame, text=text, command=cmd)
            b.pack(side=tk.LEFT, padx=4, pady=2)

        # === Aperçu ===
        preview_frame = ttk.LabelFrame(main, text="Aperçu du fichier .lay qui sera généré", padding=8)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview = scrolledtext.ScrolledText(
            preview_frame, height=12, wrap=tk.NONE,
            font=("Menlo", 11) if _OS == "mac" else ("Consolas", 11),
            bg=console_bg, fg=console_fg,
            insertbackground=fg,
            relief="flat", bd=0
        )
        self.preview.pack(fill=tk.BOTH, expand=True)

        for var in (self.code_var, self.request_type, self.url_prefix, self.wms_size,
                    self.wms_version, self.epsg_code, self.layers, self.imagery_dir,
                    self.max_threads, self.in_gui):
            var.trace_add("write", lambda *a: self.update_preview())

        self.update_preview()

        # Status
        status_text = "Prêt"
        if self.providers_dir:
            status_text += f"  —  Providers : {self.providers_dir}"
        else:
            status_text += "  —  Dossier Providers non trouvé automatiquement"
        if _HAS_THEME:
            status_text += f"  |  Thème : {THEME.current_theme_name()}"
        status_text += f"  |  OS : {_OS}"

        self.status = ttk.Label(main, text=status_text, style="Status.TLabel", anchor="w")
        self.status.pack(fill=tk.X, pady=(6, 0))

        # Appliquer le thème récursif si disponible
        if _HAS_THEME:
            try:
                THEME.apply_to_root(self.root)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Logique métier
    # ------------------------------------------------------------------
    def get_lay_content(self):
        lines = []
        lines.append(f"request_type={self.request_type.get().strip()}")
        lines.append(f"url_prefix={self.url_prefix.get().strip()}")
        lines.append(f"wms_size={self.wms_size.get().strip()}")
        lines.append(f"wms_version={self.wms_version.get().strip()}")
        lines.append(f"epsg_code={self.epsg_code.get().strip()}")
        lines.append(f"layers={self.layers.get().strip()}")
        lines.append(f"imagery_dir={self.imagery_dir.get().strip()}")
        lines.append(f"max_threads={self.max_threads.get().strip()}")
        if self.in_gui.get():
            lines.append("in_GUI=True")
        return "\n".join(lines) + "\n"

    def update_preview(self, *args):
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", self.get_lay_content())

    def _write_lay(self, path):
        content = self.get_lay_content()
        if os.path.exists(path):
            if not messagebox.askyesno("Fichier existant", f"{os.path.basename(path)} existe déjà.\nÉcraser ?"):
                return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status.config(text=f"Enregistré : {path}")
            messagebox.showinfo("Succès", f"Fichier créé :\n{path}\n\nRedémarre Ortho4XP pour le voir apparaître.")
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'écrire le fichier :\n{e}")
            return False

    def save_as(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showerror("Erreur", "Le nom du provider est obligatoire.")
            return
        folder = filedialog.askdirectory(title="Choisir le dossier de destination (Providers ou Providers/Custom)")
        if not folder:
            return
        self._write_lay(os.path.join(folder, f"{code}.lay"))

    def save_to_providers(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showerror("Erreur", "Le nom du provider est obligatoire.")
            return

        folder = self.providers_dir
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Dossier Providers non trouvé — choisis-le manuellement")
            if not folder:
                return
            self.providers_dir = folder

        custom = os.path.join(folder, "Custom")
        if os.path.isdir(custom):
            folder = custom

        self._write_lay(os.path.join(folder, f"{code}.lay"))

    def load_lay(self):
        path = filedialog.askopenfilename(
            title="Charger un fichier .lay existant",
            filetypes=[("Fichiers LAY", "*.lay"), ("Tous les fichiers", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            data = {}
            for line in content.splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()

            if "request_type" in data: self.request_type.set(data["request_type"])
            if "url_prefix" in data: self.url_prefix.set(data["url_prefix"])
            if "wms_size" in data: self.wms_size.set(data["wms_size"])
            if "wms_version" in data: self.wms_version.set(data["wms_version"])
            if "epsg_code" in data: self.epsg_code.set(data["epsg_code"])
            if "layers" in data: self.layers.set(data["layers"])
            if "imagery_dir" in data: self.imagery_dir.set(data["imagery_dir"])
            if "max_threads" in data: self.max_threads.set(data["max_threads"])
            if "in_GUI" in data:
                self.in_gui.set(data["in_GUI"].lower() in ("true", "1", "yes"))

            self.code_var.set(os.path.splitext(os.path.basename(path))[0])
            self.update_preview()
            self.status.config(text=f"Chargé : {path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier :\n{e}")

    def load_preset_pcrs(self):
        self.code_var.set("PCRS_IGN")
        self.request_type.set("wms")
        self.url_prefix.set("custom")
        self.wms_size.set("512")
        self.wms_version.set("1.3.0")
        self.epsg_code.set("3857")
        self.layers.set("PCRS.LAMB93")
        self.imagery_dir.set("code")
        self.max_threads.set("8")
        self.in_gui.set(True)
        self.update_preview()
        self.status.config(text="Preset PCRS_IGN chargé")

    def clear_form(self):
        self.code_var.set("")
        self.request_type.set("wms")
        self.url_prefix.set("custom")
        self.wms_size.set("512")
        self.wms_version.set("1.3.0")
        self.epsg_code.set("3857")
        self.layers.set("")
        self.imagery_dir.set("code")
        self.max_threads.set("8")
        self.in_gui.set(True)
        self.update_preview()
        self.status.config(text="Formulaire effacé")


def run_lay_generator(parent=None, providers_dir=None):
    """
    Point d'entrée pour Ortho4XP V3.
        from O4_lay_generator import run_lay_generator
        run_lay_generator(parent=self.root, providers_dir=chemin_Providers)
    """
    if parent is None:
        root = tk.Tk()
        LayGeneratorApp(root, providers_dir=providers_dir)
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        LayGeneratorApp(win, providers_dir=providers_dir)
        win.transient(parent)
        win.grab_set()
        parent.wait_window(win)


if __name__ == "__main__":
    run_lay_generator()