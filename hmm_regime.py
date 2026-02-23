"""
Hidden Markov Model for market regime detection.

States: S1 (Low Vol), S2 (Medium Vol), S3 (High Vol)
Observations: RDC Index (Gaussian emissions)
Algorithms: Baum-Welch (training), Viterbi (decoding), Forward-Backward (filtering)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from hmmlearn import hmm


# EUR/USD transition matrix from Charles University thesis
EURUSD_TRANSITION_MATRIX = np.array([
    [0.662, 0.335, 0.003],  # S1 -> S1, S2, S3
    [0.662, 0.329, 0.008],  # S2 -> S1, S2, S3
    [0.001, 0.006, 0.993],  # S3 -> S1, S2, S3
])


class HMMRegimeDetector:
    """
    HMM with 3 states and Gaussian emissions.
    B_j(o) = P(O_t=o|S_t=j) ~ N(μ_j, σ²_j)
    """
    
    def __init__(
        self,
        n_states: int = 3,
        n_iter: int = 100,
        init_transition: Optional[np.ndarray] = None,
        random_state: Optional[int] = None
    ):
        self.n_states = n_states
        self.model = hmm.GaussianHMM(
            n_components=n_states,
            covariance_type="diag",
            n_iter=n_iter,
            random_state=random_state
        )
        if init_transition is not None:
            self.model.transmat_ = init_transition
    
    def fit(self, observations: np.ndarray) -> "HMMRegimeDetector":
        """
        Train HMM using Baum-Welch (EM) algorithm.
        
        Estimates: A (transition), π (initial), μ_j, σ²_j (Gaussian emissions)
        """
        X = observations.reshape(-1, 1)
        self.model.fit(X)
        return self
    
    def decode(self, observations: np.ndarray) -> np.ndarray:
        """
        Viterbi algorithm: most likely state sequence.
        
        Returns regime at each time t (0, 1, or 2 for S1, S2, S3).
        """
        X = observations.reshape(-1, 1)
        return self.model.predict(X)
    
    def filter(self, observations: np.ndarray) -> np.ndarray:
        """
        Forward-Backward: smoothed P(S_t=j | O_1,...,O_T).
        
        Returns (T, n_states) array of probabilities.
        """
        X = observations.reshape(-1, 1)
        return self.model.predict_proba(X)
    
    def get_state_probabilities(
        self, 
        observations: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get p_state1, p_state2, p_state3 for each time step.
        
        Returns:
            p_state1, p_state2, p_state3: Each shape (T,)
        """
        probs = self.filter(observations)
        return probs[:, 0], probs[:, 1], probs[:, 2]
    
    def get_params_summary(self) -> dict:
        """Return HMM parameters for inspection."""
        return {
            "transition_matrix": self.model.transmat_,
            "means": self.model.means_.flatten(),
            "variances": self.model.covars_.flatten(),
            "startprob": self.model.startprob_,
        }


def run_hmm_pipeline(
    rdc_series: pd.Series,
    init_transition: Optional[np.ndarray] = None,
    fit: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, HMMRegimeDetector]:
    """
    Full HMM pipeline: fit (optional), decode, filter.
    
    Args:
        rdc_series: RDC Index observations
        init_transition: Optional initial transition matrix (e.g., EURUSD)
        fit: Whether to fit model or use provided params
    
    Returns:
        regime: Most likely state sequence (0, 1, 2)
        p_state1, p_state2, p_state3: Smoothed probabilities
        detector: Fitted HMMRegimeDetector
    """
    detector = HMMRegimeDetector(init_transition=init_transition)
    
    obs = rdc_series.values.astype(float)
    obs = np.nan_to_num(obs, nan=0.0)
    
    if fit:
        detector.fit(obs)
    else:
        detector.model.transmat_ = init_transition or EURUSD_TRANSITION_MATRIX
        # Initialize means/variances from data
        detector.model.means_ = np.array([
            [np.percentile(obs, 25)],
            [np.percentile(obs, 50)],
            [np.percentile(obs, 75)],
        ])
        detector.model.covars_ = np.array([[np.var(obs) / 3]] * 3)
    
    regime = detector.decode(obs)
    p1, p2, p3 = detector.get_state_probabilities(obs)
    
    return regime, p1, p2, p3, detector
