import pandas as pd
from .swings import identify_swings
from .trend import determine_trend
from .bos import detect_bos
from .choch import detect_choch

def analyze_market_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Falanqeeya suuqa oo soo saara Swings, Trend, BOS, iyo CHOCH
    """
    if df.empty:
        return df
        
    df = identify_swings(df)
    df = determine_trend(df)
    df = detect_bos(df)
    df = detect_choch(df)
    df['Structure'] = df.get('Trend', 'Consolidation')
    
    return df
    
