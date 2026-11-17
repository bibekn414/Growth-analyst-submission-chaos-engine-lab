import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',200)
co,_=clean_cohorts('A')
d=co[(co.network=='Net-D')&(co.country=='us')&(co.installs>0)].copy()
print(d.install_date.min(), d.install_date.max(), len(d), d.installs.sum())
w=d.groupby(pd.Grouper(key='install_date',freq='W-MON',label='left')).apply(lambda x: pd.Series({
 'inst':x.installs.sum(),'cpi':x.cost.sum()/x.installs.sum(),
 'ad7pi':x.ad_7.sum()/x.installs[x.ad_7.notna()].sum() if x.ad_7.notna().any() else np.nan,
 'iap7pi':x.iap_7.sum()/x.installs[x.iap_7.notna()].sum() if x.iap_7.notna().any() else np.nan,
 'ad30pi':x.ad_30.sum()/x.installs[x.ad_30.notna()].sum() if x.ad_30.notna().any() else np.nan,
 'iap30pi':x.iap_30.sum()/x.installs[x.iap_30.notna()].sum() if x.iap_30.notna().any() else np.nan,
 'ret1':x.retained_d1.sum()/x.installs[x.retained_d1.notna()].sum(),'ret7':x.retained_d7.sum()/x.installs[x.retained_d7.notna()].sum() if x.retained_d7.notna().any() else np.nan,
 'payers_d0':x.payers_d0.sum()/x.installs.sum()}))
print(w.round(3))
# concentration: share of d30 IAP from top 5 cohort-days
m=d[d.iap_30.notna()]
print('Net-D d30 IAP total',m.iap_30.sum(),'top5 cohorts share',m.iap_30.nlargest(5).sum()/m.iap_30.sum(), 'n cohorts',len(m))
print(m.sort_values('iap_30',ascending=False)[['install_date','installs','iap_30','payers_d0','payers_d7','payers_d30','ad_30']].head(8))
# compare with Net-A US, same period
a=co[(co.network=='Net-A')&(co.country=='us')&(co.platform=='android')&(co.install_date>='2025-07-31')&(co.installs>0)]
m=a[a.iap_30.notna()]
print('Net-A US d30 iap/inst',m.iap_30.sum()/m.installs.sum(),'ad/inst',m.ad_30.sum()/m.installs.sum())
m=d[d.iap_30.notna()]
print('Net-D US d30 iap/inst',m.iap_30.sum()/m.installs.sum(),'ad/inst',m.ad_30.sum()/m.installs.sum())
# organic US android
o=co[(co.network=='Organic')&(co.country=='us')&(co.platform=='android')&(co.install_date>='2025-07-31')&co.iap_30.notna()]
print('Organic US d30 iap/inst',o.iap_30.sum()/o.installs.sum(),'ad/inst',o.ad_30.sum()/o.installs.sum())
# raw column check
print('raw rev_d30 per inst Net-D', d[d.age>=30].raw_rev_30.sum()/d[d.age>=30].installs.sum())
print('telemetry iap per payer US recent',)
