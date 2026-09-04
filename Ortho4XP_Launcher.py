#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import platform
import tkinter as tk
import tkinter.ttk as ttk
import subprocess
import shutil
import multiprocessing
import psutil
from pathlib import Path

# --- CONFIGURATION STYLE ROLAND ---
BG_GLOBAL     = "#3b5b49"
BTN_COLOR     = "#4a6b59"
BTN_HOVER     = "#5a7b69"
BTN_TEXT      = "white"
SHADOW_COLOR  = "#2a4235"

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__))).resolve()
SYSTEM   = platform.system()

# ── Chargement du thème sauvegardé — avant création des widgets ──────────────
try:
    sys.path.insert(0, str(BASE_DIR / "src"))
    import O4_Theme_Manager as _TM_BOOT
    _t = _TM_BOOT.get_theme()
    BG_GLOBAL    = _t.get("bg",         BG_GLOBAL)
    BTN_COLOR    = _t.get("btn_bg",     BTN_COLOR)
    BTN_HOVER    = _t.get("btn_hover",  BTN_HOVER)
    BTN_TEXT     = _t.get("btn_fg",     BTN_TEXT)
    SHADOW_COLOR = _t.get("shadow",     SHADOW_COLOR)
except Exception:
    pass  # si absent → couleurs Roland par défaut
# ─────────────────────────────────────────────────────────────────────────────

# ── Traduction bilingue ──────────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR / "src"))
try:
    import O4_Lang
    # Chargement silencieux uniquement — pas de dialogue dans le Launcher
    # Le dialogue de 1er lancement est géré par INSTALL_PREREQUIS.py
    _saved = O4_Lang._read_lang_from_cfg()
    if _saved:
        O4_Lang._load_lang(_saved)
    else:
        O4_Lang._load_lang("EN")
    from O4_Lang import tr
except Exception:
    def tr(k): return k   # fallback si O4_Lang absent

# ── Version affichée — lue automatiquement depuis O4_Version.py ───────────────
# Le numéro n'est plus écrit en dur dans le titre : modifier 'version_short'
# dans src/O4_Version.py suffit à mettre à jour le titre partout.
try:
    import O4_Version as _O4V
    APP_VERSION = getattr(_O4V, "version_short", None) or "V3.0"
except Exception:
    APP_VERSION = "V3.0"

# ── Vérification nom de dossier GitHub ──────────────────────────────────────
# GitHub crée automatiquement un double nom : ORTHO4XP-V3-ORTHO4XP_V3
# Le lanceur fonctionne quand même, mais on avertit l'utilisateur pour éviter
# toute confusion future (chemins longs, scripts externes, etc.)
def _check_folder_name():
    folder_name = BASE_DIR.name
    # Détection du double nom GitHub (contient un tiret suivi du même nom)
    if "-" in folder_name and folder_name.count("ORTHO4XP") >= 2:
        correct_name = "ORTHO4XP_V3"
        parent = BASE_DIR.parent
        correct_path = parent / correct_name
        # Afficher alerte tkinter minimale avant ouverture du lanceur
        import tkinter as _tk
        import tkinter.messagebox as _mb
        _root = _tk.Tk()
        _root.withdraw()
        _mb.showwarning(
            title="⚠️  Nom de dossier incorrect",
            message=(
                f"Le dossier s'appelle :\n\n"
                f"  {folder_name}\n\n"
                f"GitHub a ajouté un double nom automatiquement.\n\n"
                f"➡  Renommez-le en :\n\n"
                f"  {correct_name}\n\n"
                f"Chemin correct :\n"
                f"  {correct_path}\n\n"
                f"Le lanceur va s'arrêter.\n"
                f"Relancez après le renommage."
            )
        )
        _root.destroy()
        sys.exit(0)

_check_folder_name()
# ────────────────────────────────────────────────────────────────────────────

ORTHO_PY    = BASE_DIR / "Ortho4XP.py"
CFG_FILE    = BASE_DIR / "Ortho4XP.cfg"
CONF_FILE   = BASE_DIR / "Ortho4XP.conf"
SRC_DIR     = BASE_DIR / "src"

if SYSTEM == "Windows":
    VENV_PY  = BASE_DIR / "venv" / "Scripts" / "python.exe"
    VENV_PIP = BASE_DIR / "venv" / "Scripts" / "pip.exe"
else:
    VENV_PY  = BASE_DIR / "venv" / "bin" / "python3"
    VENV_PIP = BASE_DIR / "venv" / "bin" / "pip"

# rasterio est autonome dans venv — pas besoin de GDAL système

# ── Helper CustomTkinter (synthèse conversion CTk) ───────────────────────────
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    _HAS_CTK = False


def _lighten_hex(hexcol, factor):
    try:
        h = hexcol.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hexcol


def _ctk_button(parent, text=None, command=None, width=None,
                corner_radius=8, **ttk_kw):
    """Bouton texte look CustomTkinter (style fenetre principale) ; repli
    ttk.Button si CTk absent. Les kwargs ttk (style, takefocus...) ne
    s'appliquent qu'au repli ttk."""
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
            fg_color=base, hover_color=_lighten_hex(base, 1.30),
            border_color=_t.get("border", base),
            text_color=_t.get("btn_fg", "#ffffff"))
        if width:
            b.configure(width=width)
        # CORRECTIF macOS OBLIGATOIRE : le remplissage arrondi n'est dessine
        # qu'une fois le bouton dimensionne -> rectangle sombre derriere le
        # texte au repos (disparait seulement au survol). On force un redessin
        # apres mise en page.
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


class HoverButton(tk.Canvas):
    def __init__(self, parent, text, command, width=380, height=55, font_size=13,
                 fill_color=None, hover_color=None, text_color=None):
        # fill_color / hover_color / text_color : optionnels. Sans valeur,
        # comportement identique a l'origine (BTN_COLOR / BTN_HOVER / BTN_TEXT).
        # La couleur est memorisee par instance -> elle persiste au survol
        # (le <Leave> revient a self._fill, plus a la constante globale).
        super().__init__(parent, width=width+15, height=height+15, 
                         bg=BG_GLOBAL, highlightthickness=0, cursor="hand2")
        self.command = command
        self.width, self.height = width, height
        self._fill  = fill_color  or BTN_COLOR
        self._hover = hover_color or BTN_HOVER
        self.create_rounded_rect(8, 8, width+5, height+5, 12, fill=SHADOW_COLOR)
        self.rect = self.create_rounded_rect(2, 2, width, height, 12, fill=self._fill)
        self.create_text(width//2 + 2, height//2 + 2, text=text, 
                         fill=(text_color or BTN_TEXT),
                         font=("Helvetica", font_size, "bold"))
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self._hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self._fill))

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r,
                  x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2,
                  x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_click(self):
        self.move(self.rect, 3, 3)
        self.after(100, lambda: [self.move(self.rect, -3, -3), self.command()])

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Ortho4XP {APP_VERSION} Launcher - Roland Edition")
        self.geometry("950x950")
        self.minsize(900, 780)
        self.configure(bg=BG_GLOBAL)

        # ── Barre de menus native (module externe O4_Menu_Bar) ─────────
        #  Ajout pur : range les fonctions (Installation, Configuration,
        #  Aide) en menu natif. Le gros bouton LANCER reste au premier
        #  niveau. Non bloquant : si le module est absent ou en erreur, le
        #  lanceur démarre normalement.
        try:
            import O4_Menu_Bar
            O4_Menu_Bar.install_launcher_menubar(self)
        except Exception as _e:
            print(f"[Launcher] menubar: {_e}")

        # ── Bannière (image d'en-tête, collée à gauche) ───────────────
        #  Titre texte « Ortho4XP V3.0 » et sous-titre supprimés : la
        #  bannière tient lieu d'en-tête. « Version : … » est déplacé en bas
        #  près de l'indicateur de langue. Non bloquant si image/Pillow absent.
        self._add_banner()

        self.log = tk.Text(
            self,
            height=12,
            bg="#0f0f1a",
            fg="#50fa7b",
            font=("Courier", 12),
            relief="flat",
            padx=15,
            pady=15,
            takefocus=0,
            cursor="arrow",
            exportselection=False
        )

        self.log.pack(
            pady=10,
            padx=30,
            fill="both",
            expand=True
        )

        # Lecture seule multi-OS : bloque saisie/suppression, autorise sélection et copie
        def _log_key(e):
            # Ctrl (Win/Linux) = state & 0x4 / Cmd (Mac) = state & 0x8
            mod = (e.state & 0x4) or (e.state & 0x8)
            if mod and e.keysym.lower() in ("c", "a"):
                return None   # Autoriser Ctrl+C / Ctrl+A / Cmd+C / Cmd+A
            return "break"    # Bloquer tout le reste
        self.log.bind("<Key>",       _log_key)
        self.log.bind("<BackSpace>", lambda e: "break")
        self.log.bind("<Delete>",    lambda e: "break")

        # ── Boutons Installer/Vérifier/Historique/Crédits : déplacés dans
        #    la barre de menus (Installation / Aide). Les méthodes restent
        #    intactes (open_install_menu, check_integrity, show_history,
        #    show_credits) — seuls les boutons d'affichage sont retirés.

        # ── Cadre bas : indicateur de langue (le sélecteur de thème et le
        #    bouton langue sont désormais dans la barre de menus →
        #    Configuration. Les méthodes de thème/langue restent intactes ;
        #    self._tm est conservé car le menu Thème s'appuie dessus). ──────
        theme_frame = tk.Frame(self, bg=BG_GLOBAL)
        theme_frame.pack(fill="x", padx=30, pady=(5, 10))

        # Chargement des thèmes disponibles (nécessaire au menu Configuration)
        self._theme_keys   = ["roland", "custom", "ardoise", "sable", "ocean"]
        self._theme_labels = ["Roland", "Personnalisée", "Ardoise", "Sable", "Océan"]
        try:
            sys.path.insert(0, str(SRC_DIR))
            import O4_Theme_Manager as _TM
            themes = _TM.list_themes()
            self._theme_keys   = list(themes.keys())
            self._theme_labels = list(themes.values())
            self._tm = _TM
        except Exception:
            self._tm = None

        # Trouver le label correspondant au thème actif
        current_key = self._theme_keys[0]
        try:
            if self._tm:
                current_key = self._tm.current_theme_name()
        except Exception:
            pass
        try:
            idx = self._theme_keys.index(current_key)
            current_label = self._theme_labels[idx]
        except (ValueError, IndexError):
            current_label = self._theme_labels[0]

        self._theme_label_var = tk.StringVar(value=current_label)
        self._theme_key_var   = tk.StringVar(value=current_key)

        def _on_theme_select(label):
            try:
                idx = self._theme_labels.index(label)
                key = self._theme_keys[idx]
            except (ValueError, IndexError):
                key = label
            self._theme_key_var.set(key)
            self._apply_theme(key)

        # Le menu déroulant de thème et le bouton palette 🎨 sont retirés de
        # l'affichage : ils vivent maintenant dans la barre de menus
        # (Configuration → Thème / Éditeur de thème personnalisé…). La
        # logique (_on_theme_select, _apply_theme, _apply_theme_btn) reste
        # disponible et appelée par le menu.

        # ── Bouton de sélection de langue ─────────────────────────────────
        # Placé ici dans la fenêtre du lanceur (Mac / Linux / Windows).
        # Réutilise le bouton existant de O4_Lang. À la validation d'une
        # langue, le choix est sauvegardé dans Ortho4XP.cfg puis le lanceur
        # se ferme et redémarre automatiquement dans la nouvelle langue
        # (callback on_change=self._restart_with_new_lang).
        try:
            import O4_Lang as _O4Lang

            # Icône d'identification linguistique, placée DEVANT le bouton.
            # Globe + code langue (FR / EN / ...) : rendu identique sur
            # Mac, Linux et Windows (les drapeaux emoji ne s'affichent pas
            # sous Windows, ils sont donc volontairement écartés).
            self._lang_icon = tk.Label(
                theme_frame,
                text="🌐 " + self._current_lang_code(),
                bg=BG_GLOBAL, fg="#a6e3a1",
                font=("Helvetica", 14, "bold"),
            )
            self._lang_icon.pack(side="left", padx=(18, 4))

            # Le bouton « Changer la langue… » est retiré de l'affichage :
            # il vit maintenant dans la barre de menus (Configuration →
            # Langue). L'indicateur 🌐 ci-dessus reste, pour montrer la
            # langue active d'un coup d'œil. show_language_dialog reste
            # disponible dans O4_Lang (premier lancement, etc.).
        except Exception:
            pass  # si O4_Lang absent → le lanceur fonctionne quand même
        # ─────────────────────────────────────────────────────────────────

        # « Version : … » déplacé ici (bas de fenêtre), collé à DROITE, sur la
        # même ligne que l'indicateur 🌐 langue (collé à gauche). Placé hors du
        # try ci-dessus pour rester visible même si O4_Lang est absent.
        tk.Label(theme_frame, text="Version : Mac • Linux • Windows",
                 font=("Helvetica", 14, "bold"), fg="#a6e3a1",
                 bg=BG_GLOBAL).pack(side="right", padx=(4, 18))

        # Gros bouton LANCER en dessous
        HoverButton(self, tr("▶️ LANCER ORTHO4XP"), self.launch_ortho, 
                    width=800, height=70, font_size=20).pack(pady=(15, 30))

        self._log(f"📍 Dossier : {BASE_DIR}")
        self.check_integrity()
        self._run_security_check()

    # ====================== IDENTIFICATION LANGUE ======================
    def _add_banner(self):
        """Affiche BanniereGithub.jpg en haut de la fenêtre du lanceur.

        Entièrement non bloquant :
          • si Pillow (PIL) est absent → on saute (Tkinter ne lit pas le JPG
            nativement) ;
          • si l'image est absente ou illisible → on saute ;
          • dans tous ces cas le lanceur s'affiche exactement comme avant.

        La PhotoImage est conservée sur l'instance (self._banner_photo) : sans
        cette référence, Tkinter la ramasse et la bannière apparaît vide.
        La largeur suit la fenêtre (≈900 px), la hauteur est plafonnée pour
        rester une bande d'en-tête et ne pas écraser la console.
        """
        try:
            from PIL import Image, ImageTk
        except Exception:
            return  # Pillow absent → pas de bannière (lanceur inchangé)

        path = BASE_DIR / "BanniereGithub.jpg"
        if not path.exists():
            return

        try:
            img = Image.open(str(path))
            w, h = img.size
            scale = 900.0 / float(w)          # ajuste à la largeur fenêtre
            if h * scale > 300:               # plafonne la hauteur
                scale = 300.0 / float(h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            # Pillow >= 10 : LANCZOS via Resampling ; repli anciennes versions
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS

            img = img.resize(new_size, resample)
            self._banner_photo = ImageTk.PhotoImage(img)   # référence conservée
            self._banner_label = tk.Label(self, image=self._banner_photo,
                                          bg=BG_GLOBAL, bd=0)
            self._banner_label.pack(anchor="w", padx=(65, 0), pady=(10, 0))
        except Exception:
            return  # toute erreur de décodage → on saute proprement

    def _current_lang_code(self):
        """
        Retourne le code de la langue active ('FR', 'EN', ...) pour l'icône.
        Lecture 100 % défensive : aucune exception ne remonte, valeur de
        repli 'EN' si O4_Lang est absent ou si Ortho4XP.cfg ne contient rien.
        """
        try:
            import O4_Lang as _L
            code = None
            for _attr in ("current_lang", "get_lang", "_read_lang_from_cfg"):
                _f = getattr(_L, _attr, None)
                if callable(_f):
                    try:
                        code = _f()
                    except Exception:
                        code = None
                    if code:
                        break
                elif isinstance(_f, str) and _f:
                    code = _f
                    break
            if not code:
                code = getattr(_L, "LANG", None)
            if code:
                return str(code).strip().upper()[:2]
        except Exception:
            pass
        return "EN"

    # ====================== REDÉMARRAGE LANGUE ======================
    def _restart_with_new_lang(self):
        """
        Appelé après validation d'une nouvelle langue dans le dialogue.
        La langue est déjà sauvegardée dans Ortho4XP.cfg par O4_Lang.
        On relance le lanceur (qui relit la langue au démarrage) puis on
        ferme l'instance courante. Multi-OS (Mac / Linux / Windows).
        """
        try:
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception:
            pass
        finally:
            self.destroy()   # ferme le lanceur courant -> mainloop se termine

    # ====================== SENTINELLE ======================
    def _run_security_check(self):
        self._log("\n--- 🛡️  SENTINELLE ---\n")
        cpu_total = multiprocessing.cpu_count()
        ram_total = round(psutil.virtual_memory().total / (1024**3))
        safe_slots = max(1, cpu_total - 2 if cpu_total > 4 else cpu_total - 1)
        safe_ram   = int(ram_total * 0.75)
        self._log(f"Matériel : {cpu_total} CPUs | {ram_total} Go RAM\n")
        self._log(f"Config auto : {safe_slots} Slots | {safe_ram} Go RAM\n")
        if CFG_FILE.exists():
            self._log("✅ Ortho4XP.cfg présent.\n")
        self._log("----------------------------------\n")

    # ── Gestion du thème ──────────────────────────────────────────────────
    def _apply_theme(self, theme_key=None):
        """Sauvegarde le thème et redémarre le Launcher."""
        if not self._tm:
            return
        key = theme_key or self._theme_key_var.get()
        if self._tm.set_theme(key):
            self.after(200, self._restart)

    def _restart(self):
        """Redémarre le Launcher avec le nouveau thème — Mac/Linux/Windows."""
        if SYSTEM == "Windows":
            python = str(BASE_DIR / "venv" / "Scripts" / "python.exe")
        else:
            python = str(BASE_DIR / "venv" / "bin" / "python3")
        launcher = str(BASE_DIR / "Ortho4XP_Launcher.py")
        subprocess.Popen([python, launcher])
        self.destroy()

    def _apply_theme_btn(self):
        """Bouton palette 🎨 → Ouvre l'éditeur uniquement sur clic explicite."""
        if not self._tm:
            self._log("❌ O4_Theme_Manager non chargé.")
            return
        try:
            self._open_custom_theme_editor_window()
        except Exception as e:
            self._log(f"❌ Erreur : {e}")

    def _open_custom_theme_editor_window(self):
        """
        Éditeur Thème Personnalisée — palette colorchooser natif.
        Compatible Mac (roue chromatique), Linux (gtk), Windows (dialog couleur).
        tkinter.colorchooser est standard sur les 3 OS.
        Par ligne : nom de l'élément | rectangle couleur actuelle | bouton Choisir.
        """
        from tkinter import colorchooser

        win = tk.Toplevel(self)
        win.title("🎨 Éditeur Thème Personnalisée")
        win.configure(bg=BG_GLOBAL)
        win.resizable(True, True)
        win.protocol("WM_DELETE_WINDOW", lambda: [win.grab_release(), win.destroy()])

        tk.Label(win, text="🎨  Éditeur Thème Personnalisée",
                 font=("Helvetica", 15, "bold"),
                 fg="#a6e3a1", bg=BG_GLOBAL).pack(pady=(12, 4))
        tk.Label(win, text="Cliquez sur une couleur pour ouvrir la palette",
                 font=("Helvetica", 11), fg="#e8f0ec", bg=BG_GLOBAL).pack(pady=(0, 8))

        # ── Scrollable ────────────────────────────────────────────────────
        outer = tk.Frame(win, bg=BG_GLOBAL)
        outer.pack(fill="both", expand=True, padx=10)
        cv_s = tk.Canvas(outer, bg=BG_GLOBAL, bd=0, highlightthickness=0)
        sb   = tk.Scrollbar(outer, orient="vertical", command=cv_s.yview)
        cv_s.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv_s.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(cv_s, bg=BG_GLOBAL)
        wid = cv_s.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv_s.configure(
            scrollregion=cv_s.bbox("all")))
        cv_s.bind("<Configure>", lambda e: cv_s.itemconfig(
            wid, width=cv_s.winfo_width()))
        # Molette — fonctionne Mac/Linux/Windows
        def _scroll(e):
            delta = int(-1 * (e.delta / 120)) if e.delta else (-1 if e.num==4 else 1)
            cv_s.yview_scroll(delta, "units")
        cv_s.bind_all("<MouseWheel>", _scroll)
        cv_s.bind_all("<Button-4>",   _scroll)
        cv_s.bind_all("<Button-5>",   _scroll)

        KEY_LABELS = {
            "bg":           "Fond principal",
            "bg_secondary": "Fond secondaire",
            "fg":           "Texte principal",
            "fg_secondary": "Texte secondaire",
            "btn_bg":       "Fond boutons",
            "btn_fg":       "Texte boutons",
            "btn_hover":    "Boutons survol",
            "btn_active":   "Boutons actifs",
            "console_bg":   "Console fond",
            "console_fg":   "Console texte",
            "accent":       "Couleur application",
            "warning":      "Avertissement",
            "error":        "Erreur",
            "success":      "Succès",
            "canvas_bg":    "Canvas fond",
            "border":       "Bordures",
            "shadow":       "Ombres",
        }

        theme_dict = self._tm.get_custom_theme()
        self._editor_vars = {}   # key → tk.StringVar(hex)

        def _pick_color(key, hex_var, rect):
            """Ouvre la palette colorchooser native — multi-OS."""
            rect.config(bd=4, relief="ridge", highlightbackground="#a6e3a1",
                        highlightthickness=3)
            win.update_idletasks()
            current = hex_var.get()
            result = colorchooser.askcolor(
                color=current,
                title=f"Choisir : {KEY_LABELS.get(key, key)}",
                parent=win
            )
            # Forcer fermeture palette et retour focus sur éditeur
            rect.config(bd=2, relief="solid", highlightthickness=0)
            win.lift()
            win.focus_force()
            if result and result[1]:
                new_color = result[1].lower()
                hex_var.set(new_color)
                try:
                    rect.config(bg=new_color)
                except Exception:
                    pass

        # ── Ligne d'en-tête ───────────────────────────────────────────────
        for col, txt in enumerate(["Élément", "Couleur actuelle"]):
            tk.Label(inner, text=txt, bg=BG_GLOBAL, fg="#a6e3a1",
                     font=("Helvetica", 10, "bold")).grid(
                     row=0, column=col, padx=12, pady=4, sticky="w")
        tk.Frame(inner, bg="#a6e3a1", height=1).grid(
            row=1, column=0, columnspan=2, sticky="we", padx=6, pady=2)

        # ── Une ligne par clé ─────────────────────────────────────────────
        for row_i, key in enumerate(KEY_LABELS):
            if key not in theme_dict:
                continue
            color   = theme_dict.get(key, "#000000")
            hex_var = tk.StringVar(value=color)
            self._editor_vars[key] = {"hex": hex_var}

            # Nom
            tk.Label(inner, text=KEY_LABELS[key], bg=BG_GLOBAL, fg="#e8f0ec",
                     font=("Helvetica", 11), width=18, anchor="w").grid(
                     row=row_i+2, column=0, padx=12, pady=4, sticky="w")

            # Rectangle couleur — clic = ouvre palette
            rect = tk.Label(inner, bg=color, width=18, height=2,
                            relief="solid", bd=2, cursor="hand2")
            rect.grid(row=row_i+2, column=1, padx=12, pady=4, sticky="w")
            rect.bind("<Enter>",
                lambda e, r=rect: r.config(bd=4, relief="ridge"))
            rect.bind("<Leave>",
                lambda e, r=rect: r.config(bd=2, relief="solid"))
            rect.bind("<Button-1>",
                lambda e, k=key, hv=hex_var, r=rect: _pick_color(k, hv, r))

        # ── Boutons bas — deux lignes pour éviter la coupure ─────────────
        n = len([k for k in KEY_LABELS if k in theme_dict])
        tk.Frame(inner, bg="#a6e3a1", height=1).grid(
            row=n+3, column=0, columnspan=2, sticky="we", padx=6, pady=8)

        btn_frame = tk.Frame(inner, bg=BG_GLOBAL)
        btn_frame.grid(row=n+4, column=0, columnspan=2, pady=12, sticky="we")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        _ctk_button(btn_frame, text="💾  Enregistrer Thème Personnalisée",
                    command=lambda: self._save_custom_colors(win)
                    ).grid(row=0, column=0, padx=6, pady=4, sticky="we")
        _ctk_button(btn_frame, text="🔄 Réinitialiser Roland",
                    command=lambda: self._reset_custom_theme(win)
                    ).grid(row=0, column=1, padx=6, pady=4, sticky="we")
        _ctk_button(btn_frame, text="Annuler",
                    command=lambda: [win.grab_release(), win.destroy()]
                    ).grid(row=0, column=2, padx=6, pady=4, sticky="we")

        win.update_idletasks()
        win.geometry("760x980")       # +60px pour que les 3 boutons rentrent
        win.minsize(700, 600)         # redimensionnable librement
        win.resizable(True, True)
        win.grab_set()
        win.focus_force()
        self._log("🎨 Éditeur Personnalisée ouvert.")

    def _save_custom_colors(self, win):
        """Sauvegarde toutes les couleurs dans THEMES['custom'] + fichier JSON"""
        try:
            for key, vars_ in self._editor_vars.items():
                color = vars_["hex"].get().strip()
                if color.startswith("#") and len(color) in (4, 7):
                    self._tm.THEMES["custom"][key] = color
            self._tm.THEMES["custom"]["name"] = "Personnalisée"
            # Sauvegarde préférence thème actif
            self._tm._active_theme_name = "custom"
            self._tm._active_theme = self._tm.THEMES["custom"]
            self._tm._save_prefs()
            # Sauvegarde fichier custom_theme.json à la racine Ortho4XP
            if hasattr(self._tm, "save_custom_theme_to_file"):
                self._tm.save_custom_theme_to_file()
            self._log("✅ Thème Personnalisée enregistré !")
            try: win.grab_release()
            except: pass
            win.destroy()
            self.after(800, self._restart)
        except Exception as e:
            self._log(f"❌ Erreur sauvegarde : {e}")

    def _reset_custom_theme(self, win):
        if hasattr(self._tm, "reset_custom_to_roland"):
            self._tm.reset_custom_to_roland()
        self._log("🔄 Thème custom réinitialisé aux couleurs Roland.")
        try: win.grab_release()
        except: pass
        win.destroy()
        self.after(800, self._restart)

####*------         

    # ── Callbacks tile_change / update_cfg ────────────────────────────────
    def _log(self, msg):
        self.log.insert("end", f"> {msg}\n")
        self.log.see("end")
        self.update_idletasks()

    def show_credits(self):
        """Affiche AVERTISSEMENT_LICENCE_LEGAL.md (bouton Crédits & Licence)."""
        self._show_md_window("AVERTISSEMENT_LICENCE_LEGAL.md", tr("📜 Crédits & Licence"))

    def show_history(self):
        """Affiche HISTORIQUE.md (bouton Historique)."""
        self._show_md_window("HISTORIQUE.md", tr("📖 Historique"))

    def _show_md_window(self, filename, title):
        """Affiche un fichier .md dans une fenêtre défilante au thème du lanceur.

        Le fichier est cherché à la racine du dossier (BASE_DIR), donc l'affichage
        suit automatiquement le dossier courant, quelle que soit la version.
        """
        md_path = BASE_DIR / filename
        try:
            with open(md_path, "r", encoding="utf-8", errors="replace") as fh:
                contenu = fh.read()
        except Exception:
            contenu = tr("Fichier introuvable :") + f"\n\n{md_path}"

        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG_GLOBAL)
        win.geometry("760x640")

        tk.Label(win, text=title, font=("Helvetica", 18, "bold"),
                 fg="#a6e3a1", bg=BG_GLOBAL).pack(pady=(15, 10))

        txt_frame = tk.Frame(win, bg=BG_GLOBAL)
        txt_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        scroll = tk.Scrollbar(txt_frame)
        scroll.pack(side="right", fill="y")

        txt = tk.Text(txt_frame, wrap="word", bg="#0f0f1a", fg="#50fa7b",
                      font=("Courier", 12), relief="flat", padx=15, pady=15,
                      yscrollcommand=scroll.set, exportselection=False)
        txt.pack(side="left", fill="both", expand=True)
        scroll.config(command=txt.yview)

        txt.insert("1.0", contenu)
        txt.config(state="disabled")   # lecture seule

        def _wheel(e):
            delta = -1 * (e.delta // 120) if e.delta else (1 if getattr(e, "num", 0) == 5 else -1)
            txt.yview_scroll(delta, "units")
            return "break"
        txt.bind("<MouseWheel>", _wheel)
        txt.bind("<Button-4>", _wheel)
        txt.bind("<Button-5>", _wheel)

        # Bouton Fermer — on utilise HoverButton (basé sur tk.Canvas) comme les
        # autres boutons du lanceur. Un tk.Button natif ignore le fond sur macOS
        # (d'où le fond blanc) ; le Canvas, lui, affiche toujours la bonne couleur.
        HoverButton(win, tr("Fermer"), win.destroy,
                    width=200, height=45, font_size=13).pack(pady=(0, 15))

    def open_install_menu(self):
        """Ouvre la fenêtre de sélection de plateforme pour l'installation."""
        win = tk.Toplevel(self)
        win.title(tr("Installer les Modules — Choisir la plateforme"))
        win.configure(bg=BG_GLOBAL)
        win.resizable(False, False)

        tk.Label(win, text=tr("Installer les Modules"),
                 font=("Helvetica", 22, "bold"), fg="#a6e3a1", bg=BG_GLOBAL).pack(pady=(20, 4))
        tk.Label(win, text=tr("Tout s'installe dans venv/ — rien dans le système"),
                 font=("Helvetica", 12), fg="#a6e3a1", bg=BG_GLOBAL).pack(pady=(0, 16))

        # Couleurs du thème actif pour mettre en valeur la plateforme courante
        # (même comportement que Roland, mais dans les teintes du thème choisi).
        try:
            _th = self._tm.get_theme() if self._tm else {}
        except Exception:
            _th = {}
        _accent   = _th.get("accent",       "#a6e3a1")   # plateforme courante
        _dark_txt = _th.get("bg",           "#1a2e1a")   # texte foncé lisible
        _dim      = _th.get("bg_secondary", "#2a3d33")   # lanceurs non courants

        # Boutons plateformes — plateforme courante mise en évidence
        platforms = [
            ("🍎  macOS  (Homebrew + pip)", "Darwin",  self._install_mac),
            ("🐧  Linux  (apt / pacman)",   "Linux",   self._install_linux),
            ("🪟  Windows  (pip)",          "Windows", self._install_windows),
        ]
        for label, plat, cmd in platforms:
            _cur = (plat == SYSTEM)
            btn = HoverButton(win, label, lambda c=cmd, w=win: [w.destroy(), c()],
                              width=420, height=60, font_size=14,
                              fill_color=(_accent if _cur else BTN_COLOR),
                              text_color=(_dark_txt if _cur else None))
            btn.pack(pady=6, padx=30)

        # ── Séparateur ───────────────────────────────────────────────────
        tk.Frame(win, bg=_accent, height=2).pack(fill="x", padx=30, pady=(10, 6))
        tk.Label(win, text=tr("Créer le lanceur Ortho4XP (double-clic quotidien)"),
                 font=("Helvetica", 12, "bold"), fg="#a6e3a1", bg=BG_GLOBAL).pack(pady=(0, 6))

        launchers = [
            ("🍎  Créer Lanceur Ortho4XP — Mac",     "Darwin",  self._create_launcher_mac),
            ("🐧  Créer Lanceur Ortho4XP — Linux",   "Linux",   self._create_launcher_linux),
            ("🪟  Créer Lanceur Ortho4XP — Windows", "Windows", self._create_launcher_windows),
        ]
        for label, plat, cmd in launchers:
            _cur = (plat == SYSTEM)
            btn = HoverButton(win, label, lambda c=cmd, w=win: [w.destroy(), c()],
                              width=420, height=55, font_size=13,
                              fill_color=(_accent if _cur else _dim),
                              text_color=(_dark_txt if _cur else None))
            btn.pack(pady=4, padx=30)

        _ctk_button(win, text="Annuler", command=win.destroy
                    ).pack(pady=(10, 20))

        win.update_idletasks()
        # Centrer sur la fenêtre principale
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _run_pip_install(self, modules, extra_msg=""):
        """Installe une liste de modules dans le venv via pip."""
        pip = str(VENV_PIP)
        try:
            self._log("📦 Mise à jour pip...")
            subprocess.run([pip, "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
            self._log(f"📦 Installation modules{extra_msg}...")
            subprocess.run([pip, "install"] + modules, check=True)
            self._log("✅ Modules installés dans venv/")
        except Exception as e:
            self._log(f"❌ Échec : {e}")

    def _install_mac(self):
        self._log("── 🍎 Installation macOS ──────────────────")
        import shutil

        # 1. Homebrew deps (sans gdal — rasterio est autonome dans venv)
        brew = shutil.which("brew") or "/opt/homebrew/bin/brew" or "/usr/local/bin/brew"
        brew_pkgs = ["python@3.12", "python-tk@3.12",
                     "spatialindex", "p7zip", "proj", "libspatialite"]
        self._log(f"📦 Homebrew : {' '.join(brew_pkgs)}")
        try:
            subprocess.run([brew, "install"] + brew_pkgs, check=True)
            self._log("✅ Dépendances Homebrew installées.")
        except Exception as e:
            self._log(f"⚠ Homebrew : {e}")

        # 2. Pip dans venv — rasterio remplace gdal (autonome, pas de dépendance système)
        pip_modules = ["pyproj", "numpy", "shapely", "rtree", "Pillow",
                       "requests", "scikit-fmm", "certifi", "urllib3",
                       "psutil", "fiona", "scipy", "customtkinter", "rasterio"]
        self._run_pip_install(pip_modules, " (venv macOS)")
        self._log("✅ rasterio installé — lecture TIF altimétrie autonome dans venv/")

        # 4. Créer Lanceur ORTHO4XP.app
        self._log("🔧 Création de Lanceur ORTHO4XP.app...")
        self._create_mac_launcher()

    def _create_launcher_mac(self):
        self._log("── 🍎 Création Lanceur ORTHO4XP.app ──────")
        # Autonome : ne dépend plus du script externe create_launcher_ORTHO.py.
        # Réutilise la méthode interne éprouvée (binaire C compilé, .app posé à
        # la racine BASE_DIR), celle du flux d'installation macOS.
        try:
            self._create_mac_daily_launcher()
        except Exception as e:
            self._log(f"❌ {e}")

    def _create_launcher_linux(self):
        self._log("── 🐧 Création Lanceur ORTHO4XP.desktop ──")
        script = BASE_DIR / "create_launcher_ORTHO.py"
        if not script.exists():
            self._log("❌ create_launcher_ORTHO.py introuvable."); return
        py = str(VENV_PY) if VENV_PY.exists() else sys.executable
        try:
            r = subprocess.run([py, str(script)], cwd=str(BASE_DIR),
                               capture_output=True, text=True)
            for line in r.stdout.splitlines(): self._log(line)
            if r.returncode == 0:
                self._log("✅ Lanceur ORTHO4XP.desktop créé !")
            else:
                self._log(f"❌ {r.stderr[:300]}")
        except Exception as e: self._log(f"❌ {e}")

    def _create_launcher_windows(self):
        self._log("── 🪟 Création Lanceur ORTHO4XP.vbs ──────")
        script = BASE_DIR / "create_launcher_ORTHO.py"
        if not script.exists():
            self._log("❌ create_launcher_ORTHO.py introuvable."); return
        py = str(VENV_PY) if VENV_PY.exists() else sys.executable
        try:
            r = subprocess.run([py, str(script)], cwd=str(BASE_DIR),
                               capture_output=True, text=True)
            for line in r.stdout.splitlines(): self._log(line)
            if r.returncode == 0:
                self._log("✅ Lanceur ORTHO4XP.vbs créé !")
            else:
                self._log(f"❌ {r.stderr[:300]}")
        except Exception as e: self._log(f"❌ {e}")


    def _install_linux(self):
        self._log("── 🐧 Installation Linux ──────────────────")
        import shutil

        # Détecter le gestionnaire de paquets
        if shutil.which("apt-get"):
            self._log("📦 Détecté : Debian/Ubuntu (apt)")
            sys_pkgs = [
                "python3-pip", "python3-venv", "python3-tk",
                "python3-numpy", "python3-pyproj",
                "python3-shapely", "python3-rtree", "python3-pil",
                "python3-pil.imagetk", "python3-requests",
                "p7zip-full"
            ]
            try:
                subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y"] + sys_pkgs, check=True)
                self._log("✅ Paquets système installés.")
            except Exception as e:
                self._log(f"⚠ apt : {e}")

        elif shutil.which("pacman"):
            self._log("📦 Détecté : Arch/Manjaro (pacman)")
            sys_pkgs = [
                "python-pip", "python-numpy", "python-pyproj",
                "python-shapely", "python-rtree",
                "python-pillow", "python-requests", "p7zip"
            ]
            try:
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm"] + sys_pkgs, check=True)
                self._log("✅ Paquets système installés.")
            except Exception as e:
                self._log(f"⚠ pacman : {e}")
        else:
            self._log("⚠ Gestionnaire de paquets non reconnu.")

        # Pip dans venv
        pip_modules = ["psutil", "numpy", "Pillow", "requests", "shapely",
                       "pyproj", "fiona", "scipy", "customtkinter",
                       "rtree", "scikit-fmm", "certifi", "urllib3", "rasterio"]
        self._run_pip_install(pip_modules, " (venv Linux)")
        self._log("✅ rasterio installé — lecture TIF altimétrie autonome dans venv/")
        self._create_daily_launcher()
        # Créer Lanceur ORTHO4XP.desktop
        self._log("🔧 Création de Lanceur ORTHO4XP.desktop...")
        self._create_linux_launcher()

    def _install_windows(self):
        self._log("── 🪟 Installation Windows ──────────────────")
        pip_modules = [
            "psutil", "numpy", "Pillow", "requests", "shapely",
            "pyproj", "fiona", "scipy", "customtkinter",
            "rtree", "scikit-fmm", "certifi", "urllib3", "rasterio"
        ]
        self._run_pip_install(pip_modules, " (venv Windows)")
        self._log("✅ rasterio installé — lecture TIF altimétrie autonome dans venv/")
        self._create_daily_launcher()
        # Créer Lanceur ORTHO4XP.vbs
        self._log("🔧 Création de Lanceur ORTHO4XP.vbs...")
        self._create_windows_launcher()




    def _create_daily_launcher(self):
        """Crée Lanceur ORTHO4XP selon la plateforme — utilise le venv."""
        import stat as st

        if SYSTEM == "Darwin":
            self._create_mac_daily_launcher()
        elif SYSTEM == "Windows":
            self._create_windows_daily_launcher()
        elif SYSTEM == "Linux":
            self._create_linux_daily_launcher()

    def _create_mac_daily_launcher(self):
        """Crée Lanceur ORTHO4XP.app — binaire C qui lance le Launcher via venv."""
        import shutil, stat as st

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
            "display dialog \"Lancez d\'abord INSTALL_ORTHO4XP.app\" "
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

        app_path = BASE_DIR / "Lanceur ORTHO4XP.app"
        macos_dir = app_path / "Contents" / "MacOS"
        res_dir   = app_path / "Contents" / "Resources"

        if app_path.exists():
            shutil.rmtree(str(app_path))

        macos_dir.mkdir(parents=True)
        res_dir.mkdir(parents=True)
        (app_path / "Contents" / "Info.plist").write_text(INFO_PLIST, encoding="utf-8")

        c_file  = BASE_DIR / "_tmp_daily.c"
        exe_out = macos_dir / "launch"
        c_file.write_text(LAUNCHER_C, encoding="utf-8")

        compiled = False
        for arch_flags in [["-arch","arm64","-arch","x86_64"], []]:
            cmd = ["gcc"] + arch_flags + [str(c_file),"-o",str(exe_out),"-framework","Foundation","-O2"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                compiled = True
                break

        c_file.unlink(missing_ok=True)

        if compiled:
            exe_out.chmod(exe_out.stat().st_mode | st.S_IEXEC | st.S_IXGRP | st.S_IXOTH)
            try:
                subprocess.run(["xattr","-cr",str(app_path)], capture_output=True, timeout=10)
                subprocess.run(["codesign","--force","--deep","--sign","-",str(app_path)],
                               capture_output=True, timeout=30)
            except Exception: pass
            self._log("✅ Lanceur ORTHO4XP.app créé — double-clic pour lancer Ortho4XP !")
        else:
            self._log("⚠️  Compilation échouée — Lanceur non créé.")

    def _create_windows_daily_launcher(self):
        """Crée Lanceur ORTHO4XP.vbs pour Windows."""
        vbs = BASE_DIR / "Lanceur ORTHO4XP.vbs"
        vbs.write_text(
            "Dim ws,fso,d,py,la\n"
            "Set ws=CreateObject(\"WScript.Shell\")\n"
            "Set fso=CreateObject(\"Scripting.FileSystemObject\")\n"
            "d=fso.GetParentFolderName(WScript.ScriptFullName)\n"
            "py=d & \"\\\\venv\\\\Scripts\\\\pythonw.exe\"\n"
            "la=d & \"\\\\Ortho4XP_Launcher.py\"\n"
            "If Not fso.FileExists(py) Then\n"
            "  MsgBox \"Lancez d'abord INSTALL_ORTHO4XP.vbs\",48,\"Ortho4XP\"\n"
            "  WScript.Quit\nEnd If\n"
            "ws.Run Chr(34)&py&Chr(34)&\" \"&Chr(34)&la&Chr(34),1,False\n",
            encoding="utf-8")
        self._log("✅ Lanceur ORTHO4XP.vbs créé !")

    def _create_linux_daily_launcher(self):
        """Crée Lanceur ORTHO4XP.desktop pour Linux."""
        import stat as st
        sh = BASE_DIR / "Lanceur ORTHO4XP.sh"
        sh.write_text(
            f'''#!/bin/bash\ncd "{BASE_DIR}"\nexec "./venv/bin/python3" "Ortho4XP_Launcher.py"\n''',
            encoding="utf-8")
        sh.chmod(sh.stat().st_mode | st.S_IEXEC | st.S_IXGRP | st.S_IXOTH)
        desktop = BASE_DIR / "Lanceur ORTHO4XP.desktop"
        desktop.write_text(
            f"[Desktop Entry]\nVersion=3.0\nName=ORTHO4XP V3 Lanceur\n"
            f"Exec={sh}\nPath={BASE_DIR}\nTerminal=false\nType=Application\n",
            encoding="utf-8")
        desktop.chmod(desktop.stat().st_mode | st.S_IEXEC | st.S_IXGRP | st.S_IXOTH)
        self._log("✅ Lanceur ORTHO4XP.desktop créé !")

    def check_integrity(self):
        self._log("Vérification fichiers...")
        self._log(f"{'✅' if ORTHO_PY.exists() else '❌'} Ortho4XP.py")
        self._log(f"{'✅' if SRC_DIR.exists() else '❌'} Dossier src")

    # ── Création des lanceurs natifs ────────────────────────────────────

    def _create_mac_launcher(self):
        """Crée Lanceur ORTHO4XP.app — double-clic pour ouvrir le Launcher."""
        import shutil, stat as st_mod
        app_path  = BASE_DIR / "Lanceur ORTHO4XP.app"
        macos_dir = app_path / "Contents" / "MacOS"
        res_dir   = app_path / "Contents" / "Resources"
        if app_path.exists():
            shutil.rmtree(str(app_path))
        macos_dir.mkdir(parents=True)
        res_dir.mkdir(parents=True)

        # Info.plist
        (app_path / "Contents" / "Info.plist").write_text(
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>CFBundleExecutable</key><string>launch</string>
    <key>CFBundleIdentifier</key><string>com.ypsos.ortho4xp.v3.lanceur</string>
    <key>CFBundleName</key><string>ORTHO4XP V3 Lanceur</string>
    <key>CFBundleDisplayName</key><string>ORTHO4XP V3 Lanceur</string>
    <key>CFBundleVersion</key><string>3.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict></plist>''', encoding="utf-8")

        # Script shell — lance Ortho4XP_Launcher.py via venv
        sh_script = f'''#!/bin/bash
MACOS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$(dirname "$(dirname "$MACOS_DIR")")")"
cd "$ROOT"
exec "$ROOT/venv/bin/python3" "$ROOT/Ortho4XP_Launcher.py"
'''
        exe = macos_dir / "launch"
        exe.write_text(sh_script, encoding="utf-8")
        exe.chmod(exe.stat().st_mode | st_mod.S_IEXEC | st_mod.S_IXGRP | st_mod.S_IXOTH)

        # Quarantaine + signature
        try:
            subprocess.run(["xattr", "-cr", str(app_path)], capture_output=True, timeout=10)
            subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
                           capture_output=True, timeout=30)
        except Exception: pass

        self._log(f"✅ Lanceur ORTHO4XP.app créé — double-clic pour lancer !")

    def _create_linux_launcher(self):
        """Crée Lanceur ORTHO4XP.desktop + .sh"""
        import stat as st_mod
        sh_path = BASE_DIR / "Lanceur ORTHO4XP.sh"
        sh_path.write_text(
            f'''#!/bin/bash
cd "{BASE_DIR}"
exec "./venv/bin/python3" "Ortho4XP_Launcher.py"
''', encoding="utf-8")
        sh_path.chmod(sh_path.stat().st_mode | st_mod.S_IEXEC | st_mod.S_IXGRP | st_mod.S_IXOTH)

        desktop = BASE_DIR / "Lanceur ORTHO4XP.desktop"
        desktop.write_text(
            f"[Desktop Entry]\nVersion=3.0\nName=ORTHO4XP V3 Lanceur\n"
            f"Exec={sh_path}\nPath={BASE_DIR}\n"
            f"Terminal=false\nType=Application\nCategories=Utility;\n",
            encoding="utf-8")
        desktop.chmod(desktop.stat().st_mode | st_mod.S_IEXEC | st_mod.S_IXGRP | st_mod.S_IXOTH)
        self._log("✅ Lanceur ORTHO4XP.desktop créé — double-clic pour lancer !")

    def _create_windows_launcher(self):
        """Crée Lanceur ORTHO4XP.vbs — chemins RELATIFS (portable).

        Le .vbs dérive son propre dossier via WScript.ScriptFullName : il
        continue de fonctionner après déplacement ou renommage du dossier de
        base (plusieurs versions dans des dossiers différents). Identique à
        _create_windows_daily_launcher (plus de chemins absolus en dur)."""
        vbs = BASE_DIR / "Lanceur ORTHO4XP.vbs"
        vbs.write_text(
            "Dim ws,fso,d,py,la\n"
            "Set ws=CreateObject(\"WScript.Shell\")\n"
            "Set fso=CreateObject(\"Scripting.FileSystemObject\")\n"
            "d=fso.GetParentFolderName(WScript.ScriptFullName)\n"
            "py=d & \"\\\\venv\\\\Scripts\\\\pythonw.exe\"\n"
            "la=d & \"\\\\Ortho4XP_Launcher.py\"\n"
            "If Not fso.FileExists(py) Then\n"
            "  MsgBox \"Lancez d'abord INSTALL_ORTHO4XP.vbs\",48,\"Ortho4XP\"\n"
            "  WScript.Quit\nEnd If\n"
            "ws.Run Chr(34)&py&Chr(34)&\" \"&Chr(34)&la&Chr(34),1,False\n",
            encoding="utf-8")
        self._log("✅ Lanceur ORTHO4XP.vbs créé — double-clic pour lancer !")

    def launch_ortho(self):
        py_exe = str(VENV_PY) if VENV_PY.exists() else sys.executable
        if ORTHO_PY.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR)
            subprocess.Popen([py_exe, str(ORTHO_PY)], cwd=str(BASE_DIR), env=env, shell=False)
            self._log("🚀 Ortho4XP lancé !")
            self.after(1500, self.destroy)
        else: self._log("❌ Ortho4XP.py introuvable.")

if __name__ == "__main__":
    Launcher().mainloop()