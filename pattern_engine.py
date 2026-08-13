import pandas as pd
import numpy as np

class SMCPatternEngine:
    def __init__(self, df: pd.DataFrame, depth: int = 10, max_tolerance: float = 0.15):
        self.df = df.copy()
        self.depth = depth
        self.max_tolerance = max_tolerance  # نسبة التفاوت المقبولة (0.15 = 15%)

    def calculate_major_swings(self):
        """
        حساب القمم والقيعان الرئيسية (Major Swings) عبر خوارزمية Pivot / ZigZag.
        """
        self.df['Major_High'] = np.nan
        self.df['Major_Low'] = np.nan

        highs = self.df['High'].values
        lows = self.df['Low'].values
        n = len(self.df)

        for i in range(self.depth, n - self.depth):
            if highs[i] == max(highs[i - self.depth : i + self.depth + 1]):
                self.df.iloc[i, self.df.columns.get_loc('Major_High')] = highs[i]
            if lows[i] == min(lows[i - self.depth : i + self.depth + 1]):
                self.df.iloc[i, self.df.columns.get_loc('Major_Low')] = lows[i]

        zigzag_points = []
        for idx in range(len(self.df)):
            if not np.isnan(self.df['Major_High'].iloc[idx]):
                zigzag_points.append((self.df.index[idx], self.df['Major_High'].iloc[idx], 'HIGH'))
            elif not np.isnan(self.df['Major_Low'].iloc[idx]):
                zigzag_points.append((self.df.index[idx], self.df['Major_Low'].iloc[idx], 'LOW'))

        self.zigzag_points = zigzag_points
        return self.df

    def check_wave_equality(self, wave1_length: float, wave2_length: float) -> tuple[bool, float]:
        """
        التحقق من تساوٍ الموجات ضمن التفاوت المسموح (0.15 كحد أقصى).
        """
        w1 = abs(wave1_length)
        w2 = abs(wave2_length)
        
        if w1 == 0:
            return False, 1.0

        diff_ratio = abs(w1 - w2) / w1
        is_valid = diff_ratio <= self.max_tolerance
        return is_valid, round(diff_ratio, 4)

    def detect_market_patterns(self):
        """
        فحص أنماط SMC وتطبيق شرط التفاوت 0.15 المحدث.
        """
        self.calculate_major_swings()

        valid_highs = self.df['Major_High'].dropna()
        valid_lows = self.df['Major_Low'].dropna()

        pattern_name = "RANGING MARKET STRUCTURE"
        pattern_found = False
        message = "Pattern xirfad leh lagama helin major swings-ka hadda jira."
        details = {}

        if len(valid_highs) >= 2 and len(valid_lows) >= 2:
            last_high = valid_highs.iloc[-1]
            prev_high = valid_highs.iloc[-2]
            last_low = valid_lows.iloc[-1]
            prev_low = valid_lows.iloc[-2]

            wave1 = prev_high - prev_low
            wave2 = last_high - last_low

            is_equal, diff_ratio = self.check_wave_equality(wave1, wave2)

            details['wave1_length'] = round(abs(wave1), 2)
            details['wave2_length'] = round(abs(wave2), 2)
            details['diff_ratio'] = diff_ratio
            details['tolerance_limit'] = self.max_tolerance

            current_close = self.df['Close'].iloc[-1]

            if is_equal:
                pattern_found = True
                if current_close > last_high:
                    pattern_name = "BULLISH CHoCH / EQUAL WAVE EXTENSION"
                    message = f"تم الكشف عن نمط متوافق: كسر صاعد مع تساوٍ الموجات (التفاوت: {diff_ratio*100:.1f}% <= 15%)."
                elif current_close < last_low:
                    pattern_name = "BEARISH CHoCH / EQUAL WAVE EXTENSION"
                    message = f"تم الكشف عن نمط متوافق: كسر هابط مع تساوٍ الموجات (التفاوت: {diff_ratio*100:.1f}% <= 15%)."
                else:
                    pattern_name = "EQUAL WAVE STRUCTURE (0.15 Tolerance)"
                    message = f"تم اكتشاف نمط موجات متساوية ضمن نطاق التفاوت المسموح ({diff_ratio*100:.1f}% <= 15%)."
            else:
                message = f"Pattern xirfad leh lagama helin major swings-ka hadda jira (نسبة التفاوت {diff_ratio*100:.1f}% تتجاوز الحد الأقصى 15%)."

        return {
            "structure_status": pattern_name,
            "pattern_found": pattern_found,
            "message": message,
            "details": details
        }

    def evaluate_strict_signal(self, symbol: str, current_price: float, rsi_val: float):
        """
        توليد إشارة التداول وأهداف أرباح وخسائر بأسعار مطلقة (Absolute Price Values).
        الرموز بصيغتها الخام بدون تعديل، مع استبعاد ADX كلياً.
        """
        analysis = self.detect_market_patterns()

        # الشرط الصارم: توفر النمط + تحقق المؤشرات
        if analysis["pattern_found"] and (rsi_val < 35 or rsi_val > 65):
            trade_type = "BUY" if rsi_val < 35 else "SELL"

            if trade_type == "BUY":
                tp = round(current_price + 1200.00, 2)
                sl = round(current_price - 450.00, 2)
            else:
                tp = round(current_price - 1200.00, 2)
                sl = round(current_price + 450.00, 2)

            return {
                "Symbol": symbol,  # الصيغة الخام للرمز
                "Signal": trade_type,
                "Entry_Price": current_price,
                "Take_Profit_Absolute": tp,
                "Stop_Loss_Absolute": sl,
                "Status": "VALID_SIGNAL",
                "Message": analysis["message"]
            }

        return {
            "Symbol": symbol,
            "Signal": "NO_TRADE",
            "Status": "NO_SIGNAL",
            "Message": analysis["message"]
        }
        
