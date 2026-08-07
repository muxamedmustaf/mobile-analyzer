import pandas as pd
import numpy as np

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = ""
    
    # Hubinta in column-yada muhiimka ah ay jiraan
    required = ['High', 'Low', 'Close', 'Swing_High', 'Swing_Low']
    for col in required:
        if col not in df.columns:
            return df

    # ATR si loo xaqiijiyo tolerance-ka
    if 'ATR' not in df.columns:
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        df['ATR'] = np.max(ranges, axis=1).rolling(14).mean()

    highs = df[df['Swing_High'].notna()]['Swing_High']
    lows = df[df['Swing_Low'].notna()]['Swing_Low']
    
    if len(highs) < 3 or len(lows) < 3:
        return df

    scored_patterns = []
    pattern_coords = {}
    
    current_close = df['Close'].iloc[-1]
    current_atr = df['ATR'].iloc[-1] if not pd.isna(df['ATR'].iloc[-1]) else (current_close * 0.01)

    h_dates = highs.index[-3:]
    l_dates = lows.index[-3:]
    h3, h4, h5 = highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
    l3, l4, l5 = lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]

    # --- 1. DOUBLE TOP (Shuruudda: Labada High waa inay isku dhow yihiin + Neckline Breakout) ---
    if abs(h5 - h4) <= (2.0 * current_atr) and (abs(h5 - h4) / h4) <= 0.01:
        # Raadi neckline-ka u dhexeeya labada high (Low-kii u dambeeyay inta u dhaxaysa)
        between_lows = lows[(lows.index > h_dates[1]) & (lows.index < h_dates[2])]
        if not between_lows.empty:
            neckline = between_lows.iloc[-1]
            # Shuruudda ganacsiga: Waa in qiimuhu jabiyo neckline-ka (Breakout confirmed)
            if current_close < neckline:
                scored_patterns.append(("Double Top (Reversal)", 96.0))
                pattern_coords["Double Top (Reversal)"] = [
                    (h_dates[1], h4, "Top 1"), 
                    (h_dates[2], h5, "Top 2")
                ]

    # --- 2. DOUBLE BOTTOM (Shuruudda: Labada Low waa inay isku dhow yihiin + Neckline Breakout) ---
    if abs(l5 - l4) <= (2.0 * current_atr) and (abs(l5 - l4) / l4) <= 0.01:
        between_highs = highs[(highs.index > l_dates[1]) & (highs.index < l_dates[2])]
        if not between_highs.empty:
            neckline = between_highs.iloc[-1]
            # Shuruudda ganacsiga: Waa in qiimuhu jabiyo neckline-ka kor u kac ah
            if current_close > neckline:
                scored_patterns.append(("Double Bottom (Reversal)", 96.0))
                pattern_coords["Double Bottom (Reversal)"] = [
                    (l_dates[1], l4, "Bottom 1"), 
                    (l_dates[2], l5, "Bottom 2")
                ]

    # --- 3. HEAD AND SHOULDERS (Shuruudda: Head waa inuu ka sarreeyaa shoulders-ka + Neckline breakout) ---
    if h4 > h3 and h4 > h5 and abs(h3 - h5) <= (2.0 * current_atr):
        # Helitaanka neckline-ka labada hoose ee u dhexeeya
        between_lows = lows[(lows.index > h_dates[0]) & (lows.index < h_dates[2])]
        if len(between_lows) >= 2:
            neckline = between_lows.min()
            if current_close < neckline:
                scored_patterns.append(("Head and Shoulders", 94.0))
                pattern_coords["Head and Shoulders"] = [
                    (h_dates[0], h3, "Left Shoulder"),
                    (h_dates[1], h4, "Head"),
                    (h_dates[2], h5, "Right Shoulder")
                ]

    # --- 4. INVERSE HEAD AND SHOULDERS ---
    if l4 < l3 and l4 < l5 and abs(l3 - l5) <= (2.0 * current_atr):
        between_highs = highs[(highs.index > l_dates[0]) & (highs.index < l_dates[2])]
        if len(between_highs) >= 2:
            neckline = between_highs.max()
            if current_close > neckline:
                scored_patterns.append(("Inverse Head and Shoulders", 94.0))
                pattern_coords["Inverse Head and Shoulders"] = [
                    (l_dates[0], l3, "Left Low"),
                    (l_dates[1], l4, "Head Low"),
                    (l_dates[2], l5, "Right Low")
                ]

    # Kaydinta pattern-ka ugu sarreeya ee shuruudaha buuxiyay
    if scored_patterns:
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best = scored_patterns[0]
        df.loc[df.index[-1], 'Pattern'] = best[0]
        if best[0] in pattern_coords:
            pts = [f"{time}_{val}_{label}" for time, val, label in pattern_coords[best[0]]]
            df.loc[df.index[-1], 'Pattern_Points'] = ",".join(pts)

    return df
    
