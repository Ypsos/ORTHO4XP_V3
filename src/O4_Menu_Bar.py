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
# =============================================================================
#  O4_Menu_Bar.py — Barre de menus native pour Ortho4XP V3
#  Auteur : Roland (Ypsos)
# =============================================================================
#
#  Rôle
#  ----
#  Fournit UNE fonction, install_menubar(window), qui pose une barre de menus
#  native (tk.Menu) sur une fenêtre Tkinter. Le même code s'affiche
#  automatiquement selon le système :
#     • macOS  → barre en haut de l'écran (look application Mac)
#     • Windows→ barre sous la barre de titre de la fenêtre
#     • Linux  → barre en haut de la fenêtre
#
#  Principe
#  --------
#  La barre est un AJOUT PUR : chaque entrée appelle une méthode qui existe
#  DÉJÀ sur la fenêtre principale (open_config_window, build_tile, …). Aucun
#  bouton de l'interface n'est retiré, aucune logique moteur n'est touchée.
#  Le module n'importe pas O4_GUI_Utils (évite tout import circulaire) : il
#  reçoit la fenêtre et appelle ses méthodes par leur nom, avec garde-fou si
#  une méthode venait à manquer.
#
#  Langue (FR / EN codées ICI, dans le module)
#  -------------------------------------------
#  Les libellés sont écrits en français ET en anglais directement dans ce
#  fichier, via l'aide L("français", "english"). La langue affichée suit la
#  langue active d'Ortho4XP (O4_Lang._current_lang, sauvegardée dans
#  Ortho4XP.cfg sous language=FR/EN). AUCUN fichier de langue externe n'est
#  modifié. Défaut de secours : anglais (comme O4_Lang).
#  La barre est construite au démarrage ; un changement de langue est pris en
#  compte au redémarrage de l'application (même comportement que les boutons,
#  eux aussi traduits à la construction).
#
#  Couleurs / police
#  -----------------
#  Les couleurs sont lues depuis O4_Theme_Manager quand il est présent. Elles
#  sont honorées par la barre sous Linux ; macOS et Windows imposent le style
#  natif de leur barre système (limite des OS, pas du code).
# =============================================================================

import sys
import os
import tkinter as tk
from tkinter import messagebox

_IS_MAC = "dar" in sys.platform


# ── Langue active ─────────────────────────────────────────────────────────
def _current_lang():
    """Renvoie le code de langue actif d'Ortho4XP ('FR', 'EN', …).

    Lu depuis O4_Lang._current_lang, avec repli sûr sur 'EN' (langue de
    secours du projet) si O4_Lang est absent ou muet.
    """
    try:
        import O4_Lang
        code = getattr(O4_Lang, "_current_lang", "EN")
        return (code or "EN").upper()
    except Exception:
        return "EN"


def L(fr, en):
    """Renvoie le texte français ou anglais selon la langue active.

    FR et EN sont ainsi codés côte à côte dans le module, sans dépendre des
    fichiers de langue externes. Toute langue autre que le français retombe
    sur l'anglais (base internationale du projet).
    """
    return fr if _current_lang().startswith("FR") else en


# ── Couleurs de thème (facultatives) ─────────────────────────────────────
def _theme_colors():
    """Renvoie (bg, fg, active_bg, active_fg) depuis le thème, avec repli sûr."""
    bg, fg = "#3b5b49", "#e8f0ec"
    active_bg, active_fg = "#a6e3a1", "#1e3028"
    try:
        import O4_Theme_Manager as _TM
        t = _TM.get_theme()
        bg = t.get("bg", bg)
        fg = t.get("fg", fg)
        active_bg = t.get("accent", active_bg)
    except Exception:
        pass
    return bg, fg, active_bg, active_fg


def _menu_kwargs():
    """Options de couleur pour les menus.

    Sous Linux la barre honore ces couleurs ; sous macOS/Windows la barre
    système ignore le style : on n'envoie donc rien pour éviter tout effet
    de bord, et l'OS applique son apparence native.
    """
    if _IS_MAC:
        return {}
    bg, fg, active_bg, active_fg = _theme_colors()
    return dict(bg=bg, fg=fg,
                activebackground=active_bg, activeforeground=active_fg)


def _wire(menu, window, label, method_name):
    """Ajoute une entrée qui appelle window.<method_name>().

    Garde-fou : si la méthode n'existe pas (ou n'est pas appelable), l'entrée
    est tout de même affichée mais désactivée, plutôt que de faire planter la
    barre entière. Aucune fonction existante n'est ainsi jamais perdue
    silencieusement — au pire elle apparaît grisée, signal visible.
    """
    fn = getattr(window, method_name, None)
    if callable(fn):
        menu.add_command(label=label, command=fn)
    else:
        menu.add_command(label=label, state="disabled")


def _about(window):
    """Boîte « À propos » — titre de la fenêtre, auteur, crédit d'origine et
    licence. Utilisée par le lanceur ET par la fenêtre principale (même
    fonction) : licence et crédits deviennent ainsi accessibles depuis les
    deux interfaces, sans ajouter d'entrée de menu. Entièrement défensive.
    """
    try:
        titre = window.title()
    except Exception:
        titre = "Ortho4XP V3"
    texte = (
        titre + "\n\n"
        + L("Auteur : Roland (Ypsos)", "Author: Roland (Ypsos)") + "\n"
        + L("D'après Ortho4XP d'Oscar Pilote et shred86 (v1.40)",
            "Based on Ortho4XP by Oscar Pilote and shred86 (v1.40)") + "\n\n"
        + L("Sous licence GPLv3", "Licensed under GPLv3")
    )
    try:
        messagebox.showinfo(L("À propos", "About"), texte)
    except Exception:
        pass


def _open_module(window, module_name, entry_point):
    """Ouvre une fenêtre de module en appelant directement son point d'entrée.

    Même principe que Altimétrie/Bathymétrie : import du module + appel de sa
    fonction run_*/open_*(parent). Entièrement défensif : si le module ou le
    point d'entrée manque, ne fait rien (le menu ne plante jamais).
    """
    try:
        import importlib
        mod = importlib.import_module(module_name)
        fn = getattr(mod, entry_point, None)
        if callable(fn):
            fn(window)
    except Exception:
        pass


# ── Tutos « Pas à pas » (autonomes, repris de O4_Menu_Avance) ─────────────
#  Rendus indépendants ici pour que O4_Menu_Avance.py puisse disparaître.
#  Convention de nommage des PDF : « <Titre>_FR.pdf » / « <Titre>_EN.pdf »
#  dans le dossier Docs/ à la racine du projet.

def _docs_dir():
    """Chemin absolu du dossier Docs/ à la racine du projet (un cran au-dessus
    de src/, où vit ce module)."""
    here = os.path.dirname(os.path.abspath(__file__))   # …/src
    root = os.path.dirname(here)                          # …/ (racine)
    return os.path.join(root, "Docs")


def _scan_tutos():
    """Scanne Docs/ et regroupe les PDF par tuto.

    Retourne une liste triée de (titre_affiché, {'FR': chemin, 'EN': chemin}).
    Un PDF sans suffixe _FR/_EN est classé EN pour rester visible.
    """
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
        base = nom[:-4]
        lang = "EN"
        cle = base
        if base[-3:].upper() == "_FR":
            lang = "FR"; cle = base[:-3]
        elif base[-3:].upper() == "_EN":
            lang = "EN"; cle = base[:-3]
        tutos.setdefault(cle, {})[lang] = os.path.join(docs, nom)
    resultat = []
    for cle in sorted(tutos.keys()):
        titre = cle.replace("_", " ").strip()
        resultat.append((titre, tutos[cle]))
    return resultat


def _open_pdf(chemin):
    """Ouvre un PDF avec le lecteur par défaut du système (multi-OS)."""
    try:
        if _IS_MAC:
            import subprocess
            subprocess.Popen(["open", chemin])
        elif sys.platform.startswith("win"):
            os.startfile(chemin)  # type: ignore[attr-defined]
        else:
            import subprocess
            subprocess.Popen(["xdg-open", chemin])
    except Exception:
        pass


def _open_one_tuto(paires):
    """Ouvre la bonne langue d'un tuto : FR si langue active = FR et fichier FR
    présent, sinon EN ; si une seule langue existe, ouvre celle-là."""
    want = "FR" if _current_lang().startswith("FR") else "EN"
    other = "EN" if want == "FR" else "FR"
    chemin = paires.get(want) or paires.get(other)
    if chemin:
        _open_pdf(chemin)


def _add_tutos_submenu(parent, window, mkw):
    """Sous-menu « Pas à pas » listant les PDF trouvés dans Docs/.

    Remplace l'ancienne fenêtre : chaque tuto est une entrée de menu qui ouvre
    directement le PDF (langue active FR/EN, repli sur l'autre). Si aucun tuto,
    une entrée grisée l'indique. Native → contraste géré par l'OS.
    """
    sub = tk.Menu(parent, tearoff=0, **mkw)
    tutos = _scan_tutos()
    if not tutos:
        sub.add_command(label=L("Aucun tuto trouvé dans Docs/",
                                "No tutorial found in Docs/"), state="disabled")
    else:
        for titre, paires in tutos:
            sub.add_command(label="📄  " + titre,
                            command=(lambda p=paires: _open_one_tuto(p)))
    parent.add_cascade(
        label=L("Pas à pas — utilisation des modules",
                "Step by step — using the modules"), menu=sub)


def install_menubar(window):
    """Construit et attache la barre de menus native sur `window`.

    `window` est la fenêtre principale Ortho4XP_GUI (un tk.Tk). La fonction
    garde une référence à la barre sur la fenêtre (window._menubar) pour
    éviter tout ramassage mémoire, et renvoie la barre.
    """
    mkw = _menu_kwargs()
    menubar = tk.Menu(window)

    # ── Fichier ───────────────────────────────────────────────────────
    m_file = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_file, window, L("Dossier de base…", "Base folder…"),
          "choose_custom_build_dir")
    m_file.add_separator()
    _wire(m_file, window, L("Quitter", "Quit"), "exit_prg")
    menubar.add_cascade(label=L("Fichier", "File"), menu=m_file)

    # ── Configuration ─────────────────────────────────────────────────
    m_cfg = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_cfg, window, L("Préférences / Configuration…", "Preferences / Configuration…"),
          "open_config_window")
    _wire(m_cfg, window, L("Providers personnels…", "Personal providers…"),
          "open_personal_provider_window")
    _wire(m_cfg, window, L("Zoom level par zone…", "Per-zone zoom level…"),
          "open_custom_zl_window")
    menubar.add_cascade(label=L("Configuration", "Configuration"), menu=m_cfg)

    # ── Outils ────────────────────────────────────────────────────────
    m_tools = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_tools, window, L("Altimétrie / DEM / QGIS…", "Altimetry / DEM / QGIS…"),
          "open_altimetrie_module")
    _wire(m_tools, window, L("Bathymétrie / QGIS…", "Bathymetry / QGIS…"),
          "open_bathymetrie_module")
    _wire(m_tools, window, L("Créer / modifier un provider (.lay)…",
                             "Create / edit a provider (.lay)…"),
          "open_lay_generator_module")
    _wire(m_tools, window, L("Cache OSM local (.pbf)…", "Local OSM cache (.pbf)…"),
          "open_pbf_module")
    _wire(m_tools, window, L("Analyse des fournisseurs…", "Provider analysis…"),
          "open_provider_score_module")
    m_tools.add_separator()
    m_tools.add_command(
        label=L("JOSM / Extents (masques, zones)", "JOSM / Extents (masks, zones)"),
        command=lambda: _open_module(window, "O4_Avance_Utils", "open_avance_window"))
    # Générer un .comb : sous-menu à deux modes (remplace la fenêtre de choix)
    m_comb = tk.Menu(m_tools, tearoff=0, **mkw)
    m_comb.add_command(
        label=L("🤖  Mode automatisé (relier mes extents aux providers)",
                "🤖  Automated mode (link my extents to providers)"),
        command=lambda: _open_module(window, "O4_comb_generator", "run_comb_assembler"))
    m_comb.add_command(
        label=L("🛠  Mode expert (tableau éditable ligne à ligne + éditeur texte)",
                "🛠  Expert mode (row-by-row editable table + text editor)"),
        command=lambda: _open_module(window, "O4_comb_generator", "run_comb_corriger"))
    m_tools.add_cascade(
        label=L("Générer un .comb", "Generate a .comb"), menu=m_comb)
    m_tools.add_command(
        label=L("Générer un Extent (pays / région)", "Generate an Extent (country / region)"),
        command=lambda: _open_module(window, "O4_Extent_Generator", "run_extent_generator"))
    m_tools.add_separator()
    _wire(m_tools, window,
          L("Corrections R.G.B., Netteté, saturation…",
            "R.G.B., Sharpness, Saturation corrections…"),
          "open_color_check")
    _wire(m_tools, window, L("Correction imagerie / zone…", "Imagery / zone correction…"),
          "open_correction_module")
    m_tools.add_separator()
    _wire(m_tools, window, L("Vue Terre…", "Earth view…"),
          "open_earth_window")
    _wire(m_tools, window, L("Simulateur d'aperçu…", "Preview simulator…"),
          "open_simulator_window")
    menubar.add_cascade(label=L("Outils", "Tools"), menu=m_tools)

    # ── Fabrication ───────────────────────────────────────────────────
    m_build = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_build, window, L("1 · Données vectorielles", "1 · Assemble Vector data"),
          "build_poly_file")
    _wire(m_build, window, L("2 · Maillage 3D", "2 · Triangulate 3D Mesh"),
          "build_mesh")
    _wire(m_build, window, L("2.1 · Patchs de mer", "2.1 · Sea Patches"),
          "build_sea_patches")
    _wire(m_build, window, L("2.5 · Masques d'eau", "2.5 · Draw Water Masks"),
          "build_masks")
    _wire(m_build, window, L("3 · Imagerie / DSF", "3 · Build Imagery / DSF"),
          "build_tile")
    m_build.add_separator()
    _wire(m_build, window, L("Tout en un", "All in one"),
          "build_all")
    menubar.add_cascade(label=L("Fabrication", "Build"), menu=m_build)

    # ── Aide ──────────────────────────────────────────────────────────
    m_help = tk.Menu(menubar, tearoff=0, **mkw)
    _add_tutos_submenu(m_help, window, mkw)
    m_help.add_separator()
    m_help.add_command(label=L("À propos d'Ortho4XP…", "About Ortho4XP…"),
                       command=lambda: _about(window))
    menubar.add_cascade(label=L("Aide", "Help"), menu=m_help)

    # ── Attache + conserve une référence (anti-ramasse-miettes) ────────
    window.config(menu=menubar)
    window._menubar = menubar
    return menubar


# =============================================================================
#  Barre de menus du LANCEUR (Ortho4XP_Launcher.py)
# =============================================================================
#
#  Fonction séparée de install_menubar (fenêtre principale). Même principe :
#  ajout pur, chaque entrée appelle une méthode DÉJÀ présente sur le lanceur.
#  Le gros bouton « LANCER ORTHO4XP » n'est PAS mis en menu : il reste au
#  premier niveau de la fenêtre (action quotidienne principale).
# =============================================================================

def _os_label(base_fr, base_en, plat_code):
    """Libellé d'entrée plateforme, avec marquage de l'OS courant.

    L'OS détecté est suffixé d'un ✓ et d'une mention lisible (fonctionne sur
    les 3 systèmes, contrairement à une couleur que la barre native ignore).
    """
    import platform
    current = (platform.system() == plat_code)
    txt = base_fr if _current_lang().startswith("FR") else base_en
    if current:
        txt += "  ✓ " + ("(votre système)" if _current_lang().startswith("FR")
                          else "(your system)")
    return txt, current


def _add_platform_submenu(parent, window, title, meth_prefix, mkw):
    """Construit un sous-menu à 3 OS (Mac/Linux/Windows).

    meth_prefix : '_install' ou '_create_launcher'. Chaque entrée appelle
    window.<meth_prefix>_<os>. L'OS courant est marqué ✓ et placé en tête.
    Garde-fou _wire : méthode absente → entrée grisée, jamais de plantage.
    """
    sub = tk.Menu(parent, tearoff=0, **mkw)
    # (libellé_fr, libellé_en, code plateforme, suffixe de méthode)
    rows = [
        ("🍎 macOS",  "🍎 macOS",   "Darwin",  "mac"),
        ("🐧 Linux",  "🐧 Linux",   "Linux",   "linux"),
        ("🪟 Windows", "🪟 Windows", "Windows", "windows"),
    ]
    # OS courant d'abord
    rows.sort(key=lambda r: r[2] != __import__("platform").system())
    for fr, en, plat, suffix in rows:
        label, _cur = _os_label(fr, en, plat)
        _wire(sub, window, label, meth_prefix + "_" + suffix)
    parent.add_cascade(label=title, menu=sub)


def _add_theme_submenu(parent, window, mkw):
    """Sous-menu Thème construit depuis O4_Theme_Manager.list_themes().

    Chaque thème appelle window._apply_theme(cle) (même effet que le sélecteur
    actuel : applique + redémarre). Le thème actif est marqué ✓. Défensif : si
    le gestionnaire de thème est absent, le sous-menu n'est simplement pas ajouté.
    """
    try:
        import O4_Theme_Manager as _TM
        themes = _TM.list_themes()               # {cle: libellé}
        try:
            active = _TM.current_theme_name()
        except Exception:
            active = None
    except Exception:
        return  # pas de gestionnaire de thème → pas de sous-menu Thème

    sub = tk.Menu(parent, tearoff=0, **mkw)
    apply_fn = getattr(window, "_apply_theme", None)
    for key, label in themes.items():
        txt = label + ("  ✓" if key == active else "")
        if callable(apply_fn):
            sub.add_command(label=txt, command=lambda k=key: window._apply_theme(k))
        else:
            sub.add_command(label=txt, state="disabled")
    parent.add_cascade(
        label=L("Thème", "Theme"), menu=sub)


def _launcher_pick_language(window, code):
    """Applique une langue choisie dans le sous-menu Langue.

    Réplique ce que fait le dialogue : écrit le code dans Ortho4XP.cfg via
    O4_Lang._write_lang_to_cfg, puis redémarre le lanceur (qui relira la
    langue au démarrage) via window._restart_with_new_lang. Entièrement
    défensif : en cas d'absence de l'un ou l'autre, ne fait rien.
    """
    try:
        import O4_Lang
        w = getattr(O4_Lang, "_write_lang_to_cfg", None)
        if callable(w):
            w(code)
        cb = getattr(window, "_restart_with_new_lang", None)
        if callable(cb):
            cb()
    except Exception:
        pass


def _add_language_submenu(parent, window, mkw):
    """Sous-menu Langue — FR + EN uniquement.

    Le projet ne maintient que le français et l'anglais (traduction codée
    dans chaque module ; toute autre langue retombe sur l'anglais). Le
    sous-menu ne propose donc que ces deux langues, pour ne pas promettre une
    traduction inexistante. Les fichiers O4_Lang_XX.py éventuels restent sur
    le disque, intacts — ils sont simplement masqués ici (cacher ≠ supprimer).
    Choisir une langue applique + redémarre. ✓ sur la langue active.
    """
    LANGS = [("EN", "🇬🇧 English"), ("FR", "🇫🇷 Français")]
    try:
        import O4_Lang
        try:
            active = (O4_Lang.current_lang() or "").upper()
        except Exception:
            active = ""
    except Exception:
        return  # pas de moteur de langue → pas de sous-menu

    sub = tk.Menu(parent, tearoff=0, **mkw)
    for code, label in LANGS:
        txt = label + ("  ✓" if code == active else "")
        sub.add_command(label=txt,
                        command=lambda c=code: _launcher_pick_language(window, c))
    parent.add_cascade(label=L("Langue", "Language"), menu=sub)


def install_launcher_menubar(window):
    """Construit et attache la barre de menus native sur le LANCEUR (enrichie).

    Structure validée avec Roland :
      Fichier       : Lancer Ortho4XP · Quitter
      Installation  : Installer les modules ▸ (3 OS) · Créer le lanceur ▸ (3 OS)
                      · Vérifier l'intégrité
      Configuration : Thème ▸ · Éditeur de thème… · Changer la langue…
      Aide          : Historique · Crédits & Licence · À propos
    Ajout pur : chaque entrée appelle une méthode DÉJÀ présente sur le lanceur.
    Le gros bouton « LANCER ORTHO4XP » reste au premier niveau de la fenêtre.
    """
    mkw = _menu_kwargs()
    menubar = tk.Menu(window)

    # ── Fichier ───────────────────────────────────────────────────────
    m_file = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_file, window, L("Lancer Ortho4XP", "Launch Ortho4XP"), "launch_ortho")
    m_file.add_separator()
    m_file.add_command(label=L("Quitter", "Quit"), command=window.destroy)
    menubar.add_cascade(label=L("Fichier", "File"), menu=m_file)

    # ── Installation ──────────────────────────────────────────────────
    m_inst = tk.Menu(menubar, tearoff=0, **mkw)
    _add_platform_submenu(
        m_inst, window,
        L("Installer les modules", "Install modules"),
        "_install", mkw)
    _add_platform_submenu(
        m_inst, window,
        L("Créer le lanceur Ortho4XP", "Create Ortho4XP launcher"),
        "_create_launcher", mkw)
    m_inst.add_separator()
    _wire(m_inst, window, L("Vérifier l'intégrité", "Check integrity"),
          "check_integrity")
    menubar.add_cascade(label=L("Installation", "Installation"), menu=m_inst)

    # ── Configuration ─────────────────────────────────────────────────
    m_cfg = tk.Menu(menubar, tearoff=0, **mkw)
    _add_theme_submenu(m_cfg, window, mkw)
    _wire(m_cfg, window, L("Éditeur de thème personnalisé…", "Custom theme editor…"),
          "_apply_theme_btn")
    _add_language_submenu(m_cfg, window, mkw)
    menubar.add_cascade(label=L("Configuration", "Configuration"), menu=m_cfg)

    # ── Aide ──────────────────────────────────────────────────────────
    m_help = tk.Menu(menubar, tearoff=0, **mkw)
    _wire(m_help, window, L("Historique", "History"), "show_history")
    _wire(m_help, window, L("Crédits & Licence", "Credits & License"), "show_credits")
    m_help.add_command(label=L("À propos d'Ortho4XP…", "About Ortho4XP…"),
                       command=lambda: _about(window))
    menubar.add_cascade(label=L("Aide", "Help"), menu=m_help)

    window.config(menu=menubar)
    window._menubar = menubar
    return menubar
