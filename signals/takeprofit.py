def calculate_take_profit(current_price: float, stop_loss: float, signal_type: str, rr_ratio: float = 2.0) -> float:
    """Xisaabinta Take Profit iyadoo la raacayo Risk/Reward ratio sax ah (TP waa inuu ka fog yahay current price)"""
    risk = abs(current_price - stop_loss)
    if signal_type == "BUY":
        return current_price + (risk * rr_ratio)
    else:
        return current_price - (risk * rr_ratio)
      
