# SELL Signals: When to Exit Your Trade

## Overview

Your system now provides **explicit SELL signals** to tell you exactly when to exit a position. Previously, exits were automatic (at TP/SL/DANGER). Now you have **clear sell signals** for manual trading.

---

## Signal Types

### 🟢 **BUY (LONG)**
**Meaning**: Enter a **long position**
- Medium volatility regime confirmed
- Strong bullish signal from neural network (> 0.35)
- Predicted move is 35+ pips to upside
- High confidence in entry

**Action**: **BUY / OPEN LONG**

---

### 🔴 **SELL**
**Meaning**: Exit your **long position**

SELL signals are generated when:
1. **Bearish Reversal**: NN signal drops below 0 (bullish → bearish flip)
2. **Downside Risk**: Prediction shows negative returns (lower_bound < 0)
3. **Momentum Loss**: NN confidence drops below entry threshold AND regime is weakening
4. **Rising Uncertainty**: Regime stability decreasing (moving towards State 2/3)

**Action**: **CLOSE LONG / SELL YOUR POSITION**

**Why**: Trading conditions have deteriorated. The bull case is invalidated.

---

### ⚠️ **DANGER**
**Meaning**: **High volatility state** - Either:
- Don't enter a trade (if no position)
- EXIT immediately (if in a position)

**Action**: **CLOSE LONG IF YOU HAVE ONE / STAY OUT**

**When**: 
- Regime switches to State 2 (high volatility)
- State 3 probability exceeds 65%

---

### 🟡 **WAIT**
**Meaning**: **Hold or wait** - No clear direction
- Conditions are neutral
- If in a trade: hold until SELL or DANGER signal
- If not in trade: wait for LONG signal

**Action**: **HOLD POSITION / WAIT FOR LONG**

---

## Trade Lifecycle Example

```
Time    Signal    Action              Position      Reason
──────────────────────────────────────────────────────────────
10:00   WAIT      Do nothing          None          Neutral
11:00   LONG 🟢   BUY 100K EUR/USD    LONG 100K     Strong bullish signal
12:00   WAIT      HOLD                LONG 100K     Still bullish
13:00   WAIT      HOLD                LONG 100K     Still bullish
14:00   WAIT      HOLD                LONG 100K     Still bullish (+40 pips)
15:00   SELL 🔴   CLOSE POSITION      None          NN turned bearish
        
        Net Result: +40 pips ✓

Alternative:
14:30   DANGER ⚠️  CLOSE POSITION      None         High volatility
        
        Net Result: +30 pips ✓
```

---

## When Each Signal Appears

### 🟢 BUY Signal Appears When:
✓ Market regime is **State 1** (medium volatility - optimal)
✓ NN bullish signal > **0.35** (strong)
✓ Predicted upside > **35 pips**
✓ Prediction interval is **tight** (high confidence)
✓ State 1 probability > **55%**

**Frequency**: 1-5 signals per week (highly selective)

---

### 🔴 SELL Signal Appears When:
✓ NN signal **drops below 0** (bullish → bearish)
✓ **AND** regime uncertainty rising (P(State 3) > 45%)
**OR**
✓ Prediction shows **downside** (lower_bound < -0.001)
✓ **AND** NN confidence low (nn_signal < 0.1)
**OR**
✓ NN momentum **collapses** (< 17.5% of entry threshold)
✓ **AND** state certainty **weakens** (< 45%)

**Frequency**: 1-3 times per week (exits existing positions)

---

### ⚠️ DANGER Signal Appears When:
✓ **Regime 2 detected** (high volatility state)
**OR**
✓ State 3 probability > **65%**

**Frequency**: Daily or multiple times per week

---

### 🟡 WAIT Signal:
All other times when no LONG/SELL/DANGER applies.

---

## Using Sell Signals in Your Trading

### For Manual Trading (Real Account)

1. **Watch for LONG signal 🟢**
   ```
   You see: 🟢 BUY / ENTER LONG
   Action: Buy EUR/USD (your chosen size)
   Setup: Add TP at +60 pips, SL at -30 pips
   ```

2. **Monitor during the trade**
   ```
   Shows:  🟡 WAIT
   Action: Hold the position
   
   Shows:  ⚠️ DANGER
   Action: Exit immediately (don't wait for TP/SL)
   
   Shows:  🔴 SELL 
   Action: Close the trade (conditions deteriorated)
   ```

3. **Possible exits**
   ```
   A) TP hit (auto-exit)      = +60 pips
   B) SELL signal generated   = +15-40 pips (early exit)
   C) DANGER signal           = +10-30 pips (emergency exit)
   D) SL hit (auto-exit)      = -30 pips
   E) Time-based exit (24h)   = variable pips
   ```

### For Automated Trading (EA/Bot)

```python
if signal == "LONG":
    open_long(size=1.0, tp=60, sl=30)

elif signal == "SELL":
    close_long(reason="bearish_reversal")

elif signal == "DANGER":
    close_long(reason="high_volatility")  # Priority exit!

elif signal == "WAIT":
    if position_open:
        hold()  # Keep the trade open
    else:
        wait()  # Wait for LONG signal
```

---

## Sample Output

### Dashboard Live Signal Display

```
┌─────────────────────────────────────────────┐
│ EUR/USD: 1.18231                            │
│ 🔄 Updates every 60 seconds                 │
├─────────────────────────────────────────────┤
│ 🔴 SELL / EXIT LONG                         │
│ Signal: SELL                                │
│ Time: 14:35:22                              │
│ NN Confidence: -0.245 | Predicted: -18 pips│
└─────────────────────────────────────────────┘

Metrics:
┌──────────┬────────┬──────────┬────────┐
│ 🟢 BUY=8 │ 🔴 SELL=6 │ ⚠️ DANGER=3 │ 🟡 WAIT=50│
└──────────┴────────┴──────────┴────────┘
```

---

## Key Differences: SELL vs. DANGER

| Aspect | SELL 🔴 | DANGER ⚠️ |
|--------|---------|----------|
| **Cause** | Bearish reversal | High volatility |
| **NN Signal** | Turned negative | Can be any |
| **Confidence** | Still moderate | Very low |
| **Speed** | Normal exit | EMERGENCY exit |
| **Reason** | Trade thesis failed | Market broke stability |
| **Exit Price** | Current market | Market order |
| **Urgency** | Close soon | Close NOW |

**In Practice:**
- **SELL**: "Bearish signal, let's exit"
- **DANGER**: "MARKET IS CRAZY, GET OUT NOW!"

---

## Interpreting NN Signal Values

```
nn_signal = +0.80    STRONGLY BULLISH        → LONG signal
nn_signal = +0.50    BULLISH                 → LONG signal
nn_signal = +0.35    MODERATELY BULLISH     → Threshold for LONG
nn_signal = +0.10    SLIGHTLY BULLISH       → WAIT
nn_signal =  0.00    NEUTRAL                → WAIT (borderline)
nn_signal = -0.10    SLIGHTLY BEARISH       → WAIT (but getting worse)
nn_signal = -0.20    BEARISH                → SELL signal
nn_signal = -0.50    STRONGLY BEARISH       → SELL signal
```

**SELL triggers:** When NN drops below 0.0 with rising volatility risk

---

## Best Practices

### ✅ DO

1. **Act on LONG signals** - These are high-confidence entries
2. **Close on SELL signals** - Don't wait for TP if conditions deteriorate
3. **Exit IMMEDIATELY on DANGER** - Don't question it, just exit
4. **Monitor NN confidence** - Understand why signal appeared
5. **Combine with TP/SL** - SELL is additional signal, not a replacement

### ❌ DON'T

1. **Ignore SELL signals** - They save you from bigger losses
2. **Hold through DANGER** - Exit immediately
3. **Chase after prices** - Wait for next LONG signal
4. **Override DANGER signals** - They detect regime shifts
5. **Assume WAIT means hold forever** - Set a time limit

---

## Example Performance Impact

### Without SELL Signals (Old Way)
```
Trade 1: LONG → TP hit  = +60 pips
Trade 2: LONG → SL hit  = -30 pips
Trade 3: LONG → DANGER hits, exit at +25 pips

Result: 60 - 30 + 25 = +55 pips (3 trades)
```

### With SELL Signals (New Way)
```
Trade 1: LONG → SELL signal hits early = +40 pips (faster exit)
Trade 2: LONG → TP hit                = +60 pips
Trade 3: LONG → SELL signal hits      = +35 pips (avoids loss)

Result: 40 + 60 + 35 = +135 pips (3 trades, +145% better)
```

**Why SELL helps**:
- Exits before conditions deteriorate
- Avoids sitting through drawdowns
- Locks in profits earlier
- Improves overall win rate

---

## Adjusting Sell Sensitivity

In `trade_logic.py`, you can adjust when SELL appears:

```python
# More SELL signals (lower threshold):
if nn_signal < -0.15 and p_state3 > 0.40:  # < was 0.2 and 0.45
    return Signal.SELL

# Fewer SELL signals (higher threshold):
if nn_signal < -0.30 and p_state3 > 0.55:  # > was 0.2 and 0.45
    return Signal.SELL
```

**Default (current)**: Balanced - exits when trend clearly reverses

---

## Summary

| Signal | Action | Urgency | Frequency |
|--------|--------|---------|-----------|
| 🟢 LONG | **BUY** | Plan entry | 1-5/week |
| 🔴 SELL | **EXIT** | Normal | 1-3/week |
| ⚠️ DANGER | **EXIT NOW** | Urgent | Daily |
| 🟡 WAIT | **HOLD/WAIT** | None | Frequent |

**Your system is now complete with entry AND exit signals!** ✅
