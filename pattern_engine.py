# ============================================================
# MOBILE ANALYZER
# PATTERN_ENGINE.PY
# PROFESSIONAL MAJOR SWING CHART PATTERN ENGINE
# STRICT 9-PATTERN STRUCTURAL VALIDATION
#
# ORDER LOGIC:
# FORMING:
#   entry = None
#   tp1   = None
#   tp2   = None
#   sl    = None
#
# CONFIRMED BULLISH:
#   SL < ENTRY < TP1 < TP2
#
# CONFIRMED BEARISH:
#   TP2 < TP1 < ENTRY < SL
#
# ENTRY = actual close of the candle that confirms breakout.
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

MIN_REACTION_RATIO = 0.20

TRIANGLE_FLAT_TOLERANCE = 0.025
TRIANGLE_MIN_SLOPE_RATIO = 0.12
WEDGE_MIN_CONVERGENCE = 0.10
WEDGE_MAX_SLOPE_RATIO = 8.0
MIN_HS_HEAD_RATIO = 0.10
MIN_HS_NECK_DEPTH = 0.20


# ============================================================
# BASIC HELPERS
# ============================================================

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


def _types(swings):
    return [x.get("type") for x in swings]


def _pattern_points(items):
    return [
        {
            "index": x.get("index"),
            "price": x.get("price"),
            "type": x.get("type"),
        }
        for x in items
    ]


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

    return _clamp(
        100 - distance / maximum * 100
    )


def _confirmation_bonus(confirmed):
    return 10 if confirmed else 0


def _build_status(confirmed, invalid=False):
    if invalid:
        return "INVALID"

    return "CONFIRMED" if confirmed else "FORMING"


def _valid_index_pair(a, b):
    try:
        return (
            a.get("index") is not None
            and b.get("index") is not None
            and b["index"] > a["index"]
        )
    except Exception:
        return False


def _leg_size(a, b):
    pa = _price(a.get("price"))
    pb = _price(b.get("price"))

    if pa is None or pb is None:
        return 0.0

    return abs(pb - pa)


def _reaction_ratio(first, reaction, second):
    a = _price(first.get("price"))
    r = _price(reaction.get("price"))
    b = _price(second.get("price"))

    if a is None or r is None or b is None:
        return 0.0

    base = (a + b) / 2.0

    distance = abs(r - base)

    pattern_height = max(
        abs(r - a),
        abs(r - b),
        abs(base),
        1e-12,
    )

    return distance / pattern_height


def _meaningful_reaction(
    first,
    reaction,
    second,
    min_ratio=MIN_REACTION_RATIO,
):
    return (
        _reaction_ratio(
            first,
            reaction,
            second,
        )
        >= min_ratio
    )


def _strict_alternating_points(s):
    if len(s) < 2:
        return False

    for i in range(1, len(s)):

        if (
            s[i].get("type")
            == s[i - 1].get("type")
        ):
            return False

        if not _valid_index_pair(
            s[i - 1],
            s[i],
        ):
            return False

    return True


def _same_level(p1, p2, tolerance):
    return (
        _distance(
            _price(p1["price"]),
            _price(p2["price"]),
        )
        <= tolerance
    )


def _strongly_higher(
    value,
    reference,
    minimum_ratio=MIN_HS_HEAD_RATIO,
):
    value = _price(value)
    reference = _price(reference)

    if (
        value is None
        or reference is None
        or reference == 0
    ):
        return False

    return (
        value - reference
    ) / abs(reference) >= minimum_ratio


def _strongly_lower(
    value,
    reference,
    minimum_ratio=MIN_HS_HEAD_RATIO,
):
    value = _price(value)
    reference = _price(reference)

    if (
        value is None
        or reference is None
        or reference == 0
    ):
        return False

    return (
        reference - value
    ) / abs(reference) >= minimum_ratio


# ============================================================
# ORDER / TARGET VALIDATION
# ============================================================

def _confirmed_order_levels(
    direction,
    close,
    structural_entry,
    height,
    structural_sl,
):
    """
    IMPORTANT:

    ENTRY:
        Actual candle close after breakout confirmation.

    TP1:
        ENTRY + pattern height for bullish.
        ENTRY - pattern height for bearish.

    TP2:
        ENTRY + 1.5 * height for bullish.
        ENTRY - 1.5 * height for bearish.

    SL:
        Structural invalidation level.

    Final validation guarantees:

        BULLISH:
            SL < ENTRY < TP1 < TP2

        BEARISH:
            TP2 < TP1 < ENTRY < SL
    """

    close = _price(close)
    structural_entry = _price(structural_entry)
    height = _price(height)
    structural_sl = _price(structural_sl)

    if close is None:
        return None, None, None, None

    if height is None or height <= 0:
        return None, None, None, None

    if structural_sl is None:
        return None, None, None, None

    # Keep structural entry available for compatibility/reference.
    _ = structural_entry

    entry = close

    if direction == "BULLISH":

        tp1 = entry + height
        tp2 = entry + (height * 1.5)

        sl = structural_sl

        # Safety:
        # SL can never be above or equal to actual entry.
        if sl >= entry:
            sl = entry - (height * 0.50)

        if not (
            sl < entry
            and entry < tp1
            and tp1 < tp2
        ):
            return None, None, None, None

        return entry, tp1, tp2, sl

    if direction == "BEARISH":

        tp1 = entry - height
        tp2 = entry - (height * 1.5)

        sl = structural_sl

        # Safety:
        # SL can never be below or equal to actual entry.
        if sl <= entry:
            sl = entry + (height * 0.50)

        if not (
            tp2 < tp1
            and tp1 < entry
            and entry < sl
        ):
            return None, None, None, None

        return entry, tp1, tp2, sl

    return None, None, None, None


def _make_confirmed_pattern(
    name,
    direction,
    quality,
    reason,
    close,
    structural_entry,
    height,
    structural_sl,
    points=None,
    neckline_points=None,
    pattern_start=None,
    pattern_end=None,
):
    (
        entry,
        tp1,
        tp2,
        sl,
    ) = _confirmed_order_levels(
        direction=direction,
        close=close,
        structural_entry=structural_entry,
        height=height,
        structural_sl=structural_sl,
    )

    if entry is None:
        return None

    return _make_pattern(
        name=name,
        direction=direction,
        quality=quality,
        status="CONFIRMED",
        reason=reason,
        entry=entry,
        tp1=tp1,
        tp2=tp2,
        sl=sl,
        points=points,
        neckline_points=neckline_points,
        pattern_start=pattern_start,
        pattern_end=pattern_end,
    )


def _make_forming_pattern(
    name,
    direction,
    quality,
    reason,
    points=None,
    neckline_points=None,
    pattern_start=None,
    pattern_end=None,
):
    return _make_pattern(
        name=name,
        direction=direction,
        quality=quality,
        status="FORMING",
        reason=reason,
        entry=None,
        tp1=None,
        tp2=None,
        sl=None,
        points=points,
        neckline_points=neckline_points,
        pattern_start=pattern_start,
        pattern_end=pattern_end,
    )


# ============================================================
# TRIPLE STRUCTURES
# ============================================================

def _triple_bottom_structure(s):

    if (
        len(s) != 5
        or not _strict_alternating_points(s)
    ):
        return False

    return (
        _meaningful_reaction(
            s[0], s[1], s[2]
        )
        and _meaningful_reaction(
            s[2], s[3], s[4]
        )
        and s[1]["price"]
        > max(
            s[0]["price"],
            s[2]["price"],
        )
        and s[3]["price"]
        > max(
            s[2]["price"],
            s[4]["price"],
        )
    )


def _triple_top_structure(s):

    if (
        len(s) != 5
        or not _strict_alternating_points(s)
    ):
        return False

    return (
        _meaningful_reaction(
            s[0], s[1], s[2]
        )
        and _meaningful_reaction(
            s[2], s[3], s[4]
        )
        and s[1]["price"]
        < min(
            s[0]["price"],
            s[2]["price"],
        )
        and s[3]["price"]
        < min(
            s[2]["price"],
            s[4]["price"],
        )
    )


# ============================================================
# 1. DOUBLE TOP
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

    if not _strict_alternating_points(s):
        return None

    a, b, c = s

    similarity = _distance(
        a["price"],
        c["price"],
    )

    if similarity > SIMILARITY_DOUBLE:
        return None

    if not _meaningful_reaction(
        a,
        b,
        c,
    ):
        return None

    top_avg = (
        a["price"]
        + c["price"]
    ) / 2.0

    reaction_depth = (
        top_avg - b["price"]
    ) / max(
        top_avg,
        1e-12,
    )

    if reaction_depth < MIN_REACTION_RATIO:
        return None

    neckline = b["price"]
    peak = max(
        a["price"],
        c["price"],
    )

    height = peak - neckline

    if height <= 0:
        return None

    confirmed = _bearish_confirmation(
        close,
        neckline,
    )

    invalid = (
        close
        > peak * (
            1 + INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        76
        + _similarity_score(
            similarity,
            SIMILARITY_DOUBLE,
        ) * 0.14
        + _confirmation_bonus(
            confirmed
        )
    )

    if confirmed:

        return _make_confirmed_pattern(
            "Double Top",
            "BEARISH",
            score,
            "Two major highs are closely matched and separated by a meaningful bearish reaction.",
            close,
            neckline,
            height,
            peak * 1.003,
            _pattern_points(s),
            [
                {
                    "index": b.get("index"),
                    "price": neckline,
                }
            ],
            a.get("index"),
            c.get("index"),
        )

    return _make_forming_pattern(
        "Double Top",
        "BEARISH",
        score,
        "Two major highs are closely matched and separated by a meaningful bearish reaction. Waiting for neckline confirmation.",
        _pattern_points(s),
        [
            {
                "index": b.get("index"),
                "price": neckline,
            }
        ],
        a.get("index"),
        c.get("index"),
    )


# ============================================================
# 2. DOUBLE BOTTOM
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

    if not _strict_alternating_points(s):
        return None

    a, b, c = s

    similarity = _distance(
        a["price"],
        c["price"],
    )

    if similarity > SIMILARITY_DOUBLE:
        return None

    if not _meaningful_reaction(
        a,
        b,
        c,
    ):
        return None

    bottom_avg = (
        a["price"]
        + c["price"]
    ) / 2.0

    reaction_height = (
        b["price"]
        - bottom_avg
    ) / max(
        bottom_avg,
        1e-12,
    )

    if reaction_height < MIN_REACTION_RATIO:
        return None

    neckline = b["price"]
    bottom = min(
        a["price"],
        c["price"],
    )

    height = neckline - bottom

    if height <= 0:
        return None

    confirmed = _bullish_confirmation(
        close,
        neckline,
    )

    invalid = (
        close
        < bottom * (
            1 - INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        76
        + _similarity_score(
            similarity,
            SIMILARITY_DOUBLE,
        ) * 0.14
        + _confirmation_bonus(
            confirmed
        )
    )

    if confirmed:

        return _make_confirmed_pattern(
            "Double Bottom",
            "BULLISH",
            score,
            "Two major lows are closely matched and separated by a meaningful bullish reaction.",
            close,
            neckline,
            height,
            bottom * 0.997,
            _pattern_points(s),
            [
                {
                    "index": b.get("index"),
                    "price": neckline,
                }
            ],
            a.get("index"),
            c.get("index"),
        )

    return _make_forming_pattern(
        "Double Bottom",
        "BULLISH",
        score,
        "Two major lows are closely matched and separated by a meaningful bullish reaction. Waiting for neckline confirmation.",
        _pattern_points(s),
        [
            {
                "index": b.get("index"),
                "price": neckline,
            }
        ],
        a.get("index"),
        c.get("index"),
    )


# ============================================================
# 3. HEAD & SHOULDERS
# ============================================================

def detect_head_shoulders(
    swings,
    close,
):

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

    if not _strict_alternating_points(s):
        return None

    (
        left,
        neck1,
        head,
        neck2,
        right,
    ) = s

    shoulder_similarity = _distance(
        left["price"],
        right["price"],
    )

    if (
        shoulder_similarity
        > SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"]
        > left["price"]
        and head["price"]
        > right["price"]
    ):
        return None

    if not (
        _strongly_higher(
            head["price"],
            left["price"],
        )
        and _strongly_higher(
            head["price"],
            right["price"],
        )
    ):
        return None

    shoulder_avg = (
        left["price"]
        + right["price"]
    ) / 2.0

    neckline_avg = (
        neck1["price"]
        + neck2["price"]
    ) / 2.0

    if neckline_avg >= shoulder_avg:
        return None

    neck_depth = (
        shoulder_avg
        - neckline_avg
    ) / max(
        shoulder_avg,
        1e-12,
    )

    if neck_depth < MIN_HS_NECK_DEPTH:
        return None

    if (
        neck1["price"]
        >= min(
            left["price"],
            head["price"],
        )
    ):
        return None

    if (
        neck2["price"]
        >= min(
            head["price"],
            right["price"],
        )
    ):
        return None

    neckline = neckline_avg
    height = head["price"] - neckline

    if height <= 0:
        return None

    confirmed = _bearish_confirmation(
        close,
        neckline,
    )

    invalid = (
        close
        > head["price"]
        * (
            1
            + INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        84
        + _similarity_score(
            shoulder_similarity,
            SIMILARITY_SHOULDER,
        ) * 0.10
        + 3
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": neck1.get("index"),
            "price": neck1.get("price"),
        },
        {
            "index": neck2.get("index"),
            "price": neck2.get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Head & Shoulders",
            "BEARISH",
            score,
            "Both shoulders are similar, the head is materially higher, and the neckline has been confirmed.",
            close,
            neckline,
            height,
            head["price"] * 1.003,
            _pattern_points(s),
            neckline_points,
            left.get("index"),
            right.get("index"),
        )

    return _make_forming_pattern(
        "Head & Shoulders",
        "BEARISH",
        score,
        "Both shoulders are similar and the head is materially higher. Waiting for neckline confirmation.",
        _pattern_points(s),
        neckline_points,
        left.get("index"),
        right.get("index"),
    )


# ============================================================
# 4. INVERSE HEAD & SHOULDERS
# ============================================================

def detect_inverse_head_shoulders(
    swings,
    close,
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

    if not _strict_alternating_points(s):
        return None

    (
        left,
        neck1,
        head,
        neck2,
        right,
    ) = s

    shoulder_similarity = _distance(
        left["price"],
        right["price"],
    )

    if (
        shoulder_similarity
        > SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"]
        < left["price"]
        and head["price"]
        < right["price"]
    ):
        return None

    if not (
        _strongly_lower(
            head["price"],
            left["price"],
        )
        and _strongly_lower(
            head["price"],
            right["price"],
        )
    ):
        return None

    shoulder_avg = (
        left["price"]
        + right["price"]
    ) / 2.0

    neckline_avg = (
        neck1["price"]
        + neck2["price"]
    ) / 2.0

    if neckline_avg <= shoulder_avg:
        return None

    neck_height = (
        neckline_avg
        - shoulder_avg
    ) / max(
        abs(shoulder_avg),
        1e-12,
    )

    if neck_height < MIN_HS_NECK_DEPTH:
        return None

    if (
        neck1["price"]
        <= max(
            left["price"],
            head["price"],
        )
    ):
        return None

    if (
        neck2["price"]
        <= max(
            head["price"],
            right["price"],
        )
    ):
        return None

    neckline = neckline_avg
    height = neckline - head["price"]

    if height <= 0:
        return None

    confirmed = _bullish_confirmation(
        close,
        neckline,
    )

    invalid = (
        close
        < head["price"]
        * (
            1
            - INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        84
        + _similarity_score(
            shoulder_similarity,
            SIMILARITY_SHOULDER,
        ) * 0.10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": neck1.get("index"),
            "price": neck1.get("price"),
        },
        {
            "index": neck2.get("index"),
            "price": neck2.get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Inverse Head & Shoulders",
            "BULLISH",
            score,
            "Both shoulders are similar, the head is materially lower, and the neckline has been confirmed.",
            close,
            neckline,
            height,
            head["price"] * 0.997,
            _pattern_points(s),
            neckline_points,
            left.get("index"),
            right.get("index"),
        )

    return _make_forming_pattern(
        "Inverse Head & Shoulders",
        "BULLISH",
        score,
        "Both shoulders are similar and the head is materially lower. Waiting for neckline confirmation.",
        _pattern_points(s),
        neckline_points,
        left.get("index"),
        right.get("index"),
    )


# ============================================================
# 5. ASCENDING TRIANGLE
# ============================================================

def detect_ascending_triangle(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    h1, h2 = highs
    l1, l2 = lows

    high_similarity = _distance(
        h1["price"],
        h2["price"],
    )

    if (
        high_similarity
        > TRIANGLE_FLAT_TOLERANCE
    ):
        return None

    low_base = max(
        abs(l1["price"]),
        1e-12,
    )

    low_rise = (
        l2["price"]
        - l1["price"]
    ) / low_base

    if (
        low_rise
        < TRIANGLE_MIN_SLOPE_RATIO
    ):
        return None

    if l2["price"] <= l1["price"]:
        return None

    resistance = (
        h1["price"]
        + h2["price"]
    ) / 2.0

    support_low = min(
        l1["price"],
        l2["price"],
    )

    height = resistance - support_low

    if height <= 0:
        return None

    if l2["price"] >= resistance:
        return None

    confirmed = _bullish_confirmation(
        close,
        resistance,
    )

    invalid = (
        close
        < l1["price"]
        * (
            1
            - INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        78
        + _similarity_score(
            high_similarity,
            TRIANGLE_FLAT_TOLERANCE,
        ) * 0.08
        + 5
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": h1.get("index"),
            "price": h1.get("price"),
        },
        {
            "index": h2.get("index"),
            "price": h2.get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Ascending Triangle",
            "BULLISH",
            score,
            "Flat resistance and materially higher major lows are confirmed by an upside breakout.",
            close,
            resistance,
            height,
            support_low * 0.997,
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    return _make_forming_pattern(
        "Ascending Triangle",
        "BULLISH",
        score,
        "Flat resistance is present together with materially higher major lows. Waiting for upside breakout.",
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
    )


# ============================================================
# 6. DESCENDING TRIANGLE
# ============================================================

def detect_descending_triangle(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    h1, h2 = highs
    l1, l2 = lows

    low_similarity = _distance(
        l1["price"],
        l2["price"],
    )

    if (
        low_similarity
        > TRIANGLE_FLAT_TOLERANCE
    ):
        return None

    high_base = max(
        abs(h1["price"]),
        1e-12,
    )

    high_drop = (
        h1["price"]
        - h2["price"]
    ) / high_base

    if (
        high_drop
        < TRIANGLE_MIN_SLOPE_RATIO
    ):
        return None

    if h2["price"] >= h1["price"]:
        return None

    support = (
        l1["price"]
        + l2["price"]
    ) / 2.0

    resistance_high = max(
        h1["price"],
        h2["price"],
    )

    height = (
        resistance_high
        - support
    )

    if height <= 0:
        return None

    if h2["price"] <= support:
        return None

    confirmed = _bearish_confirmation(
        close,
        support,
    )

    invalid = (
        close
        > resistance_high
        * (
            1
            + INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        78
        + _similarity_score(
            low_similarity,
            TRIANGLE_FLAT_TOLERANCE,
        ) * 0.08
        + 5
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": l1.get("index"),
            "price": l1.get("price"),
        },
        {
            "index": l2.get("index"),
            "price": l2.get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Descending Triangle",
            "BEARISH",
            score,
            "Flat support and materially lower major highs are confirmed by a downside breakout.",
            close,
            support,
            height,
            resistance_high * 1.003,
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    return _make_forming_pattern(
        "Descending Triangle",
        "BEARISH",
        score,
        "Flat support is present together with materially lower major highs. Waiting for downside breakout.",
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
        return _make_confirmed_pattern(
            "Descending Triangle",
            "BEARISH",
            score,
            "Flat support and materially lower major highs are confirmed by a downside breakout.",
            close,
            support,
            height,
            resistance_high * 1.003,
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    return _make_forming_pattern(
        "Descending Triangle",
        "BEARISH",
        score,
        "Flat support is present together with materially lower major highs. Waiting for downside breakout.",
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
    )


# ============================================================
# 7. SYMMETRICAL TRIANGLE
# ============================================================

def detect_symmetrical_triangle(
    swings,
    close=None,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] < h1["price"]
        and l2["price"] > l1["price"]
    ):
        return None

    upper_move = (
        h1["price"]
        - h2["price"]
    )

    lower_move = (
        l2["price"]
        - l1["price"]
    )

    if (
        upper_move <= 0
        or lower_move <= 0
    ):
        return None

    upper_ratio = (
        upper_move
        / max(
            abs(h1["price"]),
            1e-12,
        )
    )

    lower_ratio = (
        lower_move
        / max(
            abs(l1["price"]),
            1e-12,
        )
    )

    if (
        upper_ratio
        < TRIANGLE_MIN_SLOPE_RATIO
    ):
        return None

    if (
        lower_ratio
        < TRIANGLE_MIN_SLOPE_RATIO
    ):
        return None

    slope_ratio = (
        upper_ratio
        / max(
            lower_ratio,
            1e-12,
        )
    )

    if (
        slope_ratio < 0.25
        or slope_ratio > 4.0
    ):
        return None

    first_range = abs(
        h1["price"]
        - l1["price"]
    )

    last_range = abs(
        h2["price"]
        - l2["price"]
    )

    if first_range <= 0:
        return None

    contraction = (
        first_range
        - last_range
    ) / first_range

    if contraction < 0.10:
        return None

    upper_now = _trendline_value(
        h1,
        h2,
        s[-1].get("index"),
    )

    lower_now = _trendline_value(
        l1,
        l2,
        s[-1].get("index"),
    )

    direction = "NEUTRAL"
    confirmed = False

    if close is not None:

        if (
            upper_now is not None
            and close
            > upper_now
            * (
                1
                + BREAK_CONFIRM_BUFFER
            )
        ):
            direction = "BULLISH"
            confirmed = True

        elif (
            lower_now is not None
            and close
            < lower_now
            * (
                1
                - BREAK_CONFIRM_BUFFER
            )
        ):
            direction = "BEARISH"
            confirmed = True

    score = (
        78
        + contraction * 10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
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
    ]

    if not confirmed:

        return _make_forming_pattern(
            "Symmetrical Triangle",
            "NEUTRAL",
            score,
            "Lower highs and higher lows both contract toward each other. Waiting for a confirmed breakout.",
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    if direction == "BULLISH":
        structural_entry = upper_now
        structural_sl = lower_now

    else:
        structural_entry = lower_now
        structural_sl = upper_now

    return _make_confirmed_pattern(
        "Symmetrical Triangle",
        direction,
        score,
        "The symmetrical triangle has contracted and the latest candle has confirmed the breakout.",
        close,
        structural_entry,
        first_range,
        structural_sl,
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
    )


# ============================================================
# 8. RISING WEDGE
# ============================================================

def detect_rising_wedge(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] > h1["price"]
        and l2["price"] > l1["price"]
    ):
        return None

    upper_move = (
        h2["price"]
        - h1["price"]
    )

    lower_move = (
        l2["price"]
        - l1["price"]
    )

    if (
        upper_move <= 0
        or lower_move <= 0
    ):
        return None

    upper_ratio = (
        upper_move
        / max(
            abs(h1["price"]),
            1e-12,
        )
    )

    lower_ratio = (
        lower_move
        / max(
            abs(l1["price"]),
            1e-12,
        )
    )

    if (
        upper_ratio <= 0
        or lower_ratio <= 0
    ):
        return None

    if lower_ratio <= upper_ratio:
        return None

    slope_ratio = (
        lower_ratio
        / max(
            upper_ratio,
            1e-12,
        )
    )

    if slope_ratio > WEDGE_MAX_SLOPE_RATIO:
        return None

    first_range = abs(
        h1["price"]
        - l1["price"]
    )

    last_range = abs(
        h2["price"]
        - l2["price"]
    )

    if first_range <= 0:
        return None

    contraction = (
        first_range
        - last_range
    ) / first_range

    if (
        contraction
        < WEDGE_MIN_CONVERGENCE
    ):
        return None

    upper_now = _trendline_value(
        h1,
        h2,
        s[-1].get("index"),
    )

    lower_now = _trendline_value(
        l1,
        l2,
        s[-1].get("index"),
    )

    confirmed = (
        lower_now is not None
        and close
        < lower_now
        * (
            1
            - BREAK_CONFIRM_BUFFER
        )
    )

    score = (
        76
        + contraction * 10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
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
    ]

    if not confirmed:

        return _make_forming_pattern(
            "Rising Wedge",
            "BEARISH",
            score,
            "Both boundaries rise, but the lower boundary rises faster and the structure must visibly contract. Waiting for downside breakout.",
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    return _make_confirmed_pattern(
        "Rising Wedge",
        "BEARISH",
        score,
        "The rising wedge has contracted and the latest candle has confirmed a downside breakout.",
        close,
        lower_now,
        first_range,
        upper_now,
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
        # ============================================================
# 9. FALLING WEDGE
# ============================================================

def detect_falling_wedge(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    h1, h2 = highs
    l1, l2 = lows

    if not (
        h2["price"] < h1["price"]
        and l2["price"] < l1["price"]
    ):
        return None

    upper_move = (
        h1["price"]
        - h2["price"]
    )

    lower_move = (
        l1["price"]
        - l2["price"]
    )

    if (
        upper_move <= 0
        or lower_move <= 0
    ):
        return None

    upper_ratio = (
        upper_move
        / max(
            abs(h1["price"]),
            1e-12,
        )
    )

    lower_ratio = (
        lower_move
        / max(
            abs(l1["price"]),
            1e-12,
        )
    )

    if (
        upper_ratio <= 0
        or lower_ratio <= 0
    ):
        return None

    if upper_ratio <= lower_ratio:
        return None

    slope_ratio = (
        upper_ratio
        / max(
            lower_ratio,
            1e-12,
        )
    )

    if slope_ratio > WEDGE_MAX_SLOPE_RATIO:
        return None

    first_range = abs(
        h1["price"]
        - l1["price"]
    )

    last_range = abs(
        h2["price"]
        - l2["price"]
    )

    if first_range <= 0:
        return None

    contraction = (
        first_range
        - last_range
    ) / first_range

    if (
        contraction
        < WEDGE_MIN_CONVERGENCE
    ):
        return None

    upper_now = _trendline_value(
        h1,
        h2,
        s[-1].get("index"),
    )

    lower_now = _trendline_value(
        l1,
        l2,
        s[-1].get("index"),
    )

    confirmed = (
        upper_now is not None
        and close
        > upper_now
        * (
            1
            + BREAK_CONFIRM_BUFFER
        )
    )

    score = (
        76
        + contraction * 10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
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
    ]

    if not confirmed:

        return _make_forming_pattern(
            "Falling Wedge",
            "BULLISH",
            score,
            "Both boundaries fall, but the upper boundary falls faster and the structure must visibly contract. Waiting for upside breakout.",
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[-1].get("index"),
        )

    return _make_confirmed_pattern(
        "Falling Wedge",
        "BULLISH",
        score,
        "The falling wedge has contracted and the latest candle has confirmed an upside breakout.",
        close,
        upper_now,
        first_range,
        lower_now,
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[-1].get("index"),
    )


# ============================================================
# COMPATIBILITY: TRIPLE TOP
# ============================================================

def detect_triple_top(
    swings,
    close,
):

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

    if not _triple_top_structure(s):
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

    average_high = sum(highs) / 3.0

    spread = (
        max(highs)
        - min(highs)
    ) / max(
        average_high,
        1e-12,
    )

    if spread > SIMILARITY_TRIPLE:
        return None

    neckline = min(lows)
    peak = max(highs)

    height = peak - neckline

    if height <= 0:
        return None

    confirmed = close < neckline

    invalid = (
        close
        > peak
        * (
            1
            + INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        82
        + _similarity_score(
            spread,
            SIMILARITY_TRIPLE,
        ) * 0.10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": s[1].get("index"),
            "price": s[1].get("price"),
        },
        {
            "index": s[3].get("index"),
            "price": s[3].get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Triple Top",
            "BEARISH",
            score,
            "Three matched highs with meaningful reactions between them.",
            close,
            neckline,
            height,
            peak * 1.003,
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[4].get("index"),
        )

    return _make_forming_pattern(
        "Triple Top",
        "BEARISH",
        score,
        "Three matched highs with meaningful reactions between them. Waiting for neckline confirmation.",
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[4].get("index"),
    )


# ============================================================
# COMPATIBILITY: TRIPLE BOTTOM
# ============================================================

def detect_triple_bottom(
    swings,
    close,
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

    if not _triple_bottom_structure(s):
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

    average_low = sum(lows) / 3.0

    spread = (
        max(lows)
        - min(lows)
    ) / max(
        average_low,
        1e-12,
    )

    if spread > SIMILARITY_TRIPLE:
        return None

    neckline = max(highs)
    bottom = min(lows)

    height = neckline - bottom

    if height <= 0:
        return None

    confirmed = close > neckline

    invalid = (
        close
        < bottom
        * (
            1
            - INVALID_BREAK_BUFFER
        )
    )

    if invalid:
        return None

    score = (
        82
        + _similarity_score(
            spread,
            SIMILARITY_TRIPLE,
        ) * 0.10
        + _confirmation_bonus(
            confirmed
        )
    )

    neckline_points = [
        {
            "index": s[1].get("index"),
            "price": s[1].get("price"),
        },
        {
            "index": s[3].get("index"),
            "price": s[3].get("price"),
        },
    ]

    if confirmed:

        return _make_confirmed_pattern(
            "Triple Bottom",
            "BULLISH",
            score,
            "Three matched lows with meaningful reactions between them.",
            close,
            neckline,
            height,
            bottom * 0.997,
            _pattern_points(s),
            neckline_points,
            s[0].get("index"),
            s[4].get("index"),
        )

    return _make_forming_pattern(
        "Triple Bottom",
        "BULLISH",
        score,
        "Three matched lows with meaningful reactions between them. Waiting for neckline confirmation.",
        _pattern_points(s),
        neckline_points,
        s[0].get("index"),
        s[4].get("index"),
    )
   # ============================================================
# COMPATIBILITY: RECTANGLE
# ============================================================

def detect_rectangle(
    swings,
    close,
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

    if not _strict_alternating_points(s):
        return None

    highs = [
        x for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in s
        if x["type"] == "LOW"
    ]

    if (
        len(highs) != 2
        or len(lows) != 2
    ):
        return None

    resistance = (
        highs[0]["price"]
        + highs[1]["price"]
    ) / 2.0

    support = (
        lows[0]["price"]
        + lows[1]["price"]
    ) / 2.0

    if resistance <= support:
        return None

    if (
        _distance(
            highs[0]["price"],
            highs[1]["price"],
        )
        > 0.03
    ):
        return None

    if (
        _distance(
            lows[0]["price"],
            lows[1]["price"],
        )
        > 0.03
    ):
        return None

    height = resistance - support

    if close > resistance:

        return _make_confirmed_pattern(
            "Rectangle",
            "BULLISH",
            90,
            "Price has confirmed a bullish breakout from the horizontal range.",
            close,
            resistance,
            height,
            support * 0.997,
            _pattern_points(s),
            pattern_start=s[0].get("index"),
            pattern_end=s[-1].get("index"),
        )

    if close < support:

        return _make_confirmed_pattern(
            "Rectangle",
            "BEARISH",
            90,
            "Price has confirmed a bearish breakout from the horizontal range.",
            close,
            support,
            height,
            resistance * 1.003,
            _pattern_points(s),
            pattern_start=s[0].get("index"),
            pattern_end=s[-1].get("index"),
        )

    return _make_forming_pattern(
        "Rectangle",
        "NEUTRAL",
        72,
        "Price is respecting a clear horizontal resistance and support range. Waiting for breakout.",
        _pattern_points(s),
        pattern_start=s[0].get("index"),
        pattern_end=s[-1].get("index"),
    )


# ============================================================
# STRICT 9 DETECTORS
# ============================================================

STRICT_9_DETECTORS = [

    detect_double_top,

    detect_double_bottom,

    detect_head_shoulders,

    detect_inverse_head_shoulders,

    detect_ascending_triangle,

    detect_descending_triangle,

    detect_symmetrical_triangle,

    detect_rising_wedge,

    detect_falling_wedge,

]


# ============================================================
# PATTERN AGE
# ============================================================

def _pattern_age_is_valid(
    pattern,
    current_index,
):

    if pattern.get(
        "pattern_end"
    ) is None:
        return True

    try:

        age = (
            current_index
            - pattern["pattern_end"]
        )

        return age <= MAX_PATTERN_AGE

    except Exception:

        return True


# ============================================================
# FINAL ORDER SAFETY
# ============================================================

def _orders_are_logical(pattern):

    """
    Final independent protection.

    FORMING:
        No order levels.

    CONFIRMED BULLISH:
        SL < ENTRY < TP1 < TP2

    CONFIRMED BEARISH:
        TP2 < TP1 < ENTRY < SL
    """

    status = pattern.get(
        "status"
    )

    direction = pattern.get(
        "direction"
    )

    entry = _price(
        pattern.get("entry")
    )

    tp1 = _price(
        pattern.get("tp1")
    )

    tp2 = _price(
        pattern.get("tp2")
    )

    sl = _price(
        pattern.get("sl")
    )

    # FORMING must NEVER carry an order.
    if status == "FORMING":

        return (
            entry is None
            and tp1 is None
            and tp2 is None
            and sl is None
        )

    if status != "CONFIRMED":
        return False

    if None in (
        entry,
        tp1,
        tp2,
        sl,
    ):
        return False

    if direction == "BULLISH":

        return (
            sl
            < entry
            < tp1
            < tp2
        )

    if direction == "BEARISH":

        return (
            tp2
            < tp1
            < entry
            < sl
        )

    return False


# ============================================================
# MAIN DETECTOR
# ============================================================

def detect_patterns(df):

    if df is None:
        return []

    swings = df.attrs.get(
        "major_swings",
        [],
    )

    if len(swings) < 3:
        return []

    try:

        close = float(
            df["close"].iloc[-1]
        )

    except Exception:

        return []

    try:

        current_index = (
            len(df) - 1
        )

    except Exception:

        current_index = None

    detected = []

    for detector in STRICT_9_DETECTORS:

        try:

            result = detector(
                swings,
                close,
            )

            if result is None:
                continue

            if (
                result.get(
                    "quality",
                    0,
                )
                < MIN_PATTERN_SCORE
            ):
                continue

            if (
                result.get("status")
                == "INVALID"
            ):
                continue

            if (
                current_index
                is not None
            ):

                if not _pattern_age_is_valid(
                    result,
                    current_index,
                ):
                    continue

            # FINAL ORDER SAFETY
            if not _orders_are_logical(
                result
            ):
                continue

            detected.append(result)

        except Exception:

            # One detector can never
            # break the entire engine.
            continue

    def ranking_score(pattern):

        score = float(
            pattern.get(
                "quality",
                0,
            )
        )

        if (
            pattern.get("status")
            == "CONFIRMED"
        ):

            score += 12

        elif (
            pattern.get("status")
            == "FORMING"
        ):

            score += 3

        if (
            pattern.get(
                "pattern_end"
            )
            is not None
        ):

            score += 2

        return score

    detected.sort(
        key=ranking_score,
        reverse=True,
    )

    return detected
# ============================================================
# BEST PATTERN
# ============================================================

def get_best_pattern(df):

    patterns = detect_patterns(df)

    return (
        patterns[0]
        if patterns
        else None
    )


# ============================================================
# CONFIRMED PATTERNS
# ============================================================

def get_confirmed_patterns(df):

    return [
        p
        for p in detect_patterns(df)
        if p.get("status")
        == "CONFIRMED"
    ]


# ============================================================
# LATEST PATTERNS
# ============================================================

def get_latest_patterns(df):

    patterns = detect_patterns(df)

    if not patterns:
        return []

    ends = [
        p.get("pattern_end")
        for p in patterns
        if p.get("pattern_end")
        is not None
    ]

    if not ends:
        return patterns

    latest_end = max(ends)

    latest = [
        p
        for p in patterns
        if p.get("pattern_end")
        == latest_end
    ]

    return latest or patterns

    


    
