#!/usr/bin/env python3
"""
Lokaler M1-Backtest für die Strategie "ORB Spike-Reversal + RSI (NQ/ES)".

1:1-Port der Pine-v6-Logik aus ORB_Spike_Reversal_RSI_Strategy.pine,
inklusive der Order-Semantik des TradingView-Broker-Emulators
(calc_on_every_tick=false):
  - Stop-Entry-Orders werden zum Bar-Close platziert und frühestens auf
    der NÄCHSTEN Bar gefüllt (Gap → Fill zum Open).
  - Exit-Orders (SL/TP) sind erst ab der Bar NACH dem Entry-Fill aktiv.
  - Werden SL und TP in derselben Bar berührt, zählt konservativ der SL.

Datenquellen:
  --synth [TAGE]   Realistische synthetische NQ-1m-Daten (Logik-Validierung,
                   KEINE echte Performance-Aussage!)
  --csv PFAD       Echte 1m-Daten, z. B. TradingView-Chart-Export
                   (Spalten: time, open, high, low, close [, volume])

Beispiele:
  python3 backtest/orb_spike_reversal_backtest.py --synth 60 --symbol NQ
  python3 backtest/orb_spike_reversal_backtest.py --csv nq_1m.csv --symbol NQ
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import time as dtime

import numpy as np
import pandas as pd

NY_TZ = "America/New_York"

SYMBOLS = {
    "NQ": {"tick": 0.25, "point_value": 20.0},
    "MNQ": {"tick": 0.25, "point_value": 2.0},
    "ES": {"tick": 0.25, "point_value": 50.0},
    "MES": {"tick": 0.25, "point_value": 5.0},
}


# ─── Strategie-Parameter (Defaults = Pine-Inputs) ────────────────────────────
@dataclass
class Params:
    orb_start: dtime = dtime(9, 30)
    orb_end: dtime = dtime(10, 0)      # exklusiv
    trd_start: dtime = dtime(10, 0)
    trd_end: dtime = dtime(15, 0)      # exklusiv
    eod_start: dtime = dtime(15, 55)
    rsi_len: int = 14
    rsi_os: float = 30.0
    rsi_ob: float = 70.0
    atr_len: int = 14
    spike_atr: float = 0.5
    speed_bars: int = 5
    str_left: int = 3
    str_right: int = 2
    bos_off_ticks: int = 2
    max_setup_bars: int = 40
    tp_mode: str = "spike-ursprung"    # spike-ursprung | orb-mitte | gegenseite | r-multiple
    tp_r: float = 1.5
    sl_off_ticks: int = 2
    min_rr: float = 0.5
    max_trades: int = 2
    commission_per_fill: float = 1.25  # $ je Kontrakt und Fill


@dataclass
class Trade:
    direction: str
    entry_time: object
    entry: float
    sl: float
    tp: float
    exit_time: object = None
    exit: float = None
    reason: str = ""
    points: float = 0.0


# ─── Indikatoren (Wilder / RMA wie ta.rsi & ta.atr) ─────────────────────────
def rma(series: np.ndarray, length: int) -> np.ndarray:
    out = np.full(len(series), np.nan)
    alpha = 1.0 / length
    acc = np.nan
    n = 0
    for i, v in enumerate(series):
        if np.isnan(v):
            out[i] = acc
            continue
        n += 1
        if n < length:
            acc = v if np.isnan(acc) else acc + v
        elif n == length:
            acc = (acc + v) / length
            out[i] = acc
        else:
            acc = acc + alpha * (v - acc)
            out[i] = acc
    return out


def wilder_rsi(close: np.ndarray, length: int) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    up = np.where(delta > 0, delta, 0.0)
    dn = np.where(delta < 0, -delta, 0.0)
    up[0] = np.nan
    dn[0] = np.nan
    avg_up = rma(up, length)
    avg_dn = rma(dn, length)
    rs = avg_up / np.where(avg_dn == 0, np.nan, avg_dn)
    rsi = 100 - 100 / (1 + rs)
    rsi = np.where(np.isnan(rsi) & (avg_dn == 0) & ~np.isnan(avg_up), 100.0, rsi)
    return rsi


def wilder_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, length: int) -> np.ndarray:
    prev_c = np.roll(c, 1)
    prev_c[0] = np.nan
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]
    return rma(tr, length)


# ─── Backtest-Engine ─────────────────────────────────────────────────────────
def run_backtest(df: pd.DataFrame, p: Params, sym: dict, verbose: bool = False):
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    times = df.index

    rsi = wilder_rsi(c, p.rsi_len)
    atr = wilder_atr(h, l, c, p.atr_len)
    hi_n = pd.Series(h).rolling(p.speed_bars, min_periods=1).max().to_numpy()
    lo_n = pd.Series(l).rolling(p.speed_bars, min_periods=1).min().to_numpy()

    bos_off = p.bos_off_ticks * sym["tick"]
    sl_off = p.sl_off_ticks * sym["tick"]

    trades: list[Trade] = []

    # Tages-/Setup-Status
    day = None
    orb_hi = orb_lo = np.nan
    orb_done = False
    day_trades = 0
    setup_dir = 0
    spike_ext = spike_origin = np.nan
    spike_ext_bar = -1
    setup_bar = -1
    bos_lvl = np.nan

    # Orders / Position
    pending = None          # dict(dir, stop, sl, tp, placed_bar)
    pos = None              # Trade
    exits_active_from = -1
    eod_close_pending = False

    def in_win(t, a, b):
        return a <= t < b

    for i in range(len(df)):
        ts = times[i]
        t = ts.time()
        d = ts.date()

        # ── Neuer Tag ────────────────────────────────────────────────────
        if d != day:
            day = d
            orb_hi = orb_lo = np.nan
            orb_done = False
            day_trades = 0
            setup_dir = 0
            bos_lvl = np.nan
            pending = None
            eod_close_pending = False
            if pos is not None:  # Sicherheitsnetz (sollte durch EOD nie passieren)
                pos.exit_time, pos.exit, pos.reason = times[i - 1], c[i - 1], "SESSION-END"
                trades.append(pos)
                pos = None

        just_entered = False

        # ── 1) Intrabar: EOD-Marktorder, Exits, Entry-Fills ──────────────
        if pos is not None and eod_close_pending:
            pos.exit_time, pos.exit, pos.reason = ts, o[i], "EOD"
            trades.append(pos)
            pos = None
            eod_close_pending = False
        if pos is not None and i > exits_active_from:
            e = None
            if pos.direction == "long":
                if o[i] <= pos.sl:
                    e = (o[i], "SL")
                elif o[i] >= pos.tp:
                    e = (o[i], "TP")
                elif l[i] <= pos.sl:
                    e = (pos.sl, "SL")
                elif h[i] >= pos.tp:
                    e = (pos.tp, "TP")
            else:
                if o[i] >= pos.sl:
                    e = (o[i], "SL")
                elif o[i] <= pos.tp:
                    e = (o[i], "TP")
                elif h[i] >= pos.sl:
                    e = (pos.sl, "SL")
                elif l[i] <= pos.tp:
                    e = (pos.tp, "TP")
            if e:
                pos.exit_time, (pos.exit, pos.reason) = ts, e
                trades.append(pos)
                pos = None
        if pos is None and pending is not None and i > pending["placed_bar"]:
            fill = None
            if pending["dir"] == "long":
                if o[i] >= pending["stop"]:
                    fill = o[i]
                elif h[i] >= pending["stop"]:
                    fill = pending["stop"]
            else:
                if o[i] <= pending["stop"]:
                    fill = o[i]
                elif l[i] <= pending["stop"]:
                    fill = pending["stop"]
            if fill is not None:
                tp = pending["tp"]
                if p.tp_mode == "r-multiple":
                    risk = abs(fill - pending["sl"])
                    tp = fill + p.tp_r * risk if pending["dir"] == "long" else fill - p.tp_r * risk
                pos = Trade(pending["dir"], ts, fill, pending["sl"], tp)
                exits_active_from = i
                pending = None
                just_entered = True

        # ── 2) Bar-Close-Logik ───────────────────────────────────────────
        # ORB aufbauen
        if in_win(t, p.orb_start, p.orb_end):
            if np.isnan(orb_hi):
                orb_hi, orb_lo = h[i], l[i]
            else:
                orb_hi, orb_lo = max(orb_hi, h[i]), min(orb_lo, l[i])
        elif not np.isnan(orb_hi) and t >= p.orb_end:
            orb_done = True

        if just_entered:
            day_trades += 1
            setup_dir = 0
            bos_lvl = np.nan

        in_trd = in_win(t, p.trd_start, p.trd_end)
        in_eod = t >= p.eod_start

        # Setup-Abbruch
        if setup_dir != 0 and pos is None:
            missed = (setup_dir == 1 and c[i] > spike_origin) or (
                setup_dir == -1 and c[i] < spike_origin)
            timeout = i - setup_bar > p.max_setup_bars
            if missed or timeout or in_eod or not in_trd:
                setup_dir = 0
                bos_lvl = np.nan
                pending = None

        # Fast Spike erkennen
        rng = orb_hi - orb_lo
        can_setup = (orb_done and in_trd and not in_eod and pos is None
                     and setup_dir == 0 and day_trades < p.max_trades
                     and not np.isnan(rng) and rng > 0 and not np.isnan(atr[i])
                     and not np.isnan(rsi[i]))
        if can_setup:
            spike_dn = l[i] < orb_lo - p.spike_atr * atr[i] and hi_n[i] > orb_lo and rsi[i] <= p.rsi_os
            spike_up = h[i] > orb_hi + p.spike_atr * atr[i] and lo_n[i] < orb_hi and rsi[i] >= p.rsi_ob
            if spike_dn or spike_up:
                setup_dir = 1 if spike_dn else -1
                spike_ext = l[i] if spike_dn else h[i]
                spike_ext_bar = i
                spike_origin = hi_n[i] if spike_dn else lo_n[i]
                setup_bar = i
                bos_lvl = np.nan
                if verbose:
                    print(f"  {ts}  Spike {'DOWN→Long-Setup' if spike_dn else 'UP→Short-Setup'} "
                          f"RSI={rsi[i]:.1f} Extrem={spike_ext:.2f} Ursprung={spike_origin:.2f}")

        # Setup pflegen: Extrem nachziehen, BOS-Pivot suchen
        if setup_dir != 0 and pos is None:
            if setup_dir == 1 and l[i] < spike_ext:
                spike_ext, spike_ext_bar = l[i], i
            if setup_dir == -1 and h[i] > spike_ext:
                spike_ext, spike_ext_bar = h[i], i
            j = i - p.str_right           # Pivot-Kandidat (bestätigt auf Bar i)
            if j - p.str_left >= 0:
                if setup_dir == 1:
                    w = h[j - p.str_left:j + p.str_right + 1]
                    if h[j] == w.max() and (w == w.max()).sum() == 1 and j > spike_ext_bar and h[j] < spike_origin:
                        bos_lvl = h[j]
                else:
                    w = l[j - p.str_left:j + p.str_right + 1]
                    if l[j] == w.min() and (w == w.min()).sum() == 1 and j > spike_ext_bar and l[j] > spike_origin:
                        bos_lvl = l[j]

        # Entry-Order am BOS armieren / aktualisieren
        if setup_dir != 0 and pos is None and not np.isnan(bos_lvl):
            if setup_dir == 1:
                entry, sl = bos_lvl + bos_off, spike_ext - sl_off
                tp = {"spike-ursprung": spike_origin, "orb-mitte": (orb_hi + orb_lo) / 2,
                      "gegenseite": orb_hi}.get(p.tp_mode, np.nan)
                risk = entry - sl
                reward = p.tp_r * risk if p.tp_mode == "r-multiple" else tp - entry
            else:
                entry, sl = bos_lvl - bos_off, spike_ext + sl_off
                tp = {"spike-ursprung": spike_origin, "orb-mitte": (orb_hi + orb_lo) / 2,
                      "gegenseite": orb_lo}.get(p.tp_mode, np.nan)
                risk = sl - entry
                reward = p.tp_r * risk if p.tp_mode == "r-multiple" else entry - tp
            if risk > 0 and reward > 0 and (p.min_rr == 0 or reward >= p.min_rr * risk):
                pending = {"dir": "long" if setup_dir == 1 else "short",
                           "stop": entry, "sl": sl, "tp": tp, "placed_bar": i}
            else:
                pending = None
        elif setup_dir == 0 and not just_entered:
            pass  # pending bleibt nur bestehen, solange das Setup lebt

        # EOD: Orders streichen, Position glattstellen
        if in_eod:
            pending = None
            if pos is not None:
                if i + 1 < len(df) and times[i + 1].date() == d:
                    eod_close_pending = True
                else:
                    pos.exit_time, pos.exit, pos.reason = ts, c[i], "EOD"
                    trades.append(pos)
                    pos = None

    if pos is not None:
        pos.exit_time, pos.exit, pos.reason = times[-1], c[-1], "OPEN-END"
        trades.append(pos)

    for tr in trades:
        tr.points = (tr.exit - tr.entry) if tr.direction == "long" else (tr.entry - tr.exit)
    return trades


# ─── Auswertung ──────────────────────────────────────────────────────────────
def report(trades: list, sym: dict, p: Params, label: str):
    pv = sym["point_value"]
    comm = 2 * p.commission_per_fill
    print(f"\n{'═' * 74}\n  Backtest-Ergebnis: {label}\n{'═' * 74}")
    if not trades:
        print("  Keine Trades ausgelöst.")
        return
    pnl = np.array([t.points * pv - comm for t in trades])
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    equity = np.cumsum(pnl)
    dd = (np.maximum.accumulate(equity) - equity).max()
    gross_p, gross_l = wins.sum(), -losses.sum()
    print(f"  Trades gesamt:        {len(trades)}   "
          f"(Long: {sum(1 for t in trades if t.direction == 'long')}, "
          f"Short: {sum(1 for t in trades if t.direction == 'short')})")
    print(f"  Trefferquote:         {len(wins) / len(pnl) * 100:.1f} %  ({len(wins)} W / {len(losses)} L)")
    print(f"  Netto-P&L:            {pnl.sum():+,.2f} $   ({sum(t.points for t in trades):+,.2f} Punkte)")
    print(f"  Profit-Faktor:        {gross_p / gross_l if gross_l > 0 else float('inf'):.2f}")
    print(f"  Ø Gewinn / Ø Verlust: {wins.mean() if len(wins) else 0:+,.2f} $ / "
          f"{losses.mean() if len(losses) else 0:+,.2f} $")
    print(f"  Max. Drawdown:        {dd:,.2f} $")
    print(f"  Exits:                " + ", ".join(
        f"{r}: {sum(1 for t in trades if t.reason == r)}"
        for r in sorted({t.reason for t in trades})))
    print(f"\n  {'Zeit (Entry)':<22}{'Dir':<7}{'Entry':>10}{'SL':>10}{'TP':>10}"
          f"{'Exit':>10}{'Grund':>7}{'P&L $':>12}")
    for t in trades[:40]:
        print(f"  {str(t.entry_time)[:19]:<22}{t.direction:<7}{t.entry:>10.2f}{t.sl:>10.2f}"
              f"{t.tp:>10.2f}{t.exit:>10.2f}{t.reason:>7}{t.points * pv - comm:>12.2f}")
    if len(trades) > 40:
        print(f"  … und {len(trades) - 40} weitere Trades")


# ─── Synthetische NQ-1m-Daten (nur zur Logik-Validierung) ───────────────────
def gen_synth(days: int = 60, seed: int = 42, start_price: float = 20000.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    price = start_price
    bdays = pd.bdate_range("2026-04-01", periods=days, tz=NY_TZ)
    for day in bdays:
        sigma = rng.uniform(2.5, 6.0)          # Basis-Volatilität (Punkte/Min)
        drift = rng.normal(0, 0.4)
        n = 390                                 # 09:30–16:00
        t0 = day + pd.Timedelta(hours=9, minutes=30)
        # Spike-Events nach der ORB einplanen
        events = {}
        for _ in range(rng.integers(1, 4)):
            at = int(rng.integers(40, 320))     # Bar-Index im Tag (ab 10:10)
            length = int(rng.integers(2, 6))
            direction = -1 if rng.random() < 0.5 else 1
            mag = rng.uniform(2.0, 4.5) * sigma
            revert = rng.random() < 0.65
            events[at] = (direction, length, mag, revert)
        rev_drift, rev_left = 0.0, 0
        spike = None
        for b in range(n):
            ts = t0 + pd.Timedelta(minutes=b)
            vol = sigma * (1.6 if b < 30 else 1.0)
            m = drift + rng.normal(0, vol)
            if b in events:
                d_, ln, mag, rv = events[b]
                spike = [d_, ln, mag / ln, rv]
            if spike:
                m += spike[0] * spike[2] * rng.uniform(0.8, 1.3)
                spike[1] -= 1
                if spike[1] <= 0:
                    if spike[3]:
                        rev_left = int(rng.integers(10, 35))
                        rev_drift = -spike[0] * spike[2] * 0.55
                    spike = None
            if rev_left > 0:
                m += rev_drift * rng.uniform(0.5, 1.2)
                rev_left -= 1
            op = price
            cl = op + m
            wick = abs(rng.normal(0, vol * 0.5))
            hi = max(op, cl) + wick
            lo = min(op, cl) - wick
            rows.append((ts, round(op * 4) / 4, round(hi * 4) / 4,
                         round(lo * 4) / 4, round(cl * 4) / 4,
                         int(rng.integers(500, 5000))))
            price = cl
        price += rng.normal(0, 15)              # Overnight-Gap
    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    return df.set_index("time")


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    tcol = next((c for c in df.columns if c in ("time", "datetime", "date", "timestamp")), df.columns[0])
    if np.issubdtype(df[tcol].dtype, np.number):
        df[tcol] = pd.to_datetime(df[tcol], unit="s", utc=True)
    else:
        df[tcol] = pd.to_datetime(df[tcol], utc=True)
    df = df.set_index(tcol).tz_convert(NY_TZ).sort_index()
    need = ["open", "high", "low", "close"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        sys.exit(f"CSV: fehlende Spalten {missing} (gefunden: {list(df.columns)})")
    return df[need + (["volume"] if "volume" in df.columns else [])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--synth", type=int, nargs="?", const=60, metavar="TAGE",
                     help="synthetische NQ-1m-Daten (Default: 60 Handelstage)")
    src.add_argument("--csv", metavar="PFAD", help="1m-CSV (TradingView-Export)")
    ap.add_argument("--symbol", default="NQ", choices=SYMBOLS.keys())
    ap.add_argument("--tp-mode", default="spike-ursprung",
                    choices=["spike-ursprung", "orb-mitte", "gegenseite", "r-multiple"])
    ap.add_argument("--rsi-os", type=float, default=30.0)
    ap.add_argument("--rsi-ob", type=float, default=70.0)
    ap.add_argument("--spike-atr", type=float, default=0.5)
    ap.add_argument("--min-rr", type=float, default=0.5)
    ap.add_argument("--max-trades", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--verbose", action="store_true", help="Spike-Setups mitloggen")
    ap.add_argument("--trades-csv", metavar="PFAD", help="Trades als CSV speichern")
    args = ap.parse_args()

    p = Params(tp_mode=args.tp_mode, rsi_os=args.rsi_os, rsi_ob=args.rsi_ob,
               spike_atr=args.spike_atr, min_rr=args.min_rr, max_trades=args.max_trades)
    sym = SYMBOLS[args.symbol]

    if args.csv:
        df = load_csv(args.csv)
        label = f"{args.symbol} 1m · {args.csv} ({df.index[0].date()} – {df.index[-1].date()})"
    else:
        df = gen_synth(days=args.synth, seed=args.seed)
        label = (f"{args.symbol} 1m · SYNTHETISCHE Daten, {args.synth} Handelstage "
                 f"(nur Logik-Validierung!)")

    print(f"Bars: {len(df)}  |  Zeitraum: {df.index[0]} – {df.index[-1]}")
    trades = run_backtest(df, p, sym, verbose=args.verbose)
    report(trades, sym, p, label)

    if args.trades_csv and trades:
        pd.DataFrame([vars(t) for t in trades]).to_csv(args.trades_csv, index=False)
        print(f"\nTrades gespeichert: {args.trades_csv}")


if __name__ == "__main__":
    main()
