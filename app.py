import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd


# استيراد محرك النماذج بأي اسم متاح لضمان الاستقرار

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from engine import run_full_analysis
# استيراد دالة الربط بالشيت من ffff.py
try:
    from ffff import get_symbols_from_sheet
except ImportError:
    st.error("⚠️ لم يتم العثور على ملف ffff.py بجانب app.py")

st.set_page_config(page_title="Smart Market Analyzer", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

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
    
    div[data-testid="stTextInput"] input { 
        height: 50px; border-radius: 12px; background: #F1F3F4 !important; 
        color: #0B57D0 !important; border: 1px solid #DADCE0 !important; 
        font-size: 18px !important; font-weight: 700; padding: 0 20px; 
    }
    
    div[data-testid="stButton"] > button { 
        width: 100%; min-height: 58px; border: 0; border-radius: 30px; 
        color: #ffffff; font-size: 18px; font-weight: 700; 
        background: #0B57D0; box-shadow: 0 4px 6px rgba(11, 87, 208, 0.2);
    }
    div[data-testid="stButton"] > button:hover { background: #0842A0; }
    
    .status-card { border-radius: 16px; padding: 20px; margin: 18px 0; border: 1px solid #DADCE0; }
    .status-buy { background: #E6F4EA; border-color: #CEEAD6; color: #137333; }
    .status-sell { background: #FCE8E6; border-color: #FAD2CF; color: #C5221F; }
    .status-wait { background: #FEF7E0; border-color: #FCE8B2; color: #E37400; }
    .status-main { font-size: 24px; font-weight: 800; margin-top: 4px; }
    .small-muted { color: #5F6368; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .section-title { font-size: 20px; font-weight: 700; margin-top: 25px; margin-bottom: 15px; color: #202124; }
</style>
""", unsafe_allow_html=True)

# التهيئة الأولية للحالة
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = "NZDCAD=X"
if "status_summary" not in st.session_state:
    st.session_state.status_summary = "⚡ Live Scan • Ready"

st.markdown(f'''
<div class="top-row">
    <div class="brand-badge">📈 {st.session_state.current_symbol}</div>
    <div class="live-badge">{st.session_state.status_summary}</div>
</div>
''', unsafe_allow_html=True)

# اختيار طريقة الفحص
scan_mode = st.radio("طريقة العمل والمسح:", ["زوج فردي", "Google Sheet (مسح القائمة للفرص المكتملة)"], horizontal=True)

symbols_to_scan = []

if scan_mode == "زوج فردي":
    symbol = st.text_input("Market Asset Symbol", value="NZDCAD=X")
    st.session_state.current_symbol = symbol
    symbols_to_scan = [symbol]
else:
    st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">📂</div><div><div class="card-title">Google Sheet Connection</div><div class="card-subtitle">يتم الجلب تلقائياً عبر الملف المربوط ffff.py</div></div></div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        sheet_id = st.text_input("Spreadsheet ID", value="1TXvF6RhSgfJ631UpnWB38Ww1OMvZVx7VonDB_y1pO3s")
    with c2:
        sheet_name = st.text_input("Sheet Name", value="Sheet1")
    with c3:
        col_name = st.text_input("Column Name", value="Ticker")

    fetched_symbols, err = get_symbols_from_sheet(sheet_id, sheet_name, col_name)
    if err:
        st.error(err)
    else:
        symbols_to_scan = fetched_symbols
        st.success(f"تم تحميل {len(symbols_to_scan)} زوج عملات من Google Sheet!")

st.markdown('<div class="modern-card"><div class="card-heading"><div class="icon-circle">⏱️</div><div><div class="card-title">Select Timeframe</div><div class="card-subtitle">اختر الإطار الزمني للتحليل</div></div></div></div>', unsafe_allow_html=True)
tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"]
selected_tf = st.radio("Select Timeframe", options=tf_options, index=6, horizontal=True, label_visibility="collapsed")

tf_map = {
    "1m": {"interval": "1m", "period": "7d"}, "5m": {"interval": "5m", "period": "60d"},
    "15m": {"interval": "15m", "period": "60d"}, "30m": {"interval": "30m", "period": "60d"},
    "1h": {"interval": "1h", "period": "2y"}, "4h": {"interval": "1h", "period": "2y"},
    "1D": {"interval": "1d", "period": "max"}, "1W": {"interval": "1wk", "period": "max"},
    "1M": {"interval": "1mo", "period": "max"},
}
current_setting = tf_map[selected_tf]

run_scan = st.button("🚀 بدء المسح والتحليل", use_container_width=True)

if run_scan and symbols_to_scan:
    valid_signals = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, sym in enumerate(symbols_to_scan):
        status_text.text(f"جاري فحص الزوج ({idx+1}/{len(symbols_to_scan)}): {sym}...")
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
                
                # تصفية الأزواج: إبقاء أزواج الشراء والبيع فقط وتجاهل الانتظار
                if signal in ["STRONG BUY", "STRONG SELL"] or scan_mode == "زوج فردي":
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
    
    if scan_mode == "Google Sheet (مسح القائمة للفرص المكتملة)":
        if valid_signals:
            st.balloons()
            st.success(f"🎯 عثر البوت على {len(valid_signals)} فرصة شراء/بيع جاهزة من أصل {len(symbols_to_scan)} زوج!")
            
            # القائمة المنسدلة للفرص الناتجة فقط
            options = [f"{item['symbol']} | {item['signal']} ({item['pattern']})" for item in valid_signals]
            selected_option = st.selectbox("👇 اختر العملة لعرض التحليل ومستويات الأهداف والشارت:", options)
            
            selected_index = options.index(selected_option)
            selected_data = valid_signals[selected_index]
            
            active_result = selected_data["result"]
            active_symbol = selected_data["symbol"]
        else:
            st.warning("⚠️ تمت عملية الفحص بنجاح، ولم يتم العثور على أزواج في مرحلة الشراء أو البيع المكتملة حالياً (جميعها في حالة انتظار WAITING).")
            active_result = None
    else:
        active_result = valid_signals[0]["result"] if valid_signals else None
        active_symbol = symbols_to_scan[0]

    # عرض النتيجة المحددة على اللوحة والشارت
    if active_result:
        st.session_state.current_symbol = active_symbol
        df_res = active_result["df"]
        signal, pattern = active_result["signal"], active_result["pattern"]
        latest_rsi = df_res['RSI'].iloc[-1] if 'RSI' in df_res.columns else 0.0
        latest_close = df_res['Close'].iloc[-1]

        st.session_state.status_summary = f"⚡ {active_symbol} | {signal} ({pattern}) | RSI: {latest_rsi:.1f}"

        st.markdown(f"""
        <div style="margin-top: 14px; margin-bottom: 15px;">
            <div style="font-size: 52px; font-weight: 500; color: #0B57D0; line-height: 1;">{latest_close:.4f}</div>
            <div style="font-size: 15px; color: #202124; margin-top: 12px;">RSI (14)</div>
            <div style="font-size: 34px; font-weight: 400; color: #000000; line-height: 1.1;">{latest_rsi:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        status_class = "status-buy" if signal == "STRONG BUY" else "status-sell" if signal == "STRONG SELL" else "status-wait"
        status_icon = "🟢" if signal == "STRONG BUY" else "🔴" if signal == "STRONG SELL" else "🟡"

        st.markdown(f'<div class="status-card {status_class}"><div class="small-muted">Signal Status</div><div class="status-main">{status_icon} {signal}</div><div style="margin-top:4px;"><b>{pattern}</b></div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Execution Levels</div>', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        if signal != "WAITING" and pattern != "NO PATTERN DETECTED":
            e1.metric("🎯 Entry", f"{active_result['entry']}")
            e2.metric("🛑 Stop Loss", f"{active_result['sl']}")
            e3.metric("🏆 Target", f"{active_result['tp']}")
        else:
            e1.metric("🎯 Trigger", f"{active_result.get('trigger', 'N/A')}")
            e2.metric("🛑 Struct SL", f"{active_result.get('sl', 'N/A')}")
            e3.metric("🏆 Proj. TP", f"{active_result.get('tp', 'N/A')}")

        # رسم البياني لمخطط الشموع والنمط
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_res.index, open=df_res["Open"], high=df_res["High"], low=df_res["Low"], close=df_res["Close"], 
            name="Price", increasing_line_color="#137333", decreasing_line_color="#C5221F"
        ))
        
        nodes = active_result.get("nodes", [])
        if nodes:
            sorted_nodes = sorted(nodes, key=lambda item: pd.to_datetime(item[0]))
            x_nodes = [n[0] for n in sorted_nodes]
            y_nodes = [n[1] for n in sorted_nodes]
            line_color = "#137333" if active_result["bias"] == "Bullish" else "#C5221F"

            fig.add_trace(go.Scatter(
                x=x_nodes, y=y_nodes,
                mode="lines+markers", line=dict(color=line_color, width=2),
                marker=dict(size=6, color="#0B57D0"), name=f"{pattern}"
            ))

        fig.update_layout(
            template="plotly_white", 
            height=520, 
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=40, t=10, b=30),
            plot_bgcolor="#FFFFFF", 
            paper_bgcolor="#FFFFFF", 
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        
