import pandas as pd
import numpy as np

# ==========================================================
# SETTINGS
# ==========================================================
WAVE_TOLERANCE = 0.10  # التفاوت المسموح به بين الموجات هو 0.1 (10%)


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
    relative difference (10%).
    """
    if value_a == 0 or value_b == 0:
        return False

    return abs(value_a - value_b) / max(abs(value_a), abs(value_b)) <= tolerance


def equal_waves(wave_a_len, wave_b_len, tolerance=WAVE_TOLERANCE):
    """
    تأكيد تساوي أطوال الموجات الهيكلية الرئيسية ضمن التفاوت المسموح (0.1)
    """
    if wave_a_len <= 0 or wave_b_len <= 0:
        return False
    return abs(wave_a_len - wave_b_len) / max(wave_a_len, wave_b_len) <= tolerance


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


def get_strict_alternating_pivots(df):
    """
    تصفية النقاط المحورية وضمان التناوب الزمني الصارم (H -> L -> H -> L)
    """
    pivots_h = df['Pivot_H'].dropna()
    pivots_l = df['Pivot_L'].dropna()

    combined = []
    for idx, value in pivots_h.items():
        combined.append((idx, "H", value))
    for idx, value in pivots_l.items():
        combined.append((idx, "L", value))

    combined.sort(key=lambda x: x[0])

    filtered = []
    for p in combined:
        if not filtered:
            filtered.append(p)
        else:
            if p[1] != filtered[-1][1]:
                filtered.append(p)
            else:
                if p[1] == 'H' and p[2] > filtered[-1][2]:
                    filtered[-1] = p
                elif p[1] == 'L' and p[2] < filtered[-1][2]:
                    filtered[-1] = p

    return filtered


# ==========================================================
# 4. SCAN 15 CHART PATTERNS & STRUCTURAL LEVELS
# ==========================================================
def scan_15_patterns(df):
    """
    Strictly validate all 15 chart patterns using complete
    structural wave direction, strict chronological alternation, 
    and equal main wave heights within a 10% tolerance.
    """
    pivots = get_strict_alternating_pivots(df)

    if len(pivots) < 6:
        return (
            "NO PATTERN DETECTED",
            "Neutral",
            0.0,
            0.0,
            None,
            None
        )

    last_close = df['Close'].iloc[-1]

    # أحدث 6 نقاط متناوبة بصرامة لتأكيد هندسة النمط الكاملة
    p6, p5, p4, p3, p2, p1 = pivots[-6:]
    pattern_start = p6[0]
    pattern_end = p1[0]

    # ------------------------------------------------------
    # 1. DOUBLE BOTTOM (L1 -> H1 -> L2)
    # ------------------------------------------------------
    if p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
        l1, h1, l2 = p3[2], p2[2], p1[2]
        wave1 = abs(h1 - l1)
        wave2 = abs(h1 - l2)
        if within_tolerance(l1, l2) and equal_waves(wave1, wave2):
            return (
                "Double Bottom",
                "Bullish",
                h1,
                l2,
                p3[0],
                p1[0]
            )

    # ------------------------------------------------------
    # 2. DOUBLE TOP (H1 -> L1 -> H2)
    # ------------------------------------------------------
    if p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
        h1, l1, h2 = p3[2], p2[2], p1[2]
        wave1 = abs(h1 - l1)
        wave2 = abs(h2 - l1)
        if within_tolerance(h1, h2) and equal_waves(wave1, wave2):
            return (
                "Double Top",
                "Bearish",
                h2,
                l1,
                p3[0],
                p1[0]
            )

    # ------------------------------------------------------
    # 3. HEAD AND SHOULDERS (H1 -> L1 -> H2 -> L2 -> H3)
    # ------------------------------------------------------
    if p5[1] == 'H' and p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
        h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        wave_ls = abs(h1 - l1)
        wave_rs = abs(h3 - l2)
        if h2 > h1 and h2 > h3 and within_tolerance(h1, h3) and equal_waves(wave_ls, wave_rs):
            neckline = min(l1, l2)
            return (
                "Head and Shoulders",
                "Bearish",
                h2,
                neckline,
                p5[0],
                p1[0]
            )

    # ------------------------------------------------------
    # 4. INVERSE HEAD AND SHOULDERS (L1 -> H1 -> L2 -> H2 -> L3)
    # ------------------------------------------------------
    if p5[1] == 'L' and p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
        l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        wave_ls = abs(h1 - l1)
        wave_rs = abs(h2 - l3)
        if l2 < l1 and l2 < l3 and within_tolerance(l1, l3) and equal_waves(wave_ls, wave_rs):
            neckline = max(h1, h2)
            return (
                "Inverse Head and Shoulders",
                "Bullish",
                neckline,
                l2,
                p5[0],
                p1[0]
            )

    # ------------------------------------------------------
    # 5. TRIPLE BOTTOM (L1 -> H1 -> L2 -> H2 -> L3)
    # ------------------------------------------------------
    if p5[1] == 'L' and p3[1] == 'L' and p1[1] == 'L':
        l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        w1, w2, w3 = abs(h1 - l1), abs(h1 - l2), abs(h2 - l3)
        if within_tolerance(l1, l2) and within_tolerance(l2, l3) and equal_waves(w1, w2) and equal_waves(w2, w3):
            return (
                "Triple Bottom",
                "Bullish",
                max(h1, h2),
                l3,
                p5[0],
                p1[0]
            )

    # ------------------------------------------------------
    # 6. TRIPLE TOP (H1 -> L1 -> H2 -> L2 -> H3)
    # ------------------------------------------------------
    if p5[1] == 'H' and p3[1] == 'H' and p1[1] == 'H':
        h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        w1, w2, w3 = abs(h1 - l1), abs(h2 - l1), abs(h3 - l2)
        if within_tolerance(h1, h2) and within_tolerance(h2, h3) and equal_waves(w1, w2) and equal_waves(w2, w3):
            return (
                "Triple Top",
                "Bearish",
                h3,
                min(l1, l2),
                p5[0],
                p1[0]
            )

    if len(pivots) >= 4:
        p4, p3, p2, p1 = pivots[-4:]

        # --------------------------------------------------
        # 7. ASCENDING TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if within_tolerance(h1, h2) and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Ascending Triangle",
                    "Bullish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 8. DESCENDING TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if within_tolerance(l1, l2) and h2 < h1 and equal_waves(w1, w2):
                return (
                    "Descending Triangle",
                    "Bearish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 9. SYMMETRICAL TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Symmetrical Triangle",
                    "Neutral",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 10. RISING WEDGE
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 > h1 and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Rising Wedge",
                    "Bearish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 11. FALLING WEDGE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 < l1 and equal_waves(w1, w2):
                return (
                    "Falling Wedge",
                    "Bullish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 12. BULLISH FLAG
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 < l1 and equal_waves(w1, w2):
                return (
                    "Bullish Flag",
                    "Bullish",
                    h1,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 13. BEARISH FLAG
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 > h1 and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Bearish Flag",
                    "Bearish",
                    h2,
                    l1,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 14. BULLISH PENNANT
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Bullish Pennant",
                    "Bullish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

        # --------------------------------------------------
        # 15. BEARISH PENNANT
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return (
                    "Bearish Pennant",
                    "Bearish",
                    h2,
                    l2,
                    p4[0],
                    p1[0]
                )

    return (
        "NO PATTERN DETECTED",
        "Neutral",
        0.0,
        0.0,
        None,
        None
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
