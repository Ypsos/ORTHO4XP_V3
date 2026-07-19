[![ORTHO4XP V3 Banner](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/BanniereGithub.png)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/BanniereGithub.png)

**[🇫🇷 Français](#ortho4xp-v30)  |  [🇬🇧 English](#ortho4xp-v30-english)**

# ORTHO4XP V3.0

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

## ⚡ Tableau comparatif — V1.40 vs V3

| Fonctionnalité | Ortho4XP 1.40 (Shred86) | **Ortho4XP V3 (Roland)** |
| --- | --- | --- |
| **Installation** | Scripts bash/bat manuels dans le terminal | ✅ Launcher graphique — 1 clic, aucun terminal |
| **Python** | Non géré automatiquement | ✅ Python 3.12 détecté et installé automatiquement |
| **Environnement** | Dépendances sur le système hôte | ✅ Environnement isolé `venv/` — système intact |
| **Compatibilité** | macOS Intel, Windows | ✅ Apple Silicon M1–M4, Intel, Windows 10/11, Linux |
| **Performance** | Python 3.x standard | ✅ Python 3.12 — 15 à 20% plus rapide sur les calculs mesh |
| **Détection matériel** | Manuelle | ✅ Sentinelle CPU/RAM — slots sécurisés automatiques |
| **Lancement** | Terminal obligatoire | ✅ Lanceur natif `.app` / `.vbs` / `.desktop` |
| **Interface** | Fenêtre standard | ✅ Interface adaptée 4K — polices agrandies automatiquement |
| **GDAL / rasterio** | osgeo.gdal (dépendance système) | ✅ `rasterio` dans venv — 100% autonome |
| **Transparence eau XP12** | Non géré — tuiles BC1 opaques | ✅ Transparence native XP12 — textures BC3 avec canal alpha |
| **Patches mer photoréalistes** | Absent | ✅ Générateur intégré — mer conforme aux orthophotos, sans damier bleu ni triangles transparents |
| **Providers / Zoomlevel mer** | — | ✅ Compatible tout provider (BI, Esri, IGN…) et tout niveau de zoom sélectionné |
| **Color Normalize** | Absent | ✅ Correction colorimétrique automatique vers sRGB neutre |
| **Color Check** | Absent | ✅ Interface de vérification et correction des couleurs |
| **Previews** | Basique | ✅ Outil Previews avec curseurs et configuration visuelle |
| **Console de log** | Fenêtre figée | ✅ Barre de défilement + navigation clavier (flèches, Page préc./suiv.) |
| **Robustesse réseau** | Échec sur serveur occupé | ✅ Rotation des serveurs Overpass, reprise auto, gestion des dalles blanches |
| **Portabilité** | Lié au système | ✅ Dossier autonome — déplaçable sur disque externe |
| **Validation XP12** | Non testée spécifiquement | ✅ Tuiles produites et validées dans X-Plane 12 |

---

## 🚀 Pourquoi ORTHO4XP V3 ?

L'objectif est de lever définitivement la barrière technique du terminal. Cette version simplifie radicalement l'expérience utilisateur tout en conservant la puissance de l'outil original.

### ✨ Les points forts

- 📦 **Zéro Terminal** — Installation et lancement entièrement automatisés
- 🖱️ **Accessibilité** — Conçu pour les simmers qui veulent créer leurs tuiles sans manipuler de code
- 🛠️ **Fiabilité** — Base solide 1.40 avec optimisations modernes et environnement Python isolé
- 🌊 **Eau photoréaliste XP12** — Générateur de patches mer intégré : une mer conforme aux orthophotos, sans damier bleu ni triangles transparents, quel que soit le provider et le niveau de zoom
- 🎨 **Colorimétrie avancée** — Normalisation sRGB et correction visuelle par tuile
- 🌐 **Téléchargements plus fiables** — Rotation automatique des serveurs de données et reprise après incident
- 🖥️ **Console lisible** — Défilement à la souris et navigation au clavier dans le journal de traitement

---

## 🖥️ Interfaces graphiques V3.0

### Installation et Lanceur

[![Lanceur Ortho4XP V3 — installation](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)

[![Lanceur Ortho4XP V3]<img width="1826" height="1936" alt="Lanceur" src="https://github.com/user-attachments/assets/b678f804-cff4-4cdb-86f2-a6a794e3ac79" />


### Interface principale et Color Check

[![Interface principale]<img width="2644" height="796" alt="Interface principale" src="https://github.com/user-attachments/assets/fb49ffbb-3bc8-466c-a32d-622aaecdf3db" />


[![Color Check](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/04_Color%20Check_01.jpeg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/04_Color%20Check_01.jpeg)

---
Correction Patche et Visualisation DDs de la tuile
<img width="1916" height="1816" alt="Correction Visualisation5" src="https://github.com/user-attachments/assets/687af058-4b87-4a36-8dad-2aee3239d82c" />

Fenêtre de sélection des DDS à modifier
<img width="1316" height="1152" alt="Correction Visualisation2" src="https://github.com/user-attachments/assets/f652075c-ed0e-4ff0-a655-18ecada7901d" />
 
Fenêtre de sélection de l'appication de retouche d'image exemple "GIMP"

<img width="1610" height="462" alt="Correction Visualisation6" src="https://github.com/user-attachments/assets/3f650975-a479-4f39-ba3f-f30a51dd1d1e" />
-------
Intégration de la gestion des données Altimétriques et mise en place des dossiers de structures 
<img width="1598" height="320" alt="Altimétrie 1" src="https://github.com/user-attachments/assets/e2d810d0-5557-404e-80e4-bada1680db86" />

<img width="1162" height="160" alt="Altimétrie 2" src="https://github.com/user-attachments/assets/e5e8ca06-43a8-4efe-b216-1411f7632c7e" />

----
Intégration de la gestion des données et traitement dans Josm avec sauvegarde sécurisée

<img width="1650" height="1356" alt="Josm 2" src="https://github.com/user-attachments/assets/b7e6e635-e09d-4096-b99a-b65fa5bb9dbf" />

<img width="848" height="564" alt="Josm 3" src="https://github.com/user-attachments/assets/1f984c4d-2f28-4df1-94d7-5cc0ac5dd955" />

---
## 🛠 Utilisation rapide

### 🍎 Mac

> **⚠️ Étape obligatoire avant tout** — Téléchargez d'abord le lanceur pré-nettoyé (sans blocage Gatekeeper) : **[⬇️ Télécharger le lanceur Mac pré-installé](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)**

1. Téléchargez l'archive principale **ORTHO4XP_V3** (bouton vert "Code" → "Download ZIP")
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

## 📜 Crédits

|  |  |
| --- | --- |
| **Concept & Design** | Roland (Ypsos) |
| **Codage & Support** | Claude (Anthropic AI) |
| **Travaux originaux** | Oscar Pilote (Ortho4XP) |
| **Adaptation 1.40** | Shred86 |
| **Documentation** | English wiki : <https://xpconnect.me/ortho4xp/> |

---

## ⚠️ Licence

Distribué sous **GNU GPL v3** dans le respect de la licence du projet original.
Voir `AVERTISSEMENT_LICENCE_LEGAL.md` pour les détails complets.


---
---

# ORTHO4XP V3.0 (English)

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

## ⚡ Comparison table — V1.40 vs V3

| Feature | Ortho4XP 1.40 (Shred86) | **Ortho4XP V3 (Roland)** |
| --- | --- | --- |
| **Installation** | Manual bash/bat scripts in the terminal | ✅ Graphical launcher — 1 click, no terminal |
| **Python** | Not managed automatically | ✅ Python 3.12 detected and installed automatically |
| **Environment** | Dependencies on the host system | ✅ Isolated `venv/` environment — system untouched |
| **Compatibility** | macOS Intel, Windows | ✅ Apple Silicon M1–M4, Intel, Windows 10/11, Linux |
| **Performance** | Standard Python 3.x | ✅ Python 3.12 — 15 to 20% faster on mesh computations |
| **Hardware detection** | Manual | ✅ CPU/RAM sentinel — automatic safe slots |
| **Launch** | Terminal required | ✅ Native launcher `.app` / `.vbs` / `.desktop` |
| **Interface** | Standard window | ✅ 4K-ready interface — fonts enlarged automatically |
| **GDAL / rasterio** | osgeo.gdal (system dependency) | ✅ `rasterio` inside venv — 100% self-contained |
| **XP12 water transparency** | Not handled — opaque BC1 tiles | ✅ Native XP12 transparency — BC3 textures with alpha channel |
| **Photorealistic sea patches** | Absent | ✅ Built-in generator — sea matching the orthophotos, no blue checkerboard, no transparent triangles |
| **Sea providers / Zoomlevel** | — | ✅ Works with any provider (BI, Esri, IGN…) and any selected zoom level |
| **Color Normalize** | Absent | ✅ Automatic color correction toward neutral sRGB |
| **Color Check** | Absent | ✅ Color verification and correction interface |
| **Previews** | Basic | ✅ Previews tool with sliders and visual configuration |
| **Log console** | Frozen window | ✅ Scrollbar + keyboard navigation (arrows, Page up/down) |
| **Network robustness** | Failure on busy server | ✅ Overpass server rotation, auto retry, white-tile handling |
| **Portability** | Tied to the system | ✅ Self-contained folder — movable to an external drive |
| **XP12 validation** | Not specifically tested | ✅ Tiles produced and validated in X-Plane 12 |

---

## 🚀 Why ORTHO4XP V3?

The goal is to permanently remove the technical barrier of the terminal. This version radically simplifies the user experience while keeping the power of the original tool.

### ✨ Highlights

- 📦 **Zero Terminal** — Fully automated installation and launch
- 🖱️ **Accessibility** — Designed for simmers who want to create their tiles without touching any code
- 🛠️ **Reliability** — Solid 1.40 base with modern optimizations and an isolated Python environment
- 🌊 **Photorealistic XP12 water** — Built-in sea patch generator: sea matching the orthophotos, no blue checkerboard, no transparent triangles, whatever the provider and zoom level
- 🎨 **Advanced colorimetry** — sRGB normalization and per-tile visual correction
- 🌐 **More reliable downloads** — Automatic data-server rotation and recovery after an incident
- 🖥️ **Readable console** — Mouse scrolling and keyboard navigation in the processing log

---

## 🖥️ V3.0 graphical interfaces

### Installation and Launcher

[![Ortho4XP V3 Launcher — installation](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)

[![Ortho4XP V3 Launcher](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/02_Lanceur_Ortho4xp_V2.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/02_Lanceur_Ortho4xp_V2.jpg)

### Main interface and Color Check

[![Main interface](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/03_Nouvelle_interface.jpg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/03_Nouvelle_interface.jpg)

[![Color Check](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/04_Color%20Check_01.jpeg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/04_Color%20Check_01.jpeg)

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

## 📜 Credits

|  |  |
| --- | --- |
| **Concept & Design** | Roland (Ypsos) |
| **Coding & Support** | Claude (Anthropic AI) |
| **Original work** | Oscar Pilote (Ortho4XP) |
| **1.40 adaptation** | Shred86 |
| **Documentation** | English wiki: <https://xpconnect.me/ortho4xp/> |

---

## ⚠️ License

Distributed under **GNU GPL v3** in accordance with the license of the original project.
See `AVERTISSEMENT_LICENCE_LEGAL.md` for full details.
