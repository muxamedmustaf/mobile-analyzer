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
# 2. CUSTOM ZIGZAG DETECTION (Strict Depth=12)
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
# 3. STRICT CHRONOLOGICAL PATTERN ENGINE (PERFECT MATCH)
# ==========================================================
def get_chronological_pivots(df):
    """استخراج مصفوفة القمم والقيعان مرتبة زمنياً وبشكل متناوب صارم"""
    pivots = []
    for idx, row in df.iterrows():
        if not np.isnan(row['Pivot_H']):
            pivots.append({'idx': idx, 'val': row['Pivot_H'], 'type': 'H'})
        elif not np.isnan(row['Pivot_L']):
            pivots.append({'idx': idx, 'val': row['Pivot_L'], 'type': 'L'})
            
    # تنقية المصفوفة لضمان تناوب صارم (H -> L -> H -> L)
    clean_pivots = []
    for p in pivots:
        if not clean_pivots:
            clean_pivots.append(p)
        else:
            if clean_pivots[-1]['type'] != p['type']:
                clean_pivots.append(p)
            else:
                # إذا تكررت نفس النوع، نأخذ القمة الأعلى أو القاع الأقل
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

    # ---------------------------------------------------------
    # A. DOUBLE TOP (M) -> Requiring Sequence: [H1, L1, H2]
    # ---------------------------------------------------------
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'H' and p2['type'] == 'L' and p3['type'] == 'H':
            h1, l1, h2 = p1['val'], p2['val'], p3['val']
            # شرط المثالية: القمتان متساويتان بنسبة 1.5% والقاع أعمق بوضوح
            if abs(h1 - h2) / max(h1, h2) <= 0.015 and l1 < min(h1, h2) * 0.98:
                neckline = l1
                height = max(h1, h2) - neckline
                candidates.append({
                    "name": "Double Top", "bias": "Bearish", "match": 95.0,
                    "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'], # يبدأ تماماً من القاع بين القمتين
                    "sl": max(h1, h2) * 1.001, "tp": neckline - height
                })

    # ---------------------------------------------------------
    # B. DOUBLE BOTTOM (W) -> Requiring Sequence: [L1, H1, L2]
    # ---------------------------------------------------------
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'L' and p2['type'] == 'H' and p3['type'] == 'L':
            l1, h1, l2 = p1['val'], p2['val'], p3['val']
            # شرط المثالية: القاعان متساويان بنسبة 1.5% والقمة أعلى بوضوح
            if abs(l1 - l2) / max(l1, l2) <= 0.015 and h1 > max(l1, l2) * 1.02:
                neckline = h1
                height = neckline - min(l1, l2)
                candidates.append({
                    "name": "Double Bottom", "bias": "Bullish", "match": 95.0,
                    "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'], # يبدأ تماماً من القمة بين القاعين
                    "sl": min(l1, l2) * 0.999, "tp": neckline + height
                })

    # ---------------------------------------------------------
    # C. INVERSE HEAD AND SHOULDERS -> Sequence: [L1, H1, L2, H2, L3]
    # ---------------------------------------------------------
    for i in range(len(pivots) - 4):
        p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
        if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['L', 'H', 'L', 'H', 'L']:
            l1, h1, l2, h2, l3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
            
            # الشروط الهندسية الصارمة 100%:
            # 1. الرأس (L2) أعمق بوضوح من الكتف الأيسر (L1) والكتف الأيمن (L3)
            # 2. تماثل الكتفين (L1 و L3) بفارق لا يتعدى 2%
            is_head_deeper = (l2 < l1) and (l2 < l3)
            shoulder_symmetry = abs(l1 - l3) / max(l1, l3) <= 0.02
            head_prominence = (min(l1, l3) - l2) >= (max(h1, h2) - min(l1, l3)) * 0.3
            
            if is_head_deeper and shoulder_symmetry and head_prominence:
                neckline = max(h1, h2)
                height = neckline - l2
                candidates.append({
                    "name": "Inverse Head and Shoulders", "bias": "Bullish", "match": 98.0,
                    "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2), (p4['idx'], h2), (p5['idx'], l3)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'], # يبدأ من القمة الأولى الفاصلة H1
                    "sl": l3 * 0.999, "tp": neckline + height
                })

    # ---------------------------------------------------------
    # D. HEAD AND SHOULDERS -> Sequence: [H1, L1, H2, L2, H3]
    # ---------------------------------------------------------
    for i in range(len(pivots) - 4):
        p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
        if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['H', 'L', 'H', 'L', 'H']:
            h1, l1, h2, l2, h3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
            
            # الشروط الهندسية الصارمة:
            is_head_higher = (h2 > h1) and (h2 > h3)
            shoulder_symmetry = abs(h1 - h3) / max(h1, h3) <= 0.02
            head_prominence = (h2 - max(h1, h3)) >= (max(h1, h3) - min(l1, l2)) * 0.3
            
            if is_head_higher and shoulder_symmetry and head_prominence:
                neckline = min(l1, l2)
                height = h2 - neckline
                candidates.append({
                    "name": "Head and Shoulders", "bias": "Bearish", "match": 98.0,
                    "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2), (p4['idx'], l2), (p5['idx'], h3)],
                    "entry_trigger": neckline, 
                    "neckline_start_idx": p2['idx'], # يبدأ من القاع الأول الفاصل L1
                    "sl": h3 * 1.001, "tp": neckline - height
                })

    if not candidates:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    # اختيار النمط الأحدث والأكثر تطابقاً
    best_pattern = candidates[-1]
    return best_pattern

# ==========================================================
# 4. FULL ANALYSIS
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)
    
    p_data = scan_and_calculate_logic(df)
    
    if p_data["name"] == "NO PATTERN DETECTED":
        return {"df": df, "pattern": "NO PATTERN DETECTED", "signal": "WAITING", "reason": "No valid ideal pattern.", "entry": 0, "sl": 0, "tp": 0, "nodes": []}

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
    
