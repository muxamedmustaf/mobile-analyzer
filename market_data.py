import yfinance as yf
import pandas as pd

def get_data(symbol: str, timeframe: str = "30m", limit: int = 100) -> pd.DataFrame:
    """Soo jiidashada xogta suuqa iyadoo la isticmaalayo habab kala duwan oo badbaado leh"""
    df = pd.DataFrame()
    
    try:
        period_map = {
            "1m": "7d",
            "5m": "60d",
            "15m": "60d",
            "30m": "60d",
            "1h": "730d",
            "1d": "max"
        }
        period = period_map.get(timeframe, "60d")
        
        # Habka 1aad: Isticmaalka yf.download
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        # Habka 2aad: Haddii habka koowaad uu soo celiyo xog maran, isticmaal yf.Ticker.history
        if df is None or df.empty:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=timeframe)
            
        if df is None or df.empty:
            return pd.DataFrame()

        # Nadiifinta MultiIndex haddii uu jiro
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_0()

        # Ka dhig dhammaan tiirarka kuwa yaryar (lowercase)
        df.columns = [str(col).lower() for col in df.columns]

        # Xulashada inta xog ah ee ugu dambeysa
        if len(df) > limit:
            df = df.tail(limit)

        return df

    except Exception as e:
        print(f"Cilad ayaa ka dhacday soo jiidashada xogta: {e}")
        return pd.DataFrame()
        
