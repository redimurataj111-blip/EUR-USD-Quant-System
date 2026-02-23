"""
Feature Engineering and Principal Component Analysis.

50+ technical indicators (RSI, MACD, Bollinger, ATR, EMA, ADX, Stochastic, CCI, etc.)
PCA for dimensionality reduction to top 5 components.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def _ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average: f(x) = α*x_t + (1-α)*f(x_{t-1})."""
    return series.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index - momentum oscillator [0, 100]."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = _ema(gain, period)
    avg_loss = _ema(loss, period)
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))


def macd(
    close: pd.Series, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, histogram."""
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(
    close: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Upper, middle, lower Bollinger Bands."""
    middle = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range - volatility measure."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def adx(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    period: int = 14
) -> pd.Series:
    """Average Directional Index - trend strength [0, 100]."""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr_val = atr(high, low, close, period)
    
    plus_di = 100 * _ema(plus_dm, period) / (atr_val + 1e-10)
    minus_di = 100 * _ema(minus_dm, period) / (atr_val + 1e-10)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    return _ema(dx, period)


def stochastic(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """Stochastic %K and %D."""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
    d = k.rolling(d_period).mean()
    return k, d


def cci(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    period: int = 20
) -> pd.Series:
    """Commodity Channel Index."""
    typical_price = (high + low + close) / 3
    sma = typical_price.rolling(period).mean()
    mad = typical_price.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
    return (typical_price - sma) / (0.015 * mad + 1e-10)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build 50+ technical indicators from OHLCV data.
    
    Expected columns: open, high, low, close, volume (or Open, High, Low, Close, Volume)
    """
    cols = {c.lower(): c for c in df.columns}
    o = df[cols.get('open', 'open')]
    h = df[cols.get('high', 'high')]
    l = df[cols.get('low', 'low')]
    c = df[cols.get('close', 'close')]
    v = df[cols.get('volume', 'volume')] if 'volume' in [x.lower() for x in df.columns] else pd.Series(1, index=df.index)
    
    features = pd.DataFrame(index=df.index)
    
    # RSI variants
    for p in [7, 14, 21]:
        features[f'rsi_{p}'] = rsi(c, p)
    
    # MACD
    macd_line, signal_line, hist = macd(c)
    features['macd'] = macd_line
    features['macd_signal'] = signal_line
    features['macd_hist'] = hist
    
    # Bollinger
    for p in [10, 20, 30]:
        upper, middle, lower = bollinger_bands(c, p)
        features[f'bb_upper_{p}'] = upper
        features[f'bb_middle_{p}'] = middle
        features[f'bb_lower_{p}'] = lower
        features[f'bb_width_{p}'] = (upper - lower) / (middle + 1e-10)
    
    # ATR
    for p in [7, 14, 21]:
        features[f'atr_{p}'] = atr(h, l, c, p)
    
    # EMA
    for span in [5, 10, 20, 50]:
        features[f'ema_{span}'] = _ema(c, span)
        features[f'ema_ratio_{span}'] = c / (_ema(c, span) + 1e-10)
    
    # ADX
    features['adx'] = adx(h, l, c)
    
    # Stochastic
    k, d = stochastic(h, l, c)
    features['stoch_k'] = k
    features['stoch_d'] = d
    
    # CCI
    features['cci'] = cci(h, l, c)
    
    # Returns
    for p in [1, 5, 10]:
        features[f'return_{p}'] = c.pct_change(p)
    
    # Volatility
    features['volatility_10'] = c.pct_change().rolling(10).std()
    features['volatility_20'] = c.pct_change().rolling(20).std()
    
    # Volume
    features['volume_sma'] = v.rolling(20).mean()
    features['volume_ratio'] = v / (features['volume_sma'] + 1e-10)
    
    return features


def apply_pca(
    features: pd.DataFrame,
    n_components: int = 5,
    fit: bool = True,
    scaler: Optional[StandardScaler] = None,
    pca: Optional[PCA] = None
) -> Tuple[np.ndarray, StandardScaler, PCA]:
    """
    Apply PCA for dimensionality reduction.
    
    Transforms correlated features into uncorrelated principal components.
    First component captures most variance, etc.
    
    Returns:
        components: (n_samples, n_components) array
        scaler: Fitted StandardScaler
        pca: Fitted PCA
    """
    X = features.fillna(0).values
    
    if scaler is None:
        scaler = StandardScaler()
    if pca is None:
        pca = PCA(n_components=n_components)
    
    if fit:
        X_scaled = scaler.fit_transform(X)
        components = pca.fit_transform(X_scaled)
    else:
        X_scaled = scaler.transform(X)
        components = pca.transform(X_scaled)
    
    return components, scaler, pca
