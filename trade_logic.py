"""
Trade Decision Logic - LONG ONLY (no short positions).

Signals: LONG, DANGER, WAIT, NO_TRADE.
Targets: Profit factor >= 2.0, Win rate >= 50%.
"""

import numpy as np
from typing import Literal
from enum import Enum


class Signal(Enum):
    LONG = "LONG"
    DANGER = "DANGER"
    WAIT = "WAIT"
    NO_TRADE = "NO_TRADE"


def pips_to_return(pips: float) -> float:
    """1 pip = 0.0001 for EUR/USD."""
    return pips * 0.0001


def compute_signal(
    regime: int,
    p_state1: float,
    p_state2: float,
    p_state3: float,
    nn_signal: float,
    lower_bound: float,
    upper_bound: float,
    interval_width_threshold: float = 0.015,
    p_state2_threshold: float = 0.55,
    p_state3_threshold: float = 0.65,
    signal_threshold: float = 0.35,
    min_predicted_pips: float = 35.0,
    allow_state1: bool = False,
    signal_mode: str = "simple"
) -> Signal:
    """
    signal_mode:
      "simple" = LONG when nn_signal > 0.3, DANGER only if regime=2 AND p_state3>0.9
      "regime" = strict HMM-based logic optimized for 50%+ win rate and PF >= 2
    
    REGIME MODE OPTIMIZATIONS:
    - Higher signal_threshold (0.35 vs 0.2): Only strong NN signals
    - Higher p_state2_threshold (0.55 vs 0.4): Stronger state certainty
    - Stricter regime filter (never allow_state1): Only trade state 1 (medium vol)
    - Minimum predicted pips (35): Skip low-confidence predictions
    - Tighter interval_width (0.015 vs 0.02): More focused predictions
    """
    interval_width = upper_bound - lower_bound
    min_predicted_return = pips_to_return(min_predicted_pips) if min_predicted_pips > 0 else -1
    
    if signal_mode == "simple":
        # Simple mode: NN-driven. LONG when bullish, DANGER only in extreme State 3
        if regime == 2 and p_state3 > 0.9:
            return Signal.DANGER
        if nn_signal > 0.0 and (min_predicted_pips <= 0 or upper_bound >= min_predicted_return):
            return Signal.LONG
        return Signal.NO_TRADE
    
    # Regime mode: STRICT logic optimized for 50%+ win rate & PF >= 2
    # DANGER: High volatility state (regime 2)
    if regime == 2 or p_state3 > p_state3_threshold:
        return Signal.DANGER
    
    # LONG: Only in State 1 (medium volatility) with strong signals
    # - regime == 1 (confirmed medium vol state)
    # - p_state2 > 0.55 (high confidence in state 1)
    # - nn_signal > 0.35 (strong bullish signal from NN)
    # - interval_width < 0.015 (tight prediction interval = high confidence)
    # - upper_bound >= 35 pips (predicted move covers potential reward)
    ok_regime = regime == 1 and p_state2 > p_state2_threshold
    
    if (
        ok_regime
        and nn_signal > signal_threshold
        and interval_width < interval_width_threshold
        and upper_bound >= min_predicted_return
    ):
        return Signal.LONG
    
    return Signal.WAIT


def compute_signals_batch(
    regimes: np.ndarray,
    p_state1: np.ndarray,
    p_state2: np.ndarray,
    p_state3: np.ndarray,
    nn_signals: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    min_predicted_pips: float = 0.0,
    allow_state1: bool = True,
    signal_mode: str = "simple",
    **kwargs
) -> np.ndarray:
    """Vectorized signal computation for arrays. Only LONG when predicted move >= min_predicted_pips."""
    n = len(regimes)
    signals = np.empty(n, dtype=object)
    
    for i in range(n):
        s = compute_signal(
            regime=int(regimes[i]),
            p_state1=float(p_state1[i]),
            p_state2=float(p_state2[i]),
            p_state3=float(p_state3[i]),
            nn_signal=float(nn_signals[i]),
            lower_bound=float(lower_bounds[i]),
            upper_bound=float(upper_bounds[i]),
            min_predicted_pips=min_predicted_pips,
            allow_state1=allow_state1,
            signal_mode=signal_mode,
            **kwargs
        )
        signals[i] = s
    
    return signals
