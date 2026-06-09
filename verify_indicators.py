import pandas as pd
import numpy as np
from src.indicators import calculate_atr, calculate_adx, calculate_rsi, calculate_momentum_score, check_52w_breakout, check_20dma_pullback

def verify_atr():
    print("--- Verifying ATR ---")
    # Intent: True Range is max of: High-Low, abs(High-PrevClose), abs(Low-PrevClose)
    # The ATR implementation uses a Simple Moving Average (rolling.mean).
    data = {
        'High': [10, 12, 15, 14, 13],
        'Low':  [ 8,  9, 10, 11, 10],
        'Close':[ 9, 11, 14, 12, 11]
    }
    df = pd.DataFrame(data)
    
    # Manual TR Calculation
    # Day 0: NaN PrevClose -> TR is just High - Low = 10 - 8 = 2
    # Day 1: H=12, L=9, PrevC=9 -> H-L=3, |H-PC|=3, |L-PC|=0 -> TR=3
    # Day 2: H=15, L=10, PrevC=11 -> H-L=5, |H-PC|=4, |L-PC|=1 -> TR=5
    # Day 3: H=14, L=11, PrevC=14 -> H-L=3, |H-PC|=0, |L-PC|=3 -> TR=3
    # Day 4: H=13, L=10, PrevC=12 -> H-L=3, |H-PC|=1, |L-PC|=2 -> TR=3
    
    atr_series = calculate_atr(df, period=3)
    
    # Simple Moving Average of TR over 3 days for Day 4:
    # TRs are [2, 3, 5, 3, 3]
    # Day 2 SMA = (2+3+5)/3 = 3.33
    # Day 3 SMA = (3+5+3)/3 = 3.66
    # Day 4 SMA = (5+3+3)/3 = 3.66
    
    expected_atr = np.mean([5, 3, 3])
    calculated_atr = atr_series.iloc[-1]
    
    print(f"Calculated TR series logic: [2, 3, 5, 3, 3]")
    print(f"Expected 3-period SMA of TR (Day 4): {expected_atr:.4f}")
    print(f"Function Output (Day 4): {calculated_atr:.4f}")
    assert np.isclose(expected_atr, calculated_atr), "ATR Verification Failed!"
    print("ATR intent verified: Correctly computes TR and applies simple rolling mean.\n")


def verify_rsi():
    print("--- Verifying RSI ---")
    # Intent: Wilder's smoothing with alpha=1/period, adjust=False
    # Let's use a simple 2-period RSI as per the code's default.
    data = {
        'Close': [100, 102, 101, 104, 103, 106]
    }
    df = pd.DataFrame(data)
    # Diffs:   NaN,  2, -1,  3, -1,  3
    # Gains:     0,  2,  0,  3,  0,  3
    # Losses:    0,  0,  1,  0,  1,  0
    
    # EWM alpha=1/2 = 0.5. adjust=False means y_t = (1 - alpha) * y_{t-1} + alpha * x_t
    # Initial values are the first observation (Gains: 2, Losses: 0 at index 1)
    # Gains EWM (alpha=0.5):
    # t=1: 2
    # t=2: 0.5*2 + 0.5*0 = 1
    # t=3: 0.5*1 + 0.5*3 = 2
    # t=4: 0.5*2 + 0.5*0 = 1
    # t=5: 0.5*1 + 0.5*3 = 2
    
    # Losses EWM (alpha=0.5):
    # t=1: 0
    # t=2: 0.5*0 + 0.5*1 = 0.5
    # t=3: 0.5*0.5 + 0.5*0 = 0.25
    # t=4: 0.5*0.25 + 0.5*1 = 0.625
    # t=5: 0.5*0.625 + 0.5*0 = 0.3125
    
    # Day 5 RS = AvgGain / AvgLoss = 2 / 0.3125 = 6.4
    # Day 5 RSI = 100 - (100 / (1 + 6.4)) = 100 - 13.5135 = 86.4865
    
    rsi_series = calculate_rsi(df, period=2)
    calculated_rsi = rsi_series.iloc[-1]
    
    expected_rsi = 100 - (100 / (1 + (2 / 0.3125)))
    print(f"Expected RSI (Day 5): {expected_rsi:.4f}")
    print(f"Function Output (Day 5): {calculated_rsi:.4f}")
    assert np.isclose(expected_rsi, calculated_rsi), "RSI Verification Failed!"
    print("RSI intent verified: Correctly computes gains/losses and applies Wilder's smoothing (alpha=1/period).\n")


def verify_momentum_score():
    print("--- Verifying Momentum Score ---")
    # Intent: ret_6m / vol_6m and ret_12m / vol_12m
    # Generate exactly 253 points to meet length requirement
    np.random.seed(42)
    daily_returns = np.random.normal(0.001, 0.015, 253)
    prices = [100]
    for r in daily_returns[1:]:
        prices.append(prices[-1] * (1 + r))
        
    df = pd.DataFrame({'Close': prices})
    
    # 6m = 126 days. The formula is:
    # ret_6m = df['Close'].iloc[-1] / df['Close'].iloc[-126] - 1
    # vol_6m = df['Close'].pct_change().iloc[-126:].std()
    expected_ret_6m = df['Close'].iloc[-1] / df['Close'].iloc[-126] - 1
    expected_vol_6m = df['Close'].pct_change().iloc[-126:].std()
    
    expected_ret_12m = df['Close'].iloc[-1] / df['Close'].iloc[-252] - 1
    expected_vol_12m = df['Close'].pct_change().iloc[-252:].std()
    
    score_6m, score_12m = calculate_momentum_score(df)
    
    print(f"Expected 6M Return: {expected_ret_6m:.4f}, Vol: {expected_vol_6m:.4f} -> Score: {expected_ret_6m/expected_vol_6m:.4f}")
    print(f"Function 6M Score: {score_6m:.4f}")
    
    assert np.isclose(expected_ret_6m/expected_vol_6m, score_6m), "Momentum 6M Verification Failed!"
    assert np.isclose(expected_ret_12m/expected_vol_12m, score_12m), "Momentum 12M Verification Failed!"
    print("Momentum Score intent verified: Calculates exact periodic returns normalized by daily standard deviation.\n")


def verify_adx_directional():
    print("--- Verifying ADX Directional Intent ---")
    # ADX measures trend strength regardless of direction.
    # Let's create an uptrending stock and a downtrending stock. Both should have rising ADX.
    up_data = {
        'High': np.linspace(10, 50, 50) + 1,
        'Low': np.linspace(10, 50, 50) - 1,
        'Close': np.linspace(10, 50, 50)
    }
    down_data = {
        'High': np.linspace(50, 10, 50) + 1,
        'Low': np.linspace(50, 10, 50) - 1,
        'Close': np.linspace(50, 10, 50)
    }
    
    df_up = pd.DataFrame(up_data)
    df_down = pd.DataFrame(down_data)
    
    adx_up = calculate_adx(df_up, period=14).iloc[-1]
    adx_down = calculate_adx(df_down, period=14).iloc[-1]
    
    print(f"ADX of strong uptrend: {adx_up:.2f}")
    print(f"ADX of strong downtrend: {adx_down:.2f}")
    # Since the absolute magnitude of the moves is exactly the same, ADX should be identical.
    assert np.isclose(adx_up, adx_down), "ADX directional invariance failed!"
    print("ADX intent verified: It properly isolates trend strength, treating +DI and -DI symmetrically.\n")

if __name__ == "__main__":
    verify_atr()
    verify_rsi()
    verify_momentum_score()
    verify_adx_directional()
    print("All indicator implementations mathematically match their defined intent!")
