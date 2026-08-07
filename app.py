import streamlit as st
import pandas as pd
import numpy as np
from pattern_engine import PatternEngine, EngineConfig

st.set_page_config(
    page_title="Major Pattern Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Major Pattern Analyzer")
st.caption("Chart-pattern analysis using major swings and candle-close confirmation.")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Engine Settings")

    pivot_left = st.number_input(
        "Pivot left candles",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

    pivot_right = st.number_input(
        "Pivot right candles",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

    min_swing_pct = st.number_input(
        "Minimum swing %",
        min_value=0.1,
        max_value=10.0,
        value=0.4,
        step=0.1,
        format="%.1f",
    ) / 100

    level_tolerance = st.number_input(
        "Pattern level tolerance %",
        min_value=0.5,
        max_value=10.0,
        value=2.5,
        step=0.5,
        format="%.1f",
    ) / 100

    breakout_buffer = st.number_input(
        "Breakout buffer %",
        min_value=0.0,
        max_value=2.0,
        value=0.1,
        step=0.1,
        format="%.1f",
    ) / 100

    min_confidence = st.slider(
        "Minimum confidence",
        min_value=50,
        max_value=95,
        value=60,
    )

    st.divider()
    st.info(
        "Pattern-ka lama xaqiijinayo wick keliya. "
        "Engine-ku wuxuu sugayaa candle close marka breakout loo baahan yahay."
    )

# -----------------------------
# Config
# -----------------------------
config = EngineConfig(
    pivot_left=int(pivot_left),
    pivot_right=int(pivot_right),
    min_swing_pct=float(min_swing_pct),
    level_tolerance=float(level_tolerance),
    tight_level_tolerance=min(float(level_tolerance), 0.02),
    breakout_buffer=float(breakout_buffer),
    min_confidence=int(min_confidence),
)

engine = PatternEngine(config)

# -----------------------------
# Data input
# -----------------------------
st.subheader("1. Geli OHLC Data")

uploaded = st.file_uploader(
    "Upload CSV file",
    type=["csv"],
    help="CSV-ga waa inuu leeyahay High, Low, Close. Open iyo Volume waa optional.",
)

df = None

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"CSV lama akhrin karin: {e}")

else:
    st.markdown(
        "CSV ma haysatid? Hoos ku geli xogta OHLC oo tusaale ahaan leh "
        "`Open, High, Low, Close, Volume`."
    )

    sample = pd.DataFrame(
        {
            "Open": [100, 101, 103, 102, 105, 108, 106, 104],
            "High": [102, 104, 105, 106, 109, 110, 108, 106],
            "Low": [99, 100, 101, 101, 103, 105, 104, 102],
            "Close": [101, 103, 102, 105, 108, 106, 104, 105],
            "Volume": [1000] * 8,
        }
    )

    if st.checkbox("Show example data"):
        st.dataframe(sample, use_container_width=True)

# -----------------------------
# Analysis
# -----------------------------
if df is not None:
    st.subheader("2. Analysis")

    try:
        result = engine.analyze(df)

        if result.get("error"):
            st.warning(result["error"])
        else:
            patterns = result["patterns"]
            swings = result["major_swings"]
            best = result["best_pattern"]

            # Summary
            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Candles", len(df))
            c2.metric("Major Swings", len(swings))
            c3.metric("Patterns", len(patterns))

            if best:
                c4.metric("Best Pattern", best["pattern"])
            else:
                c4.metric("Best Pattern", "None")

            st.divider()

            # Best signal
            if best:
                status = best["status"]
                direction = best["direction"]

                if status == "CONFIRMED":
                    st.success(
                        f"✅ CONFIRMED: {best['pattern']} — {direction} "
                        f"({best['confidence']}%)"
                    )
                elif status == "FORMING":
                    st.warning(
                        f"⏳ FORMING: {best['pattern']} — {direction} "
                        f"({best['confidence']}%)"
                    )

                col1, col2, col3 = st.columns(3)

                col1.write("**Entry**")
                col1.write(best.get("entry") if best.get("entry") is not None else "-")

                col2.write("**Stop Loss**")
                col2.write(
                    best.get("stop_loss")
                    if best.get("stop_loss") is not None
                    else "-"
                )

                col3.write("**Target**")
                col3.write(
                    best.get("target")
                    if best.get("target") is not None
                    else "-"
                )

                st.write(f"**Reason:** {best.get('reason', '')}")

            else:
                st.info(
                    "Pattern la xaqiijiyey lama helin. "
                    "Engine-ku wuxuu sugayaa major structure ku habboon."
                )

            # Pattern table
            st.subheader("Detected Patterns")

            if patterns:
                rows = []

                for p in patterns:
                    rows.append(
                        {
                            "Pattern": p["pattern"],
                            "Status": p["status"],
                            "Direction": p["direction"],
                            "Confidence": f"{p['confidence']}%",
                            "Entry": (
                                round(p["entry"], 6)
                                if p.get("entry") is not None
                                else "-"
                            ),
                            "SL": (
                                round(p["stop_loss"], 6)
                                if p.get("stop_loss") is not None
                                else "-"
                            ),
                            "Target": (
                                round(p["target"], 6)
                                if p.get("target") is not None
                                else "-"
                            ),
                        }
                    )

                table = pd.DataFrame(rows)
                st.dataframe(table, use_container_width=True, hide_index=True)

                with st.expander("Pattern details"):
                    for p in patterns:
                        st.markdown(
                            f"### {p['pattern']} — {p['status']}"
                        )
                        st.write(
                            {
                                "direction": p["direction"],
                                "confidence": p["confidence"],
                                "neckline": p.get("neckline"),
                                "resistance": p.get("resistance"),
                                "support": p.get("support"),
                                "entry": p.get("entry"),
                                "stop_loss": p.get("stop_loss"),
                                "target": p.get("target"),
                                "invalidation": p.get("invalidation"),
                                "reason": p.get("reason"),
                            }
                        )

            # Major swings
            st.subheader("Major Swings")

            if swings:
                swing_df = pd.DataFrame(swings)
                st.dataframe(
                    swing_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Major swings lama helin.")

            # Raw data
            with st.expander("OHLC Data"):
                st.dataframe(df.tail(100), use_container_width=True)

    except Exception as e:
        st.error(f"Analysis error: {e}")
        st.exception(e)

else:
    st.info(
        "Ku bilow adigoo upload-gareynaya CSV leh High, Low, Close. "
        "Engine-ku wuxuu markaas baarayaa major swings iyo patterns."
    )

st.divider()
st.caption(
    "Pattern Analyzer v1 — Structure → Major Swings → Confirmation → Confidence"
)
