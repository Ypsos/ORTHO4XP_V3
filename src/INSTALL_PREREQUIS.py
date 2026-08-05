#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════╗
║   Ortho4XP V3.0 — INSTALLATION PRÉREQUIS              ║
║   Bootstrap autonome multiplateforme                 ║
║   Roland (Ypsos) — Mars 2026                 ║
║   macOS (Apple Silicon + Intel) / Windows / Linux    ║
╚══════════════════════════════════════════════════════╝

Ce script est le PREMIER fichier lancé par l'utilisateur.
Il ne dépend d'aucun module externe — uniquement stdlib Python.
Compatible Python 3.8+ (détecte et installe 3.12 si absent).
"""

import os
import sys
import platform
import subprocess
import shutil
import threading
import webbrowser
import datetime
from pathlib import Path

# ── tkinter : présent dans toute stdlib Python standard ──────────────────────
try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION VISUELLE — identique au Launcher
# ══════════════════════════════════════════════════════════════════════════════
BG_GLOBAL    = "#3b5b49"
BTN_COLOR    = "#4a6b59"
BTN_HOVER    = "#5a7b69"
BTN_TEXT     = "white"
SHADOW_COLOR = "#2a4235"
GREEN_OK     = "#a6e3a1"
RED_ERR      = "#ff5555"
YELLOW_WARN  = "#f1fa8c"
TEXT_BG      = "#0f0f1a"
TEXT_FG      = "#50fa7b"

# Modules essentiels vérifiés au démarrage
ESSENTIAL_MODULES = ("psutil", "numpy", "PIL", "customtkinter", "requests", "shapely")

# ══════════════════════════════════════════════════════════════════════════════
#  CHEMINS — VERSION UNIVERSELLE MULTI-OS (Correction principale)
# ══════════════════════════════════════════════════════════════════════════════
# Détection robuste du dossier de base (fonctionne avec .app sur macOS)
if getattr(sys, 'frozen', False) and platform.system() == "Darwin":
    # Cas lancé depuis l'application bundle INSTALL_Prerequis.app
    BASE_DIR = Path(sys.executable).resolve().parent.parent.parent
else:
    # Cas normal (lancé directement avec python)
    BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__))).resolve()

BASE_DIR = BASE_DIR.resolve()   # Assure un chemin propre

SYSTEM    = platform.system()          # "Darwin" / "Windows" / "Linux"
MACHINE   = platform.machine().lower() # "arm64" / "x86_64" / "amd64"

LAUNCHER_PY = BASE_DIR / "Ortho4XP_Launcher.py"
VENV_DIR    = BASE_DIR / "venv"

if SYSTEM == "Windows":
    VENV_PY = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PY = VENV_DIR / "bin" / "python3"

# ══════════════════════════════════════════════════════════════════════════════
#  FICHIER LOG — ortho4xp_install.log a la racine (multi-OS, stdlib only)
# ══════════════════════════════════════════════════════════════════════════════
LOG_FILE = BASE_DIR / "ortho4xp_install.log"


def _append_log_file(msg):
    """Ajoute une ligne au fichier log a la racine. Silencieux en cas d'echec."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass


def _init_log_session(mode):
    """Ecrit un en-tete de session horodate (n'efface jamais l'historique)."""
    try:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write("  SESSION {} — {}\n".format(mode, stamp))
            f.write("  Plateforme : {} / {}\n".format(SYSTEM, MACHINE))
            f.write("  Dossier    : {}\n".format(BASE_DIR))
            f.write("=" * 70 + "\n")
    except Exception:
        pass


def _open_log_for_subprocess():
    """Retourne un handle fichier en append pour rediriger un sous-processus
    (ex. le Launcher) vers le log, ou None si echec (lancement sans redirection)."""
    try:
        return open(LOG_FILE, "a", encoding="utf-8", errors="replace")
    except Exception:
        return None


def _check_modules_ok():
    """Vérifie que les modules essentiels sont importables dans le venv."""
    if not VENV_PY.exists():
        return False
    try:
        mods = ", ".join(ESSENTIAL_MODULES)
        code = "import " + mods.replace("PIL", "PIL")  # PIL = package Pillow
        # PIL s'importe via "from PIL" ou "import PIL" selon versions
        code = (
            "import psutil, numpy, requests, shapely, customtkinter; "
            "from PIL import Image"
        )
        r = subprocess.run(
            [str(VENV_PY), "-c", code],
            capture_output=True, timeout=8
        )
        return r.returncode == 0
    except Exception:
        return False


def _build_launch_env():
    """Construit l'environnement pour lancer Ortho4XP_Launcher."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR / "src")
    if SYSTEM == "Darwin":
        brew = find_homebrew()
        if brew:
            try:
                r = subprocess.run(
                    [brew, "--prefix", "gdal"],
                    capture_output=True, text=True, timeout=10
                )
                if r.returncode == 0 and r.stdout.strip():
                    gdal_lib = r.stdout.strip() + "/lib"
                    env["DYLD_LIBRARY_PATH"] = (
                        gdal_lib + ":" + env.get("DYLD_LIBRARY_PATH", "")
                    )
            except Exception:
                pass
    return env


def _launch_ortho4xp(py_exe=None):
    """Lance Ortho4XP_Launcher.py de façon détachée. Retourne True si OK."""
    if not LAUNCHER_PY.exists():
        return False
    if py_exe is None:
        py_exe = str(VENV_PY) if VENV_PY.exists() else find_python312()
    if not py_exe:
        return False
    env = _build_launch_env()
    _logf = _open_log_for_subprocess()
    kwargs = {
        "cwd": str(BASE_DIR),
        "env": env,
    }
    if _logf:
        kwargs["stdout"] = _logf
        kwargs["stderr"] = subprocess.STDOUT
    # Détachement propre du processus
    if SYSTEM == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([str(py_exe), str(LAUNCHER_PY)], **kwargs)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES SYSTÈME
# ══════════════════════════════════════════════════════════════════════════════

def find_python312():
    """Cherche python3.12 ou 3.11 sur le systeme. Retourne le chemin ou None."""
    candidates = []
    if SYSTEM == "Darwin":
        candidates = [
            # Python 3.12 Apple Silicon Homebrew
            "/opt/homebrew/bin/python3.12",
            "/opt/homebrew/opt/python@3.12/bin/python3.12",
            # Python 3.12 Intel Homebrew
            "/usr/local/bin/python3.12",
            "/usr/local/opt/python@3.12/bin/python3.12",
            # Python 3.11 Apple Silicon Homebrew
            "/opt/homebrew/bin/python3.11",
            "/opt/homebrew/opt/python@3.11/bin/python3.11",
            # Python 3.11 Intel Homebrew
            "/usr/local/bin/python3.11",
            "/usr/local/opt/python@3.11/bin/python3.11",
            # Python 3.11 / 3.12 installeur python.org
            "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12",
            "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11",
            "/usr/bin/python3.12",
            "/usr/bin/python3.11",
            # Fallback python3 systeme
            "/usr/bin/python3",
            "/usr/local/bin/python3",
        ]
    elif SYSTEM == "Windows":
        for name in ["python3.12", "python3.11", "python"]:
            path = shutil.which(name)
            if path:
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True, text=True, timeout=5
                    )
                    ver = result.stdout + result.stderr
                    if "3.12" in ver or "3.11" in ver:
                        return path
                except Exception:
                    pass
        user = os.environ.get("USERNAME", "user")
        candidates = [
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(user),
            r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(user),
        ]
    else:  # Linux
        candidates = [
            "/usr/bin/python3.12",
            "/usr/local/bin/python3.12",
            "/usr/bin/python3.11",
            "/usr/local/bin/python3.11",
        ]
        for name in ("python3.12", "python3.11"):
            path = shutil.which(name)
            if path:
                return path

    for c in candidates:
        p = Path(c)
        if p.exists():
            return str(p)
    return None


def find_homebrew():
    """Retourne le chemin de brew ou None."""
    for p in ["/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
        if Path(p).exists():
            return p
    return shutil.which("brew")


def run_cmd(cmd, log_fn=print, env=None, cwd=None, timeout=600):
    """Lance une commande, streame la sortie vers log_fn. Retourne le code retour.
    timeout en secondes (défaut 10 min) pour éviter les blocages infinis."""
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env=env, cwd=cwd,
            encoding="utf-8", errors="replace"
        )
        try:
            for line in proc.stdout:
                log_fn(line.rstrip())
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            log_fn("❌ Timeout ({}s) — commande interrompue.".format(timeout))
            return 1
        return proc.returncode if proc.returncode is not None else 1
    except FileNotFoundError as e:
        log_fn("❌ Commande introuvable : {}".format(e))
        return 1
    except Exception as e:
        log_fn("❌ Erreur : {}".format(e))
        return 1


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIQUE D'INSTALLATION PAR PLATEFORME
# ══════════════════════════════════════════════════════════════════════════════
class Installer:
    """Encapsule toute la logique d'installation."""

    def __init__(self, log_fn=print, progress_fn=None, done_fn=None):
        self.log      = log_fn
        self.progress = progress_fn
        self.done_fn  = done_fn
        self.python312 = None

    def _show_tkinter_status_dialog(self, is_present):
        if not HAS_TK:
            if is_present:
                print("\n✅ Tkinter est installé.")
                input("Appuyez sur Entrée pour continuer...")
            else:
                print("\n❌ Tkinter est absent.")
                print("Veuillez exécuter cette commande dans le Terminal :")
                print("   brew install python-tk@3.12")
                print("\nPuis relancez l'application.")
                input("Appuyez sur Entrée pour quitter...")
            return

        dialog = tk.Toplevel()
        dialog.title("Vérification Tkinter - macOS")
        dialog.configure(bg=BG_GLOBAL)
        dialog.geometry("650x420")
        dialog.resizable(False, False)

        if is_present:
            title = "✅ Tkinter est installé"
            color = GREEN_OK
            msg = "Tkinter est OK.\n\nCliquez sur le bouton pour continuer l'installation."
            btn_text = "✅ Continuer l'installation"
        else:
            title = "❌ Tkinter est absent"
            color = RED_ERR
            msg = (
                "Tkinter n'est pas installé.\n\n"
                "Copiez cette commande dans le Terminal :\n\n"
                "   brew install python-tk@3.12\n\n"
                "Puis relancez l'application après l'installation."
            )
            btn_text = "📋 Copier la commande"

        tk.Label(dialog, text=title, font=("Helvetica", 16, "bold"),
                 fg=color, bg=BG_GLOBAL).pack(pady=25)

        txt = tk.Text(dialog, height=10, bg=TEXT_BG, fg=TEXT_FG,
                      font=("Courier", 11), wrap="word")
        txt.pack(padx=40, pady=10, fill="both", expand=True)
        txt.insert("1.0", msg)
        txt.config(state="disabled")

        def action():
            if not is_present:
                dialog.clipboard_clear()
                dialog.clipboard_append("brew install python-tk@3.12")
                dialog.update()
                btn.config(text="✅ Commande copiée !")
                dialog.after(2000, lambda: btn.config(text=btn_text))
            else:
                dialog.destroy()

        btn = tk.Button(dialog, text=btn_text, command=action,
                        bg="#4a6b59", fg="black",
                        font=("Helvetica", 13, "bold"), height=2)
        btn.pack(pady=20)

        dialog.grab_set()
        dialog.wait_window()

    def _check_tkinter_mac(self):
        if SYSTEM != "Darwin":
            return True

        self.log("── 🔍 Vérification de Tkinter sur macOS ──────────────────────")

        python_to_check = self.python312 or find_python312()
        if not python_to_check:
            return True

        tk_present = False
        try:
            result = subprocess.run(
                [python_to_check, "-c", "import tkinter"],
                capture_output=True, text=True, timeout=8
            )
            tk_present = result.returncode == 0
        except Exception:
            pass

        self._show_tkinter_status_dialog(tk_present)

        if not tk_present:
            self._finish(False, "Installation arrêtée : Tkinter requis sur macOS")
            return False

        return True

    def run(self):
        self.log("🖥  Plateforme : {} / {}".format(SYSTEM, MACHINE))
        self.log("📍 Dossier    : {}".format(BASE_DIR))
        self.log("")

        if not self._check_tkinter_mac():
            return

        if SYSTEM == "Darwin":
            self._install_mac()
        elif SYSTEM == "Windows":
            self._install_windows()
        elif SYSTEM == "Linux":
            self._install_linux()
        else:
            self._finish(False, "Plateforme non supportée : {}".format(SYSTEM))

    # ── macOS ─────────────────────────────────────────────────────────────────
    def _install_mac(self):
        self.log("── 🍎 macOS détecté ──────────────────────────")

        self.python312 = find_python312()
        if self.python312:
            self.log("✅ Python trouvé : {}".format(self.python312))
            self._set_progress(25)
        else:
            self.log("⚠️  Python 3.12/3.11 absent. Installation via Homebrew...")
            brew = find_homebrew()
            if not brew:
                self.log("⚠️  Homebrew absent. Installation en cours...")
                self.log("   (peut demander votre mot de passe Mac)")
                rc = run_cmd(
                    ["/bin/bash", "-c",
                     'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash'],
                    self.log, timeout=900
                )
                brew = find_homebrew()
                if not brew:
                    self._finish(
                        False,
                        "❌ Impossible d'installer Homebrew.\n"
                        "Installez-le manuellement : https://brew.sh"
                    )
                    return
            self.log("✅ Homebrew trouvé : {}".format(brew))
            self._set_progress(20)

            self.log("📦 Installation python@3.12 et python-tk@3.12...")
            rc = run_cmd(
                [brew, "install", "python@3.12", "python-tk@3.12"],
                self.log, timeout=900
            )
            self.python312 = find_python312()
            if not self.python312 or rc != 0:
                self._finish(
                    False,
                    "❌ Échec installation Python 3.12.\n"
                    "Ouvrez un Terminal et tapez :\n"
                    "brew install python@3.12 python-tk@3.12"
                )
                return
            self.log("✅ Python 3.12 installé : {}".format(self.python312))
            self._set_progress(40)

        self._create_venv()
        if not self._venv_ok():
            return
        self._set_progress(60)

        self._install_requirements()
        self._set_progress(80)

        self._install_gdal_mac(find_homebrew())
        self._set_progress(90)

        self._launch_launcher()

    # ── Windows ───────────────────────────────────────────────────────────────
    def _install_windows(self):
        self.log("── 🪟 Windows détecté ────────────────────────")
        self.python312 = find_python312()
        if self.python312:
            self.log("✅ Python trouvé : {}".format(self.python312))
            self._set_progress(25)
        else:
            self.log("⚠️  Python 3.12/3.11 absent. Tentative via winget...")
            rc = run_cmd(
                ["winget", "install", "--id", "Python.Python.3.12",
                 "--silent", "--accept-package-agreements",
                 "--accept-source-agreements"],
                self.log, timeout=600
            )
            self.python312 = find_python312()
            if not self.python312:
                webbrowser.open(
                    "https://www.python.org/downloads/release/python-3120/"
                )
                self._finish(
                    False,
                    "⚠️ Installation automatique impossible.\n"
                    "La page de téléchargement Python 3.12 vient de s'ouvrir.\n"
                    "Installez-le puis relancez ce programme.\n"
                    "⚠️ Cochez 'Add Python to PATH' !"
                )
                return
            self.log("✅ Python installé : {}".format(self.python312))
            self._set_progress(40)

        self._create_venv()
        if not self._venv_ok():
            return
        self._set_progress(60)
        self._install_requirements()
        self._set_progress(85)
        self._launch_launcher()

    # ── Linux ─────────────────────────────────────────────────────────────────
    def _install_linux(self):
        self.log("── 🐧 Linux détecté ──────────────────────────")
        self.python312 = find_python312()
        if not self.python312:
            self.log("⚠️  Python 3.12/3.11 absent. Installation via gestionnaire de paquets...")
            self.log("   (peut demander votre mot de passe sudo)")
            if shutil.which("apt-get"):
                run_cmd(["sudo", "apt-get", "update", "-y"], self.log, timeout=300)
                run_cmd(
                    ["sudo", "apt-get", "install", "-y",
                     "python3.12", "python3.12-venv", "python3-pip",
                     "python3-tk", "p7zip-full", "gdal-bin", "libgdal-dev"],
                    self.log, timeout=600
                )
            elif shutil.which("dnf"):
                run_cmd(
                    ["sudo", "dnf", "install", "-y",
                     "python3.12", "python3-tkinter", "gdal", "gdal-devel"],
                    self.log, timeout=600
                )
            elif shutil.which("pacman"):
                run_cmd(
                    ["sudo", "pacman", "-S", "--noconfirm",
                     "python", "tk", "gdal"],
                    self.log, timeout=600
                )
            self.python312 = find_python312()
            if not self.python312:
                self._finish(
                    False,
                    "❌ Python 3.12/3.11 introuvable après installation.\n"
                    "Installez-le manuellement puis relancez."
                )
                return
        self._create_venv()
        if not self._venv_ok():
            return
        self._install_requirements()
        self._set_progress(85)
        self._launch_launcher()

    def _create_venv(self):
        if VENV_DIR.exists():
            self.log("♻️  Venv existant trouvé : {}".format(VENV_DIR))
            return
        self.log("🔧 Création du venv Python...")
        rc = run_cmd(
            [self.python312, "-m", "venv", str(VENV_DIR)],
            self.log, timeout=120
        )
        if rc != 0:
            self._finish(False, "❌ Échec création du venv.")

    def _venv_ok(self):
        if not VENV_PY.exists():
            self._finish(False, "❌ Venv introuvable après création.")
            return False
        return True

    def _install_requirements(self):
        req_file = BASE_DIR / "requirements.txt"
        self.log("📦 Mise à jour pip...")
        run_cmd(
            [str(VENV_PY), "-m", "pip", "install", "--upgrade",
             "pip", "setuptools", "wheel"],
            self.log, timeout=180
        )
        if req_file.exists():
            self.log("📦 Installation modules depuis requirements.txt...")
            rc = run_cmd(
                [str(VENV_PY), "-m", "pip", "install", "-r", str(req_file)],
                self.log, timeout=900
            )
        else:
            modules = [
                "psutil", "numpy", "Pillow", "requests", "Shapely",
                "pyproj", "fiona", "scipy", "customtkinter", "rtree",
                "scikit-fmm"
            ]
            rc = run_cmd(
                [str(VENV_PY), "-m", "pip", "install"] + modules,
                self.log, timeout=900
            )
        if rc != 0:
            self.log("⚠️ Certains modules n'ont pas pu être installés.")
        else:
            self.log("✅ Modules installés.")

    def _install_gdal_mac(self, brew):
        self.log("── 🗺️ GDAL macOS ───────────────────────────")
        if not brew:
            return
        run_cmd([brew, "install", "gdal"], self.log, timeout=900)

    def _launch_launcher(self):
        if not LAUNCHER_PY.exists():
            self._finish(False, "❌ Ortho4XP_Launcher.py introuvable.")
            return
        self.log("\n✅ Installation Prérequis terminée ! Lancement du Launcher...")
        py_exe = str(VENV_PY) if VENV_PY.exists() else self.python312
        ok = _launch_ortho4xp(py_exe)
        if ok:
            self._finish(True, "✅ Ortho4XP Launcher lancé !")
        else:
            self._finish(False, "❌ Impossible de lancer le Launcher.")

    def _set_progress(self, value):
        if self.progress:
            self.progress(value)

    def _finish(self, success, message):
        self.log("")
        self.log(message)
        if self.done_fn:
            self.done_fn(success, message)


# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE GRAPHIQUE tkinter (uniquement si disponible)
# ══════════════════════════════════════════════════════════════════════════════

if HAS_TK:
    class HoverButton(tk.Canvas):
        def __init__(self, parent, text, command, width=380, height=55, font_size=13):
            super().__init__(
                parent, width=width + 15, height=height + 15,
                bg=BG_GLOBAL, highlightthickness=0, cursor="hand2"
            )
            self.command = command
            self.width, self.height = width, height
            self.create_rounded_rect(8, 8, width + 5, height + 5, 12, fill=SHADOW_COLOR)
            self.rect = self.create_rounded_rect(2, 2, width, height, 12, fill=BTN_COLOR)
            self.label_id = self.create_text(
                width // 2 + 2, height // 2 + 2, text=text,
                fill=BTN_TEXT, font=("Helvetica", font_size, "bold"),
                width=width - 20
            )
            self.bind("<Button-1>", lambda e: self.on_click())
            self.bind("<Enter>",    lambda e: self.itemconfig(self.rect, fill=BTN_HOVER))
            self.bind("<Leave>",    lambda e: self.itemconfig(self.rect, fill=BTN_COLOR))

        def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
            pts = [
                x1+r, y1,  x1+r, y1,  x2-r, y1,  x2-r, y1,
                x2,   y1,  x2,   y1+r, x2,   y1+r, x2,   y2-r,
                x2,   y2-r, x2,  y2,   x2-r, y2,   x2-r, y2,
                x1+r, y2,  x1+r, y2,  x1,   y2,   x1,   y2-r,
                x1,   y2-r, x1,  y1+r, x1,   y1+r, x1,   y1
            ]
            return self.create_polygon(pts, **kwargs, smooth=True)

        def set_enabled(self, enabled):
            color = BTN_COLOR if enabled else "#2a3d33"
            self.itemconfig(self.rect, fill=color)
            self.itemconfig(self.label_id, fill=BTN_TEXT if enabled else "#667766")
            self.configure(cursor="hand2" if enabled else "arrow")
            self._enabled = enabled

        def on_click(self):
            if not getattr(self, "_enabled", True):
                return
            self.move(self.rect, 3, 3)
            self.after(100, lambda: [self.move(self.rect, -3, -3), self.command()])

    class InstallApp(tk.Tk):
        def __init__(self):
            super().__init__()
            _init_log_session("GUI")
            fsize_title  = 36
            fsize_sub    = 14
            fsize_log    = 12
            fsize_btn    = 13
            fsize_launch = 20
            self.title("Ortho4XP V3.0 — Installation Prérequis")
            self.configure(bg=BG_GLOBAL)
            self.resizable(True, True)
            self.geometry("950x850")
            self.minsize(800, 700)
            # ── Titre ───────────────────────────────────────────────────────────
            tk.Label(
                self, text="✈  Ortho4XP V3.0",
                font=("Helvetica", fsize_title, "bold"),
                fg=GREEN_OK, bg=BG_GLOBAL
            ).pack(pady=(20, 0))
            tk.Label(
                self, text="Version : Mac • Linux • Windows",
                font=("Helvetica", fsize_sub), fg=GREEN_OK, bg=BG_GLOBAL
            ).pack(pady=(2, 8))
            # ── Barre de progression ─────────────────────────────────────────────
            prog_frame = tk.Frame(self, bg=BG_GLOBAL)
            prog_frame.pack(fill="x", padx=30, pady=(0, 5))
            tk.Label(
                prog_frame, text="Progression :", fg=GREEN_OK, bg=BG_GLOBAL,
                font=("Helvetica", fsize_sub)
            ).pack(side="left")
            self.prog_var = tk.IntVar(value=0)
            self.prog_bar = tk.Canvas(
                prog_frame, height=18, bg="#1a2a22",
                highlightthickness=1, highlightbackground="#4a6b59"
            )
            self.prog_bar.pack(side="left", fill="x", expand=True, padx=(10, 0))
            self.prog_bar.bind("<Configure>", self._redraw_progress)
            self._prog_rect = None
            # ── Console log ─────────────────────────────────────────────────────
            self.log_widget = tk.Text(
                self, height=12, bg=TEXT_BG, fg=TEXT_FG,
                font=("Courier", fsize_log), relief="flat",
                padx=12, pady=12, state="disabled"
            )
            self.log_widget.pack(pady=8, padx=30, fill="both", expand=True)
            self.log_widget.tag_config("ok",   foreground=GREEN_OK)
            self.log_widget.tag_config("err",  foreground=RED_ERR)
            self.log_widget.tag_config("warn", foreground=YELLOW_WARN)
            # ── Boutons ─────────────────────────────────────────────────────────
            btn_frame = tk.Frame(self, bg=BG_GLOBAL)
            btn_frame.pack(pady=10)
            plat_label = {
                "Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"
            }.get(SYSTEM, SYSTEM)
            arch_label = "Apple Silicon" if MACHINE == "arm64" else "Intel/x86"
            btn_text = "🚀  Lancer l'Installation ({} {})".format(plat_label, arch_label)
            self.btn_install = HoverButton(
                btn_frame, btn_text, self.start_install,
                width=800, height=70, font_size=fsize_launch
            )
            self.btn_install.pack(pady=6)
            self.btn_quit = HoverButton(
                btn_frame, "✖  Quitter", self.destroy,
                width=180, height=55, font_size=fsize_btn
            )
            self.btn_quit.pack(pady=4)
            # ── Statut ──────────────────────────────────────────────────────────
            self.status_var = tk.StringVar(
                value="Prêt — cliquez sur le bouton pour commencer."
            )
            tk.Label(
                self, textvariable=self.status_var,
                fg=YELLOW_WARN, bg=BG_GLOBAL,
                font=("Helvetica", fsize_sub, "italic")
            ).pack(pady=(4, 12))
            # Affichage info plateforme au démarrage
            self._log("Plateforme détectée : {} / {}".format(SYSTEM, MACHINE))
            self._log("Dossier Ortho4XP   : {}".format(BASE_DIR))
            self._log("")
            self._check_existing()

        def _check_existing(self):
            py = find_python312()
            brew = find_homebrew() if SYSTEM == "Darwin" else None
            venv_ok = VENV_PY.exists()
            launcher_ok = LAUNCHER_PY.exists()
            modules_ok = _check_modules_ok()

            self._log("{} Python       : {}".format(
                "✅" if py else "❌", py or "non trouvé"
            ))
            if SYSTEM == "Darwin":
                self._log("{} Homebrew     : {}".format(
                    "✅" if brew else "❌", brew or "non trouvé"
                ))
            self._log("{} Venv         : {}".format(
                "✅" if venv_ok else "⭕",
                "présent" if venv_ok else "à créer"
            ))
            self._log("{} Launcher     : {}".format(
                "✅" if launcher_ok else "❌",
                "présent" if launcher_ok else "MANQUANT"
            ))
            self._log("{} Modules      : {}".format(
                "✅" if modules_ok else "⭕",
                "présents" if modules_ok else "à installer"
            ))
            self._log("")

            # ── Cas 1 : TOUT déjà prêt → lancer directement ─
            if py and venv_ok and launcher_ok and modules_ok:
                self._log("✅ Python et venv déjà présents.", tag="ok")
                self._log("✅ Tout est configuré.", tag="ok")
                if SYSTEM == "Darwin":
                    self._create_mac_launcher_app()
                self._log("✅ Lancement d'Ortho4XP...", tag="ok")
                self.status_var.set("✅ Tout est prêt — lancement dans 3 secondes...")
                self.set_progress(100)
                self.btn_install.set_enabled(False)
                self.after(1500, self._auto_launch)
                return

            # ── Cas 2 : Launcher manquant → bloquer ─────────────────────────
            if not launcher_ok:
                self._log("❌ Ortho4XP_Launcher.py introuvable !", tag="err")
                self._log("   Vérifiez que l'archive est bien décompressée.", tag="warn")

        def _create_mac_launcher_app(self):
            """Crée Lanceur ORTHO4XP.app — binaire C universel arm64+x86_64."""
            import shutil as _shutil
            import stat as st
            self._log("🔧 Création de Lanceur ORTHO4XP.app...", tag=None)
            LAUNCHER_C = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#include <libgen.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/wait.h>
extern int _NSGetExecutablePath(char *buf, uint32_t *bufsize);
static int path_exists(const char *p) { struct stat s; return stat(p,&s)==0; }
int main(int argc, char **argv) {
    char exe[PATH_MAX]; uint32_t sz = sizeof(exe);
    if (_NSGetExecutablePath(exe, &sz) != 0) return 1;
    char real[PATH_MAX];
    if (!realpath(exe, real)) strncpy(real, exe, PATH_MAX-1);
    char t1[PATH_MAX],t2[PATH_MAX],t3[PATH_MAX],tmp[PATH_MAX],root[PATH_MAX];
    strncpy(t1,real,PATH_MAX-1); strncpy(t2,dirname(t1),PATH_MAX-1);
    strncpy(t3,dirname(t2),PATH_MAX-1); strncpy(tmp,dirname(t3),PATH_MAX-1);
    strncpy(root,dirname(tmp),PATH_MAX-1);
    chdir(root);
    char venv_py[PATH_MAX], launcher[PATH_MAX], sh_path[PATH_MAX];
    snprintf(venv_py,  sizeof(venv_py),  "%s/venv/bin/python3",     root);
    snprintf(launcher, sizeof(launcher), "%s/Ortho4XP_Launcher.py", root);
    snprintf(sh_path,  sizeof(sh_path),  "%s/_ortho_run.sh",        root);
    if (!path_exists(venv_py)) {
        char *args[] = {"/usr/bin/osascript","-e",
            "display dialog \"Lancez d\'abord INSTALL_PREREQUIS.py\" "
            "buttons {\"OK\"} default button \"OK\" "
            "with title \"Ortho4XP\" with icon caution", NULL};
        pid_t p=fork(); if(p==0){execv("/usr/bin/osascript",args);_exit(1);}
        if(p>0){int s;waitpid(p,&s,0);} return 1;
    }
    FILE *sh=fopen(sh_path,"w");
    if(sh){fprintf(sh,"#!/bin/sh\ncd \"%s\"\nexec \"%s\" \"%s\"\n",root,venv_py,launcher);fclose(sh);chmod(sh_path,0755);}
    char *a[]={"/bin/sh",sh_path,NULL};
    pid_t p=fork(); if(p==0){execv("/bin/sh",a);_exit(1);}
    return 0;
}
"""
            INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>CFBundleExecutable</key><string>launch</string>
    <key>CFBundleIdentifier</key><string>com.ypsos.ortho4xp.daily</string>
    <key>CFBundleName</key><string>ORTHO4XP V3 Lanceur</string>
    <key>CFBundleDisplayName</key><string>ORTHO4XP V3 Lanceur</string>
    <key>CFBundleVersion</key><string>3.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict></plist>"""
            app_path  = BASE_DIR / "Lanceur ORTHO4XP.app"
            macos_dir = app_path / "Contents" / "MacOS"
            res_dir   = app_path / "Contents" / "Resources"
            if app_path.exists():
                _shutil.rmtree(str(app_path))
            macos_dir.mkdir(parents=True)
            res_dir.mkdir(parents=True)
            (app_path / "Contents" / "Info.plist").write_text(INFO_PLIST, encoding="utf-8")
            c_file  = BASE_DIR / "_tmp_install.c"
            exe_out = macos_dir / "launch"
            c_file.write_text(LAUNCHER_C, encoding="utf-8")
            compiled = False
            for arch_flags in [["-arch", "arm64", "-arch", "x86_64"], []]:
                cmd = ["gcc"] + arch_flags + [str(c_file), "-o", str(exe_out), "-O2"]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    compiled = True
                    break
            c_file.unlink(missing_ok=True)
            if compiled:
                exe_out.chmod(
                    exe_out.stat().st_mode | st.S_IEXEC | st.S_IXGRP | st.S_IXOTH
                )
                try:
                    subprocess.run(
                        ["xattr", "-cr", str(app_path)],
                        capture_output=True, timeout=10
                    )
                    subprocess.run(
                        ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
                        capture_output=True, timeout=30
                    )
                except Exception:
                    pass
                self._log("✅ Lanceur ORTHO4XP.app créé !", tag="ok")
            else:
                self._log(
                    "⚠️  Compilation gcc échouée — Lanceur .app non créé.",
                    tag="warn"
                )

        def _auto_launch(self):
            """Lancement direct quand tout est déjà installé.
            Ferme la fenêtre AVANT de lancer le Launcher."""
            self.destroy()
            _launch_ortho4xp()

        def start_install(self):
            self.btn_install.set_enabled(False)
            self.status_var.set("Installation en cours…")
            self._log("", tag=None)
            self._log("════════ DÉMARRAGE INSTALLATION ════════")
            installer = Installer(
                log_fn=self._log,
                progress_fn=self.set_progress,
                done_fn=self._on_done
            )
            t = threading.Thread(target=installer.run, daemon=True)
            t.start()

        def _on_done(self, success, message):
            self.after(0, lambda: self._finish_ui(success, message))

        def _finish_ui(self, success, message):
            if success:
                self.status_var.set("✅ Installation terminée — Launcher lancé !")
                self.set_progress(100)
                self.after(2500, self.destroy)
            else:
                self.status_var.set("⚠️  Voir les messages ci-dessus.")
                self.btn_install.set_enabled(True)

        def set_progress(self, value):
            self.after(0, lambda: self._update_progress(value))

        def _update_progress(self, value):
            self.prog_var.set(value)
            self._redraw_progress()

        def _redraw_progress(self, event=None):
            w = self.prog_bar.winfo_width()
            h = self.prog_bar.winfo_height()
            if w < 2:
                return
            self.prog_bar.delete("all")
            filled = int(w * self.prog_var.get() / 100)
            if filled > 0:
                self.prog_bar.create_rectangle(
                    0, 0, filled, h, fill=GREEN_OK, outline=""
                )
            pct = self.prog_var.get()
            self.prog_bar.create_text(
                w // 2, h // 2,
                text="{}%".format(pct),
                fill="white" if pct < 50 else "#0f0f1a",
                font=("Helvetica", 9, "bold")
            )

        def _log(self, msg, tag=None):
            def _insert():
                self.log_widget.config(state="normal")
                t = tag
                if t is None:
                    low = msg.lower()
                    if any(x in low for x in [
                        "✅", "ok", "créé", "trouvé", "installé", "terminé"
                    ]):
                        t = "ok"
                    elif any(x in low for x in [
                        "❌", "erreur", "impossible", "échec", "manquant"
                    ]):
                        t = "err"
                    elif any(x in low for x in [
                        "⚠", "absent", "non trouvé", "attention"
                    ]):
                        t = "warn"
                if t:
                    self.log_widget.insert("end", "{}\n".format(msg), t)
                else:
                    self.log_widget.insert("end", "{}\n".format(msg))
                self.log_widget.see("end")
                self.log_widget.config(state="disabled")
                _append_log_file(msg)
                self.update_idletasks()
            self.after(0, _insert)


# ══════════════════════════════════════════════════════════════════════════════
#  FALLBACK CONSOLE (si tkinter absent)
# ══════════════════════════════════════════════════════════════════════════════

def run_console():
    print("=" * 55)
    print("  Ortho4XP V3.0 — INSTALLATION PRÉREQUIS (mode texte)")
    print("=" * 55)
    print("Plateforme : {} / {}".format(SYSTEM, MACHINE))
    print("Dossier    : {}".format(BASE_DIR))
    print()
    _init_log_session("CONSOLE")

    def _clog(msg):
        print(msg)
        _append_log_file(msg)

    installer = Installer(log_fn=_clog)
    installer.run()
    input("\nAppuyez sur Entrée pour quitter...")


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── Si tout est déjà OK → lancer le Launcher directement, sans fenêtre ──
    py = find_python312()
    venv_ok = VENV_PY.exists()
    launcher_ok = LAUNCHER_PY.exists()
    modules_ok = _check_modules_ok()

    if py and venv_ok and launcher_ok and modules_ok:
        _init_log_session("LAUNCH")
        _launch_ortho4xp()
        sys.exit(0)

    # ── Sinon → ouvrir la fenêtre d'installation ────────────────────────────
    if HAS_TK:
        app = InstallApp()
        app.mainloop()
    else:
        print("⚠️  tkinter absent — mode console activé.")
        run_console()
