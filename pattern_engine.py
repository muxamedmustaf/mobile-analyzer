# ============================================================
# MOBILE ANALYZER
# PATTERN_ENGINE.PY
# PROFESSIONAL MAJOR SWING CHART PATTERN ENGINE
# ============================================================

import math

SIMILARITY_DOUBLE = 0.025
SIMILARITY_TRIPLE = 0.035
SIMILARITY_SHOULDER = 0.045
MIN_PATTERN_SCORE = 60
INVALID_BREAK_BUFFER = 0.003
BREAK_CONFIRM_BUFFER = 0.001
MIN_LEG_RATIO = 0.20
MAX_PATTERN_AGE = 80

# New: minimum meaningful reaction between repeated tops/bottoms.
# This does NOT replace price similarity; both conditions are required.
MIN_REACTION_RATIO = 0.20


def _safe_div(a, b):
    if b == 0:
        return 0
    return a / b


def _distance(a, b):
    return abs(a - b) / max(abs((a + b) / 2), 1e-12)


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _price(value):
    try:
        return float(value)
    except Exception:
        return None


def _make_pattern(name, direction, quality, status, reason, entry=None,
                  tp1=None, tp2=None, sl=None, points=None,
                  neckline_points=None, pattern_start=None, pattern_end=None):
    return {
        "name": name, "direction": direction,
        "quality": int(_clamp(round(quality))),
        "status": status, "reason": reason,
        "entry": entry, "tp1": tp1, "tp2": tp2, "sl": sl,
        "points": points or [], "neckline_points": neckline_points or [],
        "pattern_start": pattern_start, "pattern_end": pattern_end,
    }


def _types(swings):
    return [x.get("type") for x in swings]


def _pattern_points(items):
    return [{"index": x.get("index"), "price": x.get("price"), "type": x.get("type")}
            for x in items]


def _trendline_value(p1, p2, x):
    try:
        x1, x2 = p1.get("index"), p2.get("index")
        y1, y2 = p1.get("price"), p2.get("price")
        if x1 is None or x2 is None:
            return None
        if x2 == x1:
            return y1
        return y1 + (y2 - y1) / (x2 - x1) * (x - x1)
    except Exception:
        return None


def _bullish_confirmation(close, neckline):
    return close > neckline * (1 + BREAK_CONFIRM_BUFFER)


def _bearish_confirmation(close, neckline):
    return close < neckline * (1 - BREAK_CONFIRM_BUFFER)


def _similarity_score(distance, maximum):
    if maximum <= 0:
        return 0
    return _clamp(100 - distance / maximum * 100)


def _confirmation_bonus(confirmed):
    return 10 if confirmed else 0


def _build_status(confirmed, invalid=False):
    if invalid:
        return "INVALID"
    return "CONFIRMED" if confirmed else "FORMING"


# ============================================================
# NEW STRUCTURAL VALIDATION
# ============================================================
def _meaningful_reaction(first, reaction, second, min_ratio=MIN_REACTION_RATIO):
    """
    Ensures the swing between two repeated bottoms/tops is meaningful.
    The reaction must not sit too close to the repeated level.

    For bottoms: reaction HIGH must rise meaningfully above both bottoms.
    For tops: reaction LOW must fall meaningfully below both tops.

    This is price geometry, not candle-count distance.
    """
    a = _price(first.get("price"))
    r = _price(reaction.get("price"))
    b = _price(second.get("price"))

    if a is None or r is None or b is None:
        return False

    base = (a + b) / 2
    if base <= 0:
        return False

    reaction_size = abs(r - base) / base
    return reaction_size >= min_ratio


def _triple_bottom_structure(s):
    # L-H-L-H-L: both rebounds must be meaningful.
    return (
        _meaningful_reaction(s[0], s[1], s[2])
        and _meaningful_reaction(s[2], s[3], s[4])
        and s[1]["price"] > max(s[0]["price"], s[2]["price"])
        and s[3]["price"] > max(s[2]["price"], s[4]["price"])
    )


def _triple_top_structure(s):
    # H-L-H-L-H: both pullbacks must be meaningful.
    return (
        _meaningful_reaction(s[0], s[1], s[2])
        and _meaningful_reaction(s[2], s[3], s[4])
        and s[1]["price"] < min(s[0]["price"], s[2]["price"])
        and s[3]["price"] < min(s[2]["price"], s[4]["price"])
    )


# ============================================================
# DOUBLE TOP / BOTTOM
# ============================================================
def detect_double_top(swings, close):
    if len(swings) < 3 or _types(swings[-3:]) != ["HIGH","LOW","HIGH"]:
        return None
    a,b,c = swings[-3:]
    similarity = _distance(a["price"], c["price"])
    if similarity > SIMILARITY_DOUBLE or b["price"] >= min(a["price"], c["price"]):
        return None
    neckline, peak = b["price"], max(a["price"], c["price"])
    height = peak - neckline
    if height <= 0: return None
    confirmed = _bearish_confirmation(close, neckline)
    invalid = close > peak * (1 + INVALID_BREAK_BUFFER)
    score = 76 + _similarity_score(similarity, SIMILARITY_DOUBLE)*0.14 + _confirmation_bonus(confirmed)
    return _make_pattern("Double Top","BEARISH",score,_build_status(confirmed,invalid),
        "Two major highs form a closely matched resistance with a confirmed trough between them.",
        neckline, neckline-height, neckline-height*1.5, peak*1.003,
        _pattern_points([a,b,c]), [{"index":b.get("index"),"price":neckline}],
        a.get("index"),c.get("index"))


def detect_double_bottom(swings, close):
    if len(swings) < 3 or _types(swings[-3:]) != ["LOW","HIGH","LOW"]:
        return None
    a,b,c = swings[-3:]
    similarity = _distance(a["price"], c["price"])
    if similarity > SIMILARITY_DOUBLE or b["price"] <= max(a["price"], c["price"]):
        return None
    neckline, bottom = b["price"], min(a["price"], c["price"])
    height = neckline - bottom
    if height <= 0: return None
    confirmed = _bullish_confirmation(close, neckline)
    invalid = close < bottom * (1 - INVALID_BREAK_BUFFER)
    score = 76 + _similarity_score(similarity, SIMILARITY_DOUBLE)*0.14 + _confirmation_bonus(confirmed)
    return _make_pattern("Double Bottom","BULLISH",score,_build_status(confirmed,invalid),
        "Two major lows form closely matched support with a major peak between them.",
        neckline, neckline+height, neckline+height*1.5, bottom*0.997,
        _pattern_points([a,b,c]), [{"index":b.get("index"),"price":neckline}],
        a.get("index"),c.get("index"))


# ============================================================
# TRIPLE TOP / BOTTOM
# ============================================================
def detect_triple_top(swings, close):
    if len(swings) < 5: return None
    s = swings[-5:]
    if _types(s) != ["HIGH","LOW","HIGH","LOW","HIGH"]: return None

    # NEW: reject weak/illogical intermediate reactions.
    if not _triple_top_structure(s): return None

    highs = [s[0]["price"],s[2]["price"],s[4]["price"]]
    lows = [s[1]["price"],s[3]["price"]]
    average_high = sum(highs)/3
    spread = (max(highs)-min(highs))/max(average_high,1e-12)
    if spread > SIMILARITY_TRIPLE: return None

    neckline, peak = min(lows), max(highs)
    height = peak-neckline
    if height <= 0: return None
    confirmed = close < neckline
    invalid = close > peak*(1+INVALID_BREAK_BUFFER)
    score = 82 + _similarity_score(spread,SIMILARITY_TRIPLE)*0.10 + _confirmation_bonus(confirmed)

    return _make_pattern("Triple Top","BEARISH",score,_build_status(confirmed,invalid),
        "Three major highs form a strong resistance zone with meaningful pullbacks between them.",
        neckline, neckline-height, neckline-height*1.5, peak*1.003,
        _pattern_points(s),
        [{"index":s[1].get("index"),"price":s[1].get("price")},
         {"index":s[3].get("index"),"price":s[3].get("price")}],
        s[0].get("index"),s[4].get("index"))


def detect_triple_bottom(swings, close):
    if len(swings) < 5: return None
    s = swings[-5:]
    if _types(s) != ["LOW","HIGH","LOW","HIGH","LOW"]: return None

    # NEW: reject weak/illogical intermediate reactions.
    if not _triple_bottom_structure(s): return None

    lows = [s[0]["price"],s[2]["price"],s[4]["price"]]
    highs = [s[1]["price"],s[3]["price"]]
    average_low = sum(lows)/3
    spread = (max(lows)-min(lows))/max(average_low,1e-12)
    if spread > SIMILARITY_TRIPLE: return None

    neckline, bottom = max(highs), min(lows)
    height = neckline-bottom
    if height <= 0: return None
    confirmed = close > neckline
    invalid = close < bottom*(1-INVALID_BREAK_BUFFER)
    score = 82 + _similarity_score(spread,SIMILARITY_TRIPLE)*0.10 + _confirmation_bonus(confirmed)

    return _make_pattern("Triple Bottom","BULLISH",score,_build_status(confirmed,invalid),
        "Three major lows form a strong support zone with meaningful rebounds between them.",
        neckline, neckline+height, neckline+height*1.5, bottom*0.997,
        _pattern_points(s),
        [{"index":s[1].get("index"),"price":s[1].get("price")},
         {"index":s[3].get("index"),"price":s[3].get("price")}],
        s[0].get("index"),s[4].get("index"))


# ============================================================
# HEAD & SHOULDERS
# ============================================================
def detect_head_shoulders(swings, close):
    if len(swings)<5: return None
    s=swings[-5:]
    if _types(s)!=["HIGH","LOW","HIGH","LOW","HIGH"]: return None
    left,neck1,head,neck2,right=s
    if _distance(left["price"],right["price"])>SIMILARITY_SHOULDER: return None
    if not(head["price"]>left["price"] and head["price"]>right["price"]): return None
    neckline=(neck1["price"]+neck2["price"])/2
    height=head["price"]-neckline
    if height<=0: return None
    confirmed=close<neckline
    invalid=close>head["price"]*(1+INVALID_BREAK_BUFFER)
    score=84+_similarity_score(_distance(left["price"],right["price"]),SIMILARITY_SHOULDER)*.10+3+_confirmation_bonus(confirmed)
    return _make_pattern("Head & Shoulders","BEARISH",score,_build_status(confirmed,invalid),
        "A valid left shoulder, higher head, right shoulder and two-point neckline are present.",
        neckline,neckline-height,neckline-height*1.5,head["price"]*1.003,
        _pattern_points(s),[{"index":neck1.get("index"),"price":neck1.get("price")},{"index":neck2.get("index"),"price":neck2.get("price")}],
        left.get("index"),right.get("index"))


def detect_inverse_head_shoulders(swings, close):
    if len(swings)<5: return None
    s=swings[-5:]
    if _types(s)!=["LOW","HIGH","LOW","HIGH","LOW"]: return None
    left,neck1,head,neck2,right=s
    if _distance(left["price"],right["price"])>SIMILARITY_SHOULDER: return None
    if not(head["price"]<left["price"] and head["price"]<right["price"]): return None
    neckline=(neck1["price"]+neck2["price"])/2
    height=neckline-head["price"]
    if height<=0: return None
    confirmed=close>neckline
    invalid=close<head["price"]*(1-INVALID_BREAK_BUFFER)
    score=84+_similarity_score(_distance(left["price"],right["price"]),SIMILARITY_SHOULDER)*.10+_confirmation_bonus(confirmed)
    return _make_pattern("Inverse Head & Shoulders","BULLISH",score,_build_status(confirmed,invalid),
        "A valid left shoulder, lower head, right shoulder and two-point neckline are present.",
        neckline,neckline+height,neckline+height*1.5,head["price"]*.997,
        _pattern_points(s),[{"index":neck1.get("index"),"price":neck1.get("price")},{"index":neck2.get("index"),"price":neck2.get("price")}],
        left.get("index"),right.get("index"))


# ============================================================
# TRIANGLES
# ============================================================
def detect_ascending_triangle(swings, close):
    if len(swings)<4:return None
    s=swings[-4:]; highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    h1,h2=highs;l1,l2=lows
    sim=_distance(h1["price"],h2["price"])
    if sim>.025 or l2["price"]<=l1["price"]:return None
    resistance=(h1["price"]+h2["price"])/2;height=resistance-min(l1["price"],l2["price"])
    if height<=0:return None
    confirmed=close>resistance;invalid=close<l1["price"]*(1+0-INVALID_BREAK_BUFFER)
    score=78+_similarity_score(sim,.025)*.08+5+_confirmation_bonus(confirmed)
    return _make_pattern("Ascending Triangle","BULLISH",score,_build_status(confirmed,invalid),
        "Flat resistance is combined with progressively higher major lows.",resistance,resistance+height,resistance+height*1.5,min(l1["price"],l2["price"])*.997,
        _pattern_points(s),[{"index":h1.get("index"),"price":h1.get("price")},{"index":h2.get("index"),"price":h2.get("price")}],s[0].get("index"),s[-1].get("index"))


def detect_descending_triangle(swings, close):
    if len(swings)<4:return None
    s=swings[-4:]; highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    h1,h2=highs;l1,l2=lows
    sim=_distance(l1["price"],l2["price"])
    if sim>.025 or h2["price"]>=h1["price"]:return None
    support=(l1["price"]+l2["price"])/2;height=max(h1["price"],h2["price"])-support
    if height<=0:return None
    confirmed=close<support;invalid=close>max(h1["price"],h2["price"])*(1+INVALID_BREAK_BUFFER)
    score=78+_similarity_score(sim,.025)*.08+5+_confirmation_bonus(confirmed)
    return _make_pattern("Descending Triangle","BEARISH",score,_build_status(confirmed,invalid),
        "Flat support is combined with progressively lower major highs.",support,support-height,support-height*1.5,max(h1["price"],h2["price"])*1.003,
        _pattern_points(s),[{"index":l1.get("index"),"price":l1.get("price")},{"index":l2.get("index"),"price":l2.get("price")}],s[0].get("index"),s[-1].get("index"))


def detect_symmetrical_triangle(swings, close=None):
    if len(swings)<4:return None
    s=swings[-4:]; highs=[x for x in s if x["type"]=="HIGH"]; lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    h1,h2=highs;l1,l2=lows
    if not(h2["price"]<h1["price"] and l2["price"]>l1["price"]):return None
    ur=h1["price"]-h2["price"];lr=l2["price"]-l1["price"]
    if ur<=0 or lr<=0:return None
    ratio=ur/lr
    if ratio<.25 or ratio>4:return None
    direction="NEUTRAL";status="FORMING"
    if close is not None:
        upper=_trendline_value(h1,h2,s[-1].get("index"));lower=_trendline_value(l1,l2,s[-1].get("index"))
        if upper is not None and close>upper:direction,status="BULLISH","CONFIRMED"
        elif lower is not None and close<lower:direction,status="BEARISH","CONFIRMED"
    return _make_pattern("Symmetrical Triangle",direction,78,status,
        "Lower highs and higher lows create a contracting price structure. Breakout direction must be confirmed.",
        points=_pattern_points(s),
        neckline_points=[{"index":h1.get("index"),"price":h1.get("price")},{"index":h2.get("index"),"price":h2.get("price")},
                         {"index":l1.get("index"),"price":l1.get("price")},{"index":l2.get("index"),"price":l2.get("price")}],
        pattern_start=s[0].get("index"),pattern_end=s[-1].get("index"))


def detect_rising_wedge(swings, close):
    if len(swings)<4:return None
    s=swings[-4:];highs=[x for x in s if x["type"]=="HIGH"];lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    h1,h2=highs;l1,l2=lows
    if not(h2["price"]>h1["price"] and l2["price"]>l1["price"]):return None
    hm=h2["price"]-h1["price"];lm=l2["price"]-l1["price"]
    if hm<=0 or lm<=0 or lm<=hm:return None
    lower=_trendline_value(l1,l2,s[-1].get("index"));confirmed=lower is not None and close<lower
    return _make_pattern("Rising Wedge","BEARISH",82 if confirmed else 76,"CONFIRMED" if confirmed else "FORMING",
        "Both highs and lows rise, but the lower boundary advances faster, producing a narrowing rising structure.",
        points=_pattern_points(s),pattern_start=s[0].get("index"),pattern_end=s[-1].get("index"))


def detect_falling_wedge(swings, close):
    if len(swings)<4:return None
    s=swings[-4:];highs=[x for x in s if x["type"]=="HIGH"];lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    h1,h2=highs;l1,l2=lows
    if not(h2["price"]<h1["price"] and l2["price"]<l1["price"]):return None
    hm=h1["price"]-h2["price"];lm=l1["price"]-l2["price"]
    if hm<=0 or lm<=0 or lm<=hm:return None
    upper=_trendline_value(h1,h2,s[-1].get("index"));confirmed=upper is not None and close>upper
    return _make_pattern("Falling Wedge","BULLISH",82 if confirmed else 76,"CONFIRMED" if confirmed else "FORMING",
        "Both highs and lows fall, while the lower boundary contracts faster, producing a narrowing falling structure.",
        points=_pattern_points(s),pattern_start=s[0].get("index"),pattern_end=s[-1].get("index"))


def detect_rectangle(swings, close):
    if len(swings)<4:return None
    s=swings[-4:]
    if _types(s) not in [["HIGH","LOW","HIGH","LOW"],["LOW","HIGH","LOW","HIGH"]]:return None
    highs=[x for x in s if x["type"]=="HIGH"];lows=[x for x in s if x["type"]=="LOW"]
    if len(highs)!=2 or len(lows)!=2:return None
    resistance=(highs[0]["price"]+highs[1]["price"])/2;support=(lows[0]["price"]+lows[1]["price"])/2
    if resistance<=support:return None
    if _distance(highs[0]["price"],highs[1]["price"])>.03 or _distance(lows[0]["price"],lows[1]["price"])>.03:return None
    height=resistance-support
    if close>resistance:direction,status="BULLISH","CONFIRMED"
    elif close<support:direction,status="BEARISH","CONFIRMED"
    else:direction,status="NEUTRAL","FORMING"
    entry=resistance if direction=="BULLISH" else support if direction=="BEARISH" else None
    tp1=resistance+height if direction=="BULLISH" else support-height if direction=="BEARISH" else None
    tp2=resistance+height*1.5 if direction=="BULLISH" else support-height*1.5 if direction=="BEARISH" else None
    sl=support*.997 if direction=="BULLISH" else resistance*1.003 if direction=="BEARISH" else None
    return _make_pattern("Rectangle",direction,80 if status=="CONFIRMED" else 72,status,
        "Price is respecting a clear horizontal resistance and support range.",entry,tp1,tp2,sl,
        _pattern_points(s),pattern_start=s[0].get("index"),pattern_end=s[-1].get("index"))


# # ============================================================
# MAIN DETECTOR
# ============================================================
def detect_patterns(df):
    if df is None:return []
    swings=df.attrs.get("major_swings",[])
    if len(swings)<3:return []
    try: close=float(df["close"].iloc[-1])
    except Exception:return []

    detectors=[detect_double_top,detect_double_bottom,detect_triple_top,detect_triple_bottom,
               detect_head_shoulders,detect_inverse_head_shoulders,detect_ascending_triangle,
               detect_descending_triangle,detect_symmetrical_triangle,detect_rising_wedge,
               detect_falling_wedge,detect_rectangle]
    detected=[]
    for detector in detectors:
        try:
            result=detector(swings,close)
            if result is not None and result["quality"]>=MIN_PATTERN_SCORE:
                detected.append(result)
        except Exception:
            continue
    detected=[p for p in detected if p["status"]!="INVALID"]

    def ranking_score(p):
        score=float(p.get("quality",0))
        if p.get("status")=="CONFIRMED":score+=12
        elif p.get("status")=="FORMING":score+=3
        if p.get("pattern_end") is not None:score+=2
        return score

    detected.sort(key=ranking_score,reverse=True)
    return detected


def get_best_pattern(df):
    patterns=detect_patterns(df)
    return patterns[0] if patterns else None


def get_confirmed_patterns(df):
    return [p for p in detect_patterns(df) if p["status"]=="CONFIRMED"]


def get_latest_patterns(df):
    patterns=detect_patterns(df)
    if not patterns:return []
    ends=[p.get("pattern_end") for p in patterns if p.get("pattern_end") is not None]
    if not ends:return patterns
    latest_end=max(ends)
    latest=[p for p in patterns if p.get("pattern_end")==latest_end]
    return latest or patterns
