import pandas as pd
import numpy as np

# ==========================================================
# PATTERN ENGINE - STRICT CATALOG MATCHING
# ==========================================================

MAX_PATTERN_AGE = 25
MAX_VARIATION = 0.008  # تقليص نسبة التباين لزيادة الصرامة هندسياً
MIN_CORRECTION = 0.25

# ==========================================================
# 1. INDICATORS
# ==========================================================

def calculate_indicators(df):
    df = df.copy()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50.0)
    return df

# ==========================================================
# 2. ZIGZAG & PIVOTS
# ==========================================================

def calculate_zigzag(df, depth=12, deviation=5, backstep=3):
    df = df.copy()
    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan
    highs = df["High"].values
    lows = df["Low"].values
    last_pos = -backstep
    last_type = 0

    for i in range(depth, len(df) - backstep):
        window_high = np.max(highs[i-depth:i+1])
        window_low = np.min(lows[i-depth:i+1])
        is_high = (highs[i] == window_high)
        is_low = (lows[i] == window_low)

        if is_high and i - last_pos >= backstep:
            if last_type != 1 or highs[i] > highs[last_pos]:
                df.iloc[i, df.columns.get_loc("Pivot_H")] = highs[i]
                last_pos = i
                last_type = 1

        if is_low and i - last_pos >= backstep:
            if last_type != -1 or lows[i] < lows[last_pos]:
                df.iloc[i, df.columns.get_loc("Pivot_L")] = lows[i]
                last_pos = i
                last_type = -1
    return df

def get_chronological_pivots(df):
    pivots = []
    for pos, (idx, row) in enumerate(df.iterrows()):
        if not pd.isna(row["Pivot_H"]):
            pivots.append({"idx": idx, "pos": pos, "val": float(row["Pivot_H"]), "type": "H"})
        elif not pd.isna(row["Pivot_L"]):
            pivots.append({"idx": idx, "pos": pos, "val": float(row["Pivot_L"]), "type": "L"})

    clean = []
    for p in pivots:
        if not clean:
            clean.append(p)
            continue
        last = clean[-1]
        if last["type"] != p["type"]:
            clean.append(p)
        elif p["type"] == "H":
            if p["val"] > last["val"]:
                clean[-1] = p
        elif p["type"] == "L":
            if p["val"] < last["val"]:
                clean[-1] = p
    return clean

# ==========================================================
# 3. HELPERS
# ==========================================================

def variation(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)

def equal_within_1_percent(a, b):
    return variation(a, b) <= MAX_VARIATION

def recent_pattern(points, current_pos):
    if not points:
        return False
    return (current_pos - points[-1]["pos"] <= MAX_PATTERN_AGE)

def make_result(name, bias, points, trigger, sl, tp, score, trigger_type="neckline"):
    return {
        "name": name,
        "bias": bias,
        "match": float(score),
        "nodes": [(p["idx"], p["val"]) for p in points],
        "entry_trigger": float(trigger),
        "trigger_type": trigger_type,
        "sl": float(sl),
        "tp": float(tp),
        "neckline_start_idx": points[1]["idx"] if len(points) > 1 else points[0]["idx"]
    }

# ==========================================================
# SECTION A: REVERSAL PATTERNS
# ==========================================================

def detect_double_top(pivots, current_pos):
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["H", "L", "H"]: return None
    h1, l1, h2 = [x["val"] for x in p]
    if not recent_pattern(p, current_pos): return None
    if not equal_within_1_percent(h1, h2): return None
    correction = h1 - l1
    if correction <= 0: return None
    return make_result("Double Top", "Bearish", p, l1, max(h1, h2) * 1.001, l1 - correction, 100)

def detect_double_bottom(pivots, current_pos):
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["L", "H", "L"]: return None
    l1, h1, l2 = [x["val"] for x in p]
    if not recent_pattern(p, current_pos): return None
    if not equal_within_1_percent(l1, l2): return None
    correction = h1 - l1
    if correction <= 0: return None
    return make_result("Double Bottom", "Bullish", p, h1, min(l1, l2) * 0.999, h1 + correction, 100)

def detect_head_shoulders(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    if not (h2 > h1 and h2 > h3): return None
    if not equal_within_1_percent(h1, h3): return None
    neckline = min(l1, l2)
    height = h2 - neckline
    if height <= 0: return None
    return make_result("Head and Shoulders", "Bearish", p, neckline, h2 * 1.001, neckline - height, 100)

def detect_inverse_head_shoulders(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    if not (l2 < l1 and l2 < l3): return None
    if not equal_within_1_percent(l1, l3): return None
    neckline = max(h1, h2)
    height = neckline - l2
    if height <= 0: return None
    return make_result("Inverse Head and Shoulders", "Bullish", p, neckline, l2 * 0.999, neckline + height, 100)

# ==========================================================
# SECTION B: CONTINUATION PATTERNS
# ==========================================================

def detect_rectangle(pivots, current_pos):
    if len(pivots) < 6: return None
    p = pivots[-6:]
    highs = [x["val"] for x in p if x["type"] == "H"]
    lows = [x["val"] for x in p if x["type"] == "L"]
    if len(highs) < 2 or len(lows) < 2: return None
    if not recent_pattern(p, current_pos): return None
    
    # مطابقة صارمة للمستطيل: قمم أفقية تماماً وقيعان أفقية تماماً دون ميل
    if not (equal_within_1_percent(highs[0], highs[-1]) and equal_within_1_percent(lows[0], lows[-1])):
        return None
        
    resistance = max(highs)
    support = min(lows)
    height = resistance - support
    bias = "Bullish" if highs[-1] >= highs[0] else "Bearish"
    
    return make_result("Rectangle", bias, p, resistance if bias=="Bullish" else support, support*0.999 if bias=="Bullish" else resistance*1.001, resistance+height if bias=="Bullish" else support-height, 100)

def detect_bull_flag(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    pole = h1 - l1
    if pole <= 0: return None
    if not (h2 < h1 and l3 < l2): return None
    return make_result("Bull Flag", "Bullish", p, h2, l3 * 0.999, h2 + pole, 100)

def detect_bear_flag(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    pole = h1 - l1
    if pole <= 0: return None
    if not (l2 > l1 and h3 > h2): return None
    return make_result("Bear Flag", "Bearish", p, l2, h3 * 1.001, l2 - pole, 100)

def detect_pennant(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if not recent_pattern(p, current_pos): return None
    
    if [x["type"] for x in p] == ["L", "H", "L", "H", "L"]:
        l1, h1, l2, h2, l3 = [x["val"] for x in p]
        pole = h1 - l1
        if pole > 0 and h2 < h1 and l2 > l1 and l3 > l2:
            return make_result("Pennant", "Bullish", p, h2, l3 * 0.999, h2 + pole, 100)
            
    if [x["type"] for x in p] == ["H", "L", "H", "L", "H"]:
        h1, l1, h2, l2, h3 = [x["val"] for x in p]
        pole = h1 - l1
        if pole > 0 and l2 > l1 and h2 < h1 and h3 < h2:
            return make_result("Pennant", "Bearish", p, l2, h3 * 1.001, l2 - pole, 100)
    return None

# ==========================================================
# SECTION C: BILATERAL / WEDGES PATTERNS
# ==========================================================

def detect_ascending_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    # شرط صارم: مقاومة أفقية ثابتة + قيعان صاعدة حصراً
    if not equal_within_1_percent(h1, h2): return None
    if not (l2 > l1 and l3 > l2): return None
    
    resistance = max(h1, h2)
    support_min = min(l1, l2, l3)
    height = resistance - support_min
    return make_result("Ascending Triangle", "Bullish", p, resistance, support_min * 0.999, resistance + height, 100)

def detect_descending_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    # شرط صارم: دعم أفقية ثابتة + قمم هابطة حصراً
    if not equal_within_1_percent(l1, l2): return None
    if not (h2 < h1 and h3 < h2): return None
    
    support = min(l1, l2)
    resistance_max = max(h1, h2, h3)
    height = resistance_max - support
    return make_result("Descending Triangle", "Bearish", p, support, resistance_max * 1.001, support - height, 100)

def detect_symmetrical_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    if not (h2 < h1 and h3 < h2 and l2 > l1): return None
    return make_result("Symmetrical Triangle", "Neutral", p, h3, h1 * 1.001, l1, 100)

def detect_rising_wedge(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    if not (l2 > l1 and l3 > l2 and h2 > h1): return None
    
    upper_slope = (h2 - h1) / max(p[3]["pos"] - p[1]["pos"], 1)
    lower_slope = (l3 - l1) / max(p[4]["pos"] - p[0]["pos"], 1)
    if lower_slope <= upper_slope: return None
    
    pattern_height = max(h1, h2) - min(l1, l2, l3)
    return make_result("Rising Wedge", "Bearish", p, l3, max(h1, h2) * 1.001, l3 - pattern_height, 100)

def detect_falling_wedge(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    if not (h2 < h1 and h3 < h2 and l2 < l1): return None
    
    pattern_height = max(h1, h2, h3) - min(l1, l2)
    return make_result("Falling Wedge", "Bullish", p, h3, min(l1, l2) * 0.999, h3 + pattern_height, 100)

# ==========================================================
# 4. MASTER SCANNER & CONFIRMATION
# ==========================================================

def scan_and_calculate_logic(df):
    pivots = get_chronological_pivots(df)
    if len(pivots) < 3:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    current_pos = len(df) - 1
    detectors = [
        detect_head_shoulders, detect_inverse_head_shoulders,
        detect_double_top, detect_double_bottom,
        detect_ascending_triangle, detect_descending_triangle,
        detect_symmetrical_triangle, detect_rising_wedge,
        detect_falling_wedge, detect_rectangle,
        detect_bull_flag, detect_bear_flag, detect_pennant
    ]

    candidates = []
    for detector in detectors:
        try:
            res = detector(pivots, current_pos)
            if res is not None:
                candidates.append(res)
        except Exception:
            continue

    if not candidates:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    candidates.sort(key=lambda x: x["nodes"][-1][0])
    return candidates[-1]

def confirm_pattern(df, p_data):
    latest_closed = df.iloc[-2]
    close = float(latest_closed["Close"])
    ema50 = float(latest_closed["EMA50"])
    ema200 = float(latest_closed["EMA200"])
    rsi = float(latest_closed["RSI"])
    bias = p_data["bias"]
    trigger = p_data["entry_trigger"]
    reasons = []

    if bias == "Neutral":
        return ("WAITING", "Waiting for directional breakout.", close)

    if bias == "Bullish":
        if close <= trigger: reasons.append("Waiting for bullish breakout")
        if close <= ema50: reasons.append("Price below EMA50")
        if close <= ema200: reasons.append("Price below EMA200")
        if not (30 <= rsi <= 75): reasons.append("RSI out of 30-75 range")
        if not reasons:
            return ("STRONG BUY", "Bullish pattern confirmed with indicators.", close)

    if bias == "Bearish":
        if close >= trigger: reasons.append("Waiting for bearish breakout")
        if close >= ema50: reasons.append("Price above EMA50")
        if close >= ema200: reasons.append("Price above EMA200")
        if not (30 <= rsi <= 75): reasons.append("RSI out of 30-75 range")
        if not reasons:
            return ("STRONG SELL", "Bearish pattern confirmed with indicators.", close)

    return ("WAITING", " | ".join(reasons), close)

def build_analysis_text(pattern, bias, signal, reason, match_pct):
    if pattern == "NO PATTERN DETECTED":
        return "Pattern Analysis: No active pattern detected. Decision: WAIT."
    decision = "BUY" if signal == "STRONG BUY" else "SELL" if signal == "STRONG SELL" else "WAIT"
    return f"Pattern Analysis: {pattern} ({match_pct:.0f}% match). Bias: {bias}. Decision: {decision}. Reason: {reason}."

def run_full_analysis(df):
    df = calculate_indicators(df)
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)
    p_data = scan_and_calculate_logic(df)

    if p_data["name"] == "NO PATTERN DETECTED":
        return {
            "df": df, "pattern": "NO PATTERN DETECTED", "bias": "Neutral", "match_pct": 0,
            "signal": "WAITING", "reason": "No active recent pattern found.",
            "analysis_text": build_analysis_text("NO PATTERN DETECTED", "Neutral", "WAITING", "No pattern", 0),
            "entry": 0, "sl": 0, "tp": 0, "trigger": 0, "nodes": []
        }

    signal, reason, close = confirm_pattern(df, p_data)
    analysis_text = build_analysis_text(p_data["name"], p_data["bias"], signal, reason, p_data["match"])

    return {
        "df": df,
        "pattern": p_data["name"],
        "bias": p_data["bias"],
        "match_pct": round(p_data["match"], 2),
        "signal": signal,
        "reason": reason,
        "analysis_text": analysis_text,
        "entry": round(close, 4),
        "sl": round(p_data["sl"], 4),
        "tp": round(p_data["tp"], 4),
        "trigger": round(p_data["entry_trigger"], 4),
        "nodes": p_data["nodes"],
        "neckline_start_idx": p_data.get("neckline_start_idx", p_data["nodes"][0][0])
    }
    
