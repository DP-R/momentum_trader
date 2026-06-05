import pytest
from src.data_extractor import DataFetcher

def test_fetch_historical_data_valid_ticker():
    fetcher = DataFetcher(days_back=900)
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    data = fetcher.fetch_historical_data(ticker, start_date, end_date)
    assert not data.empty, "Data should not be empty for a valid ticker."

def test_fetch_historical_data_invalid_ticker():
    fetcher = DataFetcher(days_back=900)
    ticker = "INVALID_TICKER"
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    data = fetcher.fetch_historical_data(ticker, start_date, end_date)
    assert data.empty, "Data should be empty for an invalid ticker."

def test_fetch_historical_data_date_range():
    fetcher = DataFetcher(days_back=900)
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-10"
    data = fetcher.fetch_historical_data(ticker, start_date, end_date)
    # yfinance only returns trading days, between 2020-01-01 and 2020-01-10 there are roughly 6-7 trading days
    assert not data.empty, "Data should contain entries for the specified date range."
    assert len(data) > 0

def test_fetch_historical_data_no_data():
    fetcher = DataFetcher(days_back=900)
    ticker = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-01-01"  # No trading data on a single weekend/holiday date usually, but just in case
    data = fetcher.fetch_historical_data(ticker, start_date, end_date)
    assert data.empty, "Data should be empty if no trading occurred on the specified date."
