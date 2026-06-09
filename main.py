import logging
import json
import argparse
import pandas as pd
from datetime import datetime, timedelta
from src.config import Config
from src.data_extractor import DataFetcher
from src.screening import StockScreener
from src.trade_plan import TradePlanner
from src.simulator import simulate_trades

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Momentum Trader")
    parser.add_argument("--as-of-date", type=str, help="Backtest as of a specific date (YYYY-MM-DD)")
    parser.add_argument("--start-date", type=str, help="Backtest start date for a range (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="Backtest end date for a range (YYYY-MM-DD)")
    args = parser.parse_args()

    # Determine dates to process
    if args.start_date and args.end_date:
        start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
        dates_to_process = [
            (start_dt + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range((end_dt - start_dt).days + 1)
            if (start_dt + timedelta(days=i)).weekday() < 5
        ]
    elif args.as_of_date:
        dates_to_process = [args.as_of_date]
    else:
        dates_to_process = [datetime.today().strftime('%Y-%m-%d')]

    if not dates_to_process:
        logging.info("No valid dates to process.")
        return

    # Initialize Configuration
    config = Config()
    logging.info("Initialized configuration.")

    # Fetch Nifty 150 (Midcap 150) tickers
    tickers = config.TICKERS
    logging.info(f"Loaded {len(tickers)} hardcoded tickers from Nifty Midcap 150.")

    # Setup Data Fetcher
    earliest_date = dates_to_process[0]
    data_fetcher = DataFetcher(days_back=config.DAYS_BACK, as_of_date=earliest_date)
    
    start_fetch = (datetime.strptime(earliest_date, '%Y-%m-%d') - timedelta(days=config.DAYS_BACK)).strftime('%Y-%m-%d')
    end_fetch = (datetime.strptime(dates_to_process[-1], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Preload all ticker data at once to significantly improve performance
    # Include market indices in the preload to prevent network calls during regime checks
    tickers_to_preload = tickers + ["^NSEI", "^INDIAVIX"]
    data_fetcher.preload_data(tickers_to_preload, start_date=start_fetch, end_date=end_fetch)
    
    all_results_dfs = []
    is_single_day = len(dates_to_process) == 1

    for process_date in dates_to_process:
        logging.info(f"\n{'='*60}\nProcessing for Date: {process_date}\n{'='*60}")
        data_fetcher.as_of_date = process_date
        
        # Setup Screener
        screener = StockScreener(data_fetcher=data_fetcher, config=config)
        logging.info(f"Screening {len(tickers)} tickers...")
        screener_df, regime = screener.screen_stocks(tickers)
        
        if is_single_day:
            print(f"\n{'='*50}\nLAYER 1: MARKET REGIME (5-Point Check)\n{'='*50}")
            print(json.dumps(regime, indent=4))
            print(f"{'='*50}\n")
        
        if regime.get("all_longs_off", False):
            logging.info(f"Market is below 200-DMA on {process_date}. NO TRADES.")
            continue

        if screener_df.empty:
            logging.info(f"No stocks passed the screener on {process_date}.")
            continue

        logging.info(f"Found {len(screener_df)} candidates. Generating trade plans...")

        # Setup Trade Planner
        planner = TradePlanner(config=config, regime=regime)
        trade_plans_str, trade_plans_data = planner.generate_trade_plans(screener_df)

        if is_single_day:
            print(f"\n{'='*50}\nMOMENTUM TRADER - 5-LAYER TRADE PLANS\n{'='*50}\n")
            for plan in trade_plans_str:
                print(plan)
                print("-" * 50)
            
        if trade_plans_data:
            results_df = simulate_trades(trade_plans_data, process_date, data_fetcher)
            if not results_df.empty:
                all_results_dfs.append(results_df)

    if all_results_dfs:
        final_results = pd.concat(all_results_dfs, ignore_index=True)
        
        excel_filename = f"backtest_results_{dates_to_process[0]}"
        if not is_single_day:
            excel_filename += f"_to_{dates_to_process[-1]}"
        excel_filename += ".xlsx"
            
        final_results.to_excel(excel_filename, index=False)
        logging.info(f"Simulation complete. Results saved to {excel_filename}")
        
        print(f"\n{'='*50}\nSIMULATION RESULTS (PROFIT/LOSS)\n{'='*50}\n")
        print(final_results[['Ticker', 'Strategy', 'Entry Date', 'Status', 'Return (%)', 'Profit/Loss (₹)']].to_string(index=False))
        
        total_profit = final_results['Profit/Loss (₹)'].sum()
        print(f"\n{'-'*50}\nTOTAL PROFIT/LOSS: ₹{total_profit:,.2f}\n{'-'*50}")
    else:
        logging.info("No trades were simulated across the selected dates.")

if __name__ == "__main__":
    main()
