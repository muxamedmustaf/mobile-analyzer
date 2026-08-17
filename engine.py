import pandas as pd
import numpy as np

# ==========================================================
# SETTINGS
# ==========================================================
WAVE_TOLERANCE = 0.15


# ==========================================================
# 1. CALCULATE INDICATORS (EMA 50, EMA 200, RSI 14)
# ==========================================================
def calculate_indicators(df):
    """
    Calculate EMA 50, EMA 200 and RSI 14.
    """
    df = df.copy()

    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df


# ==========================================================
# 2. PIVOT DETECTION (H = Resistance, L = Support)
# ==========================================================
def detect_pivots(df, window=3):
    """
    Detect structural highs and structural lows.
    """
    df = df.copy()

    df['Pivot_H'] = np.nan
    df['Pivot_L'] = np.nan

    for i in range(window, len(df) - window):

        high_range = df['High'].iloc[i - window:i + window + 1]
        low_range = df['Low'].iloc[i - window:i + window + 1]

        if df['High'].iloc[i] == high_range.max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]

        if df['Low'].iloc[i] == low_range.min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]

    return df


# ==========================================================
# 3. WAVE VALIDATION HELPERS
# ==========================================================
def within_tolerance(value_a, value_b, tolerance=WAVE_TOLERANCE):
    """
    Check whether two structural values are within the allowed
    relative difference.
    """
    if value_a == 0 or value_b == 0:
        return False

    return abs(value_a - value_b) / max(abs(value_a), abs(value_b)) <= tolerance


def higher(value_a, value_b):
    """
    Strictly higher.
    """
    return value_a > value_b


def lower(value_a, value_b):
    """
    Strictly lower.
    """
    return value_a < value_b


def meaningful_rise(start_value, end_value):
    """
    Confirm a real upward structural movement.
    """
    return end_value > start_value


def meaningful_fall(start_value, end_value):
    """
    Confirm a real downward structural movement.
    """
    return end_value < start_value


def valid_alternating_structure(high_points, low_points):
    """
    Confirm that structural highs and lows exist and alternate
    naturally in time.
    """
    if len(high_points) < 1 or len(low_points) < 1:
        return False

    combined = []

    for idx, value in high_points.items():
        combined.append((idx, "H", value))

    for idx, value in low_points.items():
        combined.append((idx, "L", value))

    combined.sort(key=lambda x: x[0])

    for i in range(1, len(combined)):
        if combined[i][1] == combined[i - 1][1]:
            return False

    return True


# ==========================================================
# 4. SCAN 15 CHART PATTERNS & STRUCTURAL LEVELS
# ==========================================================
def scan_15_patterns(df):
    """
    Strictly validate all 15 chart patterns using complete
    structural wave direction and a maximum 15% wave tolerance.
    """

    pivots_h = df['Pivot_H'].dropna()
    pivots_l = df['Pivot_L'].dropna()

    if len(pivots_h) < 3 or len(pivots_l) < 3:
        return (
            "NO PATTERN DETECTED",
            "Neutral",
            0.0,
            0.0,
            None,
            None
        )

    h1 = pivots_h.iloc[-3]
    h2 = pivots_h.iloc[-2]
    h3 = pivots_h.iloc[-1]

    l1 = pivots_l.iloc[-3]
    l2 = pivots_l.iloc[-2]
    l3 = pivots_l.iloc[-1]

    h1_idx = pivots_h.index[-3]
    h2_idx = pivots_h.index[-2]
    h3_idx = pivots_h.index[-1]

    l1_idx = pivots_l.index[-3]
    l2_idx = pivots_l.index[-2]
    l3_idx = pivots_l.index[-1]

    last_close = df['Close'].iloc[-1]

    pattern_start = min(h1_idx, l1_idx)
    pattern_end = max(h3_idx, l3_idx)

    # ------------------------------------------------------
    # 1. ASCENDING TRIANGLE
    # Flat resistance + strictly rising lows
    # ------------------------------------------------------
    ascending_triangle = (
        within_tolerance(h2, h3)
        and meaningful_rise(l1, l2)
        and meaningful_rise(l2, l3)
        and h3 >= h2
    )

    if ascending_triangle:
        return (
            "Ascending Triangle",
            "Bullish",
            h3,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 2. DESCENDING TRIANGLE
    # Flat support + strictly falling highs
    # ------------------------------------------------------
    descending_triangle = (
        within_tolerance(l2, l3)
        and meaningful_fall(h1, h2)
        and meaningful_fall(h2, h3)
        and l3 <= l2
    )

    if descending_triangle:
        return (
            "Descending Triangle",
            "Bearish",
            h3,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 3. SYMMETRICAL TRIANGLE
    # Falling highs + rising lows
    # ------------------------------------------------------
    symmetrical_triangle = (
        meaningful_fall(h1, h2)
        and meaningful_fall(h2, h3)
        and meaningful_rise(l1, l2)
        and meaningful_rise(l2, l3)
        and h3 < h1
        and l3 > l1
    )

    if symmetrical_triangle:
        return (
            "Symmetrical Triangle",
            "Neutral",
            h3,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 4. DOUBLE BOTTOM
    # First bottom -> reaction -> second bottom
    # ------------------------------------------------------
    double_bottom = (
        within_tolerance(l2, l3)
        and h2 > l1
        and h2 > l3
        and l2 < h2
        and l3 < h2
    )

    if double_bottom:
        return (
            "Double Bottom",
            "Bullish",
            h2,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 5. DOUBLE TOP
    # First top -> reaction -> second top
    # ------------------------------------------------------
    double_top = (
        within_tolerance(h2, h3)
        and l2 < h2
        and l2 < h3
        and h2 > l1
        and h3 > l2
    )

    if double_top:
        return (
            "Double Top",
            "Bearish",
            h3,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 6. HEAD AND SHOULDERS
    # Left shoulder -> head -> right shoulder
    # ------------------------------------------------------
    head_and_shoulders = (
        h2 > h1
        and h2 > h3
        and within_tolerance(h1, h3)
        and l2 < h1
        and l2 < h3
    )

    if head_and_shoulders:
        neckline = min(l1, l3)

        return (
            "Head and Shoulders",
            "Bearish",
            h2,
            neckline,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 7. INVERSE HEAD AND SHOULDERS
    # Left shoulder -> head -> right shoulder
    # ------------------------------------------------------
    inverse_head_and_shoulders = (
        l2 < l1
        and l2 < l3
        and within_tolerance(l1, l3)
        and h2 > l1
        and h2 > l3
    )

    if inverse_head_and_shoulders:
        neckline = max(h1, h3)

        return (
            "Inverse Head and Shoulders",
            "Bullish",
            neckline,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 8. BULLISH FLAG
    # Rising structural highs and lows followed by breakout
    # ------------------------------------------------------
    bullish_flag = (
        meaningful_rise(h1, h2)
        and meaningful_rise(l1, l2)
        and h2 > h1
        and l2 > l1
        and last_close > h2
    )

    if bullish_flag:
        return (
            "Bullish Flag",
            "Bullish",
            h2,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 9. BEARISH FLAG
    # Falling structural highs and lows followed by breakdown
    # ------------------------------------------------------
    bearish_flag = (
        meaningful_fall(h1, h2)
        and meaningful_fall(l1, l2)
        and h2 < h1
        and l2 < l1
        and last_close < l2
    )

    if bearish_flag:
        return (
            "Bearish Flag",
            "Bearish",
            h2,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 10. BULLISH PENNANT
    # Contracting highs + rising lows + bullish breakout
    # ------------------------------------------------------
    bullish_pennant = (
        meaningful_fall(h1, h2)
        and meaningful_rise(l1, l2)
        and h2 < h1
        and l2 > l1
        and last_close > h2
    )

    if bullish_pennant:
        return (
            "Bullish Pennant",
            "Bullish",
            h2,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 11. BEARISH PENNANT
    # Contracting highs + rising lows + bearish breakdown
    # ------------------------------------------------------
    bearish_pennant = (
        meaningful_fall(h1, h2)
        and meaningful_rise(l1, l2)
        and h2 < h1
        and l2 > l1
        and last_close < l2
    )

    if bearish_pennant:
        return (
            "Bearish Pennant",
            "Bearish",
            h2,
            l2,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 12. RISING WEDGE
    # Both sides rise, but highs rise less than lows
    # ------------------------------------------------------
    high_rise = h3 - h1
    low_rise = l3 - l1

    rising_wedge = (
        meaningful_rise(h1, h2)
        and meaningful_rise(h2, h3)
        and meaningful_rise(l1, l2)
        and meaningful_rise(l2, l3)
        and high_rise > 0
        and low_rise > 0
        and high_rise < low_rise
    )

    if rising_wedge:
        return (
            "Rising Wedge",
            "Bearish",
            h3,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 13. FALLING WEDGE
    # Both sides fall, but lows fall less than highs
    # ------------------------------------------------------
    high_fall = h1 - h3
    low_fall = l1 - l3

    falling_wedge = (
        meaningful_fall(h1, h2)
        and meaningful_fall(h2, h3)
        and meaningful_fall(l1, l2)
        and meaningful_fall(l2, l3)
        and high_fall > 0
        and low_fall > 0
        and high_fall < low_fall
    )

    if falling_wedge:
        return (
            "Falling Wedge",
            "Bullish",
            h3,
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 14. TRIPLE BOTTOM
    # Three structurally similar lows + reactions between them
    # ------------------------------------------------------
    triple_bottom = (
        within_tolerance(l1, l2)
        and within_tolerance(l2, l3)
        and h1 > l1
        and h2 > l2
        and h3 > l3
    )

    if triple_bottom:
        return (
            "Triple Bottom",
            "Bullish",
            max(h1, h2, h3),
            l3,
            pattern_start,
            pattern_end
        )

    # ------------------------------------------------------
    # 15. TRIPLE TOP
    # Three structurally similar highs + reactions between them
    # ------------------------------------------------------
    triple_top = (
        within_tolerance(h1, h2)
        and within_tolerance(h2, h3)
        and l1 < h1
        and l2 < h2
        and l3 < h3
    )

    if triple_top:
        return (
            "Triple Top",
            "Bearish",
            h3,
            min(l1, l2, l3),
            pattern_start,
            pattern_end
        )

    return (
        "NO PATTERN DETECTED",
        "Neutral",
        h3,
        l3,
        pattern_start,
        pattern_end
    )


# ==========================================================
# 5. STRICT 100% VERIFICATION ENGINE
# ==========================================================
def run_full_analysis(df):
    """
    Complete strict verification.

    A signal is accepted only when:
    1. A complete structural pattern is valid.
    2. The pattern direction is valid.
    3. Breakout or breakdown is confirmed.
    4. EMA trend conditions are confirmed.
    5. RSI is inside the required range.
    """

    df = calculate_indicators(df)
    df = detect_pivots(df)

    (
        pattern_name,
        bias,
        struct_h,
        struct_l,
        pattern_start,
        pattern_end
    ) = scan_15_patterns(df)

    latest = df.iloc[-1]

    close = latest['Close']
    ema50 = latest['EMA50']
    ema200 = latest['EMA200']
    rsi = latest['RSI']

    # ------------------------------------------------------
    # MANDATORY CONDITIONS
    # ------------------------------------------------------
    c_ema_bull = (
        close > ema200
        and ema50 > ema200
    )

    c_ema_bear = (
        close < ema200
        and ema50 < ema200
    )

    c_rsi = (
        30 <= rsi <= 70
    )

    c_breakout = (
        close > struct_h
    )

    c_breakdown = (
        close < struct_l
    )

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    # ------------------------------------------------------
    # STRICT BUY VERIFICATION
    # ------------------------------------------------------
    if bias in ["Bullish", "Bullish Reversal"]:

        if not c_breakout:
            rejected_reasons.append(
                f"Breakout Level Failed: Close ({close:.2f}) <= Resistance ({struct_h:.2f})"
            )

        if not c_ema_bull:
            rejected_reasons.append(
                f"EMA Trend Failed: Close ({close:.2f}) must be above EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be above EMA200"
            )

        if not c_rsi:
            rejected_reasons.append(
                f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-70"
            )

        if (
            c_breakout
            and c_ema_bull
            and c_rsi
        ):
            final_signal = "STRONG BUY"

    # ------------------------------------------------------
    # STRICT SELL VERIFICATION
    # ------------------------------------------------------
    elif bias in ["Bearish", "Bearish Reversal"]:

        if not c_breakdown:
            rejected_reasons.append(
                f"Breakdown Level Failed: Close ({close:.2f}) >= Support ({struct_l:.2f})"
            )

        if not c_ema_bear:
            rejected_reasons.append(
                f"EMA Trend Failed: Close ({close:.2f}) must be below EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be below EMA200"
            )

        if not c_rsi:
            rejected_reasons.append(
                f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-70"
            )

        if (
            c_breakdown
            and c_ema_bear
            and c_rsi
        ):
            final_signal = "STRONG SELL"

    else:
        rejected_reasons.append(
            "No valid strict structural pattern detected."
        )

    # ------------------------------------------------------
    # ABSOLUTE PRICE TARGETS
    # ------------------------------------------------------
    entry_price = round(close, 4)

    sl = "N/A"
    tp = "N/A"

    if final_signal == "STRONG BUY":

        sl_val = round(struct_l, 4)

        risk = entry_price - sl_val

        tp_val = round(
            entry_price + (risk * 2),
            4
        )

        sl = sl_val
        tp = tp_val

        status_msg = (
            f"100% Criteria Passed! "
            f"{pattern_name} confirmed with strict structure, "
            f"EMA, RSI ({rsi:.1f}), and breakout."
        )

    elif final_signal == "STRONG SELL":

        sl_val = round(struct_h, 4)

        risk = sl_val - entry_price

        tp_val = round(
            entry_price - (risk * 2),
            4
        )

        sl = sl_val
        tp = tp_val

        status_msg = (
            f"100% Criteria Passed! "
            f"{pattern_name} confirmed with strict structure, "
            f"EMA, RSI ({rsi:.1f}), and breakdown."
        )

    else:

        status_msg = (
            "REJECTED: "
            + " | ".join(rejected_reasons)
        )

    return {
        "df": df,
        "pattern": pattern_name,
        "bias": bias,
        "signal": final_signal,
        "reason": status_msg,
        "entry": entry_price,
        "sl": sl,
        "tp": tp,
        "close": entry_price,
        "ema50": round(ema50, 4),
        "ema200": round(ema200, 4),
        "rsi": round(rsi, 2),

        # Pattern drawing information
        "pattern_start": pattern_start,
        "pattern_end": pattern_end,

        # Structural levels
        "structural_high": struct_h,
        "structural_low": struct_l
        }
