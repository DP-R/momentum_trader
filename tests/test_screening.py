import pytest
import pandas as pd
from src.screening import StockScreener
from src.data_extractor import DataFetcher
from src.config import Config

class MockDataFetcher(DataFetcher):
    def get_start_end_dates(self):
        return "2020-01-01", "2021-01-01"
    
    def fetch_historical_data(self, ticker, start, end):
        if ticker == "EMPTY":
            return pd.DataFrame()
        # Return a dummy dataframe > 252 rows with all necessary columns
        return pd.DataFrame({
            'Open': [100 + i*0.1 for i in range(300)],
            'High': [102 + i*0.1 for i in range(300)],
            'Low': [98 + i*0.1 for i in range(300)],
            'Close': [100 + i*0.1 for i in range(300)],
            'Volume': [1000000] * 300
        }, index=pd.date_range(start="2020-01-01", periods=300))

    def fetch_market_indices(self):
        # Trending market regime (Close > 200-DMA)
        nifty = pd.DataFrame({
            'Close': [10000 + i*10 for i in range(300)], 
            'High': [10100 + i*10 for i in range(300)], 
            'Low': [9900 + i*10 for i in range(300)]
        })
        vix = pd.DataFrame({'Close': [12.0] * 300})
        return {"NIFTY_50": nifty, "INDIA_VIX": vix}

def test_screen_stocks():
    fetcher = MockDataFetcher(days_back=900)
    config = Config(MIN_PRICE=50, MIN_TURNOVER=1000)
    screener = StockScreener(data_fetcher=fetcher, config=config)
    
    df, regime = screener.screen_stocks(["TEST", "EMPTY"])
    assert not df.empty
    assert "TEST" in df["Ticker"].values
    assert "EMPTY" not in df["Ticker"].values
    assert regime["nifty_above_200dma"] is True
