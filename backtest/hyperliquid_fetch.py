#!/usr/bin/env python3
"""Kerzendaten von Hyperliquid laden (z. B. Gold-Perp "xyz:GOLD") -> CSV.

Nur Python-Standardbibliothek, kein API-Key noetig. Die Ausgabe-CSV passt
direkt in killzone_sweep_bos_backtest.py.

HINWEIS: Aus der Claude-Sandbox ist api.hyperliquid.xyz netzwerkseitig
gesperrt - dieses Script auf dem eigenen Rechner ausfuehren und die CSV
ins Repo legen (oder committen), dann kann der Backtest hier laufen.

Beispiele:
  python3 hyperliquid_fetch.py --list --dex xyz          # Maerkte anzeigen
  python3 hyperliquid_fetch.py --coin xyz:GOLD --interval 5m --days 120 \
      --out gold_5m.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request

API = "https://api.hyperliquid.xyz/info"

INTERVAL_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}
MAX_CANDLES_PER_REQ = 4500  # API-Limit ~5000, mit Puffer


def post(payload: dict) -> object:
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def list_markets(dex: str) -> None:
    meta = post({"type": "meta", "dex": dex} if dex else {"type": "meta"})
    for a in meta.get("universe", []):
        flags = []
        if a.get("isDelisted"):
            flags.append("DELISTED")
        print(f"{a['name']:>20}  maxLev={a.get('maxLeverage', '?'):>3} "
              f"szDecimals={a.get('szDecimals', '?')} {' '.join(flags)}")


def fetch_candles(coin: str, interval: str, days: int) -> list[dict]:
    step = INTERVAL_MS[interval]
    now = int(time.time() * 1000)
    start = now - days * 86_400_000
    window = MAX_CANDLES_PER_REQ * step
    seen: dict[int, dict] = {}
    t0 = start
    while t0 < now:
        t1 = min(t0 + window, now)
        batch = post({"type": "candleSnapshot",
                      "req": {"coin": coin, "interval": interval,
                              "startTime": t0, "endTime": t1}})
        if not isinstance(batch, list):
            sys.exit(f"Unerwartete Antwort: {batch!r}")
        for c in batch:
            seen[int(c["t"])] = c
        print(f"  {time.strftime('%Y-%m-%d', time.gmtime(t0/1000))} -> "
              f"{time.strftime('%Y-%m-%d', time.gmtime(t1/1000))}: "
              f"{len(batch)} Kerzen (gesamt {len(seen)})")
        t0 = t1
        time.sleep(0.3)  # freundlich zum Rate-Limit
    return [seen[t] for t in sorted(seen)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coin", default="xyz:GOLD",
                    help="Markt, z. B. xyz:GOLD (HIP-3), BTC, ETH")
    ap.add_argument("--interval", default="5m", choices=INTERVAL_MS)
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--out", default="gold_5m.csv")
    ap.add_argument("--list", action="store_true", help="Maerkte anzeigen")
    ap.add_argument("--dex", default="xyz",
                    help="HIP-3-DEX-Namespace fuer --list ('' = Haupt-Perps)")
    a = ap.parse_args()

    if a.list:
        list_markets(a.dex)
        return

    print(f"Lade {a.coin} {a.interval}, {a.days} Tage ...")
    candles = fetch_candles(a.coin, a.interval, a.days)
    if not candles:
        sys.exit("Keine Kerzen erhalten - Coin-Name pruefen (--list --dex xyz).")
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        for c in candles:
            w.writerow([int(c["t"]) // 1000, c["o"], c["h"], c["l"], c["c"], c["v"]])
    first = time.strftime("%Y-%m-%d %H:%M", time.gmtime(candles[0]["t"] / 1000))
    last = time.strftime("%Y-%m-%d %H:%M", time.gmtime(candles[-1]["t"] / 1000))
    print(f"{len(candles)} Kerzen -> {a.out} ({first} bis {last} UTC)")
    print("Backtest:")
    print(f"  python3 killzone_sweep_bos_backtest.py {a.out} "
          f"--preset ny-gold --tick 0.1 --skip-weekends")


if __name__ == "__main__":
    main()
