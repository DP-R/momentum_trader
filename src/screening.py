from src.indicators import (
    calculate_atr, calculate_adx, calculate_rsi, 
    calculate_momentum_score, check_52w_breakout, check_20dma_pullback
)
from datetime import datetime
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class StockScreener:
    def __init__(self, data_fetcher, config):
        self.data_fetcher = data_fetcher
        self.config = config

    def check_market_regime(self):
        """Layer 1: Market Regime Check"""
        indices = self.data_fetcher.fetch_market_indices()
        nifty = indices.get("NIFTY_50")
        vix = indices.get("INDIA_VIX")
        
        regime = {
            "all_longs_off": False,
            "nifty_above_200dma": False,
            "vix_below_25": False,
            "stop_widen_atr": 0.0
        }
        
        if nifty is not None and not nifty.empty and len(nifty) >= 200:
            current_nifty = nifty['Close'].iloc[-1]
            ma200 = nifty['Close'].rolling(200).mean().iloc[-1]
            if current_nifty < ma200:
                regime["all_longs_off"] = True
            else:
                regime["nifty_above_200dma"] = True
                
        if vix is not None and not vix.empty:
            current_vix = vix['Close'].iloc[-1]
            if current_vix < 25:
                regime["vix_below_25"] = True
            if current_vix > 18:
                regime["stop_widen_atr"] = 0.5  # Widen stops in high volatility
                
        return regime

    def calculate_average_turnover(self, df, period=20):
        df['Turnover'] = df['Volume'] * df['Close']
        return df['Turnover'].rolling(period).mean().iloc[-1]

    def screen_stocks(self, tickers):
        regime = self.check_market_regime()
        if regime.get("all_longs_off", False):
            return pd.DataFrame(), regime

        start_date, end_date = self.data_fetcher.get_start_end_dates()
        passed_stocks = []
        
        for ticker in tickers:
            try:
                df = self.data_fetcher.fetch_historical_data(ticker, start_date, end_date)
                if df.empty or len(df) < 252:
                    continue
                
                current_price = df['Close'].iloc[-1]
                if current_price <= self.config.MIN_PRICE:
                    continue
                
                avg_turnover = self.calculate_average_turnover(df)
                if avg_turnover < self.config.MIN_TURNOVER:
                    continue
                
                atr_series = calculate_atr(df, 14)
                atr = atr_series.iloc[-1]
                atr_pct = (atr / current_price) * 100
                if not (self.config.MIN_ATR_PCT <= atr_pct <= self.config.MAX_ATR_PCT):
                    continue

                avg_vol_50 = df['Volume'].iloc[-51:-1].mean()
                vol_surge = df['Volume'].iloc[-1] / avg_vol_50 if avg_vol_50 > 0 else 1.0
                
                passed_stocks.append({
                    'Ticker': ticker,
                    'Price': current_price,
                    'Average_Turnover': avg_turnover,
                    'ATR': atr,
                    'ATR_%': atr_pct,
                    'Vol_Surge': vol_surge,
                    'Momentum_Score': calculate_momentum_score(df),
                    'Breakout_Candidate': check_52w_breakout(df),
                    'Pullback_Candidate': check_20dma_pullback(df),
                    'RSI2': calculate_rsi(df, 2).iloc[-1]
                })
            
            except Exception as e:
                logger.error(f"Error screening {ticker}: {e}")
                continue
        
        df_result = pd.DataFrame(passed_stocks) if passed_stocks else pd.DataFrame()
        if not df_result.empty:
            df_result = df_result.sort_values(by='Momentum_Score', ascending=False)
            
        return df_result, regime