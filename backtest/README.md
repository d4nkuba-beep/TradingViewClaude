# Backtest- & Validierungs-Toolchain

Da Marktdaten-APIs aus dieser Umgebung nicht erreichbar sind, läuft die
Validierung zweistufig: Kursdaten kommen per CSV-Export aus TradingView,
alles Weitere rechnet lokal.

## 1. Daten aus TradingView exportieren

1. Chart öffnen: **MNQ1!** (oder MES1!/MGC1!), Timeframe **5 Minuten**.
2. Möglichst weit zurückscrollen (lädt Historie nach).
3. Menü rechts oben → **„Chartdaten exportieren…"** → Zeitformat **ISO** →
   CSV speichern (Spalten: `time, open, high, low, close, …`).

## 2. Strategie backtesten (`killzone_sweep_bos_backtest.py`)

1:1-Port der Pine-Logik (Sweep + BOS, Break-Even, Tagesstopp, EOD flat;
konservativ: Stop+TP in derselben Bar zählt als Verlust).

```bash
python3 killzone_sweep_bos_backtest.py mnq_5m.csv --preset london
python3 killzone_sweep_bos_backtest.py mnq_5m.csv --preset ny-am
python3 killzone_sweep_bos_backtest.py mnq_5m.csv --preset ny-pm
# Gold: --tick 0.1, Parameter-Varianten: --rr 3 --no-trend --piv-len 5
```

Ausgabe: Kennzahlen (Profit-Faktor, Trefferquote, Erwartung in R, Max-DD,
Tagesverlust-Verstöße) + `trades_out.csv` mit allen R-Multiples.

**Bestehens-Kriterien** (siehe `results_monte_carlo.md`): Profit-Faktor > 1,3;
Trefferquote (entschiedene Trades) ≥ 45 % bei 2R oder ≥ 40 % bei 3R;
Max-DD < 6 %; > 100 Trades.

## 3. Challenge-Wahrscheinlichkeit (`prop_challenge_monte_carlo.py`)

```bash
# Szenario-Grid (Modell-Annahmen):
python3 prop_challenge_monte_carlo.py
# Bootstrap aus echten Backtest-Trades:
python3 prop_challenge_monte_carlo.py --csv trades_out.csv --risk-pct 0.5
```

Simuliert 20 000 FTMO-Challenges (Ziel +10 %, Tageslimit 5 %, Max-Verlust
10 %) und liefert Pass-/Breach-/Timeout-Quote sowie die mediane Dauer.

## Validierungs-Hygiene

- **Out-of-Sample:** Daten zeitlich splitten (z. B. erste 70 % für
  Parameterwahl, letzte 30 % nur einmal am Ende testen).
- **Robustheit:** Parameter ±20 % variieren; kippt das Vorzeichen der
  Erwartung, ist das Setup überoptimiert.
- **Mehrere Märkte:** MNQ, MES, MGC – ein echter Edge stirbt nicht komplett
  beim Marktwechsel.
- Der Backtester wurde mit synthetischen Zufallsdaten rauchgetestet: Auf
  Rauschen liefert er korrekt eine **negative** Erwartung – er erfindet
  keine Profite.
