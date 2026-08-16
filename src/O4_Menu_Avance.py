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
#  O4_Menu_Avance.py  —  ORTHO4XP V3
#  « Avancé » : PORTE D'ENTRÉE unique vers les outils avancés.
#  Auteur : Roland (Ypsos)
#
#  Principe (validé avec Roland) : l'interface principale (O4_GUI_Utils.py) ne
#  reçoit QU'UN seul bouton « Avancé » qui ouvre CETTE fenêtre. Tous les outils
#  futurs (JOSM/Extents, générateur .comb, Altimétrie, Correction imagerie…)
#  s'ajoutent ICI, jamais dans l'écran principal. L'écran principal n'est donc
#  plus jamais retouché → aucun risque de le casser à chaque nouveauté.
#
#  Cette fenêtre ne contient AUCUNE logique métier : elle se contente d'OUVRIR
#  les modules déjà autonomes. Elle n'écrit rien, ne calcule rien.
#
#  Style : calqué EXACTEMENT sur O4_lay_generator.py (thème via O4_Theme_Manager,
#  boutons Mac-safe = Frame+Label, JAMAIS tk.Button à cause d'Aqua sur macOS).
# ==============================================================================

import sys
import os

# Détection OS (même logique que O4_lay_generator / O4_Theme_Manager)
if "dar" in sys.platform:
    _OS = "mac"
elif "win" in sys.platform:
    _OS = "windows"
else:
    _OS = "linux"

# Thème : importé si présent, sinon on retombe sur des couleurs par défaut.
try:
    import O4_Theme_Manager as _TM
    _HAS_THEME = True
except Exception:
    _TM = None
    _HAS_THEME = False

# Traduction : import protégé. Si O4_Lang est absent, tr() renvoie le texte
# tel quel (aucun plantage, interface reste lisible en français).
try:
    from O4_Lang import tr
except Exception:
    def tr(key):
        return key

# Langue active : import protégé. Sert UNIQUEMENT à choisir la version FR ou EN
# d'un tuto PDF et à afficher les libellés de la fenêtre tutos. Si O4_Lang est
# absent ou trop ancien, on retombe sur "EN" (comportement par défaut demandé).
try:
    from O4_Lang import current_lang as _current_lang
except Exception:
    def _current_lang():
        return "EN"


def _lang_code():
    """Retourne 'FR' si la langue active est le français, sinon 'EN'.
    Toutes les langues autres que FR retombent volontairement sur EN
    (règle validée avec Roland)."""
    try:
        code = (_current_lang() or "EN").upper()
    except Exception:
        code = "EN"
    return "FR" if code == "FR" else "EN"


def _L(fr, en):
    """Libellé bilingue résolu ICI (sans toucher aux fichiers O4_Lang_*).
    FR si langue active = français, EN sinon."""
    return fr if _lang_code() == "FR" else en


def _c(key, fallback):
    """Couleur du thème actif, ou fallback si Theme Manager absent."""
    if _HAS_THEME:
        try:
            return _TM.get_theme().get(key, fallback)
        except Exception:
            return fallback
    return fallback


# ── Bouton Mac-safe : Frame + Label (JAMAIS tk.Button) ────────────────────────
# Patron identique à _make_themed_button d'O4_lay_generator.py.
def _make_themed_button(tk, parent, text, command):
    bg = _c("btn_bg", "#4a6b59")
    fg = _c("btn_fg", "#ffffff")
    hover = _c("accent", "#5a7b69")
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
        if callable(command):
            command()

    for w in (frame, label):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)
        w.bind("<ButtonRelease-1>", on_release)
    return frame


# ── Tutos PDF : localisation, scan et ouverture ───────────────────────────────
# Le dossier Docs/ est à la RACINE du projet (un niveau au-dessus de src/).
# On le calcule à partir de l'emplacement de CE fichier → robuste quel que soit
# le répertoire courant d'où Ortho4XP est lancé.

def _docs_dir():
    """Chemin absolu du dossier Docs/ à la racine du projet."""
    here = os.path.dirname(os.path.abspath(__file__))          # …/src
    root = os.path.dirname(here)                                # …/ (racine)
    return os.path.join(root, "Docs")


def _scan_tutos():
    """Scanne Docs/ et regroupe les PDF par tuto.

    Convention (validée) : « <Titre>_FR.pdf » et « <Titre>_EN.pdf ».
    Retourne une liste triée de tuples (titre_affiche, {'FR': chemin, 'EN': chemin}).
    Un tuto qui n'existe que dans une langue reste proposé (on ouvrira la
    langue disponible). Les PDF sans suffixe _FR/_EN sont classés en EN par
    défaut pour rester visibles."""
    docs = _docs_dir()
    tutos = {}
    if not os.path.isdir(docs):
        return []
    try:
        noms = os.listdir(docs)
    except Exception:
        return []
    for nom in noms:
        if not nom.lower().endswith(".pdf"):
            continue
        base = nom[:-4]  # retire « .pdf »
        lang = "EN"
        cle = base
        if base[-3:].upper() == "_FR":
            lang = "FR"; cle = base[:-3]
        elif base[-3:].upper() == "_EN":
            lang = "EN"; cle = base[:-3]
        tutos.setdefault(cle, {})[lang] = os.path.join(docs, nom)
    # Titre lisible : underscores → espaces (l'utilisateur nomme ses fichiers
    # de façon parlante, ex. « 03_Importation_Sonny » → « 03 Importation Sonny »).
    resultat = []
    for cle in sorted(tutos.keys()):
        titre = cle.replace("_", " ").strip()
        resultat.append((titre, tutos[cle]))
    return resultat


def _ouvrir_pdf(chemin, status):
    """Ouvre un PDF avec le lecteur par défaut du système. Multi-OS."""
    try:
        if _OS == "mac":
            import subprocess
            subprocess.Popen(["open", chemin])
        elif _OS == "windows":
            os.startfile(chemin)  # type: ignore[attr-defined]
        else:
            import subprocess
            subprocess.Popen(["xdg-open", chemin])
        status(_L("Tuto ouvert : %s", "Guide opened: %s")
               % os.path.basename(chemin))
    except Exception as ex:
        status(_L("Impossible d'ouvrir le PDF : %s",
                  "Could not open the PDF: %s") % ex)


def _ouvrir_un_tuto(paires, status):
    """Ouvre la bonne langue d'un tuto : FR si langue active = FR et fichier FR
    présent, sinon EN ; si une seule langue existe, ouvre celle-là."""
    want = _lang_code()
    other = "EN" if want == "FR" else "FR"
    chemin = paires.get(want) or paires.get(other)
    if not chemin:
        status(_L("Aucun fichier PDF pour ce tuto.",
                  "No PDF file for this guide."))
        return
    _ouvrir_pdf(chemin, status)


def _ouvrir_tutos(parent, status):
    """Ouvre une fenêtre listant les tutos PDF présents dans Docs/.
    Import tkinter LOCAL (au clic), comme les autres actions."""
    import tkinter as tk

    tutos = _scan_tutos()

    BG = _c("bg", "#3b5b49")
    FG = _c("fg", "#e8f0ec")
    FG2 = _c("fg_secondary", "#a6e3a1")

    win = tk.Toplevel(parent) if parent is not None else tk.Toplevel()
    win.title(_L("Pas à pas — utilisation des modules",
                 "Step by step — using the modules"))
    win.configure(bg=BG)
    win.resizable(False, False)

    tk.Label(win, text=_L("Tutoriels pas à pas", "Step-by-step tutorials"),
             bg=BG, fg=FG,
             font=("Helvetica", 15, "bold") if _OS == "mac"
             else ("Segoe UI", 12, "bold"),
             pady=8).pack(fill="x", padx=14, pady=(12, 2))
    tk.Label(win,
             text=_L("Le PDF s'ouvre en français ou en anglais selon la langue.",
                     "The PDF opens in French or English depending on the language."),
             bg=BG, fg=FG2,
             font=("Helvetica", 11) if _OS == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=14, pady=(0, 10))

    status_var = tk.StringVar(value="")

    def status_local(msg):
        status_var.set(msg)

    zone = tk.Frame(win, bg=BG)
    zone.pack(fill="both", expand=True, padx=14, pady=4)

    if not tutos:
        tk.Label(zone,
                 text=_L("Aucun tuto trouvé dans le dossier Docs/.",
                         "No tutorial found in the Docs/ folder."),
                 bg=BG, fg=FG2,
                 font=("Helvetica", 11) if _OS == "mac" else ("Segoe UI", 9)
                 ).pack(fill="x", pady=8)
    else:
        for titre, paires in tutos:
            b = _make_themed_button(
                tk, zone, "📄  " + titre,
                (lambda p=paires: _ouvrir_un_tuto(p, status_local)))
            b.pack(fill="x", pady=4)

    tk.Label(win, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=("Helvetica", 11) if _OS == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=14, pady=(6, 4))

    fermer = _make_themed_button(tk, win, _L("Fermer", "Close"), win.destroy)
    fermer.pack(padx=14, pady=(2, 12))

    status(_L("Fenêtre des tutos ouverte.", "Tutorials window opened."))
    return win


# ── Actions des boutons ───────────────────────────────────────────────────────
# Chaque action se contente d'OUVRIR un module autonome. Import LOCAL (au clic)
# pour que la fenêtre Avancé s'ouvre même si un module optionnel est absent.

def _ouvrir_comb(parent, status):
    """Ouvre le générateur de .comb (module O4_comb_generator, chapitres 1-5).
    Tant que l'interface .comb n'est pas assemblée, on signale proprement."""
    try:
        import O4_comb_generator as CG
    except Exception as ex:
        status(tr("Générateur .comb introuvable : %s") % ex)
        return
    # L'interface graphique du .comb (fenêtre dédiée) sera branchée à l'étape
    # suivante. Point d'entrée attendu : run_comb_generator(parent).
    fn = getattr(CG, "run_comb_generator", None)
    if callable(fn):
        fn(parent)
        status(tr("Générateur .comb ouvert."))
    else:
        status(tr("Moteur .comb prêt (chapitres 1-5) — interface à assembler."))


def _ouvrir_comb_assembler(parent, status):
    """Ouvre l'ASSEMBLEUR de .comb (mode guidé) : tableau qui relie chaque
    extent présent dans Extents/ à un provider, avec alertes de couverture.
    Sortie dans Providers/Provider_Extents.comb. Même module que le générateur
    (O4_comb_generator), point d'entrée run_comb_assembler(parent). Import LOCAL
    et protégé : la fenêtre Avancé reste ouvrable même si le module est absent."""
    try:
        import O4_comb_generator as CG
    except Exception as ex:
        status(tr("Assembleur .comb introuvable : %s") % ex)
        return
    fn = getattr(CG, "run_comb_assembler", None)
    if callable(fn):
        try:
            fn(parent)
            status(tr("Assembleur .comb ouvert."))
        except Exception as ex:
            status(tr("Erreur à l'ouverture de l'assembleur .comb : %s") % ex)
    else:
        status(tr("Module .comb présent mais run_comb_assembler() absent."))


def _ouvrir_josm(parent, status):
    """Ouvre la fenêtre « Avancé (couches JOSM) » existante, sans la réécrire.
    On délègue au module autonome O4_Avance_Utils (point d'entrée
    open_avance_window(parent)). Import LOCAL et protégé : si le module est
    absent, on le signale proprement au lieu de planter."""
    try:
        import O4_Avance_Utils as _AV
    except Exception as ex:
        status(tr("Module JOSM (O4_Avance_Utils) introuvable : %s") % ex)
        return
    fn = getattr(_AV, "open_avance_window", None)
    if not callable(fn):
        status(tr("O4_Avance_Utils présent mais open_avance_window() absent."))
        return
    try:
        fn(parent)
        status(tr("Fenêtre JOSM ouverte."))
    except Exception as ex:
        status(tr("Erreur à l'ouverture de JOSM : %s") % ex)


def _a_venir(nom, status):
    """Bouton encore inactif : informe sans rien casser."""
    def action():
        status(tr("« %s » : à venir.") % nom)
    return action


def _ouvrir_altimetrie(parent, status):
    """Ouvre la fenêtre Altimétrie (module O4_Altimetrie_Utils).
    Import local au clic : la fenêtre Avancé s'ouvre même si le module
    est absent."""
    try:
        import O4_Altimetrie_Utils as ALTI
    except Exception as ex:
        status("Module Altimétrie introuvable : %s" % ex)
        return
    fn = getattr(ALTI, "open_altimetrie_window", None)
    if callable(fn):
        fn(parent)
        status("Altimétrie ouverte.")
    else:
        status("Point d'entrée Altimétrie manquant.")


def _ouvrir_extent_generator(parent, status):
    """Ouvre le Générateur d'Extents (module O4_Extent_Generator).
    Import local au clic : la fenêtre Avancé s'ouvre même si le module
    est absent. Point d'entrée attendu : run_extent_generator(parent)."""
    try:
        import O4_Extent_Generator as EXT
    except Exception as ex:
        status(_L("Générateur d'Extents introuvable : %s",
                  "Extent Generator not found: %s") % ex)
        return
    fn = getattr(EXT, "run_extent_generator", None)
    if not callable(fn):
        status(_L("O4_Extent_Generator présent mais run_extent_generator() absent.",
                  "O4_Extent_Generator present but run_extent_generator() missing."))
        return
    try:
        fn(parent)
        status(_L("Générateur d'Extents ouvert.", "Extent Generator opened."))
    except Exception as ex:
        status(_L("Erreur à l'ouverture du Générateur d'Extents : %s",
                  "Error opening the Extent Generator: %s") % ex)


# ── Fenêtre « Avancé » ────────────────────────────────────────────────────────
def run_menu_avance(parent=None):
    """
    Ouvre la fenêtre « Avancé ». Chargée seulement au clic (imports tkinter ici).
    parent = fenêtre principale Ortho4XP (ou None en test autonome).
    Retourne la fenêtre créée (utile pour les tests headless).
    """
    import tkinter as tk

    BG = _c("bg", "#3b5b49")
    FG = _c("fg", "#e8f0ec")
    FG2 = _c("fg_secondary", "#a6e3a1")

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(tr("Ortho4XP — Avancé"))
    win.configure(bg=BG)
    win.resizable(False, False)

    # Titre
    tk.Label(win, text=tr("Outils avancés"), bg=BG, fg=FG,
             font=("Helvetica", 15, "bold") if _OS == "mac"
             else ("Segoe UI", 12, "bold"),
             pady=8).pack(fill="x", padx=14, pady=(12, 2))
    tk.Label(win, text=tr("Chaque outil s'ouvre dans sa propre fenêtre."),
             bg=BG, fg=FG2,
             font=("Helvetica", 11) if _OS == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=14, pady=(0, 10))

    # Barre d'état en bas
    status_var = tk.StringVar(value="")

    def status(msg):
        status_var.set(msg)

    # Les boutons de la porte d'entrée. Un seul est actif aujourd'hui (.comb) ;
    # les autres sont posés « à venir » pour montrer la structure sans mentir.
    boutons = [
        (_L("🔗  Relier mes extents aux providers (.comb)",
            "🔗  Link my extents to providers (.comb)"),
         lambda: _ouvrir_comb_assembler(parent, status)),
        (_L("🧩  Générer un .comb — mode expert",
            "🧩  Generate a .comb — expert mode"),
         lambda: _ouvrir_comb(parent, status)),
        (tr("JOSM / Extents (masques, zones)"), lambda: _ouvrir_josm(parent, status)),
        (_L("🗺  Générer un Extent (pays / région)",
            "🗺  Generate an Extent (country / region)"),
         lambda: _ouvrir_extent_generator(parent, status)),
        (tr("QGIS / Altimétrie"), lambda: _ouvrir_altimetrie(parent, status)),
             (_L("📄  Pas à pas — utilisation des modules",
            "📄  Step by step — using the modules"),
         lambda: _ouvrir_tutos(parent, status)),
    ]

    zone = tk.Frame(win, bg=BG)
    zone.pack(fill="both", expand=True, padx=14, pady=4)
    for i, (texte, action) in enumerate(boutons):
        b = _make_themed_button(tk, zone, texte, action)
        b.pack(fill="x", pady=5)

    tk.Label(win, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=("Helvetica", 11) if _OS == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=14, pady=(6, 4))

    # Bouton de fermeture (Mac-safe lui aussi)
    fermer = _make_themed_button(tk, win, tr("Fermer"), win.destroy)
    fermer.pack(padx=14, pady=(2, 12))

    return win
