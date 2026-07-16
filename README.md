# TradingView-Strategien (Pine v6) – NQ / ES / Gold

Ziel des Repos: eine **profitable Intraday-Strategie rund um die New-York-
Killzone** finden, die realistisch eine **Prop-Firm-Challenge** (FTMO, Topstep
& Co.) bestehen kann. Alle Scripts laufen im TradingView Strategy Tester auf
1–5-Minuten-Charts.

| Datei | Setup | Status |
|---|---|---|
| `NY_Killzone_Sweep_BOS_Strategy.pine` | Liquidity Sweep + Break of Structure in der NY-Killzone, mit Prop-Risikomodul | **Hauptkandidat** – backtesten |
| `IB_ORB_VWAP_Strategy.pine` | IB 25%-Retracement + ORB-Breakout (VWAP-Filter) | Baseline / Vergleich |

---

## Strategie 1: NY Killzone – Liquidity Sweep + Break of Structure

**Datei:** `NY_Killzone_Sweep_BOS_Strategy.pine`
**Empfohlene Charts:** MNQ / MES (Micros!) oder MGC, 1–5 Minuten.

### Logik

1. **Liquiditäts-Level** (die "Zonen"): Previous Day High/Low und
   Overnight High/Low (18:00–09:30 NY). Dort liegen Stops – das sind die
   natürlichen Sweep-Ziele, mechanisch definiert statt subjektiv gezeichnet.
2. **Sweep in der Killzone (Std. 09:30–11:00 NY):** Preis stößt über/unter
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

- Die NY-Killzone hat objektiv das höchste Volumen und die höchste
  Volatilität des Tages – wenn es eine handelbare Intraday-Ineffizienz gibt,
  dann dort. Enge Zeitfenster reduzieren außerdem Chop-Trades.
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

## Testprotokoll (so prüfen wir Profitabilität seriös)

1. Script auf **MNQ 5m** laden, Standardeinstellungen, möglichst viel Historie
   ("Deep Backtesting" falls verfügbar). Slippage im Tester auf 1–2 Ticks
   stellen, Kommission prüfen.
2. Kennzahlen notieren: Netto-Profit, **Profit-Faktor (> 1,3)**, max.
   Drawdown (**< 6 %**), Trefferquote, Anzahl Trades (**> 100**),
   größter Tagesverlust (**< 2 %**).
3. Varianten einzeln vergleichen (immer nur 1 Änderung): Trend-Filter an/aus,
   nur PDH/PDL vs. nur Overnight, 1,5R vs. 2R vs. 3R, Killzone 09:30–11:00
   vs. 08:30–11:00.
4. Das Gleiche auf **MES** und **MGC** wiederholen – ein echter Edge sollte
   auf mindestens zwei Märkten nicht komplett zusammenbrechen.
5. Robustheits-Check: Parameter ±20 % verschieben. Kippt das Ergebnis von
   profitabel auf unprofitabel → überoptimiert, verwerfen.
6. Erst wenn 1–5 bestehen: 2–4 Wochen forward auf Demo/Paper laufen lassen,
   dann Challenge mit halber Positionsgröße starten.

**Prop-Challenge-Rechnung (Beispiel FTMO 50k):** Ziel 10 %, max. 5 %/Tag,
10 % gesamt. Mit 0,5 % Risiko/Trade, 2R-Ziel und ~40 % Trefferquote braucht
es im Erwartungswert ~50 Trades fürs Ziel (~5–8 Wochen bei 1–2 Trades/Tag) –
bei einem Worst-Case-Pfad, der die Limits mit den Script-Defaults praktisch
nicht reißen kann (Tagesstopp bei −2 %, Gesamtstopp bei −6 %).

## Hinweise

- Alle Zeiten sind Session-Inputs in New-York-Zeit und frei anpassbar.
- Kommission ist mit 1,25 $/Kontrakt vorbelegt – an Broker/Prop-Firm anpassen.
- Keine Anlage- oder Finanzberatung; Backtest-Ergebnisse garantieren keine
  zukünftige Performance.
