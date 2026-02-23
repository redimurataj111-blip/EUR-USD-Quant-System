"""
Main EUR/USD Quant System Pipeline.

Orchestrates: DC/RDC -> HMM -> Features/PCA -> NN -> Trade Logic
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

from dc_framework import compute_rdc_series
from hmm_regime import run_hmm_pipeline, EURUSD_TRANSITION_MATRIX
from features import build_features, apply_pca
from neural_net import TradingNN, train_nn, predict
from trade_logic import compute_signals_batch, Signal


class EURUSDQuantSystem:
    """
    End-to-end EUR/USD quantitative trading system.
    
    Pipeline:
    1. RDC Index from OHLCV (Directional Change framework)
    2. HMM regime detection (Baum-Welch, Viterbi, Forward-Backward)
    3. Feature engineering + PCA (5 components)
    4. Neural network (signal + prediction interval)
    5. Trade decision logic
    """
    
    def __init__(
        self,
        theta: Optional[float] = None,
        rdc_window: int = 60,
        n_pca_components: int = 5,
        nn_epochs: int = 50,
        forward_periods: int = 24,
        min_predicted_pips: float = 0.0,
        signal_mode: str = "simple",
        random_state: Optional[int] = 42
    ):
        self.theta = theta
        self.signal_mode = signal_mode
        self.rdc_window = rdc_window
        self.n_pca_components = n_pca_components
        self.nn_epochs = nn_epochs
        self.forward_periods = forward_periods
        self.min_predicted_pips = min_predicted_pips
        self.random_state = random_state
        
        self._scaler = None
        self._pca = None
        self._hmm_detector = None
        self._nn_model = None
    
    def fit(self, df: pd.DataFrame) -> "EURUSDQuantSystem":
        """
        Fit all components on training data.
        
        Args:
            df: OHLCV DataFrame (open, high, low, close, volume)
        """
        # 1. RDC Index
        rdc_series, theta_used = compute_rdc_series(
            df, theta=self.theta, window=self.rdc_window
        )
        self.theta = theta_used
        
        # 2. HMM
        regime, p1, p2, p3, detector = run_hmm_pipeline(
            rdc_series, init_transition=EURUSD_TRANSITION_MATRIX, fit=True
        )
        self._hmm_detector = detector
        
        # 3. Features + PCA
        features = build_features(df)
        pca_input, self._scaler, self._pca = apply_pca(
            features, n_components=self.n_pca_components, fit=True
        )
        
        # 4. NN inputs: 5 PCA + 3 HMM probs
        nn_input = np.hstack([
            pca_input,
            p1.reshape(-1, 1),
            p2.reshape(-1, 1),
            p3.reshape(-1, 1),
        ])
        
        # Target: forward return
        close = df['close'].values if 'close' in df.columns else df['Close'].values
        y = np.roll(close, -self.forward_periods) / close - 1
        y[-self.forward_periods:] = 0
        
        # 5. Train NN (sklearn - no PyTorch/CUDA required)
        self._nn_model = TradingNN(
            input_dim=8,
            hidden_layer_sizes=(64, 32),
            max_iter=self.nn_epochs
        )
        train_nn(self._nn_model, nn_input, y)
        
        return self
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals for given data.
        
        If fit was not called, will fit on this data first.
        """
        if self._hmm_detector is None:
            self.fit(df)
        
        # 1. RDC
        rdc_series, _ = compute_rdc_series(
            df, theta=self.theta, window=self.rdc_window
        )
        
        # 2. HMM (use fitted detector)
        obs = np.nan_to_num(rdc_series.values.astype(float), nan=0.0)
        regime = self._hmm_detector.decode(obs.reshape(-1, 1))
        probs = self._hmm_detector.filter(obs.reshape(-1, 1))
        p1, p2, p3 = probs[:, 0], probs[:, 1], probs[:, 2]
        
        # 3. Features + PCA
        features = build_features(df)
        pca_input, _, _ = apply_pca(
            features,
            n_components=self.n_pca_components,
            fit=False,
            scaler=self._scaler,
            pca=self._pca
        )
        
        # 4. NN
        nn_input = np.hstack([
            pca_input,
            p1.reshape(-1, 1),
            p2.reshape(-1, 1),
            p3.reshape(-1, 1),
        ])
        
        signal, lower, upper = predict(self._nn_model, nn_input)
        
        # 5. Trade logic
        signals = compute_signals_batch(
            regime, p1, p2, p3, signal, lower, upper,
            min_predicted_pips=self.min_predicted_pips,
            allow_state1=True,
            signal_mode=getattr(self, "signal_mode", "simple")
        )
        
        # Fallback: if zero LONGs, take top 5% by nn_signal (guarantee some signals)
        long_count = sum(1 for s in signals if s.value == "LONG")
        if long_count == 0 and len(signals) > 20:
            n_long = max(5, int(len(signals) * 0.05))
            top_idx = np.argsort(signal)[-n_long:]
            for i in range(len(signals)):
                if i in top_idx and regime[i] != 2:
                    signals[i] = Signal.LONG
        
        # Predicted pips from upper_bound (bullish upside)
        predicted_pips = upper / 0.0001  # return to pips
        
        result = pd.DataFrame({
            'regime': regime,
            'p_state1': p1,
            'p_state2': p2,
            'p_state3': p3,
            'nn_signal': signal,
            'lower_bound': lower,
            'upper_bound': upper,
            'interval_width': upper - lower,
            'predicted_pips': predicted_pips,
            'signal': [s.value for s in signals],
        }, index=df.index)
        
        return result
    
    def run(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Run full pipeline. Fit if requested, then predict.
        """
        if fit:
            self.fit(df)
        return self.predict(df)


def create_sample_data(n: int = 1000) -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    close = 1.08 + np.cumsum(np.random.randn(n) * 0.0005)
    high = close + np.abs(np.random.randn(n) * 0.001)
    low = close - np.abs(np.random.randn(n) * 0.001)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    volume = np.random.randint(1000, 10000, n)
    return pd.DataFrame({
        'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
    })
