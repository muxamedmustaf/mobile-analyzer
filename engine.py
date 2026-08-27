import pandas as pd
import numpy as np

# ==========================================================
# ENGINE.PY
# SINGLE PATTERN ENGINE: HEAD AND SHOULDERS
# Compatible with the existing app.py and backtest.py
# ==========================================================

MAX_PATTERN_AGE = 25
MAX_VARIATION = 0.01
MIN_SWING_PERCENT = 0.005


# ==========================================================
# INDICATORS
# ==========================================================

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


# ==========================================================
# ZIGZAG
# ==========================================================

def calculate_zigzag(df, depth=7, deviation=5, backstep=3):
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


# ==========================================================
# CHRONOLOGICAL MAJOR PIVOTS
# ==========================================================

def get_chronological_pivots(df):
    raw = []

    for pos, (idx, row) in enumerate(df.iterrows()):
        if not pd.isna(row["Pivot_H"]):
            raw.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_H"]),
                "type": "H"
            })

        elif not pd.isna(row["Pivot_L"]):
            raw.append({
                "idx": idx,
                "pos": pos,
                "val": float(row["Pivot_L"]),
                "type": "L"
            })

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


# ==========================================================
# HELPERS
# ==========================================================

def variation(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)


def same_level(a, b, tolerance=MAX_VARIATION):
    return variation(a, b) <= tolerance


def recent_pattern(points, current_pos):
    if not points:
        return False
    return current_pos - points[-1]["pos"] <= MAX_PATTERN_AGE


def make_result(name, bias, points, entry, sl, tp, score=100):
    return {
        "name": name,
        "pattern": name,
        "bias": bias,
        "match": float(score),
        "nodes": [(p["idx"], p["val"]) for p in points],
        "entry": float(entry),
        "entry_trigger": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "neckline_start_idx": points[1]["idx"],
    }


# ==========================================================
# HEAD AND SHOULDERS
# ==========================================================

def detect_head_shoulders(pivots, current_pos):
    if len(pivots) < 5:
        return None

    # Examine only the latest few possible structures.
    start = max(0, len(pivots) - 7)

    for i in range(start, len(pivots) - 4):
        p = pivots[i:i + 5]

        if [x["type"] for x in p] != ["H", "L", "H", "L", "H"]:
            continue

        if not recent_pattern(p, current_pos):
            continue

        h1, l1, h2, l2, h3 = [x["val"] for x in p]

        # Head must be above both shoulders.
        if h2 <= h1 or h2 <= h3:
            continue

        # Both shoulders should be close in height.
        if not same_level(h1, h3, 0.01):
            continue

        # Neckline is formed by the two reaction lows.
        x1 = p[1]["pos"]
        x2 = p[3]["pos"]

        if x2 == x1:
            neckline = (l1 + l2) / 2.0
        else:
            slope = (l2 - l1) / float(x2 - x1)
            neckline = l2 + slope * (current_pos - x2)

        height = h2 - neckline

        if height <= 0:
            continue

        # Both neckline lows must be meaningfully below the shoulders.
        left_depth = (h1 - l1) / max(height, 1e-9)
        right_depth = (h3 - l2) / max(height, 1e-9)

        if left_depth < 0.20 or right_depth < 0.20:
            continue

        # Right shoulder must remain below the head.
        if h3 >= h2:
            continue

        # Entry = neckline break.
        entry = neckline

        # Structural invalidation above the right shoulder.
        sl = h3 * 1.001

        # Classical measured target.
        tp = neckline - height

        return make_result(
            "Head and Shoulders",
            "Bearish",
            p,
            entry,
            sl,
            tp,
            100
        )

    return None


# ==========================================================
# MAIN ANALYSIS
# ==========================================================

def run_full_analysis(df):
    if df is None or df.empty:
        return {
            "df": df,
            "signal": "WAITING",
            "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral",
            "entry": None,
            "sl": None,
            "tp": None,
            "nodes": [],
        }

    df = df.copy()

    # Normalize required columns.
    required = ["Open", "High", "Low", "Close"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)

    if len(df) < 30:
        return {
            "df": df,
            "signal": "WAITING",
            "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral",
            "entry": None,
            "sl": None,
            "tp": None,
            "nodes": [],
        }

    df = calculate_indicators(df)
    df = calculate_zigzag(df)

    pivots = get_chronological_pivots(df)
    current_pos = len(df) - 1

    pattern_result = detect_head_shoulders(
        pivots,
        current_pos
    )

    if pattern_result is None:
        return {
            "df": df,
            "signal": "WAITING",
            "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral",
            "entry": None,
            "sl": None,
            "tp": None,
            "nodes": [],
        }

    last_close = float(df["Close"].iloc[-1])
    trigger = float(pattern_result["entry_trigger"])

    # Detection is separated from trading confirmation.
    # A bearish H&S becomes STRONG SELL only after a close below neckline.
    if last_close < trigger:
        signal = "STRONG SELL"
    else:
        signal = "WAITING"

    return {
        "df": df,
        "signal": signal,
        "pattern": pattern_result["pattern"],
        "bias": pattern_result["bias"],
        "entry": pattern_result["entry"],
        "entry_trigger": pattern_result["entry_trigger"],
        "sl": pattern_result["sl"],
        "tp": pattern_result["tp"],
        "nodes": pattern_result["nodes"],
        "match": pattern_result["match"],
        "neckline_start_idx": pattern_result["neckline_start_idx"],
    }


# ==========================================================
# OPTIONAL SIMPLE TEST
# ==========================================================

if __name__ == "__main__":
    print("ENGINE.PY loaded successfully.")
    print("Active pattern: Head and Shoulders")
    
