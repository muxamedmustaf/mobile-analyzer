import pandas as pd
import numpy as np

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aqoonsada 15-ka Chart Patterns iyadoo dhibcaha si sax ah loogu hagaajiyay 
    sida ay taariikh ahaan ugu kala horreeyaan shaxda dhexdeeda.
    """
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = ""
    
    if 'Swing_High' not in df.columns or 'Swing_Low' not in df.columns:
        df['Top_3_Patterns'] = "None"
        return df

    highs = df['Swing_High'].dropna()
    lows = df['Swing_Low'].dropna()
    
    scored_patterns = []
    pattern_coords = {}

    if len(highs) >= 5 and len(lows) >= 5:
        h1, h2, h3, h4, h5 = highs.iloc[-5], highs.iloc[-4], highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
        l1, l2, l3, l4, l5 = lows.iloc[-5], lows.iloc[-4], lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]
        
        h_dates = highs.index[-5:]
        l_dates = lows.index[-5:]

        # 1. Double Top & Double Bottom
        dt_diff = abs(h5 - h4) / h4
        if dt_diff < 0.003 and h3 > h4 and h3 > h5:
            prob = round(92 - (dt_diff * 1000), 1)
            p_name = "Double Top (Reversal)"
            scored_patterns.append((p_name, prob))
            pattern_coords[p_name] = [(h_dates[3], h4), (h_dates[4], h5)]

        db_diff = abs(l5 - l4) / l4
        if db_diff < 0.003 and l3 < l4 and l3 < l5:
            prob = round(92 - (db_diff * 1000), 1)
            p_name = "Double Bottom (Reversal)"
            scored_patterns.append((p_name, prob))
            pattern_coords[p_name] = [(l_dates[3], l4), (l_dates[4], l5)]

        # 2. Triple Top & Triple Bottom
        if abs(h5 - h4) < 0.003 and abs(h4 - h3) < 0.003:
            p_name = "Triple Top (Strong Reversal)"
            scored_patterns.append((p_name, 94.0))
            pattern_coords[p_name] = [(h_dates[2], h3), (h_dates[3], h4), (h_dates[4], h5)]
            
        if abs(l5 - l4) < 0.003 and abs(l4 - l3) < 0.003:
            p_name = "Triple Bottom (Strong Reversal)"
            scored_patterns.append((p_name, 94.5))
            pattern_coords[p_name] = [(l_dates[2], l3), (l_dates[3], l4), (l_dates[4], l5)]

        # 3. Head and Shoulders & Inverse Head and Shoulders (Sida saxda ah ee Left -> Head -> Right)
        if h4 > h3 and h4 > h5 and abs(h3 - h5) / h5 < 0.02:
            p_name = "Head and Shoulders"
            scored_patterns.append((p_name, 88.5))
            # Halkaan waxaa lagu kala soocay si dhibcuhu u raacaan waqtiga (Left, Head, Right)
            pattern_coords[p_name] = [(h_dates[2], h3), (h_dates[3], h4), (h_dates[4], h5)]
            
        if l4 < l3 and l4 < l5 and abs(l3 - l5) / l5 < 0.02:
            p_name = "Inverse Head and Shoulders"
            scored_patterns.append((p_name, 89.0))
            pattern_coords[p_name] = [(l_dates[2], l3), (l_dates[3], l4), (l_dates[4], l5)]

        # 4. Triangles
        if h5 < h4 and l5 > l4:
            p_name = "Symmetrical Triangle"
            scored_patterns.append((p_name, 85.0))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]
        elif abs(h5 - h4) < 0.002 and l5 > l4:
            p_name = "Ascending Triangle"
            scored_patterns.append((p_name, 87.2))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]
        elif h5 < h4 and abs(l5 - l4) < 0.002:
            p_name = "Descending Triangle"
            scored_patterns.append((p_name, 86.5))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]

        # 5. Wedges
        if h5 > h4 and l5 > l4 and (h5 - h4) < (l5 - l4):
            p_name = "Rising Wedge"
            scored_patterns.append((p_name, 82.4))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]
        elif h5 < h4 and l5 < l4 and (h4 - h5) < (l4 - l5):
            p_name = "Falling Wedge"
            scored_patterns.append((p_name, 84.1))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]

        # 6. Rectangles
        if abs(h5 - h3) < 0.003 and abs(l5 - l3) < 0.003:
            p_name = "Bullish Rectangle" if h5 > l3 else "Bearish Rectangle"
            scored_patterns.append((p_name, 83.0))
            pattern_coords[p_name] = [(h_dates[4], h5), (l_dates[4], l5)]

        # 7. Flags & Pennants
        if abs(h5 - h4) < 0.0015 and abs(l5 - l4) < 0.0015:
            p_name = "Bullish Flag / Pennant" if h5 > l5 else "Bearish Flag / Pennant"
            scored_patterns.append((p_name, 81.5))
            pattern_coords[p_name] = [(h_dates[4], h5)]

        # 8. Cup and Handle
        if l4 < l3 and l4 < l5 and h5 > h3 * 0.98:
            p_name = "Cup and Handle"
            scored_patterns.append((p_name, 90.0))
            pattern_coords[p_name] = [(l_dates[3], l4), (h_dates[4], h5)]

    defaults = [
        ("Support / Resistance Bounce", 78.0),
        ("Consolidation Channel", 75.5),
        ("Market Equilibrium", 70.0)
    ]
    
    for p, pr in defaults:
        if not any(p == existing[0] for existing in scored_patterns):
            scored_patterns.append((p, pr))
            pattern_coords[p] = []

    scored_patterns.sort(key=lambda x: x[1], reverse=True)
    top_three = scored_patterns[:3]
    
    formatted_str = " | ".join([f"{name} ({prob}%)" for name, prob in top_three])
    df['Top_3_Patterns'] = formatted_str
    
    best_pattern = top_three[0][0]
    if any(x in best_pattern for x in ["Bottom", "Inverse", "Bullish", "Falling Wedge", "Ascending", "Bounce"]):
        df.loc[df.index[-1], 'Pattern'] = f"▲ {best_pattern}"
    elif any(x in best_pattern for x in ["Top", "Head and Shoulders", "Bearish", "Rising Wedge", "Descending"]):
        df.loc[df.index[-1], 'Pattern'] = f"▼ {best_pattern}"
    else:
        df.loc[df.index[-1], 'Pattern'] = f"◆ {best_pattern}"

    if best_pattern in pattern_coords and pattern_coords[best_pattern]:
        # Si loo hubiyo in dhibcuhu u kala soocmaan si sax ah
        sorted_pts = sorted(pattern_coords[best_pattern], key=lambda x: str(x[0]))
        coords_str = ",".join([f"{time}_{val}" for time, val in sorted_pts])
        df.loc[df.index[-1], 'Pattern_Points'] = coords_str

    return df
    
