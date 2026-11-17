import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
t=pd.read_csv('data/GameA_telemetry_daily.csv',parse_dates=['date'])
t['ad_rev']=t.banner_rev+t.interstitial_rev+t.rewarded_rev
t['imps']=t.banner_imps+t.interstitial_imps+t.rewarded_imps
s=t[(t.date>='2025-07-14')&(t.date<='2025-07-16')]
print(s.groupby(['platform']).agg(ad=('ad_rev','sum'),b=('banner_rev','sum'),i=('interstitial_rev','sum'),r=('rewarded_rev','sum'),imps=('imps','sum'),dau=('dau','sum')))
print(s.groupby('country').ad_rev.sum().sort_values(ascending=False).head(10))
base=t[(t.date>='2025-07-07')&(t.date<='2025-07-13')]
print('baseline per day',base.groupby('date').agg(ad=('ad_rev','sum'),imps=('imps','sum')).mean())
print(s.groupby('date').agg(ad=('ad_rev','sum'),imps=('imps','sum'),b=('banner_rev','sum'),i=('interstitial_rev','sum'),r=('rewarded_rev','sum'),bi=('banner_imps','sum'),ii=('interstitial_imps','sum'),ri=('rewarded_imps','sum')))
# ecpm per type baseline vs spike
for nm,df in [('base',base),('spike',s)]:
    print(nm,'ecpm banner',df.banner_rev.sum()/df.banner_imps.sum()*1000,'inter',df.interstitial_rev.sum()/df.interstitial_imps.sum()*1000,'rew',df.rewarded_rev.sum()/df.rewarded_imps.sum()*1000)
# which rows are outliers, by country-platform
t['ecpm_r']=t.rewarded_rev/t.rewarded_imps.replace(0,np.nan)*1000
print(s.sort_values('ad_rev',ascending=False).head(10)[['date','platform','country','dau','ad_rev','imps','rewarded_rev','rewarded_imps']])
# IAP anomalies
iap=t.groupby(['date']).iap_rev.sum()
print(iap[iap>3000])
big=t[t.iap_rev>2000].sort_values('iap_rev',ascending=False)
print(big[['date','platform','country','dau','payers','iap_rev']].head(30)); print(len(big))
print(t[t.iap_rev>2000].groupby(['country']).agg(n=('iap_rev','size'),iap=('iap_rev','sum'),payers=('payers','sum')).sort_values('iap',ascending=False).head(15))
print('IAP per payer distribution'); r=(t.iap_rev/t.payers.replace(0,np.nan)).describe(); print(r)
print('rows iap>0 with payers==0', ((t.iap_rev>0)&(t.payers==0)).sum(), t[(t.iap_rev>0)&(t.payers==0)].iap_rev.sum())
print(t[(t.iap_rev>0)&(t.payers==0)].sort_values('iap_rev',ascending=False).head(8)[['date','platform','country','dau','payers','iap_rev']])
# telemetry totals
print('total tel ad',t.ad_rev.sum(),'iap',t.iap_rev.sum(),'iap excluding spikes (<2000/row)',t[t.iap_rev<2000].iap_rev.sum())
print('blank country rows',t.country.isna().sum(), t[t.country.isna()].dau.sum(), t.dau.sum())
# dau vs new_installs inconsistent: new_installs > dau?
print('new_installs>dau',(t.new_installs>t.dau).sum(), 'payers>dau',(t.payers>t.dau).sum())
