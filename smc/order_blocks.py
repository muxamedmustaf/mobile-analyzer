import pandas as pd

def detect_order_blocks(df: pd.DataFrame) -> list:
    """Raadinta Bullish iyo Bearish Order Blocks ee suuqa"""
    order_blocks = []
    for i in range(2, len(df)):
        # Tusaale hordhac ah: Shamaca ka horreeya dhaqdhaqaaqa xoogan
        if df['close'].iloc[i] > df['open'].iloc[i] and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
            order_blocks.append({
                "index": i-1,
                "type": "BULLISH_OB",
                "price": df['low'].iloc[i-1]
            })
    return order_blocks
  
