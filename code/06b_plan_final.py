"""Finalise the Q2 plan: recommended plan (max installs s.t. D120 ROAS >= 1.10 central => ~80% chance to clear 1.00),
verification with an independent global optimiser, alternatives, expected results with ranges, plan.csv."""
import sys, json, importlib
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from scipy.optimize import differential_evolution, minimize
P=importlib.import_module('06_plan')
from common import *
tab=P.tab; n=P.n; w0=P.w0
TARGET=1.10
# ---------- 1) main solution + independent verification (differential evolution with penalty)
_,Q=P.solve(TARGET)
def pen_obj(Q):
    Q=np.asarray(Q); pen=0.0
    inst,rev=P.totals(Q)
    pen+=max(0,TARGET*Q.sum()-rev.sum())*20 + max(0,Q.sum()-P.BUDGET)*20
    for L in P.lines:
        m=(P.line==L); minq=P.MIN_FRAC*12*w0[m].sum()
        pen+=max(0,minq-Q[m].sum())*20
    return -inst.sum()+pen
lo=np.zeros(n); hi=24*w0
for i,L in enumerate(P.line):
    if L!='Net-A|android': lo[i]=P.MIN_FRAC*12*w0[i]
de=differential_evolution(pen_obj,list(zip(lo,hi)),seed=1,maxiter=1500,popsize=30,tol=1e-9,polish=True,x0=Q)
print('SLSQP installs %.0f spend %.0f | DE installs %.0f (penalised %.0f) spend %.0f'%(P.totals(Q)[0].sum(),Q.sum(),P.totals(de.x)[0].sum(),-de.fun,de.x.sum()))
# ---------- 2) round to $50 keeping constraints
Qr=np.round(Q/50)*50
Qr=np.minimum(Qr,24*w0); 
for i,L in enumerate(P.line):
    if L!='Net-A|android': Qr[i]=max(Qr[i],P.MIN_FRAC*12*w0[i])
inst,rev=P.totals(Qr); print('rounded: spend %.0f installs %.0f roas %.3f'%(Qr.sum(),inst.sum(),rev.sum()/Qr.sum()))
if rev.sum()/Qr.sum()<TARGET:     # nudge Net-A US down in $50 steps until target met
    i=list(tab.cell).index('Net-A|android|us')
    while P.totals(Qr)[1].sum()/Qr.sum()<TARGET: Qr[i]-=50
    print('nudged US: roas %.3f'%(P.totals(Qr)[1].sum()/Qr.sum()))
Q=Qr
# ---------- 3) alternatives
def solve_obj(obj, cons_target=1.0):
    cons=[{'type':'ineq','fun':lambda Q: P.BUDGET-Q.sum()},{'type':'ineq','fun':lambda Q: P.totals(Q)[1].sum()-cons_target*Q.sum()}]
    lo=np.zeros(n)
    for i,L in enumerate(P.line):
        if L!='Net-A|android': lo[i]=P.MIN_FRAC*12*w0[i]
    cons.append({'type':'ineq','fun':lambda Q: Q[P.line=='Net-A|android'].sum()-P.MIN_FRAC*12*w0[P.line=='Net-A|android'].sum()})
    best=None; rng=np.random.default_rng(3)
    for s in [12*w0]+[rng.uniform(lo,24*w0) for _ in range(30)]:
        r=minimize(lambda Q:-obj(Q)/1e3,np.clip(s,lo,24*w0),method='SLSQP',bounds=list(zip(lo,24*w0)),constraints=cons,options={'maxiter':400,'ftol':1e-10})
        Qx=np.clip(r.x,lo,24*w0)
        if Qx.sum()<=P.BUDGET+1 and P.totals(Qx)[1].sum()>=cons_target*Qx.sum()-1:
            v=obj(Qx)
            if best is None or v>best[0]: best=(v,Qx)
    return best[1]
alts={'CEO max installs, ROAS>=1.00 (no buffer)':P.solve(1.0)[1],
      'CFO max profit (D120 rev - spend), ROAS>=1.00':solve_obj(lambda Q:P.totals(Q)[1].sum()-Q.sum(),1.0),
      'Spend everything ($250k), no ROAS rule':P.solve(0.0)[1],
      'Do nothing: 12 x baseline':12*w0,
      'RECOMMENDED (max installs, ROAS>=1.10 buffer)':Q}
rows=[]
for nm,q in alts.items():
    i_,r_=P.totals(q); _,r365=P.totals(q,V=P.V365)
    inst_m,rev_m,rev365_m=P.mc(q); ro=rev_m.sum(1)/q.sum()
    rows.append(dict(plan=nm,spend=q.sum(),installs=i_.sum(),d120_rev=r_.sum(),d120_roas=r_.sum()/q.sum(),profit_d120=r_.sum()-q.sum(),
                     d365_rev=r365.sum(),d365_roas=r365.sum()/q.sum(),p_roas_ge1=(ro>=1).mean(),roas_p10=np.quantile(ro,.1),roas_p90=np.quantile(ro,.9),
                     lowvalue_install_share=i_[tab.ltv_120.values<1.0].sum()/i_.sum()))
alt=pd.DataFrame(rows); print(alt.round(3).to_string(index=False)); alt.to_csv(f'{OUT}/plan_alternatives.csv',index=False)
# ---------- 4) expected result with ranges for recommended plan
inst_m,rev_m,rev365_m=P.mc(Q,nsim=6000,seed=9)
def rng_(a): return float(np.quantile(a,.1)),float(np.quantile(a,.5)),float(np.quantile(a,.9))
res={'spend':float(Q.sum()),'installs':rng_(inst_m.sum(1)),'rev120':rng_(rev_m.sum(1)),'roas120':rng_(rev_m.sum(1)/Q.sum()),
     'rev365':rng_(rev365_m.sum(1)),'roas365':rng_(rev365_m.sum(1)/Q.sum()),'p_roas120_ge1':float((rev_m.sum(1)/Q.sum()>=1).mean()),
     'p_roas365_ge1':float((rev365_m.sum(1)/Q.sum()>=1).mean())}
b_inst,b_rev=P.totals(12*w0); res['baseline_installs']=float(b_inst.sum()); res['baseline_roas120']=float(b_rev.sum()/(12*w0).sum()); res['baseline_spend']=float((12*w0).sum())
print(json.dumps(res,indent=1))
# ---------- 5) plan table
x,inst,v=P.response(Q)
_,rev=P.totals(Q); _,rev365=P.totals(Q,V=P.V365)
ua=pd.read_csv(f'{DATA}/GameA_ua_daily.csv',parse_dates=['date'])
sep=ua[(ua.date>='2025-09-01')&(ua.date<='2025-09-28')&ua.network.isin(['Net-A','Net-B','Net-C','Net-D'])&(ua.cost>0)]
mem={}
for (net,plat,c),g in sep.groupby(['network','platform','country']): mem.setdefault((net,plat),[]).append((c,g.cost.sum()/4))
rows=[]
for i,r in tab.iterrows():
    net,plat,mkt=r.cell.split('|')
    ctry=mkt
    note=''
    if mkt.startswith('grp-'):
        # keep only countries with Sep baseline spend (not new countries)
        allc=r.countries.split(',')
        lst=sorted([c for c,s in mem[(net,plat)] if c in allc])
        ctry=f'GROUP {"low-CPI small countries" if mkt=="grp-lowCPI" else "other small countries"}'
        note='group of: '+', '.join(lst)+'; spread across these countries pro rata to their September spend'
    b_inst_i=12*w0[i]/r.cpi_ref
    rows.append(dict(game='Game A',network=net,platform=plat,country=ctry,baseline_weekly_spend=round(w0[i],2),quarter_spend=round(Q[i],0),
        share_of_quarter_budget=Q[i]/Q.sum(),spend_multiple_x=x[i],expected_installs=round(inst[i]),expected_d120_revenue=round(rev[i]),
        expected_d120_roas=rev[i]/Q[i] if Q[i]>0 else np.nan,expected_1y_revenue=round(rev365[i]),expected_1y_roas=rev365[i]/Q[i] if Q[i]>0 else np.nan,note=note))
plan=pd.DataFrame(rows)
tot=dict(game='Game A',network='TOTAL',platform='',country='',baseline_weekly_spend=round(w0.sum(),2),quarter_spend=round(Q.sum()),share_of_quarter_budget=1.0,
         spend_multiple_x=np.nan,expected_installs=round(inst.sum()),expected_d120_revenue=round(rev.sum()),expected_d120_roas=rev.sum()/Q.sum(),
         expected_1y_revenue=round(rev365.sum()),expected_1y_roas=rev365.sum()/Q.sum(),
         note=f'<= $250,000 cap (spend ${Q.sum():,.0f}); ranges (80%): installs {res["installs"][0]:,.0f}-{res["installs"][2]:,.0f}; D120 ROAS {res["roas120"][0]:.2f}-{res["roas120"][2]:.2f}; 1y ROAS {res["roas365"][0]:.2f}-{res["roas365"][2]:.2f}')
plan=pd.concat([plan,pd.DataFrame([tot])],ignore_index=True)
plan.to_csv(f'{OUT}/plan_full.csv',index=False)
tmpl_cols=list(pd.read_csv(f'{DATA}/Template_plan.csv').columns)
plan[tmpl_cols].round(4).to_csv(f'{ROOT}/plan.csv',index=False)
print(plan[['network','platform','country','baseline_weekly_spend','quarter_spend','share_of_quarter_budget','spend_multiple_x','expected_installs','expected_d120_roas','expected_1y_roas']].round(3).to_string(index=False))
json.dump(res,open(f'{OUT}/plan_result.json','w'),indent=1)
np.save(f'{OUT}/plan_Q.npy',Q)
