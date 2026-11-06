> **Revision status:** The original outputs below are historical. A four-factor revision using supplied vector data and standard GIS tools is documented in [revised-v2](revised-v2/README.md). The seven-factor assignment remains unfinished; do not treat the old well coordinates as a revised result.

# پتانسیل‌یابی آب زیرزمینی، محدوده کوه آسماری

این مخزن خروجی یک **مطالعه دانشگاهی GIS** برای محدوده مشخص‌شده روی نقشه زمین‌شناسی کوه آسماری است. هفت معیار مکانی به‌صورت مستقل تهیه شده‌اند، سپس با مدل جمع وزنی تلفیق شده‌اند تا پهنه‌های با **پتانسیل نسبی** بیشتر مشخص شوند. یک نقطه نیز صرفاً برای نمایش روش مکان‌یابی دانشگاهی معرفی شده است.

> **محدودیت اصلی:** نقشه نهایی برآورد آبدهی، عمق چاه، یا ضمانت وجود آب نیست. نقشه اسکن‌شده به شکل تقریبی ژئورفرنس شده و داده‌های چاه‌های موجود، آزمون پمپاژ، برداشت میدانی یا ژئوفیزیک در مدل استفاده نشده‌اند. خطواره‌ها و گسل‌ها نامزدهای تفسیری هستند و باید دستی کنترل شوند.

## خروجی‌های نهایی

- `outputs/maps/` شامل **۹ نقشه PNG**: لیتولوژی، گسل‌های نامزد، آبراهه، شیب، خطواره، تقاطع خطواره، ارتفاع، پتانسیل نهایی و بزرگنمایی نقطه منتخب.
- `outputs/rasters/` شامل لایه‌های GeoTIFF با دستگاه مختصات **EPSG:32639**، امتیاز معیارها، فاصله از پدیده‌ها، شاخص نهایی و کلاس‌بندی آن.
- `outputs/vectors/` شامل محدوده مطالعه، پلیگون‌های تفسیری لیتولوژی، خطواره‌ها، تقاطع‌ها، آبراهه‌ها و نقطه پیشنهادی (GeoJSON با مختصات WGS84).
- `outputs/report/Geo_University_Report_FA.pdf` گزارش فارسی کامل، با فونت میخک، روش اجرا، جدول وزن‌دهی، اطلس نقشه‌ها و محدودیت‌ها.
- `outputs/report/Geo_Maps_Atlas_FA.pdf` اطلس نقشه‌ها برای مشاهده و چاپ.
- `outputs/meta/` شامل مختصات، داده‌های مبنا، جدول طبقات و نتیجه کمی مدل.

## وزن‌دهی اولیه

| معیار | وزن |
|---|---:|
| لیتولوژی | ۲۵٪ |
| گسل | ۱۰٪ |
| آبراهه | ۱۰٪ |
| شیب | ۱۰٪ |
| خطواره | ۲۰٪ |
| تقاطع خطواره | ۲۰٪ |
| ارتفاع | ۵٪ |
| **جمع** | **۱۰۰٪** |

امتیاز هر لایه در بازه ۱ تا ۵ تعیین شده و حاصل‌ضرب امتیاز در وزن معیار به نقشه نهایی اضافه شده است. پنج کلاس خروجی **نسبی و مبتنی بر صدک‌های داخل محدوده** هستند، نه آستانه‌های قطعی آبدهی.

## نقطه مطالعاتی پیشنهادی

- عرض جغرافیایی تقریبی: **31.6402744° N**
- طول جغرافیایی تقریبی: **49.8530993° E**
- UTM Zone 39N: **391245 E, 3501135 N** (متر)
- امتیاز مدل: **۴٫۸۵ از ۵**

این مختصات از ژئورفرنس تقریبی و مدل هفت‌معیاره به دست آمده‌اند. برای اجرا یا حفاری **نباید** بدون اصلاح ژئورفرنس و اعتبارسنجی میدانی استفاده شوند.

## راه‌اندازی مجدد

دو تصویر اولیه کارفرما به دلیل نامشخص بودن مجوز بازنشر در مخزن عمومی قرار داده نشده‌اند. برای بازتولید، فایل کامل نقشه اسکن‌شده را با نام `data/source/geological_map_1966.jpg` و تصویر محدوده کادربندی‌شده را با نام `data/source/study_area_box.jpg` قرار دهید.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/00_fetch_assets.py
.venv/bin/python scripts/00_align.py
.venv/bin/python scripts/01_prepare.py
.venv/bin/python scripts/02_analyze.py
.venv/bin/python scripts/03_render.py
.venv/bin/python scripts/04_polish_pdf.py
.venv/bin/python scripts/05_validate.py
```

در `scripts/00_fetch_assets.py` فایل ارتفاعی HGT از Mapzen Skadi و قلم میخک صرفاً به‌عنوان وابستگی ساخت دریافت می‌شوند. فایل‌های فونت به مخزن اضافه نشده‌اند.

## منشأ داده و ارجاع

۱. Iranian Oil Operating Companies, *Kuh-e Asmari Geological Compilation Map*, Sheet 20825 E, scale 1:100,000, 1966.  
۲. Mapzen Skadi (SRTM-derived terrain), `N31E049.hgt`, https://elevation-tiles-prod.s3.amazonaws.com/skadi/  
۳. USGS, Global elevation data: https://www.usgs.gov/faqs/where-can-i-get-global-elevation-data  
۴. QGIS, Raster Terrain Analysis: https://documentation.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/rasterterrainanalysis.html  

**دقت و وضعیت:** این نسخه برای نمایش روش چندمعیاره دانشگاهی تهیه شده است. طبقه‌بندی رنگی لیتولوژی و تشخیص خطی ساختارها نیازمند بازبینی متخصص زمین‌شناسی و هیدروژئولوژی است.
