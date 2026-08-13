import pandas as pd
import numpy as np

# ==========================================================
# 1. CALCULATE INDICATORS (EMA 50, EMA 200, RSI 14)
# ==========================================================
def calculate_indicators(df):
    """
    Xisaabinta EMA 50, EMA 200 iyo RSI (14)
    """
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # RSI (14 Period)
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
    Ogaanshada Structural Highs (H) iyo Structural Lows (L)
    """
    df['Pivot_H'] = np.nan
    df['Pivot_L'] = np.nan

    for i in range(window, len(df) - window):
        high_range = df['High'].iloc[i - window : i + window + 1]
        low_range = df['Low'].iloc[i - window : i + window + 1]

        if df['High'].iloc[i] == high_range.max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]

        if df['Low'].iloc[i] == low_range.min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]

    return df

# ==========================================================
# 3. SCAN 15 CHART PATTERNS & STRUCTURAL LEVELS
# ==========================================================
def scan_15_patterns(df):
    """
    Siftaynta 15-ka Pattern iyo soo nicleynta H3 iyo L3 ee Breakout/Breakdown
    """
    pivots_h = df['Pivot_H'].dropna()
    pivots_l = df['Pivot_L'].dropna()

    if len(pivots_h) < 3 or len(pivots_l) < 3:
        return "NO PATTERN DETECTED", "Neutral", 0.0, 0.0

    h1, h2, h3 = pivots_h.iloc[-3], pivots_h.iloc[-2], pivots_h.iloc[-1]
    l1, l2, l3 = pivots_l.iloc[-3], pivots_l.iloc[-2], pivots_l.iloc[-1]

    tol = 0.0025  # 0.25% tolerance
    last_close = df['Close'].iloc[-1]

    # 1. Ascending Triangle (Flat Resistance, Rising Lows)
    if abs(h2 - h3) / h2 <= tol and l3 > l2 > l1:
        return "Ascending Triangle", "Bullish", h3, l3

    # 2. Descending Triangle (Flat Support, Falling Highs)
    if abs(l2 - l3) / l2 <= tol and h3 < h2 < h1:
        return "Descending Triangle", "Bearish", h3, l3

    # 3. Symmetrical Triangle
    if h3 < h2 < h1 and l3 > l2 > l1:
        return "Symmetrical Triangle", "Neutral", h3, l3

    # 4. Double Bottom (W Pattern)
    if abs(l2 - l3) / l2 <= tol and h3 > l3:
        return "Double Bottom", "Bullish", h3, l3

    # 5. Double Top (M Pattern)
    if abs(h2 - h3) / h2 <= tol and l3 < h3:
        return "Double Top", "Bearish", h3, l3

    # 6. Head and Shoulders
    if h2 > h1 and h2 > h3 and abs(h1 - h3) / h1 <= 0.01:
        return "Head and Shoulders", "Bearish", h2, l3

    # 7. Inverse Head and Shoulders
    if l2 < l1 and l2 < l3 and abs(l1 - l3) / l1 <= 0.01:
        return "Inverse Head and Shoulders", "Bullish", h3, l2

    # 8. Bullish Flag
    if h1 < h2 and l1 < l2 and last_close > h1:
        return "Bullish Flag", "Bullish", h2, l2

    # 9. Bearish Flag
    if h1 > h2 and l1 > l2 and last_close < l1:
        return "Bearish Flag", "Bearish", h2, l2

    # 10. Bullish Pennant
    if h2 < h1 and l2 > l1 and last_close > h2:
        return "Bullish Pennant", "Bullish", h2, l2

    # 11. Bearish Pennant
    if h2 < h1 and l2 > l1 and last_close < l2:
        return "Bearish Pennant", "Bearish", h2, l2

    # 12. Rising Wedge
    if h3 > h2 > h1 and l3 > l2 > l1 and (h3 - h1) < (l3 - l1):
        return "Rising Wedge", "Bearish", h3, l3

    # 13. Falling Wedge
    if h3 < h2 < h1 and l3 < l2 < l1 and (h1 - h3) < (l1 - l3):
        return "Falling Wedge", "Bullish", h3, l3

    # 14. Triple Bottom
    if abs(l1 - l2) / l1 <= tol and abs(l2 - l3) / l2 <= tol:
        return "Triple Bottom", "Bullish", h3, l3

    # 15. Triple Top
    if abs(h1 - h2) / h1 <= tol and abs(h2 - h3) / h2 <= tol:
        return "Triple Top", "Bearish", h3, l3

    return "NO PATTERN DETECTED", "Neutral", h3, l3

# ==========================================================
# 4. STRICT 100% VERIFICATION ENGINE
# ==========================================================
def run_full_analysis(df):
    """
    Dhamaan 4-ta shardi waa in ay 100% buuxsamaan si Signal uu u soo baxo:
    1. Pattern Valid Bias (Bullish ama Bearish)
    2. Price Breakout / Breakdown (> Structural High ama < Structural Low)
    3. EMA Filter (Close > EMA200 & EMA50 > EMA200 ee BUY | Close < EMA200 & EMA50 < EMA200 ee SELL)
    4. RSI Filter (30 <= RSI <= 70)
    """
    df = calculate_indicators(df)
    df = detect_pivots(df)

    pattern_name, bias, struct_h, struct_l = scan_15_patterns(df)

    latest = df.iloc[-1]
    close = latest['Close']
    ema50 = latest['EMA50']
    ema200 = latest['EMA200']
    rsi = latest['RSI']

    # Shuruudaha Xaqiijinta (Mandatory Check Flags)
    c_ema_bull = (close > ema200) and (ema50 > ema200)
    c_ema_bear = (close < ema200) and (ema50 < ema200)
    c_rsi = (30 <= rsi <= 70)

    c_breakout = close > struct_h
    c_breakdown = close < struct_l

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    # ------------------------------------------------------
    # STRICT BUY VERIFICATION
    # ------------------------------------------------------
    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Level Failed: Close ({close:.2f}) <= Resistance ({struct_h:.2f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Must have Close > EMA200 ({ema200:.2f}) & EMA50 > EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is out of 30-70 range")

        # 100% STRICT MANDATORY PASS CONDITION
        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    # ------------------------------------------------------
    # STRICT SELL VERIFICATION
    # ------------------------------------------------------
    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Level Failed: Close ({close:.2f}) >= Support ({struct_l:.2f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Must have Close < EMA200 ({ema200:.2f}) & EMA50 < EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is out of 30-70 range")

        # 100% STRICT MANDATORY PASS CONDITION
        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"

    else:
        rejected_reasons.append("No valid 15-chart pattern detected on market structure.")

    # ------------------------------------------------------
    # ABSOLUTE PRICE TARGETS (ENTRY, SL, TP)
    # ------------------------------------------------------
    entry_price = round(close, 4)
    sl = "N/A"
    tp = "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        tp_val = round(entry_price + (risk * 2), 4)  # 1:2 Risk-to-Reward
        sl = sl_val
        tp = tp_val
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with EMA, RSI ({rsi:.1f}), and Breakout."

    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        tp_val = round(entry_price - (risk * 2), 4)  # 1:2 Risk-to-Reward
        sl = sl_val
        tp = tp_val
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with EMA, RSI ({rsi:.1f}), and Breakdown."

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
        "rsi": round(rsi, 2)
    }
    
