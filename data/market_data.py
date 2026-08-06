import pandas as pd
from .swings import identify_swings
from .trend import determine_trend
from .bos import detect_bos
from .choch import detect_choch

def analyze_market_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Falanqeeya suuqa oo soo saara Swings, Trend, BOS, iyo CHOCH
    """
    # 1. Ogaanshaha Swings
    df = identify_swings(df)
    
    # 2. Ogaanshaha Trend-ka
    df = determine_trend(df)
    
    # 3. Ogaanshaha BOS (Break of Structure)
    df = detect_bos(df)
    
    # 4. Ogaanshaha CHOCH (Change of Character)
    df = detect_choch(df)
    
    # Habaynta Structure-ka guud ee xaaladda haysa
    df['Structure'] = df['Trend']
    
    return df
    
