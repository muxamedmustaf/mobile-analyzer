import pandas as pd

def calculate_premium_discount(df: pd.DataFrame, high: float, low: float) -> dict:
    """Xisaabinta kala qaybinta Premium iyo Discount zones"""
    equilibrium = (high + low) / 2
    return {
        "premium_zone": (high, equilibrium),
        "discount_zone": (equilibrium, low)
    }
  
