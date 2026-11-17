# Growth Analyst Assignment: Paid UA Budget Case (Games A and B)

**Candidate:** Bibek Nayak | **Role:** Growth Analyst | **Company:** Chaos Engine Labs
**Data as of:** 30 Sep 2025 (last full data day 28 Sep) | **Plan period:** 6 Oct to 28 Dec 2025 (12 weeks)

---

## 1. The answer in 30 seconds

| Question | Answer |
|---|---|
| How much should we spend (Game A)? | **About $131.6k of the $250k** (about $11k per week), not the full budget |
| What do we get? | **About 91k paid installs** (80% range 87k to 95k) |
| Does it pay back? | **D120 ROAS 1.10** (80% range 0.96 to 1.29); **1-year ROAS 1.31** (1.13 to 1.56) |
| Why not spend all $250k? | It buys about 113k installs but returns only $0.79 per dollar by D120 and loses about $53k |
| Biggest data problem | Game A in-app purchases booked in local currency (7 Apr to 8 Jun) made raw D120 ROAS look like **1.04 instead of 0.84** |
| Biggest risk | Extrapolating young cohorts from older ones. Accurate on Game A (error 6 to 9%), but 15 to 25% too low on Game B because its value curve drifts |

Read first: **`memo.pdf`** (1 page) then **`appendix.pdf`** (10 pages).

---

## 2. Deliverables

| File | What it is |
|---|---|
| `memo.pdf` | Decision memo. First five lines: spend recommendation, expected result with range, which cells pay back by D120 / within a year / never, biggest data problem, biggest risk |
| `appendix.pdf` | Data problems table; value tables for both games (by cell, network and country, at D120 and 1 year); model comparison (A on A, A on B, B on B, B on A) with lessons; model description and accuracy; filled prediction template; plan table with reasoning; creative plan; AI log; skipped list |
| `predictions.csv` | Eight ROAS predictions with 80% ranges (filled template) |
| `plan.csv` | Q4 spend plan by network, platform and country (filled template) |
| `code/` and `run_all.py` | Everything re-runs from the original CSVs in `data/` |
| `ai_log.md` | How AI was used: two mistakes caught, one time-saver |
| `skipped.md` | What I skipped and why |
| `data/` | Original assignment files, unchanged |
| `outputs/`, `figs/` | Generated tables and charts |

---

## 3. Approach, step by step

1. **Audit the data.** Reconciled cohorts, UA spend and telemetry to find errors before modelling (see section 4).
2. **Clean it.** One cleaning module (`code/common.py`) applies every fix, so results are reproducible.
3. **Value each cell.** For each network x platform x country cell, predict revenue per install at D120 and 1 year, then ROAS at September spend. Small countries are grouped by CPI.
4. **Build and test the model.** Revenue-curve ("multiplier") model, backtested by hiding the last three months, and tested across games (A on A, A on B, B on B, B on A).
5. **Fill the prediction template.** Eight predictions with 80% ranges.
6. **Plan Q4 spend (Game A).** Maximise paid installs under the budget cap, a D120 ROAS floor and the spend-range rules. Solved with two solvers, ranges from Monte Carlo.
7. **Plan creatives.** Impressions per network, new creatives needed, ready-by dates, ad types, and what happens if they are late.
8. **Report.** Memo, appendix, AI log, skipped list.

---

## 4. Data problems found and how they were handled

| Problem | Handling |
|---|---|
| `ad_rev_all_sources` is about 2x the mediation figure (double count) | Use mediation ad revenue only |
| Game A in-app purchase amounts in local currency, 7 Apr to 8 Jun (181 cohort rows, $42k) | Replaced with a typical value per install; cause flagged as an assumption |
| Rewarded-ad spike 14 to 16 Jul (A) and 15 to 16 Jul (B) | Scaled to the local norm; those install days excluded from curve fitting |
| Young cohorts filled with zeros or carried-forward values | A horizon counts only if cohort age is at least that many days |
| Installs with no cost row in paid networks | Excluded from paid cells |
| Telemetry and MMP retention use different definitions | Telemetry used for anomaly checks only |
| Net-A mix shift (20 Apr), pauses, short Net-D history | Recency weights, 6-week window, wider ranges |
| Game B Net-A reported installs about 33x MMP installs | MMP installs only |
| Net-D creative cost and installs on different rows; Net-A "unknown" creative ids | No creative-level CPI for Net-D |
| Game B value curve drifts (backtest bias -12% to -27%) | Not fixed; B ranges widened and flagged |

---

## 5. Model in brief

- Each cohort's revenue at D120 or 1 year = its latest clean reading (day 7, 14 or 30) x a multiplier learned from older, matured cohorts.
- Separate curves for ad revenue and in-app purchases; ratio of sums so tiny cohorts do not dominate.
- Three levels (all, platform, network x platform), blended toward the broader curve when data is thin.
- 1-year tail from three curve shapes (median used, spread kept in the range).
- 80% ranges from a week-block bootstrap plus backtest error.
- **No machine-learning library was used.** The data is small and the task needs extrapolation to cohorts that have not reached D120 or 1 year, which tree models cannot do.

**Backtest (D120, Game A on Game A):** error 6 to 9%, bias within about 5%.

---

## 6. Payback by cell (Game A, at September CPI)

- **Pays back within 120 days:** Net-D US Android (borderline); Net-A Android in JP, KR, ES, DE, GB, FR and the small "other" group.
- **Pays back only within a year:** Net-A low-CPI group, Net-A BR, Net-B US Android, Net-C US Android.
- **Never within a year:** Net-A US Android (D120 0.79, 1-year 0.96) and Net-B iOS US.

Game B: only Net-D US pays back by D120; Net-A US and Net-C US only within a year; the rest never.

---

## 7. Q4 plan and creative plan (Game A)

**Plan:** cut Net-B, Net-C, Net-D and US Net-A to about half of September pace; push the cheap Net-A Android countries up to 2x (cap). The plan was set to ROAS 1.10 (not 1.00) as a safety buffer. Chance that D120 ROAS is at least 1.0 is about 82%.

| Plan | Spend | Installs | D120 ROAS |
|---|---|---|---|
| **Recommended (ROAS at least 1.10)** | $131.6k | 91.0k | 1.10 |
| Max installs, ROAS at least 1.00 | $160.3k | 98.2k | 1.00 |
| Profit-first | $82.2k | 42.3k | 1.32 |
| Spend everything, no rule | $250k | 112.9k | 0.79 |
| Do nothing (September pace) | $181.8k | 72.5k | 0.91 |

**New creatives needed** (CPI wear-out capped at +30%):

| Network | Impressions next quarter | New creatives | Ready by |
|---|---|---|---|
| Net-A | 11.6M | 9 | 13 Oct, 10 Nov, 15 Dec |
| Net-B | 0.23M | 3 | 13 Oct, 17 Nov |
| Net-C | 0.24M | 3 | 13 Oct, 17 Nov |
| Net-D | 0.06M | 2 | 13 Oct |

If delivered 2 weeks late: about 5% fewer installs. 4 weeks late: about 11% fewer, and ROAS falls to 0.99.

---

## 8. Assumptions (and why)

1. As-of date 30 Sep 2025; last full data day 28 Sep. The files end there.
2. A cohort's day-N value counts only if the cohort is at least N days old.
3. Ad revenue = mediation `ad_rev` only (the all-sources column double counts).
4. In-app purchases at full price (finance rule).
5. Game A IAP window 7 Apr to 8 Jun is a currency booking error. IAP per payer was 10 to 5000x the country norm; the cause cannot be proven.
6. Rewarded-ad spike days are scaled back to normal.
7. Paid-network installs without a cost row are excluded.
8. Cells are network x platform x country; small countries grouped by CPI.
9. **Spend response is assumed:** CPI rises with spend (elasticity 0.35 to 0.65 by network). History cannot identify it.
10. The last 4 weeks of the quarter cost 25% more per install (holiday rule).
11. Plan floor is D120 ROAS 1.10, not 1.00, because the 80% range on ROAS is wide.
12. Organic installs are not counted: the link to paid spend shows in levels but disappears in week-on-week changes.
13. Creative life = impressions until CPI is 30% above fresh; 25% spare creatives; each batch ready one week early.
14. Game B is lower confidence because its curve drifts.
15. Focus: Game A plan and creatives (the decisions); Game B for value tables and the model comparison.

---

## 9. Limits and what I skipped

- Spend elasticities are assumptions, not estimates.
- The install goal favours cheap, low-value installs (64% of plan installs versus 47% at baseline).
- Game B drift was not fixed; its 1-year numbers are the least certain.
- No creative-level CPI for Net-D (cost and installs sit on different rows).
- No campaign-level modelling (too little data per campaign).
- Cause of the Game A IAP anomaly not provable from the data.

Full list: `skipped.md`.

---

## 10. AI use

Gemini (Pro High) was used heavily for this assignment along with Claude at some cases, as the brief allows. It wrote the cleaning, modelling, backtest, optimiser and report code, and I reviewed the results. Two mistakes were caught during the work (payer columns read as cumulative; the July revenue jump first read as an outage instead of an ad-rate spike) and one time-saver is described in `ai_log.md`.

---

## 11. Re-run

```bash
pip install pandas numpy scipy matplotlib reportlab pypdf pillow
python run_all.py        # about 10 to 20 minutes; rebuilds all outputs, memo.pdf and appendix.pdf
```

Order: value tables (02), backtests (03, 03b), predictions and cross-game (04), organic check (05), plan (06, 06b), creative analysis and plan (07, 08), report (09). `code/common.py` holds the cleaning rules and `code/model.py` the revenue-curve model. `code/audit_exploration/` holds the throw-away scripts behind the data problems table.

*Confidential: the data in `data/` belongs to Chaos Engine Labs.*
