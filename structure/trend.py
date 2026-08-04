import pandas as pd

def determine_trend(df: pd.DataFrame) -> str:
    """Go'aaminta in suuqu yahay Kor (Bullish) ama Hoos (Bearish)"""
    if 'close' in df.columns and len(df) > 50:
        if df['close'].iloc[-1] > df['close'].rolling(50).mean().iloc[-1]:
            return "BULLISH"
    return "BEARISH"
  
