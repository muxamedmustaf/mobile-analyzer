import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# Soo jiidashada matoorka backend-ka ee engine.py
from engine import run_full_analysis

# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="SMC & Indicator Pattern Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📊 SMC & Technical Indicator Pattern Scanner")
st.write("Dashboard-kan wuxuu si toos ah u maamulaa **engine.py** si uu 100% u dammaanad qaado shuruudaha **15-ka Pattern, EMA 50/200, RSI (30-70), iyo Breakout Confirmation**.")

# ==========================================================
# 2. SIDEBAR PARAMETERS
# ==========================================================
st.sidebar.header("⚙️ Market Settings")
symbol = st.sidebar.text_input("Asset Ticker (e.g. XAUUSD=X, BTC-USD):", "XAUUSD=X")
timeframe = st.sidebar.selectbox("Timeframe Horizon:", ["4h", "1d"], index=1)
period = st.sidebar.selectbox("Data Lookback Period:", ["60d", "100d", "200d"], index=1)

st.sidebar.markdown("---")
st.sidebar.info("""
**100% Strict Rules Enforced:**
- 15 Valid Chart Patterns
- Price > EMA200 & EMA50 > EMA200 (BUY)
- Price < EMA200 & EMA50 < EMA200 (SELL)
- RSI strictly between 30 and 70
- Structural Level Breakout / Breakdown
""")

# ==========================================================
# 3. MAIN ANALYSIS TRIGGER
# ==========================================================
if st.sidebar.button("🚀 Run Strict Market Scan"):
    with st.spinner("Soo jiidashada xogta suuqa & Siftaynta Shuruudaha..."):
        # Fetch Data via yfinance
        df = yf.download(symbol, period=period, interval=timeframe)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty:
            st.error("⚠️ Xogta ma soo doonin! Fadlan xaqiiji Ticker-ka aad gelisay.")
        else:
            # U yeerida Backend Engine-ka
            result = run_full_analysis(df)
            df_res = result['df']

            # ----------------------------------------------------
            # A. SIGNAL STATUS DISPLAY
            # ----------------------------------------------------
            st.markdown("### 🎯 Final Signal & Market Status")
            
            signal = result['signal']
            if signal == "STRONG BUY":
                st.success(f"### 🟢 SIGNAL: STRONG BUY | Pattern: {result['pattern']}")
            elif signal == "STRONG SELL":
                st.error(f"### 🔴 SIGNAL: STRONG SELL | Pattern: {result['pattern']}")
            else:
                st.warning(f"### 🟡 STATUS: {signal} | Pattern: {result['pattern']}")

            st.caption(f"**Verification Detail:** {result['reason']}")

            # ----------------------------------------------------
            # B. TRADE EXECUTION LEVELS (ENTRY, SL, TP)
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
            # D. INTERACTIVE PLOTLY CHART
            # ----------------------------------------------------
            st.markdown("### 📈 Price Chart, Indicators & Structural Levels")

            fig = go.Figure()

            # Candlesticks
            fig.add_trace(go.Candlestick(
                x=df_res.index,
                open=df_res['Open'],
                high=df_res['High'],
                low=df_res['Low'],
                close=df_res['Close'],
                name="Candlesticks"
            ))

            # EMA 50 Line
            fig.add_trace(go.Scatter(
                x=df_res.index, y=df_res['EMA50'],
                line=dict(color='orange', width=1.5), name="EMA 50"
            ))

            # EMA 200 Line
            fig.add_trace(go.Scatter(
                x=df_res.index, y=df_res['EMA200'],
                line=dict(color='deepskyblue', width=2), name="EMA 200"
            ))

            # Pivot Points (Structural Highs H & Lows L)
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
                title=f"{symbol} Chart ({timeframe}) - EMA 50/200, Structural Pivots & RSI Validation",
                xaxis_title="Time",
                yaxis_title="Price",
                template="plotly_dark",
                height=650,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
            
