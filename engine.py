import pandas as pd
import numpy as np


# ==========================================================
# HEAD & SHOULDERS ENGINE
# ==========================================================

MAX_PATTERN_AGE = 25

SHOULDER_TOLERANCE = 0.03
NECKLINE_TOLERANCE = 0.03
MIN_HEAD_DISTANCE = 0.005


# ==========================================================
# INDICATORS
# ==========================================================

def calculate_indicators(df):

    df = df.copy()

    df["EMA50"] = (
        df["Close"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    df["EMA200"] = (
        df["Close"]
        .ewm(span=200, adjust=False)
        .mean()
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

    loss = loss.replace(0, 1e-9)

    rs = gain / loss

    df["RSI"] = 100 - (
        100 / (1 + rs)
    )

    df["RSI"] = df["RSI"].fillna(50)

    return df


# ==========================================================
# ZIGZAG / MAJOR SWINGS
# ==========================================================

def calculate_zigzag(
    df,
    depth=7,
    deviation=5,
    backstep=3
):

    df = df.copy()

    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].astype(float).values
    lows = df["Low"].astype(float).values

    n = len(df)

    for i in range(
        depth,
        n - backstep
    ):

        high_window = highs[
            i - depth:
            i + backstep + 1
        ]

        low_window = lows[
            i - depth:
            i + backstep + 1
        ]

        current_high = highs[i]
        current_low = lows[i]

        is_high = (
            current_high ==
            np.max(high_window)
            and
            np.sum(
                high_window ==
                current_high
            ) == 1
        )

        is_low = (
            current_low ==
            np.min(low_window)
            and
            np.sum(
                low_window ==
                current_low
            ) == 1
        )

        if is_high and not is_low:

            df.iloc[
                i,
                df.columns.get_loc(
                    "Pivot_H"
                )
            ] = current_high

        elif is_low and not is_high:

            df.iloc[
                i,
                df.columns.get_loc(
                    "Pivot_L"
                )
            ] = current_low

    return df


# ==========================================================
# CHRONOLOGICAL PIVOTS
# ==========================================================

def get_chronological_pivots(df):

    pivots = []

    for pos, (idx, row) in enumerate(
        df.iterrows()
    ):

        if not pd.isna(
            row["Pivot_H"]
        ):

            pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(
                    row["Pivot_H"]
                ),
                "type": "H"
            })

        elif not pd.isna(
            row["Pivot_L"]
        ):

            pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(
                    row["Pivot_L"]
                ),
                "type": "L"
            })

    # ------------------------------------------------------
    # STRICT ALTERNATION
    # ------------------------------------------------------

    clean = []

    for p in pivots:

        if not clean:

            clean.append(p)
            continue

        last = clean[-1]

        if last["type"] != p["type"]:

            clean.append(p)
            continue

        if p["type"] == "H":

            if p["val"] > last["val"]:
                clean[-1] = p

        else:

            if p["val"] < last["val"]:
                clean[-1] = p

    return clean


# ==========================================================
# HELPERS
# ==========================================================

def _variation(a, b):

    return abs(a - b) / max(
        abs(a),
        abs(b),
        1e-9
    )


def _recent_pattern(
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


# ==========================================================
# HEAD & SHOULDERS DETECTOR
# ==========================================================

def detect_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    # ------------------------------------------------------
    # Examine only the latest major structures
    # ------------------------------------------------------

    start = max(
        0,
        len(pivots) - 8
    )

    for i in range(
        start,
        len(pivots) - 4
    ):

        p = pivots[
            i:i + 5
        ]

        # Required geometry:
        #
        # H - L - H - L - H
        #
        if [
            x["type"] for x in p
        ] != [
            "H",
            "L",
            "H",
            "L",
            "H"
        ]:

            continue

        # Pattern must be recent

        if not _recent_pattern(
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
        # 1. HEAD MUST BE ABOVE BOTH SHOULDERS
        # --------------------------------------------------

        if h2 <= h1:
            continue

        if h2 <= h3:
            continue

        # --------------------------------------------------
        # 2. HEAD MUST BE MEANINGFULLY HIGHER
        # --------------------------------------------------

        if _variation(
            h2,
            h1
        ) < MIN_HEAD_DISTANCE:

            continue

        if _variation(
            h2,
            h3
        ) < MIN_HEAD_DISTANCE:

            continue

        # --------------------------------------------------
        # 3. SHOULDERS SHOULD BE SIMILAR
        # --------------------------------------------------

        shoulder_difference = (
            abs(h1 - h3)
            /
            max(
                abs(h1),
                abs(h3),
                1e-9
            )
        )

        if (
            shoulder_difference
            > SHOULDER_TOLERANCE
        ):

            continue

        # --------------------------------------------------
        # 4. BOTH NECKLINE LOWS SHOULD BE REASONABLY CLOSE
        # --------------------------------------------------

        neckline_difference = (
            abs(l1 - l2)
            /
            max(
                abs(l1),
                abs(l2),
                1e-9
            )
        )

        if (
            neckline_difference
            > NECKLINE_TOLERANCE
        ):

            continue

        # --------------------------------------------------
        # 5. BOTH CORRECTIONS MUST BE MEANINGFUL
        # --------------------------------------------------

        left_depth = h1 - l1

        right_depth = h2 - l2

        if left_depth <= 0:
            continue

        if right_depth <= 0:
            continue

        # --------------------------------------------------
        # 6. NECKLINE
        # --------------------------------------------------

        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:

            neckline = (
                l1 + l2
            ) / 2

        else:

            slope = (
                l2 - l1
            ) / (
                x2 - x1
            )

            neckline = (
                l2
                +
                slope
                *
                (
                    current_pos -
                    x2
                )
            )

        # --------------------------------------------------
        # 7. PATTERN HEIGHT
        # --------------------------------------------------

        height = (
            h2 -
            neckline
        )

        if height <= 0:
            continue

        # --------------------------------------------------
        # 8. ENTRY
        #
        # Breakdown of neckline
        # --------------------------------------------------

        entry = neckline

        # --------------------------------------------------
        # 9. STOP LOSS
        #
        # Above right shoulder
        # --------------------------------------------------

        sl = h3 * 1.001

        # --------------------------------------------------
        # 10. TARGET
        #
        # Classical H&S projection:
        #
        # Head - Neckline
        # projected below neckline
        # --------------------------------------------------

        tp = (
            neckline -
            height
        )

        # --------------------------------------------------
        # 11. RESULT
        # --------------------------------------------------

        return {
            "name":
                "Head and Shoulders",

            "pattern":
                "Head and Shoulders",

            "bias":
                "Bearish",

            "signal":
                "WAITING",

            "match":
                100.0,

            "score":
                100.0,

            "entry":
                float(entry),

            "entry_trigger":
                float(entry),

            "sl":
                float(sl),

            "tp":
                float(tp),

            "trigger":
                float(entry),

            "nodes": [
                (
                    x["idx"],
                    x["val"]
                )
                for x in p
            ],

            "points": p,

            "neckline":
                float(neckline),

            "neckline_start_idx":
                p[1]["idx"],

            "pattern_start":
                p[0]["idx"],

            "pattern_end":
                p[4]["idx"],

            "reason":
                "Head and Shoulders structure detected"
        }

    return None


# ==========================================================
# SIGNAL CONFIRMATION
# ==========================================================

def confirm_signal(
    df,
    pattern
):

    if pattern is None:

        return "WAITING"

    if len(df) < 2:

        return "WAITING"

    current_close = float(
        df["Close"].iloc[-1]
    )

    previous_close = float(
        df["Close"].iloc[-2]
    )

    neckline = float(
        pattern["neckline"]
    )

    # ------------------------------------------------------
    # CONFIRMED BEARISH BREAK
    # ------------------------------------------------------

    if (
        previous_close >= neckline
        and
        current_close < neckline
    ):

        return "STRONG SELL"

    return "WAITING"


# ==========================================================
# FULL ANALYSIS
# ==========================================================

def run_full_analysis(df):

    df = df.copy()

    # ------------------------------------------------------
    # Normalize columns
    # ------------------------------------------------------

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = (
            df.columns
            .get_level_values(0)
        )

    required = [
        "Open",
        "High",
        "Low",
        "Close"
    ]

    for col in required:

        if col not in df.columns:

            raise ValueError(
                f"Missing column: {col}"
            )

    df = df[
        required
    ].copy()

    df = df.dropna()

    if len(df) < 30:

        return {
            "df": df,
            "signal": "WAITING",
            "pattern":
                "NO PATTERN DETECTED",
            "bias": "Neutral",
            "entry": None,
            "sl": None,
            "tp": None,
            "trigger": None,
            "nodes": []
        }

    # ------------------------------------------------------
    # Indicators
    # ------------------------------------------------------

    df = calculate_indicators(
        df
    )

    # ------------------------------------------------------
    # ZigZag
    # ------------------------------------------------------

    df = calculate_zigzag(
        df
    )

    # ------------------------------------------------------
    # Pivots
    # ------------------------------------------------------

    pivots = (
        get_chronological_pivots(
            df
        )
    )

    current_pos = len(df) - 1

    # ------------------------------------------------------
    # Head & Shoulders
    # ------------------------------------------------------

    pattern = detect_head_shoulders(
        pivots,
        current_pos
    )

    # ------------------------------------------------------
    # No pattern
    # ------------------------------------------------------

    if pattern is None:

        return {
            "df": df,
            "signal": "WAITING",
            "pattern":
                "NO PATTERN DETECTED",
            "bias": "Neutral",
            "entry": None,
            "sl": None,
            "tp": None,
            "trigger": None,
            "nodes": [],
            "pivots": pivots
        }

    # ------------------------------------------------------
    # Signal
    # ------------------------------------------------------

    signal = confirm_signal(
        df,
        pattern
    )

    pattern["signal"] = signal

    # ------------------------------------------------------
    # Final result
    # ------------------------------------------------------

    result = {

        "df":
            df,

        "signal":
            signal,

        "pattern":
            pattern["pattern"],

        "bias":
            pattern["bias"],

        "entry":
            pattern["entry"],

        "sl":
            pattern["sl"],

        "tp":
            pattern["tp"],

        "trigger":
            pattern["trigger"],

        "entry_trigger":
            pattern["entry_trigger"],

        "nodes":
            pattern["nodes"],

        "points":
            pattern["points"],

        "neckline":
            pattern["neckline"],

        "neckline_start_idx":
            pattern[
                "neckline_start_idx"
            ],

        "pattern_start":
            pattern[
                "pattern_start"
            ],

        "pattern_end":
            pattern[
                "pattern_end"
            ],

        "match":
            pattern["match"],

        "score":
            pattern["score"],

        "reason":
            pattern["reason"],

        "pivots":
            pivots
    }

    return result
