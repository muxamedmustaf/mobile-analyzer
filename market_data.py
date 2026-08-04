import requests
import pandas as pd

def get_data(symbol="BTC/USDT", timeframe="30m", limit=100):
    """
    Soo jiidashada xogta suuqa iyadoo la adeegsanayo CoinEx API (Bilaash oo aan u baahnayn CCXT/Binance)
    """
    # Beddelashada timeframes-ka si ay u waafaqaan CoinEx API v2
    tf_map = {
        "1m": "1min", 
        "5m": "5min", 
        "15m": "15min", 
        "30m": "30min", 
        "1h": "1hour", 
        "4h": "4hour",
        "1d": "1day"
    }
    coinex_tf = tf_map.get(timeframe, "30min")
    
    # Ka saarida calaamadda "/" si ay u noqoto magaca suuqa ee CoinEx (tusaale: BTCUSDT)
    clean_symbol = symbol.replace("/", "")
    
    url = "https://api.coinex.com/v2/market/kline"
    params = {
        "market": clean_symbol,
        "interval": coinex_tf,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            raw_candles = data.get("data", [])
            if not raw_candles:
                return pd.DataFrame()
                
            df_list = []
            for candle in raw_candles:
                # CoinEx v2 K-line format: [timestamp, open, close, high, low, volume, ...]
                df_list.append({
                    "Time": pd.to_datetime(int(candle[0]), unit='s'),
                    "Open": float(candle[1]),
                    "Close": float(candle[2]),
                    "High": float(candle[3]),
                    "Low": float(candle[4]),
                    "Volume": float(candle[5])
                })
                
            df = pd.DataFrame(df_list)
            # Nidaaminta si taariikhdu u kala horreyso si sax ah
            df = df.sort_values("Time").reset_index(drop=True)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()
        
