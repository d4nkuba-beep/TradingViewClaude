# TradingView-Strategien (Pine v6)

## Übersicht

| Datei | Strategie |
|---|---|
| `IB_ORB_VWAP_Strategy.pine` | IB 25% Retracement + ORB Breakout (VWAP-Filter) |
| `ORB_Spike_Reversal_RSI_Strategy.pine` | ORB Spike-Reversal + RSI (Fast-Spike-Setup) |

---

# ORB Spike-Reversal + RSI Strategie

Reversal-Strategie für **NQ/MNQ (Nasdaq)** oder **ES/MES (S&P)** auf Basis
des "Fast Spike"-Setups: Trades entstehen **außerhalb der Opening Range
(ORB)**, wenn ein schneller Spike den Markt überdehnt und der **RSI** ein
Extrem anzeigt.

**Datei:** `ORB_Spike_Reversal_RSI_Strategy.pine`
**Empfohlener Chart:** NQ/MNQ oder ES/MES, 1–5-Minuten-Timeframe.

## Das Setup (aus dem Referenzbild)

1. **ORB-Kennzeichnung:** Opening Range 09:30–10:00 New York wird als Box
   mit Mittellinie markiert und über den Tag verlängert.
2. **Fast Spike:** Nach der ORB spikt der Preis schnell **unter das
   ORB-Tief** (bzw. über das ORB-Hoch) – Mindestdistanz in ATR, Ausbruch
   innerhalb weniger Bars. Der Spike wird gelb markiert.
3. **RSI-Filter:** Der Spike zählt nur, wenn der RSI extrem ist –
   überverkauft (≤ 30) für ein Long-Reversal, überkauft (≥ 70) für ein
   Short-Reversal. Bei extremem RSI ist ein Reversal wahrscheinlich.
4. **Entry – Break of Structure (BOS):** Nach dem Spike-Extrem wird das
   erste Pivot-Hoch (Long) bzw. Pivot-Tief (Short) als Struktur markiert.
   Eine Stop-Order hinter dieser Struktur löst den Entry aus, sobald sie
   gebrochen wird.
5. **Stop-Loss:** am **Spike-Extrem** ("stoploss placement: at the
   extreme"), mit einstellbarem Tick-Offset.
6. **Take-Profit:** am **Ursprung des Spikes** ("target: origin of the
   spike") – dem Level, von dem der schnelle Spike gestartet ist.
   Alternativ wählbar: ORB-Mitte, Gegenseite der ORB oder R-Multiple.

## Darstellung auf dem Chart

- **ORB-Box** (aqua) mit Mittellinie, über den Tag verlängert.
- **Spike-Markierung** (gelbe Box + Label mit RSI-Wert).
- **BOS-Linie** (grau gestrichelt) mit "BOS"-Label am Pivot.
- **Trade-Boxen** wie beim TradingView-Positionstool: grüne Box
  Entry→TP, rote Box Entry→SL, die mit der offenen Position mitlaufen.
- Ziel-Linie (blau, Spike-Ursprung) und Stop-Referenz (rot gepunktet,
  Spike-Extrem) während des aktiven Setups.

## A/D-Filter (Accumulation/Distribution)

Optionaler Zusatzfilter (Input **„A/D-Bestätigung"**, Standard: Aus) für
sauberere Reversal-Trades:

- **Divergenz am Spike:** Der Preis macht am Spike ein neues Extrem, die
  A/D-Linie bestätigt es nicht (kein neues A/D-Tief/-Hoch im Lookback,
  Standard 30 Bars) → Akkumulation bzw. Distribution gegen den Spike.
  Nur dann wird das Setup überhaupt aktiviert.
- **A/D-Steigung beim BOS:** Die A/D-Linie muss beim Armieren des
  BOS-Entries bereits in Trade-Richtung drehen (Standard: 5 Bars).
- **Beide:** kombiniert beide Bedingungen.

Im Python-Backtester per `--ad-mode aus|divergenz|slope|beide`;
`--compare-ad` testet alle vier Modi auf denselben Daten gegeneinander.

## Lokaler M1-Backtest (Python)

`backtest/orb_spike_reversal_backtest.py` ist ein 1:1-Port der
Pine-Logik inkl. Order-Semantik des TradingView-Broker-Emulators
(Stop-Entries füllen frühestens auf der Folge-Bar, SL/TP erst ab der Bar
nach dem Fill aktiv, SL-vor-TP bei Berührung beider in einer Bar).

```bash
pip install pandas numpy

# Logik-Validierung auf synthetischen NQ-1m-Daten (keine echte Performance!)
python3 backtest/orb_spike_reversal_backtest.py --synth 60 --symbol NQ

# Echter Backtest: 1m-Daten als CSV (z. B. TradingView-Chart-Export,
# Spalten: time, open, high, low, close [, volume])
python3 backtest/orb_spike_reversal_backtest.py --csv nq_1m.csv --symbol NQ
```

Parameter wie im Pine-Script einstellbar (`--tp-mode`, `--rsi-os`,
`--rsi-ob`, `--spike-atr`, `--min-rr`, `--max-trades`); Trades lassen
sich mit `--trades-csv pfad.csv` exportieren.

## Schutzmechanismen

- Setup verfällt nach X Bars ohne Entry (Standard 40) oder wenn der
  Preis das Target erreicht, bevor der BOS-Entry ausgelöst wurde.
- Min. CRV-Filter (Standard 0.5): Trades mit zu schlechtem
  Reward/Risk-Verhältnis werden nicht armiert.
- Max. Trades pro Tag (Standard 2), Entry-Fenster 10:00–15:00 NY.
- Alle Positionen werden 15:55–16:00 New York glattgestellt.

---

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
