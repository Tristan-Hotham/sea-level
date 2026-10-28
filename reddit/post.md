## Title

[OC] Britain at every sea level, from the Ice Age (−120 m) to all ice melted (+70 m): in a simple bathtub model Britain's last land link to Europe goes under at −30 m, and at +70 m a third of the UK's land and 60% of the people of England and Wales would be under water

## Body (optional)

I built a bathtub model on open global elevation and sea-floor data: set the sea to any level and flood everything lower that the ocean can reach. At the Ice Age low, almost all of the southern North Sea (about 341,000 km²) is dry land, Doggerland. Using today's seabed, Ireland parts from Britain at −38 m and Britain from Europe at −30 m. At +7 m, roughly Greenland's ice, 61 UK town centres are under water. At +70 m, 33% of UK land goes but 60% of people in England and Wales live where the sea would reach: people live lower than the land.

Caveat: no defences, tides or land movement, coarse elevation, and levels are not dates. It is not a flood map.

Interactive version, with a slider and play button: https://tristan-hotham.github.io/sea-level/

## Source comment

Source: elevation and sea-floor depth from AWS Terrain Tiles (Mapzen/Tilezen terrarium tiles, built from ETOPO1, GMTED2010, SRTM, EU-DEM and other sources; zoom 7, about 700 m cells, on the maps, and a zoom-10 extract averaged to about 190 m for UK figures); coast from Natural Earth 1:10m (public domain); UK towns from OS Open Names (contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0); people from ONS Census 2021 TS001 with MSOA population-weighted centroids (Open Government Licence v3.0); Ice Age and Doggerland context from Wikipedia, "Doggerland" and "Last Glacial Maximum" (CC BY-SA 4.0); ice-sheet figures from Wikipedia, "Greenland ice sheet", and BedMachine Antarctica (Morlighem et al. 2020).

Tools: Python (NumPy, SciPy for connected-region flooding, pandas, Pillow, shapely, matplotlib).

Interactive: https://tristan-hotham.github.io/sea-level/
Blog post: https://blog.tristanhotham.com/2026/10/28/sea-level/
Paper: https://doi.org/10.5281/zenodo.23732578
