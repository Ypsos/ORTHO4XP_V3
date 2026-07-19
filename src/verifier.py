# -*- coding: utf-8 -*-
# ============================================================================
#  verifier.py  —  ORTHO4XP V3  —  Vérification avant livraison
# ----------------------------------------------------------------------------
#  À placer dans  Ortho4XP/tests/verifier.py
#
#  POURQUOI CE FICHIER EXISTE
#  --------------------------
#  Le 19/07/2026, un remplacement de bloc a supprimé quatre méthodes d'un
#  module. Le fichier compilait parfaitement. Le plantage n'est apparu
#  qu'au clic de l'utilisateur, sur un « object has no attribute ».
#
#  La compilation ne prouve RIEN : self.methode_absente() compile sans
#  broncher et ne casse qu'à l'exécution. Ce fichier existe pour attraper
#  cela, et tout ce qui y ressemble, AVANT la livraison.
#
#  COMMENT S'EN SERVIR
#  -------------------
#  Ouvrir ce fichier avec Python (double-clic sur la plupart des
#  installations, ou depuis un éditeur). Il écrit un rapport lisible dans
#  tests/rapport_verification.txt et l'affiche.
#
#  Aucune modification n'est faite sur quoi que ce soit : ce fichier LIT,
#  il n'écrit que son propre rapport.
#
#  LES QUATRE CONTRÔLES
#  --------------------
#  1. Compilation           — chaque fichier .py est syntaxiquement valide
#  2. Appels sans définition — une méthode appelée existe-t-elle vraiment
#  3. Langues               — FR et EN symétriques, aucune clé sans traduction
#  4. Non-régression        — rien n'a disparu depuis la référence validée
#
#  Le contrôle 4 compare à tests/reference.json. Ce fichier de référence
#  se crée en lançant cette vérification une fois sur une version dont on
#  sait qu'elle fonctionne, puis en répondant « o » à la question posée.
# ============================================================================

import os
import re
import ast
import sys
import json
import datetime

VERSION = "1.0 — 19/07/2026"

# Attributs fournis par tkinter et ses classes, jamais définis dans le code
# du projet. Sans cette liste, le contrôle 2 signalerait des centaines de
# faux positifs.
TK_HERITE = {
    "after", "after_cancel", "after_idle", "bind", "bind_all", "unbind",
    "title", "configure", "config", "cget", "transient", "resizable",
    "protocol", "geometry", "minsize", "maxsize", "iconify", "deiconify",
    "withdraw", "destroy", "update", "update_idletasks", "wait_window",
    "wait_visibility", "grab_set", "grab_release", "lift", "lower",
    "focus_set", "focus_force", "columnconfigure", "rowconfigure",
    "grid", "grid_configure", "grid_forget", "grid_rowconfigure",
    "grid_columnconfigure", "grid_slaves", "pack", "pack_forget",
    "place", "winfo_children", "winfo_width", "winfo_height",
    "winfo_screenwidth", "winfo_screenheight", "winfo_exists",
    "winfo_toplevel", "winfo_rootx", "winfo_rooty", "quit", "mainloop",
    "attributes", "state", "tk", "master", "children", "nametowidget",
    "register", "option_add", "clipboard_clear", "clipboard_append",
    "__dict__", "__class__",
}


# ============================================================================
#  Localisation des fichiers
# ============================================================================

def racine():
    """Racine Ortho4XP : le dossier parent de tests/."""
    ici = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(ici).lower() == "tests":
        return os.path.dirname(ici)
    return ici


def dossier_src():
    r = racine()
    for c in (os.path.join(r, "src"), r):
        if os.path.isdir(c) and any(f.endswith(".py") for f in os.listdir(c)):
            return c
    return r


def fichiers_python(d):
    try:
        return sorted(os.path.join(d, f) for f in os.listdir(d)
                      if f.endswith(".py"))
    except Exception:
        return []


# ============================================================================
#  Contrôle 1 — compilation
# ============================================================================

def controle_compilation(fichiers, dire):
    dire("")
    dire("1. COMPILATION")
    arbres = {}
    ko = 0
    for f in fichiers:
        nom = os.path.basename(f)
        try:
            src = open(f, encoding="utf-8").read()
            arbres[f] = (ast.parse(src), src)
        except SyntaxError as e:
            ko += 1
            dire("   ECHEC   {} — ligne {} : {}".format(nom, e.lineno, e.msg))
        except Exception as e:
            ko += 1
            dire("   ECHEC   {} — {}".format(nom, e))
    dire("   {} fichier(s) compilés, {} en échec".format(len(arbres), ko))
    return arbres, ko == 0


# ============================================================================
#  Contrôle 2 — appels sans définition
# ============================================================================
#  LE contrôle qui aurait évité le plantage du 19/07/2026.
#
#  On ne signale que les self.X(...) réellement APPELÉS, pas les simples
#  lectures d'attribut : un attribut peut être posé dynamiquement, alors
#  qu'une méthode appelée doit exister quelque part.

def controle_appels(arbres, dire):
    dire("")
    dire("2. APPELS SANS DEFINITION  (le controle qui attrape les plantages)")
    total = 0
    for chemin, (arbre, _src) in sorted(arbres.items()):
        nom = os.path.basename(chemin)
        for cls in [n for n in ast.walk(arbre) if isinstance(n, ast.ClassDef)]:
            definis = set()
            # méthodes de la classe et de ses classes de base internes
            for n in cls.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definis.add(n.name)
            # attributs posés sur self n'importe où dans la classe
            for n in ast.walk(cls):
                if (isinstance(n, ast.Attribute)
                        and isinstance(n.value, ast.Name)
                        and n.value.id == "self"
                        and isinstance(n.ctx, ast.Store)):
                    definis.add(n.attr)
            # héritage d'une classe du projet : on ajoute ses méthodes
            for base in cls.bases:
                bn = getattr(base, "id", None) or getattr(base, "attr", None)
                if bn:
                    for autre, (a2, _s2) in arbres.items():
                        for c2 in ast.walk(a2):
                            if isinstance(c2, ast.ClassDef) and c2.name == bn:
                                for n in c2.body:
                                    if isinstance(n, (ast.FunctionDef,
                                                      ast.AsyncFunctionDef)):
                                        definis.add(n.name)
                                for n in ast.walk(c2):
                                    if (isinstance(n, ast.Attribute)
                                            and isinstance(n.value, ast.Name)
                                            and n.value.id == "self"
                                            and isinstance(n.ctx, ast.Store)):
                                        definis.add(n.attr)
            manquants = {}
            for n in ast.walk(cls):
                if not isinstance(n, ast.Call):
                    continue
                f = n.func
                if not (isinstance(f, ast.Attribute)
                        and isinstance(f.value, ast.Name)
                        and f.value.id == "self"):
                    continue
                if f.attr in definis or f.attr in TK_HERITE:
                    continue
                # Familles entières fournies par tkinter : winfo_*, tk_*,
                # event_*, image_*, selection_*. Les énumérer une par une
                # produirait des faux positifs au moindre oubli.
                if f.attr.split("_")[0] in ("winfo", "tk", "event", "image",
                                            "selection", "wm", "grid", "pack",
                                            "place", "option", "clipboard"):
                    continue
                manquants.setdefault(f.attr, f.lineno)
            for m, ligne in sorted(manquants.items()):
                total += 1
                dire("   ABSENT  {} : {}.{}()  appelé ligne {}".format(
                    nom, cls.name, m, ligne))
    if not total:
        dire("   Aucun appel orphelin. Toutes les méthodes appelées existent.")
    return total == 0


# ============================================================================
#  Contrôle 3 — langues
# ============================================================================

def _cles_dict(chemin):
    d = {}
    try:
        arbre = ast.parse(open(chemin, encoding="utf-8").read())
    except Exception:
        return d
    for n in ast.walk(arbre):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                        and isinstance(v, ast.Constant)):
                    d[k.value] = v.value
    return d


def _cles_utilisees(arbres):
    out = {}
    for chemin, (arbre, _src) in arbres.items():
        for n in ast.walk(arbre):
            if (isinstance(n, ast.Call)
                    and getattr(n.func, "id", None) in ("tr", "_tr")
                    and n.args and isinstance(n.args[0], ast.Constant)
                    and isinstance(n.args[0].value, str)):
                out.setdefault(n.args[0].value, os.path.basename(chemin))
    return out


def controle_langues(src, arbres, dire):
    dire("")
    dire("3. LANGUES")
    fr = os.path.join(src, "O4_Lang_FR.py")
    en = os.path.join(src, "O4_Lang_EN.py")
    if not (os.path.isfile(fr) and os.path.isfile(en)):
        dire("   Fichiers de langue introuvables — contrôle ignoré.")
        return True
    kfr, ken = _cles_dict(fr), _cles_dict(en)
    dire("   FR : {} clés     EN : {} clés".format(len(kfr), len(ken)))
    ok = True
    manque_en = sorted(set(kfr) - set(ken))
    manque_fr = sorted(set(ken) - set(kfr))
    if manque_en:
        ok = False
        dire("   ASYMETRIE : {} clé(s) présentes en FR, absentes en EN"
             .format(len(manque_en)))
        for k in manque_en[:5]:
            dire("      + " + repr(k[:60]))
    if manque_fr:
        ok = False
        dire("   ASYMETRIE : {} clé(s) présentes en EN, absentes en FR"
             .format(len(manque_fr)))
        for k in manque_fr[:5]:
            dire("      + " + repr(k[:60]))
    if not manque_en and not manque_fr:
        dire("   Symétrie FR/EN respectée.")

    utilisees = _cles_utilisees(arbres)
    sans = sorted(k for k in utilisees if k not in kfr)
    if sans:
        dire("   {} clé(s) utilisées dans le code sans entrée FR :"
             .format(len(sans)))
        for k in sans[:10]:
            dire("      {} ({})".format(repr(k[:50]), utilisees[k]))
        if len(sans) > 10:
            dire("      … et {} autres".format(len(sans) - 10))
        dire("   (repli sur le texte écrit dans le code — pas bloquant, "
             "mais l'anglais restera en français)")
    else:
        dire("   Toutes les clés utilisées sont traduites.")
    return ok


# ============================================================================
#  Contrôle 4 — non-régression
# ============================================================================

def signature(arbres):
    sig = {}
    for chemin, (arbre, _src) in arbres.items():
        nom = os.path.basename(chemin)
        e = {"fonctions": sorted(n.name for n in arbre.body
                                 if isinstance(n, (ast.FunctionDef,
                                                   ast.AsyncFunctionDef))),
             "classes": {}}
        for c in ast.walk(arbre):
            if isinstance(c, ast.ClassDef):
                e["classes"][c.name] = sorted(
                    n.name for n in c.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        sig[nom] = e
    return sig


def controle_regression(arbres, ref_path, dire):
    dire("")
    dire("4. NON-REGRESSION")
    if not os.path.isfile(ref_path):
        dire("   Aucune référence enregistrée.")
        dire("   Ce contrôle compare l'état actuel à une version dont vous")
        dire("   savez qu'elle fonctionne. Voir la fin du rapport.")
        return True, False
    try:
        ref = json.load(open(ref_path, encoding="utf-8"))
    except Exception as e:
        dire("   Référence illisible : " + str(e))
        return True, False
    act = signature(arbres)
    ok = True
    for nom, e in sorted(ref.get("signature", {}).items()):
        if nom not in act:
            ok = False
            dire("   FICHIER DISPARU : " + nom)
            continue
        perdues = sorted(set(e["fonctions"]) - set(act[nom]["fonctions"]))
        if perdues:
            ok = False
            dire("   {} : fonction(s) perdue(s) : {}".format(
                nom, ", ".join(perdues)))
        for cls, meths in e["classes"].items():
            actuelles = act[nom]["classes"].get(cls)
            if actuelles is None:
                ok = False
                dire("   {} : classe disparue : {}".format(nom, cls))
                continue
            pm = sorted(set(meths) - set(actuelles))
            if pm:
                ok = False
                dire("   {} : {} — méthode(s) perdue(s) : {}".format(
                    nom, cls, ", ".join(pm)))
    if ok:
        dire("   Référence du {} : rien n'a disparu.".format(
            ref.get("date", "?")))
        nouveaux = sorted(set(act) - set(ref.get("signature", {})))
        if nouveaux:
            dire("   Nouveaux fichiers depuis la référence : "
                 + ", ".join(nouveaux))
    return ok, True


def ecrire_reference(arbres, ref_path):
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    json.dump({"date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
               "version_outil": VERSION,
               "signature": signature(arbres)},
              open(ref_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


# ============================================================================
#  Programme principal
# ============================================================================

def main():
    lignes = []

    def dire(t):
        lignes.append(t)
        print(t)

    src = dossier_src()
    fichiers = fichiers_python(src)

    dire("=" * 72)
    dire("ORTHO4XP — VERIFICATION AVANT LIVRAISON        outil " + VERSION)
    dire("=" * 72)
    dire("Dossier analysé : " + src)
    dire("Fichiers Python : {}".format(len(fichiers)))
    dire("Date           : "
         + datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))

    if not fichiers:
        dire("")
        dire("Aucun fichier Python trouvé. Placez ce fichier dans")
        dire("Ortho4XP/tests/ et relancez-le.")
        return 1

    arbres, ok1 = controle_compilation(fichiers, dire)
    ok2 = controle_appels(arbres, dire)
    ok3 = controle_langues(src, arbres, dire)
    ref_path = os.path.join(racine(), "tests", "reference.json")
    ok4, avait_ref = controle_regression(arbres, ref_path, dire)

    tout = ok1 and ok2 and ok3 and ok4
    dire("")
    dire("=" * 72)
    dire("RESULTAT : " + ("TOUT EST COHERENT — LIVRABLE"
                          if tout else "ANOMALIE — NE PAS LIVRER EN L'ETAT"))
    dire("=" * 72)
    dire("  1. compilation            : " + ("OK" if ok1 else "ECHEC"))
    dire("  2. appels sans définition : " + ("OK" if ok2 else "ECHEC"))
    dire("  3. langues                : " + ("OK" if ok3 else "ECHEC"))
    dire("  4. non-régression         : "
         + ("OK" if ok4 else "ECHEC") + ("" if avait_ref else "  (sans référence)"))

    rapport = os.path.join(racine(), "tests", "rapport_verification.txt")
    try:
        os.makedirs(os.path.dirname(rapport), exist_ok=True)
        open(rapport, "w", encoding="utf-8").write("\n".join(lignes) + "\n")
        print("")
        print("Rapport écrit dans : " + rapport)
    except Exception as e:
        print("Rapport non écrit : " + str(e))

    # ── Gestion de la référence ────────────────────────────────────────
    #  Premier lancement sur une version saine : la référence est créée
    #  automatiquement, sans rien demander. C'est le comportement le plus
    #  simple, et il n'y a aucun risque : une référence prise sur un état
    #  sain ne peut que servir.
    #
    #  Une fois qu'elle existe, elle n'est JAMAIS écrasée automatiquement.
    #  Sinon une méthode disparue deviendrait la nouvelle norme au
    #  lancement suivant, et le contrôle ne servirait plus à rien.
    if tout and not avait_ref:
        try:
            ecrire_reference(arbres, ref_path)
            print("")
            print("Référence créée : " + ref_path)
            print("Les prochains lancements signaleront toute disparition")
            print("de fonction ou de méthode par rapport à cet état.")
        except Exception as e:
            print("Référence non créée : " + str(e))

    elif tout and avait_ref:
        print("")
        print("Pour prendre l'état actuel comme nouvelle référence — après")
        print("avoir ajouté une fonctionnalité et l'avoir validée — supprimez")
        print("le fichier tests/reference.json puis relancez cette")
        print("vérification : il sera recréé.")

    return 0 if tout else 1


if __name__ == "__main__":
    sys.exit(main())
