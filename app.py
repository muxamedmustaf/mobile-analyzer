import streamlit as st
import pandas as pd
from data.market_data import fetch_market_data
from structure.swings import detect_swings

# Dejinta bogga Streamlit
st.set_page_config(page_title="Market Structure AI", page_icon="📈", layout="wide")

st.title("🚀 Market Structure AI - Engine")
st.write("Marxaladda 1: Ogaanshaha Swings (Swing High & Swing Low)")

# Qeybta dhinaca (Sidebar) ee kontoroolka
st.sidebar.header("Goobaha Xogta (Settings)")
symbol = st.sidebar.text_input("Calaamada Suuqa (Symbol)", value="GC=F")
interval = st.sidebar.selectbox("Furan (Interval)", ["15m", "30m", "1h", "4h"], index=1)
period = st.sidebar.selectbox("Mudada (Period)", ["1d", "5d", "1mo"], index=1)

if st.sidebar.button("Soo Jiido Xogta & Falanqee"):
    with st.spinner("Falanqaynaya suuqa..."):
        # 1. Soo qaadashada xogta
        df = fetch_market_data(symbol=symbol, interval=interval, period=period)
        
        if not df.empty:
            # 2. Ogaanshaha Swings
            analyzed_df = detect_swings(df)
            
            st.success("Xogta si guul leh ayaa loo falanqeeyay!")
            
            # Soo bandhigida shaxda (Chart / Table)
            st.subheader("Xogta Suuqa & Swings")
            st.dataframe(analyzed_df.tail(20))
            
            # Muujinta jaantus fudud (Line Chart) oo wata qiimaha Close-ka
            st.subheader("Jaantuska Qiimaha (Close Price)")
            st.line_chart(analyzed_df['Close'])
        else:
            st.error("Lama helin wax xog ah ama khalad ayaa dhacay.")
else:
    st.info("Guji badhanka 'Soo Jiido Xogta & Falanqee' si aad u bilowdo falanqaynta.")
    
