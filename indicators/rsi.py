import pandas as pd

def calculate_rsi(df: pd.DataFrame, period: int = 14):
    """Xisaabinta Relative Strength Index (RSI)"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.Series(index=df.index if hasattr(df, 'index') else None)
    
    # Hubinta badbaadada leh ee tiirarka
    columns = list(df.columns) if hasattr(df, 'columns') else []
    close_col = 'Close' if 'Close' in columns else ('close' if 'close' in columns else None)
    
    if close_col is None:
        # Haddii uusan helin tiir gaar ah, wuxuu qaadanayaa tiirka kowaad
        close_col = columns[0] if columns else 'Close'
        
    delta = df[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
    
