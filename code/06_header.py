"""Step 6. header.png, the 1200 x 630 social card, drawn with matplotlib from the page grids.
Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf.
Run: FONT_DIR=/path/to/fonts python3 code/06_header.py
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import render as rd

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
BG, FG, MUT, SEA, HOT, SAND = "#F3F0E6", "#13242C", "#5B6869", "#1F5F7A", "#C8492F", "#B98F3A"

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
w = rd.window("europe", -10.8, 60.9, 2.2, 49.8)
for i, (L, lab, col) in enumerate([(-125, "−125 m", SAND), (0, "today", SEA), (70, "+70 m", HOT)]):
    ax = fig.add_axes([0.505 + i * 0.163, 0.08, 0.16, 0.84]); ax.imshow(rd.render("europe", L, *w, step=2), interpolation="lanczos"); ax.axis("off")
    ax.text(0.5, -0.045, lab, transform=ax.transAxes, ha="center", va="top", family="IBM Plex Mono", fontsize=13, color=col, weight="medium")
fig.text(0.045, 0.86, "DATA STUDY  ·  SEA LEVEL", family="IBM Plex Mono", fontsize=12, color=MUT)
fig.text(0.04, 0.80, "Drowned", fontproperties=DISP, fontsize=60, color=SEA, va="top")
fig.text(0.04, 0.63, "and rising", fontproperties=DISP, fontsize=60, color=HOT, va="top")
fig.text(0.045, 0.40, "Britain and the world at every sea level,\nfrom the Ice Age to all ice melted.\n"
         f"In the model Britain becomes an island at {R['island']['gb_continent']:+.0f} m;\nat +70 m, {R['at']['p70']['uk_lost_share'] * 100:.0f}% of the UK is under water.".replace("-", "−"),
         family="Source Serif 4", fontsize=17, color=FG, va="top", linespacing=1.35)
fig.text(0.045, 0.06, "Dr Tristan Hotham · Independent researcher", family="IBM Plex Mono", fontsize=11.5, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
print("header.png")
