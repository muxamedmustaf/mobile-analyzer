import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# 1. CALCULATE INDICATORS (SAFE & ROBUST)
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50.0)
    return df

# ==========================================================
# 2. PIVOT DETECTION
# ==========================================================
def detect_pivots(df, window=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    for i in range(window, len(df) - window):
        high_win = df['High'].iloc[i - window:i + window + 1]
        low_win = df['Low'].iloc[i - window:i + window + 1]
        
        if not high_win.empty and df['High'].iloc[i] == high_win.max():
            df.loc[df.index[i], 'Pivot_H'] = df['High'].iloc[i]
        if not low_win.empty and df['Low'].iloc[i] == low_win.min():
            df.loc[df.index[i], 'Pivot_L'] = df['Low'].iloc[i]
            
    return df

def eq(a, b, tol=0.04): 
    if max(abs(a), abs(b)) == 0: return True
    return abs(a - b) / max(abs(a), abs(b)) <= tol

# ==========================================================
# 3. MULTI-PATTERN SCANNER & SCORING ENGINE (NO EARLY EXIT)
# ==========================================================
def scan_all_patterns_and_select_best(df):
    ph, pl = df['Pivot_H'].dropna(), df['Pivot_L'].dropna()
    if len(ph) < 3 or len(pl) < 3:
        return "NO PATTERN DETECTED", "Neutral", 0.0, 0.0, None, None, 0.0

    h3, h2, h1 = ph.iloc[-1], ph.iloc[-2], ph.iloc[-3]
    l3, l2, l1 = pl.iloc[-1], pl.iloc[-2], pl.iloc[-3]
    
    p_start = min(ph.index[-3], pl.index[-3])
    p_end = max(ph.index[-1], pl.index[-1])
    close = df['Close'].iloc[-1]

    candidates = []

    # --- 1. HEAD AND SHOULDERS / INVERSE ---
    if len(ph) >= 3 and len(pl) >= 2:
        if h2 > h1 and h2 > h3 and eq(h1, h3, 0.06):
            err = abs(h1 - h3) / max(h1, h3)
            score = 95 - (err * 100) + (10 if close < min(l1, l2) else 0)
            candidates.append({"name": "Head and Shoulders", "bias": "Bearish", "h": h2, "l": min(l1, l2), "start": p_start, "end": p_end, "score": score})
    if len(pl) >= 3 and len(ph) >= 2:
        if l2 < l1 and l2 < l3 and eq(l1, l3, 0.06):
            err = abs(l1 - l3) / max(l1, l3)
            score = 95 - (err * 100) + (10 if close > max(h1, h2) else 0)
            candidates.append({"name": "Inverse Head and Shoulders", "bias": "Bullish", "h": max(h1, h2), "l": l2, "start": p_start, "end": p_end, "score": score})

    # --- 2. TRIPLE TOPS & BOTTOMS ---
    if eq(l1, l2, 0.03) and eq(l2, l3, 0.03):
        err = (abs(l1 - l2) + abs(l2 - l3)) / max(l1, l2, l3)
        score = 90 - (err * 100) + (10 if close > max(h1, h2, h3) else 0)
        candidates.append({"name": "Triple Bottom", "bias": "Bullish", "h": max(h1, h2, h3), "l": min(l1, l2, l3), "start": p_start, "end": p_end, "score": score})
    if eq(h1, h2, 0.03) and eq(h2, h3, 0.03):
        err = (abs(h1 - h2) + abs(h2 - h3)) / max(h1, h2, h3)
        score = 90 - (err * 100) + (10 if close < min(l1, l2, l3) else 0)
        candidates.append({"name": "Triple Top", "bias": "Bearish", "h": max(h1, h2, h3), "l": min(l1, l2, l3), "start": p_start, "end": p_end, "score": score})

    # --- 3. DYNAMIC WEDGES (SLOPE-BASED) ---
    slope_h = h3 - h1
    slope_l = l3 - l1
    if h1 > h2 > h3 and slope_h < 0:
        score = 85 + (15 if close > h3 else 0)
        candidates.append({"name": "Falling Wedge", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "score": score})
    if h1 < h2 < h3 and slope_h > 0:
        score = 85 + (15 if close < l3 else 0)
        candidates.append({"name": "Rising Wedge", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "score": score})

    # --- 4. DOUBLE BOTTOM (W PATTERN) & DOUBLE TOP (M PATTERN) ---
    if eq(l2, l3, 0.04) and h3 > l3:
        err = abs(l2 - l3) / max(l2, l3)
        score = 80 - (err * 100) + (15 if close > h3 else 0)
        candidates.append({"name": "Double Bottom (W Pattern)", "bias": "Bullish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "score": score})
    if eq(h2, h3, 0.04) and l3 < h3:
        err = abs(h2 - h3) / max(h2, h3)
        score = 80 - (err * 100) + (15 if close < l3 else 0)
        candidates.append({"name": "Double Top (M Pattern)", "bias": "Bearish", "h": max(h2, h3), "l": min(l2, l3), "start": p_start, "end": p_end, "score": score})

    # --- 5. FLAGS & TRIANGLES ---
    if h1 < h2 and l1 < l2:
        score = 70 + (10 if close > h2 else 0)
        candidates.append({"name": "Bullish Flag", "bias": "Bullish", "h": h2, "l": l2, "start": p_start, "end": p_end, "score": score})
    if h1 > h2 and l1 > l2:
        score = 70 + (10 if close < l2 else 0)
        candidates.append({"name": "Bearish Flag", "bias": "Bearish", "h": h2, "l": l2, "start": p_start, "end": p_end, "score": score})

    if h1 < h2 and eq(h2, h3, 0.04) and l1 < l2 < l3:
        score = 75 + (10 if close > h3 else 0)
        candidates.append({"name": "Ascending Triangle", "bias": "Bullish", "h": h3, "l": l3, "start": p_start, "end": p_end, "score": score})
    if l1 > l2 and eq(l2, l3, 0.04) and h1 > h2 > h3:
        score = 75 + (10 if close < l3 else 0)
        candidates.append({"name": "Descending Triangle", "bias": "Bearish", "h": h3, "l": l3, "start": p_start, "end": p_end, "score": score})

    if h1 > h2 > h3 and l1 < l2 < l3:
        dyn_bias = "Bullish" if close >= h3 else ("Bearish" if close <= l3 else "Neutral")
        score = 65 + (15 if dyn_bias != "Neutral" else 0)
        candidates.append({"name": "Symmetrical Triangle", "bias": dyn_bias, "h": h3, "l": l3, "start": p_start, "end": p_end, "score": score})

    if not candidates:
        return "NO PATTERN DETECTED", "Neutral", h3, l3, p_start, p_end, 0.0

    # التقييم واختيار النمط الأعلى درجة
    best = max(candidates, key=lambda x: x["score"])
    return best["name"], best["bias"], best["h"], best["l"], best["start"], best["end"], round(best["score"], 2)

# ==========================================================
# 4. FULL ANALYSIS ENGINE
# ==========================================================
def run_full_analysis(df):
    df = calculate_indicators(df)
    df = detect_pivots(df)

    pattern_name, bias, struct_h, struct_l, pattern_start, pattern_end, pattern_score = scan_all_patterns_and_select_best(df)

    latest = df.iloc[-1]
    close, ema50, ema200, rsi = latest['Close'], latest['EMA50'], latest['EMA200'], latest['RSI']

    c_ema_bull = (close > ema200) and (ema50 > ema200)
    c_ema_bear = (close < ema200) and (close < ema50)
    c_rsi = (30 <= rsi <= 75)
    c_breakout = (close > struct_h)
    c_breakdown = (close < struct_l)

    final_signal = "NO SIGNAL / WAITING"
    rejected_reasons = []

    if bias in ["Bullish", "Bullish Reversal"]:
        if not c_breakout:
            rejected_reasons.append(f"Breakout Level Failed: Close ({close:.4f}) <= Resistance ({struct_h:.4f})")
        if not c_ema_bull:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be above EMA200 ({ema200:.4f}) and EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakout and c_ema_bull and c_rsi:
            final_signal = "STRONG BUY"

    elif bias in ["Bearish", "Bearish Reversal"]:
        if not c_breakdown:
            rejected_reasons.append(f"Breakdown Level Failed: Close ({close:.4f}) >= Support ({struct_l:.4f})")
        if not c_ema_bear:
            rejected_reasons.append(f"EMA Trend Failed: Close ({close:.4f}) must be below EMA200 ({ema200:.4f}) and EMA50 ({ema50:.4f})")
        if not c_rsi:
            rejected_reasons.append(f"RSI Filter Failed: RSI ({rsi:.1f}) outside range 30-75")
        if c_breakdown and c_ema_bear and c_rsi:
            final_signal = "STRONG SELL"
    else:
        rejected_reasons.append("Waiting for clear structural breakout direction.")

    entry_price = round(close, 4)
    sl, tp = "N/A", "N/A"

    if final_signal == "STRONG BUY":
        sl_val = round(struct_l, 4)
        risk = entry_price - sl_val
        sl, tp = sl_val, round(entry_price + (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed (Score: {pattern_score})."
    elif final_signal == "STRONG SELL":
        sl_val = round(struct_h, 4)
        risk = sl_val - entry_price
        sl, tp = sl_val, round(entry_price - (risk * 2), 4)
        status_msg = f"100% Criteria Passed! {pattern_name} confirmed (Score: {pattern_score})."
    else:
        status_msg = f"Pattern: {pattern_name} (Score: {pattern_score}) | REJECTED: " + " | ".join(rejected_reasons)

    return {
        "df": df, "pattern": pattern_name, "bias": bias, "score": pattern_score,
        "signal": final_signal, "reason": status_msg, "entry": entry_price, "sl": sl, "tp": tp,
        "close": entry_price, "ema50": round(ema50, 4), "ema200": round(ema200, 4),
        "rsi": round(rsi, 2), "pattern_start": pattern_start, "pattern_end": pattern_end,
        "structural_high": struct_h, "structural_low": struct_l
    }

# ==========================================================
# 5. GEOMETRIC PLOTTER (FIXED POLYGON SHADING)
# ==========================================================
def plot_pattern_geometry(analysis_result):
    df = analysis_result['df']
    p_name = analysis_result['pattern']
    bias = analysis_result['bias']
    p_start = analysis_result['pattern_start']
    p_end = analysis_result['pattern_end']
    
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='orange', width=1.5), name='EMA 50'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='deepskyblue', width=2), name='EMA 200'))

    if p_start and p_end and p_name != "NO PATTERN DETECTED":
        ph = df['Pivot_H'].dropna().loc[p_start:p_end]
        pl = df['Pivot_L'].dropna().loc[p_start:p_end]
        
        if len(ph) >= 1 and len(pl) >= 1:
            h_points = sorted(list(zip(ph.index, ph.values)), key=lambda x: x[0])
            l_points = sorted(list(zip(pl.index, pl.values)), key=lambda x: x[0])

            polygon_points = h_points + l_points[::-1] + [h_points[0]]

            x_coords = [pt[0] for pt in polygon_points]
            y_coords = [pt[1] for pt in polygon_points]

            fill_color = "rgba(46, 204, 113, 0.22)" if bias == "Bullish" else "rgba(231, 76, 60, 0.22)"
            line_color = "#2ecc71" if bias == "Bullish" else "#e74c3c"

            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode='lines',
                fill='toself',
                fillcolor=fill_color,
                line=dict(color=line_color, width=2),
                name=f"Pattern: {p_name} (Score: {analysis_result['score']})"
            ))

            fig.add_trace(go.Scatter(
                x=ph.index, y=ph.values, mode='markers',
                marker=dict(size=8, color='gold', symbol='triangle-down'), name='High Pivots'
            ))
            fig.add_trace(go.Scatter(
                x=pl.index, y=pl.values, mode='markers',
                marker=dict(size=8, color='cyan', symbol='triangle-up'), name='Low Pivots'
            ))

    fig.update_layout(
        title=f"Chart Analysis | Pattern: {p_name} (Score: {analysis_result['score']}) | Signal: {analysis_result['signal']}",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=True
    )
    
    return fig
    
