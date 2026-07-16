# TradingView-Strategien (Pine v6) – NQ / ES / Gold

Ziel des Repos: eine **profitable Intraday-Strategie** finden, die realistisch
eine **Prop-Firm-Challenge** (FTMO, Topstep & Co.) besteht – handelbar in der
London-Killzone (außerhalb der NY-Killzone), der NY-AM-Killzone oder der
NY-PM-Session. Alle Scripts laufen im TradingView Strategy Tester auf
1–5-Minuten-Charts; die Validierung läuft zusätzlich über die Python-Toolchain
in `backtest/`.

| Datei | Zweck | Status |
|---|---|---|
| `ORB_5min_Zarattini_Strategy.pine` | 5-Min-ORB nach Zarattini/Aziz 2023 – **publizierte Real-Daten-Evidenz für Netto-Profitabilität** (QQQ 2016–2023), plus Prop-Schutzschalter | **Evidenz-Kandidat** – auf QQQ/NQ verifizieren |
| `NY_Killzone_Sweep_BOS_Strategy.pine` | Liquidity Sweep + Break of Structure (Session-Presets: London / NY AM / NY PM / Custom), mit Prop-Risikomodul | Hypothesen-Kandidat – backtesten |
| `backtest/killzone_sweep_bos_backtest.py` | 1:1-Port der Sweep+BOS-Strategie für TradingView-CSV-Exporte | einsatzbereit |
| `backtest/prop_challenge_monte_carlo.py` | Monte-Carlo der Prop-Challenge (Pass-/Breach-Quote) | Ergebnisse in `backtest/results_monte_carlo.md` |
| `IB_ORB_VWAP_Strategy.pine` | IB 25%-Retracement + ORB-Breakout (VWAP-Filter) | Baseline / Vergleich |

## Strategie 0 (Evidenz-Kandidat): 5-Min-ORB nach Zarattini & Aziz

Die einzige Strategie hier mit **veröffentlichtem Real-Daten-Backtest**:
Zarattini & Aziz, *"Can Day Trading Really Be Profitable?"* (SSRN 4416622,
2023), testeten auf echten QQQ-5-Minuten-Daten 2016–2023: Erste 5-Min-Kerze
bullisch → Long am Open der zweiten Kerze (bärisch → Short), Stop am
Extrem der ersten Kerze, Take-Profit 10R oder End-of-Day-Exit, 1 % Risiko,
max. 4x Leverage, $0.0005/Aktie Kommission. **Ergebnis: ~675 % Gesamtrendite
netto vs. ~169 % QQQ Buy-and-Hold, annualisiertes Alpha ~33 %**, niedrige
Trefferquote (~25 %) bei großen Gewinnern.

`ORB_5min_Zarattini_Strategy.pine` setzt diese Regeln exakt um und ergänzt
die Prop-Schutzschalter (Tagesstopp, Max-DD-Halt, Standard 0,5 % Risiko).
Wichtige Einschränkungen, ebenso ehrlich: Die Studie endet 2023 (Regime kann
kippen), und das Profil mit niedriger Trefferquote erzeugt lange
Verluststrecken – die Monte-Carlo unten zeigt, dass es für 6-%-Trailing-
Limits nur mit 0,25–0,5 % Risiko und aktivem 10R-Target robust ist
(87,8 % Pass-Quote). Erster Schritt daher: Script auf QQQ 5m laden und
prüfen, ob der Strategy Tester die Paper-Größenordnung reproduziert; danach
auf NQ/MNQ übertragen.

---

## Strategie 1: Killzone – Liquidity Sweep + Break of Structure

**Datei:** `NY_Killzone_Sweep_BOS_Strategy.pine`
**Empfohlene Charts:** MNQ / MES (Micros!) oder MGC, 1–5 Minuten.

### Zeitfenster (Preset-Input, Zeiten in New York)

| Preset | Entry-Fenster | Liquiditäts-Range davor |
|---|---|---|
| **London Killzone** (Standard) | 02:00–05:00 | Asia 18:00–02:00 |
| NY AM Killzone | 09:30–11:00 | Overnight 18:00–09:30 |
| NY PM Session | 13:30–15:30 | AM-Session 09:30–13:30 |
| Custom | frei | frei |

Damit lässt sich derselbe Setup-Kern **außerhalb der NY-Killzone** (London)
und innerhalb (NY AM/PM) fahren und direkt vergleichen.

### Logik

1. **Liquiditäts-Level** (die "Zonen"): Previous Day High/Low und
   High/Low der Liquiditäts-Range vor dem Fenster. Dort liegen Stops – das
   sind die natürlichen Sweep-Ziele, mechanisch definiert statt subjektiv
   gezeichnet.
2. **Sweep im Entry-Fenster:** Preis stößt über/unter
   ein Level, schließt aber wieder dahinter (Stop-Run / Swing Failure).
3. **Bestätigung per Break of Structure:** Erst wenn der Preis danach das
   letzte Pivot-Tief (Short) bzw. Pivot-Hoch (Long) per **Schlusskurs**
   bricht, wird eingestiegen. Kein BOS innerhalb von N Bars → Setup verfällt.
4. **Risiko:** Stop hinter dem Sweep-Extrem (+ Tick-Offset), Take-Profit als
   R-Multiple (Std. **2R**), optional Break-Even ab +1R.
5. **Trend-Filter (optional, Std. an):** Trades nur in Richtung des
   1h-EMA(50) – Sweep-Reversals zurück in den übergeordneten Trend.

### Prop-Firm-Risikomodul (eingebaut)

- Positionsgröße aus **Risiko-% pro Trade** (Std. 0,5 %) oder fix.
- **Tages-Verlustlimit** (Std. 2 %): Handel stoppt bis zum nächsten Tag –
  bewusst deutlich unter dem 5 %-Limit vieler Prop-Firmen.
- **Max. Trailing-Drawdown** (Std. 6 %): Strategie stoppt komplett.
- Max. **2 Trades/Tag**, alle Positionen werden 15:55–16:00 NY glattgestellt
  (kein Overnight-Risiko – bei vielen Prop-Firmen ohnehin Pflicht).
- Status-Tabelle im Chart: Tages-P&L, Trades, Drawdown, Halt-Status.

> **Wichtig zur Positionsgröße:** Auf Micro-Kontrakten (MNQ/MES/MGC) testen.
> Auf den großen Kontrakten (NQ/ES/GC) ist bei 0,5 % Risiko auf einem
> 50k-Konto die Stop-Distanz oft größer als das Risiko-Budget → das Script
> lässt den Trade dann korrekt aus (0 Kontrakte).

---

## Strategie 2: IB 25% Retracement + ORB Breakout (VWAP)

**Datei:** `IB_ORB_VWAP_Strategy.pine` – Details siehe Kommentarkopf im Script.
Kurzfassung: VWAP am 9:30-Open verankert, Initial Balance 09:30–10:30,
Limit-Entry am 25%-Retracement (Stop 50 %, Target IB-Extrem, 1:1) bzw.
Stop-Order-Breakout über/unter der IB. Dient als Baseline zum Vergleich.

---

## Einschätzung: Warum dieser Ansatz – und wo die Risiken liegen

**Was für den Ansatz spricht:**

- Enge, feste Zeitfenster mit klarem Liquiditätskontext (London-Open sweept
  die Asia-Range, NY-Open die Overnight-Range) sind genau die Phasen, in
  denen Stop-Runs systematisch auftreten – und sie reduzieren Chop-Trades.
  Über die Presets lässt sich messen, ob der Edge außerhalb der NY-Killzone
  (London) oder innerhalb stärker ist, statt das zu raten.
- Sweep + BOS ist die **mechanisierbare** Version von "Supply/Demand +
  Break of Structure": Das Level ist objektiv (PDH/PDL, Overnight-Range),
  der Trigger ist objektiv (Schlusskurs bricht Pivot). Subjektiv gezeichnete
  Zonen lassen sich nicht ehrlich backtesten – das hier schon.
- Mit 2R-Zielen reicht eine Trefferquote um ~40 % für Profitabilität.
  Eine Prop-Challenge ist primär ein **Risikomanagement-Problem**, kein
  Renditeproblem: 8–10 % Ziel bei 5 %/10 % Limits heißt, der Drawdown-Pfad
  entscheidet, nicht der Durchschnittsgewinn. Genau dafür ist das Risikomodul da.

**Wo ich skeptisch bin (ehrlich):**

- "Killzone + Smart-Money-Konzepte" ist kein garantierter Edge – die
  Profitabilität muss der Backtest zeigen, nicht die Story dahinter.
- Overfitting ist der Hauptgegner: viele Parameter (Session, Pivot-Länge,
  R-Ziel, Filter) → man findet immer eine Kombination, die rückwirkend
  funktioniert. Deshalb striktes Testprotokoll (unten).
- 60–90 Tage Intraday-Historie (TradingView-Standard ohne Premium-Daten)
  sind wenig. Mindestens 200+ Trades anstreben, sonst ist das Ergebnis Rauschen.
- Gold verhält sich anders als NQ/ES (News-getrieben um 08:30, dünnere
  US-Session) – gleiche Regeln, aber separat testen, Killzone ggf. 08:30–11:00.

## Monte-Carlo-Ergebnis: Die Messlatte ist beziffert

20 000 simulierte FTMO-Challenges pro Szenario
(`backtest/results_monte_carlo.md`, Details dort):

- **2R-Ziel braucht ≥ 45 % Trefferquote** (entschiedene Trades) → 83 %
  Pass-Quote bei 0,5 % Risiko, 94 % bei 1 %. Bei 40 %/2R nur Break-Even.
- **3R-Ziel braucht nur ≥ 40 % Trefferquote** → 98 % Pass-Quote.
- **Die Risiko-Defaults sind strukturell sicher:** Breach-Wahrscheinlichkeit
  ≤ 2,4 % bei 0,5 % Risiko; das 5-%-Tageslimit ist mit max. 2 Trades ×
  0,5 % Risiko mathematisch unerreichbar.
- Negative Erwartung ist mit keinem Money-Management rettbar – der Edge
  muss aus dem Setup kommen, das Risikomodul sichert ihn nur ab.

## Testprotokoll (so prüfen wir Profitabilität seriös)

1. **Entweder** Script im TradingView Strategy Tester laden (MNQ 5m,
   Slippage 1–2 Ticks) **oder** Chartdaten als CSV exportieren und
   `backtest/killzone_sweep_bos_backtest.py` laufen lassen (siehe
   `backtest/README.md`) – das erzeugt zusätzlich die R-Multiples für die
   Monte-Carlo.
2. Kennzahlen gegen die Messlatte halten: **Profit-Faktor > 1,3**,
   Trefferquote **≥ 45 % bei 2R** (bzw. ≥ 40 % bei 3R), max. Drawdown
   **< 6 %**, Anzahl Trades **> 100**, größter Tagesverlust **< 2 %**.
3. Alle drei Session-Presets vergleichen (London / NY AM / NY PM), dann
   Varianten einzeln (immer nur 1 Änderung): Trend-Filter an/aus, nur
   PDH/PDL vs. nur Range, 1,5R vs. 2R vs. 3R.
4. Das Gleiche auf **MES** und **MGC** wiederholen – ein echter Edge sollte
   auf mindestens zwei Märkten nicht komplett zusammenbrechen.
5. Robustheits-Check: Parameter ±20 % verschieben. Kippt das Ergebnis von
   profitabel auf unprofitabel → überoptimiert, verwerfen. Out-of-Sample:
   letzte 30 % der Daten nur einmal am Ende testen.
6. Echte Trade-Verteilung in die Monte-Carlo einspeisen
   (`prop_challenge_monte_carlo.py --csv trades_out.csv`) → tatsächliche
   Pass-Wahrscheinlichkeit. Erst bei > 80 %: 2–4 Wochen forward auf Demo,
   dann Challenge mit 0,5 % Risiko starten (nach +3 % Puffer auf 1 % erhöhen
   → mediane Challenge-Dauer sinkt von ~63 auf ~31 Handelstage).

## Hinweise

- Alle Zeiten sind Session-Inputs in New-York-Zeit und frei anpassbar.
- Kommission ist mit 1,25 $/Kontrakt vorbelegt – an Broker/Prop-Firm anpassen.
- Keine Anlage- oder Finanzberatung; Backtest-Ergebnisse garantieren keine
  zukünftige Performance.
