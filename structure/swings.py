import pandas as pd

def detect_swings(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Soo saarista Swing High iyo Swing Low iyadoo la eegayo shamacyada hareeraha ah"""
    df['swing_high'] = df['high'][(df['high'] == df['high'].rolling(2*n+1, center=True).max())]
    df['swing_low'] = df['low'][(df['low'] == df['low'].rolling(2*n+1, center=True).min())]
    return df
  
