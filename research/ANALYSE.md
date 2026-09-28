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
   N=2, K=0.5: PF 1,34/1,35 auf SPY/QQQ 30m über 18 Monate, überlebt doppelte Kosten
   und das Herausnehmen des Crashs vom April 2025. **Aber:** in den letzten 3 Monaten
   (5m-Daten) negativ, und 18 Monate sind zu kurz. → Als Pine-Strategie
   (`DualThrust_Strategy.pine`) im Strategy Tester mit mehr Historie und auf ES/NQ prüfen,
   **bevor** echtes Geld fließt.

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

## Nächste Schritte

1. `DualThrust_Strategy.pine` auf ES1!/NQ1! und SPY/QQQ, 5m und 30m, mit **mehreren Jahren** Historie
   im Strategy Tester laufen lassen (Slippage 1 Tick einstellen). Kriterium: PF > 1,2 in jedem
   einzelnen Jahr, sonst verwerfen.
2. Im IB/ORB-Script den ORB-Exit von 1R auf 2R/EOD umstellen und als Variante eine
   Vortages-Range-Schwelle testen.
3. Harness erneut laufen lassen, sobald neue Daten vorliegen (Walk-forward):
   `python3 research/run_setups.py AMEX_SPY_30m NASDAQ_QQQ_30m` und `python3 research/run_dual_thrust.py`.

*Keine Anlageberatung. Backtests auf 5000-Bar-Fenstern sind statistisch dünn und garantieren nichts.*
