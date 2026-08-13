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
# 2. TRADINGVIEW STYLE TOP NAVBAR (Asset & Timeframes)
# ==========================================================
st.markdown("### 🎛️ TradingView Toolbar & Timeframe Bar")

# Row for Symbol Input and Quick Actions
col_sym, col_btn = st.columns([3, 1])
with col_sym:
    symbol = st.text_input("📍 Market Asset Symbol (Ticker):", "XAUUSD=X")
with col_btn:
    st.write("##")
    run_scan = st.button("🚀 Run Analysis", use_container_width=True)

# TRADINGVIEW HORIZONTAL TIMEFRAME BAR
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio(
    "⏱️ Select Timeframe (TradingView Standard):",
    options=tf_options,
    index=6, # Default 1D
    horizontal=True
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

            # Candlestick Series
            fig.add_trace(go.Candlestick(
                x=df_res.index,
                open=df_res['Open'],
                high=df_res['High'],
                low=df_res['Low'],
                close=df_res['Close'],
                name="Candlesticks"
            ))

            # EMA 50 Line
            if 'EMA50' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA50'],
                    line=dict(color='orange', width=1.5), name="EMA 50"
                ))

            # EMA 200 Line
            if 'EMA200' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA200'],
                    line=dict(color='deepskyblue', width=2), name="EMA 200"
                ))

            # Pivot Points (Structural Highs H & Lows L)
            if 'Pivot_H' in df_res.columns and 'Pivot_L' in df_res.columns:
                pivots_h = df_res.dropna(subset=['Pivot_H'])
                pivots_l = df_res.dropna(subset=['Pivot_L'])

                fig.add_trace(go.Scatter(
                    x=pivots_h.index, y=pivots_h['Pivot_H'],
                    mode='markers', marker=dict(symbol='triangle-down', size=11, color='red'),
                    name="Structural Resistance (H)"
                ))

                fig.add_trace(go.Scatter(
                    x=pivots_l.index, y=pivots_l['Pivot_L'],
                    mode='markers', marker=dict(symbol='triangle-up', size=11, color='green'),
                    name="Structural Support (L)"
                ))

            fig.update_layout(
                title=f"{symbol} - Chart Timeframe: {selected_tf} | Loaded Candles: {total_candles}",
                xaxis_title="Time / Date",
                yaxis_title="Price",
                template="plotly_dark",
                height=650,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
        
