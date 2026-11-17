# Assumptions and judgment calls

Where something was unclear I made a call and wrote down why. Each item also says what would change if the call is wrong.

| # | Assumption / judgment call | Why | If wrong |
|---|---|---|---|
| 1 | As-of date is 30 Sep 2025; last full data day is 28 Sep | The files end there | Cohort ages shift by a day or two; small effect |
| 2 | A cohort's day-N revenue counts only if the cohort is at least N days old | Younger values are zeros or carried forward | Young cohorts would look worse than they are |
| 3 | Ad revenue = mediation `ad_rev` only | `ad_rev_all_sources` is about 2x and double counts | ROAS would be inflated by a large margin |
| 4 | In-app purchases counted at full price | Finance rule | ROAS would be lower if platform fees were deducted |
| 5 | Game A in-app purchases from 7 Apr to 8 Jun are a local-currency booking error, replaced by a typical value per install | IAP per payer was 10 to 5000x the country norm in that window. The cause cannot be proven from the data | If the amounts were real, Game A D120 ROAS is about 1.04, not 0.84 |
| 6 | Rewarded-ad spike days (14 to 16 Jul in A, 15 to 16 Jul in B) are scaled back to normal | Ad revenue per user was more than 2x normal while impressions stayed flat | Ad value of July cohorts would be overstated |
| 7 | Installs in paid networks with no cost row are excluded | They would distort CPI and value per install | CPI would look lower than it is |
| 8 | Cells are network x platform x country; small countries are grouped by CPI | Too little data per small country | Small-country results would be noisy |
| 9 | Spend response: CPI rises with spend, with elasticity 0.35 to 0.65 by network | Assumed. History cannot identify it because spend moves with seasonality and mix | Plan ROAS and installs would move; the 2x cap limits the damage |
| 10 | The last 4 weeks of the quarter cost 25% more per install | Holiday rule in the brief | Installs in those weeks would be higher or lower |
| 11 | Plan floor is D120 ROAS 1.10, not 1.00 | The 80% range on ROAS is wide, so a buffer protects against missing 1.0 | At 1.00 the plan spends about $160k for about 7k more installs, with only about a 52% chance of reaching 1.0 |
| 12 | Organic installs are not counted | A link between paid spend and organic installs shows in levels but vanishes in week-on-week changes | If organic uplift is real, paid UA is worth more than the plan says |
| 13 | A creative is retired when its CPI is 30% above fresh; add 25% spare creatives; each batch is ready one week early | Protects against slips in delivery | Fewer spares would make late delivery cost more |
| 14 | Game B is treated as lower confidence | Its value curve drifts (backtest bias -12% to -27%) | B numbers are likely too low; B ranges are widened |
| 15 | Focus: Game A plan and creatives (the decisions); Game B for value tables and the model comparison only | The spend decision is for Game A | Game B has no spend plan in this submission |
| 16 | Value window for current performance is the last 6 weeks of cohorts | Early August cohorts were richer and overstated Net-D | A longer window would raise Net-D ROAS |
| 17 | Cohorts younger than 7 days are not used for value | Day-0 and day-3 readings are too noisy | Very new cohorts are ignored |
| 18 | Curve fitting uses recency weights (half-life 60 days) and excludes install days 13 and 17 Jul | Follows drift and avoids the days next to the spike | Slower-moving curves, slightly more stale |
| 19 | Networks with no mature curve of their own borrow the platform curve, plus extra uncertainty | Not enough old cohorts | Their ranges would be too narrow |
| 20 | Each cell's spend is capped at 2x and floored at 0.4x September pace (Net-A Android needs 0.4x in aggregate) | Rules in the brief | The optimiser would concentrate spend in a few cells |

## What I chose to focus on

- **Game A first:** it carries the budget decision, the plan and the creative plan.
- **Game B** gets value tables, predictions context and the model comparison, because the brief asks for them. It gets no spend plan.
- **Model choice:** a simple curve model with backtests, not machine learning, because the data is small and the task needs extrapolation to cohorts that have not reached D120 or 1 year.

See `appendix.pdf` for evidence and `skipped.md` for what was left out.
