import streamlit as st
import plotly.graph_objects as go

def plot_market_chart(df, symbol="Market"):
    """Muujinta jaantusyada suuqa ee Streamlit"""
    if df is None or df.empty:
        st.warning("Ma jirto xog lagu soosaaro Chart-ka.")
        return

    # Hubinta in tiirarka la helay
    x_vals = df.index if not isinstance(df.index, range) else df.iloc[:, 0]
    
    # Hubinta magacyada tiirarka xarfaha yar ama weyn
    open_col = 'open' if 'open' in df.columns else ('Open' if 'Open' in df.columns else df.columns[0])
    high_col = 'high' if 'high' in df.columns else ('High' if 'High' in df.columns else df.columns[1])
    low_col = 'low' if 'low' in df.columns else ('Low' if 'Low' in df.columns else df.columns[2])
    close_col = 'close' if 'close' in df.columns else ('Close' if 'Close' in df.columns else df.columns[3])

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
    
