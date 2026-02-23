"""
Directional Change (DC) Framework and Relative Directional Change (RDC) Index.

Mathematical foundations:
- DC event: Price moves by threshold θ from last extreme (up or down)
- DC_up: Price rises by θ from last low
- DC_down: Price falls by θ from last high
- RDC_index = (RDC_up - RDC_down) / (RDC_up + RDC_down + ε), range [-1, 1]
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel


def detect_dc_events(prices: np.ndarray, theta: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect DC_up and DC_down events from price series.
    
    Args:
        prices: Array of close prices
        theta: Threshold (e.g., 0.001 for 0.1%)
    
    Returns:
        dc_up_mask: Boolean array where True indicates DC_up event
        dc_down_mask: Boolean array where True indicates DC_down event
    """
    n = len(prices)
    dc_up = np.zeros(n, dtype=bool)
    dc_down = np.zeros(n, dtype=bool)
    
    last_low = prices[0]
    last_high = prices[0]
    
    for i in range(1, n):
        p = prices[i]
        
        # DC_up: price rises by theta from last low
        if p >= last_low * (1 + theta):
            dc_up[i] = True
            last_high = p
            last_low = p
        
        # DC_down: price falls by theta from last high
        elif p <= last_high * (1 - theta):
            dc_down[i] = True
            last_low = p
            last_high = p
        
        else:
            last_low = min(last_low, p)
            last_high = max(last_high, p)
    
    return dc_up, dc_down


def compute_rdc_index(
    dc_up: np.ndarray, 
    dc_down: np.ndarray, 
    window: int = 60,
    eps: float = 1e-8
) -> np.ndarray:
    """
    Compute RDC Index over rolling window.
    
    RDC_index = (RDC_up - RDC_down) / (RDC_up + RDC_down + ε)
    
    Args:
        dc_up: Boolean mask of DC_up events
        dc_down: Boolean mask of DC_down events
        window: Rolling window size (e.g., 60 minutes)
        eps: Small constant to prevent division by zero
    
    Returns:
        rdc_index: Array in range [-1, 1]
    """
    n = len(dc_up)
    rdc_index = np.zeros(n)
    
    for i in range(n):
        start = max(0, i - window + 1)
        rdc_up_count = np.sum(dc_up[start:i+1])
        rdc_down_count = np.sum(dc_down[start:i+1])
        total = rdc_up_count + rdc_down_count + eps
        rdc_index[i] = (rdc_up_count - rdc_down_count) / total
    
    return rdc_index


def bayesian_optimize_theta(
    prices: np.ndarray,
    forward_returns: np.ndarray,
    theta_bounds: Tuple[float, float] = (0.0001, 0.01),
    n_iterations: int = 30,
    n_initial: int = 5
) -> float:
    """
    Bayesian optimization to find optimal θ.
    
    Objective: Maximize mean(|forward_returns|) after DC events.
    Uses Gaussian Process to model objective and balance exploration/exploitation.
    
    Args:
        prices: Close prices
        forward_returns: Forward returns for each timestamp
        theta_bounds: (min_theta, max_theta)
        n_iterations: Number of Bayesian optimization iterations
        n_initial: Random initial points
    
    Returns:
        Optimal theta value
    """
    def objective(theta: float) -> float:
        """Negative mean abs forward return (minimize = maximize mean abs return)."""
        dc_up, dc_down = detect_dc_events(prices, theta)
        dc_events = dc_up | dc_down
        if np.sum(dc_events) < 10:
            return 1e6  # Penalize too few events
        event_returns = np.abs(forward_returns[dc_events])
        return -np.mean(event_returns)
    
    # Initial random samples
    thetas = np.random.uniform(theta_bounds[0], theta_bounds[1], n_initial)
    objectives = np.array([objective(t) for t in thetas])
    
    # GP kernel
    kernel = RBF(length_scale=0.001) + WhiteKernel(noise_level=0.1)
    gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)
    
    for _ in range(n_iterations - n_initial):
        gp.fit(thetas.reshape(-1, 1), objectives)
        
        # Expected Improvement acquisition
        theta_candidates = np.linspace(theta_bounds[0], theta_bounds[1], 100)
        mu, sigma = gp.predict(theta_candidates.reshape(-1, 1), return_std=True)
        sigma = np.maximum(sigma, 1e-10)
        
        best_obj = np.min(objectives)
        improvement = best_obj - mu
        z = improvement / sigma
        ei = improvement * norm.cdf(z) + sigma * norm.pdf(z)
        
        next_theta = theta_candidates[np.argmax(ei)]
        next_obj = objective(next_theta)
        
        thetas = np.append(thetas, next_theta)
        objectives = np.append(objectives, next_obj)
    
    return thetas[np.argmin(objectives)]


def compute_rdc_series(
    df: pd.DataFrame,
    theta: Optional[float] = None,
    window: int = 60,
    optimize_theta: bool = False,
    forward_periods: int = 12
) -> Tuple[pd.Series, float]:
    """
    Full pipeline: detect DC events and compute RDC Index.
    
    Args:
        df: DataFrame with 'close' column
        theta: DC threshold (if None and optimize_theta=True, will optimize)
        window: RDC rolling window
        optimize_theta: Whether to run Bayesian optimization for theta
        forward_periods: Periods for forward returns (optimization objective)
    
    Returns:
        rdc_series: RDC Index as pandas Series
        theta_used: Theta value used
    """
    prices = df['close'].values.astype(float)
    
    if theta is None or optimize_theta:
        forward_returns = np.roll(prices, -forward_periods) / prices - 1
        forward_returns[-forward_periods:] = 0
        theta = bayesian_optimize_theta(prices, forward_returns)
    
    dc_up, dc_down = detect_dc_events(prices, theta)
    rdc = compute_rdc_index(dc_up, dc_down, window=window)
    
    return pd.Series(rdc, index=df.index), theta
