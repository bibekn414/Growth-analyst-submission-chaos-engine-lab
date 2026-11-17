import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
co=pd.read_csv('data/GameA_cohorts.csv',parse_dates=['install_date'])
ad=['ad_rev_d0','ad_rev_d1','ad_rev_d3','ad_rev_d7','ad_rev_d14','ad_rev_d30','ad_rev_d60','ad_rev_d90','ad_rev_d120','ad_rev_d180']
d=co[ad].diff(axis=1).iloc[:,1:]
print('decreases by step:',(d<-1e-6).sum().to_dict())
print('size of decreases d120->d180', d['ad_rev_d180'][d['ad_rev_d180']<-1e-6].describe())
x=co[d['ad_rev_d180']<-1e-6]; print(x.install_date.dt.to_period('M').value_counts().sort_index())
# maturity: age as of 2025-09-30
asof=pd.Timestamp('2025-09-30')
co['age']=(asof-co.install_date).dt.days
# For each horizon N, rows where age<N+? are immature; check whether value equals prior horizon (carry forward)
for a,b,N in [('ad_rev_d30','ad_rev_d60',60),('ad_rev_d60','ad_rev_d90',90),('ad_rev_d90','ad_rev_d120',120),('ad_rev_d120','ad_rev_d180',180)]:
    same=(co[b]==co[a])&(co[a]>0)
    print(N,'same-as-prev share by age bucket'); print(pd.cut(co.age,[0,10,20,30,45,60,75,90,105,120,150,180,300]).pipe(lambda c: same.groupby(c,observed=True).mean()).round(2).to_string())
# retained zero by age
for N in [30,60,90,120]:
    r=co[co.installs>=20]
    print('retained_d%d zero share by age'%N, r.groupby(pd.cut(r.age,[0,N-10,N,N+5,N+10,N+30,400]),observed=True).apply(lambda g:(g[f'retained_d{N}']==0).mean()).round(2).to_dict())
# spikes: cohort-level revenue per install outliers
co['adpi30']=co.ad_rev_d30/co.installs; co['iappi30']=co.iap_rev_d30/co.installs; co['adpi7']=co.ad_rev_d7/co.installs
big=co[co.installs>=30]
print(big.sort_values('iappi30',ascending=False)[['install_date','platform','country','network','campaign_id','installs','ad_rev_d30','iap_rev_d30','iappi30','payers_d30']].head(12))
print(big.sort_values('adpi7',ascending=False)[['install_date','platform','country','network','campaign_id','installs','ad_rev_d0','ad_rev_d7','ad_rev_d30','adpi7']].head(12))
# d7->d30 jumps
co['j']=co.ad_rev_d30/co.ad_rev_d7.replace(0,np.nan)
print(co[(co.installs>=30)].sort_values('j',ascending=False)[['install_date','country','network','installs','ad_rev_d7','ad_rev_d14','ad_rev_d30','j']].head(15))
# weekly median ratio
print(co[co.installs>=30].groupby(pd.Grouper(key='install_date',freq='W-SUN')).j.median().round(2).to_string())
