import yfinance as yf
import pandas as pd

def get_data(symbol="EURUSD=X", timeframe="30m", limit=100):
    """
    Soo jiidashada xogta suuqa iyadoo la adeegsanayo yfinance (Forex & Crypto)
    """
    try:
        # Soo dejinta xogta adigoo isticmaalaya yfinance Ticker
        ticker = yf.Ticker(symbol)
        
        # yfinance timeframe-keedu wuxuu qaataa shuruudaha sida '15m', '30m', '1h', '1d'
        df = ticker.history(period="5d", interval=timeframe)
        
        if df.empty:
            return pd.DataFrame()
            
        # Nidaaminta kolamyada si ay ula jaanqaadaan app-kaaga (open, high, low, close, volume)
        df = df.reset_index()
        
        # Hubinta magaca kolamka wakhtiga (Datetime ama Date)
        time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
        
        clean_df = pd.DataFrame({
            "Time": pd.to_datetime(df[time_col]),
            "open": df['Open'].astype(float),
            "high": df['High'].astype(float),
            "low": df['Low'].astype(float),
            "close": df['Close'].astype(float),
            "volume": df['Volume'].astype(float)
        })
        
        # Soo celinta xogta iyadoo la raacayo xadka 'limit' ee la cayimay
        return clean_df.tail(limit).reset_index(drop=True)
        
    except Exception as e:
        print(f"Error fetching yfinance data: {e}")
        return pd.DataFrame()
        
