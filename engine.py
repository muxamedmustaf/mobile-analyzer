import pandas as pd
import numpy as np


# ==========================================================
# PATTERN ENGINE
# 15 PATTERNS - INDIVIDUAL STRATEGY DETECTORS
# ==========================================================

MAX_PATTERN_AGE = 20
MAX_VARIATION = 0.01
MIN_CORRECTION = 0.20


# ==========================================================
# 1. INDICATORS
# ==========================================================

def calculate_indicators(df):

    df = df.copy()

    df["EMA50"] = df["Close"].ewm(
        span=50,
        adjust=False
    ).mean()

    df["EMA200"] = df["Close"].ewm(
        span=200,
        adjust=False
    ).mean()

    ema12 = df["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = ema12 - ema26

    df["MACD_Signal"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["MACD_Hist"] = (
        df["MACD"] -
        df["MACD_Signal"]
    )

    delta = df["Close"].diff()

    gain = (
        delta.where(delta > 0, 0.0)
        .rolling(14)
        .mean()
    )

    loss = (
        -delta.where(delta < 0, 0.0)
        .rolling(14)
        .mean()
    )

    loss_safe = np.where(
        loss == 0,
        1e-9,
        loss
    )

    rs = gain / loss_safe

    df["RSI"] = (
        100 -
        (100 / (1 + rs))
    )

    df["RSI"] = df["RSI"].fillna(50.0)

    return df


# ==========================================================
# 2. ZIGZAG
# ==========================================================

def calculate_zigzag(
    df,
    depth=12,
    deviation=5,
    backstep=3
):

    df = df.copy()

    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].values
    lows = df["Low"].values

    last_pos = -backstep
    last_type = 0

    for i in range(
        depth,
        len(df) - backstep
    ):

        window_high = np.max(
            highs[i-depth:i+1]
        )

        window_low = np.min(
            lows[i-depth:i+1]
        )

        is_high = (
            highs[i] == window_high
        )

        is_low = (
            lows[i] == window_low
        )

        if (
            is_high
            and i - last_pos >= backstep
        ):

            if (
                last_type != 1
                or highs[i] > highs[last_pos]
            ):

                df.iloc[
                    i,
                    df.columns.get_loc(
                        "Pivot_H"
                    )
                ] = highs[i]

                last_pos = i
                last_type = 1

        if (
            is_low
            and i - last_pos >= backstep
        ):

            if (
                last_type != -1
                or lows[i] < lows[last_pos]
            ):

                df.iloc[
                    i,
                    df.columns.get_loc(
                        "Pivot_L"
                    )
                ] = lows[i]

                last_pos = i
                last_type = -1

    return df


# ==========================================================
# 3. CHRONOLOGICAL PIVOTS
# ==========================================================

def get_chronological_pivots(df):

    pivots = []

    for pos, (idx, row) in enumerate(
        df.iterrows()
    ):

        if not pd.isna(row["Pivot_H"]):

            pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_H"]),
                "type": "H"
            })

        elif not pd.isna(row["Pivot_L"]):

            pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_L"]),
                "type": "L"
            })

    clean = []

    for p in pivots:

        if not clean:
            clean.append(p)
            continue

        last = clean[-1]

        if last["type"] != p["type"]:

            clean.append(p)

        elif p["type"] == "H":

            if p["val"] > last["val"]:
                clean[-1] = p

        elif p["type"] == "L":

            if p["val"] < last["val"]:
                clean[-1] = p

    return clean


# ==========================================================
# 4. COMMON HELPERS
# ==========================================================

def variation(a, b):

    return abs(a - b) / max(
        abs(a),
        abs(b),
        1e-9
    )


def equal_within_1_percent(a, b):

    return variation(a, b) <= MAX_VARIATION


def wave_length(a, b):

    return abs(b - a)


def correction_depth(
    start,
    extreme,
    correction
):

    wave = abs(extreme - start)

    if wave <= 0:
        return 0

    return (
        abs(extreme - correction)
        / wave
    )


def valid_correction(
    start,
    extreme,
    correction
):

    return (
        correction_depth(
            start,
            extreme,
            correction
        )
        >= MIN_CORRECTION
    )


def recent_pattern(
    points,
    current_pos
):

    if not points:
        return False

    return (
        current_pos -
        points[-1]["pos"]
        <= MAX_PATTERN_AGE
    )


def make_result(
    name,
    bias,
    points,
    trigger,
    sl,
    tp,
    score,
    trigger_type="neckline"
):

    return {
        "name": name,
        "bias": bias,
        "match": float(score),

        "nodes": [
            (p["idx"], p["val"])
            for p in points
        ],

        "entry_trigger": float(
            trigger
        ),

        "trigger_type": trigger_type,

        "sl": float(sl),

        "tp": float(tp),

        "neckline_start_idx":
            points[1]["idx"]
            if len(points) > 1
            else points[0]["idx"]
    }


# ==========================================================
# 5. HEAD & SHOULDERS
#
# YOUR SPECIFIC STRATEGY
# ==========================================================

def detect_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    for i in range(
        len(pivots) - 5,
        len(pivots)
    ):

        if i < 0:
            continue

        p = pivots[i:i+5]

        # H L H L H
        if [x["type"] for x in p] != [
            "H",
            "L",
            "H",
            "L",
            "H"
        ]:
            continue

        if not recent_pattern(
            p,
            current_pos
        ):
            continue

        h1 = p[0]["val"]
        l1 = p[1]["val"]
        h2 = p[2]["val"]
        l2 = p[3]["val"]
        h3 = p[4]["val"]

        # --------------------------------------------------
        # 1. PREVIOUS TREND MUST BE BULLISH
        # --------------------------------------------------

        if not (
            h1 > l1
        ):
            continue

        # --------------------------------------------------
        # 2. LEFT SHOULDER WAVE
        # --------------------------------------------------

        left_wave = wave_length(
            l1,
            h1
        )

        if left_wave <= 0:
            continue

        # --------------------------------------------------
        # 3. LEFT CORRECTION >= 20%
        # --------------------------------------------------

        if not valid_correction(
            l1,
            h1,
            l1
        ):
            continue

        # --------------------------------------------------
        # 4. HEAD BREAKS LEFT SHOULDER
        # --------------------------------------------------

        if h2 <= h1:
            continue

        # Clear breakout
        if h2 <= h1 * 1.001:
            continue

        # --------------------------------------------------
        # 5. SECOND CORRECTION
        # MUST REACH / APPROACH FIRST SUPPORT
        # --------------------------------------------------

        support_distance = (
            abs(l2 - l1)
            / max(abs(l1), 1e-9)
        )

        if support_distance > 0.01:
            continue

        # Second correction must be meaningful
        if not valid_correction(
            h1,
            h2,
            l2
        ):
            continue

        # --------------------------------------------------
        # 6. RIGHT SHOULDER
        # --------------------------------------------------

        if h3 >= h2:
            continue

        # Right shoulder must be near
        # left shoulder
        if not equal_within_1_percent(
            h1,
            h3
        ):
            continue

        # --------------------------------------------------
        # 7. COMPARE CORRESPONDING MOVES
        # --------------------------------------------------

        right_wave = wave_length(
            l2,
            h3
        )

        if not equal_within_1_percent(
            left_wave,
            right_wave
        ):
            continue

        # --------------------------------------------------
        # 8. COMPARE CORRECTIONS
        # --------------------------------------------------

        left_correction = (
            h1 - l1
        )

        right_correction = (
            h2 - l2
        )

        if not equal_within_1_percent(
            left_correction,
            right_correction
        ):
            continue

        # --------------------------------------------------
        # 9. NECKLINE
        # --------------------------------------------------

        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:

            neckline = (
                l1 + l2
            ) / 2

        else:

            slope = (
                (l2 - l1)
                /
                (x2 - x1)
            )

            neckline = (
                l2
                +
                slope *
                (current_pos - x2)
            )

        # --------------------------------------------------
        # 10. TARGET
        # --------------------------------------------------

        pattern_height = (
            h2 - neckline
        )

        if pattern_height <= 0:
            continue

        target = (
            neckline -
            pattern_height
        )

        return make_result(
            "Head and Shoulders",
            "Bearish",
            p,
            neckline,
            h3 * 1.001,
            target,
            100
        )

    return None


# ==========================================================
# 6. INVERSE HEAD & SHOULDERS
#
# MIRROR OF HEAD & SHOULDERS
# ==========================================================

def detect_inverse_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    for i in range(
        len(pivots) - 5,
        len(pivots)
    ):

        if i < 0:
            continue

        p = pivots[i:i+5]

        if [x["type"] for x in p] != [
            "L",
            "H",
            "L",
            "H",
            "L"
        ]:
            continue

        if not recent_pattern(
            p,
            current_pos
        ):
            continue

        l1 = p[0]["val"]
        h1 = p[1]["val"]
        l2 = p[2]["val"]
        h2 = p[3]["val"]
        l3 = p[4]["val"]

        # Head lower than shoulders
        if not (
            l2 < l1
            and l2 < l3
        ):
            continue

        if l2 >= l1 * 0.999:
            continue

        # Shoulders equal within 1%
        if not equal_within_1_percent(
            l1,
            l3
        ):
            continue

        left_wave = wave_length(
            h1,
            l1
        )

        right_wave = wave_length(
            h2,
            l3
        )

        if not equal_within_1_percent(
            left_wave,
            right_wave
        ):
            continue

        left_correction = (
            h1 - l1
        )

        right_correction = (
            h2 - l2
        )

        if not equal_within_1_percent(
            left_correction,
            right_correction
        ):
            continue

        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:

            neckline = (
                h1 + h2
            ) / 2

        else:

            slope = (
                (h2 - h1)
                /
                (x2 - x1)
            )

            neckline = (
                h2
                +
                slope *
                (current_pos - x2)
            )

        height = (
            neckline - l2
        )

        if height <= 0:
            continue

        return make_result(
            "Inverse Head and Shoulders",
            "Bullish",
            p,
            neckline,
            l3 * 0.999,
            neckline + height,
            100
        )

    return None


# ==========================================================
# 7. DOUBLE TOP
# ==========================================================

def detect_double_top(
    pivots,
    current_pos
):

    if len(pivots) < 3:
        return None

    p = pivots[-3:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2 = [
        x["val"] for x in p
    ]

    if not recent_pattern(
        p,
        current_pos
    ):
        return None

    if not equal_within_1_percent(
        h1,
        h2
    ):
        return None

    correction = (
        h1 - l1
    )

    if correction <= 0:
        return None

    return make_result(
        "Double Top",
        "Bearish",
        p,
        l1,
        max(h1, h2) * 1.001,
        l1 - correction,
        100
    )


# ==========================================================
# 8. DOUBLE BOTTOM
# ==========================================================

def detect_double_bottom(
    pivots,
    current_pos
):

    if len(pivots) < 3:
        return None

    p = pivots[-3:]

    if [x["type"] for x in p] != [
        "L",
        "H",
        "L"
    ]:
        return None

    l1, h1, l2 = [
        x["val"] for x in p
    ]

    if not recent_pattern(
        p,
        current_pos
    ):
        return None

    if not equal_within_1_percent(
        l1,
        l2
    ):
        return None

    correction = (
        h1 - l1
    )

    if correction <= 0:
        return None

    return make_result(
        "Double Bottom",
        "Bullish",
        p,
        h1,
        min(l1, l2) * 0.999,
        h1 + correction,
        100
    )


# ==========================================================
# 9. TRIPLE TOP
# ==========================================================

def detect_triple_top(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    if not (
        equal_within_1_percent(h1, h2)
        and equal_within_1_percent(h2, h3)
    ):
        return None

    if not (
        valid_correction(h1, h2, l1)
        and valid_correction(h2, h3, l2)
    ):
        return None

    neckline = min(
        l1,
        l2
    )

    height = (
        max(h1, h2, h3)
        - neckline
    )

    return make_result(
        "Triple Top",
        "Bearish",
        p,
        neckline,
        max(h1, h2, h3) * 1.001,
        neckline - height,
        100
    )


# ==========================================================
# 10. TRIPLE BOTTOM
# ==========================================================

def detect_triple_bottom(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L",
        "H",
        "L",
        "H",
        "L"
    ]:
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    if not (
        equal_within_1_percent(l1, l2)
        and equal_within_1_percent(l2, l3)
    ):
        return None

    if not (
        valid_correction(l1, l2, h1)
        and valid_correction(l2, l3, h2)
    ):
        return None

    neckline = max(
        h1,
        h2
    )

    height = (
        neckline -
        min(l1, l2, l3)
    )

    return make_result(
        "Triple Bottom",
        "Bullish",
        p,
        neckline,
        min(l1, l2, l3) * 0.999,
        neckline + height,
        100
    )


# ==========================================================
# 11. ASCENDING TRIANGLE
# ==========================================================

def detect_ascending_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L",
        "H",
        "L",
        "H",
        "L"
    ]:
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    if not equal_within_1_percent(
        h1,
        h2
    ):
        return None

    if not (
        l2 > l1
        and l3 > l2
    ):
        return None

    return make_result(
        "Ascending Triangle",
        "Bullish",
        p,
        max(h1, h2),
        min(l1, l2, l3) * 0.999,
        max(h1, h2)
        +
        (
            max(h1, h2)
            -
            min(l1, l2, l3)
        ),
        100
    )


# ==========================================================
# 12. DESCENDING TRIANGLE
# ==========================================================

def detect_descending_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    if not equal_within_1_percent(
        l1,
        l2
    ):
        return None

    if not (
        h2 < h1
        and h3 < h2
    ):
        return None

    return make_result(
        "Descending Triangle",
        "Bearish",
        p,
        min(l1, l2),
        max(h1, h2, h3) * 1.001,
        min(l1, l2)
        -
        (
            max(h1, h2, h3)
            -
            min(l1, l2)
        ),
        100
    )


# ==========================================================
# 13. SYMMETRICAL TRIANGLE
# ==========================================================

def detect_symmetrical_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    if not (
        h2 < h1
        and h3 < h2
        and l2 > l1
    ):
        return None

    return make_result(
        "Symmetrical Triangle",
        "Neutral",
        p,
        h3,
        h1 * 1.001,
        l1,
        100
    )


# ==========================================================
# 14. RISING WEDGE
# ==========================================================

def detect_rising_wedge(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L",
        "H",
        "L",
        "H",
        "L"
    ]:
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    if not (
        l2 > l1
        and l3 > l2
        and h2 > h1
    ):
        return None

    upper_slope = (
        h2 - h1
    ) / max(
        p[3]["pos"] - p[1]["pos"],
        1
    )

    lower_slope = (
        l3 - l1
    ) / max(
        p[4]["pos"] - p[0]["pos"],
        1
    )

    if lower_slope <= upper_slope:
        return None

    return make_result(
        "Rising Wedge",
        "Bearish",
        p,
        l3,
        max(h1, h2) * 1.001,
        l3 - (
            max(h1, h2)
            -
            min(l1, l2, l3)
        ),
        100
    )


# ==========================================================
# 15. FALLING WEDGE
# ==========================================================

def detect_falling_wedge(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    if not (
        h2 < h1
        and h3 < h2
        and l2 < l1
    ):
        return None

    return make_result(
        "Falling Wedge",
        "Bullish",
        p,
        h3,
        min(l1, l2) * 0.999,
        h3 + (
            max(h1, h2, h3)
            -
            min(l1, l2)
        ),
        100
    )


# ==========================================================
# 16. RECTANGLE
# ==========================================================

def detect_rectangle(
    pivots,
    current_pos
):

    if len(pivots) < 6:
        return None

    p = pivots[-6:]

    highs = [
        x["val"]
        for x in p
        if x["type"] == "H"
    ]

    lows = [
        x["val"]
        for x in p
        if x["type"] == "L"
    ]

    if len(highs) < 2:
        return None

    if len(lows) < 2:
        return None

    if not (
        equal_within_1_percent(
            highs[0],
            highs[-1]
        )
        and
        equal_within_1_percent(
            lows[0],
            lows[-1]
        )
    ):
        return None

    resistance = max(highs)
    support = min(lows)

    return make_result(
        "Rectangle",
        "Neutral",
        p,
        resistance,
        resistance * 1.001,
        support,
        100
    )


# ==========================================================
# 17. BULL FLAG
# ==========================================================

def detect_bull_flag(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L",
        "H",
        "L",
        "H",
        "L"
    ]:
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    pole = h1 - l1

    if pole <= 0:
        return None

    correction = (
        h1 - l3
    )

    if correction >= pole:
        return None

    if not (
        h2 < h1
        and l3 < l2
    ):
        return None

    return make_result(
        "Bull Flag",
        "Bullish",
        p,
        h2,
        l3 * 0.999,
        h2 + pole,
        100
    )


# ==========================================================
# 18. BEAR FLAG
# ==========================================================

def detect_bear_flag(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    pole = h1 - l1

    if pole <= 0:
        return None

    correction = (
        h3 - l1
    )

    if correction >= pole:
        return None

    if not (
        l2 > l1
        and h3 > h2
    ):
        return None

    return make_result(
        "Bear Flag",
        "Bearish",
        p,
        l2,
        h3 * 1.001,
        l2 - pole,
        100
    )


# ==========================================================
# 19. PENNANT
# ==========================================================

def detect_pennant(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    # Bullish pennant
    if [x["type"] for x in p] == [
        "L",
        "H",
        "L",
        "H",
        "L"
    ]:

        l1, h1, l2, h2, l3 = [
            x["val"] for x in p
        ]

        pole = h1 - l1

        if (
            pole > 0
            and h2 < h1
            and l2 > l1
            and l3 > l2
        ):

            return make_result(
                "Pennant",
                "Bullish",
                p,
                h2,
                l3 * 0.999,
                h2 + pole,
                100
            )

    # Bearish pennant
    if [x["type"] for x in p] == [
        "H",
        "L",
        "H",
        "L",
        "H"
    ]:

        h1, l1, h2, l2, h3 = [
            x["val"] for x in p
        ]

        pole = h1 - l1

        if (
            pole > 0
            and l2 > l1
            and h2 < h1
            and h3 < h2
        ):

            return make_result(
                "Pennant",
                "Bearish",
                p,
                l2,
                h3 * 1.001,
                l2 - pole,
                100
            )

    return None


# ==========================================================
# 20. MASTER FUNCTION
#
# ONLY COLLECTS INDIVIDUAL PATTERN RESULTS
# ==========================================================

def scan_and_calculate_logic(df):

    pivots = get_chronological_pivots(df)

    if len(pivots) < 3:

        return {
            "name":
                "NO PATTERN DETECTED",
            "bias":
                "Neutral",
            "match":
                0
        }

    current_pos = len(df) - 1

    detectors = [

        detect_head_shoulders,

        detect_inverse_head_shoulders,

        detect_double_top,

        detect_double_bottom,

        detect_triple_top,

        detect_triple_bottom,

        detect_ascending_triangle,

        detect_descending_triangle,

        detect_symmetrical_triangle,

        detect_rising_wedge,

        detect_falling_wedge,

        detect_rectangle,

        detect_bull_flag,

        detect_bear_flag,

        detect_pennant
    ]

    candidates = []

    for detector in detectors:

        try:

            result = detector(
                pivots,
                current_pos
            )

            if result is not None:
                candidates.append(result)

        except Exception:

            continue

    if not candidates:

        return {
            "name":
                "NO PATTERN DETECTED",
            "bias":
                "Neutral",
            "match":
                0
        }

    # Most recent pattern wins
    candidates.sort(
        key=lambda x:
        x["nodes"][-1][0]
    )

    return candidates[-1]


# ==========================================================
# 21. CONFIRMATION
# ==========================================================

def confirm_pattern(
    df,
    p_data
):

    latest_closed = df.iloc[-2]

    close = float(
        latest_closed["Close"]
    )

    ema200 = float(
        latest_closed["EMA200"]
    )

    rsi = float(
        latest_closed["RSI"]
    )

    macd_hist = float(
        latest_closed["MACD_Hist"]
    )

    bias = p_data["bias"]

    trigger = p_data[
        "entry_trigger"
    ]

    reasons = []

    if bias == "Neutral":

        return (
            "WAITING",
            "Waiting for directional breakout.",
            close
        )

    if bias == "Bullish":

        if close <= trigger:

            reasons.append(
                "Waiting for bullish breakout"
            )

        if close <= ema200:

            reasons.append(
                "Price below EMA200"
            )

        if not (
            25 <= rsi <= 82
        ):

            reasons.append(
                "RSI condition not met"
            )

        if macd_hist <= 0:

            reasons.append(
                "Bullish MACD confirmation missing"
            )

        if not reasons:

            return (
                "STRONG BUY",
                "All bullish conditions confirmed.",
                close
            )

    if bias == "Bearish":

        if close >= trigger:

            reasons.append(
                "Waiting for bearish breakout"
            )

        if close >= ema200:

            reasons.append(
                "Price above EMA200"
            )

        if not (
            25 <= rsi <= 82
        ):

            reasons.append(
                "RSI condition not met"
            )

        if macd_hist >= 0:

            reasons.append(
                "Bearish MACD confirmation missing"
            )

        if not reasons:

            return (
                "STRONG SELL",
                "All bearish conditions confirmed.",
                close
            )

    return (
        "WAITING",
        " | ".join(reasons),
        close
    )


# ==========================================================
# 22. FULL ANALYSIS
#
# SAME PUBLIC FUNCTION USED BY app.py
# ==========================================================

def run_full_analysis(df):

    df = calculate_indicators(df)

    df = calculate_zigzag(
        df,
        depth=12,
        deviation=5,
        backstep=3
    )

    p_data = scan_and_calculate_logic(df)

    if (
        p_data["name"]
        == "NO PATTERN DETECTED"
    ):

        return {
            "df": df,
            "pattern":
                "NO PATTERN DETECTED",
            "bias":
                "Neutral",
            "match_pct":
                0,
            "signal":
                "WAITING",
            "reason":
                "No active recent pattern found.",
            "entry":
                0,
            "sl":
                0,
            "tp":
                0,
            "trigger":
                0,
            "nodes":
                []
        }

    signal, reason, close = (
        confirm_pattern(
            df,
            p_data
        )
    )

    return {

        "df":
            df,

        "pattern":
            p_data["name"],

        "bias":
            p_data["bias"],

        "match_pct":
            round(
                p_data["match"],
                2
            ),

        "signal":
            signal,

        "reason":
            reason,

        "entry":
            round(
                close,
                4
            ),

        "sl":
            round(
                p_data["sl"],
                4
            ),

        "tp":
            round(
                p_data["tp"],
                4
            ),

        "trigger":
            round(
                p_data["entry_trigger"],
                4
            ),

        "nodes":
            p_data["nodes"],

        "neckline_start_idx":
            p_data.get(
                "neckline_start_idx",
                p_data["nodes"][0][0]
            )
    }
