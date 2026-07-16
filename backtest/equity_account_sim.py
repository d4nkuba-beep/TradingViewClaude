#!/usr/bin/env python3
"""Eigenkapital-Konto-Simulation (statt Prop-Challenge): Risk of Ruin & Co.

Simuliert ein kleines Konto (z. B. 300 $) auf Hyperliquid-Gold mit
multiplikativem Zinseszins, inkl. zweier Venue-Realitaeten:

1. GEBUEHREN skalieren mit dem Notional, das Risiko mit der Stop-Distanz.
   Kosten in R = 2 * fee_rate * Preis / Stop-Distanz. Bei engen 5m-Stops
   frisst das den Edge (Tabelle unten).
2. TAIL-RISIKO: dokumentierter Flash-Crash (-100 $ in <1 Min). Mit
   Wahrscheinlichkeit `tail_prob` rutscht ein Verlierer per Gap auf
   `tail_r` R durch den Stop.

Nutzung:  python3 equity_account_sim.py
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from prop_challenge_monte_carlo import StrategySpec


@dataclass
class AccountSpec:
    start: float = 300.0
    n_trades: int = 250          # ~ 1 Jahr bei 1 Trade/Tag
    ruin_frac: float = 0.5       # "Ruin" = Konto halbiert
    dead_frac: float = 0.3       # praktisch tot
    tail_prob: float = 0.005     # Flash-Gap durch den Stop
    tail_r: float = -3.0


def draw_r(s: StrategySpec, a: AccountSpec, rng: random.Random) -> float:
    if rng.random() < a.tail_prob:
        return a.tail_r - s.cost_r
    u = rng.random()
    if u < s.be_rate:
        return 0.0 - s.cost_r
    if rng.random() < s.win_rate:
        return s.rr - s.cost_r
    return -1.0 - s.cost_r


def simulate(s: StrategySpec, a: AccountSpec, n_sims: int = 20000,
             seed: int = 42) -> dict:
    rng = random.Random(seed)
    ruined = dead = doubled = 0
    finals, max_dds = [], []
    for _ in range(n_sims):
        eq, peak, mdd = 1.0, 1.0, 0.0
        hit_ruin = hit_dead = hit_double = False
        for _ in range(a.n_trades):
            eq *= 1.0 + draw_r(s, a, rng) * s.risk_pct / 100.0
            peak = max(peak, eq)
            mdd = max(mdd, 1.0 - eq / peak)
            hit_double = hit_double or eq >= 2.0
            if eq <= a.ruin_frac:
                hit_ruin = True
            if eq <= a.dead_frac:
                hit_dead = True
                break
        ruined += hit_ruin
        dead += hit_dead
        doubled += hit_double
        finals.append(eq)
        max_dds.append(mdd)
    return {
        "ruin": ruined / n_sims, "dead": dead / n_sims,
        "double": doubled / n_sims,
        "median_final": statistics.median(finals),
        "median_max_dd": statistics.median(max_dds),
    }


def fee_table(price: float = 4200.0) -> None:
    print(f"\nKosten in R auf Hyperliquid-Gold (Preis ~{price:.0f} $), "
          "Round-Trip = 2 Fills:")
    print(f"{'Stop ($)':>9} | {'Taker 0.045%':>12} | {'Maker 0.015%':>12}")
    for stop in (5, 10, 20, 40, 80):
        taker = 2 * 0.00045 * price / stop
        maker = 2 * 0.00015 * price / stop
        print(f"{stop:>9} | {taker:>11.2f}R | {maker:>11.2f}R")
    print("=> Enge 5m-Stops (5-10 $) sind mit Taker-Fills strukturell tot;"
          "\n   handelbar wird es ab ~20-40 $ Stops (H1-Strukturen) mit Makern.")


def main() -> None:
    a = AccountSpec()
    print(f"Konto {a.start:.0f} $, {a.n_trades} Trades, Flash-Gap-Risiko "
          f"{a.tail_prob:.1%}/Trade auf {a.tail_r}R")
    print(f"\n{'Profil':>14} {'Risk%':>5} {'Kosten':>6} | {'P(-50%)':>8} "
          f"{'P(-70%)':>8} {'P(x2)':>6} {'MedEnd':>7} {'MedMaxDD':>8}")
    print("-" * 76)
    profiles = [
        ("Sweep 45%/2R", StrategySpec(win_rate=0.45, be_rate=0.15, rr=2.0)),
        ("Sweep 40%/2R", StrategySpec(win_rate=0.40, be_rate=0.15, rr=2.0)),
        ("ORB 24%/4R",   StrategySpec(win_rate=0.24, be_rate=0.05, rr=4.0)),
    ]
    for name, base in profiles:
        for cost in (0.10, 0.38):
            for risk in (1.0, 2.0, 5.0):
                s = StrategySpec(win_rate=base.win_rate, be_rate=base.be_rate,
                                 rr=base.rr, risk_pct=risk, cost_r=cost)
                r = simulate(s, a)
                print(f"{name:>14} {risk:>5.1f} {cost:>5.2f}R | "
                      f"{r['ruin']:>8.1%} {r['dead']:>8.1%} {r['double']:>6.1%} "
                      f"{r['median_final']:>6.2f}x {r['median_max_dd']:>8.1%}")
        print()
    fee_table()


if __name__ == "__main__":
    main()
