# ==========================================
# PROFESSIONAL MARKET SWING DETECTOR
# ADAPTIVE FOR 1m - 1Y TIMEFRAMES
# ==========================================

import pandas as pd
import numpy as np


def get_swing_window(length):
    """
    Doorashada window iyadoo ku xiran xogta
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
    Detect Swing High and Swing Low
    """

    df = df.copy()


    # Hubi columns
    required = [
        "High",
        "Low"
    ]

    for col in required:
        if col not in df.columns:
            return df



    if window is None:
        window = get_swing_window(len(df))



    # Ku samee float columns
    df["Swing_High"] = np.nan
    df["Swing_Low"] = np.nan
    df["Swing_Strength"] = np.nan



    for i in range(window, len(df) - window):


        # ===============================
        # SWING HIGH
        # ===============================

        current_high = float(
            df["High"].iloc[i]
        )


        left_highs = df["High"].iloc[
            i-window:i
        ]

        right_highs = df["High"].iloc[
            i+1:i+1+window
        ]



        if (
            current_high > left_highs.max()
            and
            current_high > right_highs.max()
        ):


            strength = (
                abs(
                    current_high - float(left_highs.max())
                )
                +
                abs(
                    current_high - float(right_highs.max())
                )
            )


            df.loc[
                df.index[i],
                "Swing_High"
            ] = current_high



            df.loc[
                df.index[i],
                "Swing_Strength"
            ] = float(strength)




        # ===============================
        # SWING LOW
        # ===============================

        current_low = float(
            df["Low"].iloc[i]
        )


        left_lows = df["Low"].iloc[
            i-window:i
        ]

        right_lows = df["Low"].iloc[
            i+1:i+1+window
        ]



        if (
            current_low < left_lows.min()
            and
            current_low < right_lows.min()
        ):


            strength = (
                abs(
                    float(left_lows.min()) - current_low
                )
                +
                abs(
                    float(right_lows.min()) - current_low
                )
            )



            df.loc[
                df.index[i],
                "Swing_Low"
            ] = current_low



            df.loc[
                df.index[i],
                "Swing_Strength"
            ] = float(strength)



    return df
