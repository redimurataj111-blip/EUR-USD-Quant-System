# EUR/USD Quant System

A sophisticated quantitative trading system combining:
- **Hidden Markov Models (HMM)** for regime detection
- **Directional Change (DC) Framework** for noise filtering
- **RDC Index** as HMM observations
- **PCA** for feature dimensionality reduction
- **Neural Network** with custom Sortino Ratio and Prediction Interval loss functions

## Mathematical Foundations

See `docs/MATHEMATICAL_FOUNDATIONS.md` for detailed mathematical derivations.

## Quick Start

**Streamlit dashboard:**
```bash
streamlit run app.py
```

**Python:**
```python
from pipeline import EURUSDQuantSystem
from data_loader import load_eurusd_data

df = load_eurusd_data(source="auto")
system = EURUSDQuantSystem()
results = system.run(df, fit=True)
```

## Project Structure

```
eurusd_quant_system/
├── dc_framework.py      # Directional Change & RDC Index
├── hmm_regime.py        # HMM with Baum-Welch, Viterbi, Forward-Backward
├── features.py          # Technical indicators & PCA
├── neural_net.py        # NN with custom loss functions
├── trade_logic.py       # Signal generation logic
├── pipeline.py          # Main orchestration
└── __init__.py
```
