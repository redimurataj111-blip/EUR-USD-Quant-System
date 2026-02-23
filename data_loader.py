"""
Load EUR/USD data from your existing sources:
- CSV (from fetch_data_v4.py)
- QuestDB (from load_to_questdb.py)
- Live (yfinance - real-time)
"""

import pandas as pd
from pathlib import Path
from typing import Optional


def load_from_live(
    period: str = "5d",
    interval: str = "1h",
    ticker: str = "EURUSD=X"
) -> pd.DataFrame:
    """
    Fetch live EUR/USD data from yfinance.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y
    interval: 1m, 5m, 15m, 1h, 1d
    Note: 1m and 5m intervals limited to 5-7 days max
    """
    import yfinance as yf
    
    # For minute-level data, limit period to avoid data gaps
    if interval in ["1m", "5m", "15m"]:
        if period not in ["1d", "5d", "7d"]:
            period = "5d"
    
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty or len(df) < 50:
        # Fallback to hourly if intraday fails
        fallback_interval = "1h" if interval in ["1m", "5m", "15m"] else "1h"
        fallback_period = "60d" if interval not in ["1m", "5m", "15m"] else "5d"
        df = yf.download(ticker, period=fallback_period, interval=fallback_interval, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError("No live data from yfinance. Check connection.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)
    df.index = pd.to_datetime(df.index)
    cols = [c for c in ['open', 'high', 'low', 'close'] if c in df.columns]
    df = df[cols].dropna()
    if 'volume' not in df.columns:
        df['volume'] = 1
    return df.sort_index()


def load_from_csv(
    path: str = "EURUSD_1h_2024_2026.csv",
    csv_dir: Optional[str] = None
) -> pd.DataFrame:
    """
    Load EUR/USD OHLC from CSV produced by fetch_data_v4.py.
    
    Handles yfinance multi-level columns. Falls back to Desktop if path not found.
    """
    p = Path(path)
    if not p.exists() and csv_dir:
        p = Path(csv_dir) / Path(path).name
    if not p.exists():
        # Try Desktop (where fetch_data_v4.py lives)
        p = Path.home() / "OneDrive" / "Desktop" / Path(path).name
    if not p.exists():
        p = Path.home() / "Desktop" / Path(path).name
    
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {path} (tried {p})")
    
    try:
        df = pd.read_csv(p, header=[0, 1], index_col=0)
    except Exception:
        df = pd.read_csv(p, index_col=0)
    # Flatten yfinance multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    # Normalize to lowercase for pipeline
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)
    df.index = pd.to_datetime(df.index)
    cols = [c for c in ['open', 'high', 'low', 'close'] if c in df.columns]
    df = df[cols].dropna()
    if 'volume' not in df.columns:
        df['volume'] = 1
    return df.sort_index()


def load_from_questdb(
    host: str = "localhost",
    port: int = 8812,
    user: str = "admin",
    password: str = "quest",
    database: str = "qdb",
    table: str = "eurusd_1h"
) -> pd.DataFrame:
    """
    Load EUR/USD OHLC from QuestDB (populated by load_to_questdb.py).
    """
    import psycopg2
    
    conn = psycopg2.connect(
        host=host, port=port,
        user=user, password=password,
        database=database
    )
    df = pd.read_sql(
        f'SELECT ts, open, high, low, close FROM {table} ORDER BY ts',
        conn,
        index_col='ts',
        parse_dates=['ts']
    )
    conn.close()
    df.columns = [c.lower() for c in df.columns]
    df['volume'] = 1  # QuestDB table has no volume
    return df


def load_eurusd_data(
    source: str = "auto",
    csv_path: str = "EURUSD_1h_2024_2026.csv",
    csv_dir: Optional[str] = None,
    live_period: str = "5d",
    live_interval: str = "1h"
) -> pd.DataFrame:
    """
    Load EUR/USD data. source: "csv", "questdb", "live", or "auto".
    "live" fetches from yfinance (real-time).
    """
    if source == "live":
        return load_from_live(period=live_period, interval=live_interval)
    
    if source == "csv":
        return load_from_csv(csv_path, csv_dir)
    
    if source == "questdb":
        return load_from_questdb()
    
    # auto: try CSV, then QuestDB
    try:
        return load_from_csv(csv_path, csv_dir)
    except FileNotFoundError:
        try:
            return load_from_questdb()
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load data. CSV not found and QuestDB failed: {e}"
            ) from e
