"""
Neural Network for EUR/USD trading.

Uses sklearn MLPRegressor (no PyTorch/CUDA DLLs required).
Architecture: 8 inputs (5 PCA + 3 HMM probs) -> 64 -> 32 -> 3 outputs
Outputs: signal [-1,1], lower_bound, upper_bound (prediction interval)
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional


class TradingNN:
    """
    Feedforward NN: 8 -> 64 -> 32 -> 3
    Uses sklearn MLPRegressor (ReLU, no custom loss - MSE).
    """
    
    def __init__(
        self,
        input_dim: int = 8,
        hidden_layer_sizes: Tuple[int, ...] = (64, 32),
        max_iter: int = 200,
        random_state: Optional[int] = 42
    ):
        self.input_dim = input_dim
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes,
            activation='relu',
            max_iter=max_iter,
            random_state=random_state,
            early_stopping=True,
            validation_fraction=0.1,
        )
        self.scaler = StandardScaler()
        self._fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "TradingNN":
        """Train on (X, y). y = forward returns. Scale targets for 30-70 pip range."""
        X_scaled = self.scaler.fit_transform(X)
        # Targets: [signal_proxy, lower, upper] for 3 outputs
        # Scale to encourage predictions in 30-70 pip range (0.003-0.007)
        margin = np.maximum(np.abs(y) * 0.5, 0.002)  # min margin ~20 pips
        y_signal = np.clip(y * 10, -1, 1)
        y_lower = y - margin
        y_upper = y + margin
        # Floor bullish predictions at 30 pips (0.003) so model learns to predict meaningful moves
        min_upside = 0.003
        y_upper = np.where(y > 0, np.maximum(y_upper, min_upside), y_upper)
        y_target = np.column_stack([y_signal, y_lower, y_upper])
        
        self.model.fit(X_scaled, y_target)
        self._fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return signal [-1,1], lower_bound, upper_bound."""
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        X_scaled = self.scaler.transform(X)
        out = self.model.predict(X_scaled)
        signal = np.tanh(out[:, 0])
        lower = out[:, 1]
        upper = out[:, 2]
        lower_bound = np.minimum(lower, upper)
        upper_bound = np.maximum(lower, upper)
        return signal, lower_bound, upper_bound


def train_nn(
    model: TradingNN,
    X: np.ndarray,
    y: np.ndarray
) -> None:
    """Train the model (sklearn handles this in fit)."""
    model.fit(X, y)


def predict(
    model: TradingNN,
    X: np.ndarray,
    device: Optional[object] = None  # ignored, for API compatibility
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Get signal, lower_bound, upper_bound from model."""
    return model.predict(X)
