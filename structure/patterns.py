import pandas as pd
import numpy as np

def calculate_zigzag(df: pd.DataFrame, deviation=0.03) -> pd.DataFrame:
    """Xisaabinta ZigZag nadiif ah si loo helo Swing High iyo Swing Low dhab ah."""
    df['ZigZag'] = np.nan
    df['Swing_Type'] = None 
    
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
    
    # Xisaabinta ATR si loo helo tolerance sax ah
    if 'ATR' not in df.columns:
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()

    # Ku shaqaynta ZigZag oo keliya
    df = calculate_zigzag(df, deviation=0.03)
    
    highs = df[df['Swing_Type'] == 'High']['ZigZag'].dropna()
    lows = df[df['Swing_Type'] == 'Low']['ZigZag'].dropna()
    
    scored_patterns = []
    pattern_coords = {}
    
    current_atr = df['ATR'].iloc[-1] if not pd.isna(df['ATR'].iloc[-1]) else (df['Close'].iloc[-1] * 0.01)

    # 1. Double Top (Iyadoo la eegayo Swing High-yada ZigZag)
    if len(highs) >= 2:
        h_dates = highs.index[-2:]
        h4, h5 = highs.iloc[-2], highs.iloc[-1]
        dt_diff = abs(h5 - h4)
        if dt_diff <= (2.0 * current_atr) and (dt_diff / h4) <= 0.01:
            scored_patterns.append(("Double Top (Reversal)", 96.0))
            pattern_coords["Double Top (Reversal)"] = [
                (h_dates[0], h4, "Top 1"), 
                (h_dates[1], h5, "Top 2")
            ]

    # 2. Double Bottom (Iyadoo la eegayo Swing Low-yada ZigZag)
    if len(lows) >= 2:
        l_dates = lows.index[-2:]
        l4, l5 = lows.iloc[-2], lows.iloc[-1]
        db_diff = abs(l5 - l4)
        if db_diff <= (2.0 * current_atr) and (db_diff / l4) <= 0.01:
            scored_patterns.append(("Double Bottom (Reversal)", 96.0))
            pattern_coords["Double Bottom (Reversal)"] = [
                (l_dates[0], l4, "Bottom 1"), 
                (l_dates[1], l5, "Bottom 2")
            ]

    # Kala saaridda iyo gelinta dhibcaha si aan khalad uga dhicin
    if scored_patterns:
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best = scored_patterns[0]
        df.loc[df.index[-1], 'Pattern'] = best[0]
        if best[0] in pattern_coords:
            pts = [f"{time}_{val}_{label}" for time, val, label in pattern_coords[best[0]]]
            df.loc[df.index[-1], 'Pattern_Points'] = ",".join(pts)

    return df
    
