# 📜 ORTHO4XP — HISTORIQUE ET MODULES

Développement : Roland (Ypsos) — assisté de Claude (IA, Anthropic) comme outil.
Basé sur Ortho4XP (Oscar Pilote) → version 1.40 (Shred86) → V2 / V3 / V4.

> 💡 Ce fichier peut être complété librement à chaque nouvelle version, sans
> toucher au code : ouvrez-le dans TextEdit (format texte), ajoutez vos lignes,
> enregistrez. Le bouton « Historique » du lanceur l'affiche automatiquement.

---

## 🆕 NOUVEAUTÉS PAR VERSION

### V4.0
- (à compléter)

### V3.x
- Module Avancé (JOSM / QGIS) : édition géographique automatisée
- Module Altimétrie : procédure QGIS de 41 étapes réduite à un bouton
- Pipeline mer photoréaliste : fin du damier bleu et des triangles transparents
- Correction colorimétrique adaptée au niveau de zoom (HDR X-Plane 12)
- Notation automatique de la qualité des providers
- Surveillance mémoire en temps réel

### V2.x
- Refonte de l'écosystème autour du moteur d'origine préservé
- Lanceur graphique, installation en un clic, sans terminal
- Interface bilingue français / anglais

---

## 🧩 MODULES DÉVELOPPÉS POUR LA V3

### Altimétrie / Bathymétrie
- O4_Altimetrie_Utils.py — gestion DEM, structure de dossiers, conversion
- O4_Bathymetrie_Utils.py — données bathymétriques

### Pipeline mer / Matériaux X-Plane 12
- O4_Sea_Texture.py — génération des patches mer conformes aux orthophotos
- O4_XP12_Materials.py — matériaux et transparence native XP12

### Gestion couleur
- O4_Color_Apply.py — application des corrections au bon moment de la chaîne
- O4_Color_Check.py — interface de vérification et correction des couleurs
- O4_Color_Normalize.py — normalisation vers un sRGB neutre

### Abstraction et notation des providers
- O4_Provider_Abstraction.py — couche d'abstraction des fournisseurs d'imagerie
- O4_Provider_Score.py — notation qualité (bruit, nuages, dérive, jointure)
- O4_Score_Logger.py — journalisation des scores

### Architecture V3
- O4_EventBus.py — bus d'événements interne
- O4_Dependency.py — gestion des dépendances entre tuiles
- O4_Memory_Manager.py — surveillance mémoire et nettoyage cache
- O4_Theme_Manager.py — thèmes d'interface personnalisables
- O4_Build_Transaction.py — écriture sécurisée des fichiers
- O4_Benchmark.py — mesures de performance

### Multilingue
- O4_Lang.py — moteur de traduction
- O4_Lang_FR.py — textes français
- O4_Lang_EN.py — textes anglais

### Correction / Outils avancés
- O4_Correction_Utils.py — correction d'imagerie et visualisation des textures
- O4_Avance_Utils.py — module Avancé (JOSM, emprises, aéroports)
- O4_PBF_Utils.py — traitement des données OSM au format PBF
- rge_download.py — téléchargement de données RGE

### Lanceur et installation
- Ortho4XP_Launcher.py — lanceur graphique multiplateforme
- INSTALL_PREREQUIS.py — installation automatique des prérequis
- create_launcher_prerequis.py — génération des lanceurs natifs

---

## 🔧 FICHIERS D'ORIGINE FORTEMENT RETRAVAILLÉS

Fichiers de l'Ortho4XP original, modifiés de façon substantielle pour la V3
(les mentions d'Oscar Pilote et de Shred86 sont conservées, GPL v3) :

- O4_GUI_Utils.py — interface principale (très largement étendue)
- O4_Tile_Utils.py — gestion des tuiles (très largement étendue)
- O4_Imagery_Utils.py — assemblage de l'imagerie
- O4_Config_Utils.py — configuration
- O4_File_Names.py, O4_Bathymetry.py, O4_Airport_Utils.py, O4_DEM_Utils.py,
  O4_OSM_Utils.py, O4_Mask_Utils.py, O4_DSF_Utils.py, O4_Mesh_Utils.py, etc.

---

_Ortho4XP est un logiciel libre sous licence GNU GPL v3._
