# ============================================================
# PATTERN_ENGINE.PY
# STRICT SMC & UNIVERSAL PATTERN RECOGNITION ENGINE
# ============================================================

import pandas as pd
import numpy as np

class SMCPatternEngine:
    def __init__(self, df: pd.DataFrame, depth: int = 8, max_tolerance: float = 0.15):
        self.df = df.copy()
        self.depth = depth
        self.max_tolerance = max_tolerance  # Strict 15% tolerance ($0.15 max)
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

    def _build_pattern_orders(self, name: str, direction: str, close_price: float, quality: int, last_high: float, last_low: float):
        """
        UNIVERSAL PATTERN EXECUTION RULE:
        Calculates SL strictly using the actual Swing High/Low Structure + Buffer.
        Calculates TP1 & TP2 using professional Risk-to-Reward Ratios (1:1.5 and 1:2.5).
        """
        swing_range = abs(last_high - last_low) if (last_high and last_low) else close_price * 0.01
        buffer = max(swing_range * 0.10, close_price * 0.002)  # Dynamic Structural Buffer

        if direction == "BULLISH":
            # SL is strictly placed BELOW the lowest structural swing low
            sl = round(last_low - buffer, 2)
            risk = max(close_price - sl, close_price * 0.005)
            tp1 = round(close_price + (risk * 1.5), 2)
            tp2 = round(close_price + (risk * 2.5), 2)

        elif direction == "BEARISH":
            # SL is strictly placed ABOVE the highest structural swing high
            sl = round(last_high + buffer, 2)
            risk = max(sl - close_price, close_price * 0.005)
            tp1 = round(close_price - (risk * 1.5), 2)
            tp2 = round(close_price - (risk * 2.5), 2)

        else:
            sl, tp1, tp2 = close_price, close_price, close_price

        return {
            "name": name,
            "direction": direction,
            "quality": quality,
            "status": "CONFIRMED" if direction != "NEUTRAL" else "FORMING",
            "reason": f"Structure matched per universal pattern rules with max tolerance ≤ {self.max_tolerance*100:.0f}%.",
            "entry": round(close_price, 2),
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
        }

    def detect_market_patterns(self):
        self.calculate_major_swings()

        valid_highs = self.df['Major_High'].dropna()
        valid_lows = self.df['Major_Low'].dropna()

        patterns = []
        trend = "RANGING"

        if len(valid_highs) >= 3 and len(valid_lows) >= 3:
            h1, h2, h3 = valid_highs.iloc[-3], valid_highs.iloc[-2], valid_highs.iloc[-1]
            l1, l2, l3 = valid_lows.iloc[-3], valid_lows.iloc[-2], valid_lows.iloc[-1]
            current_close = float(self.df['close'].iloc[-1])

            # Trend Structure
            if current_close > h3:
                trend = "BULLISH"
            elif current_close < l3:
                trend = "BEARISH"

            # ----------------------------------------------------
            # 15 DYNAMIC PATTERN RULES (UNIVERSAL STANDARD)
            # ----------------------------------------------------

            # 1. Double Bottom Reversal (W-Pattern)
            if abs(l2 - l3) / l2 <= self.max_tolerance and current_close > l3:
                patterns.append(self._build_pattern_orders("Double Bottom Reversal", "BULLISH", current_close, 92, h3, min(l2, l3)))

            # 2. Double Top Reversal (M-Pattern)
            elif abs(h2 - h3) / h2 <= self.max_tolerance and current_close < h3:
                patterns.append(self._build_pattern_orders("Double Top Reversal", "BEARISH", current_close, 92, max(h2, h3), l3))

            # 3. Head & Shoulders Reversal
            elif h2 > h1 and h2 > h3 and abs(h1 - h3) / h1 <= self.max_tolerance:
                patterns.append(self._build_pattern_orders("Head & Shoulders Reversal", "BEARISH", current_close, 95, h2, l3))

            # 4. Inverse Head & Shoulders
            elif l2 < l1 and l2 < l3 and abs(l1 - l3) / l1 <= self.max_tolerance:
                patterns.append(self._build_pattern_orders("Inverse Head & Shoulders", "BULLISH", current_close, 95, h3, l2))

            # 5. Bullish Change of Character (CHoCH)
            elif trend == "BULLISH" and current_close > h2 and l3 > l2:
                patterns.append(self._build_pattern_orders("Bullish CHoCH Breakout", "BULLISH", current_close, 90, h3, l3))

            # 6. Bearish Change of Character (CHoCH)
            elif trend == "BEARISH" and current_close < l2 and h3 < h2:
                patterns.append(self._build_pattern_orders("Bearish CHoCH Breakdown", "BEARISH", current_close, 90, h3, l3))

            # 7. Bullish Break of Structure (BOS)
            elif trend == "BULLISH" and h3 > h2 and l3 > l2:
                patterns.append(self._build_pattern_orders("Bullish Break of Structure (BOS)", "BULLISH", current_close, 88, h3, l3))

            # 8. Bearish Break of Structure (BOS)
            elif trend == "BEARISH" and h3 < h2 and l3 < l2:
                patterns.append(self._build_pattern_orders("Bearish Break of Structure (BOS)", "BEARISH", current_close, 88, h3, l3))

            # 9. Triple Bottom
            elif abs(l1 - l2)/l1 <= self.max_tolerance and abs(l2 - l3)/l2 <= self.max_tolerance:
                patterns.append(self._build_pattern_orders("Triple Bottom Reversal", "BULLISH", current_close, 91, h3, min(l1, l2, l3)))

            # 10. Triple Top
            elif abs(h1 - h2)/h1 <= self.max_tolerance and abs(h2 - h3)/h2 <= self.max_tolerance:
                patterns.append(self._build_pattern_orders("Triple Top Reversal", "BEARISH", current_close, 91, max(h1, h2, h3), l3))

            # 11. Ascending Triangle
            elif abs(h2 - h3)/h2 <= self.max_tolerance and l3 > l2:
                patterns.append(self._build_pattern_orders("Ascending Triangle Breakout", "BULLISH", current_close, 85, h3, l3))

            # 12. Descending Triangle
            elif abs(l2 - l3)/l2 <= self.max_tolerance and h3 < h2:
                patterns.append(self._build_pattern_orders("Descending Triangle Breakout", "BEARISH", current_close, 85, h3, l3))

            # 13. Bullish Flag Continuation
            elif trend == "BULLISH" and h3 < h2 and l3 < l2:
                patterns.append(self._build_pattern_orders("Bullish Flag Continuation", "BULLISH", current_close, 82, h2, l3))

            # 14. Bearish Flag Continuation
            elif trend == "BEARISH" and h3 > h2 and l3 > l2:
                patterns.append(self._build_pattern_orders("Bearish Flag Continuation", "BEARISH", current_close, 82, h3, l2))

            # 15. SMC Equal Wave Extension
            else:
                wave1 = abs(h2 - l2)
                wave2 = abs(h3 - l3)
                diff_ratio = abs(wave1 - wave2) / wave1 if wave1 > 0 else 1.0
                if diff_ratio <= self.max_tolerance:
                    p_dir = "BULLISH" if trend == "BULLISH" else ("BEARISH" if trend == "BEARISH" else "NEUTRAL")
                    patterns.append(self._build_pattern_orders("SMC Wave Extension", p_dir, current_close, int((1 - diff_ratio)*100), h3, l3))

        return {
            "trend": trend,
            "patterns": patterns,
            "latest_bos": "BULLISH BOS" if trend == "BULLISH" else ("BEARISH BOS" if trend == "BEARISH" else None),
            "latest_choch": "CHoCH Confirmed" if patterns else None
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
            
