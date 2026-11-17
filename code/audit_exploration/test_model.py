import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np, time
from common import *; from model import *
pd.set_option('display.width',250)
for g in ['A','B']:
    co,_=clean_cohorts(g); co,groups=add_cells(co,g)
    t=time.time(); cv=Curve(co,LAST,boot=100); print(g,'fit secs',round(time.time()-t,1),'weeks',len(cv.weeks))
    for T in [30,120,180]:
        print(' T',T,{(typ,seg,h):round(v,3) for (typ,seg,h,TT),v in cv.m.items() if TT==T and h in (7,30) and typ=='ad' or (TT==T and h==30 and typ=='iap' and seg=='android')})
    print(' tail',{k:{f:round(v,3) for f,v in d.items()} for k,d in cv.tail.items()})
    bt=np.array([b[1]['ad']['power'] for b in cv.boots]); print(' boot power tail sd',bt.std().round(3))
