#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et automatiséepar Roland (Ypsos) pour Ortho4XP V3. 
#  Sur la base d'une demande de LenOy d'un scan de performance manuel des meilleurs fournisseurs d'image par tuile.
#  Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
#  ============================================================
#  CREDIT — AUTHOR: Roland (Ypsos) - March 2026
#  This module was designed and automated by Roland (Ypsos) for Ortho4XP V3.
#  Based on a request from LenOy for a manual performance scan of the best imagery providers per tile.
#  This attribution notice MUST NEVER BE REMOVED, regardless of any subsequent changes to the file.
#  ============================================================

import sys
import tkinter as tk

try:
    import O4_Theme_Manager as THEME
except ImportError:
    THEME = None

try:
    import O4_GUI_Utils as GUI_UTILS
except ImportError:
    GUI_UTILS = None

# Import de la fonction de traduction (avec fallback si non chargée)
try:
    from O4_Lang import tr
except ImportError:
    def tr(text):
        return text


def cree_bouton_mac(parent, text, command, bg_color="#3A5F50", fg_color="white", hover_bg="#4A7563"):
    """
    Crée un bouton personnalisé sous forme de Label aux couleurs du thème
    pour contourner le bug visuel des boutons blancs/transparents natifs Tkinter sur macOS.
    """
    btn = tk.Label(
        parent,
        text=text,
        bg=bg_color,
        fg=fg_color,
        font=("Helvetica", 11, "bold"),
        padx=15,
        pady=6,
        relief="flat",
        bd=0,
        cursor="hand2"
    )

    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
    btn.bind("<Button-1>", lambda e: command())
    
    return btn


def valider_usage_personnel(parent=None):
    """
    Ouvre la fenêtre de confirmation d'avertissement en mode modal au premier plan.
    """
    if parent is None:
        parent = tk._default_root

    dlg = tk.Toplevel(parent)
    dlg.title(tr("Avertissement — Usage Strictement Personnel"))
    dlg.geometry("480x240")
    
    bg_theme = "#2D4A3E"
    dlg.configure(bg=bg_theme)

    msg = tr(
        "Fournisseur d'images à usage strictly personnel.\n\n"
        "Les tuiles générées à partir de ces sources ne pourront "
        "en aucun cas être diffusées ou redistribuées.\n\n"
        "Confirmez-vous cet usage strictly personnel ?"
    )
    
    lbl = tk.Label(
        dlg, 
        text=msg, 
        justify="center", 
        wraplength=420, 
        bg=bg_theme, 
        fg="white", 
        font=("Helvetica", 10, "bold")
    )
    lbl.pack(pady=20, padx=15)

    frame_btn = tk.Frame(dlg, bg=bg_theme)
    frame_btn.pack(pady=10)

    def action_valider():
        dlg.destroy()
        if 'ouvrir_fenetre_analyse_fournisseurs' in globals():
            ouvrir_fenetre_analyse_fournisseurs(parent, exclure_zonephoto=True)

    btn_valider = cree_bouton_mac(
        frame_btn, 
        text=tr("Je valide"), 
        command=action_valider,
        bg_color="#3A5F50", 
        fg_color="white",
        hover_bg="#4A7563"
    )
    btn_valider.pack(side="left", padx=15)

    btn_quitter = cree_bouton_mac(
        frame_btn, 
        text=tr("Je quitte"), 
        command=dlg.destroy,
        bg_color="#3A5F50", 
        fg_color="white",
        hover_bg="#4A7563"
    )
    btn_quitter.pack(side="right", padx=15)

    if THEME and hasattr(THEME, 'apply_to_root'):
        THEME.apply_to_root(dlg)

    dlg.transient(parent) if parent else None
    dlg.update_idletasks()
    dlg.lift()
    dlg.focus_force()
    
    try:
        dlg.grab_set()
    except tk.TclError:
        pass


def valider_usage_personnel_callback(parent, action_valider):
    """
    Ouvre l'avertissement. Si l'utilisateur clique sur 'Je valide',
    exécute 'action_valider' (qui ouvre la fenêtre d'analyse).
    """
    dlg = tk.Toplevel(parent)
    dlg.title(tr("Avertissement — Usage Strictement Personnel"))
    dlg.geometry("480x240")
    
    bg_theme = "#2D4A3E"
    dlg.configure(bg=bg_theme)

    msg = tr(
        "Fournisseur d'images à usage strictement personnel.\n\n"
        "Les tuiles générées à partir de ces sources ne pourront "
        "en aucun cas être diffusées ou redistribuées.\n\n"
        "Confirmez-vous cet usage strictement personnel ?"
    )
    lbl = tk.Label(dlg, text=msg, justify="center", wraplength=420, bg=bg_theme, fg="white", font=("Helvetica", 10, "bold"))
    lbl.pack(pady=20, padx=15)

    frame_btn = tk.Frame(dlg, bg=bg_theme)
    frame_btn.pack(pady=10)

    def valider():
        dlg.destroy()
        if action_valider:
            action_valider()

    btn_valider = cree_bouton_mac(
        frame_btn, 
        text=tr("Je valide"), 
        command=valider, 
        bg_color="#3A5F50", 
        fg_color="white",
        hover_bg="#4A7563"
    )
    btn_valider.pack(side="left", padx=15)

    btn_quitter = cree_bouton_mac(
        frame_btn, 
        text=tr("Je quitte"), 
        command=dlg.destroy, 
        bg_color="#3A5F50", 
        fg_color="white",
        hover_bg="#4A7563"
    )
    btn_quitter.pack(side="right", padx=15)

    dlg.transient(parent) if parent else None
    dlg.update_idletasks()
    dlg.lift()
    dlg.focus_force()
    try:
        dlg.grab_set()
    except tk.TclError:
        pass