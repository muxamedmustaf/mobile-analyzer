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

        if len(valid_highs) >= 2 and len(valid_lows) >= 2:
            last_high = valid_highs.iloc[-1]
            prev_high = valid_highs.iloc[-2]
            last_low = valid_lows.iloc[-1]
            prev_low = valid_lows.iloc[-2]

            wave1 = abs(prev_high - prev_low)
            wave2 = abs(last_high - last_low)

            diff_ratio = abs(wave1 - wave2) / wave1 if wave1 > 0 else 1.0
            is_valid_wave = diff_ratio <= self.max_tolerance

            current_close = self.df['close'].iloc[-1]

            if current_close > last_high:
                trend = "BULLISH"
            elif current_close < last_low:
                trend = "BEARISH"

            if is_valid_wave:
                direction = "BULLISH" if trend == "BULLISH" else ("BEARISH" if trend == "BEARISH" else "NEUTRAL")
                tp1 = round(current_close + 800.00 if direction == "BULLISH" else current_close - 800.00, 2)
                tp2 = round(current_close + 1400.00 if direction == "BULLISH" else current_close - 1400.00, 2)
                sl = round(current_close - 450.00 if direction == "BULLISH" else current_close + 450.00, 2)

                patterns.append({
                    "name": "EQUAL WAVE EXTENSION (SMC)",
                    "direction": direction,
                    "quality": int((1 - diff_ratio) * 100),
                    "status": "CONFIRMED" if direction != "NEUTRAL" else "FORMING",
                    "reason": f"Mawyado siman oo leh farqi {diff_ratio*100:.1f}% (dhan Max {self.max_tolerance*100:.0f}%).",
                    "entry": current_close,
                    "tp1": tp1,
                    "tp2": tp2,
                    "sl": sl,
                })

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
        
