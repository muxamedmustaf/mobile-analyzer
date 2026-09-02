import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from engine import run_full_analysis

try:
    from ffff import get_symbols_from_sheet
except ImportError:
    st.error("⚠️ The file ffff.py was not found alongside app.py")

st.set_page_config(page_title="Smart Market Analyzer", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# Hidden Spreadsheet Constants
SHEET_ID = "1TXvF6RhSgfJ631UpnWB38Ww1OMvZVx7VonDB_y1pO3s"
DEFAULT_SHEET_NAME = "GOLD"
DEFAULT_COL_NAME = "TOKENS"

# Session state initialization for retaining dropdown selection
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = "NZDCAD=X"
if "status_summary" not in st.session_state:
    st.session_state.status_summary = "⚡ Live Scan • Ready"
if "scanned_signals" not in st.session_state:
    st.session_state.scanned_signals = []

st.markdown(f'''
<div style="display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 24px;">
    <div style="border: 1px solid #DADCE0; background: #FFFFFF; border-radius: 16px; padding: 10px 18px; font-weight: 700; color: #0B57D0;">📈 {st.session_state.current_symbol}</div>
    <div style="border: 1px solid #DADCE0; background: #FFFFFF; border-radius: 30px; padding: 10px 18px; font-weight: 700; color: #0B57D0;">{st.session_state.status_summary}</div>
</div>
''', unsafe_allow_html=True)

scan_mode = st.radio("Scan Method:", ["Single Asset", "Google Sheet (Scan List for Completed Setups)"], horizontal=True)

symbols_to_scan = []

if scan_mode == "Single Asset":
    symbol = st.text_input("Market Asset Symbol", value="NZDCAD=X")
    st.session_state.current_symbol = symbol
    symbols_to_scan = [symbol]
else:
    fetched_symbols, err = get_symbols_from_sheet(SHEET_ID, DEFAULT_SHEET_NAME, DEFAULT_COL_NAME)
    if err:
        st.error(err)
    else:
        symbols_to_scan = fetched_symbols
        st.success(f"Successfully loaded {len(symbols_to_scan)} assets from Google Sheet!")

tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio("Select Timeframe", options=tf_options, index=6, horizontal=True)

tf_map = {
    "1m": {"interval": "1m", "period": "7d"}, "5m": {"interval": "5m", "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"}, "30m": {"interval": "30m", "period": "60d"},
    "1h": {"interval": "1h", "period": "2y"}, "4h": {"interval": "1h", "period": "2y"},
    "1D": {"interval": "1d", "period": "max"}, "1W": {"interval": "1wk", "period": "max"},
    "1M": {"interval": "1mo", "period": "max"},
}
current_setting = tf_map[selected_tf]

run_scan = st.button("🚀 Start Scan & Analysis", use_container_width=True)

if run_scan and symbols_to_scan:
    valid_signals = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, sym in enumerate(symbols_to_scan):
        status_text.text(f"Scanning asset ({idx+1}/{len(symbols_to_scan)}): {sym}...")
        progress_bar.progress((idx + 1) / len(symbols_to_scan))

        try:
            df = yf.download(sym, period=current_setting["period"], interval=current_setting["interval"], progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if selected_tf == "4h" and not df.empty:
                df = df.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()

            if not df.empty and len(df) >= 20:
                result = run_full_analysis(df)
                signal = result["signal"]
                pattern = result["pattern"]

                if signal in ["STRONG BUY", "STRONG SELL"] or scan_mode == "Single Asset":
                    valid_signals.append({
                        "symbol": sym,
                        "signal": signal,
                        "pattern": pattern,
                        "result": result
                    })
        except Exception:
            continue

    status_text.empty()
    progress_bar.empty()
    st.session_state.scanned_signals = valid_signals
    st.success(f"Scan finished! Total results found: {len(valid_signals)} valid signals out of {len(symbols_to_scan)} scanned assets.")

# Display Persistent Results
if st.session_state.scanned_signals:
    valid_signals = st.session_state.scanned_signals

    if scan_mode == "Google Sheet (Scan List for Completed Setups)":
        options = [f"{item['symbol']} | {item['signal']} ({item['pattern']})" for item in valid_signals]
        selected_option = st.selectbox("👇 Select asset to view analysis, target levels, and chart:", options)
        selected_index = options.index(selected_option)
        selected_data = valid_signals[selected_index]

        active_result = selected_data["result"]
        active_symbol = selected_data["symbol"]
    else:
        active_result = valid_signals[0]["result"]
        active_symbol = valid_signals[0]["symbol"]

    if active_result:
        st.session_state.current_symbol = active_symbol
        df_res = active_result["df"]
        signal, pattern = active_result["signal"], active_result["pattern"]
        latest_rsi = df_res['RSI'].iloc[-1] if 'RSI' in df_res.columns else 0.0
        latest_close = df_res['Close'].iloc[-1]

        st.markdown(f"""
        <div style="margin-top: 14px; margin-bottom: 15px;">
            <div style="font-size: 42px; font-weight: 650; color: #0B57D0;">{latest_close:.5f}</div>
            <div style="font-size: 15px; color: #202124;">RSI (14): {latest_rsi:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        e1, e2, e3 = st.columns(3)
        e1.metric("🎯 Entry", f"{active_result['entry']}")
        e2.metric("🛑 Stop Loss", f"{active_result['sl']}")
        e3.metric("🏆 Target", f"{active_result['tp']}")

        # --------------------------------------------------
        # Two-line English Report
        # --------------------------------------------------
        bias_text = "Bullish" if signal == "STRONG BUY" else "Bearish" if signal == "STRONG SELL" else "Neutral"
        st.info(
            f"**ANALYSIS REPORT:** A confirmed **{pattern}** pattern has been detected for **{active_symbol}** indicating a **{bias_text}** trend shift.\n"
            f"**EXECUTION PLAN:** Recommendation is **{signal}** at **{active_result['entry']}** with Stop Loss set at **{active_result['sl']}** and Target at **{active_result['tp']}**."
        )

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_res.index, open=df_res["Open"], high=df_res["High"], low=df_res["Low"], close=df_res["Close"],
            name="Price", increasing_line_color="#137333", decreasing_line_color="#C5221F"
        ))

        # 1. Draw Structure Nodes & Waves
        nodes = active_result.get("nodes", [])
        if nodes:
            sorted_nodes = sorted(nodes, key=lambda item: pd.to_datetime(item[0]))
            x_nodes = [n[0] for n in sorted_nodes]
            y_nodes = [n[1] for n in sorted_nodes]

            fig.add_trace(go.Scatter(
                x=x_nodes, y=y_nodes,
                mode="lines+markers", line=dict(color="#C5221F", width=2.5),
                marker=dict(size=7, color="#0B57D0"), name=f"{pattern}"
            ))

        # 2. Draw Neckline (خط العنق)
        neckline_nodes = active_result.get("neckline_nodes", [])
        if len(neckline_nodes) >= 2:
            x_neck = [n[0] for n in neckline_nodes]
            y_neck = [n[1] for n in neckline_nodes]
            fig.add_trace(go.Scatter(
                x=x_neck, y=y_neck,
                mode="lines",
                line=dict(color="#8E24AA", width=2, dash="dash"),
                name="Neckline"
            ))

        # 3. Draw Target Extension & Arrow (امتداد الهدف وسهم المسار)
        target_nodes = active_result.get("target_nodes", [])
        if len(target_nodes) >= 2:
            entry_idx, entry_val = target_nodes[0]
            tp_idx, tp_val = target_nodes[1]

            # Horizontal Target Line
            fig.add_trace(go.Scatter(
                x=[entry_idx, tp_idx],
                y=[tp_val, tp_val],
                mode="lines",
                line=dict(color="#0F9D58", width=2, dash="dot"),
                name="Target Level"
            ))

            # Directional Arrow Annotation
            fig.add_annotation(
                x=tp_idx,
                y=tp_val,
                ax=entry_idx,
                ay=entry_val,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor="#0F9D58" if signal == "STRONG BUY" else "#D93025"
            )

        fig.update_layout(
            template="plotly_white",
            height=520,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=40, t=10, b=30),
            showlegend=False,
            dragmode='pan'
        )

        config = {
            'scrollZoom': True,
            'displayModeBar': True,
            'responsive': True
        }

        st.plotly_chart(fig, use_container_width=True, config=config)
            
