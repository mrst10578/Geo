#!/usr/bin/env python3
"""Prepare a reproducible, explicitly preliminary groundwater-potential GIS study."""
from pathlib import Path
import json, math, gzip
import numpy as np, cv2, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.features import geometry_mask, shapes
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer
from scipy.ndimage import median_filter, gaussian_filter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/source/geological_map_1966.jpg"
DEM=ROOT/"data/raw/N31E049.hgt"
OUT=ROOT/"outputs"
(OUT/"rasters").mkdir(parents=True,exist_ok=True)
(OUT/"vectors").mkdir(parents=True,exist_ok=True)
(OUT/"meta").mkdir(parents=True,exist_ok=True)
(OUT/"maps").mkdir(parents=True,exist_ok=True)
(OUT/"report").mkdir(parents=True,exist_ok=True)

# SIFT tie points found by matching the user's study-area photograph
# against an explicitly indexed region of the supplied geological map.
H_roi=np.loadtxt(ROOT/"match_H.txt")
T=np.array([[1900/1200,0,2600],[0,2000/1263,2700],[0,0,1]])
H=T@H_roi
raw_corners=np.array([[99,43],[1057,43],[1057,921],[99,921]],dtype=np.float32).reshape(-1,1,2)
full_corners=cv2.perspectiveTransform(raw_corners,H).reshape((-1,2))
# Linear first-order scan georeferencing from labelled map-frame graticule.
# Accuracy is approximate, not survey-grade; see limitations in report.
frame={"lon_left":49.5,"lon_right":50.0,"lat_top":32.0,"lat_bottom":31.5,
       "left_px":550.0,"right_px":4260.0,"top_px":440.0,"bottom_px":4780.0}
def pix2ll(x,y):
  lon=49.5+(np.asarray(x)-550.0)/(4260.0-550.0)*0.5
  lat=32.0-(np.asarray(y)-440.0)/(4780.0-440.0)*0.5
  return lon,lat
ll=np.column_stack(pix2ll(full_corners[:,0],full_corners[:,1]))
to_utm=Transformer.from_crs("EPSG:4326","EPSG:32639",always_xy=True)
to_ll=Transformer.from_crs("EPSG:32639","EPSG:4326",always_xy=True)
utm_poly=Polygon([to_utm.transform(float(x),float(y)) for x,y in ll])
if not utm_poly.is_valid: utm_poly=utm_poly.buffer(0)
assert utm_poly.is_valid and utm_poly.area>20e6
xmin,ymin,xmax,ymax=utm_poly.bounds
res=30.0;pad=2000
left=np.floor((xmin-pad)/res)*res;top=np.ceil((ymax+pad)/res)*res
right=np.ceil((xmax+pad)/res)*res;bottom=np.floor((ymin-pad)/res)*res
w=round((right-left)/res);h=round((top-bottom)/res)
transform=from_origin(left,top,res,res)
print("ROI full map pixels",np.round(full_corners).astype(int).tolist())
print("ROI lat lon",ll.tolist())
print("Area km2",round(utm_poly.area/1e6,2),"grid",w,h)
with rasterio.open(DEM) as src:
  z=np.full((h,w),-9999,dtype="float32")
  reproject(source=rasterio.band(src,1),destination=z,
    src_transform=src.transform,src_crs=src.crs,
    dst_transform=transform,dst_crs="EPSG:32639",
    dst_nodata=-9999,resampling=Resampling.bilinear)
assert np.isfinite(z).all()
assert np.count_nonzero((z>-100)&(z<8000)) > 0.99*z.size, "DEM tile incomplete"
roi=geometry_mask([mapping(utm_poly)],out_shape=(h,w),transform=transform,invert=True)
print("Elevation range",np.percentile(z[z>0],[1,50,99]))
profile=dict(driver="GTiff",height=h,width=w,count=1,crs="EPSG:32639",
             transform=transform,compress="deflate",predictor=2,tiled=True)
def save(name,arr,dtype=None,nodata=None):
 p=OUT/"rasters"/f"{name}.tif"
 kw=profile.copy()
 if dtype is None:dtype=str(arr.dtype)
 kw["dtype"]=dtype
 if nodata is not None:kw["nodata"]=nodata
 with rasterio.open(p,"w",**kw) as dst:dst.write(arr.astype(dtype),1)
 return p
save("dem_elevation",np.where(roi,z,-9999).astype("float32"),nodata=-9999)
save("study_area_mask",roi.astype("uint8"))
# Colored geological map resampled onto 30 m UTM grid.
I=cv2.imread(str(SRC))
yy,xx=np.mgrid[0:h,0:w]
xutm=left+(xx+.5)*res; yutm=top-(yy+.5)*res
lon,lat=to_ll.transform(xutm,yutm)
px=550+(lon-49.5)/.5*(4260-550)
py=440+(32-lat)/.5*(4780-440)
B=cv2.remap(I,px.astype("float32"),py.astype("float32"),
    interpolation=cv2.INTER_AREA,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
save("geological_scan_rgb",np.zeros((h,w),dtype="uint8")) # replaced by a RGB 3-band GeoTIFF below
(OUT/"rasters"/"geological_scan_rgb.tif").unlink()
with rasterio.open(OUT/"rasters"/"geological_scan_rgb.tif","w",**{**profile,"count":3,"dtype":"uint8","photometric":"RGB"}) as dst:
 for k in range(3):dst.write(B[:,:,2-k],k+1)
# Legend color anchors sampled at interior of actual 1966 map legend swatches,
# not generic synthetic colors. Selected units require visual review.
classes=[
 (1,"Q","آبرفت و نهشته‌های جوان",(250,250,249),5),
 (2,"Tk","کنگلومرای جوان توکک",(253,252,218),4),
 (3,"Bk","سازند بختیاری",(255,244,103),4),
 (4,"Aj","عضو لهبری از سازند آغاجاری",(245,152,89),2),
 (5,"Mn","سازند میشان",(217,156,194),2),
 (6,"Gs","سازند گچساران",(224,202,181),1),
 (7,"As","سازند آسماری",(161,173,70),4),
 (8,"Pd","سازند پابده",(199,218,172),2),
 (9,"Gu","سازند گورپی",(231,250,251),2),
 (10,"Il-Sv","سازندهای ایلام و سروک",(137,205,248),3),
 (11,"Kz","سازند کژدمی",(92,163,218),2),
 (12,"Dr-Fa","سازندهای داریان و فهلیان",(166,136,190),3),
]
clab=cv2.cvtColor(np.array([[x[3] for x in classes]],dtype="uint8"),cv2.COLOR_RGB2LAB)[0].astype(float)
blab=cv2.cvtColor(cv2.GaussianBlur(B,(9,9),0),cv2.COLOR_BGR2LAB).astype(float)
ids=np.zeros((h,w),dtype="uint8")
score=np.full((h,w),100000.,dtype=np.float32)
for k,anchor in enumerate(clab):
 v=((blab-anchor)**2).sum(axis=2)
 ids[v<score]=k+1
 score=np.minimum(score,v)
ids=median_filter(ids,size=5)
ids[~roi]=0
save("lithology_classes",ids,dtype="uint8",nodata=0)
v=np.zeros((h,w),dtype="uint8")
for idx,abbr,name,color,weight in classes:v[ids==idx]=weight
save("lithology_rating",v)
meta={"date":"2026-11-06","map_source":"Kuh-e Asmari, Iranian Oil Operating Companies, Geological Compilation Map, 1:100,000, 1966, sheet 20825 E",
"dem_source":"Mapzen Skadi elevation-tiles-prod SRTM-derived HGT, N31E049, approximate 30 m",
"analysis_crs":"EPSG:32639","dem_resolution_m":30,"grid_height":h,"grid_width":w,
"roi_area_km2":round(utm_poly.area/1e6,3),
"full_map_pixel_control_points":frame,"image_matching":dict(H_crop_to_full=H.tolist(),corners_full_px=full_corners.tolist()),
"roi_polygon_lon_lat":ll.tolist(),"roi_bbox_lon_lat":[float(min(ll[:,0])),float(min(ll[:,1])),float(max(ll[:,0])),float(max(ll[:,1]))],
"lithology_classes":[dict(id=i,code=c,name_fa=n,rgb=col,rating=s) for i,c,n,col,s in classes],
"limitations":["Map scan tied to printed graticule approximately, not surveyed GCPs.",
"Rock units automatically classified from scanned map colors; check against original legend before formal use.",
"DEM/lineament and faults do not validate aquifer productivity or drilling depth."]}
(OUT/"meta"/"study_metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2))
with (OUT/"vectors"/"study_area.geojson").open("w") as f:
 json.dump({"type":"FeatureCollection","features":[{"type":"Feature","geometry":mapping(Polygon(ll)),"properties":{"name":"Study area","crs":"EPSG:4326","source":"Black frame in Telegram detail map"}}]},f,ensure_ascii=False)
# Optional polygonized lithology units for desktop GIS: discard tiny scan speckles.
features=[]
for geom,val in shapes(ids,mask=roi,transform=transform):
 idx=int(val)
 if idx==0:continue
 shp=shape(geom)
 if shp.area<9000: continue
 gg=shp_transform(to_ll.transform,shp.simplify(22,preserve_topology=True))
 d=classes[idx-1]
 features.append({"type":"Feature","geometry":mapping(gg),"properties":{"unit":d[1],"name_fa":d[2],"suitability":d[4],"area_m2":round(shp.area)}})
with (OUT/"vectors"/"lithology_interpreted.geojson").open("w") as f:json.dump({"type":"FeatureCollection","features":features},f,ensure_ascii=False)
print("Lithology classes",[(x[1],int(np.sum(ids==x[0]))) for x in classes])
print("Saved interpreted lithology polygons",len(features))