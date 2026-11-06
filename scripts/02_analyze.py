#!/usr/bin/env python3
"""DEM-derived drainage, structural screening and auditable weighted overlay."""
from pathlib import Path
import json,math,collections
import numpy as np,cv2,rasterio
from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation,median_filter
from scipy.ndimage import label as cc_label
from skimage.morphology import skeletonize,remove_small_objects
from shapely.geometry import LineString,Point,Polygon,mapping,shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer
from rasterio.features import geometry_mask,rasterize
import pyflwdir

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';R=OUT/'rasters';V=OUT/'vectors'
meta=json.loads((OUT/'meta/study_metadata.json').read_text())
to_utm=Transformer.from_crs('EPSG:4326','EPSG:32639',always_xy=True)
to_ll=Transformer.from_crs('EPSG:32639','EPSG:4326',always_xy=True)
poly=Polygon([to_utm.transform(*q) for q in meta['roi_polygon_lon_lat']])
with rasterio.open(R/'study_area_mask.tif') as ds:
 roi=ds.read(1).astype(bool);trans=ds.transform;crs=ds.crs
with rasterio.open(R/'lithology_classes.tif') as ds: lith=ds.read(1)
with rasterio.open(R/'lithology_rating.tif') as ds: lith_score=ds.read(1).astype('float32')
with rasterio.open(ROOT/'data/raw/N31E049.hgt') as src:
 from rasterio.warp import reproject,Resampling
 dem=np.full(roi.shape,-9999,dtype='float32')
 reproject(source=rasterio.band(src,1),destination=dem,src_transform=src.transform,
  src_crs=src.crs,dst_transform=trans,dst_crs=crs,dst_nodata=-9999,resampling=Resampling.bilinear)
H,W=dem.shape;resolution=abs(trans.a)
def save(name,data,nodata=None):
 kwargs=dict(driver='GTiff',height=H,width=W,count=1,crs=crs,transform=trans,
             dtype=data.dtype,compress='deflate',tiled=True)
 if nodata is not None:kwargs['nodata']=nodata
 with rasterio.open(R/(name+'.tif'),'w',**kwargs) as dst:dst.write(data,1)
def fx(col):return trans.c+(col+.5)*resolution
def fy(row):return trans.f-(row+.5)*resolution
def point_to_ll(row,col):return to_ll.transform(fx(col),fy(row))
def dump(name,features):
 with open(V/(name+'.geojson'),'w') as f:json.dump(dict(type='FeatureCollection',features=features),f,ensure_ascii=False)
def asfeature(geom,props,coord='utm'):
 if coord=='utm':geom=shp_transform(to_ll.transform,geom)
 return dict(type='Feature',geometry=mapping(geom),properties=props)
# Terrain slope (degrees): finite-difference in UTM meters.
dY,dX=np.gradient(gaussian_filter(dem,1),resolution)
slope=np.degrees(np.arctan(np.sqrt(dX*dX+dY*dY))).astype('float32')
save('slope_deg',np.where(roi,slope,-9999).astype('float32'),-9999)
# D8 drainage accumulation from DEM on buffered study area.
flow=pyflwdir.from_dem(dem,nodata=-9999,outlets='edge')
acc=flow.upstream_area(unit='cell').astype('float32')
stream=(acc>=125)&roi
stream=remove_small_objects(stream,min_size=8)
save('flow_accumulation_cells',np.where(roi,acc,-9999).astype('float32'),-9999)
save('drainage_network',stream.astype('uint8'))
# Extract line chains from 1-pixel skeleton; no invented vector flow paths.
def skeleton_chains(mask,min_m=90):
 sk=skeletonize(mask).astype(np.uint8)
 pix={(int(r),int(c)) for r,c in np.argwhere(sk)}
 around=[(dy,dx) for dy in (-1,0,1) for dx in (-1,0,1) if (dy,dx)!=(0,0)]
 def adj(p):
  y,x=p
  return [q for dy,dx in around if (q:=(y+dy,x+dx)) in pix]
 deg={p:len(adj(p)) for p in pix}
 terminals=[p for p in pix if deg[p]!=2]
 seen=set(); chains=[]
 for p in terminals+list(pix):
  for q in adj(p):
   edge=tuple(sorted((p,q)))
   if edge in seen:continue
   seen.add(edge);chain=[p,q];prev=p;cur=q
   while deg[cur]==2:
    nxt=[n for n in adj(cur) if n!=prev]
    if not nxt:break
    n=nxt[0];edge=tuple(sorted((cur,n)))
    if edge in seen:break
    seen.add(edge);chain.append(n);prev,cur=cur,n
   if len(chain)*resolution>=min_m:
    chains.append(LineString([(fx(col),fy(row)) for row,col in chain]))
 return chains
channels=skeleton_chains(stream,min_m=180)
dump('drainage_streams',[asfeature(g,{'id':i+1,'source':'DEM D8 accumulation; threshold 125 cells','length_m':round(g.length)}) for i,g in enumerate(channels)])
print('DEM drainage: stream pixels',stream.sum(),'lines',len(channels))
# Geological-map graphic structural marks: red strokes, with known anticline-axis
# contamination; these MUST be interpreted as candidates for manual validation.
source=cv2.imread(str(ROOT/'data/source/geological_map_1966.jpg'))
x0,y0,x1,y1=map(int,[min(q[0] for q in meta['image_matching']['corners_full_px'])-100,
 min(q[1] for q in meta['image_matching']['corners_full_px'])-100,
 max(q[0] for q in meta['image_matching']['corners_full_px'])+100,
 max(q[1] for q in meta['image_matching']['corners_full_px'])+100])
x0=max(x0,0);y0=max(y0,0);x1=min(x1,source.shape[1]);y1=min(y1,source.shape[0])
crop=source[y0:y1,x0:x1,:]
B,G,RR=cv2.split(crop)
red=((RR.astype(float)>110)&(RR.astype(float)>G.astype(float)*1.38)&
     (RR.astype(float)>B.astype(float)*1.18)&(G<156)&(B<160)).astype('uint8')*255
red=cv2.morphologyEx(red,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
lines=cv2.HoughLinesP(red,1,np.pi/360,threshold=31,minLineLength=42,maxLineGap=13)
faults=[]
if lines is not None:
 for ix,l in enumerate(lines.reshape(-1,4)):
  xA,yA,xB,yB=map(int,l)
  def geo(x,y):
   xp=x+x0;yp=y+y0
   lon=49.5+(xp-550)/(4260-550)*.5
   lat=32-(yp-440)/(4780-440)*.5
   return to_utm.transform(lon,lat)
  g=LineString([geo(xA,yA),geo(xB,yB)])
  clipped=g.intersection(poly)
  if clipped.is_empty:continue
  geoms=list(clipped.geoms) if hasattr(clipped,'geoms') else [clipped]
  for gg in geoms:
   if gg.geom_type=='LineString' and gg.length>350:faults.append(gg)
# Deduplicate very close Hough detections using midpoint spacing
faults.sort(key=lambda g:g.length,reverse=True)
kept=[]
for f in faults:
 if len(kept)>=120:break
 if not any(f.hausdorff_distance(g)<160 for g in kept):kept.append(f)
faults=kept
dump('fault_traces_candidates',[asfeature(g,{'id':i+1,'source':'1966 red structural graphics; fault/axis differentiation requires manual check','status':'candidate','length_m':round(g.length)}) for i,g in enumerate(faults)])
print('Geology red stroke candidates',len(faults))
fault_r=rasterize([(f,1) for f in faults],out_shape=roi.shape,transform=trans,dtype='uint8')>0 if faults else np.zeros_like(roi)
save('fault_trace_candidates',fault_r.astype('uint8'))
# DEM multiazimuth illumination; Hough candidates are geomorphic proxies, not proven faults.
z=gaussian_filter(dem.astype('float32'),sigma=2.2)
gy,gx=np.gradient(z,resolution)
lines_raw=[]
for az in [45,135,225,315]:
 azr=np.deg2rad(az);shade=-gx*np.cos(azr)-gy*np.sin(azr)
 shade=(255*(shade-np.percentile(shade,3))/max(0.001,np.percentile(shade,97)-np.percentile(shade,3)))
 shade=np.uint8(np.clip(shade,0,255))
 edges=cv2.Canny(shade,45,105)
 linesh=cv2.HoughLinesP(edges,1,np.pi/180,threshold=42,minLineLength=23,maxLineGap=6)
 if linesh is None:continue
 for ln in linesh.reshape(-1,4):
  xx0,yy0,xx1,yy1=map(int,ln)
  g=LineString([(fx(xx0),fy(yy0)),(fx(xx1),fy(yy1))])
  if g.length>660 and g.intersects(poly):lines_raw.append(g)
lines_raw.sort(key=lambda g:g.length,reverse=True)
lines_utm=[]
for l in lines_raw:
 if len(lines_utm)>=240:break
 if any(l.hausdorff_distance(k)<220 for k in lines_utm):continue
 intr=l.intersection(poly)
 if intr.geom_type=='LineString' and intr.length>500:lines_utm.append(intr)
print('DEM lineaments',len(lines_utm))
dump('lineaments_dem_candidates',[asfeature(g,{'id':i+1,'method':'multi-azimuth DEM hillshade + Hough; manual confirmation required','length_m':round(g.length)}) for i,g in enumerate(lines_utm)])
line_r=rasterize([(f,1) for f in lines_utm],out_shape=roi.shape,transform=trans,dtype='uint8')>0 if lines_utm else np.zeros_like(roi)
save('lineaments_dem',line_r.astype('uint8'))
# Exact projected line intersections with crossing-angle filter, deduplicated by 180 m grid.
intrs={}
def angle(g):
 p0=np.asarray(g.coords[0]);p1=np.asarray(g.coords[-1])
 return math.atan2(*(p1-p0)[::-1])
for i,g in enumerate(lines_utm):
 for k in lines_utm[i+1:]:
  da=abs((angle(g)-angle(k)+math.pi)%(2*math.pi)-math.pi)
  delta=min(da,math.pi-da)
  if delta<math.radians(25):continue
  if not g.bounds[0]<=k.bounds[2] or not k.bounds[0]<=g.bounds[2]:continue
  if not g.bounds[1]<=k.bounds[3] or not k.bounds[1]<=g.bounds[3]:continue
  pt=g.intersection(k)
  if pt.geom_type=='Point' and poly.contains(pt):
   key=(round(pt.x/180),round(pt.y/180))
   intrs.setdefault(key,pt)
points=list(intrs.values())
dump('lineament_intersections',[asfeature(g,{'id':i+1,'method':'crossing of mapped DEM line segments, angle >=25 degrees'}) for i,g in enumerate(points)])
point_r=rasterize([(p,1) for p in points],out_shape=roi.shape,transform=trans,dtype='uint8')>0 if points else np.zeros_like(roi)
save('intersection_points',point_r.astype('uint8'))
print('Lineament intersections',len(points))
# Distances computed in projected CRS at 30m pixel spacing.
def dist(mask):return distance_transform_edt(~mask)*resolution if np.any(mask) else np.full(roi.shape,99999.)
d_fault=dist(fault_r);d_line=dist(line_r);d_stream=dist(stream);d_intr=dist(point_r)
save('distance_fault_m',np.where(roi,d_fault,-9999).astype('float32'),-9999)
save('distance_stream_m',np.where(roi,d_stream,-9999).astype('float32'),-9999)
save('distance_lineament_m',np.where(roi,d_line,-9999).astype('float32'),-9999)
save('distance_intersection_m',np.where(roi,d_intr,-9999).astype('float32'),-9999)
# Seven transparent 1-5 suitability ratings.
s_slope=np.select([slope<4,slope<8,slope<15,slope<25],[5,4,3,2],default=1).astype('uint8')
s_dr=np.select([d_stream<120,d_stream<750,d_stream<1500,d_stream<2800],[2,5,4,3],default=2).astype('uint8')
s_fault=np.select([d_fault<160,d_fault<700,d_fault<1400,d_fault<2400],[2,5,4,3],default=2).astype('uint8') if faults else np.full(roi.shape,3,dtype='uint8')
s_line=np.select([d_line<150,d_line<750,d_line<1500,d_line<3000],[4,5,4,3],default=2).astype('uint8') if lines_utm else np.full(roi.shape,3,dtype='uint8')
s_intr=np.select([d_intr<180,d_intr<750,d_intr<1400,d_intr<2700],[3,5,4,3],default=2).astype('uint8') if points else np.full(roi.shape,3,dtype='uint8')
q=np.percentile(dem[roi],[20,40,60,80])
s_ele=np.digitize(dem,q,right=True)
s_ele=(5-s_ele).astype('uint8')
ratings=dict(lithology=lith_score.astype('uint8'),fault=s_fault,drainage=s_dr,slope=s_slope,
             lineament=s_line,intersection=s_intr,elevation=s_ele)
weights=dict(lithology=25,fault=10,drainage=10,slope=10,lineament=20,intersection=20,elevation=5)
assert sum(weights.values())==100
for key,arr in ratings.items():save('rating_'+key,np.where(roi,arr,0).astype('uint8'),0)
potential=sum(weights[k]*ratings[k].astype('float32') for k in weights)/100.
potential[~roi]=-9999
save('groundwater_potential_index',potential.astype('float32'),-9999)
breaks=np.percentile(potential[roi],[20,40,60,80])
classes=np.digitize(potential,breaks,right=True)+1
classes[~roi]=0
save('groundwater_potential_5classes',classes.astype('uint8'),0)
# Candidate deliberately avoids drainage bed, uncertain mapped fault, and AOI edge.
from scipy.ndimage import gaussian_filter
distance_to_roi_edge=distance_transform_edt(roi)*resolution
candidate_mask=roi & (slope<8)&(d_stream>250)&(distance_to_roi_edge>400)&np.isin(lith,[1,2,3,7])
if faults:candidate_mask &= d_fault>150
if candidate_mask.sum()<20:
 candidate_mask=roi & (slope<12)&(d_stream>120)&(distance_to_roi_edge>200)
if candidate_mask.sum()<10:raise RuntimeError('No defensible candidate under even relaxed preliminary screening')
blur=gaussian_filter(np.where(roi,np.maximum(potential,0),0),sigma=2.3)
cy,cx=np.unravel_index(np.argmax(np.where(candidate_mask,blur,-1)),blur.shape)
X,Y=fx(cx),fy(cy);lon,lat=to_ll.transform(X,Y)
cand=dict(utm_zone='39N',utm_crs='EPSG:32639',utm_easting_m=round(X,1),utm_northing_m=round(Y,1),
 lon=round(lon,7),lat=round(lat,7),potential_index_1_5=round(float(potential[cy,cx]),3),
 relative_class=int(classes[cy,cx]),elevation_m=round(float(dem[cy,cx]),1),
 slope_deg=round(float(slope[cy,cx]),2),lithology_code=meta['lithology_classes'][int(lith[cy,cx])-1]['code'],
 distance_to_stream_m=round(float(d_stream[cy,cx])),
 distance_to_structural_red_trace_m=round(float(d_fault[cy,cx])) if faults else None,
 lineament_distance_m=round(float(d_line[cy,cx])) if lines_utm else None,
 lineament_intersection_distance_m=round(float(d_intr[cy,cx])) if points else None,
 status='Academic screening point only; not a drilling authorization')
dump('proposed_well',[{'type':'Feature','geometry':mapping(Point(lon,lat)),'properties':cand}])
np.save(OUT/'meta/candidate_grid_row_col.npy',np.array([cy,cx],dtype='int32'))
analysis=dict(weights_percent=weights,score_ranges={k:dict(min=int(np.min(v[roi])),max=int(np.max(v[roi]))) for k,v in ratings.items()},
 potential_quantile_breaks=[float(v) for v in breaks],
 potential_min=float(np.min(potential[roi])),potential_max=float(np.max(potential[roi])),
 candidate=cand,drainage_threshold_cells=125,
 fault_candidate_segments=len(faults),lineament_candidate_segments=len(lines_utm),
 lineament_intersection_points=len(points),
 data_quality='Preliminary classroom map-based multi-criteria screening; no well logs, water table, pumping tests or geophysical confirmation')
(OUT/'meta'/'analysis_results.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2))
print(json.dumps(analysis,ensure_ascii=False,indent=2))