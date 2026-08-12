# ============================================================
# MOBILE ANALYZER
# APP.PY
# YAHOO FINANCE + MAJOR SWINGS + PROFESSIONAL PATTERNS
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


from data.market_data import (
    fetch_market_data,
    get_timeframes,
)


from structure.swings import (
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
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #888;
        margin-bottom: 20px;
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
    'Yahoo Finance • Major Swings • Professional Chart Patterns • BOS / CHOCH'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# INPUT
# ============================================================

st.subheader("🔎 Market Analysis")


c1, c2 = st.columns(
    [2, 1]
)


with c1:

    pair = st.text_input(
        "Pair / Symbol",
        value="BTC/USDT",
        placeholder=(
            "BTC/USDT, ETH/USDT, EUR/USD, XAU/USD..."
        ),
    )


with c2:

    timeframes = get_timeframes()

    timeframe = st.selectbox(
        "Timeframe",
        timeframes,
        index=min(6, len(timeframes) - 1),
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
            "Higher value = fewer but stronger "
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
        "kadib riix ANALYZE MARKET."
    )

    st.stop()


# ============================================================
# DOWNLOAD DATA
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
# VALIDATION
# ============================================================

if df is None or df.empty:

    st.error(
        "❌ Yahoo Finance wax xog ah kama soo celin."
    )

    st.stop()


if len(df) < 50:

    st.warning(
        f"⚠️ Waxaa la helay {len(df)} candles oo keliya. "
        "Major Swing Engine wuxuu u baahan yahay ugu yaraan "
        "50 candles."
    )

    st.stop()


# ============================================================
# MARKET STRUCTURE
# ============================================================

with st.spinner(
    "🔄 Waxaa la baarayaa Major Swings..."
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


result_df = structure_result["data"]

swings = structure_result["swings"]

trend = structure_result["trend"]

latest_bos = structure_result["bos"]

latest_choch = structure_result["choch"]


# ============================================================
# PATTERN ENGINE
# ============================================================

with st.spinner(
    "🔍 Waxaa la baarayaa professional chart patterns..."
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
# SUMMARY
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
        latest_bos if latest_bos else "—",
    )


with m4:

    st.metric(
        "Latest CHOCH",
        latest_choch if latest_choch else "—",
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
# PATTERN SUMMARY
# ============================================================

st.subheader(
    "🎯 Detected Chart Patterns"
)


if not patterns:

    st.info(
        "Pattern xirfad leh lagama helin "
        "major swings-ka hadda jira."
    )

else:

    st.caption(
        "Patterns-ka waxaa loo kala hormariyey "
        "quality + confirmation + structure strength."
    )


# ============================================================
# PATTERN SELECTOR
# ============================================================

selected_pattern = None


if patterns:

    pattern_names = [
        (
            f"{i + 1}. "
            f"{p['name']} — "
            f"{p['direction']} — "
            f"{p['quality']}% — "
            f"{p['status']}"
        )
        for i, p in enumerate(patterns)
    ]


    selected_name = st.selectbox(
        "👆 Dooro pattern si chart-ku kuu tuso",
        pattern_names,
    )


    selected_index = pattern_names.index(
        selected_name
    )


    selected_pattern = patterns[
        selected_index
    ]


# ============================================================
# PATTERN CARDS
# ============================================================

if patterns:

    for i, pattern in enumerate(patterns):

        name = pattern.get(
            "name",
            "Pattern",
        )

        direction = pattern.get(
            "direction",
            "NEUTRAL",
        )

        quality = pattern.get(
            "quality",
            0,
        )

        status = pattern.get(
            "status",
            "FORMING",
        )

        reason = pattern.get(
            "reason",
            "",
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


        if direction == "BULLISH":

            icon = "🟢"

            action = "BUY"

        elif direction == "BEARISH":

            icon = "🔴"

            action = "SELL"

        else:

            icon = "🟡"

            action = "WAIT"


        if status == "CONFIRMED":

            status_icon = "✅"

        elif status == "FORMING":

            status_icon = "⏳"

        else:

            status_icon = "⚠️"


        with st.container(
            border=True
        ):

            p1, p2, p3, p4 = st.columns(
                [2.4, 1, 1, 1]
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
                    f"{status_icon} {status}",
                )


            with p4:

                st.metric(
                    "Action",
                    action,
                )


            st.write(
                f"**Direction:** {direction}"
            )

            st.write(
                f"**Reason:** {reason}"
            )


            e1, e2, e3, e4 = st.columns(4)


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
# SELECTED PATTERN INFO
# ============================================================

if selected_pattern is not None:

    st.subheader(
        f"🎯 Selected Pattern: "
        f"{selected_pattern['name']}"
    )

    if selected_pattern["status"] == "CONFIRMED":

        st.success(
            "✅ Pattern-kan waa CONFIRMED."
        )

    else:

        st.warning(
            "⏳ Pattern-kan wali waa FORMING. "
            "Breakout confirmation ayaa loo baahan yahay."
        )


# ============================================================
# CHART
# ============================================================

st.subheader(
    "🕯️ Price Chart + Major Swings + Pattern"
)


chart_df = result_df.tail(
    150
).copy()


fig = go.Figure()


# ============================================================
# CANDLESTICKS
# ============================================================

fig.add_trace(
    go.Candlestick(

        x=chart_df.index,

        open=chart_df["open"],

        high=chart_df["high"],

        low=chart_df["low"],

        close=chart_df["close"],

        name="Price",
    )
)


# ============================================================
# MAJOR ZIGZAG
# ============================================================

if "zigzag" in chart_df.columns:

    zigzag = chart_df[
        chart_df["zigzag"].notna()
    ]

    if not zigzag.empty:

        fig.add_trace(
            go.Scatter(

                x=zigzag.index,

                y=zigzag["zigzag"],

                mode="lines+markers",

                name="Major ZigZag",
            )
        )


# ============================================================
# SWING HIGH MARKERS
# ============================================================

if "swing_high" in chart_df.columns:

    swing_highs = chart_df[
        chart_df["swing_high"]
    ]

    if not swing_highs.empty:

        fig.add_trace(
            go.Scatter(

                x=swing_highs.index,

                y=swing_highs["high"],

                mode="markers",

                marker=dict(
                    size=9,
                    symbol="triangle-up",
                ),

                name="Major High",
            )
        )


# ============================================================
# SWING LOW MARKERS
# ============================================================

if "swing_low" in chart_df.columns:

    swing_lows = chart_df[
        chart_df["swing_low"]
    ]

    if not swing_lows.empty:

        fig.add_trace(
            go.Scatter(

                x=swing_lows.index,

                y=swing_lows["low"],

                mode="markers",

                marker=dict(
                    size=9,
                    symbol="triangle-down",
                ),

                name="Major Low",
            )
        )


# ============================================================
# PATTERN DRAWING
# ============================================================

def get_chart_x(index_value):

    if index_value is None:
        return None

    try:

        if index_value in chart_df.index:

            return index_value

    except Exception:
        pass

    try:

        pos = int(index_value)

        if 0 <= pos < len(result_df):

            return result_df.index[pos]

    except Exception:
        pass

    return None


def draw_selected_pattern(
    figure,
    pattern
):

    if pattern is None:
        return


    points = pattern.get(
        "points",
        []
    )


    valid_points = []

    for point in points:

        x = get_chart_x(
            point.get("index")
        )

        y = point.get(
            "price"
        )

        if x is None or y is None:
            continue

        try:

            y = float(y)

        except Exception:

            continue

        valid_points.append(
            (
                x,
                y,
                point.get("type", "")
            )
        )


    if not valid_points:
        return


    # --------------------------------------------------------
    # Pattern point lines
    # --------------------------------------------------------

    figure.add_trace(
        go.Scatter(

            x=[
                p[0]
                for p in valid_points
            ],

            y=[
                p[1]
                for p in valid_points
            ],

            mode="lines+markers+text",

            text=[
                p[2]
                for p in valid_points
            ],

            textposition="top center",

            line=dict(
                width=4,
            ),

            marker=dict(
                size=12,
            ),

            name=(
                "Pattern: "
                + pattern["name"]
            ),
        )
    )


    # --------------------------------------------------------
    # Neckline
    # --------------------------------------------------------

    neckline_points = pattern.get(
        "neckline_points",
        []
    )


    nx = []
    ny = []


    for point in neckline_points:

        x = get_chart_x(
            point.get("index")
        )

        y = point.get(
            "price"
        )

        if x is None or y is None:
            continue

        try:

            y = float(y)

        except Exception:

            continue

        nx.append(x)
        ny.append(y)


    if len(nx) >= 2:

        figure.add_trace(
            go.Scatter(

                x=nx,

                y=ny,

                mode="lines",

                line=dict(
                    dash="dash",
                    width=3,
                ),

                name="Pattern Neckline",
            )
        )

    elif len(nx) == 1:

        figure.add_trace(
            go.Scatter(

                x=nx,

                y=ny,

                mode="markers",

                marker=dict(
                    size=10,
                ),

                name="Pattern Neckline",
            )
        )


    # --------------------------------------------------------
    # ENTRY / TP / SL
    # --------------------------------------------------------

    levels = [
        (
            "ENTRY",
            pattern.get("entry"),
        ),
        (
            "TP1",
            pattern.get("tp1"),
        ),
        (
            "TP2",
            pattern.get("tp2"),
        ),
        (
            "SL",
            pattern.get("sl"),
        ),
    ]


    for label, value in levels:

        if value is None:
            continue

        try:

            value = float(value)

        except Exception:

            continue

        figure.add_hline(
            y=value,

            line_dash="dot",

            annotation_text=(
                f"{label} "
                f"{value:.6g}"
            ),

            annotation_position=(
                "top right"
            ),
        )


    # --------------------------------------------------------
    # Pattern title
    # --------------------------------------------------------

    if valid_points:

        middle = valid_points[
            len(valid_points) // 2
        ]

        figure.add_annotation(

            x=middle[0],

            y=middle[1],

            text=(
                f"{pattern['name']} "
                f"({pattern['quality']}%)"
            ),

            showarrow=True,

            arrowhead=2,
        )


# ============================================================
# DRAW SELECTED PATTERN
# ============================================================

draw_selected_pattern(
    fig,
    selected_pattern
)


# ============================================================
# CHART LAYOUT
# ============================================================

fig.update_layout(

    height=750,

    xaxis_rangeslider_visible=False,

    hovermode="x unified",

    margin=dict(
        l=10,
        r=10,
        t=40,
        b=10,
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="left",
        x=0,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# TRADE PLAN
# ============================================================

if selected_pattern is not None:

    st.subheader(
        "📋 Professional Trade Plan"
    )


    p = selected_pattern


    if p["direction"] == "BULLISH":

        st.success(
            "🟢 BUY SETUP"
        )

    elif p["direction"] == "BEARISH":

        st.error(
            "🔴 SELL SETUP"
        )

    else:

        st.warning(
            "🟡 WAIT — Breakout confirmation required"
        )


    t1, t2, t3, t4 = st.columns(4)


    with t1:

        st.metric(
            "Entry",
            (
                f"{p['entry']:.6g}"
                if p.get("entry") is not None
                else "WAIT"
            ),
        )


    with t2:

        st.metric(
            "Stop Loss",
            (
                f"{p['sl']:.6g}"
                if p.get("sl") is not None
                else "—"
            ),
        )


    with t3:

        st.metric(
            "Take Profit 1",
            (
                f"{p['tp1']:.6g}"
                if p.get("tp1") is not None
                else "—"
            ),
        )


    with t4:

        st.metric(
            "Take Profit 2",
            (
                f"{p['tp2']:.6g}"
                if p.get("tp2") is not None
                else "—"
            ),
        )


    if p["status"] == "FORMING":

        st.info(
            "⚠️ Setup-ku wali ma xaqiijin. "
            "Entry-ga ha loo qaadan trade toos ah "
            "ilaa breakout + candle close la helo."
        )

    elif p["status"] == "CONFIRMED":

        st.success(
            "✅ Breakout confirmation ayaa la helay."
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
# BOS / CHOCH
# ============================================================

with st.expander(
    "⚡ BOS / CHOCH Events"
):

    if (
        "BOS" not in result_df.columns
        and
        "CHOCH" not in result_df.columns
    ):

        st.info(
            "BOS / CHOCH columns lama helin."
        )

    else:

        bos_mask = (
            result_df["BOS"].notna()
            if "BOS" in result_df.columns
            else False
        )

        choch_mask = (
            result_df["CHOCH"].notna()
            if "CHOCH" in result_df.columns
            else False
        )

        try:

            events = result_df[
                bos_mask | choch_mask
            ].copy()

        except Exception:

            events = pd.DataFrame()


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
                events[columns],
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
    "Professional Major Swing Pattern Engine"
        )
