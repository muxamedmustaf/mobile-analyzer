import pandas as pd
import numpy as np

def detect_swings(df: pd.DataFrame, window: int = 2) -> pd.DataFrame:
    """
    Ogaanaya Swing High iyo Swing Low iyadoo la adeegsanayo daaqad (window) go'an.
    """
    df = df.copy()
    df['Swing_High'] = np.nan
    df['Swing_Low'] = np.nan

    for i in range(window, len(df) - window):
        # Swing High: Qiimaha ugu sarreeya dhexda daaqada
        current_high = df['High'].iloc[i]
        left_highs = df['High'].iloc[i - window:i]
        right_highs = df['High'].iloc[i + 1:i + 1 + window]
        
        if current_high > left_highs.max() and current_high > right_highs.max():
            df.loc[df.index[i], 'Swing_High'] = current_high

        # Swing Low: Qiimaha ugu hooseeya dhexda daaqada
        current_low = df['Low'].iloc[i]
        left_lows = df['Low'].iloc[i - window:i]
        right_lows = df['Low'].iloc[i + 1:i + 1 + window]
        
        if current_low < left_lows.min() and current_low < right_lows.min():
            df.loc[df.index[i], 'Swing_Low'] = current_low

    return df
    
