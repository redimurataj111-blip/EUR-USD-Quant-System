# Live EUR/USD Price Updates (Every Minute)

## Quick Start

Run the Streamlit dashboard with live 1-minute price updates:

```bash
streamlit run app.py
```

## Configuration

### In the Sidebar:
1. **Data Source**: Select `"live"` to fetch real-time prices from yfinance
2. **Live period**: Choose `1d`, `5d`, or `7d` of historical data
3. **Interval**: Select `1m` for 1-minute candles (default), `5m`, or `1h`
4. **Auto-refresh**: Checkbox will be set to `TRUE` by default
   - Updates every **60 seconds** (1 minute)
   - Refreshes the entire dashboard with latest data

## What You Get

### Live Price Display
- **Large, prominent price ticker** showing current EUR/USD rate
- **Auto-update indicator** (🔄 Updates every 60 seconds)
- **Signal badge** (LONG, WAIT, or DANGER)
- **Last update timestamp** with HH:MM:SS format
- **NN signal score** and **predicted pips**

### Data Refresh Behavior
- Data cache TTL: **15 seconds** (for data freshness)
- Auto-refresh interval: **60 seconds** (page reload)
- Covers **1 day to 7 days** of minute-level price data

## Example Setup

```
1. Open Streamlit: streamlit run app.py
2. In sidebar, select:
   - Data Source: "live"
   - Live period: "5d"
   - Interval: "1m"
   - Auto-refresh: ✓ (checked)
3. Watch the live price update every minute!
```

## Data Sources

**Live (yfinance)**: Free, real-time 1-minute data
- Supports: 1m, 5m, 15m, 1h, 1d intervals
- Historical: 1d-7d max for minute-level data
- No API key required

## Performance Notes

- **Network**: Uses yfinance API (free, rate-limited)
- **Refresh delay**: ~2-5 seconds per update (due to data fetch + processing)
- **CPU**: Moderate (running HMM, RDC, Neural Net on every refresh)
- **Memory**: ~100-200 MB for 1-minute data buffers

## Architecture

```
app.py (Streamlit)
  ├── Sidebar: User selects "live" + "1m"
  ├── call: load_data(source="live", live_interval="1m")
  │    └── data_loader.py: load_eurusd_data()
  │         └── load_from_live(interval="1m", period="5d")
  │              └── yfinance.download("EURUSD=X", interval="1m")
  ├── Auto-refresh: st_autorefresh(interval=60000ms)
  └── Display: Large price + signal banner + charts
```

## Testing

Run the test script to verify minute-level data fetching:

```bash
python test_live_prices.py
```

Output shows:
- Number of minute candles loaded
- Latest 5 prices
- Current price
- Data structure validation

## Troubleshooting

**No data loading?**
- Check internet connection
- Try "csv" or "questdb" source as fallback
- Check `Use sample data` option for demo mode

**Slow refresh?**
- Reduce the historical period (1d instead of 5d)
- Increase refresh interval in slider (if visible)

**NN/HMM errors?**
- More data needed for 1-minute analysis
- Try 5d period instead of 1d
- Check that you have 50+ candles loaded

## Future Enhancements

- [ ] WebSocket connection for true real-time streaming (vs. 60-sec polling)
- [ ] Multiple timeframes (1m, 5m, 1h) side-by-side
- [ ] Price alerts/notifications on LONG signal
- [ ] Minute-level backtest mode
- [ ] Trade execution integration
