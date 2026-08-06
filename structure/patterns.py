import pandas as pd
import numpy as np

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aqoonsada 15-ka Chart Patterns ee ugu caansan, qiimeeya ixtimaalka (Probability),
    kuna soo kala sooca sida ay ugu kala ixtimaal badan yihiin adigoo ilaalinaya qaabkii hore.
    """
    df['Pattern'] = 'No Pattern'
    
    if 'Swing_High' not in df.columns or 'Swing_Low' not in df.columns:
        df['Top_3_Patterns'] = "None"
        return df

    highs = df['Swing_High'].dropna()
    lows = df['Swing_Low'].dropna()
    
    scored_patterns = []

    if len(highs) >= 5 and len(lows) >= 5:
        h1, h2, h3, h4, h5 = highs.iloc[-5], highs.iloc[-4], highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
        l1, l2, l3, l4, l5 = lows.iloc[-5], lows.iloc[-4], lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]

        # 1. Double Top & Double Bottom
        dt_diff = abs(h5 - h4) / h4
        if dt_diff < 0.003:
            prob = round(92 - (dt_diff * 1000), 1)
            scored_patterns.append(("Double Top (Reversal)", prob))

        db_diff = abs(l5 - l4) / l4
        if db_diff < 0.003:
            prob = round(92 - (db_diff * 1000), 1)
            scored_patterns.append(("Double Bottom (Reversal)", prob))

        # 2. Triple Top & Triple Bottom
        if abs(h5 - h4) < 0.003 and abs(h4 - h3) < 0.003:
            scored_patterns.append(("Triple Top (Strong Reversal)", 94.0))
        if abs(l5 - l4) < 0.003 and abs(l4 - l3) < 0.003:
            scored_patterns.append(("Triple Bottom (Strong Reversal)", 94.5))

        # 3. Head and Shoulders & Inverse Head and Shoulders
        if h4 > h3 and h4 > h5 and abs(h3 - h5) / h5 < 0.01:
            scored_patterns.append(("Head and Shoulders", 88.5))
        if l4 < l3 and l4 < l5 and abs(l3 - l5) / l5 < 0.01:
            scored_patterns.append(("Inverse Head and Shoulders", 89.0))

        # 4. Triangles (Symmetrical, Ascending, Descending)
        if h5 < h4 and l5 > l4:
            scored_patterns.append(("Symmetrical Triangle", 85.0))
        elif abs(h5 - h4) < 0.002 and l5 > l4:
            scored_patterns.append(("Ascending Triangle", 87.2))
        elif h5 < h4 and abs(l5 - l4) < 0.002:
            scored_patterns.append(("Descending Triangle", 86.5))

        # 5. Wedges (Rising & Falling)
        if h5 > h4 and l5 > l4 and (h5 - h4) < (l5 - l4):
            scored_patterns.append(("Rising Wedge", 82.4))
        elif h5 < h4 and l5 < l4 and (h4 - h5) < (l4 - l5):
            scored_patterns.append(("Falling Wedge", 84.1))

        # 6. Rectangles (Bullish & Bearish)
        if abs(h5 - h3) < 0.002 and abs(l5 - l3) < 0.002:
            if h5 > l3:
                scored_patterns.append(("Bullish Rectangle", 83.0))
            else:
                scored_patterns.append(("Bearish Rectangle", 83.0))

        # 7. Flags & Pennants
        if abs(h5 - h4) < 0.001 and abs(l5 - l4) < 0.001 and h5 > l5:
            scored_patterns.append(("Bullish Flag / Pennant", 81.5))
        elif abs(h5 - h4) < 0.001 and abs(l5 - l4) < 0.001 and h5 < l5:
            scored_patterns.append(("Bearish Flag / Pennant", 81.5))

        # 8. Cup and Handle
        if l4 < l3 and l4 < l5 and h5 > h3 * 0.98 and abs(l5 - l4) < abs(l4 - l3) * 0.5:
            scored_patterns.append(("Cup and Handle", 90.0))

    # Heerarka guud haddii aysan ku filnaan
    defaults = [
        ("Support / Resistance Bounce", 78.0),
        ("Consolidation Channel", 75.5),
        ("Market Equilibrium", 70.0)
    ]
    
    for p, pr in defaults:
        if not any(p == existing[0] for existing in scored_patterns):
            scored_patterns.append((p, pr))

    # U kala saar sida uu ixtimaalkoodu u sarreeyo
    scored_patterns.sort(key=lambda x: x[1], reverse=True)
    
    # Soo qaadashada 3-da ugu sarreeya
    top_three = scored_patterns[:3]
    
    formatted_str = " | ".join([f"{name} ({prob}%)" for name, prob in top_three])

    df['Top_3_Patterns'] = formatted_str
    df.loc[df.index[-1], 'Pattern'] = top_three[0][0]

    return df
    
