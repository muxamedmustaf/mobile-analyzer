import ccxt
import pandas as pd

def get_data(symbol="BTC/USDT", timeframe="30m", limit=100):
    # Isticmaal CoinEx halkii ay ka noqon lahayd Binance
    exchange = ccxt.coinex()
    
    # CoinEx magacyada suuqa waxay isticmaalaan hab aan lahayn slash (tusaale: BTCUSDT)
    clean_symbol = symbol.replace("/", "")
    
    ohlcv = exchange.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
    
    df = pd.DataFrame(
        ohlcv,
        columns=["Time", "Open", "High", "Low", "Close", "Volume"]
    )
    df["Time"] = pd.to_datetime(df["Time"], unit='ms')
    return df
    
