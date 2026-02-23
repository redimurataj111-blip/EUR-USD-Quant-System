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
    SELL = "SELL"
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
      "simple" = LONG/SELL based on NN signal strength
      "regime" = strict HMM-based logic optimized for 50%+ win rate and PF >= 2
    
    Signals:
      LONG: Buy signal (enter long position)
      SELL: Exit signal (close long position)
      DANGER: High volatility - avoid trading AND exit if in position
      WAIT: Hold position if long, wait for entry if not in position
      NO_TRADE: No signals
    
    REGIME MODE OPTIMIZATIONS:
    - Higher signal_threshold (0.35 vs 0.2): Only strong NN signals
    - Higher p_state2_threshold (0.55 vs 0.4): Stronger state certainty
    - Stricter regime filter (never allow_state1): Only trade state 1 (medium vol)
    - Minimum predicted pips (35): Skip low-confidence predictions
    - Tighter interval_width (0.015 vs 0.02): More focused predictions
    - SELL on bearish reversal: nn_signal drops below 0
    - SELL on regime deterioration: moving towards State 2/3
    """
    interval_width = upper_bound - lower_bound
    min_predicted_return = pips_to_return(min_predicted_pips) if min_predicted_pips > 0 else -1
    
    if signal_mode == "simple":
        # Simple mode: NN-driven. LONG when bullish, SELL when bearish
        if regime == 2 and p_state3 > 0.9:
            return Signal.DANGER
        # SELL: Clear bearish reversal
        if nn_signal < -0.2:
            return Signal.SELL
        # SELL: NN confidence dropped significantly
        if nn_signal < 0.0 and p_state3 > 0.5:
            return Signal.SELL
        # LONG: Strong bullish
        if nn_signal > 0.3 and (min_predicted_pips <= 0 or upper_bound >= min_predicted_return):
            return Signal.LONG
        return Signal.WAIT
    
    # Regime mode: STRICT logic optimized for 50%+ win rate & PF >= 2
    # DANGER: High volatility state (regime 2) - EXIT IMMEDIATELY
    if regime == 2 or p_state3 > p_state3_threshold:
        return Signal.DANGER
    
    # SELL: Exit signals for manual traders holding positions
    # - NN signal turned bearish (reversal)
    if nn_signal < 0.0 and p_state3 > 0.45:
        return Signal.SELL
    # - Prediction turned downside (lower_bound negative)
    if lower_bound < -0.001 and nn_signal < 0.1:
        return Signal.SELL
    # - Losing momentum and state deteriorating
    if nn_signal < signal_threshold * 0.5 and p_state2 < p_state2_threshold - 0.1:
        return Signal.SELL
    
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
