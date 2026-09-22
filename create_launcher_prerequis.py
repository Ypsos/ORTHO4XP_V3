#!/usr/bin/env python3
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
"""
create_launcher.py — Ortho4XP V3.0
Génère le lanceur natif par plateforme :
  macOS   → Lanceur_Installation_Prerequis.app  (binaire C autonome, zéro dépendance)
  Windows → Lanceur_Installation_Prerequis.vbs
  Linux   → Lanceur_Installation_Prerequis.desktop + .sh
"""
from __future__ import annotations
import os
import platform
import stat
import subprocess
import sys
from pathlib import Path

HERE   = Path(__file__).resolve().parent
SYSTEM = platform.system()

if SYSTEM == "Windows":
    VENV_PY = HERE / "venv" / "Scripts" / "python.exe"
else:
    VENV_PY = HERE / "venv" / "bin" / "python3"


# ══════════════════════════════════════════════════════════════════════════════
#  macOS — INSTALL_ORTHO4XP.app  (binaire C universel autonome)
# ══════════════════════════════════════════════════════════════════════════════
#
#  Flux complet géré par le binaire C (zéro Python requis au départ) :
#
#  1. Trouve ORTHO4XP_V2/ via _NSGetExecutablePath (chemin relatif)
#  2. Vérifie Python 3.12 → absent → installe Homebrew + python@3.12
#     via osascript dialogs natifs macOS (aucun terminal visible)
#  3. Vérifie venv/ → absent → le crée silencieusement
#  4. Lance INSTALL_PREREQUIS.py → fenêtre verte tkinter prend le relais
#
# ══════════════════════════════════════════════════════════════════════════════

LAUNCHER_C_SOURCE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#include <libgen.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/statvfs.h>
#include <dirent.h>

extern int _NSGetExecutablePath(char *buf, uint32_t *bufsize);

static int path_exists(const char *p) {
    struct stat st; return stat(p, &st) == 0;
}

/* DMG = volume en LECTURE SEULE (un disque externe choisi par
 * l'utilisateur, lui, est inscriptible). Critère fiable : ne dépend
 * pas du chemin /Volumes/ (qui contient aussi les disques externes). */
static int is_readonly_volume(const char *p) {
    struct statvfs s;
    if (statvfs(p, &s) != 0) return 0;
    return (s.f_flag & ST_RDONLY) != 0;
}

/* macOS « translocation » : une app téléchargée, ouverte la 1re fois,
 * est lancée depuis une copie cachée (…/AppTranslocation/…) et non
 * depuis le DMG. Le dossier ORTHO4XP_V3 n'est alors pas à côté du
 * lanceur : on le retrouve sur le DMG monté dans /Volumes
 * (volume en lecture seule contenant ORTHO4XP_V3/INSTALL_PREREQUIS.py). */
static int find_dmg_source_in_volumes(char *out, size_t outsz) {
    DIR *d = opendir("/Volumes");
    if (!d) return 0;
    struct dirent *e;
    int found = 0;
    while (!found && (e = readdir(d)) != NULL) {
        if (e->d_name[0] == '.') continue;
        char vol[PATH_MAX], probe[PATH_MAX];
        if (snprintf(vol, sizeof(vol), "/Volumes/%s", e->d_name) >= (int)sizeof(vol)) continue;
        if (snprintf(probe, sizeof(probe), "%s/ORTHO4XP_V3/INSTALL_PREREQUIS.py", vol) >= (int)sizeof(probe)) continue;
        if (path_exists(probe) && is_readonly_volume(vol)) {
            if (snprintf(out, outsz, "%s/ORTHO4XP_V3", vol) < (int)outsz) found = 1;
        }
    }
    closedir(d);
    return found;
}

/* Le venv Python a besoin de liens symboliques : absents sur un disque
 * formaté exFAT/FAT (format Windows) ou si le dossier n'est pas
 * inscriptible. Test réel : on crée puis on efface un lien. */
static int dest_is_usable(const char *dir) {
    char probe[PATH_MAX];
    if (snprintf(probe, sizeof(probe), "%s/.o4xp_test_lien", dir) >= (int)sizeof(probe))
        return 0;
    unlink(probe);
    if (symlink("o4xp", probe) != 0) return 0;
    unlink(probe);
    return 1;
}

/* Dialog bloquant natif */
static void dialog(const char *title, const char *msg, const char *icon) {
    char script[4096];
    snprintf(script, sizeof(script),
        "display dialog \"%s\" buttons {\"OK\"} "
        "default button \"OK\" with title \"%s\" with icon %s",
        msg, title, icon);
    char *args[] = { "/usr/bin/osascript", "-e", script, NULL };
    pid_t pid = fork();
    if (pid == 0) { execv("/usr/bin/osascript", args); _exit(1); }
    if (pid > 0) { int st; waitpid(pid, &st, 0); }
}

/* Notification non-bloquante */
static void notify(const char *title, const char *msg) {
    char script[2048];
    snprintf(script, sizeof(script),
        "display notification \"%s\" "
        "with title \"%s\" subtitle \"Ortho4XP V3.0\"",
        msg, title);
    char *args[] = { "/usr/bin/osascript", "-e", script, NULL };
    pid_t pid = fork();
    if (pid == 0) { execv("/usr/bin/osascript", args); _exit(1); }
    if (pid > 0) { int st; waitpid(pid, &st, 0); }
}

/* Exécute cmd[] via fork/execv et attend la fin — pas de bash, pas de PATH */
static int run_direct(const char *argv0, char *const argv[], const char *log) {
    pid_t pid = fork();
    if (pid == 0) {
        /* Enfant : rediriger stdout+stderr vers le log */
        FILE *f = fopen(log, "a");
        if (f) {
            int fd = fileno(f);
            dup2(fd, STDOUT_FILENO);
            dup2(fd, STDERR_FILENO);
        }
        execv(argv0, argv);
        _exit(1);
    } else if (pid > 0) {
        int status;
        waitpid(pid, &status, 0);
        return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
    }
    return 1;
}

/* Installe Homebrew via curl+bash — seule exception qui nécessite un shell */

static int choose_destination(char *out, size_t outsz) {
    FILE *p = popen(
        "/usr/bin/osascript -e 'POSIX path of (choose folder with prompt \"Choisissez le disque de destination pour ORTHO4XP V3\")' 2>/dev/null",
        "r"
    );

    if (!p) return 0;

    if (!fgets(out, (int)outsz, p)) {
        pclose(p);
        return 0;
    }

    int status = pclose(p);
    if (status != 0) return 0;

    size_t n = strlen(out);
    while (n > 0 && (out[n - 1] == '\n' || out[n - 1] == '\r'))
        out[--n] = '\0';

    return n > 0;
}

static int copy_from_dmg(const char *source, const char *destination) {
    pid_t pid = fork();

    if (pid < 0)
        return 0;

    if (pid == 0) {
        execl(
            "/usr/bin/ditto",
            "ditto",
            source,
            destination,
            (char *)NULL
        );
        _exit(127);
    }

    int status = 0;

    if (waitpid(pid, &status, 0) < 0)
        return 0;

    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

static int install_homebrew(const char *log) {
    char *argv[] = {
        "/bin/bash", "-c",
        "NONINTERACTIVE=1 /bin/bash -c "
        "\"$(/usr/bin/curl -fsSL "
        "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
        NULL
    };
    return run_direct("/bin/bash", argv, log);
}

static int find_python312(char *out, size_t n) {
    const char *c[] = {
        /* Python 3.12 — Apple Silicon Homebrew */
        "/opt/homebrew/opt/python@3.12/bin/python3.12",
        "/opt/homebrew/opt/python@3.12/libexec/bin/python3.12",
        "/opt/homebrew/Cellar/python@3.12/3.12.13/bin/python3.12",
        "/opt/homebrew/Cellar/python@3.12/3.12.13_1/bin/python3.12",
        "/opt/homebrew/bin/python3.12",
        /* Python 3.12 — Intel Homebrew */
        "/usr/local/opt/python@3.12/bin/python3.12",
        "/usr/local/bin/python3.12",
        /* Python 3.11 — Apple Silicon Homebrew */
        "/opt/homebrew/opt/python@3.11/bin/python3.11",
        "/opt/homebrew/bin/python3.11",
        /* Python 3.11 — Intel Homebrew */
        "/usr/local/opt/python@3.11/bin/python3.11",
        "/usr/local/bin/python3.11",
        /* Python 3.11 — macOS system / python.org installer */
        "/usr/bin/python3.11",
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11",
        /* Fallback python3 systeme */
        "/usr/bin/python3",
        "/usr/local/bin/python3",
        NULL
    };
    for (int i = 0; c[i]; i++) {
        if (path_exists(c[i])) {
            strncpy(out, c[i], n-1); out[n-1]='\0'; return 1;
        }
    }
    return 0;
}

static int find_brew(char *out, size_t n) {
    const char *c[] = {
        "/opt/homebrew/bin/brew",
        "/usr/local/bin/brew",
        NULL
    };
    for (int i = 0; c[i]; i++) {
        if (path_exists(c[i])) {
            strncpy(out, c[i], n-1); out[n-1]='\0'; return 1;
        }
    }
    return 0;
}

int main(int argc, char **argv) {

    /* 0. Auto-suppression quarantaine */
    {
        char exe_q[PATH_MAX]; uint32_t sz_q = sizeof(exe_q);
        if (_NSGetExecutablePath(exe_q, &sz_q) == 0) {
            char t1[PATH_MAX], t2[PATH_MAX], t3[PATH_MAX], app_q[PATH_MAX];
            strncpy(t1, exe_q,       PATH_MAX-1);
            strncpy(t2, dirname(t1), PATH_MAX-1);
            strncpy(t3, dirname(t2), PATH_MAX-1);
            strncpy(app_q, dirname(t3), PATH_MAX-1);
            char *xa[] = { "/usr/bin/xattr", "-cr", app_q, NULL };
            run_direct("/usr/bin/xattr", xa, "/dev/null");
        }
    }

    /* 1. Trouver ROOT_DIR */
    char exe[PATH_MAX]; uint32_t sz = sizeof(exe);
    if (_NSGetExecutablePath(exe, &sz) != 0) {
        dialog("Ortho4XP — Erreur",
            "Impossible de localiser le dossier Ortho4XP.", "caution");
        return 1;
    }
    char real[PATH_MAX];
    if (!realpath(exe, real)) strncpy(real, exe, PATH_MAX-1);

    char t1[PATH_MAX], t2[PATH_MAX], t3[PATH_MAX], root[PATH_MAX];
    strncpy(t1, real, PATH_MAX-1);
    t1[PATH_MAX-1] = '\0';
    strncpy(t2, dirname(t1), PATH_MAX-1);
    t2[PATH_MAX-1] = '\0';
    strncpy(t3, dirname(t2), PATH_MAX-1);
    t3[PATH_MAX-1] = '\0';

    char tmp[PATH_MAX];
    strncpy(tmp, dirname(t3), PATH_MAX-1);
    tmp[PATH_MAX-1] = '\0';
    strncpy(root, dirname(tmp), PATH_MAX-1);
    root[PATH_MAX-1] = '\0';

    /*
     * Lancement depuis le DMG :
     * le DMG est la SOURCE et ne doit jamais être modifié.
     * L'utilisateur choisit le disque/dossier parent.
     * Le programme crée ensuite ORTHO4XP_V3.
     */
    if (is_readonly_volume(root) || strstr(root, "/AppTranslocation/") != NULL) {
        char destination_parent[PATH_MAX];
        char destination_root[PATH_MAX];

        if (!choose_destination(destination_parent, sizeof(destination_parent))) {
            dialog("Ortho4XP — Installation annulée",
                   "Aucun emplacement de destination n'a été sélectionné.",
                   "caution");
            return 1;
        }

        size_t plen = strlen(destination_parent);
        while (plen > 1 && destination_parent[plen - 1] == '/')
            destination_parent[--plen] = '\0';

        if (snprintf(destination_root,
                     sizeof(destination_root),
                     "%s/ORTHO4XP_V3",
                     destination_parent) >= (int)sizeof(destination_root)) {
            dialog("Ortho4XP — Erreur",
                   "Le chemin de destination est trop long.",
                   "caution");
            return 1;
        }

        if (strcmp(destination_root, root) == 0) {
            dialog("Ortho4XP — Erreur",
                   "La destination ne peut pas être le DMG.",
                   "stop");
            return 1;
        }

        if (!dest_is_usable(destination_parent)) {
            dialog("Ortho4XP — Emplacement non compatible",
                   "Impossible d'installer ici.\\n\\n"
                   "Le disque doit etre au format Mac (APFS ou Mac OS etendu) "
                   "et autoriser l'ecriture. Un disque au format Windows "
                   "(exFAT/FAT) ne convient pas.\\n\\n"
                   "Relancez et choisissez un autre emplacement.",
                   "caution");
            return 1;
        }

        if (path_exists(destination_root)) {
            char msg[PATH_MAX + 256];
            snprintf(msg, sizeof(msg),
                     "Le dossier ORTHO4XP_V3 existe déjà ici :\n\n%s\n\n"
                     "Choisissez un autre emplacement.",
                     destination_root);
            dialog("Ortho4XP — Dossier déjà présent", msg, "caution");
            return 1;
        }

        /* Créer ORTHO4XP_V3 dans le dossier choisi.
         * mkdir -p rend la création robuste sur tous les chemins
         * accessibles à l'utilisateur.
         */
        char mkdir_cmd[PATH_MAX + 64];
        snprintf(mkdir_cmd, sizeof(mkdir_cmd),
                 "/bin/mkdir -p \"%s\"",
                 destination_root);

        if (system(mkdir_cmd) != 0 || !path_exists(destination_root)) {
            char msg[PATH_MAX + 256];
            snprintf(msg, sizeof(msg),
                     "Impossible de créer le dossier :\\n\\n%s",
                     destination_root);
            dialog("Ortho4XP — Erreur", msg, "stop");
            return 1;
        }

        /* Source : lanceur à la racine du DMG -> sous-dossier ORTHO4XP_V3 ;
         * lanceur ouvert DANS le dossier ORTHO4XP_V3 du DMG -> ce dossier. */
        char source_root[PATH_MAX];
        char probe_src[PATH_MAX];
        snprintf(probe_src, sizeof(probe_src), "%s/INSTALL_PREREQUIS.py", root);
        if (path_exists(probe_src)) {
            strncpy(source_root, root, PATH_MAX - 1);
            source_root[PATH_MAX - 1] = '\0';
        } else if (snprintf(source_root, sizeof(source_root), "%s/ORTHO4XP_V3", root) >= (int)sizeof(source_root)) {
            fprintf(stderr, "❌ Chemin source trop long.\n");
            rmdir(destination_root);
            return 1;
        }
        /* Dossier absent à côté du lanceur (translocation) -> chercher le DMG */
        {
            char probe_sub[PATH_MAX];
            snprintf(probe_sub, sizeof(probe_sub), "%s/INSTALL_PREREQUIS.py", source_root);
            if (!path_exists(probe_sub) &&
                !find_dmg_source_in_volumes(source_root, sizeof(source_root))) {
                rmdir(destination_root);
                dialog("Ortho4XP — DMG introuvable",
                       "Le dossier ORTHO4XP_V3 du DMG est introuvable.\\n\\n"
                       "Laissez le DMG ouvert (disque ORTHO4XP V3) "
                       "et relancez le lanceur.",
                       "caution");
                return 1;
            }
        }

        if (!copy_from_dmg(source_root, destination_root)) {
            char msg[PATH_MAX + 256];
            snprintf(msg, sizeof(msg),
                     "La copie depuis le DMG a échoué.\n\nDestination :\n%s",
                     destination_root);
            rmdir(destination_root);
            dialog("Ortho4XP — Erreur de copie", msg, "stop");
            return 1;
        }

        /* La copie ne doit pas garder l'étiquette « téléchargé d'internet »,
         * sinon macOS bloquerait à nouveau chaque élément copié. */
        {
            char *xq[] = { "/usr/bin/xattr", "-dr", "com.apple.quarantine",
                           destination_root, NULL };
            run_direct("/usr/bin/xattr", xq, "/dev/null");
        }

        strncpy(root, destination_root, PATH_MAX - 1);
        root[PATH_MAX - 1] = '\0';

        char installed_launcher[PATH_MAX];
        if (snprintf(installed_launcher, sizeof(installed_launcher), "%s/Lanceur_Installation_Prerequis.app/Contents/MacOS/launch", root) >= (int)sizeof(installed_launcher)) {
            dialog("Ortho4XP — Erreur", "Le chemin du lanceur installé est trop long.", "stop");
            return 1;
        }
        if (!path_exists(installed_launcher)) {
            dialog("Ortho4XP — Erreur", "Le Lanceur_Installation_Prerequis.app n'a pas été trouvé dans l'installation.", "stop");
            return 1;
        }
        char *launcher_args[] = { installed_launcher, NULL };
        execv(installed_launcher, launcher_args);
        dialog("Ortho4XP — Erreur", "Impossible de lancer le Lanceur_Installation_Prerequis installé.", "stop");
        return 1;
    } else {
        if (chdir(root) != 0) {
            dialog("Ortho4XP — Erreur",
                   "Impossible d'accéder au dossier ORTHO4XP_V3.",
                   "stop");
            return 1;
        }
    }

    char log[PATH_MAX], bootstrap[PATH_MAX], venv_py[PATH_MAX], venv_dir[PATH_MAX];
    snprintf(log,       sizeof(log),       "%s/ortho4xp_install.log", root);
    snprintf(bootstrap, sizeof(bootstrap), "%s/INSTALL_PREREQUIS.py",    root);
    snprintf(venv_py,   sizeof(venv_py),   "%s/venv/bin/python3",     root);
    snprintf(venv_dir,  sizeof(venv_dir),  "%s/venv",                 root);

    /* 2. Vérifier INSTALL_PREREQUIS.py */
    if (!path_exists(bootstrap)) {
        char msg[512];
        snprintf(msg, sizeof(msg),
            "INSTALL_PREREQUIS.py introuvable dans :\\n%s\\n\\n"
            "Verifiez que l'archive est bien decompressee.", root);
        dialog("Ortho4XP — Fichier manquant", msg, "stop");
        return 1;
    }

    /* 3. Chercher Python 3.12 */
    char py312[PATH_MAX] = {0};
    int has_py = find_python312(py312, sizeof(py312));

    /* Toujours passer par INSTALL_PREREQUIS.py — jamais directement le Launcher */
    /* INSTALL_PREREQUIS.py gère lui-même le cas "tout déjà OK" */

    /* 4. Python absent → installer Homebrew + Python */
    if (!has_py) {
        dialog("Ortho4XP V3.0 — Installation requise",
            "Python 3.12 n'est pas installe sur ce Mac.\\n\\n"
            "L'installation va demarrer automatiquement :\\n"
            "  - Homebrew\\n"
            "  - Python 3.12\\n\\n"
            "Duree estimee : 5 a 15 minutes.\\n"
            "Cliquez OK pour demarrer.", "note");

        char brew[PATH_MAX] = {0};
        if (!find_brew(brew, sizeof(brew))) {
            notify("Etape 1/3", "Installation de Homebrew...");
            install_homebrew(log);
            if (!find_brew(brew, sizeof(brew))) {
                dialog("Ortho4XP — Erreur Homebrew",
                    "Homebrew n'a pas pu etre installe.\\n\\n"
                    "Ouvrez Safari : https://brew.sh\\n"
                    "Puis relancez.", "stop");
                return 1;
            }
        }

        notify("Etape 2/3", "Installation de Python 3.12...");
        char *brew_args[] = { brew, "install", "python@3.12", "python-tk@3.12", NULL };
        run_direct(brew, brew_args, log);

        has_py = find_python312(py312, sizeof(py312));
        if (!has_py) {
            dialog("Ortho4XP — Erreur Python",
                "Python 3.12 n'a pas pu etre installe.\\n\\n"
                "Ouvrez le Terminal et tapez :\\n"
                "brew install python@3.12 python-tk@3.12", "stop");
            return 1;
        }
        notify("Etape 3/3", "Python 3.12 installe avec succes !");
    }

    /* 5. Créer venv si absent — appel direct sans bash */
    if (!path_exists(venv_dir)) {
        notify("Preparation", "Creation de l'environnement Python...");
        char *venv_args[] = { py312, "-m", "venv", venv_dir, NULL };
        run_direct(py312, venv_args, log);
    }

    /* 6. Lancer via script shell — évite que macOS ouvre l'Éditeur de Script */
    notify("Lancement", "Ouverture du Launcher Ortho4XP...");
    char sh_path[PATH_MAX];
    snprintf(sh_path, sizeof(sh_path), "%s/_ortho_launch.sh", root);
    FILE *sh = fopen(sh_path, "w");
    if (sh) {
        fprintf(sh, "#!/bin/sh\n");
        fprintf(sh, "exec \"%s\" \"%s\"\n", py312, bootstrap);
        fclose(sh);
        chmod(sh_path, 0755);
    }
    char *sh_args[] = { "/bin/sh", sh_path, NULL };
    run_direct("/bin/sh", sh_args, log);
    return 0;
}

"""

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>launch</string>
    <key>CFBundleIdentifier</key><string>com.ypsos.ortho4xp.prerequis</string>
    <key>CFBundleName</key><string>Lanceur Installation Prerequis</string>
    <key>CFBundleDisplayName</key><string>Lanceur Installation Prerequis</string>
    <key>CFBundleVersion</key><string>2.0</string>
    <key>CFBundleShortVersionString</key><string>2.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>NSRequiresAquaSystemAppearance</key><false/>
    <key>LSUIElement</key><false/>
</dict>
</plist>
"""

VBS_SCRIPT = r"""
' Lanceur_Installation_Prerequis.vbs — Ortho4XP V3.0
' Lance INSTALL_PREREQUIS.py sans console noire
' Installe Python 3.12 via winget si absent

Option Explicit

Dim WshShell, fso, scriptDir, bootstrap, python
Set WshShell = CreateObject("WScript.Shell")
Set fso      = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
bootstrap = scriptDir & "\INSTALL_PREREQUIS.py"

If Not fso.FileExists(bootstrap) Then
    MsgBox "INSTALL_PREREQUIS.py introuvable dans :" & vbCrLf & scriptDir & vbCrLf & vbCrLf & _
           "Vérifiez que l'archive est bien décompressée.", _
           vbCritical, "Ortho4XP — Fichier manquant"
    WScript.Quit
End If

python = ""
Dim pyPaths(5)
pyPaths(0) = "C:\Python312\python.exe"
pyPaths(1) = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\python.exe"
pyPaths(2) = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe"
pyPaths(3) = scriptDir & "\venv\Scripts\pythonw.exe"
pyPaths(4) = scriptDir & "\venv\Scripts\python.exe"
pyPaths(5) = "C:\Program Files\Python312\python.exe"

Dim i
For i = 0 To 5
    If fso.FileExists(pyPaths(i)) Then
        python = pyPaths(i)
        Exit For
    End If
Next

If python = "" Then
    Dim answer
    answer = MsgBox("Python 3.12 n'est pas installe." & vbCrLf & vbCrLf & _
        "L'installation va demarrer automatiquement." & vbCrLf & _
        "Duree estimee : 2 a 5 minutes." & vbCrLf & vbCrLf & _
        "Cliquez OK pour continuer.", _
        vbOKCancel + vbInformation, "Ortho4XP V3.0 — Installation Python")

    If answer <> vbOK Then WScript.Quit

    WshShell.Run "winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements", 1, True

    For i = 0 To 5
        If fso.FileExists(pyPaths(i)) Then
            python = pyPaths(i)
            Exit For
        End If
    Next

    If python = "" Then
        MsgBox "Installation automatique impossible." & vbCrLf & vbCrLf & _
            "La page de telechargement va s'ouvrir." & vbCrLf & _
            "Installez Python 3.12 puis relancez." & vbCrLf & vbCrLf & _
            "IMPORTANT : Cochez 'Add Python to PATH' !", _
            vbExclamation, "Ortho4XP — Python manquant"
        WshShell.Run "https://www.python.org/downloads/release/python-3120/"
        WScript.Quit
    End If

    MsgBox "Python 3.12 installe avec succes !", vbInformation, "Ortho4XP"
End If

Dim pyExe
pyExe = python
Dim pyW
pyW = Replace(python, "python.exe", "pythonw.exe")
If fso.FileExists(pyW) Then pyExe = pyW

WshShell.Run Chr(34) & pyExe & Chr(34) & " " & Chr(34) & bootstrap & Chr(34), 1, False
"""


def create_mac_app():
    """Crée Lanceur_Installation_Prerequis.app avec binaire C autonome.
    Sécurité : si le .app existe déjà, on ne le recrée PAS."""
    import shutil

    app_path  = HERE / "Lanceur_Installation_Prerequis.app"
    # Sécurité anti-écrasement
    if app_path.exists():
        print("  ♻️  Lanceur_Installation_Prerequis.app déjà présent — non réinstallé.")
        return app_path

    contents  = app_path / "Contents"
    macos_dir = contents / "MacOS"
    res_dir   = contents / "Resources"

    macos_dir.mkdir(parents=True)
    res_dir.mkdir(parents=True)

    (contents / "Info.plist").write_text(INFO_PLIST, encoding="utf-8")

    # Icône avec Pillow (non bloquant)
    try:
        from PIL import Image, ImageDraw
        iconset = res_dir / "AppIcon.iconset"
        iconset.mkdir(exist_ok=True)
        for s in [16, 32, 64, 128, 256, 512]:
            img = Image.new("RGBA", (s, s), (59, 91, 73, 255))
            d = ImageDraw.Draw(img)
            m = s // 8
            d.ellipse([m, m, s - m, s - m], fill=(42, 66, 53, 255))
            cx, cy, sz = s // 2, s // 2, s // 3
            d.polygon(
                [(cx, cy - sz), (cx + sz // 2, cy + sz // 2),
                 (cx, cy + sz // 4), (cx - sz // 2, cy + sz // 2)],
                fill=(166, 227, 161, 230)
            )
            img.save(iconset / f"icon_{s}x{s}.png")
            if s <= 256:
                img.resize((s * 2, s * 2), Image.LANCZOS).save(
                    iconset / f"icon_{s}x{s}@2x.png")
        r = subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(res_dir / "AppIcon.icns")],
            capture_output=True)
        if r.returncode == 0:
            print("  ✅ Icône .icns générée.")
        shutil.rmtree(str(iconset))
    except Exception as e:
        print(f"  ℹ️  Icône non générée ({e}) — non bloquant.")

    # Compilation binaire C
    c_file  = HERE / "_launcher_tmp.c"
    exe_out = macos_dir / "launch"
    c_file.write_text(LAUNCHER_C_SOURCE, encoding="utf-8")

    print("  🔨 Compilation du binaire C...")
    compiled = False
    for arch_flags in [["-arch", "arm64", "-arch", "x86_64"], []]:
        cmd = ["gcc"] + arch_flags + [
            str(c_file), "-o", str(exe_out),
            "-framework", "Foundation", "-O2"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            label = "universel arm64+x86_64" if arch_flags else "natif"
            print(f"  ✅ Binaire compilé ({label}).")
            compiled = True
            break
        else:
            print(f"  ⚠️  {arch_flags or 'natif'}: {r.stderr.strip()[:100]}")

    c_file.unlink(missing_ok=True)

    if not compiled:
        print("  ⚠️  gcc indisponible — fallback shell script.")
        _create_shell_fallback(exe_out)
    else:
        exe_out.chmod(exe_out.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Supprimer quarantaine + signer
    try:
        subprocess.run(["xattr", "-cr", str(app_path)], capture_output=True, timeout=10)
        print("  ✅ Quarantaine supprimée.")
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
            capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print("  ✅ Signature ad-hoc appliquée.")
    except Exception:
        pass

    print(f"\n  ✅ App créée : {app_path.name}")
    print("  Si macOS bloque : clic droit → Ouvrir → Ouvrir quand même")
    return app_path


def _create_shell_fallback(exe_out: Path):
    """Shell script fallback si gcc absent — même logique que le binaire C."""
    script = r"""#!/bin/bash
MACOS_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENTS_DIR="$(dirname "$MACOS_DIR")"
APP_DIR="$(dirname "$CONTENTS_DIR")"
ROOT_DIR="$(dirname "$APP_DIR")"
cd "$ROOT_DIR" || exit 1

LOG="$ROOT_DIR/ortho4xp_install.log"
BOOTSTRAP="$ROOT_DIR/INSTALL_PREREQUIS.py"
VENV_PY="$ROOT_DIR/venv/bin/python3"

echo "=== $(date) ===" >> "$LOG"

[ ! -f "$BOOTSTRAP" ] && {
    osascript -e "display dialog \"INSTALL_PREREQUIS.py introuvable dans :\n$ROOT_DIR\" buttons {\"OK\"} default button \"OK\" with title \"Ortho4XP — Fichier manquant\" with icon stop"
    exit 1
}

find_py312() {
    for p in /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 \
              /opt/homebrew/opt/python@3.12/bin/python3.12; do
        [ -f "$p" ] && echo "$p" && return 0
    done; return 1
}

PY312=$(find_py312)

[ -n "$PY312" ] && [ -f "$VENV_PY" ] && {
    PYTHONPATH="$ROOT_DIR/src" "$VENV_PY" "$BOOTSTRAP" &; exit 0
}

if [ -z "$PY312" ]; then
    osascript -e 'display dialog "Python 3.12 nest pas installé.\n\nInstallation automatique :\n• Homebrew\n• Python 3.12\n\n⏱ 5-15 minutes.\nCliquez OK." buttons {"OK"} default button "OK" with title "Ortho4XP V3.0" with icon note'

    BREW=/opt/homebrew/bin/brew
    [ ! -f "$BREW" ] && BREW=/usr/local/bin/brew
    [ ! -f "$BREW" ] && {
        osascript -e 'display notification "Installation Homebrew..." with title "Étape 1/3" subtitle "Ortho4XP V3.0"'
        NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >> "$LOG" 2>&1
        BREW=/opt/homebrew/bin/brew
        [ ! -f "$BREW" ] && BREW=/usr/local/bin/brew
    }
    [ ! -f "$BREW" ] && {
        osascript -e 'display dialog "Impossible dinstaller Homebrew.\nhttps://brew.sh" buttons {"OK"} default button "OK" with title "Erreur" with icon stop'
        exit 1
    }

    osascript -e 'display notification "Installation Python 3.12..." with title "Étape 2/3" subtitle "Ortho4XP V3.0"'
    "$BREW" install python@3.12 python-tk@3.12 >> "$LOG" 2>&1
    PY312=$(find_py312)
    [ -z "$PY312" ] && {
        osascript -e 'display dialog "Python 3.12 na pas pu être installé.\nbrew install python@3.12 python-tk@3.12" buttons {"OK"} default button "OK" with title "Erreur" with icon stop'
        exit 1
    }
    osascript -e 'display notification "Python 3.12 installé ✓" with title "✅ Étape 3/3" subtitle "Ortho4XP V3.0"'
fi

[ ! -f "$VENV_PY" ] && {
    osascript -e 'display notification "Création environnement Python..." with title "Préparation" subtitle "Ortho4XP V3.0"'
    "$PY312" -m venv "$ROOT_DIR/venv" >> "$LOG" 2>&1
}

PY_USE="$VENV_PY"; [ ! -f "$PY_USE" ] && PY_USE="$PY312"
osascript -e 'display notification "Ouverture du Launcher..." with title "Lancement" subtitle "Ortho4XP V3.0"'
PYTHONPATH="$ROOT_DIR/src" "$PY_USE" "$BOOTSTRAP" &
"""
    exe_out.write_text(script, encoding="utf-8")
    exe_out.chmod(exe_out.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print("  ✅ Shell script fallback créé.")


def create_windows_launcher():
    vbs_path = HERE / "Lanceur_Installation_Prerequis.vbs"
    # Sécurité anti-écrasement
    if vbs_path.exists():
        print("  ♻️  Lanceur_Installation_Prerequis.vbs déjà présent — non réinstallé.")
        return vbs_path
    vbs_path.write_text(VBS_SCRIPT, encoding="utf-8")
    print(f"  ✅ VBS créé : {vbs_path.name}")
    try:
        desktop  = Path(os.environ.get("USERPROFILE", "~")).expanduser() / "Desktop"
        shortcut = desktop / "Lanceur Installation Prerequis.lnk"
        ps = (f'$ws=$c=$ws.CreateShortcut("{shortcut}");'
              f'$c.TargetPath="{vbs_path}";'
              f'$c.WorkingDirectory="{HERE}";$c.Save()')
        subprocess.run(["powershell", "-Command",
                        f'$ws=New-Object -ComObject WScript.Shell;'
                        f'$sc=$ws.CreateShortcut("{shortcut}");'
                        f'$sc.TargetPath="{vbs_path}";'
                        f'$sc.WorkingDirectory="{HERE}";'
                        f'$sc.Description="Ortho4XP V3.0";$sc.Save()'],
                       capture_output=True, timeout=15)
        print("  ✅ Raccourci Bureau créé.")
    except Exception as e:
        print(f"  ℹ️  Raccourci Bureau : {e}")
    return vbs_path


def create_linux_launcher():
    import shutil
    sh_path = HERE / "Lanceur_Installation_Prerequis.sh"
    desktop_path = HERE / "Lanceur_Installation_Prerequis.desktop"
    # Sécurité anti-écrasement
    if sh_path.exists() and desktop_path.exists():
        print("  ♻️  Lanceur_Installation_Prerequis déjà présent — non réinstallé.")
        return desktop_path
    if not sh_path.exists():
        sh_path.write_text(
            f"""#!/bin/bash
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOOTSTRAP="$ROOT_DIR/INSTALL_PREREQUIS.py"
PYTHON=$(which python3.12 2>/dev/null || which python3 2>/dev/null)
if [ -z "$PYTHON" ]; then
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3.12 python3-tk python3-pip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python tk
    fi
    PYTHON=$(which python3.12 2>/dev/null || which python3)
fi
cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR/src" "$PYTHON" "$BOOTSTRAP" &
""", encoding="utf-8")
        sh_path.chmod(sh_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    if not desktop_path.exists():
        desktop_path.write_text(
            f"[Desktop Entry]\nVersion=2.0\nName=Lanceur Installation Prerequis\n"
            f"Comment=Installation Ortho4XP V3.0\nExec={sh_path}\nPath={HERE}\n"
            f"Terminal=false\nType=Application\nCategories=Utility;\nStartupNotify=true\n",
            encoding="utf-8")
        desktop_path.chmod(
            desktop_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    try:
        apps = Path.home() / ".local" / "share" / "applications"
        apps.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(desktop_path), str(apps / "Lanceur_Installation_Prerequis.desktop"))
        print(f"  ✅ .desktop copié dans {apps}")
    except Exception:
        pass
    print(f"  ✅ .sh + .desktop créés.")
    return desktop_path


def main():
    print("=" * 58)
    print("  Ortho4XP V3.0 — Création du lanceur natif")
    print(f"  Plateforme : {SYSTEM} | Dossier : {HERE}")
    print("=" * 58)

    if not (HERE / "INSTALL_PREREQUIS.py").exists():
        print("❌ INSTALL_PREREQUIS.py introuvable — archive incomplète.")
        sys.exit(1)

    if SYSTEM == "Darwin":
        create_mac_app()
    elif SYSTEM == "Windows":
        create_windows_launcher()
    elif SYSTEM == "Linux":
        create_linux_launcher()
    else:
        print(f"⚠️  Plateforme non supportée : {SYSTEM}")
        sys.exit(1)

    print()
    print("✅ Lanceur créé. Double-clic sur :")
    if SYSTEM == "Darwin":    print("   Lanceur_Installation_Prerequis.app")
    elif SYSTEM == "Windows": print("   Lanceur_Installation_Prerequis.vbs")
    elif SYSTEM == "Linux":   print("   Lanceur_Installation_Prerequis.desktop")


if __name__ == "__main__":
    main()
