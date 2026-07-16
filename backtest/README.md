# Backtest- & Validierungs-Toolchain

Da Marktdaten-APIs aus dieser Umgebung nicht erreichbar sind (geprüft:
Yahoo, Stooq, auch api.hyperliquid.xyz – alle per Netzwerk-Policy
gesperrt), läuft die Validierung zweistufig: Kursdaten kommen per CSV
(TradingView-Export **oder** Hyperliquid-Fetcher, lokal ausgeführt),
alles Weitere rechnet hier.

## 1a. Gold-Daten von Hyperliquid (`hyperliquid_fetch.py`)

Gold handelt auf Hyperliquid als HIP-3-Perpetual **`xyz:GOLD`** (trackt den
Spot-Goldpreis per Oracle, 24/7, bis 25x Hebel). Der Fetcher braucht nur
die Python-Standardbibliothek und keinen API-Key — **auf dem eigenen
Rechner ausführen** (aus der Claude-Sandbox ist die API gesperrt), die CSV
dann ins Repo committen:

```bash
python3 hyperliquid_fetch.py --list --dex xyz              # Märkte prüfen
python3 hyperliquid_fetch.py --coin xyz:GOLD --interval 5m --days 120 --out gold_5m.csv
python3 killzone_sweep_bos_backtest.py gold_5m.csv --preset ny-gold --tick 0.1 \
    --skip-weekends --cost-r 0.06
```

**Zum Hyperliquid-MCP-Server (`edkdev/hyperliquid-mcp`):** geprüft am
2026-07-16. Lokaler stdio-Server auf Basis des offiziellen Python-SDK mit
Candle-/Orderbuch-Tools, aber auch Live-Trading-Tools; verlangt zwingend
`HYPERLIQUID_PRIVATE_KEY`. Aus der Claude-Sandbox nutzlos, weil die Sperre
auf Netzwerk-Ebene liegt (SDK-Test: `ProxyError 403` gegen
`api.hyperliquid.xyz`). Für den reinen Datenabruf ist `hyperliquid_fetch.py`
die bessere Wahl: **braucht keinen Private Key**. Falls der MCP-Server
später lokal (Claude Desktop) fürs Trading eingesetzt wird: niemals den
Haupt-Wallet-Key hinterlegen, sondern eine separate Hyperliquid
API-Wallet mit begrenzten Rechten und kleinem Guthaben.

Gold-Besonderheiten, die die Flags abdecken:
- **`--skip-weekends`**: Der Perp handelt auch Sa/So, aber der
  Referenzmarkt (Spot/CME) ist zu — dünne Liquidität, Flash-Crash-Risiko
  (im Oktober 2025 fiel der HL-Gold-Perp in <1 Minute um $100). Kein Handel
  am Wochenende.
- **`--cost-r 0.06`**: Hyperliquid-Taker-Fee (~0,045 %) + Funding (8h) +
  Slippage wiegen bei engen Intraday-Stops schwerer als 1,25 $ Futures-
  Kommission.
- **`--preset ny-gold`** (08:30–11:00 NY, Range 18:00–08:30): Gold reagiert
  auf die 08:30-US-News; alternativ `--preset london` testen.

## 1b. Daten aus TradingView exportieren

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
