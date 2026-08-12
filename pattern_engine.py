# ============================================================
# MOBILE ANALYZER
# PATTERN_ENGINE.PY
# PROFESSIONAL MAJOR SWING CHART PATTERN ENGINE
# ============================================================

import math


# ============================================================
# SETTINGS
# ============================================================

SIMILARITY_DOUBLE = 0.025
SIMILARITY_TRIPLE = 0.035
SIMILARITY_SHOULDER = 0.045

MIN_PATTERN_SCORE = 60

INVALID_BREAK_BUFFER = 0.003
BREAK_CONFIRM_BUFFER = 0.001

MIN_LEG_RATIO = 0.20
MAX_PATTERN_AGE = 80


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_div(a, b):
    if b == 0:
        return 0
    return a / b


def _distance(a, b):
    return abs(a - b) / max(
        abs((a + b) / 2),
        1e-12
    )


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _price(value):
    try:
        return float(value)
    except Exception:
        return None


def _last_index(swings):
    if not swings:
        return None

    return swings[-1].get("index")


def _make_pattern(
    name,
    direction,
    quality,
    status,
    reason,
    entry=None,
    tp1=None,
    tp2=None,
    sl=None,
    points=None,
    neckline_points=None,
    pattern_start=None,
    pattern_end=None,
):
    return {
        "name": name,
        "direction": direction,
        "quality": int(_clamp(round(quality))),
        "status": status,
        "reason": reason,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "points": points or [],
        "neckline_points": neckline_points or [],
        "pattern_start": pattern_start,
        "pattern_end": pattern_end,
    }


# ============================================================
# SWING HELPERS
# ============================================================

def _types(swings):
    return [x.get("type") for x in swings]


def _prices(swings):
    return [_price(x.get("price")) for x in swings]


def _is_recent(swings):
    if not swings:
        return False

    last = swings[-1]

    if "index" not in last:
        return True

    try:
        return True
    except Exception:
        return True


def _pattern_points(items):
    points = []

    for x in items:
        points.append({
            "index": x.get("index"),
            "price": x.get("price"),
            "type": x.get("type"),
        })

    return points


def _trendline_value(p1, p2, x):
    try:
        x1 = p1.get("index")
        x2 = p2.get("index")
        y1 = p1.get("price")
        y2 = p2.get("price")

        if x1 is None or x2 is None:
            return None

        if x2 == x1:
            return y1

        slope = (y2 - y1) / (x2 - x1)

        return y1 + slope * (x - x1)

    except Exception:
        return None


# ============================================================
# CONFIRMATION
# ============================================================

def _bullish_confirmation(close, neckline):
    return close > neckline * (
        1 + BREAK_CONFIRM_BUFFER
    )


def _bearish_confirmation(close, neckline):
    return close < neckline * (
        1 - BREAK_CONFIRM_BUFFER
    )


# ============================================================
# SCORE HELPERS
# ============================================================

def _similarity_score(distance, maximum):
    if maximum <= 0:
        return 0

    score = 100 - (
        distance / maximum * 100
    )

    return _clamp(score)


def _confirmation_bonus(confirmed):
    return 10 if confirmed else 0


def _build_status(
    confirmed,
    invalid=False
):
    if invalid:
        return "INVALID"

    if confirmed:
        return "CONFIRMED"

    return "FORMING"


# ============================================================
# DOUBLE TOP
# ============================================================

def detect_double_top(swings, close):

    if len(swings) < 3:
        return None

    s = swings[-3:]

    if _types(s) != [
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    a, b, c = s

    similarity = _distance(
        a["price"],
        c["price"]
    )

    if similarity > SIMILARITY_DOUBLE:
        return None

    neckline = b["price"]

    if neckline >= min(
        a["price"],
        c["price"]
    ):
        return None

    peak = max(
        a["price"],
        c["price"]
    )

    height = peak - neckline

    if height <= 0:
        return None

    confirmed = _bearish_confirmation(
        close,
        neckline
    )

    invalid = (
        close > peak * (
            1 + INVALID_BREAK_BUFFER
        )
    )

    score = 76

    score += _similarity_score(
        similarity,
        SIMILARITY_DOUBLE
    ) * 0.14

    score += _confirmation_bonus(
        confirmed
    )

    status = _build_status(
        confirmed,
        invalid
    )

    return _make_pattern(
        name="Double Top",
        direction="BEARISH",
        quality=score,
        status=status,
        reason=(
            "Two major highs form a "
            "closely matched resistance "
            "with a confirmed trough "
            "between them."
        ),
        entry=neckline,
        tp1=neckline - height,
        tp2=neckline - height * 1.5,
        sl=peak * 1.003,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": b.get("index"),
                "price": neckline,
            }
        ],
        pattern_start=a.get("index"),
        pattern_end=c.get("index"),
    )


# ============================================================
# DOUBLE BOTTOM
# ============================================================

def detect_double_bottom(swings, close):

    if len(swings) < 3:
        return None

    s = swings[-3:]

    if _types(s) != [
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    a, b, c = s

    similarity = _distance(
        a["price"],
        c["price"]
    )

    if similarity > SIMILARITY_DOUBLE:
        return None

    neckline = b["price"]

    if neckline <= max(
        a["price"],
        c["price"]
    ):
        return None

    bottom = min(
        a["price"],
        c["price"]
    )

    height = neckline - bottom

    if height <= 0:
        return None

    confirmed = _bullish_confirmation(
        close,
        neckline
    )

    invalid = (
        close < bottom * (
            1 - INVALID_BREAK_BUFFER
        )
    )

    score = 76

    score += _similarity_score(
        similarity,
        SIMILARITY_DOUBLE
    ) * 0.14

    score += _confirmation_bonus(
        confirmed
    )

    status = _build_status(
        confirmed,
        invalid
    )

    return _make_pattern(
        name="Double Bottom",
        direction="BULLISH",
        quality=score,
        status=status,
        reason=(
            "Two major lows form closely "
            "matched support with a major "
            "peak between them."
        ),
        entry=neckline,
        tp1=neckline + height,
        tp2=neckline + height * 1.5,
        sl=bottom * 0.997,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": b.get("index"),
                "price": neckline,
            }
        ],
        pattern_start=a.get("index"),
        pattern_end=c.get("index"),
    )


# ============================================================
# TRIPLE TOP
# ============================================================

def detect_triple_top(swings, close):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    if _types(s) != [
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    highs = [
        s[0]["price"],
        s[2]["price"],
        s[4]["price"],
    ]

    lows = [
        s[1]["price"],
        s[3]["price"],
    ]

    average_high = sum(highs) / 3

    spread = (
        max(highs) - min(highs)
    ) / max(
        average_high,
        1e-12
    )

    if spread > SIMILARITY_TRIPLE:
        return None

    neckline = min(lows)
    peak = max(highs)
    height = peak - neckline

    if height <= 0:
        return None

    confirmed = (
        close < neckline
    )

    invalid = (
        close > peak * (
            1 + INVALID_BREAK_BUFFER
        )
    )

    score = 82

    score += _similarity_score(
        spread,
        SIMILARITY_TRIPLE
    ) * 0.10

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Triple Top",
        direction="BEARISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "Three major highs form a "
            "strong resistance zone with "
            "two intervening reactions."
        ),
        entry=neckline,
        tp1=neckline - height,
        tp2=neckline - height * 1.5,
        sl=peak * 1.003,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": s[1].get("index"),
                "price": s[1].get("price"),
            },
            {
                "index": s[3].get("index"),
                "price": s[3].get("price"),
            },
        ],
        pattern_start=s[0].get("index"),
        pattern_end=s[4].get("index"),
    )


# ============================================================
# TRIPLE BOTTOM
# ============================================================

def detect_triple_bottom(swings, close):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    if _types(s) != [
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    lows = [
        s[0]["price"],
        s[2]["price"],
        s[4]["price"],
    ]

    highs = [
        s[1]["price"],
        s[3]["price"],
    ]

    average_low = sum(lows) / 3

    spread = (
        max(lows) - min(lows)
    ) / max(
        average_low,
        1e-12
    )

    if spread > SIMILARITY_TRIPLE:
        return None

    neckline = max(highs)
    bottom = min(lows)
    height = neckline - bottom

    if height <= 0:
        return None

    confirmed = (
        close > neckline
    )

    invalid = (
        close < bottom * (
            1 - INVALID_BREAK_BUFFER
        )
    )

    score = 82

    score += _similarity_score(
        spread,
        SIMILARITY_TRIPLE
    ) * 0.10

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Triple Bottom",
        direction="BULLISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "Three major lows form a "
            "strong support zone with "
            "two intervening reactions."
        ),
        entry=neckline,
        tp1=neckline + height,
        tp2=neckline + height * 1.5,
        sl=bottom * 0.997,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": s[1].get("index"),
                "price": s[1].get("price"),
            },
            {
                "index": s[3].get("index"),
                "price": s[3].get("price"),
            },
        ],
        pattern_start=s[0].get("index"),
        pattern_end=s[4].get("index"),
    )


# ============================================================
# HEAD & SHOULDERS
# ============================================================

def detect_head_shoulders(swings, close):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    if _types(s) != [
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    left, neck1, head, neck2, right = s

    shoulder_similarity = _distance(
        left["price"],
        right["price"]
    )

    if (
        shoulder_similarity
        > SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"] > left["price"]
        and
        head["price"] > right["price"]
    ):
        return None

    neckline = (
        neck1["price"]
        +
        neck2["price"]
    ) / 2

    height = (
        head["price"]
        -
        neckline
    )

    if height <= 0:
        return None

    confirmed = (
        close < neckline
    )

    invalid = (
        close > head["price"] * (
            1 + INVALID_BREAK_BUFFER
        )
    )

    score = 84

    score += _similarity_score(
        shoulder_similarity,
        SIMILARITY_SHOULDER
    ) * 0.10

    if head["price"] > max(
        left["price"],
        right["price"]
    ):
        score += 3

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Head & Shoulders",
        direction="BEARISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "A valid left shoulder, higher "
            "head, right shoulder and "
            "two-point neckline are present."
        ),
        entry=neckline,
        tp1=neckline - height,
        tp2=neckline - height * 1.5,
        sl=head["price"] * 1.003,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": neck1.get("index"),
                "price": neck1.get("price"),
            },
            {
                "index": neck2.get("index"),
                "price": neck2.get("price"),
            },
        ],
        pattern_start=left.get("index"),
        pattern_end=right.get("index"),
    )


# ============================================================
# INVERSE HEAD & SHOULDERS
# ============================================================

def detect_inverse_head_shoulders(
    swings,
    close
):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    if _types(s) != [
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    left, neck1, head, neck2, right = s

    shoulder_similarity = _distance(
        left["price"],
        right["price"]
    )

    if (
        shoulder_similarity
        > SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"] < left["price"]
        and
        head["price"] < right["price"]
    ):
        return None

    neckline = (
        neck1["price"]
        +
        neck2["price"]
    ) / 2

    height = (
        neckline
        -
        head["price"]
    )

    if height <= 0:
        return None

    confirmed = (
        close > neckline
    )

    invalid = (
        close < head["price"] * (
            1 - INVALID_BREAK_BUFFER
        )
    )

    score = 84

    score += _similarity_score(
        shoulder_similarity,
        SIMILARITY_SHOULDER
    ) * 0.10

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Inverse Head & Shoulders",
        direction="BULLISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "A valid left shoulder, lower "
            "head, right shoulder and "
            "two-point neckline are present."
        ),
        entry=neckline,
        tp1=neckline + height,
        tp2=neckline + height * 1.5,
        sl=head["price"] * 0.997,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": neck1.get("index"),
                "price": neck1.get("price"),
            },
            {
                "index": neck2.get("index"),
                "price": neck2.get("price"),
            },
        ],
        pattern_start=left.get("index"),
        pattern_end=right.get("index"),
    )


# ============================================================
# ASCENDING TRIANGLE
# ============================================================

def detect_ascending_triangle(
    swings,
    close
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    resistance_similarity = _distance(
        h1["price"],
        h2["price"]
    )

    if resistance_similarity > 0.025:
        return None

    if l2["price"] <= l1["price"]:
        return None

    resistance = (
        h1["price"] + h2["price"]
    ) / 2

    height = (
        resistance
        -
        min(l1["price"], l2["price"])
    )

    if height <= 0:
        return None

    confirmed = (
        close > resistance
    )

    invalid = (
        close < l1["price"] * (
            1 - INVALID_BREAK_BUFFER
        )
    )

    score = 78

    score += _similarity_score(
        resistance_similarity,
        0.025
    ) * 0.08

    score += 5

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Ascending Triangle",
        direction="BULLISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "Flat resistance is combined "
            "with progressively higher "
            "major lows."
        ),
        entry=resistance,
        tp1=resistance + height,
        tp2=resistance + height * 1.5,
        sl=min(
            l1["price"],
            l2["price"]
        ) * 0.997,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": h1.get("index"),
                "price": h1.get("price"),
            },
            {
                "index": h2.get("index"),
                "price": h2.get("price"),
            },
        ],
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# DESCENDING TRIANGLE
# ============================================================

def detect_descending_triangle(
    swings,
    close
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    support_similarity = _distance(
        l1["price"],
        l2["price"]
    )

    if support_similarity > 0.025:
        return None

    if h2["price"] >= h1["price"]:
        return None

    support = (
        l1["price"] + l2["price"]
    ) / 2

    height = (
        max(h1["price"], h2["price"])
        -
        support
    )

    if height <= 0:
        return None

    confirmed = (
        close < support
    )

    invalid = (
        close > max(
            h1["price"],
            h2["price"]
        ) * (
            1 + INVALID_BREAK_BUFFER
        )
    )

    score = 78

    score += _similarity_score(
        support_similarity,
        0.025
    ) * 0.08

    score += 5

    score += _confirmation_bonus(
        confirmed
    )

    return _make_pattern(
        name="Descending Triangle",
        direction="BEARISH",
        quality=score,
        status=_build_status(
            confirmed,
            invalid
        ),
        reason=(
            "Flat support is combined "
            "with progressively lower "
            "major highs."
        ),
        entry=support,
        tp1=support - height,
        tp2=support - height * 1.5,
        sl=max(
            h1["price"],
            h2["price"]
        ) * 1.003,
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": l1.get("index"),
                "price": l1.get("price"),
            },
            {
                "index": l2.get("index"),
                "price": l2.get("price"),
            },
        ],
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# SYMMETRICAL TRIANGLE
# ============================================================

def detect_symmetrical_triangle(
    swings,
    close=None
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] < h1["price"]
        and
        l2["price"] > l1["price"]
    ):
        return None

    upper_range = (
        h1["price"] - h2["price"]
    )

    lower_range = (
        l2["price"] - l1["price"]
    )

    if upper_range <= 0 or lower_range <= 0:
        return None

    ratio = _safe_div(
        upper_range,
        lower_range
    )

    if ratio < 0.25 or ratio > 4:
        return None

    status = "FORMING"

    direction = "NEUTRAL"

    score = 78

    if close is not None:

        upper = _trendline_value(
            h1,
            h2,
            s[-1].get("index")
        )

        lower = _trendline_value(
            l1,
            l2,
            s[-1].get("index")
        )

        if upper is not None and close > upper:
            direction = "BULLISH"
            status = "CONFIRMED"

        elif lower is not None and close < lower:
            direction = "BEARISH"
            status = "CONFIRMED"

    return _make_pattern(
        name="Symmetrical Triangle",
        direction=direction,
        quality=score,
        status=status,
        reason=(
            "Lower highs and higher lows "
            "create a contracting price "
            "structure. Breakout direction "
            "must be confirmed."
        ),
        points=_pattern_points(s),
        neckline_points=[
            {
                "index": h1.get("index"),
                "price": h1.get("price"),
            },
            {
                "index": h2.get("index"),
                "price": h2.get("price"),
            },
            {
                "index": l1.get("index"),
                "price": l1.get("price"),
            },
            {
                "index": l2.get("index"),
                "price": l2.get("price"),
            },
        ],
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# RISING WEDGE
# ============================================================

def detect_rising_wedge(
    swings,
    close
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] > h1["price"]
        and
        l2["price"] > l1["price"]
    ):
        return None

    high_move = h2["price"] - h1["price"]
    low_move = l2["price"] - l1["price"]

    if high_move <= 0 or low_move <= 0:
        return None

    if low_move <= high_move:
        return None

    confirmed = (
        close < _trendline_value(
            l1,
            l2,
            s[-1].get("index")
        )
    )

    return _make_pattern(
        name="Rising Wedge",
        direction="BEARISH",
        quality=82 if confirmed else 76,
        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),
        reason=(
            "Both highs and lows rise, but "
            "the lower boundary advances "
            "faster, producing a narrowing "
            "rising structure."
        ),
        points=_pattern_points(s),
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# FALLING WEDGE
# ============================================================

def detect_falling_wedge(
    swings,
    close
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] < h1["price"]
        and
        l2["price"] < l1["price"]
    ):
        return None

    high_move = h1["price"] - h2["price"]
    low_move = l1["price"] - l2["price"]

    if high_move <= 0 or low_move <= 0:
        return None

    if low_move <= high_move:
        return None

    upper = _trendline_value(
        h1,
        h2,
        s[-1].get("index")
    )

    confirmed = (
        upper is not None
        and close > upper
    )

    return _make_pattern(
        name="Falling Wedge",
        direction="BULLISH",
        quality=82 if confirmed else 76,
        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),
        reason=(
            "Both highs and lows fall, "
            "while the lower boundary "
            "contracts faster, producing "
            "a narrowing falling structure."
        ),
        points=_pattern_points(s),
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# RECTANGLE
# ============================================================

def detect_rectangle(
    swings,
    close
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if _types(s) not in [
        [
            "HIGH",
            "LOW",
            "HIGH",
            "LOW",
        ],
        [
            "LOW",
            "HIGH",
            "LOW",
            "HIGH",
        ],
    ]:
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if len(highs) != 2 or len(lows) != 2:
        return None

    resistance = (
        highs[0]["price"]
        +
        highs[1]["price"]
    ) / 2

    support = (
        lows[0]["price"]
        +
        lows[1]["price"]
    ) / 2

    if resistance <= support:
        return None

    high_similarity = _distance(
        highs[0]["price"],
        highs[1]["price"]
    )

    low_similarity = _distance(
        lows[0]["price"],
        lows[1]["price"]
    )

    if (
        high_similarity > 0.03
        or
        low_similarity > 0.03
    ):
        return None

    height = resistance - support

    if close > resistance:
        direction = "BULLISH"
        status = "CONFIRMED"

    elif close < support:
        direction = "BEARISH"
        status = "CONFIRMED"

    else:
        direction = "NEUTRAL"
        status = "FORMING"

    return _make_pattern(
        name="Rectangle",
        direction=direction,
        quality=80 if status == "CONFIRMED" else 72,
        status=status,
        reason=(
            "Price is respecting a clear "
            "horizontal resistance and "
            "support range."
        ),
        entry=(
            resistance
            if direction == "BULLISH"
            else support
            if direction == "BEARISH"
            else None
        ),
        tp1=(
            resistance + height
            if direction == "BULLISH"
            else support - height
            if direction == "BEARISH"
            else None
        ),
        tp2=(
            resistance + height * 1.5
            if direction == "BULLISH"
            else support - height * 1.5
            if direction == "BEARISH"
            else None
        ),
        sl=(
            support * 0.997
            if direction == "BULLISH"
            else resistance * 1.003
            if direction == "BEARISH"
            else None
        ),
        points=_pattern_points(s),
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# MAIN DETECTOR
# ============================================================

def detect_patterns(df):

    if df is None:
        return []

    swings = df.attrs.get(
        "major_swings",
        []
    )

    if len(swings) < 3:
        return []

    try:
        close = float(
            df["close"].iloc[-1]
        )
    except Exception:
        return []

    detectors = [

        detect_double_top,

        detect_double_bottom,

        detect_triple_top,

        detect_triple_bottom,

        detect_head_shoulders,

        detect_inverse_head_shoulders,

        detect_ascending_triangle,

        detect_descending_triangle,

        detect_symmetrical_triangle,

        detect_rising_wedge,

        detect_falling_wedge,

        detect_rectangle,
    ]

    detected = []

    for detector in detectors:

        try:

            if detector == detect_symmetrical_triangle:

                result = detector(
                    swings,
                    close
                )

            else:

                result = detector(
                    swings,
                    close
                )

            if result is None:
                continue

            if (
                result["quality"]
                < MIN_PATTERN_SCORE
            ):
                continue

            detected.append(result)

        except Exception:
            continue

    # --------------------------------------------------------
    # Remove invalid patterns
    # --------------------------------------------------------

    detected = [
        p
        for p in detected
        if p["status"] != "INVALID"
    ]

    # --------------------------------------------------------
    # Rank strongest / latest structures
    # --------------------------------------------------------

    def ranking_score(pattern):

        score = float(
            pattern.get(
                "quality",
                0
            )
        )

        status = pattern.get(
            "status"
        )

        if status == "CONFIRMED":
            score += 12

        elif status == "FORMING":
            score += 3

        if pattern.get(
            "pattern_end"
        ) is not None:

            score += 2

        return score

    detected.sort(
        key=ranking_score,
        reverse=True
    )

    return detected


# ============================================================
# BEST PATTERN
# ============================================================

def get_best_pattern(df):

    patterns = detect_patterns(df)

    if not patterns:
        return None

    return patterns[0]


# ============================================================
# CONFIRMED PATTERNS ONLY
# ============================================================

def get_confirmed_patterns(df):

    patterns = detect_patterns(df)

    return [
        p
        for p in patterns
        if p["status"] == "CONFIRMED"
    ]


# ============================================================
# LATEST / ACTIVE PATTERNS
# ============================================================

def get_latest_patterns(df):

    patterns = detect_patterns(df)

    if not patterns:
        return []

    latest_end = max(
        [
            p.get("pattern_end")
            for p in patterns
            if p.get("pattern_end") is not None
        ],
        default=None
    )

    if latest_end is None:
        return patterns

    latest = [
        p
        for p in patterns
        if p.get("pattern_end") == latest_end
    ]

    return latest or patterns
