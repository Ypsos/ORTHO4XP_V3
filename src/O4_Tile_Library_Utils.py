# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# O4_Tile_Library_Utils.py
# Bibliotheque de tuiles (CDC V3.6, Priorite 2).
# Auteur : Roland (Ypsos) - GPLv3
#
# Un seul module, bilingue (_L interne), 100 % ADDITIF, appele depuis le
# Menu Avance via run_tile_library(parent).
#
# Fonctions offertes :
#   - LISTER les tuiles Ortho4XP (zOrtho4XP_...) et leur etat (active/desactivee),
#     lues dans scenery_packs.ini de X-Plane (lecture seule).
#   - ACTIVER / DESACTIVER une tuile dans X-Plane : on change uniquement
#     SCENERY_PACK <-> SCENERY_PACK_DISABLED sur SA ligne, sans toucher au
#     reste ni a l'ordre. Reversible, instantane, aucun Go deplace.
#   - SUPPRIMER une tuile : symlink -> on retire LE LIEN seulement (jamais les
#     donnees pointees) ; vrai dossier -> suppression du dossier. Confirmation
#     obligatoire, jamais en bloc silencieux. La ligne est retiree du .ini.
#   - VIDER LE CACHE d'une tuile : dossiers OSM_data / Masks / Patches propres a
#     cette tuile (via O4_File_Names, aucun chemin en dur). Confirmation.
#
# Securite :
#   - AUCUN chemin code en dur. On lit ce qui est ecrit dans scenery_packs.ini
#     et on utilise O4_File_Names pour les dossiers de cache.
#   - Toute ecriture de scenery_packs.ini fait d'abord une sauvegarde .bak.
#   - On ne suit JAMAIS un symlink pour supprimer des donnees.
#   - Aucun fichier moteur (mer/mesh/masques/DSF) touche.
#
# Le chemin du scenery_packs.ini est memorise dans un petit fichier prive
# (.tile_library_ini a la racine Ortho4XP) -> on ne touche pas a Ortho4XP.cfg
# ni a cfg_vars.
# ------------------------------------------------------------------------------

import os
import re
import shutil

_KW_ON = "SCENERY_PACK"
_KW_OFF = "SCENERY_PACK_DISABLED"
_ORTHO_MARK = "zOrtho4XP_"
_LATLON_RE = re.compile(r"zOrtho4XP_([+-]\d{2})([+-]\d{3})")


# ------------------------------------------------------------------------------
# Bilingue interne (ne touche pas aux fichiers O4_Lang_*)
# ------------------------------------------------------------------------------
def _lang_code():
    for modname, attr in (("O4_Lang", "_current_lang"),
                          ("O4_UI_Utils", "lang")):
        try:
            mod = __import__(modname)
            code = getattr(mod, attr, None)
            if isinstance(code, str) and code:
                return code[:2].lower()
        except Exception:
            pass
    return "en"


def _L(fr, en):
    return fr if _lang_code() == "fr" else en


# ------------------------------------------------------------------------------
# CHAPITRE 1 - coeur PUR (testable en headless)
# ------------------------------------------------------------------------------
def parse_scenery_packs(text):
    """PUR. Liste les entrees SCENERY_PACK : {index, enabled, path, is_ortho}."""
    entries = []
    for i, raw in enumerate(text.splitlines()):
        s = raw.strip()
        if not s:
            continue
        if s.startswith(_KW_OFF):
            path = s[len(_KW_OFF):].strip()
            enabled = False
        elif s.startswith(_KW_ON):
            path = s[len(_KW_ON):].strip()
            enabled = True
        else:
            continue
        entries.append({
            "index": i,
            "enabled": enabled,
            "path": path,
            "is_ortho": _ORTHO_MARK in path,
        })
    return entries


def list_ortho_tiles(text):
    """PUR. Seulement les tuiles Ortho4XP, dans l'ordre du fichier."""
    return [e for e in parse_scenery_packs(text) if e["is_ortho"]]


def set_tile_enabled(text, path, enabled):
    """
    PUR. (nouveau_texte, change?). Met la ligne de chemin == path a l'etat
    voulu. Matching STRICT du chemin (/ final, espaces, suffixes conserves).
    Ne change QUE le mot-cle de cette ligne ; preserve tout le reste.
    """
    lines = text.splitlines(keepends=True)
    changed = False
    for k, raw in enumerate(lines):
        nl = ""
        body = raw
        for end in ("\r\n", "\n", "\r"):
            if raw.endswith(end):
                nl = end
                body = raw[: -len(end)]
                break
        s = body.strip()
        cur = None
        if s.startswith(_KW_OFF):
            cur = s[len(_KW_OFF):].strip()
        elif s.startswith(_KW_ON):
            cur = s[len(_KW_ON):].strip()
        if cur is None or cur != path:
            continue
        kw = _KW_ON if enabled else _KW_OFF
        newbody = kw + " " + cur
        if newbody != body:
            lines[k] = newbody + nl
            changed = True
        break
    return ("".join(lines), changed)


def remove_tile_line(text, path):
    """PUR. (nouveau_texte, retiree?). Retire la ligne SCENERY_PACK[_DISABLED]
    dont le chemin == path (matching strict). Les autres lignes sont intactes."""
    lines = text.splitlines(keepends=True)
    out = []
    removed = False
    for raw in lines:
        body = raw
        for end in ("\r\n", "\n", "\r"):
            if raw.endswith(end):
                body = raw[: -len(end)]
                break
        s = body.strip()
        cur = None
        if s.startswith(_KW_OFF):
            cur = s[len(_KW_OFF):].strip()
        elif s.startswith(_KW_ON):
            cur = s[len(_KW_ON):].strip()
        if (not removed) and cur is not None and cur == path:
            removed = True
            continue  # on saute cette ligne
        out.append(raw)
    return ("".join(out), removed)


def tile_latlon_from_path(pack_path):
    """PUR. (lat, lon) entiers depuis un chemin/paquet zOrtho4XP_+46-003...,
    ou None si non reconnu. Gere les noms longs et ' symlink'."""
    m = _LATLON_RE.search(pack_path)
    if not m:
        return None
    try:
        return (int(m.group(1)), int(m.group(2)))
    except Exception:
        return None


# ------------------------------------------------------------------------------
# Acces disque
# ------------------------------------------------------------------------------
def read_scenery_file(ini_path):
    with open(ini_path, "r", encoding="utf-8") as f:
        return f.read()


def _write_with_bak(ini_path, new_text):
    shutil.copy2(ini_path, ini_path + ".bak")
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write(new_text)


def toggle_tile_in_file(ini_path, path, enabled):
    """PRODUCTION. (ok, message). Sauvegarde .bak avant toute ecriture."""
    if not os.path.isfile(ini_path):
        return (False, _L("scenery_packs.ini introuvable",
                          "scenery_packs.ini not found"))
    text = read_scenery_file(ini_path)
    new_text, changed = set_tile_enabled(text, path, enabled)
    if not changed:
        return (True, _L("deja dans l'etat demande", "already in that state"))
    _write_with_bak(ini_path, new_text)
    return (True, "ok")


def remove_tile_from_file(ini_path, path):
    """PRODUCTION. Retire la ligne de la tuile du .ini (sauvegarde .bak)."""
    if not os.path.isfile(ini_path):
        return (False, _L("scenery_packs.ini introuvable",
                          "scenery_packs.ini not found"))
    text = read_scenery_file(ini_path)
    new_text, removed = remove_tile_line(text, path)
    if not removed:
        return (True, _L("ligne absente", "line absent"))
    _write_with_bak(ini_path, new_text)
    return (True, "ok")


def xplane_root_from_ini(ini_path):
    """Racine X-Plane = parent du dossier 'Custom Scenery' qui contient le .ini."""
    custom_scenery = os.path.dirname(os.path.abspath(ini_path))
    return os.path.dirname(custom_scenery)


def tile_abspath(ini_path, pack_path):
    """Chemin absolu du dossier/paquet a partir de son chemin relatif .ini."""
    root = xplane_root_from_ini(ini_path)
    rel = pack_path.rstrip("/")
    return os.path.join(root, rel)


def delete_tile_folder(ini_path, pack_path):
    """
    PRODUCTION. Supprime le dossier de la tuile de facon symlink-safe :
      - lien symbolique  -> on retire LE LIEN uniquement (os.unlink),
                            jamais les donnees pointees.
      - vrai dossier     -> shutil.rmtree.
    Retourne (ok, message). N'ecrit pas dans le .ini (fait a part).
    """
    target = tile_abspath(ini_path, pack_path)
    try:
        if os.path.islink(target):
            os.unlink(target)  # retire le lien seulement
            return (True, _L("lien retire (donnees intactes)",
                             "link removed (data untouched)"))
        if os.path.isdir(target):
            shutil.rmtree(target)
            return (True, _L("dossier supprime", "folder deleted"))
        return (True, _L("rien a supprimer (deja absent)",
                         "nothing to delete (already gone)"))
    except Exception as e:
        return (False, str(e))


def tile_cache_dirs(lat, lon):
    """
    Dossiers de cache PROPRES a une tuile, via O4_File_Names (aucun chemin en
    dur). Retourne une liste de (libelle, chemin_absolu) existants seulement.
    On reste conservateur : OSM_data / Masks / Patches (pas les Orthophotos
    partagees). Si O4_File_Names est absent, retourne [].
    """
    dirs = []
    try:
        import O4_File_Names as FNAMES
        cand = [
            ("OSM_data", FNAMES.osm_dir(lat, lon)),
            ("Masks", FNAMES.mask_dir(lat, lon)),
            ("Patches", FNAMES.patch_dir(lat, lon)),
        ]
        for label, d in cand:
            if d and os.path.isdir(d):
                dirs.append((label, d))
    except Exception:
        pass
    return dirs


def clear_tile_cache(lat, lon):
    """PRODUCTION. Supprime les dossiers de cache de la tuile. (ok, details)."""
    done = []
    for label, d in tile_cache_dirs(lat, lon):
        try:
            shutil.rmtree(d)
            done.append(label)
        except Exception as e:
            return (False, "%s: %s" % (label, e))
    return (True, done)


# ------------------------------------------------------------------------------
# Memorisation du chemin scenery_packs.ini (fichier prive, pas Ortho4XP.cfg)
# ------------------------------------------------------------------------------
def _remember_path_file():
    try:
        import O4_File_Names as FNAMES
        root = FNAMES.Ortho4XP_dir
    except Exception:
        root = os.path.expanduser("~")
    return os.path.join(root, ".tile_library_ini")


def load_saved_ini_path():
    try:
        p = _remember_path_file()
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                cand = f.read().strip()
            if cand and os.path.isfile(cand):
                return cand
    except Exception:
        pass
    return ""


def save_ini_path(ini_path):
    try:
        with open(_remember_path_file(), "w", encoding="utf-8") as f:
            f.write(ini_path.strip())
        return True
    except Exception:
        return False


def guess_ini_path():
    """Tente de deviner scenery_packs.ini SANS rien coder en dur :
    1) chemin memorise ; 2) via custom_build_dir (config) s'il pointe dans un
    'Custom Scenery'. Sinon "" -> l'utilisateur choisira dans la fenetre."""
    saved = load_saved_ini_path()
    if saved:
        return saved
    try:
        import O4_Config_Utils as CFG
        cbd = getattr(CFG, "custom_build_dir", "") or ""
        if cbd:
            parts = os.path.abspath(cbd).split(os.sep)
            if "Custom Scenery" in parts:
                idx = len(parts) - 1 - parts[::-1].index("Custom Scenery")
                cs = os.sep.join(parts[: idx + 1])
                cand = os.path.join(cs, "scenery_packs.ini")
                if os.path.isfile(cand):
                    return cand
    except Exception:
        pass
    return ""


# ------------------------------------------------------------------------------
# CHAPITRE 3 - Fenetre (Menu Avance). Point d'entree : run_tile_library(parent)
# Import tkinter LOCAL (la fenetre s'ouvre meme si un module optionnel manque).
# ------------------------------------------------------------------------------
def run_tile_library(parent=None):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    # Couleurs depuis le theme (memes cles + memes defauts que le Menu Avance
    # et les autres fenetres du projet). apply_to_root habille les widgets
    # standards ; le theme ne gere PAS Listbox -> on la colore a la main
    # (cf. Bible O4_Theme_Manager).
    _TM = None
    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
    except Exception:
        _t = {}

    def _c(key, fallback):
        try:
            return _t.get(key, fallback)
        except Exception:
            return fallback

    BG = _c("bg", "#3b5b49")
    FG = _c("fg", "#e8f0ec")
    FG2 = _c("fg_secondary", "#a6e3a1")
    BTN_BG = _c("btn_bg", "#4a6b59")
    BTN_FG = _c("btn_fg", "#ffffff")
    HOVER = _c("accent", "#5a7b69")
    BORDER = _c("border", BTN_BG)
    SEL_BG = _c("btn_active", HOVER)
    LIST_BG = _c("canvas_bg", BG)
    FONT = ("Helvetica", 12) if ("dar" in __import__("sys").platform) \
        else ("Segoe UI", 10)

    state = {"ini": guess_ini_path(), "rows_on": [], "rows_off": []}

    root_ref = None
    try:
        root_ref = tk._default_root
    except Exception:
        pass
    win = tk.Toplevel(root_ref) if root_ref else tk.Tk()
    win.title(_L("Bibliotheque de tuiles - Ortho4XP V3",
                 "Tile library - Ortho4XP V3"))
    win.configure(bg=BG)
    # Applique le theme aux widgets standards (defensif). La Listbox n'est pas
    # geree par apply_to_root -> couleurs posees a la main plus bas.
    if _TM is not None:
        try:
            _TM.apply_to_root(win)
        except Exception:
            pass
    win.lift()
    try:
        win.focus_force()
    except Exception:
        pass

    # Boutons Mac-safe : sous macOS (Aqua), tk.Button ignore bg/fg -> texte
    # illisible. On utilise CustomTkinter si present (comme toute l'interface
    # Ortho4XP V3), sinon un repli Frame+Label colore (patron valide du projet).
    try:
        import customtkinter as _ctk
        _HAS_CTK = True
    except Exception:
        _HAS_CTK = False

    def _lighten(hexcol, factor):
        try:
            h = hexcol.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
            return "#%02x%02x%02x" % (r, g, b)
        except Exception:
            return hexcol

    def _btn(parent_w, text, cmd):
        if _HAS_CTK:
            b = _ctk.CTkButton(
                parent_w, text=text, command=cmd,
                corner_radius=8, border_width=1, height=32,
                fg_color=BTN_BG, hover_color=HOVER,
                border_color=BORDER, text_color=BTN_FG)
            # Correctif macOS : redessin apres mise en page.
            b.after_idle(
                lambda w=b, c=BTN_BG: w.winfo_exists() and w.configure(fg_color=c))
            return b
        frame = tk.Frame(parent_w, bg=BTN_BG, highlightthickness=1,
                         highlightbackground=BORDER, bd=0)
        lbl = tk.Label(frame, text=text, bg=BTN_BG, fg=BTN_FG, padx=10, pady=6,
                       font=FONT, cursor="hand2")
        lbl.pack(fill="both", expand=True)

        def _enter(e=None):
            frame.configure(bg=HOVER); lbl.configure(bg=HOVER)

        def _leave(e=None):
            frame.configure(bg=BTN_BG); lbl.configure(bg=BTN_BG)

        def _release(e=None):
            _leave()
            if callable(cmd):
                cmd()

        for w in (frame, lbl):
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<ButtonRelease-1>", _release)
        return frame

    # --- ligne du haut : fichier .ini ---
    top = tk.Frame(win, bg=BG)
    top.pack(fill=tk.X, padx=10, pady=(10, 4))
    ini_var = tk.StringVar(value=state["ini"] or _L("(non defini)", "(not set)"))
    tk.Label(top, text=_L("Fichier X-Plane :", "X-Plane file:"),
             bg=BG, fg=FG, font=FONT).pack(side=tk.LEFT)
    tk.Label(top, textvariable=ini_var, bg=BG, fg=FG, font=("TkFixedFont", 10),
             anchor="w", wraplength=560, justify="left").pack(
             side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

    # --- filtre ---
    filt = tk.Frame(win, bg=BG)
    filt.pack(fill=tk.X, padx=10, pady=(0, 4))
    tk.Label(filt, text=_L("Filtrer :", "Filter:"), bg=BG, fg=FG,
             font=FONT).pack(side=tk.LEFT)
    filter_var = tk.StringVar(value="")
    tk.Entry(filt, textvariable=filter_var, bg="#05330f", fg=FG,
             insertbackground=FG, font=FONT, width=24).pack(
             side=tk.LEFT, padx=(6, 0))

    # --- 2 listes cote a cote : ACTIVEES (gauche) et DESACTIVEES (droite) ---
    # Deux rubriques VISIBLES en meme temps : on voit d'un coup d'oeil lesquelles
    # sont actives et lesquelles reactiver, sans defiler sous les autres. On
    # selectionne une tuile dans une liste, l'autre liste se deselectionne pour
    # que le bouton agisse sans ambiguite. height basse (retour forum petit
    # ecran) : le nombre de lignes visibles suit la taille reelle (expand=True).
    mid = tk.Frame(win, bg=BG)
    mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
    mid.grid_columnconfigure(0, weight=1, uniform="cols")
    mid.grid_columnconfigure(1, weight=1, uniform="cols")
    mid.grid_rowconfigure(1, weight=1)

    hdr_on = tk.StringVar(value=_L("ACTIVEES", "ENABLED"))
    hdr_off = tk.StringVar(value=_L("DESACTIVEES", "DISABLED"))
    tk.Label(mid, textvariable=hdr_on, bg=BG, fg=FG2, font=FONT,
             anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4))
    tk.Label(mid, textvariable=hdr_off, bg=BG, fg=FG2, font=FONT,
             anchor="w").grid(row=0, column=1, sticky="w", padx=(4, 0))

    left = tk.Frame(mid, bg=BG)
    left.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
    sb_on = tk.Scrollbar(left)
    sb_on.pack(side=tk.RIGHT, fill=tk.Y)
    lb_on = tk.Listbox(left, bg="#05140a", fg=FG, selectbackground=SEL_BG,
                       selectforeground=FG, font=FONT, height=8,
                       yscrollcommand=sb_on.set, activestyle="none",
                       exportselection=False)
    lb_on.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb_on.config(command=lb_on.yview)

    right = tk.Frame(mid, bg=BG)
    right.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
    sb_off = tk.Scrollbar(right)
    sb_off.pack(side=tk.RIGHT, fill=tk.Y)
    lb_off = tk.Listbox(right, bg="#05140a", fg=FG, selectbackground=SEL_BG,
                        selectforeground=FG, font=FONT, height=8,
                        yscrollcommand=sb_off.set, activestyle="none",
                        exportselection=False)
    lb_off.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb_off.config(command=lb_off.yview)

    # Selection exclusive : cliquer dans une liste vide la selection de l'autre.
    lb_on.bind("<<ListboxSelect>>",
               lambda e: lb_off.selection_clear(0, tk.END))
    lb_off.bind("<<ListboxSelect>>",
                lambda e: lb_on.selection_clear(0, tk.END))

    status = tk.Label(win, text="", bg=BG, fg=FG, font=("TkFixedFont", 10),
                      anchor="w")
    status.pack(fill=tk.X, padx=10, pady=(2, 0))

    def _set_status(msg):
        status.config(text=msg)

    def _refresh():
        # Remplit les DEUX listes : actives a gauche, desactivees a droite.
        # Les numeros de tuiles sont conserves. Chaque liste a son propre
        # tableau parallele (rows_on / rows_off) pour retrouver la tuile
        # selectionnee.
        lb_on.delete(0, tk.END)
        lb_off.delete(0, tk.END)
        state["rows_on"] = []
        state["rows_off"] = []
        ini = state["ini"]
        if not ini or not os.path.isfile(ini):
            hdr_on.set(_L("ACTIVEES", "ENABLED"))
            hdr_off.set(_L("DESACTIVEES", "DISABLED"))
            _set_status(_L("Choisis d'abord le fichier scenery_packs.ini.",
                           "Please choose scenery_packs.ini first."))
            return
        try:
            text = read_scenery_file(ini)
        except Exception as e:
            _set_status(_L("Lecture impossible : ", "Cannot read: ") + str(e))
            return
        tiles = list_ortho_tiles(text)
        flt = filter_var.get().strip().lower()
        n_on = 0
        n_off = 0
        for tinfo in tiles:
            name = tinfo["path"].rstrip("/").split("/")[-1]
            if flt and flt not in name.lower():
                continue
            if tinfo["enabled"]:
                lb_on.insert(tk.END, " " + name)
                state["rows_on"].append(tinfo)
                n_on += 1
            else:
                lb_off.insert(tk.END, " " + name)
                state["rows_off"].append(tinfo)
                n_off += 1

        hdr_on.set(_L("ACTIVEES (%d)", "ENABLED (%d)") % n_on)
        hdr_off.set(_L("DESACTIVEES (%d)", "DISABLED (%d)") % n_off)
        _set_status(_L("%d activee(s) / %d desactivee(s).",
                       "%d enabled / %d disabled.") % (n_on, n_off))

    def _selected():
        sel = lb_on.curselection()
        if sel:
            return state["rows_on"][sel[0]]
        sel = lb_off.curselection()
        if sel:
            return state["rows_off"][sel[0]]
        messagebox.showinfo(win.title(),
                            _L("Selectionne une tuile dans une des deux listes.",
                               "Select a tile in one of the two lists."))
        return None

    def _choose_ini():
        p = filedialog.askopenfilename(
            parent=win,
            title=_L("Choisir scenery_packs.ini",
                     "Choose scenery_packs.ini"),
            filetypes=[("scenery_packs.ini", "scenery_packs.ini"),
                       (_L("Tous les fichiers", "All files"), "*")])
        if p:
            state["ini"] = p
            ini_var.set(p)
            save_ini_path(p)
            _refresh()

    def _enable(flag):
        t = _selected()
        if not t:
            return
        ok, msg = toggle_tile_in_file(state["ini"], t["path"], flag)
        if not ok:
            messagebox.showerror(win.title(), msg)
        _refresh()
        _set_status((_L("Activee : ", "Enabled: ") if flag
                     else _L("Desactivee : ", "Disabled: ")) + t["path"])

    def _delete_tile():
        t = _selected()
        if not t:
            return
        target = tile_abspath(state["ini"], t["path"])
        is_link = os.path.islink(target)
        if is_link:
            q = _L("Retirer le LIEN de cette tuile ? Les donnees pointees NE "
                   "seront PAS supprimees.\n\n",
                   "Remove this tile's LINK? The pointed data will NOT be "
                   "deleted.\n\n") + t["path"]
        else:
            q = _L("SUPPRIMER definitivement le dossier de cette tuile ?\n\n",
                   "PERMANENTLY delete this tile's folder?\n\n") + target
        if not messagebox.askyesno(win.title(), q):
            return
        ok, msg = delete_tile_folder(state["ini"], t["path"])
        if not ok:
            messagebox.showerror(win.title(), msg)
            return
        remove_tile_from_file(state["ini"], t["path"])
        _refresh()
        _set_status(_L("Supprimee : ", "Deleted: ") + msg)

    def _clear_cache():
        t = _selected()
        if not t:
            return
        ll = tile_latlon_from_path(t["path"])
        if not ll:
            messagebox.showinfo(win.title(),
                                _L("Coordonnees non reconnues pour cette tuile.",
                                   "Could not read this tile's coordinates."))
            return
        (lat, lon) = ll
        dirs = tile_cache_dirs(lat, lon)
        if not dirs:
            _set_status(_L("Aucun cache a vider pour cette tuile.",
                           "No cache to clear for this tile."))
            return
        liste = "\n".join("  - %s : %s" % (lbl, d) for lbl, d in dirs)
        q = _L("Vider le cache de cette tuile ? Dossiers supprimes :\n\n",
               "Clear this tile's cache? Folders to delete:\n\n") + liste
        if not messagebox.askyesno(win.title(), q):
            return
        ok, res = clear_tile_cache(lat, lon)
        if not ok:
            messagebox.showerror(win.title(), str(res))
            return
        _refresh()
        _set_status(_L("Cache vide : ", "Cache cleared: ") + ", ".join(res)
                    if res else _L("Rien a vider.", "Nothing to clear."))

    # --- boutons bas ---
    bot = tk.Frame(win, bg=BG)
    bot.pack(fill=tk.X, padx=10, pady=(4, 10))
    _btn(bot, _L("Choisir scenery_packs.ini", "Choose scenery_packs.ini"),
         _choose_ini).grid(row=0, column=0, padx=4, pady=3, sticky="ew")
    _btn(bot, _L("Rafraichir", "Refresh"),
         _refresh).grid(row=0, column=1, padx=4, pady=3, sticky="ew")
    _btn(bot, _L("Activer", "Enable"),
         lambda: _enable(True)).grid(row=1, column=0, padx=4, pady=3, sticky="ew")
    _btn(bot, _L("Desactiver", "Disable"),
         lambda: _enable(False)).grid(row=1, column=1, padx=4, pady=3, sticky="ew")
    _btn(bot, _L("Supprimer la tuile", "Delete tile"),
         _delete_tile).grid(row=2, column=0, padx=4, pady=3, sticky="ew")
    _btn(bot, _L("Vider le cache", "Clear cache"),
         _clear_cache).grid(row=2, column=1, padx=4, pady=3, sticky="ew")
    bot.grid_columnconfigure(0, weight=1)
    bot.grid_columnconfigure(1, weight=1)

    filter_var.trace_add("write", lambda *a: _refresh())

    # Taille souhaitee 720x560, PLAFONNEE a l'ecran reel (universel, multi-OS).
    # Sur grand ecran : min() garde 720x560 -> aucune regression. Sur ecran
    # scaled/petit (retour forum Windows 175 %) : la fenetre ne deborde plus,
    # les boutons du bas restent visibles, la liste defile.
    _want_w, _want_h = 720, 560
    try:
        _win_w = min(_want_w, int(win.winfo_screenwidth() * 0.95))
        _win_h = min(_want_h, int(win.winfo_screenheight() * 0.90))
    except Exception:
        _win_w, _win_h = _want_w, _want_h
    win.geometry("%dx%d" % (_win_w, _win_h))
    try:
        win.minsize(min(480, _win_w), min(360, _win_h))
    except Exception:
        pass
    if not state["ini"]:
        _set_status(_L("Choisis le fichier scenery_packs.ini pour commencer.",
                       "Choose scenery_packs.ini to start."))
    else:
        _refresh()
    return win


# ------------------------------------------------------------------------------
# AUTO-TEST HEADLESS (coeur uniquement ; la fenetre se teste chez Roland)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    sample = (
        "I\n"
        "1000 Version\n"
        "SCENERY\n"
        "\n"
        "SCENERY_PACK Custom Scenery/Aerosoft - LFMN Nice/\n"
        "SCENERY_PACK Custom Scenery/zOrtho4XP_+46-003/\n"
        "SCENERY_PACK *GLOBAL_AIRPORTS*\n"
        "SCENERY_PACK Custom Scenery/zOrtho4XP_+47+005_17_Dijon_XP12_2025-11 symlink/\n"
        "SCENERY_PACK_DISABLED Custom Scenery/zOrtho4XP_+61+023/\n"
    )
    ok = True

    tiles = list_ortho_tiles(sample)
    print("Tuiles Ortho :", len(tiles), "(attendu 3)")
    ok &= (len(tiles) == 3)

    # desactiver
    t2, ch = set_tile_enabled(sample, "Custom Scenery/zOrtho4XP_+46-003/", False)
    ok &= ch and ("SCENERY_PACK_DISABLED Custom Scenery/zOrtho4XP_+46-003/" in t2)
    ok &= (t2.count("\n") == sample.count("\n"))
    ok &= ("SCENERY_PACK Custom Scenery/Aerosoft - LFMN Nice/" in t2)
    ok &= ("*GLOBAL_AIRPORTS*" in t2)
    ok &= ("zOrtho4XP_+47+005_17_Dijon_XP12_2025-11 symlink/" in t2)
    print("Desactivation +46-003 : OK")

    # reactiver un OFF
    t3, ch3 = set_tile_enabled(sample, "Custom Scenery/zOrtho4XP_+61+023/", True)
    ok &= ch3 and ("SCENERY_PACK Custom Scenery/zOrtho4XP_+61+023/" in t3)
    ok &= ("SCENERY_PACK_DISABLED Custom Scenery/zOrtho4XP_+61+023/" not in t3)

    # idempotence + matching strict
    _, ch4 = set_tile_enabled(sample, "Custom Scenery/zOrtho4XP_+61+023/", False)
    ok &= (ch4 is False)
    _, ch5 = set_tile_enabled(sample, "Custom Scenery/zOrtho4XP_+99+099/", False)
    ok &= (ch5 is False)

    # retrait de ligne
    t6, rm = remove_tile_line(sample, "Custom Scenery/zOrtho4XP_+46-003/")
    ok &= rm and ("zOrtho4XP_+46-003/" not in t6)
    ok &= (t6.count("\n") == sample.count("\n") - 1)
    print("Retrait de ligne +46-003 : OK")

    # lat/lon depuis nom (simple + long + symlink)
    ok &= (tile_latlon_from_path("Custom Scenery/zOrtho4XP_+46-003/") == (46, -3))
    ok &= (tile_latlon_from_path("zOrtho4XP_+47+005_17_Dijon_XP12_2025-11 symlink/") == (47, 5))
    ok &= (tile_latlon_from_path("Custom Scenery/Aerosoft - LFMN Nice/") is None)
    print("Extraction lat/lon : OK")

    # xplane root / abspath
    ini = "/X/Custom Scenery/scenery_packs.ini"
    ok &= (xplane_root_from_ini(ini) == "/X")
    ok &= (tile_abspath(ini, "Custom Scenery/zOrtho4XP_+46-003/")
           == "/X/Custom Scenery/zOrtho4XP_+46-003")
    print("Chemins X-Plane : OK")

    # cycle fichier reel (tmp) : toggle + .bak + remove
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "scenery_packs.ini")
    with open(p, "w", encoding="utf-8") as f:
        f.write(sample)
    r1 = toggle_tile_in_file(p, "Custom Scenery/zOrtho4XP_+46-003/", False)
    ok &= (r1[0] is True)
    ok &= os.path.isfile(p + ".bak")
    ok &= ("SCENERY_PACK_DISABLED Custom Scenery/zOrtho4XP_+46-003/"
           in read_scenery_file(p))
    r2 = remove_tile_from_file(p, "Custom Scenery/zOrtho4XP_+61+023/")
    ok &= (r2[0] is True) and ("zOrtho4XP_+61+023/" not in read_scenery_file(p))
    print("Cycle fichier reel (.bak + ecriture) : OK")
    shutil.rmtree(d, ignore_errors=True)

    print("\n=== RESULTAT :", "TOUT VERT" if ok else "ECHEC", "===")
