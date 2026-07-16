# Monte-Carlo: Prop-Challenge-Bestehenswahrscheinlichkeit

Ausgeführt am 2026-07-16 mit `prop_challenge_monte_carlo.py` (20 000
Simulationen pro Szenario, Seed 42).

**Challenge-Modell (FTMO-Stil, Phase 1):** Ziel +10 %, Tages-Verlustlimit 5 %,
Max-Gesamtverlust 10 %, Horizont 120 Handelstage. **Strategie-Modell:**
0–2 Trades/Tag (Ø 1,0), 15 % Break-Even-Scratches, 0,04R Kosten pro Trade,
Strategie-eigener Tagesstopp bei −2 %.

| WinRate | RR | Risiko/Trade | E[R] | **Pass** | Breach | Timeout | Median Tage |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 35 % | 1.5 | 0.5 % | −0.15 | 0.4 % | 52.6 % | 47.0 % | 82 |
| 35 % | 2.0 | 0.5 % | ±0.00 | 15.7 % | 14.4 % | 70.0 % | 78 |
| 35 % | 3.0 | 0.5 % | +0.30 | **86.4 %** | 0.9 % | 12.6 % | 52 |
| 40 % | 1.5 | 0.5 % | −0.04 | 4.9 % | 17.5 % | 77.6 % | 84 |
| 40 % | 2.0 | 0.5 % | +0.13 | 48.8 % | 2.4 % | 48.8 % | 73 |
| 40 % | 2.0 | 1.0 % | +0.13 | 75.3 % | 16.4 % | 8.3 % | 39 |
| 40 % | 3.0 | 0.5 % | +0.47 | **98.0 %** | 0.1 % | 1.9 % | 39 |
| 45 % | 2.0 | 0.5 % | +0.26 | **83.0 %** | 0.2 % | 16.8 % | 63 |
| 45 % | 2.0 | 1.0 % | +0.26 | **93.5 %** | 4.5 % | 2.0 % | 31 |
| 45 % | 3.0 | 0.5 % | +0.64 | **99.9 %** | 0.0 % | 0.1 % | 30 |
| 50 % | 1.5 | 0.5 % | +0.17 | 60.7 % | 0.2 % | 39.1 % | 76 |
| 50 % | 2.0 | 0.5 % | +0.39 | **97.2 %** | 0.0 % | 2.8 % | 48 |
| 50 % | 3.0 | 0.5 % | +0.81 | **100.0 %** | 0.0 % | 0.0 % | 24 |

(Vollständiges Grid inkl. 1-%-Risiko-Varianten: Script ohne Argumente laufen
lassen.)

## Was daraus folgt

1. **Die Messlatte für den Backtest ist jetzt exakt definiert:** Mit dem
   Standard-Setup (2R-Ziel) muss die Strategie **≥ 45 % Trefferquote auf
   entschiedene Trades** liefern (Pass-Quote 83–94 %). Bei 40 %/2R ist sie
   praktisch Break-Even (E[R] +0.13) – das reicht nicht. Alternativ reichen
   **40 % Trefferquote bei 3R-Zielen** (98 % Pass-Quote).
2. **Die Risiko-Defaults sind strukturell sicher:** Mit 0,5 % Risiko/Trade und
   positivem Erwartungswert liegt die Breach-Wahrscheinlichkeit bei ≤ 2,4 % –
   selbst eine mittelmäßige Strategie fliegt fast nie wegen Limit-Verstoß
   raus, sie läuft höchstens in den Timeout. Das 5-%-Tageslimit ist mit max.
   2 Trades × 0,5 % Risiko mathematisch unerreichbar.
3. **1 % Risiko beschleunigt (Median ~31 statt ~63 Tage), kauft das aber mit
   Breach-Risiko** (4,5 % statt 0,2 % bei 45 %/2R). Empfehlung: Challenge mit
   0,5 % beginnen, erst nach Puffer (>+3 %) auf 1 % erhöhen.
4. **Negative oder Null-Erwartung ist mit keinem Money-Management rettbar**
   (35 %/1,5R → 0,4 % Pass). Der Edge muss aus dem Setup kommen; das
   Risikomodul entscheidet nur, ob ein vorhandener Edge die Challenge
   überlebt.

## Zusatzlauf: publiziertes ORB-Profil (Zarattini/Aziz)

Gleiches Challenge-Modell, aber Trade-Profil der 5-Min-ORB-Strategie
(1 Trade/Tag, 5 % Scratches, niedrige Trefferquote, große Gewinner):

| WinRate | RR | Risiko/Trade | E[R] | **Pass** | Breach | Timeout | Median Tage |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 % | 4.0 | 0.25 % | +0.15 | 21.7 % | 0.7 % | 77.6 % | 86 |
| 24 % | 4.0 | 0.5 % | +0.15 | 59.8 % | 12.5 % | 27.7 % | 54 |
| 24 % | 5.0 | 0.5 % | +0.38 | **87.8 %** | 4.7 % | 7.5 % | 40 |
| 24 % | 5.0 | 1.0 % | +0.38 | 80.4 % | 19.5 % | 0.1 % | 16 |
| 30 % | 4.0 | 0.5 % | +0.43 | **93.9 %** | 1.3 % | 4.8 % | 40 |

**Interpretation:** Das ORB-Profil ist auf realen Daten belegt profitabel,
aber seine niedrige Trefferquote erzeugt lange Verluststrecken – gegen ein
6-%-Trailing-Limit ist das deutlich fragiler als das 45-%/2R-Profil des
Sweep+BOS-Setups (12,5 % Breach bei 0,5 % Risiko und 4R-Payoff). Für die
Challenge heißt das: ORB nur mit 0,25–0,5 % Risiko fahren und den
10R-Take-Profit aktiv lassen (höherer Payoff → 87,8 % Pass), oder ORB als
Zweitsystem neben Sweep+BOS laufen lassen, um den Pfad zu glätten.

## Nächster Schritt

Echte R-Multiples aus dem Backtest (TradingView-CSV →
`killzone_sweep_bos_backtest.py` → `trades_out.csv`) einspeisen:

```
python3 prop_challenge_monte_carlo.py --csv trades_out.csv
```

Das ersetzt die Modell-Annahmen durch die empirische Trade-Verteilung und
liefert die tatsächliche Bestehenswahrscheinlichkeit der Strategie.
