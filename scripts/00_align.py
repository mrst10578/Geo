#!/usr/bin/env python3
"""Register Telegram-marked study region against supplied scanned geological map."""
from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FULL=ROOT/'data/source/geological_map_1966.jpg'
BOX=ROOT/'data/source/study_area_box.jpg'
if not FULL.exists() or not BOX.exists():
 raise SystemExit('Place both user-supplied images in data/source/; see README.')
a0=cv2.imread(str(FULL))
b=cv2.imread(str(BOX))
# The crop is inside this part of the supplied 5826x6592 geological sheet.
# This local search constraint stops visually repetitive map symbols from
# matching elsewhere on the same full sheet.
x0,y0,x1,y1=2600,2700,4500,4700
a=cv2.resize(a0[y0:y1,x0:x1],(1200,1263))
grayA=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)
grayB=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=14000,contrastThreshold=.01)
kp1,d1=sift.detectAndCompute(grayA,None)
kp2,d2=sift.detectAndCompute(grayB,None)
matches=cv2.BFMatcher().knnMatch(d2,d1,k=2)
good=[m for m,n in matches if m.distance < .75*n.distance]
if len(good)<35:raise RuntimeError(f'Insufficient matches ({len(good)}), check input maps')
p2=np.float32([kp2[m.queryIdx].pt for m in good]).reshape(-1,1,2)
p1=np.float32([kp1[m.trainIdx].pt for m in good]).reshape(-1,1,2)
H,inliers=cv2.findHomography(p2,p1,cv2.RANSAC,8)
if H is None or int(inliers.sum())<20:raise RuntimeError('Study area alignment unreliable')
np.savetxt(ROOT/'match_H.txt',H)
T=np.array([[1900/1200,0,x0],[0,2000/1263,y0],[0,0,1]])
corner=np.array([[99,43],[1057,43],[1057,921],[99,921]],dtype=np.float32).reshape(-1,1,2)
poly=cv2.perspectiveTransform(corner,T@H).reshape((-1,2))
print('Control matches:',int(inliers.sum()),'of',len(good),'Study area corners:',np.round(poly).astype(int).tolist())
ROOT.joinpath('alignment.json').write_text(json.dumps({'H_crop_to_roi':H.tolist(),'corners_full_px':poly.tolist(),'inliers':int(inliers.sum())},indent=2))