import pandas as pd
import numpy as np

# ==========================================================
# 1. CALCULATE INDICATORS
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    return df

# ==========================================================
# 2. PIVOT DETECTION
# ==========================================================
def detect_pivots(df, window=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    for i in range(window, len(df) - window):
        if df['High'].iloc[i] == df['High'].iloc[i - window:i + window + 1].max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]
        if df['Low'].iloc[i] == df['Low'].iloc[i - window:i + window + 1].min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]
    return df

def eq(a, b, tol=0.05): 
    return abs(a - b) / max(abs(a), abs(b)) <= tol if max(abs(a), abs(b)) > 0 else False

# ==========================================================
# 3. STRICT SCANNER FOR ALL 15 PATTERNS
# ==========================================================
def scan_15_patterns(df):
    ph, pl = df['Pivot_H'].dropna(), df['Pivot_L'].dropna()
    if len(ph) < 3 or len(pl) < 3:
        return "NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None

    h1, h2, h3 = ph.iloc[-3], ph.iloc[-2], ph.iloc[-1]
    l1, l2, l3 = pl.iloc[-3], pl.iloc[-2], pl.iloc[-1]
    p_start, p_end = min(ph.index[-3], pl.index[-3]), max(ph.index[-1], pl.index[-1])
    close = df['Close'].iloc[-1]

    # --- ALL 15 PATTERNS WITH PRIOR TREND FILTERS ---
    if h1 < h2 and eq(h2, h3) and l1 < l2 < l3:
        return "Ascending Triangle", "Bullish", h3, l3, p_start, p_end
    if l1 > l2 and eq(l2, l3) and h1 > h2 > h3:
        return "Descending Triangle", "Bearish", h3, l3, p_start, p_end
    if h1 > h2 > h3 and l1 < l2 < l3:
        return "Symmetrical Triangle", "Neutral", h3, l3, p_start, p_end
    if h1 > h2 and eq(l2, l3) and h2 > l2 and h2 > l3:
        return "Double Bottom", "Bullish", h2, l3, p_start, p_end
    if l1 < l2 and eq(h2, h3) and l2 < h2 and l2 < h3:
        return "Double Top", "Bearish", h3, l2, p_start, p_end
    if df['Close'].loc[ph.index[-3]] > df['EMA200'].loc[ph.index[-3]] and h2 >= h1 * 1.40 and l1 >= h1 * 0.70 and eq(l1, l2, 0.10) and eq(h1, h3, 0.05):
        return "Head and Shoulders", "Bearish", h2, min(l1, l2), p_start, p_end
    if df['Close'].loc[pl.index[-3]] < df['EMA200'].loc[pl.index[-3]] and l2 <= l1 * 0.60 and h1 <= l1 * 1.30 and eq(h1, h2, 0.10) and eq(l1, l3, 0.05):
        return "Inverse Head and Shoulders", "Bullish", max(h1, h2), l2, p_start, p_end
    if l1 < l2 and h1 < h2 and close > h2:
        return "Bullish Flag", "Bullish", h2, l2, p_start, p_end
    if h1 > h2 and l1 > l2 and close < l2:
        return "Bearish Flag", "Bearish", h2, l2, p_start, p_end
    if l1 < l2 and h1 > h2 and close > h2:
        return "Bullish Pennant", "Bullish", h2, l2, p_start, p_end
    if h1 > h2 and l1 > l2 and close < l2:
        return "Bearish Pennant", "Bearish", h2, l2, p_start, p_end
    if h1 < h2 < h3 and l1 < l2 < l3 and (h3 - h1) < (l3 - l1):
        return "Rising Wedge", "Bearish", h3, l3, p_start, p_end
    if h1 > h2 > h3 and l1 > l2 > l3 and (h1 - h3) > (l1 - l3):
        return "Falling Wedge", "Bullish", h3, l3, p_start, p_end
    if h1 > h2 and eq(l1, l2) and eq(l2, l3) and h1 > l1 and h2 > l2:
        return "Triple Bottom", "Bullish", max(h1, h2, h3), l3, p_start, p_end
    if l1 < l2 and eq(h1, h2) and eq(h2, h3) and l1 < h1 and l2 < h2:
        return "Triple Top", "Bearish", h3, min(l1, l2, l3), p_start, p_end

    return "NO PATTERN DETECTED", "Neutral", h3, l3, p_start, p_end

# ==========================================================
# 4. FULL ANALYSIS ENGINE (100% COMPATIBLE STRUCTURE)
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

    c_ema_bull = (close > ema200) and (ema50 > ema200)
    c_ema_bear = (close < ema200) and (close < ema50)
    c_rsi = (30 <= rsi <= 75)
    c_breakout = (close > struct_h)
    c_breakdown = (close < struct_l)

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Level Failed: Close ({close:.2f}) <= Resistance ({struct_h:.2f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.2f}) must be above EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be above EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-75")
        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Level Failed: Close ({close:.2f}) >= Support ({struct_l:.2f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.2f}) must be below EMA200 ({ema200:.2f}) and EMA50 ({ema50:.2f}) must be below EMA200")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) is outside 30-75")
        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("No valid strict structural pattern detected.")

    entry_price = round(close, 4)
    sl, tp = "N/A", "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        sl, tp = sl_val, round(entry_price + (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with strict structure, EMA, RSI ({rsi:.1f}), and breakout."
    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        sl, tp = sl_val, round(entry_price - (risk * 2), 4)
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
