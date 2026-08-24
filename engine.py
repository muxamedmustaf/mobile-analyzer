import pandas as pd
import numpy as np
import math

MAX_PATTERN_AGE = 50
MAX_VARIATION = 0.10

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

def calculate_zigzag(df, depth=7, deviation=5, backstep=3):
def calculate_zigzag(df, depth=7, deviation=5, backstep=3):
    df = df.copy()
    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan
    highs = df["High"].values
    lows = df["Low"].values

    # تقليص نطاق الحلقة لضمان وجود شموع كافية يميناً ويساراً للمقارنة
    for i in range(depth, len(df) - backstep):
        # النقطة يجب أن تكون الأعلى/الأدنى مقارنة بالشموع السابقة (depth) واللاحقة (backstep)
        window_high = np.max(highs[i - depth : i + backstep + 1])
        window_low = np.min(lows[i - depth : i + backstep + 1])

        # تعيين القمة الصارمة
        if highs[i] == window_high:
            df.iloc[i, df.columns.get_loc("Pivot_H")] = highs[i]

        # تعيين القاع الصارم
        if lows[i] == window_low:
            df.iloc[i, df.columns.get_loc("Pivot_L")] = lows[i]

    return df


def get_chronological_pivots(df):
    pivots = []
    for pos, (idx, row) in enumerate(df.iterrows()):
        # فصل الشروط لضمان التقاط جميع النقاط المتطرفة
        if not pd.isna(row["Pivot_H"]):
            pivots.append({"idx": idx, "pos": pos, "val": float(row["Pivot_H"]), "type": "H"})
        if not pd.isna(row["Pivot_L"]):
            pivots.append({"idx": idx, "pos": pos, "val": float(row["Pivot_L"]), "type": "L"})

    clean = []
    for p in pivots:
        if not clean:
            clean.append(p)
            continue
        last = clean[-1]
        
        # التناوب الصارم: إذا تتابعت قمتان، نأخذ الأعلى، وإذا تتابع قاعان نأخذ الأدنى
        if last["type"] != p["type"]:
            clean.append(p)
        elif p["type"] == "H":
            if p["val"] > last["val"]:
                clean[-1] = p
        elif p["type"] == "L":
            if p["val"] < last["val"]:
                clean[-1] = p
                
    return clean

def calculate_slope(y2, y1, x2, x1):
    dx = x2 - x1
    if dx == 0:
        return 0.0
    return (y2 - y1) / float(dx)

def variation(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)

def equal_tolerance(a, b, tol=MAX_VARIATION):
    return variation(a, b) <= tol

def recent_pattern(points, current_pos, max_age=MAX_PATTERN_AGE):
    return (current_pos - points[-1]["pos"] <= max_age) if points else False

def make_result(name, bias, points, entry, sl, tp, score=100):
    return {
        "name": name,
        "bias": bias,
        "match": float(score),
        "nodes": [(p["idx"], p["val"]) for p in points],
        "entry_trigger": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "neckline_start_idx": points[1]["idx"] if len(points) > 1 else points[0]["idx"]
    }

def build_top_banner_text(pattern_name, bias, signal, reason, match_pct, current_price, trigger, rsi_val):
    if pattern_name == "NO PATTERN DETECTED":
        line1 = "النمط السعري: لا يوجد نمط هندسي مكتمل حالياً | الحركة العامة: نطاق عرضي تذبذبي."
    else:
        line1 = f"النمط السعري: تشكّل {pattern_name} بنسبة تطابق {match_pct:.0f}% | الاتجاه المتوقع: {bias}."

    if signal in ["STRONG BUY", "STRONG SELL"]:
        line2 = f"الحالة الراهنة: السعر الحالي المغلق ({current_price:.4f}) أكد الاختراق للمستوى ({trigger:.4f}) | RSI: {rsi_val:.1f}."
    else:
        line2 = f"الحالة الراهنة: الزوج في وضع الانتظار بناءً على الشمعة المغلقة ({current_price:.4f}) | السبب: {reason}."

    return f"SIGNAL: {signal}\n{line1}\n{line2}"

def detect_double_top(pivots, current_pos):
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    
    h1, l1, h2 = [x["val"] for x in p]
    pattern_height = max(h1, h2) - l1
    if pattern_height <= 0: return None
    if abs(h1 - h2) > (pattern_height * 0.10): return None
    if not equal_tolerance(h1, h2, tol=0.003): return None
    
    return make_result("Double Top", "Bearish", p, l1, max(h1, h2) * 1.001, l1 - pattern_height)

def detect_double_bottom(pivots, current_pos):
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    
    l1, h1, l2 = [x["val"] for x in p]
    pattern_height = h1 - min(l1, l2)
    if pattern_height <= 0: return None
    if abs(l1 - l2) > (pattern_height * 0.10): return None
    if not equal_tolerance(l1, l2, tol=0.003): return None
    
    return make_result("Double Bottom", "Bullish", p, h1, min(l1, l2) * 0.999, h1 + pattern_height)

def detect_triple_top(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    height = max(h1, h2, h3) - min(l1, l2)
    if abs(h1 - h2) > height * 0.10 or abs(h2 - h3) > height * 0.10: return None
    if not (equal_tolerance(h1, h2, tol=0.003) and equal_tolerance(h2, h3, tol=0.003)): return None
    if not equal_tolerance(l1, l2, tol=0.005): return None
    
    neckline = min(l1, l2)
    return make_result("Triple Top", "Bearish", p, neckline, max(h1, h2, h3) * 1.001, neckline - height)

def detect_triple_bottom(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    height = max(h1, h2) - min(l1, l2, l3)
    if abs(l1 - l2) > height * 0.10 or abs(l2 - l3) > height * 0.10: return None
    if not (equal_tolerance(l1, l2, tol=0.003) and equal_tolerance(l2, l3, tol=0.003)): return None
    if not equal_tolerance(h1, h2, tol=0.005): return None
    
    neckline = max(h1, h2)
    return make_result("Triple Bottom", "Bullish", p, neckline, min(l1, l2, l3) * 0.999, neckline + height)

def detect_head_shoulders(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    neckline = max(l1, l2)
    pattern_height = h2 - neckline
    if pattern_height <= 0: return None
    if not (h2 > h1 and h2 > h3): return None
    if abs(h1 - h3) > (pattern_height * 0.15): return None
    
    return make_result("Head & Shoulders", "Bearish", p, l2, h2 * 1.001, l2 - pattern_height)

def detect_inverted_head_shoulders(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    neckline = min(h1, h2)
    pattern_height = neckline - l2
    if pattern_height <= 0: return None
    if not (l2 < l1 and l2 < l3): return None
    if abs(l1 - l3) > (pattern_height * 0.15): return None
    
    return make_result("Inverted H&S", "Bullish", p, h2, l2 * 0.999, h2 + pattern_height)

def detect_bearish_flag(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    pole = h1 - l1
    if pole <= 0: return None
    if not (l2 > l1 and h2 > h1 and h3 > h2): return None
    
    slope_H = calculate_slope(h3, h2, p[4]["pos"], p[2]["pos"])
    slope_L = calculate_slope(l2, l1, p[3]["pos"], p[1]["pos"])
    
    if slope_H <= 0 or slope_L <= 0: return None
    if variation(slope_H, slope_L) > 0.15: return None
    
    return make_result("Bearish Flag", "Bearish", p, l2, h3 * 1.001, l2 - pole)

def detect_bullish_flag(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    pole = h1 - l1
    if pole <= 0: return None
    if not (h2 < h1 and l2 < l1 and l3 < l2): return None
    
    slope_H = calculate_slope(h2, h1, p[3]["pos"], p[1]["pos"])
    slope_L = calculate_slope(l3, l2, p[4]["pos"], p[2]["pos"])
    
    if slope_H >= 0 or slope_L >= 0: return None
    if variation(slope_H, slope_L) > 0.15: return None
    
    return make_result("Bullish Flag", "Bullish", p, h2, l3 * 0.999, h2 + pole)

def detect_rising_wedge(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    if not (l2 > l1 and l3 > l2 and h2 > h1): return None
    
    slope_H = calculate_slope(h2, h1, p[3]["pos"], p[1]["pos"])
    slope_L = calculate_slope(l3, l1, p[4]["pos"], p[0]["pos"])
    
    if slope_H <= 0 or slope_L <= 0: return None
    if slope_L <= slope_H * 1.10: return None 
    
    height = max(h1, h2) - min(l1, l2, l3)
    return make_result("Rising Wedge", "Bearish", p, l3, max(h1, h2) * 1.001, l3 - height)

def detect_falling_wedge(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    if not (h2 < h1 and h3 < h2 and l2 < l1): return None
    
    slope_H = abs(calculate_slope(h3, h1, p[4]["pos"], p[0]["pos"]))
    slope_L = abs(calculate_slope(l2, l1, p[3]["pos"], p[1]["pos"]))
    
    if slope_H <= slope_L * 1.10: return None
    
    height = max(h1, h2) - min(l1, l2)
    return make_result("Falling Wedge", "Bullish", p, h3, min(l1, l2) * 0.999, h3 + height)

def detect_descending_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    if not equal_tolerance(l1, l2, tol=0.0025): return None
    if not (h1 > h2 > h3): return None
    
    height = h1 - l1
    return make_result("Descending Triangle", "Bearish", p, l2, h3 * 1.001, l2 - height)

def detect_ascending_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    if not equal_tolerance(h1, h2, tol=0.0025): return None
    if not (l2 > l1 and l3 > l2): return None
    
    height = h2 - l1
    return make_result("Ascending Triangle", "Bullish", p, h2, l3 * 0.999, h2 + height)

def detect_symmetrical_triangle(pivots, current_pos):
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if not recent_pattern(p, current_pos): return None
    if [x["type"] for x in p] == ["H", "L", "H", "L", "H"]:
        h1, l1, h2, l2, h3 = [x["val"] for x in p]
        if (h2 < h1 and h3 < h2) and (l2 > l1):
            return make_result("Symmetrical Triangle", "Bearish", p, l2, h3 * 1.001, l2 - (h1 - l1))
    if [x["type"] for x in p] == ["L", "H", "L", "H", "L"]:
        l1, h1, l2, h2, l3 = [x["val"] for x in p]
        if (l2 > l1 and l3 > l2) and (h2 < h1):
            return make_result("Symmetrical Triangle", "Bullish", p, h2, l3 * 0.999, h2 + (h1 - l1))
    return None

def scan_and_calculate_logic(df):
    pivots = get_chronological_pivots(df)
    if len(pivots) < 3:
        return {"name": "NO PATTERN DETECTED", "bias": "Neutral", "match": 0}

    current_pos = len(df) - 1
    detectors = [
        detect_descending_triangle, detect_ascending_triangle,
        detect_head_shoulders, detect_inverted_head_shoulders,
        detect_bearish_flag, detect_bullish_flag,
        detect_rising_wedge, detect_falling_wedge,
        detect_double_top, detect_double_bottom,
        detect_triple_top, detect_triple_bottom,
        detect_symmetrical_triangle
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
        return ("WAITING", "بانتظار اختراق واضح للاتجاه.", close, rsi)

    if bias == "Bullish":
        if close <= trigger: reasons.append("السعر لم يخترق المقاومة بعد")
        if close <= ema50: reasons.append("السعر أدنى من EMA50")
        if close <= ema200: reasons.append("السعر أدنى من EMA200")
        if not (30 <= rsi <= 75): reasons.append("RSI خارج النطاق المقبول")
        
        if not reasons:
            return ("STRONG BUY", "تأكيد النمط الصاعد مع المؤشرات", close, rsi)

    if bias == "Bearish":
        if close >= trigger: reasons.append("السعر لم يكسر الدعم بعد")
        if close >= ema50: reasons.append("السعر أعلى من EMA50")
        if close >= ema200: reasons.append("السعر أعلى من EMA200")
        if not (30 <= rsi <= 75): reasons.append("RSI خارج النطاق المقبول")
        
        if not reasons:
            return ("STRONG SELL", "تأكيد النمط الهابط مع المؤشرات", close, rsi)

    return ("WAITING", " | ".join(reasons), close, rsi)

def run_full_analysis(df):
    df = calculate_indicators(df)
    df = calculate_zigzag(df, depth=12, deviation=5, backstep=3)
    p_data = scan_and_calculate_logic(df)

    if p_data["name"] == "NO PATTERN DETECTED":
        latest_closed = df.iloc[-2]
        close = float(latest_closed["Close"])
        rsi = float(latest_closed["RSI"])
        banner = build_top_banner_text("NO PATTERN DETECTED", "Neutral", "WAITING", "لا توجد حركة هندسية حديثة", 0, close, 0, rsi)
        return {
            "df": df, "pattern": "NO PATTERN DETECTED", "bias": "Neutral", "match_pct": 0,
            "signal": "WAITING", "top_banner_text": banner,
            "entry": 0, "sl": 0, "tp": 0, "trigger": 0, "nodes": []
        }

    signal, reason, close_price, rsi_val = confirm_pattern(df, p_data)
    
    banner = build_top_banner_text(
        pattern_name=p_data["name"],
        bias=p_data["bias"],
        signal=signal,
        reason=reason,
        match_pct=p_data["match"],
        current_price=close_price,
        trigger=p_data["entry_trigger"],
        rsi_val=rsi_val
    )

    return {
        "df": df,
        "pattern": p_data["name"],
        "bias": p_data["bias"],
        "match_pct": round(p_data["match"], 2),
        "signal": signal,
        "top_banner_text": banner,
        "entry": round(close_price, 4),
        "sl": round(p_data["sl"], 4),
        "tp": round(p_data["tp"], 4),
        "trigger": round(p_data["entry_trigger"], 4),
        "nodes": p_data["nodes"],
        "neckline_start_idx": p_data.get("neckline_start_idx", p_data["nodes"][0][0])
        }
            
