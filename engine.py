import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# 1. CALCULATE INDICATORS (SAFE & ROBUST)
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50.0)
    return df

# ==========================================================
# 2. PIVOT DETECTION
# ==========================================================
def detect_pivots(df, window=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    for i in range(window, len(df) - window):
        high_win = df['High'].iloc[i - window:i + window + 1]
        low_win = df['Low'].iloc[i - window:i + window + 1]
        
        if not high_win.empty and df['High'].iloc[i] == high_win.max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]
        if not low_win.empty and df['Low'].iloc[i] == low_win.min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]
            
    return df

# ==========================================================
# 3. PERCENTAGE MATCH ENGINE (1% STRICT TOLERANCE LIMIT)
# ==========================================================
def calc_match_score(val1, val2, max_tol=0.01):
    """
    ØªØ­ÙˆÙŠÙ„ Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø¨ÙŠÙ† Ù†Ù‚Ø·ØªÙŠÙ† Ø¥Ù„Ù‰ Ù†Ø³Ø¨Ø© ØªØ·Ø§Ø¨Ù‚ Ù‡Ù†Ø¯Ø³ÙŠ Ù…Ù† 0% Ø¥Ù„Ù‰ 100%
    """
    if max(abs(val1), abs(val2)) == 0:
        return 100.0
    var_pct = abs(val1 - val2) / max(abs(val1), abs(val2))
    if var_pct <= max_tol:
        return (1.0 - (var_pct / max_tol)) * 100.0
    return 0.0

def scan_all_patterns_by_percentage(df):
    ph, pl = df['Pivot_H'].dropna(), df['Pivot_L'].dropna()
    if len(ph) < 3 or len(pl) < 3:
        return "NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None, 0.0

    h3, h2, h1 = ph.iloc[-1], ph.iloc[-2], ph.iloc[-3]
    l3, l2, l1 = pl.iloc[-1], pl.iloc[-2], pl.iloc[-3]
    
    p_start = min(ph.index[-3], pl.index[-3])
    p_end = max(ph.index[-1], pl.index[-1])
    close = df['Close'].iloc[-1]
    
    TOL = 0.01  # Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø§Ù„Ø£Ù‚ØµÙ‰ Ø§Ù„Ù…Ø³Ù…ÙˆØ­ Ø¨Ù‡Ø§: 1% ÙÙ‚Ø·
    candidates = []

    # --- 1. TRIPLE BOTTOM & TOP (ÙØ­Øµ Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø§Ù„ØªØ±Ø§ÙƒÙ…ÙŠ Ù„Ù€ 3 Ù…Ø±ØªÙƒØ²Ø§Øª) ---
    max_l, min_l = max(l1, l2, l3), min(l1, l2, l3)
    var_triple_l = (max_l - min_l) / max_l
    if var_triple_l <= TOL:
        score = (1.0 - (var_triple_l / TOL)) * 100.0
        candidates.append({"name": "Triple Bottom", "bias": "Bullish", "h": max(h1, h2, h3), "l": min_l, "start": p_start, "end": p_end, "match": score})

    max_h, min_h = max(h1, h2, h3), min(h1, h2, h3)
    var_triple_h = (max_h - min_h) / max_h
    if var_triple_h <= TOL:
        score = (1.0 - (var_triple_h / TOL)) * 100.0
        candidates.append({"name": "Triple Top", "bias": "Bearish", "h": max_h, "l": min(l1, l2, l3), "start": p_start, "end": p_end, "match": score})

    # --- 2. DOUBLE BOTTOM (W PATTERN) & DOUBLE TOP (M PATTERN) ---
    if h3 > l3:
        score_w = calc_match_score(l2, l3, TOL)
        if score_w > 0:
            candidates.append({"name": "Double Bottom (W Pattern)", "bias": "Bullish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "match": score_w})

    if l3 < h3:
        score_m = calc_match_score(h2, h3, TOL)
        if score_m > 0:
            candidates.append({"name": "Double Top (M Pattern)", "bias": "Bearish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "match": score_m})

    # --- 3. HEAD AND SHOULDERS / INVERSE ---
    if len(ph) >= 3 and len(pl) >= 2 and h2 > h1 and h2 > h3:
        score_hs = calc_match_score(h1, h3, TOL)
        if score_hs > 0:
            candidates.append({"name": "Head and Shoulders", "bias": "Bearish", "h": h2, "l": min(l1, l2), "start": p_start, "end": p_end, "match": score_hs})

    if len(pl) >= 3 and len(ph) >= 2 and l2 < l1 and l2 < l3:
        score_ihs = calc_match_score(l1, l3, TOL)
        if score_ihs > 0:
            candidates.append({"name": "Inverse Head and Shoulders", "bias": "Bullish", "h": max(h1, h2), "l": l2, "start": p_start, "end": p_end, "match": score_ihs})

    # --- 4. DYNAMIC WEDGES (SLOPE MATCHING) ---
    slope_h = (h3 - h1) / max(h1, h3)
    slope_l = (l3 - l1) / max(l1, l3)

    if h1 > h2 > h3 and slope_h < 0:
        var_wedge = min(abs(slope_h), TOL)
        score = (1.0 - (var_wedge / TOL)) * 50.0 + 50.0
        candidates.append({"name": "Falling Wedge", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if h1 < h2 < h3 and slope_h > 0:
        var_wedge = min(abs(slope_h), TOL)
        score = (1.0 - (var_wedge / TOL)) * 50.0 + 50.0
        candidates.append({"name": "Rising Wedge", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    # --- 5. TRIANGLES & FLAGS ---
    if h1 < h2 and calc_match_score(h2, h3, TOL) > 0 and l1 < l2 < l3:
        score = calc_match_score(h2, h3, TOL)
        candidates.append({"name": "Ascending Triangle", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if l1 > l2 and calc_match_score(l2, l3, TOL) > 0 and h1 > h2 > h3:
        score = calc_match_score(l2, l3, TOL)
        candidates.append({"name": "Descending Triangle", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if not candidates:
        return "NO PATTERN DETECTED", "Neutral", h3, l3, p_start, p_end, 0.0

    # Ø§Ù„Ù…ÙØ§Ø¶Ù„Ø© ÙˆØ§Ø®ØªÙŠØ§Ø± Ø£Ø¹Ù„Ù‰ Ù†Ù…Ø· Ù…Ù† Ø­ÙŠØ« Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ·Ø§Ø¨Ù‚ Ø§Ù„Ù…Ø¦ÙˆÙŠØ©
    best = max(candidates, key=lambda x: x["match"])
    return best["name"], best["bias"], best["h"], best["l"], best["start"], best["end"], round(best["match"], 2)

# ==========================================================
# 4. FULL ANALYSIS ENGINE
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = detect_pivots(df)

    pattern_name, bias, struct_h, struct_l, pattern_start, pattern_end, match_pct = scan_all_patterns_by_percentage(df)

    latest = df.iloc[-1]
    close, ema50, ema200, rsi = latest['Close'], latest['EMA50'], latest['EMA200'], latest['RSI']

    c_ema_bull = (close > ema200) and (ema50 > ema200)
    c_ema_bear = (close < ema200) and (close < ema50)
    c_rsi = (30 <= rsi <= 75)
    c_breakout = (close > struct_h)
    c_breakdown = (close < struct_l)

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Failed: Close ({close:.4f}) <= Resistance ({struct_h:.4f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be above EMA200 ({ema200:.4f}) & EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Failed: Close ({close:.4f}) >= Support ({struct_l:.4f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be below EMA200 ({ema200:.4f}) & EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("Waiting for structural breakout direction.")

    entry_price = round(close, 4)
    sl, tp = "N/A", "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        sl, tp = sl_val, round(entry_price + (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with {match_pct}% Match Score."
    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        sl, tp = sl_val, round(entry_price - (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with {match_pct}% Match Score."
    else:
        status_msg = f"Pattern: {pattern_name} ({match_pct}% Match) | REJECTED: " + " | ".join(rejected_reasons)

    return {
        "df": df, "pattern": pattern_name, "bias": bias, "match_pct": match_pct,
        "signal": final_signal, "reason": status_msg, "entry": entry_price, "sl": sl, "tp": tp,
        "close": entry_price, "ema50": round(ema50, 4), "ema200": round(ema200, 4),
        "rsi": round(rsi, 2), "pattern_start": pattern_start, "pattern_end": pattern_end,
        "structural_high": struct_h, "structural_low": struct_l
    }

import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# 1. CALCULATE INDICATORS (SAFE & ROBUST)
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50.0)
    return df

# ==========================================================
# 2. PIVOT DETECTION
# ==========================================================
def detect_pivots(df, window=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    for i in range(window, len(df) - window):
        high_win = df['High'].iloc[i - window:i + window + 1]
        low_win = df['Low'].iloc[i - window:i + window + 1]
        
        if not high_win.empty and df['High'].iloc[i] == high_win.max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]
        if not low_win.empty and df['Low'].iloc[i] == low_win.min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]
            
    return df

# ==========================================================
# 3. PERCENTAGE MATCH ENGINE (1% STRICT TOLERANCE LIMIT)
# ==========================================================
def calc_match_score(val1, val2, max_tol=0.01):
    """
    ØªØ­ÙˆÙŠÙ„ Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø¨ÙŠÙ† Ù†Ù‚Ø·ØªÙŠÙ† Ø¥Ù„Ù‰ Ù†Ø³Ø¨Ø© ØªØ·Ø§Ø¨Ù‚ Ù‡Ù†Ø¯Ø³ÙŠ Ù…Ù† 0% Ø¥Ù„Ù‰ 100%
    """
    if max(abs(val1), abs(val2)) == 0:
        return 100.0
    var_pct = abs(val1 - val2) / max(abs(val1), abs(val2))
    if var_pct <= max_tol:
        return (1.0 - (var_pct / max_tol)) * 100.0
    return 0.0

def scan_all_patterns_by_percentage(df):
    ph, pl = df['Pivot_H'].dropna(), df['Pivot_L'].dropna()
    if len(ph) < 3 or len(pl) < 3:
        return "NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None, 0.0

    h3, h2, h1 = ph.iloc[-1], ph.iloc[-2], ph.iloc[-3]
    l3, l2, l1 = pl.iloc[-1], pl.iloc[-2], pl.iloc[-3]
    
    p_start = min(ph.index[-3], pl.index[-3])
    p_end = max(ph.index[-1], pl.index[-1])
    close = df['Close'].iloc[-1]
    
    TOL = 0.01  # Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø§Ù„Ø£Ù‚ØµÙ‰ Ø§Ù„Ù…Ø³Ù…ÙˆØ­ Ø¨Ù‡Ø§: 1% ÙÙ‚Ø·
    candidates = []

    # --- 1. TRIPLE BOTTOM & TOP (ÙØ­Øµ Ø§Ù„ØªØ¨Ø§ÙŠÙ† Ø§Ù„ØªØ±Ø§ÙƒÙ…ÙŠ Ù„Ù€ 3 Ù…Ø±ØªÙƒØ²Ø§Øª) ---
    max_l, min_l = max(l1, l2, l3), min(l1, l2, l3)
    var_triple_l = (max_l - min_l) / max_l
    if var_triple_l <= TOL:
        score = (1.0 - (var_triple_l / TOL)) * 100.0
        candidates.append({"name": "Triple Bottom", "bias": "Bullish", "h": max(h1, h2, h3), "l": min_l, "start": p_start, "end": p_end, "match": score})

    max_h, min_h = max(h1, h2, h3), min(h1, h2, h3)
    var_triple_h = (max_h - min_h) / max_h
    if var_triple_h <= TOL:
        score = (1.0 - (var_triple_h / TOL)) * 100.0
        candidates.append({"name": "Triple Top", "bias": "Bearish", "h": max_h, "l": min(l1, l2, l3), "start": p_start, "end": p_end, "match": score})

    # --- 2. DOUBLE BOTTOM (W PATTERN) & DOUBLE TOP (M PATTERN) ---
    if h3 > l3:
        score_w = calc_match_score(l2, l3, TOL)
        if score_w > 0:
            candidates.append({"name": "Double Bottom (W Pattern)", "bias": "Bullish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "match": score_w})

    if l3 < h3:
        score_m = calc_match_score(h2, h3, TOL)
        if score_m > 0:
            candidates.append({"name": "Double Top (M Pattern)", "bias": "Bearish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "match": score_m})

    # --- 3. HEAD AND SHOULDERS / INVERSE ---
    if len(ph) >= 3 and len(pl) >= 2 and h2 > h1 and h2 > h3:
        score_hs = calc_match_score(h1, h3, TOL)
        if score_hs > 0:
            candidates.append({"name": "Head and Shoulders", "bias": "Bearish", "h": h2, "l": min(l1, l2), "start": p_start, "end": p_end, "match": score_hs})

    if len(pl) >= 3 and len(ph) >= 2 and l2 < l1 and l2 < l3:
        score_ihs = calc_match_score(l1, l3, TOL)
        if score_ihs > 0:
            candidates.append({"name": "Inverse Head and Shoulders", "bias": "Bullish", "h": max(h1, h2), "l": l2, "start": p_start, "end": p_end, "match": score_ihs})

    # --- 4. DYNAMIC WEDGES (SLOPE MATCHING) ---
    slope_h = (h3 - h1) / max(h1, h3)
    slope_l = (l3 - l1) / max(l1, l3)

    if h1 > h2 > h3 and slope_h < 0:
        var_wedge = min(abs(slope_h), TOL)
        score = (1.0 - (var_wedge / TOL)) * 50.0 + 50.0
        candidates.append({"name": "Falling Wedge", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if h1 < h2 < h3 and slope_h > 0:
        var_wedge = min(abs(slope_h), TOL)
        score = (1.0 - (var_wedge / TOL)) * 50.0 + 50.0
        candidates.append({"name": "Rising Wedge", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    # --- 5. TRIANGLES & FLAGS ---
    if h1 < h2 and calc_match_score(h2, h3, TOL) > 0 and l1 < l2 < l3:
        score = calc_match_score(h2, h3, TOL)
        candidates.append({"name": "Ascending Triangle", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if l1 > l2 and calc_match_score(l2, l3, TOL) > 0 and h1 > h2 > h3:
        score = calc_match_score(l2, l3, TOL)
        candidates.append({"name": "Descending Triangle", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "match": score})

    if not candidates:
        return "NO PATTERN DETECTED", "Neutral", h3, l3, p_start, p_end, 0.0

    # Ø§Ù„Ù…ÙØ§Ø¶Ù„Ø© ÙˆØ§Ø®ØªÙŠØ§Ø± Ø£Ø¹Ù„Ù‰ Ù†Ù…Ø· Ù…Ù† Ø­ÙŠØ« Ù†Ø³Ø¨Ø© Ø§Ù„ØªØ·Ø§Ø¨Ù‚ Ø§Ù„Ù…Ø¦ÙˆÙŠØ©
    best = max(candidates, key=lambda x: x["match"])
    return best["name"], best["bias"], best["h"], best["l"], best["start"], best["end"], round(best["match"], 2)

# ==========================================================
# 4. FULL ANALYSIS ENGINE
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = detect_pivots(df)

    pattern_name, bias, struct_h, struct_l, pattern_start, pattern_end, match_pct = scan_all_patterns_by_percentage(df)

    latest = df.iloc[-1]
    close, ema50, ema200, rsi = latest['Close'], latest['EMA50'], latest['EMA200'], latest['RSI']

    c_ema_bull = (close > ema200) and (ema50 > ema200)
    c_ema_bear = (close < ema200) and (close < ema50)
    c_rsi = (30 <= rsi <= 75)
    c_breakout = (close > struct_h)
    c_breakdown = (close < struct_l)

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Failed: Close ({close:.4f}) <= Resistance ({struct_h:.4f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be above EMA200 ({ema200:.4f}) & EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Failed: Close ({close:.4f}) >= Support ({struct_l:.4f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be below EMA200 ({ema200:.4f}) & EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("Waiting for structural breakout direction.")

    entry_price = round(close, 4)
    sl, tp = "N/A", "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        sl, tp = sl_val, round(entry_price + (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with {match_pct}% Match Score."
    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        sl, tp = sl_val, round(entry_price - (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed with {match_pct}% Match Score."
    else:
        status_msg = f"Pattern: {pattern_name} ({match_pct}% Match) | REJECTED: " + " | ".join(rejected_reasons)

    return {
        "df": df, "pattern": pattern_name, "bias": bias, "match_pct": match_pct,
        "signal": final_signal, "reason": status_msg, "entry": entry_price, "sl": sl, "tp": tp,
        "close": entry_price, "ema50": round(ema50, 4), "ema200": round(ema200, 4),
        "rsi": round(rsi, 2), "pattern_start": pattern_start, "pattern_end": pattern_end,
        "structural_high": struct_h, "structural_low": struct_l
    }

# ==========================================================
# 5. DYNAMIC MULTI-POINT GEOMETRIC PLOTTER
# ==========================================================
def plot_pattern_geometry(analysis_result):
    df = analysis_result['df']
    p_name = analysis_result['pattern']
    bias = analysis_result['bias']
    p_start = analysis_result['pattern_start']
    p_end = analysis_result['pattern_end']
    struct_h = analysis_result['structural_high']
    struct_l = analysis_result['structural_low']

    fig = go.Figure()

    # 1. Candles + EMA
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA50'],
        line=dict(color='orange', width=1.5),
        name='EMA 50'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA200'],
        line=dict(color='deepskyblue', width=2),
        name='EMA 200'
    ))

    # 2. Pattern geometry
    if p_name != "NO PATTERN DETECTED" and p_start is not None and p_end is not None:

        # Preserve original index relationship.
        # If pattern_start/end are integer candle positions,
        # convert them to the real dataframe index.
        try:
        
# 5. DYNAMIC MULTI-POINT GEOMETRIC PLOTTER
# ==========================================================
def plot_pattern_geometry(analysis_result):
    df = analysis_result['df']
    p_name = analysis_result['pattern']
    bias = analysis_result['bias']
    p_start = analysis_result['pattern_start']
    p_end = analysis_result['pattern_end']
    struct_h = analysis_result['structural_high']
    struct_l = analysis_result['structural_low']

    fig = go.Figure()

    # 1. Candles + EMA
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA50'],
        line=dict(color='orange', width=1.5),
        name='EMA 50'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA200'],
        line=dict(color='deepskyblue', width=2),
        name='EMA 200'
    ))

    # 2. Pattern geometry
    if p_name != "NO PATTERN DETECTED" and p_start is not None and p_end is not None:

        # Preserve original index relationship.
        # If pattern_start/end are integer candle positions,
        # convert them to the real dataframe index.
        try:
            if p_start not in df.index:
                p_start = df.index[int(p_start)]

            if p_end not in df.index:
                p_end = df.index[int(p_end)]
        except Exception:
            pass

        # Get pivots only inside the detected pattern range
        ph = df['Pivot_H'].dropna()
        pl = df['Pivot_L'].dropna()

        try:
            ph = ph.loc[p_start:p_end]
        except Exception:
            ph = ph.iloc[0:0]

        try:
            pl = pl.loc[p_start:p_end]
        except Exception:
            pl = pl.iloc[0:0]

        # --------------------------------------------------
        # A. Resistance / Neckline
        # --------------------------------------------------
        fig.add_trace(go.Scatter(
            x=[p_start, df.index[-1]],
            y=[struct_h, struct_h],
            mode='lines',
            line=dict(
                color='gold',
                width=2.5,
                dash='dash'
            ),
            name=f'Neckline / Resistance ({struct_h:.4f})'
        ))

        # --------------------------------------------------
        # B. Support
        # --------------------------------------------------
        fig.add_trace(go.Scatter(
            x=[p_start, df.index[-1]],
            y=[struct_l, struct_l],
            mode='lines',
            line=dict(
                color='cyan',
                width=2,
                dash='dot'
            ),
            name=f'Support Level ({struct_l:.4f})'
        ))

        # --------------------------------------------------
        # C. Combine pivots exactly as before
        # --------------------------------------------------
        pivots = (
            [(idx, val) for idx, val in ph.items()] +
            [(idx, val) for idx, val in pl.items()]
        )
def plot_pattern_geometry(analysis_result):
    df = analysis_result['df']
    p_name = analysis_result['pattern']
    bias = analysis_result['bias']
    p_start = analysis_result['pattern_start']
    p_end = analysis_result['pattern_end']
    struct_h = analysis_result['structural_high']
    struct_l = analysis_result['structural_low']

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA50'],
        line=dict(color='orange', width=1.5),
        name='EMA 50'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA200'],
        line=dict(color='deepskyblue', width=2),
        name='EMA 200'
    ))

    if p_name != "NO PATTERN DETECTED" and p_start is not None and p_end is not None:

        try:
            if p_start not in df.index:
                p_start = df.index[int(p_start)]

            if p_end not in df.index:
                p_end = df.index[int(p_end)]
        except Exception:
            pass

        ph = df['Pivot_H'].dropna()
        pl = df['Pivot_L'].dropna()

        try:
            ph = ph.loc[p_start:p_end]
        except Exception:
            ph = ph.iloc[0:0]

        try:
            pl = pl.loc[p_start:p_end]
        except Exception:
            pl = pl.iloc[0:0]

        fig.add_trace(go.Scatter(
            x=[p_start, df.index[-1]],
            y=[struct_h, struct_h],
            mode='lines',
            line=dict(color='gold', width=2.5, dash='dash'),
            name=f'Neckline / Resistance ({struct_h:.4f})'
        ))

        fig.add_trace(go.Scatter(
            x=[p_start, df.index[-1]],
            y=[struct_l, struct_l],
            mode='lines',
            line=dict(color='cyan', width=2, dash='dot'),
            name=f'Support Level ({struct_l:.4f})'
        ))

        pivots = (
            [(idx, val) for idx, val in ph.items()] +
            [(idx, val) for idx, val in pl.items()]
        )

        pivots.sort(key=lambda x: x[0])

        if pivots:
            x_skel = [pt[0] for pt in pivots]
            y_skel = [pt[1] for pt in pivots]

            line_color = (
                '#2ecc71'
                if bias == 'Bullish'
                else '#e74c3c'
            )

            fig.add_trace(go.Scatter(
                x=x_skel,
                y=y_skel,
                mode='lines+markers',
                line=dict(color=line_color, width=3),
                marker=dict(
                    size=8,
                    color='yellow',
                    symbol='circle'
                ),
                name=f'{p_name} Structure'
            ))

    fig.update_layout(
        title=(
            f"Chart | Pattern: {p_name} "
            f"({analysis_result['match_pct']}% Match) | "
            f"Signal: {analysis_result['signal']}"
        ),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=True
    )

    return fig
