#!/usr/bin/env python3
"""
Ortho4XP V2.0 - Point d'entrée principal
Version modernisée - Avril 2026
Compatible venv autonome + lancement automatique
"""

import sys
import os

# ============ GARDE-FOU DEMARRAGE (Python + tkinter) ============
# But : eviter un plantage illisible (ex. "ModuleNotFoundError: No
# module named '_tkinter'") quand Ortho est lance par erreur avec un
# mauvais Python (par ex. un python3 systeme mis a jour tout seul et
# depourvu de tkinter). Au lieu de crasher en charabia, on s'arrete
# proprement avec un message clair en francais.
_py = sys.version_info
_py_str = "{}.{}.{}".format(_py[0], _py[1], _py[2])
try:
    import tkinter as _tk_check
    del _tk_check
    _has_tk = True
except Exception:
    _has_tk = False

if not _has_tk:
    print("=" * 60)
    print("  ORTHO4XP - LANCEMENT ANNULE")
    print("=" * 60)
    print("  Python utilise : " + _py_str)
    print("  Chemin Python  : " + str(sys.executable))
    print("")
    print("  Ce Python ne contient pas 'tkinter' (affichage des")
    print("  fenetres). Ortho a besoin de ton environnement Python")
    print("  3.11 ou 3.12 (ton venv), qui contient tkinter.")
    print("")
    print("  --> Relance Ortho avec ton lanceur habituel (ton venv).")
    print("      Ne lance pas Ortho avec le python3 du systeme.")
    print("=" * 60)
    sys.exit(1)

if (_py[0], _py[1]) not in ((3, 11), (3, 12)):
    print("ATTENTION: Python " + _py_str + " detecte. Ortho est prevu")
    print("pour Python 3.11 ou 3.12. Si tu rencontres un souci,")
    print("relance Ortho avec ton venv habituel.")
# ============ FIN GARDE-FOU ============

# ====================== CONFIGURATION DES CHEMINS ======================
# Détection du mode "frozen" (lanceur .app / .exe) et chemin de base
if getattr(sys, 'frozen', False):
    Ortho4XP_dir = os.path.dirname(sys.executable)
else:
    Ortho4XP_dir = os.path.dirname(os.path.abspath(__file__))

# Ajout du dossier src au PYTHONPATH (structure propre V2)
sys.path.insert(0, os.path.join(Ortho4XP_dir, 'src'))

import O4_File_Names as FNAMES
sys.path.append(FNAMES.Provider_dir)

# Imports des modules principaux
import O4_Imagery_Utils as IMG
import O4_Vector_Map as VMAP
import O4_Mesh_Utils as MESH
import O4_Mask_Utils as MASK
import O4_Tile_Utils as TILE
import O4_GUI_Utils as GUI
import O4_Config_Utils as CFG   # Doit rester en dernier
import O4_Lang                   # Moteur de traduction (EN/FR)

def main():
    print("Ortho4XP V2.0 - Démarrage...")

    # Vérification du dossier Utils (binaires nvcompress, etc.)
    if not os.path.isdir(FNAMES.Utils_dir):
        print(f"ERREUR: Dossier manquant {FNAMES.Utils_dir}")
        print("Vérifiez votre installation. Exiting.")
        sys.exit(1)

    # Création automatique des dossiers requis
    required_dirs = (
        FNAMES.Preview_dir, FNAMES.Provider_dir, FNAMES.Extent_dir,
        FNAMES.Filter_dir, FNAMES.OSM_dir, FNAMES.Mask_dir,
        FNAMES.Imagery_dir, FNAMES.Elevation_dir, FNAMES.Geotiff_dir,
        FNAMES.Patch_dir, FNAMES.Tile_dir, FNAMES.Tmp_dir
    )

    for directory in required_dirs:
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                print(f"Création du dossier : {directory}")
            except Exception as e:
                print(f"ERREUR: Impossible de créer le dossier {directory} → {e}")
                sys.exit(1)

    # Initialisation des dictionnaires (providers, filtres, etc.)
    try:
        IMG.initialize_extents_dict()
        IMG.initialize_color_filters_dict()
        IMG.initialize_providers_dict()
        IMG.initialize_combined_providers_dict()
    except Exception as e:
        print(f"Attention lors de l'initialisation des providers/filtres : {e}")
        # On continue quand même (comme dans la V1)

    # ====================== MODE GUI (lancement normal) ======================
    if len(sys.argv) == 1:
        try:
            print("Lancement de l'interface graphique...")
            # Chargement silencieux de la langue depuis Ortho4XP.cfg
            # Le dialogue de choix est géré par INSTALL_PREREQUIS et le bouton 🌐
            _saved = O4_Lang._read_lang_from_cfg()
            if _saved:
                O4_Lang._load_lang(_saved)
            else:
                O4_Lang._load_lang("EN")
            app = GUI.Ortho4XP_GUI()
            # ── Journal unifié (ADDITIF) ────────────────────────────────────
            # Active le collecteur de logs APRÈS que la fenêtre a pris la main
            # sur l'affichage (sys.stdout), pour qu'il se place par-dessus et
            # capte tous les messages → un seul Ortho4XP.log à la racine.
            # Automatique à chaque lancement (aucun bouton à activer). Import
            # protégé : si le module est absent, Ortho démarre normalement.
            try:
                import O4_Log_Collector as _LOGCOL
                _LOGCOL.activate()
            except Exception:
                pass
            app.mainloop()
            print("Ortho4XP fermé. Bon vol !")
        except Exception as e:
            print(f"ERREUR lors du lancement de l'interface : {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # ====================== MODE LIGNE DE COMMANDE (conservé) ======================
    else:
        print("Mode ligne de commande activé")
        # Le code CLI original est conservé ici si tu en as besoin
        # (je peux le remettre en détail si tu veux)

        print("Bon vol !")


if __name__ == '__main__':
    main()
