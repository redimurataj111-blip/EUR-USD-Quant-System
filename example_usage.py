"""
Example: Run EUR/USD Quant System on your data.

Uses data from:
- CSV: EURUSD_1h_2024_2026.csv (from fetch_data_v4.py)
- QuestDB: eurusd_1h table (from load_to_questdb.py)

Run from project dir: python example_usage.py
"""

from pipeline import EURUSDQuantSystem
from data_loader import load_eurusd_data

# Load your EUR/USD data (tries CSV first, then QuestDB)
df = load_eurusd_data(source="auto", csv_dir=r"C:\Users\DELL\OneDrive\Desktop")
print(f"Loaded {len(df):,} rows | {df.index[0]} to {df.index[-1]}")

# Initialize and run (min_predicted_pips=0 for more signals; set 30 to filter)
system = EURUSDQuantSystem(
    rdc_window=60,
    n_pca_components=5,
    nn_epochs=50,
    min_predicted_pips=0,
)

results = system.run(df, fit=True)

# Inspect signals
print("\nSignal counts:")
print(results['signal'].value_counts())
print("\nSample output:")
print(results.tail(10))
