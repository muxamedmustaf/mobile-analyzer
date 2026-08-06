import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.market_data import fetch_market_data
from structure.market_structure import analyze_market_structure
from structure.patterns import detect_chart_patterns  # <-- Halkan ayaad ku dartay

# 1. Qurxinta Shaashadda (UI Design & Layout)
st.set_page_config(
    page_title="Smart Money Structure AI", 
    page_icon="⚡", 
    layout="wide"
)

st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        color: #FF4B4B;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #888;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">⚡ SMC Market Structure Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Falanqaynta Suuqa, Swings, BOS, iyo CHOCH oo Candlestick ah</p>', unsafe_allow_html=True)

# Sidebar-ka Kontoroolka
st.sidebar.header("⚙️ Dejinta Suuqa")
symbol = st.sidebar.text_input("Calaamada Suuqa (Symbol)", value="GC=F")
interval = st.sidebar.selectbox("Furan (Interval)", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], index=3)
period = st.sidebar.selectbox("Mudada (Period)", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=2)

run_button = st.sidebar.button("🚀 Falanqee Suuqa (Run Analysis)")

if run_button:
    with st.spinner("Waa la soo jiidayaa xogta suuqa..."):
        df = fetch_market_data(symbol, interval, period)
        
        if df.empty:
            st.error("Calaamaddu ma shaqaynayso ama xog lama helin!")
        else:
            # Falanqaynta Structure-ka iyo Patterns-ka
            df = analyze_market_structure(df)
            df = detect_chart_patterns(df)  # <-- Halkan ayaad ku baareysaa patterns-ka
            
            # Soo bandhigidda 3-da pattern ee ugu ixtimaalka badan
            latest_row = df.iloc[-1]
            top_patterns = latest_row.get('Top_3_Patterns', 'No Pattern')
            
            st.subheader("🎯 3-da Chart Pattern ee ugu Ixtimaalka badan")
            st.success(f"Siday ugu kala sarraysaan ixtimaalka ay suuqa uga dhici karaan:\n\n **{top_patterns}**")
            
            # Sawiridda Shaxda (Candlestick Chart)
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Candlestick"
            )])
            
            fig.update_layout(
                title=f"Shaxda Suuqa ee {symbol}",
                xaxis_title="Wakhtiga",
                yaxis_title="Qiimaha (Price)",
                template="plotly_dark",
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
