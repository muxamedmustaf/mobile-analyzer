import streamlit as st
import plotly.graph_objects as go

def plot_market_chart(df):
    """Muujinta jaantusyada suuqa ee Streamlit"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    fig.update_layout(title="Mobile Analyzer - Live Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)
  
