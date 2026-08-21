import math

# ==============================================================================
# HELPERS & GEOMETRY UTILITIES
# ==============================================================================

def calculate_slope(y2, y1, x2, x1):
    """حساب ميل الخط الهندسي بين نقطتين مع حماية من القسمة على صفر."""
    dx = x2 - x1
    if dx == 0:
        return 0.0
    return (y2 - y1) / float(dx)

def variation(val1, val2):
    """حساب نسبة التباين المطلق بين قيمتين."""
    denom = max(abs(val1), abs(val2), 1e-9)
    return abs(val1 - val2) / denom

def equal_tolerance(a, b, tol=0.002):
    """التحقق من التساوي ضمن نسبة تسامح محددة."""
    denom = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / denom <= tol

def recent_pattern(pivots, current_pos, max_distance=50):
    """تأكيد أن النمط حديث وقريب من الشمعة الحالية."""
    if not pivots:
        return False
    return (current_pos - pivots[-1]["pos"]) <= max_distance

def make_result(pattern_name, bias, pivots, trigger_price, stop_loss, target_price):
    """صياغة النتيجة النهائية للنموذج."""
    return {
        "pattern": pattern_name,
        "bias": bias,
        "pivots": pivots,
        "entry": round(trigger_price, 5),
        "sl": round(stop_loss, 5),
        "tp": round(target_price, 5)
    }

# ==============================================================================
# STRICT PATTERN DETECTION CATALOG (100% IDEAL RATIOS)
# ==============================================================================

def detect_double_top(pivots, current_pos):
    """القمة المزدوجة - الفارق بين القمتين يجب ألا يتجاوز 10% من عمق النموذج."""
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    
    h1, l1, h2 = p[0]["val"], p[1]["val"], p[2]["val"]
    pattern_height = max(h1, h2) - l1
    if pattern_height <= 0: return None
    
    if abs(h1 - h2) > (pattern_height * 0.10): return None
    if not equal_tolerance(h1, h2, tol=0.003): return None
    
    return make_result("Double Top", "Bearish", p, l1, max(h1, h2) * 1.001, l1 - pattern_height)


def detect_double_bottom(pivots, current_pos):
    """القاع المزدوج - الفارق بين القاعين يجب ألا يتجاوز 10% من عمق النموذج."""
    if len(pivots) < 3: return None
    p = pivots[-3:]
    if [x["type"] for x in p] != ["L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    
    l1, h1, l2 = p[0]["val"], p[1]["val"], p[2]["val"]
    pattern_height = h1 - min(l1, l2)
    if pattern_height <= 0: return None
    
    if abs(l1 - l2) > (pattern_height * 0.10): return None
    if not equal_tolerance(l1, l2, tol=0.003): return None
    
    return make_result("Double Bottom", "Bullish", p, h1, min(l1, l2) * 0.999, h1 + pattern_height)


def detect_bullish_flag(pivots, current_pos):
    """العلم الصاعد - قناة هابطة متوازية بدقة (تفاوت الميل لا يتجاوز 15%)."""
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


def detect_bearish_flag(pivots, current_pos):
    """العلم الهابط - قناة صاعدة متوازية بدقة (تفاوت الميل لا يتجاوز 15%)."""
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


def detect_rising_wedge(pivots, current_pos):
    """الوتد الصاعد - خطوط صاعدة مخروطية (ميل الدعم أسرع من ميل المقاومة بـ 10% على الأقل)."""
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
    """الوتد الهابط - خطوط هابطة مخروطية (شدة انحدار المقاومة أكبر من الدعم بـ 10% على الأقل)."""
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


def detect_head_and_shoulders(pivots, current_pos):
    """الرأس والكتفان - الرأس أعلى من الكتفين، وتماثل الكتفين ضمن 15% من الارتفاع."""
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
    
    return make_result("Head and Shoulders", "Bearish", p, l2, h2 * 1.001, l2 - pattern_height)


def detect_inv_head_and_shoulders(pivots, current_pos):
    """الرأس والكتفان المعكوس - الرأس أدنى من الكتفين، وتماثل الكتفين ضمن 15%."""
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
    
    return make_result("Inverse Head and Shoulders", "Bullish", p, h2, l2 * 0.999, h2 + pattern_height)


def detect_ascending_triangle(pivots, current_pos):
    """المثلث الصاعد - خط مقاومة أفقية ومقاومة صاعدة."""
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L"]: return None
    if not recent_pattern(p, current_pos): return None
    
    l1, h1, l2, h2, l3 = [x["val"] for x in p]
    
    if not equal_tolerance(h1, h2, tol=0.0025): return None
    if not (l1 < l2 < l3): return None
    
    height = h2 - l1
    return make_result("Ascending Triangle", "Bullish", p, h2, l3 * 0.999, h2 + height)


def detect_descending_triangle(pivots, current_pos):
    """المثلث الهابط - خط دعم أفقي ومقاومة هابطة."""
    if len(pivots) < 5: return None
    p = pivots[-5:]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]: return None
    if not recent_pattern(p, current_pos): return None
    
    h1, l1, h2, l2, h3 = [x["val"] for x in p]
    
    if not equal_tolerance(l1, l2, tol=0.0025): return None
    if not (h1 > h2 > h3): return None
    
    height = h1 - l1
    return make_result("Descending Triangle", "Bearish", p, l2, h3 * 1.001, l2 - height)


def detect_symmetrical_triangle(pivots, current_pos):
    """المثلث المتماثل - قمم هابطة وقيعان صاعدة متلاقية."""
    if len(pivots) < 4: return None
    p = pivots[-4:]
    if [x["type"] for x in p] not in [["H", "L", "H", "L"], ["L", "H", "L", "H"]]: return None
    if not recent_pattern(p, current_pos): return None
    
    vals = [x["val"] for x in p]
    if p[0]["type"] == "H":
        h1, l1, h2, l2 = vals
    else:
        l1, h1, l2, h2 = vals
        
    if not (h1 > h2 and l1 < l2): return None
    
    height = h1 - l1
    return make_result("Symmetrical Triangle", "Neutral", p, h2, l2, h2 + height)


def detect_rectangle(pivots, current_pos):
    """المستطيل - قناة أفقية تماماً."""
    if len(pivots) < 4: return None
    p = pivots[-4:]
    if not recent_pattern(p, current_pos): return None
    
    if [x["type"] for x in p] == ["H", "L", "H", "L"]:
        h1, l1, h2, l2 = [x["val"] for x in p]
    elif [x["type"] for x in p] == ["L", "H", "L", "H"]:
        l1, h1, l2, h2 = [x["val"] for x in p]
    else:
        return None
        
    if not (equal_tolerance(h1, h2, tol=0.002) and equal_tolerance(l1, l2, tol=0.002)):
        return None
        
    height = max(h1, h2) - min(l1, l2)
    return make_result("Rectangle Pattern", "Neutral", p, max(h1, h2), min(l1, l2), max(h1, h2) + height)

# ==============================================================================
# MAIN SCANNER ENGINE
# ==============================================================================

PATTERN_DETECTORS = [
    detect_double_top,
    detect_double_bottom,
    detect_bullish_flag,
    detect_bearish_flag,
    detect_rising_wedge,
    detect_falling_wedge,
    detect_head_and_shoulders,
    detect_inv_head_and_shoulders,
    detect_ascending_triangle,
    detect_descending_triangle,
    detect_symmetrical_triangle,
    detect_rectangle
]

def scan_patterns(pivots, current_pos):
    """الدالة الرئيسية لمسح الأنماط وإعادة النتيجة فقط عند تطابق الشروط بنسبة 100%."""
    for detector in PATTERN_DETECTORS:
        result = detector(pivots, current_pos)
        if result is not None:
            return result
    return None
    
