"""
Shared helpers for the Growth Case (Games A and B).

Everything here is deterministic and works from the ORIGINAL csv files in ../data.
Conventions
-----------
* "As of" date is 2025-09-30. Last full day of data is LAST = 2025-09-28.
* Cohort age = (LAST - install_date).days. A horizon N (retained_dN, *_revN) is
  only trusted when age >= N. Younger values are structural zeros / carried
  forward and are set to NaN.
* Ad revenue = mediation figure `ad_rev_*` (NOT `ad_rev_all_sources_*`, which is
  ~2x and double counts; see 01_audit.py reconciliation against telemetry).
* Revenue = ad_rev + iap_rev (IAP at full price, as the CFO rule asks).
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")
FIG = os.path.join(ROOT, "figs")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

ASOF = pd.Timestamp("2025-09-30")
LAST = pd.Timestamp("2025-09-28")
PAID = ["Net-A", "Net-B", "Net-C", "Net-D", "Net-E", "Net-F"]
HZ = [0, 1, 3, 7, 14, 30, 60, 90, 120, 180]  # cumulative revenue horizons in the cohort file
HZ_NOTE = {180: 179}  # d180 covers days 0..179


# --------------------------------------------------------------------------- loading
def load(game):
    ua = pd.read_csv(f"{DATA}/Game{game}_ua_daily.csv", parse_dates=["date"])
    co = pd.read_csv(f"{DATA}/Game{game}_cohorts.csv", parse_dates=["install_date"])
    te = pd.read_csv(f"{DATA}/Game{game}_telemetry_daily.csv", parse_dates=["date"])
    tr = pd.read_csv(f"{DATA}/Game{game}_telemetry_retention.csv", parse_dates=["install_date"])
    cr = pd.read_csv(f"{DATA}/Game{game}_creatives_daily.csv", parse_dates=["date"])
    ca = pd.read_csv(f"{DATA}/Game{game}_creatives_catalog.csv")
    return dict(ua=ua, co=co, te=te, tr=tr, cr=cr, ca=ca)


# --------------------------------------------------------------------------- telemetry anomalies
def telemetry_daily(te):
    t = te.copy()
    t["ad_rev"] = t.banner_rev + t.interstitial_rev + t.rewarded_rev
    d = t.groupby("date").agg(dau=("dau", "sum"), ad_rev=("ad_rev", "sum"), iap=("iap_rev", "sum"),
                              rimps=("rewarded_imps", "sum"), rrev=("rewarded_rev", "sum"),
                              new=("new_installs", "sum"))
    d["apd"] = d.ad_rev / d.dau.replace(0, np.nan)
    d["ecpm_rew"] = d.rrev / d.rimps.replace(0, np.nan) * 1000
    return d


def ad_spike_factors(te, min_dau=3000, thresh=2.0):
    """Days on which ad revenue per DAU is > thresh x its local median.
    Returns dict {date: factor f_t}, f_t = observed / expected (>1)."""
    d = telemetry_daily(te)
    d = d[d.dau >= min_dau]
    med = d.apd.rolling(21, center=True, min_periods=7).median()
    # median of a window containing a 3-day spike is still stable
    ratio = d.apd / med
    sp = ratio[ratio > thresh]
    return {k: float(v) for k, v in sp.items()}


def iap_window(game):
    """Calendar window in which telemetry shows IAP per payer 10x-5000x the country norm
    (local-currency amounts booked as USD; see 01_audit.py). Only Game A is affected."""
    if game == "A":
        return pd.Timestamp("2025-04-07"), pd.Timestamp("2025-06-08")
    return None


# --------------------------------------------------------------------------- cohort cleaning
def _intervals():
    """(k, lo, hi): offsets (in days after install day) covered by increment k."""
    iv = []
    prev = -1
    for k, h in enumerate(HZ):
        hi = HZ_NOTE.get(h, h)
        iv.append((k, prev + 1, hi))
        prev = hi
    return iv


def clean_cohorts(game, data=None, verbose=False):
    """Return cohort frame with
       cost (merged from UA), age, valid-horizon masks and cleaned cumulative revenue:
       ad_N, iap_N, rev_N (N in HZ); invalid horizons are NaN.
       Also returns a dict of correction diagnostics."""
    data = data or load(game)
    co, ua, te = data["co"].copy(), data["ua"], data["te"]
    key = ["install_date", "platform", "country", "network", "campaign_id"]
    cost = ua.rename(columns={"date": "install_date"})[key + ["cost", "impressions_network_reported",
                                                              "installs_network_reported"]]
    co = co.merge(cost, on=key, how="left")
    co["cost"] = co.cost.fillna(0.0)
    co["age"] = (LAST - co.install_date).dt.days
    iv = _intervals()
    diag = {}

    # ---- retention: structural zeros -> NaN
    for N in [1, 3, 7, 14, 30, 60, 90, 120]:
        co.loc[co.age < N, f"retained_d{N}"] = np.nan

    # ---- ad revenue: increments, spike correction, rebuild cumulative
    spikes = ad_spike_factors(te)
    diag["ad_spikes"] = spikes
    ad_cols = [f"ad_rev_d{h}" for h in HZ]
    iap_cols = [f"iap_rev_d{h}" for h in HZ]
    ad_inc = co[ad_cols].diff(axis=1)
    ad_inc.iloc[:, 0] = co[ad_cols[0]]
    ad_inc = ad_inc.clip(lower=0)          # tiny negative rounding (d120->d180) set to 0
    iap_inc = co[iap_cols].diff(axis=1)
    iap_inc.iloc[:, 0] = co[iap_cols[0]]
    iap_inc = iap_inc.clip(lower=0)

    excess_removed = np.zeros(len(co))
    for k, lo, hi in iv:
        n = hi - lo + 1
        s = np.zeros(len(co))
        for d, f in spikes.items():
            off = (d - co.install_date).dt.days
            inside = (off >= lo) & (off <= hi)
            s += np.where(inside, f - 1.0, 0.0)
        scale = n / (n + s)
        before = ad_inc.iloc[:, k].values
        ad_inc.iloc[:, k] = before * scale
        excess_removed += (before - before * scale)
    diag["ad_excess_removed_usd"] = float(excess_removed.sum())

    # ---- IAP: outlier increments inside the anomaly window -> replaced by trimmed mean
    win = iap_window(game)
    iap_flag = np.zeros(len(co), dtype=bool)
    iap_removed = 0.0
    if win:
        lo_d, hi_d = win
        for k, lo, hi in iv:
            start = co.install_date + pd.to_timedelta(lo, unit="D")
            end = co.install_date + pd.to_timedelta(hi, unit="D")
            overlap = (start <= hi_d) & (end >= lo_d)
            pi = iap_inc.iloc[:, k] / co.installs.replace(0, np.nan)
            clean = (~overlap) & (co.installs >= 5)
            cap = pi[clean].quantile(0.995)
            tm = pi[clean][pi[clean] <= cap].mean()
            bad = overlap & (pi > cap) & (co.installs >= 1)
            new = (tm * co.installs).where(bad, iap_inc.iloc[:, k])
            iap_removed += float((iap_inc.iloc[:, k] - new).where(bad, 0).sum())
            iap_inc.iloc[:, k] = new
            iap_flag |= bad.values
    diag["iap_flagged_rows"] = int(iap_flag.sum())
    diag["iap_removed_usd"] = iap_removed
    co["iap_flag"] = iap_flag

    ad_cum = ad_inc.cumsum(axis=1)
    iap_cum = iap_inc.cumsum(axis=1)
    for j, h in enumerate(HZ):
        # cleaned, UNMASKED cumulative revenue (use with_asof() to mask by maturity)
        co[f"ua_{h}"] = ad_cum.iloc[:, j]
        co[f"ui_{h}"] = iap_cum.iloc[:, j]
        # raw (uncorrected, unmasked) kept for audit evidence
        co[f"raw_rev_{h}"] = co[f"ad_rev_d{h}"] + co[f"iap_rev_d{h}"]
    co = with_asof(co, LAST)
    co["paid"] = co.network.isin(PAID) & (co.cost > 0)
    co["zero_cost_paid"] = co.network.isin(PAID) & (co.cost == 0)
    return co, diag


def with_asof(co, asof):
    """Mask cumulative revenue by maturity relative to `asof` (last full data day):
       a horizon h is trusted only if (asof - install_date) >= h days."""
    co = co.copy()
    co["age"] = (pd.Timestamp(asof) - co.install_date).dt.days
    for h in HZ:
        ok = co.age >= h
        co[f"ad_{h}"] = co[f"ua_{h}"].where(ok)
        co[f"iap_{h}"] = co[f"ui_{h}"].where(ok)
        co[f"rev_{h}"] = co[f"ad_{h}"] + co[f"iap_{h}"]
    return co


# --------------------------------------------------------------------------- cells
def country_groups(game, co):
    """Country grouping used inside each (network, platform). Rule (both games):
       * a country stays on its own if it holds >= 4% of that network-platform's paid
         spend over the whole history OR >= $150/week in the baseline window;
       * the rest are grouped by cost level: 'low-CPI' (< $1.00 blended) vs 'other'.
       Returns dict (network, platform) -> {country: group_name}."""
    paid = co[co.paid].copy()
    out = {}
    for (net, plat), g in paid.groupby(["network", "platform"]):
        by = g.groupby("country").agg(cost=("cost", "sum"), inst=("installs", "sum"))
        by["cpi"] = by.cost / by.inst
        tot = by.cost.sum()
        base = g[(g.install_date >= "2025-09-01") & (g.install_date <= "2025-09-28")].groupby("country").cost.sum() / 4
        mapping = {}
        for c, r in by.iterrows():
            bw = base.get(c, 0.0)
            if r.cost / tot >= 0.04 or bw >= 150:
                mapping[c] = c
            elif r.cpi < 1.0:
                mapping[c] = "grp-lowCPI"
            else:
                mapping[c] = "grp-other"
        out[(net, plat)] = mapping
    return out


def add_cells(co, game, groups=None):
    groups = groups or country_groups(game, co)
    cell = []
    grp = []
    for net, plat, c in zip(co.network, co.platform, co.country):
        m = groups.get((net, plat))
        if m is None:
            cell.append(None); grp.append(None); continue
        g = m.get(c)
        if g is None:      # country with installs but no paid spend in this net-platform
            g = "no-spend"
        grp.append(g)
        cell.append(f"{net}|{plat}|{g}")
    co = co.copy()
    co["grp"] = grp
    co["cell"] = cell
    return co, groups


def members(groups):
    """cell -> sorted list of countries (for the plan / notes)."""
    res = {}
    for (net, plat), m in groups.items():
        for c, g in m.items():
            res.setdefault(f"{net}|{plat}|{g}", []).append(c)
    return {k: sorted(v) for k, v in res.items()}
