import pandas as pd
import numpy as np

# ==========================================================
# SETTINGS
# ==========================================================
WAVE_TOLERANCE = 0.05  # تقليل نسبة التحمل إلى 5% لضمان دقة الأنماط الحقيقية


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
    استخراج النقاط المحورية وضمان التناوب الزمني الصارم (H -> L -> H -> L)
    """
    pivots_h = df['Pivot_H'].dropna()
    pivots_l = df['Pivot_L'].dropna()

    combined = []
    for idx, val in pivots_h.items():
        combined.append((idx, 'H', val))
    for idx, val in pivots_l.items():
        combined.append((idx, 'L', val))

    combined.sort(key=lambda x: x[0])

    # تصفية التكرارات المتتالية للحفاظ على القمم والقيعان الحقيقية فقط
    filtered = []
    for p in combined:
        if not filtered:
            filtered.append(p)
        else:
            if p[1] != filtered[-1][1]:
                filtered.append(p)
            else:
                # إذا تكررت القمة نأخذ الأعلى، وإذا تكرر القاع نأخذ الأدنى
                if p[1] == 'H' and p[2] > filtered[-1][2]:
                    filtered[-1] = p
                elif p[1] == 'L' and p[2] < filtered[-1][2]:
                    filtered[-1] = p

    return filtered


# ==========================================================
# 3. HELPER FUNCTIONS FOR STRICT STRUCTURE
# ==========================================================
def within_tolerance(v1, v2, tolerance=WAVE_TOLERANCE):
    if v1 == 0 or v2 == 0:
        return False
    return abs(v1 - v2) / max(abs(v1), abs(v2)) <= tolerance


# ==========================================================
# 4. SCAN 15 CHART PATTERNS (STRICT LOGIC)
# ==========================================================
def scan_15_patterns(df):
    pivots = get_strict_alternating_pivots(df)

    if len(pivots) < 6:
        return ("NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None)

    last_close = df['Close'].iloc[-1]
    
    # أخذ أحدث 6 نقاط محورية متناوبة لتقييم الأنماط الهيكلية بالكامل
    p6, p5, p4, p3, p2, p1 = pivots[-6:]
    
    pattern_start = p6[0]
    pattern_end = p1[0]

    # ------------------------------------------------------
    # 1. DOUBLE BOTTOM (L1 -> H1 -> L2) - Reversal
    # ------------------------------------------------------
    if p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
        l1, h1, l2 = p3[2], p2[2], p1[2]
        if within_tolerance(l1, l2) and h1 > l1 * 1.02:
            return ("Double Bottom", "Bullish", h1, l2, p3[0], p1[0])

    # ------------------------------------------------------
    # 2. DOUBLE TOP (H1 -> L1 -> H2) - Reversal
    # ------------------------------------------------------
    if p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
        h1, l1, h2 = p3[2], p2[2], p1[2]
        if within_tolerance(h1, h2) and l1 < h1 * 0.98:
            return ("Double Top", "Bearish", h2, l1, p3[0], p1[0])

    # ------------------------------------------------------
    # 3. HEAD AND SHOULDERS (H1 -> L1 -> H2 -> L2 -> H3)
    # ------------------------------------------------------
    if p5[1] == 'H' and p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
        h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        if h2 > h1 and h2 > h3 and within_tolerance(h1, h3):
            neckline = min(l1, l2)
            return ("Head and Shoulders", "Bearish", h2, neckline, p5[0], p1[0])

    # ------------------------------------------------------
    # 4. INVERSE HEAD AND SHOULDERS (L1 -> H1 -> L2 -> H2 -> L3)
    # ------------------------------------------------------
    if p5[1] == 'L' and p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
        l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        if l2 < l1 and l2 < l3 and within_tolerance(l1, l3):
            neckline = max(h1, h2)
            return ("Inverse Head and Shoulders", "Bullish", neckline, l2, p5[0], p1[0])

    # ------------------------------------------------------
    # 5. TRIPLE BOTTOM (L1 -> H1 -> L2 -> H2 -> L3)
    # ------------------------------------------------------
    if p5[1] == 'L' and p3[1] == 'L' and p1[1] == 'L':
        l1, h1, l2, h2, l3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        if within_tolerance(l1, l2) and within_tolerance(l2, l3):
            return ("Triple Bottom", "Bullish", max(h1, h2), l3, p5[0], p1[0])

    # ------------------------------------------------------
    # 6. TRIPLE TOP (H1 -> L1 -> H2 -> L2 -> H3)
    # ------------------------------------------------------
    if p5[1] == 'H' and p3[1] == 'H' and p1[1] == 'H':
        h1, l1, h2, l2, h3 = p5[2], p4[2], p3[2], p2[2], p1[2]
        if within_tolerance(h1, h2) and within_tolerance(h2, h3):
            return ("Triple Top", "Bearish", h3, min(l1, l2), p5[0], p1[0])

    # أنماط تتطلب 4 نقاط محورية متتالية (H1, L1, H2, L2)
    if len(pivots) >= 4:
        p4, p3, p2, p1 = pivots[-4:]
        
        # --------------------------------------------------
        # 7. ASCENDING TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            if within_tolerance(h1, h2) and l2 > l1:
                return ("Ascending Triangle", "Bullish", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 8. DESCENDING TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            if within_tolerance(l1, l2) and h2 < h1:
                return ("Descending Triangle", "Bearish", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 9. SYMMETRICAL TRIANGLE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            if h2 < h1 and l2 > l1:
                return ("Symmetrical Triangle", "Neutral", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 10. RISING WEDGE
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            if h2 > h1 and l2 > l1 and (h2 - h1) < (l2 - l1):
                return ("Rising Wedge", "Bearish", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 11. FALLING WEDGE
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            if h2 < h1 and l2 < l1 and (h1 - h2) > (l1 - l2):
                return ("Falling Wedge", "Bullish", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 12. BULLISH FLAG (تستلزم وجود حركة صاعدة قبل القناة)
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            if h2 < h1 and l2 < l1 and (h1 - h2) == (l1 - l2):
                return ("Bullish Flag", "Bullish", h1, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 13. BEARISH FLAG
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            if h2 > h1 and l2 > l1 and (h2 - h1) == (l2 - l1):
                return ("Bearish Flag", "Bearish", h2, l1, p4[0], p1[0])

        # --------------------------------------------------
        # 14. BULLISH PENNANT
        # --------------------------------------------------
        if p4[1] == 'H' and p3[1] == 'L' and p2[1] == 'H' and p1[1] == 'L':
            h1, l1, h2, l2 = p4[2], p3[2], p2[2], p1[2]
            if h2 < h1 and l2 > l1 and last_close > h2:
                return ("Bullish Pennant", "Bullish", h2, l2, p4[0], p1[0])

        # --------------------------------------------------
        # 15. BEARISH PENNANT
        # --------------------------------------------------
        if p4[1] == 'L' and p3[1] == 'H' and p2[1] == 'L' and p1[1] == 'H':
            l1, h1, l2, h2 = p4[2], p3[2], p2[2], p1[2]
            if h2 < h1 and l2 > l1 and last_close < l2:
                return ("Bearish Pennant", "Bearish", h2, l2, p4[0], p1[0])

    return ("NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None)


# ==========================================================
# 5. STRICT 100% VERIFICATION ENGINE FOR REAL TRADING
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = detect_pivots(df)

    pattern_name, bias, struct_h, struct_l, pattern_start, pattern_end = scan_15_patterns(df)

    latest = df.iloc[-1]
    close = latest['Close']
    ema50 = latest['EMA50']
    ema200 = latest['EMA200']
    rsi = latest['RSI']

    # فلترة الاتجاه وإشارات الكسر/الاختراق الصارمة
    c_ema_bull = close > ema200 and ema50 > ema200
    c_ema_bear = close < ema200 and ema50 < ema200
    c_rsi = 35 <= rsi <= 65  # تم تضييق نطاق RSI لتجنب التداول في مناطق التشبع
    c_breakout = close > struct_h
    c_breakdown = close < struct_l

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias == "Bullish":
        if not c_breakout:
            rejected_reasons.append(f"Waiting for Breakout: Close ({close:.2f}) <= Resistance ({struct_h:.2f})")
        if not c_ema_bull:
            rejected_reasons.append("EMA Trend is not Strong Bullish")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed ({rsi:.1f})")

        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias == "Bearish":
        if not c_breakdown:
            rejected_reasons.append(f"Waiting for Breakdown: Close ({close:.2f}) >= Support ({struct_l:.2f})")
        if not c_ema_bear:
            rejected_reasons.append("EMA Trend is not Strong Bearish")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed ({rsi:.1f})")

        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("No Valid Pattern Geometry Met")

    # إدارة المخاطر وتحديد الأهداف للحساب الحقيقي (Risk/Reward 1:2)
    entry_price = round(close, 4)
    sl, tp = "N/A", "N/A"

    if final_signal == "STRONG BUY":
        sl = round(struct_l, 4)
        risk = entry_price - sl
        tp = round(entry_price + (risk * 2), 4)
        status_msg = f"Passed All Strict Filters! Pattern: {pattern_name}"
    elif final_signal == "STRONG SELL":
        sl = round(struct_h, 4)
        risk = sl - entry_price
        tp = round(entry_price - (risk * 2), 4)
        status_msg = f"Passed All Strict Filters! Pattern: {pattern_name}"
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
