"""Dual-Thrust-Plausibilitätschecks: N-Sensitivität, N=1 je Jahr, Auflösung (5m/15m/30m vs 1h),
erste RTH-Kerze nicht handelbar (wie in der Pine-Version)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import *

print("## N-Sensitivität (1h, 11/2023–09/2026), Summe% (PF), Kosten 0.01%/RT")
for s in ["NASDAQ_QQQ_1h", "AMEX_XLK_1h", "NASDAQ_SMH_1h", "AMEX_SPY_1h"]:
    df = load(s)
    for dirn in ["both", "short"]:
        row = []
        for n in [1, 2, 3]:
            for k in [0.4, 0.5, 0.6]:
                st = stats(run(df, s_dual_thrust, 60, n=n, k1=k, k2=k, direction=dirn, min_bars=5), 0.01)
                row.append(f"n{n}k{k}:{st['tot_pct']:+6.1f}({st['pf']:.2f})")
        print(f"{s:14s} {dirn:5s} " + " ".join(row))

print("\n## N=1 (nur Vortagesrange), Reversal, je Jahr; Kosten 0.01% und 0.03%/RT")
for s in ["NASDAQ_QQQ_1h", "AMEX_XLK_1h", "NASDAQ_SMH_1h", "AMEX_SPY_1h", "AMEX_DIA_1h", "AMEX_IWM_1h"]:
    df = load(s)
    for k in [0.4, 0.5]:
        tr = run(df, s_dual_thrust, 60, n=1, k1=k, k2=k, min_bars=5)
        a, c = stats(tr, 0.01), stats(tr, 0.03)
        per = " ".join(f"{y}:{stats([t for t in tr if t.day.year == y], 0.01)['tot_pct']:+5.1f}"
                       for y in sorted(set(t.day.year for t in tr)))
        print(f"{s:14s} k{k}: {a['tot_pct']:+6.1f}% PF {a['pf']:.2f} DD {a['maxdd_pct']:.1f}% n={a['n']} | "
              f"Kosten×3: {c['tot_pct']:+6.1f}% PF {c['pf']:.2f} | {per}")

print("\n## Auflösungs-Check: gleicher Zeitraum, verschiedene Kerzengrößen")
for sym in ["NASDAQ_QQQ", "AMEX_SPY"]:
    h = load(f"{sym}_1h")
    for tf in [5, 15, 30]:
        df = load(f"{sym}_{tf}m"); d0 = df.date.min()
        for n, k, dirn in [(1, 0.4, "both"), (1, 0.5, "both"), (2, 0.5, "both"), (2, 0.5, "short")]:
            sa = stats(run(df, s_dual_thrust, tf, n=n, k1=k, k2=k, direction=dirn), 0.01)
            sb = stats(run(h[h.date >= d0], s_dual_thrust, 60, n=n, k1=k, k2=k, direction=dirn, min_bars=5), 0.01)
            print(f"{sym:11s} {tf:>2}m vs 1h ab {d0} n{n}k{k} {dirn:5s}: {tf}m {sa['tot_pct']:+6.2f}% PF {sa['pf']:.2f} "
                  f"n={sa['n']:>3} | 1h {sb['tot_pct']:+6.2f}% PF {sb['pf']:.2f} n={sb['n']:>3}")

print("\n## Erste RTH-Kerze nicht handelbar (Pine-Verhalten), N2/K0.5")
for name, tf in [("NASDAQ_QQQ_5m", 5), ("AMEX_SPY_5m", 5), ("NASDAQ_QQQ_15m", 15), ("AMEX_SPY_15m", 15),
                 ("NASDAQ_QQQ_30m", 30), ("AMEX_SPY_30m", 30)]:
    df = load(name)
    for dirn in ["both", "short"]:
        a = stats(run(df, s_dual_thrust, tf, n=2, k1=.5, k2=.5, direction=dirn), 0.01)
        b = stats(run(df, s_dual_thrust, tf, n=2, k1=.5, k2=.5, direction=dirn, start_bar=1), 0.01)
        print(f"{name:15s} {dirn:5s}: ab Kerze 1 {a['tot_pct']:+6.2f}% PF {a['pf']:.2f} | "
              f"ab Kerze 2 {b['tot_pct']:+6.2f}% PF {b['pf']:.2f}")
