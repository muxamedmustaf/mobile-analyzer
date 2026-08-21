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
# MODERN LIGHT UI / CSS (مستوحى من الصورة 50965.png)
# ==========================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* الخلفية الأساسية بيضاء نظيفة */
    .stApp { background: #FFFFFF; color: #202124; }
    .main .block-container { max-width: 1180px; padding: 28px 22px 50px; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    
    /* الشارات العلوية */
    .top-row { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 32px; }
    .brand-badge, .live-badge { 
        border: 1px solid #DADCE0; background: #FFFFFF; 
        border-radius: 16px; padding: 12px 20px; font-weight: 700; color: #0B57D0; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .live-badge { border-radius: 30px; }
    
    /* نصوص الترويسة */
    .hero { position: relative; min-height: 200px; padding: 8px 0 28px; }
    .hero-title { font-size: clamp(36px, 5vw, 64px); font-weight: 800; letter-spacing: -1.5px; margin: 0; color: #202124; }
    .hero-gradient { color: #0B57D0; }
    .hero-subtitle { color: #5F6368; font-size: 18px; margin-top: 16px; max-width: 650px; }
    
    /* البطاقات */
    .modern-card { 
        background: #FFFFFF; border: 1px solid #DADCE0; 
        border-radius: 16px; padding: 24px; margin-top: 18px; 
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .card-heading { display: flex; align-items: center; gap: 15px; margin-bottom: 18px; }
    .icon-circle { 
        width: 48px; height: 48px; border-radius: 50%; display: flex; 
        align-items: center; justify-content: center; font-size: 23px; 
        background: #E8F0FE; color: #0B57D0; 
    }
    .card-title { font-size: 18px; font-weight: 700; color: #202124; }
    .card-subtitle { font-size: 14px; color: #5F6368; }
    
    /* حقول الإدخال */
    div[data-testid="stTextInput"] label { display: none; }
    div[data-testid="stTextInput"] input { 
        height: 62px; border-radius: 12px; background: #F1F3F4 !important; 
        color: #0B57D0 !important; border: 1px solid #DADCE0 !important; 
        font-size: 24px !important; font-weight: 700; padding: 0 22px; 
    }
    div[data-testid="stTextInput"] input:focus { border-color: #0B57D0 !important; background: #FFFFFF !important; }
    
    /* الزر الأساسي */
    div[data-testid="stButton"] > button { 
        width: 100%; min-height: 62px; border: 0; border-radius: 30px; 
        color: #ffffff; font-size: 18px; font-weight: 700; 
        background: #0B57D0; box-shadow: 0 4px 6px rgba(11, 87, 208, 0.2);
    }
    div[data-testid="stButton"] > button:hover { background: #0842A0; }
    
    /* الأزرار الإشعاعية (Timeframes) */
    div[role="radiogroup"] { gap: 8px !important; flex-wrap: wrap !important; }
    div[role="radiogroup"] > label { 
        min-width: 80px; min-height: 48px; justify-content: center; 
        border: 1px solid #DADCE0 !important; border-radius: 24px !important; 
        background: #FFFFFF !important; padding: 0 16px !important; color: #5F6368 !important;
    }
    div[role="radiogroup"] > label:has(input:checked) { 
        border-color: #0B57D0 !important; background: #E8F0FE !important; 
        color: #0B57D0 !important; font-weight: 600;
    }
    
    /* المربعات الرقمية (Metrics) */
    div[data-testid="metric-container"] { 
        background: #FFFFFF; border: 1px solid #DADCE0; 
        border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    div[data-testid="metric-container"] label { color: #5F6368 !important; }
    div[data-testid="metric-container"] div { color: #0B57D0 !important; font-weight: 700 !important; }
    
    /* بطاقة الحالة */
    .status-card { border-radius: 16px; padding: 22px; margin: 18px 0; border: 1px solid #DADCE0; }
    .status-buy { background: #E6F4EA; border-color: #CEEAD6; color: #137333; }
    .status-sell { background: #FCE8E6; border-color: #FAD2CF; color: #C5221F; }
    .status-wait { background: #FEF7E0; border-color: #FCE8B2; color: #E37400; }
    .status-main { font-size: 26px; font-weight: 800; margin-top: 5px; }
    .small-muted { color: #5F6368; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .section-title { font-size: 20px; font-weight: 700; margin-top: 30px; margin-bottom: 15px; color: #202124; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-row"><div class="brand-badge">📈 SMART MARKET ANALYZER</div><div class="live-badge">⚡ Real-time Analysis</div></div><div class="hero"><h1 class="hero-title">Financial Market<br><span class="hero-gradient">Pattern Scanner</span></h1><div class="hero-subtitle">Clean, precise, and objective market geometry detection.</div></div>', unsafe_allow_html=True)

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">🔍</div><div><div class="card-title">Market Asset Symbol</div><div class="card-subtitle">Enter ticker (e.g., NZDCAD=X, XAUUSD=X)</div></div></div></div>', unsafe_allow_html=True)

symbol = st.text_input("Market Asset Symbol", value="NZDCAD=X")
run_scan = st.button("🚀  Run Analysis", use_container_width=True)

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">⏱️</div><div><div class="card-title">Select Timeframe</div><div class="card-subtitle">Choose chart interval</div></div></div></div>', unsafe_allow_html=True)
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio("Select Timeframe", options=tf_options, index=5, horizontal=True, label_visibility="collapsed")

with st.expander("⚙️  Chart Settings & Display Controls"):
    c_zoom, c_height = st.columns(2)
    with c_zoom: visible_candles = st.slider("🔍 Candles Visible", min_value=20, max_value=300, value=100, step=10)
    with c_height: chart_height = st.slider("📐 Chart Height", min_value=350, max_value=1000, value=550, step=50)

tf_map = {
    "1m": {"interval": "1m", "period": "7d"}, "5m": {"interval": "5m", "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"}, "30m": {"interval": "30m", "period": "60d"},
    "1h": {"interval": "1h", "period": "2y"}, "4h": {"interval": "1h", "period": "2y"},
    "1D": {"interval": "1d", "period": "max"}, "1W": {"interval": "1wk", "period": "max"},
    "1M": {"interval": "1mo", "period": "max"},
}
current_setting = tf_map[selected_tf]

if run_scan:
    with st.spinner(f"Loading market data for {symbol}..."):
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
        latest_rsi = df_res['RSI'].iloc[-1] if 'RSI' in df_res.columns else 0.0
        latest_close = df_res['Close'].iloc[-1]

        # عرض السعر و RSI بأسلوب الصورة
        st.markdown(f"""
        <div style="margin-top: 10px; margin-bottom: 20px;">
            <div style="font-size: 56px; font-weight: 500; color: #0B57D0; line-height: 1;">{latest_close:.4f}</div>
            <div style="font-size: 16px; color: #202124; margin-top: 15px;">RSI (14)</div>
            <div style="font-size: 36px; font-weight: 400; color: #000000; line-height: 1.1;">{latest_rsi:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        status_class = "status-buy" if signal == "STRONG BUY" else "status-sell" if signal == "STRONG SELL" else "status-wait"
        status_icon = "🟢" if signal == "STRONG BUY" else "🔴" if signal == "STRONG SELL" else "🟡"

        st.markdown(f'<div class="status-card {status_class}"><div class="small-muted">Analysis Signal</div><div class="status-main">{status_icon} {signal}</div><div style="margin-top:5px;"><b>{pattern}</b></div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Execution Levels</div>', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        if signal != "WAITING" and pattern != "NO PATTERN DETECTED":
            e1.metric("🎯 Entry", f"{result['entry']}")
            e2.metric("🛑 Stop Loss", f"{result['sl']}")
            e3.metric("🏆 Target", f"{result['tp']}")
        else:
            e1.metric("🎯 Trigger", f"{result.get('trigger', 'N/A')}")
            e2.metric("🛑 Struct SL", f"{result.get('sl', 'N/A')}")
            e3.metric("🏆 Proj. TP", f"{result.get('tp', 'N/A')}")

        # ==========================================
        # CHART PLOTTING (White Theme)
        # ==========================================
        fig = go.Figure()
        
        # الشموع اليابانية
        fig.add_trace(go.Candlestick(
            x=df_res.index, open=df_res["Open"], high=df_res["High"], low=df_res["Low"], close=df_res["Close"], 
            name="Price", increasing_line_color="#137333", decreasing_line_color="#C5221F"
        ))
        
        # رسم تظليل النمط
        nodes = result.get("nodes", [])
        if nodes:
            x_nodes = [n[0] for n in nodes]
            y_nodes = [n[1] for n in nodes]
            x_nodes.append(x_nodes[0])
            y_nodes.append(y_nodes[0])
            
            fill_color = "rgba(19, 115, 51, 0.1)" if result["bias"] == "Bullish" else "rgba(197, 34, 31, 0.1)"
            line_color = "#137333" if result["bias"] == "Bullish" else "#C5221F"

            fig.add_trace(go.Scatter(
                x=x_nodes, y=y_nodes, fill="toself", fillcolor=fill_color,
                mode="lines+markers", line=dict(color=line_color, width=2),
                marker=dict(size=6, color="#0B57D0"), name=f"{pattern}"
            ))
            
            trigger = result.get("trigger")
            if trigger:
                fig.add_trace(go.Scatter(
                    x=[x_nodes[0], df_res.index[-1]], y=[trigger, trigger],
                    mode="lines", line=dict(color="#E37400", width=2, dash="dash"), name="Neckline"
                ))

        x_min = df_res.index[-visible_candles] if len(df_res) > visible_candles else df_res.index[0]
        
        # تخصيص ألوان الشارت ليكون أبيض ناصع مع خطوط شبكية رمادية فاتحة
        fig.update_layout(
            title=dict(text=f"<b>{symbol} ({selected_tf}) | Pattern: {pattern}</b>", font=dict(color="#202124", size=16)),
            template="plotly_white", height=chart_height, xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=40, t=50, b=30),
            xaxis=dict(range=[x_min, df_res.index[-1]], showgrid=True, gridcolor="#F1F3F4", tickfont=dict(color="#5F6368")),
            yaxis=dict(side="right", showgrid=True, gridcolor="#F1F3F4", tickfont=dict(color="#5F6368")), 
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
