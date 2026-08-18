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
# 2. ZIGZAG INDICATOR (DEFAULT: 12, 5, 3)
# ==========================================================
def calculate_zigzag(df, depth=12, deviation=5, backstep=3):
    """
    حساب مؤشر الزجزاج بناءً على الإعدادات الافتراضية (12, 5, 3)
    """
    df = df.copy()
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    zigzag_val = [np.nan] * n
    zigzag_type = [None] * n  # 'H' for High, 'L' for Low

    stat = 0  # 0: seeking, 1: peak, -1: valley
    last_high_idx = -1
    last_low_idx = -1
    last_high_val = 0.0
    last_low_val = 0.0

    dev_threshold = deviation / 100.0  # تحويل الانحراف إلى نسبة مئوية

    for i in range(depth, n):
        # البحث عن القمة والقاع في فترة depth
        window_highs = highs[i - depth + 1 : i + 1]
        window_lows = lows[i - depth + 1 : i + 1]

        max_idx = i - depth + 1 + np.argmax(window_highs)
        min_idx = i - depth + 1 + np.argmin(window_lows)

        current_high = highs[max_idx]
        current_low = lows[min_idx]

        if stat == 0:
            if current_high >= highs[i] and max_idx == i:
                stat = 1
                last_high_idx = i
                last_high_val = highs[i]
                zigzag_val[i] = highs[i]
                zigzag_type[i] = 'H'
            elif current_low <= lows[i] and min_idx == i:
                stat = -1
                last_low_idx = i
                last_low_val = lows[i]
                zigzag_val[i] = lows[i]
                zigzag_type[i] = 'L'

        elif stat == 1:  # البحث عن قاع جديد أو تحديث القمة الأعلى
            if max_idx == i and highs[i] > last_high_val:
                zigzag_val[last_high_idx] = np.nan
                zigzag_type[last_high_idx] = None
                last_high_idx = i
                last_high_val = highs[i]
                zigzag_val[i] = highs[i]
                zigzag_type[i] = 'H'

            elif min_idx == i and (last_high_val - lows[i]) / last_high_val >= dev_threshold:
                if (i - last_high_idx) >= backstep:
                    stat = -1
                    last_low_idx = i
                    last_low_val = lows[i]
                    zigzag_val[i] = lows[i]
                    zigzag_type[i] = 'L'

        elif stat == -1:  # البحث عن قمة جديدة أو تحديث القاع الأدنى
            if min_idx == i and lows[i] < last_low_val:
                zigzag_val[last_low_idx] = np.nan
                zigzag_type[last_low_idx] = None
                last_low_idx = i
                last_low_val = lows[i]
                zigzag_val[i] = lows[i]
                zigzag_type[i] = 'L'

            elif max_idx == i and (highs[i] - last_low_val) / last_low_val >= dev_threshold:
                if (i - last_low_idx) >= backstep:
                    stat = 1
                    last_high_idx = i
                    last_high_val = highs[i]
                    zigzag_val[i] = highs[i]
                    zigzag_type[i] = 'H'

    df['ZigZag_Val'] = zigzag_val
    df['ZigZag_Type'] = zigzag_type
    return df


def get_zigzag_pivots(df):
    """
    استخراج النقاط المحورية المؤكدة الصادرة من مؤشر الزجزاج فقط
    """
    pivots = []
    zigzag_df = df.dropna(subset=['ZigZag_Val'])

    for idx, row in zigzag_df.iterrows():
        pivots.append((idx, row['ZigZag_Type'], row['ZigZag_Val']))

    return pivots


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
# 4. SCAN 15 CHART PATTERNS USING ZIGZAG WAVES
# ==========================================================
def scan_15_patterns(df):
    pivots = get_zigzag_pivots(df)

    if len(pivots) < 6:
        return ("NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None)

    # الاعتماد على نقاط الزجزاج المحسوبة
    recent_pivots = pivots[-20:]

    # --- 1. HEAD AND SHOULDERS ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'H' and p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            wave_ls = abs(h1 - l1)
            wave_rs = abs(h3 - l2)
            if h2 > h1 and h2 > h3 and within_tolerance(h1, h3) and equal_waves(wave_ls, wave_rs):
                neckline = min(l1, l2)
                return ("Head and Shoulders", "Bearish", h2, neckline, p5[0], p1[0])

    # --- 2. INVERSE HEAD AND SHOULDERS ---
    for i in range(len(recent_pivots) - 4):
        p5, p4, p3, p2, p1 = recent_pivots[i:i+5]
        if p5[1] == 'L' and p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
            wave_ls = abs(h1 - l1)
            wave_rs = abs(h2 - l3)
            if l2 < l1 and l2 < l3 and within_tolerance(l1, l3) and equal_waves(wave_ls, wave_rs):
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

    # --- 4-PIVOT PATTERNS ---
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
            w1, w2 = abs(h1 - l1), abs(h2 - l1)
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
            w1, w2 = abs(h1 - l1), abs(h2 - l1)
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
# 5. STRICT 100% VERIFICATION ENGINE (UNCHANGED SIGNALS)
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)

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

    # الإبقاء الكامل على شروط الإشارات الخاصة بك دون أي تغيير
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
                
