# ============================================================
# MOBILE ANALYZER
# PATTERNS.PY
# STRICT MAJOR-SWING PATTERN ENGINE
# ============================================================
#
# PIPELINE
#
# OHLC
#   ↓
# 50-CANDLE ZIGZAG
#   ↓
# MAJOR SWINGS
#   ↓
# GEOMETRY VALIDATION
#   ↓
# PATTERN VALIDATION
#   ↓
# NECKLINE / TRENDLINE
#   ↓
# CANDLE-CLOSE CONFIRMATION
#   ↓
# QUALITY SCORE
#   ↓
# CONFIRMED / PENDING
#
# Patterns:
#
#   Double Top
#   Double Bottom
#   Triple Top
#   Triple Bottom
#   Head & Shoulders
#   Inverse Head & Shoulders
#   Ascending Triangle
#   Descending Triangle
#   Symmetrical Triangle
#   Rising Wedge
#   Falling Wedge
#   Bullish Channel
#   Bearish Channel
#
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# STRICT SETTINGS
# ============================================================

MIN_SCORE = 65

# Price equality tolerance
LEVEL_TOLERANCE = 0.020

# Strict equality tolerance
STRICT_LEVEL_TOLERANCE = 0.012

# Minimum pattern depth relative to price
MIN_PATTERN_DEPTH = 0.008

# Minimum distance between important swings
MIN_SWING_GAP = 2

# Maximum number of major swings considered
MAX_SWINGS = 14

# Breakout buffer.
# Prevents tiny one-tick breaks from becoming confirmation.
BREAKOUT_BUFFER = 0.0015

# Minimum body ratio for breakout candle
MIN_BREAKOUT_BODY = 0.45


# ============================================================
# BASIC HELPERS
# ============================================================

def _validate(df):

    required = [
        "open",
        "high",
        "low",
        "close",
    ]

    missing = [
        x for x in required
        if x not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    if len(df) < 50:
        raise ValueError(
            "At least 50 candles are required."
        )


def _near(a, b, tolerance=LEVEL_TOLERANCE):

    if a is None or b is None:
        return False

    base = abs((a + b) / 2)

    if base == 0:
        return False

    return (
        abs(a - b) / base
        <= tolerance
    )


def _distance(a, b):

    if a is None or b is None:
        return 0.0

    base = abs((a + b) / 2)

    if base == 0:
        return 0.0

    return abs(a - b) / base


def _slope(values):

    if len(values) < 2:
        return 0.0

    x = np.arange(
        len(values),
        dtype=float
    )

    y = np.asarray(
        values,
        dtype=float
    )

    try:
        return float(
            np.polyfit(x, y, 1)[0]
        )
    except Exception:
        return 0.0


def _safe_ratio(a, b):

    if b == 0:
        return 0.0

    return a / b


# ============================================================
# SWINGS
# ============================================================

def _get_swings(df):

    swings = []

    if (
        "swing_high" not in df.columns
        or
        "swing_low" not in df.columns
    ):
        return swings

    for i, row in df.iterrows():

        if bool(row["swing_high"]):

            swings.append({
                "index": i,
                "type": "HIGH",
                "price": float(row["high"]),
            })

        elif bool(row["swing_low"]):

            swings.append({
                "index": i,
                "type": "LOW",
                "price": float(row["low"]),
            })

    swings.sort(
        key=lambda x: x["index"]
    )

    return swings[-MAX_SWINGS:]


# ============================================================
# SWING DISTANCE VALIDATION
# ============================================================

def _valid_spacing(points):

    if len(points) < 2:
        return False

    for i in range(1, len(points)):

        gap = (
            points[i]["index"]
            -
            points[i - 1]["index"]
        )

        if gap < MIN_SWING_GAP:
            return False

    return True


# ============================================================
# CANDLE INFORMATION
# ============================================================

def _candle_body(row):

    return abs(
        float(row["close"])
        -
        float(row["open"])
    )


def _candle_range(row):

    return (
        float(row["high"])
        -
        float(row["low"])
    )


def _body_ratio(row):

    rng = _candle_range(row)

    if rng <= 0:
        return 0.0

    return (
        _candle_body(row)
        /
        rng
    )


# ============================================================
# BREAKOUT CONFIRMATION
# ============================================================

def _breakout_confirmation(
    df,
    level,
    direction
):

    if level is None:
        return {
            "confirmed": False,
            "body_confirmed": False,
            "close": None,
            "index": None,
        }

    if len(df) < 2:
        return {
            "confirmed": False,
            "body_confirmed": False,
            "close": None,
            "index": None,
        }

    last = df.iloc[-1]

    close = float(
        last["close"]
    )

    body_ratio = _body_ratio(
        last
    )

    if direction == "BEARISH":

        required_close = (
            level
            *
            (1 - BREAKOUT_BUFFER)
        )

        confirmed = (
            close < required_close
        )

    elif direction == "BULLISH":

        required_close = (
            level
            *
            (1 + BREAKOUT_BUFFER)
        )

        confirmed = (
            close > required_close
        )

    else:

        confirmed = False

    body_confirmed = (
        confirmed
        and
        body_ratio >= MIN_BREAKOUT_BODY
    )

    return {
        "confirmed": confirmed,
        "body_confirmed": body_confirmed,
        "close": close,
        "index": df.index[-1],
        "body_ratio": body_ratio,
    }


# ============================================================
# SCORE
# ============================================================

def _score(
    structure,
    geometry,
    separation,
    breakout,
    candle
):

    score = 0.0

    score += (
        structure * 0.25
    )

    score += (
        geometry * 0.25
    )

    score += (
        separation * 0.15
    )

    score += (
        breakout * 0.20
    )

    score += (
        candle * 0.15
    )

    return int(
        round(
            max(
                0,
                min(100, score)
            )
        )
    )


# ============================================================
# RESULT
# ============================================================

def _result(
    pattern,
    direction,
    score,
    confirmation,
    points,
    details
):

    quality = "LOW"

    if score >= 85:
        quality = "VERY HIGH"

    elif score >= 75:
        quality = "HIGH"

    elif score >= 65:
        quality = "MEDIUM"

    return {
        "pattern": pattern,
        "direction": direction,
        "confidence": score,
        "score": score,
        "quality": quality,
        "confirmation": confirmation,
        "start_index": points[0]["index"],
        "end_index": points[-1]["index"],
        "details": details,
    }


# ============================================================
# DOUBLE TOP
# ============================================================

def _double_top(df, swings):

    if len(swings) < 3:
        return None

    p = swings[-3:]

    if [x["type"] for x in p] != [
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    left = p[0]["price"]
    valley = p[1]["price"]
    right = p[2]["price"]

    # Two tops must be close
    if not _near(
        left,
        right,
        STRICT_LEVEL_TOLERANCE
    ):
        return None

    # Valley must be meaningfully lower
    depth = (
        min(left, right)
        - valley
    )

    depth_ratio = _safe_ratio(
        depth,
        min(left, right)
    )

    if depth_ratio < MIN_PATTERN_DEPTH:
        return None

    # Current price should not already invalidate
    current_close = float(
        df["close"].iloc[-1]
    )

    neckline = valley

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BEARISH"
    )

    geometry_score = 90

    if depth_ratio > 0.02:
        geometry_score += 5

    separation_score = 90

    breakout_score = (
        100
        if breakout["confirmed"]
        else 20
    )

    candle_score = (
        100
        if breakout["body_confirmed"]
        else 30
    )

    score = _score(
        95,
        min(100, geometry_score),
        separation_score,
        breakout_score,
        candle_score
    )

    confirmation = (
        "CONFIRMED"
        if breakout["body_confirmed"]
        else "PENDING"
    )

    return _result(
        "Double Top",
        "BEARISH",
        score,
        confirmation,
        p,
        {
            "top_1": left,
            "top_2": right,
            "neckline": neckline,
            "depth_ratio": depth_ratio,
            "breakout": breakout,
        }
    )


# ============================================================
# DOUBLE BOTTOM
# ============================================================

def _double_bottom(df, swings):

    if len(swings) < 3:
        return None

    p = swings[-3:]

    if [x["type"] for x in p] != [
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    left = p[0]["price"]
    peak = p[1]["price"]
    right = p[2]["price"]

    if not _near(
        left,
        right,
        STRICT_LEVEL_TOLERANCE
    ):
        return None

    depth = (
        peak
        - max(left, right)
    )

    depth_ratio = _safe_ratio(
        depth,
        max(left, right)
    )

    if depth_ratio < MIN_PATTERN_DEPTH:
        return None

    neckline = peak

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BULLISH"
    )

    breakout_score = (
        100
        if breakout["confirmed"]
        else 20
    )

    candle_score = (
        100
        if breakout["body_confirmed"]
        else 30
    )

    score = _score(
        95,
        95,
        90,
        breakout_score,
        candle_score
    )

    confirmation = (
        "CONFIRMED"
        if breakout["body_confirmed"]
        else "PENDING"
    )

    return _result(
        "Double Bottom",
        "BULLISH",
        score,
        confirmation,
        p,
        {
            "bottom_1": left,
            "bottom_2": right,
            "neckline": neckline,
            "depth_ratio": depth_ratio,
            "breakout": breakout,
        }
    )


# ============================================================
# TRIPLE TOP
# ============================================================

def _triple_top(df, swings):

    if len(swings) < 5:
        return None

    p = swings[-5:]

    if [x["type"] for x in p] != [
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    h1 = p[0]["price"]
    l1 = p[1]["price"]
    h2 = p[2]["price"]
    l2 = p[3]["price"]
    h3 = p[4]["price"]

    # Three tops need strong level agreement
    if not (
        _near(
            h1,
            h2,
            LEVEL_TOLERANCE
        )
        and
        _near(
            h2,
            h3,
            LEVEL_TOLERANCE
        )
    ):
        return None

    neckline = (
        l1 + l2
    ) / 2

    depth1 = (
        h1 - l1
    ) / h1

    depth2 = (
        h3 - l2
    ) / h3

    if (
        depth1 < MIN_PATTERN_DEPTH
        or
        depth2 < MIN_PATTERN_DEPTH
    ):
        return None

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BEARISH"
    )

    score = _score(
        97,
        95,
        95,
        100 if breakout["confirmed"] else 20,
        100 if breakout["body_confirmed"] else 30,
    )

    return _result(
        "Triple Top",
        "BEARISH",
        score,
        (
            "CONFIRMED"
            if breakout["body_confirmed"]
            else "PENDING"
        ),
        p,
        {
            "top_1": h1,
            "top_2": h2,
            "top_3": h3,
            "neckline": neckline,
            "breakout": breakout,
        }
    )


# ============================================================
# TRIPLE BOTTOM
# ============================================================

def _triple_bottom(df, swings):

    if len(swings) < 5:
        return None

    p = swings[-5:]

    if [x["type"] for x in p] != [
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    l1 = p[0]["price"]
    h1 = p[1]["price"]
    l2 = p[2]["price"]
    h2 = p[3]["price"]
    l3 = p[4]["price"]

    if not (
        _near(
            l1,
            l2,
            LEVEL_TOLERANCE
        )
        and
        _near(
            l2,
            l3,
            LEVEL_TOLERANCE
        )
    ):
        return None

    neckline = (
        h1 + h2
    ) / 2

    depth1 = (
        h1 - l1
    ) / h1

    depth2 = (
        h2 - l3
    ) / h2

    if (
        depth1 < MIN_PATTERN_DEPTH
        or
        depth2 < MIN_PATTERN_DEPTH
    ):
        return None

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BULLISH"
    )

    score = _score(
        97,
        95,
        95,
        100 if breakout["confirmed"] else 20,
        100 if breakout["body_confirmed"] else 30,
    )

    return _result(
        "Triple Bottom",
        "BULLISH",
        score,
        (
            "CONFIRMED"
            if breakout["body_confirmed"]
            else "PENDING"
        ),
        p,
        {
            "bottom_1": l1,
            "bottom_2": l2,
            "bottom_3": l3,
            "neckline": neckline,
            "breakout": breakout,
        }
    )


# ============================================================
# HEAD & SHOULDERS
# ============================================================

def _head_shoulders(df, swings):

    if len(swings) < 5:
        return None

    p = swings[-5:]

    if [x["type"] for x in p] != [
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    left = p[0]["price"]
    valley1 = p[1]["price"]
    head = p[2]["price"]
    valley2 = p[3]["price"]
    right = p[4]["price"]

    # Head must clearly exceed both shoulders
    if not (
        head > left
        and
        head > right
    ):
        return None

    # Shoulders must be reasonably symmetric
    if not _near(
        left,
        right,
        0.06
    ):
        return None

    # Head needs meaningful depth
    head_height = (
        head
        -
        max(left, right)
    )

    head_ratio = _safe_ratio(
        head_height,
        head
    )

    if head_ratio < MIN_PATTERN_DEPTH:
        return None

    # Neckline
    neckline = (
        valley1 + valley2
    ) / 2

    # Neckline points should be reasonably close
    if _distance(
        valley1,
        valley2
    ) > 0.08:
        return None

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BEARISH"
    )

    shoulder_score = 95

    if _near(
        left,
        right,
        0.035
    ):
        shoulder_score = 100

    score = _score(
        98,
        shoulder_score,
        92,
        100 if breakout["confirmed"] else 20,
        100 if breakout["body_confirmed"] else 30,
    )

    return _result(
        "Head & Shoulders",
        "BEARISH",
        score,
        (
            "CONFIRMED"
            if breakout["body_confirmed"]
            else "PENDING"
        ),
        p,
        {
            "left_shoulder": left,
            "head": head,
            "right_shoulder": right,
            "neckline": neckline,
            "head_ratio": head_ratio,
            "breakout": breakout,
        }
    )


# ============================================================
# INVERSE HEAD & SHOULDERS
# ============================================================

def _inverse_head_shoulders(df, swings):

    if len(swings) < 5:
        return None

    p = swings[-5:]

    if [x["type"] for x in p] != [
        "LOW",
        "HIGH",
        "LOW",
        "HIGH",
        "LOW",
    ]:
        return None

    if not _valid_spacing(p):
        return None

    left = p[0]["price"]
    peak1 = p[1]["price"]
    head = p[2]["price"]
    peak2 = p[3]["price"]
    right = p[4]["price"]

    if not (
        head < left
        and
        head < right
    ):
        return None

    if not _near(
        left,
        right,
        0.06
    ):
        return None

    head_depth = (
        min(left, right)
        - head
    )

    head_ratio = _safe_ratio(
        head_depth,
        min(left, right)
    )

    if head_ratio < MIN_PATTERN_DEPTH:
        return None

    neckline = (
        peak1 + peak2
    ) / 2

    if _distance(
        peak1,
        peak2
    ) > 0.08:
        return None

    breakout = _breakout_confirmation(
        df,
        neckline,
        "BULLISH"
    )

    shoulder_score = 95

    if _near(
        left,
        right,
        0.035
    ):
        shoulder_score = 100

    score = _score(
        98,
        shoulder_score,
        92,
        100 if breakout["confirmed"] else 20,
        100 if breakout["body_confirmed"] else 30,
    )

    return _result(
        "Inverse Head & Shoulders",
        "BULLISH",
        score,
        (
            "CONFIRMED"
            if breakout["body_confirmed"]
            else "PENDING"
        ),
        p,
        {
            "left_shoulder": left,
            "head": head,
            "right_shoulder": right,
            "neckline": neckline,
            "head_ratio": head_ratio,
            "breakout": breakout,
        }
    )


# ============================================================
# TRIANGLES
# ============================================================

def _triangle(df, swings):

    if len(swings) < 6:
        return None

    p = swings[-6:]

    highs = [
        x for x in p
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in p
        if x["type"] == "LOW"
    ]

    if len(highs) != 3:
        return None

    if len(lows) != 3:
        return None

    high_values = [
        x["price"]
        for x in highs
    ]

    low_values = [
        x["price"]
        for x in lows
    ]

    hs = _slope(
        high_values
    )

    ls = _slope(
        low_values
    )

    # Normalize slopes
    high_base = np.mean(
        high_values
    )

    low_base = np.mean(
        low_values
    )

    if high_base == 0 or low_base == 0:
        return None

    hn = hs / high_base
    ln = ls / low_base

    # --------------------------------------------------------
    # ASCENDING
    # --------------------------------------------------------

    resistance_spread = _distance(
        max(high_values),
        min(high_values)
    )

    if (
        resistance_spread
        <= LEVEL_TOLERANCE
        and
        ln > 0.001
    ):

        return _result(
            "Ascending Triangle",
            "BULLISH",
            76,
            "STRUCTURE_CONFIRMED",
            p,
            {
                "resistance": np.mean(
                    high_values
                ),
                "support_slope": ln,
            }
        )

    # --------------------------------------------------------
    # DESCENDING
    # --------------------------------------------------------

    support_spread = _distance(
        max(low_values)
