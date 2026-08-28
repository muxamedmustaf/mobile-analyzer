import pandas as pd
import numpy as np

# ==========================================================
# ENGINE.PY - STRICT LOGICAL HEAD & SHOULDERS ENGINE
# ==========================================================

MIN_SWING_PERCENT = 0.005


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


def calculate_zigzag(df, depth=5, backstep=3):
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


def detect_all_head_shoulders(pivots):
    patterns = []
    if len(pivots) < 6:
        return patterns

    # Requires 6 chronological pivots: L0 -> H1 -> L1 -> H2 -> L2 -> H3
    for i in range(len(pivots) - 5):
        p = pivots[i:i + 6]
        types = [x["type"] for x in p]

        if types != ["L", "H", "L", "H", "L", "H"]:
            continue

        l0 = p[0]["val"]  # Initial Low (Start of Bullish Wave)
        h1 = p[1]["val"]  # Left Shoulder Peak
        l1 = p[2]["val"]  # Left Neckline Low
        h2 = p[3]["val"]  # Head Peak
        l2 = p[4]["val"]  # Right Neckline Low
        h3 = p[5]["val"]  # Right Shoulder Peak

        # 1. Preceding Uptrend: H1 must be higher than initial Low (L0)
        if h1 <= l0:
            continue

        # 2. Retracement: L1 must be higher than L0 (Correction < Initial Uptrend)
        if l1 <= l0:
            continue

        # 3. Head Wave: H2 strictly higher than H1 and H3
        if h2 <= h1 or h2 <= h3:
            continue

        # 4. Head Wave Height: (H2 - L1) must be longer than Left Shoulder Retracement (H1 - L1)
        if (h2 - l1) <= (h1 - l1):
            continue

        # 5. Right Shoulder: H3 stays above the Right Neckline Low (L2)
        if h3 <= l2:
            continue

        # 6. Neckline Proximity: L2 must approach/reach L1 level
        neckline_avg = (l1 + l2) / 2.0
        head_height = h2 - neckline_avg

        if head_height <= 0:
            continue

        # Reject if L2 diverges too far from L1 relative to Head height (Strict Neckline)
        if abs(l2 - l1) > (head_height * 0.35):
            continue

        # Measured Target Strategy
        entry = neckline_avg
        sl = h2  # Structural Stop Loss at the Head Peak
        tp = entry - head_height  # TP = Entry minus exact Head Height

        patterns.append({
            "name": "Head and Shoulders",
            "pattern": "Head and Shoulders",
            "bias": "Bearish",
            "match": 100.0,
            "nodes": [(x["idx"], x["val"]) for x in p],
            "entry": float(round(entry, 5)),
            "entry_trigger": float(round(entry, 5)),
            "sl": float(round(sl, 5)),
            "tp": float(round(tp, 5)),
            "neckline_start_idx": p[2]["idx"],
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
    all_patterns = detect_all_head_shoulders(pivots)

    if not all_patterns:
        return {
            "df": df, "signal": "WAITING", "pattern": "NO PATTERN DETECTED",
            "bias": "Neutral", "entry": None, "sl": None, "tp": None,
            "nodes": [], "all_patterns": []
        }

    latest_pattern = all_patterns[-1]
    last_close = float(df["Close"].iloc[-1])
    trigger = float(latest_pattern["entry_trigger"])

    signal = "STRONG SELL" if last_close < trigger else "WAITING"

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
    print("ENGINE.PY loaded with strict mathematical H&S conditions.")
    
