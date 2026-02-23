"""
Backtest module for EUR/USD Quant System.

LONG ONLY - no short positions.
Targets: Profit factor >= 2.0, Win rate >= 50%.
TP/SL 2:1 (60/30 pips) achieves PF=2 at 50% win rate.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple

# 1 pip = 0.0001 for EUR/USD
PIP = 0.0001


def run_backtest(
    df: pd.DataFrame,
    results: pd.DataFrame,
    holding_periods: int = 24,
    close_col: str = "close",
    exit_on_danger: bool = True,
    take_profit_pips: float = 60.0,
    stop_loss_pips: float = 30.0,
    use_tp_sl: bool = True
) -> Tuple[pd.DataFrame, dict]:
    """
    Backtest: LONG ONLY. Enter long on LONG signal, never short.
    Exit on: TP (60 pips), SL (30 pips), DANGER, or holding_periods.
    2:1 R:R (TP/SL) targets PF >= 2.0 and win rate >= 50%.
    
    Args:
        df: OHLCV DataFrame with close prices
        results: Pipeline results with 'signal' column
        holding_periods: Max bars to hold
        take_profit_pips: Take profit at +55 pips (middle of 50-70)
        stop_loss_pips: Stop loss at -30 pips
        use_tp_sl: If True, use TP/SL; else time-based exit only
    
    Returns:
        trades: DataFrame with entry_time, exit_time, pnl_pct, pnl_pips, exit_reason
        stats: dict with win_rate, profit_factor, avg_pips, etc.
    """
    close = df[close_col].values
    high = df["high"].values if "high" in df.columns else df["High"].values if "High" in df.columns else close
    low = df["low"].values if "low" in df.columns else df["Low"].values if "Low" in df.columns else close
    signals = results["signal"].values
    n = len(close)
    
    tp_return = take_profit_pips * PIP
    sl_return = stop_loss_pips * PIP
    
    trades = []
    i = 0
    while i < n:
        if signals[i] != "LONG":
            i += 1
            continue
        
        entry_idx = i
        entry_price = close[i]
        exit_idx = None
        exit_price = None
        exit_reason = "time"
        
        for j in range(1, min(holding_periods + 1, n - i)):
            idx = i + j
            if idx >= n:
                break
            
            current_high = high[idx]
            current_low = low[idx]
            current_close = close[idx]
            ret = (current_close - entry_price) / entry_price
            
            if use_tp_sl:
                # Check TP: high reached target
                high_ret = (current_high - entry_price) / entry_price
                if high_ret >= tp_return:
                    exit_idx = idx
                    exit_price = entry_price * (1 + tp_return)
                    exit_reason = "tp"
                    break
                # Check SL: low hit stop
                low_ret = (current_low - entry_price) / entry_price
                if low_ret <= -sl_return:
                    exit_idx = idx
                    exit_price = entry_price * (1 - sl_return)
                    exit_reason = "sl"
                    break
            
            if exit_on_danger and signals[idx] == "DANGER":
                exit_idx = idx
                exit_price = current_close
                exit_reason = "danger"
                break
            
            if j == holding_periods:
                exit_idx = idx
                exit_price = current_close
                exit_reason = "time"
                break
        
        if exit_idx is None:
            exit_idx = min(i + holding_periods, n - 1)
            exit_price = close[exit_idx]
            exit_reason = "time"
        
        pnl_pct = (exit_price - entry_price) / entry_price
        pnl_pips = (exit_price - entry_price) / PIP
        
        trades.append({
            "entry_idx": entry_idx,
            "exit_idx": exit_idx,
            "entry_time": df.index[entry_idx],
            "exit_time": df.index[exit_idx],
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct,
            "pnl_pips": pnl_pips,
            "bars_held": exit_idx - entry_idx,
            "exit_reason": exit_reason,
        })
        
        i = exit_idx + 1
    
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) == 0:
        stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "total_return_pct": 0.0,
            "avg_pips": 0.0,
            "avg_win_pct": 0.0,
            "avg_loss_pct": 0.0,
            "max_win_pct": 0.0,
            "max_loss_pct": 0.0,
        }
        return trades_df, stats
    
    winning = trades_df["pnl_pct"] > 0
    losing = trades_df["pnl_pct"] < 0
    
    gross_profit = trades_df.loc[winning, "pnl_pct"].sum()
    gross_loss = abs(trades_df.loc[losing, "pnl_pct"].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    
    stats = {
        "total_trades": len(trades_df),
        "winning_trades": int(winning.sum()),
        "losing_trades": int(losing.sum()),
        "win_rate_pct": round(100 * winning.sum() / len(trades_df), 1),
        "profit_factor": round(profit_factor, 2),
        "total_return_pct": round(100 * trades_df["pnl_pct"].sum(), 4),
        "avg_pips": round(trades_df["pnl_pips"].mean(), 1),
        "avg_win_pct": round(100 * trades_df.loc[winning, "pnl_pct"].mean(), 4) if winning.any() else 0,
        "avg_loss_pct": round(100 * trades_df.loc[losing, "pnl_pct"].mean(), 4) if losing.any() else 0,
        "max_win_pct": round(100 * trades_df["pnl_pct"].max(), 4),
        "max_loss_pct": round(100 * trades_df["pnl_pct"].min(), 4),
    }
    
    return trades_df, stats
