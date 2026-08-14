import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# Import Backend Engine
try:
    from pattern_engine import run_full_analysis
except ImportError:
    from engine import run_full_analysis

# ==========================================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================================
st.set_page_config(
    page_title="TradingView Style Pattern Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Financial Market Pattern & Indicator Scanner")

# ==========================================================
# 2. TRADINGVIEW STYLE TOP NAVBAR (Original Timeframe Bar)
# ==========================================================
st.markdown("### 🎛️ TradingView Toolbar & Timeframe Bar")

# Row for Symbol Input and Quick Actions
col_sym, col_btn = st.columns([3, 1])
with col_sym:
    symbol = st.text_input("📍 Market Asset Symbol (Ticker):", "XAUUSD=X")
with col_btn:
    st.write("##")
    run_scan = st.button("🚀 Run Analysis", use_container_width=True)

# TRADINGVIEW HORIZONTAL TIMEFRAME BAR (ORIGINAL SETUP)
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio(
    "⏱️ Select Timeframe (TradingView Standard):",
    options=tf_options,
    index=6, # Default 1D
    horizontal=True
)

# EXPANDABLE CONTROLS TO FREE UP SCREEN SPACE (COLLAPSED BY DEFAULT)
with st.expander("⚙️ Chart Settings & Display Controls (Goo'aami Muuqaalka Chart-ka)"):
    c_zoom, c_height, c_theme = st.columns([2, 2, 2])
    with c_zoom:
        visible_candles = st.slider("🔍 Zoom Level (Shumacyada la arkayo):", min_value=20, max_value=300, value=60, step=10)
    with c_height:
        chart_height = st.slider("📐 Chart Height (Dhererka Chart-ka):", min_value=350, max_value=1000, value=550, step=50)
    with c_theme:
        chart_theme = st.selectbox(
            "🎨 Background Theme (Midabka Chart-ka):",
            options=["TradingView Dark", "Classic White", "Midnight Navy"],
            index=0
        )

# Automated YFinance Mapping for Max Candles without API Crash
tf_map = {
    "1m":  {"interval": "1m",  "period": "7d"},
    "5m":  {"interval": "5m",  "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"},
    "30m": {"interval": "30m", "period": "60d"},
    "1h":  {"interval": "1h",  "period": "2y"},
    "4h":  {"interval": "1h",  "period": "2y"},  # Fetches 1h data
    "1D":  {"interval": "1d",  "period": "max"},
    "1W":  {"interval": "1wk", "period": "max"},
    "1M":  {"interval": "1mo", "period": "max"}
}

current_setting = tf_map[selected_tf]

# ==========================================================
# 3. ANALYSIS & DATA FETCHING ENGINE
# ==========================================================
if run_scan:
    with st.spinner(f"Soo jiidashada xogta kandeellada ee {selected_tf} ({current_setting['period']})..."):
        try:
            df = yf.download(
                symbol, 
                period=current_setting["period"], 
                interval=current_setting["interval"]
            )
        except Exception as e:
            df = pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Handle 4h Resampling if selected
        if selected_tf == "4h" and not df.empty:
            df = df.resample('4h').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

        if df.empty or len(df) < 14:
            st.error(f"⚠️ Xogta kandeellada ee {symbol} ma buuxdo ama ma jirto time-frame-kan. Fadlan xaqiiji Ticker-ka ama baddal Timeframe-ka.")
        else:
            # Run Strict Backend Analysis Engine (100% Rules Preserved)
            result = run_full_analysis(df)
            df_res = result['df']
            total_candles = len(df_res)

            st.markdown("---")
            # ----------------------------------------------------
            # A. SIGNAL STATUS DISPLAY
            # ----------------------------------------------------
            st.markdown(f"### 🎯 Final Signal Status (Total Candles: `{total_candles}`)")
            
            signal = result['signal']
            if signal == "STRONG BUY":
                st.success(f"### 🟢 SIGNAL: STRONG BUY | Pattern: {result['pattern']}")
            elif signal == "STRONG SELL":
                st.error(f"### 🔴 SIGNAL: STRONG SELL | Pattern: {result['pattern']}")
            else:
                st.warning(f"### 🟡 STATUS: {signal} | Pattern: {result['pattern']}")

            st.caption(f"**Verification Detail:** {result['reason']}")

            # ----------------------------------------------------
            # B. ABSOLUTE TRADE EXECUTION LEVELS (ENTRY, SL, TP)
            # ----------------------------------------------------
            st.markdown("#### 📐 Absolute Trade Execution Levels")
            e1, e2, e3 = st.columns(3)
            
            if signal in ["STRONG BUY", "STRONG SELL"]:
                e1.metric("🎯 Entry Price", f"{result['entry']}")
                e2.metric("🛑 Stop Loss (SL)", f"{result['sl']}")
                e3.metric("🏆 Take Profit (TP - 1:2 RRR)", f"{result['tp']}")
            else:
                e1.metric("🎯 Entry Price", "Waiting...")
                e2.metric("🛑 Stop Loss (SL)", "N/A")
                e3.metric("🏆 Take Profit (TP)", "N/A")

            # ----------------------------------------------------
            # C. KEY INDICATOR METRICS
            # ----------------------------------------------------
            st.markdown("#### 📊 Current Indicator Values")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Close Price", f"{result['close']}")
            m2.metric("EMA 50", f"{result['ema50']}")
            m3.metric("EMA 200", f"{result['ema200']}")
            m4.metric("RSI (14)", f"{result['rsi']}")

            # ----------------------------------------------------
            # D. TRADINGVIEW STYLE INTERACTIVE PLOTLY CHART
            # ----------------------------------------------------
            st.markdown(f"### 📈 Interactive Chart ({symbol} - {selected_tf})")

            fig = go.Figure()

            # Candlestick Series with Dark Red / Dark Green Colors
            fig.add_trace(go.Candlestick(
                x=df_res.index,
                open=df_res['Open'],
                high=df_res['High'],
                low=df_res['Low'],
                close=df_res['Close'],
                name="Candlesticks",
                increasing=dict(line=dict(color='#089981', width=1), fillcolor='#089981'), # Dark Green
                decreasing=dict(line=dict(color='#F23645', width=1), fillcolor='#F23645')  # Dark Red
            ))

            # EMA 50 Line
            if 'EMA50' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA50'],
                    line=dict(color='#FF9800', width=1.5), name="EMA 50"
                ))

            # EMA 200 Line
            if 'EMA200' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA200'],
                    line=dict(color='#29B6F6', width=2), name="EMA 200"
                ))

            # Pivot Points (Structural Highs H & Lows L)
            if 'Pivot_H' in df_res.columns and 'Pivot_L' in df_res.columns:
                pivots_h = df_res.dropna(subset=['Pivot_H'])
                pivots_l = df_res.dropna(subset=['Pivot_L'])

                fig.add_trace(go.Scatter(
                    x=pivots_h.index, y=pivots_h['Pivot_H'],
                    mode='markers', marker=dict(symbol='triangle-down', size=10, color='#F23645'),
                    name="Pivot High (H)"
                ))

                fig.add_trace(go.Scatter(
                    x=pivots_l.index, y=pivots_l['Pivot_L'],
                    mode='markers', marker=dict(symbol='triangle-up', size=10, color='#089981'),
                    name="Pivot Low (L)"
                ))

                # Pattern Boundary Lines Overlay
                pivots_h_recent = pivots_h.tail(3)
                pivots_l_recent = pivots_l.tail(3)

                if len(pivots_h_recent) >= 2:
                    fig.add_trace(go.Scatter(
                        x=pivots_h_recent.index, y=pivots_h_recent['Pivot_H'],
                        mode='lines+markers', line=dict(color='#FFD700', width=2, dash='dashdot'),
                        name=f"Pattern Resistance ({result['pattern']})"
                    ))

                if len(pivots_l_recent) >= 2:
                    fig.add_trace(go.Scatter(
                        x=pivots_l_recent.index, y=pivots_l_recent['Pivot_L'],
                        mode='lines+markers', line=dict(color='#00FFFF', width=2, dash='dashdot'),
                        name=f"Pattern Support ({result['pattern']})"
                    ))

            # Order Lines (ENTRY, SL, TP) placed nicely at the right margin
            if signal in ["STRONG BUY", "STRONG SELL"]:
                orders = [
                    ("ENTRY", result['entry'], "#2962FF"),
                    ("STOP LOSS", result['sl'], "#F23645"),
                    ("TAKE PROFIT", result['tp'], "#089981")
                ]
                for label, val, col in orders:
                    fig.add_hline(
                        y=val,
                        line_dash="dash",
                        line_color=col,
                        line_width=1.5,
                        annotation_text=f" <b>{label}: {val}</b>",
                        annotation_position="top right",
                        annotation_font_size=11,
                        annotation_font_color=col
                    )

            # Zoom range calculation for clear candles
            x_min = df_res.index[-visible_candles] if total_candles > visible_candles else df_res.index[0]
            x_max = df_res.index[-1]

            # DYNAMIC BACKGROUND COLOR MAPPING
            bg_color_map = {
                "TradingView Dark": ("#131722", "#2A2E39", "plotly_dark"),
                "Classic White": ("#FFFFFF", "#E0E0E0", "plotly_white"),
                "Midnight Navy": ("#0B192C", "#1E3E62", "plotly_dark")
            }
            bg_bg, grid_col, plotly_tpl = bg_color_map[chart_theme]

            fig.update_layout(
                title=f"<b>{symbol}</b> ({selected_tf}) | Pattern: <b>{result['pattern']}</b>",
                template=plotly_tpl,
                height=chart_height,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=80, t=40, b=10),
                xaxis=dict(
                    range=[x_min, x_max],
                    type="date"
                ),
                yaxis=dict(
                    side="right",
                    gridcolor=grid_col,
                    zerolinecolor=grid_col
                ),
                plot_bgcolor=bg_bg,
                paper_bgcolor=bg_bg
            )

            st.plotly_chart(fig, use_container_width=True)
            
