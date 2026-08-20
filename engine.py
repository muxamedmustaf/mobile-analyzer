import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# ==========================================================
# SMART MARKET ANALYZER
# MODERN MOBILE-FIRST UI
# BACKEND LOGIC PRESERVED
# ==========================================================

try:
    from pattern_engine import run_full_analysis
except ImportError:
    from engine import run_full_analysis


# ==========================================================
# 1. PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Smart Market Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==========================================================
# 2. MODERN UI / CSS
# ==========================================================

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 88% 12%, rgba(0, 115, 255, .13), transparent 26%),
            radial-gradient(circle at 15% 45%, rgba(0, 255, 190, .06), transparent 28%),
            #020712;
        color: #f7f9ff;
    }

    .main .block-container {
        max-width: 1180px;
        padding: 28px 22px 50px;
    }

    /* Remove default Streamlit decoration */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* Top badges */
    .top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 14px;
        margin-bottom: 32px;
    }

    .brand-badge,
    .live-badge {
        border: 1px solid rgba(0, 255, 200, .25);
        background: rgba(7, 20, 35, .72);
        box-shadow: 0 0 25px rgba(0, 255, 200, .07);
        border-radius: 16px;
        padding: 12px 20px;
        font-weight: 700;
        letter-spacing: .3px;
    }

    .brand-badge {
        color: #19f4cf;
    }

    .live-badge {
        color: #16f1c2;
        border-radius: 30px;
    }

    /* Hero */
    .hero {
        position: relative;
        min-height: 300px;
        padding: 8px 0 28px;
        overflow: hidden;
    }

    .hero:after {
        content: "";
        position: absolute;
        right: -50px;
        top: 35px;
        width: 48%;
        height: 220px;
        opacity: .35;
        background:
            linear-gradient(145deg, transparent 42%, #08f0c0 43%, transparent 44%),
            linear-gradient(160deg, transparent 50%, #6347ff 51%, transparent 52%),
            linear-gradient(170deg, transparent 64%, #1e70ff 65%, transparent 66%);
        pointer-events: none;
    }

    .hero-title {
        position: relative;
        z-index: 2;
        max-width: 700px;
        font-size: clamp(42px, 6vw, 78px);
        line-height: .98;
        font-weight: 800;
        letter-spacing: -2.5px;
        margin: 0;
    }

    .hero-gradient {
        background: linear-gradient(90deg, #ffffff 0%, #ffffff 37%, #2e62ff 63%, #00e7c0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        position: relative;
        z-index: 2;
        color: #aeb9cb;
        font-size: 18px;
        line-height: 1.7;
        margin-top: 24px;
        max-width: 650px;
    }

    /* Cards */
    .modern-card {
        background: linear-gradient(145deg, rgba(11, 22, 40, .94), rgba(3, 11, 24, .92));
        border: 1px solid rgba(83, 110, 160, .23);
        border-radius: 26px;
        padding: 26px;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.035),
            0 18px 50px rgba(0,0,0,.22);
        margin-top: 18px;
    }

    .card-heading {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 18px;
    }

    .icon-circle {
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        background: linear-gradient(145deg, #1269db, #05377f);
        box-shadow: 0 0 25px rgba(24, 105, 255, .28);
    }

    .purple-icon {
        background: linear-gradient(145deg, #763cff, #3d11b6);
        box-shadow: 0 0 25px rgba(116, 48, 255, .25);
    }

    .card-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }

    .card-subtitle {
        font-size: 14px;
        color: #98a5b9;
        margin-top: 4px;
    }

    /* Streamlit inputs */
    div[data-testid="stTextInput"] label {
        display: none;
    }

    div[data-testid="stTextInput"] input {
        height: 62px;
        border-radius: 18px;
        background: #071222 !important;
        color: #ffffff !important;
        border: 1px solid #344dff !important;
        box-shadow:
            0 0 0 1px rgba(49, 86, 255, .15),
            0 0 24px rgba(52, 77, 255, .08);
        font-size: 20px !important;
        font-weight: 700;
        padding: 0 22px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #00e9c0 !important;
        box-shadow: 0 0 20px rgba(0, 233, 192, .15) !important;
    }

    /* Main action button */
    div[data-testid="stButton"] > button {
        width: 100%;
        min-height: 66px;
        border: 0;
        border-radius: 18px;
        color: #ffffff;
        font-size: 20px;
        font-weight: 800;
        background: linear-gradient(100deg, #3155ff 0%, #168cff 42%, #08d8b0 100%);
        box-shadow:
            0 12px 35px rgba(24, 104, 255, .25),
            inset 0 1px 0 rgba(255,255,255,.25);
        transition: transform .15s ease, filter .15s ease;
    }

    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.08);
        color: #ffffff;
    }

    div[data-testid="stButton"] > button:active {
        transform: translateY(0);
    }

    /* Timeframe radio */
    div[role="radiogroup"] {
        gap: 10px !important;
        flex-wrap: wrap !important;
    }

    div[role="radiogroup"] > label {
        min-width: 88px;
        min-height: 52px;
        justify-content: center;
        border: 1px solid #20304c !important;
        border-radius: 18px !important;
        background: #071222 !important;
        color: #e7edf7 !important;
        padding: 0 18px !important;
        transition: all .15s ease;
    }

    div[role="radiogroup"] > label:hover {
        border-color: #3e67ff !important;
    }

    div[role="radiogroup"] > label:has(input:checked) {
        border-color: #00e9c0 !important;
        background: rgba(0, 214, 173, .08) !important;
        box-shadow:
            0 0 22px rgba(0, 233, 192, .14),
            inset 0 0 20px rgba(0, 233, 192, .03);
        color: #12edc3 !important;
    }

    div[role="radiogroup"] > label p {
        font-weight: 700 !important;
        font-size: 16px !important;
    }

    /* Metrics */
    div[data-testid="metric-container"] {
        background: #071222;
        border: 1px solid rgba(80, 110, 160, .22);
        border-radius: 18px;
        padding: 15px;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        background: linear-gradient(145deg, rgba(11,22,40,.94), rgba(3,11,24,.92));
        border: 1px solid rgba(83,110,160,.23);
        border-radius: 24px;
        margin-top: 18px;
    }

    div[data-testid="stExpander"] summary {
        color: #ffffff;
        font-weight: 700;
    }

    /* Status cards */
    .status-card {
        border-radius: 22px;
        padding: 22px;
        margin: 18px 0;
        border: 1px solid rgba(255,255,255,.08);
    }

    .status-buy {
        background: linear-gradient(135deg, rgba(0, 220, 160, .14), rgba(2, 25, 28, .85));
        border-color: rgba(0, 239, 190, .35);
    }

    .status-sell {
        background: linear-gradient(135deg, rgba(242, 54, 69, .14), rgba(28, 7, 13, .85));
        border-color: rgba(242, 54, 69, .35);
    }

    .status-wait {
        background: linear-gradient(135deg, rgba(255, 185, 0, .11), rgba(25, 19, 5, .85));
        border-color: rgba(255, 185, 0, .28);
    }

    .status-main {
        font-size: 28px;
        font-weight: 800;
    }

    .small-muted {
        color: #8f9db2;
        font-size: 13px;
    }

    /* Chart wrapper */
    .section-title {
        font-size: 23px;
        font-weight: 800;
        margin-top: 30px;
        margin-bottom: 10px;
    }

    @media (max-width: 700px) {
        .main .block-container {
            padding: 18px 12px 35px;
        }

        .top-row {
            margin-bottom: 22px;
        }

        .brand-badge,
        .live-badge {
            padding: 9px 12px;
            font-size: 12px;
        }

        .hero {
            min-height: 255px;
        }

        .hero-title {
            font-size: 43px;
            letter-spacing: -1.8px;
        }

        .hero-subtitle {
            font-size: 15px;
        }

        .modern-card {
            padding: 20px 16px;
            border-radius: 22px;
        }

        div[role="radiogroup"] > label {
            min-width: 70px;
            padding: 0 12px !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================================
# 3. HEADER
# ==========================================================

st.markdown(
    """
<div class="top-row">
    <div class="brand-badge">📈 SMART MARKET ANALYZER</div>
    <div class="live-badge">⚡ Real-time Analysis</div>
</div>

<div class="hero">
    <h1 class="hero-title">
        Financial Market<br>
        Pattern &<br>
        <span class="hero-gradient">Indicator Scanner</span>
    </h1>
    <div class="hero-subtitle">
        Advanced pattern detection • Powerful indicators<br>
        Smart insights • Better decisions
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ==========================================================
# 4. MARKET ASSET CARD
# ==========================================================

st.markdown(
    """
<div class="modern-card">
    <div class="card-heading">
        <div class="icon-circle">🌐</div>
        <div>
            <div class="card-title">Market Asset Symbol (Ticker)</div>
            <div class="card-subtitle">Enter the symbol you want to analyze</div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

symbol = st.text_input(
    "Market Asset Symbol",
    value="XAUUSD=X",
    placeholder="e.g. XAUUSD=X, EURUSD=X, BTC-USD",
)

st.markdown(
    '<div class="small-muted" style="margin:6px 4px 12px;">Yahoo Finance ticker • Example: XAUUSD=X</div>',
    unsafe_allow_html=True,
)

run_scan = st.button("🚀  Run Analysis", use_container_width=True)


# ==========================================================
# 5. TIMEFRAME CARD
# ==========================================================

st.markdown(
    """
<div class="modern-card">
    <div class="card-heading">
        <div class="icon-circle">◷</div>
        <div>
            <div class="card-title">Select Timeframe (TradingView Standard)</div>
            <div class="card-subtitle">Choose your preferred chart timeframe</div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]

selected_tf = st.radio(
    "Select Timeframe",
    options=tf_options,
    index=5,
    horizontal=True,
    label_visibility="collapsed",
)


# ==========================================================
# 6. CHART SETTINGS
# ==========================================================

with st.expander("⚙️  Chart Settings & Display Controls"):
    st.markdown(
        '<div class="small-muted">Customize your chart view and analysis preferences.</div>',
        unsafe_allow_html=True,
    )

    c_zoom, c_height, c_theme = st.columns(3)

    with c_zoom:
        visible_candles = st.slider(
            "🔍 Candles Visible",
            min_value=20,
            max_value=300,
            value=60,
            step=10,
        )

    with c_height:
        chart_height = st.slider(
            "📐 Chart Height",
            min_value=350,
            max_value=1000,
            value=550,
            step=50,
        )

    with c_theme:
        chart_theme = st.selectbox(
            "🎨 Chart Theme",
            options=["Classic White", "TradingView Dark", "Midnight Navy"],
            index=0,
        )


# ==========================================================
# 7. YFINANCE TIMEFRAME MAPPING
# ==========================================================

tf_map = {
    "1m": {"interval": "1m", "period": "7d"},
    "5m": {"interval": "5m", "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"},
    "30m": {"interval": "30m", "period": "60d"},
    "1h": {"interval": "1h", "period": "2y"},
    "4h": {"interval": "1h", "period": "2y"},
    "1D": {"interval": "1d", "period": "max"},
    "1W": {"interval": "1wk", "period": "max"},
    "1M": {"interval": "1mo", "period": "max"},
}

current_setting = tf_map[selected_tf]


# ==========================================================
# 8. ANALYSIS
# ==========================================================

if run_scan:
    with st.spinner(
        f"Loading market data for {symbol} • {selected_tf} • {current_setting['period']}..."
    ):
        try:
            df = yf.download(
                symbol,
                period=current_setting["period"],
                interval=current_setting["interval"],
                progress=False,
                auto_adjust=False,
            )
        except Exception:
            df = pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 4H resampling preserved
    if selected_tf == "4h" and not df.empty:
        df = df.resample("4h").agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        ).dropna()

    if df.empty or len(df) < 14:
        st.error(
            f"⚠️ Data for {symbol} is unavailable or insufficient for this timeframe. "
            "Please verify the ticker or choose another timeframe."
        )

    else:
        # ======================================================
        # BACKEND ENGINE — PRESERVED
        # ======================================================

        result = run_full_analysis(df)

        df_res = result["df"]
        total_candles = len(df_res)

        signal = result["signal"]
        pattern = result["pattern"]

        # ======================================================
        # SIGNAL CARD
        # ======================================================

        if signal == "STRONG BUY":
            status_class = "status-buy"
            status_icon = "🟢"
        elif signal == "STRONG SELL":
            status_class = "status-sell"
            status_icon = "🔴"
        else:
            status_class = "status-wait"
            status_icon = "🟡"

        st.markdown(
            f"""
<div class="status-card {status_class}">
    <div class="small-muted">FINAL MARKET SIGNAL • {total_candles} CANDLES</div>
    <div class="status-main">{status_icon} {signal}</div>
    <div style="margin-top:7px;color:#b9c5d8;">
        Pattern: <b>{pattern}</b>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.caption(f"Verification Detail: {result['reason']}")

        # ======================================================
        # EXECUTION LEVELS
        # ======================================================

        st.markdown(
            '<div class="section-title">📐 Absolute Trade Execution Levels</div>',
            unsafe_allow_html=True,
        )

        e1, e2, e3 = st.columns(3)

        if signal in ["STRONG BUY", "STRONG SELL"]:
            e1.metric("🎯 Entry Price", f"{result['entry']}")
            e2.metric("🛑 Stop Loss", f"{result['sl']}")
            e3.metric("🏆 Take Profit", f"{result['tp']}")
        else:
            e1.metric("🎯 Entry Price", "Waiting...")
            e2.metric("🛑 Stop Loss", "N/A")
            e3.metric("🏆 Take Profit", "N/A")

        # ======================================================
        # INDICATORS
        # ======================================================

        st.markdown(
            '<div class="section-title">📊 Current Indicator Values</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Close Price", f"{result['close']}")
        m2.metric("EMA 50", f"{result['ema50']}")
        m3.metric("EMA 200", f"{result['ema200']}")
        m4.metric("RSI (14)", f"{result['rsi']}")

        # ======================================================
        # CHART
        # ======================================================

        st.markdown(
            f'<div class="section-title">📈 Interactive Chart • {symbol} • {selected_tf}</div>',
            unsafe_allow_html=True,
        )

        fig = go.Figure()

        # Candlesticks
        fig.add_trace(
            go.Candlestick(
                x=df_res.index,
                open=df_res["Open"],
                high=df_res["High"],
                low=df_res["Low"],
                close=df_res["Close"],
                name="Candlesticks",
                increasing=dict(
                    line=dict(color="#089981", width=1),
                    fillcolor="#089981",
                ),
                decreasing=dict(
                    line=dict(color="#F23645", width=1),
                    fillcolor="#F23645",
                ),
            )
        )

        # EMA 50
        if "EMA50" in df_res.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_res.index,
                    y=df_res["EMA50"],
                    line=dict(color="#FF9800", width=1.5),
                    name="EMA 50",
                )
            )

        # EMA 200
        if "EMA200" in df_res.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_res.index,
                    y=df_res["EMA200"],
                    line=dict(color="#29B6F6", width=2),
                    name="EMA 200",
                )
            )

        # Pivot points
        if "Pivot_H" in df_res.columns and "Pivot_L" in df_res.columns:
            pivots_h = df_res.dropna(subset=["Pivot_H"])
            pivots_l = df_res.dropna(subset=["Pivot_L"])

            fig.add_trace(
                go.Scatter(
                    x=pivots_h.index,
                    y=pivots_h["Pivot_H"],
                    mode="markers",
                    marker=dict(
                        symbol="triangle-down",
                        size=10,
                        color="#F23645",
                    ),
                    name="Pivot High (H)",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=pivots_l.index,
                    y=pivots_l["Pivot_L"],
                    mode="markers",
                    marker=dict(
                        symbol="triangle-up",
                        size=10,
                        color="#089981",
                    ),
                    name="Pivot Low (L)",
                )
            )

            # Recent structural boundaries
            pivots_h_recent = pivots_h.tail(3)
            pivots_l_recent = pivots_l.tail(3)

            if len(pivots_h_recent) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=pivots_h_recent.index,
                        y=pivots_h_recent["Pivot_H"],
                        mode="lines+markers",
                        line=dict(
                            color="#FFD700",
                            width=2,
                            dash="dashdot",
                        ),
                        name=f"Pattern Resistance ({pattern})",
                    )
                )

            if len(pivots_l_recent) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=pivots_l_recent.index,
                        y=pivots_l_recent["Pivot_L"],
                        mode="lines+markers",
                        line=dict(
                            color="#00FFFF",
                            width=2,
                            dash="dashdot",
                        ),
                        name=f"Pattern Support ({pattern})",
                    )
                )

        # ======================================================
        # DETECTED PATTERN GEOMETRY + NECKLINE
        # Draw the found pattern only inside its own pivot range.
        # Backend logic is untouched.
        # ======================================================
        pattern_start = result.get("pattern_start")
        pattern_end = result.get("pattern_end")

        if pattern and pattern != "NO PATTERN DETECTED":
            ph = df_res["Pivot_H"].dropna() if "Pivot_H" in df_res.columns else pd.Series(dtype=float)
            pl = df_res["Pivot_L"].dropna() if "Pivot_L" in df_res.columns else pd.Series(dtype=float)

            # Use detected pattern range when available.
            try:
                if pattern_start in df_res.index and pattern_end in df_res.index:
                    ph = ph.loc[pattern_start:pattern_end]
                    pl = pl.loc[pattern_start:pattern_end]
            except Exception:
                pass

            # Draw the actual detected swing skeleton.
            swing_points = [(idx, val, "H") for idx, val in ph.items()]
            swing_points += [(idx, val, "L") for idx, val in pl.items()]
            swing_points.sort(key=lambda x: x[0])

            if swing_points:
                fig.add_trace(
                    go.Scatter(
                        x=[p[0] for p in swing_points],
                        y=[p[1] for p in swing_points],
                        mode="lines+markers",
                        line=dict(color="#3155FF", width=3),
                        marker=dict(size=8, color="#3155FF"),
                        name=f"Detected {pattern}",
                        hovertemplate="%{y}<extra>"+str(pattern)+"</extra>",
                    )
                )

            # Neckline construction from the pivots of the found pattern.
            # Double/Triple Top: support through intervening lows.
            # Double/Triple Bottom: resistance through intervening highs.
            # H&S: neckline through the two troughs.
            # Inverse H&S: neckline through the two peaks.
            neckline_x = []
            neckline_y = []

            p_lower = str(pattern).lower()

            if "head and shoulders" in p_lower and "inverse" not in p_lower:
                pts = list(pl.items())
                if len(pts) >= 2:
                    neckline_x = [pts[-2][0], pts[-1][0]]
                    neckline_y = [pts[-2][1], pts[-1][1]]

            elif "inverse head and shoulders" in p_lower:
                pts = list(ph.items())
                if len(pts) >= 2:
                    neckline_x = [pts[-2][0], pts[-1][0]]
                    neckline_y = [pts[-2][1], pts[-1][1]]

            elif "double top" in p_lower or "triple top" in p_lower:
                pts = list(pl.items())
                if len(pts) >= 1:
                    # Use the lowest/intervening support level in the detected range.
                    idx, val = min(pts, key=lambda x: x[1])
                    end_x = pattern_end if pattern_end in df_res.index else df_res.index[-1]
                    neckline_x = [idx, end_x]
                    neckline_y = [val, val]

            elif "double bottom" in p_lower or "triple bottom" in p_lower:
                pts = list(ph.items())
                if len(pts) >= 1:
                    idx, val = max(pts, key=lambda x: x[1])
                    end_x = pattern_end if pattern_end in df_res.index else df_res.index[-1]
                    neckline_x = [idx, end_x]
                    neckline_y = [val, val]

            elif "ascending triangle" in p_lower:
                pts = list(ph.items())
                if len(pts) >= 2:
                    neckline_x = [pts[-2][0], pts[-1][0]]
                    neckline_y = [pts[-2][1], pts[-1][1]]

            elif "descending triangle" in p_lower:
                pts = list(pl.items())
                if len(pts) >= 2:
                    neckline_x = [pts[-2][0], pts[-1][0]]
                    neckline_y = [pts[-2][1], pts[-1][1]]

            elif "wedge" in p_lower:
                # Wedges are better represented by their two converging boundaries.
                if len(ph) >= 2 and len(pl) >= 2:
                    hp = list(ph.items())[-2:]
                    lp = list(pl.items())[-2:]
                    fig.add_trace(
                        go.Scatter(
                            x=[hp[0][0], hp[1][0]],
                            y=[hp[0][1], hp[1][1]],
                            mode="lines",
                            line=dict(color="#8B5CF6", width=2.5),
                            name="Pattern Upper Boundary",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[lp[0][0], lp[1][0]],
                            y=[lp[0][1], lp[1][1]],
                            mode="lines",
                            line=dict(color="#8B5CF6", width=2.5),
                            name="Pattern Lower Boundary",
                        )
                    )

            if neckline_x and neckline_y:
                fig.add_trace(
                    go.Scatter(
                        x=neckline_x,
                        y=neckline_y,
                        mode="lines",
                        line=dict(color="#E0A800", width=3, dash="dash"),
                        name="Neckline",
                        hovertemplate="Neckline: %{y:.5f}<extra></extra>",
                    )
                )

        # Entry / SL / TP
        if signal in ["STRONG BUY", "STRONG SELL"]:
            orders = [
                ("ENTRY", result["entry"], "#2962FF"),
                ("STOP LOSS", result["sl"], "#F23645"),
                ("TAKE PROFIT", result["tp"], "#089981"),
            ]

            for label, val, col in orders:
                fig.add_hline(
                    y=val,
                    line_dash="dash",
                    line_color=col,
                    line_width=1.5,
                    annotation_text=f"<b>{label}: {val}</b>",
                    annotation_position="top right",
                    annotation_font_size=11,
                    annotation_font_color=col,
                )

        # ======================================================
        # CHART VIEW
        # ======================================================

        x_min = (
            df_res.index[-visible_candles]
            if total_candles > visible_candles
            else df_res.index[0]
        )
        x_max = df_res.index[-1]

        bg_color_map = {
            "TradingView Dark": ("#131722", "#2A2E39", "plotly_dark"),
            "Classic White": ("#FFFFFF", "#E0E0E0", "plotly_white"),
            "Midnight Navy": ("#0B192C", "#1E3E62", "plotly_dark"),
        }

        bg_bg, grid_col, plotly_tpl = bg_color_map[chart_theme]

        fig.update_layout(
            title=f"<b>{symbol}</b> ({selected_tf}) | Pattern: <b>{pattern}</b>",
            template=plotly_tpl,
            height=chart_height,
            autosize=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=40, t=72, b=28),
            showlegend=False,
            xaxis=dict(
                range=[x_min, x_max],
                type="date",
                showgrid=True,
                gridcolor=grid_col,
            ),
            yaxis=dict(
                side="right",
                gridcolor=grid_col,
                zerolinecolor=grid_col,
            ),
            plot_bgcolor=bg_bg,
            paper_bgcolor=bg_bg,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": True,
            },
        )

        # ======================================================
        # LEGEND
        # ======================================================

        with st.expander("📌 Chart Legend / Indicators"):
            st.markdown(
                """
- 🟢 **Green Candles** — Bullish price movement
- 🔴 **Red Candles** — Bearish price movement
- 🟧 **Orange Line** — EMA 50
- 🟦 **Light Blue Line** — EMA 200
- 🔻 **Red Triangle** — Pivot High / Structural Resistance
- 🔺 **Green Triangle** — Pivot Low / Structural Support
- 🟨 **Gold Dash-Dot** — Pattern Resistance
- 🟦 **Cyan Dash-Dot** — Pattern Support
- 🔵 **Blue Line** — Entry
- 🛑 **Red Line** — Stop Loss
- 🟢 **Green Line** — Take Profit
"""
            )
