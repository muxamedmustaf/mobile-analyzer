import pandas as pd

def detect_bos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ogaanaya Break of Structure (BOS) marka qiimaha xiritaanka (Close) uu ka gudbo Swing High ama Swing Low.
    """
    df = df.copy()
    df['BOS'] = None
    
    last_swing_high = None
    last_swing_low = None
    
    for i in range(len(df)):
        if pd.notna(df['Swing_High'].iloc[i]):
            last_swing_high = df['Swing_High'].iloc[i]
        if pd.notna(df['Swing_Low'].iloc[i]):
            last_swing_low = df['Swing_Low'].iloc[i]
            
        # Bullish BOS: Marka Close uu ka sarreeyo Swing High-kii ugu dambeeyay
        if last_swing_high and df['Close'].iloc[i] > last_swing_high:
            df.loc[df.index[i], 'BOS'] = 'Bullish BOS'
            last_swing_high = None # Hal mar ayaa la calaamadiyaa ilaa mid cusub laga helayo
            
        # Bearish BOS: Marka Close uu ka hooseeyo Swing Low-kii ugu dambeeyay
        elif last_swing_low and df['Close'].iloc[i] < last_swing_low:
            df.loc[df.index[i], 'BOS'] = 'Bearish BOS'
            last_swing_low = None
            
    return df
    
