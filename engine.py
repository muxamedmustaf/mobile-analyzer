import pandas as pd
import numpy as np
import math

MAX_PATTERN_AGE = 25
MAX_VARIATION = 0.0015

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
        l# ==========================================================
# ZIGZAG - STRICT MAJOR SWING DETECTION
# ==========================================================

MIN_SWING_PERCENT = 0.005   # 0.5% minimum movement


def calculate_zigzag(df, depth=7, deviation=5, backstep=3):
    df = df.copy()

    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].astype(float).values
    lows = df["Low"].astype(float).values

    n = len(df)

    for i in range(depth, n - backstep):

        high_window = highs[i-depth:i+backstep+1]
        low_window = lows[i-depth:i+backstep+1]

        current_high = highs[i]
        current_low = lows[i]

        is_high = (
            current_high == np.max(high_window)
            and np.sum(high_window == current_high) == 1
        )

        is_low = (
            current_low == np.min(low_window)
            and np.sum(low_window == current_low) == 1
        )

        # يمنع اعتبار نفس الشمعة قمة وقاعاً معاً
        if is_high and not is_low:

            df.iloc[
                i,
                df.columns.get_loc("Pivot_H")
            ] = current_high

        elif is_low and not is_high:

            df.iloc[
                i,
                df.columns.get_loc("Pivot_L")
            ] = current_low

    return df


# ==========================================================
# CHRONOLOGICAL PIVOTS + MAJOR SWING FILTER
# ==========================================================

def get_chronological_pivots(df):

    raw_pivots = []

    for pos, (idx, row) in enumerate(df.iterrows()):

        if not pd.isna(row["Pivot_H"]):

            raw_pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_H"]),
                "type": "H"
            })

        elif not pd.isna(row["Pivot_L"]):

            raw_pivots.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_L"]),
                "type": "L"
            })

    # ======================================================
    # 1. STRICT H/L ALTERNATION
    # ======================================================

    clean = []

    for p in raw_pivots:

        if not clean:
            clean.append(p)
            continue

        last = clean[-1]

        # حركة عكسية = موجة جديدة
        if last["type"] != p["type"]:

            clean.append(p)
            continue

        # قمتان متتاليتان -> نأخذ الأعلى
        if p["type"] == "H":

            if p["val"] > last["val"]:
                clean[-1] = p

        # قاعان متتاليان -> نأخذ الأدنى
        elif p["type"] == "L":

            if p["val"] < last["val"]:
                clean[-1] = p

    # ======================================================
    # 2. MAJOR SWING FILTER
    # ======================================================

    major = []

    for p in clean:

        if not major:
            major.append(p)
            continue

        last = major[-1]

        movement = abs(
            p["val"] - last["val"]
        ) / max(
            abs(last["val"]),
            1e-9
        )

        # ----------------------------------------------
        # إذا كانت الحركة صغيرة جداً
        # لا تعتبر موجة رئيسية
        # ----------------------------------------------

        if movement < MIN_SWING_PERCENT:

            # إذا كانت نفس النوع نحتفظ بالأقوى
            if p["type"] == last["type"]:

                if p["type"] == "H":
                    if p["val"] > last["val"]:
                        major[-1] = p

                else:
                    if p["val"] < last["val"]:
                        major[-1] = p

            continue

        # ----------------------------------------------
        # حركة رئيسية جديدة
        # ----------------------------------------------

        major.append(p)

    return major

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
    # ==========================================================
# 5. PATTERN DETECTION ENGINE
# 15 PATTERNS - INDIVIDUAL STRUCTURAL RULES
# ==========================================================


# ==========================================================
# COMMON PATTERN GEOMETRY HELPERS
# ==========================================================

def _same(a, b, tolerance=MAX_VARIATION):
    return variation(a, b) <= tolerance


def _slope(p1, p2):
    dx = p2["pos"] - p1["pos"]
    if dx == 0:
        return 0.0
    return (p2["val"] - p1["val"]) / dx


def _range_height(high, low):
    return abs(high - low)


def _valid_depth(start, extreme, correction):
    return valid_correction(
        start,
        extreme,
        correction
    )


def _converging(p):
    upper_1 = p[1]["val"]
    upper_2 = p[3]["val"]

    lower_1 = p[0]["val"]
    lower_2 = p[2]["val"]

    first_range = abs(
        upper_1 - lower_1
    )

    second_range = abs(
        upper_2 - lower_2
    )

    return (
        first_range > 0
        and second_range > 0
        and second_range < first_range
    )


def _recent(p, current_pos):
    return recent_pattern(
        p,
        current_pos
    )


def _support_close(a, b):
    return variation(a, b) <= MAX_VARIATION


def _previous_bullish_structure(
    pivots,
    start_index
):
    if start_index < 1:
        return True

    prev = pivots[
        max(0, start_index - 2):
        start_index
    ]

    if len(prev) < 2:
        return True

    return prev[-1]["val"] > prev[0]["val"]


def _previous_bearish_structure(
    pivots,
    start_index
):
    if start_index < 1:
        return True

    prev = pivots[
        max(0, start_index - 2):
        start_index
    ]

    if len(prev) < 2:
        return True

    return prev[-1]["val"] < prev[0]["val"]


# ==========================================================
# 6. HEAD AND SHOULDERS
# ==========================================================

def detect_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    for i in range(
        max(0, len(pivots) - 7),
        len(pivots) - 4
    ):

        p = pivots[i:i + 5]

        if [x["type"] for x in p] != [
            "H", "L", "H", "L", "H"
        ]:
            continue

        if not _recent(
            p,
            current_pos
        ):
            continue

        h1, l1, h2, l2, h3 = [
            x["val"] for x in p
        ]

        # Previous trend must be bullish
        if not _previous_bullish_structure(
            pivots,
            i
        ):
            continue

        # Left shoulder wave
        left_wave = h1 - l1

        if left_wave <= 0:
            continue

        # Left correction >= 20%
        if not _valid_depth(
            l1,
            h1,
            l1
        ):
            continue

        # Head must clearly break left shoulder
        if h2 <= h1:
            continue

        if variation(
            h2,
            h1
        ) <= 0:
            continue

        # Second correction must return
        # to first support within 1%
        if not _support_close(
            l1,
            l2
        ):
            continue

        # Second correction must be meaningful
        if not _valid_depth(
            h1,
            h2,
            l2
        ):
            continue

        # Right shoulder below head
        if h3 >= h2:
            continue

        # Shoulders must match within 1%
        if not _same(
            h1,
            h3
        ):
            continue

        # Corresponding shoulder waves
        right_wave = h3 - l2

        if not _same(
            left_wave,
            right_wave
        ):
            continue

        # Corresponding corrections
        left_correction = h1 - l1
        right_correction = h2 - l2

        if not _same(
            left_correction,
            right_correction
        ):
            continue

        # Neckline
        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:
            neckline = (
                l1 + l2
            ) / 2
        else:
            slope = (
                l2 - l1
            ) / (
                x2 - x1
            )

            neckline = (
                l2
                + slope
                * (
                    current_pos - x2
                )
            )

        height = h2 - neckline

        if height <= 0:
            continue

        return make_result(
            "Head and Shoulders",
            "Bearish",
            p,
            neckline,
            h3 * 1.001,
            neckline - height,
            100
        )

    return None


# ==========================================================
# 7. INVERSE HEAD AND SHOULDERS
# ==========================================================

def detect_inverse_head_shoulders(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    for i in range(
        max(0, len(pivots) - 7),
        len(pivots) - 4
    ):

        p = pivots[i:i + 5]

        if [x["type"] for x in p] != [
            "L", "H", "L", "H", "L"
        ]:
            continue

        if not _recent(
            p,
            current_pos
        ):
            continue

        l1, h1, l2, h2, l3 = [
            x["val"] for x in p
        ]

        # Previous trend bearish
        if not _previous_bearish_structure(
            pivots,
            i
        ):
            continue

        # Head must be lower
        if not (
            l2 < l1
            and l2 < l3
        ):
            continue

        # Shoulders equal
        if not _same(
            l1,
            l3
        ):
            continue

        # Left and right corresponding waves
        left_wave = h1 - l1
        right_wave = h2 - l3

        if left_wave <= 0:
            continue

        if not _same(
            left_wave,
            right_wave
        ):
            continue

        # Corresponding corrections
        left_correction = h1 - l1
        right_correction = h2 - l2

        if not _same(
            left_correction,
            right_correction
        ):
            continue

        # Neckline
        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:
            neckline = (
                h1 + h2
            ) / 2
        else:
            slope = (
                h2 - h1
            ) / (
                x2 - x1
            )

            neckline = (
                h2
                + slope
                * (
                    current_pos - x2
                )
            )

        height = neckline - l2

        if height <= 0:
            continue

        return make_result(
            "Inverse Head and Shoulders",
            "Bullish",
            p,
            neckline,
            l3 * 0.999,
            neckline + height,
            100
        )

    return None


# ==========================================================
# 8. DOUBLE TOP
# ==========================================================

def detect_double_top(
    pivots,
    current_pos
):

    if len(pivots) < 3:
        return None

    p = pivots[-3:]

    if [x["type"] for x in p] != [
        "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2 = [
        x["val"] for x in p
    ]

    # Tops must match within 1%
    if not _same(
        h1,
        h2
    ):
        return None

    correction = h1 - l1

    # Correction must be >= 20%
    if correction <= 0:
        return None

    if not _valid_depth(
        l1,
        h1,
        l1
    ):
        return None

    return make_result(
        "Double Top",
        "Bearish",
        p,
        l1,
        max(h1, h2) * 1.001,
        l1 - correction,
        100
    )


# ==========================================================
# 9. DOUBLE BOTTOM
# ==========================================================

def detect_double_bottom(
    pivots,
    current_pos
):

    if len(pivots) < 3:
        return None

    p = pivots[-3:]

    if [x["type"] for x in p] != [
        "L", "H", "L"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    l1, h1, l2 = [
        x["val"] for x in p
    ]

    # Bottoms must match within 1%
    if not _same(
        l1,
        l2
    ):
        return None

    correction = h1 - l1

    if correction <= 0:
        return None

    if not _valid_depth(
        l1,
        h1,
        h1
    ):
        return None

    return make_result(
        "Double Bottom",
        "Bullish",
        p,
        h1,
        min(l1, l2) * 0.999,
        h1 + correction,
        100
    )


# ==========================================================
# 10. TRIPLE TOP
# ==========================================================

def detect_triple_top(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H", "L", "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    # All three tops must match
    if not (
        _same(h1, h2)
        and _same(h2, h3)
    ):
        return None

    # Both corrections meaningful
    if not (
        _valid_depth(h1, h2, l1)
        and _valid_depth(h2, h3, l2)
    ):
        return None

    # Corresponding corrections
    c1 = h1 - l1
    c2 = h2 - l2

    if not _same(
        c1,
        c2
    ):
        return None

    neckline = min(
        l1,
        l2
    )

    height = (
        max(h1, h2, h3)
        - neckline
    )

    return make_result(
        "Triple Top",
        "Bearish",
        p,
        neckline,
        max(h1, h2, h3) * 1.001,
        neckline - height,
        100
    )


# ==========================================================
# 11. TRIPLE BOTTOM
# ==========================================================

def detect_triple_bottom(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L", "H", "L", "H", "L"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    # All bottoms equal
    if not (
        _same(l1, l2)
        and _same(l2, l3)
    ):
        return None

    # Corrections
    c1 = h1 - l1
    c2 = h2 - l2

    if not (
        c1 > 0
        and c2 > 0
    ):
        return None

    if not _same(
        c1,
        c2
    ):
        return None

    neckline = max(
        h1,
        h2
    )

    height = (
        neckline
        - min(l1, l2, l3)
    )

    return make_result(
        "Triple Bottom",
        "Bullish",
        p,
        neckline,
        min(l1, l2, l3) * 0.999,
        neckline + height,
        100
    )


# ==========================================================
# 12. ASCENDING TRIANGLE
# ==========================================================

def detect_ascending_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L", "H", "L", "H", "L"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    # Flat resistance
    if not _same(
        h1,
        h2
    ):
        return None

    # Rising supports
    if not (
        l2 > l1
        and l3 > l2
    ):
        return None

    # Range must contract
    first_range = h1 - l1
    last_range = h2 - l3

    if last_range >= first_range:
        return None

    neckline = max(
        h1,
        h2
    )

    height = (
        neckline
        - min(l1, l2, l3)
    )

    return make_result(
        "Ascending Triangle",
        "Bullish",
        p,
        neckline,
        min(l1, l2, l3) * 0.999,
        neckline + height,
        100
    )


# ==========================================================
# 13. DESCENDING TRIANGLE
# ==========================================================

def detect_descending_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H", "L", "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    # Flat support
    if not _same(
        l1,
        l2
    ):
        return None

    # Lower highs
    if not (
        h2 < h1
        and h3 < h2
    ):
        return None

    first_range = h1 - l1
    last_range = h3 - l2

    if last_range >= first_range:
        return None

    neckline = min(
        l1,
        l2
    )

    height = (
        max(h1, h2, h3)
        - neckline
    )

    return make_result(
        "Descending Triangle",
        "Bearish",
        p,
        neckline,
        max(h1, h2, h3) * 1.001,
        neckline - height,
        100
    )


# ==========================================================
# 14. SYMMETRICAL TRIANGLE
# ==========================================================

def detect_symmetrical_triangle(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H", "L", "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    # Lower highs
    if not (
        h2 < h1
        and h3 < h2
    ):
        return None

    # Higher lows
    if not (
        l2 > l1
    ):
        return None

    # Contraction
    first_range = h1 - l1
    second_range = h3 - l2

    if second_range >= first_range:
        return None

    # Both sides must converge
    upper_slope = _slope(
        p[0],
        p[2]
    )

    lower_slope = _slope(
        p[1],
        p[3]
    )

    if not (
        upper_slope < 0
        and lower_slope > 0
    ):
        return None

    return make_result(
        "Symmetrical Triangle",
        "Neutral",
        p,
        h3,
        h1 * 1.001,
        l1,
        100
    )


# ==========================================================
# 15. RISING WEDGE
# ==========================================================

def detect_rising_wedge(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L", "H", "L", "H", "L"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    # Both highs and lows rise
    if not (
        h2 > h1
        and l2 > l1
        and l3 > l2
    ):
        return None

    upper_slope = (
        h2 - h1
    ) / max(
        p[3]["pos"] - p[1]["pos"],
        1
    )

    lower_slope = (
        l3 - l1
    ) / max(
        p[4]["pos"] - p[0]["pos"],
        1
    )

    # Rising but converging
    if not (
        upper_slope > 0
        and lower_slope > 0
        and lower_slope < upper_slope
    ):
        return None

    first_range = h1 - l1
    last_range = h2 - l3

    if last_range >= first_range:
        return None

    return make_result(
        "Rising Wedge",
        "Bearish",
        p,
        l3,
        max(h1, h2) * 1.001,
        l3 - (
            max(h1, h2)
            - min(l1, l2, l3)
        ),
        100
    )


# ==========================================================
# 16. FALLING WEDGE
# ==========================================================

def detect_falling_wedge(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H", "L", "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    # Lower highs and lower lows
    if not (
        h2 < h1
        and h3 < h2
        and l2 < l1
    ):
        return None

    upper_slope = (
        h3 - h1
    ) / max(
        p[4]["pos"] - p[0]["pos"],
        1
    )

    lower_slope = (
        l2 - l1
    ) / max(
        p[3]["pos"] - p[1]["pos"],
        1
    )

    # Both lines descend
    if not (
        upper_slope < 0
        and lower_slope < 0
    ):
        return None

    # Convergence
    first_range = h1 - l1
    last_range = h3 - l2

    if last_range >= first_range:
        return None

    return make_result(
        "Falling Wedge",
        "Bullish",
        p,
        h3,
        min(l1, l2) * 0.999,
        h3 + (
            max(h1, h2, h3)
            - min(l1, l2)
        ),
        100
    )


# ==========================================================
# 17. RECTANGLE
# ==========================================================

def detect_rectangle(
    pivots,
    current_pos
):

    if len(pivots) < 6:
        return None

    p = pivots[-6:]

    if not _recent(
        p,
        current_pos
    ):
        return None

    highs = [
        x for x in p
        if x["type"] == "H"
    ]

    lows = [
        x for x in p
        if x["type"] == "L"
    ]

    if len(highs) < 3:
        return None

    if len(lows) < 3:
        return None

    # Resistance remains flat
    if not (
        _same(
            highs[0]["val"],
            highs[-1]["val"]
        )
    ):
        return None

    # Support remains flat
    if not (
        _same(
            lows[0]["val"],
            lows[-1]["val"]
        )
    ):
        return None

    resistance = max(
        x["val"] for x in highs
    )

    support = min(
        x["val"] for x in lows
    )

    if resistance <= support:
        return None

    return make_result(
        "Rectangle",
        "Neutral",
        p,
        resistance,
        resistance * 1.001,
        support,
        100
    )


# ==========================================================
# 18. BULL FLAG
# ==========================================================

def detect_bull_flag(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "L", "H", "L", "H", "L"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    l1, h1, l2, h2, l3 = [
        x["val"] for x in p
    ]

    # Strong bullish pole
    pole = h1 - l1

    if pole <= 0:
        return None

    # Flag correction
    correction = h1 - l3

    if correction <= 0:
        return None

    # Correction must not consume the pole
    if correction >= pole:
        return None

    # Flag slopes downward
    if not (
        h2 < h1
        and l3 < l2
    ):
        return None

    # Corresponding correction must be meaningful
    if correction / pole < MIN_CORRECTION:
        return None

    return make_result(
        "Bull Flag",
        "Bullish",
        p,
        h2,
        l3 * 0.999,
        h2 + pole,
        100
    )


# ==========================================================
# 19. BEAR FLAG
# ==========================================================

def detect_bear_flag(
    pivots,
    current_pos
):

    if len(pivots) < 5:
        return None

    p = pivots[-5:]

    if [x["type"] for x in p] != [
        "H", "L", "H", "L", "H"
    ]:
        return None

    if not _recent(
        p,
        current_pos
    ):
        return None

    h1, l1, h2, l2, h3 = [
        x["val"] for x in p
    ]

    # Strong beari
