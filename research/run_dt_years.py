"""Dual Thrust out-of-sample: längere Historie (1h, ~3 Jahre) und weitere Märkte (IWM, DIA), je Jahr."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import *

COST = 0.01
PARAMS = [(2, 0.5), (2, 0.3), (4, 0.5)]
for name in sys.argv[1:] or ["AMEX_SPY_1h", "NASDAQ_QQQ_1h", "AMEX_IWM_1h", "AMEX_DIA_1h",
                             "AMEX_IWM_30m", "AMEX_DIA_30m"]:
    tf = int(name.split('_')[-1][:-1]) * (60 if name.endswith('h') else 1)
    df = load(name)
    print(f"\n### {name} ({df.date.min()} – {df.date.max()})")
    for n, k in PARAMS:
        tr = run(df, s_dual_thrust, tf, n=n, k1=k, k2=k, min_bars=10 if tf < 60 else 5)
        st = stats(tr, COST)
        yrs = sorted(set(t.day.year for t in tr))
        per = "  ".join(f"{y}: {stats([t for t in tr if t.day.year == y], COST)['tot_pct']:+6.2f}% "
                        f"(PF {stats([t for t in tr if t.day.year == y], COST)['pf']:.2f})" for y in yrs)
        print(f"n{n} k{k}: gesamt {st['tot_pct']:+7.2f}% PF {st['pf']:.2f} DD {st['maxdd_pct']:.2f}% n={st['n']} | {per}")
