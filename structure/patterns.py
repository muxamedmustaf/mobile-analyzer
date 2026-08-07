# structure/patterns.py

import pandas as pd
import numpy as np

from structure.swings import detect_swings


def get_pivot_points(df):

    """
    Soo saar swing points si patterns loogu baaro
    """

    df = detect_swings(df)

    pivots = []

    for idx, row in df.iterrows():

        if not pd.isna(row["Swing_High"]):

            pivots.append({
                "index": idx,
                "price": row["Swing_High"],
                "type": "HIGH"
            })


        if not pd.isna(row["Swing_Low"]):

            pivots.append({
                "index": idx,
                "price": row["Swing_Low"],
                "type": "LOW"
            })


    return sorted(
        pivots,
        key=lambda x: x["index"]
    )



def detect_double_top(pivots, tolerance=0.03):

    results=[]

    for i in range(len(pivots)-2):

        a=pivots[i]
        b=pivots[i+1]
        c=pivots[i+2]


        if (
            a["type"]=="HIGH"
            and
            b["type"]=="LOW"
            and
            c["type"]=="HIGH"
        ):

            diff=abs(
                a["price"]-c["price"]
            ) / a["price"]


            if diff <= tolerance:

                results.append({
                    "pattern":"DOUBLE TOP",
                    "direction":"SELL",
                    "score":80,
                    "points":[a,b,c]
                })


    return results



def detect_double_bottom(pivots, tolerance=0.03):

    results=[]

    for i in range(len(pivots)-2):

        a=pivots[i]
        b=pivots[i+1]
        c=pivots[i+2]


        if (
            a["type"]=="LOW"
            and
            b["type"]=="HIGH"
            and
            c["type"]=="LOW"
        ):

            diff=abs(
                a["price"]-c["price"]
            ) / a["price"]


            if diff <= tolerance:

                results.append({
                    "pattern":"DOUBLE BOTTOM",
                    "direction":"BUY",
                    "score":80,
                    "points":[a,b,c]
                })


    return results



def detect_chart_patterns(df):

    """
    Function-ka uu app.py isticmaalo
    """

    pivots = get_pivot_points(df)


    patterns=[]


    patterns += detect_double_top(
        pivots
    )


    patterns += detect_double_bottom(
        pivots
    )


    if patterns:

        best=max(
            patterns,
            key=lambda x:x["score"]
        )


        df["Pattern"] = best["pattern"]
        df["Signal"] = best["direction"]
        df["Pattern_Score"] = best["score"]

    else:

        df["Pattern"] = "No Pattern"
        df["Signal"] = "WAIT"
        df["Pattern_Score"] = 0


    return df
