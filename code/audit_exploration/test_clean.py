import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',200)
for g in ['A','B']:
    co,diag=clean_cohorts(g)
    print('=====',g,diag)
    m=co[(co.install_date>='2025-05-25')&(co.install_date<='2025-08-10')]
    w=m.groupby(pd.Grouper(key='install_date',freq='W-SUN')).apply(lambda x: pd.Series({
        'inst':x.installs.sum(),
        'raw_ad30':x.ad_rev_d30.sum()/x.installs.sum(),
        'cln_ad30':x.ad_30.sum()/x.installs[x.ad_30.notna()].sum(),
        'raw_iap30':x.iap_rev_d30.sum()/x.installs.sum(),
        'cln_iap30':x.iap_30.sum()/x.installs[x.iap_30.notna()].sum(),
        'raw_ad120':x.ad_rev_d120.sum()/x.installs.sum(),'cln_ad120':x.ad_120.sum()/max(1,x.installs[x.ad_120.notna()].sum())}))
    print(w.round(3))
