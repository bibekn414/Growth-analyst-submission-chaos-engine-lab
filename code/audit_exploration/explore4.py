import pandas as pd, numpy as np, sys
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
g=sys.argv[1]
co=pd.read_csv(f'data/Game{g}_cohorts.csv',parse_dates=['install_date'])
ua=pd.read_csv(f'data/Game{g}_ua_daily.csv',parse_dates=['date'])
print(co.shape, co.install_date.min(), co.install_date.max())
print(co.isna().sum()[lambda s:s>0])
print('dup key',co.duplicated(['install_date','platform','country','network','campaign_id']).sum(),'full dup',co.duplicated().sum())
# installs match with UA
k=['install_date','platform','country','network','campaign_id']
m=co.merge(ua.rename(columns={'date':'install_date'}),on=k,how='outer',indicator=True)
print(m._merge.value_counts())
mm=m[m._merge=='both']; print('installs mismatch rows',(mm.installs!=mm.installs_mmp).sum(),'sum diff',(mm.installs-mm.installs_mmp).sum())
print(m[m._merge!='both'].groupby(['_merge','network']).size())
# retention > installs
for c in ['retained_d1','retained_d3','retained_d7','retained_d14','retained_d30','retained_d60','retained_d90','retained_d120']:
    print(c,'> installs',(co[c]>co.installs).sum(), end=' | ')
print()
# monotonic cumulative revenue
ad=['ad_rev_d0','ad_rev_d1','ad_rev_d3','ad_rev_d7','ad_rev_d14','ad_rev_d30','ad_rev_d60','ad_rev_d90','ad_rev_d120','ad_rev_d180']
iap=['iap_rev_d0','iap_rev_d1','iap_rev_d3','iap_rev_d7','iap_rev_d14','iap_rev_d30','iap_rev_d60','iap_rev_d90','iap_rev_d120','iap_rev_d180']
for cols,nm in [(ad,'ad'),(iap,'iap')]:
    d=co[cols].diff(axis=1).iloc[:,1:]
    print(nm,'non-monotonic rows',(d<-1e-6).any(axis=1).sum(), 'neg values',(co[cols]<0).any(axis=1).sum())
# by install date maturity: share with nonzero
co['mon']=co.install_date.dt.to_period('M')
agg=co.groupby('mon')[['installs']+['ad_rev_d30','ad_rev_d120','ad_rev_d180','iap_rev_d30','iap_rev_d120','iap_rev_d180','ad_rev_all_sources_d30']].sum()
for c in ['ad_rev_d30','ad_rev_d120','ad_rev_d180','iap_rev_d30','iap_rev_d120','iap_rev_d180','ad_rev_all_sources_d30']: agg[c+'/inst']=agg[c]/agg.installs
print(agg.filter(like='/inst').round(3))
# weekly last 150 days: d30 per install, d120 per install, to see maturity truncation
w=co.groupby(pd.Grouper(key='install_date',freq='W-SUN'))[['installs','ad_rev_d7','ad_rev_d30','ad_rev_d60','ad_rev_d90','ad_rev_d120','ad_rev_d180','iap_rev_d30','iap_rev_d120','iap_rev_d180','retained_d1','retained_d7','retained_d30','retained_d120']].sum()
for c in w.columns[1:]: w[c]=w[c]/w.installs
print(w.tail(40).round(3))
# ad_rev vs all sources
print('all_sources/med ratio d30', (co.ad_rev_all_sources_d30.sum()/co.ad_rev_d30.sum()), 'd7',(co.ad_rev_all_sources_d7.sum()/co.ad_rev_d7.sum()), 'd0',(co.ad_rev_all_sources_d0.sum()/co.ad_rev_d0.sum()))
r=co.groupby(['network'])[['ad_rev_d7','ad_rev_all_sources_d7','ad_rev_d30','ad_rev_all_sources_d30']].sum(); r['ratio7']=r.ad_rev_all_sources_d7/r.ad_rev_d7; r['ratio30']=r.ad_rev_all_sources_d30/r.ad_rev_d30; print(r.round(3))
r=co.groupby(['mon'])[['ad_rev_d30','ad_rev_all_sources_d30']].sum(); r['ratio']=r.ad_rev_all_sources_d30/r.ad_rev_d30; print(r.round(3))
