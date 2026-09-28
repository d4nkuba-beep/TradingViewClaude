# Analyse: 5 GitHub-Strategiesammlungen vs. unsere IB/ORB-Strategie

Quelle: [osaengine.com – Top trading strategies on GitHub](https://osaengine.com/en/blog/top-trading-strategies-github/)
Stand: 28.09.2026 · Daten: TradingView-MCP (`mcp-tv-get-ohlcv`), nur RTH, 15 Min verzögert.

## Kurzfazit

1. **Keine der Sammlungen liefert eine "fertig profitable" Strategie.** Die Repos
   eignen sich als Ideen- und Code-Steinbruch, nicht als Signalquelle.
2. **Unsere beiden Setups (IB-25%-Retrace und ORB-Breakout 1R) sind in den Daten
   nicht profitabel** – über alle Timeframes und beide Symbole PF < 1
   (Ausnahme: Retrace auf QQQ 15m knapp positiv, zerfällt aber in der zweiten Hälfte).
3. **Einziger ernsthafter Kandidat: Dual Thrust (aus je-suis-tm/quant-trading)** mit
   N=2, K=0.5. Runde 2 (siehe unten) mit ~3 Jahren 1h-Daten und 8 Märkten:
   **auf QQQ in jedem Jahr 2023–2026 positiv** (PF 1,38, 2024 = echter Out-of-Sample),
   ebenso XLK/SMH 2024–25; auf DIA/IWM **keine** Edge. Der Gewinn kommt überwiegend
   von der **Short-Seite** (QQQ nur Short: PF 1,53, max. DD 5,4 %). Die letzten 3 Monate
   sind leicht negativ. → Kandidat für Paper-Trading auf QQQ/NQ, 5m-Chart, nicht mehr.

## Die 5 Repos – was taugt, was lernen wir

| Repo | Inhalt | Relevanz für uns | Lehre |
|---|---|---|---|
| [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) | ~60 Python-Strategien für den Krypto-Bot FreqTrade (MACD, BB/RSI, Supertrend, Scalps) | gering – Krypto, anderes Framework | ROI-Tabellen (zeitabhängige Gewinnziele) + Custom-Stoploss sind ein gutes Exit-Konzept. Die Community-Strategien sind nicht validiert, das README warnt ausdrücklich davor, sie ungetestet einzusetzen. |
| [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) | Lehr-Backtests: **Dual Thrust**, **London Breakout**, Heikin-Ashi, Pairs, RSI/BB-Pattern, Monte Carlo | **hoch** – Dual Thrust & London Breakout sind Session-Range-Breakouts wie unser ORB | Schwellen nicht nur aus der heutigen Range, sondern aus der **Range der Vortage** ableiten; **Stop-and-Reverse** statt fester 1R-Targets; immer flat zum Session-Ende. Der Autor zeigt offen, dass viele Strategien nicht profitabel sind. |
| [StockSharp/AlgoTrading](https://github.com/StockSharp/AlgoTrading) | >4000 C#/Python-Beispiele, u. a. ~15 ORB- und ~25 VWAP-Varianten | mittel – viele Ideen, aber | **Namen ≠ Logik**: Stichproben `0766_NY_ORB_CP` und `1444_TOT_ORB_Titan` implementieren in Wahrheit einen EMA-Crossover, keine Opening Range. Die Sammlung ist offensichtlich automatisch portiert. Nichts ungeprüft übernehmen. |
| [vrishank97/AlgoTrading](https://github.com/vrishank97/AlgoTrading) | 8 fertige Indikator-Agents (EMA/DEMA/TEMA/CCI/Momentum) + genetische Parameter-Optimierung | gering | Genetische Optimierung auf einem Datensatz = Curve-Fitting-Maschine. Lehre für uns: Parameter nur akzeptieren, wenn **Nachbarwerte** auch funktionieren (Plateau statt Spitze). |
| [Alorse/pinescript-strategies](https://github.com/Alorse/pinescript-strategies) | ~50 Pine-Strategien + automatisierter PineTS-Backtest in CI | mittel – direkt TradingView | Ihr eigenes `BACKTEST.md` zeigt auf BTC 1D für **fast alle** Strategien Sharpe < 0 in beiden Perioden (2022–24 und 2025–26). Gute Idee zum Kopieren: **automatischer Backtest über zwei getrennte Regime** – genau das macht unser `research/`-Harness jetzt mit TradingView-MCP-Daten. |

## Backtest über die TradingView-MCP

### Methode

- `mcp-tv-get-ohlcv` liefert max. 5000 Bars → SPY/QQQ 5m (65 Tage), 15m (193 Tage),
  30m (386 Tage, 14.03.2025–25.09.2026). ES1! liefert nur ~18 RTH-Tage in 5m (24h-Session) → nicht verwendet.
- Bar-basierte Simulation (`bt.py`), **konservativ**: Stop & Target in derselben Kerze → Stop zuerst;
  in der Entry-Kerze zählt das Target nur, wenn die Kerze dahinter schließt.
- Kosten 0,01 % pro Round-Trip (≈ 1 ES-Tick + Kommission), zusätzlich mit 0,02 % geprüft.
- H1/H2 = Ergebnis erste/zweite Hälfte der Trades (Stabilitätscheck).
- Auf 15m/30m ist der VWAP-Chop-Filter unserer Strategie nicht sinnvoll abbildbar (nur auf 5m aktiv);
  das Retrace-Fenster startet dort erst mit der ersten Kerze nach 10:20.

### Ergebnis unserer Setups und der Repo-Ideen (Summe % bei 1 Einheit, PF)

| Setup | SPY 5m | QQQ 5m | SPY 15m | QQQ 15m | SPY 30m | QQQ 30m |
|---|---|---|---|---|---|---|
| IB-25%-Retrace (Setup 1) | −1,1 (0,57) | −3,9 (0,32) | −1,2 (0,86) | +0,3 (1,03) | −2,2 (0,69) | −3,5 (0,69) |
| ORB Mitte-Stop 1R (Setup 2) | −1,5 (0,75) | −5,0 (0,59) | −6,3 (0,72) | −13,6 (0,63) | −2,3 (0,94) | −12,0 (0,80) |
| ORB Mitte-Stop 2R | −1,5 (0,78) | −5,1 (0,62) | −3,9 (0,84) | −11,1 (0,72) | +1,3 (1,03) | −10,9 (0,83) |
| ORB bis Handelsschluss halten | −2,6 (0,64) | −6,5 (0,53) | −5,0 (0,80) | −12,5 (0,69) | +0,9 (1,02) | −7,6 (0,88) |
| ORB ohne VWAP-Filter (EOD) | −2,2 (0,67) | −6,5 (0,53) | −5,1 (0,80) | −14,0 (0,66) | −15,0 (0,73) | −23,5 (0,69) |
| Erste-Kerze-ORB → EOD (Benchmark) | −1,7 (0,78) | −0,9 (0,93) | −4,1 (0,86) | +0,5 (1,01) | −7,3 (0,90) | +4,9 (1,05) |
| Dual Thrust N4 K0.5 (Repo-Default) | +0,0 (1,04) | −2,6 (0,27) | −2,9 (0,68) | −3,6 (0,69) | −1,2 (0,94) | +0,7 (1,03) |
| **Dual Thrust N2 K0.5** | −1,7 (0,70) | −1,1 (0,87) | +1,2 (1,07) | +6,4 (1,30) | **+13,3 (1,34)** | **+17,5 (1,35)** |

Vollständige Tabellen inkl. Trefferquote, Drawdown, IB-Größenfilter und Varianten:
[`results/setups.txt`](results/setups.txt), [`results/dual_thrust.txt`](results/dual_thrust.txt).

### Was wir für unsere Strategie lernen

- **Der VWAP-Richtungsfilter hilft deutlich** (ORB bis EOD ohne Filter: −15,0 % / −23,5 % statt +0,9 % / −7,6 % auf SPY/QQQ 30m) –
  behalten.
- **1R-Target ist die schwächste Exit-Variante** beim Breakout; 2R bzw. Halten bis EOD ist auf SPY 30m
  besser (≈ Break-even). Breakouts leben von den wenigen Trend-Tagen – feste 1R-Ziele schneiden die ab.
- **IB-Größenfilter** (enge IB → Breakout, weite IB → Retrace) bringt keine stabile Verbesserung;
  einziger Lichtblick "Retrace nur bei weiter IB" auf QQQ 15m (PF 1,36), auf allen anderen Sets negativ → Zufall.
- **Die Vortages-Range ist die bessere Referenz als die IB**: Dual Thrust N=2 schlägt jede IB-Variante.
  Das spricht dafür, die Breakout-Schwelle an die Volatilität der letzten Tage zu koppeln statt an die
  ersten 60 Minuten.

### Robustheit Dual Thrust

- **Parameter-Plateau:** Auf 30m ist N=2 für alle K von 0,2 bis 0,7 auf **beiden** Symbolen positiv;
  K=0,2 für alle N von 2 bis 6. Kein einzelner Glückstreffer.
- **Kosten ×2:** SPY 30m +11,0 % (PF 1,27), QQQ 30m +15,1 % (PF 1,29).
- **Ohne den Tarif-Crash Mär–Mai 2025:** SPY +8,1 % (PF 1,29, DD 5,7 %), QQQ +10,8 % (PF 1,27, DD 4,5 %).
- **Schwachstelle:** Auf den jüngsten Daten (5m, 25.06.–25.09.2026) negativ; auf 30m sind Juli 2026
  (SPY −3,2 %) und Mai 2026 die schlechtesten Monate. Die 30m-Simulation ist gröber (Reversal nur einmal pro Kerze).

**Bewertung:** Plausible, aber unbewiesene Edge – vor allem in volatilen Trendphasen. Nicht "profitabel"
im Sinne von einsatzbereit.

## Runde 2 – längere Historie, mehr Märkte (1h-Daten 11/2023–09/2026)

Neue Skripte: `run_dt_years.py`, `run_dt_short.py`, `run_dt_checks.py`;
Ergebnisse in `results/dual_thrust_oos.txt`, `results/dual_thrust_short.txt`, `results/dual_thrust_checks.txt`.

### Dual Thrust N2/K0.5 (Stop-and-Reverse) je Jahr

| Markt | Gesamt | PF | Max-DD | 2023 (6 Wo.) | 2024 | 2025 | 2026 YTD |
|---|---|---|---|---|---|---|---|
| **QQQ** | **+35,2 %** | **1,38** | 7,1 % | +0,9 | **+11,2** | +15,8 | **+7,3** |
| XLK | +40,6 % | 1,35 | 9,7 % | −0,7 | +19,8 | +18,8 | +2,7 |
| SMH | +42,7 % | 1,25 | 17,1 % | +2,3 | +23,3 | +18,0 | −0,9 |
| SPY | +19,7 % | 1,26 | 6,5 % | +2,4 | −1,1 | +17,1 | +1,3 |
| DIA | +1,5 % | 1,02 | 10,7 % | +1,8 | −5,2 | +7,2 | −2,2 |
| IWM | −3,4 % | 0,98 | 14,3 % | +0,4 | −0,4 | +7,0 | −10,3 |

- **Tech/Nasdaq trägt, Dow/Small Caps nicht.** SPY lebt fast nur von 2025 (Zoll-Crash).
- ES1!/NQ1! liefern per MCP nur ~10 Monate 1h und die Futures-Stundenkerzen beginnen um :00
  (RTH-Open 9:30 fehlt) → nicht vergleichbar, nur zur Vollständigkeit in `dual_thrust_oos.txt`.

### Die Edge sitzt auf der Short-Seite

| Markt | Long-Anteil | Short-Anteil | Nur Short N2/K0.5 | je Jahr 2023 / 24 / 25 / 26 |
|---|---|---|---|---|
| QQQ | +6,4 % (PF 1,15) | +28,8 % (PF 1,57) | **+27,4 %, PF 1,53, DD 5,4 %** | +1,4 / +11,9 / +10,8 / **+3,3** |
| XLK | +7,2 % (PF 1,14) | +33,4 % (PF 1,53) | +31,8 %, PF 1,49, DD 6,8 % | +0,7 / +15,4 / +16,0 / −0,3 |
| SMH | +1,0 % (PF 1,01) | +41,7 % (PF 1,44) | +39,3 %, PF 1,40, DD 14,5 % | +1,8 / +20,2 / +16,0 / +1,3 |
| SPY | +5,3 % (PF 1,16) | +14,4 % (PF 1,34) | +14,5 %, PF 1,34, DD 5,3 % | +1,2 / +3,1 / +10,4 / −0,3 |

Im Bullenmarkt (QQQ Buy&Hold +94 %) verdient die Strategie vor allem an **Intraday-Abverkäufen,
die bis zum Schluss durchlaufen**. Das ist kein verstecktes Long-Beta – eher ein Hedge-artiges
Profil, das gut zu einem Long-Depot passt.

### Plausibilitätschecks

- **N=1 sieht auf 1h spektakulär aus (QQQ +80 %), ist aber ein Artefakt:** Auf 15m-Daten desselben
  Zeitraums schrumpft es von +16,6 % auf +1,8 %. Grobe Kerzen verschlucken die Whipsaws um die
  enge Vortagesrange. **Verworfen.**
- **N=2/K0.5 ist auflösungsstabil:** 5m ≈ 1h, 15m ≈ 1h, 30m ≈ 1h (Abweichung < 2 Prozentpunkte).
- **Parameter:** K 0,4–0,6 bei N=2 überall positiv auf QQQ/XLK/SMH; N=3 deutlich schwächer.
  N=2 ist also ein Grat, keine breite Hochebene – ein echtes Risiko.
- **Erste RTH-Kerze** (Pine kann dort noch nicht handeln): auf 5m ohne Effekt, auf 30m kostet sie
  ca. 15–40 % des Ergebnisses → **Pine-Strategie auf 5m-Chart laufen lassen.**

### Bewertung

Verwertbar ist **Dual Thrust N2/K0.5 auf QQQ (bzw. NQ/MNQ), 5m-Chart, optional „Nur Short“**:
drei Jahre in Folge positiv, kleiner Drawdown, robuste Kosten. Einschränkungen: nur ~3 Jahre Daten,
N=2 ist schmal, die letzten 3 Monate leicht negativ. Das reicht für **Paper-Trading**, nicht für
echtes Kapital.

## Nächste Schritte

1. `DualThrust_Strategy.pine` auf **NQ1!/MNQ1! und QQQ, 5m**, Richtung „Long & Short“ und
   „Nur Short“, im Strategy Tester mit maximaler Historie (Deep Backtesting, ab 2020) prüfen;
   Slippage 1 Tick. Kriterium: PF > 1,2 in jedem Jahr. Das deckt auch 2020–2022 ab, wo die
   MCP keine Daten liefert.
2. Bei Bestätigung: 4–8 Wochen Paper-Trading mit TradingView-Alerts (1 MNQ).
3. IB/ORB-Script: nicht weiter optimieren – keine Variante war robust.
4. Harness monatlich mit frischen MCP-Daten wiederholen (Walk-forward):
   `python3 research/run_dt_years.py NASDAQ_QQQ_1h` und `python3 research/run_dt_short.py NASDAQ_QQQ_1h`.

*Keine Anlageberatung. Backtests auf 5000-Bar-Fenstern sind statistisch dünn und garantieren nichts.*
