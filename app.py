import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pattern_engine import SMCPatternEngine

st.set_page_config(page_title="SMC Market Structure Engine", layout="wide")

st.title("⚡ SMC Market Structure Engine")

st.sidebar.header("⚙️ Configuration")
symbol = st.sidebar.text_input("Trading Symbol (Raw Format):", value="BTCUSDT")
depth = st.sidebar.slider("ZigZag Depth", min_value=3, max_value=20, value=8)
tolerance = st.sidebar.slider("Wave Equality Max Tolerance", min_value=0.01, max_value=0.30, value=0.15, step=0.01)

@st.cache_data
def get_market_data():
    np.random.seed(42)
    periods = 120
    # Waxaa lagu saxay freq='h' si uu ula jaanqaado Pandas-ka cusub
    dates = pd.date_range(end=pd.Timestamp.now(), periods=periods, freq='h')
    
    price_base = 63500.0
    swings = np.sin(np.linspace(0, 4 * np.pi, periods)) * 800
    noise = np.random.randn(periods) * 150
    close_prices = price_base + swings + noise
    
    high_prices = close_prices + np.abs(np.random.randn(periods) * 100) + 50
    low_prices = close_prices - np.abs(np.random.randn(periods) * 100) - 50
    open_prices = close_prices + np.random.randn(periods) * 50

    return pd.DataFrame({
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices
    }, index=dates)

df = get_market_data()
current_price = float(df['Close'].iloc[-1])

engine = SMCPatternEngine(df, depth=depth, max_tolerance=tolerance)
analysis = engine.detect_market_patterns()

rsi_val = 28.5
signal_result = engine.evaluate_strict_signal(symbol=symbol, current_price=current_price, rsi_val=rsi_val)

structure_status = analysis["structure_status"]
if "CHoCH" in structure_status:
    st.markdown(f"### 🟢 {structure_status}")
else:
    st.warning(f"🟡 {structure_status}")

st.markdown("### 🎯 Detected Chart Patterns")

if analysis["pattern_found"]:
    st.success(f"✅ {analysis['message']}")
else:
    st.info(f"🔵 {analysis['message']}")

if analysis["details"]:
    cols = st.columns(3)
    cols[0].metric("Wave 1 Length", f"{analysis['details']['wave1_length']}")
    cols[1].metric("Wave 2 Length", f"{analysis['details']['wave2_length']}")
    cols[2].metric("Difference Ratio / Tolerance", f"{analysis['details']['diff_ratio']*100:.1f}% / Max {tolerance*100:.0f}%")

st.markdown("### 🕯️ Price Chart + Major Swings + Order Lines")

df_swings = engine.calculate_major_swings()
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df_swings.index,
    open=df_swings['Open'],
    high=df_swings['High'],
    low=df_swings['Low'],
    close=df_swings['Close'],
    name="Price"
))

fig.add_trace(go.Scatter(
    x=df_swings.index,
    y=df_swings['Major_High'],
    mode='markers',
    name='Major High',
    marker=dict(color='red', size=9, symbol='triangle-up')
))

fig.add_trace(go.Scatter(
    x=df_swings.index,
    y=df_swings['Major_Low'],
    mode='markers',
    name='Major Low',
    marker=dict(color='pink', size=9, symbol='triangle-down')
))

if len(engine.zigzag_points) > 1:
    zz_times = [p[0] for p in engine.zigzag_points]
    zz_vals = [p[1] for p in engine.zigzag_points]
    fig.add_trace(go.Scatter(
        x=zz_times,
        y=zz_vals,
        mode='lines',
        name='Major ZigZag',
        line=dict(color='#3182ce', width=2)
    ))

# 🎯 Ku daridda خطوط الأوامر (Order Lines) على الشارت عند تووفر الإشارة
if signal_result["Status"] == "VALID_SIGNAL":
    entry_p = signal_result['Entry_Price']
    tp_p = signal_result['Take_Profit_Absolute']
    sl_p = signal_result['Stop_Loss_Absolute']

    fig.add_hline(
        y=entry_p,
        line_dash="dash",
        line_color="#3182ce",
        line_width=2,
        annotation_text=f" ENTRY: ${entry_p:,.2f}",
        annotation_position="bottom right",
        annotation_font_color="#3182ce"
    )

    fig.add_hline(
        y=tp_p,
        line_dash="dash",
        line_color="#38a169",
        line_width=2,
        annotation_text=f" TP (Absolute): ${tp_p:,.2f}",
        annotation_position="top right",
        annotation_font_color="#38a169"
    )

    fig.add_hline(
        y=sl_p,
        line_dash="dash",
        line_color="#e53e3e",
        line_width=2,
        annotation_text=f" SL (Absolute): ${sl_p:,.2f}",
        annotation_position="bottom right",
        annotation_font_color="#e53e3e"
    )

fig.update_layout(
    template="plotly_white",
    height=550,
    xaxis_rangeslider_visible=False,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 📋 Mandatory Execution Details (Absolute Values)")

if signal_result["Status"] == "VALID_SIGNAL":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Symbol", signal_result["Symbol"])
    c2.metric("Entry Price", f"${signal_result['Entry_Price']:,.2f}")
    c3.metric("Take Profit (Absolute)", f"${signal_result['Take_Profit_Absolute']:,.2f}")
    c4.metric("Stop Loss (Absolute)", f"${signal_result['Stop_Loss_Absolute']:,.2f}")
else:
    st.warning("⚠️ No trade executed: Conditions or 0.15 wave tolerance rules strictly enforced.")
    
