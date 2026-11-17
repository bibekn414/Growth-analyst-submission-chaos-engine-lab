import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',500)
ua=pd.read_csv('data/GameA_ua_daily.csv',parse_dates=['date'])
paid=ua[ua.network.isin(['Net-A','Net-B','Net-C','Net-D'])]
# monthly spend by network
paid=paid.assign(m=paid.date.dt.to_period('M'))
print(paid.pivot_table(index='m',columns='network',values='cost',aggfunc='sum').round(0))
print(paid.pivot_table(index='m',columns='network',values='installs_mmp',aggfunc='sum'))
# by platform for network
print(paid.groupby(['network','platform']).agg(cost=('cost','sum'),inst=('installs_mmp','sum')).assign(cpi=lambda d:d.cost/d.inst))
# Sept baseline cells
sep=paid[(paid.date>='2025-09-01')&(paid.date<='2025-09-28')]
c=sep.groupby(['network','platform','country']).agg(cost=('cost','sum'),inst=('installs_mmp','sum'),netinst=('installs_network_reported','sum'),imps=('impressions_network_reported','sum')).assign(wk=lambda d:d.cost/4,cpi=lambda d:d.cost/d.inst).sort_values('cost',ascending=False)
print(c.round(2).to_string())
print('total weekly',c.wk.sum(), 'x12',c.wk.sum()*12)
print(sep.groupby(['network','platform']).cost.sum()/4)
# last date of spend by network/platform
print(paid.groupby(['network','platform']).date.agg(['min','max']))
# weekly spend recent
w=paid[paid.date>='2025-07-01'].groupby([pd.Grouper(key='date',freq='W-SUN'),'network']).cost.sum().unstack().round(0)
print(w)
print(ua.groupby('platform').cost.sum())
print(ua[ua.platform.isin(['android-tv','windows'])].groupby(['platform','network']).agg(i=('installs_mmp','sum'),c=('cost','sum')))
print('blank country', (ua.country.isna()|(ua.country=='')).sum())
