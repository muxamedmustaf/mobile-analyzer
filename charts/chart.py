import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def plot_market_chart(df, symbol="Market"):
    """Muujinta jaantusyada suuqa iyadoo la baarayo xogta"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("Ma jirto xog sugan oo loo isticmaalo Chart-ka.")
        return

    # Si aad u aragto xogta dhabta ah ee soo gasha shaashaddaada
    with st.expander("Debug: Eeg xogta DataFrame-ka"):
        st.write(df.head())
        st.write(df.columns)

    # Helida tiirarka iyadoo la raadinayo xarfaha yar ama weyn
    cols = {str(col).lower(): col for col in df.columns}
    
    open_col = cols.get('open')
    high_col = cols.get('high')
    low_col = cols.get('low')
    close_col = cols.get('close')

    # Haddii aysan si toos ah u helin, isticmaal tiirarka 0, 1, 2, 3
    if not open_col or not high_col or not low_col or not close_col:
        if len(df.columns) >= 4:
            open_col, high_col, low_col, close_col = df.columns[0], df.columns[1], df.columns[2], df.columns[3]
        else:
            st.error(f"Tiirarka xogta lama helin si sax ah. Tiirarka jira waa: {list(df.columns)}")
            return

    x_vals = df.index if hasattr(df, 'index') else list(range(len(df)))

    fig = go.Figure(data=[go.Candlestick(
        x=x_vals,
        open=df[open_col],
        high=df[high_col],
        low=df[low_col],
        close=df[close_col]
    )])
    
    fig.update_layout(
        title=f"Mobile Analyzer - Live Chart ({symbol})", 
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
    
