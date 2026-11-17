"""
Revenue-curve ("multiplier") model.

Idea
----
A cohort's cumulative revenue per install grows along a curve that is similar across
cohorts of the same game: LTV(30) -> LTV(120) -> LTV(180) -> LTV(365).  For a cohort
whose age is `a`, the best available early reading h* (3, 7, 14, 30, 60, 90 days) is
multiplied by a factor m(h* -> T) learned from MATURE cohorts (age >= T):

    pred_T(cohort) = ad_{h*} * m_ad(seg, h*, T) + iap_{h*} * m_iap(seg, h*, T)

* Ratio-of-sums (not mean of ratios) so tiny / noisy cohorts do not dominate.
* Ad and IAP revenue have separate curves (IAP is lumpy, accrues later, differs by game).
* Three levels of segment, each shrunk to the one above with a pseudo-sample n0 installs:
      all paid cohorts  ->  platform (android / ios)  ->  network x platform
  (networks / platforms with little mature data automatically borrow the pooled curve).
* Recency weights (half-life in days since the cohort matured) let the curve follow drift.
* 1-year value = pred_180 * tail(180 -> 365); tail is the median of 3 functional forms
  fitted to the mature-180 curve (power-law rate, exponential rate, log-linear), the
  spread between forms being model uncertainty.
* Uncertainty: week-block bootstrap over mature cohorts (multiplier uncertainty)
  + a size-dependent residual noise term calibrated on a time-split backtest.
"""
import numpy as np
import pandas as pd
from common import HZ, with_asof

SRC = [3, 7, 14, 30, 60, 90]
TGT = [30, 60, 120, 180]
PLATS = ["android", "ios"]


def _plat(p):
    return np.where(pd.Series(p).astype(str).str.startswith("ios"), "ios", "android")


class Curve:
    def __init__(self, co, asof, halflife=60.0, n0=4000.0, boot=0, seed=0, paid_only=True,
                 exclude=("2025-07-13", "2025-07-17"), use_network=True):
        self.asof = pd.Timestamp(asof)
        self.halflife = halflife
        self.n0 = n0
        self.use_network = use_network
        d = with_asof(co, self.asof)
        d["plat"] = _plat(d.platform)
        d["np"] = d.network.astype(str) + "|" + d.plat
        base = d[(d.installs >= 1)]
        if paid_only:
            base = base[base.paid]
        if exclude:   # installs on the corrected spike days are the least reliable
            base = base[~base.install_date.between(*exclude)]
        self.base = base
        self.rng = np.random.default_rng(seed)
        self.table = {}
        self.weeks = None
        self.nps = sorted(base.np.unique())
        self._build()
        ones = np.ones(len(self.weeks))
        self.m = self._mult(ones)
        self.tail = self._tail(ones)
        self.boots = []
        for _ in range(boot):
            cnt = np.bincount(self.rng.integers(0, len(self.weeks), len(self.weeks)),
                              minlength=len(self.weeks)).astype(float)
            self.boots.append((self._mult(cnt), self._tail(cnt)))

    # ------------------------------------------------------------------ fitting helpers
    def _build(self):
        b = self.base
        wk = b.install_date.dt.to_period("W-SUN").astype(str)
        self.weeks = sorted(wk.unique())
        widx = {w: i for i, w in enumerate(self.weeks)}
        b = b.assign(w=wk.map(widx))
        nw = len(self.weeks)
        keys = [("all", "all")] + [("plat", p) for p in PLATS] + [("np", k) for k in self.nps]
        for T in TGT:
            mat = b[b.age >= T]
            wt = 0.5 ** ((mat.age - T) / self.halflife)
            for typ, pref in [("ad", "ad_"), ("iap", "iap_")]:
                for h in SRC:
                    if h >= T:
                        continue
                    ok = mat[f"{pref}{T}"].notna() & mat[f"{pref}{h}"].notna()
                    mm = mat[ok]
                    ww = wt[ok]
                    for lvl, key in keys:
                        if lvl == "all":
                            sel = np.ones(len(mm), bool)
                        elif lvl == "plat":
                            sel = (mm.plat == key).values
                        else:
                            sel = (mm.np == key).values
                        x = mm[sel]
                        w = ww[sel]
                        N = np.bincount(x.w, weights=w * x[f"{pref}{T}"], minlength=nw)
                        D = np.bincount(x.w, weights=w * x[f"{pref}{h}"], minlength=nw)
                        I = np.bincount(x.w, weights=w * x.installs, minlength=nw)
                        self.table[(typ, lvl, key, h, T)] = (N, D, I)
        mat = b[b.age >= 180]
        wt = 0.5 ** ((mat.age - 180) / self.halflife)
        self.tailpts = {}
        for typ, pref in [("ad", "ad_"), ("iap", "iap_")]:
            pts = []
            for h in [30, 60, 90, 120, 180]:
                ok = mat[f"{pref}{h}"].notna()
                x = mat[ok]
                w = wt[ok]
                num = np.bincount(x.w, weights=w * x[f"{pref}{h}"], minlength=nw)
                den = np.bincount(x.w, weights=w * x.installs, minlength=nw)
                pts.append((num, den))
            self.tailpts[typ] = pts

    def _ratio(self, cnt, typ, lvl, key, h, T):
        N, D, I = self.table[(typ, lvl, key, h, T)]
        return (cnt * N).sum(), (cnt * D).sum(), (cnt * I).sum()

    def _mult(self, cnt):
        out = {}
        for typ in ["ad", "iap"]:
            for T in TGT:
                for h in SRC:
                    if h >= T:
                        continue
                    n, d, i = self._ratio(cnt, typ, "all", "all", h, T)
                    m_all = n / d if d > 0 else 1.0
                    m_pl = {}
                    for p in PLATS:
                        n, d, i = self._ratio(cnt, typ, "plat", p, h, T)
                        raw = n / d if d > 0 else m_all
                        rho = i / (i + self.n0)
                        m_pl[p] = rho * raw + (1 - rho) * m_all
                        out[(typ, "plat", p, h, T)] = m_pl[p]
                    if self.use_network:
                        for k in self.nps:
                            p = k.split("|")[1]
                            n, d, i = self._ratio(cnt, typ, "np", k, h, T)
                            raw = n / d if d > 0 else m_pl[p]
                            rho = i / (i + self.n0)
                            out[(typ, "np", k, h, T)] = rho * raw + (1 - rho) * m_pl[p]
        return out

    def _tail(self, cnt):
        res = {}
        t_pts = np.array([30, 60, 90, 120, 179.0])
        for typ in ["ad", "iap"]:
            ltv = np.array([(cnt * n).sum() / max((cnt * dd).sum(), 1e-9) for n, dd in self.tailpts[typ]])
            dt = np.diff(t_pts)
            rate = np.diff(ltv) / dt
            tm = (t_pts[:-1] + t_pts[1:]) / 2
            r365 = {}
            ok = rate > 1e-9
            L180 = ltv[-1]
            if ok.sum() >= 3 and L180 > 0:
                p, lc = np.polyfit(np.log(tm[ok]), np.log(rate[ok]), 1)
                c = np.exp(lc)
                integ = c * np.log(365 / 180) if abs(p + 1) < 1e-6 else c / (p + 1) * (365 ** (p + 1) - 180 ** (p + 1))
                r365["power"] = 1 + max(integ, 0) / L180
                lam, la = np.polyfit(tm[ok], np.log(rate[ok]), 1)
                a = np.exp(la)
                lam = -lam
                integ = a / lam * (np.exp(-lam * 180) - np.exp(-lam * 365)) if lam > 1e-6 else a * 185
                r365["exp"] = 1 + max(integ, 0) / L180
                b_, a_ = np.polyfit(np.log(t_pts[1:]), ltv[1:], 1)
                r365["log"] = 1 + max(b_ * np.log(365 / 180), 0) / L180
            else:
                r365 = {"power": 1.0, "exp": 1.0, "log": 1.0}
            res[typ] = r365
        return res

    # ------------------------------------------------------------------ prediction
    def tail_ratio(self, typ, form="median", tail=None):
        t = (tail or self.tail)[typ]
        return float(np.median(list(t.values()))) if form == "median" else t[form]

    def _m(self, mult, typ, np_key, plat, h, Tm):
        if self.use_network and (typ, "np", np_key, h, Tm) in mult:
            return mult[(typ, "np", np_key, h, Tm)]
        return mult[(typ, "plat", plat, h, Tm)]

    def predict(self, d, T, mult=None, tail=None, form="median", min_h=3, max_h=None):
        """Per-cohort predicted cumulative revenue (ad, iap) at horizon T (30/60/120/180/365)
        using information available at self.asof only; NaN where there is no usable reading."""
        mult = mult or self.m
        age = (self.asof - d.install_date).dt.days.values
        plat = _plat(d.platform)
        npk = (d.network.astype(str) + "|" + pd.Series(plat, index=d.index)).values
        Tm = 180 if T == 365 else T
        ad = np.full(len(d), np.nan)
        ip = np.full(len(d), np.nan)
        for pref, arr, typ in [("ua_", ad, "ad"), ("ui_", ip, "iap")]:
            mature = age >= Tm
            arr[mature] = d[f"{pref}{Tm}"].values[mature]
            todo = ~mature
            chosen = np.full(len(d), -1)
            for h in sorted([h for h in SRC if h < Tm and h >= min_h and (max_h is None or h <= max_h)]):
                chosen = np.where(todo & (age >= h), h, chosen)
            for h in set(chosen[todo]):
                if h < 0:
                    continue
                sel = todo & (chosen == h)
                src = d[f"{pref}{h}"].values
                for k in set(npk[sel]):
                    ss = sel & (npk == k)
                    p = k.split("|")[1]
                    arr[ss] = src[ss] * self._m(mult, typ, k, p, h, Tm)
        if T == 365:
            ad = ad * self.tail_ratio("ad", form, tail)
            ip = ip * self.tail_ratio("iap", form, tail)
        return ad, ip


def window_table(d, curve, T_list=(30, 60, 120, 180, 365), min_h=7, boots=True, form_spread=True, max_h=None):
    """Aggregate predictions for a set of cohort rows d (one cell / window)."""
    d = d[(d.installs > 0)]
    age = (curve.asof - d.install_date).dt.days
    d = d[age >= min_h]
    out = {"installs": float(d.installs.sum()), "cost": float(d.cost.sum()), "n_rows": len(d)}
    for T in T_list:
        ad, ip = curve.predict(d, T, min_h=min_h, max_h=max_h)
        out[f"rev_{T}"] = float(np.nansum(ad + ip))
        out[f"ad_{T}"] = float(np.nansum(ad))
        out[f"iap_{T}"] = float(np.nansum(ip))
        if boots and curve.boots:
            dr = []
            for mult, tail in curve.boots:
                f_ = str(curve.rng.choice(["power", "exp", "log"])) if T == 365 else "median"
                a_, i_ = curve.predict(d, T, mult=mult, tail=tail, form=f_, min_h=min_h, max_h=max_h)
                dr.append(np.nansum(a_ + i_))
            out[f"draws_{T}"] = np.array(dr)
        if T == 365 and form_spread:
            vals = []
            for f in ["power", "exp", "log"]:
                a_, i_ = curve.predict(d, T, form=f, min_h=min_h, max_h=max_h)
                vals.append(np.nansum(a_ + i_))
            out["form_lo"], out["form_hi"] = float(min(vals)), float(max(vals))
    return out
