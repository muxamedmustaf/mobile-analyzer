import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# ==========================================================
# SMART MARKET ANALYZER
# CLEAR LIGHT MODE UI (MATCHING IMAGE DESIGN)
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
# 2. CLEAR LIGHT MODE UI / CUSTOM CSS
# ==========================================================

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Main background - Crisp White / Light Tone */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    .main .block-container {
        max-width: 1100px;
        padding: 20px 16px 40px;
    }

    /* Remove default Streamlit header & footer */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* Top Display Bar (Price & RSI) */
    .top-price-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }

    .big-price {
        font-size: 42px;
        font-weight: 700;
        color: #0044CC;
        line-height: 1.1;
        letter-spacing: -1px;
    }

    .rsi-title {
        font-size: 14px;
        color: #475569;
        margin-top: 10px;
        font-weight: 600;
    }

    .rsi-value {
        font-size: 36px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 12px;
    }

    .top-actions {
        display: flex;
        align-items: center;
        gap: 16px;
        color: #2563EB;
        font-weight: 600;
        font-size: 15px;
    }

    .chart-badge-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 22px;
        font-weight: 800;
        color: #0044CC;
        margin-bottom: 16px;
    }

    /* Modern Light Cards */
    .modern-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
        margin-top: 14px;
        margin-bottom: 14px;
    }

    .card-heading {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .icon-circle {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        background: #EFF6FF;
        color: #2563EB;
    }

    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #0F172A;
    }

    .card-subtitle {
        font-size: 13px;
        color: #64748B;
    }

    /* Input Fields */
    div[data-testid="stTextInput"] label {
        display: none;
    }

    div[data-testid="stTextInput"] input {
        height: 54px;
        border-radius: 14px;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        font-size: 18px !important;
        font-weight: 600;
        padding: 0 18px;
        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #2563EB !important;
    }

    /* Primary Button */
    div[data-testid="stButton"] > button {
        width: 100%;
        min-height: 56px;
        border: 0;
        border-radius: 14px;
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 700;
        background: #2563EB;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        transition: all 0.2s ease;
    }

    div[data-testid="stButton"] > button:hover {
        background: #1D4ED8;
        color: #FFFFFF;
    }

    /* Radio Group (Timeframes) */
    div[role="radiogroup"] {
        gap: 8px !important;
        flex-wrap: wrap !important;
    }

    div[role="radiogroup"] > label {
        min-width: 64px;
        min-height: 42px;
        justify-content: center;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        background: #F8FAFC !important;
        color: #334155 !important;
        padding: 0 14px !important;
    }

    div[role="radiogroup"] > label:has(input:checked) {
        border-color: #2563EB !important;
        background: #EFF6FF !important;
        color: #2563EB !important;
    }

    div[role="radiogroup"] > label p {
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    /* Metrics */
    div[data-testid="metric-container"] {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 12px 16px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }

    div[data-testid="stExpander"] summary {
        color: #2563EB !important;
        font-weight: 700 !important;
    }

    /* Status Cards */
    .status-card {
        border-radius: 16px;
        padding: 18px 22px;
        margin: 16px 0;
        border: 1px solid #E2E8F0;
    }

    .status-buy {
        background: #F0FDF4;
        border-color: #86EFAC;
        color: #166534;
    }

    .status-sell {
        background: #FEF2F2;
        border-color: #FECACA;
        color: #991B1B;
    }

    .status-wait {
        background: #FFFBEB;
        border-color: #FDE68A;
        color: #92400E;
    }

    .status-main {
        font-size: 26px;
        font-weight: 800;
    }

    .small-muted {
        color: #64748B;
        font-size: 13px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
        margin-top: 24px;
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================================
# 3. TOP PRICE & HEADER SECTION (LIKE ATTACHED IMAGE)
# ==========================================================

st.markdown(
    """
<div class="top-price-header">
    <div>
        <div class="big-price">0.8175</div>
    </div>
    <div class="top-actions">
        <span>Share</span>
        <span>☆</span>
        <span>✏️</span>
        <span>⛶</span>
    </div>
</div>
<div class="rsi-title">RSI (14)</div>
<div class="rsi-value">71.63</div>
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
    value="NZDCAD=X",
    placeholder="e.g. NZDCAD=X, XAUUSD=X, EURUSD=X, BTC-USD",
)

st.markdown(
    '<div class="small-muted" style="margin:-6px 4px 12px;">Yahoo Finance ticker • Example: NZDCAD=X</div>',
    unsafe_allow_html=True,
)

run_scan = st.button("🚀 Run Analysis", use_container_width=True)


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

with st.expander("⚙️ Chart Settings & Display Controls"):
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
            value=520,
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

        # Dynamic Header Update for current symbol
        st.markdown(
            f"""
        <div class="chart-badge-title">
            📊 Chart • {symbol} • {selected_tf}
        </div>
        """,
            unsafe_allow_html=True,
        )

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
    <div style="margin-top:4px;font-weight:600;">
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
                    line=dict(color="#089981", width=1.2),
                    fillcolor="#089981",
                ),
                decreasing=dict(
                    line=dict(color="#F23645", width=1.2),
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
                    line=dict(color="#2563EB", width=2),
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

            # Structural boundaries
            pivots_h_recent = pivots_h.tail(3)
            pivots_l_recent = pivots_l.tail(3)

            if len(pivots_h_recent) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=pivots_h_recent.index,
                        y=pivots_h_recent["Pivot_H"],
                        mode="lines+markers",
                        line=dict(
                            color="#D97706",
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
                            color="#0284C7",
                            width=2,
                            dash="dashdot",
                        ),
                        name=f"Pattern Support ({pattern})",
                    )
                )

        # Entry / SL / TP Lines
        if signal in ["STRONG BUY", "STRONG SELL"]:
            orders = [
                ("ENTRY", result["entry"], "#2563EB"),
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
        # CHART VIEW & LIGHT STYLING
        # ======================================================

        x_min = (
            df_res.index[-visible_candles]
            if total_candles > visible_candles
            else df_res.index[0]
        )
        x_max = df_res.index[-1]

        bg_color_map = {
            "Classic White": ("#FFFFFF", "#E2E8F0", "plotly_white"),
            "TradingView Dark": ("#131722", "#2A2E39", "plotly_dark"),
            "Midnight Navy": ("#0B192C", "#1E3E62", "plotly_dark"),
        }

        bg_bg, grid_col, plotly_tpl = bg_color_map[chart_theme]

        fig.update_layout(
            title=dict(
                text=f"<b>{symbol} ({selected_tf}) | Pattern: {pattern}</b>",
                font=dict(color="#0F172A", size=15),
            ),
            template=plotly_tpl,
            height=chart_height,
            autosize=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=50, t=45, b=20),
            showlegend=False,
            xaxis=dict(
                range=[x_min, x_max],
                type="date",
                showgrid=True,
                gridcolor=grid_col,
                tickfont=dict(color="#475569"),
            ),
            yaxis=dict(
                side="right",
                gridcolor=grid_col,
                zerolinecolor=grid_col,
                tickfont=dict(color="#475569"),
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
- 🟦 **Blue Line** — EMA 200
- 🔻 **Red Triangle** — Pivot High / Structural Resistance
- 🔺 **Green Triangle** — Pivot Low / Structural Support
- 🟧 **Orange Dash-Dot** — Pattern Resistance
- 🟦 **Cyan Dash-Dot** — Pattern Support
- 🔵 **Blue Line** — Entry
- 🛑 **Red Line** — Stop Loss
- 🟢 **Green Line** — Take Profit
"""
            )
