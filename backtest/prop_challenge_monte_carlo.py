#!/usr/bin/env python3
"""Monte-Carlo-Simulation einer Prop-Firm-Challenge (FTMO-Stil).

Beantwortet die Frage: Welche Kennzahlen (Trefferquote, R-Ziel, Risiko pro
Trade) muss die Killzone-Sweep+BOS-Strategie liefern, damit die Challenge
mit hoher Wahrscheinlichkeit bestanden wird, OHNE die Limits zu reissen?

Challenge-Modell (Standard: FTMO 2-Step, Phase 1):
  - Gewinnziel: +10 % (Phase 2: +5 %)
  - Tages-Verlustlimit: 5 % (Verstoss = sofort durchgefallen)
  - Max. Gesamtverlust: 10 % (statisch auf Startkapital)
  - Kein Zeitlimit; Simulation kappt bei `max_days` Handelstagen

Strategie-Modell (entspricht den Script-Defaults):
  - `risk_pct` Risiko pro Trade, Take-Profit bei `rr` R
  - Break-Even-Stop erzeugt Scratch-Trades (0 R) mit Wahrscheinlichkeit p_be
  - Kosten (Kommission + Slippage) als R-Abzug pro Trade
  - 0-2 Trades pro Tag, eigenes Tages-Stopp-Limit der Strategie (Default 2 %)

Nutzung:
  python3 prop_challenge_monte_carlo.py            # Szenario-Grid
  python3 prop_challenge_monte_carlo.py --csv trades.csv --r-col r_multiple
                                                   # Bootstrap aus echten
                                                   # Backtest-R-Multiples
"""

from __future__ import annotations

import argparse
import random
import statistics
from dataclasses import dataclass


@dataclass
class ChallengeSpec:
    profit_target_pct: float = 10.0
    daily_loss_pct: float = 5.0
    max_loss_pct: float = 10.0
    max_days: int = 120


@dataclass
class StrategySpec:
    win_rate: float = 0.40          # Anteil voller Gewinner (an entschiedenen Trades)
    be_rate: float = 0.15           # Anteil Scratch-Trades (Break-Even, 0 R)
    rr: float = 2.0                 # Take-Profit in R
    risk_pct: float = 0.5           # Risiko pro Trade in % des Kontos
    cost_r: float = 0.04            # Kosten pro Trade in R (Kommission+Slippage)
    max_trades_day: int = 2
    p_trades: tuple = (0.30, 0.40, 0.30)  # P(0), P(1), P(2) Trades pro Tag
    strategy_daily_stop_pct: float = 2.0  # eigenes Tageslimit der Strategie


def expectancy_r(s: StrategySpec) -> float:
    decided = 1.0 - s.be_rate
    return decided * (s.win_rate * s.rr - (1 - s.win_rate) * 1.0) - s.cost_r


def draw_trade_r(s: StrategySpec, rng: random.Random) -> float:
    u = rng.random()
    if u < s.be_rate:
        return 0.0 - s.cost_r
    if rng.random() < s.win_rate:
        return s.rr - s.cost_r
    return -1.0 - s.cost_r


def simulate_one(spec: ChallengeSpec, s: StrategySpec, rng: random.Random,
                 empirical_r: list[float] | None = None) -> tuple[str, int]:
    """Eine Challenge simulieren. Rueckgabe: (Ergebnis, Handelstage)."""
    equity = 0.0  # kumulierte % auf Startkapital
    for day in range(1, spec.max_days + 1):
        day_pnl = 0.0
        n_trades = rng.choices(range(len(s.p_trades)), weights=s.p_trades)[0]
        for _ in range(n_trades):
            if day_pnl <= -s.strategy_daily_stop_pct:
                break  # Strategie-eigener Tagesstopp
            if empirical_r is not None:
                r = rng.choice(empirical_r)
            else:
                r = draw_trade_r(s, rng)
            day_pnl += r * s.risk_pct
            # Prop-Limits werden intraday geprueft
            if day_pnl <= -spec.daily_loss_pct:
                return "breach_daily", day
            if equity + day_pnl <= -spec.max_loss_pct:
                return "breach_total", day
        equity += day_pnl
        if equity >= spec.profit_target_pct:
            return "passed", day
    return "timeout", spec.max_days


def run_scenario(spec: ChallengeSpec, s: StrategySpec, n: int = 20000,
                 seed: int = 42, empirical_r: list[float] | None = None) -> dict:
    rng = random.Random(seed)
    outcomes: dict[str, int] = {}
    pass_days: list[int] = []
    for _ in range(n):
        result, day = simulate_one(spec, s, rng, empirical_r)
        outcomes[result] = outcomes.get(result, 0) + 1
        if result == "passed":
            pass_days.append(day)
    return {
        "pass": outcomes.get("passed", 0) / n,
        "breach": (outcomes.get("breach_daily", 0) + outcomes.get("breach_total", 0)) / n,
        "timeout": outcomes.get("timeout", 0) / n,
        "median_days": statistics.median(pass_days) if pass_days else float("nan"),
        "expectancy_r": expectancy_r(s),
    }


def scenario_grid() -> None:
    spec = ChallengeSpec()
    print(f"Challenge: Ziel +{spec.profit_target_pct}% | Tageslimit {spec.daily_loss_pct}% "
          f"| Max-Verlust {spec.max_loss_pct}% | Horizont {spec.max_days} Handelstage")
    print(f"{'WinRate':>7} {'BE':>4} {'RR':>4} {'Risk%':>5} | {'E[R]':>6} "
          f"{'Pass':>6} {'Breach':>6} {'Timeout':>7} {'MedTage':>7}")
    print("-" * 66)
    for wr in (0.35, 0.40, 0.45, 0.50):
        for rr in (1.5, 2.0, 3.0):
            for risk in (0.5, 1.0):
                s = StrategySpec(win_rate=wr, rr=rr, risk_pct=risk)
                r = run_scenario(spec, s)
                print(f"{wr:>7.0%} {s.be_rate:>4.0%} {rr:>4.1f} {risk:>5.2f} | "
                      f"{r['expectancy_r']:>+6.2f} {r['pass']:>6.1%} {r['breach']:>6.1%} "
                      f"{r['timeout']:>7.1%} {r['median_days']:>7.0f}")


def from_csv(path: str, r_col: str, risk_pct: float) -> None:
    import csv

    rs: list[float] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rs.append(float(row[r_col]))
    if len(rs) < 30:
        print(f"WARNUNG: nur {len(rs)} Trades – Bootstrap-Ergebnis ist unzuverlaessig.")
    spec = ChallengeSpec()
    s = StrategySpec(risk_pct=risk_pct)
    r = run_scenario(spec, s, empirical_r=rs)
    mean_r = statistics.fmean(rs)
    print(f"Empirische Trades: {len(rs)} | Mittleres R: {mean_r:+.2f}")
    print(f"Pass: {r['pass']:.1%} | Breach: {r['breach']:.1%} | "
          f"Timeout: {r['timeout']:.1%} | Mediane Tage: {r['median_days']:.0f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", help="Trade-CSV mit R-Multiples (Bootstrap statt Modell)")
    p.add_argument("--r-col", default="r_multiple", help="Spaltenname der R-Multiples")
    p.add_argument("--risk-pct", type=float, default=0.5, help="Risiko pro Trade in %%")
    args = p.parse_args()
    if args.csv:
        from_csv(args.csv, args.r_col, args.risk_pct)
    else:
        scenario_grid()
