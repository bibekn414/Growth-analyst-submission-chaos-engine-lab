import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',80); pd.set_option('display.max_rows',500)
for g in ['A','B']:
    print('======',g)
    co=pd.read_csv(f'data/Game{g}_cohorts.csv',parse_dates=['install_date'])
    r=pd.read_csv(f'data/Game{g}_telemetry_retention.csv',parse_dates=['install_date'])
    print(r.install_type.value_counts().to_dict(), r.shape)
    # MMP retention rate d1,d7,d30 for cohorts installed Jun 1 - Aug 15 (mature through d30), all sources; telemetry same window
    w=(co.install_date>='2025-06-01')&(co.install_date<='2025-08-15')
    m=co[w]; print('MMP d1',m.retained_d1.sum()/m.installs.sum(),'d7',m.retained_d7.sum()/m.installs.sum(),'d30',m.retained_d30.sum()/m.installs.sum())
    for typ in ['install','reinstall']:
        x=r[(r.install_date>='2025-06-01')&(r.install_date<='2025-08-15')&(r.install_type==typ)]
        print('TEL',typ,'users',x.cohort_users.sum(),'d1',x.active_day1.sum()/x.cohort_users.sum(),'d7',x.active_day7.sum()/x.cohort_users.sum(),'d30',x.active_day30.sum()/x.cohort_users.sum())
    # telemetry active_day > cohort_users?
    print('active>cohort', (r.active_day1>r.cohort_users).sum(), (r.active_day30>r.cohort_users).sum())
    print('tel zeros in mature: d30 zero for install_date<=2025-08-20 share', (r[(r.install_date<='2025-08-20')&(r.cohort_users>20)].active_day30==0).mean())
    # creatives
    cr=pd.read_csv(f'data/Game{g}_creatives_daily.csv',parse_dates=['date']); ca=pd.read_csv(f'data/Game{g}_creatives_catalog.csv')
    ua=pd.read_csv(f'data/Game{g}_ua_daily.csv',parse_dates=['date'])
    print('creatives rows',len(cr),'dupkey',cr.duplicated(['date','platform','country','network','campaign_id','creative_id']).sum())
    print(cr.groupby('network').agg(rows=('cost','size'),cost=('cost','sum'),inst=('installs_mmp','sum'),unk=('creative_id',lambda s:(s=='unknown').mean())).round(3))
    paid=ua[ua.network.str.startswith('Net-')]
    a=paid.groupby('network').agg(cost=('cost','sum'),inst=('installs_mmp','sum'),imp=('impressions_network_reported','sum')); b=cr[cr.network.str.startswith('Net-')].groupby('network').agg(cost=('cost','sum'),inst=('installs_mmp','sum'),imp=('impressions_network_reported','sum'))
    print((b/a).round(3))
    print('catalog',ca.shape); print(ca.groupby('network').size().to_dict()); print(ca.creative_type.value_counts().head(25))
    # creative ids in daily but not catalog
    print('ids not in catalog',(~cr.creative_id.isin(ca.creative_id)&(cr.creative_id!='unknown')).sum())
    print('cohort_installs mismatch with installs_mmp',(cr.cohort_installs!=cr.installs_mmp).mean())
