import pandas as pd

def detect_bos(df: pd.DataFrame) -> pd.DataFrame:
    """Raadinta Break of Structure (BOS) ee suuqa"""
    df['bos'] = 0
    # Qorshaha hordhaca ah ee BOS
    return df
  
