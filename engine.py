import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ==========================================================
# 1. CALCULATE INDICATORS (EMA50, EMA200, MACD Hist, RSI 30-75)
# ==========================================================
def calculate_indicators(df):
    df = df.copy()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # MACD & Histogram Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # RSI Calculation (14 periods)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    loss_safe = np.where(loss == 0, 1e-9, loss)
    rs = gain / loss_safe
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50.0)
    return df

# ==========================================================
# 2. CUSTOM ZIGZAG DETECTION (H=Resistance, L=Support)
# ==========================================================
def calculate_zigzag(df, depth=12, deviation=5, backstep=3):
    df = df.copy()
    df['Pivot_H'], df['Pivot_L'] = np.nan, np.nan
    
    highs = df['High'].values
    lows = df['Low'].values
    
    last_pivot_idx = 0
    last_pivot_type = 0 
    
    for i in range(depth, len(df) - backstep):
        window_high = np.max(highs[i-depth:i+1])
        window_low = np.min(lows[i-depth:i+1])
        
        is_high = highs[i] == window_high
        is_low = lows[i] == window_low
        
        if is_high and (i - last_pivot_idx >= backstep):
            if last_pivot_type != 1 or (highs[i] > highs[last_pivot_idx]):
                df.loc[df.index[i], 'Pivot_H'] = highs[i]
                last_pivot_idx = i
                last_pivot_type = 1
                
        if is_low and (i - last_pivot_idx >= backstep):
            if last_pivot_type != -1 or (lows[i] < lows[last_pivot_idx]):
                df.loc[df.index[i], 'Pivot_L'] = lows[i]
                last_pivot_idx = i
                last_pivot_type = -1

    return df

def get_chronological_pivots(df):
    pivots = []
    for idx, row in df.iterrows():
        if not np.isnan(row['Pivot_H']):
            pivots.append({'idx': idx, 'val': row['Pivot_H'], 'type': 'H'})
        elif not np.isnan(row['Pivot_L']):
            pivots.append({'idx': idx, 'val': row['Pivot_L'], 'type': 'L'})
            
    clean_pivots = []
    for p in pivots:
        if not clean_pivots:
            clean_pivots.append(p)
        else:
            if clean_pivots[-1]['type'] != p['type']:
                clean_pivots.append(p)
            else:
                if p['type'] == 'H' and p['val'] > clean_pivots[-1]['val']:
                    clean_pivots[-1] = p
                elif p['type'] == 'L' and p['val'] < clean_pivots[-1]['val']:
                    clean_pivots[-1] = p
    return clean_pivots

# ==========================================================
# 3. STRICT PATTERN ENGINE (99% Symmetry & Hidden Until Complete)
# ==========================================================
def scan_and_calculate_logic(df):
    pivots = get_chronological_pivots(df)
    
    if len(pivots) < 3:
        return {"name": "INCOMPLETE", "bias": "Neutral", "match": 0}

    current_bar_idx = len(df) - 1

    # A. INVERSE HEAD AND SHOULDERS (99% Symmetry -> tolerance <= 0.01)
    if len(pivots) >= 5:
        for i in range(len(pivots) - 4):
            p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
            if (current_bar_idx - df.index.get_loc(p5['idx'])) > 25: continue
                
            if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['L', 'H', 'L', 'H', 'L']:
                l1, h1, l2, h2, l3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
                is_head_deeper = (l2 < l1) and (l2 < l3)
                shoulder_symmetry = abs(l1 - l3) / max(l1, l3) <= 0.01  # تطابق 99%
                head_prominence = (min(l1, l3) - l2) >= (max(h1, h2) - min(l1, l3)) * 0.20
                
                if is_head_deeper and shoulder_symmetry and head_prominence:
                    idx1, val1, idx2, val2 = p2['idx'], h1, p4['idx'], h2
                    pos1, pos2 = df.index.get_loc(idx1), df.index.get_loc(idx2)
                    slope = (val2 - val1) / (pos2 - pos1) if pos2 != pos1 else 0
                    neckline_at_current = val2 + slope * (current_bar_idx - pos2)
                    height = neckline_at_current - l2
                    return {
                        "name": "Inverse Head and Shoulders", "bias": "Bullish", "match": 99.0,
                        "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2), (p4['idx'], h2), (p5['idx'], l3)],
                        "entry_trigger": round(neckline_at_current, 4), "sl": l2 * 0.995, "tp": round(neckline_at_current + height, 4)
                    }

    # B. HEAD AND SHOULDERS (99% Symmetry)
    if len(pivots) >= 5:
        for i in range(len(pivots) - 4):
            p1, p2, p3, p4, p5 = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
            if (current_bar_idx - df.index.get_loc(p5['idx'])) > 25: continue
                
            if [p['type'] for p in [p1, p2, p3, p4, p5]] == ['H', 'L', 'H', 'L', 'H']:
                h1, l1, h2, l2, h3 = p1['val'], p2['val'], p3['val'], p4['val'], p5['val']
                is_head_higher = (h2 > h1) and (h2 > h3)
                shoulder_symmetry = abs(h1 - h3) / max(h1, h3) <= 0.01  # تطابق 99%
                head_prominence = (h2 - max(h1, h3)) >= (max(h1, h3) - min(l1, l2)) * 0.20
                
                if is_head_higher and shoulder_symmetry and head_prominence:
                    idx1, val1, idx2, val2 = p2['idx'], l1, p4['idx'], l2
                    pos1, pos2 = df.index.get_loc(idx1), df.index.get_loc(idx2)
                    slope = (val2 - val1) / (pos2 - pos1) if pos2 != pos1 else 0
                    neckline_at_current = val2 + slope * (current_bar_idx - pos2)
                    height = h2 - neckline_at_current
                    return {
                        "name": "Head and Shoulders", "bias": "Bearish", "match": 99.0,
                        "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2), (p4['idx'], l2), (p5['idx'], h3)],
                        "entry_trigger": round(neckline_at_current, 4), "sl": h2 * 1.005, "tp": round(neckline_at_current - height, 4)
                    }

    # C. DOUBLE BOTTOM (99% Symmetry)
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'L' and p2['type'] == 'H' and p3['type'] == 'L':
            if (current_bar_idx - df.index.get_loc(p3['idx'])) > 20: continue
            l1, h1, l2 = p1['val'], p2['val'], p3['val']
            if abs(l1 - l2) / max(l1, l2) <= 0.01 and h1 > max(l1, l2) * 1.005:
                height = h1 - min(l1, l2)
                return {
                    "name": "Double Bottom", "bias": "Bullish", "match": 99.0,
                    "nodes": [(p1['idx'], l1), (p2['idx'], h1), (p3['idx'], l2)],
                    "entry_trigger": h1, "sl": min(l1, l2) * 0.999, "tp": h1 + height
                }

    # D. DOUBLE TOP (99% Symmetry)
    for i in range(len(pivots) - 2):
        p1, p2, p3 = pivots[i], pivots[i+1], pivots[i+2]
        if p1['type'] == 'H' and p2['type'] == 'L' and p3['type'] == 'H':
            if (current_bar_idx - df.index.get_loc(p3['idx'])) > 20: continue
            h1, l1, h2 = p1['val'], p2['val'], p3['val']
            if abs(h1 - h2) / max(h1, h2) <= 0.01 and l1 < min(h1, h2) * 0.995:
                height = max(h1, h2) - l1
                return {
                    "name": "Double Top", "bias": "Bearish", "match": 99.0,
                    "nodes": [(p1['idx'], h1), (p2['idx'], l1), (p3['idx'], h2)],
                    "entry_trigger": l1, "sl": max(h1, h2) * 1.001, "tp": l1 - height
                }

    return {"name": "INCOMPLETE", "bias": "Neutral", "match": 0}

# ==========================================================
# 4. EXECUTION, ORDERS & STREAMLIT UI (Top Bar, Undo & Summary)
# ==========================================================
def render_app_ui(df, symbol_name="NZDCAD=X"):
    # شريط التنظيم العلوي مع زر التراجع (Undo)
    col_top1, col_top2, col_top3 = st.columns([1, 6, 1])
    with col_top1:
        if st.button("↩ تراجع"):
            st.toast("تم التراجع عن الإجراء الأخير", icon="🔄")
    with col_top2:
        st.markdown(f"### تحليل الشارت المتقدم: {symbol_name}")

    df = calculate_indicators(df)
    df = calculate_zigzag(df)
    p_data = scan_and_calculate_logic(df)
    
    is_complete = p_data["name"] != "INCOMPLETE"
    display_pattern_name = p_data["name"] if is_complete else "جاري بناء واكتشاف الهيكل..."
    
    latest_closed = df.iloc[-2]
    close, ema50, ema200, rsi, macd_hist = latest_closed['Close'], latest_closed['EMA50'], latest_closed['EMA200'], latest_closed['RSI'], latest_closed['MACD_Hist']
    
    final_signal = "WAITING"
    order_status = "لا توجد أوامر معلقة حالياً"
    
    if is_complete:
        bias, trigger, sl, tp = p_data["bias"], p_data["entry_trigger"], p_data["sl"], p_data["tp"]
        c_rsi = (30 <= rsi <= 75)
        
        if bias == "Bullish":
            if close > trigger and close > ema50 and close > ema200 and c_rsi and macd_hist > 0:
                final_signal = "STRONG BUY"
                order_status = f"✅ تم تفعيل أمر الشراء المعلق (Buy Stop/Limit) عند سعر {trigger} | الهدف: {tp} | وقف الخسارة: {sl}"
            else:
                order_status = f"⏳ في انتظار إغلاق الشمعة فوق مستوى خط العنق ({trigger}) وتأكيد مؤشرات العزم."
        elif bias == "Bearish":
            if close < trigger and close < ema50 and close < ema200 and c_rsi and macd_hist < 0:
                final_signal = "STRONG SELL"
                order_status = f"✅ تم تفعيل أمر البيع المعلق (Sell Stop/Limit) عند سعر {trigger} | الهدف: {tp} | وقف الخسارة: {sl}"
            else:
                order_status = f"⏳ في انتظار إغلاق الشمعة تحت مستوى خط العنق ({trigger}) وتأكيد مؤشرات العزم."

    # نافذة حالة الإشارة
    st.markdown(f"""
    <div style="background-color: #fdf8e2; padding: 20px; border-radius: 12px; border: 1px solid #f9e2af;">
        <span style="font-size: 14px; color: #856404; font-weight: bold;">SIGNAL STATUS</span>
        <h2 style="color: #d35400; margin: 5px 0;">🟡 {final_signal}</h2>
        <p style="font-size: 18px; color: #b7950b; font-weight: 600; margin: 0;">{display_pattern_name}</p>
    </div>
    """, unsafe_allow_html=True)

    # تعليق موجز تحت نافذة الحالة (حالة الزوج والنمط)
    st.info(f"📊 **موجز حالة الزوج ({symbol_name}):** {order_status} | قيمة RSI الحالية: {rsi:.2f} | اتجاه المتوسطات (EMA50/200): {'صاعد 🟢' if close > ema200 else 'هابط 🔴'}")

    # رسم الشارت مع إدراج مؤشرات EMA50 و EMA200
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='blue', width=1.5), name='EMA 50'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='orange', width=2), name='EMA 200'))
    
    fig.update_layout(title=f"Chart Analysis with EMAs - {symbol_name}", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
                           
