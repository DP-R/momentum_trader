import argparse
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings

# Ignore pandas future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from src.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def calculate_rsi_series(close, period=2):
    delta = close.diff()
    gain = delta.mask(delta < 0, 0.0)
    loss = -delta.mask(delta > 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr_series(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def compute_signals(df, config):
    res = pd.DataFrame(index=df.index)
    res['Close'] = df['Close']
    res['Open'] = df['Open']
    res['High'] = df['High']
    res['Low'] = df['Low']
    res['Volume'] = df['Volume']
    
    res['Valid'] = (df['Close'] > config.MIN_PRICE)
    
    avg_turnover = (df['Volume'] * df['Close']).rolling(20).mean()
    res['Avg_Turnover'] = avg_turnover
    res['Valid'] = res['Valid'] & (avg_turnover >= config.MIN_TURNOVER)
    
    atr = calculate_atr_series(df, 14)
    atr_pct = (atr / df['Close']) * 100
    res['ATR'] = atr
    res['ATR_%'] = atr_pct
    res['Valid'] = res['Valid'] & (atr_pct >= config.MIN_ATR_PCT) & (atr_pct <= config.MAX_ATR_PCT)
    
    ret_6m = df['Close'] / df['Close'].shift(126) - 1
    vol_6m = df['Close'].pct_change().rolling(126).std()
    ret_12m = df['Close'] / df['Close'].shift(252) - 1
    vol_12m = df['Close'].pct_change().rolling(252).std()
    res['Momentum_Score'] = 0.5 * (ret_6m / vol_6m) + 0.5 * (ret_12m / vol_12m)
    
    prev_52w_high = df['Close'].shift(1).rolling(252).max()
    avg_vol_50 = df['Volume'].shift(1).rolling(50).mean()
    ma50 = df['Close'].rolling(50).mean()
    ma200 = df['Close'].rolling(200).mean()
    ma50_prev = ma50.shift(5)
    ma200_prev = ma200.shift(5)
    
    breakout = (df['Close'] > prev_52w_high) & (df['Close'] > df['Close'].shift(1))
    volume_surge = (df['Volume'] >= 1.5 * avg_vol_50) & (avg_vol_50 > 0)
    trend_ok = (df['Close'] > ma50) & (df['Close'] > ma200)
    dma_rising = (ma50 > ma50_prev) & (ma200 > ma200_prev)
    res['Breakout_Candidate'] = breakout & volume_surge & trend_ok & dma_rising
    
    ma20 = df['Close'].rolling(20).mean()
    rsi2 = calculate_rsi_series(df['Close'], 2)
    near_20dma = (np.abs(df['Close'] - ma20) / ma20) <= 0.01
    in_uptrend = (df['Close'] > ma50) & (df['Close'] > ma200)
    bullish_reversal = (df['Close'] > df['Open']) & (df['Close'] > df['Close'].shift(1))
    res['Pullback_Candidate'] = in_uptrend & near_20dma & (rsi2 < 10) & bullish_reversal
    
    res['Vol_Surge'] = df['Volume'] / avg_vol_50
    res['RSI2'] = rsi2
    
    return res

def simulate_trades_fast(df_ticker, entry_idx, entry_price, initial_stop, t1, t2):
    current_stop = initial_stop
    
    lows = df_ticker['Low'].values
    highs = df_ticker['High'].values
    opens = df_ticker['Open'].values
    closes = df_ticker['Close'].values
    dates = df_ticker.index
    
    for i in range(len(lows)):
        low = lows[i]
        high = highs[i]
        
        if low <= current_stop:
            exit_price = opens[i] if opens[i] < current_stop else current_stop
            status = 'Closed (Stop Loss)' if current_stop == initial_stop else 'Closed (Trailing Stop)'
            return exit_price, dates[i], status
            
        if high >= t2:
            exit_price = opens[i] if opens[i] > t2 else t2
            status = 'Closed (T2 Hit)'
            return exit_price, dates[i], status
            
        if high >= t1 and current_stop < entry_price:
            current_stop = entry_price
            
    if len(closes) > 0:
        return closes[-1], dates[-1], 'Open'
    else:
        return entry_price, None, 'No Forward Data'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    config = Config()
    start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    fetch_start = (start_dt - timedelta(days=900)).strftime('%Y-%m-%d')
    fetch_end = (end_dt + timedelta(days=100)).strftime('%Y-%m-%d')

    tickers = [
        '3MINDIA.NS', 'AARTIIND.NS', 'BBTC.NS', 'BHARATFORG.NS', 'CHOLAHLDNG.NS',
        'CRISIL.NS', 'HAL.NS', 'IDFCFIRSTB.NS', 'JKCEMENT.NS', 'M&MFIN.NS',
        'SKFINDIA.NS', 'TATACHEM.NS', 'TVSMOTOR.NS', 'WHIRLPOOL.NS', 'JSWENERGY.NS',
        'RECLTD.NS', 'TATAPOWER.NS', 'GICRE.NS', 'TATACOMM.NS', 'ABFRL.NS',
        'ASHOKLEY.NS', 'BANKBARODA.NS', 'GUJGASLTD.NS', 'LALPATHLAB.NS', 'PAGEIND.NS',
        'SUNDRMFAST.NS', 'TTKPRESTIG.NS', 'VINATIORGA.NS', 'ABCAPITAL.NS',
        'ASTRAZEN.NS', 'BATAINDIA.NS', 'CANBK.NS', 'COROMANDEL.NS', 'CUMMINSIND.NS',
        'ENDURANCE.NS', 'GLAXO.NS', 'JMFINANCIL.NS', 'MPHASIS.NS', 'OFSS.NS',
        'PERSISTENT.NS', 'PFIZER.NS', 'PGHL.NS', 'SUNTV.NS', 'THERMAX.NS', 'APLLTD.NS',
        'BHEL.NS', 'DIXON.NS', 'GLENMARK.NS', 'JINDALSTEL.NS', 'OBEROIRLTY.NS',
        'PIIND.NS', 'SANOFI.NS', 'EMAMILTD.NS', 'ESCORTS.NS', 'FORTIS.NS',
        'HINDZINC.NS', 'INDHOTEL.NS', 'NHPC.NS', 'SCHAEFFLER.NS', 'SUPREMEIND.NS',
        'BANKINDIA.NS', 'CHOLAFIN.NS', 'EXIDEIND.NS', 'IDBI.NS', 'MANAPPURAM.NS',
        'METROPOLIS.NS', 'MOTILALOFS.NS', 'NATCOPHARM.NS', 'SOLARINDS.NS', 'ZEEL.NS',
        'AUBANK.NS', 'CASTROLIND.NS', 'DALBHARAT.NS', 'POLYCAB.NS', 'SAIL.NS',
        'TIINDIA.NS', 'VGUARD.NS', 'ASTRAL.NS', 'ATGL.NS', 'DEEPAKNTR.NS',
        'LAURUSLABS.NS', 'LTTS.NS', 'NAVINFLUOR.NS', 'BAYERCROP.NS', 'CONCOR.NS',
        'GODREJPROP.NS', 'IDEA.NS', 'PFC.NS', 'PRESTIGE.NS', 'ABB.NS', 'APOLLOTYRE.NS',
        'BEL.NS', 'HATSUN.NS', 'NIACL.NS', 'RAJESHEXPO.NS', 'RELAXO.NS',
        'SUNDARMFIN.NS', 'TRENT.NS', 'UNIONBANK.NS', 'AJANTPHARM.NS', 'CESC.NS',
        'CROMPTON.NS', 'FEDERALBNK.NS', 'GODREJAGRO.NS', 'GODREJIND.NS', 'IPCALAB.NS',
        'KANSAINER.NS', 'RBLBANK.NS', 'SJVN.NS', 'SUMICHEM.NS', 'ATUL.NS',
        'CREDITACC.NS', 'INDIAMART.NS', 'IRCTC.NS', 'LICHSGFIN.NS', 'OIL.NS',
        'RAMCOCEM.NS', 'SYNGENE.NS', 'VOLTAS.NS', 'AAVAS.NS', 'AIAENG.NS',
        'COFORGE.NS', 'HONAUT.NS', 'MFSL.NS', 'NAM-INDIA.NS', 'PHOENIXLTD.NS',
        'SRF.NS', 'TATAELXSI.NS', 'TORNTPOWER.NS', 'BALKRISIND.NS', 'CUB.NS',
        'GILLETTE.NS', 'ITI.NS', 'MAXHEALTH.NS', 'MGL.NS', 'VBL.NS', 'ZYDUSWELL.NS'
    ]
    all_tickers = tickers + ['^NSEI', '^INDIAVIX']

    logging.info(f"Downloading data from {fetch_start} to {fetch_end} for {len(all_tickers)} tickers...")
    raw_data = yf.download(all_tickers, start=fetch_start, end=fetch_end, progress=False)

    if raw_data.empty:
        logging.error("Failed to download any data.")
        return

    nifty = raw_data.xs('^NSEI', axis=1, level=1).dropna(how='all') if '^NSEI' in raw_data.columns.get_level_values(1) else pd.DataFrame()
    vix = raw_data.xs('^INDIAVIX', axis=1, level=1).dropna(how='all') if '^INDIAVIX' in raw_data.columns.get_level_values(1) else pd.DataFrame()

    if not nifty.empty:
        nifty['MA200'] = nifty['Close'].rolling(200).mean()

    logging.info("Calculating technical indicators across all stocks...")
    stock_signals = {}
    for ticker in tickers:
        try:
            if ticker not in raw_data.columns.get_level_values(1):
                continue
            df_ticker = raw_data.xs(ticker, axis=1, level=1).dropna(how='all')
            if df_ticker.empty or len(df_ticker) < 252:
                continue
            if df_ticker.index.tz is not None:
                df_ticker.index = df_ticker.index.tz_localize(None)
            
            signals = compute_signals(df_ticker, config)
            stock_signals[ticker] = signals
        except Exception as e:
            continue

    date_range = pd.date_range(start=start_dt, end=end_dt, freq='B')
    
    results_by_date = []

    for process_date in date_range:
        date_str = process_date.strftime('%Y-%m-%d')
        all_longs_off = False
        stop_widen_atr = 0.0
        
        if not nifty.empty:
            nifty_slice = nifty.loc[:process_date]
            if not nifty_slice.empty:
                current_nifty = nifty_slice['Close'].iloc[-1]
                ma200 = nifty_slice['MA200'].iloc[-1]
                if current_nifty < ma200:
                    all_longs_off = True

        if not vix.empty:
            vix_slice = vix.loc[:process_date]
            if not vix_slice.empty:
                current_vix = vix_slice['Close'].iloc[-1]
                if current_vix > 18:
                    stop_widen_atr = 0.5

        if all_longs_off:
            results_by_date.append({
                'Invest_Date': date_str,
                'Capital': config.CAPITAL,
                'Profit': 0.0,
                'Return_%': 0.0,
                'Trades': 0,
                'Note': 'Market Below 200DMA'
            })
            continue

        candidates = []
        for ticker, signals in stock_signals.items():
            sig_slice = signals.loc[:process_date]
            if sig_slice.empty:
                continue
            
            if sig_slice.index[-1] != process_date:
                continue

            row = sig_slice.iloc[-1]
            if not row['Valid']:
                continue
                
            if pd.isna(row['Momentum_Score']):
                continue

            candidates.append({
                'Ticker': ticker,
                'Price': row['Close'],
                'ATR': row['ATR'],
                'ATR_%': row['ATR_%'],
                'Vol_Surge': row['Vol_Surge'],
                'Momentum_Score': row['Momentum_Score'],
                'Breakout_Candidate': row['Breakout_Candidate'],
                'Pullback_Candidate': row['Pullback_Candidate'],
                'RSI2': row['RSI2']
            })

        if not candidates:
            results_by_date.append({
                'Invest_Date': date_str,
                'Capital': config.CAPITAL,
                'Profit': 0.0,
                'Return_%': 0.0,
                'Trades': 0,
                'Note': 'No Candidates Passed'
            })
            continue

        df_cand = pd.DataFrame(candidates).sort_values(by='Momentum_Score', ascending=False)
        
        momentum_candidates = df_cand.head(5)
        breakout_candidates = df_cand[df_cand['Breakout_Candidate']].sort_values(by='Vol_Surge', ascending=False).head(3)
        pullback_candidates = df_cand[df_cand['Pullback_Candidate']].sort_values(by='RSI2').head(3)

        risk_amount_rs = config.CAPITAL * config.RISK_PER_TRADE
        trade_plans = []

        def add_plan(row, label):
            entry_price = row['Price']
            atr = row['ATR']
            stop_loss = entry_price - atr * (1 + stop_widen_atr)
            t1_target = entry_price + 1.5 * atr
            t2_target = entry_price + 3 * atr
            
            stop_distance_pct = ((entry_price - stop_loss) / entry_price) * 100
            if stop_distance_pct > 5.0: return
            risk_per_share = entry_price - stop_loss
            if risk_per_share <= 0: return
            
            quantity = int(risk_amount_rs // risk_per_share)
            if quantity < 1: return
            
            trade_plans.append({
                'Strategy': label,
                'Ticker': row['Ticker'],
                'Entry_Price': entry_price,
                'Quantity': quantity,
                'Stop_Loss': stop_loss,
                'T1': t1_target,
                'T2': t2_target
            })

        for _, row in momentum_candidates.iterrows(): add_plan(row, "Momentum")
        for _, row in breakout_candidates.iterrows(): add_plan(row, "Breakout")
        for _, row in pullback_candidates.iterrows(): add_plan(row, "Pullback")

        if not trade_plans:
            results_by_date.append({
                'Invest_Date': date_str,
                'Capital': config.CAPITAL,
                'Profit': 0.0,
                'Return_%': 0.0,
                'Trades': 0,
                'Note': 'No Valid Trade Plans'
            })
            continue

        daily_profit = 0.0
        trades_count = 0
        for plan in trade_plans:
            ticker = plan['Ticker']
            df_ticker = stock_signals[ticker]
            forward_data = df_ticker.loc[process_date:]
            if len(forward_data) <= 1:
                continue 
                
            forward_data = forward_data.iloc[1:]
            
            exit_price, exit_date, status = simulate_trades_fast(
                forward_data, process_date, plan['Entry_Price'], plan['Stop_Loss'], plan['T1'], plan['T2']
            )
            
            profit = (exit_price - plan['Entry_Price']) * plan['Quantity']
            daily_profit += profit
            trades_count += 1
            
        return_pct = (daily_profit / config.CAPITAL) * 100
        
        results_by_date.append({
            'Invest_Date': date_str,
            'Capital': config.CAPITAL,
            'Profit': round(daily_profit, 2),
            'Return_%': round(return_pct, 2),
            'Trades': trades_count,
            'Note': ''
        })

    final_df = pd.DataFrame(results_by_date)
    print("\n" + "="*80)
    print("BACKTEST COMPARISON: RETURN BY INVESTMENT DATE")
    print("="*80)
    print(final_df.to_string(index=False))
    
    if len(final_df) >= 2:
        start_ret = final_df.iloc[0]['Return_%']
        end_ret = final_df.iloc[-1]['Return_%']
        print("\n" + "="*80)
        print(f"Comparing Strategy Start Dates:")
        print(f"Investing on {final_df.iloc[0]['Invest_Date']}: {start_ret:.2f}% Return")
        print(f"Investing on {final_df.iloc[-1]['Invest_Date']}: {end_ret:.2f}% Return")
        print(f"Difference: {end_ret - start_ret:.2f}%")
        print("="*80)
    
    final_df.to_csv("backtest_comparison.csv", index=False)
    logging.info("Saved results to backtest_comparison.csv")

if __name__ == "__main__":
    main()
