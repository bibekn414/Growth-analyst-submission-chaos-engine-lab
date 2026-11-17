"""Q3b: impressions, new creatives needed, ready-by dates, risk of late/short delivery."""
import sys, json
sys.path.insert(0,'code')
import numpy as np, pandas as pd
from common import *
import importlib
P=importlib.import_module('06_plan')
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
Q=np.load(f'{OUT}/plan_Q.npy'); tab=P.tab.copy(); tab['Q']=Q
RATE={'Net-A':0.20,'Net-B':3.00,'Net-C':3.00,'Net-D':1.50}      # CPI rise per 1M impressions
LIFE={n:0.30/r*1e6 for n,r in RATE.items()}                      # impressions until +30%
tab['cpm']=tab.baseline_cpm
tab['impr']=tab.Q/tab.cpm*1000
week_start=[pd.Timestamp('2025-10-06')+pd.Timedelta(days=7*i) for i in range(12)]
# weekly impressions per network (spend even over 12 weeks; shared ad set for Net-B android+ios)
net_imp=tab.groupby('network').impr.sum()
rows=[]; sched={}
for net,I in net_imp.items():
    wk=np.full(12,I/12.0); wk[:2]=0.0            # weeks 1-2 carried by today's creatives
    life=LIFE[net]
    # just-in-time schedule: at start of each week launch just enough new creatives to cover the week's impressions
    remaining=[]; launches=np.zeros(12,int)
    for w in range(2,12):
        need=wk[w]
        cap=sum(remaining)
        if cap<need:
            k=int(np.ceil((need-cap)/life)); launches[w]=k; remaining+= [life]*k
        # serve water-filling evenly
        left=need; rem=np.array(remaining,float)
        while left>1e-9 and (rem>1e-9).any():
            live=rem>1e-9; share=left/live.sum(); take=np.minimum(rem[live],share)
            rem[live]-=take; left-=take.sum()
        remaining=list(rem[rem>1e-9])
    n_min=int(launches.sum())
    n_rec=int(np.ceil(n_min*1.25)) if n_min>0 else 0
    sched[net]=launches
    rows.append(dict(network=net,spend=tab[tab.network==net].Q.sum(),impressions_q=I,impr_after_wk2=wk.sum(),life=life,
                     creatives_min=n_min,creatives_recommended=n_rec,first_needed=str(week_start[int(np.argmax(launches>0))].date()) if n_min else '-'))
cp=pd.DataFrame(rows); print(cp.round(0).to_string(index=False))
# build schedule (recommended = minimum x1.25, launched in 3 batches ready ONE WEEK before use)
sch=[]
for net in sched:
    L=sched[net]; nmin=L.sum(); nrec=int(cp[cp.network==net].creatives_recommended.iloc[0])
    if nmin==0: continue
    # spread recommended count proportionally to launch pattern, ready 1 week earlier than first use
    frac=np.cumsum(L)/nmin
    cum_target=np.ceil(frac*nrec).astype(int)
    prev=0
    for w in range(12):
        add=cum_target[w]-prev
        if add>0: sch.append(dict(network=net,ready_by=str((week_start[w]-pd.Timedelta(days=7)).date()),first_use_week=w+1,first_use=str(week_start[w].date()),new_creatives=int(add)))
        prev=cum_target[w]
sch=pd.DataFrame(sch)
# merge consecutive same-week batches; compress to <=3 batches per network by grouping into 4-week windows
def compress(g):
    g=g.copy(); g['batch']=((g.first_use_week-3)//4)
    return g.groupby('batch').agg(network=('network','first'),ready_by=('ready_by','min'),first_use=('first_use','min'),first_use_week=('first_use_week','min'),new_creatives=('new_creatives','sum')).reset_index(drop=True)
sch=pd.concat([compress(g) for _,g in sch.groupby('network')],ignore_index=True)
print(sch.to_string(index=False))
# ---------------- risk: late delivery / shortfall (excess CPI above the +30% retirement cap)
Nold={'Net-A':3,'Net-B':8,'Net-C':8,'Net-D':1}      # creatives live in Sept (today's inventory)
def week_cpi_mult(net, launches_cum_n, delay=0, short=1.0):
    """Weekly CPI multiplier vs the 'replaced in time' baseline. Old creatives are AT the cap at end of week 2.
    New creatives (N=short*recommended) arrive `delay` weeks late; impressions beyond cap raise CPI per creative at table rate."""
    I=net_imp[net]/12.0; rate=RATE[net]; life=LIFE[net]
    nrec=int(cp[cp.network==net].creatives_recommended.iloc[0]); nnew=int(np.floor(nrec*short)) if short<1 else nrec
    mult=np.ones(12); old_cum=0.0; per_new=np.zeros(0)
    new_cum=np.zeros(nnew)
    for w in range(2,12):
        if w>=2+delay and nnew>0:
            # evenly across new creatives that are live; stagger: all launched at 2+delay for simplicity (pessimistic for 'short', neutral for 'late')
            new_cum+=I/nnew; c=new_cum.mean()
            mult[w]=1+max(0.0,rate*c/1e6-0.30)
        else:
            old_cum+=I/Nold[net]; mult[w]=1.30+rate*old_cum/1e6
    return mult
def impact(net, mult):
    m=tab[tab.network==net]; share_inst=1/mult
    return mult
res=[]
for scen,(delay,short) in {'on time':(0,1.0),'2 weeks late':(2,1.0),'4 weeks late':(4,1.0),'25% too few':(0,0.75),'50% too few':(0,0.5)}.items():
    inst_base=0; inst_new=0; rev_new=0; rev_base=0
    xx,inst_c,v_c=P.response(Q); rev_c=inst_c*P.V120*v_c
    for net in net_imp.index:
        mk=(tab.network==net).values
        inst=inst_c[mk].sum(); rev=rev_c[mk].sum()
        mult=week_cpi_mult(net,None,delay,short)
        wt=np.array([1.0]*7+[1/1.25]*4+[1.0]); wt/=wt.sum()
        f=(wt/mult).sum()
        inst_base+=inst; rev_base+=rev; inst_new+=inst*f; rev_new+=rev*f
    res.append(dict(scenario=scen,installs=inst_new,installs_vs_plan_pct=100*(inst_new/inst_base-1),d120_rev=rev_new,roas120=rev_new/Q.sum()))
rk=pd.DataFrame(res); print(rk.round(3).to_string(index=False))
# per-network sensitivity (2 weeks late) - which network hurts most
per=[]
for net in net_imp.index:
    for scen,(d,s) in {'2 weeks late':(2,1.0),'25% too few':(0,0.75)}.items():
        m=week_cpi_mult(net,None,d,s); wt=np.array([1.0]*7+[1/1.25]*4+[1.0]); wt/=wt.sum()
        per.append(dict(network=net,scenario=scen,avg_cpi_uplift_pct=100*((wt/m).sum()**-1-1),max_week_cpi_uplift_pct=100*(m.max()-1)))
per=pd.DataFrame(per); print(per.round(1).to_string(index=False))
cp.to_csv(f'{OUT}/creative_need.csv',index=False); sch.to_csv(f'{OUT}/creative_schedule.csv',index=False); rk.to_csv(f'{OUT}/creative_risk.csv',index=False); per.to_csv(f'{OUT}/creative_risk_by_network.csv',index=False)
tab[['cell','Q','cpm','impr']].to_csv(f'{OUT}/creative_cells.csv',index=False)
