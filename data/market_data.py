import yfinance as yf
import pandas as pd

def fetch_market_data(symbol="GC=F", interval="30m", period="5d"):
    df = yf.download(symbol, period=period, interval=interval)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df
  
