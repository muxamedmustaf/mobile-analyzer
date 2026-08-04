import requests
import pandas as pd

def get_data(symbol="BTC/USDT", timeframe="30m", limit=100):
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
    
    # CoinEx waxay isticmaashaa magaca suuqa oo leh underscore ama si toos ah (tusaale: BTCUSDT)
    clean_symbol = symbol.replace("/", "").upper()
    
    url = "https://api.coinex.com/v2/market/kline"
    params = {
        "market": clean_symbol,
        "market_type": "spot",
        "interval": coinex_tf,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == 0 and "data" in data:
            raw_candles = data.get("data", [])
            if not raw_candles:
                return pd.DataFrame()
                
            df_list = []
            for candle in raw_candles:
                # CoinEx v2 kline object ama array ayay noqon kartaa iyadoo ku xiran endpoint-ka
                # Caadi ahaan waa list: [created_at, open, close, high, low, volume, volume_value]
                if isinstance(candle, dict):
                    ts = int(candle.get("created_at", 0))
                    o = float(candle.get("open", 0))
                    c = float(candle.get("close", 0))
                    h = float(candle.get("high", 0))
                    l = float(candle.get("low", 0))
                    v = float(candle.get("volume", 0))
                else:
                    ts = int(candle[0])
                    o = float(candle[1])
                    c = float(candle[2])
                    h = float(candle[3])
                    l = float(candle[4])
                    v = float(candle[5])
                    
                df_list.append({
                    "Time": pd.to_datetime(ts, unit='s'),
                    "Open": o,
                    "Close": c,
                    "High": h,
                    "Low": l,
                    "Volume": v
                })
                
            df = pd.DataFrame(df_list)
            df = df.sort_values("Time").reset_index(drop=True)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()
        
