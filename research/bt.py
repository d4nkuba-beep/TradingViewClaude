"""Bar-based intraday backtester for IB/ORB ideas on TradingView-MCP OHLCV data.

Conservative fill rules:
  - Stop and target touched in the same bar -> stop first.
  - Entry bar: stop counts if touched; target counts only if the bar closes beyond it.
PnL is in % of entry price, minus round-trip cost COST_PCT.
"""
import json, os, sys, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

NY = ZoneInfo("America/New_York")
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load(name):
    b = json.load(open(f"{DATA}/{name}.json"))
    df = pd.DataFrame(b)
    df["ts"] = pd.to_datetime(df.t, unit="s", utc=True).dt.tz_convert(NY)
    df["date"] = df.ts.dt.date
    df["hm"] = df.ts.dt.hour * 100 + df.ts.dt.minute
    df = df[(df.hm >= 930) & (df.hm < 1600)].reset_index(drop=True)
    return df


def mins(hm):
    return (hm // 100) * 60 + hm % 100


class Trade:
    def __init__(s, day, side, entry, stop, target, tag):
        s.day, s.side, s.entry, s.stop, s.target, s.tag = day, side, entry, stop, target, tag
        s.exit = None


def manage(tr, bars, i0, entry_bar_idx):
    """Walk bars from entry bar; return exit price."""
    for j in range(entry_bar_idx, len(bars)):
        o, h, l, c = bars.o[j], bars.h[j], bars.l[j], bars.c[j]
        first = j == entry_bar_idx
        if tr.side > 0:
            if tr.stop is not None and l <= tr.stop:
                return min(tr.stop, o) if not first else tr.stop
            if tr.target is not None and (h >= tr.target and (not first or c >= tr.target)):
                return tr.target if first else max(tr.target, o)
        else:
            if tr.stop is not None and h >= tr.stop:
                return max(tr.stop, o) if not first else tr.stop
            if tr.target is not None and (l <= tr.target and (not first or c <= tr.target)):
                return tr.target if first else min(tr.target, o)
        if bars.hm[j] >= 1555 or j == len(bars) - 1:
            return c
    return bars.c.iloc[-1]


def day_vwap(d):
    pv = (d[["h", "l", "c"]].mean(axis=1) * d.v).cumsum()
    return pv / d.v.cumsum()


def run(df, strat, tf_min, **kw):
    trades = []
    days = list(df.groupby("date"))
    ib_hist, daily = [], []
    for k, (day, d) in enumerate(days):
        d = d.reset_index(drop=True)
        d["vwap"] = day_vwap(d)
        ib_end = kw.get("ib_end", 1030)
        ib = d[d.hm < ib_end]
        if len(ib) == 0 or len(d) < 10:
            continue
        ibh, ibl = ib.h.max(), ib.l.min()
        rng = ibh - ibl
        ib_med = np.median(ib_hist[-20:]) if len(ib_hist) >= 10 else None
        ib_hist.append(rng / d.o[0])
        tr = strat(d, day, ibh, ibl, rng, ib_med, daily, tf_min, **kw)
        daily.append(dict(o=d.o[0], h=d.h.max(), l=d.l.min(), c=d.c.iloc[-1]))
        if tr:
            trades.extend(tr if isinstance(tr, list) else [tr])
    return trades


# ─── strategies ────────────────────────────────────────────────────────────
def slope_at(d, j, tf_min, slope_min=50):
    n = max(1, round(slope_min / tf_min))
    return d.vwap[j] - d.vwap[j - n] if j - n >= 0 else np.nan


def crosses_until(d, j):
    s = np.sign(d.c[: j + 1] - d.vwap[: j + 1])
    return int((s.diff().fillna(0) != 0).sum())


def ib_filter_ok(rng, d, ib_med, ibf):
    if ibf is None or ib_med is None:
        return True
    r = rng / d.o[0]
    return r < ib_med if ibf == "narrow" else r > ib_med


def s_retrace(d, day, ibh, ibl, rng, ib_med, daily, tf, entry_pct=0.25, stop_pct=0.5,
              max_cross=6, ibf=None, **_):
    """Our Setup 1: limit at 25% retrace, stop 50%, target IB extreme."""
    if rng <= 0 or not ib_filter_ok(rng, d, ib_med, ibf):
        return None
    # direction decided on the last bar before the retrace window opens (bar closing <= 10:20/10:30)
    start = mins(1020)
    for j in range(len(d)):
        bar_close_min = mins(d.hm[j]) + tf
        if bar_close_min < start:
            continue
        if d.hm[j] >= 1200:
            return None
        if j == 0:
            continue
        post = d.iloc[:j][d.hm[:j] >= 1030]
        if len(post) and (post.h.max() > ibh or post.l.min() < ibl):
            return None  # IB extreme swept -> cancel
        sl = slope_at(d, j - 1, tf)
        if np.isnan(sl):
            continue
        if tf == 5 and crosses_until(d, j - 1) > max_cross:
            continue
        c, vw = d.c[j - 1], d.vwap[j - 1]
        side = -1 if (c < vw and sl < 0) else (1 if (c > vw and sl > 0) else 0)
        if side == 0:
            continue
        if side < 0:
            e, s, t = ibl + entry_pct * rng, ibl + stop_pct * rng, ibl
            if d.h[j] >= e:
                tr = Trade(day, -1, max(e, d.o[j]) if d.o[j] > e else e, s, t, "RET")
                tr.entry = e if d.o[j] <= e else d.o[j]
                if tr.entry >= s:
                    return None
                tr.exit = manage(tr, d, 0, j)
                return tr
        else:
            e, s, t = ibh - entry_pct * rng, ibh - stop_pct * rng, ibh
            if d.l[j] <= e:
                tr = Trade(day, 1, e, s, t, "RET")
                tr.entry = e if d.o[j] >= e else d.o[j]
                if tr.entry <= s:
                    return None
                tr.exit = manage(tr, d, 0, j)
                return tr
    return None


def s_orb(d, day, ibh, ibl, rng, ib_med, daily, tf, tp_r=1.0, stop_mode="mid", vwap_dir=True,
          ibf=None, **_):
    """Our Setup 2: stop-entry beyond IB after 10:30, stop at IB mid, TP = tp_r * R (None = EOD)."""
    if rng <= 0 or not ib_filter_ok(rng, d, ib_med, ibf):
        return None
    for j in range(len(d)):
        if d.hm[j] < 1030:
            continue
        if d.hm[j] >= 1200:
            return None
        sl = slope_at(d, j - 1, tf)
        up_ok = (not vwap_dir) or sl > 0
        dn_ok = (not vwap_dir) or sl < 0
        long_hit = up_ok and d.h[j] > ibh
        short_hit = dn_ok and d.l[j] < ibl
        if long_hit and short_hit:
            return None  # ambiguous, skip
        if long_hit or short_hit:
            side = 1 if long_hit else -1
            e = max(ibh, d.o[j]) if side > 0 else min(ibl, d.o[j])
            stop = (ibh + ibl) / 2 if stop_mode == "mid" else (ibl if side > 0 else ibh)
            risk = abs(e - stop)
            tgt = None if tp_r is None else e + side * tp_r * risk
            tr = Trade(day, side, e, stop, tgt, "ORB")
            tr.exit = manage(tr, d, 0, j)
            return tr
    return None


def s_dual_thrust(d, day, ibh, ibl, rng, ib_med, daily, tf, n=4, k1=0.5, k2=0.5, **_):
    """je-suis-tm Dual Thrust: trigger = open +/- k*max(HH-LC, HC-LL) of last n days,
    stop-and-reverse on the opposite trigger, flat at EOD."""
    if len(daily) < n:
        return None
    w = pd.DataFrame(daily[-n:])
    R = max(w.h.max() - w.c.min(), w.c.max() - w.l.min())
    up, dn = d.o[0] + k1 * R, d.o[0] - k2 * R
    trades, pos = [], None
    for j in range(len(d)):
        h, l = d.h[j], d.l[j]
        if pos is None:
            if h >= up and l <= dn:
                return trades
            if h >= up:
                pos = Trade(day, 1, max(up, d.o[j]), None, None, "DT")
            elif l <= dn:
                pos = Trade(day, -1, min(dn, d.o[j]), None, None, "DT")
        elif pos.side > 0 and l <= dn:
            pos.exit = min(dn, d.o[j]); trades.append(pos)
            pos = Trade(day, -1, pos.exit, None, None, "DT")
        elif pos.side < 0 and h >= up:
            pos.exit = max(up, d.o[j]); trades.append(pos)
            pos = Trade(day, 1, pos.exit, None, None, "DT")
        if d.hm[j] >= 1555 or j == len(d) - 1:
            break
    if pos:
        pos.exit = d.c.iloc[-1]; trades.append(pos)
    return trades


def s_first_candle_orb(d, day, ibh, ibl, rng, ib_med, daily, tf, **_):
    """Benchmark (Zarattini/Aziz-style): direction of the first bar, stop at its other
    extreme, hold to EOD. Entry at open of bar 2."""
    o, c = d.o[0], d.c[0]
    if c == o or len(d) < 3:
        return None
    side = 1 if c > o else -1
    stop = d.l[0] if side > 0 else d.h[0]
    tr = Trade(day, side, d.o[1], stop, None, "FC")
    if (side > 0 and tr.entry <= stop) or (side < 0 and tr.entry >= stop):
        return None
    tr.exit = manage(tr, d, 0, 1)
    return tr


# ─── stats ─────────────────────────────────────────────────────────────────
def stats(trades, cost_pct):
    if not trades:
        return dict(n=0)
    r = np.array([t.side * (t.exit - t.entry) / t.entry * 100 - cost_pct for t in trades])
    eq = r.cumsum()
    dd = (np.maximum.accumulate(eq) - eq).max()
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    # simple 2-way split for stability
    half = len(r) // 2
    return dict(n=len(r), win=round((r > 0).mean() * 100, 1),
                pf=round(wins / losses, 2) if losses else float("inf"),
                avg_bp=round(r.mean() * 100, 2), tot_pct=round(r.sum(), 2),
                maxdd_pct=round(dd, 2),
                h1=round(r[:half].sum(), 2), h2=round(r[half:].sum(), 2))
