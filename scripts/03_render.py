#!/usr/bin/env python3
"""Publish-ready Persian maps and a compact illustrated report (Mikhak type)."""
from pathlib import Path
import json,math,io,os,zipfile
import numpy as np,rasterio
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm,LightSource
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MaxNLocator
import arabic_reshaper
from bidi.algorithm import get_display
from shapely.geometry import shape
from pyproj import Transformer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import landscape,A4
from reportlab.lib.utils import ImageReader
from PIL import Image,ImageOps,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';R=OUT/'rasters';V=OUT/'vectors'
MAPS=OUT/'maps';MAPS.mkdir(exist_ok=True);REPORT=OUT/'report';REPORT.mkdir(exist_ok=True)
meta=json.loads((OUT/'meta/study_metadata.json').read_text())
result=json.loads((OUT/'meta/analysis_results.json').read_text())
fonts=ROOT/'.fonts'
reg=FontProperties(fname=str(fonts/'Mikhak-Regular.ttf'))
medium=FontProperties(fname=str(fonts/'Mikhak-Medium.ttf'))
semi=FontProperties(fname=str(fonts/'Mikhak-SemiBold.ttf'))
bold=FontProperties(fname=str(fonts/'Mikhak-Bold.ttf'))
def fa(s):return ""
def rd(name):
 with rasterio.open(R/(name+'.tif')) as ds:return ds.read(1),ds.transform
mask,tf=rd('study_area_mask');roi=mask.astype(bool);h,w=roi.shape
extent=[tf.c,tf.c+w*tf.a,tf.f+h*tf.e,tf.f]
dem,_=rd('dem_elevation'); slope,_=rd('slope_deg'); lith,_=rd('lithology_classes')
fault,_=rd('fault_trace_candidates');drain,_=rd('drainage_network')
line,_=rd('lineaments_dem');intr,_=rd('intersection_points')
pot,_=rd('groundwater_potential_index')
classes,_=rd('groundwater_potential_5classes')
latlon=Transformer.from_crs('EPSG:4326','EPSG:32639',always_xy=True)
geoms={}
for key in ('study_area','proposed_well','fault_traces_candidates','drainage_streams','lineaments_dem_candidates','lineament_intersections'):
 try:geoms[key]=json.loads((V/(key+'.geojson')).read_text())['features']
 except Exception:geoms[key]=[]
shaped=np.ma.masked_where(~roi,dem)
terrain=np.where(roi,dem,np.median(dem[roi]))
lo,hi=np.percentile(terrain[roi],[2,98])
intensity=LightSource(azdeg=315,altdeg=45).hillshade(terrain,vert_exag=2.2,dx=30,dy=30)
def rgba_overlay():
 return plt.get_cmap('Greys')(intensity*.25+.56)
def outline(ax):
 for f in geoms['study_area']:
  coords=np.asarray(shape(f['geometry']).exterior.coords)
  xy=np.array([latlon.transform(*p) for p in coords])
  ax.plot(xy[:,0],xy[:,1],color='#111827',lw=2.2,alpha=.95,zorder=16)
def line_geo(ax,key,color,lw=1.7,alpha=.9,limit=None):
 for f in geoms[key][:limit]:
  geom=shape(f['geometry'])
  if geom.geom_type!='LineString':continue
  arr=np.array([latlon.transform(*p) for p in geom.coords])
  ax.plot(arr[:,0],arr[:,1],color=color,lw=lw,alpha=alpha,
          solid_capstyle='round',zorder=6)
def points_geo(ax,key,c='#ca1e36',sz=30):
 ps=[]
 for f in geoms[key]:
  geom=shape(f['geometry'])
  if geom.geom_type=='Point':ps.append(latlon.transform(geom.x,geom.y))
 if ps:
  xs,ys=zip(*ps)
  ax.scatter(xs,ys,s=sz,marker='o',color=c,edgecolors='white',linewidths=.5,zorder=8)
def well(ax):
 cand=result['candidate'];x=cand['utm_easting_m'];y=cand['utm_northing_m']
 ax.scatter([x],[y],s=260,marker='*',c='#f8f8f8',edgecolors='#101d2e',linewidths=2.1,zorder=22)
 ax.scatter([x],[y],s=85,marker='*',c='#ffd844',zorder=23)
def setup(title,subtitle):
 plt.rcParams.update({'figure.facecolor':'#fbfaf7','axes.facecolor':'white',
  'pdf.fonttype':42,'savefig.facecolor':'#fbfaf7'})
 fig=plt.figure(figsize=(12.4,9.2),dpi=160)
 ax=fig.add_axes([.075,.135,.64,.74])
 ax.set_aspect('equal',adjustable='box')
 ax.set_xlim(min(extent[0],extent[1])+1300,max(extent[0],extent[1])-1300)
 ax.set_ylim(min(extent[2],extent[3])+1150,max(extent[2],extent[3])-1150)
 ax.grid(color='#7f8b96',lw=.35,alpha=.35)
 ax.tick_params(axis='both',labelsize=9,colors='#435066')
 ax.set_xlabel('UTM Easting (m)  |  EPSG:32639',fontproperties=reg,fontsize=9,color='#394860',labelpad=9)
 ax.set_ylabel('UTM Northing (m)',fontproperties=reg,fontsize=9,color='#394860',labelpad=7)
 fig.text(.70,.952,fa(title),ha='right',va='center',fontproperties=bold,fontsize=22,color='#1a2a39')
 fig.text(.70,.915,fa(subtitle),ha='right',va='center',fontproperties=reg,fontsize=11,color='#52606e')
 fig.text(.075,.06,fa('پژوهش دانشگاهی | نقشه کوه آسماری ۱:۱۰۰٬۰۰۰ | داده ارتفاعی حدود ۳۰ متر | محدوده مطالعاتی انتخاب‌شده'),
  ha='left',fontproperties=reg,fontsize=8.6,color='#4f5a64')
 fig.text(.075,.03,fa('مختصات تقریبی براساس ژئورفرنس نقشه اسکن‌شده؛ نتایج برای طراحی حفاری واقعی اعتبارسنجی نشده‌اند.'),
  ha='left',fontproperties=reg,fontsize=8.2,color='#8d4851')
 fig.text(.77,.855,fa('راهنمای نقشه'),ha='left',fontproperties=semi,fontsize=13,color='#213445')
 # North marker and simple 2 km scale bar.
 ylim=ax.get_ylim();xlim=ax.get_xlim()
 ax.annotate('N',xy=(xlim[1]-800,ylim[1]-800),xytext=(xlim[1]-800,ylim[1]-2000),
             arrowprops=dict(arrowstyle='-|>',color='#222',lw=1.6),ha='center',va='center',
             fontsize=11,fontweight='bold',color='#222',zorder=20)
 x0=xlim[0]+750;y0=ylim[0]+700
 ax.plot([x0,x0+2000],[y0,y0],color='black',lw=5,zorder=20)
 ax.text(x0+1000,y0+160,'2 km',ha='center',va='bottom',fontsize=9,color='#111',zorder=20)
 return fig,ax
def add_note(fig,items):
 y=.807
 for label,text in items:
  fig.text(.77,y,fa(label),fontproperties=semi,fontsize=10,color='#263b4d',ha='left')
  y-=.033
  for part in text.split('\n'):
   fig.text(.77,y,fa(part),fontproperties=reg,fontsize=8.8,color='#526171',ha='left')
   y-=.033
  y-=.032
def colorbar(fig,im,label):
 cbax=fig.add_axes([.775,.43,.031,.30])
 cb=fig.colorbar(im,cax=cbax)
 cb.ax.tick_params(labelsize=9)
 fig.text(.775,.78,fa(label),fontproperties=reg,fontsize=9,color='#4a596b',ha='left')
def savefig(fig,name):
 path=MAPS/(name+'.png')
 fig.savefig(path,dpi=150,bbox_inches=None,pad_inches=0)
 plt.close(fig)
 print('Created',path.name,path.stat().st_size)
 return path
pics=[]
# 1 LITHOLOGY
fig,ax=setup('نقشه لیتولوژی','تفکیک تفسیری واحدهای سنگی از رنگ‌های نقشه زمین‌شناسی ۱۳۴۵')
palette=[d['rgb'] for d in meta['lithology_classes']]
cmap=ListedColormap([[r/255,g/255,b/255,1] for r,g,b in palette])
img=np.ma.masked_where(lith==0,lith)
ax.imshow(img,extent=extent,origin='upper',cmap=cmap,vmin=1,vmax=12,interpolation='nearest')
outline(ax)
yy=.825
for d in meta['lithology_classes']:
 if int(np.sum(lith==d['id']))<100:continue
 fig.patches.append(Rectangle((.775,yy-.006),.014,.017,transform=fig.transFigure,
  facecolor=np.array(d['rgb'])/255,edgecolor='#747b80',lw=.5))
 fig.text(.794,yy,fa(d['name_fa']),fontsize=9,fontproperties=reg,ha='left',va='center')
 fig.text(.945,yy,d['code'],fontsize=8,fontproperties=medium,ha='right',va='center',color='#606973')
 yy-=.046
fig.text(.77,.13,fa('طبقه‌بندی رنگ‌ها نیازمند بازبینی دستی مرز سازندهاست.'),
 fontproperties=reg,fontsize=8,color='#9f4750')
pics.append(savefig(fig,'01_lithology'))
# 2 FAULT
fig,ax=setup('نقشه ساختارهای گسلی','ردیابی اولیه خطوط ساختاری قرمز روی نقشه زمین‌شناسی')
ax.imshow(intensity,extent=extent,origin='upper',cmap='Greys',alpha=.72)
line_geo(ax,'fault_traces_candidates','#c6263e',lw=2.5,alpha=.85)
outline(ax);add_note(fig,[('تعداد پاره‌خط‌ها',f"{len(geoms['fault_traces_candidates'])}"),('روش','استخراج رنگ و آشکارسازی خط'),('تذکر','محور چین‌ها نیز ممکن است\nبا گسل اشتباه شوند.')])
pics.append(savefig(fig,'02_faults'))
# 3 DRAIN
fig,ax=setup('نقشه شبکه آبراهه','استخراج شبکه زهکشی با مدل جریان D8 از DEM')
ax.imshow(intensity,extent=extent,origin='upper',cmap='Greys',alpha=.7)
ar=np.ma.masked_where(~drain.astype(bool),drain)
ax.imshow(ar,extent=extent,origin='upper',cmap=ListedColormap(['#127bbc']),interpolation='nearest')
line_geo(ax,'drainage_streams','#126c9d',lw=1.4,alpha=.8)
outline(ax)
add_note(fig,[('روش محاسبه','مسیر جریان D8 و انباشت جریان'),('آستانه شبکه','۱۲۵ سلول بالادست'),('تذکر','شبکه استخراج‌شده آبراهه\nدائمی را اثبات نمی‌کند.')])
pics.append(savefig(fig,'03_drainage'))
# 4 SLOPE
fig,ax=setup('نقشه شیب زمین','شیب برحسب درجه، محاسبه‌شده از مدل ارتفاعی رقومی')
p=np.ma.masked_where(~roi,slope)
im=ax.imshow(p,extent=extent,origin='upper',cmap='RdYlGn_r',vmin=0,vmax=min(38,np.percentile(slope[roi],98)))
outline(ax);colorbar(fig,im,'درجه')
add_note(fig,[('شیب کم','مناسب‌تر برای دسترسی و حفاری'),('شیب زیاد','هزینه اجرایی و رواناب بیشتر'),('کاربرد','وزن معیار شیب: ۱۰ درصد')])
pics.append(savefig(fig,'04_slope'))
# 5 LINEAMENT
fig,ax=setup('نقشه خطواره‌ها','خطواره‌های احتمالی بر مبنای سایه‌روشن چندجهته DEM')
ax.imshow(intensity,extent=extent,origin='upper',cmap='Greys',alpha=.77)
line_geo(ax,'lineaments_dem_candidates','#b54c12',lw=1.6,alpha=.83)
outline(ax)
add_note(fig,[('روش','سایه‌روشن چهار جهت و Hough'),('تعداد پاره‌خط‌ها',f"{len(geoms['lineaments_dem_candidates'])}"),('محدودیت','شکل عوارض زمین همیشه معادل\nشکستگی سنگ نیست.')])
pics.append(savefig(fig,'05_lineaments'))
# 6 INTERSECTIONS
fig,ax=setup('تقاطع خطواره‌ها','تقاطع خطواره‌های دارای زاویه عبور دست‌کم ۲۵ درجه')
ax.imshow(intensity,extent=extent,origin='upper',cmap='Greys',alpha=.7)
line_geo(ax,'lineaments_dem_candidates','#888a8f',lw=.75,alpha=.35)
points_geo(ax,'lineament_intersections',c='#bc203f',sz=35)
outline(ax)
add_note(fig,[('نقاط تقاطع',f"{len(geoms['lineament_intersections'])}"),('روش','تقاطع هندسی پاره‌خط‌ها'),('تفسیر','تجمع تقاطع‌ها یک شاخص\nغیرمستقیم شکستگی است.')])
pics.append(savefig(fig,'06_lineament_intersections'))
# 7 ELEVATION
fig,ax=setup('نقشه ارتفاع','ارتفاع سطح زمین برحسب متر از داده HGT')
im=ax.imshow(np.ma.masked_where(~roi,dem),extent=extent,origin='upper',
 cmap='terrain',vmin=np.percentile(dem[roi],2),vmax=np.percentile(dem[roi],98))
outline(ax);colorbar(fig,im,'متر')
add_note(fig,[('کمینه',f"{int(np.min(dem[roi]))} متر"),('بیشینه',f"{int(np.max(dem[roi]))} متر"),('دقت شبکه','حدود ۳۰ متر در افق')])
pics.append(savefig(fig,'07_elevation'))
# 8 POTENTIAL
fig,ax=setup('پتانسیل نسبی آب زیرزمینی','تلفیق وزن‌دار هفت معیار و انتخاب یک نقطه مطالعاتی')
colors=['#a43343','#e58a52','#f5d170','#95b867','#21856d']
mc=ListedColormap(colors)
ax.imshow(np.ma.masked_where(classes==0,classes),extent=extent,origin='upper',
 cmap=mc,vmin=1,vmax=5,interpolation='nearest')
outline(ax);well(ax)
for i,(label,color) in enumerate(zip(['خیلی کم','کم','متوسط','زیاد','خیلی زیاد'],colors)):
 yy=.80-i*.074
 fig.patches.append(Rectangle((.774,yy-.008),.022,.026,transform=fig.transFigure,facecolor=color,edgecolor='white'))
 fig.text(.808,yy,fa(label),fontsize=10,fontproperties=reg,va='center',ha='left')
c=result['candidate']
add_note(fig,[('نقطه پیشنهادی',f"X {c['utm_easting_m']:.0f} / Y {c['utm_northing_m']:.0f}"),
 ('امتیاز نهایی',f"{c['potential_index_1_5']:.2f} / 5"),
 ('محدودیت','پنج کلاس نسبی براساس\nصدک‌های داخل محدوده‌اند.')])
pics.append(savefig(fig,'08_final_potential_and_well'))
# 9 Well candidate zoom context
fig,ax=setup('نقطه پیشنهادی چاه','انتخاب پژوهشی از پهنه دارای امتیاز بالاتر')
ax.imshow(np.ma.masked_where(classes==0,classes),extent=extent,origin='upper',
 cmap=mc,vmin=1,vmax=5,interpolation='nearest')
line_geo(ax,'drainage_streams','#2278b0',lw=1.4)
line_geo(ax,'fault_traces_candidates','#c3263d',lw=1.7,alpha=.7)
outline(ax);well(ax)
ax.set_xlim(c['utm_easting_m']-3600,c['utm_easting_m']+3600)
ax.set_ylim(c['utm_northing_m']-3600,c['utm_northing_m']+3600)
add_note(fig,[('مختصات جغرافیایی',f"{c['lat']:.7f} N\n{c['lon']:.7f} E"),
 ('سیستم UTM',f"Zone 39N | {c['utm_easting_m']:.1f} E\n{c['utm_northing_m']:.1f} N"),
 ('ارتفاع و شیب',f"{c['elevation_m']:.1f} m | {c['slope_deg']:.2f} deg"),
 ('اهمیت','این مکان فقط پیشنهادی است؛\nبرای حفاری نیاز به بررسی میدانی است.')])
pics.append(savefig(fig,'09_well_candidate_detail'))
# 2 x 4 attractive overview (no separate font assets shipped)
thumbs=[Image.open(p).convert('RGB') for p in pics[:8]]
tile_w,tile_h=730,550
board=Image.new('RGB',(2*tile_w+60,4*tile_h+90),(245,246,246))
for j,im in enumerate(thumbs):
 im.thumbnail((tile_w-28,tile_h-28))
 x=30+(j%2)*tile_w+(tile_w-im.width)//2
 y=45+(j//2)*tile_h+(tile_h-im.height)//2
 board.paste(im,(x,y))
board.save(MAPS/'00_overview.jpg',quality=82,optimize=True)

# PDF: A4 landscape, Mikhak typefaces and images with readable captions.
pdfmetrics.registerFont(TTFont('MikhakRegular',str(fonts/'Mikhak-Regular.ttf')))
pdfmetrics.registerFont(TTFont('MikhakMedium',str(fonts/'Mikhak-Medium.ttf')))
pdfmetrics.registerFont(TTFont('MikhakSemi',str(fonts/'Mikhak-SemiBold.ttf')))
pdfmetrics.registerFont(TTFont('MikhakBold',str(fonts/'Mikhak-Bold.ttf')))
PW,PH=landscape(A4)
cv=canvas.Canvas(str(REPORT/'Geo_University_Report_FA.pdf'),pagesize=(PW,PH),pageCompression=1)
cv.setTitle('مطالعه مقدماتی پتانسیل‌یابی آب زیرزمینی محدوده کوه آسماری')
cv.setAuthor('مطالعه دانشگاهی GIS')
def pdf_text(x,y,s,size=12,font='MikhakRegular',color='#24364a'):
 cv.setFillColor(color);cv.setFont(font,size);cv.drawRightString(x,y,fa(s))
def pdf_para(x,y,s,max_width=PW-120,fontsize=11,leading=23,font='MikhakRegular'):
 words=str(s).split(' ');line=''
 for word in words:
  test=(line+' '+word).strip()
  if pdfmetrics.stringWidth(fa(test),font,fontsize)>max_width and line:
   pdf_text(x,y,line,fontsize,font);y-=leading;line=word
  else:line=test
 if line:pdf_text(x,y,line,fontsize,font);y-=leading
 return y
def head(title,num):
 cv.setFillColor('#1b3947');cv.rect(0,PH-75,PW,75,fill=1,stroke=0)
 pdf_text(PW-48,PH-43,title,21,'MikhakBold','#ffffff')
 cv.setFillColor('#d9eceb');cv.rect(0,0,PW,31,fill=1,stroke=0)
 pdf_text(PW-40,13,'مطالعه دانشگاهی کوه آسماری | ۱۴۰۵',9,'MikhakRegular','#244057')
 cv.setFont('Helvetica',9);cv.setFillColor('#244057');cv.drawString(38,13,f'{num:02d}')
def line(y):
 cv.setStrokeColor('#d7e3e8');cv.line(55,y,PW-55,y)
# Title page
cv.setFillColor('#143344');cv.rect(0,0,PW,PH,fill=1,stroke=0)
cv.setFillColor('#45d7c6');cv.rect(PW-120,0,120,PH,fill=1,stroke=0)
pdf_text(PW-160,PH-150,'پتانسیل‌یابی آب زیرزمینی',30,'MikhakBold','#ffffff')
pdf_text(PW-160,PH-201,'محدوده مطالعاتی کوه آسماری',21,'MikhakSemi','#d3ebec')
pdf_text(PW-160,PH-264,'تحلیل هفت معیار مکانی و انتخاب یک نقطه پیشنهادی',14,'MikhakRegular','#d3ebec')
pdf_text(PW-160,160,'مقیاس نقشه مبنا: ۱:۱۰۰٬۰۰۰ | تفکیک DEM: حدود ۳۰ متر',12,'MikhakRegular','#ffffff')
pdf_text(PW-160,125,'کاربرد: پژوهش دانشگاهی، بدون تأیید امکان حفاری واقعی',11,'MikhakRegular','#f8d8b0')
cv.showPage()
head('چکیده و هدف مطالعه',2)
y=PH-112
paras=[
'در این مطالعه، محدوده‌ای در نقشه زمین‌شناسی کوه آسماری به کمک GIS بررسی شد. هدف، تهیه هفت نقشه موضوعی و تلفیق آن‌ها برای نمایش پهنه‌های دارای استعداد نسبی بیشتر جهت بررسی آب زیرزمینی است.',
'نقشه رنگی زمین‌شناسی مربوط به سال ۱۹۶۶ با مقیاس ۱:۱۰۰٬۰۰۰ است. محدوده پژوهش از کادر مشکی تصویر دوم استخراج و با ویژگی‌های مشترک دو تصویر تطبیق داده شد. ژئورفرنس به‌صورت تقریبی و مبتنی بر نوشته‌های حاشیه نقشه انجام شده است.',
'داده ارتفاعی از قطعه N31E049 در مجموعه Mapzen Skadi HGT تهیه شده و برای پردازش شیب، آبراهه، خطواره و ارتفاع به شبکه UTM منطقه تبدیل شده است.',
'خروجی‌ها برای آموزش روش تحلیل چندمعیاره مناسب‌اند. با این داده‌ها نمی‌توان وجود آب، عمق سطح ایستابی، آبدهی چاه یا موفقیت حفاری را تضمین کرد.'
]
for s in paras:y=pdf_para(PW-65,y,s,max_width=PW-130,fontsize=12,leading=30)-15
cv.showPage()
head('داده‌ها و روش انجام کار',3)
y=PH-109
items=[
'۱. ژئورفرنس: استخراج گوشه‌های محدوده از تصویر مشخص‌شده و تبدیل مختصات پیکسلی به جغرافیایی، با کنترل اولیه روی قاب مختصات نقشه.',
'۲. لیتولوژی: تفکیک طبقات رنگی نقشه اسکن‌شده با استفاده از نمونه رنگ‌های راهنمای سازندها، اصلاح مکانی و تولید لایه GeoTIFF و GeoJSON.',
'۳. گسل: آشکارسازی پاره‌خط‌های قرمز نقشه و غربال هندسی آن‌ها؛ نیازمند جداسازی نهایی گسل از محور چین و سایر علائم به‌صورت دستی.',
'۴. آبراهه: محاسبه جهت جریان D8 و انباشت جریان از DEM؛ شبکه با آستانه ۱۲۵ سلول بالادست نمایش داده شده است.',
'۵. شیب و ارتفاع: تحلیل شبکه ارتفاعی ۳۰متری در UTM39N و محاسبه شیب زمین به درجه.',
'۶. خطواره: روش سایه‌روشن چهارجهته DEM و آشکارساز خط Hough برای نامزدهای ساختاری؛ انطباق با داده زمین‌شناسی باید جداگانه کنترل شود.',
'۷. تقاطع خطواره‌ها: تعیین تقاطع‌های هندسی خطواره‌ها با اختلاف جهت دست‌کم ۲۵ درجه و حذف نقاط نزدیک تکراری.',
'۸. تلفیق: امتیازدهی هر لایه از ۱ تا ۵ و ترکیب وزن‌دار؛ دسته‌بندی نهایی بر اساس صدک‌های توزیع امتیاز در محدوده.'
]
for s in items:y=pdf_para(PW-58,y,s,max_width=PW-110,fontsize=10.6,leading=24)-8
cv.showPage()
head('جدول معیارها و ضرایب وزن‌دهی',4)
weights=[('لیتولوژی',25,'جنس و نفوذپذیری نسبی واحدها'),('گسل',10,'فاصله متعادل از ساختارهای منتخب'),
 ('آبراهه',10,'دسترسی نسبی به زهکشی سطحی'),('شیب',10,'اولویت شیب‌های ملایم'),
 ('خطواره',20,'نزدیکی به شکستگی‌های محتمل'),('تقاطع خطواره‌ها',20,'تمرکز تقاطع ساختاری'),('ارتفاع',5,'ارتفاع نسبی کمتر')]
y=PH-113
for idx,(label,pct,desc) in enumerate(weights):
 if idx%2==0:cv.setFillColor('#ecf3f5');cv.rect(55,y-19,PW-110,37,fill=1,stroke=0)
 pdf_text(PW-80,y,label,12,'MikhakMedium')
 cv.setFont('Helvetica-Bold',12);cv.setFillColor('#23475b');cv.drawRightString(PW-300,y,str(pct)+'%')
 pdf_text(PW-345,y,desc,10,'MikhakRegular')
 y-=42
line(y-9)
y=pdf_para(PW-70,y-45,'امتیاز نهایی برابر مجموع حاصل‌ضرب امتیاز استانداردشده هر معیار در وزن همان معیار است. وزن‌های این مطالعه نمونه آموزشی هستند و از تحلیل حساسیت یا بررسی نتایج چاه‌های موجود به دست نیامده‌اند.',max_width=PW-140,fontsize=11,leading=25)
cv.showPage()
# Atlas pages with maps as full-width image and small explanatory note.
notes=[
'طبقه‌بندی رنگ‌های چاپی نقشه اولیه؛ مرز سازندها برای نتیجه نهایی نیاز به بازبینی دارند.',
'خطوط قرمز استخراج‌شده نامزدهای ساختاری‌اند؛ با محور طاقدیس و سایر علامت‌ها ممکن است اشتباه شوند.',
'شبکه زهکشی با جریان D8 محاسبه شد و بیانگر آبراهه سطحی و مسیر بالقوه رواناب است.',
'شیب در ارزیابی امکان دسترسی و شرایط سطحی مفید است و به تنهایی وجود آبخوان را نشان نمی‌دهد.',
'خطواره‌های DEM فقط نامزدهای ژئومورفولوژیک‌اند، نه شکستگی تأییدشده در سنگ بستر.',
'تقاطع هندسی خطواره‌ها در این مطالعه به‌عنوان شاخص آموزشی استفاده شده است.',
'ارتفاع به‌صورت نسبی امتیاز گرفته است؛ ارتفاع کمتر لزوماً آبدهی بیشتر ایجاد نمی‌کند.',
'پنج کلاس خروجی رتبه‌بندی نسبی همین محدوده‌اند؛ نقطه پیشنهادی صرفاً مطالعاتی است.',
'نقطه با شرط شیب ملایم، فاصله از آبراهه و داخل محدوده انتخاب شده است.'
]
titles=['لیتولوژی','ساختارهای گسلی','آبراهه','شیب','خطواره','تقاطع خطواره','ارتفاع','پتانسیل نهایی','نقطه منتخب']
for ix,p in enumerate(pics):
 head('نقشه '+titles[ix],ix+5)
 im=Image.open(p)
 ratio=im.width/im.height
 maxw=PW-85;maxh=PH-150
 ww=min(maxw,maxh*ratio);hh=ww/ratio
 cv.drawImage(ImageReader(im),(PW-ww)/2,64,ww,hh,mask='auto')
 pdf_text(PW-58,48,notes[ix],9,'MikhakRegular','#6f3840')
 cv.showPage()
head('نتیجه‌گیری و محدودیت‌ها',14)
y=PH-105;c=result['candidate']
for s in [
f"نقطه پیشنهادی مطالعاتی در دستگاه UTM زون ۳۹ شمالی در شرقی {c['utm_easting_m']:.1f} متر و شمالی {c['utm_northing_m']:.1f} متر قرار دارد.",
f"مختصات جغرافیایی تقریبی: عرض {c['lat']:.7f} درجه شمالی و طول {c['lon']:.7f} درجه شرقی.",
f"امتیاز تلفیقی نقطه {c['potential_index_1_5']:.2f} از ۵ است. ارتفاع {c['elevation_m']:.1f} متر و شیب آن {c['slope_deg']:.2f} درجه محاسبه شد.",
'برای قضاوت درباره ظرفیت واقعی آبخوان، دست‌کم اطلاعات چاه‌های مجاور، عمق آب، دبی، لیتولوژی زیرسطحی، کیفیت آب و آزمون‌های میدانی لازم است.',
'محدوده با تطبیق تصویری و مختصات قاب نقشه قدیمی ژئورفرنس شده است. دقت هندسی نقاط را نباید هم‌ارز نقشه‌برداری میدانی یا GPS تفاضلی دانست.',
'گسل‌ها، خطواره‌ها و تقاطع آن‌ها به‌شکل ماشینی و تفسیری شناسایی شده‌اند؛ لازم است روی نقشه اصلی و ترجیحاً تصاویر ماهواره‌ای کنترل شوند.',
'منابع اصلی: نقشه زمین‌شناسی Kuh-e Asmari (1966)، فایل ارتفاعی SRTM-derived Mapzen Skadi N31E049، مستندات روش‌های تحلیل رستری QGIS.'
]:y=pdf_para(PW-58,y,s,max_width=PW-115,fontsize=11.5,leading=27)-14
cv.save()
# Individual map sheets in PDF for easy printing.
cv=canvas.Canvas(str(REPORT/'Geo_Maps_Atlas_FA.pdf'),pagesize=(PW,PH),pageCompression=1)
cv.setTitle('اطلس نقشه‌های پتانسیل‌یابی آب زیرزمینی کوه آسماری')
for idx,p in enumerate(pics):
 im=Image.open(p);ratio=im.width/im.height
 ww=min(PW-40,(PH-30)*ratio);hh=ww/ratio
 cv.drawImage(ImageReader(im),(PW-ww)/2,(PH-hh)/2,ww,hh)
 cv.showPage()
cv.save()
print('PDF pages',4+len(pics)+1,'maps',len(pics))