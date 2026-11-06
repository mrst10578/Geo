#!/usr/bin/env python3
"""Set Persian labels with Mikhak via Pillow libraqm and build searchable RTL PDF with WeasyPrint."""
from pathlib import Path
import json,html,os
from PIL import Image,ImageDraw,ImageFont
from weasyprint import HTML
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';MAPS=OUT/'maps';REPORT=OUT/'report';F=ROOT/'.fonts'
meta=json.loads((OUT/'meta/study_metadata.json').read_text())
res=json.loads((OUT/'meta/analysis_results.json').read_text())
c=res['candidate']
headings=[
 ('01_lithology','نقشه لیتولوژی','تفکیک واحدهای سنگی از رنگ‌های نقشه زمین‌شناسی ۱۳۴۵'),
 ('02_faults','نقشه گسل و ساختار','ردیابی اولیه نشانه‌های قرمز روی نقشه زمین‌شناسی'),
 ('03_drainage','نقشه آبراهه‌ها','استخراج شبکه زهکشی به روش D8 از مدل ارتفاعی'),
 ('04_slope','نقشه شیب زمین','شیب سطح زمین برحسب درجه از داده ارتفاعی'),
 ('05_lineaments','نقشه خطواره‌ها','خطواره‌های احتمالی از سایه‌روشن چندجهته DEM'),
 ('06_lineament_intersections','نقشه تقاطع خطواره‌ها','تقاطع خطواره‌های دارای اختلاف امتداد دست‌کم ۲۵ درجه'),
 ('07_elevation','نقشه ارتفاع','ارتفاع از سطح دریا برحسب متر'),
 ('08_final_potential_and_well','پتانسیل نسبی آب زیرزمینی','تلفیق هفت معیار و انتخاب نقطه پیشنهادی مطالعاتی'),
 ('09_well_candidate_detail','موقعیت پیشنهادی چاه','نمای نزدیک نقطه منتخب در پهنه‌بندی نهایی')
]
notes={
 '02_faults':[('تعداد پاره‌خط',str(res['fault_candidate_segments'])),('روش','رنگ‌سنجی و آشکارسازی خط'),('محدودیت','این خطوط نیاز به تأیید دستی و تفکیک از محور چین دارند.')],
 '03_drainage':[('استخراج','D8 و انباشت جریان'),('آستانه',f"{res['drainage_threshold_cells']} سلول بالادست"),('محدودیت','آبراهه استخراج‌شده لزوماً دائمی نیست.')],
 '04_slope':[('واحد اندازه‌گیری','درجه'),('تفسیر','در شیب کم، شرایط سطحی حفاری مناسب‌تر است.'),('سهم وزن','۱۰ درصد')],
 '05_lineaments':[('تعداد پاره‌خط',str(res['lineament_candidate_segments'])),('روش','سایه‌روشن چهارجهته و تشخیص خط'),('محدودیت','هر خطواره الزاماً شکستگی زمین‌شناسی نیست.')],
 '06_lineament_intersections':[('تعداد نقاط',str(res['lineament_intersection_points'])),('روش','تقاطع هندسی خطوط با اختلاف جهت کافی'),('تذکر','این شاخص به بررسی ساختاری تکمیلی نیاز دارد.')],
 '07_elevation':[('کمینه و بیشینه',f"{int(float(__import__('numpy').min(__import__('rasterio').open(OUT/'rasters/dem_elevation.tif').read(1)[__import__('rasterio').open(OUT/'rasters/study_area_mask.tif').read(1)>0])))} تا ۱۷۴۰ متر"),('کاربرد','توصیف ناهمواری و ارتفاع نسبی')],
 '08_final_potential_and_well':[('نقطه منتخب',f"X = {c['utm_easting_m']:.0f}  |  Y = {c['utm_northing_m']:.0f}"),('امتیاز مدل',f"{c['potential_index_1_5']:.2f} از ۵"),('تفسیر','پنج کلاس نقشه، رتبه‌بندی نسبی محدوده هستند.')],
 '09_well_candidate_detail':[('مختصات جغرافیایی',f"{c['lat']:.7f}°N, {c['lon']:.7f}°E"),('مختصات UTM',f"{c['utm_easting_m']:.1f} E, {c['utm_northing_m']:.1f} N"),('ارتفاع و شیب',f"{c['elevation_m']:.1f} m  |  {c['slope_deg']:.2f}°"),('وضعیت','پیشنهاد آموزشی، نه مجوز حفاری')]
}
def font(weight,px):return ImageFont.truetype(str(F/f'Mikhak-{weight}.ttf'),px)
def draw_rtl(d,x,y,t,weight='Regular',size=21,fill='#23354b',limit=None):
 ft=font(weight,size)
 if limit:
  while size>12 and d.textbbox((0,0),str(t),font=ft,direction='rtl')[2]>limit:
   size-=1;ft=font(weight,size)
 d.text((int(x),int(y)),str(t),font=ft,fill=fill,direction='rtl',anchor='ra')
def wrap_rtl(d,text,size,max_w,weight='Regular'):
 tokens=str(text).split();lines=[];cur=''
 for token in tokens:
  test=(cur+' '+token).strip()
  if d.textbbox((0,0),test,font=font(weight,size),direction='rtl')[2]>max_w and cur:
   lines.append(cur);cur=token
  else:cur=test
 if cur:lines.append(cur)
 return lines
for filename,title,subtitle in headings:
 p=MAPS/(filename+'.png')
 im=Image.open(p).convert('RGB');W,H=im.size;d=ImageDraw.Draw(im)
 draw_rtl(d,int(W*.7),int(H*.040),title,'Bold',45,'#182d3d',W*.62)
 draw_rtl(d,int(W*.7),int(H*.090),subtitle,'Regular',23,'#506478',W*.64)
 draw_rtl(d,int(W*.963),int(H*.155),'راهنمای نقشه','SemiBold',26,'#263749',W*.20)
 if filename=='01_lithology':
  yy=H*.183
  for cl in meta['lithology_classes']:
   # Keep all geological units represented in the original legend
   label=cl['name_fa']
   draw_rtl(d,W*.935,yy,label,'Regular',18,'#24394e',W*.17)
   yy+=H*.046
  draw_rtl(d,W*.96,H*.86,'مرز واحدها به کنترل دیداری نیاز دارد.','Regular',17,'#9b4147',W*.20)
 elif filename=='08_final_potential_and_well':
  labels=['خیلی کم','کم','متوسط','زیاد','خیلی زیاد']
  for i,s in enumerate(labels):draw_rtl(d,W*.96,H*(.205+i*.074),s,'Medium',24,'#1d3540',W*.13)
  y=H*.61
  for label,value in notes[filename]:
   draw_rtl(d,W*.96,y,label,'SemiBold',21,'#253a50',W*.19)
   y+=33
   for ln in wrap_rtl(d,value,18,W*.19):draw_rtl(d,W*.96,y,ln,'Regular',18,'#596779',W*.19);y+=27
   y+=22
 else:
  y=H*.225
  for label,value in notes.get(filename,[]):
   draw_rtl(d,W*.96,y,label,'SemiBold',23,'#25394a',W*.20)
   y+=35
   for ln in wrap_rtl(d,value,19,W*.20):
    draw_rtl(d,W*.96,y,ln,'Regular',19,'#566779',W*.20)
    y+=32
   y+=42
 draw_rtl(d,W*.7,H*.937,'مطالعه دانشگاهی کوه آسماری | نقشه مبنا ۱:۱۰۰٬۰۰۰ | تفکیک داده ارتفاعی حدود ۳۰ متر','Regular',18,'#596779',W*.65)
 draw_rtl(d,W*.7,H*.961,'ژئورفرنس تقریبی است؛ نتیجه برای انتخاب قطعی محل حفاری معتبر نیست.','Regular',17,'#944e55',W*.65)
 im.save(p,optimize=True)
 print('Typeset',p.name,im.size)
# Refresh collage after Persian typesetting, not before.
thumbs=[Image.open(MAPS/(z+'.png')).convert('RGB') for z,_,_ in headings[:8]]
board=Image.new('RGB',(1500,2290),(247,248,248))
for j,im in enumerate(thumbs):
 im.thumbnail((700,520))
 x=35+(j%2)*730+(700-im.width)//2
 y=40+(j//2)*560+(520-im.height)//2
 board.paste(im,(x,y))
board.save(MAPS/'00_overview.jpg',quality=86,optimize=True)

# Natural, fully Persian, searchable PDF pages. PDF carries embedded Mikhak subsets.
body='''<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<style>
@font-face{font-family:Mikhak;src:url("../.fonts/Mikhak-Regular.ttf");font-weight:400}
@font-face{font-family:Mikhak;src:url("../.fonts/Mikhak-Medium.ttf");font-weight:500}
@font-face{font-family:Mikhak;src:url("../.fonts/Mikhak-SemiBold.ttf");font-weight:600}
@font-face{font-family:Mikhak;src:url("../.fonts/Mikhak-Bold.ttf");font-weight:700}
@page{size:A4 landscape;margin:14mm 16mm;@bottom-left{content:counter(page);font-family:Mikhak;color:#697784;font-size:9pt}}
*{box-sizing:border-box}
body{font-family:Mikhak,sans-serif;direction:rtl;color:#203240;background:#fff;line-height:1.9;font-size:12pt}
.page{page-break-after:always}
.cover{margin:-14mm -16mm;padding:24mm 26mm;height:210mm;color:white;background:linear-gradient(135deg,#123345,#236777)}
.cover h1{margin-top:30mm;color:white;font-size:33pt;line-height:1.4}
.cover h2{font-size:20pt;font-weight:500;color:#eafafa}
.cover p{margin-top:13mm;font-size:14pt;color:#ecffff}
h1{font-size:23pt;color:#153a4b;margin:0 0 7mm}
h2{font-size:14pt;color:#18566c;margin:5mm 0 2mm}
p{margin:2mm 0 4mm;text-align:justify}
small,.muted{color:#7b8991}
table{border-collapse:collapse;width:100%;margin:4mm auto;font-size:11pt}
td,th{padding:3mm;border-bottom:1px solid #d8e5e8;text-align:right}
th{background:#eaf1f2}
figure{margin:0}
img.map{display:block;max-width:100%;height:138mm;object-fit:contain;margin:auto}
figcaption{font-size:10pt;color:#5c6f7b;margin-top:0mm}
strong{font-weight:700}
.warning{padding:4mm 5mm;border-right:4px solid #b75f5f;background:#f8f0ec}
.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.summary-grid>div{background:#f2f7f8;padding:5mm}
blockquote{margin:4mm 0;background:#edf5f5;padding:4mm}
ul{padding-right:7mm}
li{margin-bottom:2.3mm}
code,.ltr{direction:ltr;unicode-bidi:isolate;display:inline-block;font-family:monospace}
</style></head><body>'''
body+='<section class="page cover"><h1>پتانسیل‌یابی آب زیرزمینی</h1><h2>محدوده مطالعاتی کوه آسماری</h2><p>تهیه هفت لایه موضوعی، وزن‌دهی چندمعیاره و معرفی یک نقطه پیشنهادی چاه</p><p style="margin-top:40mm">مطالعه دانشگاهی | آبان ۱۴۰۵</p><p style="font-size:11pt">نقشه زمین‌شناسی ۱:۱۰۰٬۰۰۰ | داده ارتفاعی حدود ۳۰ متر | سیستم مختصات UTM زون ۳۹ شمالی</p></section>'
body+='<section class="page"><h1>چکیده پژوهش</h1><p>محدوده مورد مطالعه از کادر مشکی مشخص‌شده روی نقشه زمین‌شناسی کوه آسماری استخراج شد. در گام اول، موقعیت کادر روی تصویر اصلی تطبیق داده شد و محدوده به دستگاه مختصات واقعی منتقل شد. سپس داده ارتفاعی منطقه برای محاسبه شیب، ارتفاع، آبراهه‌ها، خطواره‌ها و محل تقاطع خطواره‌ها به کار رفت. اطلاعات لیتولوژی و نشانه‌های ساختاری نیز از نقشه رنگی اصلی استخراج شدند.</p><p>در مرحله تلفیق، به هر معیار امتیازی بین یک تا پنج داده شد و با وزن‌های از پیش مشخص‌شده، شاخص نسبی پتانسیل آب زیرزمینی محاسبه شد. در پایان یک نقطه از پهنه‌های دارای امتیاز بالاتر با رعایت شیب کم، فاصله از آبراهه و قرارگیری در داخل محدوده پیشنهاد شد.</p><h2>محدوده و داده‌ها</h2><div class="summary-grid"><div><strong>مساحت محدوده</strong><p>'+str(meta['roi_area_km2'])+' کیلومتر مربع</p></div><div><strong>تفکیک ارتفاعی</strong><p>حدود ۳۰ متر</p></div><div><strong>نقشه مبنا</strong><p>کوه آسماری، ۱۹۶۶، مقیاس ۱:۱۰۰٬۰۰۰</p></div><div><strong>سیستم مختصات</strong><p class="ltr">EPSG:32639</p></div></div><p class="warning">این نتایج برای آموزش تحلیل مکانی و پهنه‌بندی نسبی تهیه شده‌اند. داده موجود به‌تنهایی تأییدکننده آبدهی یا امکان حفر واقعی چاه نیست.</p></section>'
body+='<section class="page"><h1>روش انجام کار</h1><ol><li><strong>ژئورفرنس و مرزبندی:</strong> عکس محدوده با نقشه اصلی براساس ویژگی‌های مشترک تطبیق داده شد. تبدیل پیکسل به مختصات با استفاده از شبکه مختصات چاپ‌شده روی نقشه صورت گرفت و دقت آن تقریبی است.</li><li><strong>لیتولوژی:</strong> نمونه‌رنگ‌های واحدهای سنگی از راهنمای نقشه گرفته شد، پیکسل‌ها طبقه‌بندی و کلاس‌ها برای تحلیل مکانی اصلاح شدند.</li><li><strong>گسل‌ها:</strong> نشانه‌های خطی قرمز نقشه به‌صورت اولیه شناسایی شدند. تشخیص دقیق گسل از محور چین یا دیگر علائم، کنترل دستی می‌خواهد.</li><li><strong>آبراهه:</strong> با استفاده از مدل ارتفاعی، جهت جریان به روش D8 و انباشت جریان محاسبه شد. آستانه استخراج شبکه ۱۲۵ سلول بالادست در نظر گرفته شد.</li><li><strong>شیب و ارتفاع:</strong> مقادیر شیب به درجه و ارتفاع به متر از شبکه ارتفاعی استخراج شدند.</li><li><strong>خطواره و تقاطع:</strong> از سایه‌روشن چندجهته DEM و آشکارسازی خط برای نامزدهای خطواره استفاده شد. تقاطع با اختلاف امتداد حداقل ۲۵ درجه محاسبه شد.</li><li><strong>وزن‌دهی:</strong> امتیاز معیارها در بازه ۱ تا ۵ استاندارد و به‌صورت جمع وزنی تلفیق شد.</li></ol></section>'
body+='<section class="page"><h1>جدول وزن‌دهی معیارها</h1><table><thead><tr><th>معیار</th><th>وزن</th><th>منطق اولیه امتیازدهی</th></tr></thead><tbody>'
weights=[('لیتولوژی',25,'رتبه‌بندی نسبی نفوذپذیری واحدهای سنگی'),('گسل',10,'فاصله مناسب از ساختارهای نامزد و پرهیز از حریم بسیار نزدیک'),('آبراهه',10,'فاصله متعادل از شبکه زهکشی'),('شیب',10,'اولویت سطوح کم‌شیب'),('خطواره',20,'نزدیکی به خطواره‌های احتمالی'),('تقاطع خطواره‌ها',20,'نزدیکی به محل تمرکز تقاطع‌ها'),('ارتفاع',5,'اولویت ارتفاع نسبی پایین‌تر')]
for label,weight,desc in weights:body+=f'<tr><td>{label}</td><td>{weight}٪</td><td>{desc}</td></tr>'
body+='</tbody></table><blockquote>شاخص نهایی = مجموع (وزن هر معیار × امتیاز استاندارد آن) تقسیم بر ۱۰۰. وزن‌ها برای نمایش روش در یک پروژه دانشگاهی انتخاب شده‌اند؛ اعتبارسنجی آماری با چاه‌های موجود انجام نشده است.</blockquote></section>'
notes_map=[
'لیتولوژی به‌صورت طبقه‌بندی رنگی از نقشه زمین‌شناسی تهیه شده است؛ به‌علت کیفیت چاپ و اسکن، این لایه به کنترل دستی مرز سازندها نیاز دارد.',
'این نقشه ردهای ساختاری قرمز را نشان می‌دهد. هر پاره‌خط الزاماً گسل نیست و نام‌گذاری قطعی مستلزم تطبیق با علائم اصلی نقشه است.',
'شبکه آبراهه بر اساس جهت جریان و انباشت جریان DEM استخراج شده است. شبکه زهکشی مدل‌سازی‌شده با جریان آب دائمی برابر نیست.',
'شیب زمین از مشتقات DEM است. نواحی کم‌شیب از نظر دسترسی و عملیات سطحی امتیاز بیشتری می‌گیرند.',
'خطواره‌های استخراج‌شده از عوارض سطحی، نشانه‌های احتمالی هستند و نه شکستگی قطعی سنگ بستر.',
'محل تقاطع خطواره‌ها با فیلتر اختلاف امتداد تعیین شده است. این شاخص در تلفیق با وزن ۲۰ درصد وارد مدل شد.',
'ارتفاع مطلق در این مدل به‌عنوان یک متغیر کمکی با وزن ۵ درصد وارد شده است و نباید با سطح آب زیرزمینی یکسان در نظر گرفته شود.',
'نتیجه نهایی یک پهنه‌بندی نسبی از معیارهای همین مطالعه است. ستاره زرد نقطه پیشنهادی آموزشی را نشان می‌دهد.',
'نمای نزدیک نقطه پیشنهادی برای مشاهده وضعیت آن نسبت به آبراهه‌ها، خطوط ساختاری و پهنه پتانسیل تهیه شده است.'
]
for ix,(filename,title,subtitle) in enumerate(headings):
 body+=f'<section class="page"><h1>{title}</h1><figure><img class="map" src="../maps/{filename}.png"><figcaption>{notes_map[ix]}</figcaption></figure></section>'
body+='<section class="page" style="font-size:10pt;line-height:1.5"><h1>نتیجه نهایی و نقطه پیشنهادی</h1>'
body+=f'<div class="summary-grid"><div><strong>مختصات UTM</strong><p><span class="ltr">{c["utm_easting_m"]:.1f} E</span><br><span class="ltr">{c["utm_northing_m"]:.1f} N</span></p></div><div><strong>مختصات جغرافیایی</strong><p><span class="ltr">{c["lat"]:.7f}° N</span><br><span class="ltr">{c["lon"]:.7f}° E</span></p></div><div><strong>ارتفاع و شیب</strong><p>{c["elevation_m"]:.1f} متر و {c["slope_deg"]:.2f} درجه</p></div><div><strong>امتیاز مدل</strong><p>{c["potential_index_1_5"]:.2f} از ۵ (کلاس نسبی {c["relative_class"]})</p></div></div>'
body+='<h2>تفسیر نتیجه</h2><p>نقطه پیشنهادی در محدوده پهنه دارای امتیاز نسبی بالاتر انتخاب شده و در زمان غربالگری از بخش‌های پرشیب و بستر مستقیم آبراهه کنار گذاشته شده است. این پیشنهاد یک خروجی مطالعاتی از مدل هفت‌معیاره است و امکان‌پذیری حفاری، عمق برخورد با آب یا آبدهی را مشخص نمی‌کند.</p><h2>چه اطلاعاتی برای ادامه لازم است؟</h2><ul><li>اطلاعات چاه‌های مجاور، عمق سطح آب و تغییرات فصلی آن</li><li>توصیف لایه‌های زیرسطحی، شکستگی‌های تأییدشده و مطالعات ژئوفیزیکی</li><li>آزمایش پمپاژ، کیفیت آب و محدودیت‌های قانونی برداشت</li><li>کنترل دستی خطواره‌ها و مرز لیتولوژی در GIS</li></ul></section>'
body+='<section><h1>منابع و کیفیت داده</h1><ul><li>Iranian Oil Operating Companies. <i>Kuh-e Asmari Geological Compilation Map</i>, sheet 20825 E, 1:100,000, 1966.</li><li>Mapzen Skadi terrain tiles (SRTM-derived), tile N31E049, elevation data in HGT format. https://elevation-tiles-prod.s3.amazonaws.com/skadi/</li><li>QGIS Documentation: Raster Terrain Analysis, slope and raster processing. https://documentation.qgis.org/</li><li>USGS: SRTM global elevation data and limitations. https://www.usgs.gov/</li></ul><p>ژئورفرنس این پروژه تقریبی و مبتنی بر نقشه اسکن‌شده است. شناسایی خطواره و گسل خودکار انجام شده و خطای تفسیر دارد. هیچ داده‌ای از عمق آب، نفوذپذیری واقعی یا بازده چاه‌های موجود در مدل به کار نرفته است. بنابراین از مختصات خروجی فقط برای نمایش روند مکان‌یابی دانشگاهی استفاده شود.</p></section>'
body+='</body></html>'
(REPORT/'report_source.html').write_text(body,encoding='utf-8')
# Font URL path resolution: report dir ../.fonts points at ROOT/.fonts only if REPORT=ROOT/outputs/report -> ../../.fonts
body=body.replace('../.fonts/','../../.fonts/')
(REPORT/'report_source.html').write_text(body,encoding='utf-8')
HTML(filename=str(REPORT/'report_source.html'),base_url=str(REPORT)).write_pdf(str(REPORT/'Geo_University_Report_FA.pdf'))
# An independent map atlas with all maps, same RTL CSS.
atlas='''<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>
@font-face{font-family:Mikhak;src:url("../../.fonts/Mikhak-Regular.ttf")}
@page{size:A4 landscape;margin:5mm}
body{font-family:Mikhak}section{page-break-after:always}img{width:100%;height:194mm;object-fit:contain}
</style></head><body>'''
for filename,_,_ in headings:atlas+=f'<section><img src="../maps/{filename}.png"></section>'
atlas+='</body></html>'
(REPORT/'atlas_source.html').write_text(atlas,encoding='utf-8')
HTML(filename=str(REPORT/'atlas_source.html'),base_url=str(REPORT)).write_pdf(str(REPORT/'Geo_Maps_Atlas_FA.pdf'))
print('PDF files:',[(p.name,p.stat().st_size) for p in REPORT.glob('*.pdf')])