# ============================================================
# MOBILE ANALYZER
# PATTERN_ENGINE.PY
# HARDENED MAJOR-SWING CHART PATTERN ENGINE
# ============================================================
#
# Purpose:
#   OHLC -> Major Swings -> Structural Pattern Detection
#        -> Breakout Confirmation -> Quality -> TP/SL
#
# Compatible public functions:
#   detect_patterns(df)
#   get_best_pattern(df)
#   get_confirmed_patterns(df)
#
# Expected swing format:
#   {"type": "HIGH", "price": 123.45, ...}
#   {"type": "LOW",  "price": 120.00, ...}
#
# The engine intentionally uses MAJOR SWINGS only.
# It does NOT treat every small candle wiggle as a pattern.
# ============================================================

from itertools import combinations
from math import isfinite


# ============================================================
# SETTINGS
# ============================================================

SIMILARITY_DOUBLE = 0.025       # 2.5%
SIMILARITY_TRIPLE = 0.035       # 3.5%
SIMILARITY_SHOULDER = 0.045     # 4.5%

TRIANGLE_RESISTANCE_TOL = 0.025
TRIANGLE_SUPPORT_TOL = 0.025

# Breakout must close slightly beyond the level.
# 0.001 = 0.10%
BREAKOUT_BUFFER = 0.001

# Minimum structural separation.
# Prevents tiny/no-range patterns from being accepted.
MIN_STRUCTURE_RATIO = 0.003     # 0.30%

# Number of recent major swings to scan.
MAX_SWING_WINDOW = 11

# Do not report weak duplicate versions of a stronger pattern.
PATTERN_PRIORITY = {
    "Triple Top": 100,
    "Head & Shoulders": 99,
    "Double Top": 90,
    "Triple Bottom": 100,
    "Inverse Head & Shoulders": 99,
    "Double Bottom": 90,
    "Ascending Triangle": 88,
    "Descending Triangle": 88,
    "Symmetrical Triangle": 80,
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_float(value):
    try:
        value = float(value)
        return value if isfinite(value) else None
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

    denominator = max(abs((a + b) / 2.0), 1e-12)
    return abs(a - b) / denominator


def _price_close(a, b, tolerance):
    return _distance(a, b) <= tolerance


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

    if not swings:
        return cleaned

    for item in swings:
        if not isinstance(item, dict):
            continue

        swing_type = _normalize_type(
            item.get("type")
        )

        price = _safe_float(
            item.get("price")
        )

        if swing_type is None or price is None or price <= 0:
            continue

        item_copy = dict(item)
        item_copy["type"] = swing_type
        item_copy["price"] = price

        cleaned.append(item_copy)

    return cleaned


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
    confirmation=None,
    metadata=None,
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
        "confirmation": confirmation,
        "metadata": metadata or {},
    }


# ============================================================
# CONFIRMATION
# ============================================================

def _bullish_confirmation(close, neckline):
    close = _safe_float(close)
    neckline = _safe_float(neckline)

    if close is None or neckline is None:
        return False

    return close > neckline * (1.0 + BREAKOUT_BUFFER)


def _bearish_confirmation(close, neckline):
    close = _safe_float(close)
    neckline = _safe_float(neckline)

    if close is None or neckline is None:
        return False

    return close < neckline * (1.0 - BREAKOUT_BUFFER)


def _confirmation_text(confirmed, direction):
    if confirmed:
        return (
            "Candle close confirmed the "
            f"{direction.lower()} breakout."
        )

    return (
        "Pattern is forming; breakout candle "
        "close has not confirmed it yet."
    )


# ============================================================
# STRUCTURE HELPERS
# ============================================================

def _pattern_range(prices):
    if not prices:
        return 0.0

    high = max(prices)
    low = min(prices)

    return _safe_div(
        high - low,
        max(abs(high), 1e-12)
    )


def _valid_alternating_window(
    swings,
    expected_types,
):
    if len(swings) != len(expected_types):
        return False

    actual = [
        x["type"]
        for x in swings
    ]

    return actual == expected_types


def _scan_windows(
    swings,
    length,
):
    if len(swings) < length:
        return []

    start = max(
        0,
        len(swings) - MAX_SWING_WINDOW
    )

    recent = swings[start:]

    if len(recent) < length:
        return []

    return [
        recent[i:i + length]
        for i in range(
            0,
            len(recent) - length + 1
        )
    ]


def _best_candidate(candidates):
    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x.get("quality", 0),
            1 if x.get("status") == "CONFIRMED" else 0
        ),
        reverse=True
    )

    return candidates[0]


def _levels_are_structurally_valid(
    highs,
    lows,
):
    if not highs or not lows:
        return False

    all_prices = [
        x["price"]
        for x in highs + lows
    ]

    return (
        _pattern_range(all_prices)
        >= MIN_STRUCTURE_RATIO
    )


# ============================================================
# DOUBLE TOP
# ============================================================

def detect_double_top(swings, close):
    candidates = []

    for s in _scan_windows(swings, 3):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH"]
        ):
            continue

        a, b, c = s

        if not _levels_are_structurally_valid(
            [a, c],
            [b]
        ):
            continue

        similarity = _distance(
            a["price"],
            c["price"]
        )

        if similarity > SIMILARITY_DOUBLE:
            continue

        neckline = b["price"]

        if neckline >= min(
            a["price"],
            c["price"]
        ):
            continue

        peak = max(
            a["price"],
            c["price"]
        )

        target_distance = peak - neckline

        if target_distance <= 0:
            continue

        confirmed = _bearish_confirmation(
            close,
            neckline
        )

        quality = 80

        if similarity <= 0.01:
            quality += 8
        elif similarity <= 0.018:
            quality += 4

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
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
                sl=peak * 1.003,
                confirmation=_confirmation_text(
                    confirmed,
                    "bearish"
                ),
                metadata={
                    "high_similarity": similarity,
                    "swing_count": 3,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# DOUBLE BOTTOM
# ============================================================

def detect_double_bottom(swings, close):
    candidates = []

    for s in _scan_windows(swings, 3):
        if not _valid_alternating_window(
            s,
            ["LOW", "HIGH", "LOW"]
        ):
            continue

        a, b, c = s

        if not _levels_are_structurally_valid(
            [b],
            [a, c]
        ):
            continue

        similarity = _distance(
            a["price"],
            c["price"]
        )

        if similarity > SIMILARITY_DOUBLE:
            continue

        neckline = b["price"]

        if neckline <= max(
            a["price"],
            c["price"]
        ):
            continue

        bottom = min(
            a["price"],
            c["price"]
        )

        target_distance = neckline - bottom

        if target_distance <= 0:
            continue

        confirmed = _bullish_confirmation(
            close,
            neckline
        )

        quality = 80

        if similarity <= 0.01:
            quality += 8
        elif similarity <= 0.018:
            quality += 4

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
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
                sl=bottom * 0.997,
                confirmation=_confirmation_text(
                    confirmed,
                    "bullish"
                ),
                metadata={
                    "low_similarity": similarity,
                    "swing_count": 3,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# TRIPLE TOP
# ============================================================

def detect_triple_top(swings, close):
    candidates = []

    for s in _scan_windows(swings, 5):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH", "LOW", "HIGH"]
        ):
            continue

        h1, l1, h2, l2, h3 = s

        highs = [
            h1["price"],
            h2["price"],
            h3["price"],
        ]

        lows = [
            l1["price"],
            l2["price"],
        ]

        if not _levels_are_structurally_valid(
            [h1, h2, h3],
            [l1, l2]
        ):
            continue

        average_high = sum(highs) / 3.0

        high_spread = _safe_div(
            max(highs) - min(highs),
            max(abs(average_high), 1e-12)
        )

        if high_spread > SIMILARITY_TRIPLE:
            continue

        # Both pullbacks must be meaningful.
        peak = max(highs)
        neckline = min(lows)

        if neckline >= min(highs):
            continue

        target_distance = peak - neckline

        if target_distance <= 0:
            continue

        # Prevent a "fake" triple top where the middle
        # trough barely separates the peaks.
        first_depth = _safe_div(
            h1["price"] - l1["price"],
            h1["price"]
        )

        second_depth = _safe_div(
            h2["price"] - l2["price"],
            h2["price"]
        )

        if (
            first_depth < MIN_STRUCTURE_RATIO
            or
            second_depth < MIN_STRUCTURE_RATIO
        ):
            continue

        confirmed = _bearish_confirmation(
            close,
            neckline
        )

        quality = 83

        if high_spread <= 0.01:
            quality += 6
        elif high_spread <= 0.02:
            quality += 3

        if (
            first_depth >= 0.01
            and second_depth >= 0.01
        ):
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Triple Top",
                direction="BEARISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Three major highs are closely "
                    "matched, separated by two "
                    "meaningful pullbacks, with a "
                    "common neckline."
                ),
                entry=neckline,
                tp1=(
                    neckline - target_distance
                ),
                tp2=(
                    neckline -
                    target_distance * 1.5
                ),
                sl=peak * 1.003,
                confirmation=_confirmation_text(
                    confirmed,
                    "bearish"
                ),
                metadata={
                    "high_spread": high_spread,
                    "pullback_1": first_depth,
                    "pullback_2": second_depth,
                    "swing_count": 5,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# TRIPLE BOTTOM
# ============================================================

def detect_triple_bottom(swings, close):
    candidates = []

    for s in _scan_windows(swings, 5):
        if not _valid_alternating_window(
            s,
            ["LOW", "HIGH", "LOW", "HIGH", "LOW"]
        ):
            continue

        l1, h1, l2, h2, l3 = s

        lows = [
            l1["price"],
            l2["price"],
            l3["price"],
        ]

        highs = [
            h1["price"],
            h2["price"],
        ]

        if not _levels_are_structurally_valid(
            [h1, h2],
            [l1, l2, l3]
        ):
            continue

        average_low = sum(lows) / 3.0

        low_spread = _safe_div(
            max(lows) - min(lows),
            max(abs(average_low), 1e-12)
        )

        if low_spread > SIMILARITY_TRIPLE:
            continue

        bottom = min(lows)
        neckline = max(highs)

        if neckline <= max(lows):
            continue

        target_distance = neckline - bottom

        if target_distance <= 0:
            continue

        first_height = _safe_div(
            h1["price"] - l1["price"],
            max(abs(l1["price"]), 1e-12)
        )

        second_height = _safe_div(
            h2["price"] - l2["price"],
            max(abs(l2["price"]), 1e-12)
        )

        if (
            first_height < MIN_STRUCTURE_RATIO
            or
            second_height < MIN_STRUCTURE_RATIO
        ):
            continue

        confirmed = _bullish_confirmation(
            close,
            neckline
        )

        quality = 83

        if low_spread <= 0.01:
            quality += 6
        elif low_spread <= 0.02:
            quality += 3

        if (
            first_height >= 0.01
            and second_height >= 0.01
        ):
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Triple Bottom",
                direction="BULLISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Three major lows are closely "
                    "matched, separated by two "
                    "meaningful rallies, with a "
                    "common neckline."
                ),
                entry=neckline,
                tp1=(
                    neckline + target_distance
                ),
                tp2=(
                    neckline +
                    target_distance * 1.5
                ),
                sl=bottom * 0.997,
                confirmation=_confirmation_text(
                    confirmed,
                    "bullish"
                ),
                metadata={
                    "low_spread": low_spread,
                    "rally_1": first_height,
                    "rally_2": second_height,
                    "swing_count": 5,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# HEAD & SHOULDERS
# ============================================================

def detect_head_shoulders(swings, close):
    candidates = []

    for s in _scan_windows(swings, 5):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH", "LOW", "HIGH"]
        ):
            continue

        left, neck1, head, neck2, right = s

        shoulder_similarity = _distance(
            left["price"],
            right["price"]
        )

        if shoulder_similarity > SIMILARITY_SHOULDER:
            continue

        if not (
            head["price"] > left["price"]
            and
            head["price"] > right["price"]
        ):
            continue

        neckline = (
            neck1["price"] +
            neck2["price"]
        ) / 2.0

        target_distance = (
            head["price"] - neckline
        )

        if target_distance <= 0:
            continue

        # Head must stand meaningfully above shoulders.
        left_head_gap = _safe_div(
            head["price"] - left["price"],
            head["price"]
        )

        right_head_gap = _safe_div(
            head["price"] - right["price"],
            head["price"]
        )

        if (
            left_head_gap < MIN_STRUCTURE_RATIO
            or
            right_head_gap < MIN_STRUCTURE_RATIO
        ):
            continue

        confirmed = _bearish_confirmation(
            close,
            neckline
        )

        quality = 84

        if shoulder_similarity <= 0.015:
            quality += 6
        elif shoulder_similarity <= 0.03:
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Head & Shoulders",
                direction="BEARISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Major left shoulder, higher "
                    "head, and structurally similar "
                    "right shoulder are detected."
                ),
                entry=neckline,
                tp1=(
                    neckline - target_distance
                ),
                tp2=(
                    neckline -
                    target_distance * 1.5
                ),
                sl=head["price"] * 1.003,
                confirmation=_confirmation_text(
                    confirmed,
                    "bearish"
                ),
                metadata={
                    "shoulder_similarity":
                        shoulder_similarity,
                    "swing_count": 5,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# INVERSE HEAD & SHOULDERS
# ============================================================

def detect_inverse_head_shoulders(swings, close):
    candidates = []

    for s in _scan_windows(swings, 5):
        if not _valid_alternating_window(
            s,
            ["LOW", "HIGH", "LOW", "HIGH", "LOW"]
        ):
            continue

        left, neck1, head, neck2, right = s

        shoulder_similarity = _distance(
            left["price"],
            right["price"]
        )

        if shoulder_similarity > SIMILARITY_SHOULDER:
            continue

        if not (
            head["price"] < left["price"]
            and
            head["price"] < right["price"]
        ):
            continue

        neckline = (
            neck1["price"] +
            neck2["price"]
        ) / 2.0

        target_distance = (
            neckline - head["price"]
        )

        if target_distance <= 0:
            continue

        left_head_gap = _safe_div(
            left["price"] - head["price"],
            max(abs(head["price"]), 1e-12)
        )

        right_head_gap = _safe_div(
            right["price"] - head["price"],
            max(abs(head["price"]), 1e-12)
        )

        if (
            left_head_gap < MIN_STRUCTURE_RATIO
            or
            right_head_gap < MIN_STRUCTURE_RATIO
        ):
            continue

        confirmed = _bullish_confirmation(
            close,
            neckline
        )

        quality = 84

        if shoulder_similarity <= 0.015:
            quality += 6
        elif shoulder_similarity <= 0.03:
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Inverse Head & Shoulders",
                direction="BULLISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Major left shoulder, lower head, "
                    "and structurally similar right "
                    "shoulder are detected."
                ),
                entry=neckline,
                tp1=(
                    neckline + target_distance
                ),
                tp2=(
                    neckline +
                    target_distance * 1.5
                ),
                sl=head["price"] * 0.997,
                confirmation=_confirmation_text(
                    confirmed,
                    "bullish"
                ),
                metadata={
                    "shoulder_similarity":
                        shoulder_similarity,
                    "swing_count": 5,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# ASCENDING TRIANGLE
# ============================================================

def detect_ascending_triangle(swings, close):
    candidates = []

    for s in _scan_windows(swings, 4):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH", "LOW"]
        ):
            continue

        h1, l1, h2, l2 = s

        resistance_similarity = _distance(
            h1["price"],
            h2["price"]
        )

        if resistance_similarity > TRIANGLE_RESISTANCE_TOL:
            continue

        if not (
            l2["price"] > l1["price"]
        ):
            continue

        resistance = (
            h1["price"] +
            h2["price"]
        ) / 2.0

        lower_support = min(
            l1["price"],
            l2["price"]
        )

        height = resistance - lower_support

        if height <= 0:
            continue

        confirmed = _bullish_confirmation(
            close,
            resistance
        )

        quality = 78

        if resistance_similarity <= 0.01:
            quality += 6
        elif resistance_similarity <= 0.018:
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Ascending Triangle",
                direction="BULLISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Two major highs form a common "
                    "resistance while the two major "
                    "lows rise."
                ),
                entry=resistance,
                tp1=resistance + height,
                tp2=resistance + height * 1.5,
                sl=lower_support * 0.997,
                confirmation=_confirmation_text(
                    confirmed,
                    "bullish"
                ),
                metadata={
                    "resistance_similarity":
                        resistance_similarity,
                    "swing_count": 4,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# DESCENDING TRIANGLE
# ============================================================

def detect_descending_triangle(swings, close):
    candidates = []

    for s in _scan_windows(swings, 4):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH", "LOW"]
        ):
            continue

        h1, l1, h2, l2 = s

        support_similarity = _distance(
            l1["price"],
            l2["price"]
        )

        if support_similarity > TRIANGLE_SUPPORT_TOL:
            continue

        if not (
            h2["price"] < h1["price"]
        ):
            continue

        support = (
            l1["price"] +
            l2["price"]
        ) / 2.0

        upper_resistance = max(
            h1["price"],
            h2["price"]
        )

        height = upper_resistance - support

        if height <= 0:
            continue

        confirmed = _bearish_confirmation(
            close,
            support
        )

        quality = 78

        if support_similarity <= 0.01:
            quality += 6
        elif support_similarity <= 0.018:
            quality += 3

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Descending Triangle",
                direction="BEARISH",
                quality=quality,
                status=(
                    "CONFIRMED"
                    if confirmed
                    else "FORMING"
                ),
                reason=(
                    "Two major lows form a common "
                    "support while the two major "
                    "highs fall."
                ),
                entry=support,
                tp1=support - height,
                tp2=support - height * 1.5,
                sl=upper_resistance * 1.003,
                confirmation=_confirmation_text(
                    confirmed,
                    "bearish"
                ),
                metadata={
                    "support_similarity":
                        support_similarity,
                    "swing_count": 4,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# SYMMETRICAL TRIANGLE
# ============================================================

def detect_symmetrical_triangle(
    swings,
    close=None,
):
    candidates = []

    for s in _scan_windows(swings, 4):
        if not _valid_alternating_window(
            s,
            ["HIGH", "LOW", "HIGH", "LOW"]
        ):
            continue

        h1, l1, h2, l2 = s

        falling_highs = (
            h2["price"] < h1["price"]
        )

        rising_lows = (
            l2["price"] > l1["price"]
        )

        if not (
            falling_highs
            and
            rising_lows
        ):
            continue

        upper_range = (
            h1["price"] - h2["price"]
        )

        lower_range = (
            l2["price"] - l1["price"]
        )

        total_range = (
            h1["price"] - l1["price"]
        )

        if total_range <= 0:
            continue

        # Both sides should actually converge.
        if upper_range <= 0 or lower_range <= 0:
            continue

        # Require the two sides to be reasonably balanced.
        slope_balance = _distance(
            upper_range,
            lower_range
        )

        if slope_balance > 0.85:
            continue

        upper_boundary = h2["price"]
        lower_boundary = l2["price"]

        if close is None:
            confirmed = False
            direction = "NEUTRAL"
            status = "FORMING"
        else:
            bullish_break = (
                _safe_float(close)
                >
                upper_boundary *
                (1.0 + BREAKOUT_BUFFER)
            )

            bearish_break = (
                _safe_float(close)
                <
                lower_boundary *
                (1.0 - BREAKOUT_BUFFER)
            )

            if bullish_break:
                confirmed = True
                direction = "BULLISH"
                status = "CONFIRMED"
            elif bearish_break:
                confirmed = True
                direction = "BEARISH"
                status = "CONFIRMED"
            else:
                confirmed = False
                direction = "NEUTRAL"
                status = "FORMING"

        height = h1["price"] - l1["price"]

        if direction == "BULLISH":
            entry = upper_boundary
            tp1 = upper_boundary + height
            tp2 = upper_boundary + height * 1.5
            sl = lower_boundary * 0.997
        elif direction == "BEARISH":
            entry = lower_boundary
            tp1 = lower_boundary - height
            tp2 = lower_boundary - height * 1.5
            sl = upper_boundary * 1.003
        else:
            entry = None
            tp1 = None
            tp2 = None
            sl = None

        quality = 72

        if slope_balance <= 0.35:
            quality += 8
        elif slope_balance <= 0.60:
            quality += 4

        if confirmed:
            quality += 8

        candidates.append(
            _make_pattern(
                name="Symmetrical Triangle",
                direction=direction,
                quality=quality,
                status=status,
                reason=(
                    "Major highs are falling and "
                    "major lows are rising, creating "
                    "a contracting structure."
                ),
                entry=entry,
                tp1=tp1,
                tp2=tp2,
                sl=sl,
                confirmation=(
                    _confirmation_text(
                        confirmed,
                        direction
                    )
                    if direction != "NEUTRAL"
                    else (
                        "No breakout confirmed; "
                        "wait for a candle close "
                        "outside the triangle."
                    )
                ),
                metadata={
                    "slope_balance": slope_balance,
                    "upper_boundary": upper_boundary,
                    "lower_boundary": lower_boundary,
                    "swing_count": 4,
                },
            )
        )

    return _best_candidate(candidates)


# ============================================================
# DUPLICATE CONTROL
# ============================================================

def _deduplicate_patterns(patterns):
    """
    Prevent the same structural pattern from being reported
    repeatedly.

    Stronger patterns win:
        Triple Top > Double Top
        H&S > Double Top
        Triple Bottom > Double Bottom
        Inverse H&S > Double Bottom
    """

    if not patterns:
        return []

    grouped = {}

    for pattern in patterns:
        direction = pattern.get(
            "direction",
            "NEUTRAL"
        )

        key = (
            direction,
            pattern.get("name")
        )

        grouped.setdefault(
            key,
            []
        ).append(pattern)

    best_by_name = []

    for group in grouped.values():
        best = max(
            group,
            key=lambda x: (
                x.get("quality", 0),
                1 if x.get("status") == "CONFIRMED" else 0
            )
        )

        best_by_name.append(best)

    # If a stronger 3-peak structure exists, remove
    # the weaker double-top/bottom representation.
    names = {
        p["name"]
        for p in best_by_name
    }

    if "Triple Top" in names:
        best_by_name = [
            p for p in best_by_name
            if p["name"] != "Double Top"
        ]

    if "Head & Shoulders" in names:
        best_by_name = [
            p for p in best_by_name
            if p["name"] != "Double Top"
        ]

    if "Triple Bottom" in names:
        best_by_name = [
            p for p in best_by_name
            if p["name"] != "Double Bottom"
        ]

    if "Inverse Head & Shoulders" in names:
        best_by_name = [
            p for p in best_by_name
            if p["name"] != "Double Bottom"
        ]

    return best_by_name


# ============================================================
# MAIN PATTERN ENGINE
# ============================================================

def detect_patterns(df):
    """
    Detect patterns from df.attrs["major_swings"].

    The last close is used for breakout confirmation.
    Only candle-close confirmation is accepted.
    """

    if df is None:
        return []

    try:
        raw_swings = df.attrs.get(
            "major_swings",
            []
        )
    except Exception:
        return []

    swings = _clean_swings(
        raw_swings
    )

    if len(swings) < 3:
        return []

    try:
        close = _safe_float(
            df["close"].iloc[-1]
        )
    except Exception:
        return []

    if close is None:
        return []

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
                detected.append(result)

        except Exception:
            # One detector must never break the entire engine.
            continue

    try:
        triangle = detect_symmetrical_triangle(
            swings,
            close
        )

        if triangle is not None:
            detected.append(triangle)

    except Exception:
        pass

    detected = _deduplicate_patterns(
        detected
    )

    detected.sort(
        key=lambda x: (
            1 if x.get("status") == "CONFIRMED" else 0,
            x.get("quality", 0),
            PATTERN_PRIORITY.get(
                x.get("name"),
                0
            ),
        ),
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
        if p.get("status") == "CONFIRMED"
    ]


# ============================================================
# FORMING PATTERNS ONLY
# ============================================================

def get_forming_patterns(df):
    patterns = detect_patterns(df)

    return [
        p
        for p in patterns
        if p.get("status") == "FORMING"
    ]
