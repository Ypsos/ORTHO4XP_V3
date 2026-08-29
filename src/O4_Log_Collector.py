################################################################################
#
# O4_Log_Collector.py — Collecteur de journal unifié (Ortho4XP V3)
#
# Auteur : Roland (Ypsos)
#
# RÔLE
#   Regrouper TOUS les messages d'affichage d'Ortho4XP dans un unique fichier
#   « Ortho4XP.log » à la racine du projet, quel que soit le module qui les
#   produit et quel que soit le nom de log qu'il utilise en interne.
#
# PRINCIPE (non intrusif)
#   Le collecteur s'installe comme un FILTRE TRANSPARENT sur le flux de sortie
#   (sys.stdout) : tout ce qui est affiché passe d'abord par lui — il en garde
#   une copie pour le fichier — puis continue normalement vers la destination
#   d'origine (console, fenêtre principale…). Aucun module d'Ortho n'est
#   modifié : ils continuent d'afficher comme avant, sans savoir que le
#   collecteur existe.
#
# PERFORMANCE / SÉCURITÉ
#   - Les messages sont accumulés EN MÉMOIRE puis écrits par lots par un thread
#     de fond (pas d'ouverture/fermeture du fichier à chaque message → aucun
#     ralentissement des builds).
#   - Écriture protégée par un verrou (thread-safe) : les threads de build
#     n'entrent pas en collision sur le fichier.
#   - Tout est encapsulé dans des try/except : en cas de souci, l'application
#     n'est jamais bloquée (au pire, le log n'est pas écrit).
#
# ACTIVATION
#   Le collecteur ne fait rien tant qu'il n'est pas activé. L'activation se fait
#   par UN SEUL appel, au démarrage de l'interface :
#       import O4_Log_Collector as LOGCOL
#       LOGCOL.activate()
#   (Cet appel n'appartient à aucun module « moteur » : c'est juste
#    l'interrupteur du collecteur.)
#
#   Les fenêtres qui écrivent dans leur propre cadre SANS passer par print
#   (ex. le Générateur d'Extent) peuvent, si on le souhaite, envoyer une copie
#   de leurs messages au collecteur en UNE ligne :
#       import O4_Log_Collector as LOGCOL
#       LOGCOL.collect("mon message")
#   — sans que cela change quoi que ce soit à leur affichage habituel.
#
################################################################################

import os
import sys
import time
import threading
import pathlib as _pathlib

# ── Racine ABSOLUE du projet (comme O4_File_Names.py) ─────────────────────────
# Le log est TOUJOURS écrit ici, quel que soit le dossier de travail courant.
try:
    _ROOT = (
        str(_pathlib.Path(sys.executable).resolve().parent.parent)
        if getattr(sys, "frozen", False)
        else str(_pathlib.Path(__file__).resolve().parent.parent)
    )
except Exception:
    _ROOT = "."

_LOG_PATH = os.path.join(_ROOT, "Ortho4XP.log")

# ── État interne ──────────────────────────────────────────────────────────────
_lock = threading.Lock()      # protège le tampon ET l'écriture fichier
_buffer = []                  # lignes en attente d'écriture (horodatées)
_line_frag = {"stdout": "", "stderr": ""}  # fragments de ligne en cours
_downstream_out = None        # sys.stdout d'origine (là où l'affichage continue)
_downstream_err = None        # sys.stderr d'origine
_active = False
_flusher = None               # thread de fond
_stop = threading.Event()
_FLUSH_PERIOD = 2.0           # secondes entre deux écritures par lots


def _timestamp():
    return time.strftime("%c")


def _enqueue_text(text):
    """Découpe le texte en lignes complètes et empile chaque ligne horodatée.
    Les fragments sans « \\n » sont conservés jusqu'à la fin de la ligne."""
    if not text:
        return
    try:
        frag = _line_frag["stdout"] + text
        parts = frag.split("\n")
        # La dernière portion est un fragment incomplet (pas encore de \n).
        _line_frag["stdout"] = parts.pop()
        stamp = _timestamp()
        with _lock:
            for line in parts:
                # On journalise aussi les lignes vides pour rester fidèle.
                _buffer.append(stamp + " | " + line + "\n")
    except Exception:
        pass


def collect(msg):
    """Point d'entrée PUBLIC pour un message déjà constitué (une fenêtre qui
    écrit dans son coin peut l'appeler en une ligne, sans rien changer d'autre).
    """
    try:
        stamp = _timestamp()
        with _lock:
            _buffer.append(stamp + " | " + str(msg) + "\n")
    except Exception:
        pass


def _flush_now():
    """Écrit le tampon dans le fichier, en une seule ouverture (par lots)."""
    global _buffer
    try:
        with _lock:
            if not _buffer:
                return
            chunk = "".join(_buffer)
            _buffer = []
        # Écriture hors verrou fichier minimal : on rouvre à chaque lot (rare).
        with open(_LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(chunk)
    except Exception:
        pass


def _flusher_loop():
    while not _stop.is_set():
        _stop.wait(_FLUSH_PERIOD)
        _flush_now()
    # Dernier vidage à l'arrêt.
    _flush_now()


class _Tee(object):
    """Filtre transparent : recopie vers la destination d'origine ET capture."""
    def __init__(self, downstream):
        self._downstream = downstream

    def write(self, text):
        # 1) Laisser l'affichage continuer normalement (console, fenêtre…).
        try:
            if self._downstream is not None:
                self._downstream.write(text)
        except Exception:
            pass
        # 2) Capturer pour le fichier log.
        _enqueue_text(text)
        # write() doit renvoyer le nombre de caractères pour rester compatible.
        try:
            return len(text)
        except Exception:
            return 0

    def flush(self):
        try:
            if self._downstream is not None:
                self._downstream.flush()
        except Exception:
            pass

    # Certains codes interrogent ces attributs ; on les délègue proprement.
    def __getattr__(self, name):
        return getattr(self._downstream, name)


def activate():
    """Installe le collecteur : interception de sys.stdout / sys.stderr +
    démarrage du thread d'écriture. Idempotent (rien si déjà actif)."""
    global _active, _downstream_out, _downstream_err, _flusher
    if _active:
        return
    try:
        _downstream_out = sys.stdout
        _downstream_err = sys.stderr
        sys.stdout = _Tee(_downstream_out)
        sys.stderr = _Tee(_downstream_err)
        _stop.clear()
        _flusher = threading.Thread(target=_flusher_loop, daemon=True)
        _flusher.start()
        _active = True
        collect("──────── Ortho4XP — démarrage de la session ────────")
    except Exception:
        # En cas d'échec, on restaure au mieux et on n'active pas.
        try:
            if _downstream_out is not None:
                sys.stdout = _downstream_out
            if _downstream_err is not None:
                sys.stderr = _downstream_err
        except Exception:
            pass
        _active = False


def deactivate():
    """Restaure sys.stdout/err d'origine et vide le tampon. Optionnel."""
    global _active
    if not _active:
        return
    try:
        # Vider le fragment de ligne restant.
        if _line_frag["stdout"]:
            collect(_line_frag["stdout"])
            _line_frag["stdout"] = ""
        _stop.set()
        _flush_now()
        if _downstream_out is not None:
            sys.stdout = _downstream_out
        if _downstream_err is not None:
            sys.stderr = _downstream_err
    except Exception:
        pass
    finally:
        _active = False


def log_path():
    """Renvoie le chemin absolu du fichier log unifié."""
    return _LOG_PATH
