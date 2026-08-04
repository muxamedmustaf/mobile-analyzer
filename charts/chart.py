import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def plot_market_chart(df, symbol="Market"):
    """Muujinta jaantusyada suuqa oo qaabilsan dib-u-habaynta xogta"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("Ma jirto xog sugan oo loo isticmaalo Chart-ka.")
        return

    # Haddii tiirarku yihiin MultiIndex (oo ka yimaada yfinance mararka qaar), nadiifi
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_0()

    # Ka dhig dhammaan magacyada tiirarka kuwa yaryar si loo helo si fudud
    df.columns = [str(c).lower() for c in df.columns]

    # Hubinta tiirarka asaasiga ah
    required = ['open', 'high', 'low', 'close']
    for col in required:
        if col not in df.columns:
            # Haddii la waayo, ka raadi magacyo kale ama isticmaal tiirarka ugu dhow
            matching = [c for c in df.columns if col in c]
            if matching:
                df[col] = df[matching[0]]
            else:
                st.error(f"Tiirka {col} lama helin xogta dhexdeeda. Tiirarka jira waa: {list(df.columns)}")
                return

    x_vals = df.index if hasattr(df, 'index') else list(range(len(df)))

    fig = go.Figure(data=[go.Candlestick(
        x=x_vals,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    
    fig.update_layout(
        title=f"Mobile Analyzer - Live Chart ({symbol})", 
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
    
