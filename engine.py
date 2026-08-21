import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# 1. CALCULATE INDICATORS
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
# 2. CUSTOM ZIGZAG DETECTION (Depth=12, Deviation=5, Backstep=3)
# ==========================================================
def calculate_zigzag(df, depth=12, deviation=5, backstep=3):
    """محاكاة دقيقة لمؤشر ZigZag بناءً على معطيات المستخدم"""
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    highs = df['High'].values
    lows = df['Low'].values
    
    last_pivot_idx = 0
    last_pivot_type = 0 # 1 for High, -1 for Low
    
    # تحويل الانحراف إلى نسبة مئوية تقريبية للفلترة (5 = 0.5%)
    dev_pct = deviation / 1000.0 
    
    for i in range(depth, len(df) - backstep):
        window_high = np.max(highs[i-depth:i+1])
        window_low = np.min(lows[i-depth:i+1])
        
        is_high = highs[i] == window_high
        is_low = lows[i] == window_low
        
        if is_high and (i - last_pivot_idx >= backstep):
            if last_pivot_type != 1 or (highs[i] > highs[last_pivot_idx]):
                df.loc[df.index[i], 'Pivot_H'] = highs[i]
                last_pivot_idx = i
                last_pivot_type = 1
                
        if is_low and (i - last_pivot_idx >= backstep):
            if last_pivot_type != -1 or (lows[i] < lows[last_pivot_idx]):
                df.loc[df.index[i], 'Pivot_L'] = lows[i]
                last_pivot_idx = i
                last_pivot_type = -1

    return df

# ==========================================================
# 3. PATTERN SCANNER & LOGIC ENGINE
# ==========================================================
def scan_and_calculate_logic(df):
    ph = df['Pivot_H'].dropna()
    pl = df['Pivot_L'].dropna()
    
    if len(ph) < 3 or len(pl) < 3:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    # آخر 3 قمم وقيعان
    h3_idx, h3 = ph.index[-1], ph.iloc[-1]
    h2_idx, h2 = ph.index[-2], ph.iloc[-2]
    h1_idx, h1 = ph.index[-3], ph.iloc[-3]
    
    l3_idx, l3 = pl.index[-1], pl.iloc[-1]
    l2_idx, l2 = pl.index[-2], pl.iloc[-2]
    l1_idx, l1 = pl.index[-3], pl.iloc[-3]
    
    TOL = 0.01  # 1% Strict Tolerance
    candidates = []

    def match(v1, v2):
        if max(v1, v2) == 0: return 100
        var = abs(v1 - v2) / max(v1, v2)
        return (1.0 - (var / TOL)) * 100 if var <= TOL else 0

    # 1. DOUBLE BOTTOM (W)
    if h3 > l3:
        m_score = match(l2, l3)
        if m_score > 0:
            neckline = max(h2, h3)
            height = neckline - min(l2, l3)
            candidates.append({
                "name": "Double Bottom", "bias": "Bullish", "match": m_score,
                "nodes": [(l2_idx, l2), (h2_idx, h2), (l3_idx, l3)],
                "entry_trigger": neckline, "sl": min(l2, l3) * 0.999, "tp": neckline + height
            })

    # 2. DOUBLE TOP (M)
    if l3 < h3:
        m_score = match(h2, h3)
        if m_score > 0:
            neckline = min(l2, l3)
            height = max(h2, h3) - neckline
            candidates.append({
                "name": "Double Top", "bias": "Bearish", "match": m_score,
                "nodes": [(h2_idx, h2), (l2_idx, l2), (h3_idx, h3)],
                "entry_trigger": neckline, "sl": max(h2, h3) * 1.001, "tp": neckline - height
            })

    # 3. HEAD & SHOULDERS
    if len(ph) >= 3 and len(pl) >= 2 and h2 > h1 and h2 > h3:
        m_score = match(h1, h3)
        if m_score > 0:
            neckline = min(l1, l2)
            height = h2 - neckline
            candidates.append({
                "name": "Head and Shoulders", "bias": "Bearish", "match": m_score,
                "nodes": [(h1_idx, h1), (l1_idx, l1), (h2_idx, h2), (l2_idx, l2), (h3_idx, h3)],
                "entry_trigger": neckline, "sl": h3 * 1.001, "tp": neckline - height # SL فوق الكتف الأيمن
            })

    # 4. INVERSE HEAD & SHOULDERS
    if len(pl) >= 3 and len(ph) >= 2 and l2 < l1 and l2 < l3:
        m_score = match(l1, l3)
        if m_score > 0:
            neckline = max(h1, h2)
            height = neckline - l2
            candidates.append({
                "name": "Inverse Head and Shoulders", "bias": "Bullish", "match": m_score,
                "nodes": [(l1_idx, l1), (h1_idx, h1), (l2_idx, l2), (h2_idx, h2), (l3_idx, l3)],
                "entry_trigger": neckline, "sl": l3 * 0.999, "tp": neckline + height # SL تحت الكتف الأيمن
            })

    # 5. WEDGES
    slope_h = (h3 - h1) / max(h1, h3)
    slope_l = (l3 - l1) / max(l1, l3)
    
    if h1 > h2 > h3 and slope_h < 0: # Falling Wedge
        candidates.append({
            "name": "Falling Wedge", "bias": "Bullish", "match": 80.0,
            "nodes": [(h1_idx, h1), (l1_idx, l1), (h2_idx, h2), (l2_idx, l2), (h3_idx, h3), (l3_idx, l3)],
            "entry_trigger": h3, "sl": l3 * 0.999, "tp": h1 # الهدف قاعدة الوتد
        })
        
    if h1 < h2 < h3 and slope_h > 0: # Rising Wedge
        candidates.append({
            "name": "Rising Wedge", "bias": "Bearish", "match": 80.0,
            "nodes": [(l1_idx, l1), (h1_idx, h1), (l2_idx, l2), (h2_idx, h2), (l3_idx, l3), (h3_idx, h3)],
            "entry_trigger": l3, "sl": h3 * 1.001, "tp": l1 # الهدف قاعدة الوتد
        })

    if not candidates:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    best_pattern = max(candidates, key=lambda x: x["match"])
    return best_pattern

# ==========================================================
# 4. FULL ANALYSIS
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    # استخدام معطيات ZigZag المطلوبة
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)
    
    p_data = scan_and_calculate_logic(df)
    
    if p_data["name"] == "NO PATTERN DETECTED":
        return {"df": df, "pattern": "NO PATTERN DETECTED", "signal": "WAITING", "reason": "No valid geometry.", "entry": 0, "sl": 0, "tp": 0, "nodes": []}

    latest = df.iloc[-1]
    close, ema50, ema200, rsi = latest['Close'], latest['EMA50'], latest['EMA200'], latest['RSI']
    bias, trigger, sl, tp = p_data["bias"], p_data["entry_trigger"], p_data["sl"], p_data["tp"]

    c_rsi = (30 <= rsi <= 75)
    final_signal = "WAITING"
    reasons = []

    if bias == "Bullish":
        if close > trigger and close > ema200 and c_rsi:
            final_signal = "STRONG BUY"
        else:
            reasons.append(f"Waiting for close > {trigger:.4f} & EMA bull trend.")
            
    elif bias == "Bearish":
        if close < trigger and close < ema200 and c_rsi:
            final_signal = "STRONG SELL"
        else:
            reasons.append(f"Waiting for close < {trigger:.4f} & EMA bear trend.")

    return {
        "df": df, "pattern": p_data["name"], "bias": bias, "match_pct": round(p_data["match"], 2),
        "signal": final_signal, "reason": " | ".join(reasons) if final_signal == "WAITING" else "All Conditions Met!",
        "entry": round(close, 4), "sl": round(sl, 4), "tp": round(tp, 4),
        "trigger": round(trigger, 4), "nodes": p_data["nodes"]
    }
