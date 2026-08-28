import pandas as pd
import numpy as np

# ==========================================================
# ENGINE.PY - POST-HEAD INVALIDATION FILTER (v3.5)
# ==========================================================

MIN_SWING_PERCENT = 0.008
MIN_WAVE_CANDLES = 3

def calculate_indicators(df):
    df = df.copy()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()

    loss_safe = loss.replace(0, 1e-9)
    rs = gain / loss_safe

    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50.0)

    return df

def calculate_zigzag(df, depth=8, backstep=4):
    df = df.copy()
    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].astype(float).values
    lows = df["Low"].astype(float).values
    n = len(df)

    for i in range(depth, n - backstep):
        high_window = highs[i - depth:i + backstep + 1]
        low_window = lows[i - depth:i + backstep + 1]

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

        if is_high and not is_low:
            df.iloc[i, df.columns.get_loc("Pivot_H")] = current_high
        elif is_low and not is_high:
            df.iloc[i, df.columns.get_loc("Pivot_L")] = current_low

    return df

def get_chronological_pivots(df):
    raw = []
    for pos, (idx, row) in enumerate(df.iterrows()):
        if not pd.isna(row["Pivot_H"]):
            raw.append({"idx": idx, "pos": pos, "val": float(row["Pivot_H"]), "type": "H"})
        elif not pd.isna(row["Pivot_L"]):
            raw.append({"idx": idx, "pos": pos, "val": float(row["Pivot_L"]), "type": "L"})

    clean = []
    for p in raw:
        if not clean:
            clean.append(p)
            continue

        last = clean[-1]
        if last["type"] != p["type"]:
            movement = abs(p["val"] - last["val"]) / max(abs(last["val"]), 1e-9)
            if movement >= MIN_SWING_PERCENT:
                clean.append(p)
        elif p["type"] == "H" and p["val"] > last["val"]:
            clean[-1] = p
        elif p["type"] == "L" and p["val"] < last["val"]:
            clean[-1] = p

    return clean

def detect_all_head_shoulders(pivots, df):
    patterns = []
    if len(pivots) < 6:
        return patterns

    for i in range(len(pivots) - 5):
        p = pivots[i:i + 6]
        
        if [x["type"] for x in p] != ["L", "H", "L", "H", "L", "H"]:
            continue

        l0, h1, l1, h2, l2, h3 = [x["val"] for x in p]
        i_l0, i_h1, i_l1, i_h2, i_l2, i_h3 = [x["pos"] for x in p]
        idx_l0 = p[0]["idx"]
        idx_h2 = p[3]["idx"]  # مؤشر قمة الرأس
        idx_h3 = p[5]["idx"]

        # فلتر المسافة الزمنية
        if (i_h1 - i_l0 < MIN_WAVE_CANDLES) or \
           (i_l1 - i_h1 < MIN_WAVE_CANDLES) or \
           (i_h2 - i_l1 < MIN_WAVE_CANDLES) or \
           (i_l2 - i_h2 < MIN_WAVE_CANDLES) or \
           (i_h3 - i_l2 < MIN_WAVE_CANDLES):
            continue

        # فلتر الاتجاه السابق (يجب أن يكون في قمة وليست قاعاً هابطاً)
        pre_l0_df = df.loc[:idx_l0]
        if len(pre_l0_df) > 10:
            past_min = pre_l0_df['Low'].iloc[-10:].min()
            if past_min > l0:
                continue

        if h1 <= l0 or l1 <= l0: continue
        if h2 <= h1 or h2 <= h3: continue

        neckline_min = min(l1, l2)
        head_height = h2 - neckline_min
        if head_height <= 0: continue

        # هندسة الكتفين
        if abs(h1 - h3) > (head_height * 0.35): continue
        max_shoulder = max(h1, h3)
        if (h2 - max_shoulder) < (head_height * 0.25): continue
        if abs(l1 - l2) > (head_height * 0.25): continue

        # [إضافة حاسمة v3.5]: فلتر إلغاء النموذج إذا تجاوز السعر قمة الرأس لاحقاً
        post_head_df = df.loc[idx_h2:]
        if not post_head_df.empty:
            if post_head_df['High'].max() > h2:
                continue  # إلغاء النموذج فوراً لأنه تم اختراق الرأس لاحقاً

        neckline_avg = (l1 + l2) / 2.0
        actual_head_length = h2 - neckline_avg
        
        entry = neckline_avg
        sl = h2
        tp = entry - actual_head_length 
        
        # فلتر الكسر الإجباري لخط العنق بعد الكتف الأيمن
        post_h3_df = df.loc[idx_h3:]
        breakout_candles = post_h3_df[post_h3_df['Close'] < entry]
        
        if breakout_candles.empty:
            continue
            
        end_idx = breakout_candles.index[0]
        end_val = breakout_candles['Close'].iloc[0]

        nodes = [(x["idx"], x["val"]) for x in p]
        nodes.append((end_idx, float(end_val)))

        patterns.append({
            "name": "Head and Shoulders",
            "pattern": "Head and Shoulders",
            "bias": "Bearish",
            "match": 100.0,
            "nodes": nodes,
            "entry": float(round(entry, 5)),
            "entry_trigger": float(round(entry, 5)),
            "sl": float(round(sl, 5)),
            "tp": float(round(tp, 5)),
            "neckline_start_idx": p[2]["idx"],
            "neckline_end_idx": end_idx,
            "end_pos": p[5]["pos"]
        })

    return patterns

def run_full_analysis(df):
    if df is None or df.empty:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "all_patterns": []
        }

    df = df.copy()
    required = ["Open", "High", "Low", "Close"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)

    if len(df) < 30:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "all_patterns": []
        }

    df = calculate_indicators(df)
    df = calculate_zigzag(df)

    pivots = get_chronological_pivots(df)
    all_patterns = detect_all_head_shoulders(pivots, df)

    if not all_patterns:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "all_patterns": []
        }

    latest_pattern = all_patterns[-1]
    signal = "STRONG SELL"

    return {
        "df": df,
        "signal": signal,
        "pattern": latest_pattern["pattern"],
        "bias": latest_pattern["bias"],
        "entry": latest_pattern["entry"],
        "entry_trigger": latest_pattern["entry_trigger"],
        "sl": latest_pattern["sl"],
        "tp": latest_pattern["tp"],
        "nodes": latest_pattern["nodes"],
        "match": latest_pattern["match"],
        "neckline_start_idx": latest_pattern["neckline_start_idx"],
        "all_patterns": all_patterns
    }

if __name__ == "__main__":
    print("ENGINE.PY loaded with Post-Head Invalidation Filter (v3.5).")
        
