"""Dual-Thrust-Robustheit: Parameter-Grid, Timeframe-/Kosten-Check, Monatsverteilung."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import *

print("## Parameter-Grid (30m) – Summe % (PF), Kosten 0.01 %/RT")
for name in ["AMEX_SPY_30m", "NASDAQ_QQQ_30m"]:
    df = load(name); ks = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    print(f"\n{name}\nn\\k " + "".join(f"{k:>14}" for k in ks))
    for n in [2, 3, 4, 5, 6]:
        row = ""
        for k in ks:
            st = stats(run(df, s_dual_thrust, 30, n=n, k1=k, k2=k), 0.01)
            row += f"{st['tot_pct']:>8} ({st['pf']:.2f})"
        print(f"{n:<4}" + row)

print("\n## Timeframe- und Kosten-Check")
for name in ["AMEX_SPY_5m", "NASDAQ_QQQ_5m", "AMEX_SPY_15m", "NASDAQ_QQQ_15m", "AMEX_SPY_30m", "NASDAQ_QQQ_30m"]:
    tf = int(name.split('_')[-1][:-1]); df = load(name)
    for n, k in [(2, 0.2), (2, 0.3), (2, 0.5), (4, 0.5)]:
        tr = run(df, s_dual_thrust, tf, n=n, k1=k, k2=k)
        a, b = stats(tr, 0.01), stats(tr, 0.02)
        print(f"{name:16s} n{n} k{k}: n={a['n']:>4} win={a['win']:>5} PF={a['pf']:>5} "
              f"Σ={a['tot_pct']:>7}% DD={a['maxdd_pct']:>6}% H1={a['h1']:>6} H2={a['h2']:>6} "
              f"| Kosten×2: Σ={b['tot_pct']:>7}% PF={b['pf']}")

print("\n## Monatsverteilung n2 k0.5 (30m) und Ergebnis ohne Mär–Mai 2025")
for name in ["AMEX_SPY_30m", "NASDAQ_QQQ_30m"]:
    tr = run(load(name), s_dual_thrust, 30, n=2, k1=0.5, k2=0.5)
    m = collections.OrderedDict()
    for t in tr:
        key = str(t.day)[:7]
        m[key] = m.get(key, 0) + t.side * (t.exit - t.entry) / t.entry * 100 - 0.01
    ex = [t for t in tr if not ('2025-03' <= str(t.day)[:7] <= '2025-05')]
    print(f"{name}: ohne Mär–Mai 2025 -> {stats(ex, 0.01)}")
    print("   " + " ".join(f"{k[2:]}:{v:+.1f}" for k, v in m.items()))
