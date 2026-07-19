# ============================================================
#  O4_Lang_FR.py  —  ORTHO4XP V2  —  Fichier de langue : FRANÇAIS
#  Tous les textes de l'interface en français.
#  Les textes anglais d'origine ont été traduits en français.
#  Les ajouts français du projet sont conservés tels quels.
#  Généré le : 2026-05-05
# ============================================================

LANG = "FR"

T = {

    # ── FENÊTRE PRINCIPALE ─────────────────────────────────────────
    "Latitude:"                         : "Latitude :",
    "Longitude:"                        : "Longitude :",
    "Imagery:"                          : "Imagerie :",
    "Zoomlevel:"                        : "Niveau zoom :",
    "Zoomlevel : "                      : "Niveau zoom : ",
    "Base Folder:"                      : "Dossier racine :",

    # ── BOUTONS PRINCIPAUX DE BUILD ────────────────────────────────
    "Assemble Vector data"              : "Assembler vecteurs",
    "Triangulate 3D Mesh"               : "Trianguler le maillage 3D",
    " Draw Water Masks  "               : " Dessiner masques eau  ",
    " Build Imagery/DSF "               : " Construire Imagerie/DSF ",
    "    All in one     "               : "    Tout en un     ",
    "Sea Patches (2.1)"                : "Patches Mer (2.1)",

    # ── VUE CARTE / TUILE ──────────────────────────────────────────
    "Active tile"                       : "Tuile active",
    "Erase cached data"                 : "Vider le cache",
    "Batch build tiles"                 : "Construction en lot",
    "  Batch Build   "                  : "  Construction en lot  ",
    "  Delete    "                      : "  Supprimer    ",
    "    Refresh     "                  : "    Rafraîchir     ",
    "      Exit      "                  : "      Quitter      ",
    "     Exit     "                    : "     Quitter     ",
    "    Exit     "                     : "    Quitter     ",
    "Shortcuts :\\n-----------------\\nB2-press+hold=move map\\n"
                                        : "Raccourcis :\\n-----------------\\nB2-maintenu = déplacer carte\\n",
    "Carte Earth non disponible\\n"     : "Carte Earth non disponible\\n",

    # ── ÉDITEUR DE ZONES / OVERLAY ─────────────────────────────────
    "Zone params "                      : "Paramètres zone ",
    "Preview params "                   : "Paramètres preview ",
    "Preview"                           : "Aperçu",
    "Source : "                         : "Source : ",
    "Approx. Add. Size : "              : "Taille ajout approx. : ",
    "  Save zone  "                     : "  Sauv. zone  ",
    "Delete ZL zone"                    : "Suppr. zone ZL",
    "Make GeoTiffs"                     : "Créer GeoTiffs",
    "Extract Mesh "                     : "Extraire Mesh ",
    "    Apply    "                     : "    Appliquer    ",
    "    Apply     "                    : "    Appliquer     ",
    "    Reset    "                     : "    Réinitialiser    ",
    "Ctrl+B1 : add texture\\nShift+B1: add zone point\\n"
                                        : "Ctrl+B1 : ajouter texture\\nShift+B1 : ajouter point de zone\\n",

    # ── PANNEAU CONFIGURATION ──────────────────────────────────────
    "Application "                      : "Application ",
    "Load Tile Cfg "                    : "Charger cfg tuile",
    "Write Tile Cfg"                    : "Écrire cfg tuile",
    "Reload App Cfg"                    : "Recharger cfg app",
    "Write App Cfg "                    : "Écrire cfg app",
    "Ok"                                : "Ok",
    "Enable"                            : "Activer",
    "Strength:"                         : "Intensité :",

    # ── PANNEAU COLOR NORMALIZE ────────────────────────────────────
    # ── TIMELINE / BENCHMARK (Phase 3) ────────────────────────────
    "⏱ Timeline"                        : "⏱ Chronologie",
    "⏱ Timeline — Durées du build"      : "⏱ Chronologie — Durées du build",
    "Timeline non disponible."          : "Chronologie non disponible.",
    "Fermer"                            : "Fermer",
    "Step 1 — Vectors"                  : "Étape 1 — Vecteurs",
    "Step 2 — Mesh"                     : "Étape 2 — Maillage",
    "Step 2.5 — Masks"                  : "Étape 2.5 — Masques",
    "Step 2.1 — Sea Patches"            : "Étape 2.1 — Patches Mer",
    "Step 3 — DSF/Imagery"              : "Étape 3 — DSF/Imagerie",
    "Build All"                         : "Tout construire",

        "Color Normalize"                   : "Normalisation couleurs",
    "RGB adjustments, sharpness, saturation"
                                        : "Corrections R.G.B., Netteté, saturation",
    "Réf: "                             : "Réf : ",

    # ── SIMULATEUR ─────────────────────────────────────────────────
    "🎚 Visualisation réglages"         : "🎚 Visualisation réglages",
    "Survolez un curseur."              : "Survolez un curseur.",
    "↺  Recharger depuis cfg"           : "↺  Recharger depuis cfg",
    "✅  Write Tile cfg"                : "✅  Écrire cfg tuile",
    "🌍  Write App cfg"                 : "🌍  Écrire cfg app",
    "✖  Fermer"                         : "✖  Fermer",

    # Noms des onglets du simulateur
    "💧 Mer & Eau"                      : "💧 Mer & Eau",
    "🌊 Côte & Masques"                 : "🌊 Côte & Masques",
    "⛰ Terrain & Relief"               : "⛰ Terrain & Relief",
    "🗺 Mesh 3D"                        : "🗺 Mesh 3D",
    "📷 Imagerie & Aéroports"           : "📷 Imagerie & Aéroports",

    # Noms des groupes du simulateur
    "Eau & Transparence"                : "Eau & Transparence",
    "Masques côtiers"                   : "Masques côtiers",
    "Courbure côte"                     : "Courbure côte",
    "Altimétrie & Vecteurs"             : "Altimétrie & Vecteurs",
    "Terrain & Ombrage"                 : "Terrain & Ombrage",
    "Paramètres Mesh"                   : "Paramètres Mesh",
    "Qualité & Nettoyage"               : "Qualité & Nettoyage",
    "Imagerie"                          : "Imagerie",
    "Aéroports"                         : "Aéroports",
    "Routes"                            : "Routes",

    # ── COLOR CHECK ────────────────────────────────────────────────
    "Corrections R.G.B., Netteté, saturation, Zone de fusion"
                                        : "Corrections R.G.B., Netteté, saturation, Zone de fusion",
    "Couches ZL / Tuiles (toutes)"      : "Couches ZL / Tuiles (toutes)",
    "① Couches / Corrections"           : "① Couches / Corrections",
    "② Dégradé de jointure sources"     : "② Dégradé de jointure sources",
    "Couleur Cible — extends / ZL"      : "Couleur Cible — extends / ZL",
    "Correction sRGB par canal + Saturation"
                                        : "Correction sRGB par canal + Saturation",
    "Netteté"                           : "Netteté",
    "Rayon dégradé :"                   : "Rayon dégradé :",
    "Dégradé : OFF"                     : "Dégradé : OFF",
    "Dégradé de jointure : désactivé (jointure nette)"
                                        : "Dégradé de jointure : désactivé (jointure nette)",
    "Jointure colorimétrique — déplacez le curseur"
                                        : "Jointure colorimétrique — déplacez le curseur",
    "  Rayons effectifs : dégradé OFF"  : "  Rayons effectifs : dégradé OFF",
    "(damier progressif — toute la tuile)"
                                        : "(damier progressif — toute la tuile)",
    "Source A : —"                      : "Source A : —",
    "Source B : —"                      : "Source B : —",
    "Gauche = original  |  Droite = corrigé  — clic pour agrandir"
                                        : "Gauche = original  |  Droite = corrigé  — clic pour agrandir",
    "ORIGINAL"                          : "ORIGINAL",
    "CORRIGÉ"                           : "CORRIGÉ",

    # Boutons Color Check
    "🔍 Scanner couches"                : "🔍 Scanner couches",
    "📋 Exporter liste"                 : "📋 Exporter liste",
    "🎨 Appliquer au groupe"            : "🎨 Appliquer au groupe",
    "💾 Générer .comb"                  : "💾 Générer .comb",
    "👁 Batch Preview couche"           : "👁 Aperçu lot couche",
    "🗑 Supprimer DDS sélect."          : "🗑 Supprimer DDS sélect.",
    "🎯 Auto-détecter"                  : "🎯 Auto-détecter",
    "↺ Reset curseurs"                  : "↺ Reset curseurs",
    "🔬 Auto depuis Cible"              : "🔬 Auto depuis Cible",
    "🔨 Build avec dégradé (toute la tuile)"
                                        : "🔨 Construire avec dégradé (tuile entière)",
    "🔨 Lancer Build (groupe)"          : "🔨 Lancer construction (groupe)",
    "👁 Preview dégradé (avant Build)"  : "👁 Aperçu dégradé (avant construction)",
    "🛡 Générer .comb seam (zone protégée)"
                                        : "🛡 Générer .comb jointure (zone protégée)",
    "💾 Archiver"                       : "💾 Archiver",
    "📂 Restaurer"                      : "📂 Restaurer",
    "↺ Reset zoom"                      : "↺ Reset zoom",
    "↺ Vue entière"                     : "↺ Vue entière",
    "✅ Appliquer ce rayon et fermer"   : "✅ Appliquer ce rayon et fermer",
    "✅ Restaurer"                      : "✅ Restaurer",
    "✅ Valider et générer .comb"       : "✅ Valider et générer .comb",
    "✏ Renommer sélect."               : "✏ Renommer sélect.",
    "✖ Fermer sans appliquer"          : "✖ Fermer sans appliquer",
    "Archive corrections (Color_check/)": "Archiver corrections (Color_check/)",

    # Messages d'avertissement Color Check
    "⚠ Aucun DDS disponible pour le preview."
                                        : "⚠ Aucun DDS disponible pour le preview.",
    "⚠ Aucun DDS disponible."          : "⚠ Aucun DDS disponible.",
    "⚠ Aucun DDS scanné."              : "⚠ Aucun DDS scanné.",
    "⚠ Aucun DDS sélectionné pour générer le .comb seam."
                                        : "⚠ Aucun DDS sélectionné pour générer le .comb seam.",
    "⚠ Aucun fichier dans ce groupe."  : "⚠ Aucun fichier dans ce groupe.",
    "⚠ Aucune archive dans Color_check/ — archivez d'abord des corrections."
                                        : "⚠ Aucune archive dans Color_check/ — archivez d'abord des corrections.",
    "⚠ Aucune correction à archiver — appliquez d'abord des corrections."
                                        : "⚠ Aucune correction à archiver — appliquez d'abord des corrections.",
    "⚠ Dossier Color_check/ introuvable — aucune archive disponible."
                                        : "⚠ Dossier Color_check/ introuvable — aucune archive disponible.",
    "⚠ Sélectionnez d'abord un DDS."  : "⚠ Sélectionnez d'abord un DDS.",
    "⚠ Sélectionnez d'abord une couche ZL dans la liste."
                                        : "⚠ Sélectionnez d'abord une couche ZL dans la liste.",
    "⚠ Sélectionnez d'abord une couche ZL ou un fichier."
                                        : "⚠ Sélectionnez d'abord une couche ZL ou un fichier.",
    "⚠ Sélectionnez d'abord une couche ZL."
                                        : "⚠ Sélectionnez d'abord une couche ZL.",
    "⚠ Sélectionnez un DDS individuel.": "⚠ Sélectionnez un DDS individuel.",
    "⚠ Sélectionnez un DDS à gauche ET une cible à droite."
                                        : "⚠ Sélectionnez un DDS à gauche ET une cible à droite.",
    "⚠ Tous les curseurs sont à 0 — ajustez au moins un curseur."
                                        : "⚠ Tous les curseurs sont à 0 — ajustez au moins un curseur.",

    # Messages de statut Color Check
    "En attente…"                       : "En attente…",
    "Scan en cours…"                    : "Scan en cours…",
    "Analyse…"                          : "Analyse…",
    "Chargement…"                       : "Chargement…",
    "Chargement image…"                 : "Chargement image…",
    "Détection jointure…"               : "Détection jointure…",

    # Dialogues Color Check
    "Choisir une archive à restaurer :" : "Choisir une archive à restaurer :",
    "Dessinez des rectangles sur les zones à protéger (pistes, marquages)"
                                        : "Dessinez des rectangles sur les zones à protéger (pistes, marquages)",
    "Dessinez des rectangles sur les zones à protéger."
                                        : "Dessinez des rectangles sur les zones à protéger.",
    "Clic+glisser = nouveau rectangle  |  Clic sur zone = sélectionner  |  Suppr = effacer"
                                        : "Clic+glisser = nouveau rectangle  |  Clic sur zone = sélectionner  |  Suppr = effacer",
    "Zones protégées"                   : "Zones protégées",
    "Étiquette :"                       : "Étiquette :",
    "🗑 Supprimer sélect."              : "🗑 Supprimer sélect.",
    "🗑 Tout effacer"                   : "🗑 Tout effacer",
    "Annuler"                           : "Annuler",
    "💡 Seam persistante : augmentez le rayon\\n"
                                        : "💡 Jointure persistante : augmentez le rayon\\n",

    # ── MESSAGES STATUT / CONFIGURATION ───────────────────────────
    "✓ Valeurs chargées depuis le cfg." : "✓ Valeurs chargées depuis le cfg.",
    "✅ Sauvegardé dans cfg tuile."     : "✅ Sauvegardé dans cfg tuile.",
    "✅ Sauvegardé dans cfg global."    : "✅ Sauvegardé dans cfg global.",

    # ── MESSAGES CONSOLE / LOG ─────────────────────────────────────
    "-> Opening download queue."        : "-> Ouverture file de téléchargement.",
    "Download process interrupted."     : "Téléchargement interrompu.",
    " *Download of textures completed." : " *Téléchargement des textures terminé.",
    " *DDS conversion of textures completed."
                                        : " *Conversion DDS des textures terminée.",
    " *Activating DSF file."            : " *Activation du fichier DSF.",
    "DDS conversion process interrupted."
                                        : "Conversion DDS interrompue.",
    "DSF construction interrupted."    : "Construction DSF interrompue.",
    "ERROR : could not rename DSF file, tile is not actived."
                                        : "ERREUR : impossible de renommer le DSF, tuile non activée.",
    "ERROR: Cannot create tile subdirectories."
                                        : "ERREUR : impossible de créer les sous-dossiers de la tuile.",
    "-> Checking airport locations for upgraded zoomlevel."
                                        : "-> Vérification des aéroports pour ZL amélioré.",
    "-> Initializing providers with potential data on this tile."
                                        : "-> Initialisation des providers pour cette tuile.",
    "-> Reading mesh data"              : "-> Lecture des données mesh",
    "-> Reading mesh file"              : "-> Lecture du fichier mesh",
    "-> Encoding of the DSF file"       : "-> Encodage du fichier DSF",
    "-> Construction of the masks"      : "-> Construction des masques",
    "-> Deleting existing masks"        : "-> Suppression des masques existants",
    "-> Computing point pools and texture requirements"
                                        : "-> Calcul des pools de points et besoins textures",
    "-> Adapting water triangles to XP12 requirements"
                                        : "-> Adaptation des triangles eau aux exigences XP12",
    "-> Computing bathymetry depth ratio bounds based on distance masks"
                                        : "-> Calcul des bornes de bathymétrie selon masques distance",
    "App config loaded from:"           : "Config app chargée depuis :",
    "App config written to:"            : "Config app écrite dans :",
    "Tile config loaded from:"          : "Config tuile chargée depuis :",
    "Tile config written to:"           : "Config tuile écrite dans :",
    "Server could not be connected, retrying in 2 secs"
                                        : "Serveur inaccessible, nouvel essai dans 2 s",
    "Server said 'Forbidden' ! (IP banned?)"
                                        : "Serveur : 'Forbidden' ! (IP bannie ?)",
    "Server said 'Internal Error'."     : "Serveur : 'Internal Error'.",
    "Server said 'Not Found'"           : "Serveur : 'Not Found'",
    "Blur of a mask !"                  : "Flou d'un masque !",
    "Blur of the mask..."               : "Application du flou au masque…",
    "Buffer of the mask..."             : "Buffer du masque…",
    "Cannot write into"                 : "Impossible d'écrire dans",
    "Crop needed"                       : "Recadrage nécessaire",
    "Warp needed"                       : "Reprojection nécessaire",
    "Could not test coverage of "       : "Impossible de tester la couverture de ",
    "Could not write global config:"    : "Impossible d'écrire le cfg global :",
    "Error while writing tile cfg:"     : "Erreur lors de l'écriture du cfg tuile :",
    "Finished imprinting"               : "Impression terminée",
    "Imprinting for provider"           : "Impression pour le provider",
    "Global config file contains an invalid line:"
                                        : "Le cfg global contient une ligne invalide :",
    "Preview non générée :"             : "Preview non générée :",
    "   WARNING: 7z decompression failed, bathymetry skipped."
                                        : "   AVERTISSEMENT : décompression 7z échouée, bathymétrie ignorée.",
    "   WARNING: Corrupted Global Scenery DSF, bathymetry skipped."
                                        : "   AVERTISSEMENT : DSF Global Scenery corrompu, bathymétrie ignorée.",
    "   WARNING: Global Scenery DSF absent, bathymetry skipped."
                                        : "   AVERTISSEMENT : DSF Global Scenery absent, bathymétrie ignorée.",
    "   WARNING: could not copy Global Scenery DSF, bathymetry skipped."
                                        : "   AVERTISSEMENT : copie DSF Global Scenery impossible, bathymétrie ignorée.",

    # ── DIALOGUE DE SÉLECTION DE LANGUE ───────────────────────────
    "language_dialog_title"             : "Language / Langue",
    "language_dialog_message"           : "Choisissez votre langue :",
    "language_btn_en"                   : "🇬🇧  English",
    "language_btn_fr"                   : "🇫🇷  Français",
    "language_menu_tools"               : "Outils",
    "language_menu_change_lang"         : "Changer la langue…",

    # ── FENÊTRE CUSTOM ZOOMLEVELS / PREVIEW ───────────────────────
    "Preview / Custom zoomlevels"       : "Aperçu / Niveaux zoom custom",
    "Tiles collection and management"   : "Sélection et gestion des tuiles",
    "Ctrl+B1 : add texture\\nShift+B1: add zone point\\n"
                                        : "Ctrl+B1 : ajouter texture\\nShift+B1 : point de zone\\n",

    # ── TITRES SECTIONS FENÊTRE CONFIG ────────────────────────────
    "Vector data"                       : "Données vectorielles",
    "Mesh"                              : "Maillage",
    "Masks"                             : "Masques",
    "DSF/Imagery"                       : "DSF/Imagerie",

    # ── CHECKBOXES COLLECTION DE TUILES ───────────────────────────
    "OSM data"                          : "Données OSM",
    "Mask data"                         : "Données masques",
    "Jpeg imagery"                      : "Imagerie JPEG",
    "Tile (whole)"                      : "Tuile (entière)",
    "Tile (textures)"                   : "Tuile (textures)",
    "Assemble vector data"              : "Assembler vecteurs",
    "Triangulate 3D mesh"               : "Trianguler mesh 3D",
    "Draw water masks"                  : "Dessiner masques eau",
    "Build imagery/DSF"                 : "Construire Imagerie/DSF",
    "Extract overlays"                  : "Extraire overlays",
    "Read per tile cfg"                 : "Lire cfg par tuile",
    "Shortcuts :"                       : "Raccourcis :",
    "B2-press+hold=move map"            : "B2-maintenu = déplacer carte",

    # ── FENÊTRE LAUNCHER ───────────────────────────────────────────
    "1. Installer les Modules"              : "1. Installer les Modules",
    "🔍 Vérifier Intégrité"                : "🔍 Vérifier Intégrité",
    "▶️ LANCER ORTHO4XP"                   : "▶️ LANCER ORTHO4XP",
    "Installer les Modules — Choisir la plateforme"
                                            : "Installer les Modules — Choisir la plateforme",
    "Installer les Modules"                 : "Installer les Modules",
    "Tout s'installe dans venv/ — rien dans le système"
                                            : "Tout s'installe dans venv/ — rien dans le système",
    "Créer le lanceur Ortho4XP (double-clic quotidien)"
                                            : "Créer le lanceur Ortho4XP (double-clic quotidien)",

    # ── LABELS TECHNIQUES GUI (format DDS, référence couleur) ──────
    "Réf: Calibré_48753_JPG_Europe"     : "Réf : Calibré_48753_JPG_Europe",
    "BC1 — TERRE"                       : "BC1 — TERRE",
    "BC1 — MER"                         : "BC1 — MER",
    "BC3 — MER"                         : "BC3 — MER",


    # ── CORRECTION IMAGERIE/ZONE — bouton & fenêtre ───────────────
    "Visualiser la tuile"                    : "Visualiser la tuile",
    "Visualiser la tuile — Ortho4XP V3"      : "Visualiser la tuile — Ortho4XP V3",
    "Mosaïque des DDS de la tuile — à venir" : "Mosaïque des DDS de la tuile — à venir",
    "Dossier textures introuvable pour cette tuile." : "Dossier textures introuvable pour cette tuile.",
    "Aucun DDS dans le dossier textures de la tuile." : "Aucun DDS dans le dossier textures de la tuile.",
    "Préparation des vignettes…"             : "Préparation des vignettes…",
    "Supprimer patches sélectionnés"         : "Supprimer patches sélectionnés",
    "Précédent"                              : "Précédent",
    "QGIS"                                   : "QGIS",
    "Suppression dossier Preview"            : "Suppression dossier Preview",
    "Aucun dossier Preview à supprimer."     : "Aucun dossier Preview à supprimer.",
    "Supprimer le dossier Preview ({n} fichiers) ?": "Supprimer le dossier Preview ({n} fichiers) ?",
    "Dossier Preview supprimé ({n} fichiers).": "Dossier Preview supprimé ({n} fichiers).",
    "Effacer JPG source et relancer étape 3" : "Effacer JPG source et relancer étape 3",
    "Aucune vignette cochée."                : "Aucune vignette cochée.",
    "Supprimer {n} JPG source puis relancer l'étape 3 ?": "Supprimer {n} JPG source puis relancer l'étape 3 ?",
    "{n} JPG source supprimé(s). Étape 3 relancée." : "{n} JPG source supprimé(s). Étape 3 relancée.",
    "Relancez l'étape 3 dans la fenêtre principale." : "Relancez l'étape 3 dans la fenêtre principale.",
    "Suivant"                                : "Suivant",
    "Détail de la tuile"                     : "Détail de la tuile",
    "À corriger (copier le JPG source)"      : "À corriger (copier le JPG source)",
    "JPG source copié dans les patches"      : "JPG source copié dans les patches",
    "Un patch existe déjà pour cette tuile"  : "Un patch existe déjà pour cette tuile",
    "Aucun JPG source trouvé pour cette tuile": "Aucun JPG source trouvé pour cette tuile",
    "Correction (choisir application)"       : "Correction (choisir application)",
    "Ouvrir dans l'éditeur"                  : "Ouvrir dans l'éditeur",
    "GIMP"                                   : "GIMP",
    "JOSM"                                   : "JOSM",
    "à venir"                                : "à venir",
    "🖊 Correction imagerie/zone"           : "🖊 Correction imagerie/zone",
    "Correction imagerie et traitement de zone"
                                            : "Correction imagerie et traitement de zone",

    # ── GESTION JPG-PATCH — textes fenêtre ────────────────────────
    "Gestion JPG-Patch — Ortho4XP V3"       : "Gestion JPG-Patch — Ortho4XP V3",
    "Gestion des JPG-Patch existants"        : "Gestion des JPG-Patch existants",
    "patch(es) trouvé(s) dans"              : "patch(es) trouvé(s) dans",
    "Sélection patches à conserver — Ortho4XP V3" : "Sélection patches à conserver — Ortho4XP V3",
    "Cocher les patches à CONSERVER"         : "Cocher les patches à CONSERVER",
    "(Les patches non cochés seront supprimés)" : "(Les patches non cochés seront supprimés)",
    "Tout cocher"   : "Tout cocher",
    "Tout décocher" : "Tout décocher",
    "← Cliquer sur un patch"                : "← Cliquer sur un patch",
    # ── GESTION JPG-PATCH — fenêtre dialogue ──────────────────────
    "🗑  Tout supprimer"                 : "🗑  Tout supprimer",
    "✅  Tout conserver"                 : "✅  Tout conserver",
    "🔍  Sélection patches"             : "🔍  Sélection patches",

    # ── PROVIDERS PERSONNELS ───────────────────────────────────────
    "Personnel"                             : "Personnel",
    "personal_provider_window_title"        : "Providers Personnels — Ortho4XP V3",
    "personal_provider_list_label"          : "Mes providers :",
    "personal_provider_name_label"          : "Nom du provider (code) :",
    "personal_provider_url_label"           : "URL des jpg (TMS) :",
    "personal_provider_url_hint"            : "ex. : https://serveur.com/{zoom}/{x}/{y}.jpg",
    "personal_provider_save_btn"            : "💾  Enregistrer",
    "personal_provider_cancel_btn"          : "✖  Annuler",
    "personal_provider_modify_btn"          : "✏  Modifier",
    "personal_provider_delete_btn"          : "🗑  Supprimer",
    "personal_provider_saved_ok"            : "Provider enregistré. Sélectionnez-le dans la liste Imagerie.",
    "personal_provider_deleted_ok"          : "Provider supprimé.",
    "personal_provider_err_name"            : "Le nom du provider ne peut pas être vide.",
    "personal_provider_err_url"             : "L'URL ne peut pas être vide.",
    "personal_provider_err_name_invalid"    : "Le nom doit être alphanumérique (sans espaces).",
    "personal_provider_err_reserved"        : "Ce nom est réservé. Veuillez en choisir un autre.",
    "personal_provider_select_hint"         : "← Sélectionnez un provider pour modifier/supprimer",

    # ── COLOR CHECK — boutons et labels dynamiques ─────────────────
    "🗑 Supprimer TOUS DDS ZL"          : "🗑 Supprimer TOUS DDS ZL",
    "Gradient: {radius} px — next Build"     : "Dégradé : {radius} px — prochain Build",
    "Checker gradient: {radius} px — applies to all DDS at next Build"
                                        : "Dégradé damier : {radius} px — s'applique à tous les DDS au prochain Build",
    "  Effective radii (base {base}px):" : "  Rayons effectifs (base {base}px) :",
    "💡 Persistent seam: increase radius\n   or generate a .comb mask on the area."
                                        : "💡 Seam persistante : augmentez le rayon\n   ou générez un masque .comb sur la zone.",
    "⚠ too low"                         : "⚠ trop faible",
    "⚠ detail risk"                     : "⚠ risque détails",


    # ── LOGS CONSOLE — O4_Sea_Texture.py ──────────────────────────
    "   [SeaTex] JPG-Patch généré : {jpg_name}"
                                        : "   [SeaTex] JPG-Patch généré : {jpg_name}",
    "   [SeaTex] Construction arêtes mesh..."
                                        : "   [SeaTex] Construction arêtes mesh...",
    "   [SeaTex] {n} triangle(s) mer côtier(s) détecté(s)."
                                        : "   [SeaTex] {n} triangle(s) mer côtier(s) détecté(s).",

    # ── LOGS CONSOLE — O4_Mask_Utils.py ───────────────────────────
    "ERROR: masks_width = {mw} m est invalide (trop grand). Maximum autorisé pour cette tuile et ce mask_zl : {maxw} m. Diminuez masks_width dans la config de la tuile et relancez l'étape masks (2.5)."
                                        : "ERROR: masks_width = {mw} m est invalide (trop grand). Maximum autorisé pour cette tuile et ce mask_zl : {maxw} m. Diminuez masks_width dans la config de la tuile et relancez l'étape masks (2.5).",

    # ── LOGS CONSOLE — O4_Imagery_Utils.py ───────────────────────
    "   [SeaTex] Provider PATCH injecté."
                                        : "   [SeaTex] Provider PATCH injecté.",
    "   [SeaTex] PATCH injecté pour provider simple : {pc}"
                                        : "   [SeaTex] PATCH injecté pour provider simple : {pc}",
    "   [SeaTex] JPG absent — fond mer utilisé : {name}"
                                        : "   [SeaTex] JPG absent — fond mer utilisé : {name}",
    "   [SeaTex] paste masqué échoué, paste direct : {e}"
                                        : "   [SeaTex] paste masqué échoué, paste direct : {e}",
    "   [SeaTex] PATCH absent pour cette position — ignoré"
                                        : "   [SeaTex] PATCH absent pour cette position — ignoré",
    "   [SeaTex] PATCH appliqué comme fond (aucun JPG provider)"
                                        : "   [SeaTex] PATCH appliqué comme fond (aucun JPG provider)",
    "   [SeaTex] PATCH appliqué : {n} px nodata comblés"
                                        : "   [SeaTex] PATCH appliqué : {n} px nodata comblés",
    "   [SeaTex] PATCH : aucun nodata blanc détecté — ignoré"
                                        : "   [SeaTex] PATCH : aucun nodata blanc détecté — ignoré",

    # ── LOGS CONSOLE — O4_Tile_Utils.py ──────────────────────────
    "   [SeaTex] ERREUR : initialisation providers échouée."
                                        : "   [SeaTex] ERREUR : initialisation providers échouée.",
    "   [SeaTex] Aucune tuile mer côtière détectée — rien à générer."
                                        : "   [SeaTex] Aucune tuile mer côtière détectée — rien à générer.",
    "   [SeaTex] Cas 1 terminé — {n} patch(es) nodata corrigés."
                                        : "   [SeaTex] Cas 1 terminé — {n} patch(es) nodata corrigés.",
    "   [SeaTex] Step 2.1 terminé."     : "   [SeaTex] Step 2.1 terminé.",
    "   [SeaTex] Passage 2 terminé — {n} DDS générés."
                                        : "   [SeaTex] Passage 2 terminé — {n} DDS générés.",
    "   [Batch] DSF .tmp corrompu supprimé : {name}"
                                        : "   [Batch] DSF .tmp corrompu supprimé : {name}",
    "   [Batch] Tuile {tile} ignorée (erreur OSM) — batch continue."
                                        : "   [Batch] Tuile {tile} ignorée (erreur OSM) — batch continue.",
    "   [Batch] Tuile {tile} ignorée (erreur mesh) — batch continue."
                                        : "   [Batch] Tuile {tile} ignorée (erreur mesh) — batch continue.",
    "   [Batch] Tuile {tile} ignorée (erreur masque) — batch continue."
                                        : "   [Batch] Tuile {tile} ignorée (erreur masque) — batch continue.",
    "   [Batch] Tuile {tile} ignorée (erreur DSF/imagery) — batch continue."
                                        : "   [Batch] Tuile {tile} ignorée (erreur DSF/imagery) — batch continue.",
    "   [Batch] Tuile {tile} ignorée (erreur overlay) — batch continue."
                                        : "   [Batch] Tuile {tile} ignorée (erreur overlay) — batch continue.",
    "Batch terminé avec {n} tuile(s) ignorée(s) :"
                                        : "Batch terminé avec {n} tuile(s) ignorée(s) :",



    # ── ALTIMÉTRIE / DEM ───────────────────────────────────────────
    '⛰ Altimétrie / DEM'
        : '⛰ Altimétrie / DEM',
    'Altimétrie / DEM'
        : 'Altimétrie / DEM',
    'Altimétrie / DEM — Ortho4XP V3'
        : 'Altimétrie / DEM — Ortho4XP V3',
    'Le module O4_Altimetrie_Utils.py est introuvable dans le dossier src/.'
        : 'Le module O4_Altimetrie_Utils.py est introuvable dans le dossier src/.',
    'Latitude / longitude invalides.'
        : 'Latitude / longitude invalides.',
    'Créer / choisir la structure'
        : 'Créer / choisir la structure',
    'Ajouter un pays'
        : 'Ajouter un pays',
    'Rafraîchir'
        : 'Rafraîchir',
    'Assembler'
        : 'Assembler',
    'Vérifier (auto-test)'
        : 'Vérifier (auto-test)',
    'Choisir QGIS'
        : 'Choisir QGIS',
    'Ouvrir dans QGIS'
        : 'Ouvrir dans QGIS',
    'Fermer'
        : 'Fermer',
    'QGIS :'
        : 'QGIS :',
    'Débord de chevauchement (°) :'
        : 'Débord de chevauchement (°) :',
    '(0.1 = 10 % de la tuile sur les 4 côtés)'
        : '(0.1 = 10 % de la tuile sur les 4 côtés)',
    'Tuile'
        : 'Tuile',
    'emprise'
        : 'emprise',
    'Racine :'
        : 'Racine :',
    'Pays du stock :'
        : 'Pays du stock :',
    '(aucun)'
        : '(aucun)',
    'stock'
        : 'stock',
    'dossier de la tuile'
        : 'dossier de la tuile',
    '{n} source(s) trouvée(s) — origine : {o}'
        : '{n} source(s) trouvée(s) — origine : {o}',
    'Cliquer sur « Assembler » pour lancer.'
        : 'Cliquer sur « Assembler » pour lancer.',
    'Prêt.'
        : 'Prêt.',
    'Terminé.'
        : 'Terminé.',
    'TERMINÉ.'
        : 'TERMINÉ.',
    'Échec.'
        : 'Échec.',
    'ÉCHEC :'
        : 'ÉCHEC :',
    'SUCCÈS'
        : 'SUCCÈS',
    'ÉCHEC'
        : 'ÉCHEC',
    'Recherche des sources…'
        : 'Recherche des sources…',
    'Assemblage en cours… ne fermez pas la fenêtre.'
        : 'Assemblage en cours… ne fermez pas la fenêtre.',
    'Auto-test en cours…'
        : 'Auto-test en cours…',
    'Auto-test terminé.'
        : 'Auto-test terminé.',
    "Auto-test du moteur d'assemblage"
        : "Auto-test du moteur d'assemblage",
    "(aucun de vos fichiers n'est touché)"
        : "(aucun de vos fichiers n'est touché)",
    "Auto-test réussi : le moteur d'assemblage fonctionne."
        : "Auto-test réussi : le moteur d'assemblage fonctionne.",
    'Auto-test en échec — voir le détail dans la fenêtre.'
        : 'Auto-test en échec — voir le détail dans la fenêtre.',
    'Structure non créée.'
        : 'Structure non créée.',
    'Structure créée.'
        : 'Structure créée.',
    'Structure créée :'
        : 'Structure créée :',
    'Création de la structure…'
        : 'Création de la structure…',
    'Structure non configurée.'
        : 'Structure non configurée.',
    "Aucune organisation d'altimétries n'est configurée."
        : "Aucune organisation d'altimétries n'est configurée.",
    'Cliquez sur « Créer / choisir la structure ».'
        : 'Cliquez sur « Créer / choisir la structure ».',
    'Chemin mémorisé introuvable :'
        : 'Chemin mémorisé introuvable :',
    'Si vos altimétries sont sur un disque externe,'
        : 'Si vos altimétries sont sur un disque externe,',
    "vérifiez qu'il est branché."
        : "vérifiez qu'il est branché.",
    'Première utilisation : Ortho4XP va créer votre organisation des altimétries.\n\nChoisissez le disque ou le dossier de stockage (un disque externe convient).'
        : 'Première utilisation : Ortho4XP va créer votre organisation des altimétries.\n\nChoisissez le disque ou le dossier de stockage (un disque externe convient).',
    'Choisir le disque / dossier de stockage des altimétries'
        : 'Choisir le disque / dossier de stockage des altimétries',
    'Nom du pays (ex. : France, Suisse, Allemagne) :'
        : 'Nom du pays (ex. : France, Suisse, Allemagne) :',
    'À FAIRE MAINTENANT :'
        : 'À FAIRE MAINTENANT :',
    'Déposez les données altimétriques du pays dans :'
        : 'Déposez les données altimétriques du pays dans :',
    'Elles doivent être en EPSG:4326 — X-Plane ne lit aucune'
        : 'Elles doivent être en EPSG:4326 — X-Plane ne lit aucune',
    'autre projection. Ortho4XP convertira au besoin, mais'
        : 'autre projection. Ortho4XP convertira au besoin, mais',
    'préparez-les de préférence en 4326.'
        : 'préparez-les de préférence en 4326.',
    'Le résultat assemblé sera écrit dans :'
        : 'Le résultat assemblé sera écrit dans :',
    'Structure créée.\n\nDéposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.'
        : 'Structure créée.\n\nDéposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.',
    'Déposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.'
        : 'Déposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.',
    'Pays ajouté :'
        : 'Pays ajouté :',
    'Aucune source pour cette tuile.'
        : 'Aucune source pour cette tuile.',
    'Aucun fichier altimétrique ne recouvre cette tuile.'
        : 'Aucun fichier altimétrique ne recouvre cette tuile.',
    'Déposez vos données dans le stock du pays, en EPSG:4326.'
        : 'Déposez vos données dans le stock du pays, en EPSG:4326.',
    "rasterio est introuvable dans l'installation d'Ortho4XP."
        : "rasterio est introuvable dans l'installation d'Ortho4XP.",
    '{f} existe déjà. Le remplacer ?'
        : '{f} existe déjà. Le remplacer ?',
    'custom_dem renseigné dans le cfg de la tuile.'
        : 'custom_dem renseigné dans le cfg de la tuile.',
    'custom_dem non écrit :'
        : 'custom_dem non écrit :',
    "Assemblage terminé.\n\n{f}\n\ncustom_dem est renseigné : la tuile est prête pour l'étape mesh."
        : "Assemblage terminé.\n\n{f}\n\ncustom_dem est renseigné : la tuile est prête pour l'étape mesh.",
    "Choisir l'application QGIS"
        : "Choisir l'application QGIS",
    'Application QGIS enregistrée.'
        : 'Application QGIS enregistrée.',
    "Aucune application QGIS définie.\nCliquez d'abord sur « Choisir QGIS »."
        : "Aucune application QGIS définie.\nCliquez d'abord sur « Choisir QGIS ».",
    'QGIS lancé.'
        : 'QGIS lancé.',
    'Applications macOS'
        : 'Applications macOS',
    'Exécutables Windows'
        : 'Exécutables Windows',
    'Tous les fichiers'
        : 'Tous les fichiers',

    'Assemblage en cours… ne fermez pas la fenêtre'
        : 'Assemblage en cours… ne fermez pas la fenêtre',
    'Aucun dossier PATCH pour cette tuile (Step 2.1 non lancé).'
        : 'Aucun dossier PATCH pour cette tuile (Step 2.1 non lancé).',
    'Aucun patch JPG dans :'
        : 'Aucun patch JPG dans :',
    'Aucun fichier altimétrique lisible dans ce dossier.'
        : 'Aucun fichier altimétrique lisible dans ce dossier.',
    'Destination :'
        : 'Destination :',
    'Dossier des données brutes (.asc, .tif…)'
        : 'Dossier des données brutes (.asc, .tif…)',
    "Fichier préparé :\n\n{f}\n\nIl est maintenant dans le stock et sera utilisé automatiquement pour les tuiles qu'il recouvre."
        : "Fichier préparé :\n\n{f}\n\nIl est maintenant dans le stock et sera utilisé automatiquement pour les tuiles qu'il recouvre.",
    'La source est déjà à {a} m. Réduire encore donnerait {b} m et ferait perdre du relief.\n\nContinuer quand même ?'
        : 'La source est déjà à {a} m. Réduire encore donnerait {b} m et ferait perdre du relief.\n\nContinuer quand même ?',
    'Nom du fichier produit :'
        : 'Nom du fichier produit :',
    'Pays de destination ({p}) :'
        : 'Pays de destination ({p}) :',
    'Préparation :'
        : 'Préparation :',
    'Préparation en cours… ne fermez pas la fenêtre'
        : 'Préparation en cours… ne fermez pas la fenêtre',
    'Préparer un pays'
        : 'Préparer un pays',
    'Ratio :'
        : 'Ratio :',
    'Ratio invalide.'
        : 'Ratio invalide.',
    'Résolution source :'
        : 'Résolution source :',
    'Résolution source détectée : {r} m\n\nRatio de réduction en % (25 = diviser par 4) :\n100 = aucune réduction.'
        : 'Résolution source détectée : {r} m\n\nRatio de réduction en % (25 = diviser par 4) :\n100 = aucune réduction.',
    'Préparer (EPSG → réduit)'
        : 'Préparer (EPSG → réduit)',
    'Structure  →  Préparer les données (une fois par pays)  →  Assembler la tuile'
        : 'Structure  →  Préparer les données (une fois par pays)  →  Assembler la tuile',
    'Préparer les données (EPSG → réduit)'
        : 'Préparer les données (EPSG → réduit)',
}