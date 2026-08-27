# ============================================================
# BACKTEST — HEAD AND SHOULDERS
# 4H / LAST MONTH
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# ============================================================
# SETTINGS
# ============================================================

INTERVAL = "1h"
PERIOD = "60d"

PIVOT_LEFT = 3
PIVOT_RIGHT = 3

SHOULDER_TOLERANCE = 0.045
MIN_HEAD_DEPTH = 0.10
MIN_NECK_DEPTH = 0.20

MAX_PATTERN_BARS = 80
MAX_FORWARD_BARS = 80


# ============================================================
# DATA
# ============================================================

def load_data(symbol):

    df = yf.download(
        symbol,
        period=PERIOD,
        interval=INTERVAL,
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[
        ["Open", "High", "Low", "Close"]
    ].dropna()

    # Yahoo 1H → 4H
    df = df.resample("4h").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last"
    }).dropna()

    return df


# ============================================================
# PIVOTS
# ============================================================

def get_pivots(df):

    pivots = []

    highs = df["High"].values
    lows = df["Low"].values

    for i in range(
        PIVOT_LEFT,
        len(df) - PIVOT_RIGHT
    ):

        high_window = highs[
            i - PIVOT_LEFT:
            i + PIVOT_RIGHT + 1
        ]

        low_window = lows[
            i - PIVOT_LEFT:
            i + PIVOT_RIGHT + 1
        ]

        if highs[i] == max(high_window):

            pivots.append({
                "pos": i,
                "type": "H",
                "val": float(highs[i])
            })

        elif lows[i] == min(low_window):

            pivots.append({
                "pos": i,
                "type": "L",
                "val": float(lows[i])
            })

    return pivots


# ============================================================
# HELPERS
# ============================================================

def same(a, b, tolerance=SHOULDER_TOLERANCE):

    if a == 0 or b == 0:
        return False

    return abs(a - b) / max(
        abs(a),
        abs(b)
    ) <= tolerance


def valid_depth(
    level,
    reference,
    reaction
):

    distance = abs(
        reference - reaction
    )

    base = abs(reference)

    if base == 0:
        return False

    return (
        distance / base
        >= MIN_NECK_DEPTH
    )


def previous_bearish_structure(
    pivots,
    start_index
):

    if start_index < 2:
        return True

    previous = pivots[
        max(0, start_index - 3):
        start_index
    ]

    if len(previous) < 2:
        return True

    highs = [
        x["val"]
        for x in previous
        if x["type"] == "H"
    ]

    lows = [
        x["val"]
        for x in previous
        if x["type"] == "L"
    ]

    if len(highs) >= 2 and len(lows) >= 2:

        return (
            highs[-1] < highs[-2]
            and lows[-1] < lows[-2]
        )

    return True


# ============================================================
# HEAD & SHOULDERS DETECTOR
# ============================================================

def detect_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    start = max(
        0,
        len(pivots) - 7
    )

    for i in range(
        start,
        len(pivots) - 4
    ):

        p = pivots[
            i:i + 5
        ]

        if [
            x["type"]
            for x in p
        ] != [
            "H",
            "L",
            "H",
            "L",
            "H"
        ]:
            continue

        h1, l1, h2, l2, h3 = [
            x["val"]
            for x in p
        ]

        # ----------------------------------------
        # Previous bullish structure
        # ----------------------------------------

        if not previous_bullish_structure(
            pivots,
            i
        ):
            continue

        # ----------------------------------------
        # Head higher than both shoulders
        # ----------------------------------------

        if not (
            h2 > h1
            and h2 > h3
        ):
            continue

        # ----------------------------------------
        # Shoulders approximately equal
        # ----------------------------------------

        if not same(
            h1,
            h3
        ):
            continue

        # ----------------------------------------
        # Neckline depth
        # ----------------------------------------

        left_depth = h1 - l1
        right_depth = h3 - l2

        if left_depth <= 0:
            continue

        if right_depth <= 0:
            continue

        # ----------------------------------------
        # Head must be meaningful
        # ----------------------------------------

        head_depth = (
            h2
            - max(h1, h3)
        )

        if (
            head_depth
            / h2
            < MIN_HEAD_DEPTH
        ):
            continue

        # ----------------------------------------
        # Corrections should be meaningful
        # ----------------------------------------

        if not valid_depth(
            l1,
            h1,
            l1
        ):
            continue

        if not valid_depth(
            l2,
            h3,
            l2
        ):
            continue

        # ----------------------------------------
        # Neckline
        # ----------------------------------------

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
                + slope
                * (
                    current_pos - x2
                )
            )

        # ----------------------------------------
        # Pattern height
        # ----------------------------------------

        head = h2

        height = (
            head
            - neckline
        )

        if height <= 0:
            continue

        return {
            "name":
                "Head and Shoulders",

            "pivots":
                p,

            "head":
                h2,

            "left_shoulder":
                h1,

            "right_shoulder":
                h3,

            "left_neck":
                l1,

            "right_neck":
                l2,

            "neckline":
                neckline,

            "height":
                height,

            "pattern_start":
                p[0]["pos"],

            "pattern_end":
                p[-1]["pos"]
        }

    return None


def previous_bullish_structure(
    pivots,
    start_index
):

    if start_index < 2:
        return True

    previous = pivots[
        max(0, start_index - 3):
        start_index
    ]

    if len(previous) < 2:
        return True

    highs = [
        x["val"]
        for x in previous
        if x["type"] == "H"
    ]

    lows = [
        x["val"]
        for x in previous
        if x["type"] == "L"
    ]

    if len(highs) >= 2 and len(lows) >= 2:

        return (
            highs[-1] > highs[-2]
            and lows[-1] > lows[-2]
        )

    return True


# ============================================================
# FORWARD TEST
# ============================================================

def test_pattern(
    df,
    pattern
):

    start = pattern[
        "pattern_end"
    ]

    neckline = pattern[
        "neckline"
    ]

    height = pattern[
        "height"
    ]

    entry = neckline

    stop_loss = (
        pattern["right_shoulder"]
        * 1.001
    )

    target = (
        neckline
        - height
    )

    result = "OPEN"

    hit_bar = None

    for i in range(
        start + 1,
        min(
            len(df),
            start + 1 + MAX_FORWARD_BARS
        )
    ):

        high = float(
            df["High"].iloc[i]
        )

        low = float(
            df["Low"].iloc[i]
        )

        close = float(
            df["Close"].iloc[i]
        )

        # ----------------------------------------
        # Entry confirmation
        # ----------------------------------------

        if not pattern.get(
            "entered",
            False
        ):

            if close < neckline:

                pattern["entered"] = True
                pattern["entry_bar"] = i

            else:
                continue

        # ----------------------------------------
        # Stop Loss
        # ----------------------------------------

        if high >= stop_loss:

            result = "FAILED"
            hit_bar = i
            break

        # ----------------------------------------
        # Target
        # ----------------------------------------

        if low <= target:

            result = "SUCCESS"
            hit_bar = i
            break

    return {
        "result":
            result,

        "entry":
            entry,

        "sl":
            stop_loss,

        "target":
            target,

        "hit_bar":
            hit_bar
    }


# ============================================================
# FIND ALL PATTERNS
# ============================================================

def scan_month(
    df
):

    pivots = get_pivots(df)

    found = []

    used_end_positions = set()

    for current_pos in range(
        5,
        len(df)
    ):

        available = [
            p
            for p in pivots
            if p["pos"] <= current_pos
        ]

        pattern = detect_head_shoulders(
            available,
            current_pos
        )

        if pattern is None:
            continue

        end_pos = pattern[
            "pattern_end"
        ]

        if end_pos in used_end_positions:
            continue

        # Only completed patterns
        if end_pos >= current_pos:
            continue

        test = test_pattern(
            df,
            pattern
        )

        pattern.update(
            test
        )

        found.append(
            pattern
        )

        used_end_positions.add(
            end_pos
        )

    return found


# ============================================================
# DRAW PATTERN
# ============================================================

def draw_pattern(
    df,
    pattern
):

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        )
    )

    pivots = pattern[
        "pivots"
    ]

    x_nodes = [
        df.index[
            p["pos"]
        ]
        for p in pivots
    ]

    y_nodes = [
        p["val"]
        for p in pivots
    ]

    fig.add_trace(
        go.Scatter(
            x=x_nodes,
            y=y_nodes,
            mode="lines+markers",
            name="Head & Shoulders"
        )
    )

    # Neckline

    start_pos = pattern[
        "left_neck"
        if False else
        "pattern_start"
    ]

    end_pos = min(
        len(df) - 1,
        pattern[
            "pattern_end"
        ] + 30
    )

    x1 = df.index[
        pattern["pivots"][1]["pos"]
    ]

    x2 = df.index[
        end_pos
    ]

    y1 = pattern[
        "pivots"
    ][1]["val"]

    y2 = pattern[
        "neckline"
    ]

    fig.add_trace(
        go.Scatter(
            x=[
                x1,
                x2
            ],
            y=[
                y1,
                y2
            ],
            mode="lines",
            name="Neckline"
        )
    )

    # Target

    fig.add_hline(
        y=pattern["target"],
        annotation_text="TARGET"
    )

    # Stop

    fig.add_hline(
        y=pattern["sl"],
        annotation_text="STOP"
    )

    fig.update_layout(
        template="plotly_white",
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True
    )

    return fig


# ============================================================
# MAIN BACKTEST
# ============================================================

def run_backtest(
    symbol
):

    df = load_data(
        symbol
    )

    if df.empty:
        return {
            "symbol": symbol,
            "patterns": [],
            "total": 0,
            "success": 0,
            "failed": 0,
            "open": 0,
            "win_rate": 0
        }

    patterns = scan_month(
        df
    )

    success = sum(
        1
        for p in patterns
        if p["result"] == "SUCCESS"
    )

    failed = sum(
        1
        for p in patterns
        if p["result"] == "FAILED"
    )

    open_count = sum(
        1
        for p in patterns
        if p["result"] == "OPEN"
    )

    closed = (
        success
        + failed
    )

    win_rate = (
        success / closed * 100
        if closed > 0
        else 0
    )

    return {
        "symbol":
            symbol,

        "data":
            df,

        "patterns":
            patterns,

        "total":
            len(patterns),

        "success":
            success,

        "failed":
            failed,

        "open":
            open_count,

        "win_rate":
            round(
                win_rate,
                2
            )
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    SYMBOL = "NZDCAD=X"

    result = run_backtest(
        SYMBOL
    )

    print()
    print("=" * 60)
    print("HEAD AND SHOULDERS BACKTEST")
    print("=" * 60)

    print(
        f"Symbol: {result['symbol']}"
    )

    print(
        f"Patterns: {result['total']}"
    )

    print(
        f"Success: {result['success']}"
    )

    print(
        f"Failed: {result['failed']}"
    )

    print(
        f"Open: {result['open']}"
    )

    print(
        f"Win Rate: {result['win_rate']}%"
    )

    print("=" * 60)

    for n, pattern in enumerate(
        result["patterns"],
        1
    ):

        print()
        print(
            f"Pattern #{n}"
        )

        print(
            "Result:",
            pattern["result"]
        )

        print(
            "Entry:",
            round(
                pattern["entry"],
                4
            )
        )

        print(
            "SL:",
            round(
                pattern["sl"],
                4
            )
        )

        print(
            "Target:",
            round(
                pattern["target"],
                4
            )
        )
