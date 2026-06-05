import pytest
import pandas as pd
from src.indicators import calculate_atr, calculate_adx, calculate_rsi, calculate_momentum_score, check_52w_breakout, check_20dma_pullback

def test_calculate_atr():
    data = {
        'High': [10, 11, 12, 13, 14],
        'Low': [9, 8, 7, 6, 5],
        'Close': [10, 10, 10, 10, 10]
    }
    df = pd.DataFrame(data)
    atr = calculate_atr(df, period=3)
    assert atr.iloc[-1] == pytest.approx(7.0, rel=1e-2)

def test_calculate_adx():
    data = {
        'High': [10, 11, 12, 13, 14],
        'Low': [9, 8, 7, 6, 5],
        'Close': [10, 10, 10, 10, 10]
    }
    df = pd.DataFrame(data)
    adx = calculate_adx(df, period=3)
    assert adx.iloc[-1] == pytest.approx(0.0, rel=1e-2)

def test_calculate_rsi():
    data = {
        'Close': [10, 11, 12, 11, 10]
    }
    df = pd.DataFrame(data)
    rsi = calculate_rsi(df, period=2)
    assert rsi.iloc[-1] == pytest.approx(25.0, rel=1e-2)

def test_calculate_momentum_score():
    data = {
        'Close': [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] * 23  # >252 rows
    }
    df = pd.DataFrame(data)
    score = calculate_momentum_score(df)
    assert score is not None

def test_check_52w_breakout():
    data = {
        'High': [11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31] * 23,
        'Low': [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29] * 23,
        'Close': [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] * 23,
        'Volume': [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600] * 23
    }
    df = pd.DataFrame(data)
    result = check_52w_breakout(df)
    assert isinstance(result, bool)

def test_check_20dma_pullback():
    data = {
        'High': [11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31] * 20,
        'Low': [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29] * 20,
        'Close': [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] * 20,
        'Open': [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] * 20,
        'Volume': [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600] * 20
    }
    df = pd.DataFrame(data)
    result = check_20dma_pullback(df)
    assert isinstance(result, bool)
