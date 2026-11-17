"""Q2: Game A spend plan 6 Oct - 28 Dec 2025 (12 weeks).
Maximise paid installs subject to: budget <= 250k, portfolio D120 ROAS >= target (CFO rule), Appendix A rules."""
import sys, json
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from scipy.optimize import minimize
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)

K={'Net-A':0.35,'Net-B':0.40,'Net-C':0.45,'Net-D':0.65}
HOL_W=4; WEEKS=12; HOL_UP=1.25
EQW=(WEEKS-HOL_W)+HOL_W/HOL_UP       # install-weeks equivalent = 11.2
BUDGET=250000.0; MIN_FRAC=0.40
tab=pd.read_csv(f'{OUT}/value_cells_A.csv')
tab=tab[tab.baseline_weekly_spend>0].reset_index(drop=True)
tab['k']=tab.network.map(K)
n=len(tab)
w0=tab.baseline_weekly_spend.values; cpi0=tab.cpi_ref.values; V120=tab.ltv_120.values; V365=tab.ltv_365.values; k=tab.k.values
line=(tab.network+'|'+tab.platform).values
lines=sorted(set(line))

def response(Q, kk=None):
    kk=k if kk is None else kk
    x=Q/(12*w0)
    xe=np.maximum(x,0.5)
    cpi=cpi0*xe**(0.7*kk)
    inst=np.where(Q>0, Q/cpi*EQW/12, 0.0)
    v=xe**(-0.3*kk)
    return x,inst,v

def totals(Q, V=None, kk=None):
    V=V120 if V is None else V
    x,inst,v=response(Q,kk)
    rev=inst*V*v
    return inst,rev

def solve(target, x0s=None):
    lo=np.zeros(n); hi=24*w0
    cons=[{'type':'ineq','fun':lambda Q: BUDGET-Q.sum()},
          {'type':'ineq','fun':lambda Q: totals(Q)[1].sum()-target*Q.sum()}]
    for L in lines:
        m=(line==L)
        minq=MIN_FRAC*12*w0[m].sum()
        if L=='Net-A|android':
            cons.append({'type':'ineq','fun':(lambda Q,m=m,minq=minq: Q[m].sum()-minq)})
        else:
            for i in np.where(m)[0]: lo[i]=MIN_FRAC*12*w0[i]
    best=None
    rng=np.random.default_rng(0)
    starts=[12*w0]+[rng.uniform(lo,hi) for _ in range(40)]
    for s in starts:
        s=np.clip(s,lo,hi)
        r=minimize(lambda Q:-totals(Q)[0].sum()/1e3, s, method='SLSQP', bounds=list(zip(lo,hi)), constraints=cons, options={'maxiter':400,'ftol':1e-10})
        Q=np.clip(r.x,lo,hi)
        if Q.sum()<=BUDGET+1 and totals(Q)[1].sum()>=target*Q.sum()-1:
            val=totals(Q)[0].sum()
            if best is None or val>best[0]: best=(val,Q)
    return best

def mc(Q, nsim=4000, seed=1, rho=0.5, drift=0.07, kvar=0.25):
    """Monte-Carlo of outcome: cell-level ROAS error from Q1 intervals (shared+idio), future-cohort drift, uncertain k."""
    rng=np.random.default_rng(seed)
    sig=np.log(tab.roas_120_hi/tab.roas_120_lo).values/(2*1.2816)
    sig365=np.log(tab.roas_365_hi/tab.roas_365_lo).values/(2*1.2816)
    zc=rng.standard_normal((nsim,1)); zi=rng.standard_normal((nsim,n))
    eps=np.sqrt(rho)*zc+np.sqrt(1-rho)*zi
    dr=drift*rng.standard_normal((nsim,n))
    kk=np.tile(k,(nsim,1))*(1+kvar*rng.standard_normal((nsim,4))[:,[['Net-A','Net-B','Net-C','Net-D'].index(nw) for nw in tab.network]])
    kk=np.clip(kk,0.05,1.5)
    x=Q/(12*w0); xe=np.maximum(x,0.5)
    cpi=cpi0*xe**(0.7*kk); inst=np.where(Q>0,Q/cpi*EQW/12,0.0)
    v=xe**(-0.3*kk)
    lvl=np.exp(sig*eps+dr)
    rev120=inst*V120*v*lvl
    rev365=inst*V365*v*np.exp(sig365*eps+dr)
    return inst,rev120,rev365

if __name__=='__main__':
    print(tab[['cell','baseline_weekly_spend','cpi_ref','ltv_120','roas_120','k']].round(2))
    rows=[]; plans={}
    for tgt in [0.0,1.00,1.03,1.05,1.08,1.10,1.15,1.20]:
        b=solve(tgt)
        if b is None: print('infeasible',tgt); continue
        _,Q=b
        inst,rev,rev365=mc(Q)
        spend=Q.sum()
        roas=rev.sum(1)/spend
        rows.append(dict(target=tgt,spend=spend,installs=b[0],roas_central=totals(Q)[1].sum()/spend,p_ge1=(roas>=1).mean(),
                         roas_p10=np.quantile(roas,.1),roas_p50=np.quantile(roas,.5),roas_p90=np.quantile(roas,.9),
                         inst_p10=np.quantile(inst.sum(1),.1),inst_p90=np.quantile(inst.sum(1),.9)))
        plans[tgt]=Q
    fr=pd.DataFrame(rows); print(fr.round(3).to_string(index=False)); fr.to_csv(f'{OUT}/plan_frontier.csv',index=False)
    pd.DataFrame({t:Q for t,Q in plans.items()},index=tab.cell).round(0).to_csv(f'{OUT}/plan_allocations_by_target.csv')
    # baseline reference plan (12 x baseline)
    Qb=12*w0; ib,rb=totals(Qb); print('baseline-as-is: spend %.0f installs %.0f roas120 %.3f'%(Qb.sum(),ib.sum(),rb.sum()/Qb.sum()))
    print(pd.DataFrame({'cell':tab.cell,**{f'Q@{t}':plans[t].round(0) for t in plans if t in (0.0,1.0,1.08)}}).to_string(index=False))
