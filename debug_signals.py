"""
Debug script: print why we get no signals.
Run: python debug_signals.py
"""

from pipeline import EURUSDQuantSystem
from data_loader import load_eurusd_data
import numpy as np

print("Loading data...")
try:
    df = load_eurusd_data(source="auto", csv_dir=r"C:\Users\DELL\OneDrive\Desktop")
except Exception:
    from pipeline import create_sample_data
    df = create_sample_data(1000)
    print("Using sample data (no real data found)")

print(f"Rows: {len(df)}")

system = EURUSDQuantSystem(signal_mode="simple", min_predicted_pips=0)
results = system.run(df, fit=True)

print("\n" + "="*60)
print("SIGNAL COUNTS")
print("="*60)
print(results["signal"].value_counts())

print("\n" + "="*60)
print("DIAGNOSTICS")
print("="*60)
print("Regime distribution:", dict(zip(*np.unique(results["regime"], return_counts=True))))
print("NN signal: min={:.4f}, max={:.4f}, mean={:.4f}".format(
    results["nn_signal"].min(), results["nn_signal"].max(), results["nn_signal"].mean()))
print("NN signal > 0 count:", (results["nn_signal"] > 0).sum())
print("P(State 3) > 0.9 count:", (results["p_state3"] > 0.9).sum())
print("Regime == 2 count:", (results["regime"] == 2).sum())
print("Predicted pips: mean={:.1f}, max={:.1f}".format(
    results["predicted_pips"].mean(), results["predicted_pips"].max()))

# Blocking analysis
block_regime3 = (results["regime"] == 2) & (results["p_state3"] > 0.9)
block_nn = results["nn_signal"] <= 0
print("\nBlocked by DANGER (regime=2 & p3>0.9):", block_regime3.sum())
print("Blocked by nn_signal<=0:", block_nn.sum())
print("Would-be LONG (nn>0, not danger):", ((results["nn_signal"] > 0) & ~block_regime3).sum())
