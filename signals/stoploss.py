def calculate_stop_loss(df, signal_type: str, atr_value: float) -> float:
    """Xisaabinta halka la dhigayo Stop Loss iyadoo la adeegsanayo ATR"""
    last_row = df.iloc[-1]
    if signal_type == "BUY":
        return last_row['low'] - (atr_value * 1.5)
    else:
        return last_row['high'] + (atr_value * 1.5)
      
