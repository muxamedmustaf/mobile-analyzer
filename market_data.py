import yfinance as yf
import pandas as pd

def get_data(symbol: str, timeframe: str = "30m", limit: int = 100) -> pd.DataFrame:
    """Soo jiidashada xogta suuqa ee yFinance iyadoo la hubinayo badbaadada tiirarka"""
    try:
        # Kala xulashada mudada (period) iyadoo la eegayo timeframe-ka
        period_map = {
            "1m": "7d",
            "5m": "60d",
            "15m": "60d",
            "30m": "60d",
            "1h": "730d",
            "1d": "max"
        }
        
        period = period_map.get(timeframe, "60d")
        
        # Soo dejinta xogta
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        if df is None or df.empty:
            return pd.DataFrame()

        # Haddii tiirarku yihiin MultiIndex, ka dhig heerka kowaad mid caadi ah
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_0()

        # Nadiifinta magacyada tiirarka si ay u noqdaan kuwa yaryar (lowercase)
        df.columns = [str(col).lower() for col in df.columns]

        # Xulashada inta xog ah ee ugu dambeysa (limit)
        if len(df) > limit:
            df = df.tail(limit)

        return df

    except Exception as e:
        print(f"Cilad ayaa ka dhacday soo jiidashada xogta: {e}")
        return pd.DataFrame()
        
