#!/usr/bin/env python3
"""Offline-Backtest der Killzone-Sweep+BOS-Strategie (1:1-Port der Pine-Logik).

Da in dieser Umgebung keine Marktdaten-APIs erreichbar sind, arbeitet der
Backtester mit CSV-Exporten aus TradingView:
  Chart (1-5 Min, MNQ/MES/MGC) -> Menü "..." -> "Chartdaten exportieren..."
  -> ISO-Zeit, alle Bars. Erwartete Spalten: time, open, high, low, close.

Nutzung:
  python3 killzone_sweep_bos_backtest.py daten.csv --preset london
  python3 killzone_sweep_bos_backtest.py daten.csv --preset ny-am --rr 2.0
  # danach Challenge-Wahrscheinlichkeit aus den echten Trades:
  python3 prop_challenge_monte_carlo.py --csv trades_out.csv

Regeln (identisch zum Pine-Script):
  - Liquiditäts-Level: Previous Day High/Low + High/Low der Liquiditäts-Range
  - Sweep: Hoch/Tief durchstösst Level, Schlusskurs wieder dahinter
  - Entry: Schlusskurs bricht letztes Pivot-Tief/-Hoch (BOS), nur im Fenster
  - Stop hinter Sweep-Extrem (+Offset), TP = rr * R, Break-Even ab +1R
  - Max. 2 Trades/Tag, Tagesstopp -2 %, EOD flat 15:55 NY
  - Konservativ: Stop und TP in derselben Bar -> als Verlust gewertet
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

PRESETS = {
    # (killzone_start, killzone_end, range_start, range_end) in NY-Zeit
    "london": (dtime(2, 0), dtime(5, 0), dtime(18, 0), dtime(2, 0)),
    "ny-am":  (dtime(9, 30), dtime(11, 0), dtime(18, 0), dtime(9, 30)),
    "ny-pm":  (dtime(13, 30), dtime(15, 30), dtime(9, 30), dtime(13, 30)),
}


def in_session(t: dtime, start: dtime, end: dtime) -> bool:
    if start < end:
        return start <= t < end
    return t >= start or t < end  # Session über Mitternacht


@dataclass
class Bar:
    ts: datetime  # NY-Zeit
    o: float
    h: float
    l: float
    c: float


@dataclass
class Trade:
    entry_ts: datetime
    direction: str
    entry: float
    stop: float
    target: float
    risk: float
    exit_ts: datetime | None = None
    exit_price: float | None = None
    r_multiple: float | None = None
    reason: str = ""


@dataclass
class Params:
    preset: str = "london"
    piv_len: int = 3
    arm_bars: int = 12
    rr: float = 2.0
    tick: float = 0.25
    sl_off_ticks: int = 4
    use_be: bool = True
    be_trigger: float = 1.0
    use_trend: bool = True
    trend_bars: int = 600      # ~ EMA50 auf 1h bei 5-Min-Bars -> EMA(600) auf M5
    max_trades_day: int = 2
    risk_pct: float = 0.5
    daily_stop_pct: float = 2.0
    max_dd_pct: float = 6.0
    cost_r: float = 0.04
    eod: dtime = dtime(15, 55)


def load_bars(path: str) -> list[Bar]:
    bars: list[Bar] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in reader.fieldnames or []}
        need = ["time", "open", "high", "low", "close"]
        missing = [c for c in need if c not in cols]
        if missing:
            sys.exit(f"CSV-Spalten fehlen: {missing} (gefunden: {list(cols)})")
        for row in reader:
            raw = row[cols["time"]].strip()
            try:
                ts = datetime.fromtimestamp(int(raw), tz=timezone.utc)
            except ValueError:
                ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            bars.append(Bar(ts.astimezone(NY),
                            float(row[cols["open"]]), float(row[cols["high"]]),
                            float(row[cols["low"]]), float(row[cols["close"]])))
    bars.sort(key=lambda b: b.ts)
    return bars


def ema_series(closes: list[float], length: int) -> list[float]:
    out, alpha, e = [], 2 / (length + 1), None
    for c in closes:
        e = c if e is None else alpha * c + (1 - alpha) * e
        out.append(e)
    return out


def backtest(bars: list[Bar], p: Params) -> tuple[list[Trade], dict]:
    kz_s, kz_e, rg_s, rg_e = PRESETS[p.preset]
    closes = [b.c for b in bars]
    ema = ema_series(closes, p.trend_bars)

    # Previous Day High/Low je NY-Kalenderdatum
    day_hl: dict = {}
    for b in bars:
        d = b.ts.date()
        hi, lo = day_hl.get(d, (-math.inf, math.inf))
        day_hl[d] = (max(hi, b.h), min(lo, b.l))
    days_sorted = sorted(day_hl)
    prev_day = {d: days_sorted[i - 1] if i > 0 else None
                for i, d in enumerate(days_sorted)}

    trades: list[Trade] = []
    open_trade: Trade | None = None
    be_active = False

    rg_hi = rg_lo = None
    last_piv_hi = last_piv_lo = None
    armed_s = armed_l = False
    arm_s_i = arm_l_i = -1
    sweep_hi = sweep_lo = None

    cur_day = None
    trades_today = 0
    day_pnl_pct = 0.0
    equity_pct = 0.0
    peak_pct = 0.0
    max_dd = 0.0
    day_pnls: dict = {}
    halted_total = False

    def close_trade(t: Trade, b: Bar, price: float, reason: str):
        nonlocal day_pnl_pct, equity_pct, peak_pct, max_dd
        sign = 1 if t.direction == "long" else -1
        r = sign * (price - t.entry) / t.risk - p.cost_r
        t.exit_ts, t.exit_price, t.r_multiple, t.reason = b.ts, price, r, reason
        pnl = r * p.risk_pct
        day_pnl_pct += pnl
        equity_pct += pnl
        peak_pct = max(peak_pct, equity_pct)
        max_dd = max(max_dd, peak_pct - equity_pct)
        day_pnls[b.ts.date()] = day_pnls.get(b.ts.date(), 0.0) + pnl

    for i, b in enumerate(bars):
        t = b.ts.time()
        d = b.ts.date()
        if d != cur_day:
            cur_day, trades_today, day_pnl_pct = d, 0, 0.0

        in_kz = in_session(t, kz_s, kz_e)
        in_rg = in_session(t, rg_s, rg_e)
        prev_in_rg = i > 0 and in_session(bars[i - 1].ts.time(), rg_s, rg_e)

        # Liquiditäts-Range
        if in_rg and not prev_in_rg:
            rg_hi, rg_lo = b.h, b.l
        elif in_rg and rg_hi is not None:
            rg_hi, rg_lo = max(rg_hi, b.h), min(rg_lo, b.l)

        # Pivots (bestätigt nach piv_len Bars)
        j = i - p.piv_len
        if j >= p.piv_len:
            win = bars[j - p.piv_len:j + p.piv_len + 1]
            if bars[j].h == max(w.h for w in win):
                last_piv_hi = bars[j].h
            if bars[j].l == min(w.l for w in win):
                last_piv_lo = bars[j].l

        pd = prev_day.get(d)
        pdh, pdl = day_hl[pd] if pd else (None, None)

        # ── Offene Position managen ────────────────────────────────────────
        if open_trade is not None:
            ot = open_trade
            stop = ot.entry if be_active else ot.stop
            if ot.direction == "long":
                if b.l <= stop:
                    close_trade(ot, b, stop, "be" if be_active else "stop")
                    open_trade = None
                elif b.h >= ot.target:
                    close_trade(ot, b, ot.target, "target")
                    open_trade = None
                elif p.use_be and b.h >= ot.entry + p.be_trigger * ot.risk:
                    be_active = True
            else:
                if b.h >= stop:
                    close_trade(ot, b, stop, "be" if be_active else "stop")
                    open_trade = None
                elif b.l <= ot.target:
                    close_trade(ot, b, ot.target, "target")
                    open_trade = None
                elif p.use_be and b.l <= ot.entry - p.be_trigger * ot.risk:
                    be_active = True
            if open_trade is not None and t >= p.eod:
                close_trade(open_trade, b, b.c, "eod")
                open_trade = None

        # ── Risiko-Limits ──────────────────────────────────────────────────
        if max_dd >= p.max_dd_pct:
            halted_total = True
        day_halted = day_pnl_pct <= -p.daily_stop_pct
        can_trade = (in_kz and not halted_total and not day_halted
                     and trades_today < p.max_trades_day and open_trade is None
                     and t < p.eod)

        # ── Sweeps ─────────────────────────────────────────────────────────
        sw_hi = can_trade and (
            (pdh is not None and b.h > pdh and b.c < pdh) or
            (rg_hi is not None and not in_rg and b.h > rg_hi and b.c < rg_hi))
        sw_lo = can_trade and (
            (pdl is not None and b.l < pdl and b.c > pdl) or
            (rg_lo is not None and not in_rg and b.l < rg_lo and b.c > rg_lo))
        if sw_hi:
            armed_s, arm_s_i, sweep_hi = True, i, b.h
        if sw_lo:
            armed_l, arm_l_i, sweep_lo = True, i, b.l
        if armed_s:
            sweep_hi = max(sweep_hi, b.h)
            if i - arm_s_i > p.arm_bars or not in_kz:
                armed_s = False
        if armed_l:
            sweep_lo = min(sweep_lo, b.l)
            if i - arm_l_i > p.arm_bars or not in_kz:
                armed_l = False

        # ── Break of Structure -> Entry (zum Schlusskurs) ──────────────────
        trend_long = not p.use_trend or b.c > ema[i]
        trend_short = not p.use_trend or b.c < ema[i]
        if can_trade and armed_s and last_piv_lo is not None \
                and b.c < last_piv_lo and trend_short:
            sl = sweep_hi + p.sl_off_ticks * p.tick
            risk = sl - b.c
            if risk > 0:
                open_trade = Trade(b.ts, "short", b.c, sl, b.c - p.rr * risk, risk)
                trades.append(open_trade)
                be_active, armed_s = False, False
                trades_today += 1
        elif can_trade and armed_l and last_piv_hi is not None \
                and b.c > last_piv_hi and trend_long:
            sl = sweep_lo - p.sl_off_ticks * p.tick
            risk = b.c - sl
            if risk > 0:
                open_trade = Trade(b.ts, "long", b.c, sl, b.c + p.rr * risk, risk)
                trades.append(open_trade)
                be_active, armed_l = False, False
                trades_today += 1

    if open_trade is not None:
        close_trade(open_trade, bars[-1], bars[-1].c, "end_of_data")

    rs = [t.r_multiple for t in trades if t.r_multiple is not None]
    wins = [r for r in rs if r > 0.5]
    losses = [r for r in rs if r < -0.5]
    scratch = [r for r in rs if -0.5 <= r <= 0.5]
    gross_win = sum(r for r in rs if r > 0)
    gross_loss = -sum(r for r in rs if r < 0)
    stats = {
        "trades": len(rs),
        "win_rate_decided": len(wins) / max(1, len(wins) + len(losses)),
        "scratch_rate": len(scratch) / max(1, len(rs)),
        "total_r": sum(rs),
        "expectancy_r": sum(rs) / max(1, len(rs)),
        "profit_factor": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "total_pct": sum(rs) * p.risk_pct,
        "max_dd_pct": max_dd,
        "worst_day_pct": min(day_pnls.values()) if day_pnls else 0.0,
        "days_breach_2pct": sum(1 for v in day_pnls.values() if v <= -p.daily_stop_pct),
        "halted_by_max_dd": halted_total,
    }
    return trades, stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="TradingView-Chartdaten-Export (CSV)")
    ap.add_argument("--preset", choices=PRESETS, default="london")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--piv-len", type=int, default=3)
    ap.add_argument("--arm-bars", type=int, default=12)
    ap.add_argument("--tick", type=float, default=0.25)
    ap.add_argument("--risk-pct", type=float, default=0.5)
    ap.add_argument("--no-trend", action="store_true")
    ap.add_argument("--no-be", action="store_true")
    ap.add_argument("--out", default="trades_out.csv")
    a = ap.parse_args()

    p = Params(preset=a.preset, rr=a.rr, piv_len=a.piv_len, arm_bars=a.arm_bars,
               tick=a.tick, risk_pct=a.risk_pct,
               use_trend=not a.no_trend, use_be=not a.no_be)
    bars = load_bars(a.csv)
    if not bars:
        sys.exit("Keine Bars geladen.")
    print(f"{len(bars)} Bars: {bars[0].ts} -> {bars[-1].ts} | Preset: {p.preset}")

    trades, stats = backtest(bars, p)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["entry_ts", "direction", "entry", "stop", "target",
                    "exit_ts", "exit_price", "r_multiple", "reason"])
        for t in trades:
            w.writerow([t.entry_ts, t.direction, t.entry, t.stop, t.target,
                        t.exit_ts, t.exit_price,
                        f"{t.r_multiple:.3f}" if t.r_multiple is not None else "",
                        t.reason])
    print(f"Trades gespeichert: {a.out}")
    print("-" * 50)
    for k, v in stats.items():
        print(f"{k:>20}: {v:.3f}" if isinstance(v, float) else f"{k:>20}: {v}")
    print("-" * 50)
    print("Bewertung: Profit-Faktor > 1.3, Trefferquote (entschieden) >= 45 % bei "
          "2R,\nmax_dd_pct < 6 und trades > 100 anstreben. Danach:\n"
          f"  python3 prop_challenge_monte_carlo.py --csv {a.out}")


if __name__ == "__main__":
    main()
