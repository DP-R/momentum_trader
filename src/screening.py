from src.indicators import (
    calculate_atr, calculate_adx, calculate_rsi, 
    calculate_momentum_score, check_52w_breakout, check_20dma_pullback
)
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
            "reduce_size_50_nifty": False,
            "vix_below_15": False,
            "reduce_size_25_vix": False,
            "reduce_size_50_vix": False,
            "stop_widen_atr": 0.0,
            "no_breakouts": False,
            "trend_preferred": False,
            "mean_reversion_preferred": False
        }
        
        if nifty is not None and not nifty.empty and len(nifty) >= 200:
            current_nifty = nifty['Close'].iloc[-1]
            ma50 = nifty['Close'].rolling(50).mean().iloc[-1]
            ma200 = nifty['Close'].rolling(200).mean().iloc[-1]
            if current_nifty < ma200:
                regime["all_longs_off"] = True
            if current_nifty < ma50:
                regime["reduce_size_50_nifty"] = True
                
            adx = calculate_adx(nifty, 14).iloc[-1]
            if adx > 25:
                regime["trend_preferred"] = True
            elif adx < 20:
                regime["mean_reversion_preferred"] = True
                
        if vix is not None and not vix.empty:
            current_vix = vix['Close'].iloc[-1]
            if current_vix < 15:
                regime["vix_below_15"] = True
            elif 15 <= current_vix <= 20:
                regime["reduce_size_25_vix"] = True
                regime["stop_widen_atr"] = 1.0  # Widen stops by 1 ATR
            elif current_vix > 20:
                regime["reduce_size_50_vix"] = True
                regime["no_breakouts"] = True
                
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
                
                m6, m12 = calculate_momentum_score(df)
                is_breakout, breakout_info = check_52w_breakout(df)
                is_pullback, pullback_info = check_20dma_pullback(df)
                
                passed_stocks.append({
                    'Ticker': ticker,
                    'Price': current_price,
                    'Average_Turnover': avg_turnover,
                    'ATR': atr,
                    'ATR_%': atr_pct,
                    'Vol_Surge': vol_surge,
                    'M6': m6,
                    'M12': m12,
                    'Breakout_Candidate': is_breakout,
                    'Breakout_Info': breakout_info,
                    'Pullback_Candidate': is_pullback,
                    'Pullback_Info': pullback_info,
                    'RSI2': calculate_rsi(df, 2).iloc[-1]
                })
            
            except Exception as e:
                logger.error(f"Error screening {ticker}: {e}")
                continue
        
        df_result = pd.DataFrame(passed_stocks) if passed_stocks else pd.DataFrame()
        if not df_result.empty:
            from src.indicators import zscore
            df_result['M6_Z'] = zscore(df_result['M6'])
            df_result['M12_Z'] = zscore(df_result['M12'])
            df_result['Momentum_Score'] = (df_result['M6_Z'] + df_result['M12_Z']) / 2
            df_result = df_result.sort_values(by='Momentum_Score', ascending=False)
            
        return df_result, regime