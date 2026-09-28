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

# ORB Fakeout Fade GOLD M5 (v1.2)

**Datei:** `ORB_Fakeout_Fade_GOLD_M5.pine` · **Chart:** GC1! / MGC1!, 5 Minuten
· **Alert-Nachricht:** `{{strategy.order.alert_message}}` (TradersPost)

- **Setup A – Fakeout-Fade:** Ausbruch aus der Opening Range scheitert
  innerhalb von `k` Kerzen → Einstieg zurück in die Range, SL hinter dem
  Fakeout-Extrem, Ziel Range-Mitte / Gegenseite / RR.
- **Setup B – Breakout-Akzeptanz:** `N` Closes außerhalb → Continuation.

## Neu in v1.2

Alle neuen Filter stehen per Default auf **aus** – das Default-Ergebnis
entspricht v1.1. So kannst du jeden Filter einzeln zuschalten und im
Strategy Tester gegen die Baseline vergleichen.

| Filter / Option | Wirkung | Begründung |
|---|---|---|
| **A: Min. RR** | Kein Fade, wenn Ziel/Risiko < x | Bei „Ziel = Mitte" und großem Fakeout liegt das RR oft bei 0,3–0,5 – der größte Schwachpunkt von v1.1 |
| **Min. Rückkehr in Range** | Close muss x·Range innerhalb liegen | 1 Tick zurück in der Range ist oft noch kein gescheiterter Ausbruch |
| **Range-Größe / Tages-ATR** | Nur handeln, wenn OR zwischen min·ATR und max·ATR liegt | Zu enge Ranges = Rauschen, zu weite = Stop zu groß (OR/ATR ist der Standard-Filter für ORB) |
| **A: VWAP-Seite** | Short-Fade nur mit Close < VWAP (Long umgekehrt) | Bestätigung, dass die Auktion den Ausbruch abgelehnt hat |
| **B: VWAP-Richtung** | Continuation nur mit dem VWAP | Klassischer ORB+VWAP-Bias |
| **A: schwacher Ausbruch (Volumen)** | Fade nur, wenn Ausbruchsvolumen ≤ x·Durchschnitt | Ausbrüche ohne Beteiligung scheitern häufiger |
| **B: nur mit Volumen** | Continuation nur mit Volumen ≥ x·Durchschnitt (z. B. 1,2) | Volumen bestätigt echte Ausbrüche |
| **A: Liquidity-Sweep** | Fakeout muss Vortageshoch/-tief oder Overnight-Hoch/-Tief nehmen | Stop-Run über ein Key-Level → gefangene Breakout-Trader als Treibstoff |
| **Handelstage / Sperrdaten** | Wochentage wählen, News-Tage (FOMC, CPI, NFP) sperren | Pine hat keinen Wirtschaftskalender; an News-Tagen laufen Ausbrüche eher durch |
| **Break-even ab x R** | SL auf Einstieg + 1 Tick | Fakeouts, die funktionieren, drehen meist schnell |
| **Zeit-Stop nach x Kerzen** | Trade schließen, wenn er nicht läuft | wie oben |
| **Kontrakte** | Menge wird auch im Alert-JSON übergeben | v1.1 hatte `quantity: 1` fest im JSON |
| **Gefilterte Signale** | Graues Label „x Grund" am Chart | Man sieht, welcher Filter welchen Trade verhindert |
| `use_bar_magnifier` | Genauere Fills, wenn SL und TP in derselben Kerze liegen | Nur mit TradingView-Premium aktiv |

## Empfohlene Test-Reihenfolge

1. Baseline v1.2 mit Default-Einstellungen (= v1.1) notieren.
2. **Min. RR = 1,0** → meist der größte Effekt.
3. **Range/ATR** (z. B. 0,15–0,60) → schließt Extremtage aus.
4. **Rückkehr-Tiefe 0,1**, dann **Liquidity-Sweep** und **VWAP** einzeln.
5. **Break-even 1R** bzw. **Zeit-Stop 6–9 Kerzen**.
6. Gold-spezifisch: Opening Range auf die COMEX-Eröffnung **08:20–08:35**
   (Entry-Fenster z. B. 08:35–10:30) legen und gegen 09:30 vergleichen –
   um 08:20 ist das Volumen in GC typischerweise am höchsten.

Nur Filter behalten, die Profit-Faktor **und** Drawdown verbessern, ohne
die Trade-Anzahl zu stark zu senken (Overfitting-Gefahr). Gegenprobe
immer in einem Zeitraum machen, der nicht zum Optimieren genutzt wurde.

**Hinweis TradersPost:** Der Bracket beim Broker ist statisch. Greifen
Break-even oder Zeit-Stop, sendet die Strategie ein `exit` und der
Broker wird glattgestellt.
