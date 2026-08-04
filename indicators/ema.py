import pandas as pd

def calculate_ema(df: pd.DataFrame, period: int = 50) -> pd.Series:
    """Xisaabinta Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()
  
