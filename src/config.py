from dataclasses import dataclass

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
