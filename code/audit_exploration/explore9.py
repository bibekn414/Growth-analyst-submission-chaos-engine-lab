import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
for g in ['A','B']:
    print('=========== GAME',g)
    t=pd.read_csv(f'data/Game{g}_telemetry_daily.csv',parse_dates=['date'])
    t['ad_rev']=t.banner_rev+t.interstitial_rev+t.rewarded_rev
    d=t.groupby('date').agg(dau=('dau','sum'),ni=('new_installs','sum'),nr=('new_reinstalls','sum'),ad=('ad_rev','sum'),iap=('iap_rev','sum'),rew=('rewarded_rev','sum'),rimps=('rewarded_imps','sum'))
    d['ecpm_rew']=d.rew/d.rimps*1000; d['apd']=d.ad/d.dau
    w=d.resample('W-SUN').agg({'dau':'mean','ni':'sum','nr':'sum','ad':'sum','iap':'sum','apd':'mean','ecpm_rew':'mean'})
    print(w.round(3).to_string())
    # daily outliers in ad per dau / iap
    z=(d.apd/d.apd.rolling(15,center=True,min_periods=5).median())
    print('apd outlier days', d[(z>2.5)|(z<0.4)].round(3)[['dau','ad','apd','ecpm_rew']])
    print('iap>10x median days', d[d.iap>10*d.iap.median()].round(1)[['dau','iap']].head(20))
# reconciliation: cohort-implied calendar revenue vs telemetry, Game A & B, windows without anomalies
H=[0,1,3,7,14,30,60,90,120,180]
def implied(g,col_ad):
    co=pd.read_csv(f'data/Game{g}_cohorts.csv',parse_dates=['install_date'])
    # only cohorts with install >= 2025-04-01 and daily approx via interval uniform; limit to horizons <=30 (accurate) 
    cols=[f'{col_ad}_d{h}' for h in [0,7,30]]
    return co,cols
for g,win in [('A',('2025-06-10','2025-07-10')),('B',('2025-07-01','2025-09-15'))]:
    co=pd.read_csv(f'data/Game{g}_cohorts.csv',parse_dates=['install_date'])
    t=pd.read_csv(f'data/Game{g}_telemetry_daily.csv',parse_dates=['date'])
    t['ad_rev']=t.banner_rev+t.interstitial_rev+t.rewarded_rev
    tel=t[(t.date>=win[0])&(t.date<=win[1])].ad_rev.sum()
    # reconstruct calendar-day revenue for window from cohorts: use mediation ad_rev horizons 0,1,3,7,14,30,60,90,120 piecewise uniform increments
    hs=[0,1,3,7,14,30,60,90,120]
    def calendar_rev(prefix):
        tot=0.0
        for _,r in co.iterrows() if False else []: pass
        return tot
    # vectorised: for each interval (h_{k-1}+1..h_k) uniform; day0 interval = day0 only
    a,b=pd.Timestamp(win[0]),pd.Timestamp(win[1])
    out={}
    for prefix in ['ad_rev','ad_rev_all_sources']:
        tot=0.0
        avail=[h for h in hs if f'{prefix}_d{h}' in co.columns]
        prev=0; prevcol=None
        for h in avail:
            col=f'{prefix}_d{h}'
            inc=co[col]-(co[prevcol] if prevcol else 0)
            lo=0 if prevcol is None else prev+1; hi=h
            n=hi-lo+1
            # days offsets lo..hi; calendar dates install_date+off; count offsets with date in window
            cnt=np.zeros(len(co))
            for off in range(lo,hi+1):
                dt=co.install_date+pd.Timedelta(days=off)
                cnt+=((dt>=a)&(dt<=b)).astype(float).values
            tot+=(inc.values*cnt/n).sum()
            prev=h; prevcol=col
        out[prefix]=tot
    print(g,'window',win,'telemetry ad rev',round(tel),'cohort implied (mediation)',round(out['ad_rev']),'(all_sources, only d0,7,30)',round(out['ad_rev_all_sources']))
