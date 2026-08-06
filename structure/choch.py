import pandas as pd

def detect_choch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ogaanaya Change of Character (CHOCH) markii ugu horreysay ee suuqu beddelo jihadiisa.
    """
    df = df.copy()
    df['CHOCH'] = None
    
    # Tani waxay raacdaa jabinta qaab-dhismeedka hore ee suuqa (Trend Shift)
    # Halkaan waxaan ku dabaqeynaa sharciga ah in jebinta ugu horreysa ee struktur-ka ay tahay CHOCH.
    trend = 0 # 1 = Bullish, -1 = Bearish
    
    for i in range(1, len(df)):
        if df['Structure'].iloc[i] == 'HH' and trend <= 0:
            df.loc[df.index[i], 'CHOCH'] = 'Bullish CHOCH'
            trend = 1
        elif df['Structure'].iloc[i] == 'LL' and trend >= 0:
            df.loc[df.index[i], 'CHOCH'] = 'Bearish CHOCH'
            trend = -1
            
    return df
  
