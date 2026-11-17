import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
t=pd.read_csv('data/GameA_telemetry_daily.csv',parse_dates=['date'])
t['pp']=t.iap_rev/t.payers.replace(0,np.nan)
# per-payer median by country (Jun 10 - Sep 28 as clean reference)
ref=t[(t.date>='2025-06-10')&t.payers.gt(0)]
med=ref.groupby('country').pp.median()
print(med[['kr','jp','us','de','es','in','gb','fr','br','mx']])
t=t.merge(med.rename('med_pp'),on='country',how='left')
t['rel']=t.pp/t.med_pp
x=t[(t.rel>8)&(t.payers>0)].sort_values('date')
print(len(x)); print(x[['date','platform','country','payers','iap_rev','pp','med_pp','rel']].head(70).to_string())
print(x.groupby(x.date.dt.to_period('M')).size())
print(x.groupby('country').size().sort_values(ascending=False).head(10))
# by date for May 24 - Jun 8: kr / us per-payer
for c in ['kr','us','jp','de']:
    print(c); print(t[(t.country==c)&(t.platform=='android')&(t.date>='2025-05-24')&(t.date<='2025-06-08')][['date','dau','payers','iap_rev','pp']].round(1).to_string())
