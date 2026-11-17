import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
t=pd.read_csv('data/GameA_telemetry_daily.csv',parse_dates=['date'])
print(t.shape,t.date.min(),t.date.max()); print(t.isna().sum()[lambda s:s>0])
print(t.platform.value_counts().to_dict()); print(t.country.fillna('<blank>').value_counts().head(8).to_dict())
print('dup',t.duplicated(['date','platform','country']).sum())
t['ad_rev']=t.banner_rev+t.interstitial_rev+t.rewarded_rev
d=t.groupby('date').agg(dau=('dau','sum'),ni=('new_installs','sum'),nr=('new_reinstalls','sum'),ad=('ad_rev','sum'),iap=('iap_rev','sum'),pay=('payers','sum'),sm=('session_minutes','sum'),rew=('rewarded_imps','sum'),ban=('banner_imps','sum'),inter=('interstitial_imps','sum'))
d['ad_per_dau']=d.ad/d.dau; d['iap_per_dau']=d.iap/d.dau
w=d.resample('W-SUN').agg({'dau':'mean','ni':'sum','nr':'sum','ad':'sum','iap':'sum','ad_per_dau':'mean','iap_per_dau':'mean','pay':'sum'})
print(w.round(3).to_string())
# daily detail Jun 15 - Jul 20
print(d.loc['2025-06-14':'2025-07-20',['dau','ni','ad','iap','ad_per_dau']].round(3).to_string())
# MMP installs vs telemetry new installs
ua=pd.read_csv('data/GameA_ua_daily.csv',parse_dates=['date'])
m=ua.groupby('date').installs_mmp.sum()
x=pd.concat([m,d.ni,d.nr],axis=1).dropna(); x.columns=['mmp','tel_new','tel_reinst']
x['ratio']=x.tel_new/x.mmp
print(x.resample('W-SUN').sum().assign(ratio=lambda z:z.tel_new/z.mmp).round(3).to_string())
