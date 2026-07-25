import os
import sys
import hmac
import hashlib
import binascii
from math import floor

g2xpl_16_prefix = ""
g2xpl_16_suffix = ""

import pathlib as _pathlib
Ortho4XP_dir = str(_pathlib.Path(__file__).resolve().parent.parent) if not getattr(sys, "frozen", False) else str(_pathlib.Path(sys.executable).parent.parent)
Preview_dir = os.path.join(Ortho4XP_dir, "Previews")
Provider_dir = os.path.join(Ortho4XP_dir, "Providers")
Extent_dir = os.path.join(Ortho4XP_dir, "Extents")
Filter_dir = os.path.join(Ortho4XP_dir, "Filters")
OSM_dir = os.path.join(Ortho4XP_dir, "OSM_data")
Mask_dir = os.path.join(Ortho4XP_dir, "Masks")
Imagery_dir = os.path.join(Ortho4XP_dir, "Orthophotos")
Elevation_dir = os.path.join(Ortho4XP_dir, "Elevation_data")
Geotiff_dir = os.path.join(Ortho4XP_dir, "Geotiffs")
Patch_dir = os.path.join(Ortho4XP_dir, "Patches")
Utils_dir = os.path.join(Ortho4XP_dir, "Utils")
Tile_dir = os.path.join(Ortho4XP_dir, "Tiles")
Tmp_dir = os.path.join(Ortho4XP_dir, "tmp")
os.makedirs(Tmp_dir, exist_ok=True)
Overlay_dir = os.path.join(Ortho4XP_dir, "yOrtho4XP_Overlays")
##############################################################################
def short_latlon(lat, lon):
    strlat = "{:+.0f}".format(lat).zfill(3)
    strlon = "{:+.0f}".format(lon).zfill(4)
    return strlat + strlon


def round_latlon(lat, lon):
    strlatround = "{:+.0f}".format(floor(lat / 10) * 10).zfill(3)
    strlonround = "{:+.0f}".format(floor(lon / 10) * 10).zfill(4)
    return strlatround + strlonround


def long_latlon(lat, lon):
    strlat = "{:+.0f}".format(lat).zfill(3)
    strlon = "{:+.0f}".format(lon).zfill(4)
    strlatround = "{:+.0f}".format(floor(lat / 10) * 10).zfill(3)
    strlonround = "{:+.0f}".format(floor(lon / 10) * 10).zfill(4)
    return os.path.join(strlatround + strlonround, strlat + strlon)


def hem_latlon(lat, lon):
    hemisphere = "N" if lat >= 0 else "S"
    greenwichside = "E" if lon >= 0 else "W"
    return (
        hemisphere
        + "{:.0f}".format(abs(lat)).zfill(2)
        + greenwichside
        + "{:.0f}".format(abs(lon)).zfill(3)
    )


##############################################################################


def tile_dir(lat, lon):
    return "zOrtho4XP_" + short_latlon(lat, lon)


def build_dir(lat, lon, custom_build_dir):
    if not custom_build_dir:
        return os.path.join(Tile_dir, tile_dir(lat, lon))
    elif custom_build_dir[-1] == "/":
        return os.path.join(custom_build_dir[:-1], tile_dir(lat, lon))
    else:
        return custom_build_dir


def osm_dir(lat, lon):
    return os.path.join(OSM_dir, long_latlon(lat, lon))


def mask_dir(lat, lon):
    return os.path.join(Mask_dir, long_latlon(lat, lon))


def patch_dir(lat, lon):
    return os.path.join(Patch_dir, long_latlon(lat, lon))


def input_node_file(tile):
    if tile.iterate:
        return os.path.join(
            tile.build_dir,
            "Data"
            + short_latlon(tile.lat, tile.lon)
            + "."
            + str(tile.iterate)
            + ".node",
        )
    else:
        return os.path.join(
            tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".node"
        )


def input_poly_file(tile):
    if tile.iterate:
        return os.path.join(
            tile.build_dir,
            "Data"
            + short_latlon(tile.lat, tile.lon)
            + "."
            + str(tile.iterate)
            + ".poly",
        )
    else:
        return os.path.join(
            tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".poly"
        )


def input_ele_file(tile):
    if tile.iterate:
        return os.path.join(
            tile.build_dir,
            "Data"
            + short_latlon(tile.lat, tile.lon)
            + "."
            + str(tile.iterate)
            + ".ele",
        )
    else:
        return os.path.join(
            tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".ele"
        )


def output_node_file(tile):
    return os.path.join(
        tile.build_dir,
        "Data"
        + short_latlon(tile.lat, tile.lon)
        + "."
        + str(tile.iterate + 1)
        + ".node",
    )


def output_poly_file(tile):
    return os.path.join(
        tile.build_dir,
        "Data"
        + short_latlon(tile.lat, tile.lon)
        + "."
        + str(tile.iterate + 1)
        + ".poly",
    )


def output_ele_file(tile):
    return os.path.join(
        tile.build_dir,
        "Data"
        + short_latlon(tile.lat, tile.lon)
        + "."
        + str(tile.iterate + 1)
        + ".ele",
    )


def alt_file(tile):
    if tile.iterate:
        return os.path.join(
            tile.build_dir,
            "Data"
            + short_latlon(tile.lat, tile.lon)
            + "."
            + str(tile.iterate)
            + ".alt",
        )
    else:
        return os.path.join(
            tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".alt"
        )


def apt_file(tile):
    return os.path.join(
        tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".apt"
    )


##############################################################################
# SIGNATURE DU CACHE AÉROPORTS
#
# Le cache aéroports (.apt) est relu à l'étape 2 et à l'étape 3. Son format
# exécute du code au moment de l'ouverture : un fichier .apt fabriqué ailleurs
# et déposé dans un dossier de tuile suffirait à faire tourner n'importe quel
# programme sur la machine.
#
# Chaque cache écrit par Ortho4XP est donc accompagné d'une signature calculée
# avec une clé propre à cette installation. Avant toute relecture, la signature
# est vérifiée : si elle est absente ou ne correspond pas, le cache est
# simplement effacé et sera régénéré normalement. Aucun changement visible
# pour l'utilisateur.
##############################################################################

apt_cache_key_file = os.path.join(Ortho4XP_dir, ".apt_cache_key")


def apt_sig_file(tile):
    return apt_file(tile) + ".sig"


def _apt_notify(*args):
    """Message d'information, sans dépendance d'import au chargement."""
    try:
        import O4_UI_Utils as UI

        UI.lvprint(1, *args)
    except Exception:
        print(" ".join(str(x) for x in args))


def apt_cache_key():
    """Clé de signature propre à cette installation.

    Créée au premier usage à partir du générateur aléatoire du système, puis
    conservée. Elle ne quitte jamais la machine : un cache signé ailleurs ne
    peut donc pas être accepté ici.
    """
    try:
        with open(apt_cache_key_file, "rb") as f:
            key = f.read().strip()
        if len(key) >= 32:
            return key
    except Exception:
        pass
    key = binascii.hexlify(os.urandom(32))
    try:
        fd = os.open(
            apt_cache_key_file,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        with os.fdopen(fd, "wb") as f:
            f.write(key)
    except Exception:
        # Clé non conservée (dossier en lecture seule) : la vérification
        # échouera au build suivant et le cache sera régénéré. Sans danger.
        pass
    return key


def apt_signature(file_name):
    """Empreinte signée du contenu d'un fichier."""
    h = hmac.new(apt_cache_key(), digestmod=hashlib.sha256)
    with open(file_name, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().encode("ascii")


def sign_apt_file(tile):
    """Écrit la signature du cache aéroports. Retourne True si réussi."""
    try:
        with open(apt_sig_file(tile), "wb") as f:
            f.write(apt_signature(apt_file(tile)))
        return True
    except Exception:
        _apt_notify(
            "WARNING: Could not sign airport cache", apt_file(tile)
        )
        return False


def check_apt_file(tile):
    """Vérifie le cache aéroports avant toute relecture.

    Retourne True si le cache est présent et authentique. Sinon le cache et sa
    signature sont effacés : le programme se comporte alors exactement comme
    si le fichier n'avait jamais existé (cas déjà prévu partout).
    """
    apt = apt_file(tile)
    sig = apt_sig_file(tile)
    if not os.path.isfile(apt):
        return False
    try:
        with open(sig, "rb") as f:
            expected = f.read().strip()
        if expected and hmac.compare_digest(expected, apt_signature(apt)):
            return True
        reason = "signature does not match"
    except Exception:
        reason = "signature missing"
    _apt_notify(
        "WARNING: Airport cache",
        apt,
        "rejected (" + reason + "), it will be rebuilt.",
    )
    for f_name in (apt, sig):
        try:
            os.remove(f_name)
        except Exception:
            pass
    return False


def weight_file(tile):
    return os.path.join(
        tile.build_dir, "Data" + short_latlon(tile.lat, tile.lon) + ".weight"
    )


def mesh_file(build_dir, lat, lon):
    return os.path.join(build_dir, "Data" + short_latlon(lat, lon) + ".mesh")


def dsf_file(build_dir, lat, lon):
    if "Earth nav data" in build_dir:
        return os.path.join(build_dir, long_latlon(lat, lon) + ".dsf")
    else:
        return os.path.join(build_dir, "Earth nav data", long_latlon(lat, lon) + ".dsf")


def obj_file(til_x_left, til_y_top, zoomlevel, provider_code):
    return os.path.join(
        Geotiff_dir,
        str(til_y_top)
        + "_"
        + str(til_x_left)
        + "_"
        + provider_code
        + str(zoomlevel)
        + ".obj",
    )


def mtl_file(til_x_left, til_y_top, zoomlevel, provider_code):
    return os.path.join(
        Geotiff_dir,
        str(til_y_top)
        + "_"
        + str(til_x_left)
        + "_"
        + provider_code
        + str(zoomlevel)
        + ".mtl",
    )


##############################################################################

##############################################################################
def preview(lat, lon, zoomlevel, provider_code):
    return os.path.join(
        Preview_dir,
        short_latlon(lat, lon) + "_" + provider_code + str(zoomlevel) + ".jpg",
    )


##############################################################################

##############################################################################
def custom_coastline(lat, lon):
    return os.path.join(
        OSM_dir,
        long_latlon(lat, lon),
        short_latlon(lat, lon) + "_custom_coastline.osm.bz2",
    )


def custom_coastline_dir(lat, lon):
    return os.path.join(OSM_dir, long_latlon(lat, lon), "custom_coastline")


def custom_water(lat, lon):
    return os.path.join(
        OSM_dir,
        long_latlon(lat, lon),
        short_latlon(lat, lon) + "_custom_water.osm.bz2",
    )


def custom_water_dir(lat, lon):
    return os.path.join(OSM_dir, long_latlon(lat, lon), "custom_water")


def osm_cached(lat, lon, cached_suffix):
    return os.path.join(
        OSM_dir,
        long_latlon(lat, lon),
        short_latlon(lat, lon) + "_" + cached_suffix + ".osm.bz2",
    )


def osm_old_cached(lat, lon, query):
    subtags = query.split('"')
    return os.path.join(
        OSM_dir,
        long_latlon(lat, lon),
        short_latlon(lat, lon)
        + "_"
        + subtags[0][0:-1]
        + "_"
        + subtags[1]
        + "_"
        + subtags[3]
        + ".osm",
    )


##############################################################################
def base_file_name(lat, lon):
    return os.path.join(
        Elevation_dir, round_latlon(lat, lon), hem_latlon(lat, lon)
    )


##############################################################################

##############################################################################
def elevation_data(source, lat, lon):
    if source == "View":
        return base_file_name(lat, lon) + ".hgt"
    elif source == "SRTM":
        return base_file_name(lat, lon) + "_SRTMv3.hgt"
    elif source == "ALOS":
        return base_file_name(lat, lon) + "_ALOS3W30.tif"
    elif source == "NED1/3":
        return base_file_name(lat, lon) + "_NED13.tif"
    elif source == "NED1":
        return base_file_name(lat, lon) + "_NED1.tif"
##############################################################################

##############################################################################
def generic_tif(lat, lon):
    return base_file_name(lat, lon) + ".tif"


##############################################################################

##############################################################################
def viewfinderpanorama(lat, lon):
    return base_file_name(lat, lon) + ".hgt"


##############################################################################

##############################################################################
def SRTM_1sec(lat, lon):
    return base_file_name(lat, lon) + "_SRTM_1sec.hgt"


##############################################################################

##############################################################################
def legacy_mask(m_til_x_left, m_til_y_top):
    return str(m_til_y_top) + "_" + str(m_til_x_left) + ".png"

def distance_mask(m_til_x_left, m_til_y_top):
    return str(m_til_y_top) + "_" + str(m_til_x_left) + "_dist.png"


def mask_file(til_x_left, til_y_top, zoomlevel, provider_code):
    return (
        str(til_y_top) + "_" + str(til_x_left) + "_ZL" + str(zoomlevel) + ".png"
    )


##############################################################################

##############################################################################
def jpeg_file_name_from_attributes(
    til_x_left, til_y_top, zoomlevel, provider_code
):
    if provider_code == "g2xpl_16":
        file_name = (
            g2xpl_16_prefix
            + str(zoomlevel)
            + "_"
            + str(til_x_left)
            + "_"
            + str(2 ** zoomlevel - 16 - til_y_top)
            + g2xpl_16_suffix
            + ".jpg"
        )
    else:
        file_name = (
            str(til_y_top)
            + "_"
            + str(til_x_left)
            + "_"
            + provider_code
            + str(zoomlevel)
            + ".jpg"
        )
    return file_name


##############################################################################

##############################################################################
def jpeg_file_dir_from_attributes(lat, lon, zoomlevel, provider):
    if not provider:
        file_dir = "."
    elif provider["imagery_dir"] == "patch":
        # Mode PATCH : Patches/{tile_key}/PATCH_{zl}/
        file_dir = os.path.join(
            Patch_dir,
            short_latlon(lat, lon),
            "PATCH_" + str(zoomlevel),
        )
    elif provider["imagery_dir"] == "normal":
        file_dir = os.path.join(
            Imagery_dir,
            short_latlon(lat, lon),
            provider["code"] + "_" + str(zoomlevel),
        )
    elif provider["imagery_dir"] == "grouped":
        file_dir = os.path.join(
            Imagery_dir,
            long_latlon(lat, lon),
            provider["code"] + "_" + str(zoomlevel),
        )
    elif provider["imagery_dir"] == "code":
        file_dir = os.path.join(
            Imagery_dir,
            provider["code"],
            provider["code"] + "_" + str(zoomlevel),
        )
    else:
        file_dir = os.path.join(
            Imagery_dir,
            provider["imagery_dir"],
            provider["code"] + "_" + str(zoomlevel),
        )
    return file_dir


##############################################################################

##############################################################################
def dds_file_name_from_attributes(
    til_x_left, til_y_top, zoomlevel, provider_code, file_ext="dds"
):
    if provider_code == "g2xpl_16":
        file_name = (
            g2xpl_16_prefix
            + str(zoomlevel)
            + "_"
            + str(til_x_left)
            + "_"
            + str(2 ** zoomlevel - 16 - til_y_top)
            + g2xpl_16_suffix
            + "."
            + file_ext
        )
    else:
        file_name = (
            str(til_y_top)
            + "_"
            + str(til_x_left)
            + "_"
            + provider_code
            + str(zoomlevel)
            + "."
            + file_ext
        )
    return file_name


##############################################################################

##############################################################################
def geotiff_file_name_from_attributes(
    til_x_left, til_y_top, zoomlevel, provider_code
):
    return (
        str(til_y_top)
        + "_"
        + str(til_x_left)
        + "_"
        + provider_code
        + str(zoomlevel)
        + "-WGS84.tif"
    )


##############################################################################
