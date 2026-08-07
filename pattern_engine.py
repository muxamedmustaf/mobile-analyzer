# ==========================================
# PROFESSIONAL PATTERN ENGINE
# CONNECTOR FOR APP.PY
# ==========================================


from pivot_scanner import PivotScanner

from patterns.double import DoublePatternDetector

from patterns.head_shoulders import HeadShouldersDetector

from filters.confirmation import PatternConfirmationEngine

from filters.market import MarketContextFilter

from signal import FinalSignalGenerator



def normalize_columns(df):
    """
    Sax columns-ka app.py-gaaga
    oo isticmaala:
    Open High Low Close
    """

    rename = {}

    for col in df.columns:

        if col.lower() == "open":
            rename[col] = "open"

        elif col.lower() == "high":
            rename[col] = "high"

        elif col.lower() == "low":
            rename[col] = "low"

        elif col.lower() == "close":
            rename[col] = "close"



    return df.rename(
        columns=rename
    )





def analyze_market(df):


    # 1. Column normalization

    df = normalize_columns(df)



    # 2. Pivot Scanner

    scanner = PivotScanner(
        depth=5
    )


    pivots = scanner.find_pivots(
        df
    )



    if len(pivots) < 5:

        return {

            "signal":
            "WAIT",

            "pattern":
            "No Pattern",

            "confidence":
            0,

            "reason":
            "Pivots not enough"

        }




    # 3. Pattern Detection

    patterns=[]



    double = DoublePatternDetector()


    patterns += (
        double.detect_double_top(
            pivots
        )
    )


    patterns += (
        double.detect_double_bottom(
            pivots
        )
    )



    hs = HeadShouldersDetector()



    patterns += (
        hs.detect_head_shoulders(
            pivots
        )
    )


    patterns += (
        hs.detect_inverse_head_shoulders(
            pivots
        )
    )



    if not patterns:

        return {

            "signal":
            "WAIT",

            "pattern":
            "No Pattern",

            "confidence":
            0

        }



    # Dooro pattern-ka ugu fiican

    best_pattern = max(
        patterns,
        key=lambda x:x["score"]
    )



    # 4. Confirmation

    confirmation_engine = (
        PatternConfirmationEngine()
    )


    confirmation = (
        confirmation_engine.confirm(
            best_pattern,
            df
        )
    )



    if not confirmation["confirmed"]:

        return {

            "signal":
            "WAIT",

            "pattern":
            best_pattern["pattern"],

            "confidence":
            confirmation["final_score"],

            "reason":
            "Breakout not confirmed"

        }





    # 5. Market Filter

    market_filter = (
        MarketContextFilter()
    )


    market = (
        market_filter.check(
            df,
            best_pattern
        )
    )



    # 6. Final Decision

    generator = FinalSignalGenerator()



    result = generator.generate(

        best_pattern,

        confirmation,

        market,

        df

    )



    return result
