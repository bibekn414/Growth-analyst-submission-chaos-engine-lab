import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',200)
def ratios(df, num, den):
    m=df[num].notna()&df[den].notna()
    return df.loc[m,num].sum()/df.loc[m,den].sum(), m.sum(), df.loc[m,'installs'].sum()
for g in ['A','B']:
    co,_=clean_cohorts(g)
    co,groups=add_cells(co,g)
    print('=======',g)
    base=co[co.installs>=1]
    # exclude cohorts affected by spike-day installs
    base=base[~base.install_date.between('2025-07-13','2025-07-17')]
    for name,seg in [('ALL',base),('paid',base[base.paid]),('organic',base[base.network=='Organic']),
                     ('Net-A us',base[(base.network=='Net-A')&(base.country=='us')]),('Net-A nonus',base[(base.network=='Net-A')&(base.country!='us')&base.paid]),
                     ('Net-B and',base[(base.network=='Net-B')&(base.platform=='android')]),('Net-B ios',base[(base.network=='Net-B')&(base.platform=='ios')]),
                     ('android',base[base.platform=='android']),('ios',base[base.platform=='ios'])]:
        row={}
        for typ in ['ad','iap','rev']:
            for a,b in [(7,120),(30,120),(30,180),(120,180)]:
                r,n,i=ratios(seg,f'{typ}_{b}',f'{typ}_{a}'); row[f'{typ}{a}->{b}']=round(r,2) if np.isfinite(r) else None
        print(name,'inst_total',int(seg.installs.sum()),row)
    # by install month for 30->120 rev ratio for paid
    p=base[base.paid]
    mo=p.groupby(p.install_date.dt.to_period('M')).apply(lambda x: pd.Series({'r30_120':x.loc[x.rev_120.notna(),'rev_120'].sum()/x.loc[x.rev_120.notna(),'rev_30'].sum() if x.rev_120.notna().any() else np.nan,
        'ad30_120':x.loc[x.ad_120.notna(),'ad_120'].sum()/x.loc[x.ad_120.notna(),'ad_30'].sum() if x.ad_120.notna().any() else np.nan,
        'r7_30':x.loc[x.rev_30.notna(),'rev_30'].sum()/x.loc[x.rev_30.notna(),'rev_7'].sum() if x.rev_30.notna().any() else np.nan,
        'r120_180':x.loc[x.rev_180.notna(),'rev_180'].sum()/x.loc[x.rev_180.notna(),'rev_120'].sum() if x.rev_180.notna().any() else np.nan,
        'n180':x.rev_180.notna().sum()}))
    print(mo.round(3))
    # curve: pooled paid mature (age>=180) cohorts per-install revenue at each horizon
    m180=p[p.rev_180.notna()]
    print('mature180 inst',m180.installs.sum(), {h: round(m180[f'ad_{h}'].sum()/m180.installs.sum(),3) for h in HZ},{h: round(m180[f'iap_{h}'].sum()/m180.installs.sum(),3) for h in HZ})
