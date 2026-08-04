from structure.swings import detect_swings
from structure.trend import determine_trend

class MarketStructureAnalyzer:
    def __init__(self, df):
        self.df = df

    def analyze(self):
        """Isku xidhka falanqaynta Swings iyo Trend-ka"""
        df_swings = detect_swings(self.df)
        trend = determine_trend(self.df)
        return {
            "trend": trend,
            "data": df_swings
        }
      
