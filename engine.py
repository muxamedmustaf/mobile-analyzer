import pandas as pd
import numpy as np


# ==========================================================
# HEAD & SHOULDERS ENGINE
# ==========================================================

LOOKBACK = 80
PIVOT_LEFT = 3
PIVOT_RIGHT = 3

SHOULDER_TOLERANCE = 0.045
MIN_HEAD_HEIGHT = 0.10
MIN_NECK_DEPTH = 0.15
BREAK_BUFFER = 0.001


# ==========================================================
# BASIC HELPERS
# ==========================================================

def _same(a, b, tolerance=SHOULDER_TOLERANCE):
    if a == 0 or b == 0:
        return False

    return (
        abs(a - b)
        / max(abs(a), abs(b))
        <= tolerance
    )


def _recent(pivots, current_pos):
    if not pivots:
        return False

    return (
        current_pos - pivots[0]["pos"]
        <= LOOKBACK
    )


# ==========================================================
# PIVOT ENGINE
# ==========================================================

def _get_pivots(df):
    highs = []
    lows = []

    high = df["High"].astype(float).values
    low = df["Low"].astype(float).values

    for i in range(
        PIVOT_LEFT,
        len(df) - PIVOT_RIGHT
    ):

        left_highs = high[
            i - PIVOT_LEFT:i
        ]

        right_highs = high[
            i + 1:i + PIVOT_RIGHT + 1
        ]

        left_lows = low[
            i - PIVOT_LEFT:i
        ]

        right_lows = low[
            i + 1:i + PIVOT_RIGHT + 1
        ]

        # --------------------------------------------------
        # HIGH PIVOT
        # --------------------------------------------------

        if (
            high[i] > left_highs.max()
            and high[i] >= right_highs.max()
        ):
            highs.append({
                "pos": i,
                "time": df.index[i],
                "val": float(high[i]),
                "type": "H"
            })

        # --------------------------------------------------
        # LOW PIVOT
        # --------------------------------------------------

        if (
            low[i] < left_lows.min()
            and low[i] <= right_lows.min()
        ):
            lows.append({
                "pos": i,
                "time": df.index[i],
                "val": float(low[i]),
                "type": "L"
            })

    pivots = highs + lows

    pivots.sort(
        key=lambda x: x["pos"]
    )

    # ------------------------------------------------------
    # Remove consecutive pivots of same type
    # Keep the stronger extreme
    # ------------------------------------------------------

    clean = []

    for pivot in pivots:

        if not clean:
            clean.append(pivot)
            continue

        previous = clean[-1]

        if pivot["type"] != previous["type"]:
            clean.append(pivot)
            continue

        if pivot["type"] == "H":

            if pivot["val"] > previous["val"]:
                clean[-1] = pivot

        else:

            if pivot["val"] < previous["val"]:
                clean[-1] = pivot

    return clean


# ==========================================================
# NECKLINE CALCULATION
# ==========================================================

def _neckline_at(
    left_low,
    right_low,
    current_pos
):

    x1 = left_low["pos"]
    y1 = left_low["val"]

    x2 = right_low["pos"]
    y2 = right_low["val"]

    if x2 == x1:
        return (
            y1 + y2
        ) / 2

    slope = (
        y2 - y1
    ) / (
        x2 - x1
    )

    return (
        y2
        + slope
        * (
            current_pos - x2
        )
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
    # Search recent structures
    # ------------------------------------------------------

    start = max(
        0,
        len(pivots) - 10
    )

    for i in range(
        start,
        len(pivots) - 4
    ):

        p = pivots[
            i:i + 5
        ]

        # --------------------------------------------------
        # Required structure
        #
        # H - L - H - L - H
        #
        # Left Shoulder
        # Valley
        # Head
        # Valley
        # Right Shoulder
        # --------------------------------------------------

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

        if not _recent(
            p,
            current_pos
        ):
            continue

        left_shoulder = p[0]["val"]
        left_valley = p[1]["val"]
        head = p[2]["val"]
        right_valley = p[3]["val"]
        right_shoulder = p[4]["val"]

        # --------------------------------------------------
        # HEAD MUST BE HIGHER
        # --------------------------------------------------

        if not (
            head > left_shoulder
            and
            head > right_shoulder
        ):
            continue

        # --------------------------------------------------
        # SHOULDERS MUST BE SIMILAR
        # --------------------------------------------------

        if not _same(
            left_shoulder,
            right_shoulder
        ):
            continue

        # --------------------------------------------------
        # LEFT / RIGHT VALLEYS
        # Must remain below shoulders
        # --------------------------------------------------

        if not (
            left_valley < left_shoulder
            and
            right_valley < right_shoulder
        ):
            continue

        # --------------------------------------------------
        # HEAD DEPTH
        # --------------------------------------------------

        shoulder_average = (
            left_shoulder
            + right_shoulder
        ) / 2

        head_extra = (
            head
            - shoulder_average
        )

        if head_extra <= 0:
            continue

        if (
            head_extra / head
            < MIN_HEAD_HEIGHT
        ):
            continue

        # --------------------------------------------------
        # NECKLINE DEPTH
        # --------------------------------------------------

        raw_neckline = (
            left_valley
            + right_valley
        ) / 2

        neck_depth = (
            head
            - raw_neckline
        )

        if neck_depth <= 0:
            continue

        if (
            neck_depth / head
            < MIN_NECK_DEPTH
        ):
            continue

        # --------------------------------------------------
        # NECKLINE AT CURRENT CANDLE
        # --------------------------------------------------

        neckline = _neckline_at(
            p[1],
            p[3],
            current_pos
        )

        if neckline <= 0:
            continue

        # --------------------------------------------------
        # CURRENT PRICE
        # --------------------------------------------------

        # Price confirmation is calculated outside here
        # because this detector only receives pivots.
        #
        # The returned structure is therefore FORMING.
        # run_full_analysis() performs final confirmation.
        # --------------------------------------------------

        height = (
            head
            - neckline
        )

        if height <= 0:
            continue

        # --------------------------------------------------
        # STRUCTURAL STOP
        # --------------------------------------------------

        sl = (
            max(
                left_shoulder,
                head,
                right_shoulder
            )
            * 1.003
        )

        # --------------------------------------------------
        # TARGET
        # --------------------------------------------------

        tp = (
            neckline
            - height
        )

        # --------------------------------------------------
        # ENTRY
        # --------------------------------------------------

        entry = neckline

        nodes = [
            (
                p[0]["time"],
                left_shoulder
            ),
            (
                p[1]["time"],
                left_valley
            ),
            (
                p[2]["time"],
                head
            ),
            (
                p[3]["time"],
                right_valley
            ),
            (
                p[4]["time"],
                right_shoulder
            )
        ]

        return {
            "name":
                "Head & Shoulders",

            "bias":
                "Bearish",

            "entry_trigger":
                float(entry),

            "sl":
                float(sl),

            "tp":
                float(tp),

            "nodes":
                nodes,

            "neckline_points": [
                (
                    p[1]["time"],
                    left_valley
                ),
                (
                    p[3]["time"],
                    right_valley
                )
            ],

            "pattern_start":
                p[0]["time"],

            "pattern_end":
                p[4]["time"],

            "head":
                head,

            "left_shoulder":
                left_shoulder,

            "right_shoulder":
                right_shoulder,

            "left_valley":
                left_valley,

            "right_valley":
                right_valley,

            "height":
                float(height)
        }

    return None


# ==========================================================
# FINAL ANALYSIS
# ==========================================================

def run_full_analysis(df):

    # ------------------------------------------------------
    # Safety copy
    # ------------------------------------------------------

    df_calc = df.copy()

    # ------------------------------------------------------
    # Normalize columns
    # ------------------------------------------------------

    required = [
        "Open",
        "High",
        "Low",
        "Close"
    ]

    for col in required:
        if col not in df_calc.columns:
            raise ValueError(
                f"Missing column: {col}"
            )

        df_calc[col] = pd.to_numeric(
            df_calc[col],
            errors="coerce"
        )

    df_calc = df_calc.dropna(
        subset=required
    )

    if len(df_calc) < 30:
        raise ValueError(
            "Not enough candles"
        )

    # ------------------------------------------------------
    # RSI
    # ------------------------------------------------------

    delta = (
        df_calc["Close"]
        .diff()
    )

    gain = (
        delta.clip(lower=0)
        .rolling(14)
        .mean()
    )

    loss = (
        -delta.clip(upper=0)
        .rolling(14)
        .mean()
    )

    rs = gain / loss.replace(
        0,
        np.nan
    )

    df_calc["RSI"] = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    # ------------------------------------------------------
    # PIVOTS
    # ------------------------------------------------------

    pivots = _get_pivots(
        df_calc
    )

    current_pos = (
        len(df_calc) - 1
    )

    # ------------------------------------------------------
    # DETECT HEAD & SHOULDERS
    # ------------------------------------------------------

    detected = detect_head_shoulders(
        pivots,
        current_pos
    )

    latest_close = float(
        df_calc["Close"].iloc[-1]
    )

    # ======================================================
    # NO PATTERN
    # ======================================================

    if detected is None:

        return {
            "df":
                df_calc,

            "signal":
                "WAITING",

            "pattern":
                "NO PATTERN DETECTED",

            "bias":
                "Neutral",

            "entry":
                round(
                    latest_close,
                    4
                ),

            "sl":
                round(
                    latest_close * 0.99,
                    4
                ),

            "tp":
                round(
                    latest_close * 1.01,
                    4
                ),

            "trigger":
                latest_close,

            "nodes":
                []
        }

    # ======================================================
    # PATTERN FOUND
    # ======================================================

    neckline = detected[
        "entry_trigger"
    ]

    sl = detected["sl"]
    tp = detected["tp"]

    # ------------------------------------------------------
    # Confirmation
    #
    # Bearish H&S:
    # Current candle must close below neckline
    # ------------------------------------------------------

    confirmation_level = (
        neckline
        * (
            1
            - BREAK_BUFFER
        )
    )

    confirmed = (
        latest_close
        < confirmation_level
    )

    # ------------------------------------------------------
    # Signal
    # ------------------------------------------------------

    if confirmed:

        signal = "STRONG SELL"

    else:

        signal = "WAITING"

    # ------------------------------------------------------
    # Result
    # ------------------------------------------------------

    return {
        "df":
            df_calc,

        "signal":
            signal,

        "pattern":
            "Head & Shoulders",

        "bias":
            "Bearish",

        "entry":
            round(
                neckline,
                4
            ),

        "sl":
            round(
                sl,
                4
            ),

        "tp":
            round(
                tp,
                4
            ),

        "trigger":
            round(
                neckline,
                4
            ),

        "nodes":
            detected["nodes"],

        "neckline_points":
            detected[
                "neckline_points"
            ],

        "pattern_start":
            detected[
                "pattern_start"
            ],

        "pattern_end":
            detected[
                "pattern_end"
            ],

        "head":
            detected["head"],

        "left_shoulder":
            detected[
                "left_shoulder"
            ],

        "right_shoulder":
            detected[
                "right_shoulder"
            ],

        "height":
            detected["height"]
    }
