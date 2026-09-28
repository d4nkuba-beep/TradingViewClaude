# IB 25% Retracement + ORB Breakout Strategie (TradingView / Pine v6)

Strategie-Script für den TradingView Strategy Tester, basierend auf dem
"IB 25 Retracement"-Setup (VWAP am 9:30-Open verankert, Opening Range
09:30–10:30 New York) – erweitert um einen **ORB-Breakout-Modus**, um zu
prüfen, wie sich ein Breakout-Trade nach Abschluss der Opening Range um
10:30 verhält.

**Datei:** `IB_ORB_VWAP_Strategy.pine`
**Empfohlener Chart:** ES/MES (oder SPY/QQQ), 1–5-Minuten-Timeframe.

## Setup 1 – IB 25% Retracement (Original aus den Screenshots)

1. VWAP wird am 9:30-Open (New York) verankert.
2. Initial Balance (IB) = Hoch/Tief von 09:30–10:30.
3. Richtung: Preis unter VWAP + VWAP fällt → Short (umgekehrt Long).
4. Limit-Order am **25%-Retracement** der IB-Range, Stop am
   **50%-Retracement**, Target am IB-Extrem → **1:1**.
5. Einstieg frühestens ab 10:20 (10 Min vor IB-Ende), keine neuen
   Entries nach 12:00.
6. Kein Trade bei flachem VWAP bzw. wenn der Preis zu oft um den VWAP
   gependelt ist (Chop-Filter: max. Kreuzungen seit 9:30).
7. Sobald IB-Hoch oder -Tief gesweept wurde, werden offene
   Entry-Orders gestrichen (abschaltbar).

## Setup 2 – ORB Breakout (die zu prüfende Idee)

Sobald die Opening Range um 10:30 steht:

- Stop-Order **über dem IB-Hoch** (Long) bzw. **unter dem IB-Tief**
  (Short), mit einstellbarem Tick-Offset.
- Standardmäßig nur in VWAP-Richtung (Steigung), optional beide Seiten
  als OCO-Paar (die Gegenseite wird bei Ausführung gestrichen).
- Stop-Loss wählbar: **IB-Mitte** (Standard), **Gegenseite der IB**
  oder **% der IB-Range**; Take-Profit als **R-Multiple** (Standard 1R).
- Entry-Fenster 10:30–12:00, max. 1 Breakout-Trade pro Tag (einstellbar).

## Modi im Strategy Tester vergleichen

Der Input **„Handelsmodus"** schaltet um:

| Modus | Verhalten |
|---|---|
| Nur Retracement | Nur das Original-Setup (Baseline) |
| Nur ORB-Breakout | Nur der Breakout nach 10:30 |
| Beide | Limit im Range-Inneren + Breakout-Stop außen; füllt eine Seite, wird die andere gestrichen |

So prüfst du die Breakout-Idee: Strategie auf den Chart laden, Modus
„Nur Retracement" testen, dann „Nur ORB-Breakout" mit denselben
Einstellungen, und Netto-Profit, Profit-Faktor, Trefferquote und max.
Drawdown im Strategy Tester vergleichen. Interessant ist v. a., ob der
Breakout an Tagen funktioniert, an denen das Retracement-Setup
gestrichen wird (Sweep der Range = genau das Breakout-Szenario).

Alle Positionen werden um 15:55–16:00 New York glattgestellt.

## Hinweise

- Alle Zeiten sind Session-Inputs in New-York-Zeit und frei anpassbar.
- Kommission ist mit 1,25 $/Kontrakt vorbelegt – an den eigenen Broker
  anpassen; Slippage im Strategy Tester zusätzlich einstellen.
- Kein Anlage- oder Finanzberatung; Backtest-Ergebnisse garantieren
  keine zukünftige Performance.

---

# Dual Thrust Intraday (neu)

**Datei:** `DualThrust_Strategy.pine` – Session-Breakout nach
[je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading):
Range der letzten N RTH-Tage, Stop-Buy bei `Open + K1·Range`, Stop-Sell bei
`Open − K2·Range`, Stop-and-Reverse, flat zum Handelsschluss. Standard N=2, K=0,5.

# Research

`research/` enthält einen Python-Backtest-Harness auf TradingView-MCP-Daten
(SPY/QQQ 5m/15m/30m) und die Auswertung der 5 GitHub-Strategiesammlungen aus
[diesem Artikel](https://osaengine.com/en/blog/top-trading-strategies-github/):
**[research/ANALYSE.md](research/ANALYSE.md)**.

Kurz: Unsere IB-Retrace- und ORB-1R-Setups sind auf diesen Daten nicht
profitabel. Dual Thrust (N=2, K=0,5) ist auf QQQ 2023–2026 in jedem Jahr
positiv (Edge v. a. Short-Seite), auf DIA/IWM nicht → Kandidat für
Paper-Trading auf QQQ/NQ im 5m-Chart, nach Bestätigung per Deep Backtesting.

```bash
pip install pandas numpy
python3 research/run_setups.py AMEX_SPY_30m NASDAQ_QQQ_30m
python3 research/run_dual_thrust.py
python3 research/run_dt_years.py      # 1h, ~3 Jahre, je Jahr
python3 research/run_dt_short.py      # Long/Short-Zerlegung
python3 research/run_dt_checks.py     # Auflösung, N-Sensitivität
```

Neue Daten: `mcp-tv-get-ohlcv` (count=5000) aufrufen und die `bars` als
`research/data/<EXCHANGE>_<TICKER>_<interval>.json` speichern.
