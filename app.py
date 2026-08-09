import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# DATA
# ============================================================

try:
    from data.market_data import fetch_market_data, get_timeframes
except ImportError:
    from market_data import fetch_market_data, get_timeframes

# ============================================================
# STRUCTURE
# ============================================================

from structure.swings import (
    analyze_market_structure,
)

# ============================================================
# PATTERNS
# ============================================================

from pattern_engine import detect_patterns

# ============================================================
# INDICATORS
# ============================================================

from indicators.atr import calculate_atr
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi

# ============================================================
# SIGNAL ENGINE
# ============================================================

try:
    from signal_engine import generate_signal
except ImportError:
    generate_signal = None


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Mobile Market Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CLEAN MOBILE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 30px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2px;
    }

    .subtitle {
        text-align: center;
        color: #888;
        font-size: 13px;
        margin-bottom: 18px;
    }

    .signal-card {
        padding: 22px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        text-align: center;
        margin-bottom: 18px;
    }

    .signal-buy {
        font-size: 38px;
        font-weight: 900;
    }

    .signal-sell {
        font-size: 38px;
        font-weight: 900;
    }

    .signal-wait {
        font-size: 38px;
        font-weight: 900;
    }

    .pattern-name {
        font-size: 21px;
        font-weight: 800;
    }

    .small-text {
        color: #888;
        font-size: 13px;
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
    '<div class="subtitle">Pattern Scanner • BUY / SELL / WAIT</div>',
    unsafe_allow_html=True,
)


# ============================================================
# INPUT
# ============================================================

col1, col2 = st.columns([2, 1])

with col1:
    pair = st.text_input(
        "Pair / Symbol",
        value="BTC/USDT",
        placeholder="BTC/USDT, ETH/USDT, EUR/USD, XAU/USD...",
    )

with col2:
    timeframe = st.selectbox(
        "Timeframe",
        get_timeframes(),
        index=6,
    )


history_options = {
    "Short": "60d",
    "Medium": "180d",
    "Long": "1y",
    "Very Long": "5y",
    "Maximum": "max",
}

history = st.selectbox(
    "Historical Data",
    list(history_options.keys()),
    index=1,
)


# ============================================================
# ADVANCED SETTINGS - HIDDEN
# ============================================================

with st.expander("⚙️ Advanced"):
    threshold = st.slider(
        "Major Swing Threshold",
        min_value=0.005,
        max_value=0.050,
        value=0.012,
        step=0.001,
        format="%.3f",
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
        "Geli Pair-ka iyo Timeframe-ka, kadib riix **ANALYZE MARKET**."
    )
    st.stop()


# ============================================================
# FETCH MARKET DATA
# ============================================================

with st.spinner("📡 Market data ayaa la soo dejinayaa..."):

    try:
        df = fetch_market_data(
            pair,
            timeframe,
            history_options[history],
        )

    except Exception as error:

        st.error(
            f"❌ Market data lama helin.\n\n{error}"
        )

        st.stop()


if df is None or df.empty:

    st.error(
        "❌ Market data lama helin."
    )

    st.stop()


# ============================================================
# NORMALIZE DATA
# ============================================================

df = df.copy()

df.columns = [
    str(column).lower()
    for column in df.columns
]


required_columns = {
    "open",
    "high",
    "low",
    "close",
}


missing_columns = (
    required_columns
    - set(df.columns)
)


if missing_columns:

    st.error(
        "❌ Columns ayaa maqan: "
        + ", ".join(sorted(missing_columns))
    )

    st.stop()


if len(df) < 50:

    st.warning(
        f"⚠️ Waxaa jira {len(df)} candles oo keliya."
    )

    st.stop()


# ============================================================
# INDICATORS
# BACKGROUND ONLY
# ============================================================

with st.spinner("📐 Technical calculations..."):

    try:

        df["ATR"] = calculate_atr(
            df,
            14,
        )

        df["EMA7"] = calculate_ema(
            df,
            7,
        )

        df["EMA15"] = calculate_ema(
            df,
            15,
        )

        df["EMA50"] = calculate_ema(
            df,
            50,
        )

        df["EMA200"] = calculate_ema(
            df,
            200,
        )

        df["RSI"] = calculate_rsi(
            df,
            14,
        )

    except Exception as error:

        st.error(
            f"❌ Indicator calculation error: {error}"
        )

        st.stop()


# ============================================================
# MARKET STRUCTURE
# BACKGROUND ONLY
# ============================================================

with st.spinner("🔄 Major market structure..."):

    try:

        structure_result = analyze_market_structure(
            df,
            threshold=threshold,
        )

    except Exception as error:

        st.error(
            f"❌ Structure analysis error: {error}"
        )

        st.stop()


result_df = structure_result["data"]

swings = structure_result.get(
    "swings",
    [],
)

trend = structure_result.get(
    "trend",
    "UNKNOWN",
)

latest_bos = structure_result.get(
    "bos",
    None,
)

latest_choch = structure_result.get(
    "choch",
    None,
)


# ============================================================
# RESTORE INDICATORS
# ============================================================

for column in [
    "ATR",
    "EMA7",
    "EMA15",
    "EMA50",
    "EMA200",
    "RSI",
]:

    if column not in result_df.columns:

        result_df[column] = df[column]


# ============================================================
# PATTERN ENGINE
# BACKGROUND ONLY
# ============================================================

with st.spinner("🔍 Chart patterns ayaa la baarayaa..."):

    try:

        patterns = detect_patterns(
            result_df
        )

    except Exception as error:

        st.error(
            f"❌ Pattern engine error: {error}"
        )

        st.stop()


if patterns is None:
    patterns = []


# ============================================================
# SIGNAL ENGINE
# ============================================================

signal_result = None


if generate_signal is not None:

    try:

        signal_result = generate_signal(
            df=result_df,
            patterns=patterns,
            trend=trend,
            bos=latest_bos,
            choch=latest_choch,
        )

    except Exception:
        signal_result = None


# ============================================================
# FALLBACK SIGNAL
# ============================================================

if signal_result is None:

    signal_result = {
        "signal": "WAIT",
        "direction": "NEUTRAL",
        "quality": 0,
        "reason": "Signal engine lama helin.",
        "entry": None,
        "tp1": None,
        "tp2": None,
        "sl": None,
        "pattern": None,
    }


# ============================================================
# HELPERS
# ============================================================

def fmt(value):

    try:

        if value is None or pd.isna(value):
            return "—"

        return f"{float(value):.6g}"

    except Exception:

        return "—"


def signal_icon(signal):

    signal = str(signal).upper()

    if signal == "BUY":
        return "🟢"

    if signal == "SELL":
        return "🔴"

    return "🟡"


def direction_icon(direction):

    direction = str(direction).upper()

    if direction == "BULLISH":
        return "🟢"

    if direction == "BEARISH":
        return "🔴"

    return "🟡"


# ============================================================
# CURRENT SIGNAL
# ============================================================

main_signal = str(
    signal_result.get(
        "signal",
        "WAIT",
    )
).upper()


main_direction = str(
    signal_result.get(
        "direction",
        "NEUTRAL",
    )
).upper()


quality = signal_result.get(
    "quality",
    0,
)


selected_pattern = signal_result.get(
    "pattern",
)


# ============================================================
# MAIN SIGNAL CARD
# ============================================================

st.divider()

st.markdown(
    f"### {pair.upper()}  •  {timeframe}"
)


if main_signal == "BUY":

    st.success(
        f"""
        ## 🟢 BUY

        **{pair.upper()} • {timeframe}**

        Pattern: **{
            selected_pattern.get("name", "—")
            if isinstance(selected_pattern, dict)
            else "—"
        }**

        Quality: **{quality}%**
        """
    )

elif main_signal == "SELL":

    st.error(
        f"""
        ## 🔴 SELL

        **{pair.upper()} • {timeframe}**

        Pattern: **{
            selected_pattern.get("name", "—")
            if isinstance(selected_pattern, dict)
            else "—"
        }**

        Quality: **{quality}%**
        """
    )

else:

    st.warning(
        f"""
        ## 🟡 WAIT

        **{pair.upper()} • {timeframe}**

        Direction: **{main_direction}**

        Quality: **{quality}%**
        """
    )


# ============================================================
# TRADE LEVELS
# ============================================================

if main_signal in {"BUY", "SELL"}:

    st.subheader("🎯 Trade Levels")

    l1, l2, l3, l4 = st.columns(4)

    with l1:
        st.metric(
            "Entry",
            fmt(signal_result.get("entry")),
        )

    with l2:
        st.metric(
            "TP1",
            fmt(signal_result.get("tp1")),
        )

    with l3:
        st.metric(
            "TP2",
            fmt(signal_result.get("tp2")),
        )

    with l4:
        st.metric(
            "SL",
            fmt(signal_result.get("sl")),
        )


# ============================================================
# ALL DETECTED PATTERNS
# ============================================================

st.divider()

st.subheader("🔎 Detected Patterns")


if not patterns:

    st.info(
        "🟡 Pattern lama helin waqtigan."
    )

else:

    for pattern in patterns:

        name = pattern.get(
            "name",
            "Unknown Pattern",
        )

        direction = str(
            pattern.get(
                "direction",
                "NEUTRAL",
            )
        ).upper()

        pattern_quality = pattern.get(
            "quality",
            0,
        )

        status = str(
            pattern.get(
                "status",
                "WAIT",
            )
        ).upper()

        icon = direction_icon(
            direction
        )

        # ----------------------------------------------------
        # DETERMINE DISPLAY SIGNAL
        # ----------------------------------------------------

        pattern_signal = "WAIT"

        if (
            status == "CONFIRMED"
            and direction == "BULLISH"
            and main_signal == "BUY"
            and isinstance(selected_pattern, dict)
            and selected_pattern.get("name") == name
        ):

            pattern_signal = "BUY"

        elif (
            status == "CONFIRMED"
            and direction == "BEARISH"
            and main_signal == "SELL"
            and isinstance(selected_pattern, dict)
            and selected_pattern.get("name") == name
        ):

            pattern_signal = "SELL"

        # ----------------------------------------------------
        # PATTERN CARD
        # ----------------------------------------------------

        with st.container(border=True):

            p1, p2 = st.columns(
                [3, 1]
            )

            with p1:

                st.markdown(
                    f"### {icon} {name}"
                )

                st.caption(
                    f"Direction: {direction}"
                )

            with p2:

                if pattern_signal == "BUY":

                    st.success(
                        "🟢 BUY"
                    )

                elif pattern_signal == "SELL":

                    st.error(
                        "🔴 SELL"
                    )

                else:

                    st.warning(
                        "🟡 WAIT"
                    )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Quality",
                    f"{pattern_quality}%",
                )

            with c2:

                st.metric(
                    "Pattern",
                    status,
                )

            with c3:

                if status == "CONFIRMED":
                    st.metric(
                        "Decision",
                        pattern_signal,
                    )
                else:
                    st.metric(
                        "Decision",
                        "WAIT",
                    )

            # ------------------------------------------------
            # LEVELS
            # ------------------------------------------------

            e1, e2, e3, e4 = st.columns(4)

            with e1:
                st.metric(
                    "Entry",
                    fmt(
                        pattern.get(
                            "entry"
                        )
                    ),
                )

            with e2:
                st.metric(
                    "TP1",
                    fmt(
                        pattern.get(
                            "tp1"
                        )
                    ),
                )

            with e3:
                st.metric(
                    "TP2",
                    fmt(
                        pattern.get(
                            "tp2"
                        )
                    ),
                )

            with e4:
                st.metric(
                    "SL",
                    fmt(
                        pattern.get(
                            "sl"
                        )
                    ),
                )


# ============================================================
# BACKGROUND INFORMATION
# HIDDEN FROM MAIN SCREEN
# ============================================================

with st.expander("🧠 Signal Engine Details"):

    st.write(
        signal_result.get(
            "reason",
            "—",
        )
    )

    conditions = signal_result.get(
        "conditions",
        [],
    )

    if conditions:

        condition_rows = []

        for name, passed in conditions:

            condition_rows.append(
                {
                    "Condition": name,
                    "Status": (
                        "✅ PASS"
                        if passed
                        else "❌ FAIL"
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                condition_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TECHNICAL DATA
# ============================================================

with st.expander("📐 Technical Data"):

    latest = result_df.iloc[-1]

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.metric(
            "EMA7",
            fmt(latest.get("EMA7")),
        )

    with c2:
        st.metric(
            "EMA15",
            fmt(latest.get("EMA15")),
        )

    with c3:
        st.metric(
            "EMA50",
            fmt(latest.get("EMA50")),
        )

    with c4:
        st.metric(
            "EMA200",
            fmt(latest.get("EMA200")),
        )

    with c5:
        st.metric(
            "RSI",
            fmt(latest.get("RSI")),
        )

    with c6:
        st.metric(
            "ATR",
            fmt(latest.get("ATR")),
        )

    st.write(
        f"Trend: **{trend}**"
    )

    st.write(
        f"BOS: **{latest_bos or '—'}**"
    )

    st.write(
        f"CHOCH: **{latest_choch or '—'}**"
    )


# ============================================================
# PRICE CHART
# HIDDEN
# ============================================================

with st.expander("📈 Price Chart"):

    chart_df = result_df.tail(
        100
    ).copy()

    fig = go.Figure()

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

    for column in [
        "EMA7",
        "EMA15",
        "EMA50",
        "EMA200",
    ]:

        if column in chart_df.columns:

            fig.add_trace(
                go.Scatter(
                    x=chart_df.index,
                    y=chart_df[column],
                    mode="lines",
                    name=column,
                )
            )

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

    fig.update_layout(
        height=600,
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
# RAW DATA
# ============================================================

with st.expander("📋 Raw Market Data"):

    st.dataframe(
        result_df.tail(30),
        use_container_width=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Mobile Market Analyzer • Background Analysis • Pattern Engine • Signal Engine"
    )
