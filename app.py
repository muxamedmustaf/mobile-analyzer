app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from data.market_data import fetch_market_data, get_timeframes
except ImportError:
    from market_data import fetch_market_data, get_timeframes

from structure.swings import analyze_market_structure
from pattern_engine import detect_patterns, get_best_pattern

from indicators.atr import calculate_atr
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Mobile Market Analyzer",
    page_icon="📊",
    layout="wide",
)

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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">📊 Mobile Market Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Yahoo Finance • Current Active Patterns • EMA • RSI • ATR</div>',
    unsafe_allow_html=True,
)


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


def pattern_icon(direction):
    if direction == "BUY":
        return "🟢"
    if direction == "SELL":
        return "🔴"
    return "🟡"


def resolve_chart_index(result_df, chart_df, index_value):
    """
    Pattern engine wuxuu soo celin karaa candle position ama
    dataframe index.
    """

    if index_value in chart_df.index:
        return index_value

    try:
        position = int(index_value)
    except Exception:
        return None

    if 0 <= position < len(result_df):
        real_index = result_df.index[position]

        if real_index in chart_df.index:
            return real_index

    return None


def draw_pattern(fig, pattern, result_df, chart_df):
    """
    Kaliya hal pattern ayaa chart-ka lagu sawirayaa:
    pattern-ka ugu xooggan/current active pattern.

    Pattern points waxay si toos ah uga imanayaan:
        pattern["points"]
    """

    if not pattern:
        return False

    points = pattern.get("points", [])

    if not isinstance(points, list):
        return False

    if len(points) < 2:
        return False

    visible = []

    for point in points:

        if not isinstance(point, dict):
            continue

        idx = point.get("index")
        price = point.get("price")

        try:
            price = float(price)
        except Exception:
            continue

        x = resolve_chart_index(
            result_df,
            chart_df,
            idx,
        )

        if x is None:
            continue

        visible.append(
            {
                "x": x,
                "price": price,
                "name": point.get("name", "POINT"),
            }
        )

    if len(visible) < 2:
        return False

    name = pattern.get("name", "Pattern")
    direction = pattern.get("direction", "NEUTRAL")
    status = pattern.get("status", "FORMING")

    x_values = [p["x"] for p in visible]
    y_values = [p["price"] for p in visible]

    if direction == "BUY":
        dash = "solid"
    elif direction == "SELL":
        dash = "dash"
    else:
        dash = "dot"

    # --------------------------------------------------------
    # PATTERN STRUCTURE
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name=f"ACTIVE • {name}",
            line=dict(
                width=4,
                dash=dash,
            ),
            marker=dict(
                size=10,
            ),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Price: %{y}<extra></extra>"
            ),
        )
    )

    # --------------------------------------------------------
    # POINT LABELS
    # --------------------------------------------------------

    labels = [
        p["name"]
        for p in visible
    ]

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="text",
            text=labels,
            textposition="top center",
            name=f"{name} points",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # --------------------------------------------------------
    # ENTRY / NECKLINE
    # --------------------------------------------------------

    entry = pattern.get("entry")

    try:
        entry = float(entry)
    except Exception:
        entry = None

    if entry is not None:

        fig.add_trace(
            go.Scatter(
                x=[
                    x_values[0],
                    x_values[-1],
                ],
                y=[
                    entry,
                    entry,
                ],
                mode="lines",
                name=f"{name} Entry / Neckline",
                line=dict(
                    width=2,
                    dash="dashdot",
                ),
                hovertemplate=(
                    f"<b>{name} Entry / Neckline</b><br>"
                    "Level: %{y}<extra></extra>"
                ),
            )
        )

    return True


# ============================================================
# INPUT
# ============================================================

st.subheader("🔎 Market Analysis")

col1, col2 = st.columns([2, 1])

with col1:

    pair = st.text_input(
        "Pair / Symbol",
        value="BTC/USDT",
        placeholder="BTC/USDT, ETH/USDT, EUR/USD, XAU/USD...",
    )

with col2:

    timeframes = get_timeframes()

    if not timeframes:
        st.error("❌ Timeframes lama helin.")
        st.stop()

    timeframe_index = 6 if len(timeframes) > 6 else 0

    timeframe = st.selectbox(
        "Timeframe",
        timeframes,
        index=timeframe_index,
    )


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


with st.expander("⚙️ Advanced Swing Settings"):

    threshold = st.slider(
        "Major Swing Threshold",
        min_value=0.005,
        max_value=0.050,
        value=0.012,
        step=0.001,
        format="%.3f",
        help="Higher value = fewer and stronger major swings.",
    )


analyze = st.button(
    "🔍 ANALYZE MARKET",
    type="primary",
    use_container_width=True,
)


if not analyze:

    st.info(
        "Geli pair-ka, dooro timeframe-ka, kadib riix ANALYZE MARKET."
    )

    st.stop()


# ============================================================
# MARKET DATA
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
            f"❌ Xogta lama helin:\n\n{error}"
        )

        st.stop()


if df is None or df.empty:

    st.error(
        "❌ Yahoo Finance wax xog ah kama soo celin."
    )

    st.stop()


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

missing = required_columns.difference(
    df.columns
)

if missing:

    st.error(
        "❌ Columns ayaa maqan: "
        + ", ".join(sorted(missing))
    )

    st.stop()


if len(df) < 50:

    st.warning(
        f"⚠️ Waxaa la helay {len(df)} candles oo keliya. "
        "Ugu yaraan 50 candles ayaa loo baahan yahay."
    )

    st.stop()


# ============================================================
# INDICATORS
# ============================================================

with st.spinner(
    "📐 Waxaa la xisaabinayaa indicators..."
):

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
# ============================================================

with st.spinner(
    "🔄 Waxaa la baarayaa market structure..."
):

    try:

        structure_result = analyze_market_structure(
            df,
            threshold=threshold,
        )

    except Exception as error:

        st.error(
            f"❌ Swing analysis error: {error}"
        )

        st.stop()


if not isinstance(
    structure_result,
    dict,
):

    st.error(
        "❌ Market structure engine-ku "
        "ma soo celin dictionary sax ah."
    )

    st.stop()


result_df = structure_result.get(
    "data",
    df.copy(),
)

swings = structure_result.get(
    "swings",
    [],
)

trend = structure_result.get(
    "trend",
    "UNKNOWN",
)

latest_bos = structure_result.get(
    "bos"
)

latest_choch = structure_result.get(
    "choch"
)


result_df = result_df.copy()


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
# CURRENT ACTIVE PATTERNS
# ============================================================

with st.spinner(
    "🔍 Waxaa la baarayaa current active patterns..."
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


# Pattern engine cusub ayaa hore u kala hormariyey.
# Sidaas darteed kan ugu horreeya waa strongest pattern.

best_pattern = (
    patterns[0]
    if patterns
    else None
)


latest = result_df.iloc[-1]


close_value = latest.get(
    "close"
)

atr_value = latest.get(
    "ATR"
)

ema7_value = latest.get(
    "EMA7"
)

ema15_value = latest.get(
    "EMA15"
)

ema50_value = latest.get(
    "EMA50"
)

ema200_value = latest.get(
    "EMA200"
)

rsi_value = latest.get(
    "RSI"
)


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
        "Active Patterns",
        len(patterns),
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
# INDICATORS
# ============================================================

st.subheader(
    "📐 Technical Indicators"
)


i1, i2, i3, i4, i5, i6 = st.columns(6)


with i1:
    st.metric(
        "EMA 7",
        fmt(ema7_value),
    )

with i2:
    st.metric(
        "EMA 15",
        fmt(ema15_value),
    )

with i3:
    st.metric(
        "EMA 50",
        fmt(ema50_value),
    )

with i4:
    st.metric(
        "EMA 200",
        fmt(ema200_value),
    )

with i5:
    st.metric(
        "RSI 14",
        fmt(rsi_value),
    )

with i6:
    st.metric(
        "ATR 14",
        fmt(atr_value),
    )


try:

    ema200_ok = (
        float(close_value)
        > float(ema200_value)
    )

except Exception:

    ema200_ok = False


try:

    rsi_ok = (
        30
        < float(rsi_value)
        < 70
    )

except Exception:

    rsi_ok = False


s1, s2, s3 = st.columns(3)


with s1:

    if ema200_ok:
        st.success(
            "🟢 Price > EMA200"
        )
    else:
        st.error(
            "🔴 Price ≤ EMA200"
        )


with s2:

    if rsi_ok:
        st.success(
            "🟢 RSI 30–70"
        )
    else:
        st.warning(
            "🟡 RSI outside 30–70"
        )


with s3:

    if pd.notna(atr_value):
        st.info(
            f"📏 ATR(14): {fmt(atr_value)}"
        )
    else:
        st.warning(
            "ATR lama helin"
        )


# ============================================================
# MARKET STRUCTURE STATUS
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
# BEST CURRENT PATTERN
# ============================================================

st.subheader(
    "🏆 Strongest Current Pattern"
)


if best_pattern is None:

    st.info(
        "Pattern active ah lama helin. "
        "Patterns hore ama breakout-kii dhacay "
        "waa la iska indhatiray."
    )

else:

    name = best_pattern.get(
        "name",
        "Pattern",
    )

    direction = best_pattern.get(
        "direction",
        "NEUTRAL",
    )

    quality = best_pattern.get(
        "quality",
        0,
    )

    status = best_pattern.get(
        "status",
        "FORMING",
    )

    reason = best_pattern.get(
        "reason",
        "—",
    )

    icon = pattern_icon(
        direction
    )


    with st.container(
        border=True
    ):

        st.markdown(
            f"## {icon} {name}"
        )


        b1, b2, b3 = st.columns(3)


        with b1:

            st.metric(
                "Quality",
                f"{quality}%",
            )


        with b2:

            st.metric(
                "Direction",
                direction,
            )


        with b3:

            st.metric(
                "Status",
                status,
            )


        st.write(
            f"**Reason:** {reason}"
        )


        p1, p2, p3, p4 = st.columns(4)


        with p1:

            st.metric(
                "Entry",
                fmt(
                    best_pattern.get(
                        "entry"
                    )
                ),
            )


        with p2:

            st.metric(
                "TP1",
                fmt(
                    best_pattern.get(
                        "tp1"
                    )
                ),
            )


        with p3:

            st.metric(
                "TP2",
                fmt(
                    best_pattern.get(
                        "tp2"
                    )
                ),
            )


        with p4:

            st.metric(
                "SL",
                fmt(
                    best_pattern.get(
                        "sl"
                    )
                ),
            )


        if status == "READY":

            st.success(
                "🟢 READY — price-ku wuxuu ku dhow yahay entry/neckline."
            )

        else:

            st.warning(
                "⏳ FORMING — pattern-ku wali wuu samaysmayaa."
            )


# ============================================================
# ACTIVE PATTERNS RANKING
# ============================================================

st.subheader(
    "🎯 Current Active Patterns — Quality Ranking"
)


if not patterns:

    st.info(
        "Ma jiraan current active patterns."
    )

else:

    for pattern in patterns:

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
            "—",
        )

        rank = pattern.get(
            "rank",
            "—",
        )

        icon = pattern_icon(
            direction
        )


        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = st.columns(
                [3, 1, 1, 1]
            )


            with c1:

                st.markdown(
                    f"### {icon} #{rank} {name}"
                )


            with c2:

                st.metric(
                    "Quality",
                    f"{quality}%",
                )


            with c3:

                st.metric(
                    "Direction",
                    direction,
                )


            with c4:

                st.metric(
                    "Status",
                    status,
                )


            st.write(
                f"**Reason:** {reason}"
            )


# ============================================================
# PRICE CHART
# ============================================================

st.subheader(
    "🕯️ Price Chart + Strongest Current Pattern"
)


chart_df = result_df.tail(
    150
).copy()


fig = go.Figure()


# ------------------------------------------------------------
# CANDLES
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# EMA
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# ONLY BEST PATTERN
# ------------------------------------------------------------

drawn = draw_pattern(
    fig,
    best_pattern,
    result_df,
    chart_df,
)


fig.update_layout(
    height=720,
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


if best_pattern and drawn:

    st.success(
        "📌 Chart-ka waxaa lagu sawiray oo keliya "
        f"pattern-ka ugu xooggan: {best_pattern.get('name')}."
    )

elif best_pattern:

    st.warning(
        "Pattern-ka ugu xooggan waa la helay, "
        "laakiin points-kiisu kuma jiraan chart window-ga."
    )


# ============================================================
# CURRENT PATTERN POINTS
# ============================================================

with st.expander(
    "📍 Current Pattern Points"
):

    if (
        best_pattern
        and best_pattern.get("points")
    ):

        rows = []

        for point in best_pattern["points"]:

            rows.append(
                {
                    "Point": point.get(
                        "name"
                    ),
                    "Index": point.get(
                        "index"
                    ),
                    "Price": point.get(
                        "price"
                    ),
                    "Type": point.get(
                        "type"
                    ),
                }
            )


        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Current pattern points lama helin."
        )


# ============================================================
# BOS / CHOCH
# ============================================================

with st.expander(
    "⚡ BOS / CHOCH Events"
):

    if "BOS" in result_df.columns:

        bos_mask = result_df[
            "BOS"
        ].notna()

    else:

        bos_mask = pd.Series(
            False,
            index=result_df.index,
        )


    if "CHOCH" in result_df.columns:

        choch_mask = result_df[
            "CHOCH"
        ].notna()

    else:

        choch_mask = pd.Series(
            False,
            index=result_df.index,
        )


    events = result_df[
        bos_mask | choch_mask
    ].copy()


    if events.empty:

        st.info(
            "BOS ama CHOCH lama helin."
        )

    else:

        columns = [
            column
            for column in [
                "close",
                "zigzag_type",
                "structure",
                "BOS",
                "CHOCH",
            ]
            if column in events.columns
        ]


        st.dataframe(
            events[columns],
            use_container_width=True,
        )


# ============================================================
# INDICATOR DATA
# ============================================================

with st.expander(
    "📐 Indicator Data"
):

    columns = [
        column
        for column in [
            "close",
            "ATR",
            "EMA7",
            "EMA15",
            "EMA50",
            "EMA200",
            "RSI",
        ]
        if column in result_df.columns
    ]


    st.dataframe(
        result_df[columns].tail(30),
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
        f"**Latest Close:** {fmt(close_value)}"
    )


# ============================================================
# OHLC
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
    "Mobile Analyzer • Yahoo Finance • "
    "Current Active Pattern Engine • "
    "Strongest Pattern Drawing • EMA • RSI • ATR")

