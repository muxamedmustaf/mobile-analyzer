import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.market_data import fetch_market_data
from structure.market_structure import analyze_market_structure

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
interval = st.sidebar.selectbox("Furan (Interval)", ["15m", "30m", "1h", "4h"], index=1)
period = st.sidebar.selectbox("Mudada (Period)", ["1d", "5d", "1mo"], index=1)

run_analysis = st.sidebar.button("🚀 Falanqee Suuqa (Run Analysis)")

if run_analysis:
    with st.spinner("Fadlan sug, xogta suuqa iyo structure-ka ayaa la socodsiiyay..."):
        df = fetch_market_data(symbol=symbol, interval=interval, period=period)
        
        if not df.empty:
            # Falanqaynta buuxda
            analyzed_df = analyze_market_structure(df)
            
            st.success("✨ Xogta si guul leh ayaa loo falanqeeyay!")
            
            # Xaaladda Hadda ee Structure-ka
            latest_row = analyzed_df.iloc[-1]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Qiimaha Hadda (Close)", f"{latest_row['Close']:.2f}")
            with col2:
                current_struct = latest_row.get('Structure', 'Waiting')
                st.metric("Trend / Structure", current_struct if current_struct else "Consolidation")
            with col3:
                bos_val = latest_row.get('BOS', 'None')
                st.metric("Jebinta (BOS)", bos_val if pd.notna(bos_val) else "No BOS")
            with col4:
                choch_val = latest_row.get('CHOCH', 'None')
                st.metric("Isbeddelka (CHOCH)", choch_val if pd.notna(choch_val) else "No CHOCH")
            
            st.markdown("---")
            
            # 2. Soo bandhigidda Candlestick Chart (TradingView Style iyadoo la adeegsanayo Plotly)
            st.subheader("📈 Candlestick Chart-ka Suuqa")
            
            fig = go.Figure(data=[go.Candlestick(
                x=analyzed_df.index,
                open=analyzed_df['Open'],
                high=analyzed_df['High'],
                low=analyzed_df['Low'],
                close=analyzed_df['Close'],
                name='OHLC'
            )])
            
            fig.update_layout(
                template='plotly_dark',
                xaxis_title='Wakhtiga (Datetime)',
                yaxis_title='Qiimaha (Price)',
                height=600,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. Miiska Xogta ee Nidaamsan
            st.subheader("📋 Faahfaahinta Xogta & Calaamadaha (Data Table)")
            display_cols = ['Open', 'High', 'Low', 'Close', 'Swing_High', 'Swing_Low', 'Structure', 'BOS', 'CHOCH']
            st.dataframe(analyzed_df[display_cols].tail(30), use_container_width=True)
            
        else:
            st.error("Lama helin wax xog ah ama khalad ayaa ka dhacay soo jiidashada xogta.")
else:
    st.info("👈 Fadlan ka dooro goobaha sidebar-ka kadibna guji badhanka **'Falanqee Suuqa'** si aad u bilowdo.")
            
