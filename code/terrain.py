"""Shared helpers: read the bundled AWS Terrain Tiles (terrarium PNGs) into web-mercator mosaics, and project lon/lat."""
import base64, gzip, io, json, math, os
import numpy as np
from PIL import Image

D13 = os.environ.get("D13", "/home/claude/hist/_data13")
NE = os.environ.get("NE", "/home/claude/hist/_data3/ne/geojson")
R_EARTH = 6371008.8


def load_tiles():
    return json.load(gzip.open(os.path.join(D13, "terrarium_tiles.json.gz")))


def decode(b64):
    a = np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def mosaic(T, z, x0, x1, y0, y1):
    """Elevation mosaic (metres) of tiles x0..x1, y0..y1 inclusive at zoom z."""
    out = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), np.float32)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            out[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = decode(T["tiles"][f"{z}/{x}/{y}"])
    return out


def lonlat_to_gpx(lon, lat, z):
    """Global pixel coordinates at zoom z (256 px tiles)."""
    n = 256 * 2 ** z
    lat = np.clip(np.asarray(lat, dtype=np.float64), -85.0511, 85.0511)
    x = (np.asarray(lon, dtype=np.float64) + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(np.radians(lat)) + 1.0 / np.cos(np.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def gpy_to_lat(y, z):
    n = 256 * 2 ** z
    return np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * np.asarray(y, dtype=np.float64) / n))))


def gpx_to_lon(x, z):
    return np.asarray(x, dtype=np.float64) / (256 * 2 ** z) * 360.0 - 180.0


def cell_area_km2(rows_gy, z):
    """Area (km2) of one pixel in each row, given the row's global pixel y of its centre."""
    lat = gpy_to_lat(rows_gy, z)
    side = 2 * math.pi * R_EARTH / (256 * 2 ** z) * np.cos(np.radians(lat))
    return side ** 2 / 1e6
