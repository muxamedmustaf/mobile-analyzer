import streamlit as st
import pandas as pd
from data.market_data import fetch_coinex_kline
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from structure.market_structure import MarketStructureAnalyzer
from smc.order_blocks import detect_order_blocks
from smc.fvg import detect_fvg
from smc.premium_discount import calculate_premium_discount
from signals.signal import generate_signal
from charts.chart import plot_market_chart

# Page Configuration
st.set_page_config(page_title="Mobile Analyzer - CoinEx Live", layout="wide")

st.title("📈 Mobile Analyzer: Live Market Strategy (CoinEx)")

# Sidebar for settings
st.sidebar.header("Market Settings")
# Waxaad dooran kartaa suuqyada caanka ah ee CoinEx (Tusaale: BTCUSDT, ETHUSDT, XRPUSDT)
market_symbol = st.sidebar.selectbox("Select Market Pair", ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"])
timeframe = st.sidebar.selectbox("Select Timeframe", ["5min", "15min", "30min", "1hour", "4hour", "1day"], index=2)

# Soo jiidashada xogta adigoo isticmaalaya CoinEx API
@st.cache_data(ttl=60) # Xogta waxay cusboonaysmaysaa daqiiqad kasta
def load_market_data(market, interval):
    df = fetch_coinex_kline(market=market, interval=interval, limit=100)
    return df

with st.spinner(f"Soo jiidashada xogta {market_symbol}..."):
    df = load_market_data(market_symbol, timeframe)

if df.empty:
       st.error(f"Lama helin xogta suuqa ee {market_symbol}. Fadlan hubi xiriirkaaga internetka ama suuqa la doortay.")
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
       st.subheader(f"Current Status for {market_symbol}")
       col1, col2, col3 = st.columns(3)

       with col1:
           st.metric(label="Current Price", value=f"${current_price:,.2f}")
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

       st.success("Mashruucu wuxuu si buuxda uga shaqaynayaa xogta nolosha ee CoinEx!")
           
