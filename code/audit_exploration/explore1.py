import pandas as pd, numpy as np, sys
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
D=sys.argv[1]
for g in ['A','B']:
    ua=pd.read_csv(f'{D}/Game{g}_ua_daily.csv',parse_dates=['date'])
    print('=====',g,'UA',ua.shape, ua.date.min(), ua.date.max())
    print(ua.dtypes.to_string())
    print(ua.isna().sum().to_string())
    print(ua.network.value_counts().to_string())
    print(ua.platform.value_counts().to_string())
    print(ua.country.fillna('<blank>').value_counts().head(25).to_string())
    print('dups full-row',ua.duplicated().sum(),' dups key',ua.duplicated(['date','platform','country','network','campaign_id']).sum())
    print(ua.describe().T.to_string())
    print((ua.cost<0).sum(),(ua.installs_mmp<0).sum())
    print(ua.groupby('network')[['cost','installs_mmp','installs_network_reported']].sum().assign(cpi=lambda d:d.cost/d.installs_mmp, ratio=lambda d:d.installs_network_reported/d.installs_mmp).to_string())
