import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import run_full_analysis

st.set_page_config(page_title="Mobile Analyzer - Advanced Patterns", layout="centered")

# ==========================================================
# TOP BAR WITH UNDO BUTTON
# ==========================================================
col_top1, col_top2, col_top3 = st.columns([1, 6, 1])
with col_top1:
    if st.button("↩ تراجع"):
        st.toast("تم التراجع عن الإجراء الأخير بنجاح", icon="🔄")
with col_top2:
    st.markdown("<h3 style='text-align: center; margin: 0;'>محلل الأنماط الذكي</h3>", unsafe_allow_html=True)

# Generate dummy/sample dataframe for demonstration if no live data feed is connected
# (Replace this section with your live data loading mechanism if needed)
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
prices = 0.82 + np.cumsum(np.random.randn(100) * 0.002)
df_sample = pd.DataFrame({
    'Open': prices + 0.001,
    'High': prices + 0.003,
    'Low': prices - 0.003,
    'Close': prices
}, index=dates)

# Run full analysis via engine
analysis_result = run_full_analysis(df_sample)
df = analysis_result["df"]
pattern_name = analysis_result["pattern"]
final_signal = analysis_result["signal"]
match_pct = analysis_result["match_pct"]
rsi_val = df.iloc[-2]['RSI']
close_val = df.iloc[-2]['Close']
ema50_val = df.iloc[-2]['EMA50']
ema200_val = df.iloc[-2]['EMA200']

# Rule: Hide pattern name until complete
is_complete = pattern_name != "INCOMPLETE"
display_name = pattern_name if is_complete else "جاري بناء واكتشاف الهيكل (غير مكتمل)..."

# Order status post-signal
order_status = "لا توجد أوامر معلقة حالياً"
if is_complete and final_signal in ["STRONG BUY", "STRONG SELL"]:
    order_status = f"✅ تم تفعيل الأوامر المعلقة بنجاح | الدخول: {analysis_result['trigger']} | الهدف (TP): {analysis_result['tp']} | وقف الخسارة (SL): {analysis_result['sl']}"
elif is_complete:
    order_status = f"⏳ الهيكل مكتمل بنسبة {match_pct}%، في انتظار إغلاق الشمعة لتفعيل الأوامر."

# Signal Status Display Box
st.markdown(f"""
<div style="background-color: #fdf8e2; padding: 20px; border-radius: 12px; border: 1px solid #f9e2af; margin-top: 10px;">
    <span style="font-size: 14px; color: #856404; font-weight: bold;">SIGNAL STATUS</span>
    <h2 style="color: #d35400; margin: 5px 0;">🟡 {final_signal}</h2>
    <p style="font-size: 18px; color: #b7950b; font-weight: 600; margin: 0;">{display_name}</p>
</div>
""", unsafe_allow_html=True)

# Brief summary comment under the status window
st.info(f"📊 **موجز السوق:** {order_status} | مؤشر RSI: {rsi_val:.2f} | اتجاه المتوسطات: {'صاعد 🟢' if close_val > ema200_val else 'هابط 🔴'}")

# Execution Levels Header & Data
st.markdown("### Execution Levels")
col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
with col_lvl1:
    st.metric("🎯 Trigger", f"{analysis_result['trigger']}")
with col_lvl2:
    st.metric("🛑 Struct SL", f"{analysis_result['sl']}")
with col_lvl3:
    st.metric("🏆 Proj. TP", f"{analysis_result['tp']}")

# ==========================================================
# CHART RENDERING WITH EMAs (EMA50 & EMA200)
# ==========================================================
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'
))
fig.add_trace(go.Scatter(
    x=df.index, y=df['EMA50'], line=dict(color='blue', width=1.5), name='EMA 50'
))
fig.add_trace(go.Scatter(
    x=df.index, y=df['EMA200'], line=dict(color='orange', width=2), name='EMA 200'
))

fig.update_layout(
    title="NZDCAD Chart & Indicators",
    xaxis_rangeslider_visible=False,
    height=450,
    margin=dict(l=10, r=10, t=30, b=10)
)
st.plotly_chart(fig, use_container_width=True)
