import pandas as pd

def calculate_atr(df: pd.DataFrame, period: int = 14):
    """Xisaabinta Average True Range (ATR)"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.Series(index=df.index if hasattr(df, 'index') else None)
    
    # Hubinta magacyada tiirarka (High, Low, Close) si aysan KeyError u dhicin
    cols = {col.lower(): col for col in df.columns}
    
    high_col = cols.get('high', 'High' if 'High' in df.columns else df.columns[1] if len(df.columns) > 1 else None)
    low_col = cols.get('low', 'Low' if 'Low' in df.columns else df.columns[2] if len(df.columns) > 2 else None)
    close_col = cols.get('close', 'Close' if 'Close' in df.columns else df.columns[3] if len(df.columns) > 3 else None)
    
    if not high_col or not low_col or not close_col:
        return pd.Series(0, index=df.index)

    high = df[high_col]
    low = df[low_col]
    close = df[close_col]
    
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr
    
