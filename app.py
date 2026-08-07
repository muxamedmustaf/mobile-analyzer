import streamlit as st
import plotly.graph_objects as go

from data.market_data import fetch_market_data
from pattern_engine import analyze_market


# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(
    page_title="SMC Market Structure AI",
    page_icon="⚡",
    layout="wide"
)


# ===============================
# STYLE
# ===============================

st.markdown(
    """
    <style>
    .main-title {
        font-size:2.2rem;
        text-align:center;
        font-weight:bold;
        color:#FF4B4B;
    }
    .card {
        background:#1e1e1e;
        padding:15px;
        border-radius:10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    '<p class="main-title">⚡ SMC Market Structure Engine AI</p>',
    unsafe_allow_html=True
)


# ===============================
# SIDEBAR
# ===============================

st.sidebar.header("⚙️ Market Settings")


symbol = st.sidebar.text_input(
    "Symbol",
    value="GC=F"
)


interval = st.sidebar.selectbox(
    "Interval",
    [
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d"
    ],
    index=5
)


period = st.sidebar.selectbox(
    "Period",
    [
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y"
    ],
    index=3
)


run = st.sidebar.button(
    "🚀 Analyze"
)



# ===============================
# ANALYSIS
# ===============================

if run:

    with st.spinner("Analyzing market..."):


        df = fetch_market_data(
            symbol,
            interval,
            period
        )


        if df.empty:

            st.error(
                "No market data found"
            )


        else:


            result = analyze_market(df)


            last_price = df["Close"].iloc[-1]



            col1, col2, col3 = st.columns(3)


            with col1:

                st.markdown(
                    f"""
                    <div class="card">

                    <h4>📈 Signal</h4>

                    <h2>{result['signal']}</h2>

                    </div>
                    """,
                    unsafe_allow_html=True
                )



            with col2:

                st.markdown(
                    f"""
                    <div class="card">

                    <h4>🎯 Pattern</h4>

                    <h3>{result['pattern']}</h3>

                    </div>
                    """,
                    unsafe_allow_html=True
                )



            with col3:

                st.markdown(
                    f"""
                    <div class="card">

                    <h4>Confidence</h4>

                    <h3>{result['confidence']}%</h3>

                    </div>
                    """,
                    unsafe_allow_html=True
                )



            # ===============================
            # STRUCTURE INFO
            # ===============================


            st.subheader(
                "Market Structure"
            )


            st.write(
                {
                    "Trend": result.get("trend"),
                    "Structure": result.get("structure"),
                    "BOS": result.get("BOS"),
                    "CHOCH": result.get("CHOCH")
                }
            )



            # ===============================
            # CHART
            # ===============================


            fig = go.Figure()


            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="Price"
                )
            )


            fig.add_hline(
                y=last_price,
                annotation_text=f"Price {last_price}"
            )


            fig.update_layout(
                template="plotly_dark",
                height=650,
                xaxis_rangeslider_visible=False
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


            # raw result

            st.subheader(
                "Engine Output"
            )

            st.json(result)
