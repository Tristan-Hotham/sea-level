"""Step 7. Static figures for the paper (release/paper/f_*.png, 200 dpi, white) and blog (release/blog/b_*.png, 1520 px wide).
Maps are rendered from the published page grids with code/render.py (no web tiles); numbers from data/results.json.
Run: FONT_DIR=/path/to/fonts python3 code/07_figures.py
"""
import json, os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import render as rd

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
plt.rcParams["font.family"] = "IBM Plex Mono"
plt.rcParams["axes.unicode_minus"] = True
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
LV = np.array(R["levels"]); K0 = R["k0"]; POS = LV > 0
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
FG, MUT, RULE, SEA, HOT, SAND, VIO = "#13242C", "#5B6869", "#D5CFBD", "#1F5F7A", "#C8492F", "#B98F3A", "#7D5BA6"
BLOGBG = "#F3F0E6"
mfmt = lambda v: ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):g}"


def style(ax, grid="y"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(MUT); ax.spines["bottom"].set_color(MUT)
    ax.tick_params(colors=FG, length=0, labelsize=11)
    if grid: ax.grid(axis=grid, color=RULE, lw=.8); ax.set_axisbelow(True)


def save(fig, name, blog):
    if blog: fig.savefig(os.path.join(BO, f"b_{name}.png"), dpi=160, facecolor=BLOGBG)
    else: fig.savefig(os.path.join(PO, f"f_{name}.png"), dpi=200, facecolor="white")
    plt.close(fig)


def bg(blog):
    plt.rcParams["axes.facecolor"] = BLOGBG if blog else "white"
    return BLOGBG if blog else "white"


KEY = [Patch(fc="#C6D1A8", label="land today"), Patch(fc="#E07A5C", label="land drowned"), Patch(fc="#9B7BC0", label="already below sea level, drowned"),
       Patch(fc="#E8D49C", label="sea floor exposed"), Patch(fc="#8CC3C4", label="shallow sea"), Patch(fc="#2C5F82", label="deep sea")]


def fig_britain(blog):
    levels = [-125, R["island"]["gb_continent"], 0, 7, 70]
    labs = ["Ice Age low", "Britain an island\n(in the model)", "today", "Greenland's ice", "all ice"]
    w = rd.window("europe", -11, 61.0, 9.5, 49.5)
    fig = plt.figure(figsize=(9.5, 3.9) if blog else (10, 4.1), facecolor=bg(blog))
    for i, (L, lab) in enumerate(zip(levels, labs)):
        ax = fig.add_axes([0.005 + i * 0.199, 0.22, 0.195, 0.68]); ax.imshow(rd.render("europe", L, *w, step=2), interpolation="lanczos"); ax.axis("off")
        ax.set_title(f"{mfmt(L)} m", fontsize=14, color=FG, weight="medium", pad=4)
        ax.text(0.5, -0.03, lab, transform=ax.transAxes, ha="center", va="top", fontsize=10.5, color=MUT)
    fig.legend(handles=KEY, loc="lower center", ncol=6 if not blog else 3, frameon=False, fontsize=9.5, handlelength=1.2, columnspacing=1.0)
    save(fig, "britain", blog)


def fig_world(blog):
    rows = rd.window("world", -180, 78, 180, -58)
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 10.2) if blog else (9, 9.7), facecolor=bg(blog))
    for ax, L, t in zip(axs, (-125, 70), ("Ice Age low, −125 m", "All ice melted, +70 m")):
        ax.imshow(rd.render("world", L, *rows, step=2), interpolation="lanczos"); ax.axis("off")
        ax.set_title(t, fontsize=14, color=FG, weight="medium", loc="left")
    fig.legend(handles=KEY, loc="lower center", ncol=3, frameon=False, fontsize=10, handlelength=1.2)
    fig.subplots_adjust(left=.01, right=.99, top=.96, bottom=.08, hspace=.1)
    save(fig, "world", blog)


def fig_curves(blog):
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.5, 4.6) if blog else (10, 4.4), facecolor=bg(blog))
    g = np.array(R["world"]["gained_km2"]); l = np.array(R["world"]["lost_km2"]); lb = np.array(R["world"]["lost_below0_km2"])
    y = np.where(LV < 0, g, -l) / 1e6; yb = np.where(LV < 0, g, -(l + lb)) / 1e6
    a.plot(LV, yb, color=VIO, lw=2, label="counting land already\nbelow sea level")
    a.plot(LV, y, color=HOT, lw=2.4, label="land change")
    a.axhline(0, color=MUT, lw=.8); a.axvline(0, color=MUT, lw=.8, ls=":")
    a.set_xlabel("sea level (m)", color=MUT); a.set_ylabel("million km² vs today", color=MUT)
    a.legend(frameon=False, fontsize=9.5, loc="upper right"); style(a)
    a.set_title("World, outside Antarctica", fontsize=12.5, color=FG, loc="left")
    xs = LV[POS]
    b.plot(xs, np.array(R["uk"]["lost_km2"]) / R["uk"]["land_km2"] * 100, color=HOT, lw=2.4, label="UK land drowned")
    b.plot(xs, np.array(R["uk_msoa"]["under_pop"]) / R["uk_msoa"]["pop_total"] * 100, color=SEA, lw=2.4, label="people, England and Wales")
    b.plot(xs, np.array(R["uk_towns"]["under"]) / R["uk_towns"]["n"] * 100, color=SAND, lw=2, ls="--", label="UK towns and cities")
    b.set_xlabel("sea level (m)", color=MUT); b.set_ylabel("% under water", color=MUT); b.set_xlim(0, 70); b.set_ylim(0, 65)
    b.legend(frameon=False, fontsize=9.5, loc="upper left"); style(b)
    b.set_title("United Kingdom", fontsize=12.5, color=FG, loc="left")
    fig.tight_layout()
    save(fig, "curves", blog)


def fig_dogger(blog):
    fig, ax = plt.subplots(figsize=(9.5, 4.6) if blog else (9, 4.2), facecolor=bg(blog))
    m = LV <= 0
    ax.fill_between(LV[m], np.array(R["doggerland"]["land_km2"])[m] / 1000, color=SAND, alpha=.35, lw=0)
    ax.plot(LV[m], np.array(R["doggerland"]["land_km2"])[m] / 1000, color=SAND, lw=2.6)
    for v, t, dy in [(R["island"]["gb_continent"], "Britain's last land link\ngoes under", 150), (R["island"]["ie_gb"], "Ireland parts\nfrom Britain", 230),
                     (R["dogger_bank"]["sea_from_m"], "Dogger Bank\ngoes under", 300)]:
        ax.axvline(v, color=FG, lw=.8, ls=":")
        ax.text(v + 1, dy, f"{mfmt(v)} m: {t}", fontsize=9.5, color=FG, va="top")
    ax.set_xlim(-130, 0); ax.set_ylim(0, 360)
    ax.set_xlabel("sea level (m)", color=MUT); ax.set_ylabel("dry land in the box (thousand km²)", color=MUT); style(ax)
    fig.tight_layout(); save(fig, "dogger", blog)


def fig_bridges(blog):
    rows = [(b["name"], b["joined_below_m"], "700 m grid") for b in R["bridges_europe"]] + [(b["name"], b["joined_below_m"], "10 km grid") for b in R["bridges_world"]]
    rows = sorted(rows, key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(9.5, 4.8) if blog else (9, 4.4), facecolor=bg(blog))
    for i, (n, v, g) in enumerate(rows):
        ax.plot([v, 0], [i, i], color=RULE, lw=2)
        ax.scatter([v], [i], s=70, color=SEA if g.startswith("700") else SAND, zorder=3, edgecolor=FG, lw=.6)
        ax.text(v - 1.5, i, f"{mfmt(v)} m", ha="right", va="center", fontsize=10, color=FG)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=10.5)
    ax.set_xlim(-70, 1); ax.set_xlabel("joined by land when the sea is at or below (m)", color=MUT); style(ax, "x")
    ax.legend(handles=[Patch(fc=SEA, label="zoom 7 (about 700 m)"), Patch(fc=SAND, label="zoom 4 (about 10 km)")], frameon=False, fontsize=9.5, loc="upper left")
    fig.tight_layout(); save(fig, "bridges", blog)


def fig_cities(blog):
    xs = LV[POS]
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.5, 4.4) if blog else (10, 4.2), facecolor=bg(blog))
    a.plot(xs, np.array(R["cities"]["under_pop"]) / 1e9, color=HOT, lw=2.4); a.set_ylabel("billion people", color=MUT)
    a.set_title("People in cities over 15,000\nwhose centre is under water", fontsize=11.5, color=FG, loc="left")
    b.plot(xs, R["cities"]["under_n"], color=SEA, lw=2.4); b.set_ylabel("cities", color=MUT)
    b.set_title("Number of those cities\n(of " + f"{R['cities']['n']:,})", fontsize=11.5, color=FG, loc="left")
    for ax in (a, b):
        ax.set_xlim(0, 70); ax.set_xlabel("sea level (m)", color=MUT); style(ax)
    a.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:,.1f}"))
    b.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    fig.tight_layout(); save(fig, "cities", blog)


for blog in (False, True):
    fig_britain(blog); fig_world(blog); fig_curves(blog); fig_dogger(blog); fig_bridges(blog); fig_cities(blog)
print("figures written")
