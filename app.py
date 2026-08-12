import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from data.market_data import fetch_market_data, get_timeframes
except ImportError:
    from market_data import fetch_market_data, get_timeframes

from structure.market_structure import analyze_market_structure
from pattern_engine import detect_patterns, get_best_pattern

from indicators.atr import calculate_atr
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi


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
        margin-bottom: 5px;
    }

    .subtitle {
        color: #888;
        margin-bottom: 20px;
    }

    .best-pattern {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
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
    'Yahoo Finance • Current Active Pattern Engine • EMA • RSI • ATR • BOS / CHOCH'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# MARKET INPUT
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

    st.selectbox(
        "Timeframe",
        timeframes,
        index=min(6, len(timeframes) - 1),
        key="timeframe",
    )

timeframe = st.session_state["timeframe"]


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
        "Geli pair-ka, dooro timeframe-ka, kadib riix **ANALYZE MARKET**."
    )
    st.stop()


# ============================================================
# FETCH MARKET DATA
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


if df is None or df.empty:

    st.error(
        "❌ Yahoo Finance wax xog ah kama soo celin."
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
        "❌ Market data columns ayaa maqan: "
        + ", ".join(sorted(missing_columns))
    )

    st.stop()


if len(df) < 50:

    st.warning(
        f"⚠️ Waxaa la helay {len(df)} candles oo keliya. "
        "Major swing engine wuxuu u baahan yahay ugu yaraan 50 candles."
    )

    st.stop()


# ============================================================
# INDICATORS
# ============================================================

with st.spinner(
    "📐 Waxaa la xisaabinayaa ATR, EMA iyo RSI..."
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
#
# IMPORTANT:
# We still calculate major swings because the pattern engine
# needs them internally.
#
# They are NOT displayed on the chart.
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
            f"❌ Market structure error: {error}"
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
)

latest_choch = structure_result.get(
    "choch",
)


# ============================================================
# PRESERVE MAJOR SWINGS FOR PATTERN ENGINE
#
# The engine reads:
# df.attrs["major_swings"]
# ============================================================

result_df = result_df.copy()

result_df.attrs["major_swings"] = swings


# ============================================================
# COPY INDICATORS INTO RESULT DATA
# ============================================================

for col in [
    "ATR",
    "EMA7",
    "EMA15",
    "EMA50",
    "EMA200",
    "RSI",
]:

    if col not in result_df.columns:

        result_df[col] = df[col]


# ============================================================
# PATTERN ENGINE
# ============================================================

with st.spinner(
    "🔍 Waxaa la baarayaa CURRENT ACTIVE PATTERNS..."
):

    try:

        patterns = detect_patterns(
            result_df
        )

        best_pattern = (
            patterns[0]
            if patterns
            else None
        )

    except Exception as error:

        st.error(
            f"❌ Pattern engine error: {error}"
        )

        st.stop()


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


def get_signal(pattern):

    if not pattern:
        return "WAIT"

    status = str(
        pattern.get(
            "status",
            ""
        )
    ).upper()

    direction = str(
        pattern.get(
            "direction",
            ""
        )
    ).upper()

    if status == "READY":

        if direction == "BUY":
            return "BUY"

        if direction == "SELL":
            return "SELL"

    return "WAIT"


def get_signal_icon(signal):

    if signal == "BUY":
        return "🟢"

    if signal == "SELL":
        return "🔴"

    return "🟡"


def get_direction_icon(direction):

    if direction == "BUY":
        return "🟢"

    if direction == "SELL":
        return "🔴"

    return "🟡"


# ============================================================
# PATTERN POINTS
# ============================================================

def get_pattern_points(pattern):

    """
    pattern_engine.py returns:

        "points": [
            {
                "name": ...,
                "index": ...,
                "price": ...,
                "type": ...
            }
        ]

    This function converts those points into dataframe x-values.
    """

    points = pattern.get(
        "points",
        [],
    )

    if not points:
        return []


    output = []


    for point in points:

        try:

            if not isinstance(
                point,
                dict,
            ):
                continue


            idx = point.get(
                "index"
            )

            price = point.get(
                "price"
            )


            if idx is None or price is None:
                continue


            price = float(price)


            # Exact dataframe index
            if idx in result_df.index:

                x = idx

            else:

                # Candle position
                try:

                    pos = int(idx)

                    if (
                        pos < 0
                        or pos >= len(result_df)
                    ):
                        continue

                    x = result_df.index[pos]

                except Exception:

                    continue


            output.append(
                (
                    x,
                    price,
                )
            )

        except Exception:

            continue


    return output


# ============================================================
# DRAW ONLY BEST PATTERN
# ============================================================

def add_best_pattern_drawing(
    fig,
    pattern,
    chart_df,
):

    if not pattern:
        return False


    points = get_pattern_points(
        pattern
    )


    if len(points) < 2:
        return False


    visible = [
        (x, y)
        for x, y in points
        if x in chart_df.index
    ]


    if len(visible) < 2:
        return False


    x_values = [
        item[0]
        for item in visible
    ]

    y_values = [
        item[1]
        for item in visible
    ]


    name = pattern.get(
        "name",
        "Pattern",
    )

    direction = pattern.get(
        "direction",
        "WAIT",
    )

    status = pattern.get(
        "status",
        "FORMING",
    )


    # --------------------------------------------
    # Pattern structure line
    # --------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name=f"ACTIVE • {name}",
            line=dict(
                width=4,
            ),
            marker=dict(
                size=10,
            ),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Price: %{y}<br>"
                f"Direction: {direction}<br>"
                f"Status: {status}"
                "<extra></extra>"
            ),
        )
    )


    # --------------------------------------------
    # Point labels
    # --------------------------------------------

    point_names = []

    for point in pattern.get(
        "points",
        [],
    ):

        point_names.append(
            point.get(
                "name",
                "",
            )
        )


    if len(point_names) == len(
        visible
    ):

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="text",
                text=point_names,
                textposition="top center",
                name=f"{name} points",
                showlegend=False,
                hoverinfo="skip",
            )
        )


    # --------------------------------------------
    # Entry / neckline
    # --------------------------------------------

    entry = pattern.get(
        "entry"
    )

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
                name="Entry / Neckline",
                line=dict(
                    width=2,
                    dash="dash",
                ),
                hovertemplate=(
                    "<b>Entry / Neckline</b><br>"
                    "Level: %{y}"
                    "<extra></extra>"
                ),
            )
        )


    # --------------------------------------------
    # TP1
    # --------------------------------------------

    tp1 = pattern.get(
        "tp1"
    )

    try:

        tp1 = float(tp1)

    except Exception:

        tp1 = None


    if tp1 is not None:

        fig.add_trace(
            go.Scatter(
                x=[
                    x_values[0],
                    x_values[-1],
                ],
                y=[
                    tp1,
                    tp1,
                ],
                mode="lines",
                name="TP1",
                line=dict(
                    width=1.5,
                    dash="dot",
                ),
                hovertemplate=(
                    "<b>TP1</b><br>"
                    "Price: %{y}"
                    "<extra></extra>"
                ),
            )
        )


    # --------------------------------------------
    # TP2
    # --------------------------------------------

    tp2 = pattern.get(
        "tp2"
    )

    try:

        tp2 = float(tp2)

    except Exception:

        tp2 = None


    if tp2 is not None:

        fig.add_trace(
            go.Scatter(
                x=[
                    x_values[0],
                    x_values[-1],
                ],
                y=[
                    tp2,
                    tp2,
                ],
                mode="lines",
                name="TP2",
                line=dict(
                    width=1.5,
                    dash="dot",
                ),
                hovertemplate=(
                    "<b>TP2</b><br>"
                    "Price: %{y}"
                    "<extra></extra>"
                ),
            )
        )


    # --------------------------------------------
    # SL
    # --------------------------------------------

    sl = pattern.get(
        "sl"
    )

    try:

        sl = float(sl)

    except Exception:

        sl = None


    if sl is not None:

        fig.add_trace(
            go.Scatter(
                x=[
                    x_values[0],
                    x_values[-1],
                ],
                y=[
                    sl,
                    sl,
                ],
                mode="lines",
                name="SL",
                line=dict(
                    width=1.5,
                    dash="dash",
                ),
                hovertemplate=(
                    "<b>SL</b><br>"
                    "Price: %{y}"
                    "<extra></extra>"
                ),
            )
        )


    return True


# ============================================================
# LATEST VALUES
# ============================================================

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
# PAGE TITLE
# ============================================================

st.divider()

st.subheader(
    f"📈 {pair.upper()} — {timeframe}"
)


# ============================================================
# MARKET SUMMARY
# ============================================================

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


# ============================================================
# BASIC MARKET CONDITIONS
# ============================================================

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

    try:

        atr_missing = pd.isna(
            atr_value
        )

    except Exception:

        atr_missing = True


    if not atr_missing:

        st.info(
            f"📏 ATR(14): {fmt(atr_value)}"
        )

    else:

        st.warning(
            "ATR lama helin"
        )


# ============================================================
# MARKET STRUCTURE
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
# CURRENT ACTIVE PATTERNS
# ============================================================

st.subheader(
    "🎯 Current Active Patterns"
)


if not patterns:

    st.info(
        "Pattern hadda active ah lagama helin "
        "major swings-ka ugu dambeeya."
    )

else:

    # --------------------------------------------------------
    # BEST PATTERN
    # --------------------------------------------------------

    best = patterns[0]

    best_name = best.get(
        "n
