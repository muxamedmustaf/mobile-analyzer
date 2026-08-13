import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# استدعاء المحرك المبرمج (يدعم كلا الاسمين pattern_engine أو engine)
try:
    from pattern_engine import run_full_analysis
except ImportError:
    from engine import run_full_analysis

# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="SMC & Indicator Pattern Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Financial Market Pattern & Indicator Scanner")
st.write("الواجهة الكاملة لتحليل الأنماط الفنية والمؤشرات عبر جميع الإطارات الزمنية وجلب أكبر عدد من الشموع.")

# ==========================================================
# 2. SIDEBAR - ALL TIMEFRAMES & MAXIMUM CANDLES LOOKBACK
# ==========================================================
st.sidebar.header("⚙️ إعدادات السوق والإطارات الزمنية")
symbol = st.sidebar.text_input("رمز الأداة المالية (Ticker):", "XAUUSD=X")

# جميع الإطارات الزمنية المتاحة
timeframe = st.sidebar.selectbox(
    "الإطار الزمني (Timeframe):",
    ["1m", "2m", "5m", "15m", "30m", "60m", "1h", "1d", "1wk", "1mo"],
    index=7  # الافتراضي 1d
)

# اختيار جلب أكبر عدد من الشموع التاريخية
period = st.sidebar.selectbox(
    "نطاق الشموع التاريخية (Lookback Period):",
    ["max", "5y", "2y", "1y", "6d", "60d", "1mo", "7d"],
    index=0  # الافتراضي max لجلب أقصى عدد شموع ممكن
)

st.sidebar.markdown("---")
st.sidebar.info("""
**الشروط المشددة المفعلة 100%:**
- 15 نمطاً هندسياً للشارت
- EMA 200 & EMA 50 للاتجاه
- RSI في النطاق (30 - 70)
- كسر / اختراق المستويات الهيكلية
""")

# ==========================================================
# 3. MAIN SCANNER EXECUTION
# ==========================================================
if st.sidebar.button("🚀 تشغيل الفحص الشامل (Run Scan)"):
    with st.spinner("جاري جلب أقصى عدد من الشموع وتحليل البيانات..."):
        
        # جلب البيانات من yfinance بالاعتماد على التايم فريم والماكس period
        try:
            df = yf.download(symbol, period=period, interval=timeframe)
        except Exception as e:
            df = pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 14:
            st.error("⚠️ لم يتم جلب البيانات أو أن عدد الشموع غير كافٍ لهذا الإطار الزمني. يرجى اختيار إطار زمني أو فترة مختلفة.")
        else:
            # تشغيل محرك التحليل
            result = run_full_analysis(df)
            df_res = result['df']
            total_candles = len(df_res)

            # ----------------------------------------------------
            # A. SIGNAL STATUS & CANDLE COUNT
            # ----------------------------------------------------
            st.markdown(f"### 🎯 حالة الإشارة (إجمالي الشموع التي تم جلبها: `{total_candles}` شمعة)")
            
            signal = result['signal']
            if signal == "STRONG BUY":
                st.success(f"### 🟢 SIGNAL: STRONG BUY | Pattern: {result['pattern']}")
            elif signal == "STRONG SELL":
                st.error(f"### 🔴 SIGNAL: STRONG SELL | Pattern: {result['pattern']}")
            else:
                st.warning(f"### 🟡 STATUS: {signal} | Pattern: {result['pattern']}")

            st.caption(f"**تفاصيل التفعيل / الرفض:** {result['reason']}")

            # ----------------------------------------------------
            # B. ABSOLUTE TRADE EXECUTION LEVELS
            # ----------------------------------------------------
            st.markdown("#### 📐 مستويات الدخول والأهداف المباشرة (Absolute Levels)")
            e1, e2, e3 = st.columns(3)
            
            if signal in ["STRONG BUY", "STRONG SELL"]:
                e1.metric("🎯 سعر الدخول (Entry Price)", f"{result['entry']}")
                e2.metric("🛑 وقف الخسارة (Stop Loss)", f"{result['sl']}")
                e3.metric("🏆 هدف الربح (Take Profit 1:2)", f"{result['tp']}")
            else:
                e1.metric("🎯 سعر الدخول", "في انتظار الشروط...")
                e2.metric("🛑 وقف الخسارة", "N/A")
                e3.metric("🏆 هدف الربح", "N/A")

            # ----------------------------------------------------
            # C. CURRENT INDICATOR METRICS
            # ----------------------------------------------------
            st.markdown("#### 📊 قيم المؤشرات الحالية")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("سعر الإغلاق", f"{result['close']}")
            m2.metric("EMA 50", f"{result['ema50']}")
            m3.metric("EMA 200", f"{result['ema200']}")
            m4.metric("RSI (14)", f"{result['rsi']}")

            # ----------------------------------------------------
            # D. FULL INTERACTIVE PLOTLY CHART
            # ----------------------------------------------------
            st.markdown("### 📈 الرسم البياني والمستويات الهيكلية")

            fig = go.Figure()

            # Candlesticks
            fig.add_trace(go.Candlestick(
                x=df_res.index,
                open=df_res['Open'],
                high=df_res['High'],
                low=df_res['Low'],
                close=df_res['Close'],
                name="الشموع اليابانية"
            ))

            # EMA 50
            if 'EMA50' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA50'],
                    line=dict(color='orange', width=1.5), name="EMA 50"
                ))

            # EMA 200
            if 'EMA200' in df_res.columns:
                fig.add_trace(go.Scatter(
                    x=df_res.index, y=df_res['EMA200'],
                    line=dict(color='deepskyblue', width=2), name="EMA 200"
                ))

            # Structural Pivots H & L
            if 'Pivot_H' in df_res.columns and 'Pivot_L' in df_res.columns:
                pivots_h = df_res.dropna(subset=['Pivot_H'])
                pivots_l = df_res.dropna(subset=['Pivot_L'])

                fig.add_trace(go.Scatter(
                    x=pivots_h.index, y=pivots_h['Pivot_H'],
                    mode='markers', marker=dict(symbol='triangle-down', size=11, color='red'),
                    name="مقاومة هيكلية (H)"
                ))

                fig.add_trace(go.Scatter(
                    x=pivots_l.index, y=pivots_l['Pivot_L'],
                    mode='markers', marker=dict(symbol='triangle-up', size=11, color='green'),
                    name="دعم هيكلي (L)"
                ))

            fig.update_layout(
                title=f"{symbol} - الشارت على إطار ({timeframe}) | عدد الشموع: {total_candles}",
                xaxis_title="التاريخ / الوقت",
                yaxis_title="السعر",
                template="plotly_dark",
                height=650,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
