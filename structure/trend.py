import pandas as pd

def classify_swings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kala saaraya Swing Highs iyo Swing Lows una beddelaya HH, HL, LH, LL.
    """
    df = df.copy()
    df['Structure'] = ""
    
    # Soo saarista liiska swings-ka si loo barbardhigo
    swings = []
    for i in range(len(df)):
        if pd.notna(df['Swing_High'].iloc[i]):
            swings.append((i, 'HIGH', df['Swing_High'].iloc[i]))
        elif pd.notna(df['Swing_Low'].iloc[i]):
            swings.append((i, 'LOW', df['Swing_Low'].iloc[i]))
            
    # Barbardhigga si loo ogaado HH, HL, LH, LL
    last_high = None
    last_low = None
    
    for idx, stype, val in swings:
        if stype == 'HIGH':
            if last_high is not None:
                if val > last_high:
                    df.loc[df.index[idx], 'Structure'] = 'HH'
                else:
                    df.loc[df.index[idx], 'Structure'] = 'LH'
            last_high = val
        elif stype == 'LOW':
            if last_low is not None:
                if val > last_low:
                    df.loc[df.index[idx], 'Structure'] = 'HL'
                else:
                    df.loc[df.index[idx], 'Structure'] = 'LL'
            last_low = val
            
    return df
    
