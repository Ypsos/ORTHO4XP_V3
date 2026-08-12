[![ORTHO4XP V3 Banner](https://github.com/user-attachments/assets/3e1d4da4-c585-4476-8657-34843d364f30)](https://github.com/Ypsos/ORTHO4XP_V3)

**[🇫🇷 Français](#ortho4xp-v3--version-officielle) | [🇬🇧 English](#ortho4xp-v3--official-version)**

---

# ORTHO4XP V3 — Version officielle

> ## ✅ DÉPÔT OFFICIEL
>
> Ce dépôt GitHub est le **dépôt officiel d'ORTHO4XP V3**.
>
> **ORTHO4XP V3** est développé et maintenu par **Roland (Ypsos)**, dans le respect du projet original **Ortho4XP**, créé par **Oscar Pilote**.
>
> Les forks, versions renommées ou projets dérivés sont des projets **indépendants**.
>
> **Pour télécharger la version officielle et obtenir les dernières mises à jour, utilisez toujours ce dépôt GitHub.**
>
> Conçue, réalisée et maintenue par Roland (Ypsos) — assisté de Claude (IA, Anthropic) comme outil d'aide au développement.
>
> **La version moderne d'Ortho4XP**  
> Installation automatique • Sans terminal • Pour X-Plane 12
>
> [![TÉLÉCHARGER LA DERNIÈRE VERSION](https://img.shields.io/badge/T%C3%89L%C3%89CHARGER%20LA%20DERNI%C3%88RE%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 1. À propos des forks

Ortho4XP V3 est libre sous GPL v3. D'autres projets peuvent reprendre son architecture et ses modules. C'est l'esprit du logiciel libre.

**Règle de la licence :** lorsqu'une partie du travail développé pour ORTHO4XP V3 est réutilisée, la **paternité d'origine doit être conservée**. La stabilité et la compatibilité des versions dérivées ne sont pas garanties.

La version officielle maintenue ici reste **gratuite**, sans demande de donation ni bouton de soutien financier.

**Dépôt officiel :** https://github.com/Ypsos/ORTHO4XP_V3

---

## 2. Origine du projet

| | |
| --- | --- |
| **Logiciel original** | Créé par Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Version 1.40 maintenue** | Fork par Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **Cette V3** | **Refonte modernisée par Roland (Ypsos)**, autour du moteur d'origine préservé — assisté de Claude (Anthropic) |

**Auteur principal de l'architecture moderne V3** (Event Bus, Pipeline, Memory Manager, Provider Scoring, Altimétrie, JOSM, Correction image, Visualisateur, etc.) : Roland (Ypsos).

Cette version reste la référence officielle et la plus à jour du projet original.

---

## 3. L'idée directrice

Ortho4XP est un outil puissant, longtemps réservé à ceux qui acceptaient le terminal, Python manuel et les fichiers de configuration. La V3 repose sur trois principes :

1. **Le moteur d'origine est préservé.** Le calcul du mesh (cœur du travail d'Oscar Pilote) n'a pas été touché. Tous les ajouts sont des modules autonomes : si l'un manque ou échoue, Ortho4XP démarre et fonctionne quand même.

2. **Les barrières tombent.** Installation en un clic, aucun terminal, opérations autrefois manuelles devenues des boutons : retouche des textures, édition OSM dans JOSM, emprises de provider, nivellement, aéroports. Exemple : la procédure altimétrique de **41 étapes manuelles dans QGIS** tient désormais dans un seul clic.

3. **De nouvelles capacités apparaissent.** Mer photoréaliste conforme aux orthophotos, correction colorimétrique adaptée au zoom et validée pour le HDR de X-Plane 12, notation automatique de la qualité des images, surveillance mémoire… Rien de tout cela n'existe dans les versions antérieures.

**En résumé :** un simmer doit pouvoir fabriquer ses tuiles sans jamais écrire une ligne de code — et obtenir un meilleur résultat qu'auparavant.

---

## 4. Tableau comparatif — V1.40 vs V3

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
| **Patches mer photoréalistes** | Absent | ✅ Générateur intégré — mer conforme aux orthophotos |
| **Providers / Zoomlevel mer** | — | ✅ Compatible tout provider (BI, Esri, IGN…) et tout ZL |
| **Color Normalize** | Absent | ✅ Correction colorimétrique automatique vers sRGB neutre |
| **Color Check** | Absent | ✅ Interface de vérification et correction des couleurs |
| **Correction d'imagerie** | Aucune | ✅ Module dédié — visualisation DDS, retouche externe, retéléchargement ciblé |
| **Altimétrie / DEM** | Configuration manuelle | ✅ Module dédié — structure de dossiers auto, préparation des fichiers |
| **Édition OSM (JOSM)** | Manipulation manuelle des fichiers | ✅ Module **Avancé** — JOSM lancé automatiquement, fichiers protégés |
| **Emprises / Extents** | Écriture manuelle des `.ext` | ✅ Dessin dans JOSM → publication auto en `.ext` + archive OSM |
| **Nivellement / Aéroports** | Patches à écrire à la main | ✅ Modèles générés auto, code OACI lu dans les données de la tuile |
| **Altimétrie : procédure QGIS** | 41 étapes manuelles + tableur `.ods` | ✅ Un seul bouton — reprojection, découpe, fusion et `custom_dem` auto |
| **QGIS** | — | ✅ Intégré au module Altimétrie — mémorisé et ouvert sur le résultat |
| **Qualité des providers** | Aucune mesure | ✅ Scoring automatique — bruit, compression, nuages, dérive, risque de jointure |
| **Gestion mémoire** | Aucune | ✅ Surveillance RAM en temps réel et nettoyage automatique du cache |
| **Previews** | Basique | ✅ Outil Previews avec curseurs et configuration visuelle |
| **Console de log** | Fenêtre figée | ✅ Barre de défilement + navigation clavier |
| **Robustesse réseau** | Échec sur serveur occupé | ✅ Rotation des serveurs Overpass, reprise auto, gestion des dalles blanches |
| **Langues** | Anglais | ✅ Interface complète français et anglais |
| **Portabilité** | Lié au système | ✅ Dossier autonome — déplaçable sur disque externe |
| **Validation XP12** | Non testée spécifiquement | ✅ Tuiles produites et validées dans X-Plane 12 |

---

## 5. Les points forts

- 📦 **Zéro Terminal** — Installation, lancement et mises à jour entièrement automatisés
- 🖱️ **Accessibilité** — Créer ses tuiles sans manipuler de code, chaque automatisme reste réglable
- 🛠️ **Fiabilité** — Base solide 1.40, optimisations modernes, environnement Python isolé
- 🌊 **Eau photoréaliste XP12** — Générateur de patches mer intégré, conforme aux orthophotos
- 🎨 **Colorimétrie avancée** — Normalisation sRGB, contrôle visuel et correction par tuile
- 🖼️ **Correction d'imagerie** — Visualisation des textures, retouche externe, regénération ciblée
- ⛰️ **Altimétrie assistée** — Structure de dossiers, préparation et conversion des données DEM
- 🗺️ **JOSM et QGIS intégrés** — Édition géographique depuis l'interface, sans chemin de fichier
- 🌐 **Téléchargements plus fiables** — Rotation automatique des serveurs et reprise après incident
- 📊 **Qualité mesurée** — Chaque image notée : bruit, compression, nuages, dérive, risque de jointure
- 🧠 **Mémoire surveillée** — Nettoyage automatique avant saturation sur les grosses tuiles
- 🖥️ **Console lisible** — Défilement souris et navigation clavier dans le journal
- 🌍 **Bilingue** — Interface complète en français et en anglais

---

## 6. Le module Avancé — JOSM et QGIS

Bouton **🛠 Avancé (JOSM)** : gère de bout en bout les travaux d'édition géographique autrefois manuels.

### 6.1 Ce que le module fait à votre place

| Vous voulez… | Le module s'occupe de… |
| --- | --- |
| **Définir une emprise de provider** | Créer le fichier d'édition, ouvrir JOSM, puis **publier automatiquement** l'emprise (`.ext` + archive OSM) |
| **Niveler un terrain** | Générer le patch de la tuile avec le bon tag d'altitude |
| **Corriger un aéroport ou une piste** | Lire le **code OACI** dans les données de la tuile et nommer le patch correctement |
| **Modifier les données OSM** | Proposer un bouton par couche présente (eau, trait de côte, aéroports, routes) |

### 6.2 Sécurités intégrées

- **Sauvegarde automatique** avant ouverture : original conservé hors du dossier de tuile
- **Restauration en un clic** de la version d'origine ou modifiée
- **Envoi vers OpenStreetMap bloqué** : marqueur anti-upload sur tous les fichiers créés
- **Récupération des fichiers égarés** : repérage et remise en place automatique
- **Lancement de JOSM automatique** sur macOS, Windows et Linux (Remote Control + repli)

> ℹ️ **JOSM et QGIS ne sont pas fournis.** Installez-les depuis leurs sites officiels ; l'interface les mémorise et les lance ensuite automatiquement.

---

## 7. Le module Altimétrie — la procédure QGIS en un bouton

Intégrer un MNT demandait **41 étapes manuelles dans QGIS** + un tableur `.ods`. Le module le fait **en un clic** :

| Étape manuelle | Ce que fait le module |
| --- | --- |
| *Raster / Projections / Warp* | Reprojection auto en EPSG:4326 (système source **lu dans le fichier**) |
| Changement NoData | Appliqué automatiquement |
| Calcul d'emprise dans le tableur | Découpe à l'emprise de la tuile + débord 0,1° pour raccord sans couture |
| *Raster / Divers / Fusion* | Fusion des dalles |
| Export + saisie du champ DEM | Écriture du `.tif` final et **renseignement auto de `custom_dem`** |

Le module crée aussi la **structure de dossiers** au premier lancement. Les fichiers sources ne sont jamais modifiés. Liens symboliques acceptés.

**QGIS à portée de main** : boutons « Choisir QGIS » et « Ouvrir dans QGIS » mémorisent l'installation et ouvrent le `.tif` produit.

---

## 8. Les modules absents de la 1.40

Tous sont **autonomes** : aucun fichier du moteur d'origine n'est modifié. Si un module manque, Ortho4XP démarre quand même.

| Module | Apport |
| --- | --- |
| **Patches mer** | Mer conforme aux orthophotos, tout provider et ZL — fin du damier bleu et des triangles transparents |
| **Color Normalize** | Correction sRGB neutre **adaptée au zoom** (forte en vue large, légère en ZL18+). Validation HDR XP12 |
| **Color Check** | Comparaison avant/après, aperçu de fusion, correction par lot, masques de protection |
| **Color Apply** | Applique les corrections au bon moment de la chaîne. **Sources jamais modifiées** |
| **Correction d'imagerie** | Visualise les textures, sélection, retouche externe (GIMP…), regénération ciblée |
| **Altimétrie / DEM** | Procédure QGIS de 41 étapes → 1 bouton |
| **Avancé (JOSM)** | Édition géographique, emprises, nivellement, aéroports |
| **Provider Score** | Note chaque image : bruit, compression, **nuages**, dérive, risque de jointure — désigne le meilleur provider |
| **Gestion mémoire** | Surveillance RAM temps réel + nettoyage auto avant saturation |

---

## 9. Interfaces graphiques

### 9.1 Installation et Lanceur

[![Lanceur Ortho4XP V3 — installation](https://github.com/user-attachments/assets/e0c62747-a4fb-4afd-9645-caa196a19c27)](https://github.com/user-attachments/assets/e0c62747-a4fb-4afd-9645-caa196a19c27)

![Interface principale](https://github.com/user-attachments/assets/9eacd131-76a9-44cf-8d60-76866ddd8095)

### 9.2 Personnalisation des couleurs de l'interface

Plusieurs thèmes sont disponibles. L'utilisateur peut modifier un tableau existant ou créer des couleurs personnalisées à partir d'une roue de couleur.

![Thème Couleur](https://github.com/user-attachments/assets/e4f11a47-7e1f-43df-b8be-d9d370397a9a)

### 9.3 Interface principale et Color Check

![Interface principale et Color Check](https://github.com/user-attachments/assets/e18294fd-4dbf-42f6-8eda-4f003645844b)

### 9.4 Correction d'imagerie — visualisation des textures

![Correction Visualisation](https://github.com/user-attachments/assets/687af058-4b87-4a36-8dad-2aee3239d82c)

Fenêtre de sélection des textures à modifier :

![Sélection textures](https://github.com/user-attachments/assets/f652075c-ed0e-4ff0-a655-18ecada7901d)

Choix de l'application de retouche (exemple : GIMP) :

![Choix éditeur](https://github.com/user-attachments/assets/3f650975-a479-4f39-ba3f-f30a51dd1d1e)

### 9.5 Altimétrie — gestion des données et structure de dossiers

![Altimétrie 1](https://github.com/user-attachments/assets/e2d810d0-5557-404e-80e4-bada1680db86)

![Altimétrie 2](https://github.com/user-attachments/assets/e5e8ca06-43a8-4efe-b216-1411f7632c7e)

### 9.6 Module Avancé — édition JOSM avec sauvegarde sécurisée

![JOSM 2](https://github.com/user-attachments/assets/b7e6e635-e09d-4096-b99a-b65fa5bb9dbf)

![JOSM 3](https://github.com/user-attachments/assets/1f984c4d-2f28-4df1-94d7-5cc0ac5dd955)

### 9.7 Gestion du cache OSM local multi-fichiers

![Gestion cache OSM Local](https://github.com/user-attachments/assets/9d5a9f19-aa61-46c1-aada-fa823b170ddc)

---

## 10. Provider PCRS_IGN & Générateur .lay

Outil qui ajoute le support du provider PCRS_IGN et un générateur automatique de fichiers `.lay`.

**Fonctionnalités :**
- Images Ultra Haute Définition (jusqu'au ZL 21) via le Plan Corps de Rue Simplifié (PCRS) de l'IGN
- Génération de `.lay` 100 % automatisée (`O4_lay_generator.py`)
- Préréglage inclus : bouton Preset PCRS_IGN
- Protection anti-bannissement IP : temporisation dynamique dans `O4_Custom_URL.py`
- Interface multiplateforme thématisée (macOS, Windows, Linux)

![Générateur Lay](https://github.com/user-attachments/assets/4440001a-58e3-4c0c-bc74-b34251c427f4)

**Presets intégrés :** IGN Ortho France (France + DOM-TOM) et PCRS_IGN  
**Crédit preset IGN Ortho France :** contribution de domisilasol (Dominique), X-Plane.fr

---

## 11. Module ProviderScore (choix intelligent de fournisseurs)

Analyse automatique multicritères des fournisseurs d'imagerie (Bing, ESRI, Google, etc.).

**Fonctionnalités :**
- 📊 Évaluation automatique (Score /100) : netteté, contraste, homogénéité, couverture nuageuse
- ⚡ Sélection & sélection auto du meilleur fournisseur dans la liste imagery
- 📈 Comparatif historisé des notes
- 🖥️ UI multiplateforme (Windows, macOS, Linux)
- 🌐 Multilingue (système O4_Lang)

![Analyse Fournisseur](https://github.com/user-attachments/assets/df0b4271-8724-4f4e-8fbd-ead4b321ab3d)

**Gestion des droits :** fenêtre d'avertissement pour les fournisseurs réservés à un usage strictement personnel. Le choix « Je quitte » empêche l'utilisation des sources interdisant la redistribution gratuite des tuiles.

![Avertissement droits](https://github.com/user-attachments/assets/a1ee2ec2-ab90-4a6f-879d-9c9d40c4eede)

---

## 12. Assistant graphique de fichiers .comb

Création visuelle des fichiers `.comb` (fournisseurs, zones, priorités) via le bouton **🛠 Avancé**.

**Fonctionnalités principales :**
- Liste des fournisseurs classés par score de qualité
- Mode Automatique : configuration en un clic (imagerie locale prioritaire, fournisseurs mondiaux en secours)
- Mode Manuel : sélection des zones et priorités (Haute / Moyenne / Basse) via menus déroulants
- Aperçu et génération au format exact requis
- Importation d'un `.comb` préexistant
- Accès direct au générateur `.lay`

**Sécurité :**
- Aucune donnée écrasée sans confirmation
- Sauvegarde automatique avant chaque modification
- Compatibilité totale avec les standards communauté

![Créateur fichier Comb FR](https://github.com/user-attachments/assets/a5eb68e7-86f4-4c45-85cc-6140d17c4a8e)

---

## 13. Tutoriels PDF intégrés (menu Avancé)

Nouveau bouton **« 📄 Pas à pas — utilisation des modules »** dans le menu Avancé.

- Scanne le dossier `Docs/` et liste automatiquement les tutoriels disponibles
- Ouvre chaque tuto en **FR** ou **EN** selon la langue active
- Ajout d'un PDF = liste mise à jour automatiquement, sans modification de code
- Compatible macOS / Windows / Linux

**Convention de nommage :** `<Titre>_FR.pdf` et `<Titre>_EN.pdf` dans `Docs/`.

Fichier modifié : `src/O4_Menu_Avance.py` (aucun fichier de langue impacté).

---

## 14. Utilisation rapide

### 🍎 Mac

> **⚠️ Étape obligatoire avant tout** — Téléchargez d'abord le lanceur pré-nettoyé (sans blocage Gatekeeper) :  
> **[⬇️ Télécharger le lanceur Mac pré-installé](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)**

1. Téléchargez l'archive principale **ORTHO4XP_V3** (bouton vert « Code » → « Download ZIP »)
2. Décompressez l'archive — renommez le dossier en `ORTHO4XP_V3`
3. Téléchargez le ZIP de la Release ci-dessus et extrayez `Lanceur_Installation_Prerequis.app` directement dans le dossier `ORTHO4XP_V3`
4. Placez le dossier `ORTHO4XP_V3` dans votre dossier **`Applications`** (`/Users/votre_nom/Applications/`)
5. Double-cliquez sur `Lanceur_Installation_Prerequis.app`

### 🪟 Windows

1. Téléchargez l'archive principale **ORTHO4XP_V3** et décompressez
2. Double-cliquez sur `LANCEUR_INSTALL_WINDOWS.bat`

### 🐧 Linux

1. Téléchargez l'archive principale **ORTHO4XP_V3** et décompressez
2. Double-cliquez sur `LANCEUR_INSTALL_LINUX.sh`

---

## 15. Remerciements

Merci en particulier à **Jojo**, référence technique sur Ortho4XP, QGIS et JOSM ; et à **Cricri**, pour les tests et validations sous Windows et Linux.

Merci également à tous ceux qui remontent leurs retours sur les forums.

---

## 16. Crédits

| | |
| --- | --- |
| **Idée, conception, réalisation, développement** | Roland (Ypsos) |
| **Assistance au développement (outil IA)** | Claude (Anthropic) |
| **Œuvre originale** | Oscar Pilote (Ortho4XP) |
| **Adaptation 1.40** | Shred86 |
| **Référence technique** | Jojo |
| **Tests Windows / Linux** | Cricri |
| **Autres contributeurs** | domisilasol(Dominique), Jasum,  Len0y|

---

## 17. Licence

Distribué sous **GNU GPL v3** dans le respect de la licence du projet original.  
Voir `AVERTISSEMENT_LICENCE_LEGAL.md` pour les détails complets.

JOSM, QGIS et GIMP sont des logiciels tiers indépendants, distribués sous leurs propres licences.

Données altimétriques (relief) : Modèles numériques de terrain LiDAR de Sonny — Sonny's LiDAR Digital Terrain Models of Europe — disponibles sur sonny.4lima.de. Licenciés sous Creative Commons Attribution 4.0 (CC BY 4.0).

---

[![ORTHO4XP V3 Banner](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/BanniereGithub.png)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/BanniereGithub.png)

---
---

# ORTHO4XP V3 — Official Version

> ## ✅ OFFICIAL REPOSITORY
>
> This GitHub repository is the **official repository for ORTHO4XP V3**.
>
> **ORTHO4XP V3** is developed and maintained by **Roland (Ypsos)**, in respect of the original **Ortho4XP** project created by **Oscar Pilote**.
>
> Forks, renamed versions, or derivative projects are **independent** projects.
>
> **To download the official version and get the latest updates, always use this GitHub repository.**
>
> Developed and maintained by Roland (Ypsos) with assistance from Claude AI (Anthropic).
>
> **The modern version of Ortho4XP**  
> Automatic installation • No terminal required • For X-Plane 12
>
> [![DOWNLOAD LATEST VERSION](https://img.shields.io/badge/DOWNLOAD%20LATEST%20VERSION-00C853?style=for-the-badge&logo=download&logoColor=white)](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)

---

## 1. About Forks

Ortho4XP V3 is free software under GPL v3. Other projects may reuse its architecture and modules. This is the spirit of open source.

**License rule only:** when part of the work developed for ORTHO4XP V3 is reused, the **original authorship must be preserved**. Stability and compatibility of derivative versions are not guaranteed.

The official version maintained here remains **completely free**, with no donation requests or support buttons.

**Official repository:** https://github.com/Ypsos/ORTHO4XP_V3

---

## 2. Project Origin

| | |
| --- | --- |
| **Original software** | Created by Oscar Pilote → [github.com/oscarpilote/Ortho4XP](https://github.com/oscarpilote/Ortho4XP) |
| **Maintained Version 1.40** | Fork by Shred86 → [github.com/shred86/Ortho4XP](https://github.com/shred86/Ortho4XP) |
| **This V3** | Complete overhaul by Roland (Ypsos) with assistance from Claude (Anthropic AI) |

**Main author of the modern V3 architecture** (Event Bus, Pipeline, Memory Manager, Provider Scoring, Altimetry, JOSM, Image Correction, Viewer, etc.): Roland (Ypsos).

This version remains the official reference and the most up-to-date version of the original project.

---

## 3. The Guiding Idea

Ortho4XP is a powerful tool, but for a long time it was only within reach of those willing to open a terminal, install Python by hand and write configuration files. V3 rests on three principles:

1. **The original engine is preserved.** The mesh computation (the heart of Oscar Pilote's work) has not been touched. Every addition is a self-contained module: if one is missing or fails, Ortho4XP still starts and works.

2. **The barriers come down.** One-click installation, no terminal, and operations once reserved for experts turned into buttons: texture retouching, OSM editing in JOSM, provider extents, terrain flattening, airports. The clearest example: the elevation workflow — **41 manual steps in QGIS** — now fits into a single click.

3. **Entirely new capabilities appear.** A photorealistic sea matching the orthophotos, colour correction adapted to the zoom level and validated for X-Plane 12 HDR, automatic quality rating of every downloaded image, memory monitoring… None of this exists in earlier versions.

**In short:** a simmer should be able to build tiles without ever writing a line of code — and get a better result than before.

---

## 4. Comparison Table — V1.40 vs V3

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
| **Photorealistic sea patches** | Absent | ✅ Built-in generator — sea matching the orthophotos |
| **Sea providers / Zoom level** | — | ✅ Works with any provider (BI, Esri, IGN…) and any zoom level |
| **Color Normalize** | Absent | ✅ Automatic color correction toward neutral sRGB |
| **Color Check** | Absent | ✅ Color verification and correction interface |
| **Imagery correction** | None | ✅ Dedicated module — view tile textures, retouch externally, targeted re-download |
| **Elevation / DEM** | Manual configuration | ✅ Dedicated module — folder structure created automatically, file preparation |
| **OSM editing (JOSM)** | Manual file handling | ✅ **Advanced** module — JOSM detected and launched automatically, files protected |
| **Extents** | `.ext` files written by hand | ✅ Draw the extent in JOSM → automatic publication as `.ext` + OSM archive |
| **Flattening / Airports** | Patches written by hand | ✅ Templates generated automatically, ICAO code read from the tile data |
| **Elevation: QGIS procedure** | 41 manual steps in QGIS + `.ods` spreadsheet | ✅ A single button — reprojection, clipping, merging and `custom_dem` filled in automatically |
| **QGIS** | — | ✅ Built into the Elevation module — remembered and opened on the result |
| **Provider quality** | No measurement | ✅ Automatic scoring — noise, compression, clouds, colour drift, seam risk |
| **Memory management** | None | ✅ Real-time RAM monitoring and automatic cache cleanup |
| **Previews** | Basic | ✅ Previews tool with sliders and visual configuration |
| **Log console** | Frozen window | ✅ Scrollbar + keyboard navigation |
| **Network robustness** | Failure on busy server | ✅ Overpass server rotation, auto retry, white-tile handling |
| **Languages** | English | ✅ Full French and English interface |
| **Portability** | Tied to the system | ✅ Self-contained folder — movable to an external drive |
| **XP12 validation** | Not specifically tested | ✅ Tiles produced and validated in X-Plane 12 |

---

## 5. Highlights

- 📦 **Zero Terminal** — Fully automated installation, launch and updates
- 🖱️ **Accessibility** — Build tiles without touching code; every automation remains adjustable
- 🛠️ **Reliability** — Solid 1.40 base, modern optimizations, isolated Python environment
- 🌊 **Photorealistic XP12 water** — Built-in sea patch generator matching the orthophotos
- 🎨 **Advanced colorimetry** — sRGB normalization, visual checking and per-tile correction
- 🖼️ **Imagery correction** — View tile textures, retouch in the editor of your choice, regenerate only what changed
- ⛰️ **Assisted elevation workflow** — Folder structure, preparation and conversion of DEM data
- 🗺️ **JOSM and QGIS built in** — Edit geographic data from the interface, without dealing with file paths
- 🌐 **More reliable downloads** — Automatic data-server rotation and recovery after an incident
- 📊 **Measured quality** — Every downloaded image is scored: noise, compression, clouds, colour drift, seam risk
- 🧠 **Monitored memory** — Automatic cleanup before saturation on large tiles
- 🖥️ **Readable console** — Mouse scrolling and keyboard navigation in the processing log
- 🌍 **Bilingual** — Complete interface in French and English

---

## 6. The Advanced Module — JOSM and QGIS

A **🛠 Advanced (JOSM)** button opens a window that handles geographic editing tasks end-to-end.

### 6.1 What the module does for you

| You want to… | The module takes care of… |
| --- | --- |
| **Define a provider extent** | Creating the editing file, opening JOSM, then **automatically publishing** the extent (`.ext` + OSM archive) |
| **Flatten terrain** | Generating the tile patch with the correct altitude tag |
| **Fix an airport or a runway** | Reading the **ICAO code** from the tile data and naming the patch correctly |
| **Edit OSM data** | Offering one button per layer actually present (water, coastline, airports, roads) |

### 6.2 Built-in safeguards

- **Automatic backup** before anything is opened: original kept outside the tile folder
- **One-click restore** of the original or your modified version
- **Upload to OpenStreetMap blocked**: every generated file carries the anti-upload flag
- **Stray file recovery**: finds misplaced files and puts them back
- **Automatic JOSM launch** on macOS, Windows and Linux (Remote Control + fallback)

> ℹ️ **JOSM and QGIS are not bundled.** Install them from their official websites; the interface remembers them and launches them automatically afterwards.

---

## 7. The Elevation Module — the QGIS procedure in one button

Until now, adding a digital elevation model meant a **41-step manual procedure** in QGIS plus an `.ods` spreadsheet. The Elevation module does that work **in one click**:

| Step of the manual procedure | What the module does |
| --- | --- |
| *Raster / Projections / Warp* | Automatic reprojection to EPSG:4326 (source coordinate system **read from the file**) |
| Changing the NoData value | Applied automatically |
| Working out the extent in the spreadsheet | Clipping to the tile extent, widened by the 0.1° overlap margin |
| *Raster / Miscellaneous / Merge* | Tiles merged |
| Export then filling in the DEM field | Final `.tif` written and **`custom_dem` filled in automatically** |

The module also creates the **folder structure** on first launch. Source files are never modified. Symbolic links are accepted.

**QGIS stays within reach**: the "Choose QGIS" and "Open in QGIS" buttons remember your installation and open the produced `.tif` directly.

---

## 8. Modules that did not exist in 1.40

They all follow the same design rule: **a self-contained file that modifies no part of the original engine.** If a module is missing or fails, Ortho4XP still starts and works.

| Module | What it brings |
| --- | --- |
| **Sea patches** | Sea matching the orthophotos, any provider and zoom level — no more blue checkerboard or transparent triangles |
| **Color Normalize** | Automatic colour correction toward neutral sRGB, **adapted to the zoom level**. X-Plane 12 HDR validation |
| **Color Check** | Before/after comparison, fusion preview, batch correction, protection masks |
| **Color Apply** | Applies saved corrections at the right point in the chain. **Source files are never modified** |
| **Imagery correction** | Displays tile textures, lets you select them, retouch in an external editor (GIMP…), regenerate only what needs it |
| **Elevation / DEM** | The 41-step QGIS procedure reduced to one button |
| **Advanced (JOSM)** | Geographic data editing, extents, terrain flattening and airports |
| **Provider Score** | Rates every downloaded image: noise, compression artefacts, **cloud cover**, colour drift, seam risk — points to the best provider |
| **Memory management** | Monitors RAM in real time and clears the cache before saturation |

---

## 9. Graphical Interfaces

### 9.1 Installation and Launcher

[![Ortho4XP V3 Launcher — installation](https://github.com/user-attachments/assets/528f32df-ba3f-425c-88bb-0f70d23eb423)](https://github.com/user-attachments/assets/528f32df-ba3f-425c-88bb-0f70d23eb423)

![Main interface](https://github.com/user-attachments/assets/75a942d1-0347-422b-9d86-979a9d589e65)

### 9.2 Interface Color Customization

Several interface colors are already available. Users can modify colors within an existing palette or create custom colors using a color wheel.

![Color Theme](https://github.com/user-attachments/assets/ef1dfe79-fc23-43ab-a2aa-d448681a24b9)

### 9.3 Main Interface and Color Check

[![Color Check](https://github.com/Ypsos/ORTHO4XP_V3/raw/ORTHO4XP_V3/04_Color%20Check_01.jpeg)](https://github.com/Ypsos/ORTHO4XP_V3/blob/ORTHO4XP_V3/04_Color%20Check_01.jpeg)

### 9.4 Imagery Correction — Viewing Tile Textures

![Correction view 5](https://github.com/user-attachments/assets/687af058-4b87-4a36-8dad-2aee3239d82c)

Selecting the textures to edit:

![Correction view 2](https://github.com/user-attachments/assets/f652075c-ed0e-4ff0-a655-18ecada7901d)

Choosing the image editor (example: GIMP):

![Correction view 6](https://github.com/user-attachments/assets/3f650975-a479-4f39-ba3f-f30a51dd1d1e)

### 9.5 Elevation — Data Management and Folder Structure

![Elevation 1](https://github.com/user-attachments/assets/e2d810d0-5557-404e-80e4-bada1680db86)

![Elevation 2](https://github.com/user-attachments/assets/e5e8ca06-43a8-4efe-b216-1411f7632c7e)

### 9.6 Advanced Module — JOSM Editing with Protected Backups

![JOSM 2](https://github.com/user-attachments/assets/b7e6e635-e09d-4096-b99a-b65fa5bb9dbf)

![JOSM 3](https://github.com/user-attachments/assets/1f984c4d-2f28-4df1-94d7-5cc0ac5dd955)

### 9.7 Local OSM Cache Management Multi-file

![Local OSM cache management](https://github.com/user-attachments/assets/9d5a9f19-aa61-46c1-aada-fa823b170ddc)

---

## 10. Provider PCRS_IGN & .lay Generator

This tool adds PCRS_IGN provider support and an automatic `.lay` configuration file generator.

**What the tool does:**
- Ultra High Definition Images (up to ZL 21) via IGN's Simplified Street Body Plan (PCRS)
- 100 % automated `.lay` generation (`O4_lay_generator.py`)
- Preset included: PCRS_IGN Preset button
- IP anti-ban protection: dynamic timing in `O4_Custom_URL.py`
- Cross-platform themed interface (macOS, Windows, Linux)

![Lay Generator](https://github.com/user-attachments/assets/4440001a-58e3-4c0c-bc74-b34251c427f4)

**Built-in presets:** IGN Ortho France (France + overseas territories) and PCRS_IGN  
**IGN Ortho France preset credit:** contribution from domisilasol (Dominique), X-Plane.fr

---

## 11. ProviderScore Module (Smart Provider Selection)

Automated multi-criteria analysis system for satellite imagery providers (Bing, ESRI, Google, etc.).

**Features:**
- 📊 Automatic Evaluation (Score /100): sharpness, contrast, uniformity, cloud cover
- ⚡ Selection & Auto-Selection of the best provider in the imagery list
- 📈 Historical Comparison of scores across generations
- 🖥️ Cross-Platform UI (Windows, macOS, Linux)
- 🌐 Multilingual (compatible with O4_Lang)

![Provider Analysis](https://github.com/user-attachments/assets/43e36f2f-bb65-41dc-bcd0-f1d0f095ab90)

**Rights Management & Distribution Protection:** Integrated warning window for providers restricted to strictly personal use. Selecting “Exit” prevents the use of sources that prohibit free redistribution of tiles.

![Provider Analysis warning](https://github.com/user-attachments/assets/6c9113fe-ccae-4814-a0a9-5c3ec4cb3707)

---

## 12. Graphical .comb File Wizard

Until now, creating `.comb` files required a text editor. This is now fully automated and visual via the **🛠 Advanced** button.

**Key Features:**
- Provider List sorted by quality score
- Automatic Mode: one-click configuration (local imagery prioritized, global providers as fallback)
- Manual Mode: select zones and priorities (High / Medium / Low) via drop-downs
- Preview and Generation in the exact required format
- Import of an existing `.comb` file
- Direct access to the `.lay` generator

**Security:**
- No data overwritten without confirmation
- Automatic backup before each modification
- Full compliance with community file standards

![Comb file creator EN](https://github.com/user-attachments/assets/95c49c62-d0e0-451a-8d74-e2a2758035e3)

---

## 13. Built-in PDF Tutorials (Advanced Menu)

New button **« 📄 Step-by-step — using the modules »** in the Advanced menu.

- Scans the `Docs/` folder and lists available tutorials automatically
- Opens each tutorial in **FR** or **EN** according to the active language
- Adding a PDF updates the list automatically, with no code change
- Compatible with macOS / Windows / Linux

**Naming convention:** `<Title>_FR.pdf` and `<Title>_EN.pdf` in `Docs/`.

Modified file: `src/O4_Menu_Avance.py` (no language file impacted).

---

## 14. Quick Start

### 🍎 Mac

> **⚠️ Mandatory first step** — First download the pre-cleaned launcher (no Gatekeeper block):  
> **[⬇️ Download the pre-installed Mac launcher](https://github.com/Ypsos/ORTHO4XP_V3/releases/latest)**

1. Download the main archive **ORTHO4XP_V3** (green "Code" button → "Download ZIP")
2. Unzip the archive — rename the folder to `ORTHO4XP_V3`
3. Download the Release ZIP above and extract `Lanceur_Installation_Prerequis.app` directly into the `ORTHO4XP_V3` folder
4. Place the `ORTHO4XP_V3` folder into your **`Applications`** folder (`/Users/your_name/Applications/`)
5. Double-click `Lanceur_Installation_Prerequis.app`

### 🪟 Windows

1. Download the main archive **ORTHO4XP_V3** and unzip
2. Double-click `LANCEUR_INSTALL_WINDOWS.bat`

### 🐧 Linux

1. Download the main archive **ORTHO4XP_V3** and unzip
2. Double-click `LANCEUR_INSTALL_LINUX.sh`

---

## 15. Acknowledgements

Special thanks to **Jojo**, the technical reference on Ortho4XP, QGIS and JOSM; and to **Cricri**, for testing and validating on Windows and Linux.

Thanks as well to everyone posting feedback on the forums.

---

## 16. Credits

| | |
| --- | --- |
| **Idea, design, implementation, development** | Roland (Ypsos) |
| **Development support (AI tool)** | Claude (Anthropic) |
| **Original work** | Oscar Pilote (Ortho4XP) |
| **1.40 adaptation** | Shred86 |
| **Technical reference** | Jojo |
| **Windows / Linux testing** | Cricri |
| **Other contributorss** | domisilasol(Dominique), Jasum,  Len0y|

---

## 17. License

Distributed under **GNU GPL v3** in accordance with the license of the original project.  
See `AVERTISSEMENT_LICENCE_LEGAL.md` for full details.

JOSM, QGIS and GIMP are independent third-party applications, distributed under their own licenses.

Altimetric data (relief): Sonny's LiDAR Digital Terrain Models of Europe — available on sonny.4lima.de. Licensed under Creative Commons Attribution 4.0 (CC BY 4.0).
