
import pandas as pd

def detect_fvg(df: pd.DataFrame) -> list:
    """Raadinta Fair Value Gaps (FVG) ee bannaan"""
    fvgs = []
    for i in range(1, len(df) - 1):
        # Bullish FVG
        if df['low'].iloc[i+1] > df['high'].iloc[i-1]:
            fvgs.append({
                "index": i,
                "type": "BULLISH_FVG",
                "bottom": df['high'].iloc[i-1],
                "top": df['low'].iloc[i+1]
            })
    return fvgs
  
