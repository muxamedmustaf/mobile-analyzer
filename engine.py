# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

# ==========================================================
# ENGINE_APP.PY - LIVE MARKET SCANNER (v5.2 Complete Strict Rules)
# ==========================================================

MIN_WAVE_CANDLES = 5  # Shuruudda 5-ta laambadood ee mowjad kasta (File 1)


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

    is_high = current_high == np.max(high_window) and np.sum(
        high_window == current_high
    ) == 1
    is_low = current_low == np.min(low_window) and np.sum(
        low_window == current_low
    ) == 1

    if is_high and not is_low:
      df.iloc[i, df.columns.get_loc("Pivot_H")] = current_high
    elif is_low and not is_high:
      df.iloc[i, df.columns.get_loc("Pivot_L")] = current_low

  return df


def get_chronological_pivots(df):
  raw = []
  for pos, (idx, row) in enumerate(df.iterrows()):
    if not pd.isna(row["Pivot_H"]):
      raw.append({
          "idx": idx,
          "pos": pos,
          "val": float(row["Pivot_H"]),
          "type": "H",
          "dynamic_swing": float(row.get("Dynamic_Swing", 0.001)),
      })
    elif not pd.isna(row["Pivot_L"]):
      raw.append({
          "idx": idx,
          "pos": pos,
          "val": float(row["Pivot_L"]),
          "type": "L",
          "dynamic_swing": float(row.get("Dynamic_Swing", 0.001)),
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

  def time_filter(self, p):
    i_l0, i_h1, i_l1, i_h2, i_l2, i_h3 = [x["pos"] for x in p]
    if (
        (i_h1 - i_l0 < MIN_WAVE_CANDLES)
        or (i_l1 - i_h1 < MIN_WAVE_CANDLES)
        or (i_h2 - i_l1 < MIN_WAVE_CANDLES)
        or (i_l2 - i_h2 < MIN_WAVE_CANDLES)
        or (i_h3 - i_l2 < MIN_WAVE_CANDLES)
    ):
      return False
    return True

  def trend_filter(self, p, pattern_type="normal"):
    idx_p0 = p[0]["idx"]
    pre_df = self.df.loc[:idx_p0]
    if len(pre_df) > 10:
      if pattern_type == "normal":
        past_min = float(pre_df["Low"].iloc[-10:].min())
        if past_min > p[0]["val"]:
          return False
      else:  # inverse
        past_max = float(pre_df["High"].iloc[-10:].max())
        if past_max < p[0]["val"]:
          return False
    return True

  def invalidation_filter(self, p, pattern_type="normal"):
    head_val = p[3]["val"]
    idx_head = p[3]["idx"]
    post_head_df = self.df.loc[idx_head:]
    if not post_head_df.empty:
      if pattern_type == "normal":
        if float(post_head_df["High"].max()) > head_val:
          return False
      else:  # inverse
        if float(post_head_df["Low"].min()) < head_val:
          return False
    return True

  def breakout_and_indicator_filter(self, p, pattern_type="normal"):
    idx_h3 = p[5]["idx"]
    pos_n1, pos_n2 = p[2]["pos"], p[4]["pos"]
    val_n1, val_n2 = p[2]["val"], p[4]["val"]

    if pos_n1 == pos_n2:
      return False, None, None

    slope = (val_n2 - val_n1) / (pos_n2 - pos_n1)
    post_h3_df = self.df.loc[idx_h3:]

    if len(post_h3_df) <= 1:
      return False, None, None

    for current_idx, row in post_h3_df.iloc[1:].iterrows():
      current_pos = self.df.index.get_loc(current_idx)
      current_neckline = val_n2 + slope * (current_pos - pos_n2)
      close_price = float(row["Close"])
      rsi_val = float(row["RSI"])
      ema50 = row["EMA50"]
      ema200 = row["EMA200"]

      if pd.isna(ema50) or pd.isna(ema200):
        continue

      vol_val = row.get("Volume", 0)
      vol_sma = row.get("Volume_SMA", 0)
      vol_confirmed = (vol_sma == 0) or (vol_val >= vol_sma * 0.8)

      if pattern_type == "normal":
        if close_price < current_neckline:
          if (30 <= rsi_val <= 75) and (ema50 > ema200) and vol_confirmed:
            return True, current_idx, close_price
          else:
            return False, None, None
      else:  # inverse
        if close_price > current_neckline:
          if (25 <= rsi_val <= 70) and (ema50 < ema200) and vol_confirmed:
            return True, current_idx, close_price
          else:
            return False, None, None

    return False, None, None


def detect_all_head_shoulders(pivots, df):
  patterns = []
  if len(pivots) < 6:
    return patterns

  validator = PatternValidatorPipeline(df)
  total_candles = len(df)

  for i in range(len(pivots) - 5):
    p = pivots[i : i + 6]
    if [x["type"] for x in p] != ["L", "H", "L", "H", "L", "H"]:
      continue

    l0, h1, l1, h2, l2, h3 = [x["val"] for x in p]

    # Basic height checks
    if h1 <= l0 or l1 <= l0 or h2 <= h1 or h2 <= h3:
      continue

    # SHARDI 3: H1 garabka bidix waa in uu yahay kan ugu dheer uguna sarreeya garabkaas
    if h1 <= max(l0, l1):
      continue

    left_shoulder_height = h1 - min(l0, l1)
    right_shoulder_height = h3 - min(l1, l2)

    if left_shoulder_height <= 0 or right_shoulder_height <= 0:
      continue

    # SHARDI 1 & 2: Garabka midig 3-diisa nuqul vs Garabka bidix (Tolerance <= 0.5)
    height_diff_ratio = abs(
        right_shoulder_height - left_shoulder_height
    ) / max(left_shoulder_height, 1e-9)
    if height_diff_ratio > 0.5:
      continue

    if abs(l2 - l0) / max(left_shoulder_height, 1e-9) > 0.5:
      continue
    if abs(l2 - l1) / max(left_shoulder_height, 1e-9) > 0.5:
      continue
    if abs(h3 - h1) / max(left_shoulder_height, 1e-9) > 0.5:
      continue

    neckline_min = min(l1, l2)
    head_height = h2 - neckline_min
    if head_height <= 0:
      continue

    if abs(h1 - h3) > (head_height * 0.15):
      continue

    max_shoulder = max(h1, h3)
    if (h2 - max_shoulder) < (head_height * 0.25):
      continue

    if abs(l1 - l2) > (head_height * 0.25):
      continue

    # Pipeline Filters
    if not validator.time_filter(p):
      continue
    if not validator.trend_filter(p, pattern_type="normal"):
      continue
    if not validator.invalidation_filter(p, pattern_type="normal"):
      continue

    passed_breakout, end_idx, end_val = validator.breakout_and_indicator_filter(
        p, pattern_type="normal"
    )
    if not passed_breakout:
      continue

    end_pos = df.index.get_loc(end_idx)
    if (total_candles - end_pos) > 10:  # Caadada live-ka: 10 laambadood ee ugu dambeeyay
      continue

    l1_idx, l2_idx = p[2]["idx"], p[4]["idx"]
    slope = (l2 - l1) / (p[4]["pos"] - p[2]["pos"])
    breakout_neckline_price = l2 + slope * (end_pos - p[4]["pos"])
    actual_head_length = h2 - breakout_neckline_price

    entry = float(end_val)
    sl = float(round(h2, 5))
    shoulder_sl = float(round(max(h1, h3), 5))
    tp = float(round(entry - actual_head_length, 5))

    nodes = [(x["idx"], x["val"]) for x in p] + [(end_idx, float(end_val))]
    neckline_nodes = [(l1_idx, l1), (l2_idx, l2)]
    target_nodes = [(end_idx, float(round(entry, 5))), (end_idx, tp)]

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
        "neckline_start_idx": l1_idx,
        "neckline_end_idx": end_idx,
        "neckline_nodes": neckline_nodes,
        "target_nodes": target_nodes,
        "end_pos": p[5]["pos"],
    })

  return patterns


def detect_all_inverse_head_shoulders(pivots, df):
  patterns = []
  if len(pivots) < 6:
    return patterns

  validator = PatternValidatorPipeline(df)
  total_candles = len(df)

  for i in range(len(pivots) - 5):
    p = pivots[i : i + 6]
    if [x["type"] for x in p] != ["H", "L", "H", "L", "H", "L"]:
      continue

    h0, l1, h1, l2, h2, l3 = [x["val"] for x in p]

    if l2 >= l1 or l2 >= l3:
      continue

    # SHARDI 3 (Inverse): L1 waa in uu yahay kan ugu hooseeya garabka bidix
    if l1 >= min(h0, h1):
      continue

    left_shoulder_depth = max(h0, h1) - l1
    right_shoulder_depth = max(h1, h2) - l3

    if left_shoulder_depth <= 0 or right_shoulder_depth <= 0:
      continue

    # SHARDI 1 & 2 (Inverse): 0.5 Tolerance rule
    depth_diff_ratio = abs(right_shoulder_depth - left_shoulder_depth) / max(
        left_shoulder_depth, 1e-9
    )
    if depth_diff_ratio > 0.5:
      continue

    if abs(h2 - h0) / max(left_shoulder_depth, 1e-9) > 0.5:
      continue
    if abs(h2 - h1) / max(left_shoulder_depth, 1e-9) > 0.5:
      continue
    if abs(l3 - l1) / max(left_shoulder_depth, 1e-9) > 0.5:
      continue

    neckline_max = max(h1, h2)
    head_depth = neckline_max - l2
    if head_depth <= 0:
      continue

    if abs(l1 - l3) > (head_depth * 0.65):
      continue

    min_shoulder = min(l1, l3)
    if (min_shoulder - l2) < (head_depth * 0.25):
      continue

    if abs(h1 - h2) > (head_depth * 0.25):
      continue

    # Pipeline Filters
    if not validator.time_filter(p):
      continue
    if not validator.trend_filter(p, pattern_type="inverse"):
      continue
    if not validator.invalidation_filter(p, pattern_type="inverse"):
      continue

    passed_breakout, end_idx, end_val = validator.breakout_and_indicator_filter(
        p, pattern_type="inverse"
    )
    if not passed_breakout:
      continue

    end_pos = df.index.get_loc(end_idx)
    if (total_candles - end_pos) > 10:  # Caadada live-ka: 10 laambadood ee ugu dambeeyay
      continue

    h1_idx, h2_idx = p[2]["idx"], p[4]["idx"]
    slope = (h2 - h1) / (p[4]["pos"] - p[2]["pos"])
    breakout_neckline_price = h2 + slope * (end_pos - p[4]["pos"])
    actual_head_length = breakout_neckline_price - l2

    entry = float(end_val)
    sl = float(round(l2, 5))
    shoulder_sl = float(round(min(l1, l3), 5))
    tp = float(round(entry + actual_head_length, 5))

    nodes = [(x["idx"], x["val"]) for x in p] + [(end_idx, float(end_val))]
    neckline_nodes = [(h1_idx, h1), (h2_idx, h2)]
    target_nodes = [(end_idx, float(round(entry, 5))), (end_idx, tp)]

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
        "neckline_end_idx": end_idx,
        "neckline_nodes": neckline_nodes,
        "target_nodes": target_nodes,
        "end_pos": p[5]["pos"],
    })

  return patterns


def _detect_both_head_shoulders(pivots, df):
  normal_patterns = detect_all_head_shoulders(pivots, df)
  inverse_patterns = detect_all_inverse_head_shoulders(pivots, df)
  return sorted(
      normal_patterns + inverse_patterns, key=lambda x: x.get("end_pos", -1)
  )


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
  signal = (
      "STRONG BUY" if latest_pattern["bias"] == "Bullish" else "STRONG SELL"
  )

  return {
      "df": df_active,
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
    
