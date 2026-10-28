"""Step 2. A finer bathtub grid for the United Kingdom and Ireland, for the UK numbers.

Input: the zoom-10 AWS Terrain Tiles extract for Britain and Ireland (hist_dem_z10.bin, about 95 m pixels at 52 N),
averaged in 2 x 2 blocks to zoom 9 (about 190 m by 190 m at 52 N, a little finer in the north) to keep memory small.
Missing tiles are open sea. The same rules as step 1: today's land from Natural Earth 1:10m, sea floods only cells
connected to the ocean, levels from 0 to +70 m (the UK figures for falling seas come from the zoom-7 grid).
Output: work/uk_code.npy, work/uk_elev.npy, work/uk_land.npy, work/uk_country.npy, work/uk_meta.json
Run: python3 code/02_uk_grid.py
"""
import json, os, sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import terrain as t
from importlib import util
spec = util.spec_from_file_location("g", os.path.join(HERE, "01_grids.py")); g = util.module_from_spec(spec); spec.loader.exec_module(g)

DEM_BIN = os.environ.get("DEM_BIN", "/mnt/user-data/uploads/Downloads/hist_dem_z10.bin")
DEM_IDX = os.environ.get("DEM_IDX", "/mnt/user-data/uploads/Downloads/hist_dem_z10_index.json")
WORK = os.path.join(ROOT, "work")
idx = json.load(open(DEM_IDX))
xr0, xr1, yr0, yr1 = idx["range"]
flat = np.memmap(DEM_BIN, dtype="<i2", mode="r")
H, W = (yr1 - yr0 + 1) * 128, (xr1 - xr0 + 1) * 128
elev = np.full((H, W), -50.0, np.float32)  # missing tiles: sea
for i, k in enumerate(idx["tiles"]):
    x, y = map(int, k.split("_"))
    a = np.asarray(flat[i * 65536:(i + 1) * 65536], dtype=np.float32).reshape(256, 256)
    a = a.reshape(128, 2, 128, 2).mean(axis=(1, 3))
    elev[(y - yr0) * 128:(y - yr0 + 1) * 128, (x - xr0) * 128:(x - xr0 + 1) * 128] = a
elev = np.clip(elev, -500, 1400)  # the extract has a few spikes above Ben Nevis (1,345 m)
z, x0, y0 = 9, xr0 * 128, yr0 * 128
land_geo = json.load(open(os.path.join(t.NE, "ne_10m_land.geojson")))
land = g.raster_polys([f["geometry"] for f in land_geo["features"]], z, x0, y0, W, H) > 0
cty = json.load(open(os.path.join(t.NE, "ne_10m_admin_0_countries.geojson")))
country = g.raster_polys([f["geometry"] for f in cty["features"]], z, x0, y0, W, H, values=list(range(1, len(cty["features"]) + 1)), mode="I").astype(np.uint16)
ocean = ~land
eff = elev.copy(); eff[ocean] = np.minimum(eff[ocean], -1.0)
LV = g.LEVELS; K0 = g.K0
code = np.full((H, W), 255, np.uint8)
code[ocean] = K0
for k, L in enumerate(LV, start=1):
    if L <= 0: continue
    below = eff < L
    lb, _ = ndimage.label(below, structure=np.ones((3, 3)))
    seeds = np.unique(lb[ocean & below]); seeds = seeds[seeds > 0]
    keep = np.zeros(lb.max() + 1, bool); keep[seeds] = True
    sea = keep[lb]
    code[sea & (code == 255)] = k
    del lb, below, sea
    if k % 20 == 0: print(L, flush=True)
np.save(os.path.join(WORK, "uk_code.npy"), code)
np.save(os.path.join(WORK, "uk_elev.npy"), elev)
np.save(os.path.join(WORK, "uk_land.npy"), land.astype(np.uint8))
np.save(os.path.join(WORK, "uk_country.npy"), country)
json.dump(dict(z=z, x0=x0, y0=y0, H=H, W=W), open(os.path.join(WORK, "uk_meta.json"), "w"))
print("uk grid", H, W)
