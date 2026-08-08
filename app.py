# ============================================================
# MOBILE ANALYZER
# APP.PY
# STREAMLIT MARKET STRUCTURE + MAJOR SWING ANALYZER
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

from structure.swings import (
    detect_major_swings,
    analyze_market_structure,
    get_major_swings,
    get_latest_structure,
    get_trend,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Mobile Analyzer",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("📊 Mobile Analyzer")

st.caption(
    "Major Swing • ZigZag • Market Structure • BOS • CHOCH • Trend"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Settings")

threshold = st.sidebar.slider(
    "ZigZag Threshold",
    min_value=0.005,
    max_value=0.050,
    value=0.012,
    step=0.001,
    format="%.3f",
)

st.sidebar.info(
    "Major swing analysis uses the last 50 candles."
)


# ============================================================
# DATA INPUT
# ============================================================

st.subheader("📥 OHLC Data")

uploaded_file = st.file_uploader(
    "Upload CSV file",
    type=["csv"],
)


# ============================================================
# DEMO DATA
# ============================================================

def create_demo_data():

    np.random.seed(42)

    candles = 100

    close = [100.0]

    for _ in range(candles - 1):

        change = np.random.normal(
            0,
            1.2
        )

        close.append(
            max(
                1,
                close[-1] + change
            )
        )

    close = np.array(close)

    high = close + np.random.uniform(
        0.2,
        1.5,
        candles
    )

    low = close - np.random.uniform(
        0.2,
        1.5,
        candles
    )

    open_price = (
        close
        + np.random.uniform(
            -0.8,
            0.8,
            candles
        )
    )

    volume = np.random.uniform(
        1000,
        5000,
        candles
    )

    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


# ============================================================
# LOAD DATA
# ============================================================

if uploaded_file is not None:

    try:

        df = pd.read_csv(
            uploaded_file
        )

        # Convert column names to lowercase
        df.columns = [
            str(c).strip().lower()
            for c in df.columns
        ]

    except Exception as e:

        st.error(
            f"❌ Failed to read CSV: {e}"
        )

        st.stop()

else:

    st.info(
        "No CSV uploaded. Demo OHLC data is being used."
    )

    df = create_demo_data()


# ============================================================
# VALIDATE OHLC
# ============================================================

required_columns = [
    "open",
    "high",
    "low",
    "close",
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:

    st.error(
        "❌ Missing required OHLC columns: "
        + ", ".join(missing)
    )

    st.write(
        "Required columns:"
    )

    st.code(
        "open, high, low, close"
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

for column in required_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(
    subset=required_columns
).reset_index(
    drop=True
)


# ============================================================
# MINIMUM DATA
# ============================================================

if len(df) < 50:

    st.warning(
        f"⚠️ At least 50 candles are required. "
        f"Current candles: {len(df)}"
    )

    st.stop()


# ============================================================
# RUN MARKET STRUCTURE ENGINE
# ============================================================

try:

    analysis = analyze_market_structure(
        df,
        threshold=threshold
    )

except Exception as e:

    st.error(
        f"❌ Market structure error: {e}"
    )

    st.stop()


# ============================================================
# RESULTS
# ============================================================

result_df = analysis["data"]

swings = analysis["swings"]

trend = analysis["trend"]

latest_bos = analysis["bos"]

latest_choch = analysis["choch"]


# ============================================================
# TOP METRICS
# ============================================================

st.subheader("📈 Market Structure")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Trend",
        trend
    )

with col2:

    st.metric(
        "Major Swings",
        len(swings)
    )

with col3:

    st.metric(
        "Latest BOS",
        latest_bos if latest_bos else "None"
    )

with col4:

    st.metric(
        "Latest CHOCH",
        latest_choch if latest_choch else "None"
    )


# ============================================================
# TREND MESSAGE
# ============================================================

if trend == "BULLISH":

    st.success(
        "🟢 Market structure is BULLISH"
    )

elif trend == "BEARISH":

    st.error(
        "🔴 Market structure is BEARISH"
    )

elif trend == "RANGING":

    st.warning(
        "🟡 Market structure is RANGING"
    )

else:

    st.info(
        "⚪ Market structure is UNKNOWN"
    )


# ============================================================
# MAJOR SWINGS
# ============================================================

st.subheader("🔄 Major Swings")

if swings:

    swing_table = pd.DataFrame(
        swings
    )

    display_columns = [
        "index",
        "type",
        "price",
        "structure",
    ]

    display_columns = [
        c
        for c in display_columns
        if c in swing_table.columns
    ]

    st.dataframe(
        swing_table[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No major swings detected."
    )


# ============================================================
# LATEST STRUCTURE
# ============================================================

st.subheader("🎯 Latest Structure")

latest_structure = get_latest_structure(
    df,
    threshold=threshold
)

if latest_structure:

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Type",
            latest_structure["type"]
        )

    with c2:

        st.metric(
            "Price",
            f'{latest_structure["price"]:.6f}'
        )

    with c3:

        st.metric(
            "Structure",
            latest_structure["structure"]
        )

    with c4:

        st.metric(
            "Candle",
            latest_structure["index"]
        )

else:

    st.info(
        "No latest structure available."
    )


# ============================================================
# MARKET DATA
# ============================================================

st.subheader("🕯️ Latest Candles")

latest_columns = [
    c
    for c in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "swing_high",
        "swing_low",
        "zigzag",
        "zigzag_type",
        "structure",
        "BOS",
        "CHOCH",
    ]
    if c in result_df.columns
]

st.dataframe(
    result_df[
        latest_columns
    ].tail(20),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# SWING CHART
# ============================================================

st.subheader("📊 Price + Major Swings")

chart_df = result_df[
    [
        "close",
        "zigzag",
    ]
].copy()

chart_df = chart_df.tail(50)

st.line_chart(
    chart_df,
    use_container_width=True,
)


# ============================================================
# BOS / CHOCH EVENTS
# ============================================================

st.subheader("⚡ BOS / CHOCH Events")

events = result_df[
    result_df["BOS"].notna()
    |
    result_df["CHOCH"].notna()
].copy()

if not events.empty:

    event_columns = [
        "close",
        "zigzag_type",
        "structure",
        "BOS",
        "CHOCH",
    ]

    event_columns = [
        c
        for c in event_columns
        if c in events.columns
    ]

    st.dataframe(
        events[
            event_columns
        ].tail(20),
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No BOS / CHOCH events detected."
    )


# ============================================================
# ENGINE INFORMATION
# ============================================================

with st.expander(
    "🔧 Engine Information"
):

    st.write(
        "Lookback:",
        50
    )

    st.write(
        "ZigZag Threshold:",
        threshold
    )

    st.write(
        "Minimum Swing Distance:",
        2
    )

    st.write(
        "Maximum Swings:",
        30
    )

    st.write(
        "Candles analyzed:",
        len(df)
    )


# ============================================================
# RAW DATA
# ============================================================

with st.expander(
    "📋 Raw Analysis Data"
):

    st.dataframe(
        result_df.tail(100),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Mobile Analyzer — Major Swing / ZigZag Market Structure Engine"
    )
