import pandas as pd
import numpy as np

def calculate_zigzag(df: pd.DataFrame, deviation=0.03) -> pd.DataFrame:
    """
    Xisaabinta ZigZag si loo helo Swing High iyo Swing Low dhab ah 
    oo leh fogaan/dhaqaaq caksiya oo ugu yaraan ah deviation-ka la cayimay (tusaale 3% -> 0.03).
    """
    df['ZigZag'] = np.nan
    df['Swing_Type'] = None # 'High' ama 'Low'
    
    last_pivot_price = df['Close'].iloc[0]
    last_pivot_idx = 0
    trend = 0 # 1 kor, -1 hoos
    
    for i in range(1, len(df)):
        current_price = df['Close'].iloc[i]
        change = (current_price - last_pivot_price) / last_pivot_price
        
        if trend == 0:
            if change >= deviation:
                trend = 1
                last_pivot_price = current_price
                last_pivot_idx = i
            elif change <= -deviation:
                trend = -1
                last_pivot_price = current_price
                last_pivot_idx = i
        elif trend == 1:
            if current_price > last_pivot_price:
                last_pivot_price = current_price
                last_pivot_idx = i
            elif (last_pivot_price - current_price) / last_pivot_price >= deviation:
                df.loc[df.index[last_pivot_idx], 'ZigZag'] = last_pivot_price
                df.loc[df.index[last_pivot_idx], 'Swing_Type'] = 'High'
                trend = -1
                last_pivot_price = current_price
                last_pivot_idx = i
        elif trend == -1:
            if current_price < last_pivot_price:
                last_pivot_price = current_price
                last_pivot_idx = i
            elif (current_price - last_pivot_price) / last_pivot_price >= deviation:
                df.loc[df.index[last_pivot_idx], 'ZigZag'] = last_pivot_price
                df.loc[df.index[last_pivot_idx], 'Swing_Type'] = 'Low'
                trend = 1
                last_pivot_price = current_price
                last_pivot_idx = i
                
    return df

def detect_chart_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df['Pattern'] = 'No Pattern'
    df['Pattern_Points'] = ""
    
    # Hubinta in ZigZag la isticmaalay
    df = calculate_zigzag(df, deviation=0.03)
    
    highs = df[df['Swing_Type'] == 'High']['ZigZag'].dropna()
    lows = df[df['Swing_Type'] == 'Low']['ZigZag'].dropna()
    
    scored_patterns = []
    pattern_coords = {}

    # 1. Double Top (Labada dhibcood waa inay ka yimaadaan Swing High)
    if len(highs) >= 2:
        h_dates = highs.index[-2:]
        h4, h5 = highs.iloc[-2], highs.iloc[-1]
        dt_diff = abs(h5 - h4) / h4
        if dt_diff <= 0.01:
            prob = round(96.0 - (dt_diff * 100), 1)
            p_name = "Double Top (Reversal)"
            scored_patterns.append((p_name, prob))
            # Si loo hubiyo in dhibic walba nambarkeeda la siiyo (Top 1 iyo Top 2)
            pattern_coords[p_name] = [
                (h_dates[0], h4, "Top 1"), 
                (h_dates[1], h5, "Top 2")
            ]

    # 2. Double Bottom (Labada dhibcood waa inay ka yimaadaan Swing Low)
    if len(lows) >= 2:
        l_dates = lows.index[-2:]
        l4, l5 = lows.iloc[-2], lows.iloc[-1]
        db_diff = abs(l5 - l4) / l4
        if db_diff <= 0.01:
            prob = round(96.0 - (db_diff * 100), 1)
            p_name = "Double Bottom (Reversal)"
            scored_patterns.append((p_name, prob))
            # Si loo hubiyo in dhibic walba nambarkeeda la siiyo (Bottom 1 iyo Bottom 2)
            pattern_coords[p_name] = [
                (l_dates[0], l4, "Bottom 1"), 
                (l_dates[1], l5, "Bottom 2")
            ]

    # Kala saaridda iyo gelinta natiijada
    if scored_patterns:
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best_pattern = scored_patterns[0][0]
        df.loc[df.index[-1], 'Pattern'] = best_pattern
        
        if best_pattern in pattern_coords:
            # Qaabka loo dhisayo dhibcaha iyagoo wata magacyadooda saxda ah (tusaale: time_price_label)
            pts = [f"{time}_{val}_{label}" for time, val, label in pattern_coords[best_pattern]]
            df.loc[df.index[-1], 'Pattern_Points'] = ",".join(pts)

    return df
            
