import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, days_back: int = 900, as_of_date: str = None):
        self.days_back = days_back
        self.as_of_date = as_of_date

    def get_start_end_dates(self):
        if self.as_of_date:
            end_date_obj = datetime.strptime(self.as_of_date, '%Y-%m-%d')
        else:
            end_date_obj = datetime.today()
            
        start_date = (end_date_obj - timedelta(days=self.days_back)).strftime('%Y-%m-%d')
        # yfinance end_date is exclusive, so we add 1 day to ensure the as_of_date is included
        end_date = (end_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        return start_date, end_date

    def fetch_historical_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            data = yf.Ticker(ticker).history(start=start_date, end=end_date)
            if data.empty:
                logger.warning(f"No data found for {ticker} between {start_date} and {end_date}.")
                return pd.DataFrame()
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_multiple_stocks(self, tickers: list[str]) -> dict[str, pd.DataFrame]:
        start_date, end_date = self.get_start_end_dates()
        stock_data = {}
        for ticker in tickers:
            df = self.fetch_historical_data(ticker, start_date, end_date)
            if not df.empty:
                stock_data[ticker] = df
        return stock_data

    def fetch_market_indices(self) -> dict[str, pd.DataFrame]:
        """Fetches Nifty 50 and India VIX for Market Regime filters."""
        start_date, end_date = self.get_start_end_dates()
        return {
            "NIFTY_50": self.fetch_historical_data("^NSEI", start_date, end_date),
            "INDIA_VIX": self.fetch_historical_data("^INDIAVIX", start_date, end_date)
        }
