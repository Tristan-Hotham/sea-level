"""Step 9. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/09_release.py
"""
import importlib.util, json, os, re, shutil, zipfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "05_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
# facts stated in words in the blog
U = pd.read_csv(os.path.join(ROOT, "data", "uk_towns.csv"))
fl = dict(zip(U.name, U.flood_level_m))
assert all(fl[n] <= 7 for n in ["Great Yarmouth", "Skegness", "Canvey Island", "Gosport"])
assert all(fl[n] <= 70 for n in ["London", "Kingston upon Hull", "Norwich", "Cambridge", "York", "Cardiff"])
assert R["bridges_world"][0]["name"].startswith("Beringia") and R["bridges_world"][3]["name"].startswith("Sunda")
assert R["nld"]["p70"] > 0.95
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"): assert bad not in vis, bad
os.makedirs(os.path.join(ROOT, "release", "blog"), exist_ok=True)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
A = R["at"]
meta = dict(
    title="Drowned and rising: Britain and the world at every sea level",
    slug="sea-level",
    excerpt=(f"A bathtub model of every sea level from the Ice Age to an ice-free world. In the model Britain becomes an island at {b.signed(R['island']['gb_continent'])} m; "
             f"at +70 m, {A['p70']['uk_lost_share'] * 100:.0f}% of the UK is under water."),
    seo_description=f"Drag the sea from the Ice Age to all ice melted: Doggerland, land bridges, and what +7 m or +70 m would take from Britain and the world.",
    tags=["sea level", "Doggerland", "climate change", "Ice Age", "maps", "Britain", "interactive", "data"],
    header_alt=("Title card reading 'Drowned and rising' in sea blue and coral on pale sand, beside three maps of Britain and the North Sea: at minus 125 m the "
                "North Sea floor is dry sand-coloured land, today's coast in the middle, and at plus 70 m large coral areas of drowned land. Text: Britain and the world "
                f"at every sea level, from the Ice Age to all ice melted. In the model Britain becomes an island at {b.signed(R['island']['gb_continent'])} m; at +70 m, "
                f"{A['p70']['uk_lost_share'] * 100:.0f}% of the UK is under water."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("—", "–", "--"): assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Sea_Level"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$-$", "−").replace("km\\textsuperscript{2}", "km²")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="Drowned and Rising: A Bathtub Model of Britain and the World from the Last Glacial Maximum to an Ice-Free Earth",
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/sea-level/. Data and code: https://github.com/Tristan-Hotham/sea-level. Blog post: to follow.</p>"
                     "<p>Elevation: AWS Terrain Tiles (Mapzen; ETOPO1, GMTED2010, SRTM, EU-DEM and others). Coast: Natural Earth (public domain). Cities: GeoNames (CC BY 4.0). "
                     "Contains OS data © Crown copyright and database right 2026; ONS data (Open Government Licence v3.0).</p>",
    keywords=["sea level", "bathtub model", "Doggerland", "Last Glacial Maximum", "land bridges", "sea-level rise", "ice sheets", "United Kingdom",
              "digital elevation model", "open data"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/sea-level", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/sea-level/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://registry.opendata.aws/terrain-tiles/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://download.geonames.org/export/dump/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://geoportal.statistics.gov.uk", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.nomisweb.co.uk", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/Doggerland", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.ipcc.ch/report/ar6/wg1/", relation="isderivedfrom", resource_type="other"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["levels_world.csv", "levels_uk.csv", "countries_lost.csv", "land_bridges.csv", "cities_world.csv", "uk_towns.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "sea-level_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"sea-level/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"sea-level/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split())
print("release files written; post words:", words)
