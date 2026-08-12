# ============================================================
# MOBILE ANALYZER - PATTERN ENGINE
# MAJOR SWING CHART PATTERN ENGINE + DRAWING METADATA
# ============================================================

import math

SIMILARITY_DOUBLE = 0.025
SIMILARITY_TRIPLE = 0.035
SIMILARITY_SHOULDER = 0.045
TRIANGLE_TOLERANCE = 0.025
BREAKOUT_BUFFER = 0.001
MIN_STRUCTURE_RATIO = 0.003
MAX_SWING_WINDOW = 11

PATTERN_PRIORITY = {
    "Triple Top": 100, "Triple Bottom": 100,
    "Head & Shoulders": 99, "Inverse Head & Shoulders": 99,
    "Double Top": 90, "Double Bottom": 90,
    "Ascending Triangle": 88, "Descending Triangle": 88,
    "Symmetrical Triangle": 80,
}


def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except Exception:
        return None


def _safe_div(a, b):
    a, b = _safe_float(a), _safe_float(b)
    if a is None or b is None or b == 0:
        return 0.0
    return a / b


def _distance(a, b):
    a, b = _safe_float(a), _safe_float(b)
    if a is None or b is None:
        return 999.0
    return abs(a - b) / max(abs((a + b) / 2.0), 1e-12)


def _normalize_type(value):
    if value is None:
        return None
    value = str(value).upper().strip()
    if value in ("HIGH", "H", "TOP"):
        return "HIGH"
    if value in ("LOW", "L", "BOTTOM"):
        return "LOW"
    return None


def _clean_swings(swings):
    cleaned = []
    for item in swings or []:
        if not isinstance(item, dict):
            continue
        swing_type = _normalize_type(item.get("type"))
        price = _safe_float(item.get("price"))
        if swing_type is None or price is None or price <= 0:
            continue
        item = dict(item)
        item["type"] = swing_type
        item["price"] = price
        cleaned.append(item)
    return cleaned


def _pattern_range(prices):
    values = [_safe_float(x) for x in prices]
    values = [x for x in values if x is not None]
    if not values:
        return 0.0
    return _safe_div(max(values) - min(values), max(abs(max(values)), 1e-12))


def _valid_alternating_window(swings, expected_types):
    return len(swings) == len(expected_types) and [x["type"] for x in swings] == expected_types


def _scan_windows(swings, length):
    if len(swings) < length:
        return []
    recent = swings[max(0, len(swings) - MAX_SWING_WINDOW):]
    return [recent[i:i + length] for i in range(len(recent) - length + 1)]


def _levels_are_structurally_valid(highs, lows):
    if not highs or not lows:
        return False
    return _pattern_range([x["price"] for x in highs + lows]) >= MIN_STRUCTURE_RATIO


def _bullish_confirmation(close, level):
    close, level = _safe_float(close), _safe_float(level)
    return close is not None and level is not None and close > level * (1 + BREAKOUT_BUFFER)


def _bearish_confirmation(close, level):
    close, level = _safe_float(close), _safe_float(level)
    return close is not None and level is not None and close < level * (1 - BREAKOUT_BUFFER)


def _confirmation_text(confirmed, direction):
    return (f"Candle close confirmed the {direction.lower()} breakout."
            if confirmed else
            "Pattern is forming; breakout candle close has not confirmed it yet.")


# ---------- CHART DRAWING METADATA ----------

def _swing_point(swing, label=None):
    point = {
        "type": swing.get("type"),
        "price": _safe_float(swing.get("price")),
        "label": label or swing.get("type"),
    }
    for key in ("index", "position", "bar_index", "timestamp", "time",
                "date", "datetime", "candle_index"):
        if key in swing:
            point[key] = swing[key]
    return point


def _pattern_points(swings, labels=None):
    return [_swing_point(s, labels[i] if labels and i < len(labels) else None)
            for i, s in enumerate(swings)]


def _make_pattern(name, direction, quality, status, reason, entry=None,
                  tp1=None, tp2=None, sl=None, confirmation=None,
                  pattern_swings=None, labels=None, neckline_points=None):
    metadata = {
        "pattern_points": _pattern_points(pattern_swings or [], labels),
        "swing_count": len(pattern_swings or []),
    }
    if neckline_points:
        metadata["neckline_points"] = _pattern_points(neckline_points)
    return {
        "name": name, "direction": direction,
        "quality": int(max(0, min(100, round(quality)))),
        "status": status, "reason": reason, "entry": entry,
        "tp1": tp1, "tp2": tp2, "sl": sl,
        "confirmation": confirmation, "metadata": metadata,
    }


def _best(candidates):
    return max(candidates, key=lambda x: (x["quality"], x["status"] == "CONFIRMED"), default=None)


# ---------- DOUBLE TOP ----------
def detect_double_top(swings, close):
    out = []
    for s in _scan_windows(swings, 3):
        if not _valid_alternating_window(s, ["HIGH", "LOW", "HIGH"]): continue
        a, b, c = s
        if not _levels_are_structurally_valid([a, c], [b]): continue
        similarity = _distance(a["price"], c["price"])
        if similarity > SIMILARITY_DOUBLE: continue
        neckline = b["price"]
        if neckline >= min(a["price"], c["price"]): continue
        peak = max(a["price"], c["price"])
        distance = peak - neckline
        if distance <= 0: continue
        confirmed = _bearish_confirmation(close, neckline)
        quality = 80 + (8 if similarity <= .01 else 4 if similarity <= .018 else 0) + (8 if confirmed else 0)
        out.append(_make_pattern("Double Top", "BEARISH", quality,
            "CONFIRMED" if confirmed else "FORMING",
            "Two major highs are closely matched with a major trough between them.",
            neckline, neckline-distance, neckline-distance*1.5, peak*1.003,
            _confirmation_text(confirmed, "bearish"), s,
            ["Peak 1", "Neckline", "Peak 2"], [b]))
    return _best(out)


# ---------- DOUBLE BOTTOM ----------
def detect_double_bottom(swings, close):
    out = []
    for s in _scan_windows(swings, 3):
        if not _valid_alternating_window(s, ["LOW", "HIGH", "LOW"]): continue
        a, b, c = s
        if not _levels_are_structurally_valid([b], [a, c]): continue
        similarity = _distance(a["price"], c["price"])
        if similarity > SIMILARITY_DOUBLE: continue
        neckline = b["price"]
        if neckline <= max(a["price"], c["price"]): continue
        bottom = min(a["price"], c["price"])
        distance = neckline - bottom
        if distance <= 0: continue
        confirmed = _bullish_confirmation(close, neckline)
        quality = 80 + (8 if similarity <= .01 else 4 if similarity <= .018 else 0) + (8 if confirmed else 0)
        out.append(_make_pattern("Double Bottom", "BULLISH", quality,
            "CONFIRMED" if confirmed else "FORMING",
            "Two major lows are closely matched with a major peak between them.",
            neckline, neckline+distance, neckline+distance*1.5, bottom*.997,
            _confirmation_text(confirmed, "bullish"), s,
            ["Bottom 1", "Neckline", "Bottom 2"], [b]))
    return _best(out)


# ---------- TRIPLE TOP ----------
def detect_triple_top(swings, close):
    out = []
    for s in _scan_windows(swings, 5):
        if not _valid_alternating_window(s, ["HIGH", "LOW", "HIGH", "LOW", "HIGH"]): continue
        h1,l1,h2,l2,h3=s; highs=[h1,h2,h3]; lows=[l1,l2]
        if not _levels_are_structurally_valid(highs,lows): continue
        prices=[x["price"] for x in highs]; avg=sum(prices)/3
        spread=_safe_div(max(prices)-min(prices), max(abs(avg),1e-12))
        if spread>SIMILARITY_TRIPLE: continue
        neckline=min(x["price"] for x in lows); peak=max(prices); distance=peak-neckline
        if distance<=0: continue
        d1=_safe_div(h1["price"]-l1["price"],h1["price"]); d2=_safe_div(h2["price"]-l2["price"],h2["price"])
        if d1<MIN_STRUCTURE_RATIO or d2<MIN_STRUCTURE_RATIO: continue
        confirmed=_bearish_confirmation(close,neckline)
        quality=83+(6 if spread<=.01 else 3 if spread<=.02 else 0)+(3 if d1>=.01 and d2>=.01 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Triple Top","BEARISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Three major highs are closely matched and separated by two meaningful pullbacks.",
            neckline,neckline-distance,neckline-distance*1.5,peak*1.003,
            _confirmation_text(confirmed,"bearish"),s,
            ["Peak 1","Neckline 1","Peak 2","Neckline 2","Peak 3"],[l1,l2]))
    return _best(out)


# ---------- TRIPLE BOTTOM ----------
def detect_triple_bottom(swings, close):
    out=[]
    for s in _scan_windows(swings,5):
        if not _valid_alternating_window(s,["LOW","HIGH","LOW","HIGH","LOW"]): continue
        l1,h1,l2,h2,l3=s; lows=[l1,l2,l3]; highs=[h1,h2]
        if not _levels_are_structurally_valid(highs,lows): continue
        prices=[x["price"] for x in lows]; avg=sum(prices)/3
        spread=_safe_div(max(prices)-min(prices),max(abs(avg),1e-12))
        if spread>SIMILARITY_TRIPLE: continue
        bottom=min(prices); neckline=max(x["price"] for x in highs); distance=neckline-bottom
        if distance<=0: continue
        hgt1=_safe_div(h1["price"]-l1["price"],l1["price"]); hgt2=_safe_div(h2["price"]-l2["price"],l2["price"])
        if hgt1<MIN_STRUCTURE_RATIO or hgt2<MIN_STRUCTURE_RATIO: continue
        confirmed=_bullish_confirmation(close,neckline)
        quality=83+(6 if spread<=.01 else 3 if spread<=.02 else 0)+(3 if hgt1>=.01 and hgt2>=.01 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Triple Bottom","BULLISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Three major lows are closely matched and separated by two meaningful rallies.",
            neckline,neckline+distance,neckline+distance*1.5,bottom*.997,
            _confirmation_text(confirmed,"bullish"),s,
            ["Bottom 1","Neckline 1","Bottom 2","Neckline 2","Bottom 3"],[h1,h2]))
    return _best(out)


# ---------- HEAD & SHOULDERS ----------
def detect_head_shoulders(swings, close):
    out=[]
    for s in _scan_windows(swings,5):
        if not _valid_alternating_window(s,["HIGH","LOW","HIGH","LOW","HIGH"]): continue
        left,neck1,head,neck2,right=s
        similarity=_distance(left["price"],right["price"])
        if similarity>SIMILARITY_SHOULDER: continue
        if not(head["price"]>left["price"] and head["price"]>right["price"]): continue
        neckline=(neck1["price"]+neck2["price"])/2
        distance=head["price"]-neckline
        if distance<=0: continue
        gap1=_safe_div(head["price"]-left["price"],head["price"]); gap2=_safe_div(head["price"]-right["price"],head["price"])
        if gap1<MIN_STRUCTURE_RATIO or gap2<MIN_STRUCTURE_RATIO: continue
        confirmed=_bearish_confirmation(close,neckline)
        quality=84+(6 if similarity<=.015 else 3 if similarity<=.03 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Head & Shoulders","BEARISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Major left shoulder, higher head, and structurally similar right shoulder are detected.",
            neckline,neckline-distance,neckline-distance*1.5,head["price"]*1.003,
            _confirmation_text(confirmed,"bearish"),s,
            ["Left Shoulder","Neckline 1","Head","Neckline 2","Right Shoulder"],[neck1,neck2]))
    return _best(out)


# ---------- INVERSE HEAD & SHOULDERS ----------
def detect_inverse_head_shoulders(swings, close):
    out=[]
    for s in _scan_windows(swings,5):
        if not _valid_alternating_window(s,["LOW","HIGH","LOW","HIGH","LOW"]): continue
        left,neck1,head,neck2,right=s
        similarity=_distance(left["price"],right["price"])
        if similarity>SIMILARITY_SHOULDER: continue
        if not(head["price"]<left["price"] and head["price"]<right["price"]): continue
        neckline=(neck1["price"]+neck2["price"])/2
        distance=neckline-head["price"]
        if distance<=0: continue
        gap1=_safe_div(left["price"]-head["price"],head["price"]); gap2=_safe_div(right["price"]-head["price"],head["price"])
        if gap1<MIN_STRUCTURE_RATIO or gap2<MIN_STRUCTURE_RATIO: continue
        confirmed=_bullish_confirmation(close,neckline)
        quality=84+(6 if similarity<=.015 else 3 if similarity<=.03 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Inverse Head & Shoulders","BULLISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Major left shoulder, lower head, and structurally similar right shoulder are detected.",
            neckline,neckline+distance,neckline+distance*1.5,head["price"]*.997,
            _confirmation_text(confirmed,"bullish"),s,
            ["Left Shoulder","Neckline 1","Head","Neckline 2","Right Shoulder"],[neck1,neck2]))
    return _best(out)


# ---------- TRIANGLES ----------
def detect_ascending_triangle(swings, close):
    out=[]
    for s in _scan_windows(swings,4):
        highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
        if len(highs)!=2 or len(lows)!=2: continue
        h1,h2=highs; l1,l2=lows
        sim=_distance(h1["price"],h2["price"])
        if sim>TRIANGLE_TOLERANCE or l2["price"]<=l1["price"]: continue
        resistance=(h1["price"]+h2["price"])/2; height=resistance-min(l1["price"],l2["price"])
        if height<=0: continue
        confirmed=_bullish_confirmation(close,resistance); quality=82+(5 if sim<=.01 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Ascending Triangle","BULLISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Major highs form common resistance while major lows continue rising.",resistance,resistance+height,resistance+height*1.5,min(l1["price"],l2["price"])*.997,
            _confirmation_text(confirmed,"bullish"),s,["Resistance 1","Higher Low 1","Resistance 2","Higher Low 2"],[h1,h2]))
    return _best(out)


def detect_descending_triangle(swings, close):
    out=[]
    for s in _scan_windows(swings,4):
        highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
        if len(highs)!=2 or len(lows)!=2: continue
        h1,h2=highs; l1,l2=lows
        sim=_distance(l1["price"],l2["price"])
        if sim>TRIANGLE_TOLERANCE or h2["price"]>=h1["price"]: continue
        support=(l1["price"]+l2["price"])/2; height=max(h1["price"],h2["price"])-support
        if height<=0: continue
        confirmed=_bearish_confirmation(close,support); quality=82+(5 if sim<=.01 else 0)+(8 if confirmed else 0)
        out.append(_make_pattern("Descending Triangle","BEARISH",quality,"CONFIRMED" if confirmed else "FORMING",
            "Major lows form common support while major highs continue falling.",support,support-height,support-height*1.5,max(h1["price"],h2["price"])*1.003,
            _confirmation_text(confirmed,"bearish"),s,["Lower High 1","Support 1","Lower High 2","Support 2"],[l1,l2]))
    return _best(out)


def detect_symmetrical_triangle(swings, close=None):
    out=[]
    for s in _scan_windows(swings,4):
        highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
        if len(highs)!=2 or len(lows)!=2: continue
        h1,h2=highs; l1,l2=lows
        if not(h2["price"]<h1["price"] and l2["price"]>l1["price"]): continue
        out.append(_make_pattern("Symmetrical Triangle","NEUTRAL",80,"FORMING",
            "Major highs are falling while major lows are rising, creating a contracting structure.",
            pattern_swings=s,labels=["High 1","Low 1","High 2","Low 2"]))
    return _best(out)


# ---------- PUBLIC API ----------
def detect_patterns(df):
    if df is None or df.empty: return []
    swings=_clean_swings(df.attrs.get("major_swings",[]))
    if len(swings)<3: return []
    close=_safe_float(df["close"].iloc[-1])
    if close is None: return []
    detected=[]
    for detector in [detect_double_top,detect_double_bottom,detect_triple_top,detect_triple_bottom,
                      detect_head_shoulders,detect_inverse_head_shoulders,detect_ascending_triangle,
                      detect_descending_triangle]:
        try:
            result=detector(swings,close)
            if result is not None: detected.append(result)
        except Exception:
            continue
    try:
        result=detect_symmetrical_triangle(swings,close)
        if result is not None: detected.append(result)
    except Exception:
        pass
    detected.sort(key=lambda x:(x.get("quality",0),x.get("status")=="CONFIRMED",PATTERN_PRIORITY.get(x.get("name"),0)),reverse=True)
    return detected


def get_best_pattern(df):
    patterns=detect_patterns(df)
    return patterns[0] if patterns else None


def get_confirmed_patterns(df):
    return [p for p in detect_patterns(df) if p.get("status")=="CONFIRMED"]
                           
