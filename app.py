import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.market_data import fetch_market_data
from structure.market_structure import analyze_market_structure
from structure.patterns import detect_chart_patterns

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
    .card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">⚡ SMC Market Structure Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Falanqaynta Suuqa, Swings, BOS, CHOCH, iyo Istaraatiijiyadaha Ganacsiga</p>', unsafe_allow_html=True)

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
            # Falanqaynta Structure-ka iyo Patterns-ka
            df = analyze_market_structure(df)
            df = detect_chart_patterns(df) 
            
            latest_row = df.iloc[-1]
            top_patterns = latest_row.get('Top_3_Patterns', 'No Pattern Found')
            best_pattern = latest_row.get('Pattern', 'No Pattern')
            current_price = latest_row['Close']
            
            # --- QODOBKA 2AAD: GO'AAMINTA TREND-KA ---
            # Waxaan ku cabiraynaa EMA ama isbarbardhigga qiimaha iyo Swing-yada
            prev_price = df.iloc[-5]['Close'] if len(df) >= 5 else current_price
            is_uptrend = current_price >= prev_price
            trend_text = "🟢 Kor u socda (Bullish Trend)" if is_uptrend else "🔴 Hoos u socda (Bearish Trend)"
            
            # Soo bandhigidda xaaladda Trend-ka iyo Patterns-ka
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="card">
                        <h4>📊 Xaaladda Suuqa (Trend)</h4>
                        <p style="font-size: 1.2rem; font-weight: bold;">{trend_text}</p>
                        <p>Qiimaha Hadda: <b>{current_price:.4f}</b></p>
                    </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                    <div class="card">
                        <h4>🎯 Pattern-ka Ugu Sarreeya</h4>
                        <p style="font-size: 1.1rem; color: #FF4B4B; font-weight: bold;">{best_pattern}</p>
                        <p>Ixtimaalka Guud: {top_patterns.split('|')[0] if '|' in top_patterns else top_patterns}</p>
                    </div>
                """, unsafe_allow_html=True)

            # --- QODOBKA 3AAD: ISTARAATIIIJIYADDA GANACSIGA EE PATTERN-KA ---
            st.subheader("💡 Qorshaha Ganacsiga (Trading Plan & Execution)")
            
            # Xisaabinta loogiga saxda ah ee Entry, SL, iyo TP (iyadoo TP uu ka sarreeyo xaaladda Buy)
            if "Bottom" in best_pattern or "Inverse" in best_pattern or "Ascending" in best_pattern or "Bounce" in best_pattern:
                action = "BUY (Iibso)"
                entry_price = current_price
                stop_loss = current_price - (current_price * 0.005)  # 0.5% hoos
                take_profit = current_price + (current_price * 0.012) # 1.2% kor (TP waa ka sarreeyaa qiimaha)
                strat_desc = "Qaabkani wuxuu tilmaamayaa in suuqu ka helayo taageero hoose oo uu u jeesanayo kor u kac."
            elif "Top" in best_pattern or "Head and Shoulders" in best_pattern or "Descending" in best_pattern or "Wedge" in best_pattern:
                action = "SELL (Iibi / Gaab)"
                entry_price = current_price
                stop_loss = current_price + (current_price * 0.005)  # 0.5% kor
                take_profit = current_price - (current_price * 0.012) # 1.2% hoos
                strat_desc = "Qaabkani wuxuu tilmaamayaa cadaadis iib ah oo keeni kara in qiimuhu hoos u dhaco."
            else:
                action = "HOLD / WAIT (Sug inuu suuqu caddaado)"
                entry_price = current_price
                stop_loss = current_price * 0.99
                take_profit = current_price * 1.01
                strat_desc = "Suuqu wuxuu ku jiraa xaalad dhex-dhexaad ah (Consolidation)."

            st.info(f"""
            * **Tallaabada la qaadayo:** **{action}**
            * **Qiimaha la galayo (Entry):** `{entry_price:.4f}`
            * **Khasaaraha la xirayo (Stop Loss - SL):** `{stop_loss:.4f}`
            * **Faa'iidada la beegsanayo (Take Profit - TP):** `{take_profit:.4f}`
            * **Faahfaahin:** {strat_desc}
            """)

            # --- QODOBKA 1AAD: SHAADHA CANDLESTICK OO WADATA PRICE LINE (TRADINGVIEW STYLE) ---
            annotations_list = []
            
            if best_pattern != 'No Pattern':
                arrow_color = "#00E676" if "BUY" in action or "Bottom" in best_pattern else "#FF1744"
                annotations_list.append(go.layout.Annotation(
                    x=df.index[-1],
                    y=current_price,
                    xref="x",
                    yref="y",
                    text=f"⭐ {best_pattern} ({action.split()[0]})",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowcolor=arrow_color,
                    ax=0,
                    ay=-50,
                    bgcolor="rgba(0,0,0,0.85)",
                    bordercolor=arrow_color,
                    borderwidth=1.5,
                    borderpad=5,
                    font=dict(size=11, color="#FFFFFF")
                ))

            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Candlestick"
            )])
            
            # Ku darista xariiqda qiimaha taagan ee dhinaca midig (TradingView Style Last Price Line)
            fig.add_hline(
                y=current_price, 
                line_dash="dot", 
                line_color="#00E676" if is_uptrend else "#FF1744",
                annotation_text=f"Hadda: {current_price:.4f}", 
                annotation_position="bottom right"
            )
            
            fig.update_layout(
                title=f"Shaxda Suuqa ee {symbol} (TradingView Style)",
                xaxis_title="Wakhtiga",
                yaxis_title="Qiimaha (Price)",
                template="plotly_dark",
                height=600,
                annotations=annotations_list,
                yaxis=dict(tickformat=".4f", side="right") # Xariiqda qiimaha iyo lambarada oo dhinaca midig la geeyay
            )
            
            st.plotly_chart(fig, use_container_width=True)
                
