import os
import sys
import time
import pathlib as _pathlib
from O4_Lang import tr

Ortho4XP_dir = ".." if getattr(sys, "frozen", False) else "."

# Racine ABSOLUE du projet, calculée comme dans O4_File_Names.py (à partir de
# l'emplacement réel de ce fichier, src/ → racine). Sert UNIQUEMENT à écrire
# Ortho4XP.log toujours à la racine, quel que soit le dossier de travail
# courant. L'ancien Ortho4XP_dir="." (relatif) suivait le dossier courant : le
# log partait alors dans le dossier de travail (ex. dossier d'un extent).
# On ne modifie PAS Ortho4XP_dir (lu ailleurs) : on ajoute juste cette racine
# dédiée au log, avec repli sûr sur l'ancien comportement en cas d'imprévu.
try:
    _LOG_ROOT = (
        str(_pathlib.Path(sys.executable).resolve().parent.parent)
        if getattr(sys, "frozen", False)
        else str(_pathlib.Path(__file__).resolve().parent.parent)
    )
except Exception:
    _LOG_ROOT = Ortho4XP_dir
verbosity = 1
red_flag = False
is_working = False
cleaning_level = 1
gui = None
log = True

# ---------------------------------------------------------------------------
# Point 3 (V3.6) — Suivi de build detaille en console (temps restant + vitesse)
#
# 100 % ADDITIF. progress_bar continue d'etre appelee EXACTEMENT comme avant
# par le moteur (mesh, masques, textures...). On ajoute seulement, a la fin de
# progress_bar, un appel a un observateur qui regarde la suite des pourcentages
# deja transmis et imprime de temps en temps une ligne d'estimation en console.
# Aucune dependance au GUI, aucun reseau, aucune ecriture disque. Tout est
# enferme dans des try/except : si quoi que ce soit tourne mal, le suivi
# echoue en SILENCE et n'impacte jamais le build. Pour desactiver ce suivi,
# il suffit de mettre _ETA_ENABLED = False ci-dessous (rien d'autre a toucher).
_ETA_ENABLED = True         # False = plus aucune ligne de suivi, comme avant
_ETA_INTERVAL = 5.0         # secondes minimum entre deux lignes affichees
_ETA_MIN_PERCENT = 3        # on attend un peu d'avancee avant d'estimer
# Libelles bilingues (fr, en) par numero de barre. Une barre absente de cette
# table n'affiche AUCUN suivi (evite de noyer la console sur les micro-etapes).
_ETA_BAR_LABELS = {
    2: ("Mer/masques", "Sea/masks"),
    3: ("Textures", "Textures"),
}
# Etat interne par barre : {nbr: {"t0", "last_print", "p0", "last_p"}}
_eta_state = {}


def _L(fr, en):
    # Helper bilingue interne, totalement defensif : si la langue ne peut pas
    # etre lue pour une raison quelconque, on retombe sur le francais.
    try:
        code = ""
        try:
            import O4_Lang as _lang
            _fn = getattr(_lang, "current_lang", None)
            if callable(_fn):
                code = str(_fn() or "")
            else:
                code = str(getattr(_lang, "_current_lang", "") or "")
        except Exception:
            code = ""
        return en if code.lower().startswith("en") else fr
    except Exception:
        return fr


def _eta_bar_label(nbr):
    pair = _ETA_BAR_LABELS.get(nbr)
    if not pair:
        return None
    return _L(pair[0], pair[1])


def _eta_observe(nbr, percentage):
    # Appelee depuis progress_bar. 100 % defensive : toute erreur est avalee
    # pour ne JAMAIS perturber le build.
    try:
        if not _ETA_ENABLED:
            return
        label = _eta_bar_label(nbr)
        if label is None:
            return
        try:
            p = int(percentage)
        except Exception:
            return
        now = time.time()
        st = _eta_state.get(nbr)
        # (Re)demarrage d'une phase : pas d'etat, ou le pourcentage recule
        # (nouvelle tuile / nouvelle passe sur la meme barre).
        if st is None or p < st.get("last_p", 0):
            _eta_state[nbr] = {
                "t0": now,
                "last_print": now,
                "p0": p,
                "last_p": p,
            }
            return
        st["last_p"] = p
        # Fin de phase : une ligne finale nette, puis on oublie l'etat.
        if p >= 100:
            elapsed = now - st["t0"]
            if elapsed >= 1:
                print(
                    "      [" + label + "] 100% — "
                    + _L("termine en ", "done in ")
                    + nicer_timer(elapsed)
                )
            _eta_state.pop(nbr, None)
            return
        # Trop tot pour une estimation fiable.
        if p < _ETA_MIN_PERCENT:
            return
        # On n'imprime qu'a intervalle regulier (ne pas noyer la console).
        if now - st["last_print"] < _ETA_INTERVAL:
            return
        elapsed = now - st["t0"]
        gained = p - st["p0"]
        if elapsed <= 0 or gained <= 0:
            return
        pct_per_sec = gained / elapsed
        if pct_per_sec <= 0:
            return
        remaining = (100 - p) / pct_per_sec
        speed_per_min = pct_per_sec * 60.0
        print(
            "      [" + label + "] " + str(p) + "% — "
            + _L("vitesse ~", "speed ~")
            + "{:.0f}".format(speed_per_min)
            + _L("%/min — reste ~", "%/min — left ~")
            + nicer_timer(remaining)
        )
        st["last_print"] = now
    except Exception:
        # Le suivi ne doit JAMAIS casser le build.
        pass


################################################################################
def progress_bar(nbr, percentage, message=None):
    if gui:
        gui.pgrbv[nbr].set(percentage)
    # Point 3 : suivi console non-intrusif (n'affiche rien pour une barre
    # inconnue, et n'echoue jamais).
    _eta_observe(nbr, percentage)


################################################################################
def vprint(min_verbosity, *args):
    if verbosity >= min_verbosity:
        print(*args)


################################################################################
def logprint(*args):
    try:
        f = open(os.path.join(_LOG_ROOT, "Ortho4XP.log"), "a")
        f.write(
            time.strftime("%c")
            + " | "
            + " ".join([str(x) for x in args])
            + "\n"
        )
        f.close()
    except:
        pass


################################################################################
def lvprint(min_verbosity, *args):
    if verbosity >= min_verbosity:
        print(*args)
    if log:
        logprint(*args)


################################################################################
def bug_report(*args):
    logprint(
        "An internal error occured. Please file a bug with lat/lon and cfg"
    )
    if args:
        logprint(*args)


################################################################################
def exit_message_and_bottom_line(*args):
    global is_working
    if not args:
        args = ("Next Step",)
    if args[0]:
        logprint(*args)
        print(*args)
    print(
        "_____________________________________________________________"
        + "____________________________________"
    )
    is_working = False


################################################################################
def timings_and_bottom_line(tinit):
    global is_working
    print("\nCompleted in " + nicer_timer(time.time() - tinit) + ".")
    print(
        "_____________________________________________________________"
        + "____________________________________"
    )
    is_working = False


################################################################################
def human_print(num, suffix=""):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "{:.1f}{}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:.1f}{}{}".format(num, "Y", suffix)


################################################################################
def nicer_timer(elapsed):
    out_string = ""
    hours = elapsed // 3600
    if hours:
        elapsed -= 3600 * hours
        out_string += str(int(hours)) + "h"
    minutes = elapsed // 60
    if hours or minutes:
        elapsed -= 60 * minutes
        out_string += str(int(minutes)) + "m"
    elapsed = "{:.2f}".format(elapsed) if not out_string else int(elapsed)
    out_string += str(elapsed) + "sec"
    return out_string
