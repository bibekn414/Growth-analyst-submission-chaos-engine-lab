# Growth Analyst assignment - Bibek Nayak

# Files: 
memo.pdf, 
appendix.pdf, 
predictions.csv, 
plan.csv, 
ai_log.md (+ ai_transcripts/), 
skipped.md, 
code/, 
data/ (original files, unchanged), 
outputs/ (generated tables), 
figs/.

Re-run: `pip install pandas numpy scipy matplotlib reportlab pypdf pillow`, then `python run_all.py`. Everything is rebuilt from data/*.csv. Order: value tables (02), backtests (03, 03b), predictions + cross-game (04), organic check (05), plan (06, 06b), creative analysis and plan (07, 08), report (09). code/common.py holds the cleaning rules; code/model.py the revenue-curve model. code/audit_exploration/ holds the throw-away scripts used for the data audit (evidence behind the data problems table).

# Key assumptions (all in appendix): 

as-of 30 Sep 2025, last full data day 28 Sep; 
mediation ad revenue only; 
IAP at full price; 
horizon N valid only if cohort age >= N; 
spend-response elasticity 0.35-0.65 by network (assumed); 
holiday weeks (last 4) cost 25% more per install; 
creative life = impressions until CPI +30%.
