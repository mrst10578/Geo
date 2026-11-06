#!/usr/bin/env python3
"""Basic reproducibility, integrity, and cross-layer spatial sanity checks."""
from pathlib import Path
import json,hashlib
import numpy as np,rasterio
from shapely.geometry import shape,Point
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';R=OUT/'rasters';V=OUT/'vectors'
results=json.loads((OUT/'meta/analysis_results.json').read_text())
assert sum(results['weights_percent'].values())==100
check=['lithology_classes','fault_trace_candidates','drainage_network','slope_deg',
       'lineaments_dem','intersection_points','dem_elevation',
       'groundwater_potential_index','groundwater_potential_5classes']
matrices={}
crs=None;xf=None
for name in check:
 p=R/(name+'.tif')
 assert p.exists() and p.stat().st_size>100
 with rasterio.open(p) as src:
  if crs is None:crs=src.crs;xf=src.transform;shape_hw=(src.height,src.width)
  assert src.crs==crs and src.transform==xf and (src.height,src.width)==shape_hw
  matrices[name]=src.read(1)
assert str(crs)=='EPSG:32639'
mask,= [rasterio.open(R/'study_area_mask.tif').read(1).astype(bool)]
assert np.all(matrices['groundwater_potential_5classes'][~mask]==0)
assert all(np.any(matrices['groundwater_potential_5classes'][mask]==x) for x in range(1,6))
assert np.isfinite(matrices['groundwater_potential_index'][mask]).all()
assert np.all((matrices['groundwater_potential_index'][mask]>=1)&(matrices['groundwater_potential_index'][mask]<=5))
area=json.loads((V/'study_area.geojson').read_text())['features'][0]
candidate=json.loads((V/'proposed_well.geojson').read_text())['features'][0]
assert shape(area['geometry']).contains(shape(candidate['geometry']))
pidx=results['candidate']['potential_index_1_5']
assert pidx>1 and pidx<=5
maps=list((OUT/'maps').glob('0[1-9]_*.png'));assert len(maps)==9
report=OUT/'report/Geo_University_Report_FA.pdf'
atlas=OUT/'report/Geo_Maps_Atlas_FA.pdf'
pages=len(pymupdf.open(report));atlas_pages=len(pymupdf.open(atlas))
assert pages>=14 and atlas_pages==9
assert all(f.exists() and f.stat().st_size>100_000 for f in (report,atlas))
manifest=[]
publish=[ROOT/'requirements.txt',ROOT/'run_all.sh',ROOT/'data/README.md']
publish.extend(sorted((ROOT/'scripts').glob('*.py')))
publish.extend(sorted((OUT/'maps').glob('*.png')))
publish.extend(sorted((OUT/'maps').glob('*.jpg')))
publish.extend(sorted((OUT/'rasters').glob('*.tif')))
publish.extend(sorted((OUT/'vectors').glob('*.geojson')))
publish.extend(sorted((OUT/'meta').glob('*.json')))
publish.extend([report,atlas])
publish=[p for p in publish if 'geological_scan_rgb.tif' not in str(p)]
for p in publish:
 b=p.read_bytes()
 manifest.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
state={'status':'PASS','crs':str(crs),'resolution_m':30,
 'study_area_km2':json.loads((OUT/'meta/study_metadata.json').read_text())['roi_area_km2'],
 'total_output_maps':len(maps),'report_pages':pages,'atlas_pages':atlas_pages,
 'vector_counts':{p.stem:len(json.loads(p.read_text())['features']) for p in V.glob('*.geojson')},
 'publish_manifest':manifest,'disclaimer':'Provisional classroom modeling; visually validate map interpretation and control points.'}
(OUT/'meta/quality_audit.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
(ROOT/'SHA256SUMS.txt').write_text(''.join(row['sha256']+'  '+row['path']+'\n' for row in manifest))
print('QA PASS, maps=',len(maps),'report pages=',pages,'atlas pages=',atlas_pages,
      'publish items=',len(publish),'candidate=',results['candidate'])