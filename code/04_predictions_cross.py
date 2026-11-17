"""(a) The 8 required predictions (Game A, Template_predictions.csv)
   (b) Cross-game application at the final as-of date: A model on A / A on B / B on B / B on A."""
import sys, json
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *; from model import *
import importlib; vt=importlib.import_module('02_value_tables')
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
NP=json.load(open(f'{OUT}/noise_params.json'))
rng=np.random.default_rng(21)

# ------------------------------------------------------------------ (a) predictions
co,diag=clean_cohorts('A'); co,groups=add_cells(co,'A')
ua=pd.read_csv(f'{DATA}/GameA_ua_daily.csv',parse_dates=['date'])
curve=Curve(co,LAST,halflife=60.0,boot=300,seed=5)
tmpl=pd.read_csv(f'{DATA}/Template_predictions.csv')

def rows_for(cell_spec, lo, hi):
    net,plat,mkt=cell_spec
    c=co[(co.network==net)&(co.platform==plat)&co.install_date.between(lo,hi)&(co.installs>0)]
    u=ua[(ua.network==net)&(ua.platform==plat)&ua.date.between(lo,hi)]
    if mkt=='us': c=c[c.country=='us']; u=u[u.country=='us']
    elif mkt=='nonus': c=c[c.country!='us']; u=u[u.country!='us']
    return c,u

SPEC={'P1':(('Net-A','android','us'),30,'2025-09-01','2025-09-14'),
      'P2':(('Net-A','android','nonus'),30,'2025-09-01','2025-09-14'),
      'P3':(('Net-B','android','us'),30,'2025-09-01','2025-09-14'),
      'P4':(('Net-B','ios','us'),30,'2025-09-01','2025-09-14'),
      'P5':(('Net-C','android','us'),30,'2025-09-01','2025-09-14'),
      'P6':(('Net-D','android','us'),30,'2025-09-01','2025-09-14'),
      'P7':(('Net-A','android','us'),60,'2025-08-04','2025-08-17'),
      'P8':(('Net-D','android','us'),60,'2025-08-04','2025-08-17')}
out=[]
for pid,(cell,T,lo,hi) in SPEC.items():
    c,u=rows_for(cell,lo,hi)
    cost=u.cost.sum()
    wt=window_table(c.assign(cost=c.cost),curve,T_list=(T,),min_h=3)   # all installs incl. zero-cost attributed ones
    n=wt['installs']
    dr=wt[f'draws_{T}']
    own=vt.mature_own(curve,cell[0],cell[1])
    # prediction from very early readings (d7/d14) -> use backtest-like noise; add model-risk for networks w/o own mature curve
    sd=np.sqrt(NP['A']['a']+NP['A']['b']/n+(0.0 if own else vt.NEW_NET_SD**2)+(0.03**2 if T==30 else 0.0))
    sims=rng.choice(dr,6000)*np.exp(rng.normal(0,sd,6000))/cost
    pred=wt[f'rev_{T}']/cost
    lo80,hi80=np.quantile(sims,[0.1,0.9])
    ages=(LAST-c.install_date).dt.days
    note=(f"Cohort-level ratio model: latest cleaned reading (d{'14' if T==30 else '30'}, falls back to d7) x multiplier fitted on mature A cohorts "
          f"({'own network curve' if own else 'platform-pooled curve + extra model-risk'}); ROAS = predicted revenue (mediation ad_rev + full-price IAP) / spend on the same install days "
          f"(${cost:,.0f}, {n:,.0f} installs); range = bootstrap + backtest residual noise")
    out.append(dict(id=pid,pred=pred,lo=lo80,hi=hi80,installs=n,spend=cost,note=note,age_min=int(ages.min()),age_max=int(ages.max())))
P=pd.DataFrame(out)
t=tmpl.copy()
t['your_prediction']=P.pred.round(4).values; t['low_80']=P.lo.round(4).values; t['high_80']=P.hi.round(4).values; t['method_note']=P.note.values
t.to_csv(f'{ROOT}/predictions.csv',index=False)
print(P.drop(columns='note').round(3).to_string(index=False))

# ------------------------------------------------------------------ (b) cross-game
res={}
for tg in 'AB':
    co_t,groups,cv_own,tab_own,wins,_=vt.build(tg)
    res[(tg,tg)]=tab_own
    other='B' if tg=='A' else 'A'
    co_o,_=clean_cohorts(other); co_o,_=add_cells(co_o,other)
    cv_other=Curve(co_o,LAST,halflife=60.0,boot=0)
    # apply the other game's fitted curve to this game's cohorts (own cells, own levels)
    co2,groups2,_,tab_x,_,_=vt.build(tg,boot=0,curve=cv_other) if False else (None,)*6
    # build() needs boots for intervals; give other curve boots by re-fitting with boot
    cv_other=Curve(co_o,LAST,halflife=60.0,boot=200,seed=3)
    _,_,_,tab_x,_,_=vt.build(tg,curve=cv_other)
    res[(other,tg)]=tab_x
rows=[]
for tg in 'AB':
    own=res[(tg,tg)].set_index('cell'); oth=res[('B' if tg=='A' else 'A',tg)].set_index('cell')
    j=own[['baseline_weekly_spend','cpi_ref','roas_120','roas_365','ltv_120','ltv_365','win_installs']].join(oth[['roas_120','roas_365','ltv_120','ltv_365']],rsuffix='_x')
    j['game']=tg; j['model_own']=tg; j['model_x']='B' if tg=='A' else 'A'
    rows.append(j.reset_index())
X=pd.concat(rows)
X['d120_pct']=100*(X.ltv_120_x/X.ltv_120-1); X['d365_pct']=100*(X.ltv_365_x/X.ltv_365-1)
X.to_csv(f'{OUT}/cross_game_final.csv',index=False)
print(X[['game','cell','win_installs','ltv_120','ltv_120_x','d120_pct','ltv_365','ltv_365_x','d365_pct']].round(2).to_string(index=False))
for g in 'AB':
    s=X[X.game==g]; w=s.win_installs
    print(g,'install-weighted LTV120 diff (other-model vs own): %.1f%%; LTV365: %.1f%%'%(100*(np.average(s.ltv_120_x,weights=w)/np.average(s.ltv_120,weights=w)-1),100*(np.average(s.ltv_365_x,weights=w)/np.average(s.ltv_365,weights=w)-1)))
