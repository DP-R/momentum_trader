import logging
import sys
import json
import argparse
from src.config import Config
from src.data_extractor import DataFetcher
from src.screening import StockScreener
from src.trade_plan import TradePlanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Momentum Trader")
    parser.add_argument("--as-of-date", type=str, help="Backtest as of a specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    # 1. Initialize Configuration
    config = Config()
    logging.info("Initialized configuration.")

    # 2. Setup Data Fetcher
    data_fetcher = DataFetcher(days_back=config.DAYS_BACK, as_of_date=args.as_of_date)
    
    # 3. Setup Screener
    screener = StockScreener(
        data_fetcher=data_fetcher, 
        config=config
    )

    # 4. Fetch Nifty 150 (Midcap 150)
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
    
    logging.info(f"Screening {len(tickers)} tickers...")
    screener_df, regime = screener.screen_stocks(tickers)
    
    print("\n" + "="*50)
    print("LAYER 1: MARKET REGIME (5-Point Check)")
    print("="*50)
    print(json.dumps(regime, indent=4))
    print("="*50 + "\n")
    
    if regime.get("all_longs_off", False):
        logging.info("Market is below 200-DMA. NO TRADES. EXITING.")
        sys.exit(0)

    if screener_df.empty:
        logging.info("No stocks passed the screener (Liquidity / ATR filters).")
        sys.exit(0)

    logging.info(f"Found {len(screener_df)} candidates. Generating trade plans based on Strategy preference...")

    # 5. Setup Trade Planner
    planner = TradePlanner(
        config=config, 
        regime=regime
    )

    trade_plans_str, trade_plans_data = planner.generate_trade_plans(screener_df)

    # 6. Output results
    print("\n" + "="*50)
    print("MOMENTUM TRADER - 5-LAYER TRADE PLANS")
    print("="*50 + "\n")
    for plan in trade_plans_str:
        print(plan)
        print("-" * 50)
        
    # 7. Simulate trades if backtesting
    if args.as_of_date and trade_plans_data:
        logging.info("Starting forward simulation of generated trades...")
        from src.simulator import simulate_trades
        results_df = simulate_trades(trade_plans_data, args.as_of_date)
        if not results_df.empty:
            excel_filename = f"backtest_results_{args.as_of_date}.xlsx"
            results_df.to_excel(excel_filename, index=False)
            logging.info(f"Simulation complete. Results saved to {excel_filename}")
            
            print("\n" + "="*50)
            print("SIMULATION RESULTS (PROFIT/LOSS)")
            print("="*50 + "\n")
            print(results_df[['Ticker', 'Strategy', 'Status', 'Return (%)', 'Profit/Loss (₹)']].to_string(index=False))
            
            total_profit = results_df['Profit/Loss (₹)'].sum()
            print("\n" + "-"*50)
            print(f"TOTAL PROFIT/LOSS: ₹{total_profit:,.2f}")
            print("-"*50)

if __name__ == "__main__":
    main()
