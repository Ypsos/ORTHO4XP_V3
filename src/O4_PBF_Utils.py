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

#  O4_PBF_Utils.py  —  ORTHO4XP V3.2
#
#  Cache OSM local a partir d'un extrait .pbf (Geofabrik ou equivalent).
#
#  MODULE AUTONOME :
#    - il n'importe rien du pipeline sauf O4_File_Names, O4_OSM_Utils et
#      O4_UI_Utils, et il ne modifie AUCUN de ces fichiers ;
#    - il se contente de remplir a l'avance le dossier OSM_data/ avec les
#      memes fichiers <tuile>_<suffixe>.osm.bz2 que produirait un
#      telechargement Overpass ;
#    - le Step 1 d'Ortho4XP trouve alors les fichiers deja presents et ne
#      telecharge plus rien (mecanisme de recyclage natif, non modifie).
#
#  AUCUN binaire externe (pas d'osmconvert ni d'osmfilter) : le format PBF
#  est decode en Python pur. Seule dependance : numpy, deja requis par
#  Ortho4XP.
#
#  AUCUN mode "bypass" : ce module n'ecrit jamais de fichier factice. Si une
#  categorie ne contient aucune donnee sur la tuile, le fichier est ecrit
#  vide mais valide (exactement comme une reponse Overpass vide).
#
#  Compatible Windows / macOS (Apple Silicon et Intel) / Linux.
#
#  Idee inspiree de l'utilitaire Ortho-Vectors-Optimizer d'Ahmed
#  Qanadeely. Implementation entierement independante : aucune ligne
#  de son code n'a ete reprise.
# ==============================================================================

import os
import sys
import zlib
import struct
import time

import numpy

try:
    import O4_UI_Utils as UI
except Exception:  # utilisation hors Ortho4XP (tests)
    class _UIStub:
        red_flag = 0

        @staticmethod
        def vprint(level, *args):
            print(" ".join(str(a) for a in args))

        lvprint = vprint
        logprint = vprint

    UI = _UIStub()

import O4_File_Names as FNAMES
import O4_OSM_Utils as OSM


# ==============================================================================
#  CATEGORIES — copie stricte des requetes de O4_Vector_Map.py
#  Toute modification ici doit refleter O4_Vector_Map.py, jamais l'inverse.
# ==============================================================================
#  Une requete est decrite par (type_osm, cle, valeur_ou_None).
#  "tags_of_interest" reprend le parametre homonyme passe par O4_Vector_Map.

CATEGORIES = {
    "airports": {
        "queries": [
            ("n", "aeroway", None),
            ("w", "aeroway", None),
            ("r", "aeroway", None),
        ],
        "tags_of_interest": "all",
    },
    "big_roads": {
        "queries": [
            ("w", "highway", "motorway"),
            ("w", "highway", "trunk"),
            ("w", "highway", "primary"),
            ("w", "highway", "secondary"),
            ("w", "railway", "rail"),
            ("w", "railway", "narrow_gauge"),
        ],
        "tags_of_interest": ["bridge", "tunnel"],
    },
    "coastline": {
        "queries": [
            ("w", "natural", "coastline"),
        ],
        "tags_of_interest": [],
    },
    "water": {
        "queries": [
            ("r", "natural", "water"),
            ("r", "waterway", "riverbank"),
            ("w", "natural", "water"),
            ("w", "waterway", "riverbank"),
            ("w", "waterway", "dock"),
        ],
        "tags_of_interest": ["name"],
    },
}

# small_roads depend du road_level de la tuile (cf. O4_Vector_Map.py)
SMALL_ROADS_BY_LEVEL = {
    2: [("w", "highway", "tertiary")],
    3: [
        ("w", "highway", "tertiary"),
        ("w", "highway", "unclassified"),
        ("w", "highway", "residential"),
    ],
    4: [
        ("w", "highway", "tertiary"),
        ("w", "highway", "unclassified"),
        ("w", "highway", "residential"),
        ("w", "highway", "service"),
    ],
    5: [
        ("w", "highway", "tertiary"),
        ("w", "highway", "unclassified"),
        ("w", "highway", "residential"),
        ("w", "highway", "service"),
        ("w", "highway", "track"),
    ],
}


def categories_for(road_level=0):
    """Renvoie le dictionnaire des categories a produire."""
    cats = dict(CATEGORIES)
    if road_level >= 2:
        cats["small_roads"] = {
            "queries": SMALL_ROADS_BY_LEVEL[min(int(road_level), 5)],
            "tags_of_interest": ["bridge", "tunnel"],
        }
    return cats


# ==============================================================================
#  DECODEUR PROTOBUF MINIMAL
# ==============================================================================

_MASK64 = (1 << 64) - 1


def _read_varint(buf, pos):
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def _to_int64(val):
    """int64 non zigzag."""
    return val - (1 << 64) if val >= (1 << 63) else val


def _zigzag(val):
    """sint64 zigzag."""
    return (val >> 1) ^ -(val & 1)


def _iter_fields(buf, start=0, end=None):
    """Itere (numero_champ, type_fil, valeur_ou_(deb,fin)) sur un message."""
    if end is None:
        end = len(buf)
    pos = start
    while pos < end:
        key, pos = _read_varint(buf, pos)
        fnum = key >> 3
        wtype = key & 7
        if wtype == 0:
            val, pos = _read_varint(buf, pos)
            yield fnum, 0, val
        elif wtype == 2:
            ln, pos = _read_varint(buf, pos)
            yield fnum, 2, (pos, pos + ln)
            pos += ln
        elif wtype == 5:
            yield fnum, 5, buf[pos:pos + 4]
            pos += 4
        elif wtype == 1:
            yield fnum, 1, buf[pos:pos + 8]
            pos += 8
        else:
            raise ValueError("Type protobuf non supporte: %d" % wtype)


def _packed_varints(buf, start, end):
    out = []
    pos = start
    ap = out.append
    while pos < end:
        v, pos = _read_varint(buf, pos)
        ap(v)
    return out


# ==============================================================================
#  LECTURE DES BLOCS PBF
# ==============================================================================

def iter_primitive_blocks(pbf_path, progress_cb=None):
    """Itere sur les PrimitiveBlock decompresses d'un fichier .pbf."""
    total = os.path.getsize(pbf_path)
    with open(pbf_path, "rb") as f:
        while True:
            head = f.read(4)
            if len(head) < 4:
                return
            (hlen,) = struct.unpack(">I", head)
            bh = f.read(hlen)
            btype = None
            dsize = 0
            for fnum, wt, val in _iter_fields(bh):
                if fnum == 1 and wt == 2:
                    btype = bh[val[0]:val[1]].decode("utf-8")
                elif fnum == 3 and wt == 0:
                    dsize = val
            blob = f.read(dsize)
            if btype != "OSMData":
                continue
            data = None
            for fnum, wt, val in _iter_fields(blob):
                if fnum == 1 and wt == 2:          # raw
                    data = blob[val[0]:val[1]]
                elif fnum == 3 and wt == 2:        # zlib_data
                    data = zlib.decompress(blob[val[0]:val[1]])
            if data is None:
                continue
            if progress_cb:
                progress_cb(f.tell(), total)
            yield data


def _parse_block_header(block):
    """Renvoie (stringtable, groupes, granularity, lat_off, lon_off)."""
    strings = []
    groups = []
    granularity = 100
    lat_off = 0
    lon_off = 0
    for fnum, wt, val in _iter_fields(block):
        if fnum == 1 and wt == 2:       # StringTable
            s, e = val
            for f2, w2, v2 in _iter_fields(block, s, e):
                if f2 == 1 and w2 == 2:
                    strings.append(block[v2[0]:v2[1]])
        elif fnum == 2 and wt == 2:     # PrimitiveGroup
            groups.append(val)
        elif fnum == 17 and wt == 0:
            granularity = val
        elif fnum == 19 and wt == 0:
            lat_off = _to_int64(val)
        elif fnum == 20 and wt == 0:
            lon_off = _to_int64(val)
    return strings, groups, granularity, lat_off, lon_off


# ==============================================================================
#  CORRESPONDANCE DES TAGS
# ==============================================================================

class TagMatcher:
    """Compare les tags d'un objet aux requetes, par type OSM."""

    def __init__(self, cats):
        # {type: {cle: {valeur|None: set(categories)}}}
        self.rules = {"n": {}, "w": {}, "r": {}}
        # tags a conserver a la sortie, par categorie
        self.keep = {}
        self.keep_all = set()
        for cat, spec in cats.items():
            keys = set()
            for (otype, key, value) in spec["queries"]:
                self.rules[otype].setdefault(key, {}).setdefault(
                    value, set()
                ).add(cat)
                keys.add(key)
            toi = spec["tags_of_interest"]
            if toi == "all":
                self.keep_all.add(cat)
                self.keep[cat] = None
            else:
                self.keep[cat] = keys | set(toi)

    def types_used(self, otype):
        return bool(self.rules[otype])

    def match(self, otype, tags):
        """Renvoie l'ensemble des categories concernees par cet objet."""
        rules = self.rules[otype]
        if not rules:
            return None
        found = None
        for key, val in tags.items():
            sub = rules.get(key)
            if not sub:
                continue
            for wanted, cats in sub.items():
                if wanted is None or wanted == val:
                    if found is None:
                        found = set()
                    found |= cats
        return found

    def filtered_tags(self, cat, tags):
        wanted = self.keep[cat]
        if wanted is None:
            return dict(tags)
        return {k: v for k, v in tags.items() if k in wanted}


# ==============================================================================
#  COLLECTE
# ==============================================================================

class _Harvest:
    """Donnees brutes recoltees pour un lot de tuiles."""

    def __init__(self):
        self.node_ids = None      # numpy int64 trie (noeuds dans la bbox)
        self.node_lat = None      # numpy float64
        self.node_lon = None
        self.first_nodes = {}     # nid -> (cats, tags)
        self.ways = {}            # wid -> (cats|None, [refs])
        self.way_tags = {}        # wid -> tags
        self.rels = {}            # rid -> (cats, outer, inner, tags)
        self.extra_nodes = {}     # nid -> (lon, lat) hors bbox


def _bbox_of(tiles, margin=0.0):
    lats = [t[0] for t in tiles]
    lons = [t[1] for t in tiles]
    return (
        min(lats) - margin,
        min(lons) - margin,
        max(lats) + 1.0 + margin,
        max(lons) + 1.0 + margin,
    )


def _pass_nodes_bbox(pbf_path, bbox, matcher, harvest, prog):
    lat_min, lon_min, lat_max, lon_max = bbox
    ids = []
    lats = []
    lons = []
    want_node_tags = matcher.types_used("n")
    for block in iter_primitive_blocks(pbf_path, prog):
        strings, groups, gran, lat_off, lon_off = _parse_block_header(block)
        scale = 1e-9
        for gs, ge in groups:
            for fnum, wt, val in _iter_fields(block, gs, ge):
                if fnum == 2 and wt == 2:
                    _dense_nodes(
                        block, val, strings, gran, lat_off, lon_off, scale,
                        bbox, matcher, harvest, ids, lats, lons,
                        want_node_tags,
                    )
                elif fnum == 1 and wt == 2:
                    _plain_node(
                        block, val, strings, gran, lat_off, lon_off, scale,
                        bbox, matcher, harvest, ids, lats, lons,
                        want_node_tags,
                    )
    # Fusion cumulative : on concatene avec ce qui a deja ete recolte
    # lors des fichiers .pbf precedents (tuiles a cheval sur 2 regions),
    # puis on trie et on deduplique par identifiant de noeud.
    if harvest.node_ids is not None and len(harvest.node_ids):
        ids = list(harvest.node_ids) + ids
        lats = list(harvest.node_lat) + lats
        lons = list(harvest.node_lon) + lons
    if ids:
        a_id = numpy.array(ids, dtype=numpy.int64)
        a_lat = numpy.array(lats, dtype=numpy.float64)
        a_lon = numpy.array(lons, dtype=numpy.float64)
        order = numpy.argsort(a_id, kind="stable")
        a_id = a_id[order]
        a_lat = a_lat[order]
        a_lon = a_lon[order]
        keep = numpy.ones(len(a_id), dtype=bool)
        if len(a_id) > 1:
            keep[1:] = a_id[1:] != a_id[:-1]
        harvest.node_ids = a_id[keep]
        harvest.node_lat = a_lat[keep]
        harvest.node_lon = a_lon[keep]
    else:
        harvest.node_ids = numpy.zeros(0, dtype=numpy.int64)
        harvest.node_lat = numpy.zeros(0)
        harvest.node_lon = numpy.zeros(0)


def _dense_nodes(block, span, strings, gran, lat_off, lon_off, scale,
                 bbox, matcher, harvest, ids, lats, lons, want_node_tags):
    s, e = span
    d_id = d_lat = d_lon = None
    kv = None
    for fnum, wt, val in _iter_fields(block, s, e):
        if wt != 2:
            continue
        if fnum == 1:
            d_id = _packed_varints(block, val[0], val[1])
        elif fnum == 8:
            d_lat = _packed_varints(block, val[0], val[1])
        elif fnum == 9:
            d_lon = _packed_varints(block, val[0], val[1])
        elif fnum == 10:
            kv = _packed_varints(block, val[0], val[1])
    if not d_id:
        return
    lat_min, lon_min, lat_max, lon_max = bbox
    nid = 0
    clat = 0
    clon = 0
    kvpos = 0
    for i in range(len(d_id)):
        nid += _zigzag(d_id[i])
        clat += _zigzag(d_lat[i])
        clon += _zigzag(d_lon[i])
        tags = None
        if kv is not None:
            tags = {}
            while kvpos < len(kv) and kv[kvpos] != 0:
                k = strings[kv[kvpos]].decode("utf-8", "replace")
                v = strings[kv[kvpos + 1]].decode("utf-8", "replace")
                tags[k] = v
                kvpos += 2
            kvpos += 1
        latf = scale * (lat_off + gran * clat)
        lonf = scale * (lon_off + gran * clon)
        if lat_min <= latf <= lat_max and lon_min <= lonf <= lon_max:
            ids.append(nid)
            lats.append(latf)
            lons.append(lonf)
            if want_node_tags and tags:
                cats = matcher.match("n", tags)
                if cats:
                    harvest.first_nodes[nid] = (cats, tags)


def _plain_node(block, span, strings, gran, lat_off, lon_off, scale,
                bbox, matcher, harvest, ids, lats, lons, want_node_tags):
    s, e = span
    nid = 0
    rlat = 0
    rlon = 0
    keys = []
    vals = []
    for fnum, wt, val in _iter_fields(block, s, e):
        if fnum == 1 and wt == 0:
            nid = _zigzag(val)
        elif fnum == 8 and wt == 0:
            rlat = _zigzag(val)
        elif fnum == 9 and wt == 0:
            rlon = _zigzag(val)
        elif fnum == 2 and wt == 2:
            keys = _packed_varints(block, val[0], val[1])
        elif fnum == 3 and wt == 2:
            vals = _packed_varints(block, val[0], val[1])
    latf = scale * (lat_off + gran * rlat)
    lonf = scale * (lon_off + gran * rlon)
    lat_min, lon_min, lat_max, lon_max = bbox
    if not (lat_min <= latf <= lat_max and lon_min <= lonf <= lon_max):
        return
    ids.append(nid)
    lats.append(latf)
    lons.append(lonf)
    if want_node_tags and keys:
        tags = {
            strings[keys[i]].decode("utf-8", "replace"):
            strings[vals[i]].decode("utf-8", "replace")
            for i in range(len(keys))
        }
        cats = matcher.match("n", tags)
        if cats:
            harvest.first_nodes[nid] = (cats, tags)


def _decode_way(block, span, strings):
    s, e = span
    wid = 0
    keys = []
    vals = []
    refs = []
    for fnum, wt, val in _iter_fields(block, s, e):
        if fnum == 1 and wt == 0:
            wid = _to_int64(val)
        elif fnum == 2 and wt == 2:
            keys = _packed_varints(block, val[0], val[1])
        elif fnum == 3 and wt == 2:
            vals = _packed_varints(block, val[0], val[1])
        elif fnum == 8 and wt == 2:
            raw = _packed_varints(block, val[0], val[1])
            cur = 0
            for r in raw:
                cur += _zigzag(r)
                refs.append(cur)
    tags = {}
    for i in range(len(keys)):
        tags[strings[keys[i]].decode("utf-8", "replace")] = \
            strings[vals[i]].decode("utf-8", "replace")
    return wid, tags, refs


def _decode_relation(block, span, strings):
    s, e = span
    rid = 0
    keys = []
    vals = []
    roles = []
    memids = []
    types = []
    for fnum, wt, val in _iter_fields(block, s, e):
        if fnum == 1 and wt == 0:
            rid = _to_int64(val)
        elif fnum == 2 and wt == 2:
            keys = _packed_varints(block, val[0], val[1])
        elif fnum == 3 and wt == 2:
            vals = _packed_varints(block, val[0], val[1])
        elif fnum == 8 and wt == 2:
            roles = _packed_varints(block, val[0], val[1])
        elif fnum == 9 and wt == 2:
            raw = _packed_varints(block, val[0], val[1])
            cur = 0
            for r in raw:
                cur += _zigzag(r)
                memids.append(cur)
        elif fnum == 10 and wt == 2:
            types = _packed_varints(block, val[0], val[1])
    tags = {}
    for i in range(len(keys)):
        tags[strings[keys[i]].decode("utf-8", "replace")] = \
            strings[vals[i]].decode("utf-8", "replace")
    outer = []
    inner = []
    for i in range(len(memids)):
        if i < len(types) and types[i] != 1:   # 1 = way
            continue
        role = strings[roles[i]].decode("utf-8", "replace") if i < len(roles) \
            else ""
        if role == "inner":
            inner.append(memids[i])
        else:
            outer.append(memids[i])
    return rid, tags, outer, inner


def _in_bbox_ids(harvest, refs):
    """True si au moins une reference figure parmi les noeuds de la bbox."""
    arr = harvest.node_ids
    if not len(arr) or not refs:
        return False
    q = numpy.array(refs, dtype=numpy.int64)
    pos = numpy.searchsorted(arr, q)
    pos[pos >= len(arr)] = len(arr) - 1
    return bool((arr[pos] == q).any())


def _pass_ways(pbf_path, matcher, harvest, prog):
    for block in iter_primitive_blocks(pbf_path, prog):
        strings, groups, _g, _a, _o = _parse_block_header(block)
        for gs, ge in groups:
            for fnum, wt, val in _iter_fields(block, gs, ge):
                if fnum != 3 or wt != 2:
                    continue
                wid, tags, refs = _decode_way(block, val, strings)
                cats = matcher.match("w", tags)
                if not cats:
                    continue
                if not _in_bbox_ids(harvest, refs):
                    continue
                harvest.ways[wid] = (cats, refs)
                harvest.way_tags[wid] = tags


def _pass_relations(pbf_path, matcher, harvest, prog):
    if not matcher.types_used("r"):
        return set()
    needed = set()
    for block in iter_primitive_blocks(pbf_path, prog):
        strings, groups, _g, _a, _o = _parse_block_header(block)
        for gs, ge in groups:
            for fnum, wt, val in _iter_fields(block, gs, ge):
                if fnum != 4 or wt != 2:
                    continue
                rid, tags, outer, inner = _decode_relation(
                    block, val, strings
                )
                cats = matcher.match("r", tags)
                if not cats:
                    continue
                harvest.rels[rid] = (cats, outer, inner, tags)
                for w in outer + inner:
                    if w not in harvest.ways:
                        needed.add(w)
    return needed


def _pass_member_ways(pbf_path, needed, harvest, prog):
    if not needed:
        return
    for block in iter_primitive_blocks(pbf_path, prog):
        strings, groups, _g, _a, _o = _parse_block_header(block)
        for gs, ge in groups:
            for fnum, wt, val in _iter_fields(block, gs, ge):
                if fnum != 3 or wt != 2:
                    continue
                wid, tags, refs = _decode_way(block, val, strings)
                if wid not in needed:
                    continue
                harvest.ways[wid] = (None, refs)
                harvest.way_tags[wid] = tags


def _pass_complete_nodes(pbf_path, harvest, prog):
    """Recupere les noeuds hors bbox necessaires aux chemins complets."""
    needed = set()
    arr = harvest.node_ids
    for wid, (_c, refs) in harvest.ways.items():
        for r in refs:
            needed.add(r)
    if len(arr):
        have = set(int(x) for x in arr)
        needed -= have
    if not needed:
        return
    for block in iter_primitive_blocks(pbf_path, prog):
        strings, groups, gran, lat_off, lon_off = _parse_block_header(block)
        scale = 1e-9
        for gs, ge in groups:
            for fnum, wt, val in _iter_fields(block, gs, ge):
                if fnum == 2 and wt == 2:
                    _dense_complete(
                        block, val, gran, lat_off, lon_off, scale,
                        needed, harvest,
                    )
                elif fnum == 1 and wt == 2:
                    nid, latf, lonf = _plain_node_coords(
                        block, val, gran, lat_off, lon_off, scale
                    )
                    if nid in needed:
                        harvest.extra_nodes[nid] = (lonf, latf)


def _dense_complete(block, span, gran, lat_off, lon_off, scale,
                    needed, harvest):
    s, e = span
    d_id = d_lat = d_lon = None
    for fnum, wt, val in _iter_fields(block, s, e):
        if wt != 2:
            continue
        if fnum == 1:
            d_id = _packed_varints(block, val[0], val[1])
        elif fnum == 8:
            d_lat = _packed_varints(block, val[0], val[1])
        elif fnum == 9:
            d_lon = _packed_varints(block, val[0], val[1])
    if not d_id:
        return
    nid = 0
    clat = 0
    clon = 0
    for i in range(len(d_id)):
        nid += _zigzag(d_id[i])
        clat += _zigzag(d_lat[i])
        clon += _zigzag(d_lon[i])
        if nid in needed:
            harvest.extra_nodes[nid] = (
                scale * (lon_off + gran * clon),
                scale * (lat_off + gran * clat),
            )


def _plain_node_coords(block, span, gran, lat_off, lon_off, scale):
    s, e = span
    nid = 0
    rlat = 0
    rlon = 0
    for fnum, wt, val in _iter_fields(block, s, e):
        if fnum == 1 and wt == 0:
            nid = _zigzag(val)
        elif fnum == 8 and wt == 0:
            rlat = _zigzag(val)
        elif fnum == 9 and wt == 0:
            rlon = _zigzag(val)
    return (
        nid,
        scale * (lat_off + gran * rlat),
        scale * (lon_off + gran * rlon),
    )


# ==============================================================================
#  ECRITURE DU CACHE
# ==============================================================================

_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
            ('"', "&quot;"), ("'", "&apos;"))


def _xml_escape(text):
    for a, b in _ESCAPES:
        text = text.replace(a, b)
    return text


def _coords_of(harvest, nid):
    arr = harvest.node_ids
    if len(arr):
        pos = numpy.searchsorted(arr, nid)
        if pos < len(arr) and arr[pos] == nid:
            return (float(harvest.node_lon[pos]), float(harvest.node_lat[pos]))
    return harvest.extra_nodes.get(nid)


def _way_touches_tile(harvest, refs, lat, lon):
    for r in refs:
        c = _coords_of(harvest, r)
        if c is None:
            continue
        if lon <= c[0] <= lon + 1 and lat <= c[1] <= lat + 1:
            return True
    return False


def _write_tile_category(harvest, matcher, cat, lat, lon, overwrite):
    """Construit puis ecrit le fichier cache d'une categorie pour une tuile."""
    target = FNAMES.osm_cached(lat, lon, cat)
    if os.path.isfile(target) and not overwrite:
        UI.vprint(1, "    * Deja present, conserve :", target)
        return 0
    layer = OSM.OSM_layer()

    kept_ways = {}
    for wid, (cats, refs) in harvest.ways.items():
        if cats is None or cat not in cats:
            continue
        if not _way_touches_tile(harvest, refs, lat, lon):
            continue
        kept_ways[wid] = refs

    kept_rels = {}
    for rid, (cats, outer, inner, tags) in harvest.rels.items():
        if cat not in cats:
            continue
        members = outer + inner
        touch = False
        for w in members:
            entry = harvest.ways.get(w)
            if entry and _way_touches_tile(harvest, entry[1], lat, lon):
                touch = True
                break
        if not touch:
            continue
        kept_rels[rid] = (outer, inner, tags)
        for w in members:
            if w in harvest.ways and w not in kept_ways:
                kept_ways[w] = harvest.ways[w][1]

    # noeuds
    needed_nodes = set()
    for wid, refs in kept_ways.items():
        needed_nodes.update(refs)
    for nid, (cats, tags) in harvest.first_nodes.items():
        if cat not in cats:
            continue
        c = _coords_of(harvest, nid)
        if c and lon <= c[0] <= lon + 1 and lat <= c[1] <= lat + 1:
            needed_nodes.add(nid)
            layer.dicosmfirst["n"].add(nid)
            layer.dicosmtags["n"][nid] = {
                _xml_escape(k): _xml_escape(v)
                for k, v in matcher.filtered_tags(cat, tags).items()
            }

    for nid in needed_nodes:
        c = _coords_of(harvest, nid)
        if c is None:
            continue
        layer.dicosmn[nid] = c

    for wid, refs in kept_ways.items():
        clean = [r for r in refs if r in layer.dicosmn]
        if not clean:
            continue
        layer.dicosmw[wid] = clean
        tags = matcher.filtered_tags(cat, harvest.way_tags.get(wid, {}))
        if tags:
            layer.dicosmtags["w"][wid] = {
                _xml_escape(k): _xml_escape(v) for k, v in tags.items()
            }
        entry = harvest.ways.get(wid)
        if entry and entry[0] and cat in entry[0]:
            layer.dicosmfirst["w"].add(wid)

    for rid, (outer, inner, tags) in kept_rels.items():
        layer.dicosmrorig[rid] = {
            "outer": [w for w in outer if w in layer.dicosmw],
            "inner": [w for w in inner if w in layer.dicosmw],
        }
        layer.dicosmfirst["r"].add(rid)
        ftags = matcher.filtered_tags(cat, tags)
        if ftags:
            layer.dicosmtags["r"][rid] = {
                _xml_escape(k): _xml_escape(v) for k, v in ftags.items()
            }

    os.makedirs(os.path.dirname(target), exist_ok=True)
    layer.write_to_file(target)
    UI.vprint(
        1,
        "    * %s : %d noeuds, %d chemins, %d relations -> %s"
        % (cat, len(layer.dicosmn), len(layer.dicosmw),
           len(layer.dicosmrorig), os.path.basename(target)),
    )
    return 1


# ==============================================================================
#  POINT D'ENTREE PRINCIPAL
# ==============================================================================

def _harvest_batch(pbf_paths, bbox, matcher, cats, bi, nbatches,
                   progress):
    """Recolte un lot de tuiles depuis un ou plusieurs fichiers .pbf.

    Les noeuds, chemins et relations sont d'abord lus dans TOUS les
    fichiers (passes 1 a 4), puis la completion des noeuds hors emprise
    (passe 5) est faite sur TOUS les fichiers a la fin. Cela permet a un
    chemin issu du fichier A d'etre complete par un noeud present dans le
    fichier B — le cas d'une cote qui traverse la frontiere regionale.
    """
    harvest = _Harvest()
    nfiles = len(pbf_paths)

    def mk(step, fi):
        # fraction globale : lot, puis fichier, puis etape dans le fichier
        def cb(done, total):
            if progress:
                inner = (step - 1 + done / max(total, 1)) / 5.0
                per_file = (fi + inner) / nfiles
                frac = (bi + per_file) / nbatches
                progress("lot %d/%d" % (bi + 1, nbatches), frac)
        return cb

    t0 = time.time()
    # Passes 1 a 3 sur chaque fichier ; on cumule les chemins membres de
    # relations restant a trouver (ils peuvent se trouver dans un AUTRE
    # fichier que celui ou la relation est declaree).
    needed = set()
    for fi, pbf in enumerate(pbf_paths):
        if getattr(UI, "red_flag", 0):
            break
        if nfiles > 1:
            UI.vprint(1, "   fichier %d/%d : %s"
                      % (fi + 1, nfiles, os.path.basename(pbf)))
        UI.vprint(1, "   1/5 lecture des noeuds")
        _pass_nodes_bbox(pbf, bbox, matcher, harvest, mk(1, fi))
        UI.vprint(1, "   2/5 lecture des chemins")
        _pass_ways(pbf, matcher, harvest, mk(2, fi))
        UI.vprint(1, "   3/5 lecture des relations")
        needed |= _pass_relations(pbf, matcher, harvest, mk(3, fi))

    # Passe 4 : chercher les chemins membres manquants dans TOUS les
    # fichiers (un membre peut etre au-dela de la frontiere regionale).
    needed = {w for w in needed if w not in harvest.ways}
    UI.vprint(1, "   4/5 chemins membres de relations")
    for fi, pbf in enumerate(pbf_paths):
        if getattr(UI, "red_flag", 0):
            break
        if needed:
            _pass_member_ways(pbf, needed, harvest, mk(4, fi))

    # Passe 5 : completion des noeuds hors emprise, sur tous les fichiers.
    UI.vprint(1, "   5/5 completion des chemins")
    for fi, pbf in enumerate(pbf_paths):
        if getattr(UI, "red_flag", 0):
            break
        _pass_complete_nodes(pbf, harvest, mk(5, fi))

    UI.vprint(1, "   lot lu en %.1f s" % (time.time() - t0))
    return harvest


def build_osm_cache(pbf_path, tiles, road_level=0, overwrite=False,
                    batch_size=6, progress=None):
    """
    Remplit le cache OSM_data/ a partir d'un ou plusieurs extraits .pbf.

      pbf_path   : chemin d'un .pbf, OU liste/tuple de chemins .pbf.
                   Plusieurs fichiers servent aux tuiles a cheval sur
                   deux regions Geofabrik : leurs donnees sont fusionnees.
      tiles      : liste de couples (lat, lon)
      road_level : 0 = pas de small_roads, sinon 2 a 5
      overwrite  : ecraser les fichiers cache deja presents
      batch_size : nombre de tuiles traitees par passe (memoire)
      progress   : fonction(texte, fraction) facultative

    Renvoie le nombre de fichiers ecrits.
    """
    # Uniformise l'entree : accepte un chemin unique ou une liste.
    if isinstance(pbf_path, (list, tuple)):
        pbf_paths = list(pbf_path)
    else:
        pbf_paths = [pbf_path]
    pbf_paths = [p for p in pbf_paths if p]

    missing = [p for p in pbf_paths if not os.path.isfile(p)]
    if missing:
        for p in missing:
            UI.lvprint(1, "Fichier .pbf introuvable :", p)
        return 0
    if not pbf_paths or not tiles:
        return 0

    cats = categories_for(road_level)
    matcher = TagMatcher(cats)
    written = 0
    tiles = sorted(set((int(a), int(b)) for a, b in tiles))
    batches = [tiles[i:i + batch_size]
               for i in range(0, len(tiles), batch_size)]

    if len(pbf_paths) > 1:
        UI.vprint(0, "-> %d extraits .pbf fusionnes." % len(pbf_paths))

    for bi, batch in enumerate(batches):
        if getattr(UI, "red_flag", 0):
            UI.vprint(1, "Interruption demandee.")
            return written
        bbox = _bbox_of(batch)
        UI.vprint(
            0,
            "-> Lot %d/%d : %d tuile(s)" % (bi + 1, len(batches), len(batch)),
        )

        harvest = _harvest_batch(pbf_paths, bbox, matcher, cats,
                                 bi, len(batches), progress)

        for (lat, lon) in batch:
            UI.vprint(0, "   Tuile %+03d%+04d" % (lat, lon))
            for cat in cats:
                written += _write_tile_category(
                    harvest, matcher, cat, lat, lon, overwrite
                )
        del harvest

    UI.vprint(0, "-> Cache OSM local termine : %d fichier(s)." % written)
    return written


# ==============================================================================
#  INTERFACE GRAPHIQUE
#  Fenetre autonome, aux couleurs et polices d'Ortho4XP.
#  Aucun fichier du pipeline n'est importe ni modifie ici.
# ==============================================================================

# ------------------------------------------------------------------
#  Cles de traduction (voir O4_Lang_FR.py / O4_Lang_EN.py)
#  Convention du projet : la cle est le texte francais.
# ------------------------------------------------------------------
K_TITLE = "Cache OSM local (.pbf)"
K_BUTTON = "\U0001F5FA Cache OSM local (.pbf)"
K_INTRO = ("Remplit OSM_data/ \u00e0 partir d'un ou plusieurs extraits .pbf "
           "locaux afin que l'\u00e9tape 1 ne t\u00e9l\u00e9charge plus rien.")
K_FILE = "Fichier(s) PBF :"
K_BROWSE = "Parcourir (un ou plusieurs)..."
K_FROM = "De latitude / longitude :"
K_TO = "\u00c0 latitude / longitude :"
K_ROAD = "Niveau de routes (0 = aucun) :"
K_OVER = "\u00c9craser les fichiers de cache existants"
K_RUN = "Construire le cache OSM local"
K_CLOSE = "Fermer"
K_ERRLL = "La latitude et la longitude doivent \u00eatre des nombres entiers."
K_ERRFILE = "Fichier PBF introuvable."
K_MANY = "Nombre de tuiles demand\u00e9 tr\u00e8s important. Continuer ?"
K_DONE = "Cache OSM local termin\u00e9. Fichiers \u00e9crits :"
K_ERRPBF = "Erreur pendant la lecture du fichier PBF."
K_HINT = ("Chaque fichier est relu 5 fois : comptez quelques minutes par lot "
          "de tuiles. Pour une tuile \u00e0 cheval sur deux r\u00e9gions, "
          "s\u00e9lectionnez les deux extraits .pbf \u00e0 la fois.")
K_FILE_HINT = ("Astuce : vous pouvez s\u00e9lectionner plusieurs fichiers "
               "\u00e0 la fois (Cmd-clic ou Ctrl-clic) \u2014 utile pour une "
               "tuile \u00e0 cheval sur deux r\u00e9gions.")

# ------------------------------------------------------------------
#  Theme — memes valeurs par defaut que O4_GUI_Utils, rechargees
#  depuis O4_Theme_Manager quand il est present.
# ------------------------------------------------------------------
_BG = "#3b5b49"
_FG = "#e8f0ec"
_FG2 = "#a6e3a1"
_BTN_BG = "#4a6b59"
_BTN_FG = "#ffffff"
_ACCENT = "#a6e3a1"
_ENTRY_BG = "#f0f4f2"
_ENTRY_FG = "#1e3028"


def _reload_theme():
    """Recharge les couleurs depuis le theme actif d'Ortho4XP."""
    global _BG, _FG, _FG2, _BTN_BG, _BTN_FG, _ACCENT
    try:
        import O4_Theme_Manager as _TM
        _t = _TM.get_theme()
        _BG = _t.get("bg", _BG)
        _FG = _t.get("fg", _FG)
        _FG2 = _t.get("fg_secondary", _FG2)
        _BTN_BG = _t.get("btn_bg", _BTN_BG)
        _BTN_FG = _t.get("btn_fg", _BTN_FG)
        _ACCENT = _t.get("accent", _ACCENT)
    except Exception:
        pass


def _get_tr():
    """Renvoie la fonction de traduction du projet (O4_Lang.tr).

    Repli sur l'identite si le moteur de langue est absent : l'interface
    reste alors en francais brut, sans jamais planter.
    """
    try:
        import O4_Lang
        if callable(getattr(O4_Lang, "tr", None)):
            return O4_Lang.tr
    except Exception:
        pass
    return lambda key: key


def open_pbf_window(parent=None):
    """Ouvre la fenetre « Cache OSM local (.pbf) »."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    _reload_theme()
    tr = _get_tr()

    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.configure(bg=_BG)
    win.title(tr(K_TITLE))
    # Redimensionnable, mais bornee par une taille minimale (fixee plus
    # bas apres mesure du contenu) : agrandir est permis, retrecir au
    # point de masquer un bouton ne l'est pas.
    win.resizable(True, True)

    FONT = ("TkFixedFont", 11)
    FONT_B = ("TkFixedFont", 11, "bold")
    FONT_S = ("TkFixedFont", 10, "italic")
    LBL_W = 30

    v_pbf = tk.StringVar()
    v_lat = tk.StringVar(value="46")
    v_lon = tk.StringVar(value="-3")
    v_lat2 = tk.StringVar(value="46")
    v_lon2 = tk.StringVar(value="-3")
    v_road = tk.StringVar(value="0")
    v_over = tk.IntVar(value=0)

    def sep():
        tk.Frame(win, bg=_BTN_BG, height=1).pack(fill="x", padx=10, pady=6)

    def entry(master, var, width):
        return tk.Entry(master, textvariable=var, width=width,
                        bg=_ENTRY_BG, fg=_ENTRY_FG, font=FONT,
                        insertbackground=_ENTRY_FG)

    # ── Intitule ──────────────────────────────────────────────────
    tk.Label(win, text=tr(K_INTRO), bg=_BG, fg=_FG, font=FONT,
             justify="left", wraplength=560, anchor="w").pack(
        fill="x", padx=12, pady=(10, 2))
    tk.Label(win, text=tr(K_HINT), bg=_BG, fg="#888888", font=FONT_S,
             justify="left", wraplength=560, anchor="w").pack(
        fill="x", padx=12, pady=(0, 2))
    sep()

    # ── Fichier PBF ───────────────────────────────────────────────
    row_file = tk.Frame(win, bg=_BG)
    row_file.pack(fill="x", padx=10, pady=4)
    tk.Label(row_file, text=tr(K_FILE), bg=_BG, fg=_FG, font=FONT,
             width=LBL_W, anchor="e").pack(side="left")
    e_file = entry(row_file, v_pbf, 34)
    e_file.pack(side="left", fill="x", expand=True, padx=(6, 6))

    def browse():
        # Selection multiple possible : une tuile a cheval sur deux
        # regions Geofabrik peut necessiter deux extraits .pbf.
        paths = filedialog.askopenfilenames(
            title=tr(K_FILE),
            filetypes=[("OpenStreetMap PBF", "*.pbf"), ("*", "*")],
        )
        if paths:
            v_pbf.set(";".join(paths))

    ttk.Button(row_file, text=tr(K_BROWSE), command=browse,
               width=26).pack(side="left")

    # Astuce multi-selection, juste sous le champ fichier
    tk.Label(win, text=tr(K_FILE_HINT), bg=_BG, fg=_FG2, font=FONT_S,
             justify="left", wraplength=560, anchor="w").pack(
        fill="x", padx=12, pady=(0, 2))

    # ── Coordonnees ───────────────────────────────────────────────
    for label_key, va, vo in ((K_FROM, v_lat, v_lon), (K_TO, v_lat2, v_lon2)):
        row = tk.Frame(win, bg=_BG)
        row.pack(fill="x", padx=10, pady=2)
        tk.Label(row, text=tr(label_key), bg=_BG, fg=_FG, font=FONT,
                 width=LBL_W, anchor="e").pack(side="left")
        entry(row, va, 6).pack(side="left", padx=(6, 4))
        entry(row, vo, 6).pack(side="left")

    # ── Niveau de routes ──────────────────────────────────────────
    row_road = tk.Frame(win, bg=_BG)
    row_road.pack(fill="x", padx=10, pady=(6, 2))
    tk.Label(row_road, text=tr(K_ROAD), bg=_BG, fg=_FG, font=FONT,
             width=LBL_W, anchor="e").pack(side="left")
    ttk.Combobox(row_road, textvariable=v_road,
                 values=["0", "2", "3", "4", "5"], width=4,
                 state="readonly", font=FONT).pack(side="left", padx=(6, 0))

    # ── Ecrasement ────────────────────────────────────────────────
    row_over = tk.Frame(win, bg=_BG)
    row_over.pack(fill="x", padx=10, pady=(2, 4))
    tk.Label(row_over, text="", bg=_BG, width=LBL_W).pack(side="left")
    tk.Checkbutton(row_over, text=tr(K_OVER), variable=v_over,
                   bg=_BG, fg=_FG, selectcolor=_BG, font=FONT,
                   activebackground=_BG, activeforeground=_BTN_FG,
                   anchor="w").pack(side="left", padx=(6, 0))
    sep()

    # ── Progression ───────────────────────────────────────────────
    bar = ttk.Progressbar(win, length=560, mode="determinate", maximum=1000)
    bar.pack(fill="x", padx=12, pady=(2, 2))
    lbl_state = tk.Label(win, text="", bg=_BG, fg=_FG2, font=FONT_B,
                         anchor="w")
    lbl_state.pack(fill="x", padx=12, pady=(0, 4))

    def progress(label, frac):
        bar["value"] = max(0, min(1000, int(frac * 1000)))
        lbl_state.config(text=label)
        win.update_idletasks()

    # ── Boutons ───────────────────────────────────────────────────
    row_btn = tk.Frame(win, bg=_BG)
    row_btn.pack(fill="x", padx=10, pady=(4, 10))

    def run():
        try:
            la1, la2 = int(v_lat.get()), int(v_lat2.get())
            lo1, lo2 = int(v_lon.get()), int(v_lon2.get())
        except ValueError:
            messagebox.showerror(tr(K_TITLE), tr(K_ERRLL), parent=win)
            return
        pbf_list = [p.strip() for p in v_pbf.get().split(";") if p.strip()]
        if not pbf_list or any(not os.path.isfile(p) for p in pbf_list):
            messagebox.showerror(tr(K_TITLE), tr(K_ERRFILE), parent=win)
            return
        tiles = [
            (a, b)
            for a in range(min(la1, la2), max(la1, la2) + 1)
            for b in range(min(lo1, lo2), max(lo1, lo2) + 1)
        ]
        if len(tiles) > 200 and not messagebox.askyesno(
            tr(K_TITLE), tr(K_MANY), parent=win
        ):
            return
        btn_run.config(state="disabled")
        try:
            written = build_osm_cache(
                pbf_list, tiles,
                road_level=int(v_road.get()),
                overwrite=bool(v_over.get()),
                progress=progress,
            )
            messagebox.showinfo(
                tr(K_TITLE), tr(K_DONE) + " %d" % written, parent=win
            )
        except Exception as exc:
            try:
                UI.vprint(1, "[PBF] " + str(exc))
            except Exception:
                pass
            messagebox.showerror(
                tr(K_TITLE), tr(K_ERRPBF) + "\n\n%s" % exc, parent=win
            )
        finally:
            btn_run.config(state="normal")
            bar["value"] = 0
            lbl_state.config(text="")

    btn_run = ttk.Button(row_btn, text=tr(K_RUN), command=run, width=32)
    btn_run.pack(side="left", padx=(0, 6), fill="x", expand=True)
    ttk.Button(row_btn, text=tr(K_CLOSE), command=win.destroy,
               width=14).pack(side="left")

    # ── Application du theme global ───────────────────────────────
    try:
        import O4_Theme_Manager as _TM
        _TM.apply_to_root(win)
    except Exception:
        pass

    # ── Taille minimale : jamais aucun bouton recouvert ───────────
    # On laisse Tk calculer la taille requise par tout le contenu,
    # puis on la fixe comme minimum absolu. La fenetre ne peut donc
    # pas etre reduite au point de masquer les boutons du bas.
    def _lock_min_size():
        try:
            win.update_idletasks()
            need_w = win.winfo_reqwidth()
            need_h = win.winfo_reqheight()
            win.minsize(need_w, need_h)
            # Ouvre exactement a la taille requise (aucune troncature).
            if not win.winfo_ismapped():
                win.geometry("%dx%d" % (need_w, need_h))
        except Exception:
            pass

    try:
        # differe le calcul apres le premier trace des widgets
        win.after(0, _lock_min_size)
    except Exception:
        _lock_min_size()

    # exposes pour les tests automatises (aucun effet sur l'interface)
    win._pbf_run = run
    win._pbf_vars = {
        "pbf": v_pbf, "lat": v_lat, "lon": v_lon,
        "lat2": v_lat2, "lon2": v_lon2,
        "road": v_road, "overwrite": v_over,
    }
    return win


if __name__ == "__main__":
    open_pbf_window().mainloop()
