# ==========================================
# PROFESSIONAL PATTERN ENGINE
# CONNECTOR FOR CURRENT PROJECT
# ==========================================


from structure.market_structure import analyze_market_structure
from structure.patterns import detect_chart_patterns



def normalize_columns(df):

    df = df.copy()

    rename = {}

    for col in df.columns:

        name = str(col).lower()

        if name == "open":
            rename[col] = "Open"

        elif name == "high":
            rename[col] = "High"

        elif name == "low":
            rename[col] = "Low"

        elif name == "close":
            rename[col] = "Close"

        elif name == "volume":
            rename[col] = "Volume"


    return df.rename(columns=rename)



def analyze_market(df):


    if df is None or df.empty:

        return {

            "signal": "WAIT",
            "pattern": "No Data",
            "confidence": 0

        }



    # Normalize data

    df = normalize_columns(df)



    required = [
        "Open",
        "High",
        "Low",
        "Close"
    ]


    for col in required:

        if col not in df.columns:

            return {

                "signal":"WAIT",
                "pattern":"Missing Data",
                "confidence":0

            }



    # Market Structure

    df = analyze_market_structure(df)



    # Pattern Detection

    df = detect_chart_patterns(df)



    last = df.iloc[-1]



    return {


        "signal": last.get(
            "Signal",
            "WAIT"
        ),


        "pattern": last.get(
            "Pattern",
            "No Pattern"
        ),


        "confidence": int(
            last.get(
                "Pattern_Score",
                0
            )
        ),



        "trend": last.get(
            "Trend",
            "Unknown"
        ),


        "structure": last.get(
            "Structure",
            "Unknown"
        ),


        "BOS": last.get(
            "BOS",
            False
        ),


        "CHOCH": last.get(
            "CHOCH",
            False
        ),



        # Future chart marking

        "pattern_points": last.get(
            "Pattern_Points",
            None
        )

    }
