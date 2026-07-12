# TradingView Scripts: IB-Zonen, NY Opening Range & IB/ORB-Strategie (Pine v6)

## Indikator: NASDAQ IB-Zonen + NY Opening Range

**Datei:** `IB_ORB_Zones_Indicator.pine`
**Empfohlener Chart:** NQ/MNQ (oder QQQ), 1–5-Minuten-Timeframe.

Reines Visualisierungs-Tool (Overlay-Indikator) als Grundlage für die
Entwicklung der NASDAQ-Strategie – zeigt pro Handelstag:

1. **Initial Balance (IB)** als horizontale Level: **IB Hoch, IB75,
   IB50, IB25, IB Tief** (Quartile der IB-Range).
   - IB-Session frei einstellbar (Standard 09:30–10:30 New York).
   - Wahlweise live während der Bildung oder erst nach IB-Abschluss.
   - Quartils-Zonen optional eingefärbt (oberes Viertel grün, unteres
     rot, Mitte neutral), Farben anpassbar.
2. **NY Opening Range (ORB)** grafisch als Box (Standard: erste
   15 Minuten, 09:30–09:45, frei einstellbar). ORB Hoch/Tief laufen
   nach Range-Ende optional als Linien weiter.

Weitere Einstellungen: Anzeigefenster (bis wann die Level nach rechts
laufen, Standard 16:00 NY), Anzahl der dargestellten Tage (1–20),
Beschriftungen mit Preisangabe an/aus. Enthaltene **Alerts**: Bruch von
ORB Hoch/Tief sowie IB Hoch/Tief nach Abschluss der jeweiligen Range.

---

## Strategie: IB Quartils-Reversal (ORB-Ausbruch → Rejection → 25/75-Bruch)

**Datei:** `IB_ORB_Quarter_Reversal_Strategy.pine`
**Empfohlener Chart:** NQ/MNQ (oder QQQ), 1–5-Minuten-Timeframe.

Setzt das im Chat besprochene Setup ("Spike → Konsolidierung im
äußeren Viertel → Break of Structure → Reversal zum Ursprung des
Spikes") direkt auf die IB/ORB-Zonen um und backtestet es im Strategy
Tester. Zeichnet dieselben IB25/50/75- und ORB-Level wie der reine
Zonen-Indikator.

**Setup-Logik:**

1. **Voraussetzung:** Der Kurs muss die NY Opening Range (ORB) einmal
   nach oben oder unten verlassen haben (Ausbruch/"Spike" über ORB
   Hoch bzw. unter ORB Tief).
2. Der Kurs kehrt in die IB-Range zurück und bleibt im äußeren Viertel
   hängen (zwischen IB-Tief und IB25 nach einem Ausbruch nach unten,
   bzw. zwischen IB75 und IB-Hoch nach einem Ausbruch nach oben) – er
   "rejected" also am ORB-Extrem. Das Setup wird verworfen, sobald der
   Kurs die IB-Mittellinie erreicht oder das IB-Extrem selbst bricht.
3. Erst wenn eine Kerze **auf Schlusskurs-Basis** über IB25 (long)
   bzw. unter IB75 (short) schließt ("Break of Structure"), gilt das
   Setup als bestätigt:
   - **Long:** Einstieg long, Stop am Tages-Extrem des Spikes
     (tiefster Punkt seit IB-Beginn, mit Tick-Puffer), Ziel IB75.
   - **Short:** Einstieg short, Stop am Tages-Extrem des Spikes
     (höchster Punkt seit IB-Beginn, mit Tick-Puffer), Ziel IB25.
4. Kein neuer Einstieg nach einer einstellbaren Uhrzeit (Standard
   18:00 deutsche Zeit), max. Trades pro Tag einstellbar (Standard 1).
5. Optionales Glattstellen zum NY-Handelsschluss (15:55–16:00).

Alle Zeiten, der SL-Tick-Puffer, das Invalidierungs-Verhalten sowie
alle Darstellungsoptionen sind über Inputs anpassbar. Enthält Alerts
für Long- und Short-Einstieg.

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
