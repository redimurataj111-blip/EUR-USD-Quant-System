"""
EUR/USD Quant System - A sophisticated quantitative trading system.

Components:
- dc_framework: Directional Change & RDC Index
- hmm_regime: Hidden Markov Model for regime detection
- features: Technical indicators & PCA
- neural_net: NN with Sortino Ratio & Prediction Interval loss
- trade_logic: Signal generation (LONG, DANGER, WAIT, NO_TRADE)
- pipeline: Main orchestration
"""

from .pipeline import EURUSDQuantSystem, create_sample_data
from .trade_logic import Signal, compute_signal
from .dc_framework import compute_rdc_series, detect_dc_events, compute_rdc_index
from .hmm_regime import HMMRegimeDetector, EURUSD_TRANSITION_MATRIX
from .features import build_features, apply_pca
from .neural_net import TradingNN

__all__ = [
    "EURUSDQuantSystem",
    "create_sample_data",
    "Signal",
    "compute_signal",
    "compute_rdc_series",
    "detect_dc_events",
    "compute_rdc_index",
    "HMMRegimeDetector",
    "EURUSD_TRANSITION_MATRIX",
    "build_features",
    "apply_pca",
    "TradingNN",
]
