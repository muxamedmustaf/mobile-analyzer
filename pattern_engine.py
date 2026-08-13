# pattern_engine.py
import pandas as pd
import numpy as np
import talib
from scipy.signal import find_peaks

def detect_patterns(df):
    """
    محرك كشف النماذج مع رسم الخط البصري الكامل للنموذج (من البداية للنهاية)،
    وخط الكسر (Neckline)، وخطوط الهدف والوقف بأسعار مطلقة.
    """
    patterns = []
    if df is None or len(df) < 20:
        return patterns

    # توحيد أسماء الأعمدة لتفادي أخطاء الأحرف الكبيرة والصغيرة
    df_work = df.copy()
    df_work.columns = [c.lower() for c in df_work.columns]

    highs = df_work['high'].values
    lows = df_work['low'].values
    closes = df_work['close'].values
    indices = df_work.index

    # حساب المؤشرات الفنية الإلزامية (EMA 50, EMA 200, RSI 14)
    try:
        ema50 = talib.EMA(closes, timeperiod=min(50, len(closes)-1))
        ema200 = talib.EMA(closes, timeperiod=min(200, len(closes)-1))
        rsi = talib.RSI(closes, timeperiod=14)
    except Exception:
        ema50 = np.full_like(closes, np.nan)
        ema200 = np.full_like(closes, np.nan)
        rsi = np.full_like(closes, 50.0)

    # تحديد القمم والقيعان الرئيسية
    peaks, _ = find_peaks(highs, distance=5)
    troughs, _ = find_peaks(-lows, distance=5)

    curr_price = closes[-1]
    curr_idx = indices[-1]

    # ============================================================
    # 1. نموذج القاع المزدوج (Double Bottom - W Pattern)
    # ============================================================
    if len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        if abs(lows[t1] - lows[t2]) / lows[t1] < 0.015:
            between_p = [p for p in peaks if t1 < p < t2]
            if between_p:
                p_peak = between_p[0]
                neckline_val = highs[p_peak]
                pattern_height = neckline_val - min(lows[t1], lows[t2])
                is_confirmed = curr_price > neckline_val
                
                # نقطة البداية قبل القاع الأول لرسم الهيكل كاملاً (W)
                start_idx_pos = max(0, t1 - 5)
                start_price = highs[start_idx_pos]

                rsi_val = rsi[-1] if not np.isnan(rsi[-1]) else 55
                ema_filter = curr_price > ema50[-1] if not np.isnan(ema50[-1]) else True
                
                quality = 70
                if is_confirmed: quality += 15
                if rsi_val > 50: quality += 10
                if ema_filter: quality += 5

                entry_p = curr_price if is_confirmed else neckline_val
                tp1_p = entry_p + pattern_height
                tp2_p = entry_p + (pattern_height * 1.8)
                sl_p = min(lows[t1], lows[t2]) * 0.998

                patterns.append({
                    "name": "Double Bottom (W)",
                    "direction": "BULLISH",
                    "quality": min(quality, 98),
                    "status": "CONFIRMED" if is_confirmed else "FORMING",
                    "reason": "قاع مزدوج مكتمل مع كسر خط العنق والدعم الفني" if is_confirmed else "قاع مزدوج قيد التكون، يرجى انتظار اختراق خط العنق",
                    "entry": round(entry_p, 4),
                    "tp1": round(tp1_p, 4),
                    "tp2": round(tp2_p, 4),
                    "sl": round(sl_p, 4),
                    # رسم الخط المتصل من بداية النموذج إلى آخره (W)
                    "points": [
                        {"index": indices[start_idx_pos], "price": start_price, "type": "Start"},
                        {"index": indices[t1], "price": lows[t1], "type": "Low 1"},
                        {"index": indices[p_peak], "price": neckline_val, "type": "Neckline Peak"},
                        {"index": indices[t2], "price": lows[t2], "type": "Low 2"},
                        {"index": curr_idx, "price": curr_price, "type": "Breakout"}
                    ],
                    # خط الكسر أفقي ينتهي عند آخر شمعة
                    "neckline_points": [
                        {"index": indices[t1], "price": neckline_val},
                        {"index": curr_idx, "price": neckline_val}
                    ]
                })

    # ============================================================
    # 2. نموذج القمة المزدوجة (Double Top - M Pattern)
    # ============================================================
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        if abs(highs[p1] - highs[p2]) / highs[p1] < 0.015:
            between_t = [t for t in troughs if p1 < t < p2]
            if between_t:
                t_trough = between_t[0]
                neckline_val = lows[t_trough]
                pattern_height = max(highs[p1], highs[p2]) - neckline_val
                is_confirmed = curr_price < neckline_val

                # نقطة البداية قبل القمة الأولى لرسم الهيكل كاملاً (M)
                start_idx_pos = max(0, p1 - 5)
                start_price = lows[start_idx_pos]

                rsi_val = rsi[-1] if not np.isnan(rsi[-1]) else 45
                ema_filter = curr_price < ema50[-1] if not np.isnan(ema50[-1]) else True

                quality = 70
                if is_confirmed: quality += 15
                if rsi_val < 50: quality += 10
                if ema_filter: quality += 5

                entry_p = curr_price if is_confirmed else neckline_val
                tp1_p = entry_p - pattern_height
                tp2_p = entry_p - (pattern_height * 1.8)
                sl_p = max(highs[p1], highs[p2]) * 1.002

                patterns.append({
                    "name": "Double Top (M)",
                    "direction": "BEARISH",
                    "quality": min(quality, 98),
                    "status": "CONFIRMED" if is_confirmed else "FORMING",
                    "reason": "قمة مزدوجة محققة مع كسر المستوى السفلي" if is_confirmed else "قمة مزدوجة قيد التكون عند منطقة مقاومة",
                    "entry": round(entry_p, 4),
                    "tp1": round(tp1_p, 4),
                    "tp2": round(tp2_p, 4),
                    "sl": round(sl_p, 4),
                    # رسم الخط المتصل من بداية النموذج إلى آخره (M)
                    "points": [
                        {"index": indices[start_idx_pos], "price": start_price, "type": "Start"},
                        {"index": indices[p1], "price": highs[p1], "type": "High 1"},
                        {"index": indices[t_trough], "price": neckline_val, "type": "Neckline Trough"},
                        {"index": indices[p2], "price": highs[p2], "type": "High 2"},
                        {"index": curr_idx, "price": curr_price, "type": "Breakout"}
                    ],
                    # خط الكسر أفقي ينتهي عند آخر شمعة
                    "neckline_points": [
                        {"index": indices[p1], "price": neckline_val},
                        {"index": curr_idx, "price": neckline_val}
                    ]
                })

    # ============================================================
    # 3. اختراق هيكل السوق (SMC Bullish BOS)
    # ============================================================
    if len(peaks) >= 1:
        last_peak = peaks[-1]
        if curr_price > highs[last_peak]:
            diff = curr_price - highs[last_peak]
            start_idx_pos = max(0, last_peak - 5)
            
            patterns.append({
                "name": "SMC Bullish BOS",
                "direction": "BULLISH",
                "quality": 92,
                "status": "CONFIRMED",
                "reason": "اختراق هيكلي صاعد (Break of Structure) فوق القمة الرئيسية السابقة",
                "entry": round(curr_price, 4),
                "tp1": round(curr_price + (diff * 2.0), 4),
                "tp2": round(curr_price + (diff * 3.5), 4),
                "sl": round(highs[last_peak] * 0.995, 4),
                "points": [
                    {"index": indices[start_idx_pos], "price": lows[start_idx_pos], "type": "Start"},
                    {"index": indices[last_peak], "price": highs[last_peak], "type": "Major High"},
                    {"index": curr_idx, "price": curr_price, "type": "BOS Breakout"}
                ],
                "neckline_points": [
                    {"index": indices[last_peak], "price": highs[last_peak]},
                    {"index": curr_idx, "price": highs[last_peak]}
                ]
            })

    patterns = sorted(patterns, key=lambda x: x['quality'], reverse=True)
    return patterns
