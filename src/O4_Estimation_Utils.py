# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# O4_Estimation_Utils.py
# Estimation locale (disque + temps) AVANT le build d'une tuile.
#
# Auteur : Roland (Ypsos) - GPLv3
#
# ROLE (CDC V3.6, Priorite 1) :
#   Afficher, avant lancement, l'espace disque requis + la duree estimee
#   pour tuile + provider + ZL choisis. 100 % calcul LOCAL, aucun reseau,
#   aucun build.
#
# PRINCIPE (le plus sur) :
#   On NE recopie PAS la formule de grille. On REUTILISE la vraie fonction
#   moteur O4_DSF_Utils.zone_list_to_ortho_dico(tile), exactement celle
#   qu'utilise le build. Le nombre de textures est donc, par construction,
#   IDENTIQUE a celui du build reel : zones a ZL personnalise et
#   sur-resolution aeroport comprises, pour toujours et sans divergence.
#
# CHAPITRE 1 (ce fichier) : coeur de calcul pur, sans interface, sans
#   dependance tkinter/theme -> ne peut rien casser dans les fenetres.
#   Le bouton d'entree (Menu Avance / fenetre de config) = Chapitre 2,
#   livre apres validation de ce coeur.
#
# 100 % ADDITIF : aucun fichier moteur touche. Import de O4_DSF_Utils en
#   LOCAL (dans la fonction) pour eviter tout cycle d'import a l'ouverture.
# ------------------------------------------------------------------------------

# --- Reperes CDC V3.6 (Priorite 1). Constantes ajustables sans toucher a la
# --- logique. Toutes les textures Ortho4XP font 4096x4096 quel que soit le ZL,
# --- donc la taille par texture ne depend pas du ZL (seule leur QUANTITE change).
#
# Disque : le CDC donne "ZL16 ~ 1,5-4 Go/tuile" ; en ZL16 une tuile ~ 234
# textures -> 1,5-4 Go / 234 ~ 6,5 a 17,5 Mo par texture (DDS + JPG source
# conserves). On garde une fourchette min/max, plus honnete qu'un faux chiffre.
MO_PAR_TEXTURE_MIN = 6.5
MO_PAR_TEXTURE_MAX = 17.5

# Temps : le CDC donne "~40-60 s/texture-tuile en telechargement SEQUENTIEL".
SEC_PAR_TEXTURE_MIN = 40.0
SEC_PAR_TEXTURE_MAX = 60.0


def _L(fr, en):
    """Libelle bilingue resolu dans le module (ne touche pas O4_Lang_*)."""
    try:
        import O4_Lang_Utils  # noqa
        code = getattr(O4_Lang_Utils, "_current_lang", "en")
    except Exception:
        try:
            import O4_UI_Utils as UI
            code = getattr(UI, "lang", "en")
        except Exception:
            code = "en"
    code = (code or "en")
    code = code[:2].lower() if isinstance(code, str) else "en"
    return fr if code == "fr" else en


def _counts_from_dico(dico_customzl):
    """
    Coeur PUR et testable en headless.
    Entree : dico_customzl tel que renvoye par zone_list_to_ortho_dico,
             cad { (til_x, til_y) : (til_x_text, til_y_text, zl, provider) }.
    Sortie : (total_textures, { zl : nb_textures }) sur les textures DISTINCTES.
    """
    textures = set(dico_customzl.values())  # (txt, tyt, zl, provider) uniques
    par_zl = {}
    for (_txt, _tyt, zl, _prov) in textures:
        par_zl[zl] = par_zl.get(zl, 0) + 1
    return (len(textures), dict(sorted(par_zl.items())))


def compute_counts(tile):
    """
    Chemin de PRODUCTION : reutilise la vraie fonction moteur.
    Retourne (total_textures, { zl : nb }) ou leve l'exception d'origine.
    Import LOCAL de O4_DSF_Utils (aucun effet a l'ouverture du module).
    """
    import O4_DSF_Utils as DSF
    dico = DSF.zone_list_to_ortho_dico(tile)
    return _counts_from_dico(dico)


def estimate_from_counts(total, par_zl):
    """
    Calcul pur disque + temps a partir d'un comptage de textures.
    Retourne un dict structure (aucun arrondi trompeur : fourchettes min/max).
    """
    disque_go_min = total * MO_PAR_TEXTURE_MIN / 1024.0
    disque_go_max = total * MO_PAR_TEXTURE_MAX / 1024.0
    temps_s_min = total * SEC_PAR_TEXTURE_MIN
    temps_s_max = total * SEC_PAR_TEXTURE_MAX
    return {
        "total_textures": total,
        "par_zl": par_zl,
        "disque_go_min": disque_go_min,
        "disque_go_max": disque_go_max,
        "temps_s_min": temps_s_min,
        "temps_s_max": temps_s_max,
    }


def estimate(tile):
    """Production : de la tuile a l'estimation complete."""
    total, par_zl = compute_counts(tile)
    return estimate_from_counts(total, par_zl)


def _fmt_duree(sec):
    sec = int(round(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    if h:
        return "%dh%02d" % (h, m)
    if m:
        return "%dmin" % m
    return "%ds" % sec


def format_report(est):
    """Texte bilingue pret a afficher (fenetre ou console)."""
    lignes = []
    lignes.append(_L("Estimation AVANT build (calcul local, aucun reseau)",
                     "Estimate BEFORE build (local calc, no network)"))
    lignes.append(_L("Textures a generer : ", "Textures to generate: ")
                  + str(est["total_textures"]))
    if len(est["par_zl"]) > 1:
        det = ", ".join("ZL%d: %d" % (zl, n) for zl, n in est["par_zl"].items())
        lignes.append(_L("  detail par ZL : ", "  by ZL: ") + det)
    lignes.append(_L("Disque estime : ", "Estimated disk: ")
                  + "%.1f - %.1f Go" % (est["disque_go_min"], est["disque_go_max"]))
    lignes.append(_L("Temps estime (telechargement sequentiel) : ",
                     "Estimated time (sequential download): ")
                  + "%s - %s" % (_fmt_duree(est["temps_s_min"]),
                                 _fmt_duree(est["temps_s_max"])))
    lignes.append(_L("  (le build parallele est generalement plus rapide)",
                     "  (parallel build is usually faster)"))
    return "\n".join(lignes)


# ------------------------------------------------------------------------------
# AUTO-TEST HEADLESS (ne s'execute qu'en lancement direct ; jamais a l'import).
# Reproduit fidelement l'algorithme moteur pour prouver le comptage SANS le
# moteur, puis verifie estimate_from_counts et format_report.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    from math import pi, log, tan, atan, exp
    from PIL import Image, ImageDraw

    def _orthogrid(lat, lon, zl):
        rx = lon / 180
        ry = log(tan((90 + lat) * pi / 360)) / pi
        m = 2 ** (zl - 5)
        return (int((rx + 1) * m) * 16, int((1 - ry) * m) * 16)

    def _gtile(tx, ty, zl):
        rx = tx / (2 ** (zl - 1)) - 1
        ry = 1 - ty / (2 ** (zl - 1))
        return (360 / pi * atan(exp(pi * ry)) - 90, rx * 180)

    class _T:
        def __init__(s, lat, lon, dzl, mzl=19, zl=None):
            s.lat = lat; s.lon = lon; s.default_zl = dzl; s.mesh_zl = mzl
            s.default_website = "TEST"; s.zone_list = zl or []

    def _fake_dico(tile):
        im = Image.new("L", (4096, 4096), "black"); dr = ImageDraw.Draw(im)
        dt = {}; dico = {}
        xmn, ymn = _orthogrid(tile.lat + 1, tile.lon, tile.mesh_zl)
        xmx, ymx = _orthogrid(tile.lat, tile.lon + 1, tile.mesh_zl)
        i = 1
        base = ([tile.lat, tile.lon, tile.lat, tile.lon + 1,
                 tile.lat + 1, tile.lon + 1, tile.lat + 1, tile.lon,
                 tile.lat, tile.lon], tile.default_zl, tile.default_website)
        for region in [base] + tile.zone_list[::-1]:
            dt[i] = (region[1], region[2])
            pol = [(round((x - tile.lon) * 4095), round((tile.lat + 1 - y) * 4095))
                   for (x, y) in zip(region[0][1::2], region[0][::2])]
            dr.polygon(pol, fill=i); i += 1
        for tx in range(xmn, xmx + 1, 16):
            for ty in range(ymn, ymx + 1, 16):
                latp, lonp = _gtile(tx + 8, ty + 8, tile.mesh_zl)
                lonp = max(min(lonp, tile.lon + 1), tile.lon)
                latp = max(min(latp, tile.lat + 1), tile.lat)
                x = round((lonp - tile.lon) * 4095); y = round((tile.lat + 1 - latp) * 4095)
                zl, prov = dt[im.getpixel((x, y))]
                txt = 16 * (int(tx / 2 ** (tile.mesh_zl - zl)) // 16)
                tyt = 16 * (int(ty / 2 ** (tile.mesh_zl - zl)) // 16)
                dico[(tx, ty)] = (txt, tyt, zl, prov)
        return dico

    print("=== AUTO-TEST O4_Estimation_Utils ===")
    ok = True

    # T1 : comptage uniforme = valeurs de reference du Chapitre 1
    attendu = {16: 234, 17: 816, 18: 3082}
    for zl in (16, 17, 18):
        total, par = _counts_from_dico(_fake_dico(_T(46, -3, zl)))
        flag = "OK" if total == attendu[zl] else "ECHEC"
        if total != attendu[zl]:
            ok = False
        print("T1 ZL%d uniforme -> %d textures [%s]" % (zl, total, flag))

    # T2 : zone perso ZL18 dans une base ZL17
    zone = ([46.4, -2.6, 46.4, -2.4, 46.6, -2.4, 46.6, -2.6, 46.4, -2.6], 18, "TEST")
    total2, par2 = _counts_from_dico(_fake_dico(_T(46, -3, 17, zl=[zone])))
    cond = (17 in par2 and 18 in par2 and par2[17] + par2[18] == total2)
    ok = ok and cond
    print("T2 ZL17 + zone ZL18 -> %d textures, par_zl=%s [%s]"
          % (total2, par2, "OK" if cond else "ECHEC"))

    # T3 : estimate_from_counts + format_report sur 816 textures
    est = estimate_from_counts(816, {17: 816})
    print("T3 estimate 816 tex :")
    print(format_report(est))
    cond3 = (abs(est["disque_go_min"] - 816 * 6.5 / 1024) < 1e-9
             and est["temps_s_max"] == 816 * 60)
    ok = ok and cond3
    print("T3 math [%s]" % ("OK" if cond3 else "ECHEC"))

    print("=== RESULTAT GLOBAL : %s ===" % ("TOUT VERT" if ok else "ECHEC"))


# ------------------------------------------------------------------------------
# CHAPITRE 2b : controle de place disque AVANT l'Etape 1 (fabrication).
# Appele tout au debut de build_tile, dans le thread principal, AVANT tout
# traitement. Regle de securite : on ne BLOQUE que si la place manque meme
# dans l'hypothese la plus OPTIMISTE (+ marge) -> jamais de faux blocage d'un
# build qui a des chances de tenir. Si le controle lui-meme echoue, l'appelant
# laisse le build demarrer (fail-open) : ce controle ne casse jamais un build.
# ------------------------------------------------------------------------------
import os
import shutil

MARGE_GO = 1.0  # marge de travail (fichiers temporaires, JPG sources, etc.)


def _disque_libre_go(path):
    """Place libre (Go) sur le disque du dossier ; remonte au 1er dossier
    existant si build_dir n'existe pas encore ; repli sur ~ en dernier."""
    p = path or ""
    while p and not os.path.isdir(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    if not p or not os.path.isdir(p):
        p = os.path.expanduser("~")
    return shutil.disk_usage(p).free / (1024.0 ** 3)


def _disk_decision(est, libre_go):
    """PUR et testable. (ok, message). Bloque seulement si libre < min+marge."""
    requis_min = est["disque_go_min"] + MARGE_GO
    if libre_go >= requis_min:
        return (True, "")
    manque = requis_min - libre_go
    msg = _L(
        "ERREUR : place disque insuffisante pour l'Etape 1. Besoin d'au moins "
        "%.1f Go, disponible %.1f Go (il manque %.1f Go). Libere de la place "
        "ou choisis un autre disque, puis relance."
        % (requis_min, libre_go, manque),
        "ERROR: not enough disk space for Step 1. Need at least %.1f GB, "
        "available %.1f GB (missing %.1f GB). Free up space or pick another "
        "disk, then relaunch."
        % (requis_min, libre_go, manque),
    )
    return (False, msg)


def check_disk_before_build(tile):
    """Production : (ok, message). Utilise l'estimation reelle de la tuile."""
    est = estimate(tile)
    libre = _disque_libre_go(getattr(tile, "build_dir", "") or "")
    return _disk_decision(est, libre)
