# ==========================================
# PROFESSIONAL CHART PATTERN DETECTOR
# ADAPTIVE DOUBLE TOP / DOUBLE BOTTOM
# ==========================================

import pandas as pd
import numpy as np

from structure.swings import detect_swings



def get_pivot_points(df):

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



def price_tolerance(df):

    avg_price = df["Close"].mean()

    if avg_price < 100:
        return 0.015

    else:
        return 0.02



def detect_double_top(df, pivots):

    results = []

    tolerance = price_tolerance(df)



    for i in range(len(pivots)-2):

        a = pivots[i]
        b = pivots[i+1]
        c = pivots[i+2]


        if (
            a["type"] == "HIGH"
            and
            b["type"] == "LOW"
            and
            c["type"] == "HIGH"
        ):


            diff = abs(
                a["price"] - c["price"]
            ) / a["price"]



            neckline_drop = (
                (a["price"] - b["price"])
                /
                a["price"]
            )



            if (
                diff <= tolerance
                and
                neckline_drop >= 0.02
            ):


                results.append({

                    "pattern":"DOUBLE TOP",

                    "direction":"SELL",

                    "score":85,

                    "points":[a,b,c]

                })


    return results




def detect_double_bottom(df, pivots):

    results = []

    tolerance = price_tolerance(df)



    for i in range(len(pivots)-2):

        a = pivots[i]
        b = pivots[i+1]
        c = pivots[i+2]



        if (
            a["type"] == "LOW"
            and
            b["type"] == "HIGH"
            and
            c["type"] == "LOW"
        ):


            diff = abs(
                a["price"] - c["price"]
            ) / a["price"]



            neckline_rise = (
                (b["price"] - a["price"])
                /
                a["price"]
            )



            if (
                diff <= tolerance
                and
                neckline_rise >= 0.02
            ):


                results.append({

                    "pattern":"DOUBLE BOTTOM",

                    "direction":"BUY",

                    "score":85,

                    "points":[a,b,c]

                })


    return results




def detect_chart_patterns(df):


    pivots = get_pivot_points(df)


    patterns = []


    patterns += detect_double_top(
        df,
        pivots
    )


    patterns += detect_double_bottom(
        df,
        pivots
    )



    if patterns:


        best = max(
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
