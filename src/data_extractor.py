import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, days_back: int = 900, as_of_date: str = None):
        self.days_back = days_back
        self.as_of_date = as_of_date
        self.cached_data = None
        self.cached_tickers = []

    def get_start_end_dates(self):
        if self.as_of_date:
            end_date_obj = datetime.strptime(self.as_of_date, '%Y-%m-%d')
        else:
            end_date_obj = datetime.today()
            
        start_date = (end_date_obj - timedelta(days=self.days_back)).strftime('%Y-%m-%d')
        # yfinance end_date is exclusive, so we add 1 day to ensure the as_of_date is included
        end_date = (end_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        return start_date, end_date

    def preload_data(self, tickers: list[str], start_date: str = None, end_date: str = None):
        if not start_date or not end_date:
            start_date, end_date = self.get_start_end_dates()
        try:
            logger.info(f"Bulk downloading data for {len(tickers)} tickers...")
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            self.cached_data = data
            self.cached_tickers = tickers
        except Exception as e:
            logger.error(f"Error in bulk download: {e}")
            self.cached_data = None
            self.cached_tickers = []

    def fetch_historical_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        if self.cached_data is not None and ticker in self.cached_tickers:
            if len(self.cached_tickers) > 1:
                try:
                    df = self.cached_data.xs(ticker, axis=1, level=1).dropna(how='all')
                except KeyError:
                    df = pd.DataFrame()
            else:
                df = self.cached_data.dropna(how='all')
                
            if not df.empty:
                # timezone naive vs aware index fix
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                # Slice data between start_date and end_date (exclusive of end_date as per yfinance behavior)
                sliced_df = df.loc[(df.index >= pd.to_datetime(start_date)) & (df.index < pd.to_datetime(end_date))]
                if not sliced_df.empty:
                    return sliced_df.copy()
                else:
                    return pd.DataFrame()

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
