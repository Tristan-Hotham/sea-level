"""r/dataisbeautiful collage: reddit/britain_at_every_sea_level.png (2400 x 3000), light sea glass and sand.
Maps are rendered from the published page grids (../data/*_code.png, *_relief.png) with ../code/render.py;
every number comes from ../data/results.json. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run from anywhere: FONT_DIR=/path/to/fonts python3 reddit/collage.py
"""
import json, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "code"))
import render as rd

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, SEA, HOT, SAND, VIO = "#E9F1EE", "#13242C", "#4F6062", "#1F5F7A", "#C8492F", "#A87C2A", "#7D5BA6"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
A = R["at"]; LV = np.array(R["levels"]); K0 = R["k0"]
sg = lambda v: ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):g}"

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.975, "Britain at every sea level,", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.045, 0.930, "from the Ice Age to all ice melted", fontproperties=DISP, fontsize=46, color=SEA, va="top")
fig.text(0.045, 0.877, "A bathtub model: set the sea to a level, flood everything lower that the ocean can reach.\n"
         "Today's seabed and land, no defences, no tides. Broad shapes, not a flood map.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.15)

# hero: three maps
w = rd.window("europe", -10.6, 60.95, 5.2, 49.7)
heads = [(-120, "Ice Age low", SAND), (0, "Today", SEA), (70, "All ice melted", HOT)]
img0 = rd.render("europe", 0, *w, step=1)
hfrac = 0.305 * 12 * img0.shape[0] / img0.shape[1] / 15  # keep the map's true proportions
top = 0.80
for i, (L, t, c) in enumerate(heads):
    ax = fig.add_axes([0.03 + i * 0.318, top - hfrac, 0.305, hfrac]); ax.imshow(rd.render("europe", L, *w, step=1), interpolation="lanczos"); ax.axis("off")
    fig.text(0.03 + i * 0.318 + 0.1525, top + 0.004, f"{sg(L)} m", fontproperties=DISP, fontsize=30, color=c, ha="center", va="bottom")
    fig.text(0.03 + i * 0.318 + 0.1525, top - hfrac - 0.008, t, family=MONO, fontsize=13, color=FG, ha="center", va="top", weight="medium")
print("map height", hfrac)
key = [Patch(fc="#C6D1A8", label="land today"), Patch(fc="#E8D49C", label="sea floor exposed"), Patch(fc="#E07A5C", label="land drowned"),
       Patch(fc="#9B7BC0", label="below sea level today, drowned"), Patch(fc="#8CC3C4", label="sea")]
fig.legend(handles=key, loc="upper center", bbox_to_anchor=(0.5, top - hfrac - 0.033), ncol=5, frameon=False, fontsize=10.5, handlelength=1.1, columnspacing=1.1, prop={"family": MONO, "size": 10.5})

# big numbers
nums = [
    (f"{R['doggerland']['max_km2'] / 1000:,.0f}k km²", SAND, f"of southern North Sea floor dry\nat the Ice Age low: Doggerland,\nalmost the whole box"),
    (f"{sg(R['island']['gb_continent'])} m", SEA, f"the sea level at which Britain's\nlast land link to Europe goes\nunder (Ireland's link: {sg(R['island']['ie_gb'])} m)"),
    (f"{int(A['p7']['uk_towns'])} towns", HOT, f"UK town centres under at +7 m,\nGreenland's ice; {A['p7']['uk_lost_share'] * 100:.1f}% of UK\nland drowned"),
    (f"{A['p70']['msoa_pop_share'] * 100:.0f}%", HOT, f"of people in England and Wales\nlive where a +70 m sea would\nreach; {A['p70']['uk_lost_share'] * 100:.0f}% of UK land"),
]
for i, (big, c, txt) in enumerate(nums):
    x = 0.045 + i * 0.237
    fig.text(x, 0.405, big, fontproperties=DISP, fontsize=31, color=c, va="top")
    fig.text(x, 0.362, txt, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.12)

# supporting row: UK curves and Doggerland curve
fig.text(0.045, 0.282, "PEOPLE LIVE LOWER THAN THE LAND", family=MONO, fontsize=11, color=MUT)
a = fig.add_axes([0.075, 0.115, 0.4, 0.15], facecolor=BG)
xs = LV[K0:]
a.plot(xs, np.array(R["uk_msoa"]["under_pop"]) / R["uk_msoa"]["pop_total"] * 100, color=SEA, lw=2.6)
a.plot(xs, np.array(R["uk"]["lost_km2"]) / R["uk"]["land_km2"] * 100, color=HOT, lw=2.6)
a.text(45, 47, "people,\nEngland and Wales", color=SEA, fontsize=10.5, family=MONO, ha="right")
a.text(60, 16, "UK land", color=HOT, fontsize=10.5, family=MONO)
a.set_xlim(0, 70); a.set_ylim(0, 65); a.set_xticks([0, 10, 20, 30, 40, 50, 60, 70]); a.set_xticklabels(["0", "+10", "+20", "+30", "+40", "+50", "+60", "+70 m"])
a.set_yticks([0, 20, 40, 60]); a.set_yticklabels(["0", "20%", "40%", "60%"])
fig.text(0.53, 0.282, "DOGGERLAND DROWNS", family=MONO, fontsize=11, color=MUT)
b = fig.add_axes([0.575, 0.115, 0.39, 0.15], facecolor=BG)
m = LV <= 0
dl = np.array(R["doggerland"]["land_km2"])[m] / 1000
b.fill_between(LV[m], dl, color=SAND, alpha=.35, lw=0); b.plot(LV[m], dl, color=SAND, lw=2.6)
b.axvline(R["island"]["gb_continent"], color=FG, lw=.9, ls=":")
b.text(R["island"]["gb_continent"] + 2, 340, f"Britain an\nisland, {sg(R['island']['gb_continent'])} m", fontsize=10.5, family=MONO, color=FG, ha="left", va="top")
b.set_xlim(-130, 0); b.set_ylim(0, 360); b.set_xticks([-120, -90, -60, -30, 0]); b.set_xticklabels(["−120", "−90", "−60", "−30", "0 m"])
b.set_yticks([0, 100, 200, 300]); b.set_yticklabels(["0", "100k", "200k", "300k km²"])
for ax in (a, b):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(MUT); ax.spines["bottom"].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=10.5, length=0); ax.grid(axis="y", color="#C9D6D2", lw=.8); ax.set_axisbelow(True)
    for lb in ax.get_xticklabels() + ax.get_yticklabels(): lb.set_family(MONO)

fig.text(0.045, 0.072, "Elevation and sea floor: AWS Terrain Tiles (Mapzen; ETOPO1, GMTED2010, SRTM, EU-DEM and others); 700 m cells on the maps,\n"
         "190 m for UK figures. Coast: Natural Earth. Towns: OS Open Names (OS data © Crown copyright 2026). People: ONS Census 2021, by\n"
         "neighbourhood centre, England and Wales (OGL v3). Bathtub model on today's seabed: levels are not dates; no defences, tides or\n"
         "land movement. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.3, color=MUT, va="top", linespacing=1.3)
fig.savefig(os.path.join(HERE, "britain_at_every_sea_level.png"), dpi=200, facecolor=BG)
print("collage written")
