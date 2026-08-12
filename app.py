# ============================================================
# MOBILE ANALYZER
# APP.PY
# YAHOO FINANCE + MAJOR SWINGS + CHART PATTERNS
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from market_data import (
    fetch_market_data,
    get_timeframes,
)

from structure.swings import (
    detect_major_swings,
    analyze_market_structure,
)

from pattern_engine import (
    detect_patterns,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Mobile Market Analyzer",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #888;
        margin-bottom: 20px;
    }

    .pattern-box {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 12px;
    }

    .confirmed {
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📊 Mobile Market Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Yahoo Finance • Major Swings • Chart Patterns • BOS / CHOCH'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# ANALYSIS INPUT
# ============================================================

st.subheader("🔎 Market Analysis")

col1, col2 = st.columns(
    [2, 1]
)

with col1:

    pair = st.text_input(
        "Pair / Symbol",
        value="BTC/USDT",
        placeholder=(
            "BTC/USDT, ETH/USDT, EUR/USD, XAU/USD..."
        ),
    )

with col2:

    timeframe = st.selectbox(
        "Timeframe",
        get_timeframes(),
        index=6,
    )


# ============================================================
# HISTORY
# ============================================================

history_options = {

    "Short": "60d",

    "Medium": "180d",

    "Long": "1y",

    "Very Long": "5y",

    "Maximum": "max",
}


history = st.selectbox(
    "📅 Historical Data",
    list(history_options.keys()),
    index=1,
)


# ============================================================
# SWING SETTINGS
# ============================================================

with st.expander(
    "⚙️ Advanced Swing Settings"
):

    threshold = st.slider(
        "Major Swing Threshold",
        min_value=0.005,
        max_value=0.050,
        value=0.012,
        step=0.001,
        format="%.3f",
        help=(
            "Higher value = fewer and stronger "
            "major swings."
        ),
    )


# ============================================================
# ANALYZE BUTTON
# ============================================================

analyze = st.button(
    "🔍 ANALYZE MARKET",
    type="primary",
    use_container_width=True,
)


if not analyze:

    st.info(
        "Geli pair-ka, dooro timeframe-ka, "
        "kadib riix **ANALYZE MARKET**."
    )

    st.stop()


# ============================================================
# DOWNLOAD MARKET DATA
# ============================================================

with st.spinner(
    f"📡 Yahoo Finance ayaa keenaya xogta {pair}..."
):

    try:

        df = fetch_market_data(
            pair,
            timeframe,
            history_options[history],
        )

    except Exception as error:

        st.error(
            f"❌ Xogta lama helin.\n\n{error}"
        )

        st.stop()


# ============================================================
# DATA VALIDATION
# ============================================================

if df is None or df.empty:

    st.error(
        "❌ Yahoo Finance wax xog ah kama soo celin."
    )

    st.stop()


if len(df) < 50:

    st.warning(
        f"⚠️ Waxaa la helay {len(df)} candles oo keliya. "
        "Major swing engine wuxuu u baahan yahay ugu yaraan "
        "50 candles."
    )

    st.stop()


# ============================================================
# MAJOR SWING ENGINE
# ============================================================

with st.spinner(
    "🔄 Waxaa la baarayaa major swings..."
):

    try:

        structure_result = (
            analyze_market_structure(
                df,
                threshold=threshold,
            )
        )

    except Exception as error:

        st.error(
            f"❌ Swing analysis error: {error}"
        )

        st.stop()


result_df = structure_result[
    "data"
]

swings = structure_result[
    "swings"
]

trend = structure_result[
    "trend"
]

latest_bos = structure_result[
    "bos"
]

latest_choch = structure_result[
    "choch"
]


# ============================================================
# PATTERN ENGINE
# ============================================================

with st.spinner(
    "🔍 Waxaa la baarayaa chart patterns..."
):

    try:

        patterns = detect_patterns(
            result_df
        )

    except Exception as error:

        st.error(
            f"❌ Pattern engine error: {error}"
        )

        st.stop()


# ============================================================
# TOP SUMMARY
# ============================================================

st.divider()

st.subheader(
    f"📈 {pair.upper()} — {timeframe}"
)

m1, m2, m3, m4 = st.columns(4)

with m1:

    st.metric(
        "Trend",
        trend,
    )

with m2:

    st.metric(
        "Major Swings",
        len(swings),
    )

with m3:

    st.metric(
        "Latest BOS",
        latest_bos
        if latest_bos
        else "—",
    )

with m4:

    st.metric(
        "Latest CHOCH",
        latest_choch
        if latest_choch
        else "—",
    )


# ============================================================
# TREND STATUS
# ============================================================

if trend == "BULLISH":

    st.success(
        "🟢 BULLISH MARKET STRUCTURE"
    )

elif trend == "BEARISH":

    st.error(
        "🔴 BEARISH MARKET STRUCTURE"
    )

elif trend == "RANGING":

    st.warning(
        "🟡 RANGING MARKET STRUCTURE"
    )

else:

    st.info(
        "⚪ MARKET STRUCTURE UNKNOWN"
    )


# ============================================================
# PATTERNS
# ============================================================

st.subheader(
    "🎯 Detected Chart Patterns"
)


if not patterns:

    st.info(
        "Pattern la aqoonsaday lagama helin "
        "major swings-ka hadda jira."
    )

else:

    for pattern in patterns:

        name = pattern[
            "name"
        ]

        direction = pattern[
            "direction"
        ]

        quality = pattern[
            "quality"
        ]

        status = pattern[
            "status"
        ]

        reason = pattern[
            "reason"
        ]

        if direction == "BULLISH":

            icon = "🟢"

        elif direction == "BEARISH":

            icon = "🔴"

        else:

            icon = "🟡"


        with st.container(
            border=True
        ):

            p1, p2, p3 = st.columns(
                [2, 1, 1]
            )

            with p1:

                st.markdown(
                    f"### {icon} {name}"
                )

            with p2:

                st.metric(
                    "Quality",
                    f"{quality}%",
                )

            with p3:

                st.metric(
                    "Status",
                    status,
                )


            st.write(
                f"**Direction:** {direction}"
            )

            st.write(
                f"**Reason:** {reason}"
            )


            entry = pattern.get(
                "entry"
            )

            tp1 = pattern.get(
                "tp1"
            )

            tp2 = pattern.get(
                "tp2"
            )

            sl = pattern.get(
                "sl"
            )


            e1, e2, e3, e4 = st.columns(
                4
            )


            with e1:

                st.metric(
                    "Entry",
                    (
                        f"{entry:.6g}"
                        if entry is not None
                        else "—"
                    ),
                )


            with e2:

                st.metric(
                    "TP1",
                    (
                        f"{tp1:.6g}"
                        if tp1 is not None
                        else "—"
                    ),
                )


            with e3:

                st.metric(
                    "TP2",
                    (
                        f"{tp2:.6g}"
                        if tp2 is not None
                        else "—"
                    ),
                )


            with e4:

                st.metric(
                    "SL",
                    (
                        f"{sl:.6g}"
                        if sl is not None
                        else "—"
                    ),
                )


# ============================================================
# CANDLESTICK CHART
# ============================================================

st.subheader(
    "🕯️ Price Chart + Major Swings"
)


chart_df = result_df.tail(
    100
).copy()


fig = go.Figure()


# ============================================================
# CANDLES
# ============================================================

fig.add_trace(
    go.Candlestick(

        x=chart_df.index,

        open=chart_df[
            "open"
        ],

        high=chart_df[
            "high"
        ],

        low=chart_df[
            "low"
        ],

        close=chart_df[
            "close"
        ],

        name="Price",
    )
)


# ============================================================
# MAJOR ZIGZAG
# ============================================================

zigzag = chart_df[
    chart_df[
        "zigzag"
    ].notna()
]


if not zigzag.empty:

    fig.add_trace(
        go.Scatter(

            x=zigzag.index,

            y=zigzag[
                "zigzag"
            ],

            mode=(
                "lines+markers+text"
            ),

            text=zigzag[
                "structure"
            ],

            textposition=(
                "top center"
            ),

            name="Major ZigZag",
        )
    )


# ============================================================
# SWING HIGH MARKERS
# ============================================================

swing_highs = chart_df[
    chart_df[
        "swing_high"
    ]
]


if not swing_highs.empty:

    fig.add_trace(
        go.Scatter(

            x=swing_highs.index,

            y=swing_highs[
                "high"
            ],

            mode="markers",

            name="Major High",
        )
    )


# ============================================================
# SWING LOW MARKERS
# ============================================================

swing_lows = chart_df[
    chart_df[
        "swing_low"
    ]
]


if not swing_lows.empty:

    fig.add_trace(
        go.Scatter(

            x=swing_lows.index,

            y=swing_lows[
                "low"
            ],

            mode="markers",

            name="Major Low",
        )
    )


# ============================================================
# CHART SETTINGS
# ============================================================

fig.update_layout(

    height=700,

    xaxis_rangeslider_visible=False,

    hovermode="x unified",

    margin=dict(
        l=10,
        r=10,
        t=30,
        b=10,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# MAJOR SWINGS TABLE
# ============================================================

with st.expander(
    "🔄 Major Swings"
):

    if swings:

        swing_df = pd.DataFrame(
            swings
        )

        st.dataframe(
            swing_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Major swings lama helin."
        )


# ============================================================
# BOS / CHOCH EVENTS
# ============================================================

with st.expander(
    "⚡ BOS / CHOCH Events"
):

    events = result_df[
        result_df[
            "BOS"
        ].notna()
        |
        result_df[
            "CHOCH"
        ].notna()
    ].copy()


    if events.empty:

        st.info(
            "BOS ama CHOCH lama helin."
        )

    else:

        columns = [
            "close",
            "zigzag_type",
            "structure",
            "BOS",
            "CHOCH",
        ]

        columns = [
            c
            for c in columns
            if c in events.columns
        ]

        st.dataframe(
            events[
                columns
            ],
            use_container_width=True,
        )


# ============================================================
# DATA INFORMATION
# ============================================================

with st.expander(
    "📋 Data Information"
):

    st.write(
        "**Source:** Yahoo Finance"
    )

    st.write(
        f"**Yahoo Symbol:** "
        f"{df.attrs.get('yahoo_symbol', '—')}"
    )

    st.write(
        f"**Pair:** {pair.upper()}"
    )

    st.write(
        f"**Timeframe:** {timeframe}"
    )

    st.write(
        f"**Candles:** {len(df)}"
    )

    st.write(
        f"**Latest Close:** "
        f"{float(df['close'].iloc[-1]):.6g}"
    )


# ============================================================
# RAW DATA
# ============================================================

with st.expander(
    "🧾 Latest OHLC Data"
):

    st.dataframe(
        result_df.tail(30),
        use_container_width=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Mobile Analyzer • Yahoo Finance only • "
    "Major Swing Pattern Engine"
)
