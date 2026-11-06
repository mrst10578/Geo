#!/usr/bin/env python3
"""Download openly licensed analysis dependencies; user map images are never fetched or published."""
from pathlib import Path
from urllib.request import urlopen
import gzip,shutil
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
fonts=ROOT/'.fonts';fonts.mkdir(exist_ok=True)
url='https://elevation-tiles-prod.s3.amazonaws.com/skadi/N31/N31E049.hgt.gz'
z=raw/'N31E049.hgt.gz'
if not z.exists():
 print('Downloading DEM source',url)
 with urlopen(url,timeout=120) as r,z.open('wb') as f:shutil.copyfileobj(r,f)
hgt=raw/'N31E049.hgt'
if not hgt.exists():
 with gzip.open(z,'rb') as src,hgt.open('wb') as dst:shutil.copyfileobj(src,dst)
 if hgt.stat().st_size!=3601*3601*2:
  raise RuntimeError('Wrong HGT tile dimensions')
for weight in ('Regular','Medium','SemiBold','Bold'):
 path=fonts/f'Mikhak-{weight}.ttf'
 if path.exists():continue
 url=f'https://raw.githubusercontent.com/aminabedi68/Mikhak/master/fonts/ttf/FD/Mikhak-FD-{weight}.ttf'
 with urlopen(url,timeout=40) as r,path.open('wb') as dst:shutil.copyfileobj(r,dst)
print('Ready DEM and Persian fonts. Fonts are build dependencies, not published artifacts.')