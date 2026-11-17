import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
LAST=pd.Timestamp('2025-09-28')
co=pd.read_csv('data/GameA_cohorts.csv',parse_dates=['install_date'])
co=co[co.installs>=30].copy(); co['age']=(LAST-co.install_date).dt.days   # age = days of data after install day
# exact-equality of consecutive horizons by age (ad revenue), only rows w/ ad rev>0
pairs=[('ad_rev_d14','ad_rev_d30',30),('ad_rev_d30','ad_rev_d60',60),('ad_rev_d60','ad_rev_d90',90),('ad_rev_d90','ad_rev_d120',120)]
for a,b,N in pairs:
    eq=(co[a]==co[b])
    s=eq.groupby(co.age).mean()
    # show ages around N
    print(b,'equal-to-prev share by age:',{int(k):round(v,2) for k,v in s.loc[N-8:N+6].items()})
# d180 vs d120 equality by age around 180
eq=(co.ad_rev_d120.round(3)==co.ad_rev_d180.round(3)); s=eq.groupby(co.age).mean(); print('d180~d120 by age',{int(k):round(v,2) for k,v in s.loc[165:190].items()})
# retained zeros
for N in [30,60,90,120]:
    z=(co[f'retained_d{N}']==0).groupby(co.age).mean(); print('ret',N,{int(k):round(v,2) for k,v in z.loc[N-4:N+4].items()})
# IAP increments per install
iap=['iap_rev_d0','iap_rev_d1','iap_rev_d3','iap_rev_d7','iap_rev_d14','iap_rev_d30','iap_rev_d60','iap_rev_d90','iap_rev_d120','iap_rev_d180']
inc=co[iap].diff(axis=1); inc.iloc[:,0]=co[iap[0]]
pi=inc.div(co.installs,axis=0)
print(pi.describe(percentiles=[.5,.9,.99,.999]).T.round(3))
big=pi.max(axis=1).sort_values(ascending=False).head(15)
print(co.loc[big.index,['install_date','platform','country','network','installs']].assign(maxinc=big))
