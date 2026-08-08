# ============================================================
# MOBILE ANALYZER
# MARKET_DATA.PY
# YAHOO FINANCE ONLY
# ============================================================

import pandas as pd
import yfinance as yf


# ============================================================
# TIMEFRAME MAP
# ============================================================

TIMEFRAMES = {
    "1 Minute": "1m",
    "2 Minutes": "2m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "1h",
    "4 Hours": "4h",
    "1 Day": "1d",
    "1 Week": "1wk",
    "1 Month": "1mo",
}


# ============================================================
# SYMBOL CONVERTER
# ============================================================

def normalize_symbol(symbol):
    """
    Converts user-friendly symbols to Yahoo Finance symbols.

    Examples:

        BTC/USDT -> BTC-USD
        ETH/USDT -> ETH-USD
        EUR/USD  -> EURUSD=X
        GBP/USD  -> GBPUSD=X
        XAU/USD  -> GC=F
        XAG/USD  -> SI=F
    """

    symbol = str(symbol).strip().upper()

    symbol = symbol.replace(" ", "")
    symbol = symbol.replace("-", "/")

    # --------------------------------------------------------
    # Crypto
    # --------------------------------------------------------

    if symbol.endswith("/USDT"):

        base = symbol.replace(
            "/USDT",
            ""
        )

        return f"{base}-USD"

    if symbol.endswith("/USDC"):

        base = symbol.replace(
            "/USDC",
            ""
        )

        return f"{base}-USD"

    # --------------------------------------------------------
    # Forex
    # --------------------------------------------------------

    if symbol.endswith("/USD"):

        base = symbol.replace(
            "/USD",
            ""
        )

        if base == "XAU":
            return "GC=F"

        if base == "XAG":
            return "SI=F"

        return f"{base}USD=X"

    if "/" in symbol:

        base, quote = symbol.split(
            "/",
            1
        )

        return f"{base}{quote}=X"

    # --------------------------------------------------------
    # Common direct symbols
    # --------------------------------------------------------

    aliases = {

        "BTC": "BTC-USD",
        "BTCUSD": "BTC-USD",

        "ETH": "ETH-USD",
        "ETHUSD": "ETH-USD",

        "SOL": "SOL-USD",
        "SOLUSD": "SOL-USD",

        "BNB": "BNB-USD",
        "BNBUSD": "BNB-USD",

        "XRP": "XRP-USD",
        "XRPUSD": "XRP-USD",

        "GOLD": "GC=F",
        "XAU": "GC=F",
        "XAUUSD": "GC=F",

        "SILVER": "SI=F",
        "XAG": "SI=F",
        "XAGUSD": "SI=F",
    }

    return aliases.get(
        symbol,
        symbol
    )


# ============================================================
# TIMEFRAME VALIDATION
# ============================================================

def normalize_timeframe(timeframe):

    if timeframe in TIMEFRAMES:
        return TIMEFRAMES[timeframe]

    valid_values = list(
        TIMEFRAMES.values()
    )

    if timeframe in valid_values:
        return timeframe

    raise ValueError(
        f"Unsupported timeframe: {timeframe}"
    )


# ============================================================
# YAHOO PERIOD
# ============================================================

def recommended_period(interval):

    """
    Yahoo Finance has different historical limits
    depending on the interval.

    We use a safe default period.
    """

    if interval == "1m":
        return "7d"

    if interval in {
        "2m",
        "5m",
        "15m",
        "30m",
        "1h",
    }:
        return "60d"

    if interval == "4h":
        return "730d"

    if interval == "1d":
        return "5y"

    if interval == "1wk":
        return "10y"

    if interval == "1mo":
        return "max"

    return "1y"


# ============================================================
# DOWNLOAD DATA
# ============================================================

def fetch_market_data(
    symbol,
    timeframe,
    period=None,
):

    yahoo_symbol = normalize_symbol(
        symbol
    )

    interval = normalize_timeframe(
        timeframe
    )

    if period is None:

        period = recommended_period(
            interval
        )

    try:

        data = yf.download(
            yahoo_symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

    except Exception as error:

        raise RuntimeError(
            "Yahoo Finance data request failed: "
            f"{error}"
        )

    if data is None or data.empty:

        raise ValueError(
            f"Yahoo Finance ma helin xogta "
            f"{symbol} ({timeframe})."
        )

    # ========================================================
    # MULTI INDEX FIX
    # ========================================================

    if isinstance(
        data.columns,
        pd.MultiIndex
    ):

        data.columns = (
            data.columns
            .get_level_values(0)
        )

    # ========================================================
    # LOWERCASE COLUMNS
    # ========================================================

    data.columns = [
        str(column).strip().lower()
        for column in data.columns
    ]

    # ========================================================
    # REQUIRED OHLC
    # ========================================================

    required = [
        "open",
        "high",
        "low",
        "close",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            "Yahoo Finance data is missing "
            f"columns: {missing}"
        )

    # ========================================================
    # KEEP OHLC + VOLUME
    # ========================================================

    columns = [
        "open",
        "high",
        "low",
        "close",
    ]

    if "volume" in data.columns:

        columns.append(
            "volume"
        )

    data = data[
        columns
    ].copy()

    # ========================================================
    # NUMERIC CONVERSION
    # ========================================================

    for column in columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # ========================================================
    # REMOVE INVALID ROWS
    # ========================================================

    data = data.dropna(
        subset=required
    )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    data = data[
        ~data.index.duplicated(
            keep="last"
        )
    ]

    # ========================================================
    # SORT CHRONOLOGICALLY
    # ========================================================

    data = data.sort_index()

    # ========================================================
    # METADATA
    # ========================================================

    data.attrs["symbol"] = symbol
    data.attrs["yahoo_symbol"] = yahoo_symbol
    data.attrs["timeframe"] = timeframe
    data.attrs["interval"] = interval
    data.attrs["source"] = "Yahoo Finance"

    return data


# ============================================================
# GET AVAILABLE TIMEFRAMES
# ============================================================

def get_timeframes():

    return list(
        TIMEFRAMES.keys()
    )


# ============================================================
# GET YAHOO SYMBOL
# ============================================================

def get_yahoo_symbol(symbol):

    return normalize_symbol(
        symbol
    )


# ============================================================
# QUICK DATA TEST
# ============================================================

def test_connection(
    symbol="BTC/USDT",
    timeframe="4 Hours",
):

    data = fetch_market_data(
        symbol,
        timeframe
    )

    return {
        "success": True,
        "symbol": symbol,
        "yahoo_symbol": data.attrs.get(
            "yahoo_symbol"
        ),
        "timeframe": timeframe,
        "candles": len(data),
        "source": "Yahoo Finance",
    }
