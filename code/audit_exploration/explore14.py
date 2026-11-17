import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',200)
for g in ['B','A']:
    co,_=clean_cohorts(g); co,groups=add_cells(co,g)
    d=co[co.paid & co.rev_120.notna() & co.rev_30.notna() & ~co.install_date.between('2025-07-13','2025-07-17')].copy()
    d['mon']=d.install_date.dt.to_period('M').astype(str)
    d['us']=np.where(d.country=='us','US','nonUS')
    def r(x): return pd.Series({'inst':x.installs.sum(),'r30_120':x.rev_120.sum()/x.rev_30.sum(),'rev30_pi':x.rev_30.sum()/x.installs.sum(),'rev120_pi':x.rev_120.sum()/x.installs.sum()})
    print('=====',g)
    print(d.groupby(['us','mon']).apply(r).round(3).to_string())
    print(d.groupby(['network','platform','mon']).apply(r).round(3).query('inst>1500').to_string())
    # Retention-based: retention d30 vs d120
    d['ret']=d.retained_d120/d.retained_d30.replace(0,np.nan)
