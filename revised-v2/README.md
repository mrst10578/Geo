# Asmari revision v2

This revision uses the client-supplied lithology polygons and fault lines with standard QGIS/GDAL processing tools. It is an exploratory **four-factor** result, not the completed seven-factor assignment.

The new report contains map explanations, source attribution and references. The manual guide describes graphical QGIS reproduction and equivalent ArcGIS tools. The model was actually executed automatically with `qgis_process`; no claim is made that ArcGIS or a manual click sequence was used.

## Scope

- Lithology: 31 supplied polygons. The Id-to-formation mapping is a tentative visual match to the supplied map and needs confirmation.
- Faults: 17 supplied polylines. Hydraulic properties and field verification are unavailable.
- Boundary: dissolved lithology footprint, approximately 229.758 square kilometres. The supplied Cadr is an open line and was not used as a raster mask.
- Elevation: Mapzen Skadi N31E049, reprojected to EPSG:32639 at 30 metres.
- Slope: standard GIS slope tool, degrees.
- Fault influence: Euclidean distance, not line density.
- Weighted index: 50% lithology, 20% fault distance, 20% slope, 10% elevation. These are scenario assumptions, not AHP weights.

The output has 255,284 valid cells and scores from approximately 1.2 to 4.9. Five fixed score intervals are used. All analysis rasters share the same grid. No well location from the previous version is carried forward.

## Reproduction

Open `model/Asmari_four_factor.model3` in QGIS Model Designer. Select the supplied `Litologh.shp` and `Fault.shp` and the full Skadi elevation tile. Choose output destinations and run. The source ZIP and scanned maps are not republished in this public repository; restore them locally from the provided project materials. The separately delivered complete package contains these supplied inputs and an editable QGIS project.

The report and guide are in `report/`, maps in `maps/`, and actual native processing records and validation in `model/`. The model contains only standard processing algorithms. No custom analysis script is required to rerun it in the graphical interface.

## Unfinished work

Drainage, lineaments and lineament intersections require an appropriate source, manual interpretation and checking. Georeferencing accuracy and the lithology Id mapping also need confirmation. A fault–drainage intersection must not be labelled a lineament–lineament intersection. The seven-factor result should be produced only after those inputs and weights are reviewed.

Previous `outputs/` and the original scripts are retained as historical material. They do not establish that the revised methodology was performed.
