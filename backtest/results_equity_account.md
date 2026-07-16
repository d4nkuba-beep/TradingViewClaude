# Eigenkapital-Konto 300 $ auf Hyperliquid-Gold: Simulation

Ausgeführt am 2026-07-16 mit `equity_account_sim.py` (20 000 Pfade à 250
Trades, inkl. 0,5 % Flash-Gap-Wahrscheinlichkeit pro Trade auf −3R wegen der
dokumentierten Flash-Crash-Historie von `xyz:GOLD`).

## Kernergebnis: 5 % Risiko pro Trade ist auf diesem Konto nicht tragfähig

| Profil | Risiko/Trade | Kosten | P(Konto −50 %) | P(Konto −70 %) | P(Verdopplung) | Median Endstand | Median Max-DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sweep 45 %/2R | 1 % | 0.10R | 0.0 % | 0.0 % | 14.4 % | 1.53x | 12.5 % |
| Sweep 45 %/2R | **2 %** | 0.10R | 0.1 % | 0.0 % | **69.3 %** | **2.23x** | 23.9 % |
| Sweep 45 %/2R | **5 %** | 0.10R | **11.6 %** | 2.2 % | 91.0 % | 5.20x | **52.1 %** |
| Sweep 45 %/2R | 5 % | 0.38R | **94.0 %** | 82.5 % | 10.4 % | 0.29x | 74.7 % |
| Sweep 40 %/2R | 5 % | 0.10R | 46.7 % | 22.0 % | 52.3 % | 1.08x | 67.6 % |
| ORB 24 %/4R | 5 % | 0.10R | 70.6 % | 49.8 % | 53.2 % | 0.33x | 76.4 % |

(Alle Kombinationen: Script laufen lassen.)

Selbst mit dem **besten** Profil (45 %/2R) und günstigen Kosten bedeutet
5 % Risiko: Median-Drawdown 52 %, jede 9. Simulation halbiert das Konto —
und das Profil muss erst mal erreicht werden. Mit dem Break-Even-Profil
(40 %/2R) halbiert sich das Konto in fast der Hälfte der Fälle.

## Der eigentliche Killer bei 300 $: Gebühren vs. Stop-Distanz

Gebühren skalieren mit dem **Notional**, das Risiko mit der
**Stop-Distanz**: Kosten in R = 2 × Fee × Preis / Stop.

| Stop ($, Gold ~4200 $) | Taker (0.045 %) | Maker (0.015 %) |
|---:|---:|---:|
| 5 | 0.76R | 0.25R |
| 10 | 0.38R | 0.13R |
| 20 | 0.19R | 0.06R |
| 40 | 0.09R | 0.03R |

**Typische 5m-Killzone-Stops (5–10 $) sind mit Market-Orders strukturell
unprofitabel** (0.38–0.76R Kosten pro Trade frisst jeden realistischen
Edge; Median-Endstand 0.29x). HIP-3-Märkte können zusätzlich eine
Builder-Fee erheben — vor dem Livegang die effektive Fee im UI prüfen.

## Zusätzliches Venue-Risiko: Hebel & Flash-Gaps

5 % Risiko bei 10-$-Stop heißt ~21x Hebel auf Gold. Der dokumentierte
Flash-Crash (−100 $ in <1 Min) wäre ein 10R-Gap durch den Stop =
**−50 % Konto in einer Minute**. Die Simulation rechnet konservativ nur
mit −3R-Gaps — die Realität kann schlechter sein.

## Empfehlung für das 300-$-Konto

1. **Risiko 1–2 % pro Trade, nicht 5 %.** Bei 45 %/2R und 2 %:
   69 % Verdopplungschance, 0,1 % Halbierungsrisiko, Median +123 % über
   250 Trades. Das ist der beste Erwartungswert-zu-Ruin-Tradeoff.
2. **Stops ≥ 20–40 $** (H1-Strukturen bzw. weite Sweep-Level statt engster
   5m-Pivots) und **Limit-Orders (Maker)** für den Entry — sonst gewinnen
   nur die Gebühren. Der Sweep+BOS-Entry lässt sich als Limit in den
   Retest des BOS-Levels legen.
3. **Wochenenden flach** (`--skip-weekends`), wegen Flash-Gap-Risiko nie
   ohne Stop-Order im Markt.
4. Erst der Gold-Backtest (CSV via `hyperliquid_fetch.py`) entscheidet, ob
   das 45 %/2R-Profil auf `xyz:GOLD` überhaupt erreicht wird — vorher kein
   Live-Trade.
