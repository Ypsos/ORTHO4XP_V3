# ============================================================
#  O4_Lang_EN.py  —  ORTHO4XP V2  —  Language file : ENGLISH
#  All interface strings in English.
#  French additions have been translated to English.
#  Generated: 2026-05-05
# ============================================================

LANG = "EN"

T = {

    # ── MAIN WINDOW ────────────────────────────────────────────────
    "🖼 Add Image Provider"                 : "🛰 Add high-resolution imagery",

    "Latitude:"                         : "Latitude:",
    "Longitude:"                        : "Longitude:",
    "Imagery:"                          : "Imagery:",
    "Zoomlevel:"                        : "Zoomlevel:",
    "Zoomlevel : "                      : "Zoomlevel: ",
    "Base Folder:"                      : "Base Folder:",

    # ── MAIN BUILD BUTTONS ─────────────────────────────────────────
    "Assemble Vector data"              : "Assemble Vector data",
    "Triangulate 3D Mesh"               : "Triangulate 3D Mesh",
    " Draw Water Masks  "               : " Draw Water Masks  ",
    " Build Imagery/DSF "               : " Build Imagery/DSF ",
    "    All in one     "               : "    All in one     ",
    "Sea Patches (2.1)"                : "Sea Patches (2.1)",

    # ── MAP / TILE VIEW ────────────────────────────────────────────
    "Active tile"                       : "Active tile",
    "Erase cached data"                 : "Erase cached data",
    "Batch build tiles"                 : "Batch build tiles",
    "  Batch Build   "                  : "  Batch Build   ",
    "  Delete    "                      : "  Delete    ",
    "    Refresh     "                  : "    Refresh     ",
    "      Exit      "                  : "      Exit      ",
    "     Exit     "                    : "     Exit     ",
    "    Exit     "                     : "    Exit     ",
    "Shortcuts :\\n-----------------\\nB2-press+hold=move map\\n"
                                        : "Shortcuts:\\n-----------------\\nB2-press+hold=move map\\n",
    "Carte Earth non disponible\\n"     : "Earth map unavailable\\n",

    # ── ZONE / OVERLAY EDITOR ──────────────────────────────────────
    "Zone params "                      : "Zone params ",
    "Preview params "                   : "Preview params ",
    "Preview"                           : "Preview",
    "Source : "                         : "Source: ",
    "Approx. Add. Size : "              : "Approx. Add. Size: ",
    "  Save zone  "                     : "  Save zone  ",
    "Delete ZL zone"                    : "Delete ZL zone",
    "Make GeoTiffs"                     : "Make GeoTiffs",
    "Extract Mesh "                     : "Extract Mesh ",
    "    Apply    "                     : "    Apply    ",
    "    Apply     "                    : "    Apply     ",
    "    Reset    "                     : "    Reset    ",
    "Ctrl+B1 : add texture\\nShift+B1: add zone point\\n"
                                        : "Ctrl+B1: add texture\\nShift+B1: add zone point\\n",

    # ── CONFIG PANEL ───────────────────────────────────────────────
    "Application "                      : "Application ",
    "Load Tile Cfg "                    : "Load Tile Cfg",
    "Write Tile Cfg"                    : "Write Tile Cfg",
    "Reload App Cfg"                    : "Reload App Cfg",
    "Write App Cfg "                    : "Write App Cfg",
    "Ok"                                : "Ok",
    "Enable"                            : "Enable",
    "Strength:"                         : "Strength:",

    # ── COLOR NORMALIZE PANEL ──────────────────────────────────────
    "Color Normalize"                   : "Color Normalize",
    "RGB adjustments, sharpness, saturation"
                                        : "RGB adjustments, sharpness, saturation",
    "Réf: "                             : "Ref: ",

    # ── TIMELINE / BENCHMARK (Phase 3) ────────────────────────────
    "⏱ Timeline"                        : "⏱ Timeline",
    "🎯 Scoring build : ON" : "🎯 Scoring build: ON",
    "🎯 Scoring build : OFF" : "🎯 Scoring build: OFF",
    "scoring_build_tooltip" : "ON: provider scoring runs during the build (slower). OFF: faster build, no scoring.",
    "⏱ Timeline — Durées du build"      : "⏱ Timeline — Build durations",
    "Timeline non disponible."          : "Timeline not available.",
    "Fermer"                            : "Close",
    "Step 1 — Vectors"                  : "Step 1 — Vectors",
    "Step 2 — Mesh"                     : "Step 2 — Mesh",
    "Step 2.5 — Masks"                  : "Step 2.5 — Masks",
    "Step 2.1 — Sea Patches"            : "Step 2.1 — Sea Patches",
    "Step 3 — DSF/Imagery"              : "Step 3 — DSF/Imagery",
    "Build All"                         : "Build All",

    # ── SIMULATOR ─────────────────────────────────────────────────
    "🎚 Visualisation réglages"         : "🎚 Settings Preview",
    "Survolez un curseur."              : "Hover over a slider.",
    "↺  Recharger depuis cfg"           : "↺  Reload from cfg",
    "✅  Write Tile cfg"                : "✅  Write Tile cfg",
    "🌍  Write App cfg"                 : "🌍  Write App cfg",
    "✖  Fermer"                         : "✖  Close",

    # Simulator tab names
    "💧 Mer & Eau"                      : "💧 Sea & Water",
    "🌊 Côte & Masques"                 : "🌊 Coast & Masks",
    "⛰ Terrain & Relief"               : "⛰ Terrain & Elevation",
    "🗺 Mesh 3D"                        : "🗺 3D Mesh",
    "📷 Imagerie & Aéroports"           : "📷 Imagery & Airports",

    # Simulator group names
    "Eau & Transparence"                : "Water & Transparency",
    "Masques côtiers"                   : "Coastal Masks",
    "Courbure côte"                     : "Coastline Curvature",
    "Altimétrie & Vecteurs"             : "Altimetry & Vectors",
    "Terrain & Ombrage"                 : "Terrain & Shading",
    "Paramètres Mesh"                   : "Mesh Parameters",
    "Qualité & Nettoyage"               : "Quality & Cleanup",
    "Imagerie"                          : "Imagery",
    "Aéroports"                         : "Airports",
    "Routes"                            : "Roads",

    # ── COLOR CHECK ────────────────────────────────────────────────
    "Corrections R.G.B., Netteté, saturation, Zone de fusion"
                                        : "R.G.B. Corrections, Sharpness, Saturation, Blend Zone",
    "Couches ZL / Tuiles (toutes)"      : "ZL Layers / Tiles (all)",
    "① Couches / Corrections"           : "① Layers / Corrections",
    "② Dégradé de jointure sources"     : "② Source Seam Gradient",
    "Couleur Cible — extends / ZL"      : "Target Color — extents / ZL",
    "Correction sRGB par canal + Saturation"
                                        : "Per-channel sRGB Correction + Saturation",
    "Netteté"                           : "Sharpness",
    "Rayon dégradé :"                   : "Gradient radius:",
    "Dégradé : OFF"                     : "Gradient: OFF",
    "Dégradé de jointure : désactivé (jointure nette)"
                                        : "Seam gradient: disabled (sharp seam)",
    "Jointure colorimétrique — déplacez le curseur"
                                        : "Colour seam — move the slider",
    "  Rayons effectifs : dégradé OFF"  : "  Effective radii: gradient OFF",
    "(damier progressif — toute la tuile)"
                                        : "(progressive checker — whole tile)",
    "Source A : —"                      : "Source A: —",
    "Source B : —"                      : "Source B: —",
    "Gauche = original  |  Droite = corrigé  — clic pour agrandir"
                                        : "Left = original  |  Right = corrected  — click to enlarge",
    "ORIGINAL"                          : "ORIGINAL",
    "CORRIGÉ"                           : "CORRECTED",

    # Color Check buttons
    "🔍 Scanner couches"                : "🔍 Scan layers",
    "📋 Exporter liste"                 : "📋 Export list",
    "🎨 Appliquer au groupe"            : "🎨 Apply to group",
    "💾 Générer .comb"                  : "💾 Generate .comb",
    "🛡 Création Zones à protéger"      : "🛡 Create protected zones",
    "👁 Batch Preview couche"           : "👁 Batch Preview layer",
    "🗑 Supprimer DDS sélect."          : "🗑 Delete selected DDS",
    "🎯 Auto-détecter"                  : "🎯 Auto-detect",
    "↺ Reset curseurs"                  : "↺ Reset sliders",
    "🔬 Auto depuis Cible"              : "🔬 Auto from Target",
    "🔨 Build avec dégradé (toute la tuile)"
                                        : "🔨 Build with gradient (whole tile)",
    "🔨 Lancer Build (groupe)"          : "🔨 Launch Build (group)",
    "👁 Preview dégradé (avant Build)"  : "👁 Gradient preview (before Build)",
    "🛡 Générer .comb seam (zone protégée)"
                                        : "🛡 Generate .comb seam (protected zone)",
    "💾 Archiver"                       : "💾 Archive",
    "📂 Restaurer"                      : "📂 Restore",
    "↺ Reset zoom"                      : "↺ Reset zoom",
    "↺ Vue entière"                     : "↺ Full view",
    "✅ Appliquer ce rayon et fermer"   : "✅ Apply this radius and close",
    "✅ Restaurer"                      : "✅ Restore",
    "✅ Valider et générer .comb"       : "✅ Validate and generate .comb",
    "✏ Renommer sélect."               : "✏ Rename selected",
    "✖ Fermer sans appliquer"          : "✖ Close without applying",
    "Archive corrections (Color_check/)" : "Archive corrections (Color_check/)",

    # Color Check warning messages
    "⚠ Aucun DDS disponible pour le preview."
                                        : "⚠ No DDS available for preview.",
    "⚠ Aucun DDS disponible."          : "⚠ No DDS available.",
    "⚠ Aucun DDS scanné."              : "⚠ No DDS scanned.",
    "⚠ Aucun DDS sélectionné pour générer le .comb seam."
                                        : "⚠ No DDS selected to generate .comb seam.",
    "⚠ Aucun fichier dans ce groupe."  : "⚠ No file in this group.",
    "⚠ Aucune archive dans Color_check/ — archivez d'abord des corrections."
                                        : "⚠ No archive in Color_check/ — archive corrections first.",
    "⚠ Aucune correction à archiver — appliquez d'abord des corrections."
                                        : "⚠ No correction to archive — apply corrections first.",
    "⚠ Dossier Color_check/ introuvable — aucune archive disponible."
                                        : "⚠ Color_check/ folder not found — no archive available.",
    "⚠ Sélectionnez d'abord un DDS."  : "⚠ Select a DDS first.",
    "⚠ Sélectionnez d'abord une couche ZL dans la liste."
                                        : "⚠ Select a ZL layer from the list first.",
    "⚠ Sélectionnez d'abord une couche ZL ou un fichier."
                                        : "⚠ Select a ZL layer or a file first.",
    "⚠ Sélectionnez d'abord une couche ZL."
                                        : "⚠ Select a ZL layer first.",
    "⚠ Sélectionnez un DDS individuel.": "⚠ Select an individual DDS.",
    "⚠ Sélectionnez un DDS à gauche ET une cible à droite."
                                        : "⚠ Select a DDS on the left AND a target on the right.",
    "⚠ Tous les curseurs sont à 0 — ajustez au moins un curseur."
                                        : "⚠ All sliders are at 0 — adjust at least one slider.",

    # Color Check status messages
    "En attente…"                       : "Waiting…",
    "Scan en cours…"                    : "Scanning…",
    "Analyse…"                          : "Analysing…",
    "Chargement…"                       : "Loading…",
    "Chargement image…"                 : "Loading image…",
    "Détection jointure…"               : "Seam detection…",

    # Color Check dialogs
    "Choisir une archive à restaurer :" : "Choose an archive to restore:",
    "Dessinez des rectangles sur les zones à protéger (pistes, marquages)"
                                        : "Draw rectangles over areas to protect (runways, markings)",
    "Dessinez des rectangles sur les zones à protéger."
                                        : "Draw rectangles over areas to protect.",
    "Clic+glisser = nouveau rectangle  |  Clic sur zone = sélectionner  |  Suppr = effacer"
                                        : "Click+drag = new rectangle  |  Click zone = select  |  Del = erase",
    "Zones protégées"                   : "Protected zones",
    "Étiquette :"                       : "Label:",
    "🗑 Supprimer sélect."              : "🗑 Delete selected",
    "🗑 Tout effacer"                   : "🗑 Clear all",
    "Annuler"                           : "Cancel",
    "💡 Seam persistante : augmentez le rayon\\n"
                                        : "💡 Persistent seam: increase the radius\\n",

    # ── STATUS / CONFIG MESSAGES ───────────────────────────────────
    "✓ Valeurs chargées depuis le cfg." : "✓ Values loaded from cfg.",
    "✅ Sauvegardé dans cfg tuile."     : "✅ Saved to tile cfg.",
    "✅ Sauvegardé dans cfg global."    : "✅ Saved to global cfg.",

    # ── CONSOLE / LOG MESSAGES ─────────────────────────────────────
    "-> Opening download queue."        : "-> Opening download queue.",
    "Download process interrupted."     : "Download process interrupted.",
    " *Download of textures completed." : " *Download of textures completed.",
    " *DDS conversion of textures completed."
                                        : " *DDS conversion of textures completed.",
    " *Activating DSF file."            : " *Activating DSF file.",
    "DDS conversion process interrupted."
                                        : "DDS conversion process interrupted.",
    "DSF construction interrupted."    : "DSF construction interrupted.",
    "ERROR : could not rename DSF file, tile is not actived."
                                        : "ERROR: could not rename DSF file, tile not activated.",
    "ERROR: Cannot create tile subdirectories."
                                        : "ERROR: Cannot create tile subdirectories.",
    "-> Checking airport locations for upgraded zoomlevel."
                                        : "-> Checking airport locations for upgraded zoomlevel.",
    "-> Initializing providers with potential data on this tile."
                                        : "-> Initializing providers with potential data on this tile.",
    "-> Reading mesh data"              : "-> Reading mesh data",
    "-> Reading mesh file"              : "-> Reading mesh file",
    "-> Encoding of the DSF file"       : "-> Encoding of the DSF file",
    "-> Construction of the masks"      : "-> Construction of the masks",
    "-> Deleting existing masks"        : "-> Deleting existing masks",
    "-> Computing point pools and texture requirements"
                                        : "-> Computing point pools and texture requirements",
    "-> Adapting water triangles to XP12 requirements"
                                        : "-> Adapting water triangles to XP12 requirements",
    "-> Computing bathymetry depth ratio bounds based on distance masks"
                                        : "-> Computing bathymetry depth ratio bounds based on distance masks",
    "App config loaded from:"           : "App config loaded from:",
    "App config written to:"            : "App config written to:",
    "Tile config loaded from:"          : "Tile config loaded from:",
    "Tile config written to:"           : "Tile config written to:",
    "Server could not be connected, retrying in 2 secs"
                                        : "Server could not be connected, retrying in 2 secs",
    "Server said 'Forbidden' ! (IP banned?)"
                                        : "Server said 'Forbidden'! (IP banned?)",
    "Server said 'Internal Error'."     : "Server said 'Internal Error'.",
    "Server said 'Not Found'"           : "Server said 'Not Found'",
    "Blur of a mask !"                  : "Blur of a mask!",
    "Blur of the mask..."               : "Blurring the mask...",
    "Buffer of the mask..."             : "Buffering the mask...",
    "Cannot write into"                 : "Cannot write into",
    "Crop needed"                       : "Crop needed",
    "Warp needed"                       : "Warp needed",
    "Could not test coverage of "       : "Could not test coverage of ",
    "Could not write global config:"    : "Could not write global config:",
    "Error while writing tile cfg:"     : "Error while writing tile cfg:",
    "Finished imprinting"               : "Finished imprinting",
    "Imprinting for provider"            : "Imprinting for provider",
    "Global config file contains an invalid line:"
                                        : "Global config file contains an invalid line:",
    "Preview non générée :"             : "Preview not generated:",
    "   WARNING: 7z decompression failed, bathymetry skipped."
                                        : "   WARNING: 7z decompression failed, bathymetry skipped.",
    "   WARNING: Corrupted Global Scenery DSF, bathymetry skipped."
                                        : "   WARNING: Corrupted Global Scenery DSF, bathymetry skipped.",
    "   WARNING: Global Scenery DSF absent, bathymetry skipped."
                                        : "   WARNING: Global Scenery DSF absent, bathymetry skipped.",
    "   WARNING: could not copy Global Scenery DSF, bathymetry skipped."
                                        : "   WARNING: could not copy Global Scenery DSF, bathymetry skipped.",

    # ── LANGUAGE SELECTION DIALOG ──────────────────────────────────
    "language_dialog_title"             : "Language / Langue",
    "language_dialog_message"           : "Choose your language:",
    "language_btn_en"                   : "🇬🇧  English",
    "language_btn_fr"                   : "🇫🇷  Français",
    "language_menu_tools"               : "Tools",
    "language_menu_change_lang"         : "Change language…",

    # ── FENÊTRE CUSTOM ZOOMLEVELS / PREVIEW ───────────────────────
    "Preview / Custom zoomlevels"       : "Preview / Custom zoomlevels",
    "Tiles collection and management"   : "Tiles collection and management",
    "Ctrl+B1 : add texture\\nShift+B1: add zone point\\n"
                                        : "Ctrl+B1: add texture\\nShift+B1: add zone point\\n",

    # ── CONFIG WINDOW SECTION TITLES ──────────────────────────────
    "Vector data"                       : "Vector data",
    "Mesh"                              : "Mesh",
    "Masks"                             : "Masks",
    "DSF/Imagery"                       : "DSF/Imagery",

    # ── TILE COLLECTION CHECKBOXES ─────────────────────────────────
    "OSM data"                          : "OSM data",
    "Mask data"                         : "Mask data",
    "Jpeg imagery"                      : "Jpeg imagery",
    "Tile (whole)"                      : "Tile (whole)",
    "Tile (textures)"                   : "Tile (textures)",
    "Assemble vector data"              : "Assemble vector data",
    "Triangulate 3D mesh"               : "Triangulate 3D mesh",
    "Draw water masks"                  : "Draw water masks",
    "Build imagery/DSF"                 : "Build imagery/DSF",
    "Extract overlays"                  : "Extract overlays",
    "Read per tile cfg"                 : "Read per tile cfg",
    "Shortcuts :"                       : "Shortcuts:",
    "B2-press+hold=move map"            : "B2-press+hold=move map",

    # ── LAUNCHER WINDOW ────────────────────────────────────────────
    "1. Installer les Modules"              : "1. Install Modules",
    "🔍 Vérifier Intégrité"                : "🔍 Check Integrity",
    "📜 Crédits & Licence"                 : "📜 Credits & License",
    "📖 Historique"                        : "📖 History",
    "Fichier introuvable :"                : "File not found:",
    "Fichier de crédits introuvable :"     : "Credits file not found:",
    "▶️ LANCER ORTHO4XP"                   : "▶️ LAUNCH ORTHO4XP",
    "Installer les Modules — Choisir la plateforme"
                                            : "Install Modules — Choose platform",
    "Installer les Modules"                 : "Install Modules",
    "Tout s'installe dans venv/ — rien dans le système"
                                            : "Everything installs in venv/ — nothing system-wide",
    "Créer le lanceur Ortho4XP (double-clic quotidien)"
                                            : "Create Ortho4XP launcher (daily double-click)",

    # ── LABELS TECHNIQUES GUI (DDS format, référence couleur) ──────
    "Réf: Calibré_48753_JPG_Europe"     : "Ref: Calibré_48753_JPG_Europe",
    "BC1 — TERRE"                       : "BC1 — LAND",
    "BC1 — MER"                         : "BC1 — SEA",
    "BC3 — MER"                         : "BC3 — SEA",

    # ── IMAGERY/ZONE CORRECTION — button & window ─────────────────
    "Visualiser la tuile"                    : "View tile",
    "Visualiser la tuile — Ortho4XP V3"      : "View tile — Ortho4XP V3",
    "Mosaïque des DDS de la tuile — à venir" : "Tile DDS mosaic — coming soon",
    "Dossier textures introuvable pour cette tuile." : "Textures folder not found for this tile.",
    "Aucun DDS dans le dossier textures de la tuile." : "No DDS found in the tile's textures folder.",
    "Préparation des vignettes…"             : "Preparing thumbnails…",
    "Supprimer patches sélectionnés"         : "Delete selected patches",
    "Précédent"                              : "Previous",
    "QGIS"                                   : "QGIS",
    "Suppression dossier Preview"            : "Delete Preview folder",
    "Aucun dossier Preview à supprimer."     : "No Preview folder to delete.",
    "Supprimer le dossier Preview ({n} fichiers) ?": "Delete the Preview folder ({n} files)?",
    "Dossier Preview supprimé ({n} fichiers).": "Preview folder deleted ({n} files).",
    "Effacer JPG source et relancer étape 3" : "Delete source JPG and re-run step 3",
    "Aucune vignette cochée."                : "No thumbnail selected.",
    "Supprimer {n} JPG source puis relancer l'étape 3 ?": "Delete {n} source JPG then re-run step 3?",
    "{n} JPG source supprimé(s). Étape 3 relancée." : "{n} source JPG deleted. Step 3 restarted.",
    "Relancez l'étape 3 dans la fenêtre principale." : "Please re-run step 3 in the main window.",
    "Suivant"                                : "Next",
    "Détail de la tuile"                     : "Tile detail",
    "À corriger (copier le JPG source)"      : "To correct (copy source JPG)",
    "JPG source copié dans les patches"      : "Source JPG copied to patches",
    "Un patch existe déjà pour cette tuile"  : "A patch already exists for this tile",
    "Aucun JPG source trouvé pour cette tuile": "No source JPG found for this tile",
    "Correction (choisir application)"       : "Correction (choose application)",
    "Ouvrir dans l'éditeur"                  : "Open in editor",
    "GIMP"                                   : "GIMP",
    "JOSM"                                   : "JOSM",
    "à venir"                                : "coming soon",
    "🖊 Correction imagerie/zone"           : "🖊 Imagery/zone correction",
    "Correction imagerie et traitement de zone"
                                            : "Imagery correction and zone processing",

    # ── JPG-PATCH MANAGEMENT — window texts ───────────────────────
    "Gestion JPG-Patch — Ortho4XP V3"       : "JPG-Patch Manager — Ortho4XP V3",
    "Gestion des JPG-Patch existants"        : "Existing JPG-Patches",
    "patch(es) trouvé(s) dans"              : "patch(es) found in",
    "Sélection patches à conserver — Ortho4XP V3" : "Select patches to keep — Ortho4XP V3",
    "Cocher les patches à CONSERVER"         : "Check the patches to KEEP",
    "(Les patches non cochés seront supprimés)" : "(Unchecked patches will be deleted)",
    "Tout cocher"   : "Check all",
    "Tout décocher" : "Uncheck all",
    "← Cliquer sur un patch"                : "← Click on a patch",

    # ── JPG-PATCH MANAGEMENT — dialog window ──────────────────────
    "🗑  Tout supprimer"                 : "🗑  Delete all",
    "✅  Tout conserver"                 : "✅  Keep all",
    "🔍  Sélection patches"             : "🔍  Select patches",

    # ── PROVIDERS PERSONNELS ───────────────────────────────────────
    "Personnel"                             : "Custom",
    "personal_provider_window_title"        : "Custom Providers — Ortho4XP V3",
    "personal_provider_list_label"          : "My providers:",
    "personal_provider_name_label"          : "Provider name (code):",
    "personal_provider_url_label"           : "jpg URL (TMS):",
    "personal_provider_url_hint"            : "e.g. https://server.com/{zoom}/{x}/{y}.jpg",
    "personal_provider_save_btn"            : "💾  Save",
    "personal_provider_cancel_btn"          : "✖  Cancel",
    "personal_provider_modify_btn"          : "✏  Modify",
    "personal_provider_delete_btn"          : "🗑  Delete",
    "personal_provider_saved_ok"            : "Provider saved. Select it in the Imagery list.",
    "personal_provider_deleted_ok"          : "Provider deleted.",
    "personal_provider_err_name"            : "Provider name cannot be empty.",
    "personal_provider_err_url"             : "URL cannot be empty.",
    "personal_provider_err_name_invalid"    : "Name must be alphanumeric (no spaces).",
    "personal_provider_err_reserved"        : "This name is reserved. Please choose another.",
    "personal_provider_select_hint"         : "← Select a provider to modify/delete",

    # ── COLOR CHECK — boutons et labels dynamiques ─────────────────
    "🗑 Supprimer TOUS DDS ZL"          : "🗑 Delete ALL ZL DDS",
    "Gradient: {radius} px — next Build"     : "Gradient: {radius} px — next Build",
    "Checker gradient: {radius} px — applies to all DDS at next Build"
                                        : "Checker gradient: {radius} px — applies to all DDS at next Build",
    "  Effective radii (base {base}px):" : "  Effective radii (base {base}px):",
    "💡 Persistent seam: increase radius\n   or generate a .comb mask on the area."
                                        : "💡 Persistent seam: increase radius\n   or generate a .comb mask on the area.",
    '🔨 Construire cette image'
                                        : '🔨 Build this image',
    "Reconstruit UNIQUEMENT l'image sélectionnée (pas tout le groupe) avec la correction des curseurs. Idéal pour peaufiner une seule image à la main."
                                        : 'Rebuilds ONLY the selected image (not the whole group) with the slider correction. Ideal to fine-tune a single image by hand.',
    '✅ Build lancé — image seule : {name}'
                                        : '✅ Build launched — single image: {name}',
    "⚠ Sélectionnez d'abord une image dans la liste."
                                        : '⚠ Select an image in the list first.',
    "⚠ too low"                         : "⚠ too low",
    "⚠ detail risk"                     : "⚠ detail risk",

    # Drift grouping + status (left column)
    "Dérive"                            : "Drift",
    "Dérive faible"                     : "Weak drift",
    "{total} DDS — {n_corr} à corriger ({n_grp} groupes) — {n_ok} conformes (±{tol})"
                                        : "{total} DDS — {n_corr} to correct ({n_grp} groups) — {n_ok} conforming (±{tol})",
    "{title} — {n} DDS — « Correction en série » corrige tout ce chapitre"
                                        : "{title} — {n} DDS — « Batch correction » corrects this whole chapter",
    "Auto-détecter : corr R{r:+d} G{g:+d} B{b:+d} | Cont {cr:+d}/{cg:+d}/{cb:+d} | Sat {sr:+d}/{sg:+d}/{sb:+d}"
                                        : "Auto-detect: corr R{r:+d} G{g:+d} B{b:+d} | Cont {cr:+d}/{cg:+d}/{cb:+d} | Sat {sr:+d}/{sg:+d}/{sb:+d}",
    "Auto depuis cible : corr R{r:+d} G{g:+d} B{b:+d} | Cont {cr:+d}/{cg:+d}/{cb:+d} | Sat {sr:+d}/{sg:+d}/{sb:+d}"
                                        : "Auto from target: corr R{r:+d} G{g:+d} B{b:+d} | Cont {cr:+d}/{cg:+d}/{cb:+d} | Sat {sr:+d}/{sg:+d}/{sb:+d}",
    "🎨 Correction en série"            : "🎨 Batch correction",
    "Enregistre la correction du groupe SANS lancer le build.\nCorrigez un groupe → Correction en série → recommencez pour d'autres groupes → puis « Lancer construction » UNE seule fois pour tout construire (économise des builds)."
                                        : "Saves the group's correction WITHOUT building.\nCorrect a group → Batch correction → repeat for other groups → then « Launch build » ONCE to build everything (saves builds).",
    "Supprime les DDS du groupe, enregistre la correction, puis lance la construction (utilise votre quota). Traite d'un coup toutes les corrections enregistrées en série."
                                        : "Deletes the group's DDS, saves the correction, then builds (uses your quota). Processes all batch-saved corrections at once.",
    "  → recommencez pour d'autres groupes, puis « Lancer construction »"
                                        : "  → repeat for other groups, then « Launch build »",
    "🔨 Build en cours… {done}/{total} DDS régénérés — rescan automatique à la fin."
                                        : "🔨 Building… {done}/{total} DDS regenerated — auto-rescan when done.",


    # ── LOGS CONSOLE — O4_Sea_Texture.py ──────────────────────────
    "   [SeaTex] JPG-Patch généré : {jpg_name}"
                                        : "   [SeaTex] JPG-Patch generated: {jpg_name}",
    "   [SeaTex] Construction arêtes mesh..."
                                        : "   [SeaTex] Building mesh edges...",
    "   [SeaTex] {n} triangle(s) mer côtier(s) détecté(s)."
                                        : "   [SeaTex] {n} coastal sea triangle(s) detected.",

    # ── LOGS CONSOLE — O4_Mask_Utils.py ───────────────────────────
    "ERROR: masks_width = {mw} m est invalide (trop grand). Maximum autorisé pour cette tuile et ce mask_zl : {maxw} m. Diminuez masks_width dans la config de la tuile et relancez l'étape masks (2.5)."
                                        : "ERROR: masks_width = {mw} m is invalid (too large). Maximum allowed for this tile and mask_zl is {maxw} m. Please lower masks_width in the tile config and relaunch the masks step (2.5).",

    # ── LOGS CONSOLE — O4_Imagery_Utils.py ───────────────────────
    "   [SeaTex] Provider PATCH injecté."
                                        : "   [SeaTex] PATCH provider injected.",
    "   [SeaTex] PATCH injecté pour provider simple : {pc}"
                                        : "   [SeaTex] PATCH injected for simple provider: {pc}",
    "   [SeaTex] JPG absent — fond mer utilisé : {name}"
                                        : "   [SeaTex] JPG missing — sea background used: {name}",
    "   [SeaTex] paste masqué échoué, paste direct : {e}"
                                        : "   [SeaTex] masked paste failed, direct paste: {e}",
    "   [SeaTex] PATCH absent pour cette position — ignoré"
                                        : "   [SeaTex] PATCH missing for this position — skipped",
    "   [SeaTex] PATCH appliqué comme fond (aucun JPG provider)"
                                        : "   [SeaTex] PATCH applied as background (no provider JPG)",
    "   [SeaTex] PATCH appliqué : {n} px nodata comblés"
                                        : "   [SeaTex] PATCH applied: {n} nodata px filled",
    "   [SeaTex] PATCH : aucun nodata blanc détecté — ignoré"
                                        : "   [SeaTex] PATCH: no white nodata detected — skipped",

    # ── LOGS CONSOLE — O4_Tile_Utils.py ──────────────────────────
    "   [SeaTex] ERREUR : initialisation providers échouée."
                                        : "   [SeaTex] ERROR: provider initialisation failed.",
    "   [SeaTex] Aucune tuile mer côtière détectée — rien à générer."
                                        : "   [SeaTex] No coastal sea tile detected — nothing to generate.",
    "   [SeaTex] Cas 1 terminé — {n} patch(es) nodata corrigés."
                                        : "   [SeaTex] Case 1 done — {n} nodata patch(es) corrected.",
    "   [SeaTex] Step 2.1 terminé."     : "   [SeaTex] Step 2.1 done.",
    "   [SeaTex] Passage 2 terminé — {n} DDS générés."
                                        : "   [SeaTex] Pass 2 done — {n} DDS generated.",
    "   [Batch] DSF .tmp corrompu supprimé : {name}"
                                        : "   [Batch] Corrupted DSF .tmp deleted: {name}",
    "   [Batch] Tuile {tile} ignorée (erreur OSM) — batch continue."
                                        : "   [Batch] Tile {tile} skipped (OSM error) — batch continues.",
    "   [Batch] Tuile {tile} ignorée (erreur mesh) — batch continue."
                                        : "   [Batch] Tile {tile} skipped (mesh error) — batch continues.",
    "   [Batch] Tuile {tile} ignorée (erreur masque) — batch continue."
                                        : "   [Batch] Tile {tile} skipped (mask error) — batch continues.",
    "   [Batch] Tuile {tile} ignorée (erreur DSF/imagery) — batch continue."
                                        : "   [Batch] Tile {tile} skipped (DSF/imagery error) — batch continues.",
    "   [Batch] Tuile {tile} ignorée (erreur overlay) — batch continue."
                                        : "   [Batch] Tile {tile} skipped (overlay error) — batch continues.",
    "Batch terminé avec {n} tuile(s) ignorée(s) :"
                                        : "Batch done — {n} tile(s) skipped:",



    # ── ALTIMÉTRIE / DEM ───────────────────────────────────────────
    '⛰ Altimétrie / DEM / QGIS'
        : '⛰ Elevation / DEM / QGIS',
    'Altimétrie / DEM / QGIS'
        : 'Elevation / DEM / QGIS',
    'Altimétrie / DEM / QGIS — Ortho4XP V3'
        : 'Elevation / DEM / QGIS — Ortho4XP V3',
    'Le module O4_Altimetrie_Utils.py est introuvable dans le dossier src/.'
        : 'Module O4_Altimetrie_Utils.py not found in the src/ folder.',
    'Latitude / longitude invalides.'
        : 'Invalid latitude / longitude.',
    'Créer / choisir la structure'
        : 'Create / choose folder structure',
    'Ajouter un pays'
        : 'Add a country',
    'Rafraîchir'
        : 'Refresh',
    'Assembler'
        : 'Assemble',
    'Vérifier (auto-test)'
        : 'Check (self-test)',
    'Choisir QGIS'
        : 'Choose QGIS',
    'Ouvrir dans QGIS'
        : 'Open in QGIS',
    'Fermer'
        : 'Close',
    'QGIS :'
        : 'QGIS:',
    'Débord de chevauchement (°) :'
        : 'Overlap margin (°):',
    '(0.1 = 10 % de la tuile sur les 4 côtés)'
        : '(0.1 = 10% of the tile on all 4 sides)',
    'Tuile'
        : 'Tile',
    'emprise'
        : 'extent',
    'Racine :'
        : 'Root:',
    'Pays du stock :'
        : 'Countries in store:',
    '(aucun)'
        : '(none)',
    'stock'
        : 'store',
    'dossier de la tuile'
        : 'tile folder',
    '{n} source(s) trouvée(s) — origine : {o}'
        : '{n} source(s) found — from: {o}',
    'Cliquer sur « Assembler » pour lancer.'
        : 'Click the Assemble button to start.',
    'Prêt.'
        : 'Ready.',
    'Terminé.'
        : 'Done.',
    'TERMINÉ.'
        : 'DONE.',
    'Échec.'
        : 'Failed.',
    'ÉCHEC :'
        : 'FAILED:',
    'SUCCÈS'
        : 'SUCCESS',
    'ÉCHEC'
        : 'FAILED',
    'Recherche des sources…'
        : 'Looking for sources…',
    'Assemblage en cours… ne fermez pas la fenêtre.'
        : 'Assembling… please do not close this window.',
    'Auto-test en cours…'
        : 'Self-test running…',
    'Auto-test terminé.'
        : 'Self-test finished.',
    "Auto-test du moteur d'assemblage"
        : 'Self-test of the assembly engine',
    "(aucun de vos fichiers n'est touché)"
        : '(none of your files are touched)',
    "Auto-test réussi : le moteur d'assemblage fonctionne."
        : 'Self-test passed: the assembly engine works.',
    'Auto-test en échec — voir le détail dans la fenêtre.'
        : 'Self-test failed — see details in the window.',
    'Structure non créée.'
        : 'Folder structure not created.',
    'Structure créée.'
        : 'Folder structure created.',
    'Structure créée :'
        : 'Folder structure created:',
    'Création de la structure…'
        : 'Creating folder structure…',
    'Structure non configurée.'
        : 'Folder structure not configured.',
    "Aucune organisation d'altimétries n'est configurée."
        : 'No elevation folder structure is configured.',
    'Cliquez sur « Créer / choisir la structure ».'
        : 'Click the Create / choose folder structure button.',
    'Chemin mémorisé introuvable :'
        : 'Saved path not found:',
    'Si vos altimétries sont sur un disque externe,'
        : 'If your elevation data is on an external drive,',
    "vérifiez qu'il est branché."
        : 'please check that it is plugged in.',
    'Première utilisation : Ortho4XP va créer votre organisation des altimétries.\n\nChoisissez le disque ou le dossier de stockage (un disque externe convient).'
        : 'First use: Ortho4XP will create your elevation folder structure.\n\nChoose the drive or folder where it will be stored (an external drive is fine).',
    'Choisir le disque / dossier de stockage des altimétries'
        : 'Choose the drive / folder for elevation storage',
    'Nom du pays (ex. : France, Suisse, Allemagne) :'
        : 'Country name (e.g. France, Switzerland, Germany):',
    'À FAIRE MAINTENANT :'
        : 'WHAT TO DO NOW:',
    'Déposez les données altimétriques du pays dans :'
        : "Put the country's elevation data into:",
    'Elles doivent être en EPSG:4326 — X-Plane ne lit aucune'
        : 'It must be in EPSG:4326 — X-Plane cannot read any',
    'autre projection. Ortho4XP convertira au besoin, mais'
        : 'other projection. Ortho4XP will convert if needed, but',
    'préparez-les de préférence en 4326.'
        : 'prepare your files in 4326 whenever possible.',
    'Le résultat assemblé sera écrit dans :'
        : 'The assembled result will be written to:',
    'Structure créée.\n\nDéposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.'
        : 'Folder structure created.\n\nPut your elevation data into:\n{d}\n\nRequired format: EPSG:4326.',
    'Déposez vos altimétries dans :\n{d}\n\nFormat requis : EPSG:4326.'
        : 'Put your elevation data into:\n{d}\n\nRequired format: EPSG:4326.',
    'Pays ajouté :'
        : 'Country added:',
    'Aucune source pour cette tuile.'
        : 'No source for this tile.',
    'Aucun fichier altimétrique ne recouvre cette tuile.'
        : 'No elevation file covers this tile.',
    'Déposez vos données dans le stock du pays, en EPSG:4326.'
        : 'Put your data into the country store, in EPSG:4326.',
    "rasterio est introuvable dans l'installation d'Ortho4XP."
        : 'rasterio was not found in the Ortho4XP installation.',
    '{f} existe déjà. Le remplacer ?'
        : '{f} already exists. Replace it?',
    'custom_dem renseigné dans le cfg de la tuile.'
        : 'custom_dem set in the tile cfg.',
    'custom_dem non écrit :'
        : 'custom_dem not written:',
    "Assemblage terminé.\n\n{f}\n\ncustom_dem est renseigné : la tuile est prête pour l'étape mesh."
        : 'Assembly finished.\n\n{f}\n\ncustom_dem is set: the tile is ready for the mesh step.',
    "Choisir l'application QGIS"
        : 'Choose the QGIS application',
    'Application QGIS enregistrée.'
        : 'QGIS application saved.',
    "Aucune application QGIS définie.\nCliquez d'abord sur « Choisir QGIS »."
        : 'No QGIS application set.\nUse the Choose QGIS button first.',
    'QGIS lancé.'
        : 'QGIS launched.',
    'Applications macOS'
        : 'macOS applications',
    'Exécutables Windows'
        : 'Windows executables',
    'Tous les fichiers'
        : 'All files',

    'Assemblage en cours… ne fermez pas la fenêtre'
        : 'Assembling… please do not close this window',
    'Aucun dossier PATCH pour cette tuile (Step 2.1 non lancé).'
        : 'No PATCH folder for this tile (Step 2.1 not run).',
    'Aucun patch JPG dans :'
        : 'No JPG patch in:',
    'Aucun fichier altimétrique lisible dans ce dossier.'
        : 'No readable elevation file in this folder.',
    'Destination :'
        : 'Destination:',
    'Dossier des données brutes (.asc, .tif…)'
        : 'Folder with the raw data (.asc, .tif…)',
    "Fichier préparé :\n\n{f}\n\nIl est maintenant dans le stock et sera utilisé automatiquement pour les tuiles qu'il recouvre."
        : 'File prepared:\n\n{f}\n\nIt is now in the store and will be used automatically for the tiles it covers.',
    'La source est déjà à {a} m. Réduire encore donnerait {b} m et ferait perdre du relief.\n\nContinuer quand même ?'
        : 'The source is already at {a} m. Reducing further would give {b} m and lose terrain detail.\n\nContinue anyway?',
    'Nom du fichier produit :'
        : 'Name of the produced file:',
    'Pays de destination ({p}) :'
        : 'Destination country ({p}):',
    'Préparation :'
        : 'Preparing:',
    'Préparation en cours… ne fermez pas la fenêtre'
        : 'Preparing… please do not close this window',
    'Préparer un pays'
        : 'Prepare a country',
    'Ratio :'
        : 'Ratio:',
    'Ratio invalide.'
        : 'Invalid ratio.',
    'Résolution source :'
        : 'Source resolution:',
    'Résolution source détectée : {r} m\n\nRatio de réduction en % (25 = diviser par 4) :\n100 = aucune réduction.'
        : 'Detected source resolution: {r} m\n\nReduction ratio in % (25 = divide by 4):\n100 = no reduction.',
    'Préparer (EPSG → réduit)'
        : 'Prepare (EPSG → reduced)',
    'Structure  →  Préparer les données (une fois par pays)  →  Assembler la tuile'
        : 'Structure  →  Prepare the data (once per country)  →  Assemble the tile',
    'Préparer les données (EPSG → réduit)'
        : 'Prepare the data (EPSG → reduced)',

    # ── FENÊTRE « AVANCÉ » (JOSM) — module O4_Avance_Utils ─────────
    '\n\nOuvrir quand même le fichier dans JOSM ?'
        : '\n\nOpen the file in JOSM anyway?',
    "\n\npar sa copie d'origine ?"
        : '\n\nwith its original copy?',
    'Aide JOSM'
        : 'JOSM help',
    "Après l'édition dans JOSM"
        : 'After editing in JOSM',
    'Aucun dossier de données OSM pour cette tuile.'
        : 'No OSM data folder for this tile.',
    "Aucun dossier de données OSM pour cette tuile.\n\nLancez d'abord l'étape 1 (Assemble Vector data) : Ortho4XP téléchargera les données OpenStreetMap, qui pourront ensuite être retouchées ici."
        : 'No OSM data folder for this tile.\n\nRun step 1 (Assemble Vector data) first: Ortho4XP will download the OpenStreetMap data, which can then be edited here.',
    "Aucune copie « .original » n'existe pour cette tuile : aucun fichier n'a encore été ouvert dans JOSM."
        : 'No « .original » copy exists for this tile: no file has been opened in JOSM yet.',
    'Avancé (JOSM)'
        : 'Advanced (JOSM)',
    'Avancé — Couches JOSM'
        : 'Advanced — JOSM layers',
    'Aéroport & Runways'
        : 'Airport & Runways',
    'Copie de sécurité créée : '
        : 'Safety copy created: ',
    'Copie de sécurité déjà présente, conservée : '
        : 'Safety copy already present, kept: ',
    'Copie de sécurité impossible'
        : 'Safety copy failed',
    'Données OSM de la tuile'
        : 'Tile OSM data',
    'Dossier absent : '
        : 'Missing folder: ',
    "Enregistrez régulièrement votre travail dans JOSM (une copie « .original » a été créée avant ouverture : le bouton « Restaurer l'original » permet de revenir en arrière à tout moment).\n\nUne fois l'édition terminée et enregistrée, relancez l'étape 1 (Assemble Vector data) dans Ortho4XP : les données modifiées seront reprises telles quelles, sans nouveau téléchargement."
        : 'Save your work in JOSM regularly (an « .original » copy was created before opening: the « Restore the original » button lets you roll back at any time).\n\nOnce editing is finished and saved, run step 1 (Assemble Vector data) again in Ortho4XP: the modified data will be reused as is, with no new download.',
    "Extents/  —  définit où s'applique tel ou tel provider,\nen bord de mer, de lac, ou en pleine terre.\nProduit une paire .ext + _osm.bz2."
        : 'Extents/  —  defines where a given provider applies,\nalong the sea, a lake, or fully inland.\nProduces an .ext + _osm.bz2 pair.',
    'Fichier envoyé à la fenêtre JOSM déjà ouverte.'
        : 'File sent to the already running JOSM window.',
    "Fichier restauré. Relancez l'étape 1 pour que la tuile reparte de la donnée d'origine."
        : 'File restored. Run step 1 again so the tile starts from the original data.',
    'JOSM :'
        : 'JOSM:',
    'JOSM introuvable'
        : 'JOSM not found',
    'JOSM introuvable.'
        : 'JOSM not found.',
    'JOSM lancé avec le fichier.'
        : 'JOSM launched with the file.',
    "JOSM n'a pas été trouvé sur cet ordinateur.\n\nJOSM est l'éditeur OpenStreetMap officiel, gratuit et multiplateforme.\nIl se télécharge sur le site officiel : josm.openstreetmap.de\n\nInstallation :\n  • macOS : télécharger la version macOS et glisser JOSM dans le dossier Applications.\n  • Windows : télécharger l'installeur et l'exécuter.\n  • Linux : installer le paquet josm de la distribution.\n\nUne fois JOSM installé, activez le Remote Control :\n  Menu Édition → Préférences → Remote Control → cocher « Activer le Remote Control ».\nOrtho4XP pourra alors ouvrir les fichiers directement dans la fenêtre JOSM déjà lancée, sans en relancer une seconde."
        : 'JOSM was not found on this computer.\n\nJOSM is the official OpenStreetMap editor, free and cross-platform.\nIt can be downloaded from the official site: josm.openstreetmap.de\n\nInstallation:\n  • macOS: download the macOS build and drag JOSM into the Applications folder.\n  • Windows: download the installer and run it.\n  • Linux: install the josm package of your distribution.\n\nOnce JOSM is installed, enable Remote Control:\n  Edit menu → Preferences → Remote Control → tick « Enable remote control ».\nOrtho4XP will then open files directly in the already running JOSM window, instead of starting a second one.',
    'JOSM répond mais a refusé le fichier.'
        : 'JOSM answered but refused the file.',
    'Java est introuvable : JOSM ne peut pas être lancé depuis le fichier .jar.'
        : 'Java not found: JOSM cannot be started from the .jar file.',
    "La copie de sécurité n'a pas pu être créée :\n"
        : 'The safety copy could not be created:\n',
    "La tuile active n'est pas déterminée : renseignez la latitude et la longitude dans la fenêtre principale."
        : 'The active tile is undefined: please set latitude and longitude in the main window.',
    "Le dossier existe mais ne contient aucun fichier .osm.bz2. Lancez d'abord l'étape 1."
        : 'The folder exists but contains no .osm.bz2 file. Run step 1 first.',
    "Le fichier choisi sera remplacé par sa copie d'origine.\nLes modifications faites dans JOSM seront perdues."
        : 'The selected file will be replaced by its original copy.\nChanges made in JOSM will be lost.',
    'Le module O4_Avance_Utils.py est introuvable dans le dossier src/.'
        : 'Module O4_Avance_Utils.py was not found in the src/ folder.',
    'Nivellement & Terrain'
        : 'Levelling & Terrain',
    'OSM_data/  —  bords de lac, trait de côte, aéroports.\nOn ouvre le fichier existant ; une copie « .original »\nest créée avant, pour pouvoir revenir en arrière.'
        : 'OSM_data/  —  lake shores, coastline, airports.\nThe existing file is opened; an « .original » copy\nis created first, so you can roll back.',
    'Original restauré : '
        : 'Original restored: ',
    'Ouverture : '
        : 'Opening: ',
    'Ouvrir dans JOSM'
        : 'Open in JOSM',
    'Patches/  —  altitude du mesh : aplanir un plateau,\ncreuser une vallée, corriger une bosse du DEM.\nProduit un fichier .patch.osm.'
        : 'Patches/  —  mesh altitude: flatten a plateau,\ncarve a valley, fix a DEM bump.\nProduces a .patch.osm file.',
    'Patches/  —  profil de piste et abords.\nLe nom du fichier doit commencer par le code OACI,\nfaute de quoi le patch reste sans effet.'
        : 'Patches/  —  runway profile and surroundings.\nThe file name must start with the ICAO code,\notherwise the patch has no effect.',
    'Provider & Emprises'
        : 'Provider & Extents',
    'Quel fichier ouvrir ?'
        : 'Which file to open?',
    'Remplacer définitivement :\n'
        : 'Permanently replace:\n',
    'Restaurer'
        : 'Restore',
    "Restaurer l'original"
        : 'Restore the original',
    'Tuile active :'
        : 'Active tile:',
    "Une copie « .original » sera créée si elle n'existe pas encore,\npuis le fichier sera ouvert dans JOSM.\nC'est bien le fichier réel que vous modifiez : Ortho4XP le reprendra tel quel."
        : 'An « .original » copy will be created if it does not exist yet,\nthen the file will be opened in JOSM.\nYou are editing the real file: Ortho4XP will use it as is.',
    'bords de lac, étangs, rivières'
        : 'lake shores, ponds, rivers',
    'bâtiments'
        : 'buildings',
    'emprises aéroportuaires'
        : 'airport areas',
    "en cours d'exécution (Remote Control actif)"
        : 'running (Remote Control active)',
    'indéterminée'
        : 'undefined',
    'installé, non lancé'
        : 'installed, not running',
    'introuvable'
        : 'not found',
    'patches'
        : 'patches',
    'recherche…'
        : 'searching…',
    'routes principales'
        : 'main roads',
    'routes secondaires'
        : 'minor roads',
    'trait de côte'
        : 'coastline',
    'Échec du lancement : '
        : 'Launch failed: ',
    '🛠 Avancé (JOSM)'
        : '🛠 Advanced (JOSM)',

    # ── FENÊTRE « AVANCÉ » (JOSM) — boutons Extents / Patches ──────
    'Application JOSM enregistrée : '
        : 'JOSM application saved: ',
    'Archives Java'
        : 'Java archives',
    "Aucun aérodrome n'a été trouvé dans les données OSM de la tuile.\nZZZZ est le code officiel des aérodromes non répertoriés : le patch s'appliquera normalement, mais l'aplanissement automatique ne sera pas désactivé."
        : 'No aerodrome was found in the tile OSM data.\nZZZZ is the official code for unlisted aerodromes: the patch will apply normally, but automatic flattening will not be disabled.',
    'Aucun nœud lisible dans ce fichier.'
        : 'No readable node in this file.',
    'Aucune emprise dans le dossier Extents/.'
        : 'No extent in the Extents/ folder.',
    "Aérodromes trouvés dans les données OSM de la tuile.\nLe nom du fichier reprend le code OACI : c'est lui qui désactive l'aplanissement automatique."
        : 'Aerodromes found in the tile OSM data.\nThe file name uses the ICAO code: that is what disables automatic flattening.',
    "Choisir l'application JOSM"
        : 'Choose the JOSM application',
    'Créer et ouvrir'
        : 'Create and open',
    'Emprise mise à jour :\n'
        : 'Extent updated:\n',
    'Emprise recalculée : '
        : 'Extent recomputed: ',
    'Fichier .ext créé : '
        : '.ext file created: ',
    "Fichier déjà présent, ouverture de l'existant : "
        : 'File already present, opening the existing one: ',
    "Le dossier Extents/ n'existe pas encore."
        : 'The Extents/ folder does not exist yet.',
    "Le fichier .ext sera réécrit d'après le tracé réellement enregistré dans JOSM."
        : 'The .ext file will be rewritten from the outline actually saved in JOSM.',
    'Modèle créé : '
        : 'Template created: ',
    'Nom du fichier :'
        : 'File name:',
    'Recalculer'
        : 'Recompute',
    "Recalculer l'emprise"
        : 'Recompute the extent',
    "Un rectangle pré-tagué va s'ouvrir dans JOSM : déplacez ses nœuds pour épouser la zone souhaitée.\n\nUNE FOIS ENREGISTRÉ dans JOSM, revenez ici et cliquez sur « Recalculer l'emprise » : le fichier .ext sera mis à jour d'après votre tracé. Sans cela l'emprise reste celle du rectangle d'origine."
        : 'A pre-tagged rectangle will open in JOSM: move its nodes to match the area you want.\n\nONCE SAVED in JOSM, come back here and click « Recompute the extent »: the .ext file will be updated from your outline. Otherwise the extent stays that of the original rectangle.',
    "Un rectangle pré-tagué va s'ouvrir dans JOSM.\n\nPlacez-le sur la piste, puis renseignez altitude_low et altitude_high en MÈTRES aux deux extrémités. Pour une piste plate, mettez la même valeur des deux côtés, ou remplacez les deux tags par un seul tag altitude."
        : 'A pre-tagged rectangle will open in JOSM.\n\nPlace it over the runway, then set altitude_low and altitude_high in METRES at both ends. For a flat runway, use the same value on both sides, or replace both tags with a single altitude tag.',
    "Un rectangle pré-tagué « altitude=0 » va s'ouvrir dans JOSM.\n\nDéplacez ses nœuds sur la zone à corriger, puis remplacez la valeur d'altitude par l'altitude voulue, en MÈTRES.\n\nPour une pente, remplacez le tag altitude par altitude_low et altitude_high, et ajoutez si besoin profile=spline."
        : 'A rectangle pre-tagged « altitude=0 » will open in JOSM.\n\nMove its nodes over the area to fix, then replace the altitude value with the one you want, in METRES.\n\nFor a slope, replace the altitude tag with altitude_low and altitude_high, and add profile=spline if needed.',
    'aérodrome non répertorié'
        : 'unlisted aerodrome',

    # ── Avancé (JOSM) — boutons de couches ─────────────────────────
    "Aucune donnée — lancer l'étape 1"
        : 'No data — run step 1',

    # ── Avancé (JOSM) — sauvegarde fichier source ──────────────────
    "Aucune copie d'origine pour cette tuile : aucun fichier n'a encore été ouvert dans JOSM."
        : 'No original copy for this tile: no file has been opened in JOSM yet.',
    "Enregistrez régulièrement votre travail dans JOSM (une copie d'origine a été rangée dans « Sauvegarde fichier source » avant ouverture : le bouton « Restaurer l'original » permet de revenir en arrière à tout moment).\n\nUne fois l'édition terminée et enregistrée, relancez l'étape 1 (Assemble Vector data) dans Ortho4XP : les données modifiées seront reprises telles quelles, sans nouveau téléchargement."
        : 'Save your work in JOSM regularly (an original copy was stored in « Sauvegarde fichier source » before opening: the « Restore the original » button lets you roll back at any time).\n\nOnce editing is finished and saved, run step 1 (Assemble Vector data) again in Ortho4XP: the modified data will be reused as is, with no new download.',
    'OSM_data/  —  bords de lac, trait de côte, aéroports.\nOn ouvre le fichier existant ; une copie est rangée dans\n« Sauvegarde fichier source » pour revenir en arrière.'
        : 'OSM_data/  —  lake shores, coastline, airports.\nThe existing file is opened; a copy is stored in\n« Sauvegarde fichier source » so you can roll back.',
    "Une copie d'origine sera rangée dans « Sauvegarde fichier source »\nsi elle n'existe pas encore, puis le fichier sera ouvert dans JOSM.\nC'est bien le fichier réel que vous modifiez : Ortho4XP le reprendra tel quel."
        : 'An original copy will be stored in « Sauvegarde fichier source »\nif it does not exist yet, then the file will be opened in JOSM.\nYou are editing the real file: Ortho4XP will use it as is.',

    # ── Avancé (JOSM) — sauvegarde / réapplication ─────────────────
    "\n\nRelancez ensuite l'étape 1."
        : '\n\nThen run step 1 again.',
    'Aucune modification sauvegardée pour cette tuile.'
        : 'No saved changes for this tile.',
    "Aucune modification à sauvegarder : les fichiers sont identiques à l'original."
        : 'Nothing to save: the files are identical to the original.',
    "Deux copies vivent dans « Sauvegarde fichier source », hors\ndu dossier de la tuile : elles survivent donc à sa suppression.\n\n• l'original, tel qu'Ortho4XP l'avait téléchargé\n• vos modifications, à réappliquer sur une tuile reconstruite"
        : 'Two copies live in « Sauvegarde fichier source », outside\nthe tile folder: they therefore survive its deletion.\n\n• the original, as Ortho4XP downloaded it\n• your changes, to reapply on a rebuilt tile',
    "Enregistrez régulièrement votre travail dans JOSM (une copie d'origine a été rangée dans « Sauvegarde fichier source » avant ouverture : le bouton « Restaurer l'original » permet de revenir en arrière à tout moment).\n\nQuand votre édition sera terminée et enregistrée, cliquez sur « Sauvegardes… » puis « Sauvegarder mes modifications » : votre travail sera alors protégé même si la tuile est supprimée ou reconstruite.\n\nUne fois l'édition terminée et enregistrée, relancez l'étape 1 (Assemble Vector data) dans Ortho4XP : les données modifiées seront reprises telles quelles, sans nouveau téléchargement."
        : 'Save your work in JOSM regularly (an original copy was stored in « Sauvegarde fichier source » before opening: the « Restore the original » button lets you roll back at any time).\n\nWhen your editing is finished and saved, click « Backups… » then « Save my changes »: your work will then be protected even if the tile is deleted or rebuilt.\n\nOnce editing is finished and saved, run step 1 (Assemble Vector data) again in Ortho4XP: the modified data will be reused as is, with no new download.',
    'Fichiers sauvegardés : '
        : 'Files saved: ',
    'Modifications réappliquées : '
        : 'Changes reapplied: ',
    "Modifications réappliquées. Relancez l'étape 1 pour que la tuile les prenne en compte."
        : 'Changes reapplied. Run step 1 again so the tile takes them into account.',
    'Modifications sauvegardées : '
        : 'Changes saved: ',
    'Remplacer les données OSM de la tuile par vos modifications sauvegardées ?\n\nFichiers concernés : '
        : 'Replace the tile OSM data with your saved changes?\n\nFiles concerned: ',
    'Réappliquer mes modifications'
        : 'Reapply my changes',
    'Sauvegarder mes modifications'
        : 'Save my changes',
    'Sauvegarder mes modifications maintenant'
        : 'Save my changes now',
    'Sauvegardes'
        : 'Backups',
    'Sauvegardes…'
        : 'Backups…',

    # ── Avancé (JOSM) — sauvegarde à la fermeture ──────────────────
    'Modifications sauvegardées à la fermeture : '
        : 'Changes saved on closing: ',

    # ── Avancé (JOSM) — état de l'application ──────────────────────
    "non sélectionné — cliquez sur « Choisir l'application JOSM »"
        : 'not selected — click « Choose the JOSM application »',

    # ── Avancé (JOSM) — lancement de l'application ─────────────────
    'Démarrage de JOSM, veuillez patienter…'
        : 'Starting JOSM, please wait…',
    'Fichier transmis à JOSM.'
        : 'File sent to JOSM.',
    "JOSM a été lancé. Si le fichier ne s'ouvre pas, activez le Remote Control dans les préférences de JOSM (voir « Aide JOSM »)."
        : 'JOSM has been launched. If the file does not open, enable Remote Control in the JOSM preferences (see « JOSM help »).',

    # ── Avancé (JOSM) — publication d'emprise ──────────────────────
    'Emprise publiée : '
        : 'Extent published: ',
    'Emprise publiée et mise à jour :\n'
        : 'Extent published and updated:\n',
    "Le fichier compressé attendu par Ortho4XP et l'emprise .ext\nseront écrits d'après le tracé réellement enregistré dans JOSM."
        : 'The compressed file expected by Ortho4XP and the .ext extent\nwill be written from the outline actually saved in JOSM.',
    'Publier'
        : 'Publish',
    "Publier l'emprise"
        : 'Publish the extent',
    "Un rectangle pré-tagué va s'ouvrir dans JOSM : déplacez ses nœuds pour épouser la zone souhaitée.\n\nUNE FOIS ENREGISTRÉ dans JOSM, revenez ici et cliquez sur « Publier l'emprise » : Ortho4XP attend un fichier compressé au nom particulier, que JOSM ne sait pas ouvrir. La publication écrit ce fichier et met l'emprise à jour d'après votre tracé.\n\nSans cette publication, votre emprise ne sera pas prise en compte."
        : 'A pre-tagged rectangle will open in JOSM: move its nodes to match the area you want.\n\nONCE SAVED in JOSM, come back here and click « Publish the extent »: Ortho4XP expects a compressed file with a particular name that JOSM cannot open. Publishing writes that file and updates the extent from your outline.\n\nWithout publishing, your extent will not be taken into account.',

    # ── Avancé (JOSM) — avertissement téléversement ────────────────
    "Dans JOSM, utilisez toujours ENREGISTRER, jamais ENVOYER : « Envoyer » téléverse vers les serveurs publics d'OpenStreetMap.\n\nUn rectangle pré-tagué va s'ouvrir dans JOSM : déplacez ses nœuds pour épouser la zone souhaitée.\n\nUNE FOIS ENREGISTRÉ dans JOSM, revenez ici et cliquez sur « Publier l'emprise » : Ortho4XP attend un fichier compressé au nom particulier, que JOSM ne sait pas ouvrir. La publication écrit ce fichier et met l'emprise à jour d'après votre tracé.\n\nSans cette publication, votre emprise ne sera pas prise en compte."
        : 'In JOSM, always use SAVE, never UPLOAD: « Upload » sends your data to the public OpenStreetMap servers.\n\nA pre-tagged rectangle will open in JOSM: move its nodes to match the area you want.\n\nONCE SAVED in JOSM, come back here and click « Publish the extent »: Ortho4XP expects a compressed file with a particular name that JOSM cannot open. Publishing writes that file and updates the extent from your outline.\n\nWithout publishing, your extent will not be taken into account.',

    # ── Avancé (JOSM) — récupération de fichier égaré ──────────────
    'Fichier récupéré et rangé dans Extents/ : '
        : 'File recovered and filed into Extents/: ',

    # ── Avancé (JOSM) — fichiers au mauvais endroit ────────────────
    "\n\nRanger maintenant ? Aucun doublon ne subsistera : chaque fichier rejoint Extents/ ou disparaît s'il y fait doublon."
        : '\n\nFile them now? No duplicate will remain: each file either joins Extents/ or is removed if it duplicates what is already there.',
    ' fichier(s) laissé(s) en place.'
        : ' file(s) left in place.',
    "Des fichiers d'emprise ont été enregistrés ailleurs que dans Extents/.\nOrtho4XP ne les voit pas à cet endroit.\n\n"
        : 'Some extent files were saved outside Extents/.\nOrtho4XP does not see them there.\n\n',
    'Doublon supprimé : '
        : 'Duplicate deleted: ',
    'DÉPLACER vers Extents/'
        : 'MOVE to Extents/',
    'Déplacé dans Extents/ : '
        : 'Moved to Extents/: ',
    'Fichiers enregistrés au mauvais endroit'
        : 'Files saved in the wrong place',
    'Rangement refusé : '
        : 'Filing declined: ',
    'SUPPRIMER'
        : 'DELETE',
    'absent de Extents/'
        : 'missing from Extents/',
    'identique à celui de Extents/'
        : 'identical to the one in Extents/',
    'plus ancien que celui de Extents/'
        : 'older than the one in Extents/',
    'plus récent que celui de Extents/'
        : 'newer than the one in Extents/',
    'Échec : '
        : 'Failed: ',

    # ── Avancé (JOSM) — consigne d'enregistrement ──────────────────
    ", ou menu Fichier puis Enregistrer.\n\nLe fichier repart directement au bon endroit : JOSM a retenu son emplacement, il n'y a aucun dossier à choisir.\n\nÉvitez « Enregistrer sous » et « Enregistrer la session » : ce sont les deux commandes qui font atterrir le fichier au mauvais endroit. Raccourcis équivalents : Cmd+S sur macOS, Ctrl+S sur Windows et Linux."
        : ', or the File menu then Save.\n\nThe file goes straight back to the right place: JOSM remembers its location, there is no folder to choose.\n\nAvoid « Save as » and « Save session »: those are the two commands that make the file land in the wrong place. Equivalent shortcuts: Cmd+S on macOS, Ctrl+S on Windows and Linux.',
    "Enregistrez régulièrement votre travail dans JOSM (une copie d'origine a été rangée dans « Sauvegarde fichier source » avant ouverture : le bouton « Restaurer l'original » permet de revenir en arrière à tout moment).\n\nQuand votre édition sera terminée et enregistrée, cliquez sur « Sauvegardes… » puis « Sauvegarder mes modifications » : votre travail sera alors protégé même si la tuile est supprimée ou reconstruite.\n\nUne fois l'édition terminée et enregistrée, relancez l'étape 1 (Assemble Vector data) dans Ortho4XP : les données modifiées seront reprises telles quelles, sans nouveau téléchargement.\n\n"
        : 'Save your work in JOSM regularly (an original copy was stored in « Sauvegarde fichier source » before opening: the « Restore the original » button lets you roll back at any time).\n\nWhen your editing is finished and saved, click « Backups… » then « Save my changes »: your work will then be protected even if the tile is deleted or rebuilt.\n\nOnce editing is finished and saved, run step 1 (Assemble Vector data) again in Ortho4XP: the modified data will be reused as is, with no new download.\n\n',
    'POUR ENREGISTRER dans JOSM : '
        : 'TO SAVE in JOSM: ',
    "Un rectangle pré-tagué va s'ouvrir dans JOSM.\n\nPlacez-le sur la piste, puis renseignez altitude_low et altitude_high en MÈTRES aux deux extrémités. Pour une piste plate, mettez la même valeur des deux côtés, ou remplacez les deux tags par un seul tag altitude.\n\n"
        : 'A pre-tagged rectangle will open in JOSM.\n\nPlace it over the runway, then set altitude_low and altitude_high in METRES at both ends. For a flat runway, use the same value on both sides, or replace both tags with a single altitude tag.\n\n',
    "Un rectangle pré-tagué « altitude=0 » va s'ouvrir dans JOSM.\n\nDéplacez ses nœuds sur la zone à corriger, puis remplacez la valeur d'altitude par l'altitude voulue, en MÈTRES.\n\nPour une pente, remplacez le tag altitude par altitude_low et altitude_high, et ajoutez si besoin profile=spline.\n\n"
        : 'A rectangle pre-tagged « altitude=0 » will open in JOSM.\n\nMove its nodes over the area to fix, then replace the altitude value with the one you want, in METRES.\n\nFor a slope, replace the altitude tag with altitude_low and altitude_high, and add profile=spline if needed.\n\n',
    'sur Linux'
        : 'on Linux',
    'sur Windows'
        : 'on Windows',
    'sur macOS'
        : 'on macOS',

    # ── Avancé (JOSM) — saisie de nom ──────────────────────────────
    'Valider'
        : 'OK',

    # ── Avancé (JOSM) — publication automatique ────────────────────
    "Dans JOSM, utilisez toujours ENREGISTRER, jamais ENVOYER : « Envoyer » téléverse vers les serveurs publics d'OpenStreetMap.\n\nUn rectangle pré-tagué va s'ouvrir dans JOSM : déplacez ses nœuds pour épouser la zone souhaitée.\n\nDès que vous enregistrerez dans JOSM, Ortho4XP recevra automatiquement votre tracé : vous n'avez aucune autre manipulation à faire.\n\n"
        : 'In JOSM, always use SAVE, never UPLOAD: « Upload » sends your data to the public OpenStreetMap servers.\n\nA pre-tagged rectangle will open in JOSM: move its nodes to match the area you want.\n\nAs soon as you save in JOSM, Ortho4XP automatically receives your outline: there is nothing else for you to do.\n\n',

    # ── Lacunes anterieures comblees le 19/07/2026 (GUI + Correction) ──
    '0%=gris  100%=réf.48753JPG  200%=×2'
        : '0%=grey  100%=ref.48753JPG  200%=×2',
    'Application :'
        : 'Application:',
    "Aucun dossier PATCH trouvé pour cette tuile.\nLancer d'abord le Step 2.1 — Sea Patches."
        : 'No PATCH folder found for this tile.\nRun Step 2.1 — Sea Patches first.',
    'Aucun patch JPG trouvé dans :\n'
        : 'No JPG patch found in:\n',
    'Aucun patch sélectionné.'
        : 'No patch selected.',
    "Aucune application définie.\nCliquer d'abord sur 'Correction' pour choisir l'application."
        : "No application set.\nClick 'Correction' first to choose the application.",
    'Boost:'
        : 'Boost:',
    "Choisir l'application de correction (GIMP, Photoshop…)"
        : 'Choose the editing application (GIMP, Photoshop…)',
    'Cocher les patches à traiter'
        : 'Tick the patches to process',
    'Confirmation'
        : 'Confirmation',
    'Correction Patches'
        : 'Patch correction',
    'Correction imagerie/zone'
        : 'Imagery / area correction',
    'Correction patches'
        : 'Patch correction',
    'Correction patches — Ortho4XP V3'
        : 'Patch correction — Ortho4XP V3',
    'Erreur'
        : 'Error',
    'Erreur ouverture'
        : 'Opening error',
    "Impossible d'ouvrir l'application"
        : 'Could not open the application',
    'Impossible de sauvegarder le chemin éditeur'
        : 'Could not save the editor path',
    'Impossible de supprimer'
        : 'Could not delete',
    'Lacs & Rivières'
        : 'Lakes & Rivers',
    'Saturation:'
        : 'Saturation:',
    'Supprimer {n} patch(es) sélectionné(s) ?'
        : 'Delete {n} selected patch(es)?',
    '── JPG à corriger ──'
        : '── JPG to correct ──',
    '🌊 Mer & Côte'
        : '🌊 Sea & Coast',

    # ── Altimétrie / DEM — dossiers désignés par l'utilisateur ─────
    '(non configurée)'
        : '(not set)',
    "Aucun dossier d'altimétries n'est configuré."
        : 'No elevation folder is set.',
    'Choisissez le disque ou le dossier où créer votre organisation des altimétries (un disque externe convient).'
        : 'Choose the drive or folder where your elevation data structure should be created (an external drive works fine).',
    'Cliquez sur « Dossier des sources ».'
        : 'Click « Source folder ».',
    'Créer la structure'
        : 'Create the structure',
    "Deux dossiers sont nécessaires :\n\n1) celui où se trouvent vos altimétries sources ;\n2) celui où écrire les altimétries assemblées.\n\nVoulez-vous qu'Ortho4XP crée cette organisation pour vous ?\n\nOUI  →  la structure est créée automatiquement.\nNON  →  vous désignez vos propres dossiers, qui sont utilisés tels quels."
        : 'Two folders are required:\n\n1) the one holding your source elevation files;\n2) the one where assembled elevation files are written.\n\nDo you want Ortho4XP to create this structure for you?\n\nYES  →  the structure is created automatically.\nNO   →  you pick your own folders, used exactly as they are.',
    'Dossier de destination des altimétries assemblées'
        : 'Destination folder for assembled elevation files',
    'Dossier de sortie'
        : 'Output folder',
    'Dossier de sortie :'
        : 'Output folder:',
    'Dossier de vos altimétries sources (.tif, .asc…)'
        : 'Folder holding your source elevation files (.tif, .asc…)',
    'Dossier des sources'
        : 'Source folder',
    'Dossier des sources :'
        : 'Source folder:',
    'Dossiers enregistrés.'
        : 'Folders saved.',
    'Dossiers enregistrés.\n\nSources :\n{s}\n\nSortie :\n{d}'
        : 'Folders saved.\n\nSources:\n{s}\n\nOutput:\n{d}',
    'Dossiers non configurés.'
        : 'Folders not set.',
    'Déposez vos données dans le dossier des sources, en EPSG:4326.'
        : 'Put your data in the source folder, in EPSG:4326.',
    'Les sources doivent être en EPSG:4326 — X-Plane ne lit'
        : 'Sources must be in EPSG:4326 — X-Plane reads no',
    "Où créer l'organisation des altimétries"
        : 'Where to create the elevation data structure',
    'Sortie :'
        : 'Output:',
    'Sources :'
        : 'Sources:',
    'aucune autre projection. Ortho4XP convertira au besoin,'
        : 'other projection. Ortho4XP will convert if needed,',
    'dossier des sources'
        : 'source folder',
    'mais préparez-les de préférence en 4326.'
        : 'but preparing them in 4326 is preferable.',

    # ── Altimétrie / DEM — rappel des dossiers ─────────────────────
    '(non configuré)'
        : '(not set)',
    'Le fichier assemblé sera écrit ici :\n\n{f}\n\nEst-ce le bon emplacement ?\n\nNON  →  utilisez le bouton « Dossier de sortie ».'
        : 'The assembled file will be written here:\n\n{f}\n\nIs this the right location?\n\nNO  →  use the « Output folder » button.',

    # ── LOCAL OSM CACHE (.pbf) — O4_PBF_Utils module ─────
    'Cache OSM local (.pbf)'
        : 'Local OSM cache (.pbf)',
    '🗺 Cache OSM local (.pbf)'
        : '🗺 Local OSM cache (.pbf)',
    "Remplit OSM_data/ à partir d'un ou plusieurs extraits .pbf locaux afin que l'étape 1 ne télécharge plus rien."
        : 'Fills OSM_data/ from one or more local .pbf extracts so that Step 1 no longer downloads anything.',
    'Fichier(s) PBF :'
        : 'PBF file(s):',
    'Parcourir (un ou plusieurs)...'
        : 'Browse (one or more)...',
    'Astuce : vous pouvez sélectionner plusieurs fichiers à la fois (Cmd-clic ou Ctrl-clic) — utile pour une tuile à cheval sur deux régions.'
        : 'Tip: you can select several files at once (Cmd-click or Ctrl-click) — useful for a tile straddling two regions.',
    'De latitude / longitude :'
        : 'From latitude / longitude:',
    'À latitude / longitude :'
        : 'To latitude / longitude:',
    'Niveau de routes (0 = aucun) :'
        : 'Road level (0 = none):',
    'Écraser les fichiers de cache existants'
        : 'Overwrite existing cache files',
    'Construire le cache OSM local'
        : 'Build local OSM cache',
    'La latitude et la longitude doivent être des nombres entiers.'
        : 'Latitude and longitude must be whole numbers.',
    'Fichier PBF introuvable.'
        : 'PBF file not found.',
    'Nombre de tuiles demandé très important. Continuer ?'
        : 'A very large number of tiles was requested. Continue?',
    'Cache OSM local terminé. Fichiers écrits :'
        : 'Local OSM cache completed. Files written:',
    'Erreur pendant la lecture du fichier PBF.'
        : 'Error while reading the PBF file.',
    'Chaque fichier est relu 5 fois : comptez quelques minutes par lot de tuiles. Pour une tuile à cheval sur deux régions, sélectionnez les deux extraits .pbf à la fois.'
        : 'Each file is read 5 times: allow a few minutes per batch of tiles. For a tile straddling two regions, select both .pbf extracts at once.',
    'Le module O4_PBF_Utils.py est introuvable dans le dossier src/.'
        : 'Module O4_PBF_Utils.py not found in the src/ folder.',

    # ── AJOUTS SESSION 23/07/2026 — TEXTES FRANÇAIS DE O4_GUI_Utils.py ──
    '100%  (réf.)'
        : '100%  (ref.)',
    'Avertissement save_zone_list: '
        : 'Warning save_zone_list: ',
    'Boost — intensité de la saturation'
        : 'Boost — saturation intensity',
    'Coordonnées et dossier de la tuile'
        : 'Tile coordinates and folder',
    'Copiez Utils/Earth/ depuis Ortho4XP 2.00\n\nDouble-clic = sélectionner tuile\nShift+clic = ajouter au batch'
        : 'Copy Utils/Earth/ from Ortho4XP 2.00\n\nDouble-click = select tile\nShift+click = add to batch',
    'Corrections avancées'
        : 'Advanced corrections',
    'Erreur : '
        : 'Error: ',
    'Fabrication Tuile'
        : 'Tile Building',
    'Fenêtre de configuration\n('
        : 'Configuration window\n(',
    'Gestion des Couleurs automatisée'
        : 'Automated Colour Management',
    'Gestion des Données'
        : 'Data Management',
    'Intensité de la correction'
        : 'Correction intensity',
    'Red flag activé'
        : 'Red flag enabled',
    'Zones sauvegardées dans cfg tuile '
        : 'Zones saved in tile cfg ',
    "[CorrMod] Repli sur l'ancienne fenêtre : "
        : '[CorrMod] Falling back to the legacy window: ',
    '[OACI] Serveurs Overpass indisponibles — cercles aéroports non affichés.'
        : '[ICAO] Overpass servers unavailable — airport circles not displayed.',
    '[Timeline] Erreur affichage : '
        : '[Timeline] Display error: ',
    'apt_curv_ext : extension de la zone de précision autour des aéroports. 1.0 = recommandé.'
        : 'apt_curv_ext: extension of the precision area around airports. 1.0 = recommended.',
    'apt_curv_tol : tolérance de courbure spécifique aux aéroports. 1.5 = recommandé. Valeur basse = géométrie aéroport plus précise.'
        : 'apt_curv_tol: curvature tolerance specific to airports. 1.5 = recommended. Lower value = more precise airport geometry.',
    'apt_smoothing_pix : lissage en pixels de la zone aéroport dans le mesh. 8 = recommandé pour éviter les bosses sur les pistes.'
        : 'apt_smoothing_pix: smoothing in pixels of the airport area in the mesh. 8 = recommended to avoid bumps on the runways.',
    'aéroport ZL'
        : 'airport ZL',
    'aéroport: ZL défaut'
        : 'airport: default ZL',
    'clean_bad_geometries : supprime les géométries vectorielles invalides avant la triangulation. True = recommandé.'
        : 'clean_bad_geometries: removes invalid vector geometries before triangulation. True = recommended.',
    'courbure'
        : 'curvature',
    'cover_airports_with_highres : active la haute résolution autour des aéroports. True = recommandé si un aéroport est présent sur la tuile.'
        : 'cover_airports_with_highres: enables high resolution around airports. True = recommended if an airport is present on the tile.',
    'cover_extent : rayon en km autour des aéroports pour la haute résolution. 1.0 = recommandé. 3.0 = large zone haute résolution.'
        : 'cover_extent: radius in km around airports for high resolution. 1.0 = recommended. 3.0 = large high-resolution area.',
    'cover_zl : zoom level haute résolution autour des aéroports. 18 = recommandé pour voir les marquages et taxiways.'
        : 'cover_zl: high-resolution zoom level around airports. 18 = recommended to see markings and taxiways.',
    'curvature_tol : tolérance de courbure générale du mesh. Valeur basse = plus de triangles, relief plus précis. 16 = recommandé. 1 = très dense (lent). 30 = grossier.'
        : 'curvature_tol: overall curvature tolerance of the mesh. Lower value = more triangles, more precise relief. 16 = recommended. 1 = very dense (slow). 30 = coarse.',
    "default_zl : niveau de zoom de l'imagerie principale. 14-15 = faible résolution, flou. 17 = résolution standard, recommandé. 19-20 = très haute résolution, très lourd en VRAM."
        : 'default_zl: zoom level of the main imagery. 14-15 = low resolution, blurry. 17 = standard resolution, recommended. 19-20 = very high resolution, very heavy on VRAM.',
    'décals terrain'
        : 'terrain decals',
    'décals='
        : 'decals=',
    'fill_nodata : remplit les zones sans données altimétriques par interpolation du voisin le plus proche. True = recommandé pour les DEM avec trous sur la mer.'
        : 'fill_nodata: fills areas with no elevation data by nearest-neighbour interpolation. True = recommended for DEMs with holes over the sea.',
    'grossier'
        : 'coarse',
    'imprint_masks_to_dds : grave le canal alpha dans le DDS (BC3). True = nécessaire pour transparence XP12 (recommandé). ⚠ False + water_tech=XP12 = jointures visibles.'
        : 'imprint_masks_to_dds: burns the alpha channel into the DDS (BC3). True = required for XP12 transparency (recommended). ⚠ False + water_tech=XP12 = visible seams.',
    "iterate : nombre d'itérations de raffinement du mesh. 0 = pas d'itération (rapide). 1-2 = meilleure qualité côtière. 3 = très long."
        : 'iterate: number of mesh refinement iterations. 0 = no iteration (fast). 1-2 = better coastal quality. 3 = very slow.',
    'limit_tris : limite du nombre de triangles en millions. 15 = recommandé. Augmenter pour les zones très complexes.'
        : 'limit_tris: triangle count limit in millions. 15 = recommended. Increase for very complex areas.',
    'limite'
        : 'limit',
    'mask_zl : résolution des masques côtiers. 17 = bon équilibre (recommandé). 19-20 = très précis, fichiers lourds.'
        : 'mask_zl: coastal mask resolution. 17 = good balance (recommended). 19-20 = very precise, heavy files.',
    'masking_mode : algorithme masque. sand = dégradé naturel (recommandé). rocks = transition abrupte (falaises). 3steps = 3 étapes personnalisées.'
        : 'masking_mode: mask algorithm. sand = natural gradient (recommended). rocks = abrupt transition (cliffs). 3steps = 3 custom steps.',
    'masks_width : largeur en mètres de la zone de dégradé côtier. 100m = transition nette (recommandé). 500m = dégradé naturel. ⚠ Valeurs > 500m peuvent produire des jointures visibles.'
        : 'masks_width: width in metres of the coastal blending band. 100m = sharp transition (recommended). 500m = natural gradient. ⚠ Values > 500m may produce visible seams.',
    "max_area : surface maximum d'un polygone vectoriel. Les polygones plus grands sont découpés. 100 = recommandé."
        : 'max_area: maximum area of a vector polygon. Larger polygons are split. 100 = recommended.',
    'max_levelled_segs : nombre maximum de segments de route nivelés. 200000 = recommandé.'
        : 'max_levelled_segs: maximum number of levelled road segments. 200000 = recommended.',
    'mesh_zl : zoom level du maillage 3D. 14-16 = mesh grossier, relief approximatif. 19 = mesh très précis, côtes et falaises détaillées (recommandé). 20 = très lourd, rarement nécessaire.'
        : 'mesh_zl: zoom level of the 3D mesh. 14-16 = coarse mesh, approximate relief. 19 = very precise mesh, detailed coastlines and cliffs (recommended). 20 = very heavy, rarely needed.',
    'min_angle : angle minimum des triangles du mesh. 0.5 = recommandé. Valeur basse = meilleure qualité géométrique.'
        : 'min_angle: minimum angle of the mesh triangles. 0.5 = recommended. Lower value = better geometric quality.',
    "min_area : surface minimum d'un polygone vectoriel (en degrés²). Les polygones plus petits sont ignorés. 0.0001 = recommandé (élimine les micro-polygones parasites)."
        : 'min_area: minimum area of a vector polygon (in square degrees). Smaller polygons are ignored. 0.0001 = recommended (removes spurious micro-polygons).',
    'moyen'
        : 'medium',
    "normal_map_strength : intensité de l'ombrage terrain. 0 = terrain plat visuellement. 1.0 = ombrage exact (recommandé). 2.0 = ombrage très marqué, peut sembler exagéré sur terrain plat."
        : 'normal_map_strength: terrain shading intensity. 0 = visually flat terrain. 1.0 = exact shading (recommended). 2.0 = very strong shading, may look exaggerated on flat terrain.',
    'ombres='
        : 'shadows=',
    "overlay_lod : distance en mètres jusqu'où XPlane affiche l'imagerie sur la mer. 30000 = recommandé."
        : 'overlay_lod: distance in metres up to which X-Plane displays imagery over the sea. 30000 = recommended.',
    'précis'
        : 'precise',
    'ratio_bathy : dégradé de profondeur XP12. 0 = mer uniforme. 1 = eau profonde sombre → turquoise côtier (recommandé).'
        : 'ratio_bathy: XP12 depth gradient. 0 = uniform sea. 1 = dark deep water → coastal turquoise (recommended).',
    'ratio_water : 0 = JPG satellite opaque sur mer. 1 = eau XP12 entièrement visible (vagues, reflets, bathymétrie). Recommandé : 0.10 pour Vendée/Atlantique.'
        : 'ratio_water: 0 = opaque satellite JPG over the sea. 1 = XP12 water fully visible (waves, reflections, bathymetry). Recommended: 0.10 for Vendée/Atlantic.',
    'road_level : densité des routes intégrées dans le mesh. 0 = aucune route. 4 = toutes les routes (recommandé).'
        : 'road_level: density of roads embedded in the mesh. 0 = no roads. 4 = all roads (recommended).',
    'terrain_casts_shadows : le terrain projette des ombres sur lui-même. True = ombres réalistes (recommandé). False = moins réaliste mais gain de performances.'
        : 'terrain_casts_shadows: the terrain casts shadows on itself. True = realistic shadows (recommended). False = less realistic but faster.',
    'triangles'
        : 'triangles',
    'très précis'
        : 'very precise',
    'tuile '
        : 'tile ',
    'use_decal_on_terrain : applique des décals de texture (herbe/roche) sur le terrain pour améliorer le rendu au sol à basse altitude. True = recommandé pour la Vendée.'
        : 'use_decal_on_terrain: applies texture decals (grass/rock) on the terrain to improve ground rendering at low altitude. True = recommended for the Vendée.',
    'use_masks_for_inland : applique les masques côtiers sur lacs et rivières. False = recommandé (économise VRAM). True = masque lac visible dans le canvas ci-dessus.'
        : 'use_masks_for_inland: applies coastal masks to lakes and rivers. False = recommended (saves VRAM). True = lake mask visible in the canvas above.',
    'water_simplification : simplification des polygones eau. 0 = pas de simplification (précis). 0.5 = simplification modérée. 1.0 = très simplifié (rapide mais moins précis).'
        : 'water_simplification: water polygon simplification. 0 = no simplification (precise). 0.5 = moderate simplification. 1.0 = heavily simplified (fast but less precise).',
    'water_smoothing : lissage du maillage eau intérieure. 2 = recommandé.'
        : 'water_smoothing: inland water mesh smoothing. 2 = recommended.',
    'water_tech : XP12 = eau dynamique (vagues, reflets, bathymétrie). ⚠ XP11+bathy = ancien mode, incompatible avec imprint_masks_to_dds=True.'
        : 'water_tech: XP12 = dynamic water (waves, reflections, bathymetry). ⚠ XP11+bathy = legacy mode, incompatible with imprint_masks_to_dds=True.',
    'zone aéroport XP12'
        : 'XP12 airport zone',
    '── Navigation ──\nClic + glisser\n   Déplacer la carte\nMolette\n   Zoom avant / arrière\n\n── Tracer une zone ──\nShift + clic\n   Ajouter un point\nCtrl+Shift + clic\n   Point aligné grille\n Sauvegarder la zone\nBackspace  Annuler dernier pt\n\n── Rectangle ZL ──\nCtrl + clic (vide)\n   Créer rectangle\nCtrl + clic (zone)\n   Supprimer rectangle\nd  Supprimer dernière zone'
        : '── Navigation ──\nClick + drag\n   Pan the map\nMouse wheel\n   Zoom in / out\n\n── Draw a zone ──\nShift + click\n   Add a point\nCtrl+Shift + click\n   Grid-aligned point\n Save the zone\nBackspace  Undo last point\n\n── ZL rectangle ──\nCtrl + click (empty)\n   Create rectangle\nCtrl + click (zone)\n   Delete rectangle\nd  Delete last zone',
    '⚠ XP11+bathy : vagues XP12 désactivées'
        : '⚠ XP11+bathy: XP12 waves disabled',
    '🎚  Simulateur Ortho4XP — tuile '
        : '🎚  Ortho4XP Simulator — tile ',

    # ── BATHYMÉTRIE / fonds marins (module O4_Bathymetrie_Utils) ──
    '🌊 Bathymétrie'
        : '🌊 Bathymetry',
    'Bathymétrie'
        : 'Bathymetry',
    'Le module O4_Bathymetrie_Utils.py est introuvable dans le dossier src/.'
        : 'The O4_Bathymetrie_Utils.py module was not found in the src/ folder.',
    'Bathymétrie — Ortho4XP V3'
        : 'Bathymetry — Ortho4XP V3',
    "Assemblage terminé.\n\n{f}\n\ncustom_bathy_dem est renseigné : la tuile est prête pour l'étape mesh."
        : 'Assembly complete.\n\n{f}\n\ncustom_bathy_dem is set: the tile is ready for the mesh step.',
    "Aucun dossier de bathymétries n'est configuré."
        : 'No bathymetry folder is set.',
    'Aucun fichier bathymétrique lisible dans ce dossier.'
        : 'No readable bathymetry file in this folder.',
    'Aucun fichier bathymétrique ne recouvre cette tuile.'
        : 'No bathymetry file covers this tile.',
    'Choisissez le disque ou le dossier où créer votre organisation des bathymétries (un disque externe convient).'
        : 'Choose the drive or folder where your bathymetry data structure should be created (an external drive works fine).',
    'Dans quel dossier de la structure Bathymétrie voulez-vous travailler ?'
        : 'Which folder of the Bathymetry structure do you want to work in?',
    "Deux dossiers sont nécessaires :\n\n1) celui où se trouvent vos bathymétries sources ;\n2) celui où écrire les bathymétries assemblées.\n\nVoulez-vous qu'Ortho4XP crée cette organisation pour vous ?\n\nOUI  →  la structure est créée automatiquement.\nNON  →  vous désignez vos propres dossiers, qui sont utilisés tels quels."
        : 'Two folders are needed:\n\n1) the one holding your source bathymetry files;\n2) the one where assembled bathymetry files are written.\n\nDo you want Ortho4XP to create this structure for you?\n\nYES  →  the structure is created automatically.\nNO  →  you designate your own folders, used as-is.',
    'Dossier de destination des bathymétries assemblées'
        : 'Destination folder for assembled bathymetry files',
    'Dossier de vos bathymétries sources (.tif, .asc…)'
        : 'Folder holding your source bathymetry files (.tif, .asc…)',
    'Dossier enregistré.'
        : 'Folder saved.',
    'Emplacement TIFF / assemble'
        : 'TIFF / assemble location',
    'Ouvrez le dossier « Bathymétrie » de votre structure.'
        : 'Open the « Bathymetry » folder of your structure.',
    'Ouvrir la racine Bathymétrie'
        : 'Open the Bathymetry root',
    "Où créer l'organisation des bathymétries"
        : 'Where to create the bathymetry data structure',
    'Si vos bathymétries sont sur un disque externe,'
        : 'If your bathymetry data is on an external drive,',
    'Structure créée.\n\nDéposez vos bathymétries dans :\n{d}\n\nFormat requis : EPSG:4326.'
        : 'Structure created.\n\nDrop your bathymetry files into:\n{d}\n\nRequired format: EPSG:4326.',
    'custom_bathy_dem non écrit :'
        : 'custom_bathy_dem not written:',
    'custom_bathy_dem renseigné dans le cfg de la tuile.'
        : 'custom_bathy_dem set in the tile cfg.',

    # ── .comb MODULE + ADVANCED MENU (project additions) ───────────
    "Ortho4XP — Avancé"                     : "Ortho4XP — Advanced",
    "Outils avancés"                        : "Advanced tools",
    "Chaque outil s'ouvre dans sa propre fenêtre." : "Each tool opens in its own window.",
    "Générer un fichier .comb"              : "Generate a .comb file",
    "JOSM / Extents (masques, zones)"       : "JOSM / Extents (masks, zones)",
    "Altimétrie"                            : "Elevation",
    "Correction imagerie"                   : "Imagery correction",
    "Fermer"                                : "Close",
    "Générer un .comb global (style EUR.comb)" : "Generate a global .comb (EUR.comb style)",
    "Coche les providers, choisis zone + priorité, puis Générer." : "Tick providers, set zone + priority, then Generate.",
    "Provider"                              : "Provider",
    "Score"                                 : "Score",
    "Zone / extent"                         : "Zone / extent",
    "Priorité"                              : "Priority",
    "Automatique"                           : "Automatic",
    "Importer un .comb"                     : "Import a .comb",
    "Créer un provider (.lay)"              : "Create a provider (.lay)",
    "Aperçu"                                : "Preview",
    "Générer"                               : "Generate",
    "Nom du fichier :"                      : "File name:",
    "🛠 Avancé"                              : "🛠 Advanced",
    "haute"                                 : "high",
    "moyenne"                               : "medium",
    "basse"                                 : "low",


    "lay_win_title"      : "Provider generator (.lay)",
    "lay_active_tile"    : "Active tile:",
    "lay_provider_name"  : "Provider name",
    "lay_request_type"   : "Request type",
    "lay_url_prefix"     : "url_prefix (WMS)",
    "lay_url_template"   : "url_template (TMS)",
    "lay_layers"         : "layers (WMS)",
    "lay_in_gui"         : "Show in menu (in_GUI)",
    "lay_preview_label"  : "Preview of the .lay file to be generated",
    "lay_btn_pcrs"       : "Preset PCRS_IGN",
    "lay_btn_ign"        : "Preset IGN Ortho",
    "lay_btn_load"       : "Load a .lay",
    "lay_btn_clear"      : "Clear",
    "lay_btn_create"     : "Create the .lay",
    "lay_msg_name_req"   : "Provider name is required.",
    "lay_msg_created"    : "File created:",
    "lay_msg_restart"    : "Close and restart Ortho4XP so the new imagery appears in the Imagery menu.",
    # ── RELIEF SONNY (module altimétrie auto) ──────────────────────
    "Aucun .hgt en place après décompression."          : "No .hgt in place after extraction.",
    "Aucun .hgt valide dans ce ZIP."                    : "No valid .hgt in this ZIP.",
    "Aucun emplacement de relief valide.\n\n"           : "No valid relief location.\n\n",
    "Ce disque ne dispose que de %.1f Go "              : "This disk only has %.1f GB ",
    "cfg application non mis à jour : "                 : "app cfg not updated: ",
    "Choisissez le disque ou le dossier où créer votre " : "Choose the disk or folder where to create your ",
    "custom_dem renseigné aussi dans le cfg application." : "custom_dem also set in the app cfg.",
    "Décompression dans %s…"                            : "Extracting into %s…",
    "Dépôt Sonny indisponible (%s)."                    : "Sonny storage unavailable (%s).",
    "Disque où STOCKER le relief (rien à chercher "     : "Disk to STORE the relief (nothing to look for ",
    "Emplacement relief déjà défini : %s"               : "Relief location already set: %s",
    "Espace disque limité"                              : "Limited disk space",
    "Étape 1 sur 2 — Emplacement de stockage"           : "Step 1 of 2 — Storage location",
    "Étape 2 sur 2 — Téléchargement"                    : "Step 2 of 2 — Download",
    "Hors zone Sonny : relief standard."                : "Outside Sonny coverage: standard relief.",
    "Import annulé : aucun ZIP trouvé."                 : "Import cancelled: no ZIP found.",
    "Import du relief"                                  : "Relief import",
    "Import Sonny : modules absents (%s)."              : "Sonny import: missing modules (%s).",
    "Import Sonny : tuile courante illisible."          : "Sonny import: current tile unreadable.",
    "Installer le ZIP téléchargé"                       : "Install the downloaded ZIP",
    "L'emplacement du relief défini précédemment est "  : "The previously set relief location is ",
    "Le site Sonny va s'ouvrir.\n\n"                    : "The Sonny website will open.\n\n",
    "Relief haute définition"                           : "High-definition relief",
    "Relief HD intégré."                                : "HD relief integrated.",
    "Relief installé"                                   : "Relief installed",
    "Relief rangé dans :\n%s\n\n"                       : "Relief stored in:\n%s\n\n",
    "Relief Sonny : modules absents (%s)."              : "Sonny relief: missing modules (%s).",
    "Relief Sonny : tuile courante illisible."          : "Sonny relief: current tile unreadable.",
    "Relief Sonny automatique"                          : "Automatic Sonny relief",
    "Relief Sonny déjà installé pour cette tuile : %s"  : "Sonny relief already installed for this tile: %s",
    "Relief Sonny indisponible : relief standard."      : "Sonny relief unavailable: standard relief.",
    "Relief Sonny intégré : %d dalle(s)."               : "Sonny relief integrated: %d tile(s).",
    "Relief Sonny prêt."                                : "Sonny relief ready.",
    "Relief standard conservé."                         : "Standard relief kept.",
    "Sélectionnez le fichier ZIP Sonny (%s.zip)"        : "Select the Sonny ZIP file (%s.zip)",
    "Si vos altimétries sont sur un disque externe,"    : "If your elevation data is on an external disk,",
    "Téléchargez %s puis « Importer le relief téléchargé »." : "Download %s then \"Install the downloaded ZIP\".",
    "Un relief haute définition (Sonny) est disponible pour " : "A high-definition relief (Sonny) is available for ",
}
