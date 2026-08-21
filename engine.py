import pandas as pd
import numpy as np

# ==========================================================
# 1. CALCULATE INDICATORS (MACD Histogram & RSI)
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # MACD & Histogram Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50.0)
    return df

# ==========================================================
# 2. CUSTOM ZIGZAG DETECTION (H=Resistance, L=Support)
# ==========================================================
def calculate_zigzag(df, depth=12, deviation=5, backstep=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    highs = df['High'].values
    lows = df['Low'].values
    
    last_pivot_idx = 0
    last_pivot_type = 0 # 1 for High (Resistance), -1 for Low (Support)
    
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
# 3. ROBUST PATTERN ENGINE (Slanted Necklines & Active Frontier)
# ==========================================================
def get_chronological_pivots(df):
    pivots = []
    for idx, row in df.iterrows():
        if not np.isnan(row['Pivot_H']):
            pivots.append({'idx': idx, 'val': row['Pivot_H'], 'type': 'H'}) # Resistance
        elif not np.isnan(row['Pivot_L']):
            pivots.append({'idx': idx, 'val': row['Pivot_L'], 'type': 'L'}) # Support
            
    clean_pivots = []
    for p in pivots:
        if not clean_pivots:
            clean_pivots.append(p)
        else:
            if clean_pivots[-1]['type'] != p['type']:
                clean_pivots.append(p)
            else:
                if p['type'] == 'H' and p['val'] > clean_pivots[-1]['val']:
                    clean_pivots[-1] = p
                elif p['type'] == 'L' and p['val'] < clean_pivots[-1]['val']:
                    clean_pivots[-1] = p
    return clean_pivots

def scan_and_calculate_logic(df):
    pivots = get_chronological_pivots(df)
    
    if len(pivots) < 5:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    candidates = []
    current_pos = len(df) - 1

    # ---------------------------------------------------------
    # A. DOUBLE TOP (M)
    # ---------------------------------------------------------
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'H' and p2['type'] == 'L' and p3['type'] == 'H':
            p3_pos = df.index.get_loc(p3['idx'])
            if (current_pos - p3_pos) > 20:
                continue
                
            h1, l1, h2 = p1['val'], p2['val'], p3['val']
            if abs(h1 - h2) / max(h1, h2) <= 0.03 and l1 < min(h1, h2) * 0.99:
                neckline = l1
                height = max(h1, h2) - neckline
                candidates.append({
                    "name": "Double Top", "bias": "Bearish", "match": 95.0,
                    "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'],
                    "sl": max(h1, h2) * 1.001, "tp": neckline - height
                })

    # ---------------------------------------------------------
    # B. DOUBLE BOTTOM (W)
    # ---------------------------------------------------------
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'L' and p2['type'] == 'H' and p3['type'] == 'L':
            p3_pos = df.index.get_loc(p3['idx'])
            if (current_pos - p3_pos) > 20:
                continue
                
            l1, h1, l2 = p1['val'], p2['val'], p3['val']
            if abs(l1 - l2) / max(l1, l2) <= 0.03 and h1 > max(l1, l2) * 1.01:
                neckline = h1
                height = neckline - min(l1, l2)
                candidates.append({
                    "name": "Double Bottom", "bias": "Bullish", "match": 95.0,
                    "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'],
                    "sl": min(l1, l2) * 0.999, "tp": neckline + height
                })

    # ---------------------------------------------------------
    # C. INVERSE HEAD AND SHOULDERS (Slanted Neckline)
    # ---------------------------------------------------------
    for i in range(len(pivots) - 4):
        p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
        
        p5_pos = df.index.get_loc(p5['idx'])
        if (current_pos - p5_pos) > 20:
            continue
            
        if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['L', 'H', 'L', 'H', 'L']:
            l1, h1, l2, h2, l3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
            
            is_head_deeper = (l2 < l1) and (l2 < l3)
            shoulder_symmetry = abs(l1 - l3) / max(l1, l3) <= 0.04
            head_prominence = (min(l1, l3) - l2) >= (max(h1, h2) - min(l1, l3)) * 0.25
            
            if is_head_deeper and shoulder_symmetry and head_prominence:
                idx1, val1 = p2['idx'], h1
                idx2, val2 = p4['idx'], h2
                pos1 = df.index.get_loc(idx1)
                pos2 = df.index.get_loc(idx2)
                if pos2 != pos1:
                    slope = (val2 - val1) / (pos2 - pos1)
                    neckline_at_current = val2 + slope * (current_pos - pos2)
                else:
                    neckline_at_current = max(h1, h2)
                    
                height = neckline_at_current - l2
                candidates.append({
                    "name": "Inverse Head and Shoulders", "bias": "Bullish", "match": 98.0,
                    "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2), (p4['idx'], h2), (p5['idx'], l3)],
                    "entry_trigger": round(neckline_at_current, 4), 
                    "neckline_start_idx": p2['idx'],
                    "sl": l3 * 0.999, "tp": round(neckline_at_current + height, 4)
                })

    # ---------------------------------------------------------
    # D. HEAD AND SHOULDERS (Slanted Neckline)
    # ---------------------------------------------------------
    for i in range(len(pivots) - 4):
        p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
        
        p5_pos = df.index.get_loc(p5['idx'])
        if (current_pos - p5_pos) > 20:
            continue
            
        if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['H', 'L', 'H', 'L', 'H']:
            h1, l1, h2, l2, h3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
            
            is_head_higher = (h2 > h1) and (h2 > h3)
            shoulder_symmetry = abs(h1 - h3) / max(h1, h3) <= 0.04
            head_prominence = (h2 - max(h1, h3)) >= (max(h1, h3) - min(l1, l2)) * 0.25
            
            if is_head_higher and shoulder_symmetry and head_prominence:
                idx1, val1 = p2['idx'], l1
                idx2, val2 = p4['idx'], l2
                pos1 = df.index.get_loc(idx1)
                pos2 = df.index.get_loc(idx2)
                if pos2 != pos1:
                    slope = (val2 - val1) / (pos2 - pos1)
                    neckline_at_current = val2 + slope * (current_pos - pos2)
                else:
                    neckline_at_current = min(l1, l2)
                    
                height = h2 - neckline_at_current
                candidates.append({
                    "name": "Head and Shoulders", "bias": "Bearish", "match": 98.0,
                    "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2), (p4['idx'], l2), (p5['idx'], h3)],
                    "entry_trigger": round(neckline_at_current, 4), 
                    "neckline_start_idx": p2['idx'],
                    "sl": h3 * 1.001, "tp": round(neckline_at_current - height, 4)
                })

    if not candidates:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    return candidates[-1]

# ==========================================================
# 4. FULL ANALYSIS (Closed-Bar Validation & Fixed Syntax)
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)
    
    p_data = scan_and_calculate_logic(df)
    
    if p_data["name"] == "NO PATTERN DETECTED":
        return {"df": df, "pattern": "NO PATTERN DETECTED", "signal": "WAITING", "reason": "No active recent pattern found.", "entry": 0, "sl": 0, "tp": 0, "nodes": []}

    latest_closed = df.iloc[-2]
    close, ema50, ema200, rsi, macd_hist = latest_closed['Close'], latest_closed['EMA50'], latest_closed['EMA200'], latest_closed['RSI'], latest_closed['MACD_Hist']
    bias, trigger, sl, tp = p_data["bias"], p_data["entry_trigger"], p_data["sl"], p_data["tp"]

    c_rsi = (25 <= rsi <= 82)
    final_signal = "WAITING"
    reasons = []

    if bias == "Bullish":
        if close > trigger and close > ema200 and c_rsi and macd_hist > 0:
            final_signal = "STRONG BUY"
        else:
            reasons.append(f"Waiting for closed bar > {trigger:.4f} & Bullish MACD Hist.")
            
    elif bias == "Bearish":
        if close < trigger and close < ema200 and c_rsi and macd_hist < 0:
            final_signal = "STRONG SELL"
        else:
            reasons.append(f"Waiting for closed bar < {trigger:.4f} & Bearish MACD Hist.")

    return {
        "df": df, "pattern": p_data["name"], "bias": bias, "match_pct": round(p_data["match"], 2),
        "signal": final_signal, "reason": " | ".join(reasons) if final_signal == "WAITING" else "All Conditions Met!",
        "entry": round(close, 4), "sl": round(sl, 4), "tp": round(tp, 4),
        "trigger": round(trigger, 4), "nodes": p_data["nodes"],
        "neckline_start_idx": p_data.get("neckline_start_idx", p_data["nodes"][0][0])
                }
                
