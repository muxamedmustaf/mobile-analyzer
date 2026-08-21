import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

try:
    from pattern_engine import run_full_analysis
except ImportError:
    from engine import run_full_analysis

st.set_page_config(page_title="Smart Market Analyzer", page_icon="ðŸ“ˆ", layout="wide", initial_sidebar_state="collapsed")

# ==========================================================
# MODERN LIGHT UI / CSS
# ==========================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background: #FFFFFF; color: #202124; }
    .main .block-container { max-width: 1180px; padding: 28px 22px 50px; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    
    .top-row { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 24px; }
    .brand-badge, .live-badge { 
        border: 1px solid #DADCE0; background: #FFFFFF; 
        border-radius: 16px; padding: 10px 18px; font-weight: 700; color: #0B57D0; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .live-badge { border-radius: 30px; }
    
    /* Ø´Ø±ÙŠØ· Ø£Ø²Ø±Ø§Ø± ØªØ­ÙƒÙ… Ø§Ù„Ø´Ø§Ø±Øª Ø§Ù„Ø¹Ù„ÙˆÙŠ */
    .chart-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #DADCE0;
        border-bottom: none;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        padding: 12px 20px;
        margin-top: 25px;
    }
    .chart-toolbar-title {
        font-weight: 700;
        font-size: 15px;
        color: #0B57D0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .chart-actions {
        display: flex;
        gap: 16px;
        font-size: 18px;
        color: #0B57D0;
        cursor: pointer;
    }

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
    
    div[data-testid="stTextInput"] label { display: none; }
    div[data-testid="stTextInput"] input { 
        height: 60px; border-radius: 12px; background: #F1F3F4 !important; 
        color: #0B57D0 !important; border: 1px solid #DADCE0 !important; 
        font-size: 22px !important; font-weight: 700; padding: 0 20px; 
    }
    
    div[data-testid="stButton"] > button { 
        width: 100%; min-height: 58px; border: 0; border-radius: 30px; 
        color: #ffffff; font-size: 18px; font-weight: 700; 
        background: #0B57D0; box-shadow: 0 4px 6px rgba(11, 87, 208, 0.2);
    }
    div[data-testid="stButton"] > button:hover { background: #0842A0; }
    
    div[role="radiogroup"] { gap: 8px !important; flex-wrap: wrap !important; }
    div[role="radiogroup"] > label { 
        min-width: 75px; min-height: 44px; justify-content: center; 
        border: 1px solid #DADCE0 !important; border-radius: 22px !important; 
        background: #FFFFFF !important; padding: 0 14px !important; color: #5F6368 !important;
    }
    div[role="radiogroup"] > label:has(input:checked) { 
        border-color: #0B57D0 !important; background: #E8F0FE !important; 
        color: #0B57D0 !important; font-weight: 600;
    }
    
    .status-card { border-radius: 16px; padding: 20px; margin: 18px 0; border: 1px solid #DADCE0; }
    .status-buy { background: #E6F4EA; border-color: #CEEAD6; color: #137333; }
    .status-sell { background: #FCE8E6; border-color: #FAD2CF; color: #C5221F; }
    .status-wait { background: #FEF7E0; border-color: #FCE8B2; color: #E37400; }
    .status-main { font-size: 24px; font-weight: 800; margin-top: 4px; }
    .small-muted { color: #5F6368; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .section-title { font-size: 20px; font-weight: 700; margin-top: 25px; margin-bottom: 15px; color: #202124; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-row"><div class="brand-badge">ðŸ“ˆ SMART ANALYZER</div><div class="live-badge">âš¡ Live Scan</div></div>', unsafe_allow_html=True)

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">ðŸ”</div><div><div class="card-title">Market Asset Symbol</div><div class="card-subtitle">Enter ticker (e.g., NZDCAD=X)</div></div></div></div>', unsafe_allow_html=True)

symbol = st.text_input("Market Asset Symbol", value="NZDCAD=X")
run_scan = st.button("ðŸš€ Run Analysis", use_container_width=True)

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">â±ï¸</div><div><div class="card-title">Select Timeframe</div><div class="card-subtitle">Choose interval</div></div></div></div>', unsafe_allow_html=True)
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio("Select Timeframe", options=tf_options, index=6, horizontal=True, label_visibility="collapsed")

with st.expander("âš™ï¸ Advanced Display Configuration"):
    c_zoom, c_height = st.columns(2)
    with c_zoom: visible_candles = st.slider("ðŸ” Default Visible Candles", min_value=20, max_value=300, value=90, step=10)
    with c_height: chart_height = st.slider("ðŸ“ Chart Height", min_value=350, max_value=900, value=520, step=50)

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
        st.error(f"âš ï¸ Data unavailable or network issue for ticker: {symbol}")
    else:
        result = run_full_analysis(df)
        df_res = result["df"]
        signal, pattern = result["signal"], result["pattern"]
        latest_rsi = df_res['RSI'].iloc[-1] if 'RSI' in df_res.columns else 0.0
        latest_close = df_res['Close'].iloc[-1]

        # Ø§Ù„ØªØ±ÙˆÙŠØ³Ø© Ø§Ù„Ø¹Ù„ÙˆÙŠØ© Ù„Ù„Ø³Ø¹Ø± Ùˆ RSI
        st.markdown(f"""
        <div style="margin-top: 14px; margin-bottom: 15px;">
            <div style="font-size: 52px; font-weight: 500; color: #0B57D0; line-height: 1;">{latest_close:.4f}</div>
            <div style="font-size: 15px; color: #202124; margin-top: 12px;">RSI (14)</div>
            <div style="font-size: 34px; font-weight: 400; color: #000000; line-height: 1.1;">{latest_rsi:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        status_class = "status-buy" if signal == "STRONG BUY" else "status-sell" if signal == "STRONG SELL" else "status-wait"
        status_icon = "ðŸŸ¢" if signal == "STRONG BUY" else "ðŸ”´" if signal == "STRONG SELL" else "ðŸŸ¡"

        st.markdown(f'<div class="status-card {status_class}"><div class="small-muted">Signal Status</div><div class="status-main">{status_icon} {signal}</div><div style="margin-top:4px;"><b>{pattern}</b></div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Execution Levels</div>', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        if signal != "WAITING" and pattern != "NO PATTERN DETECTED":
            e1.metric("ðŸŽ¯ Entry", f"{result['entry']}")
            e2.metric("ðŸ›‘ Stop Loss", f"{result['sl']}")
            e3.metric("ðŸ† Target", f"{result['tp']}")
        else:
            e1.metric("ðŸŽ¯ Trigger", f"{result.get('trigger', 'N/A')}")
            e2.metric("ðŸ›‘ Struct SL", f"{result.get('sl', 'N/A')}")
            e3.metric("ðŸ† Proj. TP", f"{result.get('tp', 'N/A')}")

        # ==========================================
        # Ø´Ø±ÙŠØ· Ø£Ø²Ø±Ø§Ø± Ø§Ù„ØªØ­ÙƒÙ… Ø§Ù„Ø¹Ù„ÙˆÙŠ ÙÙˆÙ‚ Ø§Ù„Ø´Ø§Ø±Øª
        # ==========================================
        st.markdown(f"""
        <div class="chart-toolbar">
            <div class="chart-toolbar-title">ðŸ“ˆ Chart &bull; {symbol} &bull; {selected_tf}</div>
            <div class="chart-actions">
                <span>ðŸ”—</span>
                <span>â­</span>
                <span>âœï¸</span>
                <span>â›¶</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Ø¨Ù†Ø§Ø¡ Ø§Ù„Ø±Ø³Ù… Ø§Ù„Ø¨ÙŠØ§Ù†ÙŠ
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=df_res.index, open=df_res["Open"], high=df_res["High"], low=df_res["Low"], close=df_res["Close"], 
            name="Price", increasing_line_color="#137333", decreasing_line_color="#C5221F"
        ))
        
        nodes = result.get("nodes", [])
        if nodes:
            # 1. ØªØ±ØªÙŠØ¨ Ø§Ù„Ø¹Ù‚Ø¯ Ø²Ù…Ù†ÙŠØ§Ù‹ Ù…Ù† Ø§Ù„ÙŠØ³Ø§Ø± Ù„Ù„ÙŠÙ…ÙŠÙ† Ù„Ù…Ù†Ø¹ Ø£ÙŠ ØªÙ‚Ø§Ø·Ø¹ Ø£Ùˆ ØªØ¯Ø§Ø®Ù„ Ø®Ø·ÙˆØ·
            sorted_nodes = sorted(nodes, key=lambda item: pd.to_datetime(item[0]))
            x_nodes = [n[0] for n in sorted_nodes]
            y_nodes = [n[1] for n in sorted_nodes]
            
            fill_color = "rgba(19, 115, 51, 0.08)" if result["bias"] == "Bullish" else "rgba(197, 34, 31, 0.08)"
            line_color = "#137333" if result["bias"] == "Bullish" else "#C5221F"

            # Ø±Ø³Ù… Ø®Ø· Ø§Ù„Ù†Ù…Ø· Ø§Ù„Ù‡Ù†Ø¯Ø³ÙŠ Ø¨ØªØ±ØªÙŠØ¨Ù‡ Ø§Ù„ØµØ­ÙŠØ­
            fig.add_trace(go.Scatter(
                x=x_nodes, y=y_nodes,
                mode="lines+markers", line=dict(color=line_color, width=2),
                marker=dict(size=6, color="#0B57D0"), name=f"{pattern}"
            ))
            
            # 2. ØªØµØ­ÙŠØ­ Ø®Ø· Ø§Ù„Ø¹Ù†Ù‚ (Neckline): ÙŠØ¨Ø¯Ø£ Ø£ÙÙ‚ÙŠØ§Ù‹ Ù…Ù† Ø¨Ø¯Ø§ÙŠØ© Ø§Ù„Ù†Ù…Ø· ÙˆÙŠÙ…ØªØ¯ Ø­ØªÙ‰ Ù†Ù‡Ø§ÙŠØ© Ø§Ù„Ø´Ø§Ø±Øª
            trigger = result.get("trigger")
            if trigger and len(x_nodes) >= 2:
                x_neckline_start = x_nodes[0]
                x_neckline_end = df_res.index[-1]
                
                fig.add_trace(go.Scatter(
                    x=[x_neckline_start, x_neckline_end], y=[trigger, trigger],
                    mode="lines", line=dict(color="#E37400", width=1.5, dash="dash"), name="Neckline"
                ))

        x_min = df_res.index[-visible_candles] if len(df_res) > visible_candles else df_res.index[0]
        
        fig.update_layout(
            template="plotly_white", 
            height=chart_height, 
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=40, t=10, b=30),
            xaxis=dict(
                range=[x_min, df_res.index[-1]], 
                showgrid=True, 
                gridcolor="#F1F3F4", 
                tickfont=dict(color="#5F6368"),
                fixedrange=False
            ),
            yaxis=dict(
                side="right", 
                showgrid=True, 
                gridcolor="#F1F3F4", 
                tickfont=dict(color="#5F6368"),
                fixedrange=False
            ), 
            plot_bgcolor="#FFFFFF", 
            paper_bgcolor="#FFFFFF", 
            showlegend=False
        )

        config_options = {
            'scrollZoom': True,
            'displayModeBar': False,
            'doubleClick': 'reset',
            'responsive': True
        }

        st.plotly_chart(fig, use_container_width=True, config=config_options)
        
