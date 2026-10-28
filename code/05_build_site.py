"""Step 5. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json (plus a few values derived from it
below), so the page cannot drift from the analysis. Facts the template states in words are checked here. A slim copy of
the per-level results is embedded; the map grids, coastline, cities and towns are fetched from data/.
Run: python3 code/05_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
GR = json.load(open(os.path.join(ROOT, "data", "grids.json")))
tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()

# derived values used in the text
R["gain_vs_land"] = R["at"]["m125"]["world_gained"] / R["world"]["land_km2"]
R["island"]["gb_continent_abs"] = abs(R["island"]["gb_continent"])
R["doggerland"]["box"]["lon0_abs"] = abs(R["doggerland"]["box"]["lon0"])


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def signed(v):
    s = f"{abs(v):g}"
    return ("+" if v > 0 else "−" if v < 0 else "") + s


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "kk": return f"{round(v / 1000):,}k"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "signed": return signed(v)
    if f == "mkm": return f"{v / 1e6:.1f}"
    if f == "mn": return f"{round(v / 1e6):,}"
    if f == "bn": return f"{v / 1e9:.2f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


# facts stated in words in the template
A = R["at"]
assert R["doggerland"]["max_km2"] > 0.99 * R["doggerland"]["sea_km2"]  # "almost all of the box"
assert R["dogger_bank"]["sea_from_m"] < A["m20"]["level"]  # the Dogger Bank is under water at -20 m
assert R["levels"][5] == -125 and R["levels"][0] == -130
NLD = R["nld"]["p70"]
SH = {r["a3"]: r["share"] for r in R["top_countries"]["p70"]["by_share"]}
assert 0.86 <= SH["DNK"] <= 0.95 and 0.86 <= SH["BGD"] <= 0.95  # "Denmark and Bangladesh lose about nine tenths"
assert R["island"]["ie_gb"] < R["island"]["gb_continent"]  # Ireland parts from Britain earlier (at a lower sea)
assert A["p70"]["uk_lost_share"] > 0.3 and A["p70"]["uk_lost_share"] < 0.36  # "a third of the UK's land" (meta description)
uk_london = [r for r in R["top_cities"]["p70"]]
assert R["london"]["flood_level"] < 70  # "a new coast through London"


def slim():
    K0 = R["k0"]
    r0 = lambda a: [round(x) for x in a]
    br = [dict(name=b["name"], at=b["joined_below_m"]) for b in R["bridges_europe"] + R["bridges_world"]]
    return dict(levels=R["levels"], k0=K0,
                world=dict(land=round(R["world"]["land_km2"]), gained=r0(R["world"]["gained_km2"]), lost=r0(R["world"]["lost_km2"]), lost_b0=r0(R["world"]["lost_below0_km2"])),
                doggerland=dict(land=r0(R["doggerland"]["land_km2"]), sea=round(R["doggerland"]["sea_km2"]), box=R["doggerland"]["box"]),
                europe=dict(exposed=r0(R["europe_window"]["exposed_km2"])),
                uk=dict(land=round(R["uk"]["land_km2"]), lost=r0(R["uk"]["lost_km2"]), lost_b0=r0(R["uk"]["lost_below0_km2"]), below0=round(R["uk"]["below0_km2"])),
                uk_towns=dict(n=R["uk_towns"]["n"], under=r0(R["uk_towns"]["under"])),
                msoa=dict(pop_total=round(R["uk_msoa"]["pop_total"]), under_pop=r0(R["uk_msoa"]["under_pop"])),
                cities=dict(n=R["cities"]["n"], under_n=r0(R["cities"]["under_n"]), under_pop=r0(R["cities"]["under_pop"])),
                bridges=br, island=R["island"],
                countries=[dict(a3=c["a3"], name=c["name"], land=round(c["land_km2"]), lost=r0(c["lost"])) for c in R["countries"] if c["land_km2"] >= 20000])


if __name__ == "__main__":
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    html = html.replace("/*RESULTS*/", json.dumps(slim(), ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*GRIDS*/", json.dumps(GR, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    for bad in ("—", "–"):
        assert bad not in js, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
