import pandas as pd
import numpy as np

# ==========================================================
# SETTINGS
# ==========================================================
WAVE_TOLERANCE = 0.10  # التفاوت المسموح به بين الموجات هو 10%


# ==========================================================
# 1. CALCULATE INDICATORS (EMA 50, EMA 200, RSI 14)
# ==========================================================
def calculate_indicators(df):
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
# 2. PIVOT DETECTION & STRICT ALTERNATION
# ==========================================================
def detect_pivots(df, window=3):
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
# 3. WAVE VALIDATION HELPERS
# ==========================================================
def within_tolerance(value_a, value_b, tolerance=WAVE_TOLERANCE):
    if value_a == 0 or value_b == 0:
        return False
    return abs(value_a - value_b) / max(abs(value_a), abs(value_b)) <= tolerance


def equal_waves(wave_a_len, wave_b_len, tolerance=WAVE_TOLERANCE):
    if wave_a_len <= 0 or wave_b_len <= 0:
        return False
    return abs(wave_a_len - wave_b_len) / max(wave_a_len, wave_b_len) <= tolerance


# ==========================================================
# 4. ADVANCED SCAN 15 PATTERNS (DYNAMIC SLIDING WINDOW)
# ==========================================================
def scan_15_patterns(df):
    pivots = get_strict_alternating_pivots(df)

    if len(pivots) < 6:
        return ("NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None)

    last_close = df['Close'].iloc[-1]
    
    # البحث عبر نافذة متحركة في آخر 20 نقطة محورية بدلاً من إجبار النمط على أحدث 6 نقاط
    recent_pivots = pivots[-20:]

    # --- 1. HEAD AND SHOULDERS (H1 -> L1 -> H2 -> L2 -> H3) ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'H' and p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            wave_ls = abs(h1 - l1)
            wave_rs = abs(h3 - l2)
            # شرط بروز الرأس بنسبة 1.5% على الأقل لمنع التقاط التذبذب الأفقي
            if h2 > h1 * 1.015 and h2 > h3 * 1.015 and within_tolerance(h1, h3) and equal_waves(wave_ls, wave_rs):
                neckline = min(l1, l2)
                return ("Head and Shoulders", "Bearish", h2, neckline, p5[0], p1[0])

    # --- 2. INVERSE HEAD AND SHOULDERS (L1 -> H1 -> L2 -> H2 -> L3) ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'L' and p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            wave_ls = abs(h1 - l1)
            wave_rs = abs(h2 - l3)
            if l2 < l1 * 0.985 and l2 < l3 * 0.985 and within_tolerance(l1, l3) and equal_waves(wave_ls, wave_rs):
                neckline = max(h1, h2)
                return ("Inverse Head and Shoulders", "Bullish", neckline, l2, p5[0], p1[0])

    # --- 3. TRIPLE BOTTOM ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'L' and p3[1] == 'L' and p1[1] == 'L':
            l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            w1, w2, w3 = abs(h1 - l1), abs(h1 - l2), abs(h2 - l3)
            if within_tolerance(l1, l2) and within_tolerance(l2, l3) and equal_waves(w1, w2) and equal_waves(w2, w3):
                return ("Triple Bottom", "Bullish", max(h1, h2), l3, p5[0], p1[0])

    # --- 4. TRIPLE TOP ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'H' and p3[1] == 'H' and p1[1] == 'H':
            h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            w1, w2, w3 = abs(h1 - l1), abs(h2 - l1), abs(h3 - l2)
            if within_tolerance(h1, h2) and within_tolerance(h2, h3) and equal_waves(w1, w2) and equal_waves(w2, w3):
                return ("Triple Top", "Bearish", h3, min(l1, l2), p5[0], p1[0])

    # --- 5. DOUBLE BOTTOM ---
    for i in range(len(recent_pivots) - 2):
        p3, p2, p1 = recent_pivots[i:i+3]
        if p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            l1, h1, l2 = p3[2], p2[2], p1[2]
            wave1, wave2 = abs(h1 - l1), abs(h1 - l2)
            if within_tolerance(l1, l2) and equal_waves(wave1, wave2):
                return ("Double Bottom", "Bullish", h1, l2, p3[0], p1[0])

    # --- 6. DOUBLE TOP ---
    for i in range(len(recent_pivots) - 2):
        p3, p2, p1 = recent_pivots[i:i+3]
        if p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            h1, l1, h2 = p3[2], p2[2], p1[2]
            wave1, wave2 = abs(h1 - l1), abs(h2 - l1)
            if within_tolerance(h1, h2) and equal_waves(wave1, wave2):
                return ("Double Top", "Bearish", h2, l1, p3[0], p1[0])

    # --- ANATOMY OF 4-PIVOT PATTERNS ---
    for i in range(len(recent_pivots) - 3):
        p4, p3, p2, p1 = recent_pivots[i:i+4]
        
        # Ascending Triangle
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if within_tolerance(h1, h2) and l2 > l1 and equal_waves(w1, w2):
                return ("Ascending Triangle", "Bullish", h2, l2, p4[0], p1[0])

        # Descending Triangle
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if within_tolerance(l1, l2) and h2 < h1 and equal_waves(w1, w2):
                return ("Descending Triangle", "Bearish", h2, l2, p4[0], p1[0])

        # Symmetrical Triangle
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return ("Symmetrical Triangle", "Neutral", h2, l2, p4[0], p1[0])

        # Rising Wedge
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 > h1 and l2 > l1 and equal_waves(w1, w2):
                return ("Rising Wedge", "Bearish", h2, l2, p4[0], p1[0])

        # Falling Wedge
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 < l1 and equal_waves(w1, w2):
                return ("Falling Wedge", "Bullish", h2, l2, p4[0], p1[0])

        # Bullish Flag
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 < l1 and equal_waves(w1, w2):
                return ("Bullish Flag", "Bullish", h1, l2, p4[0], p1[0])

        # Bearish Flag
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 > h1 and l2 > l1 and equal_waves(w1, w2):
                return ("Bearish Flag", "Bearish", h2, l1, p4[0], p1[0])

        # Bullish Pennant
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return ("Bullish Pennant", "Bullish", h2, l2, p4[0], p1[0])

        # Bearish Pennant
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            w1, w2 = abs(h1 - l1), abs(h2 - l2)
            if h2 < h1 and l2 > l1 and equal_waves(w1, w2):
                return ("Bearish Pennant", "Bearish", h2, l2, p4[0], p1[0])

    return ("NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None)


# ==========================================================
# 5. STRICT 100% VERIFICATION ENGINE
# ==========================================================
def run_full_analysis(df):
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

    c_ema_bull = close > ema200 and ema50 > ema200
    c_ema_bear = close < ema200 and ema50 < ema200
    c_rsi = 30 <= rsi <= 70
    c_breakout = close > struct_h
    c_breakdown = close < struct_l

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Level Failed: Close ({close:.2f}) <= Resistance ({struct_h:.2f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.2f}) must be above EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be above EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-70")

        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Level Failed: Close ({close:.2f}) >= Support ({struct_l:.2f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.2f}) must be below EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be below EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-70")

        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("No valid strict structural pattern detected.")

    entry_price = round(close, 4)
    sl = "N/A"
    tp = "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        tp_val = round(entry_price + (risk * 2), 4)
        sl, tp = sl_val, tp_val
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with strict structure, EMA, RSI ({rsi:.1f}), and breakout."

    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        tp_val = round(entry_price - (risk * 2), 4)
        sl, tp = sl_val, tp_val
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with strict structure, EMA, RSI ({rsi:.1f}), and breakdown."

    else:
        status_msg = "REJECTED: " + " | ".join(rejected_reasons)

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
        "pattern_start": pattern_start,
        "pattern_end": pattern_end,
        "structural_high": struct_h,
        "structural_low": struct_l
            }
        
