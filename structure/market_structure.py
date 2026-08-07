import pandas as pd
import numpy as np

from structure.swings import detect_swings


def determine_trend(df):

    df["Trend"] = "Bullish"

    df["Trend"] = np.where(
        df["Close"] < df["Close"].rolling(20).mean(),
        "Bearish",
        df["Trend"]
    )

    return df



def detect_bos(df):

    df["BOS"] = None

    highs = df["Swing_High"].dropna()
    lows = df["Swing_Low"].dropna()


    if len(highs) > 1:

        last_high = highs.iloc[-1]

        previous_high = highs.iloc[-2]

        if last_high > previous_high:

            df.loc[
                df.index[-1],
                "BOS"
            ] = "Bullish BOS"



    if len(lows) > 1:

        last_low = lows.iloc[-1]

        previous_low = lows.iloc[-2]

        if last_low < previous_low:

            df.loc[
                df.index[-1],
                "BOS"
            ] = "Bearish BOS"


    return df



def detect_choch(df):

    df["CHOCH"] = None


    if len(df) < 3:
        return df


    last = df.iloc[-1]

    previous = df.iloc[-2]


    if (
        previous["Trend"] == "Bearish"
        and
        last["Trend"] == "Bullish"
    ):

        df.loc[
            df.index[-1],
            "CHOCH"
        ] = "Bullish CHOCH"



    elif (
        previous["Trend"] == "Bullish"
        and
        last["Trend"] == "Bearish"
    ):

        df.loc[
            df.index[-1],
            "CHOCH"
        ] = "Bearish CHOCH"


    return df



def analyze_market_structure(df: pd.DataFrame):


    if df.empty:
        return df


    # Swing engine-ka saxda ah
    df = detect_swings(df)


    # Trend
    df = determine_trend(df)


    # Structure
    df = detect_bos(df)

    df = detect_choch(df)


    df["Structure"] = df["Trend"]


    return df
