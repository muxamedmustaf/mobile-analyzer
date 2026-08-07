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

        if col.lower() == "open":
            rename[col] = "Open"

        elif col.lower() == "high":
            rename[col] = "High"

        elif col.lower() == "low":
            rename[col] = "Low"

        elif col.lower() == "close":
            rename[col] = "Close"


    return df.rename(columns=rename)



def analyze_market(df):


    if df.empty:

        return {

            "signal":"WAIT",
            "pattern":"No Data",
            "confidence":0

        }



    # Sax columns

    df = normalize_columns(df)



    # Market Structure
    df = analyze_market_structure(df)



    # Chart Patterns
    df = detect_chart_patterns(df)



    last = df.iloc[-1]



    pattern = last.get(
        "Pattern",
        "No Pattern"
    )


    signal = last.get(
        "Signal",
        "WAIT"
    )


    score = last.get(
        "Pattern_Score",
        0
    )



    return {

        "signal": signal,

        "pattern": pattern,

        "confidence": score,

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
            None
        ),

        "CHOCH": last.get(
            "CHOCH",
            None
        )

    }
