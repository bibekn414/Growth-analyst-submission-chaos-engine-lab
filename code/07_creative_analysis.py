"""Q3a: what the ad-level data says: spend, IPM, early value by creative type and network (Game A)."""
import sys; sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *
pd.set_option('display.width',260); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
cr=pd.read_csv(f'{DATA}/GameA_creatives_daily.csv',parse_dates=['date']); ca=pd.read_csv(f'{DATA}/GameA_creatives_catalog.csv')
cr=cr.merge(ca[['creative_id','creative_type','first_seen','last_seen']],on='creative_id',how='left')
cr['creative_type']=cr.creative_type.fillna('unknown (no id reported)')
paid=cr[cr.network.isin(['Net-A','Net-B','Net-C','Net-D'])&(cr.cost>0)].copy()
paid['age']=(LAST-paid.date).dt.days
# value metrics: mature (>=7d), after the IAP anomaly window and outside the ad spike (installs 7-16 Jul affect d7)
val=paid[(paid.age>=7)&(paid.date>='2025-06-09')&(~paid.date.between('2025-07-07','2025-07-16'))].copy()
val['rev7']=val.ad_rev_d7+val.iap_rev_d7
def agg(g):
    return pd.Series({'spend':g.cost.sum(),'installs':g.installs_mmp.sum(),'cpi':g.cost.sum()/max(g.installs_mmp.sum(),1),
        'ipm':g.installs_mmp.sum()/g.impressions_network_reported.sum()*1000 if g.impressions_network_reported.sum()>0 else np.nan,
        'cpm':g.cost.sum()/g.impressions_network_reported.sum()*1000 if g.impressions_network_reported.sum()>0 else np.nan,
        'roas_d7':g.rev7.sum()/g.cost.sum(),'rev7_per_inst':g.rev7.sum()/max(g.installs_mmp.sum(),1),
        'ret_d1':g.retained_d1.sum()/max(g.cohort_installs.sum(),1),'ret_d7':g.retained_d7.sum()/max(g.cohort_installs.sum(),1)})
# spend share uses all paid rows (full history)
sp=paid.groupby(['network','creative_type']).cost.sum().rename('spend_all')
sh=(sp/sp.groupby(level=0).transform('sum')).rename('spend_share_all')
t=val.groupby(['network','creative_type']).apply(agg)
t=t.join(sh).join(sp)
t['n_creatives']=paid.groupby(['network','creative_type']).creative_id.nunique()
t=t.sort_values(['network','spend'],ascending=[True,False])
print(t[['n_creatives','spend_all','spend_share_all','spend','installs','cpi','ipm','roas_d7','rev7_per_inst','ret_d1','ret_d7']].round(3).to_string())
t.reset_index().to_csv(f'{OUT}/creative_types_A.csv',index=False)
# Sep creatives: how many were active in the last 28 days (current 'worn' inventory)
act=paid[paid.date>='2025-09-01'].groupby('network').creative_id.nunique(); print('active creative ids in Sep:',act.to_dict())
# per-creative within Net-B/C: top / bottom by D7 ROAS with decent spend
for net in ['Net-B','Net-C']:
    c=val[val.network==net].groupby(['creative_id','creative_type']).apply(agg).reset_index()
    c=c[c.spend>=1500].sort_values('roas_d7',ascending=False)
    print(net,'creatives with >=$1.5k value-window spend:',len(c)); print(c[['creative_id','creative_type','spend','cpi','ipm','roas_d7','rev7_per_inst']].round(2).head(8).to_string(index=False)); print(c[['creative_id','creative_type','spend','cpi','ipm','roas_d7','rev7_per_inst']].round(2).tail(5).to_string(index=False))
# IPM vs value: correlation across creatives (is the cheap installer the valuable one?)
for net in ['Net-B','Net-C']:
    c=val[val.network==net].groupby('creative_id').apply(agg); c=c[c.spend>=800]
    print(net,'corr(IPM, rev7_per_inst)=%.2f ; corr(IPM, ROAS_d7)=%.2f ; n=%d'%(c.ipm.corr(c.rev7_per_inst),c.ipm.corr(c.roas_d7),len(c)))
# wear-out evidence: CPI vs cumulative impressions per creative (Net-B, Net-C)
for net in ['Net-B','Net-C','Net-D','Net-A']:
    d=paid[paid.network==net].sort_values('date').copy()
    d['cum_imp']=d.groupby('creative_id').impressions_network_reported.cumsum()
    d['b']=pd.cut(d.cum_imp,[0,25e3,50e3,100e3,200e3,400e3,1e6,3e6,1e9])
    e=d.groupby('b',observed=True).apply(lambda g: pd.Series({'cpi':g.cost.sum()/max(g.installs_mmp.sum(),1),'ipm':g.installs_mmp.sum()/g.impressions_network_reported.sum()*1000,'imps':g.impressions_network_reported.sum()}))
    print(net,'CPI by cumulative impressions of the creative'); print(e.round(3).to_string())
