"""Step 8. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Sea_Level.tex and compile it with xelatex (figures from step 7).
Run: python3 code/08_paper.py
"""
import json, os, re, shutil, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Sea_Level"
LV = R["levels"]; K0 = R["k0"]
pi = lambda L: LV.index(float(L)) - K0  # index into per-positive-level arrays

# derived values
R["gain_vs_land"] = R["at"]["m125"]["world_gained"] / R["world"]["land_km2"]
R["world_land_m"] = f"{R['world']['land_km2'] / 1e6:.1f}"
R["doggerland"]["box"]["lon0_abs"] = abs(R["doggerland"]["box"]["lon0"])
R["uk20_pop"] = R["uk_msoa"]["under_pop"][pi(20)] / R["uk_msoa"]["pop_total"]
R["uk20_land"] = R["uk"]["lost_km2"][pi(20)] / R["uk"]["land_km2"]
R["ie70"] = R["uk"]["ireland_lost_km2"][pi(70)] / R["uk"]["ireland_land_km2"]
# facts stated in words
dl = dict(zip(LV, R["doggerland"]["land_km2"]))
assert (dl[-50.0] - dl[-20.0]) > 0.5 * (dl[-125.0] - dl[-20.0])  # "most of that change happens between about -50 and -20 m"
assert R["at"]["p1"]["uk_towns"] == 0 and R["at"]["p2"]["uk_towns"] > 0 and R["uk_towns"]["under"][pi(1.5)] == 0
assert R["at"]["p0_25"]["world_lost"] == R["at"]["p1"]["world_lost"]
assert [r["a3"] for r in R["top_countries"]["p70"]["by_area"][:3]] == ["RUS", "BRA", "USA"]
assert [r["a3"] for r in R["top_countries"]["p70"]["by_share"][:3]] == ["NLD", "DNK", "BGD"]
assert [r["a3"] for r in R["top_countries"]["p7"]["by_share"][:3]] == ["NLD", "BGD", "VNM"]
assert R["uk20_pop"] > R["uk20_land"] and R["at"]["p70"]["msoa_pop_share"] > 0.5
assert R["island"]["ie_gb"] < R["island"]["gb_continent"]
assert dl[R["island"]["gb_continent"]] < 0.5 * R["doggerland"]["sea_km2"]  # most of the box under water when Britain becomes an island


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def sg(v):
    s = f"{abs(v):g}"
    return ("+" if v > 0 else "$-$" if v < 0 else "") + s


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "sg": return sg(v)
    if f == "mkm": return f"{v / 1e6:.1f}"
    if f == "mkm2": return f"{v / 1e6:.2f}"
    if f == "mn": return f"{round(v / 1e6):,}"
    if f == "bn": return f"{v / 1e9:.2f}"
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


z4 = {b["name"]: b["joined_below_m"] for b in R["bridges_world_check"]}
brow = [(b["name"], f"{b['a']} and {b['b']}", sg(b["joined_below_m"]), sg(z4[b["name"]])) for b in R["bridges_europe"]] + \
       [(b["name"], f"{b['a']} and {b['b']}", "", sg(b["joined_below_m"])) for b in R["bridges_world"]]
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Land bridges on today's seabed: the highest sea level (m) at which the two places are joined by land, "
      "on the 700 m grid (zoom 7) and the 10 km grid (zoom 4).}\\label{tab:bridges}\\begin{tabular}{llrr}\\toprule Link & Places tested & 700 m & 10 km\\\\\\midrule\n" +
      "".join(f"{tex(a)} & {tex(b)} & {c} & {d}\\\\\n" for a, b, c, d in brow) + "\\bottomrule\\end{tabular}\\end{table}")
LAB = {125: "Ice Age low", 60: "", 40: "", 20: "", 1: "2100, top of AR6 likely range", 2: "", 7: "Greenland's ice", 58: "Antarctica's ice", 70: "all ice"}
rows = ""
for key in ["m125", "m60", "m20", "p1", "p2", "p7", "p58", "p70"]:
    a = R["at"][key]; L = a["level"]
    if L < 0:
        rows += f"{sg(L)} & {LAB.get(abs(int(L)), '')} & +{a['world_gained'] / 1e6:.2f} & {a['dogger']:,.0f} & & & & \\\\\n"
    else:
        rows += (f"{sg(L)} & {LAB.get(int(L), '')} & $-${a['world_lost'] / 1e6:.2f} & & {a['uk_lost_share'] * 100:.1f} & {int(a['uk_towns'])} & {a['msoa_pop_share'] * 100:.1f} & {a['cities_pop'] / 1e6:,.0f}\\\\\n")
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{The model at marked sea levels. World: change in land outside Antarctica, million km\\textsuperscript{2} "
      "(land the model already puts below sea level excluded). Dogger: dry land in the Doggerland box, km\\textsuperscript{2}. UK land: \\% drowned. Towns: OS Open Names "
      f"cities and towns (of {R['uk_towns']['n']:,}) with the centre under water. E\\&W people: \\% of residents whose MSOA centroid is under water. Cities: millions of people in GeoNames cities over 15,000 whose centre is under water.}}"
      "\\label{tab:levels}\\begin{tabular}{rlrrrrrr}\\toprule Level & & World & Dogger & UK land & Towns & E\\&W people & Cities\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_BRIDGES}}", TB).replace("{{TABLE_LEVELS}}", TL)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
