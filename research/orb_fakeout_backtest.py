"""Python-Nachbau der Pine-Strategie 'ORB Fakeout Fade GOLD' fuer Parameter-Tests.

Semantik wie TradingView mit process_orders_on_close=true:
- Signale/Entries auf dem Close der Signalkerze (+ Slippage)
- Stop/Limit ab der naechsten Kerze intrabar; beide in einer Kerze ->
  TV-Pfad: Open naeher am High => O-H-L-C, sonst O-L-H-C
- Zeit-Stop / EOD auf dem Close

Daten: JSON im Format {"bars": [{"t": unix_sec, "o", "h", "l", "c", "v"}]}
(z. B. TradingView-Export). tpMode "MaxMitteRR" = Pine "Mitte/RR max".

Beispiel:
    python3 orb_fakeout_backtest.py gc5.json 5 0.1
"""
import json, math, datetime as dt
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def hm(x):
    return x.hour * 100 + x.minute


def in_sess(h, s):  # s = (start, end) HHMM, end exklusiv, overnight moeglich
    a, b = s
    return a <= h < b if a < b else (h >= a or h < b)


def load(path, bs):
    bars = json.load(open(path))["bars"]
    out = []
    for x in bars:
        t = dt.datetime.fromtimestamp(x["t"], NY)
        tc = dt.datetime.fromtimestamp(x["t"] + bs * 60, NY)
        tday = (t + dt.timedelta(hours=6)).date()  # Futures-Tag startet 18:00
        out.append(dict(t=t, hm=hm(t), chm=hm(tc), day=tday, date=t.date(),
                        dow=t.isoweekday(), o=x["o"], h=x["h"], l=x["l"],
                        c=x["c"], v=x["v"]))
    return out


def daily_from(bars):
    """Futures-Tageskerzen (18:00-17:00) -> {tday: (atr14 Vortag, pdh, pdl)}"""
    days = {}
    for b in bars:
        d = days.setdefault(b["day"], [b["h"], b["l"], b["c"]])
        d[0] = max(d[0], b["h"]); d[1] = min(d[1], b["l"]); d[2] = b["c"]
    keys = sorted(days)
    res, atr, pc = {}, None, None
    hist = []
    for k in keys:
        h, l, c = days[k]
        tr = h - l if pc is None else max(h - l, abs(h - pc), abs(l - pc))
        hist.append(tr)
        # Wilder RMA wie ta.atr
        if len(hist) == 14:
            atr = sum(hist) / 14
        elif len(hist) > 14:
            atr = (atr * 13 + tr) / 14
        res[k] = (atr, h, l)
        pc = c
    out = {}
    for i, k in enumerate(keys):
        if i == 0:
            continue
        pa, ph, pl = res[keys[i - 1]]
        out[k] = (pa, ph, pl)
    return out


DEF = dict(
    orS=(930, 945), entS=(945, 1130), flat=1200, onS=(1800, 930),
    useFade=True, kBars=3, bufT=2, maxExc=1.0, depth=0.0, tpMode="Mitte",
    rrA=1.5, useCont=False, nAcc=2, rrB=1.5,
    minRR=0.0, useAtr=False, atrMin=0.15, atrMax=0.6, useVwA=False,
    useVwB=False, useVolA=False, volA=1.5, useVolB=False, volB=1.2,
    volLen=20, useSwp=False, days="12345", beR=0.0, maxBars=0,
    # neue Ideen v1.3
    slMode="Extrem",   # "Extrem" | "Kerze" (SL hinter Signalkerze, max Extrem)
    tp2=False,         # Teil-TP: halbe Pos an Mitte, Rest Gegenseite (nur Report)
    reentry=False,     # nach Stop-out 2. Fade in Gegenrichtung erlauben
    tick=0.1, slipT=1, comm=0.0,
)


def run(bars, daily, p=None, collect=False):
    P = dict(DEF); P.update(p or {})
    tk = P["tick"]; slip = P["slipT"] * tk
    trades = []
    # rolling
    vols = []
    vw_num = vw_den = 0.0
    cur_day = None
    orH = orL = None; active = False; brk = 0; brkBar = None; ext = None
    bVol = None; traded = False; upC = dnC = 0; nTr = 0
    onH = onL = None; prev_inON = False; prev_inOR = False
    pos = None  # dict(side, entry, sl, tp, bar, risk0, be)
    for i, b in enumerate(bars):
        # VWAP (Reset Futures-Tag)
        if b["day"] != cur_day:
            cur_day = b["day"]; vw_num = vw_den = 0.0
        hlc3 = (b["h"] + b["l"] + b["c"]) / 3
        vw_num += hlc3 * b["v"]; vw_den += b["v"]
        vw = vw_num / vw_den if vw_den else b["c"]
        volAvg = (sum(vols[-P["volLen"]:]) / P["volLen"]
                  if len(vols) >= P["volLen"] else None)
        vols.append(b["v"])

        # ---- 1) offene Position: intrabar Stop/Limit (Orders von vorher)
        if pos is not None and i > pos["bar"]:
            s = pos["side"]; sl = pos["sl"]; tp = pos["tp"]
            o, h, l = b["o"], b["h"], b["l"]
            ex = None
            if s == 1:
                if o <= sl: ex = (o - slip, "SL")
                elif o >= tp: ex = (o, "TP")
                else:
                    hitS = l <= sl; hitT = h >= tp
                    if hitS and hitT:
                        ex = (tp, "TP") if (h - o) < (o - l) else (sl - slip, "SL")
                    elif hitS: ex = (sl - slip, "SL")
                    elif hitT: ex = (tp, "TP")
            else:
                if o >= sl: ex = (o + slip, "SL")
                elif o <= tp: ex = (o, "TP")
                else:
                    hitS = h >= sl; hitT = l <= tp
                    if hitS and hitT:
                        ex = (tp, "TP") if (o - l) < (h - o) else (sl + slip, "SL")
                    elif hitS: ex = (sl + slip, "SL")
                    elif hitT: ex = (tp, "TP")
            if ex:
                close_pos(trades, pos, ex[0], ex[1], b, P)
                pos = None

        # ---- 2) Session-Logik (Script auf dem Close)
        inOR = in_sess(b["hm"], P["orS"]); inEnt = in_sess(b["hm"], P["entS"])
        inON = in_sess(b["hm"], P["onS"])
        if inON and not prev_inON:
            onH, onL = b["h"], b["l"]
        elif inON:
            onH = max(onH, b["h"]); onL = min(onL, b["l"])
        orNew = inOR and not prev_inOR; orEnd = (not inOR) and prev_inOR
        prev_inON, prev_inOR = inON, inOR
        if orNew:
            orH, orL = b["h"], b["l"]; active = False; brk = 0; brkBar = None
            ext = None; bVol = None; traded = False; upC = dnC = 0; nTr = 0
        elif inOR:
            orH = max(orH, b["h"]); orL = min(orL, b["l"])
        if orEnd:
            active = True
        if orH is None:
            continue
        rng = orH - orL; mid = (orH + orL) / 2
        dinfo = daily.get(b["day"], (None, None, None))
        atrD, pdh, pdl = dinfo
        sizeOk = (not P["useAtr"]) or (atrD is not None and
                  P["atrMin"] * atrD <= rng <= P["atrMax"] * atrD)
        dayOk = str(b["dow"]) in P["days"]

        # ---- Setup A
        if active and not traded and brk != 9 and rng > 0 and pos is None:
            if brk == 0:
                if b["h"] > orH and b["l"] < orL: brk = 9
                elif b["h"] > orH:
                    brk, brkBar, ext, bVol = 1, i, b["h"], b["v"]
                elif b["l"] < orL:
                    brk, brkBar, ext, bVol = -1, i, b["l"], b["v"]
            elif brk == 1:
                ext = max(ext, b["h"]); bVol = max(bVol, b["v"])
            elif brk == -1:
                ext = min(ext, b["l"]); bVol = max(bVol, b["v"])
            c = b["c"]
            failU = brk == 1 and c < orH - P["depth"] * rng
            failD = brk == -1 and c > orL + P["depth"] * rng
            if failU or failD:
                exc = ext - orH if failU else orL - ext
                if P["slMode"] == "Kerze":
                    sl = (b["h"] + P["bufT"] * tk) if failU else (b["l"] - P["bufT"] * tk)
                else:
                    sl = ext + P["bufT"] * tk if failU else ext - P["bufT"] * tk
                if P["tpMode"] == "Mitte": tp = mid
                elif P["tpMode"] == "Gegenseite": tp = orL if failU else orH
                else: tp = c + P["rrA"] * (c - sl)
                if P["tpMode"] == "MaxMitteRR":  # weiteres Ziel von Mitte / RR
                    r_tp = c + P["rrA"] * (c - sl)
                    tp = min(mid, r_tp) if failU else max(mid, r_tp)
                rr = abs(tp - c) / max(abs(c - sl), 1e-9)
                okT = (c > mid if P["tpMode"] in ("Mitte",) else c > orL) if failU else \
                      (c < mid if P["tpMode"] == "Mitte" else c < orH)
                swU = (pdh is not None and pdh > orH and ext > pdh) or (onH is not None and onH > orH and ext > onH)
                swD = (pdl is not None and pdl < orL and ext < pdl) or (onL is not None and onL < orL and ext < onL)
                ok = (exc <= P["maxExc"] * rng and okT and
                      (P["minRR"] <= 0 or rr >= P["minRR"]) and sizeOk and dayOk and
                      (not P["useVwA"] or (c < vw if failU else c > vw)) and
                      (not P["useVolA"] or (volAvg and bVol <= P["volA"] * volAvg)) and
                      (not P["useSwp"] or (swU if failU else swD)))
                if P["useFade"] and inEnt and ok:
                    side = -1 if failU else 1
                    e = c + side * slip
                    pos = dict(side=side, entry=e, sl=sl, tp=tp, bar=i,
                               risk0=abs(e - sl), be=False, kind="A",
                               date=b["date"], mid=mid, orH=orH, orL=orL)
                    traded = True; nTr += 1
                brk = 9
            elif brk in (1, -1) and i - brkBar >= P["kBars"]:
                brk = 9

        # ---- Setup B
        if active:
            upC = upC + 1 if b["c"] > orH else 0
            dnC = dnC + 1 if b["c"] < orL else 0
        if P["useCont"] and active and inEnt and not traded and rng > 0 and sizeOk and dayOk and pos is None:
            volOk = (not P["useVolB"]) or (volAvg and b["v"] >= P["volB"] * volAvg)
            goL = upC >= P["nAcc"] and volOk and (not P["useVwB"] or b["c"] > vw)
            goS = dnC >= P["nAcc"] and volOk and (not P["useVwB"] or b["c"] < vw)
            if goL or goS:
                side = 1 if goL else -1
                sl = orH - 0.25 * rng if goL else orL + 0.25 * rng
                c = b["c"]; tp = c + P["rrB"] * (c - sl)
                e = c + side * slip
                pos = dict(side=side, entry=e, sl=sl, tp=tp, bar=i,
                           risk0=abs(e - sl), be=False, kind="B", date=b["date"])
                traded = True

        # ---- Management
        if pos is not None and i > pos["bar"]:
            s = pos["side"]
            if P["beR"] > 0 and not pos["be"]:
                hit = (b["h"] >= pos["entry"] + P["beR"] * pos["risk0"]) if s == 1 else \
                      (b["l"] <= pos["entry"] - P["beR"] * pos["risk0"])
                if hit:
                    pos["sl"] = pos["entry"] + s * tk; pos["be"] = True
            if P["maxBars"] > 0 and i - pos["bar"] >= P["maxBars"]:
                close_pos(trades, pos, b["c"] - s * slip, "Zeit", b, P); pos = None

        # ---- EOD
        if active and b["chm"] >= P["flat"]:
            if pos is not None:
                close_pos(trades, pos, b["c"] - pos["side"] * slip, "EOD", b, P); pos = None
            active = False
    return trades


def close_pos(trades, pos, px, why, b, P):
    pts = (px - pos["entry"]) * pos["side"] - P["comm"]
    trades.append(dict(date=pos["date"], kind=pos["kind"], side=pos["side"],
                       entry=pos["entry"], exit=px, why=why, pts=pts,
                       R=pts / pos["risk0"] if pos["risk0"] else 0))


def stats(tr, dfrom=None):
    if dfrom: tr = [t for t in tr if t["date"] >= dfrom]
    n = len(tr)
    if n == 0: return dict(n=0, win=0, pf=0, net=0, R=0, dd=0, avgR=0)
    w = [t for t in tr if t["pts"] > 0]
    gp = sum(t["pts"] for t in w); gl = -sum(t["pts"] for t in tr if t["pts"] <= 0)
    eq = pk = dd = 0.0
    for t in tr:
        eq += t["R"]; pk = max(pk, eq); dd = max(dd, pk - eq)
    return dict(n=n, win=round(100 * len(w) / n), pf=round(gp / gl, 2) if gl else 99,
                net=round(sum(t["pts"] for t in tr), 1),
                R=round(sum(t["R"] for t in tr), 2),
                avgR=round(sum(t["R"] for t in tr) / n, 2), dd=round(dd, 2))


if __name__ == "__main__":
    import sys
    path, bs, tick = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    bars = load(path, bs); daily = daily_from(bars)
    for name, p in [("v1.1", {}),
                    ("v1.3", dict(tpMode="MaxMitteRR", rrA=1.0, useVwA=True))]:
        p = dict(p, tick=tick)
        if bs >= 15: p["kBars"] = 1
        print(name, stats(run(bars, daily, p)))
