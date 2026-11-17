import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
ub=pd.read_csv('data/GameB_ua_daily.csv',parse_dates=['date'])
a=ub[ub.network=='Net-A']
print(a.groupby('campaign_id').agg(cost=('cost','sum'),mmp=('installs_mmp','sum'),net=('installs_network_reported','sum'),imp=('impressions_network_reported','sum'),clk=('clicks_network_reported','sum'),rows=('cost','size')).assign(ratio=lambda d:d.net/d.mmp))
print(a.groupby(['platform']).agg(cost=('cost','sum'),mmp=('installs_mmp','sum'),net=('installs_network_reported','sum')))
a2=a.groupby(pd.Grouper(key='date',freq='W-SUN')).agg(cost=('cost','sum'),mmp=('installs_mmp','sum'),net=('installs_network_reported','sum'),imp=('impressions_network_reported','sum'))
a2['ratio']=a2.net/a2.mmp; a2['cpi_mmp']=a2.cost/a2.mmp
print(a2.round(2).to_string())
print(a.groupby('country').agg(cost=('cost','sum'),mmp=('installs_mmp','sum'),net=('installs_network_reported','sum')).assign(ratio=lambda d:d.net/d.mmp).sort_values('net',ascending=False).head(10))
# B monthly spend by network / platform
paid=ub[ub.network.str.startswith('Net-')].copy(); paid['m']=paid.date.dt.to_period('M')
print(paid.pivot_table(index='m',columns='network',values='cost',aggfunc='sum').round(0))
print(paid.pivot_table(index='m',columns='network',values='installs_mmp',aggfunc='sum'))
print(paid.groupby(['network','platform']).agg(cost=('cost','sum'),inst=('installs_mmp','sum')).assign(cpi=lambda d:d.cost/d.inst))
w=paid[paid.date>='2025-08-01'].groupby([pd.Grouper(key='date',freq='W-SUN'),'network']).cost.sum().unstack().round(0); print(w)
sep=paid[(paid.date>='2025-09-01')&(paid.date<='2025-09-28')]
c=sep.groupby(['network','platform','country']).agg(cost=('cost','sum'),inst=('installs_mmp','sum')).assign(cpi=lambda d:d.cost/d.inst).sort_values('cost',ascending=False)
print(c.head(25).round(2)); print('weekly total',c.cost.sum()/4)
print(ub[(ub.cost==0)&(ub.installs_mmp>0)&ub.network.str.startswith('Net-')].groupby(['network','country']).installs_mmp.sum().sort_values(ascending=False).head(10))
# Game A zero-cost installs value
co=pd.read_csv('data/GameA_cohorts.csv',parse_dates=['install_date'])
for c_ in ['ir','sy','be','cz']:
    x=co[(co.network=='Net-A')&(co.country==c_)]
    print(c_,x.installs.sum(),'ad_d7/inst',x.ad_rev_d7.sum()/x.installs.sum(),'ret7',x.retained_d7.sum()/x.installs.sum(), 'dates',x.install_date.min().date(),x.install_date.max().date())
x=co[(co.network=='Net-A')&(co.country=='ir')]; print(x.groupby(x.install_date.dt.to_period('M')).installs.sum())
