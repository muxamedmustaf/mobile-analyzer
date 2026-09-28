# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

# ==========================================================
# ENGINE.PY - STRICT REAL-TIME H&S LIVE SCANNER
# ==========================================================

MIN_WAVE_CANDLES = 3
MAX_H3_AGE = 8
MAX_PATTERN_SPAN = 60
MAX_ACTIVE_CANDLES = 50


def calculate_indicators(df):
    df = df.copy()

    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()

    loss_safe = loss.replace(0, 1e-9)
    rs = gain / loss_safe

    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50.0)

    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())

    ranges = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    )

    true_range = ranges.max(axis=1)

    df["ATR"] = true_range.rolling(14).mean()

    df["Dynamic_Swing"] = (
        df["ATR"] / df["Close"]
    ) * 0.5

    df["Dynamic_Swing"] = df["Dynamic_Swing"].fillna(0.001)

    if "Volume" in df.columns:
        df["Volume_SMA"] = (
            df["Volume"]
            .rolling(20)
            .mean()
            .bfill()
            .fillna(0)
        )
    else:
        df["Volume_SMA"] = 0

    return df


def calculate_zigzag(df, depth=12, backstep=6):
    df = df.copy()

    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].astype(float).values
    lows = df["Low"].astype(float).values

    n = len(df)

    for i in range(depth, n - backstep):

        high_window = highs[
            i - depth:i + backstep + 1
        ]

        low_window = lows[
            i - depth:i + backstep + 1
        ]

        current_high = highs[i]
        current_low = lows[i]

        is_high = (
            current_high == np.max(high_window)
            and np.sum(high_window == current_high) == 1
        )

        is_low = (
            current_low == np.min(low_window)
            and np.sum(low_window == current_low) == 1
        )

        if is_high and not is_low:
            df.iloc[
                i,
                df.columns.get_loc("Pivot_H")
            ] = current_high

        elif is_low and not is_high:
            df.iloc[
                i,
                df.columns.get_loc("Pivot_L")
            ] = current_low

    return df


def get_chronological_pivots(df):
    raw = []

    for pos, (idx, row) in enumerate(df.iterrows()):

        if not pd.isna(row["Pivot_H"]):

            raw.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_H"]),
                "type": "H",
                "dynamic_swing": float(
                    row.get("Dynamic_Swing", 0.001)
                )
            })

        elif not pd.isna(row["Pivot_L"]):

            raw.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_L"]),
                "type": "L",
                "dynamic_swing": float(
                    row.get("Dynamic_Swing", 0.001)
                )
            })

    if not raw:
        return []

    clean = []

    for p in raw:

        if not clean:
            clean.append(p)
            continue

        last = clean[-1]

        current_min_swing = p["dynamic_swing"]

        if last["type"] != p["type"]:

            movement = (
                abs(p["val"] - last["val"])
                / max(abs(last["val"]), 1e-9)
            )

            if movement >= current_min_swing:

                clean.append(p)

            else:

                if (
                    last["type"] == "H"
                    and p["val"] > last["val"]
                ):
                    clean[-1] = p

                elif (
                    last["type"] == "L"
                    and p["val"] < last["val"]
                ):
                    clean[-1] = p

        elif (
            p["type"] == "H"
            and p["val"] > last["val"]
        ):

            clean[-1] = p

        elif (
            p["type"] == "L"
            and p["val"] < last["val"]
        ):

            clean[-1] = p

    final_clean = []

    for p in clean:

        if not final_clean:

            final_clean.append(p)

        else:

            if (
                final_clean[-1]["type"]
                != p["type"]
            ):

                final_clean.append(p)

            else:

                if (
                    p["type"] == "H"
                    and p["val"] > final_clean[-1]["val"]
                ):
                    final_clean[-1] = p

                elif (
                    p["type"] == "L"
                    and p["val"] < final_clean[-1]["val"]
                ):
                    final_clean[-1] = p

    return final_clean


# ==========================================================
# ACTIVE TRADE TRACKING
# ==========================================================

def check_active_trade(
    df,
    activation_pos,
    entry,
    sl,
    tp,
    bias
):
    latest_pos = len(df) - 1

    candles_active = latest_pos - activation_pos

    if candles_active > MAX_ACTIVE_CANDLES:
        return "TIMEOUT"

    for pos in range(
        activation_pos + 1,
        latest_pos + 1
    ):

        row = df.iloc[pos]

        high = float(row["High"])
        low = float(row["Low"])

        if bias == "Bearish":

            hit_sl = high >= sl
            hit_tp = low <= tp

            if hit_sl:
                return "SL"

            if hit_tp:
                return "TP"

        else:

            hit_sl = low <= sl
            hit_tp = high >= tp

            if hit_sl:
                return "SL"

            if hit_tp:
                return "TP"

    return "ACTIVE"


# ==========================================================
# NORMAL HEAD & SHOULDERS
# ==========================================================

def detect_all_head_shoulders(pivots, df):

    patterns = []

    if len(pivots) < 6:
        return patterns

    total_candles = len(df)

    for i in range(len(pivots) - 5):

        p = pivots[i:i + 6]

        if [
            x["type"] for x in p
        ] != [
            "L", "H", "L", "H", "L", "H"
        ]:
            continue

        pos_l0 = p[0]["pos"]
        pos_h3 = p[5]["pos"]

        if (
            pos_h3 - pos_l0
        ) > MAX_PATTERN_SPAN:
            continue

        l0, h1, l1, h2, l2, h3 = [
            x["val"] for x in p
        ]

        if h1 <= l0:
            continue

        if l1 <= l0:
            continue

        if h2 <= h1:
            continue

        if h2 <= h3:
            continue

        left_shoulder_height = (
            h1 - min(l0, l1)
        )

        right_shoulder_height = (
            h3 - min(l1, l2)
        )

        if (
            left_shoulder_height <= 0
            or right_shoulder_height <= 0
        ):
            continue

        head_height = (
            h2 - min(l1, l2)
        )

        if head_height <= 0:
            continue

        if abs(h1 - h3) > (
            head_height * 0.20
        ):
            continue

        idx_l1 = p[2]["idx"]
        idx_l2 = p[4]["idx"]

        pos_l1 = p[2]["pos"]
        pos_l2 = p[4]["pos"]

        if pos_l1 == pos_l2:
            continue

        slope = (
            l2 - l1
        ) / (
            pos_l2 - pos_l1
        )

        # --------------------------------------------------
        # SEARCH FOR THE FIRST VALID NECKLINE BREAK
        # --------------------------------------------------

        activation_pos = None

        start_pos = pos_h3 + 1

        end_pos = total_candles - 1

        for pos in range(
            start_pos,
            end_pos + 1
        ):

            # H3 must be recent when the signal activates
            if (
                pos - pos_h3
            ) > MAX_H3_AGE:
                break

            row = df.iloc[pos]

            neckline = (
                l2
                + slope * (pos - pos_l2)
            )

            close_price = float(
                row["Close"]
            )

            if close_price >= neckline:
                continue

            # Previous candle must still be
            # on/above the neckline.
            if pos > start_pos:

                prev_row = df.iloc[pos - 1]

                prev_neckline = (
                    l2
                    + slope * (
                        pos - 1 - pos_l2
                    )
                )

                if float(
                    prev_row["Close"]
                ) < prev_neckline:
                    continue

            rsi_val = float(
                row["RSI"]
            )

            ema50 = row["EMA50"]
            ema200 = row["EMA200"]

            if (
                pd.isna(ema50)
                or pd.isna(ema200)
            ):
                continue

            vol_val = row.get(
                "Volume", 0
            )

            vol_sma = row.get(
                "Volume_SMA", 0
            )

            vol_confirmed = (
                vol_sma == 0
                or vol_val >= vol_sma * 0.8
            )

            if not (
                30 <= rsi_val <= 75
            ):
                continue

            if not (
                ema50 > ema200
            ):
                continue

            if not vol_confirmed:
                continue

            activation_pos = pos
            break

        if activation_pos is None:
            continue

        activation_idx = df.index[
            activation_pos
        ]

        activation_row = df.iloc[
            activation_pos
        ]

        entry = float(
            activation_row["Close"]
        )

        activation_neckline = (
            l2
            + slope * (
                activation_pos - pos_l2
            )
        )

        sl = float(
            round(h2, 5)
        )

        shoulder_sl = float(
            round(max(h1, h3), 5)
        )

        actual_head_length = (
            h2 - activation_neckline
        )

        tp = float(
            round(
                entry - actual_head_length,
                5
            )
        )

        if tp <= 0:
            continue

        outcome = check_active_trade(
            df=df,
            activation_pos=activation_pos,
            entry=entry,
            sl=sl,
            tp=tp,
            bias="Bearish"
        )

        if outcome != "ACTIVE":
            continue

        nodes = [
            (x["idx"], x["val"])
            for x in p
        ]

        nodes.append(
            (
                activation_idx,
                entry
            )
        )

        neckline_nodes = [
            (p[2]["idx"], l1),
            (p[4]["idx"], l2)
        ]

        target_nodes = [
            (
                activation_idx,
                entry
            ),
            (
                activation_idx,
                tp
            )
        ]

        patterns.append({
            "name": "Head and Shoulders",
            "pattern": "Head and Shoulders",
            "bias": "Bearish",
            "match": 100.0,
            "nodes": nodes,
            "entry": float(
                round(entry, 5)
            ),
            "entry_trigger": float(
                round(entry, 5)
            ),
            "sl": sl,
            "shoulder_sl": shoulder_sl,
            "tp": tp,
            "neckline_start_idx": p[2]["idx"],
            "neckline_end_idx": activation_idx,
            "neckline_nodes": neckline_nodes,
            "target_nodes": target_nodes,
            "end_pos": p[5]["pos"],
            "activation_pos": activation_pos,
            "activation_idx": activation_idx,
            "status": "ACTIVE",
            "outcome": "ACTIVE",
            "candles_active": (
                total_candles - 1
                - activation_pos
            )
        })

    return patterns


# ==========================================================
# INVERSE HEAD & SHOULDERS
# ==========================================================

def detect_all_inverse_head_shoulders(
    pivots,
    df
):

    patterns = []

    if len(pivots) < 6:
        return patterns

    total_candles = len(df)

    for i in range(len(pivots) - 5):

        p = pivots[i:i + 6]

        if [
            x["type"] for x in p
        ] != [
            "H", "L", "H", "L", "H", "L"
        ]:
            continue

        pos_h0 = p[0]["pos"]
        pos_l3 = p[5]["pos"]

        if (
            pos_l3 - pos_h0
        ) > MAX_PATTERN_SPAN:
            continue

        h0, l1, h1, l2, h2, l3 = [
            x["val"] for x in p
        ]

        if l2 >= l1:
            continue

        if l2 >= l3:
            continue

        head_depth = (
            max(h1, h2) - l2
        )

        if head_depth <= 0:
            continue

        if abs(l1 - l3) > (
            head_depth * 0.20
        ):
            continue

        idx_h1 = p[2]["idx"]
        idx_h2 = p[4]["idx"]

        pos_h1 = p[2]["pos"]
        pos_h2 = p[4]["pos"]

        if pos_h1 == pos_h2:
            continue

        slope = (
            h2 - h1
        ) / (
            pos_h2 - pos_h1
        )

        # --------------------------------------------------
        # SEARCH FOR THE FIRST VALID NECKLINE BREAK
        # --------------------------------------------------

        activation_pos = None

        start_pos = pos_l3 + 1
        end_pos = total_candles - 1

        for pos in range(
            start_pos,
            end_pos + 1
        ):

            # L3 must be recent when the signal activates
            if (
                pos - pos_l3
            ) > MAX_H3_AGE:
                break

            row = df.iloc[pos]

            neckline = (
                h2
                + slope * (
                    pos - pos_h2
                )
            )

            close_price = float(
                row["Close"]
            )

            if close_price <= neckline:
                continue

            # Previous candle must still be
            # on/below the neckline.
            if pos > start_pos:

                prev_row = df.iloc[pos - 1]

                prev_neckline = (
                    h2
                    + slope * (
                        pos - 1 - pos_h2
                    )
                )

                if float(
                    prev_row["Close"]
                ) > prev_neckline:
                    continue

            rsi_val = float(
                row["RSI"]
            )

            ema50 = row["EMA50"]
            ema200 = row["EMA200"]

            if (
                pd.isna(ema50)
                or pd.isna(ema200)
            ):
                continue

            vol_val = row.get(
                "Volume", 0
            )

            vol_sma = row.get(
                "Volume_SMA", 0
            )

            vol_confirmed = (
                vol_sma == 0
                or vol_val >= vol_sma * 0.8
            )

            if not (
                25 <= rsi_val <= 70
            ):
                continue

            if not (
                ema50 < ema200
            ):
                continue

            if not vol_confirmed:
                continue

            activation_pos = pos
            break

        if activation_pos is None:
            continue

        activation_idx = df.index[
            activation_pos
        ]

        activation_row = df.iloc[
            activation_pos
        ]

        entry = float(
            activation_row["Close"]
        )

        activation_neckline = (
            h2
            + slope * (
                activation_pos - pos_h2
            )
        )

        sl = float(
            round(l2, 5)
        )

        shoulder_sl = float(
            round(min(l1, l3), 5)
        )

        actual_head_length = (
            activation_neckline - l2
        )

        tp = float(
            round(
                entry + actual_head_length,
                5
            )
        )

        if tp <= 0:
            continue

        outcome = check_active_trade(
            df=df,
            activation_pos=activation_pos,
            entry=entry,
            sl=sl,
            tp=tp,
            bias="Bullish"
        )

        if outcome != "ACTIVE":
            continue

        nodes = [
            (x["idx"], x["val"])
            for x in p
        ]

        nodes.append(
            (
                activation_idx,
                entry
            )
        )

        neckline_nodes = [
            (p[2]["idx"], h1),
            (p[4]["idx"], h2)
        ]

        target_nodes = [
            (
                activation_idx,
                entry
            ),
            (
                activation_idx,
                tp
            )
        ]

        patterns.append({
            "name": "Inverse Head and Shoulders",
            "pattern": "Inverse Head and Shoulders",
            "bias": "Bullish",
            "match": 100.0,
            "nodes": nodes,
            "entry": float(
                round(entry, 5)
            ),
            "entry_trigger": float(
                round(entry, 5)
            ),
            "sl": sl,
            "shoulder_sl": shoulder_sl,
            "tp": tp,
            "neckline_start_idx": p[2]["idx"],
            "neckline_end_idx": activation_idx,
            "neckline_nodes": neckline_nodes,
            "target_nodes": target_nodes,
            "end_pos": p[5]["pos"],
            "activation_pos": activation_pos,
            "activation_idx": activation_idx,
            "status": "ACTIVE",
            "outcome": "ACTIVE",
            "candles_active": (
                total_candles - 1
                - activation_pos
            )
        })

    return patterns


# ==========================================================
# COMBINED DETECTION
# ==========================================================

def _detect_both_head_shoulders(
    pivots,
    df
):

    normal_patterns = (
        detect_all_head_shoulders(
            pivots,
            df
        )
    )

    inverse_patterns = (
        detect_all_inverse_head_shoulders(
            pivots,
            df
        )
    )

    all_patterns = (
        normal_patterns
        + inverse_patterns
    )

    return sorted(
        all_patterns,
        key=lambda x: x.get(
            "activation_pos",
            -1
        )
    )


# ==========================================================
# MAIN ENGINE
# ==========================================================

def run_full_analysis(df):

    default_response = {
        "df": df,
        "signal": "WAITING",
        "pattern": "NO PATTERN DETECTED",
        "bias": "Neutral",
        "entry": None,
        "entry_trigger": None,
        "sl": None,
        "shoulder_sl": None,
        "tp": None,
        "nodes": [],
        "match": 0.0,
        "neckline_start_idx": None,
        "neckline_nodes": [],
        "target_nodes": [],
        "all_patterns": [],
    }

    if df is None or df.empty:
        return default_response

    df = df.copy()

    required = [
        "Open",
        "High",
        "Low",
        "Close"
    ]

    for col in required:

        if col not in df.columns:
            raise ValueError(
                f"Missing required column: {col}"
            )

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=required
    )

    if len(df) < 30:

        default_response["df"] = df

        return default_response

    # ----------------------------------
