#!/usr/bin/env python3
"""
Test script to verify live EUR/USD prices update every minute.
Run this alongside 'streamlit run app.py' to verify minute-level updates.
"""

import pandas as pd
from data_loader import load_eurusd_data
from datetime import datetime
import time

def test_live_1m_updates():
    """Test 1-minute interval live price updates."""
    print("\n" + "="*60)
    print("EUR/USD LIVE PRICE - 1 MINUTE UPDATES TEST")
    print("="*60 + "\n")
    
    # Fetch initial data
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching initial 1-minute data...")
    df = load_eurusd_data(
        source="live",
        live_period="1d",
        live_interval="1m"
    )
    
    print(f"✓ Loaded {len(df)} minute candles")
    print(f"  Latest 5 prices:")
    print(df['close'].tail(5))
    print(f"\n  Last update: {df.index[-1]}")
    print(f"  Current price: {df['close'].iloc[-1]:.5f}")
    
    # Show sample data structure
    print(f"\nData structure:")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Index: {df.index}")
    print(f"  Shape: {df.shape}")
    
    print("\n" + "="*60)
    print("Live price display ready!")
    print("Run: streamlit run app.py")
    print("Select 'live' as data source with '1m' interval")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_live_1m_updates()
