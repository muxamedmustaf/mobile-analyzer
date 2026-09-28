# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

# ==========================================================
# ENGINE_APP.PY - LIVE MARKET SCANNER (STRICT STRICT STRICT)
# ==========================================================

MIN_WAVE_CANDLES = 3
MAX_H3_AGE = 15       # H3/L3 waa in uu samaysmay 15 laambadood gudahood
MAX_PATTERN_SPAN = 80 # Pattern-ka oo dhan waa in uusan ka badanayn 80 laambadood


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

    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df["ATR"] = true_range.rolling(14).mean()

    df["Dynamic_Swing"] = (df["ATR"] / df["Close"]) * 0.5
    df["Dynamic_Swing"] = df["Dynamic_Swing"].fillna(0.001)

    if "Volume" in df.columns:
        df["Volume_SMA"] = df["Volume"].rolling(20).mean().bfill().fillna(0)
    else:
        df["Volume_SMA"] = 0

    return df


def calculate_zigzag(df, depth=12, backstep=6):
    df = df.copy()
    df["Pivot_H"] = np.nan
    df["Pivot_L"] = np.nan

    highs = df["High"].astype(float).values
    lows = df["Low"].astype(float).values
    n = len(df)

    for i in range(depth, n - backstep):
        high_window = highs[i - depth : i + backstep + 1]
        low_window = lows[i - depth : i + backstep + 1]

        current_high = highs[i]
        current_low = lows[i]

        is_high = current_high == np.max(high_window) and np.sum(high_window == current_high) == 1
        is_low = current_low == np.min(low_window) and np.sum(low_window == current_low) == 1

        if is_high and not is_low:
            df.iloc[i, df.columns.get_loc("Pivot_H")] = current_high
        elif is_low and not is_high:
            df.iloc[i, df.columns.get_loc("Pivot_L")] = current_low

    return df


def get_chronological_pivots(df):
    raw = []
    for pos, (idx, row) in enumerate(df.iterrows()):
        if not pd.isna(row["Pivot_H"]):
            raw.append({"idx": idx, "pos": pos, "val": float(row["Pivot_H"]), "type": "H", "dynamic_swing": float(row.get("Dynamic_Swing", 0.001))})
        elif not pd.isna(row["Pivot_L"]):
            raw.append({"idx": idx, "pos": pos, "val": float(row["Pivot_L"]), "type": "L", "dynamic_swing": float(row.get("Dynamic_Swing", 0.001))})

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


def detect_all_head_shoulders(pivots, df):
    patterns = []
    if len(pivots) < 6:
        return patterns

    total_candles = len(df)

    for i in range(len(pivots) - 5):
        p = pivots[i : i + 6]
        if [x["type"] for x in p] != ["L", "H", "L", "H", "L", "H"]:
            continue

        pos_l0, pos_h3 = p[0]["pos"], p[5]["pos"]

        # SHURUUDDII 1: Pattern-ku waa in uusan aad u fidsanayn (Max Span)
        if (pos_h3 - pos_l0) > MAX_PATTERN_SPAN:
            continue

        # SHURUUDDII 2: Pivot-ka H3 waa in uu dhacay 15 laambadood u dambeeyay gudahooda
        if (total_candles - 1 - pos_h3) > MAX_H3_AGE:
            continue

        l0, h1, l1, h2, l2, h3 = [x["val"] for x in p]

        if h1 <= l0 or l1 <= l0 or h2 <= h1 or h2 <= h3:
            continue

        left_shoulder_height = h1 - min(l0, l1)
        right_shoulder_height = h3 - min(l1, l2)
        if left_shoulder_height <= 0 or right_shoulder_height <= 0:
            continue

        head_height = h2 - min(l1, l2)
        if head_height <= 0:
            continue

        if abs(h1 - h3) > (head_height * 0.20):
            continue

        # HUBIN BREAKOUT LAAMBADDA UGU DAMBEYSA KALIYA (`df.iloc[-1]`)
        idx_h3 = p[5]["idx"]
        l1_val, l2_val = p[2]["val"], p[4]["val"]
        idx_l1, idx_l2 = p[2]["pos"], p[4]["pos"]
        if idx_l1 == idx_l2:
            continue

        slope = (l2_val - l1_val) / (idx_l2 - idx_l1)
        post_h3_df = df.loc[idx_h3:]

        # Haddii laambad ka horreysa tan maanta ay mar hore jebisay -> ISKA INDHATIR
        already_broken = False
        for prev_idx, prev_row in post_h3_df.iloc[1:-1].iterrows():
            prev_pos = df.index.get_loc(prev_idx)
            prev_neckline = l2_val + slope * (prev_pos - idx_l2)
            if prev_row["Close"] < prev_neckline:
                already_broken = True
                break

        if already_broken:
            continue

        # EEK WAA IN LAAMBADDA UGU DAMBEYSA AY HADDA JEBINAYSO
        latest_row = df.iloc[-1]
        latest_idx = df.index[-1]
        latest_pos = total_candles - 1

        current_neckline = l2_val + slope * (latest_pos - idx_l2)
        close_price = latest_row["Close"]

        if close_price < current_neckline:
            rsi_val = latest_row["RSI"]
            ema50 = latest_row["EMA50"]
            ema200 = latest_row["EMA200"]

            if pd.isna(ema50) or pd.isna(ema200):
                continue

            vol_val = latest_row.get("Volume", 0)
            vol_sma = latest_row.get("Volume_SMA", 0)
            vol_confirmed = (vol_sma == 0) or (vol_val >= vol_sma * 0.8)

            if (30 <= rsi_val <= 75) and (ema50 > ema200) and vol_confirmed:
                entry = float(close_price)
                sl = float(round(h2, 5))
                shoulder_sl = float(round(max(h1, h3), 5))
                actual_head_length = h2 - current_neckline
                tp = float(round(entry - actual_head_length, 5))

                nodes = [(x["idx"], x["val"]) for x in p] + [(latest_idx, float(entry))]
                neckline_nodes = [(p[2]["idx"], l1), (p[4]["idx"], l2)]
                target_nodes = [(latest_idx, float(round(entry, 5))), (latest_idx, tp)]

                patterns.append({
                    "name": "Head and Shoulders",
                    "pattern": "Head and Shoulders",
                    "bias": "Bearish",
                    "match": 100.0,
                    "nodes": nodes,
                    "entry": float(round(entry, 5)),
                    "entry_trigger": float(round(entry, 5)),
                    "sl": sl,
                    "shoulder_sl": shoulder_sl,
                    "tp": tp,
                    "neckline_start_idx": p[2]["idx"],
                    "neckline_end_idx": latest_idx,
                    "neckline_nodes": neckline_nodes,
                    "target_nodes": target_nodes,
                    "end_pos": p[5]["pos"],
                })

    return patterns


def detect_all_inverse_head_shoulders(pivots, df):
    patterns = []
    if len(pivots) < 6:
        return patterns

    total_candles = len(df)

    for i in range(len(pivots) - 5):
        p = pivots[i : i + 6]
        if [x["type"] for x in p] != ["H", "L", "H", "L", "H", "L"]:
            continue

        pos_h0, pos_l3 = p[0]["pos"], p[5]["pos"]

        # SHURUUDDII 1: Pattern-ku waa in uusan aad u fidsanayn (Max Span)
        if (pos_l3 - pos_h0) > MAX_PATTERN_SPAN:
            continue

        # SHURUUDDII 2: Pivot-ka L3 waa in uu dhacay 15 laambadood u dambeeyay gudahooda
        if (total_candles - 1 - pos_l3) > MAX_H3_AGE:
            continue

        h0, l1, h1, l2, h2, l3 = [x["val"] for x in p]

        if l2 >= l1 or l2 >= l3:
            continue

        head_depth = max(h1, h2) - l2
        if head_depth <= 0:
            continue

        if abs(l1 - l3) > (head_depth * 0.20):
            continue

        idx_l3 = p[5]["idx"]
        h1_idx, h2_idx = p[2]["idx"], p[4]["idx"]
        pos_h1, pos_h2 = p[2]["pos"], p[4]["pos"]
        if pos_h1 == pos_h2:
            continue

        slope = (h2 - h1) / (pos_h2 - pos_h1)
        post_l3_df = df.loc[idx_l3:]

        # Haddii laambad ka horreysa tan maanta ay mar hore jebisay -> ISKA INDHATIR
        already_broken = False
        for prev_idx, prev_row in post_l3_df.iloc[1:-1].iterrows():
            prev_pos = df.index.get_loc(prev_idx)
            prev_neckline = h2 + slope * (prev_pos - pos_h2)
            if prev_row["Close"] > prev_neckline:
                already_broken = True
                break

        if already_broken:
            continue

        # EEK WAA IN LAAMBADDA UGU DAMBEYSA AY HADDA JEBINAYSO
        latest_row = df.iloc[-1]
        latest_idx = df.index[-1]
        latest_pos = total_candles - 1

        current_neckline = h2 + slope * (latest_pos - pos_h2)
        close_price = latest_row["Close"]

        if close_price > current_neckline:
            rsi_val = latest_row["RSI"]
            ema50 = latest_row["EMA50"]
            ema200 = latest_row["EMA200"]

            if pd.isna(ema50) or pd.isna(ema200):
                continue

            vol_val = latest_row.get("Volume", 0)
            vol_sma = latest_row.get("Volume_SMA", 0)
            vol_confirmed = (vol_sma == 0) or (vol_val >= vol_sma * 0.8)

            if (25 <= rsi_val <= 70) and (ema50 < ema200) and vol_confirmed:
                entry = float(close_price)
                sl = float(round(l2, 5))
                shoulder_sl = float(round(min(l1, l3), 5))
                actual_head_length = current_neckline - l2
                tp = float(round(entry + actual_head_length, 5))

                nodes = [(x["idx"], x["val"]) for x in p] + [(latest_idx, float(entry))]
                neckline_nodes = [(h1_idx, h1), (h2_idx, h2)]
                target_nodes = [(latest_idx, float(round(entry, 5))), (latest_idx, tp)]

                patterns.append({
                    "name": "Inverse Head and Shoulders",
                    "pattern": "Inverse Head and Shoulders",
                    "bias": "Bullish",
                    "match": 100.0,
                    "nodes": nodes,
                    "entry": float(round(entry, 5)),
                    "entry_trigger": float(round(entry, 5)),
                    "sl": sl,
                    "shoulder_sl": shoulder_sl,
                    "tp": tp,
                    "neckline_start_idx": h1_idx,
                    "neckline_end_idx": latest_idx,
                    "neckline_nodes": neckline_nodes,
                    "target_nodes": target_nodes,
                    "end_pos": p[5]["pos"],
                })

    return patterns


def _detect_both_head_shoulders(pivots, df):
    normal_patterns = detect_all_head_shoulders(pivots, df)
    inverse_patterns = detect_all_inverse_head_shoulders(pivots, df)
    return sorted(normal_patterns + inverse_patterns, key=lambda x: x.get("end_pos", -1))


def run_full_analysis(df):
    default_response = {
        "df": df,
        "signal": "WAITING",
        "pattern": "NO PATTERN DETECTED",
        "bias": "Neutral",
        "entry": None,
        "entry_trigger": None,
        "sl": None,
        "shoulder_sl": None,
        "tp": None,
        "nodes": [],
        "match": 0.0,
        "neckline_start_idx": None,
        "neckline_nodes": [],
        "target_nodes": [],
        "all_patterns": [],
    }

    if df is None or df.empty:
        return default_response

    df = df.copy()
    required = ["Open", "High", "Low", "Close"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)

    if len(df) < 30:
        default_response["df"] = df
        return default_response

    df_active = df.tail(200).copy()
    df_active = calculate_indicators(df_active)
    df_active = calculate_zigzag(df_active)

    pivots = get_chronological_pivots(df_active)
    all_patterns = _detect_both_head_shoulders(pivots, df_active)

    if not all_patterns:
        default_response["df"] = df_active
        return default_response

    latest_pattern = all_patterns[-1]
    signal = "STRONG BUY" if latest_pattern["bias"] == "Bullish" else "STRONG SELL"

    return {
        "df": df,
        "signal": signal,
        "pattern": latest_pattern["pattern"],
        "bias": latest_pattern["bias"],
        "entry": latest_pattern["entry"],
        "entry_trigger": latest_pattern["entry_trigger"],
        "sl": latest_pattern["sl"],
        "shoulder_sl": latest_pattern["shoulder_sl"],
        "tp": latest_pattern["tp"],
        "nodes": latest_pattern["nodes"],
        "match": latest_pattern["match"],
        "neckline_start_idx": latest_pattern["neckline_start_idx"],
        "neckline_nodes": latest_pattern.get("neckline_nodes", []),
        "target_nodes": latest_pattern.get("target_nodes", []),
        "all_patterns": all_patterns,
  }
  
