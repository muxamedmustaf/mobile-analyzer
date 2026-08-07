import pandas as pd
import numpy as np

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aqoonsada 15-ka Chart Patterns ee ugu caansan, qiimeeya ixtimaalka (Probability),
    kuna soo kala sooca sida ay ugu kala ixtimaal badan yihiin adigoo ilaalinaya qaabkii hore.
    Waxaa la raaciyay keydinta dhibcaha taabashada (Pattern_Points) si loogu sawiro fallaarahooda.
    """
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = "" # Kudarista kolamka lagu keydiyo dhibcaha fallaarahooda
    
    if 'Swing_High' not in df.columns or 'Swing_Low' not in df.columns:
        df['Top_3_Patterns'] = "None"
        return df

    highs = df['Swing_High'].dropna()
    lows = df['Swing_Low'].dropna()
    
    scored_patterns = []
    pattern_markers = {} # Keydinta dhibcaha taabashada ee pattern walba

    if len(highs) >= 5 and len(lows) >= 5:
        h1, h2, h3, h4, h5 = highs.iloc[-5], highs.iloc[-4], highs.iloc[-3], highs.iloc[-2], highs.iloc[-1]
        l1, l2, l3, l4, l5 = lows.iloc[-5], lows.iloc[-4], lows.iloc[-3], lows.iloc[-2], lows.iloc[-1]

        # 1. Double Top & Double Bottom
        dt_diff = abs(h5 - h4) / h4
        if dt_diff < 0.003:
            prob = round(92 - (dt_diff * 1000), 1)
            p_name = "Double Top (Reversal)"
            scored_patterns.append((p_name, prob))
            pattern_markers[p_name] = [h4.name, h5.name]

        db_diff = abs(l5 - l4) / l4
        if db_diff < 0.003:
            prob = round(92 - (db_diff * 1000), 1)
            p_name = "Double Bottom (Reversal)"
            scored_patterns.append((p_name, prob))
            pattern_markers[p_name] = [l4.name, l5.name]

        # 2. Triple Top & Triple Bottom
        if abs(h5 - h4) < 0.003 and abs(h4 - h3) < 0.003:
            p_name = "Triple Top (Strong Reversal)"
            scored_patterns.append((p_name, 94.0))
            pattern_markers[p_name] = [h3.name, h4.name, h5.name]
            
        if abs(l5 - l4) < 0.003 and abs(l4 - l3) < 0.003:
            p_name = "Triple Bottom (Strong Reversal)"
            scored_patterns.append((p_name, 94.5))
            pattern_markers[p_name] = [l3.name, l4.name, l5.name]

        # 3. Head and Shoulders & Inverse Head and Shoulders
        if h4 > h3 and h4 > h5 and abs(h3 - h5) / h5 < 0.01:
            p_name = "Head and Shoulders"
            scored_patterns.append((p_name, 88.5))
            pattern_markers[p_name] = [h3.name, h4.name, h5.name]
            
        if l4 < l3 and l4 < l5 and abs(l3 - l5) / l5 < 0.01:
            p_name = "Inverse Head and Shoulders"
            scored_patterns.append((p_name, 89.0))
            pattern_markers[p_name] = [l3.name, l4.name, l5.name]

        # 4. Triangles (Symmetrical, Ascending, Descending)
        if h5 < h4 and l5 > l4:
            p_name = "Symmetrical Triangle"
            scored_patterns.append((p_name, 85.0))
            pattern_markers[p_name] = [h4.name, h5.name, l4.name, l5.name]
        elif abs(h5 - h4) < 0.002 and l5 > l4:
            p_name = "Ascending Triangle"
            scored_patterns.append((p_name, 87.2))
            pattern_markers[p_name] = [h4.name, h5.name, l4.name, l5.name]
        elif h5 < h4 and abs(l5 - l4) < 0.002:
            p_name = "Descending Triangle"
            scored_patterns.append((p_name, 86.5))
            pattern_markers[p_name] = [h4.name, h5.name, l4.name, l5.name]

        # 5. Wedges (Rising & Falling)
        if h5 > h4 and l5 > l4 and (h5 - h4) < (l5 - l4):
            p_name = "Rising Wedge"
            scored_patterns.append((p_name, 82.4))
            pattern_markers[p_name] = [h4.name, h5.name, l4.name, l5.name]
        elif h5 < h4 and l5 < l4 and (h4 - h5) < (l4 - l5):
            p_name = "Falling Wedge"
            scored_patterns.append((p_name, 84.1))
            pattern_markers[p_name] = [h4.name, h5.name, l4.name, l5.name]

        # 6. Rectangles (Bullish & Bearish)
        if abs(h5 - h3) < 0.002 and abs(l5 - l3) < 0.002:
            if h5 > l3:
                p_name = "Bullish Rectangle"
                scored_patterns.append((p_name, 83.0))
            else:
                p_name = "Bearish Rectangle"
                scored_patterns.append((p_name, 83.0))
            pattern_markers[p_name] = [h3.name, h5.name, l3.name, l5.name]

        # 7. Flags & Pennants
        if abs(h5 - h4) < 0.001 and abs(l5 - l4) < 0.001 and h5 > l5:
            p_name = "Bullish Flag / Pennant"
            scored_patterns.append((p_name, 81.5))
            pattern_markers[p_name] = [h4.name, h5.name]
        elif abs(h5 - h4) < 0.001 and abs(l5 - l4) < 0.001 and h5 < l5:
            p_name = "Bearish Flag / Pennant"
            scored_patterns.append((p_name, 81.5))
            pattern_markers[p_name] = [h4.name, h5.name]

        # 8. Cup and Handle
        if l4 < l3 and l4 < l5 and h5 > h3 * 0.98 and abs(l5 - l4) < abs(l4 - l3) * 0.5:
            p_name = "Cup and Handle"
            scored_patterns.append((p_name, 90.0))
            pattern_markers[p_name] = [l3.name, l4.name, l5.name, h5.name]

    # Heerarka guud haddii aysan ku filnaan
    defaults = [
        ("Support / Resistance Bounce", 78.0),
        ("Consolidation Channel", 75.5),
        ("Market Equilibrium", 70.0)
    ]
    
    for p, pr in defaults:
        if not any(p == existing[0] for existing in scored_patterns):
            scored_patterns.append((p, pr))
            pattern_markers[p] = []

    # U kala saار sida uu ixtimaalkoodu u sarreeyo
    scored_patterns.sort(key=lambda x: x[1], reverse=True)
    
    # Soo qaadashada 3-da ugu sarreeya
    top_three = scored_patterns[:3]
    
    formatted_str = " | ".join([f"{name} ({prob}%)" for name, prob in top_three])

    best_pattern = top_three[0][0]
    df['Top_3_Patterns'] = formatted_str
    df.loc[df.index[-1], 'Pattern'] = best_pattern
    
    # Kaydinta dhibcaha pattern-ka ugu sarreeya si loogu saaro fallaaro/calaamado
    if best_pattern in pattern_markers:
        df.loc[df.index[-1], 'Pattern_Points'] = str(pattern_markers[best_pattern])

    return df
        
