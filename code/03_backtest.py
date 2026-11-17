"""Time-split backtests and the 2x2 cross-game test (A on A, A on B, B on B, B on A).
Honest as-of design:
  * curves are fitted at AS-OF date 2025-06-30 using only cohorts old enough to have the
    target horizon at that date (age >= 120 on 30 Jun  ->  installs on/before 2 Mar);
  * test cohorts are installs 3 Mar - 31 May (age 30-119 on 30 Jun). Predictions use ONLY
    their readings available on 30 Jun, optionally capped to an early horizon (7/14/30/60);
  * the truth is their actual D120 (known today). ROAS error = revenue error (cost is known).
"""
import sys, json
sys.path.insert(0, 'code')
import numpy as np, pandas as pd
from common import *
from model import *

pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
ASOF_T = pd.Timestamp('2025-06-30')
TEST_LO, TEST_HI = pd.Timestamp('2025-03-03'), pd.Timestamp('2025-05-31')

def prep(g):
    co, diag = clean_cohorts(g)
    co, groups = add_cells(co, g)
    return co, groups

def windows(co):
    d = co[(co.paid) & co.install_date.between(TEST_LO, TEST_HI) & (co.installs > 0)].copy()
    d['mon'] = d.install_date.dt.to_period('M').astype(str)
    return d

def actual(d, T):
    return float((d[f'ua_{T}'] + d[f'ui_{T}']).sum())

def evaluate(curve, test_df, T, max_h, min_n=300):
    rows = []
    for (cell, mon), d in test_df.groupby(['cell', 'mon']):
        if d.installs.sum() < min_n:
            continue
        # keep only cohorts with an early reading at the as-of date
        wt = window_table(d, curve, T_list=(T,), min_h=3, boots=False, max_h=max_h, form_spread=False)
        pr = wt[f'rev_{T}']
        ac = actual(d[(curve.asof - d.install_date).dt.days >= 3], T)
        if pr > 0 and ac > 0:
            rows.append(dict(cell=cell, mon=mon, installs=wt['installs'], pred=pr, act=ac, lr=np.log(ac / pr)))
    return pd.DataFrame(rows)

def summarize(r):
    if len(r) == 0:
        return dict(n=0)
    w = r.installs / r.installs.sum()
    return dict(n=len(r), bias_pct=100 * (np.exp(np.average(r.lr, weights=w)) - 1),
                mape_pct=100 * np.median(np.abs(np.exp(r.lr) - 1)),
                wape_pct=100 * (np.abs(r.act - r.pred).sum() / r.act.sum()),
                sd_log=r.lr.std(ddof=1) if len(r) > 2 else np.nan)

if __name__ == '__main__':
    data = {g: prep(g) for g in 'AB'}
    curves = {g: Curve(data[g][0], ASOF_T, halflife=60.0) for g in 'AB'}
    curves_flat = {g: Curve(data[g][0], ASOF_T, halflife=1e9) for g in 'AB'}
    curves_nonet = {g: Curve(data[g][0], ASOF_T, halflife=60.0, use_network=False) for g in 'AB'}
    tests = {g: windows(data[g][0]) for g in 'AB'}
    res = []
    allr = {}
    for train in 'AB':
        for test in 'AB':
            for T in [120]:
                for mh in [7, 14, 30, 60]:
                    r = evaluate(curves[train], tests[test], T, mh)
                    s = summarize(r); s.update(train=train, test=test, T=T, max_h=mh, variant='halflife60')
                    res.append(s); allr[(train, test, T, mh)] = r
            # shape-only variants for the same test
    # flat weights comparison, same-game only
    for g in 'AB':
        for mh in [7, 30]:
            r = evaluate(curves_flat[g], tests[g], 120, mh)
            s = summarize(r); s.update(train=g, test=g, T=120, max_h=mh, variant='flat'); res.append(s)
    for g in 'AB':
        for mh in [7, 30]:
            r = evaluate(curves_nonet[g], tests[g], 120, mh)
            s = summarize(r); s.update(train=g, test=g, T=120, max_h=mh, variant='platform-only'); res.append(s)
    out = pd.DataFrame(res)[['variant','train','test','T','max_h','n','bias_pct','mape_pct','wape_pct','sd_log']]
    print(out.round(1).to_string(index=False))
    out.to_csv(f'{OUT}/backtest_2x2.csv', index=False)
    # save residual tables for later noise calibration
    pd.concat([r.assign(train=k[0], test=k[1], T=k[2], max_h=k[3]) for k, r in allr.items()]).to_csv(f'{OUT}/backtest_residuals.csv', index=False)
