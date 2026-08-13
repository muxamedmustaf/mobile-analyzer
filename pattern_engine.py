import pandas as pd
import numpy as np

class SMCPatternEngine:
    def __init__(self, df: pd.DataFrame, depth: int = 8, max_tolerance: float = 0.15):
        self.df = df.copy()
        self.depth = depth
        self.max_tolerance = max_tolerance
        self.zigzag_points = []

    def calculate_major_swings(self):
        self.df['Major_High'] = np.nan
        self.df['Major_Low'] = np.nan

        highs = self.df['high'].values
        lows = self.df['low'].values
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

    def detect_market_patterns(self):
        self.calculate_major_swings()

        valid_highs = self.df['Major_High'].dropna()
        valid_lows = self.df['Major_Low'].dropna()

        patterns = []
        trend = "RANGING"

        if len(valid_highs) >= 3 and len(valid_lows) >= 3:
            h1, h2, h3 = valid_highs.iloc[-3], valid_highs.iloc[-2], valid_highs.iloc[-1]
            l1, l2, l3 = valid_lows.iloc[-3], valid_lows.iloc[-2], valid_lows.iloc[-1]
            current_close = self.df['close'].iloc[-1]

            # Determine Trend Status
            if current_close > h3:
                trend = "BULLISH"
            elif current_close < l3:
                trend = "BEARISH"

            # ----------------------------------------------------
            # DYNAMIC DETECTION LOGIC (15 MAJOR PATTERNS)
            # ----------------------------------------------------

            # 1. Head & Shoulders Reversal
            if h2 > h1 and h2 > h3 and abs(h1 - h3) / h1 <= self.max_tolerance:
                patterns.append(self._build_pattern("Head & Shoulders Reversal", "BEARISH", current_close, 95))

            # 2. Inverse Head & Shoulders
            elif l2 < l1 and l2 < l3 and abs(l1 - l3) / l1 <= self.max_tolerance:
                patterns.append(self._build_pattern("Inverse Head & Shoulders", "BULLISH", current_close, 95))

            # 3. Triple Top Reversal
            elif abs(h1 - h2)/h1 <= self.max_tolerance and abs(h2 - h3)/h2 <= self.max_tolerance:
                patterns.append(self._build_pattern("Triple Top Reversal", "BEARISH", current_close, 90))

            # 4. Triple Bottom Reversal
            elif abs(l1 - l2)/l1 <= self.max_tolerance and abs(l2 - l3)/l2 <= self.max_tolerance:
                patterns.append(self._build_pattern("Triple Bottom Reversal", "BULLISH", current_close, 90))

            # 5. Double Bottom (W-Pattern)
            elif abs(l2 - l3) / l2 <= self.max_tolerance and current_close > l3:
                patterns.append(self._build_pattern("Double Bottom Reversal", "BULLISH", current_close, 88))

            # 6. Double Top (M-Pattern)
            elif abs(h2 - h3) / h2 <= self.max_tolerance and current_close < h3:
                patterns.append(self._build_pattern("Double Top Reversal", "BEARISH", current_close, 88))

            # 7. Bullish Change of Character (CHoCH)
            elif trend == "BULLISH" and current_close > h2 and l3 > l2:
                patterns.append(self._build_pattern("Bullish CHoCH Breakdown", "BULLISH", current_close, 92))

            # 8. Bearish Change of Character (CHoCH)
            elif trend == "BEARISH" and current_close < l2 and h3 < h2:
                patterns.append(self._build_pattern("Bearish CHoCH Breakdown", "BEARISH", current_close, 92))

            # 9. Bullish Break of Structure (BOS)
            elif trend == "BULLISH" and h3 > h2 and l3 > l2:
                patterns.append(self._build_pattern("Bullish Break of Structure (BOS)", "BULLISH", current_close, 85))

            # 10. Bearish Break of Structure (BOS)
            elif trend == "BEARISH" and h3 < h2 and l3 < l2:
                patterns.append(self._build_pattern("Bearish Break of Structure (BOS)", "BEARISH", current_close, 85))

            # 11. Ascending Triangle
            elif abs(h2 - h3)/h2 <= self.max_tolerance and l3 > l2:
                patterns.append(self._build_pattern("Ascending Triangle Breakout", "BULLISH", current_close, 82))

            # 12. Descending Triangle
            elif abs(l2 - l3)/l2 <= self.max_tolerance and h3 < h2:
                patterns.append(self._build_pattern("Descending Triangle Breakout", "BEARISH", current_close, 82))

            # 13. Bullish Flag / Channel
            elif trend == "BULLISH" and h3 < h2 and l3 < l2 and (h2 - h3) <= (l2 - l3)*(1 + self.max_tolerance):
                patterns.append(self._build_pattern("Bullish Flag Continuation", "BULLISH", current_close, 80))

            # 14. Bearish Flag / Channel
            elif trend == "BEARISH" and h3 > h2 and l3 > l2 and (h3 - h2) <= (l3 - l2)*(1 + self.max_tolerance):
                patterns.append(self._build_pattern("Bearish Flag Continuation", "BEARISH", current_close, 80))

            # 15. Equal Wave Extension
            else:
                wave1 = abs(h2 - l2)
                wave2 = abs(h3 - l3)
                diff_ratio = abs(wave1 - wave2) / wave1 if wave1 > 0 else 1.0
                if diff_ratio <= self.max_tolerance:
                    p_dir = "BULLISH" if trend == "BULLISH" else ("BEARISH" if trend == "BEARISH" else "NEUTRAL")
                    patterns.append(self._build_pattern("SMC Equal Wave Extension", p_dir, current_close, int((1 - diff_ratio)*100)))

        return {
            "trend": trend,
            "patterns": patterns,
            "latest_bos": "BULLISH BOS" if trend == "BULLISH" else ("BEARISH BOS" if trend == "BEARISH" else None),
            "latest_choch": "CHoCH Confirmed" if patterns else None
        }

    def _build_pattern(self, name: str, direction: str, close_price: float, quality: int):
        """Helper to build absolute price TP/SL orders"""
        tp1 = round(close_price + 800.00 if direction == "BULLISH" else close_price - 800.00, 2)
        tp2 = round(close_price + 1400.00 if direction == "BULLISH" else close_price - 1400.00, 2)
        sl = round(close_price - 450.00 if direction == "BULLISH" else close_price + 450.00, 2)

        return {
            "name": name,
            "direction": direction,
            "quality": quality,
            "status": "CONFIRMED" if direction != "NEUTRAL" else "FORMING",
            "reason": f"Structure recognized under strictly enforced {self.max_tolerance*100:.0f}% wave tolerance.",
            "entry": close_price,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
        }

    def evaluate_strict_signal(self, symbol: str, current_price: float, rsi_val: float):
        analysis = self.detect_market_patterns()
        patterns = analysis["patterns"]

        if patterns and (rsi_val < 35 or rsi_val > 65):
            p = patterns[0]
            return {
                "Symbol": symbol,
                "Status": "VALID_SIGNAL",
                "Entry_Price": p["entry"],
                "Take_Profit_Absolute": p["tp1"],
                "Stop_Loss_Absolute": p["sl"]
            }

        return {"Symbol": symbol, "Status": "NO_SIGNAL"}
                                                    
