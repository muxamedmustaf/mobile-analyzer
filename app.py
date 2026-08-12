import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from data.market_data import fetch_market_data, get_timeframes
except ImportError:
    from market_data import fetch_market_data, get_timeframes

from structure.swings import analyze_market_structure
from pattern_engine import detect_patterns

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
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="main-title">📊 Mobile Market Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Yahoo Finance • Current Active Pattern • EMA • RSI • ATR • BOS / CHOCH'
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

    timeframe = st.selectbox(
        "Timeframe",
        timeframes,
        index=min(6, len(timeframes) - 1),
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
        "Geli pair-ka, dooro timeframe-ka, kadib riix "
        "**ANALYZE MARKET**."
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


df = df.copy()

df.columns = [
    str(column).lower()
    for column in df.columns
]


# ============================================================
# REQUIRED COLUMNS
# ============================================================

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
        + ", ".join(
            sorted(missing_columns)
        )
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
# ============================================================

with st.spinner(
    "🔄 Waxaa la baarayaa major market structure..."
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


result_df = structure_result.get(
    "data",
    df.copy(),
).copy()


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
# IMPORTANT
# Pattern Engine wuxuu major swings ka akhriyaa
# df.attrs["major_swings"]
# ============================================================

result_df.attrs["major_swings"] = swings


# Restore indicators if structure engine removed them.

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
    "🔍 Waxaa la baarayaa CURRENT ACTIVE PATTERNS..."
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


# Pattern engine already sorts strongest first.
best_pattern = (
    patterns[0]
    if patterns
    else None
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


def direction_icon(direction):

    direction = str(
        direction or ""
    ).upper()

    if direction == "BUY":
        return "🟢"

    if direction == "SELL":
        return "🔴"

    return "🟡"


def action_for(pattern):

    if not pattern:
        return "WAIT"

    direction = str(
        pattern.get(
            "direction",
            "",
        )
    ).upper()

    status = str(
        pattern.get(
            "status",
            "",
        )
    ).upper()

    if (
        status == "READY"
        and direction in {"BUY", "SELL"}
    ):

        return direction

    return "WAIT"


def get_pattern_points(
    pattern,
    data,
):

    if not pattern:
        return []

    points = pattern.get(
        "points",
        [],
    )

    output = []

    for point in points:

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

        try:

            price = float(price)

        except Exception:

            continue

        try:

            if idx in data.index:

                x = idx

            else:

                position = int(idx)

                if (
                    position < 0
                    or position >= len(data)
                ):
                    continue

                x = data.index[
                    position
                ]

        except Exception:

            continue

        output.append(
            {
                "x": x,
                "price": price,
                "name": point.get(
                    "name",
                    "",
                ),
            }
        )

    return output


def add_level(
    fig,
    x0,
    x1,
    level,
    name,
    dash="dot",
):

    if level is None:
        return

    try:

        level = float(level)

    except Exception:

        return

    fig.add_trace(
        go.Scatter(
            x=[
                x0,
                x1,
            ],
            y=[
                level,
                level,
            ],
            mode="lines",
            name=name,
            line=dict(
                width=1.5,
                dash=dash,
            ),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Price: %{y}"
                "<extra></extra>"
            ),
        )
    )


def draw_best_pattern(
    fig,
    pattern,
    chart_df,
    source_df,
):

    if not pattern:
        return False

    points = get_pattern_points(
        pattern,
        source_df,
    )

    if len(points) < 2:
        return False

    visible = [
        point
        for point in points
        if point["x"] in chart_df.index
    ]

    if len(visible) < 2:
        return False

    x_values = [
        point["x"]
        for point in visible
    ]

    y_values = [
        point["price"]
        for point in visible
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

    quality = pattern.get(
        "quality",
        0,
    )

    # ========================================================
    # PATTERN STRUCTURE
    # ========================================================

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name=f"⭐ ACTIVE • {name}",
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
                f"Status: {status}<br>"
                f"Quality: {quality}/100"
                "<extra></extra>"
            ),
        )
    )

    # ========================================================
    # POINT LABELS
    # ========================================================

    point_names = [
        point["name"]
        for point in visible
    ]

    if any(point_names):

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="text",
                text=point_names,
                textposition="top center",
                name="Pattern Points",
                showlegend=False,
                hoverinfo="skip",
            )
        )


    x0 = x_values[0]
    x1 = x_values[-1]


    # ========================================================
    # ENTRY
    # ========================================================

    add_level(
        fig,
        x0,
        x1,
        pattern.get("entry"),
        "Entry / Neckline",
        "dash",
    )


    # ========================================================
    # TP1
    # ========================================================

    add_level(
        fig,
        x0,
        x1,
        pattern.get("tp1"),
        "TP1",
        "dot",
    )


    # ========================================================
    # TP2
    # ========================================================

    add_level(
        fig,
        x0,
        x1,
        pattern.get("tp2"),
        "TP2",
        "dot",
    )


    # ========================================================
    # SL
    # ========================================================

    add_level(
        fig,
        x0,
        x1,
        pattern.get("sl"),
        "SL",
        "dashdot",
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
# MARKET HEADER
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
        "Current Patterns",
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
# BASIC CONDITIONS
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

        atr_ok = pd.notna(
            atr_value
        )

    except Exception:

        atr_ok = False


    if atr_ok:

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
    "⭐ Best Current Pattern"
)


if best_pattern is None:

    st.info(
        "Pattern hadda ACTIVE ah lagama helin "
        "major swings-ka ugu dambeeya."
    )

else:

    name = best_pattern.get(
        "name",
        "Pattern",
    )

    direction = best_pattern.get(
        "direction",
        "WAIT",
    )

    quality = best_pattern.get(
        "quality",
        0,
    )

    status = best_pattern.get(
        "status",
        "FORMING",
    )

    action = action_for(
        best_pattern
    )

    b1, b2, b3, b4 = st.columns(4)


    with b1:

        st.metric(
            "Pattern",
            name,
        )


    with b2:

        st.metric(
            "Quality",
            f"{quality}/100",
        )


    with b3:

        st.metric(
            "Direction",
            direction,
        )


    with b4:

        st.metric(
            "Action",
            f"{direction_icon(action)} {action}",
        )


    st.write(
        f"**Reason:** "
        f"{best_pattern.get('reason', '—')}"
    )


    e1, e2, e3, e4, e5 = st.columns(5)


    with e1:

        st.metric(
            "Entry",
            fmt(
                best_pattern.get(
                    "entry"
                )
            ),
        )


    with e2:

        st.metric(
            "TP1",
            fmt(
                best_pattern.get(
                    "tp1"
                )
            ),
        )


    with e3:

        st.metric(
            "TP2",
            fmt(
                best_pattern.get(
                    "tp2"
                )
            ),
        )


    with e4:

        st.metric(
            "SL",
            fmt(
                best_pattern.get(
                    "sl"
                )
            ),
        )


    with e5:

        st.metric(
            "Status",
            status,
        )


    if status == "READY":

        if direction == "BUY":

            st.success(
                "🟢 BUY setup: pattern-ku wuxuu "
                "gaaray active entry zone. "
                "Strategy confirmation-ka dheeraadka ah "
                "weli waa in la hubiyaa."
            )

        elif direction == "SELL":

            st.error(
                "🔴 SELL setup: pattern-ku wuxuu "
                "gaaray active entry zone. "
                "Strategy confirmation-ka dheeraadka ah "
                "weli waa in la hubiyaa."
            )

    else:

        st.warning(
            "⏳ WAIT — pattern-ku weli waa FORMING; "
            "entry confirmation lama gaarin."
        )


# ============================================================
# RANKED CURRENT PATTERNS
# ============================================================

st.subheader(
    "📊 Current Patterns — Ranked by Quality"
)


if not patterns:

    st.info(
        "Ma jiro pattern current ah "
        "oo buuxiyay shuruudaha."
    )

else:

    for pattern in patterns:

        rank = pattern.get(
            "rank",
            "—",
        )

        name = pattern.get(
            "name",
            "Pattern",
        )

        direction = pattern.get(
            "direction",
            "WAIT",
        )

        quality = pattern.get(
            "quality",
            0,
        )

        status = pattern.get(
            "status",
            "FORMING",
        )

        action = action_for(
            pattern
        )


        with st.container(
            border=True
        ):

            p1, p2, p3, p4 = st.columns(
                [3, 1, 1, 1]
            )


            with p1:

                st.markdown(
                    f"### #{rank} "
                    f"{direction_icon(direction)} "
                    f"{name}"
                )


            with p2:

                st.metric(
                    "Quality
