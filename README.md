# Drowned and rising: Britain and the world at every sea level

A sea-level slider from the depth of the last Ice Age (−130 m) to a world with no ice left (+70 m). A simple, openly documented bathtub model floods every place below the chosen level that the ocean can reach, and the page redraws the map of the world or of Britain and the North Sea, with live numbers: land gained and lost, Doggerland's area, famous land bridges, UK towns and people below the line, and cities worldwide.

**Interactive version:** https://tristan-hotham.github.io/sea-level/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23732578

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

**This is a bathtub model, not a flood map.** It has no defences, tides, storms or land movement, and its elevation is coarse (about 10 km for the world, 700 m around Britain, 190 m for UK numbers). It says nothing reliable about any single street or house.

## Headline results

- At the Ice Age low (−125 m) the model exposes 19.4 million km² of sea floor outside Antarctica, 14% of today's 137.3 million km² of land in the grid. The southern North Sea box (51° to 57.5° N, 3° W to 9° E) is 340,713 km² of dry land at most, almost all of its 341,416 km².
- Using today's seabed, Britain's last land link to the continent goes under at −30 m (−29 m on the 10 km grid), and Ireland's link to Britain at −38 m. A point on the Dogger Bank goes under at −22 m. Other land bridges on the 10 km grid: Taiwan −56 m, Beringia −43 m, Borneo and the Malay Peninsula −35 m, Tasmania −23 m, New Guinea and Australia −5 m, Sri Lanka −1 m.
- At +1 m (the top of the IPCC AR6 likely range for 2100 under very high emissions) the UK grid drowns 275 km² of land above today's sea level plus 574 km² that it already places below sea level; no OS town centre is reached until between +1.5 and +2 m. The world grid stores whole metres, so its sub-metre figures are not meaningful.
- At +7 m (about the Greenland ice sheet): 10,509 km² of the UK (4.3%), 61 of 1,426 OS towns and cities, and 2,645,000 people in England and Wales (4.4%, by MSOA centroid). Worldwide 1.50 million km² (1.1%) and 1,877 cities over 15,000 people with 234 million people.
- At +70 m (about all land ice): 33% of the UK's land and 60% of the people of England and Wales; 39% of Ireland; 10.2% of the world's land outside Antarctica (14.0 million km², plus 2.17 million km² already below sea level) and 12,857 cities with 1.91 billion people. Among countries with at least 20,000 km² of land: Netherlands 96%, Denmark 94%, Bangladesh 90%.
- The UK's people live lower than its land: at +20 m, 19% of England and Wales residents but 11% of UK land are under water.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page: slider, play button, world and Britain views, live numbers, land bridges, charts, country and city tables, place search. The map is drawn in the browser from the grids in `data/`; when zoomed in it also fetches finer AWS Terrain Tiles if the browser allows. |
| `header.png` | Social card (1200 by 630). |
| `data/world_code.png`, `data/europe_code.png` | The drowning code of each cell (zoom 4 world, 4,096 by 4,096; zoom 7 Britain and North Sea window): the first level on the ladder at which the cell is sea, 255 if still land at +70 m. |
| `data/world_relief.png`, `data/europe_relief.png` | Hill shading (3 bits), height class (4 bits) and Caspian lake flag, at lower resolution, for colouring. |
| `data/grids.json`, `data/levels.json` | Grid positions and the level ladder (216 levels). |
| `data/levels_world.csv` | World land drowned and sea floor exposed (outside Antarctica), Doggerland dry land, cities and city population under water, at every level. |
| `data/levels_uk.csv` | UK and Ireland land drowned, UK towns and people (England and Wales) under water, at every positive level. |
| `data/countries_lost.csv` | Land drowned by country (Natural Earth admin-0) at every positive level, zoom-4 grid. |
| `data/land_bridges.csv` | The level at which each pair of places is joined by land. |
| `data/cities_world.csv` | GeoNames cities over 15,000 people with point height and the modelled level at which the sea reaches them. |
| `data/uk_towns.csv` | OS Open Names cities and towns with point height, modelled level, matched 2022 built-up area and its Census 2021 population. |
| `data/cities_page.json`, `data/uk_towns_page.json`, `data/coast.json` | Compact copies for the page; simplified Natural Earth coastline. |
| `data/results.json` | Every number used anywhere. |
| `code/terrain.py`, `code/render.py` | Helpers: decode terrarium tiles and project; render the map at any level from the published grids. |
| `code/01_grids.py` | Builds the world and Britain bathtub grids (connectivity flooding at every level). |
| `code/02_uk_grid.py` | Builds the 190 m UK and Ireland grid from the zoom-10 extract. |
| `code/03_analyse.py` | All statistics: areas, land bridges, cities, towns, people; writes `data/results.json` and the tables. |
| `code/04_page_data.py` | Writes the page grids, coastline and place lists. |
| `code/05_build_site.py` | Fills `code/page_template.html` to make `index.html` and checks facts stated in words. |
| `code/06_header.py`, `code/07_figures.py` | Header card and static figures. |
| `code/08_paper.py`, `code/09_release.py` | Paper PDF, blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Elevation.** AWS Terrain Tiles (terrarium encoding, land and sea floor): zoom 4 for the world, zoom 7 for 16.9° W to 16.9° E and about 45° to 65° N, and a zoom-10 extract for Britain and Ireland averaged to zoom 9.
- **Today's coast.** Natural Earth 1:10m land. Today's ocean cells are capped at −1 m; the Caspian Sea is a lake.
- **Flooding.** At each of 216 levels (1 m steps; 0.25 m between −2 and +3 m), a cell is sea if below the level and 8-connected to the ocean through cells below it. At or below 0 m today's land stays land; at or above 0 m today's sea stays sea. Land with a model height below 0 m is reported separately.
- **Areas.** Web-mercator cell areas by latitude; world figures exclude south of 60° S.
- **Places.** Under water when the point height is below the level and the modelled sea reaches within one cell (world cities: GeoNames point heights, 10 km or 700 m cells; UK places and MSOA centroids: zoom-10 heights, 190 m cells).
- **Land bridges.** Highest level at or below 0 m at which two places are joined by 4-connected land.

## Known limits

- No tides, storms, waves, defences, rivers, groundwater or land movement (no glacial isostatic adjustment or subsidence), no change to the seabed, and a flat sea surface.
- Coarse and mixed elevation sources; interpolated sea-floor depths; coastal cells that average land and sea; whole-metre heights on the world grid.
- Levels are not dates: today's seabed is not the seabed of the past.
- Population covers England and Wales only (MSOA centroids). Town and city tests use one central point each.
- The live terrain in the browser is fetched from the public AWS bucket and recoloured with the same rules, using the coarse grid to decide whether the sea can reach each fine pixel; it is a visual enhancement, not used for any number.

## How to rerun

Inputs are read in place: `terrarium_tiles.json.gz` and `cities15000.zip` (folder in `D13`), the zoom-10 extract `hist_dem_z10.bin` with its index, Natural Earth GeoJSON (`NE`), OS Open Names (`osnames_gb.tsv`), and the ONS geography and Census 2021 files. `code/03_analyse.py` reads point heights with the `dem.py` reader from https://github.com/Tristan-Hotham/within-sight.

```
python3 code/01_grids.py
python3 code/02_uk_grid.py
python3 code/03_analyse.py
python3 code/04_page_data.py
python3 code/05_build_site.py
FONT_DIR=path/to/fonts python3 code/06_header.py
FONT_DIR=path/to/fonts python3 code/07_figures.py
python3 code/08_paper.py
python3 code/09_release.py
FONT_DIR=path/to/fonts python3 reddit/collage.py
```

Needs Python 3 with numpy, scipy, pandas, Pillow, shapely and matplotlib, and xelatex with TeX Gyre Pagella and Inter for the paper. The temporary grids go in `work/` (about 300 MB, not published).

## Sources and licences

- Elevation and sea-floor depth: AWS Terrain Tiles, https://registry.opendata.aws/terrain-tiles/ (Mapzen and Tilezen). Contributing sources as listed at https://github.com/tilezen/joerd/blob/master/docs/attribution.md, including ETOPO1 (NOAA), GMTED2010 (USGS), SRTM (NASA), EU-DEM (produced using Copernicus data and information funded by the European Union), and data.gov.uk Environment Agency LIDAR (Open Government Licence).
- Coast and countries: Natural Earth 1:10m (public domain).
- World cities: GeoNames cities15000 (CC BY 4.0).
- UK places: OS Open Names, contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0).
- Census 2021 TS001, MSOA population-weighted centroids, 2022 built-up areas and lookups: Office for National Statistics (Open Government Licence v3.0).
- Sea-level history and projections (labels only): IPCC AR6 WG I (2021) and Synthesis Report (2023); Wikipedia "Doggerland", "Last Glacial Maximum", "Greenland ice sheet" (CC BY-SA 4.0); BedMachine Antarctica, Morlighem et al. (2020), Nature Geoscience 13.
- Map library: Leaflet 1.9.4.

Derived data: CC BY 4.0 with the credits above. Text and figures: CC BY 4.0. Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) Drowned and Rising: A Bathtub Model of Britain and the World from the Last Glacial Maximum to an Ice-Free Earth. Zenodo. https://doi.org/10.5281/zenodo.23732578

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
