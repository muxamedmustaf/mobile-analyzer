import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

try:
    from pattern_engine import run_full_analysis
except ImportError:
    from engine import run_full_analysis

st.set_page_config(page_title="Smart Market Analyzer", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================================
# MODERN UI / CSS (محفوظة بالكامل)
# ==========================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at 88% 12%, rgba(0, 115, 255, .13), transparent 26%), radial-gradient(circle at 15% 45%, rgba(0, 255, 190, .06), transparent 28%), #020712; color: #f7f9ff; }
    .main .block-container { max-width: 1180px; padding: 28px 22px 50px; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    .top-row { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 32px; }
    .brand-badge, .live-badge { border: 1px solid rgba(0, 255, 200, .25); background: rgba(7, 20, 35, .72); box-shadow: 0 0 25px rgba(0, 255, 200, .07); border-radius: 16px; padding: 12px 20px; font-weight: 700; }
    .brand-badge { color: #19f4cf; } .live-badge { color: #16f1c2; border-radius: 30px; }
    .hero { position: relative; min-height: 300px; padding: 8px 0 28px; overflow: hidden; }
    .hero-title { font-size: clamp(42px, 6vw, 78px); font-weight: 800; letter-spacing: -2.5px; margin: 0; }
    .hero-gradient { background: linear-gradient(90deg, #ffffff 0%, #ffffff 37%, #2e62ff 63%, #00e7c0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-subtitle { color: #aeb9cb; font-size: 18px; margin-top: 24px; max-width: 650px; }
    .modern-card { background: linear-gradient(145deg, rgba(11, 22, 40, .94), rgba(3, 11, 24, .92)); border: 1px solid rgba(83, 110, 160, .23); border-radius: 26px; padding: 26px; margin-top: 18px; }
    .card-heading { display: flex; align-items: center; gap: 15px; margin-bottom: 18px; }
    .icon-circle { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 23px; background: linear-gradient(145deg, #1269db, #05377f); }
    .card-title { font-size: 20px; font-weight: 700; color: #ffffff; }
    .card-subtitle { font-size: 14px; color: #98a5b9; }
    div[data-testid="stTextInput"] label { display: none; }
    div[data-testid="stTextInput"] input { height: 62px; border-radius: 18px; background: #071222 !important; color: #ffffff !important; border: 1px solid #344dff !important; font-size: 20px !important; font-weight: 700; padding: 0 22px; }
    div[data-testid="stButton"] > button { width: 100%; min-height: 66px; border: 0; border-radius: 18px; color: #ffffff; font-size: 20px; font-weight: 800; background: linear-gradient(100deg, #3155ff 0%, #168cff 42%, #08d8b0 100%); }
    div[role="radiogroup"] { gap: 10px !important; flex-wrap: wrap !important; }
    div[role="radiogroup"] > label { min-width: 88px; min-height: 52px; justify-content: center; border: 1px solid #20304c !important; border-radius: 18px !important; background: #071222 !important; padding: 0 18px !important; }
    div[role="radiogroup"] > label:has(input:checked) { border-color: #00e9c0 !important; background: rgba(0, 214, 173, .08) !important; color: #12edc3 !important; }
    div[data-testid="metric-container"] { background: #071222; border: 1px solid rgba(80, 110, 160, .22); border-radius: 18px; padding: 15px; }
    .status-card { border-radius: 22px; padding: 22px; margin: 18px 0; border: 1px solid rgba(255,255,255,.08); }
    .status-buy { background: linear-gradient(135deg, rgba(0, 220, 160, .14), rgba(2, 25, 28, .85)); border-color: rgba(0, 239, 190, .35); }
    .status-sell { background: linear-gradient(135deg, rgba(242, 54, 69, .14), rgba(28, 7, 13, .85)); border-color: rgba(242, 54, 69, .35); }
    .status-wait { background: linear-gradient(135deg, rgba(255, 185, 0, .11), rgba(25, 19, 5, .85)); border-color: rgba(255, 185, 0, .28); }
    .status-main { font-size: 28px; font-weight: 800; }
    .small-muted { color: #8f9db2; font-size: 13px; }
    .section-title { font-size: 23px; font-weight: 800; margin-top: 30px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-row"><div class="brand-badge">📈 SMART MARKET ANALYZER</div><div class="live-badge">⚡ Real-time Analysis</div></div><div class="hero"><h1 class="hero-title">Financial Market<br>Pattern &<br><span class="hero-gradient">Indicator Scanner</span></h1><div class="hero-subtitle">Advanced pattern detection • Powerful indicators<br>Smart insights • Better decisions</div></div>', unsafe_allow_html=True)
st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">🌐</div><div><div class="card-title">Market Asset Symbol (Ticker)</div><div class="card-subtitle">Enter the symbol you want to analyze</div></div></div></div>', unsafe_allow_html=True)

symbol = st.text_input("Market Asset Symbol", value="XAUUSD=X")
run_scan = st.button("🚀  Run Analysis", use_container_width=True)

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">◷</div><div><div class="card-title">Select Timeframe</div><div class="card-subtitle">Choose your preferred chart timeframe</div></div></div></div>', unsafe_allow_html=True)
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio("Select Timeframe", options=tf_options, index=5, horizontal=True, label_visibility="collapsed")

with st.expander("⚙️  Chart Settings & Display Controls"):
    c_zoom, c_height, c_theme = st.columns(3)
    with c_zoom: visible_candles = st.slider("🔍 Candles Visible", min_value=20, max_value=300, value=100, step=10)
    with c_height: chart_height = st.slider("📐 Chart Height", min_value=350, max_value=1000, value=650, step=50)
    with c_theme: chart_theme = st.selectbox("🎨 Chart Theme", options=["TradingView Dark", "Classic White", "Midnight Navy"], index=0)

tf_map = {
    "1m": {"interval": "1m", "period": "7d"}, "5m": {"interval": "5m", "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"}, "30m": {"interval": "30m", "period": "60d"},
    "1h": {"interval": "1h", "period": "2y"}, "4h": {"interval": "1h", "period": "2y"},
    "1D": {"interval": "1d", "period": "max"}, "1W": {"interval": "1wk", "period": "max"},
    "1M": {"interval": "1mo", "period": "max"},
}
current_setting = tf_map[selected_tf]

if run_scan:
    with st.spinner(f"Loading market data & calculating ZigZag (12, 5, 3) for {symbol}..."):
        try:
            df = yf.download(symbol, period=current_setting["period"], interval=current_setting["interval"], progress=False, auto_adjust=False)
        except Exception:
            df = pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if selected_tf == "4h" and not df.empty:
        df = df.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()

    if df.empty or len(df) < 20:
        st.error(f"⚠️ Data unavailable. Verify ticker.")
    else:
        result = run_full_analysis(df)
        df_res = result["df"]
        signal, pattern = result["signal"], result["pattern"]

        status_class = "status-buy" if signal == "STRONG BUY" else "status-sell" if signal == "STRONG SELL" else "status-wait"
        status_icon = "🟢" if signal == "STRONG BUY" else "🔴" if signal == "STRONG SELL" else "🟡"

        st.markdown(f'<div class="status-card {status_class}"><div class="small-muted">FINAL MARKET SIGNAL</div><div class="status-main">{status_icon} {signal}</div><div style="margin-top:7px;color:#b9c5d8;">Pattern: <b>{pattern}</b></div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">📐 Absolute Trade Execution Levels</div>', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        if signal != "WAITING" and pattern != "NO PATTERN DETECTED":
            e1.metric("🎯 Entry Price", f"{result['entry']}")
            e2.metric("🛑 Stop Loss", f"{result['sl']}")
            e3.metric("🏆 Take Profit", f"{result['tp']}")
        else:
            e1.metric("🎯 Trigger Neckline", f"{result.get('trigger', 'N/A')}")
            e2.metric("🛑 Structure SL", f"{result.get('sl', 'N/A')}")
            e3.metric("🏆 Measured TP", f"{result.get('tp', 'N/A')}")

        # ==========================================
        # CHART PLOTTING WITH SHADING
        # ==========================================
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_res.index, open=df_res["Open"], high=df_res["High"], low=df_res["Low"], close=df_res["Close"], name="Price"))
        if "EMA50" in df_res.columns: fig.add_trace(go.Scatter(x=df_res.index, y=df_res["EMA50"], line=dict(color="#FF9800", width=1.5), name="EMA 50"))
        if "EMA200" in df_res.columns: fig.add_trace(go.Scatter(x=df_res.index, y=df_res["EMA200"], line=dict(color="#29B6F6", width=2), name="EMA 200"))

        # رسم تظليل النمط (Pattern Shading)
        nodes = result.get("nodes", [])
        if nodes:
            # تجهيز الإحداثيات لرسم مضلع النمط
            x_nodes = [n[0] for n in nodes]
            y_nodes = [n[1] for n in nodes]
            
            # إغلاق المضلع لضمان تظليل صحيح
            x_nodes.append(x_nodes[0])
            y_nodes.append(y_nodes[0])
            
            # تحديد لون التظليل حسب الاتجاه
            fill_color = "rgba(46, 204, 113, 0.15)" if result["bias"] == "Bullish" else "rgba(231, 76, 60, 0.15)"
            line_color = "#2ECC71" if result["bias"] == "Bullish" else "#E74C3C"

            # تظليل النطاق الداخلي
            fig.add_trace(go.Scatter(
                x=x_nodes, y=y_nodes, fill="toself", fillcolor=fill_color,
                mode="lines+markers", line=dict(color=line_color, width=3),
                marker=dict(size=8, color="#F1C40F"), name=f"{pattern} Structure"
            ))
            
            # رسم خط العنق أو نقطة الكسر (Trigger Level)
            trigger = result.get("trigger")
            if trigger:
                fig.add_trace(go.Scatter(
                    x=[x_nodes[0], df_res.index[-1]], y=[trigger, trigger],
                    mode="lines", line=dict(color="#E0A800", width=2, dash="dash"), name="Neckline / Trigger"
                ))

        # خطوط الهدف والوقف
        if signal in ["STRONG BUY", "STRONG SELL"]:
            fig.add_hline(y=result["entry"], line_dash="dash", line_color="#2962FF", annotation_text="ENTRY")
            fig.add_hline(y=result["sl"], line_dash="dash", line_color="#F23645", annotation_text="SL")
            fig.add_hline(y=result["tp"], line_dash="dash", line_color="#089981", annotation_text="TP")

        x_min = df_res.index[-visible_candles] if len(df_res) > visible_candles else df_res.index[0]
        bg_bg, grid_col, plotly_tpl = {"TradingView Dark": ("#131722", "#2A2E39", "plotly_dark"), "Classic White": ("#FFFFFF", "#E0E0E0", "plotly_white"), "Midnight Navy": ("#0B192C", "#1E3E62", "plotly_dark")}[chart_theme]
        
        fig.update_layout(
            title=f"<b>{symbol}</b> | Pattern: <b>{pattern}</b>",
            template=plotly_tpl, height=chart_height, xaxis_rangeslider_visible=False,
            xaxis=dict(range=[x_min, df_res.index[-1]], showgrid=True, gridcolor=grid_col),
            yaxis=dict(side="right", gridcolor=grid_col), plot_bgcolor=bg_bg, paper_bgcolor=bg_bg
        )

        st.plotly_chart(fig, use_container_width=True)
