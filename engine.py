import pandas as pd
import numpy as np

# ==========================================================
# ENGINE.PY - OPTIMIZED DYNAMIC SWING SCANNER (v4.7)
# ==========================================================

MIN_WAVE_CANDLES = 3
MIN_PRE_TREND_MOVE = 0.01
MIN_SHOULDER_REACTION = 0.003


def calculate_indicators(df):
    df = df.copy()
    
    # حساب المتوسطات
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # حساب RSI
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()

    loss_safe = loss.replace(0, 1e-9)
    rs = gain / loss_safe
    df["RSI"] = (100 - (100 / (1 + rs))).fillna(50.0)

    # حساب ATR باستخدام NumPy المباشر لتوفير الذاكرة
    high_low = (df["High"] - df["Low"]).to_numpy()
    high_close = np.abs(df["High"].to_numpy() - df["Close"].shift().to_numpy())
    low_close = np.abs(df["Low"].to_numpy() - df["Close"].shift().to_numpy())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    df["ATR"] = pd.Series(true_range, index=df.index).rolling(14).mean()

    # حساب التأرجح الديناميكي
    df["Dynamic_Swing"] = ((df["ATR"] / df["Close"]) * 0.5).fillna(0.001)

    return df


def calculate_zigzag(df, depth=12, backstep=6):
    df = df.copy()
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)
    n = len(df)

    pivot_h = np.full(n, np.nan)
    pivot_l = np.full(n, np.nan)

    # استخدام مصفوفات NumPy بدلاً من Pandas iloc لإلغاء الضغط على المعالج
    for i in range(depth, n - backstep):
        high_window = highs[i - depth : i + backstep + 1]
        low_window = lows[i - depth : i + backstep + 1]

        curr_h = highs[i]
        curr_l = lows[i]

        is_high = (curr_h == np.max(high_window)) and (np.count_nonzero(high_window == curr_h) == 1)
        is_low = (curr_l == np.min(low_window)) and (np.count_nonzero(low_window == curr_l) == 1)

        if is_high and not is_low:
            pivot_h[i] = curr_h
        elif is_low and not is_high:
            pivot_l[i] = curr_l

    df["Pivot_H"] = pivot_h
    df["Pivot_L"] = pivot_l
    return df


def get_chronological_pivots(df):
    p_h = df["Pivot_H"].to_numpy()
    p_l = df["Pivot_L"].to_numpy()
    swings = df["Dynamic_Swing"].to_numpy() if "Dynamic_Swing" in df.columns else np.full(len(df), 0.001)
    indices = df.index.to_numpy()

    raw = []
    # استخراج النقاط باستخدام NumPy دون iterrows()
    for pos in range(len(df)):
        val_h = p_h[pos]
        val_l = p_l[pos]

        if not np.isnan(val_h):
            raw.append({
                "idx": indices[pos],
                "pos": pos,
                "val": float(val_h),
                "type": "H",
                "dynamic_swing": float(swings[pos])
            })
        elif not np.isnan(val_l):
            raw.append({
                "idx": indices[pos],
                "pos": pos,
                "val": float(val_l),
                "type": "L",
                "dynamic_swing": float(swings[pos])
            })

    if not raw:
        return []

    clean = []
    for p in raw:
        if not clean:
            clean.append(p)
            continue

        last = clean[-1]
        current_min_swing = p["dynamic_swing"]

        if last["type"] != p["type"]:
            movement = abs(p["val"] - last["val"]) / max(abs(last["val"]), 1e-9)

            if movement >= current_min_swing:
                clean.append(p)
            else:
                if last["type"] == "H" and p["val"] > last["val"]:
                    clean[-1] = p
                elif last["type"] == "L" and p["val"] < last["val"]:
                    clean[-1] = p
        elif p["type"] == "H" and p["val"] > last["val"]:
            clean[-1] = p
        elif p["type"] == "L" and p["val"] < last["val"]:
            clean[-1] = p

    final_clean = []
    for p in clean:
        if not final_clean:
            final_clean.append(p)
        else:
            if final_clean[-1]["type"] != p["type"]:
                final_clean.append(p)
            else:
                if p["type"] == "H" and p["val"] > final_clean[-1]["val"]:
                    final_clean[-1] = p
                elif p["type"] == "L" and p["val"] < final_clean[-1]["val"]:
                    final_clean[-1] = p

    return final_clean


class PatternValidatorPipeline:

    def __init__(self, df):
        self.df = df
        self.filters = [
            self.time_filter,
            self.trend_filter,
            self.invalidation_filter,
            self.indicator_confirmation_filter,
            self.breakout_filter
        ]

    def time_filter(self, p, data):
        i_l0, i_h1, i_l1, i_h2, i_l2, i_h3 = [x["pos"] for x in p]
        if (i_h1 - i_l0 < MIN_WAVE_CANDLES) or \
           (i_l1 - i_h1 < MIN_WAVE_CANDLES) or \
           (i_h2 - i_l1 < MIN_WAVE_CANDLES) or \
           (i_l2 - i_h2 < MIN_WAVE_CANDLES) or \
           (i_h3 - i_l2 < MIN_WAVE_CANDLES):
            return False, None, None
        return True, None, None

    def trend_filter(self, p, data):
        idx_l0 = p[0]["idx"]
        pre_l0_df = data.loc[:idx_l0]

        if len(pre_l0_df) > 10:
            past_min = pre_l0_df["Low"].iloc[-10:].min()
            if past_min > p[0]["val"]:
                return False, None, None

            pre_trend_move = (p[1]["val"] - past_min) / max(abs(past_min), 1e-9)
            if pre_trend_move < MIN_PRE_TREND_MOVE or p[0]["val"] <= past_min:
                return False, None, None

        return True, None, None

    def invalidation_filter(self, p, data):
        h2 = p[3]["val"]
        idx_h2 = p[3]["idx"]
        post_head_df = data.loc[idx_h2:]

        if not post_head_df.empty and post_head_df["High"].max() > h2:
            return False, None, None

        return True, None, None

    def indicator_confirmation_filter(self, p, data):
        idx_h3 = p[5]["idx"]
        rsi_val = data.loc[idx_h3, "RSI"]

        if not (30 <= rsi_val <= 75):
            return False, None, None

        ema50 = data.loc[idx_h3, "EMA50"]
        ema200 = data.loc[idx_h3, "EMA200"]

        if pd.isna(ema50) or pd.isna(ema200):
            return False, None, None

        return True, None, None

    def breakout_filter(self, p, data):
        idx_h3 = p[5]["idx"]
        l1, l2 = p[2]["val"], p[4]["val"]
        h2 = p[3]["val"]

        neckline_avg = (l1 + l2) / 2.0
        post_h3_df = data.loc[idx_h3:]

        head_length = h2 - neckline_avg
        tp_level = neckline_avg - head_length

        current_close = float(data["Close"].iloc[-1])
        if current_close >= neckline_avg or current_close <= tp_level:
            return False, None, None

        # التكرار باستخدام NumPy السريع بدلاً من iterrows
        closes = post_h3_df["Close"].to_numpy()
        idxs = post_h3_df.index.to_numpy()

        for i in range(len(closes)):
            close = float(closes[i])
            idx = idxs[i]

            if close <= tp_level:
                return False, None, None
            if close < neckline_avg:
                return True, idx, close

        return False, None, None

    def run(self, p):
        end_idx, end_val = None, None
        for f in self.filters:
            passed, e_idx, e_val = f(p, self.df)
            if not passed:
                return False, None, None
            if e_idx is not None:
                end_idx, end_val = e_idx, e_val

        return True, end_idx, end_val


def detect_all_head_shoulders(pivots, df):
    patterns = []
    if len(pivots) < 6:
        return patterns

    validator = PatternValidatorPipeline(df)
    total_candles = len(df)

    for i in range(len(pivots) - 5):
        p = pivots[i:i + 6]

        if [x["type"] for x in p] != ["L", "H", "L", "H", "L", "H"]:
            continue

        l0, h1, l1, h2, l2, h3 = [x["val"] for x in p]

        if h1 <= l0 or l1 <= l0:
            continue

        left_reaction_up = (h1 - l0) / max(abs(l0), 1e-9)
        left_reaction_down = (h1 - l1) / max(abs(h1), 1e-9)

        if left_reaction_up < MIN_SHOULDER_REACTION or left_reaction_down < MIN_SHOULDER_REACTION:
            continue

        if abs(l1 - l0) / max(abs(l0), 1e-9) > 0.02:
            continue

        right_reaction_up = (h3 - l2) / max(abs(l2), 1e-9)
        if right_reaction_up < MIN_SHOULDER_REACTION:
            continue

        if h2 <= h1 or h2 <= h3:
            continue

        neckline_min = min(l1, l2)
        head_height = h2 - neckline_min

        if head_height <= 0:
            continue

        if abs(h1 - h3) > (head_height * 0.35):
            continue

        max_shoulder = max(h1, h3)
        if (h2 - max_shoulder) < (head_height * 0.25):
            continue

        if abs(l1 - l2) > (head_height * 0.25):
            continue

        passed, end_idx, end_val = validator.run(p)
        if not passed:
            continue

        end_pos = df.index.get_loc(end_idx)
        if (total_candles - end_pos) > 10:
            continue

        l1_idx, l2_idx = p[2]["idx"], p[4]["idx"]
        neckline_avg = (l1 + l2) / 2.0
        actual_head_length = h2 - neckline_avg

        entry = neckline_avg
        sl = h2
        tp = entry - actual_head_length

        current_close = float(df["Close"].iloc[-1])
        if current_close >= entry or current_close <= tp:
            continue

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
            "neckline_start_idx": l1_idx,
            "neckline_end_idx": end_idx,
            "neckline_nodes": [(l1_idx, l1), (l2_idx, l2)],
            "target_nodes": [(end_idx, float(round(entry, 5))), (end_idx, float(round(tp, 5)))],
            "end_pos": p[5]["pos"]
        })

    return patterns


def detect_all_inverse_head_shoulders(pivots, df):
    patterns = []
    if len(pivots) < 6:
        return patterns

    total_candles = len(df)

    for i in range(len(pivots) - 5):
        p = pivots[i:i + 6]

        if [x["type"] for x in p] != ["H", "L", "H", "L", "H", "L"]:
            continue

        h0, l1, h1, l2, h2, l3 = [x["val"] for x in p]

        if l2 >= l1 or l2 >= l3:
            continue

        neckline_max = max(h1, h2)
        head_depth = neckline_max - l2

        if head_depth <= 0 or abs(l1 - l3) > (head_depth * 0.35):
            continue

        min_shoulder = min(l1, l3)
        if (min_shoulder - l2) < (head_depth * 0.25) or abs(h1 - h2) > (head_depth * 0.25):
            continue

        positions = [x["pos"] for x in p]
        if any((positions[j] - positions[j - 1]) < MIN_WAVE_CANDLES for j in range(1, 6)):
            continue

        idx_h0 = p[0]["idx"]
        pre_left_df = df.loc[:idx_h0]
        if len(pre_left_df) > 10 and pre_left_df["High"].iloc[-10:].max() < p[0]["val"]:
            continue

        idx_l2 = p[3]["idx"]
        post_head_df = df.loc[idx_l2:]
        if not post_head_df.empty and post_head_df["Low"].min() < l2:
            continue

        idx_l3 = p[5]["idx"]
        if idx_l3 not in df.index:
            continue

        rsi_val = df.loc[idx_l3, "RSI"]
        if not (25 <= rsi_val <= 70):
            continue

        ema50 = df.loc[idx_l3, "EMA50"]
        ema200 = df.loc[idx_l3, "EMA200"]
        if pd.isna(ema50) or pd.isna(ema200):
            continue

        h1_idx, h2_idx = p[2]["idx"], p[4]["idx"]
        neckline_avg = (h1 + h2) / 2.0

        post_l3_df = df.loc[idx_l3:]
        head_length = neckline_avg - l2
        tp_level = neckline_avg + head_length

        end_idx = None
        end_val = None

        closes = post_l3_df["Close"].to_numpy()
        idxs = post_l3_df.index.to_numpy()

        for idx_pos in range(len(closes)):
            close = float(closes[idx_pos])
            idx_val = idxs[idx_pos]

            if close >= tp_level:
                break
            if close > neckline_avg:
                end_idx = idx_val
                end_val = close
                break

        if end_idx is None:
            continue

        end_pos = df.index.get_loc(end_idx)
        if (total_candles - end_pos) > 10:
            continue

        entry = neckline_avg
        sl = l2
        actual_head_length = neckline_avg - l2
        tp = entry + actual_head_length

        current_close = float(df["Close"].iloc[-1])
        if current_close <= entry or current_close >= tp:
            continue

        nodes = [(x["idx"], x["val"]) for x in p]
        nodes.append((end_idx, end_val))

        patterns.append({
            "name": "Inverse Head and Shoulders",
            "pattern": "Inverse Head and Shoulders",
            "bias": "Bullish",
            "match": 100.0,
            "nodes": nodes,
            "entry": float(round(entry, 5)),
            "entry_trigger": float(round(entry, 5)),
            "sl": float(round(sl, 5)),
            "tp": float(round(tp, 5)),
            "neckline_start_idx": h1_idx,
            "neckline_end_idx": end_idx,
            "neckline_nodes": [(h1_idx, h1), (h2_idx, h2)],
            "target_nodes": [(end_idx, float(round(entry, 5))), (end_idx, float(round(tp, 5)))],
            "end_pos": p[5]["pos"]
        })

    return patterns


_original_detect_all_head_shoulders = detect_all_head_shoulders


def _detect_both_head_shoulders(pivots, df):
    normal_patterns = _original_detect_all_head_shoulders(pivots, df)
    inverse_patterns = detect_all_inverse_head_shoulders(pivots, df)

    all_patterns = normal_patterns + inverse_patterns
    all_patterns.sort(key=lambda x: x.get("end_pos", -1))
    return all_patterns


detect_all_head_shoulders = _detect_both_head_shoulders


def run_full_analysis(df):
    if df is None or df.empty:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "neckline_nodes": [], "target_nodes": [], "all_patterns": []
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
            "nodes": [], "neckline_nodes": [], "target_nodes": [], "all_patterns": []
        }

    # تحديد أحدث 200 شمعة فقط للحسابات لتوفير الاستهلاك
    df_active = df.tail(200).copy()
    df_active = calculate_indicators(df_active)
    df_active = calculate_zigzag(df_active)

    pivots = get_chronological_pivots(df_active)
    all_patterns = detect_all_head_shoulders(pivots, df_active)

    if not all_patterns:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "neckline_nodes": [], "target_nodes": [], "all_patterns": []
        }

    latest_pattern = all_patterns[-1]
    signal = "STRONG BUY" if latest_pattern["pattern"] == "Inverse Head and Shoulders" else "STRONG SELL"

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
        "neckline_nodes": latest_pattern.get("neckline_nodes", []),
        "target_nodes": latest_pattern.get("target_nodes", []),
        "all_patterns": all_patterns
    }


if __name__ == "__main__":
    print("ENGINE.PY loaded with Optimized Dynamic ATR Swing Scanner (v4.7).")
        
