"""Is organic driven by paid advertising?  Weekly organic installs vs paid installs / spend (Game A and B)."""
import sys; sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
res={}
for g in 'AB':
    ua=pd.read_csv(f'{DATA}/Game{g}_ua_daily.csv',parse_dates=['date'])
    ua['kind']=np.where(ua.network.isin(PAID),'paid',np.where(ua.network=='Organic','organic',np.where(ua.network=='Store-Search','store','unattr')))
    w=ua.groupby([pd.Grouper(key='date',freq='W-SUN'),'kind']).agg(inst=('installs_mmp','sum'),cost=('cost','sum')).unstack().fillna(0)
    d=pd.DataFrame({'paid_inst':w[('inst','paid')],'org_inst':w[('inst','organic')],'spend':w[('cost','paid')]})
    d=d.iloc[1:-1]   # drop partial weeks
    d['org_share']=d.org_inst/(d.org_inst+d.paid_inst)
    print('=====',g); print(d.round(2).to_string())
    # first-difference log-log elasticity (weekly), controlling for nothing else
    x=np.log(d.paid_inst.replace(0,np.nan)); y=np.log(d.org_inst.replace(0,np.nan))
    for lab,(xx,yy) in {'levels':(x,y),'first-diff':(x.diff(),y.diff()),'lag1 first-diff':(x.diff().shift(1),y.diff())}.items():
        m=pd.concat([xx,yy],axis=1).dropna(); m.columns=['x','y']
        b=np.polyfit(m.x,m.y,1)[0]; r=m.corr().iloc[0,1]
        # block bootstrap CI for slope
        rng=np.random.default_rng(0); bs=[]
        for _ in range(500):
            idx=rng.integers(0,len(m),len(m)); mm=m.iloc[idx]
            if mm.x.std()>0: bs.append(np.polyfit(mm.x,mm.y,1)[0])
        print(f'{lab}: elasticity of organic wrt paid installs = {b:.2f} (80% CI {np.quantile(bs,0.1):.2f}..{np.quantile(bs,0.9):.2f}), corr {r:.2f}, n={len(m)}')
        res[(g,lab)]=(b,np.quantile(bs,0.1),np.quantile(bs,0.9),r,len(m))
    # natural experiments: Game A Net-B pause (Mar16-Jul10) is on small base. Game B: Net-B stopped Sep.
    if g=='B':
        print(d.tail(8)[['paid_inst','org_inst','spend']])
pd.DataFrame(res,index=['elasticity','lo80','hi80','corr','n']).T.to_csv(f'{OUT}/organic_elasticity.csv')
