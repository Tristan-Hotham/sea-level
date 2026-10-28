"""Render the bathtub map at any sea level from the published page grids (data/<grid>_code.png and _relief.png),
with the same colours and rules as the interactive page. Used by the header, figures and collage scripts.
"""
import json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
LVJ = json.load(open(os.path.join(DATA, "levels.json"))); LV = np.array(LVJ["levels"]); K = len(LV); K0 = LVJ["k0"]
GM = json.load(open(os.path.join(DATA, "grids.json")))
CLS_H = np.array([-5000, -3000, -1500, -600, -165, 35, 110, 225, 450, 800, 1250, 2000, 3200, 5000, 5000, 5000], float)


def hexc(h): return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], float)


def ramp(stops):
    xs = np.array([s[0] for s in stops], float); cs = np.array([hexc(s[1]) for s in stops])
    return lambda v: np.stack([np.interp(v, xs, cs[:, j]) for j in range(3)], -1)


LAND = ramp([[0, "#D3DBBA"], [40, "#C6D1A8"], [150, "#CFC9A0"], [500, "#C2AC84"], [1500, "#A88F72"], [3000, "#C9C1B8"], [5500, "#F4F2EE"]])
SEA = ramp([[0, "#A9D8D3"], [20, "#8CC3C4"], [80, "#6AA8B6"], [300, "#4A86A3"], [1500, "#2C5F82"], [5000, "#1D4766"]])
DROWN = ramp([[0, "#EE9B7E"], [10, "#E07A5C"], [40, "#C8573C"], [70, "#A9452F"]])
EXPOSE = ramp([[0, "#EFE0AE"], [20, "#E8D49C"], [60, "#DCC07E"], [130, "#C9A962"]])
BELOW, LAKE = hexc("#9B7BC0"), hexc("#9CC9D6")


def kof(level): return int((LV <= level + 1e-9).sum())


def lut(level):
    k = kof(level)
    c = np.arange(256)[:, None]; cls = np.arange(16)[None, :]
    prev = np.r_[LV[0] - 1, LV]
    hcode = np.where((c >= 1) & (c <= K), LV[np.clip(c - 1, 0, K - 1)] - (LV[np.clip(c - 1, 0, K - 1)] - prev[np.clip(c - 1, 0, K - 1)]) / 2, np.nan)
    h = np.where((c >= 2) & (c <= K), hcode, CLS_H[cls])
    water = c <= k; today = c > K0
    out = np.zeros((256, 16, 3)); isl = np.zeros((256, 16), bool)
    m1 = water & today; out[...] = LAND(np.maximum(0, h)); isl[...] = True
    d = DROWN(level - h); out = np.where(m1[..., None], d, out); isl &= ~m1
    out = np.where((m1 & (c == K0 + 1))[..., None], BELOW, out)
    m2 = water & ~today; out = np.where(m2[..., None], SEA(level - h), out); isl &= ~m2
    m3 = ~water & ~today; out = np.where(m3[..., None], EXPOSE(h - level), out)
    sh = np.arange(8)
    mul = np.where(isl[..., None], 0.74 + sh * 0.048, 0.93 + sh * 0.012)
    full = out[:, :, None, :] * mul[..., None]
    return np.clip(full, 0, 255).astype(np.uint8), k


_cache = {}


def grid(name):
    if name not in _cache:
        g = GM[name]
        code = np.asarray(Image.open(os.path.join(DATA, f"{name}_code.png")))
        rel = np.asarray(Image.open(os.path.join(DATA, f"{name}_relief.png")))
        _cache[name] = (g, code, rel)
    return _cache[name]


def render(name, level, rows=None, cols=None, step=1):
    """RGB image of grid `name` at `level` (m). rows/cols: slices of the grid; step: subsampling."""
    g, code, rel = grid(name)
    rows = rows or slice(0, g["h"]); cols = cols or slice(0, g["w"])
    rr = np.arange(rows.start, rows.stop, step); cc = np.arange(cols.start, cols.stop, step)
    c = code[np.ix_(rr, cc)].astype(int)
    r = rel[np.ix_(np.minimum(rr // g["rf"], rel.shape[0] - 1), np.minimum(cc // g["rf"], rel.shape[1] - 1))].astype(int)
    L, k = lut(level)
    img = L[c, r & 15, (r >> 4) & 7]
    lake = (r & 128) > 0
    img[lake & (c > k)] = LAKE
    wl = lake & (c <= k)  # the Caspian joined by the ocean: drawn as sea
    if wl.any():
        h = np.where(c[wl] <= K, LV[np.clip(c[wl] - 1, 0, K - 1)], 0)
        img[wl] = np.clip(SEA(level - h), 0, 255).astype(np.uint8)
    if name == "world":  # Antarctica as today
        pass
    return img


def window(name, lon0, lat0, lon1, lat1):
    """Row and column slices of grid `name` covering a lon/lat box."""
    import terrain as t
    g = GM[name]
    x0, y0 = t.lonlat_to_gpx(lon0, lat0, g["z"]); x1, y1 = t.lonlat_to_gpx(lon1, lat1, g["z"])
    return (slice(max(0, int(y0 - g["y0"])), min(g["h"], int(y1 - g["y0"]))), slice(max(0, int(x0 - g["x0"])), min(g["w"], int(x1 - g["x0"]))))
