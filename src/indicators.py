import pandas as pd
import numpy as np
def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_adx(df, period=14):
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff()

    plus_dm[plus_dm < 0] = 0
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()

    tr = calculate_atr(df, 1)
    atr_smooth = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_smooth)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_smooth)

    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx

def calculate_rsi(df, period=2):
    delta = df['Close'].diff()
    gain = delta.mask(delta < 0, 0.0)
    loss = -delta.mask(delta > 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def zscore(series):
    mean = series.mean()
    std = series.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(np.nan, index=series.index)
    return (series - mean) / std

def calculate_momentum_score(df):
    if len(df) < 252:
        return np.nan, np.nan

    ret_6m = df['Close'].iloc[-1] / df['Close'].iloc[-126] - 1
    vol_6m = df['Close'].pct_change().iloc[-126:].std()
    ret_12m = df['Close'].iloc[-1] / df['Close'].iloc[-252] - 1
    vol_12m = df['Close'].pct_change().iloc[-252:].std()

    if vol_6m <= 0 or vol_12m <= 0:
        return np.nan, np.nan

    return (ret_6m / vol_6m), (ret_12m / vol_12m)

def check_52w_breakout(df):
    if len(df) < 252:
        return False, {}

    current_price = df['Close'].iloc[-1]
    prev_52w_high = df['Close'].iloc[-253:-1].max()
    avg_vol_50 = df['Volume'].iloc[-51:-1].mean()
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    ma200 = df['Close'].rolling(200).mean().iloc[-1]
    ma50_prev = df['Close'].rolling(50).mean().iloc[-6]
    ma200_prev = df['Close'].rolling(200).mean().iloc[-6]

    breakout = current_price > prev_52w_high and current_price > df['Close'].iloc[-2]
    volume_surge = avg_vol_50 > 0 and df['Volume'].iloc[-1] >= 1.5 * avg_vol_50
    trend_ok = current_price > ma50 and current_price > ma200
    dma_rising = ma50 > ma50_prev and ma200 > ma200_prev
    
    # 3-week base check: past 15 days max/min shouldn't vary by more than 15%
    base_high = df['High'].iloc[-16:-1].max()
    base_low = df['Low'].iloc[-16:-1].max() # Actually we want min
    base_low = df['Low'].iloc[-16:-1].min()
    base_tight = False
    if base_low > 0:
        base_tight = (base_high / base_low - 1) < 0.15

    is_candidate = breakout and volume_surge and trend_ok and dma_rising and base_tight
    
    # Stop loss: low of breakout candle or recent swing low (using 5 day low)
    swing_low = df['Low'].iloc[-5:].min()
    candle_low = df['Low'].iloc[-1]
    stop_loss = min(swing_low, candle_low)
    
    return is_candidate, {"stop_loss": stop_loss}

def check_20dma_pullback(df):
    if len(df) < 200:
        return False, {}

    current_price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    ma200 = df['Close'].rolling(200).mean().iloc[-1]
    rsi2 = calculate_rsi(df, 2).iloc[-1]

    near_20dma = abs(current_price - ma20) / ma20 <= 0.01
    in_uptrend = current_price > ma50 and current_price > ma200
    bullish_reversal = df['Close'].iloc[-1] > df['Open'].iloc[-1] and df['Close'].iloc[-1] > df['Close'].iloc[-2]

    is_candidate = in_uptrend and near_20dma and rsi2 < 10 and bullish_reversal
    
    # Stop loss: low of signal candle or swing low
    swing_low = df['Low'].iloc[-5:].min()
    candle_low = df['Low'].iloc[-1]
    stop_loss = min(swing_low, candle_low)
    
    # Target 1: prior swing high
    swing_high = df['High'].iloc[-20:-1].max()
    
    return is_candidate, {"stop_loss": stop_loss, "swing_high": swing_high}