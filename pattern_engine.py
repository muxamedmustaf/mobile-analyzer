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


def _direction_from_trend(trend):

    if trend == "BULLISH":
        return "BULLISH"

    if trend == "BEARISH":
        return "BEARISH"

    return "NEUTRAL"


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
    }


# ============================================================
# CONFIRMATION
# ============================================================

def _bullish_confirmation(
    close,
    neckline,
):

    return close > neckline


def _bearish_confirmation(
    close,
    neckline,
):

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

    confirmed = (
        close < neckline
    )

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

    confirmed = (
        close > neckline
    )

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

    if len(highs) != 2:
        return None

    if len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    resistance_similarity = (
        _distance(
            h1["price"],
            h2["price"]
        )
    )

    rising_lows = (
        l2["price"]
        >
        l1["price"]
    )

    if (
        resistance_similarity
        >
        0.025
    ):

        return None

    if not rising_lows:
        return None

    resistance = (
        h1["price"]
        +
        h2["price"]
    ) / 2

    confirmed = (
        close > resistance
    )

    height = (
        resistance
        -
        min(
            l1["price"],
            l2["price"]
        )
    )

    return _make_pattern(

        name="Ascending Triangle",

        direction="BULLISH",

        quality=92 if confirmed else 82,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Major highs form a common "
            "resistance while major lows "
            "continue rising."
        ),

        entry=resistance,

        tp1=(
            resistance + height
        ),

        tp2=(
            resistance + height * 1.5
        ),

        sl=(
            min(
                l1["price"],
                l2["price"]
            ) * 0.997
        ),
    )


# ============================================================
# DESCENDING TRIANGLE
# ============================================================

def detect_descending_triangle(
    swings,
    close,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

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

    if len(highs) != 2:
        return None

    if len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    support_similarity = (
        _distance(
            l1["price"],
            l2["price"]
        )
    )

    falling_highs = (
        h2["price"]
        <
        h1["price"]
    )

    if (
        support_similarity
        >
        0.025
    ):

        return None

    if not falling_highs:
        return None

    support = (
        l1["price"]
        +
        l2["price"]
    ) / 2

    confirmed = (
        close < support
    )

    height = (
        max(
            h1["price"],
            h2["price"]
        )
        -
        support
    )

    return _make_pattern(

        name="Descending Triangle",

        direction="BEARISH",

        quality=92 if confirmed else 82,

        status=(
            "CONFIRMED"
            if confirmed
            else "FORMING"
        ),

        reason=(
            "Major lows form common "
            "support while major highs "
            "continue falling."
        ),

        entry=support,

        tp1=(
            support - height
        ),

        tp2=(
            support - height * 1.5
        ),

        sl=(
            max(
                h1["price"],
                h2["price"]
            ) * 1.003
        ),
    )


# ============================================================
# SYMMETRICAL TRIANGLE
# ============================================================

def detect_symmetrical_triangle(
    swings,
):

    if len(swings) < 4:
        return None

    s = swings[-4:]

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

    if len(highs) != 2:
        return None

    if len(lows) != 2:
        return None

    h1, h2 = highs
    l1, l2 = lows

    falling_highs = (
        h2["price"]
        <
        h1["price"]
    )

    rising_lows = (
        l2["price"]
        >
        l1["price"]
    )

    if not (
        falling_highs
        and
        rising_lows
    ):

        return None

    return _make_pattern(

        name="Symmetrical Triangle",

        direction="NEUTRAL",

        quality=80,

        status="FORMING",

        reason=(
            "Major highs are falling while "
            "major lows are rising, creating "
            "a contracting structure."
        ),
    )


# ============================================================
# MAIN PATTERN ENGINE
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

    close = float(
        df["close"].iloc[-1]
    )

    detected = []

    detectors = [

        detect_double_top,

        detect_double_bottom,

        detect_triple_top,

        detect_triple_bottom,

        detect_head_shoulders,

        detect_inverse_head_shoulders,

        detect_ascending_triangle,

        detect_descending_triangle,
    ]

    for detector in detectors:

        try:

            result = detector(
                swings,
                close
            )

            if result is not None:

                detected.append(
                    result
                )

        except Exception:
            continue

    try:

        triangle = (
            detect_symmetrical_triangle(
                swings
            )
        )

        if triangle is not None:

            detected.append(
                triangle
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # Sort strongest patterns first
    # --------------------------------------------------------

    detected.sort(
        key=lambda x: x["quality"],
        reverse=True
    )

    return detected


# ============================================================
# BEST PATTERN
# ============================================================

def get_best_pattern(df):

    patterns = detect_patterns(
        df
    )

    if not patterns:
        return None

    return patterns[0]


# ============================================================
# CONFIRMED PATTERNS ONLY
# ============================================================

def get_confirmed_patterns(df):

    patterns = detect_patterns(
        df
    )

    return [
        p
        for p in patterns
        if p["status"] == "CONFIRMED"
    ]
