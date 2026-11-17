import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',500)
ua=pd.read_csv('data/GameA_ua_daily.csv',parse_dates=['date'])
paid=ua[ua.network.isin(['Net-A','Net-B','Net-C','Net-D'])].copy()
# installs with zero spend
z=paid[(paid.cost==0)&(paid.installs_mmp>0)]
print('zero-cost installs rows',len(z),'installs',z.installs_mmp.sum(),'of',paid.installs_mmp.sum())
print(z.groupby(['network','country']).installs_mmp.sum().sort_values(ascending=False).head(15))
print(z.groupby(z.date.dt.to_period('M')).installs_mmp.sum())
# weekly CPI Net-A US android, ratio net/mmp
def wk(df,name):
    w=df.groupby(pd.Grouper(key='date',freq='W-SUN')).agg(cost=('cost','sum'),inst=('installs_mmp','sum'),net=('installs_network_reported','sum'),imp=('impressions_network_reported','sum'),clk=('clicks_network_reported','sum'))
    w['cpi']=w.cost/w.inst; w['net/mmp']=w.net/w.inst; w['cpm']=w.cost/w.imp*1000; w['ctr']=w.clk/w.imp; w['ipm']=w.inst/w.imp*1000
    print('---',name); print(w.round(3).to_string())
wk(paid[(paid.network=='Net-A')&(paid.country=='us')],'NetA us')
wk(paid[(paid.network=='Net-A')&(paid.country!='us')],'NetA non-us')
for n,p in [('Net-B','android'),('Net-B','ios'),('Net-C','android'),('Net-D','android')]:
    wk(paid[(paid.network==n)&(paid.platform==p)],f'{n} {p}')
# outlier daily cost
d=paid.groupby(['date','network']).agg(cost=('cost','sum'),inst=('installs_mmp','sum')).reset_index()
d['cpi']=d.cost/d.inst
print(d.sort_values('cpi',ascending=False).head(10))
# daily missing dates
alld=pd.date_range('2025-01-06','2025-09-28')
for n in ['Net-A','Net-B','Net-C','Net-D']:
    s=set(paid[paid.network==n].date); print(n,'missing days since first',len([x for x in alld if x not in s and x>=min(s)]))
# extreme rows
print(paid.sort_values('cost',ascending=False).head(8))
print(paid[paid.installs_mmp>0].assign(cpi=lambda d:d.cost/d.installs_mmp).sort_values('cpi',ascending=False).head(8))
