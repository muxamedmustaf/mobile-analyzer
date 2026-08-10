# ============================================================
# MOBILE ANALYZER
# SWING.PY
# STRICT 50-CANDLE MAJOR ZIGZAG ENGINE
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

LOOKBACK = 1000

# Higher = fewer but stronger major swings
ZIGZAG_THRESHOLD = 0.012

# Minimum candles between major swings
MIN_SWING_DISTANCE = 2

# Maximum swings retained
MAX_SWINGS = 30


# ============================================================
# VALIDATION
# ============================================================

def _validate(df):

    required = [
        "open",
        "high",
        "low",
        "close",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing OHLC columns: {missing}"
        )

    if len(df) < LOOKBACK:
        raise ValueError(
            f"At least {LOOKBACK} candles are required."
        )


# ============================================================
# PIVOT DETECTION
# ============================================================

def _candidate_pivots(df):

    pivots = []

    high_values = df["high"].values
    low_values = df["low"].values

    # Use local neighborhood
    window = 3

    for i in range(
        window,
        len(df) - window
    ):

        current_high = high_values[i]
        current_low = low_values[i]

        left_highs = high_values[
            i - window:i
        ]

        right_highs = high_values[
            i + 1:i + window + 1
        ]

        left_lows = low_values[
            i - window:i
        ]

        right_lows = low_values[
            i + 1:i + window + 1
        ]

        is_high = (
            current_high >= left_highs.max()
            and
            current_high >= right_highs.max()
        )

        is_low = (
            current_low <= left_lows.min()
            and
            current_low <= right_lows.min()
        )

        if is_high:
            pivots.append({
                "index": i,
                "type": "HIGH",
                "price": float(
                    current_high
                ),
            })

        if is_low:
            pivots.append({
                "index": i,
                "type": "LOW",
                "price": float(
                    current_low
                ),
            })

    return pivots


# ============================================================
# ZIGZAG FILTER
# ============================================================

def _build_zigzag(
    pivots,
    threshold=ZIGZAG_THRESHOLD
):

    if not pivots:
        return []

    pivots = sorted(
        pivots,
        key=lambda x: x["index"]
    )

    result = []

    for pivot in pivots:

        if not result:

            result.append(
                pivot.copy()
            )
            continue

        last = result[-1]

        # ----------------------------------------------------
        # Same type:
        # keep the stronger extreme
        # ----------------------------------------------------

        if pivot["type"] == last["type"]:

            if pivot["type"] == "HIGH":

                if pivot["price"] > last["price"]:
                    result[-1] = pivot.copy()

            else:

                if pivot["price"] < last["price"]:
                    result[-1] = pivot.copy()

            continue

        # ----------------------------------------------------
        # Opposite type:
        # check price movement
        # ----------------------------------------------------

        movement = (
            abs(
                pivot["price"]
                -
                last["price"]
            )
            /
            last["price"]
        )

        if movement < threshold:
            continue

        candle_gap = (
            pivot["index"]
            -
            last["index"]
        )

        if candle_gap < MIN_SWING_DISTANCE:
            continue

        result.append(
            pivot.copy()
        )

    return result


# ============================================================
# STRUCTURE CLASSIFICATION
# ============================================================

def _classify_structure(swings):

    labels = []

    previous_high = None
    previous_low = None

    for swing in swings:

        label = None

        if swing["type"] == "HIGH":

            if previous_high is None:

                label = "H"

            elif swing["price"] > previous_high:

                label = "HH"

            else:

                label = "LH"

            previous_high = swing["price"]

        else:

            if previous_low is None:

                label = "L"

            elif swing["price"] > previous_low:

                label = "HL"

            else:

                label = "LL"

            previous_low = swing["price"]

        item = swing.copy()

        item["structure"] = label

        labels.append(item)

    return labels


# ============================================================
# TREND
# ============================================================

def _get_trend(swings):

    if len(swings) < 4:
        return "UNKNOWN"

    recent = swings[-6:]

    highs = [
        s for s in recent
        if s["type"] == "HIGH"
    ]

    lows = [
        s for s in recent
        if s["type"] == "LOW"
    ]

    bullish = False
    bearish = False

    if len(highs) >= 2:

        bullish_highs = (
            highs[-1]["price"]
            >
            highs[-2]["price"]
        )

        bearish_highs = (
            highs[-1]["price"]
            <
            highs[-2]["price"]
        )

    else:

        bullish_highs = False
        bearish_highs = False

    if len(lows) >= 2:

        bullish_lows = (
            lows[-1]["price"]
            >
            lows[-2]["price"]
        )

        bearish_lows = (
            lows[-1]["price"]
            <
            lows[-2]["price"]
        )

    else:

        bullish_lows = False
        bearish_lows = False

    if (
        bullish_highs
        and
        bullish_lows
    ):
        bullish = True

    if (
        bearish_highs
        and
        bearish_lows
    ):
        bearish = True

    if bullish:
        return "BULLISH"

    if bearish:
        return "BEARISH"

    return "RANGING"


# ============================================================
# BOS / CHOCH
# ============================================================

def _structure_events(
    df,
    swings
):

    bos = [None] * len(df)
    choch = [None] * len(df)

    if len(swings) < 3:
        return bos, choch

    trend = "UNKNOWN"

    last_high = None
    last_low = None

    for swing in swings:

        if swing["type"] == "HIGH":

            if last_high is not None:

                if (
                    swing["price"]
                    >
                    last_high
                ):

                    if trend == "BEARISH":

                        choch[
                            swing["index"]
                        ] = "CHOCH ↑"

                    else:

                        bos[
                            swing["index"]
                        ] = "BOS ↑"

                    trend = "BULLISH"

            last_high = swing["price"]

        else:

            if last_low is not None:

                if (
                    swing["price"]
                    <
                    last_low
                ):

                    if trend == "BULLISH":

                        choch[
                            swing["index"]
                        ] = "CHOCH ↓"

                    else:

                        bos[
                            swing["index"]
                        ] = "BOS ↓"

                    trend = "BEARISH"

            last_low = swing["price"]

    return bos, choch


# ============================================================
# MAIN ENGINE
# ============================================================

def detect_major_swings(
    df,
    threshold=ZIGZAG_THRESHOLD
):

    _validate(df)

    df = df.copy()

    # --------------------------------------------------------
    # Keep original index
    # --------------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Only last 50 candles are used
    # for major swing analysis
    # --------------------------------------------------------

    analysis_start = max(
        0,
        len(df) - LOOKBACK
    )

    work = df.iloc[
        analysis_start:
    ].copy()

    # --------------------------------------------------------
    # Candidate pivots
    # --------------------------------------------------------

    candidates = _candidate_pivots(
        work
    )

    # Convert local indexes to global indexes
    for pivot in candidates:

        pivot["index"] += analysis_start

    # --------------------------------------------------------
    # Strict ZigZag
    # --------------------------------------------------------

    zigzag = _build_zigzag(
        candidates,
        threshold
    )

    # --------------------------------------------------------
    # Structure
    # --------------------------------------------------------

    structured = _classify_structure(
        zigzag
    )

    # --------------------------------------------------------
    # Output columns
    # --------------------------------------------------------

    df["swing_high"] = False
    df["swing_low"] = False

    df["zigzag"] = np.nan
    df["zigzag_type"] = None

    df["structure"] = None

    # --------------------------------------------------------
    # Mark swings
    # --------------------------------------------------------

    for swing in structured:

        idx = swing["index"]

        if idx < 0 or idx >= len(df):
            continue

        if swing["type"] == "HIGH":

            df.loc[
                idx,
                "swing_high"
            ] = True

        else:

            df.loc[
                idx,
                "swing_low"
            ] = True

        df.loc[
            idx,
            "zigzag"
        ] = swing["price"]

        df.loc[
            idx,
            "zigzag_type"
        ] = swing["type"]

        df.loc[
            idx,
            "structure"
        ] = swing["structure"]

    # --------------------------------------------------------
    # BOS / CHOCH
    # --------------------------------------------------------

    bos, choch = _structure_events(
        df,
        structured
    )

    df["BOS"] = bos
    df["CHOCH"] = choch

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    trend = _get_trend(
        structured
    )

    # --------------------------------------------------------
    # Swing list
    # --------------------------------------------------------

    recent_swings = structured[
        -MAX_SWINGS:
    ]

    # --------------------------------------------------------
    # Attach useful metadata
    # --------------------------------------------------------

    df.attrs["major_swings"] = (
        recent_swings
    )

    df.attrs["trend"] = trend

    df.attrs["zigzag_threshold"] = (
        threshold
    )

    df.attrs["lookback"] = LOOKBACK

    return df


# ============================================================
# MARKET STRUCTURE ANALYSIS
# ============================================================

def analyze_market_structure(
    df,
    threshold=ZIGZAG_THRESHOLD
):

    result = detect_major_swings(
        df,
        threshold
    )

    swings = result.attrs.get(
        "major_swings",
        []
    )

    trend = result.attrs.get(
        "trend",
        "UNKNOWN"
    )

    # Latest BOS
    bos_values = result[
        result["BOS"].notna()
    ]["BOS"]

    latest_bos = (
        bos_values.iloc[-1]
        if len(bos_values)
        else None
    )

    # Latest CHOCH
    choch_values = result[
        result["CHOCH"].notna()
    ]["CHOCH"]

    latest_choch = (
        choch_values.iloc[-1]
        if len(choch_values)
        else None
    )

    return {
        "data": result,
        "swings": swings,
        "trend": trend,
        "bos": latest_bos,
        "choch": latest_choch,
    }


# ============================================================
# GET MAJOR SWINGS ONLY
# ============================================================

def get_major_swings(
    df,
    threshold=ZIGZAG_THRESHOLD
):

    result = detect_major_swings(
        df,
        threshold
    )

    return result.attrs.get(
        "major_swings",
        []
    )


# ============================================================
# GET LATEST STRUCTURE
# ============================================================

def get_latest_structure(
    df,
    threshold=ZIGZAG_THRESHOLD
):

    swings = get_major_swings(
        df,
        threshold
    )

    if not swings:
        return None

    return swings[-1]


# ============================================================
# GET TREND
# ============================================================

def get_trend(
    df,
    threshold=ZIGZAG_THRESHOLD
):

    result = detect_major_swings(
        df,
        threshold
    )

    return result.attrs.get(
        "trend",
        "UNKNOWN"
        )
