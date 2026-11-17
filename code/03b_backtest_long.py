"""Backtest of the 180-day horizon and of tail extrapolation; residual-noise calibration."""
import sys, json
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *; from model import *
from importlib import import_module
bt=import_module('03_backtest')
pd.set_option('display.width',250)
res={}
# ---- 180-day backtest: as-of 2025-08-01, train installs <= Feb 2 (age>=180), test Feb 3 - Mar 31
ASOF2=pd.Timestamp('2025-08-01')
rows=[]
for g in 'AB':
    co,groups=bt.prep(g)
    cv=Curve(co,ASOF2,halflife=1e9)
    d=co[(co.paid)&co.install_date.between('2025-02-03','2025-03-31')&(co.installs>0)].copy()
    d['mon']=d.install_date.dt.to_period('M').astype(str)
    for mh in [7,30,90]:
        r=bt.evaluate(cv,d,180,mh,min_n=300)
        s=bt.summarize(r); s.update(game=g,T=180,max_h=mh); rows.append(s)
print(pd.DataFrame(rows).round(2).to_string(index=False))
# ---- tail form test: fit on points up to d120 only, predict LTV(179)/LTV(120), compare with actual
tt=[]
for g in 'AB':
    co,_=bt.prep(g)
    cv=Curve(co,LAST,halflife=1e9)
    for typ in ['ad','iap']:
        ltv=np.array([n.sum()/dd.sum() for n,dd in cv.tailpts[typ]])   # at 30,60,90,120,179
        t=np.array([30,60,90,120.]); rate=np.diff(ltv[:4])/30.0; tm=np.array([45,75,105.])
        ok=rate>0
        if ok.sum()<3 or ltv[3]<=0: continue
        p,lc=np.polyfit(np.log(tm),np.log(rate),1); c=np.exp(lc)
        integ=c/(p+1)*(179**(p+1)-120**(p+1)); fp=1+integ/ltv[3]
        lam,la=np.polyfit(tm,np.log(rate),1); a=np.exp(la); lam=-lam
        fe=1+a/lam*(np.exp(-lam*120)-np.exp(-lam*179))/ltv[3]
        b_,a_=np.polyfit(np.log(t[1:]),ltv[1:4],1); fl=1+b_*np.log(179/120)/ltv[3]
        tt.append(dict(game=g,typ=typ,actual=ltv[4]/ltv[3],power=fp,exp=fe,log=fl,median=np.median([fp,fe,fl])))
tt=pd.DataFrame(tt); print(tt.round(3).to_string(index=False))
tt.to_csv(f'{OUT}/tail_form_backtest.csv',index=False)
# ---- noise calibration from T=120 residuals (same-game, as-of Jun 30)
R=pd.read_csv(f'{OUT}/backtest_residuals.csv')
same=R[(R.train==R.test)&(R.max_h.isin([7,14,30]))].copy()
same['inv']=1/same.installs
# lr^2 ~ a + b/n  (non-negative LS)
for g in 'AB':
    s=same[same.train==g]
    X=np.c_[np.ones(len(s)),s.inv.values]; y=(s.lr-s.lr.mean())**2
    coef=np.linalg.lstsq(X,y,rcond=None)[0]; coef=np.maximum(coef,[0.0004,0.0])
    print(g,'sigma^2 = %.4f + %.1f/n'%tuple(coef),' bias(mean lr)=%.3f'%s.lr.mean())
    res[g]=dict(a=float(coef[0]),b=float(coef[1]),bias=float(s.lr.mean()))
json.dump(res,open(f'{OUT}/noise_params.json','w'),indent=1)
