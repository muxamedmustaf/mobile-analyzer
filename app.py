import streamlit as st
import pandas as pd
from market_data import get_data
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from structure.market_structure import MarketStructureAnalyzer
from smc.order_blocks import detect_order_blocks
from smc.fvg import detect_fvg
from signals.signal import generate_signal
from charts.chart import plot_market_chart

# Page Configuration
st.set_page_config(page_title="Mobile Analyzer - yFinance", layout="wide")

st.title("📈 Mobile Analyzer: Forex & Crypto (yFinance)")

# Sidebar for settings
st.sidebar.header("Market Settings")

# 1. View-ga lagu qoro ama lagu doorto magaca lammaanaha (Symbol)
symbol = st.sidebar.text_input("Enter Market Symbol", value="EURUSD=X")

# 2. View-ga timeframe-ka lagu doorto
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "30m", "1h", "1d"], index=3)

# Soo jiidashada xogta iyadoo la adeegsanayo yfinance
@st.cache_data(ttl=60)
def load_market_data(sym, tf):
    df = get_data(symbol=sym, timeframe=tf, limit=100)
    return df

with st.spinner(f"Soo jiidashada xogta {symbol}..."):
    df = load_market_data(symbol, timeframe)

if df.empty:
    st.error(f"Lama helin xogta suuqa ee {symbol}. Fadlan hubi in magacu sax yahay (Tusaale: EURUSD=X ee Forex ama BTC-USD ee Crypto).")
else:
    # Xisaabinta Tilmaamayaasha (Indicators)
    df['ema_50'] = calculate_ema(df, 50)
    df['rsi'] = calculate_rsi(df, 14)
    df['atr'] = calculate_atr(df, 14)

    current_price = df['close'].iloc[-1]

    # Falanqaynta Qaab-dhismeedka (Structure) iyo SMC
    structure_analyzer = MarketStructureAnalyzer(df)
    market_analysis = structure_analyzer.analyze()

    order_blocks = detect_order_blocks(df)
    fvgs = detect_fvg(df)

    # Soo saarista Signal-ka
    signal = generate_signal(df, current_price)

    # Daabacaadda Natiijada UI-ga (Dashboard)
    st.subheader(f"Current Status for {symbol}")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Current Price", value=f"${current_price:,.4f}")
    with col2:
        st.metric(label="Market Trend", value=market_analysis.get("trend", "NEUTRAL"))
    with col3:
        st.metric(label="Generated Signal", value=signal)

    # Muujinta Jaantuska (Interactive Chart)
    st.subheader("Market Price Chart")
    plot_market_chart(df)

    # Faahfaahinta Dheeraadka ah
    with st.expander("View Raw Data & SMC Details"):
        st.write("Recent Candles Data:")
        st.dataframe(df.tail(10))
        
        st.write("Detected Order Blocks:", order_blocks)
        st.write("Detected Fair Value Gaps (FVG):", fvgs)

    st.success("App-ku wuxuu si guul leh uga shaqaynayaa xogta yfinance!")
    
