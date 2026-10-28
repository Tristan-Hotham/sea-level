"""Step 1. Build the bathtub grids.

For each grid (world at zoom 4, about 10 km pixels; Britain, Ireland and the North Sea at zoom 7, about 700 m pixels)
this script:
  1. decodes the AWS Terrain Tiles (terrarium) elevations, which include the seabed;
  2. rasterises today's land from Natural Earth 1:10m land (so today's coast, not the elevation model, sets level 0);
  3. finds the world ocean (Natural Earth water connected to the open ocean; the Caspian Sea counts as a lake);
  4. for every sea level on a fixed ladder from -130 m to +70 m, floods only the cells that are below that level AND
     joined to the ocean through other cells below it (8-connected), and records for each cell the first level at
     which it is sea. That index (the "drowning code") is all the page needs to redraw the map at any level.
Rules: at or below today's level, today's land never becomes sea (a falling sea cannot flood land); at or above it,
today's sea never becomes land. Land already below sea level today (polders, the Fens, the Caspian lowland) floods at
the first rise above 0 if the ocean can reach it, because the model has no sea walls.
Outputs (work/ is temporary, data/ is published):
  work/<grid>_code.npy, work/<grid>_elev.npy, work/<grid>_land.npy, work/<grid>_country.npy
  data/levels.json (the level ladder)
Run: python3 code/01_grids.py
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import terrain as t

WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
# the level ladder: 1 m steps, 0.25 m steps between -2 and +3 m (where the 2100 projections sit)
LEVELS = sorted(set([float(v) for v in range(-130, -2)] + [round(-2 + 0.25 * i, 2) for i in range(21)] + [float(v) for v in range(4, 71)]))
assert len(LEVELS) < 250
K0 = sum(1 for v in LEVELS if v <= 0)  # number of levels at or below 0
json.dump({"levels": LEVELS, "k0": K0, "note": "code c (1..len) = first level index (1-based) at which the cell is sea; 255 = still land at +70 m"},
          open(os.path.join(ROOT, "data", "levels.json"), "w"))

GRIDS = {
    "world": dict(z=4, x0=0, y0=0, file="z4.npy"),
    "europe": dict(z=7, x0=58 * 256, y0=34 * 256, file="z7.npy"),
}


def raster_polys(geoms, z, x0, y0, W, H, values=None, mode="L"):
    img = Image.new(mode, (W, H), 0); dr = ImageDraw.Draw(img)
    for i, g in enumerate(geoms):
        v = 1 if values is None else values[i]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for j, ring in enumerate(poly):
                a = np.array(ring)
                if len(a) < 3: continue
                x, y = t.lonlat_to_gpx(a[:, 0], a[:, 1], z)
                pts = list(zip((x - x0).tolist(), (y - y0).tolist()))
                dr.polygon(pts, fill=v if j == 0 else 0)
    return np.asarray(img)


def build(name, z, x0, y0, file):
    elev = np.load(os.path.join(WORK, file)).astype(np.float32)
    elev = np.clip(elev, -11000, 8900)
    H, W = elev.shape
    land_geo = json.load(open(os.path.join(t.NE, "ne_10m_land.geojson")))
    land = raster_polys([f["geometry"] for f in land_geo["features"]], z, x0, y0, W, H) > 0
    cty = json.load(open(os.path.join(t.NE, "ne_10m_admin_0_countries.geojson")))
    codes = [f["properties"]["ADM0_A3"] for f in cty["features"]]
    country = raster_polys([f["geometry"] for f in cty["features"]], z, x0, y0, W, H, values=list(range(1, len(codes) + 1)), mode="I").astype(np.int32)
    # the ocean: water components of the Natural Earth land mask, excluding the Caspian Sea
    water = ~land
    lab, n = ndimage.label(water, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    cx, cy = t.lonlat_to_gpx(51.0, 42.0, z)
    casp = 0
    if 0 <= cx - x0 < W and 0 <= cy - y0 < H:
        casp = lab[int(cy - y0), int(cx - x0)]
    ocean = water & (lab != casp) if casp else water.copy()
    # drop tiny enclosed water specks (lagoons cut off by the raster) unless large
    small = np.zeros(n + 1, bool); small[1:] = sizes[1:] < 30
    if casp: small[casp] = True
    ocean &= ~small[lab]
    lake = water & ~ocean
    eff = elev.copy()
    eff[ocean] = np.minimum(eff[ocean], -1.0)  # today's sea is sea at level 0 whatever the coarse model says
    code = np.full((H, W), 255, np.uint8)
    for k, L in enumerate(LEVELS, start=1):
        below = eff < L
        if L > 0:
            lb, _ = ndimage.label(below, structure=np.ones((3, 3)))
            seeds = np.unique(lb[ocean & below]); seeds = seeds[seeds > 0]
            keep = np.zeros(lb.max() + 1, bool); keep[seeds] = True
            sea = keep[lb]
        else:
            sea = ocean & below
        newly = sea & (code == 255)
        code[newly] = k
        if k % 25 == 0: print(name, L, flush=True)
    # rules for today's land and sea
    code[land | lake] = np.maximum(code[land | lake], K0 + 1)
    code[ocean] = np.minimum(code[ocean], K0)
    np.save(os.path.join(WORK, f"{name}_code.npy"), code)
    np.save(os.path.join(WORK, f"{name}_elev.npy"), elev)
    np.save(os.path.join(WORK, f"{name}_land.npy"), (land.astype(np.uint8) + 2 * lake.astype(np.uint8)))
    np.save(os.path.join(WORK, f"{name}_country.npy"), country.astype(np.uint16))
    json.dump(codes, open(os.path.join(WORK, "country_codes.json"), "w"))
    print(name, "done", H, W)


if __name__ == "__main__":
    for nm, g in GRIDS.items():
        if len(sys.argv) > 1 and nm not in sys.argv[1:]: continue
        build(nm, g["z"], g["x0"], g["y0"], g["file"])
