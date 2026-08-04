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

# Liiska lammaanaha Forex ee background-ka lagu baarayo
DEFAULT_FOREX_LIST = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDJPY=X", "USDCAD=X", "NZDUSD=X", "EURJPY=X"]

# Navigation mode: Laba qaybood (Scanner-ka tooska ah iyo Single Chart View)
app_mode = st.sidebar.radio("Navigation", ["Market Scanner (Fursadaha Otomaatigga ah)", "Single Chart Analysis"])

@st.cache_data(ttl=60)
def load_market_data(sym, tf):
    df = get_data(symbol=sym, timeframe=tf, limit=100)
    return df

if app_mode == "Market Scanner (Fursadaha Otomaatigga ah)":
    st.subheader("🔍 Live Market Opportunity Scanner (Auto-Scan)")
    st.write("App-ku wuxuu si toos ah u baarayay suuqa... Halkan waxaa ka muuqda lammaanaha fursadaha leh:")
    
    timeframe = st.selectbox("Select Scan Timeframe", ["15m", "30m", "1h", "1d"], index=1)
    
    # Otomaatig ah: Si toos ah ayuu u baaraa adigoo aan badhan sugin markuu app-ku furmo ama refresh noqdo
    scanner_results = []
    
    with st.spinner("Waa la baaraa lammaanayaasha Forex-ka... Fadlan sug."):
        for sym in DEFAULT_FOREX_LIST:
            try:
                temp_df = get_data(symbol=sym, timeframe=timeframe, limit=100)
                if not temp_df.empty:
                    signal_result = generate_signal(temp_df)  # Hubinta signal-ka
                    
                    if signal_result in ["BUY", "SELL"]:
                        scanner_results.append({
                            "Symbol": sym,
                            "Signal": signal_result,
                            "Price": temp_df['Close'].iloc[-1]
                        })
            except Exception as e:
                continue
    
    if scanner_results:
        result_df = pd.DataFrame(scanner_results)
        st.success("✨ Waxaa la helay lammaanayaal fursad wata!")
        
        # Soo bandhigida miiska oo leh badhamo toos ah oo kuu furaya chart-ka
        for index, row in result_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                st.write(f"**{row['Symbol']}**")
            with col2:
                st.write(f"Signal: **{row['Signal']}**")
            with col3:
                st.write(f"Price: {row['Price']:.4f}")
            with col4:
                if st.button(f"View Chart", key=f"btn_{row['Symbol']}"):
                    st.session_state['selected_symbol'] = row['Symbol']
                    # Si toos ah ugu beddel bogga Single Chart Analysis
                    st.rerun()
    else:
        st.info("Waqtigan xaadirka ah lammaane soo saaray BUY ola SELL ma jiro. Waa la sii wadi doonaa baaritaanka.")

else:
    # Sidebar for settings (Muraayaddii faahfaahinta iyo chart-ka ee quruxda badneyd)
    st.sidebar.header("Market Settings")

    # Haddii laga soo doortay scanner-ka, halkaan ayay si otomaatig ah ugu soo gelaysaa
    default_sym = st.session_state.get('selected_symbol', "EURUSD=X")
    symbol = st.sidebar.text_input("Enter Market Symbol", value=default_sym)

    timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "30m", "1h", "1d"], index=3)

    with st.spinner(f"Soo jiidashada xogta {symbol}..."):
        df = load_market_data(symbol, timeframe)

    if df.empty:
        st.warning(f"Lama helin xog ku saabsan lammaanaha {symbol}. Fadlan hubi magaca.")
    else:
        st.success(f"Xogta lammaanaha {symbol} waa la helay!")
        
        # Halkan geli koodkaagii hore ee falanqaynta, SMC, iyo plot_market_chart...
        # tusaale ahaan:
        # plot_market_chart(df, symbol)
        
