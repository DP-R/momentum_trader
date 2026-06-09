import pandas as pd
from src.trade_plan import TradePlanner
from src.config import Config

def test_display_trade_plan():
    config = Config(CAPITAL=500000, RISK_PER_TRADE=0.01)
    regime = {"reduce_size_pct": 0.0, "vix_value": 12.0}
    planner = TradePlanner(config=config, regime=regime)
    
    row = pd.Series({
        'Ticker': 'TEST',
        'Price': 100.0,
        'ATR': 2.0,
        'ATR_%': 2.0,
        'Vol_Surge': 1.5,
        'RSI2': 5.0,
        'Swing_Low': 96.0
    })
    
    output, plan_dict = planner.display_trade_plan(row, "Momentum", risk_amount_rs=5000.0, stop_widen_atr=0.0)

    assert "Momentum" in output
    assert "Buy" in output
    assert "Stop Loss:" in output
    assert "T1:" in output
    assert "T2:" in output

def test_display_trade_plan_skip_wide_stop():
    config = Config(CAPITAL=500000, RISK_PER_TRADE=0.01)
    regime = {"reduce_size_pct": 0.0, "vix_value": 12.0}
    planner = TradePlanner(config=config, regime=regime)
    
    row = pd.Series({
        'Ticker': 'TEST',
        'Price': 100.0,
        'ATR': 10.0,  # This will create a wide stop (>8%)
        'ATR_%': 10.0,
        'Vol_Surge': 1.5,
        'RSI2': 5.0,
        'Swing_Low': 90.0
    })

    output, plan_dict = planner.display_trade_plan(row, "Momentum", risk_amount_rs=5000.0, stop_widen_atr=0.0)
    assert "SKIP: Stop loss too wide" in output

def test_display_trade_plan_invalid_stop():
    config = Config(CAPITAL=500000, RISK_PER_TRADE=0.01)
    regime = {"reduce_size_pct": 0.0, "vix_value": 12.0}
    planner = TradePlanner(config=config, regime=regime)
    
    row = pd.Series({
        'Ticker': 'TEST',
        'Price': 100.0,
        'ATR': 0.0,  # This will create an invalid stop
        'ATR_%': 0.0,
        'Vol_Surge': 1.5,
        'RSI2': 5.0,
        'Swing_Low': 100.0
    })

    output, plan_dict = planner.display_trade_plan(row, "Breakout", risk_amount_rs=5000.0, stop_widen_atr=0.0)
    assert "SKIP: Invalid stop level." in output

def test_display_trade_plan_small_position_size():
    # Capital 100, risk 0.01 = 1 rs risk amount
    config = Config(CAPITAL=100, RISK_PER_TRADE=0.01)
    regime = {"reduce_size_pct": 0.0, "vix_value": 12.0}
    planner = TradePlanner(config=config, regime=regime)
    
    row = pd.Series({
        'Ticker': 'TEST',
        'Price': 100.0,
        'ATR': 2.0,  # risk per share = 2.0
        'ATR_%': 2.0,
        'Vol_Surge': 1.5,
        'RSI2': 5.0,
        'Swing_Low': 98.0
    })

    output, plan_dict = planner.display_trade_plan(row, "Breakout", risk_amount_rs=1.0, stop_widen_atr=0.0)
    assert "SKIP: Position size too small after risk sizing." in output

def test_generate_trade_plans():
    config = Config(CAPITAL=500000, RISK_PER_TRADE=0.01, MAX_HEAT=0.05) # Max 5 positions
    regime = {"reduce_size_pct": 0.0, "vix_value": 12.0, "strategy_preference": "NEUTRAL"}
    planner = TradePlanner(config=config, regime=regime)
    
    df = pd.DataFrame({
        'Ticker': ['MOM1', 'BRK1', 'PUL1'],
        'Price': [100.0, 100.0, 100.0],
        'ATR': [1.0, 1.0, 1.0],
        'ATR_%': [1.0, 1.0, 1.0],
        'Vol_Surge': [2.0, 2.0, 2.0],
        'RSI2': [5.0, 5.0, 5.0],
        'Swing_Low': [99.0, 99.0, 99.0],
        'Breakout_Candidate': [False, True, False],
        'Pullback_Candidate': [False, False, True]
    })
    
    plans_str, plans_data = planner.generate_trade_plans(df)
    # We have 3 rows. The logic checks pullback, breakout, then momentum. 
    # Should get 1 pullback, 1 breakout, 1 momentum.
    assert len(plans_str) == 5
    assert any("Momentum" in p for p in plans_str)
    assert any("Breakout" in p for p in plans_str)
    assert any("Pullback" in p for p in plans_str)
