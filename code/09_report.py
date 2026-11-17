"""Builds figures, memo.pdf and appendix.pdf from outputs/*.csv (run after 02-08)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from common import OUT, FIG, ROOT

R = lambda f: pd.read_csv(f'{OUT}/{f}.csv')
pr = json.load(open(f'{OUT}/plan_result.json'))
vA, vB = R('value_cells_A'), R('value_cells_B')
tA, tB = R('value_totals_A'), R('value_totals_B')
plan = R('plan_full'); alt = R('plan_alternatives'); fr = R('plan_frontier')
cn, cs, crk = R('creative_need'), R('creative_schedule'), R('creative_risk')
ct = R('creative_types_A'); bt = R('backtest_2x2'); cx = R('cross_game_final'); org = R('organic_elasticity')

# ------------------------------------------------------------------ figures
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False})
def fig_cells(v, name, title):
    d = v.sort_values('roas_120')
    f, ax = plt.subplots(figsize=(6.4, 3.6))
    y = np.arange(len(d))
    ax.errorbar(d.roas_120, y, xerr=[d.roas_120 - d.roas_120_lo, d.roas_120_hi - d.roas_120], fmt='o', color='#1f4e79', ms=4, lw=1, label='D120 ROAS (80% range)')
    ax.scatter(d.roas_365, y, marker='D', color='#c55a11', s=14, label='1-year ROAS')
    ax.axvline(1, color='k', lw=.8, ls='--'); ax.set_yticks(y); ax.set_yticklabels(d.cell, fontsize=6.5)
    ax.set_xlabel('ROAS (revenue / spend)'); ax.set_title(title, fontsize=9); ax.legend(fontsize=7, loc='lower right')
    f.tight_layout(); f.savefig(f'{FIG}/{name}.png', dpi=200); plt.close(f)
fig_cells(vA, 'cells_A', 'Game A: value by cell (baseline CPI)')
fig_cells(vB, 'cells_B', 'Game B: value by cell (baseline CPI)')
f, ax = plt.subplots(figsize=(6.4, 3))
ax.plot(fr.spend / 1e3, fr.installs / 1e3, 'o-', color='#1f4e79')
for _, r in fr.iterrows(): ax.annotate(f"ROAS≥{r.target:.2f}" if r.target else 'no rule', (r.spend / 1e3, r.installs / 1e3), fontsize=6.5, xytext=(3, -9), textcoords='offset points')
ax.set_xlabel('Spend, $k'); ax.set_ylabel('Paid installs, k'); ax.set_title('Q2 frontier: installs vs. portfolio D120 ROAS floor', fontsize=9)
f.tight_layout(); f.savefig(f'{FIG}/frontier.png', dpi=200); plt.close(f)
f, ax = plt.subplots(figsize=(6.4, 3))
w = bt[(bt.variant == 'halflife60') & (bt.max_h.isin([7, 30]))]
lab = [f"{r.train} on {r.test}\n(d{r.max_h})" for r in w.itertuples()]
ax.bar(range(len(w)), w.bias_pct, color=['#1f4e79' if t == s else '#c55a11' for t, s in zip(w.train, w.test)])
ax.set_xticks(range(len(w))); ax.set_xticklabels(lab, fontsize=6); ax.axhline(0, color='k', lw=.6)
ax.set_ylabel('Bias of D120 prediction, %'); ax.set_title('Backtest bias (train on X, predict Y; reading at day 7 / 30)', fontsize=9)
f.tight_layout(); f.savefig(f'{FIG}/backtest.png', dpi=200); plt.close(f)

# ------------------------------------------------------------------ styles
ss = getSampleStyleSheet()
B = ParagraphStyle('B', parent=ss['BodyText'], fontSize=8.3, leading=10.2, spaceAfter=3)
H1 = ParagraphStyle('H1', parent=ss['Heading1'], fontSize=12, spaceAfter=3, spaceBefore=5)
H2 = ParagraphStyle('H2', parent=ss['Heading2'], fontSize=9.5, spaceAfter=2, spaceBefore=4)
L5 = ParagraphStyle('L5', parent=B, fontSize=8.6, leading=10.8, spaceAfter=2.5)
SM = ParagraphStyle('SM', parent=B, fontSize=6.6, leading=7.8, spaceAfter=0)
def P(t, s=B): return Paragraph(t, s)
def tbl(rows, widths, hdr=True, fs=6.6, zebra=True):
    data = [[Paragraph(str(c), ParagraphStyle('c', parent=SM, fontSize=fs, leading=fs + 1.2, fontName='Helvetica-Bold' if (hdr and i == 0) else 'Helvetica')) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if hdr else 0)
    st = [('GRID', (0, 0), (-1, -1), .3, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2), ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]
    if hdr: st.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9e2f3')))
    t.setStyle(TableStyle(st)); return t
def img(n, w): 
    from PIL import Image as PI
    iw, ih = PI.open(f'{FIG}/{n}.png').size; return Image(f'{FIG}/{n}.png', width=w, height=w * ih / iw)
def f0(x): return f'{x:,.0f}'
def f2(x): return f'{x:.2f}'

# ------------------------------------------------------------------ numbers
tot = plan[plan.network == 'TOTAL'].iloc[0]
pl = plan[plan.network != 'TOTAL']
ip10, ip90 = pr['installs'][0], pr['installs'][2]
rec = alt[alt.plan.str.startswith('RECOMMENDED')].iloc[0]
A_all = tA[tA.kind == 'all'].iloc[0]; B_all = tB[tB.kind == 'all'].iloc[0]
grpA = vA[vA.baseline_weekly_spend > 0].groupby('payback_group').cell.apply(lambda s: ', '.join(x.replace('Net-', '').replace('|android|', ' And ').replace('|ios|', ' iOS ') for x in s))

# ------------------------------------------------------------------ MEMO
def memo():
    doc = SimpleDocTemplate(f'{ROOT}/memo.pdf', pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=13*mm, bottomMargin=12*mm, title='Memo - UA budget Q4 2025', author='Bibek Nayak')
    S = []
    S.append(P('<b>To:</b> Marketing leadership &nbsp; <b>From:</b> Bibek Nayak, Growth Analyst applicant &nbsp; <b>Re:</b> Game A paid UA, 6 Oct - 28 Dec 2025 (Game B for reference)', B))
    five = [
     f"<b>1. Spend:</b> spend about <b>${f0(tot.quarter_spend)}</b> of the $250k (about ${f0(tot.quarter_spend/12)}/week), not $250k. Cut Net-B, Net-C, Net-D and US Net-A to about half of September pace; push the cheap Net-A Android countries (ES, DE, JP, GB, KR, other) up to 2x. Each extra dollar beyond this plan buys installs worth less than $1 by day 120.",
     f"<b>2. Expected result (80% range):</b> {f0(tot.expected_installs)} paid installs ({f0(ip10)}-{f0(ip90)}); D120 ROAS <b>{tot.expected_d120_roas:.2f}</b> ({pr['roas120'][0]:.2f}-{pr['roas120'][2]:.2f}); 1-year ROAS <b>{tot.expected_1y_roas:.2f}</b> ({pr['roas365'][0]:.2f}-{pr['roas365'][2]:.2f}). The plan was set to 1.10, not 1.00, as a safety buffer; chance D120 ROAS is at least 1.0 is about {pr['p_roas120_ge1']*100:.0f}%.",
     "<b>3. Payback (Game A, at September CPI):</b> within 120 days: Net-D US Android (borderline), Net-A Android in JP, KR, ES, DE, GB, FR and the small 'other' group. Only within a year: Net-A low-CPI group, Net-A BR, Net-B US Android, Net-C US Android. Never in a year: Net-A US Android (D120 0.79, 1-year 0.96) and Net-B iOS US. Game B: only Net-D US pays back by D120; Net-A US, Net-C US only within a year; the rest never.",
     "<b>4. Data problem that hurt most:</b> in Game A, 7 Apr - 8 Jun in-app purchase amounts were booked in local currency as if dollars; with the 14-16 Jul rewarded-ad spike this made raw D120 ROAS 1.04 versus 0.84 after cleaning (-19%). Also, <i>ad_rev_all_sources</i> is about twice the mediation figure (double count), so I use only mediation revenue.",
     "<b>5. Biggest risk:</b> the payback numbers rest on extrapolating young cohorts with a curve learned from older ones. Game A backtests well (bias within +/-6%, error about 6-9%); the same method is 15-25% too low on Game B because B's value curve drifts, so I do not carry A's curve to B. Second risk: Net-D has only about 2 months of history and one creative.",
    ]
    for t in five: S.append(P(t, L5))
    S.append(Spacer(1, 3))
    S.append(P('Evidence and what I would do', H1))
    S.append(P("<b>Why not spend the full $250k?</b> Spending everything with no ROAS rule buys about 113k installs but returns only $0.79 of D120 revenue per dollar and loses about $53k by D120. The recommended plan buys about 91k installs (25% more than doing nothing, 72.5k at last month's pace) and still clears the 1.10 buffer. If the CFO accepts ROAS exactly 1.0, the plan would spend $160k and add about 7k installs, but the chance of reaching 1.0 falls to about 52%. A profit-first plan would spend only $82k and buy 42k installs.", B))
    S.append(img('frontier', 120*mm))
    S.append(P("<b>How the numbers were made.</b> Per-cohort revenue is predicted from the best reading each cohort has (day 7/14/30) times a multiplier learned from older cohorts of the same network and platform (shrunk to the platform and all-network curve when data is thin). Ad and in-app revenue have separate curves; 1-year value adds a tail from three curve shapes (median used, spread kept in the range). I tested this by hiding the last three months: on Game A the day-120 forecast is within 6-9% (bias +/-5%).", B))
    S.append(P("<b>Spend response (assumption).</b> More spend in one cell raises its cost per install (CPI) with elasticity 0.35-0.65 depending on network, and lowers the value of each marginal install. These elasticities are assumptions (the data cannot identify them); the plan caps any cell at 2x, keeps each line at or above 40% of September, and treats the 4 holiday weeks as 25% more expensive. Organic installs are not counted: a link between paid spend and organic installs shows in levels but vanishes in week-on-week changes.", B))
    S.append(P("<b>Creatives (Net-A takes 56% of spend).</b> To avoid CPI rising more than 30% from creative wear-out I need about <b>9 new Net-A creatives, 3 each for Net-B and Net-C, 2 for Net-D</b>, first batch ready by 13 Oct, then 10 Nov, with a last small batch by 15 Dec. Delivering 2 weeks late costs about 5% of installs, 4 weeks late about 11% and would drop ROAS to 0.99 (Appendix, section 7).", B))
    S.append(P("<b>Things to know.</b> (a) Installs are the stated goal, so the optimiser loads cheap, low-value installs; the 'low-value install share' is 64% in the plan versus 47% at baseline. (b) Net-B/Net-C/Net-D numbers have wider ranges. (c) I cannot prove the cause of the IAP anomaly from the data; I treated it as currency booking error. (d) Everything re-runs from the original files with <i>python run_all.py</i>.", B))
    doc.build(S)

# ------------------------------------------------------------------ APPENDIX
def cell_table(v, show_zero=True):
    rows = [['Cell', 'Wkly spend', 'CPI', 'ROAS D120 (80%)', 'ROAS 1y (80%)', 'P(D120>=1)', 'Group']]
    for r in v.itertuples():
        rows.append([r.cell, f0(r.baseline_weekly_spend), f2(r.cpi_ref), f"{r.roas_120:.2f} ({r.roas_120_lo:.2f}-{r.roas_120_hi:.2f})",
                     f"{r.roas_365:.2f} ({r.roas_365_lo:.2f}-{r.roas_365_hi:.2f})", f"{r.p_roas120_ge1:.2f}", r.payback_group.split('.')[0] + ('*' if isinstance(r.flag, str) else '')])
    return tbl(rows, [38*mm, 17*mm, 11*mm, 33*mm, 33*mm, 15*mm, 11*mm])
def tot_table(t):
    rows = [['Group', 'Installs (window)', 'CPI', 'LTV D120', 'ROAS D120 (80%)', 'LTV 1y', 'ROAS 1y (80%)']]
    for r in t.itertuples():
        rows.append([r.group, f0(r.installs), f2(r.cpi_ref), f2(r.ltv_120), f"{r.roas_120:.2f} ({r.roas_120_lo:.2f}-{r.roas_120_hi:.2f})", f2(r.ltv_365), f"{r.roas_365:.2f} ({r.roas_365_lo:.2f}-{r.roas_365_hi:.2f})"])
    return tbl(rows, [50*mm, 22*mm, 12*mm, 14*mm, 30*mm, 14*mm, 30*mm], fs=6.3)

PROBLEMS = [
 ['Problem', 'Where', 'Evidence', 'What it distorts', 'How handled'],
 ['Ad revenue "all sources" double counts', 'cohorts: ad_rev_all_sources_*', 'About 2x mediation ad_rev; mediation reconciles to telemetry ad revenue', 'Ad revenue about 2x, ROAS inflated', 'Use mediation ad_rev only'],
 ['Rewarded-ad eCPM spike 14-16 Jul (A), 15-16 Jul (B)', 'telemetry, cohorts d7-d30 jumps', 'Ad revenue per DAU >2x local median; rewarded eCPM jumps while impressions flat', 'D30/D60 multipliers; A removed $14.9k, B $4.0k of ad revenue', 'Spike days scaled to local norm in the cohort increments; installs of 13 and 17 Jul excluded from curve fitting'],
 ['IAP booked in local currency (A, 7 Apr - 8 Jun)', 'cohorts iap_rev; telemetry IAP per payer', 'IAP per payer 10-5000x country norm; 181 cohort rows', 'D120 ROAS overstated; $42k removed (raw A D120 ROAS 1.04 vs 0.84)', 'Outlier rows in window replaced by trimmed-mean per install. Cause not provable, flagged as assumption'],
 ['Immature horizons filled with zeros/carry-forward', 'cohorts retained_dN, *_revN', 'Values for N > age equal last value or 0', 'Understates young cohorts, ruins curves', 'A horizon is valid only if (28 Sep - install date) >= N, otherwise NaN'],
 ['Zero-cost installs inside paid networks', 'cohorts vs ua_daily (Iran etc.)', '1,936 (A) / 1,760 (B) paid-network installs with no cost row', 'CPI too low, LTV mixed', 'Excluded from paid cells and curves'],
 ['Retention in telemetry vs MMP use different definitions', 'telemetry_retention vs cohorts', 'Systematic gap; telemetry coverage ramps early on', 'Retention-based checks', 'Cohorts file used for value; telemetry only for anomaly detection'],
 ['Net-A mix shift 20 Apr; Net-B/C/D pauses and short history', 'ua_daily', 'Country mix and CPI change; Net-D starts about Aug 2025', 'Old cohorts not like new ones; thin curves', 'Recency weights (half-life 60 d), 6-week value window, extra uncertainty for networks without a mature curve'],
 ['Game B Net-A reported installs about 33x MMP installs', 'B ua_daily installs_network_reported', 'Reported vs MMP installs', 'CPI if network-reported installs were used', 'MMP installs only'],
 ['Net-D creative: cost and installs on different rows', 'A creatives_daily', 'A-K029: $0 cost, 4,171 installs; creative "unknown": $43k cost, 0 installs', 'Creative-level CPI/ROAS for Net-D', 'No creative-level CPI for Net-D; planned with network totals'],
 ['Net-A "unknown" creative id', 'A creatives_daily', '$97k cost, 573 installs on id unknown (7.2M impressions)', 'Creative-level CPI by type', 'Type comparison uses ids with installs only'],
 ['Retained > installs; d180 < d120 by rounding; odd platforms/blank countries', 'cohorts; telemetry', '27 rows in A; tiny negative increments', 'Minor', 'Negative increments clipped to 0; odd rows left in totals, excluded from cells'],
 ['Game B value curve drifts over time', 'B cohorts', 'B-on-B backtest bias -18% to -27% at day 7-30 reading', 'B forecasts too low', 'Not fixed; B intervals widened, B treated as lower confidence'],
]

def appendix():
    doc = SimpleDocTemplate(f'{ROOT}/appendix.pdf', pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=12*mm, bottomMargin=11*mm, title='Appendix', author='Bibek Nayak')
    S = []
    S.append(P('Appendix', H1)); S.append(P('1. Data problems', H2))
    S.append(tbl(PROBLEMS, [32*mm, 28*mm, 42*mm, 36*mm, 44*mm], fs=6.2))
    S.append(P('"Value" below = mediation ad revenue + full-price IAP per install, from cleaned cohorts. ROAS uses September-pace spend at a reference CPI (6-week window). Group: A = pays back within 120 days, B = only within a year, C = never; * = 80% range crosses 1.0.', SM))
    S.append(PageBreak())
    S.append(P('2. Value tables - Game A', H2)); S.append(cell_table(vA)); S.append(Spacer(1, 3)); S.append(img('cells_A', 105*mm))
    S.append(PageBreak())
    S.append(P('Game A - totals by network and country (D120 and 1 year)', H2)); S.append(tot_table(tA))
    S.append(PageBreak())
    S.append(P('3. Value tables - Game B', H2)); S.append(cell_table(vB)); S.append(Spacer(1, 3)); S.append(img('cells_B', 105*mm))
    S.append(PageBreak())
    S.append(P('Game B - totals by network and country (D120 and 1 year)', H2)); S.append(tot_table(tB))
    S.append(PageBreak())
    # model
    S.append(P('4. Model, accuracy and cross-game comparison', H2))
    S.append(P("<b>Model.</b> Cohort-level 'multiplier' curves, ratio of sums, ad and IAP separately; three levels (all, platform, network x platform) with shrinkage n0=4000 installs; recency half-life 60 days; 1-year tail = median of power-law-rate, exponential-rate and log-linear fits (spread kept as uncertainty); 80% ranges = week-block bootstrap + size-dependent residual noise + extra sd for networks without own mature curve. Cohorts younger than 7 days are not used.", B))
    w = bt[(bt.variant == 'halflife60')]
    rows = [['Train -> test', 'Reading used up to', 'n', 'Bias %', 'MAPE %', 'WAPE %']]
    for r in w.itertuples(): rows.append([f"{r.train} on {r.test}", f"day {r.max_h}", r.n, f"{r.bias_pct:.1f}", f"{r.mape_pct:.1f}", f"{r.wape_pct:.1f}"])
    S.append(tbl(rows, [32*mm, 32*mm, 12*mm, 20*mm, 20*mm, 20*mm], fs=6.4))
    S.append(P('Backtest: installs up to 2 Mar used to fit, installs 3 Mar - 31 May as test; D120 revenue per (week x network x platform) cell. A on B / B on A = curve learned on one game applied to the other.', SM))
    S.append(img('backtest', 105*mm))
    S.append(P("<b>Lessons.</b> A on A is accurate (error 6-9%, bias small). B on B has a systematic bias of -12% to -27% because its value per install keeps rising or its early readings under-state later value, so a curve from past cohorts is too low. A on B is better than B on B at short readings (bias -10% to -4%), meaning pooling across games is a reasonable fallback when a game drifts, but it is not a license to copy numbers. B on A is worst (-13% to -22%). Takeaways: use a long reading (day 30+) when available, re-fit often with recency weights, keep Game B ranges wide, and never transfer curves without a drift check. Tail shapes: the three forms differ by under 3% on A but by up to 14% on B's IAP (1.25-1.42), so B's 1-year numbers are the least certain.", B))
    S.append(PageBreak())
    # predictions
    S.append(P('5. Prediction template (filled)', H2))
    pdf = pd.read_csv(f'{ROOT}/predictions.csv')
    rows = [['ID', 'Cell', 'Metric', 'Installs from-to', 'Pred', '80% low', '80% high']]
    for r in pdf.itertuples(): rows.append([r.id, r.cell, r.metric, f"{r.install_from} to {r.install_to}", f"{r.your_prediction:.2f}", f"{r.low_80:.2f}", f"{r.high_80:.2f}"])
    S.append(tbl(rows, [10*mm, 52*mm, 18*mm, 40*mm, 14*mm, 15*mm, 15*mm], fs=6.5))
    S.append(P('Method for all eight: latest cleaned reading (d14, d30 for the D60 rows; d7 fallback) x multiplier fitted on mature Game A cohorts; for Net-B/C/D the platform curve plus extra model risk because those networks lack their own mature curve; ROAS divides by spend on the same install days.', SM))
    S.append(P('6. Plan for 6 Oct - 28 Dec (Game A)', H2))
    rows = [['Network', 'Platform', 'Country / group', 'Base wk $', 'Quarter $', 'x', 'Installs', 'D120 rev', 'ROAS D120', 'ROAS 1y']]
    for r in plan.itertuples():
        rows.append([r.network, '' if pd.isna(r.platform) else r.platform, 'TOTAL' if r.network == 'TOTAL' else str(r.country).replace('GROUP ', '')[:22], f0(r.baseline_weekly_spend), f0(r.quarter_spend), '' if pd.isna(r.spend_multiple_x) else f2(r.spend_multiple_x), f0(r.expected_installs), f0(r.expected_d120_revenue), f2(r.expected_d120_roas), f2(r.expected_1y_roas)])
    S.append(tbl(rows, [14*mm, 14*mm, 38*mm, 15*mm, 16*mm, 9*mm, 14*mm, 16*mm, 15*mm, 14*mm], fs=6.3))
    S.append(PageBreak())
    S.append(P('Plan reasoning and alternatives', H2))
    rows = [['Plan', 'Spend', 'Installs', 'D120 ROAS', 'D120 profit', '1y ROAS', 'P(ROAS>=1)', 'Low-value install share']]
    for r in alt.itertuples(): rows.append([r.plan, f0(r.spend), f0(r.installs), f2(r.d120_roas), f0(r.profit_d120), f2(r.d365_roas), f2(r.p_roas_ge1), f"{r.lowvalue_install_share:.2f}"])
    S.append(tbl(rows, [58*mm, 15*mm, 15*mm, 15*mm, 17*mm, 14*mm, 16*mm, 20*mm], fs=6.3))
    S.append(P("<b>Reasoning.</b> Objective: maximise paid installs (marketing's goal) subject to (i) budget <= $250k, (ii) portfolio D120 ROAS >= 1.10 (finance wants >= 1.0; I add 10% buffer because the 80% range on ROAS is wide), (iii) no cell above 2x or below 0.4x September pace (Net-A Android needs only 40% in aggregate), (iv) holiday weeks cost 25% more per install. Solved with SLSQP from 40 starts and confirmed with differential evolution. Spend flows to cells with cheap installs that still earn their cost (Net-A Android ES, DE, JP, other), and away from US Net-A and Net-B iOS. Net-D US has the best ROAS but the highest CPI (about $8), so it buys the fewest installs per dollar and the install objective cuts it to about half pace; a profit objective would do the opposite (see the profit-first row). Monte Carlo (shared error 0.5, curve drift 7%, elasticity uncertainty 25%) gives the ranges. The frontier in the memo shows the trade: from ROAS 1.00 to 1.10 costs about 7k installs.", B))
    S.append(P("<b>Weaknesses.</b> Elasticities are assumed, not estimated; installs-as-goal favours cheap low-value installs; the holiday uplift is a given; organic spillover ignored (levels elasticity 0.30 on A but zero in changes).", B))
    S.append(PageBreak())
    S.append(P('7. Creative plan (Game A, next quarter)', H2))
    ctype = {'Net-A': 'Video and playable pieces plus search text ads (search ROAS D7 0.55 vs display 0.40; IPM 13 vs 6); keep display as the base',
             'Net-B': 'Playable sets (89% of spend today); do not pick winners on IPM alone (IPM 13-19 but ROAS D7 0.35-0.39)',
             'Net-C': 'Video + playable (99% of spend); add a second concept to test, CPI 2.6',
             'Net-D': 'Single store-listing image slot (only one creative can run); refresh it, report cost and installs on the same id'}
    lead = {'Net-A': 'Batches 13 Oct, 10 Nov, 15 Dec', 'Net-B': '13 Oct and 17 Nov', 'Net-C': '13 Oct and 17 Nov', 'Net-D': '13 Oct'}
    rows = [['Network', 'Impressions next quarter', 'New creatives needed (min / plan)', 'Ready by', 'Type of ad']]
    for r in cn.itertuples(): rows.append([r.network, f0(r.impressions_q), f"{r.creatives_min} / {r.creatives_recommended}", lead[r.network], ctype[r.network]])
    S.append(tbl(rows, [14*mm, 24*mm, 26*mm, 26*mm, 92*mm], fs=6.4))
    S.append(P("<b>Method.</b> Impressions = spend / CPM x 1000 per cell at September CPM. Weeks 1-2 are served by today's creatives. A creative is retired when its CPI is 30% above fresh (Net-A 1.5M impressions, Net-B and Net-C 100k, Net-D 200k). I schedule just enough new creatives week by week, add 25% spare, and ready each batch one week before use. Net-B Android and iOS share ad sets, so they are counted together.", B))
    S.append(P("<b>Late or short?</b> (A) 2 weeks late: about -5% installs and ROAS 1.05; (B) 4 weeks late: about -11% installs and ROAS 0.99; (C) 25% too few: almost no effect because spare was built in; 50% too few: -3%. Net-A is the one to protect (56% of spend, 43% peak CPI uplift if late).", B))
    rows = [['Scenario', 'Installs', 'vs plan %', 'D120 revenue', 'D120 ROAS']]
    for r in crk.itertuples(): rows.append([r.scenario, f0(r.installs), f"{r.installs_vs_plan_pct:.1f}", f0(r.d120_rev), f2(r.roas120)])
    S.append(tbl(rows, [40*mm, 22*mm, 22*mm, 26*mm, 22*mm], fs=6.4))
    ctt = ct.copy()
    rows = [['Network', 'Creative type', 'Spend', 'CPI', 'IPM', 'ROAS D7', 'Ret D7']]
    for r in ctt.itertuples():
        if r.installs > 0: rows.append([r.network, r.creative_type[:48], f0(r.spend), f2(r.cpi), f"{r.ipm:.1f}", f"{r.roas_d7:.2f}", f"{r.ret_d7:.2f}"])
    S.append(Spacer(1, 3)); S.append(tbl(rows, [14*mm, 70*mm, 18*mm, 12*mm, 12*mm, 16*mm, 18*mm], fs=6.3))
    S.append(P('Caveat: creative-type evidence is thin (one id per type for Net-A; Net-D has no usable creative CPI because of the cost/installs split).', SM))
    S.append(PageBreak())
    S.append(P('8. AI use log', H2))
    S.append(P("<b>Tool:</b> Claude (Anthropic) did the analysis in one session; full transcripts are attached separately in /ai_transcripts. <b>Two mistakes caught:</b> (1) I first read payers_dN as cumulative, which made the payer curve impossible; checking against telemetry showed it is per-day, and I fixed it. (2) I first explained the Jun-Jul d7-to-d30 jumps as an outage or backfill; telemetry showed a rewarded-eCPM spike on 14-16 Jul instead, so the correction is a spike correction. Also: early Net-D ROAS was too high because the window included rich early August cohorts; I moved to a 6-week window. <b>Time saver:</b> having the assistant write the cohort cleaning, curve fitting, bootstrapping and the optimiser in re-runnable code, with a verification solver, saved most of the hours.", B))
    S.append(P('9. What I skipped and why', H2))
    for t in ["Per-campaign (below cell) modelling - too little data per campaign.",
              "Estimating spend elasticity from history - spend moves are confounded with seasonality and mix shifts; assumed 0.35-0.65 and stated.",
              "Fixing Game B drift - would need more time; B intervals widened and flagged.",
              "Creative-level CPI for Net-D and part of Net-A - source rows do not link cost and installs.",
              "Counting organic uplift - evidence inconsistent between levels and changes.",
              "Confirming the cause of the IAP anomaly - not possible from the data."]: S.append(P('- ' + t, B))
    doc.build(S)

memo(); appendix()
from pypdf import PdfReader
for n in ['memo', 'appendix']: print(n, len(PdfReader(f'{ROOT}/{n}.pdf').pages), 'pages')
