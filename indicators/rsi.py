import pandas as pd

def calculate_rsi(df: pd.DataFrame, period: int = 14):
    """Xisaabinta Relative Strength Index (RSI)"""
    # Hubinta in tiirka 'close' ama 'Close' la isticmaali karo
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    delta = df[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
    
