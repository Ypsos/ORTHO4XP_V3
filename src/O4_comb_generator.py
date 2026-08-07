# -*- coding: utf-8 -*-
# ==============================================================================
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


#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================


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
#  CHAPITRE 6 — INTERFACE GRAPHIQUE (fenêtre « Générer un .comb »)  — v1
#  Rôle : poser un VISAGE sur le moteur (chapitres 1-5). Produit UN .comb
#  GLOBAL (style EUR.comb : multi-provider / multi-tuile), écrit dans Providers/.
#
#  v1 (cette étape) :
#     - liste des providers réels + score (Chapitre 1), cases à cocher ;
#     - colonne ZONE (extent) éditable + PRIORITÉ en menu déroulant 3 choix
#       (Haute / Moyenne / Basse), JAMAIS de saisie clavier pour la priorité ;
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


# Correspondance affichage <-> valeur moteur pour la priorité.
_PRIO_AFF = {"high": "Haute", "medium": "Moyenne", "low": "Basse"}
_PRIO_VAL = {"Haute": "high", "Moyenne": "medium", "Basse": "low"}
_PRIO_LISTE = ("Haute", "Moyenne", "Basse")


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


def run_comb_generator(parent=None):
    """
    Ouvre la fenêtre « Générer un .comb » (v1). Chargée seulement au clic.
    parent = fenêtre principale Ortho4XP (ou None en test isolé).
    Retourne la fenêtre (utile aux tests headless).
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

    # Racine Ortho4XP → dossier Providers/ (là où vivent EUR.comb, etc.).
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prov_dir = _providers_dir(base_dir)

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title(_tr("Générer un fichier .comb"))
    win.configure(bg=BG)

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
    tk.Label(win, text=_tr("Coche les providers, choisis zone + priorité, puis Générer."),
             bg=BG, fg=FG2,
             font=("Helvetica", 11) if _OS_UI == "mac" else ("Segoe UI", 9)
             ).pack(fill="x", padx=12, pady=(0, 8))

    # ── Zone scrollable listant les providers ────────────────────────────────
    cadre = tk.Frame(win, bg=BG)
    cadre.pack(fill="both", expand=True, padx=12, pady=4)
    canvas = tk.Canvas(cadre, bg=BG, highlightthickness=0, height=280)
    scroll = ttk.Scrollbar(cadre, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # En-tête de colonnes
    entete = tk.Frame(inner, bg=BG)
    entete.grid(row=0, column=0, sticky="ew", pady=(0, 4))
    for c, (txt, w) in enumerate((("", 3), (_tr("Provider"), 28),
                                  (_tr("Score"), 7), (_tr("Zone / extent"), 18),
                                  (_tr("Priorité"), 10))):
        tk.Label(entete, text=txt, bg=BG, fg=FG2, width=w, anchor="w",
                 font=("Helvetica", 11, "bold") if _OS_UI == "mac"
                 else ("Segoe UI", 9, "bold")).grid(row=0, column=c, padx=2)

    for i, item in enumerate(vue, start=1):
        rowf = tk.Frame(inner, bg=BG)
        rowf.grid(row=i, column=0, sticky="ew")
        var_check = tk.IntVar(value=0)
        tk.Checkbutton(rowf, variable=var_check, bg=BG,
                       activebackground=BG, selectcolor=CON_BG).grid(
                       row=0, column=0, padx=2)
        tk.Label(rowf, text=item["provider"], bg=BG, fg=FG, width=28,
                 anchor="w",
                 font=("Helvetica", 11) if _OS_UI == "mac"
                 else ("Segoe UI", 9)).grid(row=0, column=1, padx=2)
        sc = "  —  " if item["score"] is None else ("%.1f" % item["score"])
        tk.Label(rowf, text=sc, bg=BG, fg=FG2, width=7, anchor="w",
                 font=("Helvetica", 11) if _OS_UI == "mac"
                 else ("Segoe UI", 9)).grid(row=0, column=2, padx=2)
        var_zone = tk.StringVar(value="")
        tk.Entry(rowf, textvariable=var_zone, width=18,
                 bg=ENTRY_BG, fg=ENTRY_FG,
                 insertbackground=ENTRY_FG).grid(row=0, column=3, padx=2)
        var_prio = tk.StringVar(value="Moyenne")
        ttk.Combobox(rowf, textvariable=var_prio, values=_PRIO_LISTE,
                     state="readonly", width=8,
                     style="O4Comb.TCombobox").grid(row=0, column=4, padx=2)
        lignes.append({
            "provider": item["provider"], "score": item["score"],
            "check": var_check, "zone": var_zone, "prio": var_prio,
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
                sel.ajouter(lg["provider"], zone=lg["zone"].get().strip(),
                            filtre="none", priorite=prio)
        return sel

    # ── Mode AUTOMATIQUE : coche + priorise tout seul (le reste = manuel) ─────
    def _remplir_auto():
        """Aide « clé en main » pour l'utilisateur : coche les providers
        évalués corrects et pose une priorité par défaut sensée.
        - provider MONDIAL (Esri/BI/Maxar…) → priorité Basse (filet de secours,
          ne recouvre jamais un local) ;
        - provider local bien noté (score ≥ 70) → Haute ;
        - autre provider évalué → Moyenne.
        L'utilisateur peut tout ajuster ensuite à la main (mode manuel)."""
        n = 0
        for lg in lignes:
            score = lg["score"]
            if score is None:          # non évalué → on ne coche pas d'office
                lg["check"].set(0)
                continue
            lg["check"].set(1)
            if est_provider_mondial(lg["provider"]):
                lg["prio"].set("Basse")
            elif score >= 70:
                lg["prio"].set("Haute")
            else:
                lg["prio"].set("Moyenne")
            n += 1
        status(_tr("Automatique : %d provider(s) coché(s) et priorisé(s). "
                   "Ajuste les zones puis Aperçu/Générer.") % n)

    # ── Aperçu (Chapitre 4, sans écrire) ─────────────────────────────────────
    def _apercu():
        sel = _selection_depuis_ihm()
        ok, problemes = valider_selection(sel)
        preview.delete("1.0", "end")
        if not ok:
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

    # ── Importer un .comb (Chapitre 5) ───────────────────────────────────────
    def _importer():
        from tkinter import filedialog
        chemin = filedialog.askopenfilename(
            title=_tr("Importer un .comb"), initialdir=prov_dir,
            filetypes=[("Fichiers .comb", "*.comb"), ("Tous", "*.*")])
        if not chemin:
            return
        sel, rapport = importer_comb(chemin)
        if sel is None:
            messagebox.showerror(_tr("Importer .comb"), "\n".join(rapport))
            status(rapport[0] if rapport else _tr("Import impossible."))
            return
        # reporter l'import sur les cases : on coche/prio/zone selon le fichier
        par_nom = {e["provider"]: e for e in sel.entrees()}
        for lg in lignes:
            e = par_nom.get(lg["provider"])
            if e:
                lg["check"].set(1)
                lg["zone"].set(e["zone"])
                lg["prio"].set(_PRIO_AFF.get(e["priorite"], "Moyenne"))
            else:
                lg["check"].set(0)
        preview.delete("1.0", "end")
        preview.insert("1.0", construire_texte_comb(sel))
        status(rapport[0] if rapport else _tr("Import effectué."))

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
    barre = tk.Frame(win, bg=BG)
    barre.pack(fill="x", padx=12, pady=(6, 2))
    tk.Label(barre, text=_tr("Nom du fichier :"), bg=BG, fg=FG,
             font=("Helvetica", 11) if _OS_UI == "mac"
             else ("Segoe UI", 9)).pack(side="left")
    nom_var = tk.StringVar(value="MON_EUROPE.comb")
    tk.Entry(barre, textvariable=nom_var, width=26,
             bg=ENTRY_BG, fg=ENTRY_FG,
             insertbackground=ENTRY_FG).pack(side="left", padx=6)

    # ── Rangée de boutons ────────────────────────────────────────────────────
    btns = tk.Frame(win, bg=BG)
    btns.pack(fill="x", padx=12, pady=4)
    for txt, cmd in ((_tr("Automatique"), _remplir_auto),
                     (_tr("Importer un .comb"), _importer),
                     (_tr("Créer un provider (.lay)"), _creer_lay),
                     (_tr("Aperçu"), _apercu),
                     (_tr("Générer"), _generer)):
        _make_themed_button_c(tk, btns, txt, cmd).pack(side="left", padx=4)

    # ── Aperçu texte ─────────────────────────────────────────────────────────
    preview = tk.Text(win, height=8, width=64, bg=CON_BG, fg=CON_FG,
                      insertbackground=CON_FG)
    preview.pack(fill="both", expand=False, padx=12, pady=(4, 4))

    tk.Label(win, textvariable=status_var, bg=BG, fg=FG2, anchor="w",
             font=("Helvetica", 11) if _OS_UI == "mac"
             else ("Segoe UI", 9)).pack(fill="x", padx=12, pady=(2, 2))

    _make_themed_button_c(tk, win, _tr("Fermer"), win.destroy).pack(pady=(2, 10))

    return win
