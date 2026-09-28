"""Dual Thrust: Long/Short-Zerlegung und reine Short-Variante je Jahr (1h, ~3 Jahre)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import *

COST = 0.01
for name in sys.argv[1:] or ["NASDAQ_QQQ_1h", "AMEX_XLK_1h", "NASDAQ_SMH_1h", "AMEX_SPY_1h",
                             "AMEX_DIA_1h", "AMEX_IWM_1h"]:
    df = load(name)
    both = run(df, s_dual_thrust, 60, n=2, k1=0.5, k2=0.5, min_bars=5)
    L = [t for t in both if t.side > 0]; S = [t for t in both if t.side < 0]
    bh = (df.c.iloc[-1] / df.o.iloc[0] - 1) * 100
    print(f"\n### {name}  Buy&Hold {bh:+.1f}%")
    print(f"Reversal N2/K0.5 zerlegt: Long {stats(L, COST)['tot_pct']:+.2f}% (PF {stats(L, COST)['pf']:.2f}) | "
          f"Short {stats(S, COST)['tot_pct']:+.2f}% (PF {stats(S, COST)['pf']:.2f})")
    for n, k in [(2, 0.3), (2, 0.5), (2, 0.7), (3, 0.5)]:
        tr = run(df, s_dual_thrust, 60, n=n, k1=k, k2=k, direction="short", min_bars=5)
        st = stats(tr, COST)
        yrs = sorted(set(t.day.year for t in tr))
        per = "  ".join(f"{y}: {stats([t for t in tr if t.day.year == y], COST)['tot_pct']:+6.2f}% "
                        f"(PF {stats([t for t in tr if t.day.year == y], COST)['pf']:.2f})" for y in yrs)
        print(f"Nur Short n{n} k{k}: {st['tot_pct']:+7.2f}% PF {st['pf']:.2f} DD {st['maxdd_pct']:.2f}% "
              f"n={st['n']} win={st['win']}% | {per}")
