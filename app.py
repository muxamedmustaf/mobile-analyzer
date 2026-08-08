# ============================================================
# MOBILE ANALYZER
# APP.PY
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from swing import (
    detect_major_swings,
    analyze_market_structure,
)

from patterns import (
    detect_patterns,
)


# ============================================================
# PAGE
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
    "Major Swing + ZigZag + Market Structure + Pattern Engine"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Market Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload OHLC CSV",
    type=["csv"],
)


# ============================================================
# DATA LOADER
# ============================================================

def load_csv(file):

    df = pd.read_csv(file)

    # Normalize column names
    df.columns = [
        str(c).strip().lower()
        for c in df.columns
    ]

    # Common timestamp names
    rename = {}

    if "date" in df.columns:
        rename["date"] = "timestamp"

    if "datetime" in df.columns:
        rename["datetime"] = "timestamp"

    if "time" in df.columns:
        rename["time"] = "timestamp"

    df = df.rename(
        columns=rename
    )

    required = [
        "open",
        "high",
        "low",
        "close",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        st.error(
            f"CSV-ga waxaa ka maqan: {missing}"
        )
        st.stop()

    for col in required:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=required
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# DEMO DATA
# ============================================================

def generate_demo():

    import numpy as np

    np.random.seed(42)

    n = 250

    returns = np.random.normal(
        0,
        0.008,
        n
    )

    close = (
        100
        *
        np.exp(
            np.cumsum(returns)
        )
    )

    open_price = np.roll(
        close,
        1
    )

    open_price[0] = close[0]

    high = np.maximum(
        open_price,
        close
    ) * (
        1
        +
        np.random.uniform(
            0,
            0.008,
            n
        )
    )

    low = np.minimum(
        open_price,
        close
    ) * (
        1
        -
        np.random.uniform(
            0,
            0.008,
            n
        )
    )

    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
    })


# ============================================================
# LOAD DATA
# ============================================================

if uploaded_file is not None:

    df = load_csv(
        uploaded_file
    )

else:

    st.info(
        "Upload OHLC CSV si aad u falanqayso market-ka."
    )

    if st.button(
        "▶ Run Demo"
    ):

        df = generate_demo()

    else:

        st.stop()


# ============================================================
# DATA CHECK
# ============================================================

if len(df) < 50:

    st.error(
        "Engine-ku wuxuu u baahan yahay ugu yaraan 50 candles."
    )

    st.stop()


# ============================================================
# RUN SWING ENGINE
# ============================================================

try:

    swing_df = detect_major_swings(
        df
    )

except Exception as e:

    st.error(
        f"Swing Engine Error: {e}"
    )

    st.stop()


# ============================================================
# MARKET STRUCTURE
# ============================================================

try:

    structure_result = (
        analyze_market_structure(
            swing_df
        )
    )

    analysis_df = (
        structure_result["data"]
    )

    trend = (
        structure_result["trend"]
    )

    latest_bos = (
        structure_result["bos"]
    )

    latest_choch = (
        structure_result["choch"]
    )

except Exception as e:

    st.error(
        f"Market Structure Error: {e}"
    )

    st.stop()


# ============================================================
# PATTERN ENGINE
# ============================================================

try:

    detected_patterns = detect_patterns(
        analysis_df
    )

except Exception as e:

    st.error(
        f"Pattern Engine Error: {e}"
    )

    detected_patterns = []


# ============================================================
# TOP METRICS
# ============================================================

major_swings = (
    analysis_df[
        (
            analysis_df["swing_high"]
            |
            analysis_df["swing_low"]
        )
    ]
)

confirmed_patterns = [
    p
    for p in detected_patterns
    if p["confirmation"]
    == "CONFIRMED"
]


c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "Trend",
        trend
    )

with c2:

    st.metric(
        "Major Swings",
        len(major_swings)
    )

with c3:

    st.metric(
        "BOS",
        latest_bos or "None"
    )

with c4:

    st.metric(
        "CHOCH",
        latest_choch or "None"
    )

with c5:

    st.metric(
        "Confirmed",
        len(confirmed_patterns)
    )


# ============================================================
# MAIN CHART
# ============================================================

st.subheader(
    "📈 Market Structure Chart"
)

fig = go.Figure()


# ------------------------------------------------------------
# Candles
# ------------------------------------------------------------

fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    )
)


# ============================================================
# ZIGZAG
# ============================================================

zigzag = analysis_df[
    analysis_df["zigzag"].notna()
]

if len(zigzag) > 1:

    fig.add_trace(
        go.Scatter(
            x=zigzag.index,
            y=zigzag["zigzag"],
            mode="lines+markers",
            name="Major ZigZag",
            line=dict(
                width=2
            ),
        )
    )


# ============================================================
# SWING HIGH
# ============================================================

swh = analysis_df[
    analysis_df["swing_high"]
]

if len(swh) > 0:

    fig.add_trace(
        go.Scatter(
            x=swh.index,
            y=swh["high"],
            mode="markers+text",
            text=["SH"] * len(swh),
            textposition="top center",
            name="Major High",
            marker=dict(
                size=9,
                symbol="triangle-up",
            ),
        )
    )


# ============================================================
# SWING LOW
# ============================================================

swl = analysis_df[
    analysis_df["swing_low"]
]

if len(swl) > 0:

    fig.add_trace(
        go.Scatter(
            x=swl.index,
            y=swl["low"],
            mode="markers+text",
            text=["SL"] * len(swl),
            textposition="bottom center",
            name="Major Low",
            marker=dict(
                size=9,
                symbol="triangle-down",
            ),
        )
    )


# ============================================================
# STRUCTURE LABELS
# ============================================================

structure_rows = analysis_df[
    analysis_df["structure"].notna()
]

if len(structure_rows) > 0:

    fig.add_trace(
        go.Scatter(
            x=structure_rows.index,
            y=structure_rows["close"],
            mode="text",
            text=structure_rows[
                "structure"
            ],
            textposition="middle center",
            name="Structure",
        )
    )


# ============================================================
# BOS / CHOCH
# ============================================================

bos_rows = analysis_df[
    analysis_df["BOS"].notna()
]

if len(bos_rows) > 0:

    fig.add_trace(
        go.Scatter(
            x=bos_rows.index,
            y=bos_rows["close"],
            mode="markers+text",
            text=bos_rows["BOS"],
            textposition="top center",
            name="BOS",
            marker=dict(
                size=11,
                symbol="diamond",
            ),
        )
    )


choch_rows = analysis_df[
    analysis_df["CHOCH"].notna()
]

if len(choch_rows) > 0:

    fig.add_trace(
        go.Scatter(
            x=choch_rows.index,
            y=choch_rows["close"],
            mode="markers+text",
            text=choch_rows["CHOCH"],
            textposition="bottom center",
            name="CHOCH",
            marker=dict(
                size=11,
                symbol="star",
            ),
        )
    )


# ============================================================
# LAYOUT
# ============================================================

fig.update_layout(
    height=700,
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# PATTERN RESULTS
# ============================================================

st.subheader(
    "🔎 Detected Patterns"
)

if not detected_patterns:

    st.warning(
        "Pattern lama helin oo buuxiyay shuruudaha strict engine-ka."
    )

else:

    rows = []

    for p in detected_patterns:

        rows.append({
            "Pattern": p["pattern"],
            "Direction": p["direction"],
            "Confidence": f'{p["confidence"]}%',
            "Quality": p["quality"],
            "Status": p["confirmation"],
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# BEST PATTERN
# ============================================================

if detected_patterns:

    best = detected_patterns[0]

    st.subheader(
        "🏆 Best Pattern"
    )

    b1, b2, b3, b4 = st.columns(4)

    with b1:
        st.metric(
            "Pattern",
            best["pattern"]
        )

    with b2:
        st.metric(
            "Direction",
            best["direction"]
        )

    with b3:
        st.metric(
            "Confidence",
            f'{best["confidence"]}%'
        )

    with b4:
        st.metric(
            "Status",
            best["confirmation"]
        )

    st.write(
        "### Pattern Details"
    )

    st.json(
        best["details"]
    )


# ============================================================
# RAW STRUCTURE DATA
# ============================================================

with st.expander(
    "🧩 Show Market Structure Data"
):

    columns = [
        "open",
        "high",
        "low",
        "close",
        "swing_high",
        "swing_low",
        "zigzag",
        "zigzag_type",
        "structure",
        "BOS",
        "CHOCH",
    ]

    available = [
        c
        for c in columns
        if c in analysis_df.columns
    ]

    st.dataframe(
        analysis_df[
            available
        ].tail(100),
        use_container_width=True,
        )
