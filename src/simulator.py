import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def simulate_trades(trade_plans_data, as_of_date, data_fetcher=None):
    if not trade_plans_data:
        return pd.DataFrame()

    start_date = (datetime.strptime(as_of_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')

    results = []

    for plan in trade_plans_data:
        ticker = plan['Ticker']
        entry_price = plan['Entry_Price']
        qty = plan['Quantity']
        t1 = plan['T1']
        t2 = plan['T2']
        initial_stop = plan['Stop_Loss']

        logger.info(f"Simulating {ticker} from {start_date}...")

        try:
            if data_fetcher:
                df = data_fetcher.fetch_historical_data(ticker, start_date, end_date)
            else:
                import yfinance as yf
                df = yf.Ticker(ticker).history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"No forward data for {ticker}")
                continue

            status = 'Open'
            exit_price = None
            exit_date = None
            current_stop = initial_stop
            for date, row in df.iterrows():
                low = row['Low']
                high = row['High']
                
                # Check for stop loss hit
                if low <= current_stop:
                    # If gap down below stop loss, exit at Open
                    exit_price = row['Open'] if row['Open'] < current_stop else current_stop
                    status = 'Closed (Stop Loss)' if current_stop == initial_stop else 'Closed (Trailing Stop)'
                    exit_date = date.strftime('%Y-%m-%d')
                    break
                    
                # Check for T2 hit
                if high >= t2:
                    # Exit at T2
                    exit_price = row['Open'] if row['Open'] > t2 else t2
                    status = 'Closed (T2 Hit)'
                    exit_date = date.strftime('%Y-%m-%d')
                    break
                    
                # Check for T1 hit (trail stop to entry)
                if high >= t1 and current_stop < entry_price:
                    current_stop = entry_price
            
            # If still open, use last close
            if status == 'Open':
                exit_price = df['Close'].iloc[-1]
                exit_date = df.index[-1].strftime('%Y-%m-%d')
                
            profit = (exit_price - entry_price) * qty
            profit_pct = (exit_price - entry_price) / entry_price * 100
            
            results.append({
                'Ticker': ticker,
                'Strategy': plan['Strategy'],
                'Entry Date': as_of_date,
                'Entry Price': round(entry_price, 2),
                'Quantity': qty,
                'Status': status,
                'Exit Date': exit_date,
                'Exit Price': round(exit_price, 2),
                'Profit/Loss (₹)': round(profit, 2),
                'Return (%)': round(profit_pct, 2)
            })
            
        except Exception as e:
            logger.error(f"Error simulating {ticker}: {e}")
            
    return pd.DataFrame(results)
