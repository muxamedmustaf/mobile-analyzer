import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def plot_market_chart(df, symbol="Market"):
    """Muujinta jaantusyada suuqa ee Streamlit oo badbaado leh"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("Ma jirto xog sugan oo loo isticmaalo Chart-ka.")
        return

    # Hubinta badbaadada leh ee index-ka iyo x-axis
    x_vals = df.index if hasattr(df, 'index') else list(range(len(df)))
    
    # Helida magacyada tiirarka si dhab ah iyadoo la isticmaalayo dict ama list comprehension
    cols = {str(col).lower(): col for col in df.columns}
    
    open_col = cols.get('open', df.columns[0] if len(df.columns) > 0 else None)
    high_col = cols.get('high', df.columns[1] if len(df.columns) > 1 else None)
    low_col = cols.get('low', df.columns[2] if len(df.columns) > 2 else None)
    close_col = cols.get('close', df.columns[3] if len(df.columns) > 3 else None)

    if not open_col or not high_col or not low_col or not close_col:
        st.error("Tiirarka xogta candlestick lama helin si sax ah.")
        return

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
    
