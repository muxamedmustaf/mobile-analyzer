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
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    highs = df['High'].values
    lows = df['Low'].values
    
    last_pivot_idx = 0
    last_pivot_type = 0 # 1 for High, -1 for Low
    
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
# 3. 15 CLASSIC PATTERNS SCANNER & LOGIC ENGINE
# ==========================================================
def scan_and_calculate_logic(df):
    ph = df['Pivot_H'].dropna()
    pl = df['Pivot_L'].dropna()
    
    if len(ph) < 4 or len(pl) < 4:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    # استخراج آخر القمم والقيعان بدقة للنماذج المعقدة (حتى 4 قمم وقيعان)
    h_idx = list(ph.index[-4:])
    h_val = list(ph.iloc[-4:])
    l_idx = list(pl.index[-4:])
    l_val = list(pl.iloc[-4:])
    
    TOL = 0.015  # 1.5% Strict Global Tolerance
    candidates = []

    def match(v1, v2):
        if max(v1, v2) == 0: return 100
        var = abs(v1 - v2) / max(v1, v2)
        return (1.0 - (var / TOL)) * 100 if var <= TOL else 0

    # ---------------------------------------------------------
    # 1. DOUBLE BOTTOM (W)
    # ---------------------------------------------------------
    m_db = match(l_val[-1], l_val[-2])
    if m_db > 0 and h_val[-1] > l_val[-1]:
        neckline = max(h_val[-2], h_val[-1])
        height = neckline - min(l_val[-2], l_val[-1])
        candidates.append({
            "name": "Double Bottom", "bias": "Bullish", "match": m_db,
            "nodes": [(l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1])],
            "entry_trigger": neckline, "neckline_start_idx": h_idx[-2],
            "sl": min(l_val[-2], l_val[-1]) * 0.999, "tp": neckline + height
        })

    # ---------------------------------------------------------
    # 2. DOUBLE TOP (M)
    # ---------------------------------------------------------
    m_dt = match(h_val[-1], h_val[-2])
    if m_dt > 0 and l_val[-1] < h_val[-1]:
        neckline = min(l_val[-2], l_val[-1])
        height = max(h_val[-2], h_val[-1]) - neckline
        candidates.append({
            "name": "Double Top", "bias": "Bearish", "match": m_dt,
            "nodes": [(h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1])],
            "entry_trigger": neckline, "neckline_start_idx": l_idx[-2],
            "sl": max(h_val[-2], h_val[-1]) * 1.001, "tp": neckline - height
        })

    # ---------------------------------------------------------
    # 3. HEAD AND SHOULDERS
    # ---------------------------------------------------------
    if h_val[-2] > h_val[-3] and h_val[-2] > h_val[-1]:
        m_hs = match(h_val[-3], h_val[-1])
        if m_hs > 0:
            neckline = min(l_val[-2], l_val[-3])
            height = h_val[-2] - neckline
            candidates.append({
                "name": "Head and Shoulders", "bias": "Bearish", "match": m_hs,
                "nodes": [(h_idx[-3], h_val[-3]), (l_idx[-3], l_val[-3]), (h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1])],
                "entry_trigger": neckline, "neckline_start_idx": l_idx[-3],
                "sl": h_val[-1] * 1.001, "tp": neckline - height
            })

    # ---------------------------------------------------------
    # 4. INVERSE HEAD AND SHOULDERS
    # ---------------------------------------------------------
    if l_val[-2] < l_val[-3] and l_val[-2] < l_val[-1]:
        m_ihs = match(l_val[-3], l_val[-1])
        if m_ihs > 0:
            neckline = max(h_val[-2], h_val[-3])
            height = neckline - l_val[-2]
            candidates.append({
                "name": "Inverse Head and Shoulders", "bias": "Bullish", "match": m_ihs,
                "nodes": [(l_idx[-3], l_val[-3]), (h_idx[-3], h_val[-3]), (l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1])],
                "entry_trigger": neckline, "neckline_start_idx": h_idx[-3],
                "sl": l_val[-1] * 0.999, "tp": neckline + height
            })

    # ---------------------------------------------------------
    # 5. TRIPLE TOP
    # ---------------------------------------------------------
    if len(h_val) >= 3:
        m_tp1 = match(h_val[-1], h_val[-2])
        m_tp2 = match(h_val[-2], h_val[-3])
        if m_tp1 > 0 and m_tp2 > 0:
            neckline = min(l_val[-2], l_val[-3])
            height = max(h_val[-3], h_val[-2], h_val[-1]) - neckline
            candidates.append({
                "name": "Triple Top", "bias": "Bearish", "match": (m_tp1 + m_tp2) / 2,
                "nodes": [(h_idx[-3], h_val[-3]), (l_idx[-3], l_val[-3]), (h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1])],
                "entry_trigger": neckline, "neckline_start_idx": l_idx[-3],
                "sl": max(h_val) * 1.001, "tp": neckline - height
            })

    # ---------------------------------------------------------
    # 6. TRIPLE BOTTOM
    # ---------------------------------------------------------
    if len(l_val) >= 3:
        m_tb1 = match(l_val[-1], l_val[-2])
        m_tb2 = match(l_val[-2], l_val[-3])
        if m_tb1 > 0 and m_tb2 > 0:
            neckline = max(h_val[-2], h_val[-3])
            height = neckline - min(l_val[-3], l_val[-2], l_val[-1])
            candidates.append({
                "name": "Triple Bottom", "bias": "Bullish", "match": (m_tb1 + m_tb2) / 2,
                "nodes": [(l_idx[-3], l_val[-3]), (h_idx[-3], h_val[-3]), (l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1])],
                "entry_trigger": neckline, "neckline_start_idx": h_idx[-3],
                "sl": min(l_val) * 0.999, "tp": neckline + height
            })

    # ---------------------------------------------------------
    # 7. ASCENDING TRIANGLE
    # ---------------------------------------------------------
    if match(h_val[-1], h_val[-2]) > 80 and l_val[-1] > l_val[-2]:
        resistance = max(h_val[-1], h_val[-2])
        height = resistance - l_val[-2]
        candidates.append({
            "name": "Ascending Triangle", "bias": "Bullish", "match": 85.0,
            "nodes": [(l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1]), (h_idx[-1], h_val[-1])],
            "entry_trigger": resistance, "neckline_start_idx": h_idx[-2],
            "sl": l_val[-1] * 0.999, "tp": resistance + height
        })

    # ---------------------------------------------------------
    # 8. DESCENDING TRIANGLE
    # ---------------------------------------------------------
    if match(l_val[-1], l_val[-2]) > 80 and h_val[-1] < h_val[-2]:
        support = min(l_val[-1], l_val[-2])
        height = h_val[-2] - support
        candidates.append({
            "name": "Descending Triangle", "bias": "Bearish", "match": 85.0,
            "nodes": [(h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1]), (l_idx[-1], l_val[-1])],
            "entry_trigger": support, "neckline_start_idx": l_idx[-2],
            "sl": h_val[-1] * 1.001, "tp": support - height
        })

    # ---------------------------------------------------------
    # 9. SYMMETRICAL TRIANGLE
    # ---------------------------------------------------------
    if h_val[-1] < h_val[-2] and l_val[-1] > l_val[-2]:
        candidates.append({
            "name": "Symmetrical Triangle", "bias": "Bullish", "match": 80.0,
            "nodes": [(l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1]), (h_idx[-1], h_val[-1])],
            "entry_trigger": h_val[-1], "neckline_start_idx": l_idx[-2],
            "sl": l_val[-1] * 0.999, "tp": h_val[-1] + (h_val[-2] - l_val[-2])
        })

    # ---------------------------------------------------------
    # 10. RISING WEDGE
    # ---------------------------------------------------------
    if h_val[-1] > h_val[-2] and l_val[-1] > l_val[-2] and (h_val[-1] - h_val[-2]) < (l_val[-1] - l_val[-2]):
        candidates.append({
            "name": "Rising Wedge", "bias": "Bearish", "match": 82.0,
            "nodes": [(l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1]), (h_idx[-1], h_val[-1])],
            "entry_trigger": l_val[-1], "neckline_start_idx": l_idx[-2],
            "sl": h_val[-1] * 1.001, "tp": l_val[-1] - (h_val[-2] - l_val[-2])
        })

    # ---------------------------------------------------------
    # 11. FALLING WEDGE
    # ---------------------------------------------------------
    if h_val[-1] < h_val[-2] and l_val[-1] < l_val[-2] and abs(h_val[-1] - h_val[-2]) > abs(l_val[-1] - l_val[-2]):
        candidates.append({
            "name": "Falling Wedge", "bias": "Bullish", "match": 82.0,
            "nodes": [(h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1]), (l_idx[-1], l_val[-1])],
            "entry_trigger": h_val[-1], "neckline_start_idx": h_idx[-2],
            "sl": l_val[-1] * 0.999, "tp": h_val[-1] + (h_val[-2] - l_val[-2])
        })

    # ---------------------------------------------------------
    # 12. BROADENING TOP (MEGAPHONE)
    # ---------------------------------------------------------
    if h_val[-1] > h_val[-2] and l_val[-1] < l_val[-2]:
        candidates.append({
            "name": "Broadening Top", "bias": "Bearish", "match": 78.0,
            "nodes": [(h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1]), (l_idx[-1], l_val[-1])],
            "entry_trigger": l_val[-1], "neckline_start_idx": l_idx[-2],
            "sl": h_val[-1] * 1.001, "tp": l_val[-1] - (h_val[-1] - l_val[-1])
        })

    # ---------------------------------------------------------
    # 13. ROUNDING BOTTOM (SAUCER)
    # ---------------------------------------------------------
    if l_val[-1] > l_val[-2] and l_val[-2] < l_val[-3]:
        candidates.append({
            "name": "Rounding Bottom", "bias": "Bullish", "match": 80.0,
            "nodes": [(l_idx[-3], l_val[-3]), (l_idx[-2], l_val[-2]), (l_idx[-1], l_val[-1])],
            "entry_trigger": max(h_val[-2], h_val[-1]), "neckline_start_idx": h_idx[-2],
            "sl": l_val[-2] * 0.999, "tp": max(h_val[-2], h_val[-1]) + (max(h_val[-2], h_val[-1]) - l_val[-2])
        })

    # ---------------------------------------------------------
    # 14. RECTANGLE TOP
    # ---------------------------------------------------------
    if match(h_val[-1], h_val[-2]) > 90 and match(l_val[-1], l_val[-2]) > 90:
        candidates.append({
            "name": "Rectangle Top", "bias": "Bearish", "match": 85.0,
            "nodes": [(h_idx[-2], h_val[-2]), (l_idx[-2], l_val[-2]), (h_idx[-1], h_val[-1]), (l_idx[-1], l_val[-1])],
            "entry_trigger": min(l_val[-1], l_val[-2]), "neckline_start_idx": l_idx[-2],
            "sl": max(h_val) * 1.001, "tp": min(l_val) - (max(h_val) - min(l_val))
        })

    # ---------------------------------------------------------
    # 15. RECTANGLE BOTTOM
    # ---------------------------------------------------------
    if match(h_val[-1], h_val[-2]) > 90 and match(l_val[-1], l_val[-2]) > 90:
        candidates.append({
            "name": "Rectangle Bottom", "bias": "Bullish", "match": 85.0,
            "nodes": [(l_idx[-2], l_val[-2]), (h_idx[-2], h_val[-2]), (l_idx[-1], l_val[-1]), (h_idx[-1], h_val[-1])],
            "entry_trigger": max(h_val[-1], h_val[-2]), "neckline_start_idx": h_idx[-2],
            "sl": min(l_val) * 0.999, "tp": max(h_val) + (max(h_val) - min(l_val))
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
        "trigger": round(trigger, 4), "nodes": p_data["nodes"],
        "neckline_start_idx": p_data.get("neckline_start_idx", p_data["nodes"][0][0])
    }
    
