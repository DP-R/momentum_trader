import logging
import sys
import json
import argparse
import pandas as pd
from datetime import datetime, timedelta
from src.config import Config
from src.data_extractor import DataFetcher
from src.screening import StockScreener
from src.trade_plan import TradePlanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Momentum Trader")
    parser.add_argument("--as-of-date", type=str, help="Backtest as of a specific date (YYYY-MM-DD)")
    parser.add_argument("--start-date", type=str, help="Backtest start date for a range (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="Backtest end date for a range (YYYY-MM-DD)")
    args = parser.parse_args()

    # Determine dates to process
    dates_to_process = []
    if args.start_date and args.end_date:
        start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
        current_dt = start_dt
        while current_dt <= end_dt:
            # Skip weekends
            if current_dt.weekday() < 5:
                dates_to_process.append(current_dt.strftime('%Y-%m-%d'))
            current_dt += timedelta(days=1)
    elif args.as_of_date:
        dates_to_process = [args.as_of_date]
    else:
        dates_to_process = [datetime.today().strftime('%Y-%m-%d')]

    # 1. Initialize Configuration
    config = Config()
    logging.info("Initialized configuration.")

    # Fetch Nifty 150 (Midcap 150)
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
    logging.info(f"Loaded {len(tickers)} hardcoded tickers from Nifty Midcap 150.")

    # Setup Data Fetcher
    # Use the earliest date to preload enough data for the whole range
    earliest_date = dates_to_process[0]
    data_fetcher = DataFetcher(days_back=config.DAYS_BACK, as_of_date=earliest_date)
    # Actually, we need data up to the latest date. Modify DataFetcher internally or just override dates here.
    start_fetch = (datetime.strptime(earliest_date, '%Y-%m-%d') - timedelta(days=config.DAYS_BACK)).strftime('%Y-%m-%d')
    end_fetch = (datetime.strptime(dates_to_process[-1], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Temporarily monkey-patch get_start_end_dates for preload to fetch the FULL range
    def custom_get_dates():
        return start_fetch, end_fetch
    data_fetcher.get_start_end_dates = custom_get_dates
    
    # Preload all ticker data at once to significantly improve performance
    data_fetcher.preload_data(tickers)
    
    # Restore original method behavior so it dynamically updates based on data_fetcher.as_of_date
    del data_fetcher.get_start_end_dates
    
    all_results_dfs = []

    for process_date in dates_to_process:
        logging.info(f"\n{'='*60}\nProcessing for Date: {process_date}\n{'='*60}")
        data_fetcher.as_of_date = process_date
        
        # Setup Screener
        screener = StockScreener(
            data_fetcher=data_fetcher, 
            config=config
        )

        logging.info(f"Screening {len(tickers)} tickers...")
        screener_df, regime = screener.screen_stocks(tickers)
        
        if len(dates_to_process) == 1:
            print("\n" + "="*50)
            print("LAYER 1: MARKET REGIME (5-Point Check)")
            print("="*50)
            print(json.dumps(regime, indent=4))
            print("="*50 + "\n")
        
        if regime.get("all_longs_off", False):
            logging.info(f"Market is below 200-DMA on {process_date}. NO TRADES.")
            continue

        if screener_df.empty:
            logging.info(f"No stocks passed the screener on {process_date}.")
            continue

        logging.info(f"Found {len(screener_df)} candidates. Generating trade plans...")

        # Setup Trade Planner
        planner = TradePlanner(
            config=config, 
            regime=regime
        )

        trade_plans_str, trade_plans_data = planner.generate_trade_plans(screener_df)

        if len(dates_to_process) == 1:
            print("\n" + "="*50)
            print("MOMENTUM TRADER - 5-LAYER TRADE PLANS")
            print("="*50 + "\n")
            for plan in trade_plans_str:
                print(plan)
                print("-" * 50)
            
        if trade_plans_data:
            from src.simulator import simulate_trades
            results_df = simulate_trades(trade_plans_data, process_date, data_fetcher)
            if not results_df.empty:
                all_results_dfs.append(results_df)

    if all_results_dfs:
        final_results = pd.concat(all_results_dfs, ignore_index=True)
        # Assuming we save to excel or display
        if len(dates_to_process) > 1:
            excel_filename = f"backtest_results_{dates_to_process[0]}_to_{dates_to_process[-1]}.xlsx"
        else:
            excel_filename = f"backtest_results_{dates_to_process[0]}.xlsx"
            
        final_results.to_excel(excel_filename, index=False)
        logging.info(f"Simulation complete. Results saved to {excel_filename}")
        
        print("\n" + "="*50)
        print("SIMULATION RESULTS (PROFIT/LOSS)")
        print("="*50 + "\n")
        print(final_results[['Ticker', 'Strategy', 'Entry Date', 'Status', 'Return (%)', 'Profit/Loss (₹)']].to_string(index=False))
        
        total_profit = final_results['Profit/Loss (₹)'].sum()
        print("\n" + "-"*50)
        print(f"TOTAL PROFIT/LOSS: ₹{total_profit:,.2f}")
        print("-"*50)
    else:
        logging.info("No trades were simulated across the selected dates.")

if __name__ == "__main__":
    main()
