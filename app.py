"""
EUR/USD Quant System - Streamlit Dashboard

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pipeline import EURUSDQuantSystem, create_sample_data
from data_loader import load_eurusd_data
from backtest import run_backtest

st.set_page_config(page_title="EUR/USD Quant System", layout="wide")

st.title("EUR/USD Quant System")
st.caption("LONG only (no shorts) • HMM • RDC • NN • Targets: PF≥2, Win rate≥50%")

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Data Source")
    data_source = st.radio(
        "Source",
        ["live", "auto", "csv", "questdb"],
        format_func=lambda x: "Live (yfinance)" if x == "live" else x,
        horizontal=True
    )
    use_sample = st.checkbox("Use sample data (no real data)", value=False)
    
    live_period, live_interval, auto_refresh, refresh_sec = "5d", "1h", False, 60
    if data_source == "live":
        live_period = st.selectbox("Live period", ["1d", "5d", "7d"], index=1)
        live_interval = st.selectbox("Interval", ["1m", "5m", "1h"], index=0)
        auto_refresh = st.checkbox("Auto-refresh every minute", value=True, help="Updates live price every 60 seconds")
        refresh_sec = 60  # Fixed 60 seconds for minute-by-minute updates
    
    st.header("Parameters")
    rdc_window = st.slider("RDC window", 30, 120, 60, help="60 = optimal for hourly data")
    n_pca = st.slider("PCA components", 3, 10, 5, help="5 = good balance")
    nn_epochs = st.slider("NN epochs", 10, 100, 50, help="50+ for better convergence")
    
    csv_dir = st.text_input(
        "CSV directory (optional)",
        value=r"C:\Users\DELL\OneDrive\Desktop",
        help="Where to find EURUSD_1h_2024_2026.csv"
    )
    
    st.header("Signal Mode")
    signal_mode = st.radio(
        "Mode",
        ["regime", "simple"],
        format_func=lambda x: "Regime (HMM + NN, stricter) 🎯 50%+ WR, PF≥2" if x == "regime" else "Simple (NN only, more signals)",
        horizontal=True,
        help="Regime mode is optimized for 50% win rate and 2.0+ profit factor"
    )
    min_predicted_pips = st.slider("Min predicted pips", 20, 60, 35, help="Only take trades predicting 35+ pips move")
    
    st.header("Backtest Settings (for 50%+ WR & PF≥2)")
    holding_periods = st.slider("Holding periods (bars)", 1, 48, 24, help="Max bars to hold trade")
    take_profit_pips = st.slider("Take profit (pips)", 40, 80, 60, help="TP at 60 pips (2:1 R:R with 30 pips SL)")
    stop_loss_pips = st.slider("Stop loss (pips)", 15, 50, 30, help="SL at 30 pips (mathematically: PF=3 at 50% WR)")
    use_tp_sl = st.checkbox("Use TP/SL", value=True, help="Exit at TP or SL; else time-based only")
    exit_on_danger = st.checkbox("Exit on DANGER signal", value=True, help="Exit immediately on high volatility")

# ── Load Data ────────────────────────────────────────────────
@st.cache_data(ttl=15)
def load_data(source: str, use_sample: bool, csv_dir: str, live_period: str = "5d", live_interval: str = "1h"):
    if use_sample:
        return create_sample_data(n=1000)
    return load_eurusd_data(
        source=source,
        csv_dir=csv_dir if csv_dir else None,
        live_period=live_period,
        live_interval=live_interval
    )

@st.cache_resource
def run_system(df: pd.DataFrame, rdc_window: int, n_pca: int, nn_epochs: int, min_predicted_pips: float, signal_mode: str):
    system = EURUSDQuantSystem(
        rdc_window=rdc_window,
        n_pca_components=n_pca,
        nn_epochs=nn_epochs,
        min_predicted_pips=min_predicted_pips,
        signal_mode=signal_mode,
    )
    return system.run(df, fit=True)

# Auto-refresh for live mode
if data_source == "live" and auto_refresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_sec * 1000, key="live_refresh")
    except ImportError:
        pass

try:
    df = load_data(
        data_source, use_sample, csv_dir,
        live_period=live_period if data_source == "live" else "5d",
        live_interval=live_interval if data_source == "live" else "1h"
    )
    results = run_system(df, rdc_window, n_pca, nn_epochs, min_predicted_pips, signal_mode)
except Exception as e:
    st.error(f"Error: {e}")
    st.info("Try enabling 'Use sample data' or check your data path.")
    st.stop()

close_col = "close" if "close" in df.columns else "Close"

# ── Live signal banner (when live mode) ────────────────────────
if data_source == "live":
    latest_signal = results["signal"].iloc[-1]
    latest_price = df[close_col].iloc[-1]
    latest_time = df.index[-1]
    nn_sig = results["nn_signal"].iloc[-1]
    pred_pips = results["predicted_pips"].iloc[-1]
    
    sig_color = "green" if latest_signal == "LONG" else "red" if latest_signal == "DANGER" else "orange"
    
    # Display live price prominently with auto-update indicator
    col_price, col_info = st.columns([3, 2])
    with col_price:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {sig_color} 0%, rgba(255,255,255,0.1) 100%); padding:20px; border-radius:10px; margin-bottom:15px; border:3px solid {sig_color};">
        <h2 style="margin:0; color:white;">EUR/USD: {latest_price:.5f}</h2>
        <p style="margin:5px 0 0 0; color:white; font-size:14px;">🔄 Updates every 60 seconds</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info:
        st.markdown(f"""
        <div style="background:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:15px;">
        <h3 style="margin:0; color:{sig_color};">Signal: {latest_signal}</h3>
        <p style="margin:5px 0 0 0; font-size:12px;"><b>Time:</b> {latest_time.strftime('%H:%M:%S')}</p>
        <p style="margin:3px 0 0 0; font-size:12px;"><b>NN:</b> {nn_sig:.3f} | <b>Pips:</b> {pred_pips:.1f}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Metrics ──────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Rows", f"{len(df):,}")
with col2:
    st.metric("Date range", f"{df.index[0].strftime('%Y-%m-%d')} → {df.index[-1].strftime('%Y-%m-%d')}")
with col3:
    long_count = (results["signal"] == "LONG").sum()
    st.metric("LONG signals", long_count)
with col4:
    danger_count = (results["signal"] == "DANGER").sum()
    st.metric("DANGER (no longs)", danger_count)
with col5:
    wait_count = (results["signal"] == "WAIT").sum()
    st.metric("WAIT", wait_count)

# ── Backtest ─────────────────────────────────────────────────
trades_df, bt_stats = run_backtest(
    df, results,
    holding_periods=holding_periods,
    close_col=close_col,
    exit_on_danger=exit_on_danger,
    take_profit_pips=take_profit_pips,
    stop_loss_pips=stop_loss_pips,
    use_tp_sl=use_tp_sl,
)

st.subheader("Backtest Results (LONG only — no shorts)")
target_pf, target_wr = 2.0, 50.0
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1:
    wr = bt_stats['win_rate_pct']
    status = "✓" if wr >= target_wr else "⚠"
    st.metric("Win Rate", f"{wr:.1f}%", delta=f"{status} Target: >{target_wr}%")
with col2:
    pf = bt_stats["profit_factor"]
    status = "✓" if pf >= target_pf else "⚠"
    st.metric("Profit Factor", f"{pf:.2f}" if pf != float("inf") else "∞", delta=f"{status} Target: ≥{target_pf}")
with col3:
    st.metric("Total Trades", bt_stats["total_trades"])
with col4:
    st.metric("Avg Pips", f"{bt_stats.get('avg_pips', 0):.1f}", help="Target: 50-70 pips per trade")
with col5:
    st.metric("Total Return", f"{bt_stats['total_return_pct']:.2f}%")
with col6:
    st.metric("Avg Win", f"{bt_stats['avg_win_pct']:.3f}%")
with col7:
    st.metric("Avg Loss", f"{bt_stats['avg_loss_pct']:.3f}%")

# Status bar showing if targets are met
if wr >= target_wr and pf >= target_pf:
    st.success(f"🎯 **TARGETS MET!** Win Rate ≥ {target_wr}% AND Profit Factor ≥ {target_pf}")
elif wr >= target_wr or pf >= target_pf:
    st.info(f"⚠️  **PARTIAL SUCCESS:** {'WR ✓' if wr >= target_wr else 'WR ✗'} | {'PF ✓' if pf >= target_pf else 'PF ✗'}")
else:
    st.warning(f"❌ **TARGETS NOT MET** - WR: {wr:.1f}% (target >{target_wr}) | PF: {pf:.2f} (target ≥{target_pf})")

# ── Charts ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Price & Signals", "Regime", "HMM Probabilities", "Backtest", "Data Table"
])

with tab1:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.4],
        subplot_titles=("EUR/USD Close", "NN Signal")
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df[close_col], name="Close", line=dict(color="#1f77b4")),
        row=1, col=1
    )
    # Mark LONG signals
    long_mask = results["signal"] == "LONG"
    if long_mask.any():
        long_times = results.index[long_mask]
        long_prices = df.loc[long_times, close_col].values
        fig.add_trace(
            go.Scatter(
                x=long_times, y=long_prices,
                mode="markers", name="LONG",
                marker=dict(symbol="triangle-up", size=12, color="green")
            ),
            row=1, col=1
        )
    fig.add_trace(
        go.Scatter(x=results.index, y=results["nn_signal"], name="NN Signal", line=dict(color="#ff7f0e")),
        row=2, col=1
    )
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", row=2, col=1)
    fig.add_hline(y=-0.5, line_dash="dash", line_color="gray", row=2, col=1)
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    regime_map = {0: "S1 (Low Vol)", 1: "S2 (Medium Vol)", 2: "S3 (High Vol)"}
    results["regime_label"] = results["regime"].map(regime_map)
    fig = go.Figure()
    for regime_id, label in regime_map.items():
        mask = results["regime"] == regime_id
        fig.add_trace(
            go.Scatter(
                x=results.index[mask], y=df.loc[results.index[mask], close_col],
                mode="markers", name=label,
                marker=dict(size=4, opacity=0.7)
            )
        )
    fig.update_layout(
        title="Price colored by HMM regime",
        xaxis_title="Time",
        yaxis_title="Close",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    if len(trades_df) > 0:
        # Equity curve
        trades_df = trades_df.copy()
        trades_df["cumulative_return"] = trades_df["pnl_pct"].cumsum()
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=("Cumulative Return (%)", "Trade PnL (%)")
        )
        fig.add_trace(
            go.Scatter(
                x=trades_df["exit_time"],
                y=100 * trades_df["cumulative_return"],
                fill="tozeroy",
                name="Cumulative Return"
            ),
            row=1, col=1
        )
        colors = ["green" if p > 0 else "red" for p in trades_df["pnl_pct"]]
        fig.add_trace(
            go.Bar(
                x=trades_df["exit_time"],
                y=100 * trades_df["pnl_pct"],
                name="Trade PnL",
                marker_color=colors
            ),
            row=2, col=1
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        display_cols = ["entry_time", "exit_time", "entry_price", "exit_price", "pnl_pips", "pnl_pct", "exit_reason", "bars_held"]
        display_df = trades_df[[c for c in display_cols if c in trades_df.columns]].copy()
        if "pnl_pct" in display_df.columns:
            display_df["pnl_pct"] = display_df["pnl_pct"].apply(lambda x: f"{x:.4%}")
        st.dataframe(display_df, use_container_width=True, height=300)
    else:
        st.info("No trades executed. Check if you have LONG signals.")

with tab3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results.index, y=results["p_state1"], name="P(State 1)"))
    fig.add_trace(go.Scatter(x=results.index, y=results["p_state2"], name="P(State 2)"))
    fig.add_trace(go.Scatter(x=results.index, y=results["p_state3"], name="P(State 3)"))
    fig.update_layout(
        title="HMM Smoothed Probabilities",
        xaxis_title="Time",
        yaxis_title="Probability",
        yaxis_range=[0, 1],
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.dataframe(
        results.join(df[[close_col]], how="left").tail(100),
        use_container_width=True,
        height=400
    )

# ── Signal counts ────────────────────────────────────────────
st.subheader("Signal distribution")
st.bar_chart(results["signal"].value_counts())

# ── Diagnostic: why no signals? ─────────────────────────────
with st.expander("Diagnostic: signal blockers"):
    st.caption("If you get no LONG signals, check these distributions.")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.write("**Regime distribution**")
        st.bar_chart(results["regime"].value_counts().sort_index())
    with d2:
        st.write("**NN signal** (need > 0.2)")
        st.metric("Mean", f"{results['nn_signal'].mean():.3f}")
        st.metric("Max", f"{results['nn_signal'].max():.3f}")
        st.metric("Count > 0.2", f"{(results['nn_signal'] > 0.2).sum()}")
    with d3:
        st.write("**Predicted pips** (upper_bound)")
        st.metric("Mean", f"{results['predicted_pips'].mean():.1f}")
        st.metric("Max", f"{results['predicted_pips'].max():.1f}")
        st.metric("Count >= 30", f"{(results['predicted_pips'] >= 30).sum()}")
    st.write("**P(State 2)** (need > 0.4 for State 2):")
    st.metric("Mean", f"{results['p_state2'].mean():.3f}")
    st.metric("Count > 0.4", f"{(results['p_state2'] > 0.4).sum()}")
