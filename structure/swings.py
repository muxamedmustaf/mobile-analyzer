import pandas as pd
import numpy as np

def calculate_zigzag(df: pd.DataFrame, period=10, deviation=5.0, backstep=5) -> pd.DataFrame:
    """
    Xisaabinta ZigZag dhab ah oo ku saleysan Period, Deviation (%), iyo Backstep 
    adigoo meesha ka saaray ATR gebi ahaanba.
    """
    df = df.copy()
    df['ZigZag'] = np.nan
    df['Swing_Type'] = None
    
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)
    
    if n < period:
        return df

    last_pivot_idx = 0
    last_pivot_val = highs[0]
    trend = 0  # 1 = up, -1 = down
    
    for i in range(period, n):
        current_high = highs[i]
        current_low = lows[i]
        
        if trend == 0:
            if current_high >= last_pivot_val * (1 + deviation / 100.0):
                trend = 1
                last_pivot_idx = i
                last_pivot_val = current_high
            elif current_low <= last_pivot_val * (1 - deviation / 100.0):
                trend = -1
                last_pivot_idx = i
                last_pivot_val = current_low
        elif trend == 1:
            if current_high >= last_pivot_val:
                last_pivot_val = current_high
                last_pivot_idx = i
            elif current_low <= last_pivot_val * (1 - deviation / 100.0):
                # Saxitaanka Swing High oo la xaqiijiyay
                df.loc[df.index[last_pivot_idx], 'ZigZag'] = last_pivot_val
                df.loc[df.index[last_pivot_idx], 'Swing_Type'] = 'High'
                trend = -1
                last_pivot_val = current_low
                last_pivot_idx = i
        elif trend == -1:
            if current_low <= last_pivot_val:
                last_pivot_val = current_low
                last_pivot_idx = i
            elif current_high >= last_pivot_val * (1 + deviation / 100.0):
                # Saxitaanka Swing Low oo la xaqiijiyay
                df.loc[df.index[last_pivot_idx], 'ZigZag'] = last_pivot_val
                df.loc[df.index[last_pivot_idx], 'Swing_Type'] = 'Low'
                trend = 1
                last_pivot_val = current_high
                last_pivot_idx = i
                
    return df

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = ""
    
    required = ['High', 'Low', 'Close']
    for col in required:
        if col not in df.columns:
            return df

    # Ku shaqaynta ZigZag oo kaliya (Period=10, Deviation=5.0, Backstep=5)
    df = calculate_zigzag(df, period=10, deviation=5.0, backstep=5)
    
    highs = df[df['Swing_Type'] == 'High']['ZigZag'].dropna()
    lows = df[df['Swing_Type'] == 'Low']['ZigZag'].dropna()
    
    if len(highs) < 5 or len(lows) < 5:
        return df

    scored_patterns = []
    pattern_coords = {}
    
    current_close = df['Close'].iloc[-1]

    h_dates = highs.index[-5:]
    l_dates = lows.index[-5:]
    
    h1, h2, h3, h4, h5 = highs.iloc[-5], highs.iloc[-4], highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
    l1, l2, l3, l4, l5 = lows.iloc[-5], lows.iloc[-4], lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]

    # --- 1. DOUBLE TOP (Farqiga ≤ 0.5%) ---
    if abs(h5 - h4) / h4 <= 0.005:
        between_lows = lows[(lows.index > h_dates[3]) & (lows.index < h_dates[4])]
        if not between_lows.empty and current_close < between_lows.iloc[-1]:
            scored_patterns.append(("Double Top", 96.0))
            pattern_coords["Double Top"] = [(h_dates[3], h4, "Top 1"), (h_dates[4], h5, "Top 2")]

    # --- 2. DOUBLE BOTTOM (Farqiga ≤ 0.5%) ---
    if abs(l5 - l4) / l4 <= 0.005:
        between_highs = highs[(highs.index > l_dates[3]) & (highs.index < l_dates[4])]
        if not between_highs.empty and current_close > between_highs.iloc[-1]:
            scored_patterns.append(("Double Bottom", 96.0))
            pattern_coords["Double Bottom"] = [(l_dates[3], l4, "Bottom 1"), (l_dates[4], l5, "Bottom 2")]

    # --- 3. TRIPLE TOP (Farqiga kasta ≤ 0.5%) ---
    if (abs(h5 - h4) / h4 <= 0.005) and (abs(h4 - h3) / h3 <= 0.005):
        between_lows = lows[(lows.index > h_dates[2]) & (lows.index < h_dates[4])]
        if not between_lows.empty and current_close < between_lows.min():
            scored_patterns.append(("Triple Top", 97.0))
            pattern_coords["Triple Top"] = [(h_dates[2], h3, "Top 1"), (h_dates[3], h4, "Top 2"), (h_dates[4], h5, "Top 3")]

    # --- 4. TRIPLE BOTTOM (Farqiga kasta ≤ 0.5%) ---
    if (abs(l5 - l4) / l4 <= 0.005) and (abs(l4 - l3) / l3 <= 0.005):
        between_highs = highs[(highs.index > l_dates[2]) & (highs.index < l_dates[4])]
        if not between_highs.empty and current_close > between_highs.max():
            scored_patterns.append(("Triple Bottom", 97.0))
            pattern_coords["Triple Bottom"] = [(l_dates[2], l3, "Bottom 1"), (l_dates[3], l4, "Bottom 2"), (l_dates[4], l5, "Bottom 3")]

    # --- 5. HEAD AND SHOULDERS ---
    if h4 > h3 and h4 > h5 and abs(h3 - h5) / h5 <= 0.01:
        between_lows = lows[(lows.index > h_dates[2]) & (lows.index < h_dates[4])]
        if not between_lows.empty and current_close < between_lows.min():
            scored_patterns.append(("Head and Shoulders", 95.0))
            pattern_coords["Head and Shoulders"] = [(h_dates[2], h3, "Left Shoulder"), (h_dates[3], h4, "Head"), (h_dates[4], h5, "Right Shoulder")]

    # --- 6. INVERSE HEAD AND SHOULDERS ---
    if l4 < l3 and l4 < l5 and abs(l3 - l5) / l5 <= 0.01:
        between_highs = highs[(highs.index > l_dates[2]) & (highs.index < l_dates[4])]
        if not between_highs.empty and current_close > between_highs.max():
            scored_patterns.append(("Inverse Head and Shoulders", 95.0))
            pattern_coords["Inverse Head and Shoulders"] = [(l_dates[2], l3, "Left Low"), (l_dates[3], l4, "Head Low"), (l_dates[4], l5, "Right Low")]

    # --- 7. ASCENDING TRIANGLE ---
    if abs(h5 - h4) / h4 <= 0.005 and l5 > l4 and current_close > h5:
        scored_patterns.append(("Ascending Triangle", 93.0))
        pattern_coords["Ascending Triangle"] = [(h_dates[3], h4, "Resistance 1"), (h_dates[4], h5, "Resistance 2")]

    # --- 8. DESCENDING TRIANGLE ---
    if abs(l5 - l4) / l4 <= 0.005 and h5 < h4 and current_close < l5:
        scored_patterns.append(("Descending Triangle", 93.0))
        pattern_coords["Descending Triangle"] = [(l_dates[3], l4, "Support 1"), (l_dates[4], l5, "Support 2")]

    # --- 9. SYMMETRICAL TRIANGLE ---
    if h5 < h4 and l5 > l4:
        scored_patterns.append(("Symmetrical Triangle", 90.0))
        pattern_coords["Symmetrical Triangle"] = [(h_dates[4], h5, "High"), (l_dates[4], l5, "Low")]

    # --- 10. RISING WEDGE ---
    if h5 > h4 and l5 > l4 and (h5 - h4) < (l5 - l4) and current_close < l5:
        scored_patterns.append(("Rising Wedge", 91.0))
        pattern_coords["Rising Wedge"] = [(h_dates[4], h5, "High"), (l_dates[4], l5, "Low")]

    # --- 11. FALLING WEDGE ---
    if h5 < h4 and l5 < l4 and (h4 - h5) < (l4 - l5) and current_close > h5:
        scored_patterns.append(("Falling Wedge", 91.0))
        pattern_coords["Falling Wedge"] = [(h_dates[4], h5, "High"), (l_dates[4], l5, "Low")]

    # --- 12. BULL FLAG ---
    if h5 > h3 and l5 > l3 and current_close > h5:
        scored_patterns.append(("Bull Flag", 92.0))
        pattern_coords["Bull Flag"] = [(h_dates[4], h5, "Flag High"), (l_dates[4], l5, "Flag Low")]

    # --- 13. BEAR FLAG ---
    if h5 < h3 and l5 < l3 and current_close < l5:
        scored_patterns.append(("Bear Flag", 92.0))
        pattern_coords["Bear Flag"] = [(h_dates[4], h5, "Flag High"), (l_dates[4], l5, "Flag Low")]

    # --- 14. BULL PENNANT ---
    if h5 < h4 and l5 > l4 and current_close > h5:
        scored_patterns.append(("Bull Pennant", 90.0))
        pattern_coords["Bull Pennant"] = [(h_dates[4], h5, "Pennant Top"), (l_dates[4], l5, "Pennant Bottom")]

    # --- 15. BEAR PENNANT ---
    if h5 < h4 and l5 > l4 and current_close < l5:
        scored_patterns.append(("Bear Pennant", 90.0))
        pattern_coords["Bear Pennant"] = [(h_dates[4], h5, "Pennant Top"), (l_dates[4], l5, "Pennant Bottom")]

    # --- 16. RECTANGLE ---
    if abs(h5 - h4) / h4 <= 0.005 and abs(l5 - l4) / l4 <= 0.005:
        scored_patterns.append(("Rectangle", 92.0))
        pattern_coords["Rectangle"] = [(h_dates[4], h5, "Resistance"), (l_dates[4], l5, "Support")]

    # --- 17. CUP AND HANDLE ---
    if l5 > l4 and h5 < h4 and current_close > h4:
        scored_patterns.append(("Cup and Handle", 94.0))
        pattern_coords["Cup and Handle"] = [(l_dates[4], l5, "Handle Low"), (h_dates[4], h4, "Rim")]

    # --- 18. ROUNDING BOTTOM ---
    if l5 > l4 and l4 < l3 and current_close > h5:
        scored_patterns.append(("Rounding Bottom", 93.0))
        pattern_coords["Rounding Bottom"] = [(l_dates[4], l5, "Bottom Center")]

    # --- 19. BROADENING FORMATION ---
    if h5 > h4 and l5 < l4:
        scored_patterns.append(("Broadening Formation", 89.0))
        pattern_coords["Broadening Formation"] = [(h_dates[4], h5, "High"), (l_dates[4], l5, "Low")]

    # --- 20. DIAMOND TOP ---
    if h5 < h4 and l5 > l4 and current_close < l5:
        scored_patterns.append(("Diamond Top", 95.0))
        pattern_coords["Diamond Top"] = [(h_dates[4], h5, "Apex High"), (l_dates[4], l5, "Apex Low")]

    # --- 21. TRIPLE TOP REVERSAL ---
    if (abs(h5 - h4) / h4 <= 0.005) and current_close < l5:
        scored_patterns.append(("Triple Top Reversal", 96.0))
        pattern_coords["Triple Top Reversal"] = [(h_dates[4], h5, "Top 3")]

    # --- 22. TRIPLE BOTTOM REVERSAL ---
    if (abs(l5 - l4) / l4 <= 0.005) and current_close > h5:
        scored_patterns.append(("Triple Bottom Reversal", 96.0))
        pattern_coords["Triple Bottom Reversal"] = [(l_dates[4], l5, "Bottom 3")]

    # --- 23. BUMP AND RUN REVERSAL ---
    if h5 > h4 * 1.05:
        scored_patterns.append(("Bump and Run Reversal", 91.0))
        pattern_coords["Bump and Run Reversal"] = [(h_dates[4], h5, "Bump High")]

    # --- 24. HOOK REVERSAL ---
    if h5 > h4 and current_close < df['Close'].iloc[-2]:
        scored_patterns.append(("Hook Reversal", 88.0))
        pattern_coords["Hook Reversal"] = [(h_dates[4], h5, "Hook High")]

    # --- 25. ISLAND REVERSAL ---
    if abs(df['Low'].iloc[-1] - df['High'].iloc[-2]) > (df['Close'].iloc[-1] * 0.01):
        scored_patterns.append(("Island Reversal", 94.0))
        pattern_coords["Island Reversal"] = [(df.index[-1], current_close, "Island")]

    # --- 26. TRAY PATTERN ---
    if abs(l5 - l4) / l4 <= 0.005 and h5 > h4:
        scored_patterns.append(("Tray Pattern", 89.0))
        pattern_coords["Tray Pattern"] = [(l_dates[4], l5, "Tray Base")]

    # --- 27. PIPE TOP ---
    if abs(h5 - h4) / h4 <= 0.002 and current_close < l5:
        scored_patterns.append(("Pipe Top", 90.0))
        pattern_coords["Pipe Top"] = [(h_dates[4], h5, "Pipe")]

    # --- 28. PIPE BOTTOM ---
    if abs(l5 - l4) / l4 <= 0.002 and current_close > h5:
        scored_patterns.append(("Pipe Bottom", 90.0))
        pattern_coords["Pipe Bottom"] = [(l_dates[4], l5, "Pipe")]

    # --- 29. TOWER TOP ---
    if h5 > h4 and current_close < l5:
        scored_patterns.append(("Tower Top", 91.0))
        pattern_coords["Tower Top"] = [(h_dates[4], h5, "Tower")]

    # --- 30. TOWER BOTTOM ---
    if l5 < l4 and current_close > h5:
        scored_patterns.append(("Tower Bottom", 91.0))
        pattern_coords["Tower Bottom"] = [(l_dates[4], l5, "Tower")]

    if scored_patterns:
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best = scored_patterns[0]
        df.loc[df.index[-1], 'Pattern'] = best[0]
        if best[0] in pattern_coords:
            pts = [f"{time}_{val}_{label}" for time, val, label in pattern_coords[best[0]]]
            df.loc[df.index[-1], 'Pattern_Points'] = ",".join(pts)

    return df
    
