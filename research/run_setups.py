import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import *
COST = {'SPY': 0.01, 'QQQ': 0.01}  # Round-Trip in % (≈ Spread + Slippage)
setups=[
 ("RET  IB-25%-Retrace (unser Setup 1)", s_retrace, {}),
 ("RET  + nur weite IB", s_retrace, dict(ibf="wide")),
 ("ORB  Mitte-Stop, 1R (unser Setup 2)", s_orb, {}),
 ("ORB  Mitte-Stop, 2R", s_orb, dict(tp_r=2.0)),
 ("ORB  Mitte-Stop, Halten bis EOD", s_orb, dict(tp_r=None)),
 ("ORB  EOD + nur enge IB", s_orb, dict(tp_r=None, ibf="narrow")),
 ("ORB  1R + nur enge IB", s_orb, dict(ibf="narrow")),
 ("ORB  EOD, ohne VWAP-Filter", s_orb, dict(tp_r=None, vwap_dir=False)),
 ("DT   Dual Thrust n4 k0.5 (je-suis-tm)", s_dual_thrust, {}),
 ("DT   Dual Thrust n4 k0.3", s_dual_thrust, dict(k1=0.3,k2=0.3)),
 ("FC   Erste-Kerze-ORB -> EOD (Benchmark)", s_first_candle_orb, {}),
]
for name in sys.argv[1:]:
    tf=int(name.split('_')[-1][:-1]); sym=name.split('_')[1]
    df=load(name); nd=df.date.nunique()
    print(f"\n### {name}  ({nd} Tage, {df.date.min()} – {df.date.max()}, Kosten {COST[sym]}%/RT)")
    print(f"{'Setup':42s} {'n':>4} {'Win%':>5} {'PF':>5} {'Ø bp':>6} {'Summe%':>7} {'MaxDD%':>6} {'H1%':>6} {'H2%':>6}")
    for lbl,fn,kw in setups:
        st=stats(run(df,fn,tf,**kw),COST[sym])
        if st['n']==0: print(f"{lbl:42s}    0"); continue
        print(f"{lbl:42s} {st['n']:>4} {st['win']:>5} {st['pf']:>5} {st['avg_bp']:>6} {st['tot_pct']:>7} {st['maxdd_pct']:>6} {st['h1']:>6} {st['h2']:>6}")
