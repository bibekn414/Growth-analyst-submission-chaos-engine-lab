"""Q1 value tables: per cell (network x platform x country/group) for each game:
baseline weekly spend, CPI, D7/D30 ROAS (mature cohorts only), D120 and 1-year LTV/ROAS with 80% ranges.
Reference CPI = Sep-2025 baseline CPI for cells still buying, else the CPI of the value window."""
import sys, json
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *; from model import *
pd.set_option('display.width',280); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',300)
NP=json.load(open(f'{OUT}/noise_params.json'))
EXT={'A':{30:0.0,60:0.0,120:0.0,180:0.04,365:0.07},'B':{30:0.0,60:0.0,120:0.0,180:0.06,365:0.10}}   # extra sd (log) for extrapolation beyond 120d
RNG=np.random.default_rng(7)
NEW_NET_SD=0.08      # extra sd for networks with no mature (>=120d) cohorts of their own

def interval(wt, game, T, extra=0.0, q=(0.1,0.9), nsim=4000, rng=RNG):
    dr=wt[f'draws_{T}']
    n=max(wt['installs'],1)
    sd=np.sqrt(NP[game]['a']+NP[game]['b']/n+EXT[game][T]**2+extra**2)
    sims=rng.choice(dr,nsim)*np.exp(rng.normal(0,sd,nsim))
    return np.quantile(sims,q[0]),np.quantile(sims,q[1]),sims

def mature_own(curve, net, plat):
    """True if this network x platform has >= 1500 installs with D120 known in the model fit."""
    k=f'{net}|{plat}'
    N,D,I=curve.table[('ad','np',k,30,120)] if ('ad','np',k,30,120) in curve.table else (0,0,np.zeros(1))
    return float(np.sum(I))>=1500

def cell_row(name, d, base_d, curve, game):
    net,plat,mkt=name.split('|')
    row={'cell':name}
    row['baseline_weekly_spend']=base_d.cost.sum()/4.0
    bi=base_d.installs.sum()
    row['baseline_cpi']=base_d.cost.sum()/bi if bi>0 else np.nan
    row['baseline_installs_wk']=bi/4.0
    row['baseline_cpm']=(base_d.cost.sum()/base_d.impressions_network_reported.sum()*1000) if base_d.impressions_network_reported.sum()>0 else np.nan
    row['last_spend_date']=d.install_date.max().date()
    row['active']=row['baseline_weekly_spend']>0
    for h in [7,30]:
        m=d[(d[f'rev_{h}'].notna())&(d.cost>0)]
        row[f'roas_d{h}']=m[f'rev_{h}'].sum()/m.cost.sum() if m.cost.sum()>0 else np.nan
        row[f'n_inst_d{h}']=m.installs.sum()
    wt0=window_table(d,curve,T_list=(120,),min_h=7,boots=False)
    row['win_installs']=wt0['installs']; row['win_cost']=wt0['cost']
    row['win_cpi']=wt0['cost']/wt0['installs'] if wt0['installs']>0 else np.nan
    cpi_ref=row['baseline_cpi'] if row['active'] else row['win_cpi']
    row['cpi_ref']=cpi_ref
    extra=0.0 if mature_own(curve,net,plat) else NEW_NET_SD
    row['own_mature_curve']=extra==0.0
    wt=window_table(d,curve,T_list=(120,180,365),min_h=7)
    for T in [120,180,365]:
        lo,hi,sims=interval(wt,game,T,extra)
        n=wt['installs']
        row[f'ltv_{T}']=wt[f'rev_{T}']/n; row[f'ltv_{T}_lo']=lo/n; row[f'ltv_{T}_hi']=hi/n
        row[f'roas_{T}']=row[f'ltv_{T}']/cpi_ref; row[f'roas_{T}_lo']=row[f'ltv_{T}_lo']/cpi_ref; row[f'roas_{T}_hi']=row[f'ltv_{T}_hi']/cpi_ref
        row[f'ad_share_{T}']=wt[f'ad_{T}']/wt[f'rev_{T}'] if wt[f'rev_{T}']>0 else np.nan
        if T==120: row['p_roas120_ge1']=float(np.mean(sims/n/cpi_ref>=1))
        if T==365: row['p_roas365_ge1']=float(np.mean(sims/n/cpi_ref>=1))
    row['ltv_365_formrange']=f"{wt['form_lo']/wt['installs']:.2f}-{wt['form_hi']/wt['installs']:.2f}"
    row['ltv_120_ad']=wt['ad_120']/wt['installs']; row['ltv_120_iap']=wt['iap_120']/wt['installs']
    return row

def classify(r):
    if r['roas_120']>=1: g='A. pays back within 120 days'
    elif r['roas_365']>=1: g='B. pays back only within a year'
    else: g='C. does not pay back within a year'
    border = (0.2<=r['p_roas120_ge1']<=0.8) if r['roas_120']>=0 else False
    return g, ('borderline' if border else '')

def build(game, boot=200, curve_game=None, curve=None):
    """curve_game: use curves fitted on the OTHER game (cross-game application)."""
    co,diag=clean_cohorts(game); co,groups=add_cells(co,game)
    if curve is None:
        curve=Curve(co,LAST,halflife=60.0,boot=boot,seed=11)
    paid=co[co.paid & co.cell.notna() & (co.installs>0)].copy()
    rows=[]; wins={}
    mem=members(groups)
    for cell,d in paid.groupby('cell'):
        if cell.split('|')[2]=='no-spend': continue
        last=d.install_date.max()
        for span in (41, 83, 139):
            win=d[(d.install_date>last-pd.Timedelta(days=span))&(~d.install_date.between('2025-07-13','2025-07-17'))]
            if win[(LAST-win.install_date).dt.days>=7].installs.sum()>=500: break
        base_d=d[(d.install_date>='2025-09-01')&(d.install_date<='2025-09-28')]
        if win.installs.sum()<30: continue
        r=cell_row(cell,win,base_d,curve,game); r['countries']=','.join(mem.get(cell,[]))
        r['total_installs_hist']=d.installs.sum(); r['total_cost_hist']=d.cost.sum()
        cpi_ref=r['cpi_ref']; w=win.copy(); w['cost']=w.installs*cpi_ref; w['cellname']=cell
        # country-level reference CPI (Sep baseline if still buying, else window) for country totals
        src=base_d if r['active'] else win
        cc=src.groupby('country').agg(c=('cost','sum'),i=('installs','sum'))
        cc=cc[(cc.c>=20)&(cc.i>=10)]
        w['cpi_c']=w.country.map((cc.c/cc.i)).fillna(cpi_ref)
        wins[cell]=w; rows.append(r)
    tab=pd.DataFrame(rows)
    tab[['network','platform','market']]=tab.cell.str.split('|',expand=True)
    cls=tab.apply(classify,axis=1,result_type='expand'); tab['payback_group']=cls[0]; tab['flag']=cls[1]
    return co,groups,curve,tab,wins,diag

def total_row(label, wins_list, curve, game, extra=0.0):
    d=pd.concat(wins_list); wt=window_table(d,curve,T_list=(120,365),min_h=7)
    r={'group':label,'installs':wt['installs'],'cost_ref':wt['cost'],'cpi_ref':wt['cost']/wt['installs']}
    for T in [120,365]:
        lo,hi,_=interval(wt,game,T,extra)
        r[f'ltv_{T}']=wt[f'rev_{T}']/wt['installs']; r[f'roas_{T}']=wt[f'rev_{T}']/wt['cost']
        r[f'roas_{T}_lo']=lo/wt['cost']; r[f'roas_{T}_hi']=hi/wt['cost']
    return r

def totals(tab, wins, curve, game):
    out=[]
    for net,g in tab.groupby('network'):
        out.append(dict(total_row(f'Network {net}',[wins[c] for c in g.cell],curve,game),kind='network'))
    allw=pd.concat([wins[c] for c in tab.cell])
    # by country (countries as they appear in the cohort windows; weight = installs x cpi_ref)
    allw_c=allw.assign(cost=allw.installs*allw.cpi_c)
    for c,x in allw_c.groupby('country'):
        if x.installs.sum()>=400:
            out.append(dict(total_row(f'Country {c}',[x],curve,game),kind='country'))
    rest=allw_c[allw_c.groupby('country').installs.transform('sum')<400]
    if len(rest): out.append(dict(total_row('Countries other (<400 installs in window)',[rest],curve,game),kind='country'))
    out.append(dict(total_row('ALL paid cells',[allw],curve,game),kind='all'))
    return pd.DataFrame(out)

if __name__=='__main__':
    for g in 'AB':
        co,groups,curve,tab,wins,diag=build(g)
        tab=tab.sort_values(['network','platform','baseline_weekly_spend'],ascending=[True,True,False])
        tab.to_csv(f'{OUT}/value_cells_{g}.csv',index=False)
        tot=totals(tab,wins,curve,g); tot.to_csv(f'{OUT}/value_totals_{g}.csv',index=False)
        print('=====',g, len(tab),'cells')
        print(tab[['cell','baseline_weekly_spend','cpi_ref','roas_d7','roas_d30','win_installs','ltv_120','roas_120','roas_120_lo','roas_120_hi','ltv_365','roas_365','p_roas120_ge1','payback_group','flag']].round(2).to_string(index=False))
        print(tot.round(2).to_string(index=False))
