[![ORTHO4XP V3 Banner]<img width="1536" height="1024" alt="BanniereGithub" src="https://github.com/user-attachments/assets/3e1d4da4-c585-4476-8657-34843d364f30" />


**[🇫🇷 Français](#ortho4xp-v3) | [🇬🇧 English](#ortho4xp-v3-english)**

# ORTHO4XP V3 — **Version Officielle**

> ## ✅ DÉPÔT OFFICIEL
>
> Ce dépôt GitHub est le **dépôt officiel d'ORTHO4XP V3**.
>
> **ORTHO4XP V3** est développé et maintenu par **Roland (Ypsos)**, dans le respect du projet original **Ortho4XP**, créé par **Oscar Pilote**.
>
> Les forks, versions renommées ou projets dérivés sont des projets **indépendants** et ne constituent **pas** le dépôt officiel d'ORTHO4XP V3.
>
> **Pour télécharger la version officielle et obtenir les dernières mises à jour, utilisez toujours ce dépôt GitHub.**

**Développée et maintenue par Roland (Ypsos) avec l'assistance de Claude IA (Anthropic)**

**La version moderne d'Ortho4XP**  
Installation automatique • Sans terminal • Pour X-Plane 12
[![TÉLÉCHARGER LA DERNIÈRE VERSION](https://img.shields.io/badge/T%C3%89L%C3%89CHARGER%20LA%20DERNI%C3%88RE%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 🧭 Origine du projet

|  |  |
| --- | --- |
| **Logiciel original** | Créé par Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Version 1.40 maintenue** | Fork par Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **Cette V3** | **Refonte complète par Roland (Ypsos)** avec l’aide de Claude (Anthropic AI) |

**Je suis l’auteur principal de l’architecture moderne V3** (Event Bus, Pipeline, Memory Manager, Provider Scoring, Altimétrie, JOSM, Correction image, Visualisateur, etc.).

**Ma version reste la référence officielle et la plus à jour du projet original.**

---

## 📌 Dépôt officiel

Ce dépôt constitue la **source officielle de développement d'ORTHO4XP V3**.

Il centralise les versions officielles, les mises à jour, la documentation, le suivi des anomalies et les contributions au projet.

Au fil des années, plusieurs forks, versions renommées ou projets dérivés ont été publiés par la communauté. Ces projets sont **indépendants** et suivent leur propre évolution.

Pour télécharger la version officielle, signaler un problème, proposer une amélioration ou contribuer au développement, utilisez toujours ce dépôt :

➡ **https://github.com/Ypsos/ORTHO4XP_V3**

**Toutes les contributions sont les bienvenues.** Merci d'utiliser exclusivement ce dépôt pour les rapports de bugs, les demandes d'évolution et les discussions concernant **ORTHO4XP V3**.
---

## 🎯 L'idée directrice

Ortho4XP est un outil puissant, mais son accès a longtemps été réservé à ceux qui acceptaient d'ouvrir un terminal, d'installer Python à la main et d'écrire des fichiers de configuration. La V3 repose sur trois partis pris.

**Le moteur d'origine est préservé.** Le calcul du mesh, le cœur du travail d'Oscar Pilote, n'a pas été touché. Tous les ajouts sont des modules autonomes : si l'un d'eux manque ou échoue, Ortho4XP démarre et fonctionne quand même.

**Les barrières tombent.** Installation en un clic, aucun terminal, et des opérations autrefois réservées aux initiés devenues des boutons : retouche des textures, édition OSM dans JOSM, emprises de provider, nivellement, aéroports. L'exemple le plus parlant : la procédure altimétrique de **41 étapes manuelles dans QGIS, tableur `.ods` à l'appui**, tient désormais dans un seul clic.

**Et des capacités entièrement nouvelles apparaissent.** Une mer photoréaliste conforme aux orthophotos, quel que soit le provider. Une correction colorimétrique **adaptée au niveau de zoom** et validée pour le HDR de X-Plane 12. Une notation automatique de la qualité de chaque image téléchargée — bruit, nuages, dérive, risque de jointure. Une surveillance de la mémoire qui évite l'effondrement des gros builds. Rien de tout cela n'existe dans les versions antérieures.

**En résumé :** un simmer doit pouvoir fabriquer ses tuiles sans jamais écrire une ligne de code — et obtenir un meilleur résultat qu'auparavant, pas seulement plus facilement.

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
| **Altimétrie : procédure QGIS** | 41 étapes manuelles dans QGIS + tableur `.ods` | ✅ Un seul bouton — reprojection, découpe, fusion et `custom_dem` renseigné automatiquement |
| **QGIS** | — | ✅ Intégré au module Altimétrie — mémorisé et ouvert sur le résultat pour contrôle visuel |
| **Qualité des providers** | Aucune mesure | ✅ Scoring automatique — bruit, compression, nuages, dérive colorimétrique, risque de jointure |
| **Gestion mémoire** | Aucune | ✅ Surveillance RAM en temps réel et nettoyage automatique du cache |
| **Previews** | Basique | ✅ Outil Previews avec curseurs et configuration visuelle |
| **Console de log** | Fenêtre figée | ✅ Barre de défilement + navigation clavier (flèches, Page préc./suiv.) |
| **Robustesse réseau** | Échec sur serveur occupé | ✅ Rotation des serveurs Overpass, reprise auto, gestion des dalles blanches |
| **Langues** | Anglais | ✅ Interface complète français et anglais |
| **Portabilité** | Lié au système | ✅ Dossier autonome — déplaçable sur disque externe |
| **Validation XP12** | Non testée spécifiquement | ✅ Tuiles produites et validées dans X-Plane 12 |

---

## 🚀 Les points forts

- 📦 **Zéro Terminal** — Installation, lancement et mises à jour entièrement automatisés
- 🖱️ **Accessibilité** — Créer ses tuiles sans manipuler de code, sans rien perdre en contrôle : chaque automatisme reste réglable
- 🛠️ **Fiabilité** — Base solide 1.40, optimisations modernes, environnement Python isolé
- 🌊 **Eau photoréaliste XP12** — Générateur de patches mer intégré : une mer conforme aux orthophotos, sans damier bleu ni triangles transparents, quel que soit le provider et le niveau de zoom
- 🎨 **Colorimétrie avancée** — Normalisation sRGB, contrôle visuel et correction par tuile
- 🖼️ **Correction d'imagerie** — Visualisation des textures de la tuile, retouche dans l'éditeur de votre choix, regénération ciblée
- ⛰️ **Altimétrie assistée** — Structure de dossiers, préparation et conversion des données DEM
- 🗺️ **JOSM et QGIS intégrés** — Édition des données géographiques depuis l'interface, sans jamais toucher à un chemin de fichier
- 🌐 **Téléchargements plus fiables** — Rotation automatique des serveurs de données et reprise après incident
- 📊 **Qualité mesurée** — Chaque image téléchargée est notée : bruit, compression, nuages, dérive colorimétrique, risque de jointure
- 🧠 **Mémoire surveillée** — Nettoyage automatique avant saturation sur les grosses tuiles
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

> ℹ️ **JOSM et QGIS ne sont pas fournis** avec Ortho4XP V3. Vous devez les installer depuis leurs sites officiels ; l'interface les mémorise et les lance ensuite automatiquement.

---

## ⛰️ Le module Altimétrie — la procédure QGIS en un bouton

Intégrer un modèle numérique de terrain dans Ortho4XP demandait jusqu'ici de suivre dans QGIS une procédure de **41 étapes manuelles**, appuyée sur un tableur `.ods` pour calculer les coordonnées d'emprise. Une erreur de saisie, et la tuile était fausse.

Le module Altimétrie fait ce travail à votre place, **sans aucune commande, en un clic** :

| Étape de la procédure manuelle | Ce que fait le module |
| --- | --- |
| *Raster / Projections / Warp* | Reprojection automatique en EPSG:4326 — le système de coordonnées source est **lu dans le fichier**, jamais deviné |
| Changement de la valeur NoData | Appliqué automatiquement |
| Calcul de l'emprise dans le tableur | Découpe à l'emprise de la tuile, élargie du débord de chevauchement de 0,1° pour que les bords se raccordent sans couture avec la tuile voisine |
| *Raster / Divers / Fusion* | Fusion des dalles |
| Export puis saisie du champ DEM | Écriture du `.tif` final et **renseignement automatique de `custom_dem`** dans la configuration de la tuile |

Le module crée aussi la **structure de dossiers** au premier lancement, ce qui supprime d'un coup toute la catégorie d'erreurs « chemin introuvable » chez les utilisateurs sans organisation particulière. Les fichiers sources ne sont jamais modifiés, et les liens symboliques sont acceptés au même titre que les fichiers réels.

**QGIS reste à portée de main** : les boutons « Choisir QGIS » et « Ouvrir dans QGIS » mémorisent votre installation et ouvrent directement le `.tif` produit, pour vérifier le résultat à l'œil.

---

## 🧩 Les modules qui n'existaient pas en 1.40

Tous suivent la même règle de conception : **un fichier autonome, qui ne modifie aucun fichier du moteur d'origine.** Si un module manque ou échoue, Ortho4XP démarre et fonctionne quand même.

| Module | Ce qu'il apporte |
| --- | --- |
| **Patches mer** | Génère une mer conforme aux orthophotos, quel que soit le provider et le niveau de zoom — fin du damier bleu et des triangles transparents |
| **Color Normalize** | Correction colorimétrique automatique vers un sRGB neutre, **adaptée au niveau de zoom** : forte en vue large, légère en ZL18+ pour préserver le détail. Validation HDR compatible X-Plane 12, recalage d'exposition, dégradé de jointure à rayon adaptatif |
| **Color Check** | Interface de contrôle et de correction : comparaison avant/après, aperçu de fusion avec mesure de l'écart colorimétrique entre deux sources, correction par lot, masques de protection |
| **Color Apply** | Applique les corrections enregistrées au bon moment de la chaîne — sur chaque image source avant assemblage, puis sur l'assemblage final. **Les fichiers sources ne sont jamais modifiés** |
| **Correction d'imagerie** | Visualise les textures de la tuile, permet d'en sélectionner, de les retoucher dans l'éditeur de votre choix (GIMP…) et de relancer uniquement ce qui doit l'être |
| **Altimétrie / DEM** | La procédure QGIS de 41 étapes réduite à un bouton (ci-dessus) |
| **Avancé (JOSM)** | Édition des données géographiques, emprises, nivellement et aéroports (ci-dessus) |
| **Provider Score** | Note automatiquement chaque image téléchargée : bruit, artefacts de compression, **couverture nuageuse**, dérive colorimétrique, risque de jointure — et désigne le meilleur provider pour une tuile donnée |
| **Gestion mémoire** | Surveille la RAM en temps réel et nettoie le cache avant saturation, au lieu de laisser le build s'effondrer sur les grosses tuiles |

---

## 🖥️ Interfaces graphiques

### Installation et Lanceur

[![Lanceur Ortho4XP V3 — installation]<img width="1826" height="1936" alt="Lanceur" src="https://github.com/user-attachments/assets/8af30d11-dd03-400f-8056-990217b6c15b" />
(https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/01_Lanceur_installation_python%2C_%20venv.jpg)


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

---

## ⚠️ Licence

Distribué sous **GNU GPL v3** dans le respect de la licence du projet original.
Voir `AVERTISSEMENT_LICENCE_LEGAL.md` pour les détails complets.

JOSM, QGIS et GIMP sont des logiciels tiers indépendants, distribués sous leurs propres licences.

[![ORTHO4XP V3 Banner](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/BanniereGithub.png)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/BanniereGithub.png)

**[🇫🇷 Français](#ortho4xp-v3) | [🇬🇧 English](#ortho4xp-v3-english)**

# ORTHO4XP V3 — **Official Version**

> ## ✅ OFFICIAL REPOSITORY
>
> This GitHub repository is the **official repository of ORTHO4XP V3**.
>
> **ORTHO4XP V3** is developed and maintained by **Roland (Ypsos)**, in accordance with the original **Ortho4XP** project created by **Oscar Pilote**.
>
> Forks, renamed versions, or derivative projects are **independent projects** and are **not** the official ORTHO4XP V3 repository.
>
> **To download the official version and receive the latest updates, always use this GitHub repository.**

**Developed and maintained by Roland (Ypsos) with the assistance of Claude AI (Anthropic)**

**The modern evolution of Ortho4XP**  
Automatic installation • No terminal • For X-Plane 12

[![DOWNLOAD LATEST VERSION](https://img.shields.io/badge/DOWNLOAD%20LATEST%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 🧭 Project Origin

|  |  |
| --- | --- |
| **Original software** | Created by Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Maintained 1.40 version** | Fork by Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **This V3** | **Complete rework by Roland (Ypsos)** with the help of Claude (Anthropic AI) |

**I am the main author of the modern V3 architecture** (Event Bus, Pipeline, Memory Manager, Provider Scoring, Elevation, JOSM, Imagery Correction, Visualizer, etc.).

**My version remains the official reference and the most up-to-date version of the original project.**

---

## 📌 Official Repository

This repository is the **official development source for ORTHO4XP V3**.

It is the central location for official releases, updates, documentation, issue tracking, and project contributions.

Over the years, several forks, renamed versions, and derivative projects have been created by the community. These are **independent projects** and follow their own development paths.

To download the official version, report an issue, suggest an improvement, or contribute to the development of ORTHO4XP V3, please always use this repository:

➡ **https://github.com/Ypsos/ORTHO4XP_V3**

**All contributions are welcome.** Please use this repository exclusively for bug reports, feature requests, and discussions related to **ORTHO4XP V3**.
---

## 🎯 The guiding idea

Ortho4XP is a powerful tool, but for a long time it was only within reach of those willing to open a terminal, install Python by hand and write configuration files. V3 rests on three principles.

**The original engine is preserved.** The mesh computation, the heart of Oscar Pilote's work, has not been touched. Every addition is a self-contained module: if one of them is missing or fails, Ortho4XP still starts and works.

**The barriers come down.** One-click installation, no terminal, and operations once reserved for experts turned into buttons: texture retouching, OSM editing in JOSM, provider extents, terrain flattening, airports. The clearest example: the elevation workflow — **41 manual steps in QGIS, spreadsheet in hand** — now fits into a single click.

**And entirely new capabilities appear.** A photorealistic sea matching the orthophotos, whatever the provider. Colour correction **adapted to the zoom level** and validated for X-Plane 12 HDR. Automatic quality rating of every downloaded image — noise, clouds, drift, seam risk. Memory monitoring that keeps large builds from collapsing. None of this exists in earlier versions.

**In short:** a simmer should be able to build tiles without ever writing a line of code — and get a better result than before, not merely an easier one.

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
| **Elevation: QGIS procedure** | 41 manual steps in QGIS + an `.ods` spreadsheet | ✅ A single button — reprojection, clipping, merging and `custom_dem` filled in automatically |
| **QGIS** | — | ✅ Built into the Elevation module — remembered and opened on the result for visual checking |
| **Provider quality** | No measurement | ✅ Automatic scoring — noise, compression, clouds, colour drift, seam risk |
| **Memory management** | None | ✅ Real-time RAM monitoring and automatic cache cleanup |
| **Previews** | Basic | ✅ Previews tool with sliders and visual configuration |
| **Log console** | Frozen window | ✅ Scrollbar + keyboard navigation (arrows, Page up/down) |
| **Network robustness** | Failure on busy server | ✅ Overpass server rotation, auto retry, white-tile handling |
| **Languages** | English | ✅ Full French and English interface |
| **Portability** | Tied to the system | ✅ Self-contained folder — movable to an external drive |
| **XP12 validation** | Not specifically tested | ✅ Tiles produced and validated in X-Plane 12 |

---

## 🚀 Highlights

- 📦 **Zero Terminal** — Fully automated installation, launch and updates
- 🖱️ **Accessibility** — Build your tiles without touching code, without giving up control: every automation remains adjustable
- 🛠️ **Reliability** — Solid 1.40 base, modern optimizations, isolated Python environment
- 🌊 **Photorealistic XP12 water** — Built-in sea patch generator: sea matching the orthophotos, no blue checkerboard, no transparent triangles, whatever the provider and zoom level
- 🎨 **Advanced colorimetry** — sRGB normalization, visual checking and per-tile correction
- 🖼️ **Imagery correction** — View the tile textures, retouch them in the editor of your choice, regenerate only what you changed
- ⛰️ **Assisted elevation workflow** — Folder structure, preparation and conversion of DEM data
- 🗺️ **JOSM and QGIS built in** — Edit geographic data from the interface, without ever dealing with a file path
- 🌐 **More reliable downloads** — Automatic data-server rotation and recovery after an incident
- 📊 **Measured quality** — Every downloaded image is scored: noise, compression, clouds, colour drift, seam risk
- 🧠 **Monitored memory** — Automatic cleanup before saturation on large tiles
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

> ℹ️ **JOSM and QGIS are not bundled** with Ortho4XP V3. Install them from their official websites; the interface remembers them and launches them automatically afterwards.

---

## ⛰️ The Elevation module — the QGIS procedure in one button

Until now, adding a digital elevation model to Ortho4XP meant following a **41-step manual procedure** in QGIS, backed by an `.ods` spreadsheet to work out the bounding coordinates. One typing mistake and the tile was wrong.

The Elevation module does that work for you, **with no commands, in one click**:

| Step of the manual procedure | What the module does |
| --- | --- |
| *Raster / Projections / Warp* | Automatic reprojection to EPSG:4326 — the source coordinate system is **read from the file**, never guessed |
| Changing the NoData value | Applied automatically |
| Working out the extent in the spreadsheet | Clipping to the tile extent, widened by the 0.1° overlap margin so edges join seamlessly with the neighbouring tile |
| *Raster / Miscellaneous / Merge* | Tiles merged |
| Export then filling in the DEM field | The final `.tif` is written and **`custom_dem` is filled in automatically** in the tile configuration |

The module also creates the **folder structure** on first launch, which removes at a stroke the whole category of "path not found" errors for users without a particular filing system. Source files are never modified, and symbolic links are accepted just like real files.

**QGIS stays within reach**: the "Choose QGIS" and "Open in QGIS" buttons remember your installation and open the produced `.tif` directly, so you can check the result visually.

---

## 🧩 The modules that did not exist in 1.40

They all follow the same design rule: **a self-contained file that modifies no part of the original engine.** If a module is missing or fails, Ortho4XP still starts and works.

| Module | What it brings |
| --- | --- |
| **Sea patches** | Generates a sea matching the orthophotos, whatever the provider and zoom level — no more blue checkerboard, no more transparent triangles |
| **Color Normalize** | Automatic colour correction toward neutral sRGB, **adapted to the zoom level**: strong at wide zoom, light at ZL18+ to preserve detail. X-Plane 12 HDR validation, exposure realignment, seam blending with an adaptive radius |
| **Color Check** | Checking and correction interface: before/after comparison, fusion preview measuring the colour gap between two sources, batch correction, protection masks |
| **Color Apply** | Applies the saved corrections at the right point in the chain — on each source image before assembly, then on the final assembly. **Source files are never modified** |
| **Imagery correction** | Displays the tile textures, lets you select them, retouch them in the editor of your choice (GIMP…) and regenerate only what needs it |
| **Elevation / DEM** | The 41-step QGIS procedure reduced to one button (above) |
| **Advanced (JOSM)** | Geographic data editing, extents, terrain flattening and airports (above) |
| **Provider Score** | Automatically rates every downloaded image: noise, compression artefacts, **cloud cover**, colour drift, seam risk — and points to the best provider for a given tile |
| **Memory management** | Monitors RAM in real time and clears the cache before saturation, instead of letting the build collapse on large tiles |

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


---

## ⚠️ License

Distributed under **GNU GPL v3** in accordance with the license of the original project.
See `AVERTISSEMENT_LICENCE_LEGAL.md` for full details.

JOSM, QGIS and GIMP are independent third-party applications, distributed under their own licenses.
