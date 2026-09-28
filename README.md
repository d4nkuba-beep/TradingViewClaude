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

# ORB Fakeout Fade GOLD M5 (v1.3)

**Datei:** `ORB_Fakeout_Fade_GOLD_M5.pine` · **Chart:** GC1! / MGC1!, 5 Minuten
· **Alert-Nachricht:** `{{strategy.order.alert_message}}` (TradersPost)

- **Setup A – Fakeout-Fade:** Ausbruch aus der Opening Range scheitert
  innerhalb von `k` Kerzen → Einstieg zurück in die Range, SL hinter dem
  Fakeout-Extrem.
- **Setup B – Breakout-Akzeptanz:** `N` Closes außerhalb → Continuation
  (per Default aus – verlor im Backtest auf allen Datensätzen).

## v1.3 – Defaults aus dem Backtest

Die Logik wurde in Python 1:1 nachgebaut (`research/orb_fakeout_backtest.py`:
Entry auf dem Close, Stop/Limit intrabar mit TradingView-Pfadregel,
1 Tick Slippage) und auf TradingView-Daten getestet: **GC, SI, PL, HG**,
jeweils **5 min** (02.–25.09.2026, ~18 Handelstage) und **15 min**
(03.08.–25.09.2026). Metalle ohne Gold dienen als Robustheits-Check.

| Variante | Trades | Summe R | Datensätze positiv | Gold (5m / 15m) |
|---|---|---|---|---|
| v1.1 (Ziel Mitte, keine Filter) | 115 | +3,2 R | 4 / 8 | +4,2 R / +7,8 R |
| **v1.3 (Ziel = weiteres von Mitte / 1R, VWAP-Bestätigung)** | 65 | **+11,7 R** | **8 / 8** | +1,5 R / +3,5 R |

Wichtige Ergebnisse (je Filter einzeln gegen v1.1):

| Änderung | Effekt |
|---|---|
| Ziel **1R** statt Mitte | +13,9 R, 6/8 besser – „Mitte" bringt oft nur 0,2–0,4 R |
| Ziel **weiteres von Mitte / 1R** + **VWAP** | als einzige Kombination auf allen 8 Datensätzen positiv → neuer Default |
| VWAP-Bestätigung | halbiert die Trades, ~6× höheres Ø-R pro Trade |
| **Min-RR-Filter** | **schadet** (−4 bis −7 R) – filtert gerade die Trades mit hoher Trefferquote; bleibt aus |
| Setup B (Continuation) | −19 R, 0/8 besser → aus |
| Ziel Gegenseite | −19 R |
| Opening Range 08:20 (COMEX) | schlechter als 09:30 |
| Rückkehr-Tiefe, Max-Fakeout 0,5, Zeit-Stop, Liquidity-Sweep | uneinheitlich bzw. zu wenige Trades |
| Break-even 0,5R / 1R | etwa neutral |
| Ohne Montag (`3456`) | besser (+15,8 R, 8/8) – aber nur ~4–10 Montage je Datensatz, daher nicht Default |

**Ehrlicher Hinweis:** Auf *Gold allein* war v1.1 in diesem kurzen Zeitraum
besser (10 bzw. 13 Trades). Über alle Metalle hatte v1.1 aber praktisch
keinen Vorteil (+0,03 R/Trade), v1.3 dagegen +0,18 R/Trade und kein
negativer Datensatz. Das ist das verlässlichere Signal. Die Stichprobe
ist trotzdem klein – vor Live-Einsatz im TradingView Strategy Tester
über 6–12 Monate (Deep Backtesting) prüfen.

## Filter und Optionen

| Filter / Option | Wirkung |
|---|---|
| **Ziel** | `Mitte/RR max` (Default), `Mitte`, `Gegenseite`, `RR` |
| **A: VWAP-Seite** (Default an) | Short-Fade nur mit Close < VWAP, Long nur mit Close > VWAP |
| A: Min. RR | Kein Fade, wenn Ziel/Risiko < x (laut Backtest nicht empfohlen) |
| Min. Rückkehr in Range | Close muss x·Range innerhalb liegen |
| Range-Größe / Tages-ATR | Nur handeln, wenn OR zwischen min·ATR und max·ATR |
| B: VWAP-Richtung / Volumen | Filter für Setup B |
| A: schwacher Ausbruch (Volumen) | Fade nur bei Ausbruchsvolumen ≤ x·Durchschnitt |
| A: Liquidity-Sweep | Fakeout muss PDH/PDL oder Overnight-High/-Low nehmen |
| Handelstage / Sperrdaten | Wochentage (Pine: 2=Mo … 6=Fr) und News-Tage (FOMC, CPI, NFP) |
| Break-even ab x R / Zeit-Stop | Trade-Management |
| Kontrakte | Menge auch im Alert-JSON |
| Gefilterte Signale | Graues Label „x Grund" am Chart |

**Hinweis TradersPost:** Der Bracket beim Broker ist statisch. Greifen
Break-even oder Zeit-Stop, sendet die Strategie ein `exit` und der
Broker wird glattgestellt.
