# Asmari exploratory GIS revision

This revision replaces the original custom extraction workflow with standard native QGIS/GDAL toolbox algorithms, visual interpretation inputs and a graphical processing model. The full private delivery has a portable QGIS project, source data, GeoPackages, rasters, 16 maps, a 13-page Persian report, a 6-page manual and two CC BY scientific papers. Persian documents use Mikhak.

The seven criteria are lithology, fault proximity, interpreted watercourse proximity, slope, topographic lineament proximity, geometric lineament-intersection proximity and elevation. Fourteen generalized watercourse candidates and ten valley-alignment candidates were read visually; six ridge/contact-like alignments were excluded. Only three unique interior geometric intersections remain. These are not verified fractures or well sites.

The model uses 33 built-in native/GDAL algorithms. It does not use D8, Hough extraction, custom Python analysis algorithms or AHP. It was executed through the QGIS processing engine; manual mouse-based ArcGIS execution is not claimed. The manual provides GUI reproduction steps and ArcGIS equivalents. Image-reading vertices were entered as recorded data, not extracted automatically.

All seven weights and rating tables are explicit assumptions. The seven-criterion scenario has weights 25/10/10/10/20/20/5 percent. The four-criterion comparison uses 50/20/20/10 percent. This comparison changes both inputs and weights; it is not a one-at-a-time sensitivity experiment. About 70.38 percent of valid cells change class. Both scenarios remain unvalidated against wells or springs, and no drilling location is proposed.

## Validation

- EPSG:32639, 30 m grid, 527 by 538 cells; 255,284 valid index cells.
- Seven-criterion index approximately 1.10 to 4.45.
- All vectors are inside the analysis mask; intersection pairs are distinct and nonduplicate, and crossings are not endpoint-only.
- Model providers restricted to native and GDAL.
- Portable project checked after relocation: 26 valid layers and 16 layouts, with no workspace-absolute paths in the project.
- Final report and manual rendered and visually checked: 13 and 6 pages.
- Four-control affine map registration has 76.5 m control-fit RMSE, assumed WGS84 datum, and no independent check points. Fit residual is not independent positional accuracy.

Full-resolution source scans, editable client vectors and interpreted feature coordinate tables are withheld from this public review subset. The report includes a reduced source-map excerpt with attribution; separate public map files are derived thematic outputs. The full data bundle was delivered separately. The old four-factor model file in this directory is retained as a historical intermediate; use `Asmari_seven_criteria.model3` for the current workflow.

## References

- Arulbalaji, P., Padmalal, D., Sreelash, K. (2019). Scientific Reports 9,2082. https://doi.org/10.1038/s41598-019-38567-x
- Ahmadi, H., Pekkan, E. (2021). Geosciences 11(5),183. https://doi.org/10.3390/geosciences11050183
- QGIS model designer and vector-overlay documentation; Esri Euclidean Distance, Line Density and Flow Direction documentation. Full bibliography and sources appear in the report. Referencing AHP or D8 documentation does not mean those methods were performed here.
