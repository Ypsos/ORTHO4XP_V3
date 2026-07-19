[![ORTHO4XP V3 Banner](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/BanniereGithub.png)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/BanniereGithub.png)

**[🇫🇷 Français](#ortho4xp-v3)  |  [🇬🇧 English](#ortho4xp-v3-english)**

# ORTHO4XP V3

**La version moderne d'Ortho4XP**
Installation automatique • Sans terminal • Pour X-Plane 12

[![TÉLÉCHARGER LA DERNIÈRE VERSION](https://img.shields.io/badge/T%C3%89L%C3%89CHARGER%20LA%20DERNI%C3%88RE%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 🧭 Origine du projet

|  |  |
| --- | --- |
| **Logiciel original** | Créé par Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Version 1.40 maintenue** | Fork par Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **Cette V3** | Refonte complète par **Roland (Ypsos)** avec **Claude (Anthropic AI)** |

En mars 2026, j'ai contacté Oscar Pilote et la communauté (Issue GitHub #299, Topic X-Plane.org).
Réponse : *« Tu fais ce que tu veux, tu es libre »*.
Cet espace a été créé afin que la version V3 soit **claire, indépendante et accessible à tous**.

---

## 🎯 L'idée directrice

Ortho4XP est un outil puissant, mais son accès a longtemps été réservé à ceux qui acceptaient d'ouvrir un terminal, d'installer Python à la main et de modifier des fichiers de configuration.

La V3 ne change pas le moteur : elle **enlève les barrières**. Installation en un clic, interface complète, et surtout des outils qui rendent accessibles des opérations autrefois réservées aux initiés — retouche des textures, gestion de l'altimétrie, édition des données OSM dans JOSM, préparation des données géographiques dans QGIS.

L'objectif est simple : **un simmer doit pouvoir fabriquer ses tuiles sans jamais écrire une ligne de code.**

---

## ⚡ Tableau comparatif — V1.40 vs V3

| Fonctionnalité | Ortho4XP 1.40 (Shred86) | **Ortho4XP V3 (Roland)** |
| --- | --- | --- |
| **Installation** | Scripts bash/bat manuels dans le terminal | ✅ Launcher graphique — 1 clic, aucun terminal |
| **Python** | Non géré automatiquement | ✅ Python 3.12 détecté et installé automatiquement |
| **Environnement** | Dépendances sur le système hôte | ✅ Environnement isolé `venv/` — système intact |
| **Compatibilité** | macOS Intel, Windows | ✅ Apple Silicon M1–M4, Intel, Windows 10/11, Linux |
| **Performance** | Python 3.x standard | ✅ Python 3.12 — 15 à 20 % plus rapide sur les calculs mesh |
| **Détection matériel** | Manuelle | ✅ Sentinelle CPU/RAM — slots sécurisés automatiques |
| **Lancement** | Terminal obligatoire | ✅ Lanceur natif `.app` / `.vbs` / `.desktop` |
| **Interface** | Fenêtre standard | ✅ Interface adaptée 4K — polices agrandies automatiquement |
| **GDAL / rasterio** | osgeo.gdal (dépendance système) | ✅ `rasterio` dans venv — 100 % autonome |
| **Transparence eau XP12** | Non géré — tuiles BC1 opaques | ✅ Transparence native XP12 — textures BC3 avec canal alpha |
| **Patches mer photoréalistes** | Absent | ✅ Générateur intégré — mer conforme aux orthophotos, sans damier bleu ni triangles transparents |
| **Providers / Zoomlevel mer** | — | ✅ Compatible tout provider (BI, Esri, IGN…) et tout niveau de zoom sélectionné |
| **Color Normalize** | Absent | ✅ Correction colorimétrique automatique vers sRGB neutre |
| **Color Check** | Absent | ✅ Interface de vérification et correction des couleurs |
| **Correction d'imagerie** | Aucune | ✅ Module dédié — visualisation des DDS de la tuile, sélection, retouche externe (GIMP…), retéléchargement ciblé |
| **Altimétrie / DEM** | Configuration manuelle | ✅ Module dédié — structure de dossiers créée automatiquement, préparation des fichiers (reprojection, réduction) |
| **Édition OSM (JOSM)** | Manipulation manuelle des fichiers | ✅ Module **Avancé** — JOSM détecté et lancé automatiquement, fichiers créés, protégés et rangés au bon endroit |
| **Emprises / Extents** | Écriture manuelle des `.ext` | ✅ Dessin de l'emprise dans JOSM → publication automatique en `.ext` + archive OSM |
| **Nivellement / Aéroports** | Patches à écrire à la main | ✅ Modèles générés automatiquement, code OACI lu dans les données de la tuile |
| **QGIS** | — | ✅ Intégration prévue pour la préparation et le contrôle des données géographiques |
| **Previews** | Basique | ✅ Outil Previews avec curseurs et configuration visuelle |
| **Console de log** | Fenêtre figée | ✅ Barre de défilement + navigation clavier (flèches, Page préc./suiv.) |
| **Robustesse réseau** | Échec sur serveur occupé | ✅ Rotation des serveurs Overpass, reprise auto, gestion des dalles blanches |
| **Langues** | Anglais | ✅ Interface complète français et anglais |
| **Portabilité** | Lié au système | ✅ Dossier autonome — déplaçable sur disque externe |
| **Validation XP12** | Non testée spécifiquement | ✅ Tuiles produites et validées dans X-Plane 12 |

---

## 🚀 Les points forts

- 📦 **Zéro Terminal** — Installation, lancement et mises à jour entièrement automatisés
- 🖱️ **Accessibilité** — Conçu pour les simmers qui veulent créer leurs tuiles sans manipuler de code
- 🛠️ **Fiabilité** — Base solide 1.40, optimisations modernes, environnement Python isolé
- 🌊 **Eau photoréaliste XP12** — Générateur de patches mer intégré : une mer conforme aux orthophotos, sans damier bleu ni triangles transparents, quel que soit le provider et le niveau de zoom
- 🎨 **Colorimétrie avancée** — Normalisation sRGB, contrôle visuel et correction par tuile
- 🖼️ **Correction d'imagerie** — Visualisation des textures de la tuile, retouche dans l'éditeur de votre choix, regénération ciblée
- ⛰️ **Altimétrie assistée** — Structure de dossiers, préparation et conversion des données DEM
- 🗺️ **JOSM et QGIS intégrés** — Édition des données géographiques depuis l'interface, sans jamais toucher à un chemin de fichier
- 🌐 **Téléchargements plus fiables** — Rotation automatique des serveurs de données et reprise après incident
- 🖥️ **Console lisible** — Défilement à la souris et navigation au clavier dans le journal de traitement
- 🌍 **Bilingue** — Interface complète en français et en anglais

---

## 🗺️ Le module Avancé — JOSM et QGIS

C'est la nouveauté majeure de cette mise à jour. Un bouton **🛠 Avancé (JOSM)** ouvre une fenêtre qui prend en charge, de bout en bout, les travaux d'édition géographique qui demandaient jusqu'ici de connaître l'arborescence d'Ortho4XP par cœur.

### Ce que le module fait à votre place

| Vous voulez… | Le module s'occupe de… |
| --- | --- |
| **Définir une emprise de provider** | Créer le fichier d'édition, ouvrir JOSM dessus, puis **publier automatiquement** l'emprise au format attendu par Ortho4XP (`.ext` + archive OSM) |
| **Niveler un terrain** | Générer le patch de la tuile avec le bon tag d'altitude, au bon emplacement |
| **Corriger un aéroport ou une piste** | Lire le **code OACI** directement dans les données de la tuile et nommer le patch correctement — un nom erroné rendrait le patch silencieusement inopérant |
| **Modifier les données OSM** | Proposer un bouton par couche réellement présente (eau, trait de côte, aéroports, routes) |

### Les sécurités intégrées

- **Sauvegarde automatique** avant toute ouverture : l'original de chaque couche est conservé hors du dossier de tuile, là où le nettoyage de l'interface ne peut pas l'effacer.
- **Restauration en un clic** de la version d'origine ou de votre version modifiée.
- **Envoi vers OpenStreetMap bloqué** : tous les fichiers créés portent le marqueur qui empêche JOSM de téléverser vos essais sur les serveurs publics.
- **Récupération des fichiers égarés** : si un fichier a été enregistré au mauvais endroit, le module le repère et le remet en place.
- **Lancement de JOSM automatique** sur macOS, Windows et Linux, avec détection du Remote Control et repli si l'application est déjà ouverte.

### QGIS

Le cadre **QGIS** est en place dans l'interface, aux côtés de GIMP et de JOSM, pour la préparation et le contrôle des données géographiques (altimétrie, emprises, vérification des couches). Son intégration se poursuit.

> ℹ️ **JOSM et QGIS ne sont pas fournis** avec Ortho4XP V3. Vous devez les installer depuis leurs sites officiels ; l'interface vous guide et détecte ensuite l'application automatiquement.

---

## 🖥️ Interfaces graphiques

### Installation et Lanceur

[![Lanceur Ortho4XP V3 — installation](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)

<img width="1826" height="1936" alt="Lanceur" src="https://github.com/user-attachments/assets/b678f804-cff4-4cdb-86f2-a6a794e3ac79" />

### Interface principale et Color Check

<img width="2644" height="796" alt="Interface principale" src="https://github.com/user-attachments/assets/fb49ffbb-3bc8-466c-a32d-622aaecdf3db" />

[![Color Check](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/04_Color%20Check_01.jpeg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/04_Color%20Check_01.jpeg)

### Correction d'imagerie — visualisation des textures de la tuile

<img width="1916" height="1816" alt="Correction Visualisation5" src="https://github.com/user-attachments/assets/687af058-4b87-4a36-8dad-2aee3239d82c" />

Fenêtre de sélection des textures à modifier

<img width="1316" height="1152" alt="Correction Visualisation2" src="https://github.com/user-attachments/assets/f652075c-ed0e-4ff0-a655-18ecada7901d" />

Choix de l'application de retouche d'image (exemple : GIMP)

<img width="1610" height="462" alt="Correction Visualisation6" src="https://github.com/user-attachments/assets/3f650975-a479-4f39-ba3f-f30a51dd1d1e" />

### Altimétrie — gestion des données et structure de dossiers

<img width="1598" height="320" alt="Altimétrie 1" src="https://github.com/user-attachments/assets/e2d810d0-5557-404e-80e4-bada1680db86" />

<img width="1162" height="160" alt="Altimétrie 2" src="https://github.com/user-attachments/assets/e5e8ca06-43a8-4efe-b216-1411f7632c7e" />

### Module Avancé — édition JOSM avec sauvegarde sécurisée

<img width="1650" height="1356" alt="Josm 2" src="https://github.com/user-attachments/assets/b7e6e635-e09d-4096-b99a-b65fa5bb9dbf" />

<img width="848" height="564" alt="Josm 3" src="https://github.com/user-attachments/assets/1f984c4d-2f28-4df1-94d7-5cc0ac5dd955" />

---

## 🛠 Utilisation rapide

### 🍎 Mac

> **⚠️ Étape obligatoire avant tout** — Téléchargez d'abord le lanceur pré-nettoyé (sans blocage Gatekeeper) : **[⬇️ Télécharger le lanceur Mac pré-installé](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)**

1. Téléchargez l'archive principale **ORTHO4XP_V3** (bouton vert « Code » → « Download ZIP »)
2. Décompressez l'archive — renommez le dossier en `ORTHO4XP_V3`
3. Téléchargez le ZIP de la Release ci-dessus et extrayez `Lanceur_Installation_Prerequis.app` directement dans le dossier `ORTHO4XP_V3`
4. Placez le dossier `ORTHO4XP_V3` dans votre dossier **`Applications`** (`/Users/votre_nom/Applications/`)
5. Double-cliquez sur `Lanceur_Installation_Prerequis.app`

---

### 🪟 Windows

1. Téléchargez l'archive principale **ORTHO4XP_V3** et décompressez
2. Double-cliquez sur `LANCEUR_INSTALL_WINDOWS.bat`

---

### 🐧 Linux

1. Téléchargez l'archive principale **ORTHO4XP_V3** et décompressez
2. Double-cliquez sur `LANCEUR_INSTALL_LINUX.sh`

---

## 🤝 Remerciements

Ce projet avance grâce à la communauté. Merci en particulier à **Jojo**, référence technique sur Ortho4XP, QGIS et JOSM, dont les explications ont permis de comprendre le fonctionnement réel des emprises, des patches et des codes OACI ; et à **Cricri**, pour les tests et validations sous Windows et Linux, sans lesquels la compatibilité multiplateforme resterait une hypothèse.

Merci également à tous ceux qui remontent leurs retours sur les forums : chaque rapport précis fait gagner des heures.

---

## 📜 Crédits

|  |  |
| --- | --- |
| **Concept & Design** | Roland (Ypsos) |
| **Codage & Support** | Claude (Anthropic AI) |
| **Travaux originaux** | Oscar Pilote (Ortho4XP) |
| **Adaptation 1.40** | Shred86 |
| **Référence technique** | Jojo |
| **Tests Windows / Linux** | Cricri |
| **Documentation** | English wiki : <https://xpconnect.me/ortho4xp/> |

---

## ⚠️ Licence

Distribué sous **GNU GPL v3** dans le respect de la licence du projet original.
Voir `AVERTISSEMENT_LICENCE_LEGAL.md` pour les détails complets.

JOSM, QGIS et GIMP sont des logiciels tiers indépendants, distribués sous leurs propres licences.

---
---

# ORTHO4XP V3 (English)

**The modern version of Ortho4XP**
Automatic installation • No terminal • For X-Plane 12

[![DOWNLOAD LATEST VERSION](https://img.shields.io/badge/DOWNLOAD%20LATEST%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 🧭 Project origin

|  |  |
| --- | --- |
| **Original software** | Created by Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Maintained 1.40 version** | Fork by Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **This V3** | Complete rework by **Roland (Ypsos)** with **Claude (Anthropic AI)** |

In March 2026, I contacted Oscar Pilote and the community (GitHub Issue #299, X-Plane.org topic).
Answer: *"Do whatever you want, you are free"*.
This space was created so that the V3 version is **clear, independent and accessible to everyone**.

---

## 🎯 The guiding idea

Ortho4XP is a powerful tool, but for a long time it was only within reach of those willing to open a terminal, install Python by hand and edit configuration files.

V3 does not change the engine: it **removes the barriers**. One-click installation, a complete interface, and above all tools that open up operations previously reserved for experts — texture retouching, elevation data management, OSM editing in JOSM, geographic data preparation in QGIS.

The goal is simple: **a simmer should be able to build tiles without ever writing a line of code.**

---

## ⚡ Comparison table — V1.40 vs V3

| Feature | Ortho4XP 1.40 (Shred86) | **Ortho4XP V3 (Roland)** |
| --- | --- | --- |
| **Installation** | Manual bash/bat scripts in the terminal | ✅ Graphical launcher — 1 click, no terminal |
| **Python** | Not managed automatically | ✅ Python 3.12 detected and installed automatically |
| **Environment** | Dependencies on the host system | ✅ Isolated `venv/` environment — system untouched |
| **Compatibility** | macOS Intel, Windows | ✅ Apple Silicon M1–M4, Intel, Windows 10/11, Linux |
| **Performance** | Standard Python 3.x | ✅ Python 3.12 — 15 to 20 % faster on mesh computations |
| **Hardware detection** | Manual | ✅ CPU/RAM sentinel — automatic safe slots |
| **Launch** | Terminal required | ✅ Native launcher `.app` / `.vbs` / `.desktop` |
| **Interface** | Standard window | ✅ 4K-ready interface — fonts enlarged automatically |
| **GDAL / rasterio** | osgeo.gdal (system dependency) | ✅ `rasterio` inside venv — 100 % self-contained |
| **XP12 water transparency** | Not handled — opaque BC1 tiles | ✅ Native XP12 transparency — BC3 textures with alpha channel |
| **Photorealistic sea patches** | Absent | ✅ Built-in generator — sea matching the orthophotos, no blue checkerboard, no transparent triangles |
| **Sea providers / Zoom level** | — | ✅ Works with any provider (BI, Esri, IGN…) and any selected zoom level |
| **Color Normalize** | Absent | ✅ Automatic color correction toward neutral sRGB |
| **Color Check** | Absent | ✅ Color verification and correction interface |
| **Imagery correction** | None | ✅ Dedicated module — view the tile textures, select them, retouch in an external editor (GIMP…), targeted re-download |
| **Elevation / DEM** | Manual configuration | ✅ Dedicated module — folder structure created automatically, file preparation (reprojection, downsampling) |
| **OSM editing (JOSM)** | Manual file handling | ✅ **Advanced** module — JOSM detected and launched automatically, files created, protected and filed in the right place |
| **Extents** | `.ext` files written by hand | ✅ Draw the extent in JOSM → automatic publication as `.ext` + OSM archive |
| **Flattening / Airports** | Patches written by hand | ✅ Templates generated automatically, ICAO code read from the tile data |
| **QGIS** | — | ✅ Integration under way for geographic data preparation and checking |
| **Previews** | Basic | ✅ Previews tool with sliders and visual configuration |
| **Log console** | Frozen window | ✅ Scrollbar + keyboard navigation (arrows, Page up/down) |
| **Network robustness** | Failure on busy server | ✅ Overpass server rotation, auto retry, white-tile handling |
| **Languages** | English | ✅ Full French and English interface |
| **Portability** | Tied to the system | ✅ Self-contained folder — movable to an external drive |
| **XP12 validation** | Not specifically tested | ✅ Tiles produced and validated in X-Plane 12 |

---

## 🚀 Highlights

- 📦 **Zero Terminal** — Fully automated installation, launch and updates
- 🖱️ **Accessibility** — Designed for simmers who want to create their tiles without touching any code
- 🛠️ **Reliability** — Solid 1.40 base, modern optimizations, isolated Python environment
- 🌊 **Photorealistic XP12 water** — Built-in sea patch generator: sea matching the orthophotos, no blue checkerboard, no transparent triangles, whatever the provider and zoom level
- 🎨 **Advanced colorimetry** — sRGB normalization, visual checking and per-tile correction
- 🖼️ **Imagery correction** — View the tile textures, retouch them in the editor of your choice, regenerate only what you changed
- ⛰️ **Assisted elevation workflow** — Folder structure, preparation and conversion of DEM data
- 🗺️ **JOSM and QGIS built in** — Edit geographic data from the interface, without ever dealing with a file path
- 🌐 **More reliable downloads** — Automatic data-server rotation and recovery after an incident
- 🖥️ **Readable console** — Mouse scrolling and keyboard navigation in the processing log
- 🌍 **Bilingual** — Complete interface in French and English

---

## 🗺️ The Advanced module — JOSM and QGIS

This is the main addition in this update. A **🛠 Advanced (JOSM)** button opens a window that handles, from start to finish, the geographic editing tasks that until now required knowing the Ortho4XP folder tree by heart.

### What the module does for you

| You want to… | The module takes care of… |
| --- | --- |
| **Define a provider extent** | Creating the editing file, opening JOSM on it, then **automatically publishing** the extent in the format Ortho4XP expects (`.ext` + OSM archive) |
| **Flatten terrain** | Generating the tile patch with the correct altitude tag, in the correct location |
| **Fix an airport or a runway** | Reading the **ICAO code** directly from the tile data and naming the patch correctly — a wrong name would silently disable the patch |
| **Edit OSM data** | Offering one button per layer actually present (water, coastline, airports, roads) |

### Built-in safeguards

- **Automatic backup** before anything is opened: the original of each layer is kept outside the tile folder, where the interface cleanup cannot delete it.
- **One-click restore** of either the original version or your modified version.
- **Upload to OpenStreetMap blocked**: every generated file carries the flag that prevents JOSM from uploading your experiments to the public servers.
- **Stray file recovery**: if a file was saved in the wrong place, the module finds it and puts it back.
- **Automatic JOSM launch** on macOS, Windows and Linux, with Remote Control detection and a fallback when the application is already running.

### QGIS

The **QGIS** panel is in place in the interface, next to GIMP and JOSM, for preparing and checking geographic data (elevation, extents, layer verification). Its integration is ongoing.

> ℹ️ **JOSM and QGIS are not bundled** with Ortho4XP V3. Install them from their official websites; the interface then guides you and detects the application automatically.

---

## 🖥️ Graphical interfaces

### Installation and Launcher

[![Ortho4XP V3 Launcher — installation](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)

<img width="1826" height="1936" alt="Launcher" src="https://github.com/user-attachments/assets/b678f804-cff4-4cdb-86f2-a6a794e3ac79" />

### Main interface and Color Check

<img width="2644" height="796" alt="Main interface" src="https://github.com/user-attachments/assets/fb49ffbb-3bc8-466c-a32d-622aaecdf3db" />

[![Color Check](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/04_Color%20Check_01.jpeg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/04_Color%20Check_01.jpeg)

### Imagery correction — viewing the tile textures

<img width="1916" height="1816" alt="Correction view 5" src="https://github.com/user-attachments/assets/687af058-4b87-4a36-8dad-2aee3239d82c" />

Selecting the textures to edit

<img width="1316" height="1152" alt="Correction view 2" src="https://github.com/user-attachments/assets/f652075c-ed0e-4ff0-a655-18ecada7901d" />

Choosing the image editor (example: GIMP)

<img width="1610" height="462" alt="Correction view 6" src="https://github.com/user-attachments/assets/3f650975-a479-4f39-ba3f-f30a51dd1d1e" />

### Elevation — data management and folder structure

<img width="1598" height="320" alt="Elevation 1" src="https://github.com/user-attachments/assets/e2d810d0-5557-404e-80e4-bada1680db86" />

<img width="1162" height="160" alt="Elevation 2" src="https://github.com/user-attachments/assets/e5e8ca06-43a8-4efe-b216-1411f7632c7e" />

### Advanced module — JOSM editing with protected backups

<img width="1650" height="1356" alt="Josm 2" src="https://github.com/user-attachments/assets/b7e6e635-e09d-4096-b99a-b65fa5bb9dbf" />

<img width="848" height="564" alt="Josm 3" src="https://github.com/user-attachments/assets/1f984c4d-2f28-4df1-94d7-5cc0ac5dd955" />

---

## 🛠 Quick start

### 🍎 Mac

> **⚠️ Mandatory first step** — First download the pre-cleaned launcher (no Gatekeeper block): **[⬇️ Download the pre-installed Mac launcher](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)**

1. Download the main archive **ORTHO4XP_V3** (green "Code" button → "Download ZIP")
2. Unzip the archive — rename the folder to `ORTHO4XP_V3`
3. Download the Release ZIP above and extract `Lanceur_Installation_Prerequis.app` directly into the `ORTHO4XP_V3` folder
4. Place the `ORTHO4XP_V3` folder into your **`Applications`** folder (`/Users/your_name/Applications/`)
5. Double-click `Lanceur_Installation_Prerequis.app`

---

### 🪟 Windows

1. Download the main archive **ORTHO4XP_V3** and unzip
2. Double-click `LANCEUR_INSTALL_WINDOWS.bat`

---

### 🐧 Linux

1. Download the main archive **ORTHO4XP_V3** and unzip
2. Double-click `LANCEUR_INSTALL_LINUX.sh`

---

## 🤝 Acknowledgements

This project moves forward thanks to the community. Special thanks to **Jojo**, the technical reference on Ortho4XP, QGIS and JOSM, whose explanations made it possible to understand how extents, patches and ICAO codes actually work; and to **Cricri**, for testing and validating on Windows and Linux, without whom cross-platform compatibility would remain a theory.

Thanks as well to everyone posting feedback on the forums: every precise report saves hours of work.

---

## 📜 Credits

|  |  |
| --- | --- |
| **Concept & Design** | Roland (Ypsos) |
| **Coding & Support** | Claude (Anthropic AI) |
| **Original work** | Oscar Pilote (Ortho4XP) |
| **1.40 adaptation** | Shred86 |
| **Technical reference** | Jojo |
| **Windows / Linux testing** | Cricri |
| **Documentation** | English wiki: <https://xpconnect.me/ortho4xp/> |

---

## ⚠️ License

Distributed under **GNU GPL v3** in accordance with the license of the original project.
See `AVERTISSEMENT_LICENCE_LEGAL.md` for full details.

JOSM, QGIS and GIMP are independent third-party applications, distributed under their own licenses.
