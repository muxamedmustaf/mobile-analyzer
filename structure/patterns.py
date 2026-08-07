import pandas as pd
import numpy as np

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = ""
    
    if 'Swing_High' not in df.columns or 'Swing_Low' not in df.columns:
        return df

    highs = df['Swing_High'].dropna()
    lows = df['Swing_Low'].dropna()
    
    if len(highs) < 5 or len(lows) < 5:
        return df

    h3, h4, h5 = highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
    l3, l4, l5 = lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]
    h_dates = highs.index[-3:]
    l_dates = lows.index[-3:]

    scored_patterns = []
    pattern_coords = {}

    # --- 1% Farqiga ugu badan & 3% Dhaqaaq Caksiya ---
    
    # Double Top (Farqiga u dhexeeya h4 iyo h5 waa inuu ka yar yahay ama la siman yahay 1% -> 0.01)
    dt_diff = abs(h5 - h4) / h4
    if dt_diff <= 0.01 and (h4 - h3) / h4 >= 0.03:
        prob = round(95.0 - (dt_diff * 100), 1)
        scored_patterns.append(("Double Top (Reversal)", prob))
        pattern_coords["Double Top (Reversal)"] = [(h_dates[1], h4), (h_dates[2], h5)]

    # Double Bottom
    db_diff = abs(l5 - l4) / l4
    if db_diff <= 0.01 and (l3 - l4) / l4 >= 0.03:
        prob = round(95.0 - (db_diff * 100), 1)
        scored_patterns.append(("Double Bottom (Reversal)", prob))
        pattern_coords["Double Bottom (Reversal)"] = [(l_dates[1], l4), (l_dates[2], l5)]

    # Triple Top
    if abs(h5 - h4) / h4 <= 0.01 and abs(h4 - h3) / h3 <= 0.01:
        scored_patterns.append(("Triple Top (Strong Reversal)", 96.5))
        pattern_coords["Triple Top (Strong Reversal)"] = [(h_dates[0], h3), (h_dates[1], h4), (h_dates[2], h5)]

    # Triple Bottom
    if abs(l5 - l4) / l4 <= 0.01 and abs(l4 - l3) / l3 <= 0.01:
        scored_patterns.append(("Triple Bottom (Strong Reversal)", 97.0))
        pattern_coords["Triple Bottom (Strong Reversal)"] = [(l_dates[0], l3), (l_dates[1], l4), (l_dates[2], l5)]

    # Head and Shoulders (Garabka bidix iyo midig farqigoodu waa inuu ka yar yahay 1%)
    hs_diff = abs(h3 - h5) / h5
    if hs_diff <= 0.01 and (h4 - h3) / h3 >= 0.03:
        scored_patterns.append(("Head and Shoulders", 92.0))
        pattern_coords["Head and Shoulders"] = [(h_dates[0], h3), (h_dates[1], h4), (h_dates[2], h5)]

    # Inverse Head and Shoulders
    ihs_diff = abs(l3 - l5) / l5
    if ihs_diff <= 0.01 and (l3 - l4) / l3 >= 0.03:
        scored_patterns.append(("Inverse Head and Shoulders", 92.0))
        pattern_coords["Inverse Head and Shoulders"] = [(l_dates[0], l3), (l_dates[1], l4), (l_dates[2], l5)]

    # Rectangles
    if abs(h5 - h4) / h4 <= 0.01 and abs(l5 - l4) / l4 <= 0.01 and (h4 - l4) / l4 >= 0.03:
        p_name = "Bullish Rectangle" if h5 > l5 else "Bearish Rectangle"
        scored_patterns.append((p_name, 90.0))
        pattern_coords[p_name] = [(h_dates[1], h4), (h_dates[2], h5), (l_dates[1], l4), (l_dates[2], l5)]

    # Nidaamka kala saaridda natiijada ugu fiican
    if scored_patterns:
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best = scored_patterns[0]
        df.loc[df.index[-1], 'Pattern'] = best[0]
        if best[0] in pattern_coords:
            pts = [f"{t}_{v}" for t, v in pattern_coords[best[0]]]
            df.loc[df.index[-1], 'Pattern_Points'] = ",".join(pts)

    return df
    
