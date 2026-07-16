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

## Nachtrag: 10–15 % Risiko ("High Risk zum schnellen Skalieren")

Gleiche Simulation plus numerische Kelly-Analyse (E[ln(1+f·R)], 400 000
Züge), Kosten 0,10R:

| Profil | Risiko | P(−50 %) | P(−70 %) | Median Endstand | Median Max-DD |
|---|---:|---:|---:|---:|---:|
| 45 %/2R (Ziel) | 10 % | 45.0 % | 25.3 % | 6.81x | 78.4 % |
| 45 %/2R (Ziel) | **15 %** | **69.7 %** | **54.4 %** | **0.30x** | 87.9 % |
| 40 %/2R (realistisch) | 10 % | 82.2 % | 69.0 % | 0.29x | 82.1 % |
| 40 %/2R (realistisch) | 15 % | 94.5 % | 89.7 % | 0.28x | 84.8 % |

Kelly-Optimum (maximales Log-Wachstum): **~10 %** beim Ziel-Profil,
**~3 %** beim realistischen Profil. Daraus folgt:

1. **15 % liegt jenseits von Voll-Kelly selbst für das Traumprofil** – das
   Median-Ergebnis ist dann ein Verlustkonto (0.30x), obwohl einzelne
   Pfade explodieren. Mehr Risiko = langsameres Wachstum ab ~10 %.
2. **Ob Kelly 10 % oder 3 % ist, entscheiden 5 Prozentpunkte Trefferquote** –
   und die kennen wir ohne Backtest/Live-Stichprobe schlicht nicht.
   Overbetting gegenüber dem wahren Kelly ruiniert auch eine profitable
   Strategie. Standard-Praxis ist deshalb maximal Halb-Kelly.
3. **Mechanisch geht 15 % oft gar nicht:** bei 20-$-Stop auf Gold bräuchte
   es ~31x Hebel (Cap: 25x). Und ein Flash-Gap von −3R bedeutet bei 15 %
   Risiko −45 % Konto in einer Minute – zwei davon = tot.
4. Wer "schnell skalieren" will: Der Unterschied zwischen 2 % und 10 %
   Risiko ist beim Zielprofil 2.2x vs. 8.5x im Median über 250 Trades –
   aber erkauft mit 45 % Halbierungsrisiko und 78 % Median-Drawdown, den
   psychologisch niemand durchhandelt. Bei 300 $ Startkapital ist
   **Nachschießen** (z. B. +100 $/Monat) der schnellere und sichere
   Skalierungshebel, nicht die Risikoschraube.

**Risiko-Fahrplan:** 2 % solange unbewiesen → nach bestandenem Backtest
(≥ 45 %/2R über > 100 Trades) und 1 Monat live im Plus: 3–5 %
(≈ Halb-Kelly) → niemals 10 %+.

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
