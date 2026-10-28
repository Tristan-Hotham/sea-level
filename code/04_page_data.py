"""Step 4. Compact map data for the page.

Each grid becomes one RGB PNG that the page decodes on a canvas and recolours in the browser as the slider moves:
  R = drowning code (1..N: the first level on the ladder at which the cell is sea; 255: still land at +70 m)
  G = hill shading (1..255), or 0 for the Caspian Sea (a lake the model keeps apart from the ocean)
  B = height for colouring, 128 + 1.35 * sign(h) * sqrt(|h|) (so 0 m = 128; about 1 m steps near sea level)
Antarctica (south of 60 S) is drawn as it is today at every level: its land surface is the ice sheet itself.
Also writes data/coast.json (Natural Earth 1:10m coastline, simplified) and data/cities_page.json.
Run: python3 code/04_page_data.py
"""
import json, os, sys
import numpy as np, pandas as pd
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import terrain as t

WORK, DATA = os.path.join(ROOT, "work"), os.path.join(ROOT, "data")
LVJ = json.load(open(os.path.join(DATA, "levels.json"))); K0 = LVJ["k0"]


def shade(e, z, y0, exag):
    H, W = e.shape
    lat = t.gpy_to_lat(np.arange(H) + 0.5 + y0, z)
    px = 2 * np.pi * t.R_EARTH / (256 * 2 ** z) * np.cos(np.radians(lat))[:, None]
    gy, gx = np.gradient(e.astype(np.float32))
    dzdx, dzdy = gx / px * exag, gy / px * exag
    # light from the north-west, 45 degrees up (rows run southwards, so d/dnorth = -d/drow)
    dzdn = -dzdy
    alt = np.radians(45)
    lx, ly, lz = -np.cos(alt) * np.sqrt(.5), np.cos(alt) * np.sqrt(.5), np.sin(alt)
    hs = (-dzdx * lx - dzdn * ly + lz) / np.sqrt(1 + dzdx ** 2 + dzdn ** 2)
    return np.clip(hs, 0, 1)


ECL = [-4000, -2000, -1000, -200, -130, 70, 150, 300, 600, 1000, 1500, 2500, 4000]  # height classes 0..13 (5 = within the slider range)


def export(name, z, x0, y0, exag, crop, rf, out):
    """Write <out>_code.png (drowning code, full grid resolution) and <out>_relief.png (shade and height class, 1/rf resolution)."""
    code = np.load(os.path.join(WORK, f"{name}_code.npy"))
    e = np.load(os.path.join(WORK, f"{name}_elev.npy"))
    ld = np.load(os.path.join(WORK, f"{name}_land.npy"))
    if name == "world":
        lat = t.gpy_to_lat(np.arange(code.shape[0]) + 0.5, z)
        ant = lat < -60
        code[ant] = np.where(ld[ant] > 0, 255, 1)
    hs = shade(e, z, y0, exag)
    if crop:
        (lo0, la0), (lo1, la1) = crop
        X0, Y0 = t.lonlat_to_gpx(lo0, la0, z); X1, Y1 = t.lonlat_to_gpx(lo1, la1, z)
        r0, r1 = int(Y0 - y0) // rf * rf, int(Y1 - y0) // rf * rf; c0, c1 = int(X0 - x0) // rf * rf, int(X1 - x0) // rf * rf
        code, e, ld, hs = (a[r0:r1, c0:c1] for a in (code, e, ld, hs))
        x0, y0 = x0 + c0, y0 + r0
    H, W = code.shape
    Image.fromarray(code, "L").save(os.path.join(DATA, out + "_code.png"), optimize=True)
    # relief: mean shade over rf x rf blocks, 8 steps; height class of the block mean; +128 if the block is mostly Caspian
    blk = lambda a: a[:H // rf * rf, :W // rf * rf].reshape(H // rf, rf, W // rf, rf).mean(axis=(1, 3))
    sh = np.clip(np.round(blk(hs) * 7), 0, 7).astype(np.uint8)
    cl = np.digitize(blk(e), ECL).astype(np.uint8)
    lk = blk((ld == 2).astype(np.float32)) > 0.5
    rel = (cl + 16 * sh + 128 * lk).astype(np.uint8)
    Image.fromarray(rel, "L").save(os.path.join(DATA, out + "_relief.png"), optimize=True)
    meta = dict(z=z, x0=int(x0), y0=int(y0), w=int(W), h=int(H), rf=rf)
    print(out, meta, os.path.getsize(os.path.join(DATA, out + "_code.png")), os.path.getsize(os.path.join(DATA, out + "_relief.png")))
    return meta


GM = dict(world=export("world", 4, 0, 0, 30, None, 4, "world"),
          europe=export("europe", 7, 58 * 256, 34 * 256, 6, ((-14, 62.5), (14, 47.8)), 2, "europe"),
          height_classes=ECL)
json.dump(GM, open(os.path.join(DATA, "grids.json"), "w"))
for f in ("world_z3.png", "europe_z7.png"):
    if os.path.exists(os.path.join(DATA, f)): os.remove(os.path.join(DATA, f))

# coastline today (Natural Earth 1:10m, simplified for drawing)
from shapely.geometry import shape, mapping
cl = json.load(open(os.path.join(t.NE, "ne_10m_coastline.geojson")))
lines = []
for f in cl["features"]:
    s = shape(f["geometry"]).simplify(0.04, preserve_topology=False)
    if s.length < 0.4: continue
    for gm in (s.geoms if s.geom_type == "MultiLineString" else [s]):
        c = np.round(np.array(gm.coords), 2)
        if len(c) >= 2: lines.append(c.tolist())
json.dump(lines, open(os.path.join(DATA, "coast.json"), "w"), separators=(",", ":"))
print("coast.json", os.path.getsize(os.path.join(DATA, "coast.json")))

# cities for the page: all GeoNames cities the model floods at or below +70 m, as compact rows
C = pd.read_csv(os.path.join(DATA, "cities_world.csv"), keep_default_na=False, na_values=[""])  # "NA" is Namibia
C = C[(C.flood_level_m <= 70) | (C["pop"] >= 50000)].sort_values("pop", ascending=False)
C["flood_level_m"] = C.flood_level_m.where(np.isfinite(C.flood_level_m), 999)
rows = [[str(r["name"]), r.country, round(r.lat, 3), round(r.lon, 3), int(r["pop"]), round(float(r.flood_level_m), 2), int(r.height_m)] for _, r in C.iterrows()]
json.dump(dict(cols=["name", "cc", "lat", "lon", "pop", "flood_level", "height"], rows=rows), open(os.path.join(DATA, "cities_page.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("cities_page.json", len(rows), os.path.getsize(os.path.join(DATA, "cities_page.json")))
# UK towns for the page and the search: all OS Open Names cities and towns
U = pd.read_csv(os.path.join(DATA, "uk_towns.csv"))
urows = [[r.name, r.county if isinstance(r.county, str) else (r.district if isinstance(r.district, str) else r.country), round(r.lat, 4), round(r.lon, 4),
          round(float(r.elev_m), 1), round(float(r.flood_level_m), 2) if np.isfinite(r.flood_level_m) else 999, int(r.bua_pop2021) if r.bua_pop2021 == r.bua_pop2021 else 0]
         for r in U.itertuples(index=False)]
json.dump(dict(cols=["name", "area", "lat", "lon", "height", "flood_level", "pop"], rows=urows), open(os.path.join(DATA, "uk_towns_page.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("uk_towns_page.json", len(urows), os.path.getsize(os.path.join(DATA, "uk_towns_page.json")))
