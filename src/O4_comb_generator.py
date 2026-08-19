# -*- coding: utf-8 -*-
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — Mars 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CREDIT — AUTHOR: Roland (Ypsos) — March 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================
#  O4_comb_generator.py  —  ORTHO4XP V3
#  Générateur de fichier .comb assisté (destiné aux utilisateurs sans expert).
#  Auteur : Roland (Ypsos)
#
#  Construit par FONCTIONS FONCTIONNELLES, chaque fonction = un CHAPITRE complet
#  et testable. On enrichit ce même fichier chapitre après chapitre.
#
#  CHAPITRE 1 — AFFICHAGE DES PROVIDERS + SCORES   ← fonction livrée
#  CHAPITRE 2 — (à venir) Sélection + priorités
#  CHAPITRE 3 — (à venir) Détection frontière + garde-fous
#  CHAPITRE 4 — (à venir) Génération du .comb
# ==============================================================================

import os
import json

# Traduction : import protégé. Si O4_Lang est absent, tr() renvoie le texte
# tel quel (aucun plantage). Utilisé uniquement par la fenêtre (chapitre 6) ;
# le moteur (chapitres 1-5) reste en français interne et n'appelle pas tr().
try:
    from O4_Lang import tr as _tr
except Exception:
    def _tr(key):
        return key

# Langue active : import protégé. Sert à choisir la version FR ou EN d'un
# libellé bilingue résolu ICI (sans toucher aux fichiers O4_Lang_*). Même
# mécanisme que O4_Menu_Avance. Si O4_Lang est absent/ancien → EN par défaut.
try:
    from O4_Lang import current_lang as _current_lang
except Exception:
    def _current_lang():
        return "EN"


def _lang_code():
    """Retourne 'FR' si la langue active est le français, sinon 'EN'."""
    try:
        code = (_current_lang() or "EN").upper()
    except Exception:
        code = "EN"
    return "FR" if code == "FR" else "EN"


def _L(fr, en):
    """Libellé bilingue résolu ICI (sans toucher aux fichiers O4_Lang_*).
    FR si langue active = français, EN sinon."""
    return fr if _lang_code() == "FR" else en

# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 1 — AFFICHAGE DES PROVIDERS + SCORES
#  Rôle : scanner le dossier Providers/, lister tous les providers (.lay) que
#  l'utilisateur possède réellement, lire les scores déjà calculés dans
#  _score_exports/_score_log.json, et présenter chaque provider avec son
#  dernier score connu + label, trié du meilleur au moins bon.
#  Ne touche à AUCUN fichier existant. N'écrit rien. Lecture seule.
# ══════════════════════════════════════════════════════════════════════════════

def _providers_dir(base_dir):
    """Retourne le chemin du dossier Providers/ à partir de la racine Ortho4XP."""
    return os.path.join(base_dir, "Providers")


def _score_log_path(base_dir):
    """Chemin du journal des scores (peut être dans src/ ou à la racine)."""
    candidats = [
        os.path.join(base_dir, "src", "_score_exports", "_score_log.json"),
        os.path.join(base_dir, "_score_exports", "_score_log.json"),
    ]
    for c in candidats:
        if os.path.isfile(c):
            return c
    return None


def scan_providers(base_dir):
    """
    Scanne Providers/ et retourne la liste des providers réels de l'utilisateur.
    Chaque provider = nom du fichier .lay sans extension.
    Ignore le dossier __pycache__ et les tuiles perso (dossiers +NN...).
    Retourne une liste triée, sans doublon.
    """
    prov_dir = _providers_dir(base_dir)
    trouves = set()
    if not os.path.isdir(prov_dir):
        return []
    for racine, dossiers, fichiers in os.walk(prov_dir):
        # on ne descend pas dans __pycache__
        dossiers[:] = [d for d in dossiers if d != "__pycache__"]
        for f in fichiers:
            if f.lower().endswith(".lay"):
                trouves.add(f[:-len(".lay")])
    return sorted(trouves)


def load_scores(base_dir):
    """
    Lit _score_log.json et retourne, pour chaque provider, son score le PLUS
    RÉCENT (dernier timestamp), sous forme d'un dict :
      { "Esri_07-2022": {"global_score": 88.5, "label": "✅ Excellent"}, ... }
    Si le fichier n'existe pas ou est illisible, retourne un dict vide (aucun
    plantage — le module reste utilisable même sans scores).
    """
    chemin = _score_log_path(base_dir)
    resultat = {}
    if not chemin:
        return resultat
    try:
        with open(chemin, encoding="utf-8") as fp:
            entrees = json.load(fp)
    except Exception:
        return resultat
    if not isinstance(entrees, list):
        return resultat
    for e in entrees:
        try:
            code = e.get("provider_code")
            ts = float(e.get("timestamp", 0))
            if code is None:
                continue
            ancien = resultat.get(code)
            if ancien is None or ts > ancien["_ts"]:
                resultat[code] = {
                    "global_score": float(e.get("global_score", 0.0)),
                    "label": e.get("label", ""),
                    "_ts": ts,
                }
        except Exception:
            continue
    # on retire le champ interne _ts
    for code in resultat:
        resultat[code].pop("_ts", None)
    return resultat


def build_provider_view(base_dir):
    """
    Combine scan_providers + load_scores et retourne une liste prête à afficher,
    triée du MEILLEUR score au moins bon (les non-évalués en dernier) :
      [ {"provider": "...", "score": 88.5, "label": "✅ Excellent", "evalue": True}, ... ]
    """
    providers = scan_providers(base_dir)
    scores = load_scores(base_dir)
    vue = []
    for p in providers:
        s = scores.get(p)
        if s is not None:
            vue.append({
                "provider": p,
                "score": s["global_score"],
                "label": s["label"],
                "evalue": True,
            })
        else:
            vue.append({
                "provider": p,
                "score": None,
                "label": "— non évalué",
                "evalue": False,
            })
    # tri : évalués d'abord (meilleur score en tête), non évalués à la fin
    vue.sort(key=lambda x: (not x["evalue"], -(x["score"] or 0)))
    return vue


# ── Affichage console (test de la fonction sans interface graphique) ──────────
def afficher_console(base_dir):
    """Affiche la vue providers+scores en mode texte. Sert au test headless."""
    vue = build_provider_view(base_dir)
    print("Providers trouvés :", len(vue))
    print("-" * 60)
    for item in vue:
        if item["evalue"]:
            print(f"  {item['score']:5.1f}/100  {item['label']:15s}  {item['provider']}")
        else:
            print(f"    —        {item['label']:15s}  {item['provider']}")
    print("-" * 60)
    return vue


if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    afficher_console(base)


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 2 — SÉLECTION DES PROVIDERS + PRIORITÉS
#  Rôle : à partir de la vue du Chapitre 1 (providers + scores), permettre de
#  construire une SÉLECTION : quels providers l'utilisateur retient pour son
#  .comb, dans quel ORDRE, avec quelle PRIORITÉ (low / medium / high).
#  Cette sélection est une structure en mémoire, pas encore un fichier écrit
#  (l'écriture du .comb sera le Chapitre 4). Aucune écriture disque ici.
#
#  Rappel format .comb (validé sur EUR.comb et ZonePhoto.comb) : 4 colonnes
#     provider | zone | filtre(none) | priorité
#  La priorité décide qui passe au-dessus de qui sur les zones de recouvrement.
# ══════════════════════════════════════════════════════════════════════════════

# Priorités autorisées, du plus faible au plus fort. L'ordre sert à trier et à
# valider : on n'accepte jamais une valeur hors de cette liste (rien en dur
# ailleurs, une seule source de vérité).
PRIORITES_VALIDES = ("low", "medium", "high")


class SelectionComb:
    """
    Panier de sélection pour construire un .comb.
    Contient une liste ordonnée d'entrées ; chaque entrée =
        {"provider": str, "zone": str, "filtre": "none", "priorite": "medium"}
    L'ordre de la liste = l'ordre dans lequel les lignes seront écrites.
    """

    def __init__(self):
        self._entrees = []   # liste de dict, ordre = ordre d'écriture

    # ── Consultation ──────────────────────────────────────────────────────────
    def entrees(self):
        """Retourne une COPIE de la liste des entrées (lecture sûre)."""
        return [dict(e) for e in self._entrees]

    def contient(self, provider):
        """Vrai si ce provider est déjà dans la sélection."""
        return any(e["provider"] == provider for e in self._entrees)

    def taille(self):
        return len(self._entrees)

    # ── Ajout / retrait ───────────────────────────────────────────────────────
    def ajouter(self, provider, zone="", filtre="none", priorite="medium"):
        """
        Ajoute un provider à la sélection.
        - Refuse un doublon exact (même provider + même zone) : renvoie False.
          (Un même provider PEUT figurer deux fois si la ZONE diffère — c'est le
           cas frontière légitime « straddling 2 régions » ; on ne l'interdit pas.)
        - Refuse une priorité invalide : renvoie False.
        Renvoie True si l'ajout a réussi.
        """
        if priorite not in PRIORITES_VALIDES:
            return False
        for e in self._entrees:
            if e["provider"] == provider and e["zone"] == zone:
                return False  # doublon exact
        self._entrees.append({
            "provider": provider,
            "zone": zone,
            "filtre": filtre or "none",
            "priorite": priorite,
        })
        return True

    def retirer(self, index):
        """Retire l'entrée à la position donnée. Renvoie True si fait."""
        if 0 <= index < len(self._entrees):
            del self._entrees[index]
            return True
        return False

    def vider(self):
        """Vide toute la sélection."""
        self._entrees = []

    # ── Modification d'une entrée ─────────────────────────────────────────────
    def changer_priorite(self, index, priorite):
        """Change la priorité d'une entrée. Refuse une valeur invalide."""
        if priorite not in PRIORITES_VALIDES:
            return False
        if 0 <= index < len(self._entrees):
            self._entrees[index]["priorite"] = priorite
            return True
        return False

    def changer_zone(self, index, zone):
        """Change la zone d'une entrée."""
        if 0 <= index < len(self._entrees):
            self._entrees[index]["zone"] = zone
            return True
        return False

    # ── Réordonnancement (l'ordre compte dans un .comb) ───────────────────────
    def monter(self, index):
        """Remonte l'entrée d'un cran (priorité d'écriture plus haute)."""
        if 0 < index < len(self._entrees):
            self._entrees[index - 1], self._entrees[index] = (
                self._entrees[index], self._entrees[index - 1])
            return True
        return False

    def descendre(self, index):
        """Descend l'entrée d'un cran."""
        if 0 <= index < len(self._entrees) - 1:
            self._entrees[index + 1], self._entrees[index] = (
                self._entrees[index], self._entrees[index + 1])
            return True
        return False


def suggerer_selection(vue, seuil_bon=70.0, max_auto=1):
    """
    Aide au démarrage pour l'utilisateur débutant (garde-fou anti-page-blanche).
    À partir de la vue du Chapitre 1 (triée par score décroissant), propose une
    sélection de départ : les 'max_auto' meilleurs providers ÉVALUÉS dont le
    score dépasse 'seuil_bon'. Ne devine rien de la géographie (ça viendra au
    Chapitre 3) — pose juste un point de départ que l'utilisateur ajustera.
    Renvoie une SelectionComb.
    """
    sel = SelectionComb()
    retenus = 0
    for item in vue:
        if not item.get("evalue"):
            continue
        if item.get("score") is None or item["score"] < seuil_bon:
            continue
        sel.ajouter(item["provider"], zone="", filtre="none", priorite="high")
        retenus += 1
        if retenus >= max_auto:
            break
    return sel


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 3 — DÉTECTION FRONTIÈRE + GARDE-FOUS
#  Rôle : à partir des zones qu'une tuile recouvre (une tuile mono-zone en
#  recouvre une seule ; une tuile FRONTIÈRE — cas alsacien FR/DE/CH/LUX — en
#  recouvre deux ou plus), décider POUR CHAQUE ZONE quel provider utiliser :
#     1) tuile mono-zone  → provider LOCAL par défaut, sans rien demander ;
#     2) zone sans provider local → REPLI sur un provider MONDIAL (Esri/BI/Maxar)
#        s'il est présent chez l'utilisateur ;
#     3) zone sans AUCUN provider disponible → message clair
#        « fournissez le lien pour la zone X » (aucun plantage, aucun blanc).
#
#  Ce chapitre ne lit AUCUN fichier et n'écrit RIEN : il travaille sur des
#  données déjà en mémoire (la vue du Chapitre 1 + une correspondance
#  provider → zones fournie par l'appelant, issue des Extents/). La géométrie
#  réelle « quelles zones cette tuile touche » est produite en amont par le
#  système Extents/ (module à part) ; le Chapitre 3 en consomme le résultat.
#  Il ne modifie ni le Chapitre 1 ni le Chapitre 2 : il ne fait que RÉUTILISER
#  l'API publique de SelectionComb (méthode .ajouter) pour proposer un panier.
# ══════════════════════════════════════════════════════════════════════════════

# Jetons de tête reconnus comme providers MONDIAUX (couverture planétaire).
# Une seule source de vérité, éditable ici. Comparaison sur le 1er jeton du nom
# du provider (ex. « Esri_07-2022 » → « esri »), insensible à la casse.
FOURNISSEURS_MONDIAUX = ("esri", "bi", "bing", "maxar", "arc", "google")


def _jeton_provider(nom_provider):
    """Retourne le 1er jeton alphanumérique du nom, en minuscules.
    Ex. « Esri_07-2022 » → « esri » ; « BI » → « bi » ; « IGN » → « ign »."""
    jeton = ""
    for ch in (nom_provider or ""):
        if ch.isalnum():
            jeton += ch
        else:
            break
    return jeton.lower()


def est_provider_mondial(nom_provider):
    """Vrai si le provider est un fournisseur mondial (repli possible)."""
    return _jeton_provider(nom_provider) in FOURNISSEURS_MONDIAUX


def construire_modele_zones(vue, provider_zones):
    """
    Assemble le « modèle de zones » utilisé par la résolution.

    Entrées :
      - vue : sortie de build_provider_view (Chapitre 1) — providers réels + scores.
      - provider_zones : dict { nom_provider : [zone1, zone2, ...] } décrivant,
        pour chaque provider LOCAL, la ou les zones qu'il couvre (issu des
        Extents/). Un provider mondial peut être absent de ce dict, ou porter
        ["*"] : il ira dans « mondiaux », jamais dans une zone locale.

    Sortie (dict) :
      {
        "zones"    : { zone : [providers locaux, meilleur d'abord] },
        "mondiaux" : [providers mondiaux, meilleur d'abord],
        "scores"   : { provider : score (float) ou None si non évalué },
        "locaux_sans_zone" : [providers locaux dont la zone est inconnue],
      }
    """
    scores = {}
    for item in vue:
        scores[item["provider"]] = item.get("score")

    zones = {}
    mondiaux = []
    locaux_sans_zone = []

    for item in vue:
        p = item["provider"]
        zlist = provider_zones.get(p, [])
        # Un provider est « mondial » soit par son nom, soit par la marque ["*"].
        if est_provider_mondial(p) or zlist == ["*"]:
            if p not in mondiaux:
                mondiaux.append(p)
            continue
        if not zlist:
            # Provider local dont on ne connaît pas la zone (pas d'extent).
            locaux_sans_zone.append(p)
            continue
        for z in zlist:
            zones.setdefault(z, [])
            if p not in zones[z]:
                zones[z].append(p)

    # Tri « meilleur d'abord » : score décroissant (non évalué = -1), puis nom.
    def _cle(prov):
        s = scores.get(prov)
        return (-(s if s is not None else -1.0), prov)

    for z in zones:
        zones[z].sort(key=_cle)
    mondiaux.sort(key=_cle)
    locaux_sans_zone.sort(key=_cle)

    return {
        "zones": zones,
        "mondiaux": mondiaux,
        "scores": scores,
        "locaux_sans_zone": locaux_sans_zone,
    }


def _meilleur(candidats, scores, seam_risk):
    """
    Choisit le meilleur provider d'une liste :
      - score le plus haut d'abord (non évalué compté comme -1) ;
      - à score égal, le seam_risk (risque de jointure) le plus BAS d'abord
        (utile en frontière) ; seam_risk absent = 0.0 (aucun risque connu) ;
      - à égalité, ordre alphabétique (déterministe).
    seam_risk est un dict optionnel { provider : risque (float) }.
    """
    if not candidats:
        return None
    sr = seam_risk or {}

    def _cle(prov):
        s = scores.get(prov)
        r = sr.get(prov, 0.0)
        try:
            r = float(r)
        except (TypeError, ValueError):
            r = 0.0
        return (-(s if s is not None else -1.0), r, prov)

    return sorted(candidats, key=_cle)[0]


def resoudre_zone(zone, modele, seam_risk=None):
    """
    Résout UNE zone selon les trois cas de la Bible.
    Retourne un dict :
      { "zone", "provider", "origine", "score", "priorite", "message" }
    origine ∈ { "local", "repli_mondial", "manque" }.
    Règle de priorité : LOCAL = "high" (l'imagerie locale prime sur son
    territoire) ; REPLI MONDIAL = "low" (ne doit jamais recouvrir un local).
    """
    scores = modele["scores"]

    locaux = modele["zones"].get(zone, [])
    if locaux:
        p = _meilleur(locaux, scores, seam_risk)
        return {
            "zone": zone, "provider": p, "origine": "local",
            "score": scores.get(p), "priorite": "high", "message": None,
        }

    mondiaux = modele["mondiaux"]
    if mondiaux:
        p = _meilleur(mondiaux, scores, seam_risk)
        return {
            "zone": zone, "provider": p, "origine": "repli_mondial",
            "score": scores.get(p), "priorite": "low",
            "message": ("Zone « %s » : aucun provider local, repli mondial "
                        "sur %s." % (zone, p)),
        }

    return {
        "zone": zone, "provider": None, "origine": "manque",
        "score": None, "priorite": None,
        "message": ("Aucun provider disponible pour la zone « %s ». "
                    "Fournissez le lien (.lay + extent) pour cette zone."
                    % zone),
    }


def resoudre_tuile(zones_de_la_tuile, modele, seam_risk=None):
    """
    Résout une tuile complète à partir de la liste des zones qu'elle recouvre.
      - 1 zone   → tuile mono-zone (cas 1) ;
      - 2 zones+ → tuile FRONTIÈRE (cas alsacien) : une résolution par zone,
                   ce qui produit légitimement plusieurs lignes .comb (même
                   provider possible deux fois si la zone diffère — accepté par
                   le Chapitre 2).
    Retourne un « plan » :
      {
        "zones"       : [zones demandées, sans doublon, ordre conservé],
        "resolutions" : [dict resoudre_zone, un par zone],
        "manques"     : [zones sans aucun provider],
        "messages"    : [messages à afficher à l'utilisateur],
        "frontiere"   : bool (True si 2 zones distinctes ou plus),
      }
    """
    # dédoublonnage en conservant l'ordre d'arrivée
    zones = []
    for z in (zones_de_la_tuile or []):
        if z not in zones:
            zones.append(z)

    plan = {
        "zones": zones,
        "resolutions": [],
        "manques": [],
        "messages": [],
        "frontiere": len(zones) >= 2,
    }

    if not zones:
        plan["messages"].append(
            "Zones de la tuile inconnues : impossible de résoudre. "
            "Renseignez les zones de la tuile (via les Extents/).")
        return plan

    for z in zones:
        r = resoudre_zone(z, modele, seam_risk)
        plan["resolutions"].append(r)
        if r["origine"] == "manque":
            plan["manques"].append(z)
        if r["message"]:
            plan["messages"].append(r["message"])

    return plan


def appliquer_plan_a_selection(plan, selection):
    """
    Reporte un plan dans une SelectionComb (Chapitre 2) via sa seule API
    publique .ajouter — le Chapitre 2 n'est pas modifié. Les zones en
    « manque » (provider None) sont ignorées (rien à ajouter, un message a déjà
    été émis). Retourne le nombre de lignes réellement ajoutées.
    """
    ajouts = 0
    for r in plan.get("resolutions", []):
        if r.get("provider"):
            ok = selection.ajouter(
                r["provider"], zone=r["zone"], filtre="none",
                priorite=(r["priorite"] or "medium"))
            if ok:
                ajouts += 1
    return ajouts


def afficher_resolution(plan):
    """Affiche un plan en texte (test headless, aucune interface graphique)."""
    print("Tuile %s — zones : %s"
          % ("FRONTIÈRE" if plan["frontiere"] else "mono-zone",
             ", ".join(plan["zones"]) or "(aucune)"))
    print("-" * 60)
    for r in plan["resolutions"]:
        if r["origine"] == "manque":
            print("  %-14s  → MANQUE (aucun provider)" % r["zone"])
        else:
            sc = "  —  " if r["score"] is None else ("%5.1f" % r["score"])
            print("  %-14s  → %-22s [%s] %s / %s"
                  % (r["zone"], r["provider"], sc,
                     r["origine"], r["priorite"]))
    if plan["messages"]:
        print("-" * 60)
        for m in plan["messages"]:
            print("  ⚠ " + m)
    print("-" * 60)
    return plan


def _demo_chapitre3():
    """
    Démonstration headless du Chapitre 3 (n'écrit rien, ne lit rien sur disque).
    Reproduit le besoin alsacien : une tuile mono-zone FR, une tuile frontière
    FR/DE, une zone étrangère sans provider. Sert à vérifier la logique sans
    interface. N'est jamais appelée automatiquement.
    """
    vue = [
        {"provider": "IGN_FR",     "score": 88.5, "label": "", "evalue": True},
        {"provider": "DE_Bayern",  "score": 72.0, "label": "", "evalue": True},
        {"provider": "Esri_07-2022","score": 61.0,"label": "", "evalue": True},
        {"provider": "BI",         "score": None, "label": "", "evalue": False},
    ]
    provider_zones = {
        "IGN_FR":    ["FR"],
        "DE_Bayern": ["DE"],
        # Esri et BI : mondiaux (détectés par le nom), pas de zone locale.
    }
    modele = construire_modele_zones(vue, provider_zones)

    print("\n### Cas 1 — tuile mono-zone FR")
    afficher_resolution(resoudre_tuile(["FR"], modele))

    print("\n### Cas frontière — tuile FR/DE (Alsace)")
    afficher_resolution(resoudre_tuile(["FR", "DE"], modele))

    print("\n### Cas 2 — zone CH sans provider local → repli mondial")
    afficher_resolution(resoudre_tuile(["CH"], modele))

    print("\n### Cas 3 — zone étrangère sans AUCUN provider")
    modele_vide = construire_modele_zones(
        [{"provider": "IGN_FR", "score": 88.5, "label": "", "evalue": True}],
        {"IGN_FR": ["FR"]})
    afficher_resolution(resoudre_tuile(["LUX"], modele_vide))


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 4 — GÉNÉRATION DU FICHIER .comb
#  Rôle : transformer une SelectionComb (Chapitre 2, éventuellement remplie par
#  le plan du Chapitre 3) en un vrai fichier .comb, au format EXACT d'Ortho4XP.
#
#  Format observé sur EUR.comb (référence communauté) :
#     - 4 colonnes séparées par des ESPACES (jamais de tabulation) :
#          provider(13) | zone/extent(15) | filtre(8) | priorité
#     - lignes « # … » = commentaires ; lignes vides ignorées ;
#     - fins de ligne Unix (\n).
#
#  GARDE-FOUS (Bible) :
#     - ZonePhoto.comb est INTOUCHABLE : toute écriture visant un fichier dont
#       le nom contient « zonephoto » est REFUSÉE, sans discussion.
#     - Aucun .comb existant n'est écrasé en silence : si le fichier existe,
#       l'écriture n'a lieu que si forcer=True, et une sauvegarde « .bak » est
#       créée AVANT tout écrasement.
#     - Écriture atomique (fichier temporaire puis remplacement) : jamais de
#       .comb à moitié écrit si une coupure survient.
#     - Validation préalable : provider vide, zone vide ou priorité invalide
#       bloquent l'écriture (message clair, rien n'est écrit).
#  Ce chapitre ne modifie ni le Chapitre 1, ni le 2, ni le 3.
# ══════════════════════════════════════════════════════════════════════════════

# Largeurs de colonnes reproduisant EUR.comb (cosmétique ; Ortho4XP découpe au
# blanc, mais on garde l'alignement pour un fichier lisible et « communautaire »).
_COL_PROVIDER = 13
_COL_ZONE = 15
_COL_FILTRE = 8


def _cellule(texte, largeur):
    """Complète 'texte' à 'largeur' avec des espaces, en garantissant TOUJOURS
    au moins 2 espaces de séparation (même si le nom dépasse la largeur)."""
    texte = "" if texte is None else str(texte)
    manque = largeur - len(texte)
    return texte + " " * (manque if manque >= 2 else 2)


def formater_ligne(provider, zone, filtre="none", priorite="medium"):
    """Formate UNE ligne .comb alignée (sans le saut de ligne final)."""
    return (_cellule(provider, _COL_PROVIDER)
            + _cellule(zone, _COL_ZONE)
            + _cellule(filtre or "none", _COL_FILTRE)
            + str(priorite)).rstrip()


def valider_selection(selection):
    """
    Vérifie qu'une SelectionComb est écrivable telle quelle.
    Retourne (ok: bool, problemes: [str]).
    Refuse : provider vide, zone vide (un .comb exige un extent par ligne),
    priorité hors low/medium/high. Signale aussi une sélection vide.
    """
    problemes = []
    entrees = selection.entrees()
    if not entrees:
        problemes.append("Sélection vide : rien à écrire.")
    for i, e in enumerate(entrees):
        if not (e.get("provider") or "").strip():
            problemes.append("Ligne %d : provider vide." % (i + 1))
        if not (e.get("zone") or "").strip():
            problemes.append(
                "Ligne %d : zone/extent vide (provider « %s »). "
                "Chaque ligne .comb doit cibler une zone."
                % (i + 1, e.get("provider", "?")))
        if e.get("priorite") not in PRIORITES_VALIDES:
            problemes.append(
                "Ligne %d : priorité « %s » invalide (attendu low/medium/high)."
                % (i + 1, e.get("priorite")))
    return (len(problemes) == 0, problemes)


def construire_texte_comb(selection, entete_lignes=None):
    """
    Construit le TEXTE complet du .comb à partir d'une SelectionComb.
    L'ordre des lignes = l'ordre de la sélection (il compte : la priorité et
    l'ordre décident des recouvrements). Ne fait AUCUNE écriture disque.
    entete_lignes : liste de lignes de commentaire (sans le « # »). Si None, un
    en-tête générique est posé.
    """
    if entete_lignes is None:
        entete_lignes = [
            "Combined layer généré par Ortho4XP V3 (module .comb assisté).",
            "Éditable : ajustez zones, filtres et priorités selon vos besoins.",
        ]
    lignes = ["# " + l for l in entete_lignes]
    lignes.append("")  # ligne vide de séparation, comme EUR.comb
    for e in selection.entrees():
        lignes.append(formater_ligne(
            e["provider"], e["zone"], e.get("filtre", "none"), e["priorite"]))
    return "\n".join(lignes) + "\n"


def _est_zonephoto(chemin):
    """Vrai si le chemin vise un fichier ZonePhoto.comb (intouchable)."""
    return "zonephoto" in os.path.basename(chemin).lower()


def ecrire_comb(selection, chemin, entete_lignes=None, forcer=False,
                confirmer_zonephoto=False):
    """
    Écrit la sélection dans un fichier .comb, avec tous les garde-fous.
    Retourne (ok: bool, message: str).

    Cas ZonePhoto.comb (fichier PERSONNEL de Roland — jamais un référent, jamais
    publié, mais ÉDITABLE en local) : l'écriture n'est autorisée que si
    confirmer_zonephoto=True (double sécurité : confirmation explicite + .bak).
    Sans ce drapeau, l'écriture est refusée pour éviter toute modification
    accidentelle.

    Refus (rien n'est écrit) si :
      - le fichier ciblé est ZonePhoto.comb et confirmer_zonephoto=False ;
      - la sélection est invalide (voir valider_selection) ;
      - le fichier existe déjà et forcer=False.
    Si le fichier existe et forcer=True : une sauvegarde « <fichier>.bak » est
    créée avant remplacement. Écriture atomique (tmp puis os.replace), LF forcé.
    """
    import shutil

    if _est_zonephoto(chemin) and not confirmer_zonephoto:
        return (False, "ZonePhoto.comb est ton fichier personnel. "
                       "Confirme explicitement pour le modifier "
                       "(une sauvegarde .bak sera créée).")

    ok, problemes = valider_selection(selection)
    if not ok:
        return (False, "REFUS : sélection non écrivable.\n  - "
                + "\n  - ".join(problemes))

    existe = os.path.isfile(chemin)
    if existe and not forcer:
        return (False, "Le fichier « %s » existe déjà. "
                       "Relancez avec forcer=True pour le remplacer "
                       "(une sauvegarde .bak sera créée automatiquement)."
                       % chemin)

    texte = construire_texte_comb(selection, entete_lignes)

    dossier = os.path.dirname(os.path.abspath(chemin))
    try:
        if existe:  # forcer=True garanti ici
            shutil.copy2(chemin, chemin + ".bak")
        # écriture atomique : on écrit à côté puis on remplace
        tmp = os.path.join(dossier, ".__comb_tmp__")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(texte)
        os.replace(tmp, chemin)
    except Exception as ex:
        return (False, "ERREUR d'écriture : %s" % ex)

    nb = selection.taille()
    suffixe = " (ancien fichier sauvegardé en .bak)" if existe else ""
    return (True, "Fichier .comb écrit : %s — %d ligne(s)%s."
            % (chemin, nb, suffixe))


def apercu_comb(selection):
    """Affiche le .comb qui serait produit, sans rien écrire (test headless)."""
    ok, problemes = valider_selection(selection)
    if not ok:
        print("Sélection non écrivable :")
        for p in problemes:
            print("  - " + p)
        print("-" * 60)
    print(construire_texte_comb(selection), end="")
    print("-" * 60)


def _demo_chapitre4():
    """
    Démonstration headless du Chapitre 4. N'écrit QUE dans un dossier temporaire
    système (jamais dans le projet). Montre : aperçu, écriture réelle, relecture,
    refus ZonePhoto, refus d'écrasement, puis écrasement avec .bak.
    """
    import tempfile

    sel = SelectionComb()
    sel.ajouter("FRorth", zone="France", filtre="none", priorite="medium")
    sel.ajouter("DOP40", zone="Germany", filtre="none", priorite="medium")
    sel.ajouter("Esri_07-2022", zone="Switzerland", filtre="none", priorite="low")

    print("### Aperçu du .comb (aucune écriture)")
    apercu_comb(sel)

    tmp = tempfile.mkdtemp(prefix="comb_demo_")
    cible = os.path.join(tmp, "MON_EUROPE.comb")

    print("\n### Écriture réelle (fichier neuf)")
    print("  ", ecrire_comb(sel, cible)[1])

    print("\n### Relecture du fichier écrit")
    with open(cible, encoding="utf-8") as fp:
        print(fp.read(), end="")
    print("-" * 60)

    print("\n### Refus ZonePhoto.comb")
    print("  ", ecrire_comb(sel, os.path.join(tmp, "ZonePhoto.comb"))[1])

    print("\n### Refus d'écrasement sans forcer")
    print("  ", ecrire_comb(sel, cible)[1])

    print("\n### Écrasement autorisé (forcer=True) → sauvegarde .bak")
    print("  ", ecrire_comb(sel, cible, forcer=True)[1])
    print("   .bak présent :", os.path.isfile(cible + ".bak"))


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 5 — IMPORT D'UN FICHIER .comb EXISTANT
#  Rôle : ouvrir un .comb déjà écrit (celui d'un expert, ou un ancien fichier)
#  et le recharger dans une SelectionComb (Chapitre 2), pour le MODIFIER dans
#  l'interface puis le RÉÉCRIRE en fichier neuf (Chapitre 4). C'est la 2e porte
#  d'entrée de l'interface : « j'importe et j'ajuste » vs « je pars de zéro ».
#
#  Points vérifiés sur les vrais fichiers (EUR.comb + ZonePhoto.comb) :
#     - 4 colonnes : provider | zone | filtre | priorité ;
#     - le séparateur peut être des ESPACES (EUR.comb) OU des TABULATIONS
#       (ZonePhoto.comb) → on découpe sur tout blanc (split universel) ;
#     - la colonne 3 (filtre) n'est PAS toujours « none » (patches en ZonePhoto)
#       → on la PRÉSERVE telle quelle, on ne la réécrit jamais ;
#     - priorités réelles : uniquement low / medium / high.
#
#  Robustesse : une ligne qui n'a pas 4 colonnes, ou une priorité inconnue, est
#  ÉCARTÉE et SIGNALÉE dans un rapport — jamais de plantage. Commentaires « # »
#  et lignes vides ignorés. ZonePhoto.comb n'est jamais importé (intouchable).
#  Ce chapitre ne modifie ni les chapitres 1, 2, 3 ni 4.
# ══════════════════════════════════════════════════════════════════════════════

def parser_lignes_comb(texte):
    """
    Analyse le TEXTE d'un .comb et retourne (entrees, rapport).
      - entrees : liste de dict {provider, zone, filtre, priorite}, ordre du
        fichier conservé. La colonne filtre est gardée telle quelle.
      - rapport : liste de messages sur les lignes écartées (n° + raison).
    Ne lit rien sur disque ; travaille sur une chaîne (facile à tester).
    """
    entrees = []
    rapport = []
    for no, brute in enumerate(texte.splitlines(), start=1):
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        champs = ligne.split()  # découpe sur espaces ET tabulations
        if len(champs) != 4:
            rapport.append("Ligne %d écartée : %d colonne(s) au lieu de 4 "
                           "→ %r" % (no, len(champs), ligne))
            continue
        provider, zone, filtre, priorite = champs
        if priorite not in PRIORITES_VALIDES:
            rapport.append("Ligne %d écartée : priorité « %s » inconnue "
                           "(attendu low/medium/high)." % (no, priorite))
            continue
        entrees.append({
            "provider": provider,
            "zone": zone,
            "filtre": filtre,   # PRÉSERVÉ (peut être « none » ou un patch)
            "priorite": priorite,
        })
    return entrees, rapport


def importer_comb(chemin):
    """
    Importe un fichier .comb dans une SelectionComb.
    Retourne (selection, rapport) où rapport est une liste de messages.

    Refus (selection None) si :
      - le fichier est introuvable ou illisible.
    ZonePhoto.comb (fichier personnel de Roland) PEUT être importé pour édition
    locale ; on le signale seulement dans le rapport, sans bloquer. Sa
    réécriture, elle, reste protégée par confirmer_zonephoto (voir ecrire_comb).
    Les lignes mal formées sont écartées et listées dans le rapport ; l'import
    n'échoue pas pour autant (le reste est importé).
    """
    note_zp = None
    if _est_zonephoto(chemin):
        note_zp = ("ZonePhoto.comb (fichier personnel) importé pour édition "
                   "locale — il ne sera jamais publié.")
    if not os.path.isfile(chemin):
        return (None, ["Fichier introuvable : %s" % chemin])
    try:
        with open(chemin, encoding="utf-8") as fp:
            texte = fp.read()
    except Exception as ex:
        return (None, ["ERREUR de lecture : %s" % ex])

    entrees, rapport = parser_lignes_comb(texte)

    sel = SelectionComb()
    ignorees = 0
    for e in entrees:
        # On réutilise l'API publique du Chapitre 2 (ajouter), qui refuse les
        # doublons EXACTS provider+zone. Un doublon exact dans le fichier source
        # est donc signalé plutôt que dupliqué.
        ok = sel.ajouter(e["provider"], zone=e["zone"],
                         filtre=e["filtre"], priorite=e["priorite"])
        if not ok:
            ignorees += 1
            rapport.append("Doublon exact ignoré : %s / %s"
                           % (e["provider"], e["zone"]))

    rapport.insert(0, "Import : %d ligne(s) retenue(s)%s."
                   % (sel.taille(),
                      (", %d écartée(s)/ignorée(s)" % (len(entrees) - sel.taille() + ignorees))
                      if (len(entrees) != sel.taille() or ignorees) else ""))
    if note_zp:
        rapport.insert(1, note_zp)
    return (sel, rapport)


def _demo_chapitre5():
    """
    Démonstration headless du Chapitre 5. N'écrit QUE dans un dossier temporaire
    système. Montre : import d'un .comb « espaces », import d'un .comb
    « tabulations » avec filtre non-none préservé, ligne mal formée écartée,
    aller-retour fidèle (import → réécriture identique), refus ZonePhoto.
    """
    import tempfile

    tmp = tempfile.mkdtemp(prefix="comb_import_")

    # 1) fichier style EUR.comb (espaces) + une ligne cassée (3 colonnes)
    src1 = os.path.join(tmp, "EUR_like.comb")
    with open(src1, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("# en-tete\n\n"
                 "FRorth       France         none    medium\n"
                 "DOP40        Germany        none    high\n"
                 "LigneCassee  SansPriorite\n")           # 3 colonnes → écartée
    sel1, rap1 = importer_comb(src1)
    print("### Import style EUR (espaces)")
    for m in rap1:
        print("  -", m)
    print("   entrées :", sel1.entrees())

    # 2) fichier style ZonePhoto (tabulations) avec filtre = patch (non none)
    src2 = os.path.join(tmp, "TAB_like.comb")
    with open(src2, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("A_Provider\tA_Zone\tA_Patch_Filtre\thigh\n"
                 "B_Provider\tB_Zone\tnone\tmedium\n")
    sel2, rap2 = importer_comb(src2)
    print("\n### Import style ZonePhoto (tabulations, filtre préservé)")
    for m in rap2:
        print("  -", m)
    print("   entrées :", sel2.entrees())

    # 3) aller-retour fidèle : on réécrit sel2 et on relit → identique ?
    cible = os.path.join(tmp, "reecrit.comb")
    ecrire_comb(sel2, cible)
    sel3, _ = importer_comb(cible)
    print("\n### Aller-retour import→écriture→import fidèle :",
          sel2.entrees() == sel3.entrees())

    # 4) refus ZonePhoto
    zp = os.path.join(tmp, "ZonePhoto.comb")
    with open(zp, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("X\tY\tnone\tlow\n")
    selzp, rapzp = importer_comb(zp)
    print("\n### Import ZonePhoto AUTORISÉ (édition locale) :",
          selzp is not None, "|", rapzp[1] if len(rapzp) > 1 else rapzp[0])
    print("### Écriture ZonePhoto SANS confirmation (refusée) :",
          ecrire_comb(selzp, zp, forcer=True)[1])
    print("### Écriture ZonePhoto AVEC confirmation (+.bak) :",
          ecrire_comb(selzp, zp, forcer=True, confirmer_zonephoto=True)[1])


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 7 — BRANCHEMENT AUTOMATIQUE DEPUIS LES EXTENTS
#  Rôle : reproduire AUTOMATIQUEMENT ce que Roland fait à la main dans son
#  ZonePhoto.comb, mais dans un fichier propre et diffusable
#  (Provider_Extents.comb), rangé dans Providers/ pour qu'Ortho le charge et
#  affiche l'entrée « Provider_Extents » dans la liste imagery.
#
#  Chaîne complète (chantier bouclé) :
#     1. l'utilisateur choisit un provider dans imagery      → default_website
#     2. l'utilisateur crée ses extents (module Extents)      → Extents/<pays>/
#     3. CE CHAPITRE lit les extents + le provider actif      → SelectionComb
#     4. le Chapitre 4 (ecrire_comb) écrit Provider_Extents.comb
#     5. Ortho scanne Providers/, charge le .comb             → imagery
#
#  Réutilise les Chapitres 2 (SelectionComb) et 4 (ecrire_comb) — ne les modifie
#  pas. Ne touche JAMAIS ZonePhoto.comb (nom de sortie fixe et distinct).
# ══════════════════════════════════════════════════════════════════════════════

# Nom FIXE du fichier de sortie (jamais « zonephoto » → garde-fou du Chapitre 4
# satisfait, et ZonePhoto.comb personnel de Roland jamais menacé).
COMB_OUTPUT_NAME = "Provider_Extents.comb"


def _find_names_module():
    """Récupère O4_File_Names s'il est déjà chargé (Ortho tourne), sinon None."""
    import sys
    return sys.modules.get("O4_File_Names")


def _extents_dir_auto(base_dir=None):
    """Dossier Extents/. Priorité : O4_File_Names.Extent_dir (source Ortho) ;
    repli : <base_dir>/Extents ; dernier repli : ./Extents."""
    FN = _find_names_module()
    if FN is not None and getattr(FN, "Extent_dir", None):
        return FN.Extent_dir
    if base_dir:
        return os.path.join(base_dir, "Extents")
    return os.path.join(os.getcwd(), "Extents")


def _providers_dir_auto(base_dir=None):
    """Dossier Providers/. Même logique que _extents_dir_auto."""
    FN = _find_names_module()
    if FN is not None and getattr(FN, "Provider_dir", None):
        return FN.Provider_dir
    if base_dir:
        return os.path.join(base_dir, "Providers")
    return os.path.join(os.getcwd(), "Providers")


def scanner_extents(base_dir=None):
    """Parcourt Extents/ et renvoie la liste triée, sans doublon, des codes
    d'extent (nom de fichier .ext sans extension). Voit AUTOMATIQUEMENT tout
    extent présent : les anciens comme ceux tout juste créés. Jamais
    d'exception : en cas de souci disque, renvoie ce qui a pu être lu."""
    edir = _extents_dir_auto(base_dir)
    trouves = []
    seen = set()
    try:
        sous_dossiers = os.listdir(edir)
    except Exception:
        return []
    for dossier in sorted(sous_dossiers):
        chemin = os.path.join(edir, dossier)
        if not os.path.isdir(chemin):
            continue
        try:
            fichiers = os.listdir(chemin)
        except Exception:
            continue
        for f in fichiers:
            if "." not in f or f.rsplit(".", 1)[-1].lower() != "ext":
                continue
            code = f.rsplit(".", 1)[0]
            if code and code not in seen:
                seen.add(code)
                trouves.append(code)
    trouves.sort(key=lambda s: s.lower())
    return trouves


def construire_selection_depuis_extents(provider_actif, extents,
                                        priorite="medium", filtre="none"):
    """Construit une SelectionComb (Chapitre 2) : une ligne par extent, reliant
    le PROVIDER ACTIF (choisi dans imagery) à cet extent. Réutilise la classe
    SelectionComb existante et sa méthode .ajouter (aucune modification du
    Chapitre 2). Renvoie (selection, nb_ajouts)."""
    provider_actif = (provider_actif or "").strip()
    if not provider_actif:
        return (None, 0)
    sel = SelectionComb()
    n = 0
    for code in extents:
        code = (code or "").strip()
        if not code:
            continue
        if sel.ajouter(provider_actif, zone=code, filtre=filtre,
                       priorite=priorite):
            n += 1
    return (sel, n)


def generer_comb_depuis_extents(provider_actif, base_dir=None,
                                priorite="medium", forcer=True, log=None):
    """Génère Providers/Provider_Extents.comb à partir de TOUS les extents
    présents dans Extents/, reliés au provider_actif.

    - provider_actif : nom du provider choisi dans imagery (default_website).
    - forcer=True : régénère si le fichier existe (le Chapitre 4 fait une .bak).
    - log : fonction d'affichage optionnelle.
    Renvoie (ok: bool, message: str). Ne lève jamais d'exception. Réutilise
    ecrire_comb (Chapitre 4) pour l'écriture sécurisée."""
    def _say(m):
        if callable(log):
            try:
                log(m)
            except Exception:
                pass

    extents = scanner_extents(base_dir)
    if not extents:
        return (False, "Aucun extent trouvé dans Extents/ — rien à brancher.")

    provider_actif = (provider_actif or "").strip()
    if not provider_actif:
        return (False, "Aucun provider actif fourni (imagery non sélectionnée).")

    sel, n = construire_selection_depuis_extents(provider_actif, extents,
                                                 priorite=priorite)
    if sel is None or n == 0:
        return (False, "Impossible de construire la sélection.")

    _say("Provider actif : %s" % provider_actif)
    _say("%d extent(s) à brancher." % n)

    pdir = _providers_dir_auto(base_dir)
    try:
        os.makedirs(pdir, exist_ok=True)
    except Exception as ex:
        return (False, "Dossier Providers/ inaccessible : %s" % ex)

    chemin = os.path.join(pdir, COMB_OUTPUT_NAME)
    entete = [
        "Provider_Extents.comb — genere automatiquement par Ortho4XP V3.",
        "Relie le provider actif aux extents crees. Editable a la main.",
        "Provider : %s" % provider_actif,
    ]
    return ecrire_comb(sel, chemin, entete_lignes=entete, forcer=forcer)


def recharger_comb_a_chaud():
    """Après écriture, demande à Ortho de re-scanner Providers/ pour que la
    nouvelle entrée « Provider_Extents » apparaisse dans imagery sans relancer.
    Protégé : True si réussi, False sinon (repli : relancer Ortho)."""
    try:
        import sys
        IMG = sys.modules.get("O4_Imagery_Utils")
        if IMG is None:
            return False
        fn = getattr(IMG, "initialize_combined_providers_dict", None)
        if not callable(fn):
            return False
        fn()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 6 — INTERFACE GRAPHIQUE (fenêtre « Générer un .comb »)  — v1
#  Rôle : poser un VISAGE sur le moteur (chapitres 1-5). Produit UN .comb
#  GLOBAL (style EUR.comb : multi-provider / multi-tuile), écrit dans Providers/.
#
#  v1 (cette étape) :
#     - liste des providers réels + score (Chapitre 1), cases à cocher ;
#     - colonne ZONE (extent) éditable + PRIORITÉ en menu déroulant 3 choix
#       (haute / moyenne / basse), JAMAIS de saisie clavier pour la priorité ;
#     - bouton « Remplir automatiquement » (suggère une sélection de départ) ;
#     - bouton « Importer un .comb » (Chapitre 5) ;
#     - « Aperçu » (Chapitre 4) et « Générer » (écrit dans Providers/, refuse
#       ZonePhoto, .bak + confirmation si le fichier existe).
#
#  Style calqué sur O4_lay_generator.py : thème O4_Theme_Manager, boutons
#  Mac-safe = Frame+Label (JAMAIS tk.Button), combobox « O4Comb.TCombobox ».
#  Aucune logique métier nouvelle ici : on n'appelle que les chapitres 1-5.
# ══════════════════════════════════════════════════════════════════════════════

# Détection OS (même logique que les autres modules).
import sys as _sys
if "dar" in _sys.platform:
    _OS_UI = "mac"
elif "win" in _sys.platform:
    _OS_UI = "windows"
else:
    _OS_UI = "linux"

# Thème (facultatif : fallback si absent → jamais de plantage).
try:
    import O4_Theme_Manager as _TMC
    _HAS_THEME_C = True
except Exception:
    _TMC = None
    _HAS_THEME_C = False


def _cc(key, fallback):
    """Couleur du thème actif, ou fallback."""
    if _HAS_THEME_C:
        try:
            return _TMC.get_theme().get(key, fallback)
        except Exception:
            return fallback
    return fallback


# On utilise des clés techniques neutres en anglais, et _tr() fait le travail selon la langue active
_PRIO_AFF = {"high": _tr("high"), "medium": _tr("medium"), "low": _tr("low")}
_PRIO_VAL = {_tr("high"): "high", _tr("medium"): "medium", _tr("low"): "low"}
_PRIO_LISTE = (_tr("high"), _tr("medium"), _tr("low"))


def _make_themed_button_c(tk, parent, text, command):
    """Bouton Mac-safe (Frame+Label), identique au patron du .lay."""
    bg = _cc("btn_bg", "#4a6b59")
    fg = _cc("btn_fg", "#ffffff")
    hover = _cc("accent", "#5a7b69")
    active = _cc("fg_secondary", "#a6e3a1")
    frame = tk.Frame(parent, bg=bg, highlightthickness=1,
                     highlightbackground=bg, highlightcolor=active, bd=0)
    label = tk.Label(frame, text=text, bg=bg, fg=fg, padx=10, pady=5,
                     font=("Helvetica", 12) if _OS_UI == "mac" else ("Segoe UI", 10),
                     cursor="hand2")
    label.pack(fill="both", expand=True)

    def on_enter(e=None):
        frame.configure(bg=hover); label.configure(bg=hover)

    def on_leave(e=None):
        frame.configure(bg=bg); label.configure(bg=bg)

    def on_click(e=None):
        frame.configure(bg=active); label.configure(bg=active)

    def on_release(e=None):
        frame.configure(bg=hover); label.configure(bg=hover)
        if callable(command):
            command()

    for w in (frame, label):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)
        w.bind("<ButtonRelease-1>", on_release)
    return frame


def run_comb_creer(parent=None):
    """
    MODE 1 — « Créer un nouveau .comb » (liste des providers à cocher).
    Fenêtre INCHANGÉE (le mode qui fonctionne) : on coche les providers, on
    renseigne zone / filtre / priorité, puis Aperçu / Générer. Chargée seulement
    au clic. parent = fenêtre principale Ortho4XP (ou None en test isolé).
    Retourne la fenêtre. Appelée par le sélecteur run_comb_generator (écran de
    choix). L'ancien bouton « Importer un .comb » (qui cochait par erreur dans
    la liste figée) a été RETIRÉ : l'import se fait désormais en mode 2
    (run_comb_corriger), une ligne du fichier = une ligne éditable.
    """
    import tkinter as tk
    from tkinter import ttk, messagebox

    BG = _cc("bg", "#3b5b49")
    FG = _cc("fg", "#e8f0ec")
    FG2 = _cc("fg_secondary", "#a6e3a1")
    CON_BG = _cc("console_bg", "#0f0f1a")
    CON_FG = _cc("console_fg", "#50fa7b")
    ENTRY_BG = "#f0f4f2"
    ENTRY_FG = "#1e3028"
    # Police normale — MANQUAIT dans cette fonction : sans elle, la création du
    # label d'aide levait un NameError, d'où le message d'aide jamais affiché.
    FONT_N = ("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)

    # Racine Ortho4XP → dossier Providers/ (là où vivent EUR.comb, etc.).
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prov_dir = _providers_dir(base_dir)

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_tr("Créer un nouveau .comb"))
    win.configure(bg=BG)
    # Fenêtre dimensionnée et redimensionnable (cohérence avec l'assembleur ;
    # évite les libellés/boutons coupés selon la plateforme).
    try:
        win.geometry("1180x800")
        win.minsize(1000, 600)
        win.resizable(True, True)
    except Exception:
        pass

    # Style combobox (couleurs thème + fix macOS), comme le .lay.
    style = ttk.Style(win)
    try:
        style.theme_use("alt")
    except Exception:
        pass
    style.configure("O4Comb.TCombobox", fieldbackground=ENTRY_BG,
                    background=ENTRY_BG, foreground=ENTRY_FG)

    # Vue providers + scores (Chapitre 1).
    vue = build_provider_view(base_dir)

    # État : une ligne d'IHM par provider (case cochée, zone, priorité).
    lignes = []  # liste de dict {provider, score, var_check, var_zone, var_prio}

    tk.Label(win, text=_tr("Générer un .comb global (style EUR.comb)"),
             bg=BG, fg=FG,
             font=("Helvetica", 14, "bold") if _OS_UI == "mac"
             else ("Segoe UI", 12, "bold")).pack(fill="x", padx=12, pady=(10, 2))
    tk.Label(win, text=_tr("Coche les providers, choisis zone, filtre et priorité, puis Générer."),
             bg=BG, fg=FG2,
             font=("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=12, pady=(0, 8))

    # ── Bas de fenêtre ANCRÉ — créé et empilé AVANT la liste ─────────────────
    # Empilé en bas (side='bottom') AVANT la zone scrollable : si la fenêtre
    # manque de hauteur, c'est la LISTE (défilable) qui cède de la place, JAMAIS
    # le bas. Le message d'aide, les boutons et Fermer restent donc TOUJOURS
    # visibles. Les enfants du bas sont ajoutés plus bas dans le code.
    foot = tk.Frame(win, bg=BG)
    foot.pack(side="bottom", fill="x")

    # ── Zone scrollable listant les providers (défilement vertical) ──────────
    cadre = tk.Frame(win, bg=BG)
    cadre.pack(side="top", fill="both", expand=True, padx=12, pady=4)
    canvas = tk.Canvas(cadre, bg=BG, highlightthickness=0, height=280)
    scroll = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # En-tête + rangées dans UNE SEULE grille partagée (inner) : chaque colonne
    # tombe donc exactement sous son titre. Largeurs de colonnes fixées une fois.
    _COLW = {0: 40, 1: 220, 2: 70, 3: 200, 4: 150, 5: 110}
    for _c, _w in _COLW.items():
        inner.grid_columnconfigure(_c, minsize=_w)

    # En-tête (ligne 0)
    for c, txt in ((1, _tr("Provider")), (2, _tr("Score")),
                   (3, _tr("Zone / extent")), (4, _tr("Filtre")),
                   (5, _tr("Priorité"))):
        tk.Label(inner, text=txt, bg=BG, fg=FG2, anchor="w",
                 font=("Helvetica", 11, "bold") if _OS_UI == "mac"
                 else ("Segoe UI", 9, "bold")).grid(
                     row=0, column=c, sticky="w", padx=6, pady=(0, 6))

    for i, item in enumerate(vue, start=1):
        var_check = tk.IntVar(value=0)
        tk.Checkbutton(inner, variable=var_check, bg=BG,
                       activebackground=BG, selectcolor=CON_BG).grid(
                       row=i, column=0, padx=2, pady=1)
        tk.Label(inner, text=item["provider"], bg=BG, fg=FG, anchor="w",
                 font=("Helvetica", 11) if _OS_UI == "mac"
                 else ("Segoe UI", 9)).grid(row=i, column=1, sticky="w",
                                            padx=6, pady=1)
        sc = "  —  " if item["score"] is None else ("%.1f" % item["score"])
        tk.Label(inner, text=sc, bg=BG, fg=FG2, anchor="w",
                 font=("Helvetica", 11) if _OS_UI == "mac"
                 else ("Segoe UI", 9)).grid(row=i, column=2, sticky="w",
                                            padx=6, pady=1)
        var_zone = tk.StringVar(value="")
        tk.Entry(inner, textvariable=var_zone, width=18,
                 bg=ENTRY_BG, fg=ENTRY_FG, relief="solid", bd=1,
                 highlightthickness=0,
                 insertbackground=ENTRY_FG).grid(row=i, column=3, sticky="w",
                                                 padx=6, pady=1)
        var_filtre = tk.StringVar(value="none")
        tk.Entry(inner, textvariable=var_filtre, width=12,
                 bg=ENTRY_BG, fg=ENTRY_FG, relief="solid", bd=1,
                 highlightthickness=0,
                 insertbackground=ENTRY_FG).grid(row=i, column=4, sticky="w",
                                                 padx=6, pady=1)
        var_prio = tk.StringVar(value=_PRIO_AFF["medium"])
        ttk.Combobox(inner, textvariable=var_prio, values=_PRIO_LISTE,
                     state="readonly", width=8,
                     style="O4Comb.TCombobox").grid(row=i, column=5, sticky="w",
                                                    padx=6, pady=1)
        lignes.append({
            "provider": item["provider"], "score": item["score"],
            "check": var_check, "zone": var_zone, "filtre": var_filtre,
            "prio": var_prio,
        })

    # ── Barre d'état ─────────────────────────────────────────────────────────
    status_var = tk.StringVar(value="%d provider(s) chargé(s)." % len(lignes))

    def status(msg):
        status_var.set(msg)

    # ── Construire une SelectionComb à partir des cases cochées ──────────────
    def _selection_depuis_ihm():
        sel = SelectionComb()
        for lg in lignes:
            if lg["check"].get():
                prio = _PRIO_VAL.get(lg["prio"].get(), "medium")
                filtre = (lg["filtre"].get().strip() or "none")
                sel.ajouter(lg["provider"], zone=lg["zone"].get().strip(),
                            filtre=filtre, priorite=prio)
        return sel

    # ── Aperçu (Chapitre 4, sans écrire) ─────────────────────────────────────
    def _apercu():
        sel = _selection_depuis_ihm()
        ok, problemes = valider_selection(sel)
        preview.delete("1.0", "end")
        if not ok:
            if sel.taille() == 0:
                preview.insert("1.0",
                               _L("Cochez au moins un provider dans la liste "
                                  "de gauche, puis Aperçu.",
                                  "Tick at least one provider in the list on "
                                  "the left, then Preview."))
                status(_L("Cochez au moins un provider avant l'aperçu.",
                          "Tick at least one provider before previewing."))
                return
            preview.insert("1.0", "Sélection non valide :\n  - "
                           + "\n  - ".join(problemes))
            status(_tr("Aperçu : sélection incomplète."))
            return
        preview.insert("1.0", construire_texte_comb(sel))
        status(_tr("Aperçu généré (%d ligne(s)).") % sel.taille())

    # ── Générer (écrit dans Providers/, confirme si existe) ──────────────────
    def _generer():
        sel = _selection_depuis_ihm()
        ok, problemes = valider_selection(sel)
        if not ok:
            # Cas le plus courant : aucune case cochée → message explicite,
            # plutôt que le libellé technique « Sélection vide : rien à écrire ».
            if sel.taille() == 0:
                messagebox.showwarning(
                    _L("Générer .comb", "Generate .comb"),
                    _L("Cochez au moins un provider dans la liste de gauche "
                       "avant de générer.",
                       "Tick at least one provider in the list on the left "
                       "before generating."))
                status(_L("Cochez au moins un provider avant de générer.",
                          "Tick at least one provider before generating."))
                return
            messagebox.showwarning(_tr("Générer .comb"),
                                   "Sélection incomplète :\n- "
                                   + "\n- ".join(problemes))
            return
        nom = nom_var.get().strip()
        if not nom:
            messagebox.showwarning(_tr("Générer .comb"), _tr("Donne un nom de fichier."))
            return
        if not nom.lower().endswith(".comb"):
            nom += ".comb"
        chemin = os.path.join(prov_dir, nom)

        # Cas fichier personnel ZonePhoto.comb : double sécurité (confirmation
        # explicite + .bak). On ne le publie jamais, mais Roland peut l'éditer.
        conf_zp = False
        if _est_zonephoto(chemin):
            if not messagebox.askyesno(
                    _tr("Fichier personnel"),
                    "Tu vas modifier TON fichier personnel ZonePhoto.comb.\n"
                    "Il ne sera jamais publié, et une sauvegarde .bak sera "
                    "créée.\n\nContinuer ?"):
                status(_tr("Modification de ZonePhoto.comb annulée."))
                return
            conf_zp = True

        ok1, msg1 = ecrire_comb(sel, chemin, forcer=False,
                                confirmer_zonephoto=conf_zp)
        if not ok1 and "existe déjà" in msg1:
            if messagebox.askyesno(_tr("Générer .comb"),
                                   "%s existe déjà.\nLe remplacer ? "
                                   "(sauvegarde .bak automatique)" % nom):
                ok1, msg1 = ecrire_comb(sel, chemin, forcer=True,
                                        confirmer_zonephoto=conf_zp)
        status(msg1)
        if ok1:
            messagebox.showinfo(_tr("Générer .comb"), msg1)
        elif "REFUS" in msg1 or "personnel" in msg1:
            messagebox.showerror(_tr("Générer .comb"), msg1)

    # ── Créer un provider (.lay) : ouvre le générateur .lay existant ──────────
    def _creer_lay():
        """Ouvre le générateur de provider (.lay). C'est LUI qui contient les
        deux modes : Preset automatique (ex. PCRS_IGN) et saisie manuelle.
        Import local et protégé : ne plante pas si le module est absent."""
        try:
            import O4_lay_generator as LG
        except Exception as ex:
            status(_tr("Générateur .lay introuvable : %s") % ex)
            return
        fn = getattr(LG, "run_lay_generator", None)
        if not callable(fn):
            status(_tr("O4_lay_generator présent mais run_lay_generator() absent."))
            return
        try:
            fn(parent)
            status(_tr("Générateur de provider (.lay) ouvert."))
        except Exception as ex:
            status(_tr("Erreur à l'ouverture du générateur .lay : %s") % ex)

    # ── Ligne : nom du fichier de sortie ─────────────────────────────────────
    barre = tk.Frame(foot, bg=BG)
    barre.pack(fill="x", padx=12, pady=(6, 2))
    tk.Label(barre, text=_tr("Nom du fichier :"), bg=BG, fg=FG,
             font=("Helvetica", 11) if _OS_UI == "mac"
             else ("Segoe UI", 9)).pack(side="left")
    nom_var = tk.StringVar(value="MON_EUROPE.comb")
    tk.Entry(barre, textvariable=nom_var, width=26,
             bg=ENTRY_BG, fg=ENTRY_FG,
             insertbackground=ENTRY_FG).pack(side="left", padx=6)

    # ── Rangée de boutons : Générer/Aperçu (gauche) / Créer un provider (droite) ─
    btns = tk.Frame(foot, bg=BG)
    btns.pack(fill="x", padx=12, pady=4)
    # Gauche : Générer (action principale de cette fenêtre) puis Aperçu.
    b_gen = _make_themed_button_c(
        tk, btns, _L("✅  Générer le .comb", "✅  Generate the .comb"), _generer)
    b_gen.pack(side="left", padx=4)
    b_ap = _make_themed_button_c(tk, btns, _L("Aperçu", "Preview"), _apercu)
    b_ap.pack(side="left", padx=4)
    # Droite : ouvre un AUTRE outil (fabrique un provider manquant .lay).
    b_lay = _make_themed_button_c(
        tk, btns, _L("➕  Créer un provider manquant (.lay)…",
                     "➕  Create a missing provider (.lay)…"), _creer_lay)
    b_lay.pack(side="right", padx=4)

    # ── Ligne d'aide FIXE sous les boutons (remplace les info-bulles) ─────────
    # Deux langues embarquées via _L : identique et lisible sur Windows, macOS
    # et Linux. Aucun Toplevel, aucune dépendance à un fichier de langue.
    tk.Label(foot,
             text=_L("✅ Générer : écrit le .comb (cochez d'abord un provider).   "
                     "👁 Aperçu : montre le texte sans écrire.   "
                     "➕ Créer un provider : raccourci pour générer un fichier "
                     "provider (.lay) manquant (n'écrit pas le .comb).",
                     "✅ Generate: writes the .comb (tick a provider first).   "
                     "👁 Preview: shows the text without writing.   "
                     "➕ Create a provider: shortcut to generate a missing "
                     "provider (.lay) file (does not write the .comb)."),
             bg=BG, fg=FG2, anchor="w", justify="left",
             font=FONT_N).pack(fill="x", padx=12, pady=(0, 4))

    # ── Aperçu texte ─────────────────────────────────────────────────────────
    preview = tk.Text(foot, height=5, width=64, bg=CON_BG, fg=CON_FG,
                      insertbackground=CON_FG)
    preview.pack(fill="both", expand=False, padx=12, pady=(4, 4))

    tk.Label(foot, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=("Helvetica", 11) if _OS_UI == "mac"
             else ("Segoe UI", 9)).pack(fill="x", padx=12, pady=(2, 2))

    _make_themed_button_c(tk, foot, _tr("Fermer"), win.destroy).pack(pady=(2, 10))

    # ── Verrou de largeur : aucune colonne ne doit jamais être masquée ────────
    # On MESURE la largeur réelle de la grille (dépend de la longueur des noms
    # de providers) et du bas, puis on fixe la largeur MINIMALE de la fenêtre à
    # cette valeur. Réduire la fenêtre en dessous devient impossible → toutes
    # les colonnes restent visibles en permanence. Mesure faite une fois la
    # fenêtre réellement affichée (win.after), sinon winfo_reqwidth() = 1.
    def _verrouiller_largeur():
        try:
            win.update_idletasks()
            besoin_liste = inner.winfo_reqwidth() + 24 + 20  # padx cadre + défil.
            besoin_bas = foot.winfo_reqwidth()
            larg = max(besoin_liste, besoin_bas, 1000)
            win.minsize(larg, 600)
            if win.winfo_width() < larg:
                haut = max(win.winfo_height(), 780)
                win.geometry("%dx%d" % (larg, haut))
        except Exception:
            pass

    try:
        win.after(80, _verrouiller_largeur)
    except Exception:
        pass

    return win


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 8 — ÉCRAN D'ASSEMBLAGE .comb (extents ↔ providers)
#  Rôle : remplacer le travail manuel du préparateur. Un TABLEAU éditable, une
#  ligne = une ligne du .comb :
#        Extent  |  Provider  |  Filtre  |  Priorité
#  L'utilisateur relie CHAQUE extent (dossier Extents/) au provider (.lay) de
#  son choix. Le module PROPOSE les providers dont le nom correspond, mais
#  l'association reste un CHOIX HUMAIN (provider ≠ nom d'extent, non déductible).
#
#  Modèle .comb reproduit (logique du préparateur) :
#     - BASE   = provider large, priorité « medium » → le fond ;
#     - PATCH  = sous-zone précise, priorité « high » (+ filtre) → passe dessus.
#     L'ORDRE des lignes et la PRIORITÉ décident des recouvrements : d'où les
#     flèches ▲▼ (réordonnancement) et la colonne Priorité.
#
#  Sortie : Providers/Provider_Extents.comb (LE fichier diffusable — jamais
#  ZonePhoto.comb, protégé de toute façon par le Chapitre 4).
#
#  RÉUTILISE sans les modifier : SelectionComb (Ch.2), valider_selection /
#  construire_texte_comb / ecrire_comb (Ch.4), scan_providers (Ch.1),
#  scanner_extents (Ch.7), recharger_comb_a_chaud (Ch.7), est_provider_mondial /
#  _jeton_provider (Ch.3), et les helpers GUI du Chapitre 6.
#  Aucune logique métier nouvelle : que de l'assemblage d'API déjà validées.
# ══════════════════════════════════════════════════════════════════════════════

def proposer_providers(extent, providers):
    """Trie une liste de providers pour un extent donné, du plus PROBABLE au
    moins probable (pure logique de NOM, aucun accès disque) :
      1) providers dont le nom correspond à l'extent (sous-chaîne ou même 1er
         jeton, ex. « FR » ↔ « IGN_FR », « Bayern » ↔ « DE_Bayern ») ;
      2) providers MONDIAUX (Esri/BI/Maxar…) — filet de secours ;
      3) le reste, ordre alphabétique.
    Sert à PRÉ-remplir la liste déroulante : l'utilisateur choisit au final."""
    ext_l = (extent or "").strip().lower()
    matches, globaux, autres = [], [], []
    for p in providers:
        pl = (p or "").lower()
        if ext_l and (ext_l in pl or pl in ext_l
                      or _jeton_provider(p) == _jeton_provider(extent)):
            matches.append(p)
        elif est_provider_mondial(p):
            globaux.append(p)
        else:
            autres.append(p)
    return sorted(matches) + sorted(globaux) + sorted(autres)


def couverture_nom(extent, provider):
    """Garde-fou de NOMMAGE (pas une preuve géométrique — ne lit ni .ext ni
    .lay). Indique si le provider PARAÎT couvrir l'extent d'après son nom :
      « ok »        → provider mondial, OU nom correspondant à l'extent ;
      « attention » → provider local dont le nom ne correspond pas à l'extent
                      (l'utilisateur doit vérifier la couverture réelle) ;
      « neutre »    → extent ou provider non renseigné.
    Une vraie vérification géographique (bbox des .ext) pourra être ajoutée
    ultérieurement à partir d'un fichier .ext d'exemple fourni par Roland."""
    extent = (extent or "").strip()
    provider = (provider or "").strip()
    if not extent or not provider:
        return "neutre"
    if est_provider_mondial(provider):
        return "ok"
    pl = provider.lower()
    el = extent.lower()
    if el in pl or pl in el or _jeton_provider(provider) == _jeton_provider(extent):
        return "ok"
    return "attention"


def run_comb_assembler(parent=None):
    """
    Ouvre l'écran d'assemblage « Assembler un .comb (extents ↔ providers) ».
    Chargé seulement au clic (import tkinter local). parent = fenêtre Ortho4XP
    (ou None en test isolé). Retourne la fenêtre (utile aux tests headless).
    """
    import tkinter as tk
    from tkinter import ttk, messagebox

    BG = _cc("bg", "#3b5b49")
    FG = _cc("fg", "#e8f0ec")
    FG2 = _cc("fg_secondary", "#a6e3a1")
    CON_BG = _cc("console_bg", "#0f0f1a")
    CON_FG = _cc("console_fg", "#50fa7b")
    ENTRY_BG = "#f0f4f2"
    ENTRY_FG = "#1e3028"
    OK_C = _cc("fg_secondary", "#a6e3a1")
    WARN_C = _cc("warn", "#f0c040")
    BTN_BG = _cc("btn_bg", "#4a6b59")
    BTN_FG = _cc("btn_fg", "#ffffff")
    BTN_HOVER = _cc("accent", "#5a7b69")

    FONT_N = ("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)
    FONT_B = ("Helvetica", 11, "bold") if _OS_UI == "mac" else ("Segoe UI", 9, "bold")

    # Racine Ortho4XP → Providers/ et Extents/.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prov_dir = _providers_dir(base_dir)

    providers_all = scan_providers(base_dir)      # Chapitre 1
    extents = scanner_extents(base_dir)           # Chapitre 7

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_tr("Relier mes extents aux providers (.comb)"))
    win.configure(bg=BG)
    # Fenêtre large dès l'ouverture pour ne PAS couper la colonne Priorité ni le
    # dernier bouton du bas (largeurs colonnes Extent+Provider+Filtre+Priorité +
    # scrollbar). Redimensionnable : Roland peut l'agrandir/réduire librement.
    try:
        win.geometry("1180x680")
        win.minsize(1180, 680)
        win.resizable(True, True)
    except Exception:
        pass

    style = ttk.Style(win)
    try:
        style.theme_use("alt")
    except Exception:
        pass
    style.configure("O4Comb.TCombobox", fieldbackground=ENTRY_BG,
                    background=ENTRY_BG, foreground=ENTRY_FG)

    # ── Petit bouton Mac-safe (Label cliquable) pour ▲ ▼ ✕ ────────────────────
    def _mini_bouton(parent_w, texte, cmd):
        lbl = tk.Label(parent_w, text=texte, bg=BTN_BG, fg=BTN_FG,
                       padx=6, pady=2, cursor="hand2", font=FONT_N)

        def _enter(e=None):
            lbl.configure(bg=BTN_HOVER)

        def _leave(e=None):
            lbl.configure(bg=BTN_BG)

        def _clic(e=None):
            if callable(cmd):
                cmd()

        lbl.bind("<Enter>", _enter)
        lbl.bind("<Leave>", _leave)
        lbl.bind("<Button-1>", _clic)
        return lbl

    # ── État : liste ordonnée de lignes (StringVars persistantes) ─────────────
    rows = []

    def _new_row(ext="", prov="", filtre="none", prio_aff=None):
        return {
            "ext": tk.StringVar(value=ext),
            "prov": tk.StringVar(value=prov),
            "filtre": tk.StringVar(value=filtre or "none"),
            "prio": tk.StringVar(value=prio_aff or _PRIO_AFF["medium"]),
        }

    def _providers_pour(ext):
        return proposer_providers(ext, providers_all)

    # ── Titre + aide ─────────────────────────────────────────────────────────
    tk.Label(win, text=_tr("Assembler un .comb : relie chaque extent à un provider"),
             bg=BG, fg=FG,
             font=("Helvetica", 14, "bold") if _OS_UI == "mac"
             else ("Segoe UI", 12, "bold")).pack(fill="x", padx=12, pady=(10, 2))
    tk.Label(win, text=_tr("Astuce : l'ordre (▲▼) et la priorité décident des "
                           "recouvrements (BASE = fond, PATCH = passe dessus)."),
             bg=BG, fg=FG2, justify="left", anchor="w",
             font=FONT_N).pack(fill="x", padx=12, pady=(0, 8))

    # ── Zone scrollable du tableau ───────────────────────────────────────────
    cadre = tk.Frame(win, bg=BG)
    cadre.pack(fill="both", expand=True, padx=12, pady=4)
    canvas = tk.Canvas(cadre, bg=BG, highlightthickness=0, height=300)
    scroll = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    status_var = tk.StringVar(value="")

    def status(msg):
        status_var.set(msg)

    # ── Indicateur de couverture (nom) d'une ligne ───────────────────────────
    def _maj_indic(r):
        lbl = r.get("_indic")
        if lbl is None:
            return
        etat = couverture_nom(r["ext"].get(), r["prov"].get())
        if etat == "ok":
            lbl.configure(text="✓", fg=OK_C)
        elif etat == "attention":
            lbl.configure(text="⚠", fg=WARN_C)
        else:
            lbl.configure(text="", fg=FG2)

    def _on_ext(r):
        """Extent choisi → reproposer la liste providers (matches d'abord) et,
        si le provider est encore vide, préremplir le meilleur candidat."""
        props = _providers_pour(r["ext"].get())
        cb = r.get("_prov_cb")
        if cb is not None:
            cb.configure(values=props)
        if not r["prov"].get().strip() and props:
            r["prov"].set(props[0])
        _maj_indic(r)

    # ── (Re)dessin du tableau depuis 'rows' ──────────────────────────────────
    def _rebuild():
        for w in inner.winfo_children():
            w.destroy()

        hdr = tk.Frame(inner, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        colonnes = ((_tr("Ordre"), 5), (_tr("Extent"), 22),
                    (_tr("Provider"), 28), (_tr("Filtre"), 9),
                    (_tr("Priorité"), 9), (_tr("Couv."), 4), ("", 3))
        for c, (txt, w) in enumerate(colonnes):
            tk.Label(hdr, text=txt, bg=BG, fg=FG2, width=w, anchor="w",
                     font=FONT_B).grid(row=0, column=c, padx=2)

        for i, r in enumerate(rows):
            rowf = tk.Frame(inner, bg=BG)
            rowf.grid(row=i + 1, column=0, sticky="ew", pady=1)

            nav = tk.Frame(rowf, bg=BG)
            nav.grid(row=0, column=0, padx=2)
            _mini_bouton(nav, "▲", lambda i=i: _monter(i)).pack(side="left", padx=1)
            _mini_bouton(nav, "▼", lambda i=i: _descendre(i)).pack(side="left", padx=1)

            ext_cb = ttk.Combobox(rowf, textvariable=r["ext"], values=extents,
                                  state="readonly", width=20,
                                  style="O4Comb.TCombobox")
            ext_cb.grid(row=0, column=1, padx=2)

            prov_cb = ttk.Combobox(rowf, textvariable=r["prov"],
                                   values=_providers_pour(r["ext"].get()),
                                   state="readonly", width=26,
                                   style="O4Comb.TCombobox")
            prov_cb.grid(row=0, column=2, padx=2)
            r["_prov_cb"] = prov_cb

            tk.Entry(rowf, textvariable=r["filtre"], width=10, bg=ENTRY_BG,
                     fg=ENTRY_FG, insertbackground=ENTRY_FG).grid(
                     row=0, column=3, padx=2)

            ttk.Combobox(rowf, textvariable=r["prio"], values=_PRIO_LISTE,
                         state="readonly", width=8,
                         style="O4Comb.TCombobox").grid(row=0, column=4, padx=2)

            indic = tk.Label(rowf, text="", bg=BG, fg=FG2, width=5, anchor="w",
                             font=FONT_N)
            indic.grid(row=0, column=5, padx=2)
            r["_indic"] = indic

            _mini_bouton(rowf, "✕", lambda i=i: _supprimer(i)).grid(
                row=0, column=6, padx=2)

            ext_cb.bind("<<ComboboxSelected>>",
                        lambda e=None, r=r: _on_ext(r))
            prov_cb.bind("<<ComboboxSelected>>",
                         lambda e=None, r=r: _maj_indic(r))
            _maj_indic(r)

        canvas.configure(scrollregion=canvas.bbox("all"))

    # ── Actions sur les lignes ───────────────────────────────────────────────
    def _ajouter_ligne():
        rows.append(_new_row())
        _rebuild()
        status(_tr("Ligne ajoutée."))

    def _supprimer(i):
        if 0 <= i < len(rows):
            del rows[i]
            _rebuild()
            status(_tr("Ligne supprimée."))

    def _monter(i):
        if 0 < i < len(rows):
            rows[i - 1], rows[i] = rows[i], rows[i - 1]
            _rebuild()

    def _descendre(i):
        if 0 <= i < len(rows) - 1:
            rows[i + 1], rows[i] = rows[i], rows[i + 1]
            _rebuild()

    def _proposer_depuis_extents():
        """Point de départ : une ligne par extent présent dans Extents/, chacune
        reliée au meilleur provider candidat (par nom), priorité BASE (moyenne).
        L'utilisateur ajuste ensuite provider / priorité / ordre. (Remplace, en
        correct, l'ancien bouton faux qui reliait tout à default_website.)"""
        rows.clear()
        if not extents:
            _rebuild()
            status(_tr("Aucun extent dans Extents/ — créez d'abord vos extents."))
            return
        for e in extents:
            props = _providers_pour(e)
            rows.append(_new_row(ext=e, prov=(props[0] if props else ""),
                                 prio_aff=_PRIO_AFF["medium"]))
        _rebuild()
        status(_tr("%d extent(s) proposé(s). Vérifiez les providers et priorités.")
               % len(extents))

    # ── Construire une SelectionComb depuis le tableau ───────────────────────
    def _selection_depuis_table():
        sel = SelectionComb()
        incompletes = 0
        for r in rows:
            ext = r["ext"].get().strip()
            prov = r["prov"].get().strip()
            if not ext or not prov:
                incompletes += 1
                continue
            prio = _PRIO_VAL.get(r["prio"].get(), "medium")
            filtre = r["filtre"].get().strip() or "none"
            sel.ajouter(prov, zone=ext, filtre=filtre, priorite=prio)
        return sel, incompletes

    def _alertes_couverture():
        """Liste des lignes complètes dont le provider ne PARAÎT pas couvrir
        l'extent (garde-fou de nom). Retourne une liste de messages."""
        msgs = []
        for r in rows:
            ext = r["ext"].get().strip()
            prov = r["prov"].get().strip()
            if ext and prov and couverture_nom(ext, prov) == "attention":
                msgs.append("• %s ← %s" % (ext, prov))
        return msgs

    # ── Aperçu (Chapitre 4, sans écrire) ─────────────────────────────────────
    def _apercu():
        sel, incompletes = _selection_depuis_table()
        ok, problemes = valider_selection(sel)
        preview.delete("1.0", "end")
        if not ok:
            preview.insert("1.0", _tr("Sélection non valide :") + "\n  - "
                           + "\n  - ".join(problemes))
            status(_tr("Aperçu : sélection incomplète."))
            return
        preview.insert("1.0", construire_texte_comb(sel, _entete()))
        note = ""
        if incompletes:
            note = _tr("  (%d ligne(s) incomplète(s) ignorée(s))") % incompletes
        status(_tr("Aperçu généré (%d ligne(s)).") % sel.taille() + note)

    def _entete():
        return [
            "Provider_Extents.comb — assemble par l'ecran d'assemblage (Ch.8).",
            "BASE = provider large, priorite medium. PATCH = sous-zone, high.",
            "L'ordre des lignes et la priorite decident des recouvrements.",
        ]

    # ── Générer → Providers/Provider_Extents.comb ────────────────────────────
    def _generer():
        sel, _inc = _selection_depuis_table()
        ok, problemes = valider_selection(sel)
        if not ok:
            messagebox.showwarning(_tr("Assembler .comb"),
                                   _tr("Sélection incomplète :") + "\n- "
                                   + "\n- ".join(problemes))
            return

        alertes = _alertes_couverture()
        if alertes:
            if not messagebox.askyesno(
                    _tr("Couverture à vérifier"),
                    _tr("Ces providers ne semblent pas correspondre à leur "
                        "extent (vérification par le nom) :") + "\n\n"
                    + "\n".join(alertes)
                    + "\n\n" + _tr("Générer quand même ?")):
                status(_tr("Génération annulée (couverture à vérifier)."))
                return

        chemin = os.path.join(prov_dir, COMB_OUTPUT_NAME)
        ok1, msg1 = ecrire_comb(sel, chemin, entete_lignes=_entete(),
                                forcer=False)
        if not ok1 and "existe déjà" in msg1:
            if messagebox.askyesno(
                    _tr("Assembler .comb"),
                    "%s %s" % (COMB_OUTPUT_NAME,
                               _tr("existe déjà.\nLe remplacer ? "
                                   "(sauvegarde .bak automatique)"))):
                ok1, msg1 = ecrire_comb(sel, chemin, entete_lignes=_entete(),
                                        forcer=True)
        status(msg1)
        if ok1:
            recharge = recharger_comb_a_chaud()   # Chapitre 7
            suffixe = ("\n\n" + _tr("Liste imagery rafraîchie.")) if recharge \
                else ("\n\n" + _tr("Relancez Ortho4XP pour voir l'entrée dans "
                                   "imagery."))
            messagebox.showinfo(_tr("Assembler .comb"), msg1 + suffixe)
        else:
            messagebox.showerror(_tr("Assembler .comb"), msg1)

    # ── Ouvrir le générateur .lay (si un provider manque) ────────────────────
    def _creer_lay():
        try:
            import O4_lay_generator as LG
        except Exception as ex:
            status(_tr("Générateur .lay introuvable : %s") % ex)
            return
        fn = getattr(LG, "run_lay_generator", None)
        if not callable(fn):
            status(_tr("O4_lay_generator présent mais run_lay_generator() absent."))
            return
        try:
            fn(parent)
            status(_tr("Générateur de provider (.lay) ouvert."))
        except Exception as ex:
            status(_tr("Erreur à l'ouverture du générateur .lay : %s") % ex)

    # ── Rangée de boutons : bloc TABLEAU (gauche) / bloc SORTIE (droite) ──────
    btns = tk.Frame(win, bg=BG)
    btns.pack(fill="x", padx=12, pady=(8, 2))
    # Gauche : actions qui construisent/modifient le tableau.
    for txt, cmd in ((_tr("Proposer depuis les extents"), _proposer_depuis_extents),
                     (_tr("Ajouter une ligne"), _ajouter_ligne),
                     (_tr("Créer un provider (.lay)"), _creer_lay)):
        _make_themed_button_c(tk, btns, txt, cmd).pack(side="left", padx=4)
    # Droite : actions de sortie (aperçu puis génération du fichier).
    for txt, cmd in ((_tr("Générer"), _generer),
                     (_tr("Aperçu"), _apercu)):
        _make_themed_button_c(tk, btns, txt, cmd).pack(side="right", padx=4)

    # ── Rappel du fichier de sortie (fixe, non éditable = anti-ZonePhoto) ─────
    tk.Label(win, text=_tr("Fichier généré : Providers/%s") % COMB_OUTPUT_NAME,
             bg=BG, fg=FG2, anchor="w",
             font=FONT_N).pack(fill="x", padx=12, pady=(4, 0))

    # ── Aperçu texte ─────────────────────────────────────────────────────────
    preview = tk.Text(win, height=8, width=68, bg=CON_BG, fg=CON_FG,
                      insertbackground=CON_FG)
    preview.pack(fill="both", expand=False, padx=12, pady=(4, 4))

    tk.Label(win, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=FONT_N).pack(fill="x", padx=12, pady=(2, 2))

    _make_themed_button_c(tk, win, _tr("Fermer"), win.destroy).pack(pady=(2, 10))

    # Démarrage : tableau vide et propre (plus de remplissage automatique).
    # L'utilisateur clique « Proposer depuis les extents » pour préremplir,
    # ou « Ajouter une ligne » pour partir de zéro.
    _rebuild()
    status(_tr("Cliquez « Proposer depuis les extents » pour préremplir, "
               "ou « Ajouter une ligne »."))

    return win


def _demo_chapitre8():
    """Démonstration headless du Chapitre 8 (aucune interface, aucun disque).
    Vérifie la proposition de providers, le garde-fou de couverture par nom, et
    l'assemblage base+patch en un texte .comb. N'est jamais appelée seule."""
    providers = ["IGN_FR", "DE_Bayern", "Esri_07-2022", "BI", "PCRS_Alsace"]

    print("### Proposition providers pour « FR »")
    print("   ", proposer_providers("FR", providers))
    print("### Proposition providers pour « Bayern »")
    print("   ", proposer_providers("Bayern", providers))

    print("\n### Garde-fou couverture (par nom)")
    for ext, prov in (("FR", "IGN_FR"), ("CH", "IGN_FR"),
                      ("CH", "Esri_07-2022"), ("Alsace", "PCRS_Alsace")):
        print("    %-8s ← %-14s : %s"
              % (ext, prov, couverture_nom(ext, prov)))

    print("\n### Assemblage base (medium) + patch (high)")
    sel = SelectionComb()
    sel.ajouter("Esri_07-2022", zone="EUR", filtre="none", priorite="medium")
    sel.ajouter("IGN_FR", zone="FR", filtre="none", priorite="high")
    sel.ajouter("DE_Bayern", zone="Bayern", filtre="none", priorite="high")
    apercu_comb(sel)


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPITRE 9 — MODE EXPERT À DEUX VOIES (écran de choix)
#  Rôle : poser DEVANT le mode expert un écran de choix à deux voies distinctes,
#  demandé par Roland :
#     1) « Créer un nouveau .comb »   → run_comb_creer (mode 1, liste à cocher —
#        inchangé, celui qui fonctionne).
#     2) « Corriger un .comb existant » → run_comb_corriger (CE chapitre) : on
#        importe un .comb et le tableau se RECONSTRUIT à partir des LIGNES du
#        fichier — une ligne du fichier = une ligne éditable (Provider / Zone /
#        Filtre / Priorité). Aucune case à cocher, aucune liste figée de
#        providers : donc plus AUCUNE perte des lignes à noms longs
#        (EXCEPTION_…, FRANCE_…), plus aucune colonne vide, plus aucun cochage
#        parasite. 149 lignes dans le fichier = 149 lignes éditables.
#
#  Le point d'entrée du menu reste run_comb_generator : il devient l'ÉCRAN DE
#  CHOIX (aucun fichier menu à modifier). Sortie toujours dans
#  Providers/Provider_Extents.comb — jamais ZonePhoto.comb (garde-fou Ch.4).
#
#  RÉUTILISE sans les modifier : parser_lignes_comb (Ch.5, conserve TOUTES les
#  lignes du fichier dans l'ordre, y compris noms longs et filtres non-none),
#  SelectionComb (Ch.2), valider_selection / construire_texte_comb / ecrire_comb
#  (Ch.4), COMB_OUTPUT_NAME / recharger_comb_a_chaud (Ch.7), les helpers GUI et
#  _PRIO_* (Ch.6). Aucune logique métier nouvelle : que de l'assemblage d'API
#  déjà validées.
# ══════════════════════════════════════════════════════════════════════════════

def run_comb_corriger(parent=None):
    """
    MODE 2 — « Corriger un .comb existant ».
    Importe un .comb et reconstruit UN tableau éditable : une ligne du fichier =
    une ligne éditable (Provider / Zone / Filtre / Priorité). On édite exactement
    les lignes du fichier (noms longs EXCEPTION_/FRANCE_ compris), on peut
    réordonner (▲▼), supprimer (✕) ou ajouter une ligne, puis régénérer.
    Sortie : Providers/Provider_Extents.comb (jamais ZonePhoto.comb).
    parent = fenêtre Ortho4XP (ou None en test isolé). Retourne la fenêtre.
    """
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    BG = _cc("bg", "#3b5b49")
    FG = _cc("fg", "#e8f0ec")
    FG2 = _cc("fg_secondary", "#a6e3a1")
    CON_BG = _cc("console_bg", "#0f0f1a")
    CON_FG = _cc("console_fg", "#50fa7b")
    ENTRY_BG = "#f0f4f2"
    ENTRY_FG = "#1e3028"
    BTN_BG = _cc("btn_bg", "#4a6b59")
    BTN_FG = _cc("btn_fg", "#ffffff")
    BTN_HOVER = _cc("accent", "#5a7b69")

    FONT_N = ("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)
    FONT_B = ("Helvetica", 11, "bold") if _OS_UI == "mac" else ("Segoe UI", 9, "bold")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prov_dir = _providers_dir(base_dir)

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_tr("Corriger un .comb existant"))
    win.configure(bg=BG)
    try:
        win.geometry("1180x680")
        win.minsize(1180, 680)
        win.resizable(True, True)
    except Exception:
        pass

    style = ttk.Style(win)
    try:
        style.theme_use("alt")
    except Exception:
        pass
    style.configure("O4Comb.TCombobox", fieldbackground=ENTRY_BG,
                    background=ENTRY_BG, foreground=ENTRY_FG)

    # ── Petit bouton Mac-safe (Label cliquable) pour ▲ ▼ ✕ ────────────────────
    def _mini_bouton(parent_w, texte, cmd):
        lbl = tk.Label(parent_w, text=texte, bg=BTN_BG, fg=BTN_FG,
                       padx=6, pady=2, cursor="hand2", font=FONT_N)

        def _enter(e=None):
            lbl.configure(bg=BTN_HOVER)

        def _leave(e=None):
            lbl.configure(bg=BTN_BG)

        def _clic(e=None):
            if callable(cmd):
                cmd()

        lbl.bind("<Enter>", _enter)
        lbl.bind("<Leave>", _leave)
        lbl.bind("<Button-1>", _clic)
        return lbl

    # ── État : liste ordonnée de lignes (StringVars persistantes) ─────────────
    rows = []

    def _new_row(prov="", zone="", filtre="none", prio_aff=None):
        return {
            "prov": tk.StringVar(value=prov),
            "zone": tk.StringVar(value=zone),
            "filtre": tk.StringVar(value=filtre or "none"),
            "prio": tk.StringVar(value=prio_aff or _PRIO_AFF["medium"]),
        }

    # ── Titre + aide ─────────────────────────────────────────────────────────
    tk.Label(win, text=_tr("Corriger un .comb : chaque ligne du fichier est éditable"),
             bg=BG, fg=FG,
             font=("Helvetica", 14, "bold") if _OS_UI == "mac"
             else ("Segoe UI", 12, "bold")).pack(fill="x", padx=12, pady=(10, 2))
    tk.Label(win, text=_tr("Importe ton .comb : une ligne du fichier = une ligne "
                           "éditable (Provider / Zone / Filtre / Priorité). "
                           "Réordonne (▲▼), supprime (✕) ou ajoute des lignes, "
                           "puis Générer."),
             bg=BG, fg=FG2, justify="left", wraplength=980,
             font=FONT_N).pack(fill="x", padx=12, pady=(0, 8))

    # ── Zone scrollable du tableau ───────────────────────────────────────────
    cadre = tk.Frame(win, bg=BG)
    cadre.pack(fill="both", expand=True, padx=12, pady=4)
    canvas = tk.Canvas(cadre, bg=BG, highlightthickness=0, height=320)
    scroll = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    status_var = tk.StringVar(value="")

    def status(msg):
        status_var.set(msg)

    # ── (Re)dessin du tableau depuis 'rows' ──────────────────────────────────
    def _rebuild():
        for w in inner.winfo_children():
            w.destroy()

        hdr = tk.Frame(inner, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        colonnes = ((_tr("Ordre"), 6), (_tr("Provider"), 34),
                    (_tr("Zone / extent"), 34), (_tr("Filtre"), 18),
                    (_tr("Priorité"), 10), ("", 4))
        for c, (txt, w) in enumerate(colonnes):
            tk.Label(hdr, text=txt, bg=BG, fg=FG2, width=w, anchor="w",
                     font=FONT_B).grid(row=0, column=c, padx=2)

        for i, r in enumerate(rows):
            rowf = tk.Frame(inner, bg=BG)
            rowf.grid(row=i + 1, column=0, sticky="ew", pady=1)

            nav = tk.Frame(rowf, bg=BG)
            nav.grid(row=0, column=0, padx=2)
            _mini_bouton(nav, "▲", lambda i=i: _monter(i)).pack(side="left", padx=1)
            _mini_bouton(nav, "▼", lambda i=i: _descendre(i)).pack(side="left", padx=1)

            # Provider et Zone en SAISIE LIBRE : on ne perd aucun nom long,
            # aucune liste figée, aucune déduction. Le champ défile si le nom
            # dépasse la largeur ; la valeur complète est conservée.
            tk.Entry(rowf, textvariable=r["prov"], width=32, bg=ENTRY_BG,
                     fg=ENTRY_FG, relief="solid", bd=1, highlightthickness=0,
                     insertbackground=ENTRY_FG).grid(row=0, column=1, padx=2)
            tk.Entry(rowf, textvariable=r["zone"], width=32, bg=ENTRY_BG,
                     fg=ENTRY_FG, relief="solid", bd=1, highlightthickness=0,
                     insertbackground=ENTRY_FG).grid(row=0, column=2, padx=2)
            tk.Entry(rowf, textvariable=r["filtre"], width=16, bg=ENTRY_BG,
                     fg=ENTRY_FG, relief="solid", bd=1, highlightthickness=0,
                     insertbackground=ENTRY_FG).grid(row=0, column=3, padx=2)
            ttk.Combobox(rowf, textvariable=r["prio"], values=_PRIO_LISTE,
                         state="readonly", width=8,
                         style="O4Comb.TCombobox").grid(row=0, column=4, padx=2)

            _mini_bouton(rowf, "✕", lambda i=i: _supprimer(i)).grid(
                row=0, column=5, padx=2)

        canvas.configure(scrollregion=canvas.bbox("all"))

    # ── Actions sur les lignes ───────────────────────────────────────────────
    def _ajouter_ligne():
        rows.append(_new_row())
        _rebuild()
        status(_tr("Ligne ajoutée."))

    def _supprimer(i):
        if 0 <= i < len(rows):
            del rows[i]
            _rebuild()
            status(_tr("Ligne supprimée."))

    def _monter(i):
        if 0 < i < len(rows):
            rows[i - 1], rows[i] = rows[i], rows[i - 1]
            _rebuild()

    def _descendre(i):
        if 0 <= i < len(rows) - 1:
            rows[i + 1], rows[i] = rows[i], rows[i + 1]
            _rebuild()

    # ── Import : une ligne du fichier = une ligne éditable ───────────────────
    def _importer():
        chemin = filedialog.askopenfilename(
            title=_tr("Importer un .comb à corriger"), initialdir=prov_dir,
            filetypes=[("Fichiers .comb", "*.comb"), ("Tous", "*.*")])
        if not chemin:
            return
        try:
            with open(chemin, encoding="utf-8") as fp:
                texte = fp.read()
        except Exception as ex:
            messagebox.showerror(_tr("Importer .comb"),
                                 _tr("Lecture impossible : %s") % ex)
            status(_tr("Lecture impossible : %s") % ex)
            return
        # parser_lignes_comb (Ch.5) conserve TOUTES les lignes valides du
        # fichier, dans l'ordre, sans dédoublonnage ni liste figée.
        entrees, rapport = parser_lignes_comb(texte)
        rows.clear()
        for e in entrees:
            rows.append(_new_row(prov=e["provider"], zone=e["zone"],
                                 filtre=e.get("filtre", "none"),
                                 prio_aff=_PRIO_AFF.get(e["priorite"], "medium")))
        _rebuild()

        note_zp = ""
        if _est_zonephoto(chemin):
            note_zp = ("  " + _tr("(ZonePhoto.comb chargé pour édition — la "
                                  "sortie ira dans Provider_Extents.comb.)"))
        ecartees = len(rapport)
        status(_tr("%d ligne(s) importée(s)%s.")
               % (len(rows), (", %d écartée(s)" % ecartees) if ecartees else "")
               + note_zp)

        # Rapport des lignes écartées (mauvais nombre de colonnes ou priorité
        # inconnue) affiché dans l'aperçu, jamais masqué.
        preview.delete("1.0", "end")
        if rapport:
            preview.insert("1.0", _tr("Lignes écartées à l'import :") + "\n- "
                           + "\n- ".join(rapport))
        else:
            preview.insert("1.0", _tr("Import : toutes les lignes ont été "
                                      "reprises telles quelles."))

    # ── En-tête du fichier généré ────────────────────────────────────────────
    def _entete():
        return [
            "Provider_Extents.comb — corrige via l'ecran « Corriger un .comb » (Ch.9).",
            "Chaque ligne provient d'un .comb importe puis edite a la main.",
            "L'ordre des lignes et la priorite decident des recouvrements.",
        ]

    # ── Construire une SelectionComb depuis le tableau ───────────────────────
    def _selection_depuis_table():
        sel = SelectionComb()
        incompletes = 0
        dups = 0
        for r in rows:
            prov = r["prov"].get().strip()
            zone = r["zone"].get().strip()
            if not prov or not zone:
                incompletes += 1
                continue
            prio = _PRIO_VAL.get(r["prio"].get(), "medium")
            filtre = r["filtre"].get().strip() or "none"
            if not sel.ajouter(prov, zone=zone, filtre=filtre, priorite=prio):
                dups += 1
        return sel, incompletes, dups

    def _note_lignes(incompletes, dups):
        notes = []
        if incompletes:
            notes.append(_tr("%d ligne(s) incomplète(s) ignorée(s)") % incompletes)
        if dups:
            notes.append(_tr("%d doublon(s) exact(s) fusionné(s)") % dups)
        return ("  (" + ", ".join(notes) + ")") if notes else ""

    # ── Aperçu (Ch.4, sans écrire) ───────────────────────────────────────────
    def _apercu():
        sel, incompletes, dups = _selection_depuis_table()
        ok, problemes = valider_selection(sel)
        preview.delete("1.0", "end")
        if not ok:
            preview.insert("1.0", _tr("Sélection non valide :") + "\n  - "
                           + "\n  - ".join(problemes))
            status(_tr("Aperçu : sélection incomplète."))
            return
        preview.insert("1.0", construire_texte_comb(sel, _entete()))
        status(_tr("Aperçu généré (%d ligne(s)).") % sel.taille()
               + _note_lignes(incompletes, dups))

    # ── Générer → Providers/Provider_Extents.comb ────────────────────────────
    def _generer():
        sel, incompletes, dups = _selection_depuis_table()
        ok, problemes = valider_selection(sel)
        if not ok:
            messagebox.showwarning(_tr("Corriger .comb"),
                                   _tr("Sélection incomplète :") + "\n- "
                                   + "\n- ".join(problemes))
            return
        chemin = os.path.join(prov_dir, COMB_OUTPUT_NAME)
        ok1, msg1 = ecrire_comb(sel, chemin, entete_lignes=_entete(),
                                forcer=False)
        if not ok1 and "existe déjà" in msg1:
            if messagebox.askyesno(
                    _tr("Corriger .comb"),
                    "%s %s" % (COMB_OUTPUT_NAME,
                               _tr("existe déjà.\nLe remplacer ? "
                                   "(sauvegarde .bak automatique)"))):
                ok1, msg1 = ecrire_comb(sel, chemin, entete_lignes=_entete(),
                                        forcer=True)
        status(msg1 + _note_lignes(incompletes, dups))
        if ok1:
            recharge = recharger_comb_a_chaud()   # Chapitre 7
            suffixe = ("\n\n" + _tr("Liste imagery rafraîchie.")) if recharge \
                else ("\n\n" + _tr("Relancez Ortho4XP pour voir l'entrée dans "
                                   "imagery."))
            messagebox.showinfo(_tr("Corriger .comb"), msg1 + suffixe)
        else:
            messagebox.showerror(_tr("Corriger .comb"), msg1)

    # ── Rangée de boutons ────────────────────────────────────────────────────
    btns = tk.Frame(win, bg=BG)
    btns.pack(fill="x", padx=12, pady=(8, 2))
    for txt, cmd in ((_tr("Importer un .comb"), _importer),
                     (_tr("Ajouter une ligne"), _ajouter_ligne),
                     (_tr("Aperçu"), _apercu),
                     (_tr("Générer"), _generer)):
        _make_themed_button_c(tk, btns, txt, cmd).pack(side="left", padx=4)

    # ── Rappel du fichier de sortie (fixe = anti-ZonePhoto) ───────────────────
    tk.Label(win, text=_tr("Fichier généré : Providers/%s") % COMB_OUTPUT_NAME,
             bg=BG, fg=FG2, anchor="w",
             font=FONT_N).pack(fill="x", padx=12, pady=(4, 0))

    # ── Aperçu texte ─────────────────────────────────────────────────────────
    preview = tk.Text(win, height=8, width=68, bg=CON_BG, fg=CON_FG,
                      insertbackground=CON_FG)
    preview.pack(fill="both", expand=False, padx=12, pady=(4, 4))

    tk.Label(win, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=FONT_N).pack(fill="x", padx=12, pady=(2, 2))

    _make_themed_button_c(tk, win, _tr("Fermer"), win.destroy).pack(pady=(2, 10))

    # Démarrage : on propose d'emblée l'import (cœur du mode 2). Si l'utilisateur
    # annule, on laisse une ligne vide éditable (garde-fou anti-page-blanche).
    _importer()
    if not rows:
        _ajouter_ligne()

    return win


def run_comb_generator(parent=None):
    """
    ÉCRAN DE CHOIX du mode expert .comb (point d'entrée appelé par le menu).
    Deux voies distinctes :
      1) « Créer un nouveau .comb »   → run_comb_creer   (liste à cocher, inchangé)
      2) « Corriger un .comb existant » → run_comb_corriger (tableau éditable
         ligne à ligne, reconstruit depuis le fichier importé)
    Le bouton choisi ouvre la fenêtre voulue puis ferme ce sélecteur.
    parent = fenêtre Ortho4XP (ou None en test isolé). Retourne la fenêtre.
    Le nom est conservé (run_comb_generator) pour que le menu reste inchangé.
    """
    import tkinter as tk

    BG = _cc("bg", "#3b5b49")
    FG = _cc("fg", "#e8f0ec")
    FG2 = _cc("fg_secondary", "#a6e3a1")

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_tr("Mode expert .comb — choisir"))
    win.configure(bg=BG)
    try:
        win.resizable(False, False)
    except Exception:
        pass

    tk.Label(win, text=_tr("Que veux-tu faire ?"), bg=BG, fg=FG,
             font=("Helvetica", 15, "bold") if _OS_UI == "mac"
             else ("Segoe UI", 12, "bold")).pack(fill="x", padx=18, pady=(14, 2))
    tk.Label(win, text=_tr("Deux voies : partir de zéro, ou corriger un fichier "
                           ".comb existant."),
             bg=BG, fg=FG2,
             font=("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=18, pady=(0, 12))

    def _ouvrir_creer():
        try:
            run_comb_creer(parent)
        finally:
            try:
                win.destroy()
            except Exception:
                pass

    def _ouvrir_corriger():
        try:
            run_comb_corriger(parent)
        finally:
            try:
                win.destroy()
            except Exception:
                pass

    zone = tk.Frame(win, bg=BG)
    zone.pack(fill="both", expand=True, padx=18, pady=4)
    _make_themed_button_c(
        tk, zone,
        _tr("🆕  Créer un nouveau .comb (liste des providers à cocher)"),
        _ouvrir_creer).pack(fill="x", pady=6)
    _make_themed_button_c(
        tk, zone,
        _tr("✏  Corriger un .comb existant (tableau éditable ligne à ligne)"),
        _ouvrir_corriger).pack(fill="x", pady=6)

    _make_themed_button_c(tk, win, _tr("Fermer"), win.destroy).pack(pady=(6, 14))

    return win


def _demo_chapitre9():
    """Démonstration headless du Chapitre 9 (aucune interface, aucun disque).
    Prouve le POINT CLÉ du mode 2 : le chargement conserve TOUTES les lignes du
    fichier (noms longs EXCEPTION_/FRANCE_, filtres non-none, séparateurs
    tabulation/espaces, plusieurs lignes pour un même provider avec zones
    différentes) — une ligne du fichier = une ligne éditable, aucune perte.
    N'est jamais appelée automatiquement."""
    texte = (
        "# en-tete de test\n"
        "\n"
        "FRorth\tFrance\tnone\tmedium\n"
        "Arc@\tIreland\tnone\tmedium\n"
        "Arc@\tUK\tnone\tmedium\n"
        "EXCEPTION_FRANCE_Auvergne-Rhone-Alpes_43_Histo-2019_IGN\t"
        "EXCEPTION_FRANCE_43\tEXCEPTION_FRANCE_43_PATCH\thigh\n"
        "FRANCE_Ortho-Litto-V2_GEOLITTORAL\t62-Pas-de-Calais\tnone\thigh\n"
        "FRANCE_Ortho-Litto-V2_GEOLITTORAL\t59-Nord\tnone\thigh\n"
        "LigneCassee   SansAssezDeColonnes\n"            # 2 colonnes → écartée
        "X\tY\tnone\tinconnue\n"                          # priorité invalide → écartée
    )
    entrees, rapport = parser_lignes_comb(texte)
    print("### Chargement mode 2 (parser_lignes_comb)")
    print("   Lignes retenues (= lignes éditables) :", len(entrees))
    for e in entrees:
        print("     %-52s | %-18s | %-28s | %s"
              % (e["provider"], e["zone"], e["filtre"], e["priorite"]))
    print("   Lignes écartées :", len(rapport))
    for m in rapport:
        print("     ⚠", m)

    # Aller-retour : reconstruire un SelectionComb et le texte .comb.
    sel = SelectionComb()
    for e in entrees:
        sel.ajouter(e["provider"], zone=e["zone"], filtre=e["filtre"],
                    priorite=e["priorite"])
    print("\n### Réécriture (construire_texte_comb) — aucune perte attendue")
    print("   Lignes dans la sélection :", sel.taille())
    apercu_comb(sel)
