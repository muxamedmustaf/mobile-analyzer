import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.market_data import fetch_market_data
from structure.market_structure import analyze_market_structure
from structure.patterns import detect_chart_patterns  # Shaqadaada asalka ah

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
    with st.spinner("Waa la soo jiidayaa oo la falanqeynayaa xogta suuqa..."):
        df = fetch_market_data(symbol, interval, period)
        
        if df.empty:
            st.error("Calaamaddu ma shaqaynayso ama xog lama helin!")
        else:
            # Falanqaynta Structure-ka iyo Patterns-ka adigoo adeegsanaya script-kaaga
            df = analyze_market_structure(df)
            df = detect_chart_patterns(df) 
            
            # Soo bandhigidda 3-da pattern ee ugu ixtimaalka badan safka ugu dambeeya
            latest_row = df.iloc[-1]
            top_patterns = latest_row.get('Top_3_Patterns', 'No Pattern Found')
            best_pattern = latest_row.get('Pattern', 'No Pattern')
            
            st.subheader("🎯 Falanqaynta Qaababka Suuqa")
            st.success(f"Siday ugu kala sarraysaan ixtimaalka suuqa:\n\n **{top_patterns}**")
            
            # --- DIYAARINTA ANNOTATION-KA KANU UGA JEEDO KAN UGU WEYN (LATEST PATTERN) ---
            annotations_list = []
            
            # Maadaama shaqadaadu ay pattern-ka ugu xoogga badan geliso safka ugu dambeeya (df.iloc[-1])
            if best_pattern != 'No Pattern':
                last_time = df.index[-1]
                last_price = latest_row['Close'] # Ama qiimaha High/Low ee u dhow
                
                # Kala saar midabka iyadoo la eegayo magaca pattern-ka (Bullish vs Bearish)
                is_bullish = "Bottom" in best_pattern or "Inverse" in best_pattern or "Ascending" in best_pattern or "Falling" in best_pattern or "Bounce" in best_pattern
                arrow_color = "#00E676" if is_bullish else "#FF1744"
                
                annotations_list.append(go.layout.Annotation(
                    x=last_time,
                    y=last_price,
                    xref="x",
                    yref="y",
                    text=f"⭐ {best_pattern}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowcolor=arrow_color,
                    ax=0,
                    ay=-50, # Kor ka dul saar shumaca ugu dambeeya
                    bgcolor="rgba(0,0,0,0.85)",
                    bordercolor=arrow_color,
                    borderwidth=1.5,
                    borderpad=5,
                    font=dict(size=11, color="#FFFFFF")
                ))

            # --- Sawiridda Shaxda (Candlestick Chart oo wadata Annotation-ka Pattern-ka ugu xoogga badan) ---
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Candlestick"
            )])
            
            fig.update_layout(
                title=f"Shaxda Suuqa ee {symbol} iyo Pattern-ka ugu sarreeya",
                xaxis_title="Wakhtiga",
                yaxis_title="Qiimaha (Price)",
                template="plotly_dark",
                height=650,
                annotations=annotations_list
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
