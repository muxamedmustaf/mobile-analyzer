# ============================================================
# MOBILE ANALYZER
# PATTERN_ENGINE.PY
# MAJOR SWING CHART PATTERN ENGINE
# ============================================================

import math


# ============================================================
# SETTINGS
# ============================================================

SIMILARITY_DOUBLE = 0.025
SIMILARITY_TRIPLE = 0.035
SIMILARITY_SHOULDER = 0.045

TRIANGLE_TOL = 0.025


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except Exception:
        return None


def _safe_div(a, b):
    a = _safe_float(a)
    b = _safe_float(b)

    if a is None or b is None or b == 0:
        return 0.0

    return a / b


def _distance(a, b):
    a = _safe_float(a)
    b = _safe_float(b)

    if a is None or b is None:
        return 999.0

    return abs(a - b) / max(
        abs((a + b) / 2.0),
        1e-12
    )


def _direction_from_trend(trend):

    if trend == "BULLISH":
        return "BULLISH"

    if trend == "BEARISH":
        return "BEARISH"

    return "NEUTRAL"


# ============================================================
# NEW:
# POINT BUILDER
#
# Keeps the original swing information so app.py can draw
# the exact pattern on the chart.
# ============================================================

def _make_point(name, swing):

    if not isinstance(swing, dict):
        return {
            "name": name,
            "price": None,
            "index": None,
            "timestamp": None,
            "type": None,
        }

    return {
        "name": name,
        "price": swing.get("price"),
        "index": swing.get("index"),
        "timestamp": (
            swing.get("timestamp")
            or swing.get("time")
            or swing.get("datetime")
            or swing.get("date")
        ),
        "type": swing.get("type"),
    }


def _make_line_point(
    name,
    price,
    index=None,
    timestamp=None,
):
    return {
        "name": name,
        "price": price,
        "index": index,
        "timestamp": timestamp,
        "type": "LINE",
    }


# ============================================================
# PATTERN OBJECT
# ============================================================

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
    lines=None,
):

    return {

        "name": name,

        "direction": direction,

        "quality": int(
            max(
                0,
                min(
                    100,
                    round(quality)
                )
            )
        ),

        "status": status,

        "reason": reason,

        "entry": entry,

        "tp1": tp1,

        "tp2": tp2,

        "sl": sl,

        # ====================================================
        # NEW CHART DATA
        # ====================================================

        "points": points or [],

        "lines": lines or [],
    }


# ============================================================
# CONFIRMATION
# ============================================================

def _bullish_confirmation(
    close,
    neckline,
):

    close = _safe_float(close)
    neckline = _safe_float(neckline)

    if close is None or neckline is None:
        return False

    return close > neckline


def _bearish_confirmation(
    close,
    neckline,
):

    close = _safe_float(close)
    neckline = _safe_float(neckline)

    if close is None or neckline is None:
        return False

    return close < neckline


# ============================================================
# DOUBLE TOP
# ============================================================

def detect_double_top(
    swings,
    close,
):

    if len(swings) < 3:
        return None

    a, b, c = swings[-3:]

    if [
        a["type"],
        b["type"],
        c["type"],
    ] != [
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

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

    target_distance = (
        peak - neckline
    )

    confirmed = _bearish_confirmation(
        close,
        neckline
    )

    quality = 82

    if similarity < 0.01:
        quality += 8

    if confirmed:
        quality += 7

    points = [
        _make_point("Top 1", a),
        _make_point("Neckline", b),
        _make_point("Top 2", c),
    ]

    lines = [
        {
            "name": "Pattern",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neckline,
                    a.get("index"),
                    a.get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neckline,
                    c.get("index"),
                    c.get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Double Top",

        direction="BEARISH",

        quality=quality,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Two major highs are closely "
            "matched with a major trough "
            "between them."
        ),

        entry=neckline,

        tp1=(
            neckline - target_distance
        ),

        tp2=(
            neckline -
            target_distance * 1.5
        ),

        sl=(
            peak * 1.003
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# DOUBLE BOTTOM
# ============================================================

def detect_double_bottom(
    swings,
    close,
):

    if len(swings) < 3:
        return None

    a, b, c = swings[-3:]

    if [
        a["type"],
        b["type"],
        c["type"],
    ] != [
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

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

    target_distance = (
        neckline - bottom
    )

    confirmed = _bullish_confirmation(
        close,
        neckline
    )

    quality = 82

    if similarity < 0.01:
        quality += 8

    if confirmed:
        quality += 7

    points = [
        _make_point("Bottom 1", a),
        _make_point("Neckline", b),
        _make_point("Bottom 2", c),
    ]

    lines = [
        {
            "name": "Pattern",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neckline,
                    a.get("index"),
                    a.get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neckline,
                    c.get("index"),
                    c.get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Double Bottom",

        direction="BULLISH",

        quality=quality,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Two major lows are closely "
            "matched with a major peak "
            "between them."
        ),

        entry=neckline,

        tp1=(
            neckline + target_distance
        ),

        tp2=(
            neckline +
            target_distance * 1.5
        ),

        sl=(
            bottom * 0.997
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# TRIPLE TOP
# ============================================================

def detect_triple_top(
    swings,
    close,
):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    types = [
        x["type"]
        for x in s
    ]

    if types != [
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

    average_high = (
        sum(highs) / len(highs)
    )

    high_spread = (
        max(highs)
        -
        min(highs)
    ) / max(
        average_high,
        1e-12
    )

    if high_spread > SIMILARITY_TRIPLE:
        return None

    neckline = min(lows)

    peak = max(highs)

    target_distance = (
        peak - neckline
    )

    confirmed = (
        close < neckline
    )

    points = [
        _make_point("Top 1", s[0]),
        _make_point("Neckline 1", s[1]),
        _make_point("Top 2", s[2]),
        _make_point("Neckline 2", s[3]),
        _make_point("Top 3", s[4]),
    ]

    lines = [
        {
            "name": "Pattern",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neckline,
                    s[0].get("index"),
                    s[0].get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neckline,
                    s[4].get("index"),
                    s[4].get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Triple Top",

        direction="BEARISH",

        quality=91 if confirmed else 86,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Three major highs are "
            "forming a common resistance."
        ),

        entry=neckline,

        tp1=(
            neckline - target_distance
        ),

        tp2=(
            neckline -
            target_distance * 1.5
        ),

        sl=(
            peak * 1.003
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# TRIPLE BOTTOM
# ============================================================

def detect_triple_bottom(
    swings,
    close,
):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    types = [
        x["type"]
        for x in s
    ]

    if types != [
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

    average_low = (
        sum(lows) / len(lows)
    )

    low_spread = (
        max(lows)
        -
        min(lows)
    ) / max(
        average_low,
        1e-12
    )

    if low_spread > SIMILARITY_TRIPLE:
        return None

    neckline = max(highs)

    bottom = min(lows)

    target_distance = (
        neckline - bottom
    )

    confirmed = (
        close > neckline
    )

    points = [
        _make_point("Bottom 1", s[0]),
        _make_point("Neckline 1", s[1]),
        _make_point("Bottom 2", s[2]),
        _make_point("Neckline 2", s[3]),
        _make_point("Bottom 3", s[4]),
    ]

    lines = [
        {
            "name": "Pattern",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neckline,
                    s[0].get("index"),
                    s[0].get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neckline,
                    s[4].get("index"),
                    s[4].get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Triple Bottom",

        direction="BULLISH",

        quality=91 if confirmed else 86,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Three major lows are "
            "forming a common support."
        ),

        entry=neckline,

        tp1=(
            neckline + target_distance
        ),

        tp2=(
            neckline +
            target_distance * 1.5
        ),

        sl=(
            bottom * 0.997
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# HEAD & SHOULDERS
# ============================================================

def detect_head_shoulders(
    swings,
    close,
):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    types = [
        x["type"]
        for x in s
    ]

    if types != [
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    left = s[0]
    neck1 = s[1]
    head = s[2]
    neck2 = s[3]
    right = s[4]

    shoulder_similarity = _distance(
        left["price"],
        right["price"]
    )

    if (
        shoulder_similarity
        >
        SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"]
        >
        left["price"]
        and
        head["price"]
        >
        right["price"]
    ):
        return None

    neckline = (
        neck1["price"]
        +
        neck2["price"]
    ) / 2

    target_distance = (
        head["price"]
        -
        neckline
    )

    if target_distance <= 0:
        return None

    confirmed = (
        close < neckline
    )

    points = [
        _make_point(
            "Left Shoulder",
            left
        ),
        _make_point(
            "Neckline 1",
            neck1
        ),
        _make_point(
            "Head",
            head
        ),
        _make_point(
            "Neckline 2",
            neck2
        ),
        _make_point(
            "Right Shoulder",
            right
        ),
    ]

    lines = [
        {
            "name": "Head & Shoulders",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neck1["price"],
                    neck1.get("index"),
                    neck1.get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neck2["price"],
                    neck2.get("index"),
                    neck2.get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Head & Shoulders",

        direction="BEARISH",

        quality=94 if confirmed else 88,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Left shoulder, higher head, "
            "and similar right shoulder "
            "are detected."
        ),

        entry=neckline,

        tp1=(
            neckline -
            target_distance
        ),

        tp2=(
            neckline -
            target_distance * 1.5
        ),

        sl=(
            head["price"] * 1.003
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# INVERSE HEAD & SHOULDERS
# ============================================================

def detect_inverse_head_shoulders(
    swings,
    close,
):

    if len(swings) < 5:
        return None

    s = swings[-5:]

    types = [
        x["type"]
        for x in s
    ]

    if types != [
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    left = s[0]
    neck1 = s[1]
    head = s[2]
    neck2 = s[3]
    right = s[4]

    shoulder_similarity = _distance(
        left["price"],
        right["price"]
    )

    if (
        shoulder_similarity
        >
        SIMILARITY_SHOULDER
    ):
        return None

    if not (
        head["price"]
        <
        left["price"]
        and
        head["price"]
        <
        right["price"]
    ):
        return None

    neckline = (
        neck1["price"]
        +
        neck2["price"]
    ) / 2

    target_distance = (
        neckline
        -
        head["price"]
    )

    if target_distance <= 0:
        return None

    confirmed = (
        close > neckline
    )

    points = [
        _make_point(
            "Left Shoulder",
            left
        ),
        _make_point(
            "Neckline 1",
            neck1
        ),
        _make_point(
            "Head",
            head
        ),
        _make_point(
            "Neckline 2",
            neck2
        ),
        _make_point(
            "Right Shoulder",
            right
        ),
    ]

    lines = [
        {
            "name": "Inverse Head & Shoulders",
            "points": points,
        },
        {
            "name": "Neckline",
            "points": [
                _make_line_point(
                    "Neckline Start",
                    neck1["price"],
                    neck1.get("index"),
                    neck1.get("timestamp"),
                ),
                _make_line_point(
                    "Neckline End",
                    neck2["price"],
                    neck2.get("index"),
                    neck2.get("timestamp"),
                ),
            ],
        },
    ]

    return _make_pattern(

        name="Inverse Head & Shoulders",

        direction="BULLISH",

        quality=94 if confirmed else 88,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Left shoulder, lower head, "
            "and similar right shoulder "
            "are detected."
        ),

        entry=neckline,

        tp1=(
            neckline +
            target_distance
        ),

        tp2=(
            neckline +
            target_distance * 1.5
        ),

        sl=(
            head["price"] * 0.997
        ),

        points=points,

        lines=lines,
    )


# ============================================================
# ASCENDING TRIANGLE
# ============================================================

def detect_ascending_triangle(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

    if [
        x["type"]
        for x in s
    ] not in [
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
        x
        for x in s
        if x["type"] == "HIGH"
    ]

    lows = [
        x
        for x in s
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

    rising_lows = (
        l2["price"]
   
