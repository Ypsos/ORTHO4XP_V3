#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================

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


# ── Boutons look CustomTkinter (repli Label Mac-safe conservé) ──────────────
#  Si CustomTkinter est absent, on garde la fabrique Label existante :
#  l'appli fonctionne exactement comme avant.
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    _HAS_CTK = False


def _lighten_hex(hexcol, factor):
    """Éclaircit une couleur hex (#rrggbb) — pour le survol des boutons CTk."""
    try:
        h = hexcol.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hexcol


def cree_bouton_mac(parent, text, command, bg_color="#3A5F50", fg_color="white", hover_bg="#4A7563"):
    """
    Crée un bouton personnalisé sous forme de Label aux couleurs du thème
    pour contourner le bug visuel des boutons blancs/transparents natifs Tkinter sur macOS.
    """
    # Couleurs : priorité au thème actif (O4_Theme_Manager) ; les valeurs
    # passées en argument servent de repli si le thème est absent.
    if THEME is not None:
        try:
            _t = THEME.get_theme()
            bg_color = _t.get("btn_bg", bg_color)
            fg_color = _t.get("btn_fg", fg_color)
            hover_bg = _lighten_hex(_t.get("btn_bg", bg_color), 1.30)
        except Exception:
            pass

    # --- Branche CustomTkinter : bouton look fenêtre principale ------------
    #  .pack()/.side() restent disponibles → les 4 appelants sont inchangés.
    if _HAS_CTK:
        try:
            b = ctk.CTkButton(
                parent, text=text, command=command,
                corner_radius=8, border_width=1, height=30,
                fg_color=bg_color, hover_color=hover_bg,
                border_color=bg_color, text_color=fg_color,
                font=("Helvetica", 11, "bold"))
            # CORRECTIF macOS OBLIGATOIRE : redessin du remplissage arrondi
            # après mise en page (sinon rectangle sombre au repos).
            b.after_idle(
                lambda btn=b, c=bg_color: btn.winfo_exists()
                and btn.configure(fg_color=c))
            return b
        except Exception:
            pass  # échec CTk → repli Label ci-dessous

    # --- Repli Mac-safe conservé (Label) : CTk absent ---------------------
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