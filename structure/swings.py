# ==========================================
# PROFESSIONAL MARKET SWING DETECTOR
# ADAPTIVE FOR 1m - 1Y TIMEFRAMES
# ==========================================

import pandas as pd
import numpy as np


def get_swing_window(length):
    """
    Window adaptive ah si uu ula qabsado xogta
    """

    if length < 100:
        return 2

    elif length < 300:
        return 3

    elif length < 700:
        return 5

    else:
        return 7



def detect_swings(df: pd.DataFrame, window=None) -> pd.DataFrame:
    """
    Detects strong Swing High / Swing Low

    Waxaa loogu talagalay:
    1m ilaa 1Y charts
    """

    df = df.copy()


    if window is None:
        window = get_swing_window(len(df))


    df["Swing_High"] = np.nan
    df["Swing_Low"] = np.nan

    df["Swing_Strength"] = 0



    for i in range(window, len(df)-window):


        current_high = df["High"].iloc[i]

        left_highs = df["High"].iloc[
            i-window:i
        ]

        right_highs = df["High"].iloc[
            i+1:i+1+window
        ]



        # Swing High

        if (
            current_high > left_highs.max()
            and
            current_high > right_highs.max()
        ):

            strength = (
                (current_high - left_highs.max())
                +
                (current_high - right_highs.max())
            )


            df.loc[
                df.index[i],
                "Swing_High"
            ] = current_high


            df.loc[
                df.index[i],
                "Swing_Strength"
            ] = strength




        current_low = df["Low"].iloc[i]


        left_lows = df["Low"].iloc[
            i-window:i
        ]

        right_lows = df["Low"].iloc[
            i+1:i+1+window
        ]



        # Swing Low

        if (
            current_low < left_lows.min()
            and
            current_low < right_lows.min()
        ):

            strength = (
                (left_lows.min() - current_low)
                +
                (right_lows.min() - current_low)
            )


            df.loc[
                df.index[i],
                "Swing_Low"
            ] = current_low


            df.loc[
                df.index[i],
                "Swing_Strength"
            ] = strength



    return df
