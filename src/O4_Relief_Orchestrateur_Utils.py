# -*- coding: utf-8 -*-
#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================
#  O4_Relief_Orchestrateur_Utils.py  —  ÉTAPE 3 : orchestration mode débutant
#
#  Auteur : Roland (Ypsos)
#  Projet : Ortho4XP V3
#
#  RÔLE — Chef d'orchestre du relief HAUTE DÉFINITION automatique pour le
#    MODE DÉBUTANT (uniquement Sonny .hgt). Il n'invente aucune logique : il
#    ENCHAÎNE des briques déjà écrites et validées :
#
#      chapitre 1  O4_Relief_Auto_Utils   -> zone couverte par Sonny ?
#      chapitre 2  O4_Relief_Sonny_Utils  -> .hgt rangés couvrant la tuile ?
#      garde-fou   O4_Datum_Utils         -> alerte si dalle ellipsoïdale
#      Altimétrie  O4_Altimetrie_Utils    -> assembler_tuile() + ecrire_custom_dem()
#
#  COMPORTEMENT (décidé avec Roland) :
#    - .hgt couvrants PRÉSENTS  -> on assemble et on renseigne custom_dem,
#      SILENCE total (aucune question). Vaut pour toute tuile d'un pays déjà
#      installé (France entière, Alsace, Alpes, bord de mer… peu importe).
#    - .hgt couvrants ABSENTS   -> on NE construit PAS de relief HD ; on
#      retourne un statut « À_INSTALLER » pour que l'interface pose UNE seule
#      question « installer le relief HD de cette zone ? ». Si l'utilisateur
#      refuse, Ortho4XP reprend son DEM classique (custom_dem non écrit).
#
#  Ce module NE modifie pas O4_Altimetrie_Utils.py : il appelle ses fonctions
#  publiques (assembler_tuile, ecrire_custom_dem) par import. Il ne touche pas
#  au moteur, n'écrit custom_dem que via la fonction existante de Roland, et
#  ne lève JAMAIS vers l'appelant.
#
#  IMPORTANT : ce module se contente d'ORCHESTRER. La partie interface
#  (bouton, question Oui/Non, guidage téléchargement, choix du disque) sera
#  branchée dans la fenêtre Altimétrie du Menu Avancé — pas ici.
# ----------------------------------------------------------------------------

import os

# Statuts de retour (stables, lisibles par l'interface).
FAIT          = "fait"           # relief HD assemblé + custom_dem écrit
A_INSTALLER   = "a_installer"    # zone Sonny mais .hgt manquants -> question
HORS_ZONE     = "hors_zone"      # pas de couverture Sonny -> relief standard
ECHEC         = "echec"          # incident maîtrisé -> relief standard


# Imports « souples » : si un module manque, on retombe proprement sur ECHEC
# plutôt que de casser (aucun import ne doit faire planter l'orchestrateur).
try:
    import O4_Relief_Auto_Utils as RAUTO
except Exception:
    RAUTO = None
try:
    import O4_Relief_Sonny_Utils as SONNY
except Exception:
    SONNY = None
try:
    import O4_Datum_Utils as DATUM
except Exception:
    DATUM = None


def _log_fn(log):
    def _l(m):
        try:
            (log or (lambda *_: None))(m)
        except Exception:
            pass
    return _l


def _ouvrir_datasets(chemins):
    """Ouvre les .hgt via rasterio pour le contrôle datum, si rasterio est
    présent. Retourne (liste_ouverts, fermeture). En l'absence de rasterio,
    retourne ([], noop) : le garde-fou est simplement sauté, jamais bloquant.
    """
    try:
        import rasterio
    except Exception:
        return [], (lambda: None)
    ouverts = []
    for c in chemins:
        try:
            ouverts.append(rasterio.open(c))
        except Exception:
            pass

    def _fermer():
        for o in ouverts:
            try:
                o.close()
            except Exception:
                pass
    return ouverts, _fermer


def generer_relief_tuile(lat, lon, dossier_tuile, cfg_path,
                         dossier_gere, debord=0.0,
                         assembler=None, ecrire_cfg=None,
                         index=None, log=None):
    """Tente de produire le relief HD Sonny pour la tuile (lat, lon).

    Paramètres injectables (pour test / découplage) :
      assembler(lat, lon, dossier_tuile, sources=...)-> chemin .tif
          défaut : O4_Altimetrie_Utils.assembler_tuile
      ecrire_cfg(cfg_path, chemin_tif) -> None
          défaut : O4_Altimetrie_Utils.ecrire_custom_dem

    Retour : dict {
        'statut'  : FAIT | A_INSTALLER | HORS_ZONE | ECHEC,
        'tif'     : chemin du .tif produit (si FAIT),
        'source'  : identifiant source (Sonny / swiss / None),
        'message' : texte prêt à afficher à l'utilisateur,
        'dalles'  : nb de .hgt utilisés (si FAIT),
    }
    Ne lève JAMAIS. Sur tout incident -> statut ECHEC -> relief standard.
    """
    _l = _log_fn(log)
    res = {"statut": ECHEC, "tif": None, "source": None,
           "message": "", "dalles": 0}

    # 0) Modules de base présents ?
    if SONNY is None:
        res["message"] = "Module Sonny indisponible : relief standard."
        _l("   [RELIEF] " + res["message"])
        return res

    # 1) Zone couverte par une source HR ? (chapitre 1)
    source = None
    if RAUTO is not None:
        try:
            source = RAUTO.source_pour_tuile(lat, lon)
        except Exception:
            source = None
    res["source"] = source
    if not source:
        res["statut"] = HORS_ZONE
        res["message"] = ("Pas de relief haute définition pour cette zone : "
                          "relief standard utilisé.")
        _l("   [RELIEF] Hors zone HR → relief standard.")
        return res

    # 2) A-t-on les .hgt couvrant la tuile ? (chapitre 2)
    try:
        couv = SONNY.dalles_pour_tuile(dossier_gere, lat, lon,
                                       debord=debord, index=index, log=log)
    except Exception:
        couv = {"ok": False, "fichiers": []}

    if not couv.get("ok"):
        # Zone Sonny mais données pas encore installées → question interface.
        res["statut"] = A_INSTALLER
        res["message"] = ("Un relief haute définition est disponible pour "
                          "cette zone. Souhaitez-vous l'installer ?")
        _l("   [RELIEF] Données manquantes → proposer l'installation.")
        return res

    fichiers = couv["fichiers"]

    # 3) Garde-fou datum (jamais bloquant, seulement informatif).
    if DATUM is not None:
        ouverts, fermer = _ouvrir_datasets(fichiers)
        try:
            if ouverts:
                DATUM.avertir_si_datum_suspect(ouverts, log=log)
        finally:
            fermer()

    # 4) Assemblage via la fonction RÉELLE de l'Altimétrie (ou injectée).
    if assembler is None:
        try:
            import O4_Altimetrie_Utils as ALTI
            assembler = ALTI.assembler_tuile
        except Exception:
            res["message"] = "Module Altimétrie indisponible : relief standard."
            _l("   [RELIEF] " + res["message"])
            return res

    try:
        tif = assembler(lat, lon, dossier_tuile, sources=fichiers, log=log)
    except TypeError:
        # Signature sans 'log' : on retente sans ce paramètre.
        try:
            tif = assembler(lat, lon, dossier_tuile, sources=fichiers)
        except Exception as e:
            res["message"] = "Assemblage impossible (%s) : relief standard." \
                             % type(e).__name__
            _l("   [RELIEF] " + res["message"])
            return res
    except Exception as e:
        res["message"] = "Assemblage impossible (%s) : relief standard." \
                         % type(e).__name__
        _l("   [RELIEF] " + res["message"])
        return res

    if not tif or not os.path.isfile(tif):
        res["message"] = "TIFF non produit : relief standard."
        _l("   [RELIEF] " + res["message"])
        return res

    # 5) Écriture custom_dem via la fonction RÉELLE de l'Altimétrie (ou injectée).
    if ecrire_cfg is None:
        try:
            import O4_Altimetrie_Utils as ALTI
            ecrire_cfg = ALTI.ecrire_custom_dem
        except Exception:
            ecrire_cfg = None

    if ecrire_cfg is not None and cfg_path:
        try:
            ecrire_cfg(cfg_path, tif)
        except Exception as e:
            # Le TIFF existe ; seule l'écriture cfg a échoué. On le signale,
            # mais on n'efface rien : l'utilisateur peut pointer le TIFF.
            _l("   [RELIEF] custom_dem non écrit (%s)." % type(e).__name__)

    res["statut"] = FAIT
    res["tif"] = tif
    res["dalles"] = len(fichiers)
    res["message"] = ("Relief haute définition intégré (%d dalle(s))."
                      % len(fichiers))
    _l("   [RELIEF] " + res["message"])
    return res
