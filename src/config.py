from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # Layer 4 - Position Sizing & Risk Control
    CAPITAL: float = 500000.0        # Total Portfolio Capital (₹)
    RISK_PER_TRADE: float = 0.01     # 1% risk rule
    MAX_HEAT: float = 0.05           # 5% max portfolio heat (max 5 open positions)
    
    # Layer 2 - Stock Universe & Screening Filters
    MIN_PRICE: float = 50.0          # Avoid tick slippage on penny stocks
    MIN_TURNOVER: float = 50000000.0 # ₹5 crore average daily turnover
    MIN_ATR_PCT: float = 1.5         # Volatility filter (min 1.5% daily move)
    MAX_ATR_PCT: float = 5.0         # Volatility filter (max 5% daily move)
    
    # Technicals
    DAYS_BACK: int = 900             # Ensure enough history for 200DMA and 52W Highs

    # Tickers
    TICKERS: List[str] = field(default_factory=lambda: [
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
    ])
