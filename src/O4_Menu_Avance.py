# -*- coding: utf-8 -*-
# ==============================================================================
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
        (tr("Générer un fichier .comb"), lambda: _ouvrir_comb(parent, status)),
        (tr("JOSM / Extents (masques, zones)"), lambda: _ouvrir_josm(parent, status)),
        (tr("Altimétrie"), _a_venir(tr("Altimétrie"), status)),
        (tr("Correction imagerie"), _a_venir(tr("Correction imagerie"), status)),
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


if __name__ == "__main__":
    # Ouverture réelle si lancé directement (utile pour vérifier à l'œil).
    run_menu_avance().mainloop()
