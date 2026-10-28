"""Step 3. Every number: areas, land bridges, cities, UK towns and people at each sea level.

Inputs: the grids from steps 1 and 2 (work/), GeoNames cities15000 (CC BY 4.0), OS Open Names (OGL v3),
ONS BUA22 centroids and areas, LSOA to BUA22 lookup, MSOA 2021 population-weighted centroids and Census 2021 TS001
(OGL v3), and the zoom-10 elevation extract (for point heights of UK places).
Outputs: data/results.json (every number used anywhere), data/levels_world.csv, data/levels_uk.csv,
data/countries_lost.csv, data/land_bridges.csv, data/cities_world.csv, data/uk_towns.csv
Run: python3 code/03_analyse.py
"""
import io, json, math, os, sys, zipfile
import numpy as np, pandas as pd
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import terrain as t

WORK, DATA = os.path.join(ROOT, "work"), os.path.join(ROOT, "data")
D8 = "/home/claude/hist/_data8"
OSN = "/home/claude/hist/osnames_gb.tsv"
LVJ = json.load(open(os.path.join(DATA, "levels.json")))
LV = np.array(LVJ["levels"]); K = len(LV); K0 = LVJ["k0"]
POS = np.arange(K0, K)  # indices (0-based) of positive levels
NEG = np.arange(0, K0)  # indices of levels at or below 0
kof = lambda L: int((LV <= L + 1e-9).sum())  # number of ladder levels at or below L; a cell is sea if code <= kof(L)
CODES = json.load(open(os.path.join(WORK, "country_codes.json")))
cty = json.load(open(os.path.join(t.NE, "ne_10m_admin_0_countries.geojson")))
CNAME = {f["properties"]["ADM0_A3"]: f["properties"]["NAME"] for f in cty["features"]}
R = {"levels": LV.tolist(), "k0": K0}


def grid(name):
    c = np.load(os.path.join(WORK, f"{name}_code.npy"))
    e = np.load(os.path.join(WORK, f"{name}_elev.npy"))
    ld = np.load(os.path.join(WORK, f"{name}_land.npy"))
    co = np.load(os.path.join(WORK, f"{name}_country.npy"))
    return c, e, ld, co


def cum_by_code(code, weights, mask):
    """Area (weights) of masked cells whose code <= k, for k = 1..K."""
    h = np.bincount(code[mask].astype(np.int64), weights=weights[mask], minlength=256)
    return np.cumsum(h)[1:K + 1]


# ---------------------------------------------------------------- world (zoom 4)
code, elev, ld, co = grid("world")
H, W = code.shape
rows = np.arange(H) + 0.5
lat_row = t.gpy_to_lat(rows, 4)
area = np.repeat(t.cell_area_km2(rows, 4)[:, None], W, axis=1).astype(np.float64)
keep = (lat_row > -60)[:, None] & np.ones((1, W), bool)  # Antarctica left out: its 'land' surface is the ice sheet itself
land, lake = ld == 1, ld == 2
ocean = ~(land | lake)
today_land = float(area[land & keep].sum())
hi = elev >= 0  # land the elevation model puts at or above today's sea level
lost = cum_by_code(code, area, land & keep & hi)  # today's land (model height >= 0) that is sea at level k
lost_b0 = cum_by_code(code, area, land & keep & ~hi)  # today's land the model already puts below sea level
sea_ocean = cum_by_code(code, area, ocean & keep)  # today's sea still sea at level k
ocean_area = float(area[ocean & keep].sum())
gained = ocean_area - sea_ocean
below0 = land & keep & (elev < 0) & (code == K0 + 1)  # already below today's sea level and reachable at the first rise
R["world"] = dict(land_km2=today_land, below0_reach_km2=float(area[below0].sum()),
                  lost_km2=[float(v) if i >= K0 else 0.0 for i, v in enumerate(lost)],
                  lost_below0_km2=[float(v) if i >= K0 else 0.0 for i, v in enumerate(lost_b0)], below0_km2=float(area[land & keep & ~hi].sum()),
                  gained_km2=[float(v) if i < K0 else 0.0 for i, v in enumerate(gained)],
                  grid="AWS Terrain Tiles zoom 4, 4096 x 4096 web-mercator pixels (about 9.8 km at the equator, 6 km at 52 N)")
# countries: land lost at each positive level
cid = co.astype(np.int64)
m = land & keep & (cid > 0) & hi
h = np.bincount(cid[m] * 256 + code[m].astype(np.int64), weights=area[m], minlength=(len(CODES) + 1) * 256).reshape(len(CODES) + 1, 256)
cum = np.cumsum(h, axis=1)[:, 1:K + 1]
tot = h.sum(axis=1)
crow = []
for i, a3 in enumerate(CODES, start=1):
    if tot[i] < 1: continue
    crow.append(dict(a3=a3, name=CNAME[a3], land_km2=float(tot[i]), lost=[float(cum[i, j]) for j in POS]))
R["countries"] = sorted(crow, key=lambda r: -r["land_km2"])
pd.DataFrame([[r["a3"], r["name"], round(r["land_km2"])] + [round(v, 1) for v in r["lost"]] for r in R["countries"]],
             columns=["adm0_a3", "name", "land_km2_in_grid"] + [f"lost_km2_at_{LV[j]:g}m" for j in POS]).to_csv(os.path.join(DATA, "countries_lost.csv"), index=False)

# land bridges at falling sea levels (4-connected land; today's sea uses 8-connectivity)
BR_WORLD = [
    ("Beringia: Asia and North America", "Chukotka", 66.16, -169.8, "Alaska", 64.5, -165.4),
    ("Sahul: New Guinea and Australia", "Merauke, New Guinea", -8.47, 140.4, "Cape York, Australia", -12.6, 142.5),
    ("Tasmania and mainland Australia", "Hobart", -42.88, 147.33, "Melbourne", -37.81, 144.96),
    ("Sunda: Borneo and the Malay Peninsula", "Kuching", 1.55, 110.34, "Kuala Lumpur", 3.14, 101.69),
    ("Sri Lanka and India", "Jaffna", 9.66, 80.02, "Madurai", 9.93, 78.12),
    ("Taiwan and mainland China", "Taipei", 25.03, 121.56, "Fuzhou", 26.07, 119.30),
]
BR_EU = [
    ("Great Britain and continental Europe", "London", 51.51, -0.13, "Paris", 48.86, 2.35),
    ("Ireland and Great Britain", "Dublin", 53.35, -6.26, "Liverpool", 53.41, -2.98),
]


def bridges(name, z, x0, y0, pairs):
    c = np.load(os.path.join(WORK, f"{name}_code.npy"))
    pts = []
    for p in pairs:
        ax, ay = t.lonlat_to_gpx(p[3], p[2], z); bx, by = t.lonlat_to_gpx(p[6], p[5], z)
        pts.append((int(ay - y0), int(ax - x0), int(by - y0), int(bx - x0)))
    best = [None] * len(pairs)
    for j in NEG[::-1]:  # from 0 downwards
        landL = c > (j + 1)
        lb, _ = ndimage.label(landL)
        for i, (ay, ax, by, bx) in enumerate(pts):
            if best[i] is None and lb[ay, ax] > 0 and lb[ay, ax] == lb[by, bx]:
                best[i] = float(LV[j])
        if all(b is not None for b in best): break
    return [dict(name=p[0], a=p[1], b=p[4], joined_below_m=best[i]) for i, p in enumerate(pairs)]


R["bridges_world"] = bridges("world", 4, 0, 0, BR_WORLD)
R["bridges_europe"] = bridges("europe", 7, 58 * 256, 34 * 256, BR_EU)
R["bridges_world_check"] = bridges("world", 4, 0, 0, BR_EU)  # the same two links on the coarse world grid
pd.DataFrame([dict(link=b["name"], place_a=b["a"], place_b=b["b"], grid=g, joined_when_sea_at_or_below_m=b["joined_below_m"])
              for g, L in (("zoom 4 world", R["bridges_world"]), ("zoom 7 Europe", R["bridges_europe"]), ("zoom 4 world", R["bridges_world_check"])) for b in L]
             ).to_csv(os.path.join(DATA, "land_bridges.csv"), index=False)
print("bridges", R["bridges_world"], R["bridges_europe"], R["bridges_world_check"])

# ---------------------------------------------------------------- Europe grid (zoom 7): Doggerland
ce, ee, le, coe = grid("europe")
He, We = ce.shape
rows_e = np.arange(He) + 0.5 + 34 * 256
area_e = np.repeat(t.cell_area_km2(rows_e, 7)[:, None], We, axis=1)
lat_e = t.gpy_to_lat(rows_e, 7); lon_e = t.gpx_to_lon(np.arange(We) + 0.5 + 58 * 256, 7)
DB = dict(lat0=51.0, lat1=57.5, lon0=-3.0, lon1=9.0)
box = ((lat_e >= DB["lat0"]) & (lat_e <= DB["lat1"]))[:, None] & ((lon_e >= DB["lon0"]) & (lon_e <= DB["lon1"]))[None, :]
oc_e = le == 0
dog_sea = cum_by_code(ce, area_e, oc_e & box)
dog_total = float(area_e[oc_e & box].sum())
R["doggerland"] = dict(box=DB, sea_km2=dog_total, land_km2=[float(dog_total - v) if i < K0 else 0.0 for i, v in enumerate(dog_sea)])
# the Dogger Bank itself (a point on the bank, 54.75 N 2.0 E): the highest level at which the model still has it dry
gx, gy = t.lonlat_to_gpx(2.0, 54.75, 7)
cdb = int(ce[int(gy - 34 * 256), int(gx - 58 * 256)])
R["dogger_bank"] = dict(lat=54.75, lon=2.0, sea_from_m=float(LV[cdb - 1]), dry_at_or_below_m=float(LV[cdb - 2]))
# exposed sea floor around Britain and Ireland (whole zoom-7 window)
all_sea = cum_by_code(ce, area_e, oc_e)
R["europe_window"] = dict(sea_km2=float(area_e[oc_e].sum()), exposed_km2=[float(area_e[oc_e].sum() - v) if i < K0 else 0.0 for i, v in enumerate(all_sea)],
                          bounds=[float(lon_e[0]), float(lat_e[-1]), float(lon_e[-1]), float(lat_e[0])])
# Netherlands and others on the finer grid (for the text)
eu_c = {}
for a3 in ["NLD", "BEL", "DEU", "DNK", "FRA", "IRL", "GBR"]:
    i = CODES.index(a3) + 1
    mm = (le == 1) & (coe == i) & (ee >= 0)
    cc = cum_by_code(ce, area_e, mm)
    eu_c[a3] = dict(name=CNAME[a3], land_km2=float(area_e[mm].sum()), lost=[float(cc[j]) for j in POS])
R["europe_countries"] = eu_c
del ce, ee, le, coe, area_e

# ---------------------------------------------------------------- UK grid (zoom 9)
cu = np.load(os.path.join(WORK, "uk_code.npy")); eu = np.load(os.path.join(WORK, "uk_elev.npy"))
lu = np.load(os.path.join(WORK, "uk_land.npy")) == 1; cou = np.load(os.path.join(WORK, "uk_country.npy"))
um = json.load(open(os.path.join(WORK, "uk_meta.json")))
rows_u = np.arange(um["H"]) + 0.5 + um["y0"]
area_u = np.repeat(t.cell_area_km2(rows_u, 9)[:, None].astype(np.float32), um["W"], axis=1)
gbr = lu & (cou == CODES.index("GBR") + 1)
irl = lu & (cou == CODES.index("IRL") + 1)
uk_lost = cum_by_code(cu, area_u, gbr & (eu >= 0))
uk_lost_b0 = cum_by_code(cu, area_u, gbr & (eu < 0))
ie_lost = cum_by_code(cu, area_u, irl & (eu >= 0))
uk_below0 = gbr & (eu < 0) & (cu == K0 + 1)
R["uk"] = dict(land_km2=float(area_u[gbr].sum()), lost_km2=[float(uk_lost[j]) for j in POS], lost_below0_km2=[float(uk_lost_b0[j]) for j in POS],
               below0_km2=float(area_u[gbr & (eu < 0)].sum()),
               below0_reach_km2=float(area_u[uk_below0].sum()),
               ireland_land_km2=float(area_u[irl].sum()), ireland_lost_km2=[float(ie_lost[j]) for j in POS],
               grid="AWS Terrain Tiles zoom 10 averaged to zoom 9 (about 190 m pixels at 52 N)")
# point heights from the zoom-10 extract
sys.path.insert(0, "/home/claude/hist/within-sight/code")
from dem import DEM
dem = DEM()


def uk_flood_level(lat, lon):
    """Point height (zoom-10, bilinear) and the level at which the modelled sea reaches within one zoom-9 cell."""
    h = dem.elev(lat, lon)
    gx, gy = t.lonlat_to_gpx(lon, lat, 9)
    ix = np.floor(gx - um["x0"]).astype(int); iy = np.floor(gy - um["y0"]).astype(int)
    nb = np.full(len(ix), 255)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            yy = np.clip(iy + dy, 0, um["H"] - 1); xx = np.clip(ix + dx, 0, um["W"] - 1)
            nb = np.minimum(nb, cu[yy, xx])
    reach = np.where(nb <= K, LV[np.clip(nb - 1, 0, K - 1)], np.inf)
    fl = np.maximum(np.maximum(h, reach), LV[K0])  # nothing floods unless the sea rises above today's level
    return h, fl


def under_counts(fl, w):
    o = np.argsort(fl)
    fs, ws = fl[o], np.cumsum(w[o])
    out = []
    for L in LV[POS]:
        n = np.searchsorted(fs, L + 1e-9, side="right")
        out.append(float(ws[n - 1]) if n > 0 else 0.0)
    return out


O = pd.read_csv(OSN, sep="\t", dtype=str, quoting=3)
O = O[(O.type == "populatedPlace") & O.local_type.isin(["City", "Town"])].copy()
for c in ("lat", "lon", "x", "y"): O[c] = O[c].astype(float)
O = O.drop_duplicates(["name1", "x", "y"])
O["elev_m"], O["flood_level_m"] = uk_flood_level(O.lat.values, O.lon.values)
# Census 2021 populations of 2022 built-up areas (England and Wales), matched to the OS place as in my postbox study
G = json.load(open(os.path.join(D8, "ons_geo.json")))
BU = pd.DataFrame(G["bua22_gb"])[["BUA22CD", "BUA22NM", "LAT", "LONG", "BNG_E", "BNG_N", "Shape__Area"]]
BU["r"] = np.sqrt(BU.Shape__Area / np.pi)
lk = pd.DataFrame(json.load(open(os.path.join(D8, "lsoa21_bua22_lookup.json"))))
pop = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-lsoa.csv"))
pop = pop.rename(columns={"geography code": "LSOA21CD", "Residence type: Total; measures: Value": "pop"})[["LSOA21CD", "pop"]]
lkc = [c for c in lk.columns if c.upper().startswith("LSOA")][0]
lk = lk.rename(columns={lkc: "LSOA21CD"}).merge(pop, on="LSOA21CD", how="left")
BU["pop2021"] = BU.BUA22CD.map(lk.groupby("BUA22CD")["pop"].sum())
BU = BU[BU.pop2021.notna()].reset_index(drop=True)
bt = cKDTree(BU[["BNG_E", "BNG_N"]].values)
dd, ii = bt.query(O[["x", "y"]].values, k=8, distance_upper_bound=40000)
best = np.full(len(O), -1); bestv = np.full(len(O), np.inf)
nm_norm = lambda s: str(s).lower().replace("-", " ").replace("'", "").strip()
for j in range(8):
    ok = np.isfinite(dd[:, j]); jj = np.minimum(ii[:, j], len(BU) - 1)
    v = np.where(ok, dd[:, j] / (BU.r.values[jj] + 150.0), np.inf)
    same = np.array([nm_norm(a) == nm_norm(b) for a, b in zip(O.name1.values, BU.BUA22NM.values[jj])])
    v = np.where(same, v * 0.5, v)  # prefer the built-up area with the same name
    upd = v < bestv; best[upd] = jj[upd]; bestv[upd] = v[upd]
O["bua"] = np.where(bestv <= 1.25, BU.BUA22CD.values[np.maximum(best, 0)], "")
O["bua_name"] = np.where(bestv <= 1.25, BU.BUA22NM.values[np.maximum(best, 0)], "")
O["bua_pop2021"] = np.where(bestv <= 1.25, BU.pop2021.values[np.maximum(best, 0)], np.nan)
O["_v"] = bestv
# one OS place per built-up area carries its population (the closest match)
O = O.sort_values("_v")
dup = O.bua.ne("") & O.duplicated("bua")
O.loc[dup, "bua_pop2021"] = np.nan
O = O.sort_values(["country", "name1"])
uk_t = O[["name1", "local_type", "lat", "lon", "district", "county", "country", "elev_m", "flood_level_m", "bua", "bua_name", "bua_pop2021"]].rename(columns={"name1": "name"})
uk_t.round({"lat": 5, "lon": 5, "elev_m": 1, "flood_level_m": 2}).to_csv(os.path.join(DATA, "uk_towns.csv"), index=False)
fl = O.flood_level_m.values
R["uk_towns"] = dict(n=len(O), n_city=int((O.local_type == "City").sum()), with_pop=int(O.bua_pop2021.notna().sum()),
                     pop_total=float(O.bua_pop2021.sum()),
                     under=under_counts(fl, np.ones(len(O))), under_pop=under_counts(fl, O.bua_pop2021.fillna(0).values))
# MSOA population-weighted centroids (England and Wales)
M = pd.DataFrame(G["msoa21_pwc"])
mp = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-msoa.csv")).rename(columns={"geography code": "MSOA21CD", "Residence type: Total; measures: Value": "pop"})
M = M.merge(mp[["MSOA21CD", "pop"]], on="MSOA21CD")
M["elev_m"], M["flood_level_m"] = uk_flood_level(M._y.values, M._x.values)
R["uk_msoa"] = dict(n=len(M), pop_total=float(M["pop"].sum()), under_pop=under_counts(M.flood_level_m.values, M["pop"].values.astype(float)),
                    under_n=under_counts(M.flood_level_m.values, np.ones(len(M))))
del cu, eu, lu, cou, area_u

# ---------------------------------------------------------------- world cities (GeoNames cities15000)
cols = ["geonameid", "name", "asciiname", "alt", "lat", "lon", "fclass", "fcode", "cc", "cc2", "a1", "a2", "a3", "a4", "pop", "elevation", "dem", "tz", "mod"]
C = pd.read_csv(zipfile.ZipFile("/home/claude/hist/_data13/cities15000.zip").open("cities15000.txt"), sep="\t", header=None, names=cols,
                usecols=["geonameid", "name", "lat", "lon", "fcode", "cc", "pop", "elevation", "dem"], quoting=3, keep_default_na=False, na_values=[""])
C = C[C.lat > -60].reset_index(drop=True)
cw = np.load(os.path.join(WORK, "world_code.npy")); ce = np.load(os.path.join(WORK, "europe_code.npy"))


def nbmin(cgrid, z, x0, y0, lat, lon):
    gx, gy = t.lonlat_to_gpx(lon, lat, z)
    ix = np.floor(gx - x0).astype(int); iy = np.floor(gy - y0).astype(int)
    Hh, Ww = cgrid.shape
    inside = (ix >= 2) & (ix < Ww - 2) & (iy >= 2) & (iy < Hh - 2)
    nb = np.full(len(ix), 255)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nb = np.minimum(nb, cgrid[np.clip(iy + dy, 0, Hh - 1), np.clip(ix + dx, 0, Ww - 1) % Ww])
    return nb, inside


nb_w, _ = nbmin(cw, 4, 0, 0, C.lat.values, C.lon.values)
nb_e, ins = nbmin(ce, 7, 58 * 256, 34 * 256, C.lat.values, C.lon.values)
nb = np.where(ins, nb_e, nb_w)
gx, gy = t.lonlat_to_gpx(C.lon.values, C.lat.values, 4)
wel = np.load(os.path.join(WORK, "world_elev.npy"))[np.clip(gy.astype(int), 0, 4095), np.clip(gx.astype(int), 0, 4095)]
h = C.dem.astype(float).values
h = np.where(h < -1000, np.where(C.elevation.notna(), C.elevation.astype(float), wel), h)  # -9999 = no value
C["height_m"] = h
reach = np.where(nb <= K, LV[np.clip(nb - 1, 0, K - 1)], np.inf)
C["flood_level_m"] = np.maximum(np.maximum(h, reach), LV[K0])
C["grid"] = np.where(ins, "zoom 7", "zoom 4")
C["country"] = C.cc
R["cities"] = dict(n=len(C), pop_total=float(C["pop"].sum()), under_n=under_counts(C.flood_level_m.values, np.ones(len(C))),
                   under_pop=under_counts(C.flood_level_m.values, C["pop"].values.astype(float)),
                   below0=int((C.height_m <= 0).sum()),
                   under_n_b0=under_counts(np.where(C.height_m <= 0, C.flood_level_m.values, np.inf), np.ones(len(C))),
                   under_pop_b0=under_counts(np.where(C.height_m <= 0, C.flood_level_m.values, np.inf), C['pop'].values.astype(float)))
C[["geonameid", "name", "country", "lat", "lon", "pop", "height_m", "flood_level_m", "grid"]].round({"lat": 4, "lon": 4, "flood_level_m": 2}).to_csv(
    os.path.join(DATA, "cities_world.csv"), index=False)
del cw, ce, wel

# ---------------------------------------------------------------- tables per level
LVp = LV[POS]
dfw = pd.DataFrame(dict(level_m=LV, world_land_lost_km2=np.round(R["world"]["lost_km2"]), world_land_already_below0_reached_km2=np.round(R["world"]["lost_below0_km2"]), world_seabed_exposed_km2=np.round(R["world"]["gained_km2"]),
                        doggerland_land_km2=np.round(R["doggerland"]["land_km2"]), nw_europe_seabed_exposed_km2=np.round(R["europe_window"]["exposed_km2"])))
cu_n = dict(zip(LVp, R["cities"]["under_n"])); cu_p = dict(zip(LVp, R["cities"]["under_pop"]))
dfw["cities_under"] = [int(cu_n.get(L, 0)) for L in LV]; dfw["cities_under_pop"] = [int(cu_p.get(L, 0)) for L in LV]
dfw.to_csv(os.path.join(DATA, "levels_world.csv"), index=False)
dfu = pd.DataFrame(dict(level_m=LVp, uk_land_lost_km2=np.round(R["uk"]["lost_km2"], 1), uk_land_already_below0_reached_km2=np.round(R["uk"]["lost_below0_km2"], 1), ireland_land_lost_km2=np.round(R["uk"]["ireland_lost_km2"], 1),
                        uk_towns_under=np.array(R["uk_towns"]["under"]).astype(int), uk_towns_under_bua_pop=np.array(R["uk_towns"]["under_pop"]).astype(int),
                        ew_msoa_under=np.array(R["uk_msoa"]["under_n"]).astype(int), ew_msoa_under_pop=np.array(R["uk_msoa"]["under_pop"]).astype(int)))
dfu.to_csv(os.path.join(DATA, "levels_uk.csv"), index=False)


# ---------------------------------------------------------------- headline numbers at the marked levels
def at(arr, L, pos=True):
    j = int(np.where(np.isclose(LV, L))[0][0])
    return arr[j - K0] if pos else arr[j]


MARK = [-125, -120, -60, -40, -20, 0.25, 0.5, 0.75, 1.0, 2.0, 7.0, 58.0, 66.0, 70.0]
hl = {}
for L in MARK:
    key = ("m" if L < 0 else "p") + f"{abs(L):g}".replace(".", "_")
    d = dict(level=L)
    if L < 0:
        d.update(world_gained=at(R["world"]["gained_km2"], L, False), dogger=at(R["doggerland"]["land_km2"], L, False))
    else:
        d.update(world_lost=at(R["world"]["lost_km2"], L, False), uk_lost=at(R["uk"]["lost_km2"], L), cities_n=at(R["cities"]["under_n"], L),
                 cities_pop=at(R["cities"]["under_pop"], L), uk_towns=at(R["uk_towns"]["under"], L), uk_towns_pop=at(R["uk_towns"]["under_pop"], L),
                 msoa_pop=at(R["uk_msoa"]["under_pop"], L), world_lost_b0=at(R["world"]["lost_below0_km2"], L, False), uk_lost_b0=at(R["uk"]["lost_below0_km2"], L),
                 cities_n_b0=at(R["cities"]["under_n_b0"], L), cities_pop_b0=at(R["cities"]["under_pop_b0"], L))
        d["world_lost_share"] = d["world_lost"] / today_land; d["uk_lost_share"] = d["uk_lost"] / R["uk"]["land_km2"]
        d["msoa_pop_share"] = d["msoa_pop"] / R["uk_msoa"]["pop_total"]
    hl[key] = d
R["at"] = hl


def topc(L, n=12, minland=20000):
    j = int(np.where(np.isclose(LVp, L))[0][0])
    rr = [dict(a3=r["a3"], name=r["name"], lost=r["lost"][j], share=r["lost"][j] / r["land_km2"]) for r in R["countries"] if r["land_km2"] >= minland]
    return dict(by_area=sorted(rr, key=lambda r: -r["lost"])[:n], by_share=sorted(rr, key=lambda r: -r["share"])[:n])


R["top_countries"] = {f"p{L:g}": topc(L) for L in (1.0, 7.0, 70.0)}
NLD = R["europe_countries"]["NLD"]; jj = lambda L: int(np.where(np.isclose(LVp, L))[0][0])
R["nld"] = {f"p{L:g}": NLD["lost"][jj(L)] / NLD["land_km2"] for L in (1.0, 7.0, 70.0)}
# largest cities under at +7 and +70, and the London story
def topcities(L, n=10):
    s = C[C.flood_level_m <= L + 1e-9].sort_values("pop", ascending=False).head(n)
    return [dict(name=r["name"], cc=r.cc, pop=int(r["pop"]), h=float(r.height_m)) for _, r in s.iterrows()]
R["top_cities"] = {f"p{L:g}": topcities(L) for L in (1.0, 7.0, 70.0)}
lon_row = C[(C.name == "London") & (C.cc == "GB")].iloc[0]
R["london"] = dict(height=float(lon_row.height_m), flood_level=float(lon_row.flood_level_m))
# Britain island moment
R["island"] = dict(gb_continent=R["bridges_europe"][0]["joined_below_m"], ie_gb=R["bridges_europe"][1]["joined_below_m"],
                   gb_continent_z4=R["bridges_world_check"][0]["joined_below_m"], ie_gb_z4=R["bridges_world_check"][1]["joined_below_m"])
# the largest Doggerland figure
R["doggerland"]["max_km2"] = max(R["doggerland"]["land_km2"])
R["meta"] = dict(levels_n=K, cities_src="GeoNames cities15000", retrieved_tiles="28 October 2026")
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), separators=(",", ":"))
print(json.dumps({k: R[k] for k in ("at", "island", "london", "nld")}, indent=0)[:4000])
print("world land", today_land, "uk land", R["uk"]["land_km2"], "ireland", R["uk"]["ireland_land_km2"], "below0", R["world"]["below0_reach_km2"], R["uk"]["below0_reach_km2"])
print(R["top_countries"]["p7"]["by_area"][:3])
