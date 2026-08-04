import ccxt
import pandas as pd

exchange = ccxt.binance()

def get_data(symbol="BTC/USDT", timeframe="15m", limit=200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    )

    df["Time"] = pd.to_datetime(df["Time"], unit="ms")

    return df
