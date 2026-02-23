# Quick Reference: Buy and Sell Signals

## At a Glance

Your EUR/USD trading system now gives you **BOTH entry AND exit signals**:

```
Signal      Icon  Meaning              Action
──────────────────────────────────────────────────────────
LONG        🟢    Time to BUY          Open long position
SELL        🔴    Time to SELL/EXIT    Close long position
DANGER      ⚠️    High volatility      Close IMMEDIATELY
WAIT        🟡    Hold/wait            Do nothing
```

---

## When Trading

### You see 🟢 **LONG**
**→ BUY EUR/USD**
- Enter long position
- Set TP at +60 pips
- Set SL at -30 pips
- Risk 30 pips, reward 60 pips (2:1 ratio)

### You see 🟡 **WAIT**
**→ HOLD** (if in trade) **or WAIT** (if no trade)
- If you're already in a trade: do nothing
- If you're not in a trade: wait for LONG signal

### You see 🔴 **SELL**
**→ CLOSE YOUR LONG POSITION**
- Exit your trade at market
- Conditions have turned bearish
- Chart: NN signal dropped below 0 or prediction turned negative

### You see ⚠️ **DANGER**
**→ CLOSE YOUR LONG POSITION IMMEDIATELY**
- Emergency exit
- Market volatility spiked
- Don't wait for SELL, exit NOW

---

## Dashboard Indicators

### Signal Bar (Top)
```
🟢 BUY / ENTER LONG           ← Open a position
🔴 SELL / EXIT LONG           ← Close your position
⚠️ DANGER / EXIT LONG         ← Emergency exit
🟡 WAIT / HOLD               ← No action
```

### Metrics Row
```
🟢 BUY=8   🔴 SELL=6   ⚠️ DANGER=3   🟡 WAIT=50
  (count)   (count)    (count)      (count)
```

Shows how many of each signal have appeared historically.

---

## Exit Reasons (Why SELL?)

SELL signal triggers when:

1. **NN Goes Bearish** (nn_signal < 0)
   - Neural network flipped from bullish to bearish
   - Original trade thesis is broken
   
2. **Prediction Turns Downside** (lower bound < 0)
   - Forecast changed to expect losses
   - Better to exit than wait for SL
   
3. **Momentum Collapses** (NN low + state weakening)
   - Bullish pressure is fading
   - Regime stability deteriorating
   - Risk increasing

---

## What NN Signal Means

```
NN Signal    Interpretation         Signal Generated
───────────────────────────────────────────────────
+0.50 to +0.80   STRONG BUY        🟢 LONG
+0.35 to +0.50   MODERATE BUY      🟢 LONG  
+0.10 to +0.35   SLIGHT BUY        🟡 WAIT
0.00 to +0.10    NEUTRAL           🟡 WAIT
-0.10 to 0.00    SLIGHT SELL       🟡 WAIT (deteriorating)
-0.20 to -0.10   MODERATE SELL     🔴 SELL (if state unstable)
-0.50 to -0.20   STRONG SELL       🔴 SELL
```

**Key Point**: When NN drops below 0 with rising volatility, you get a SELL signal.

---

## Example Trade Sequence

```
Time    Signal    Your Action           Result
────────────────────────────────────────────────
10:00   🟡 WAIT   Nothing               —
11:00   🟢 LONG   Buy 100K EUR at 1.1822
12:00   🟡 WAIT   Hold                  Price: 1.1835 (+13 pips)
13:00   🟡 WAIT   Hold                  Price: 1.1847 (+25 pips)
14:00   🟡 WAIT   Hold                  Price: 1.1855 (+33 pips)
15:00   🔴 SELL   Close at 1.1857
                  
                  Exit Result: +35 pips ✓

Alternative Scenario:
15:00   ⚠️ DANGER  Exit at 1.1850        Result: +28 pips ✓
                  (beats SL at 1.1792)
```

---

## Comparison: Old vs. New

### OLD WAY (Before SELL Signals)
```
Trades had implicit exits:
✓ TP (take profit at 60 pips)
✓ SL (stop loss at 30 pips)  
✓ DANGER (emergency exit)
✗ NO explicit signal when conditions deteriorate
```

### NEW WAY (With SELL Signals)
```
Trades have explicit signals PLUS implicit exits:
✓ LONG signal for entry
✓ SELL signal when conditions turn (explicit)
✓ WAIT signals to hold
✓ DANGER signal for emergencies
✓ TP/SL still active as backup
```

**Benefit**: You know WHY you're exiting - conditions are clear

---

## Key Parameters (For Understanding)

```python
# When NN drops below 0 + state unstable → SELL
if nn_signal < 0.0 and p_state3 > 0.45:
    signal = SELL

# When prediction shows downside + NN uncertain → SELL
if lower_bound < -0.001 and nn_signal < 0.1:
    signal = SELL

# When momentum collapses + state weakening → SELL
if nn_signal < 0.175 and p_state2 < 0.45:
    signal = SELL
```

---

## Rules for Trading Sell Signals

### ✅ DO

1. **Act on SELL signals** - They prevent larger losses
2. **Close immediately on DANGER** - Don't hesitate
3. **Hold on WAIT** - Don't close early
4. **Monitor in real-time** - Check dashboard every 1-2 hours
5. **Combine signals with TP/SL** - They work together

### ❌ DON'T

1. **Ignore SELL** - It's saving you from bigger losses
2. **Wait past DANGER** - Exit immediately
3. **Trade counter to signals** - Don't short on SELL
4. **Expect perfect timing** - SELL exits at market (may not be 60 pips)
5. **Trust only TP/SL** - SELL signals help optimize exits

---

## Example Profit Impact

### Without SELL Signals
```
Trade 1: LONG 1.1800 → TP at 1.1860 = +60 pips ✓
Trade 2: LONG 1.1850 → SL at 1.1820 = -30 pips ✗
Trade 3: LONG 1.1900 → DANGER exit = +35 pips ✓

Total: 60 - 30 + 35 = +65 pips
```

### With SELL Signals
```
Trade 1: LONG 1.1800 → SELL at 1.1840 = +40 pips ✓
Trade 2: LONG 1.1850 → SELL at 1.1878 = +28 pips ✓
Trade 3: LONG 1.1900 → TP at 1.1960 = +60 pips ✓

Total: 40 + 28 + 60 = +128 pips (+97% better)
```

SELL signals help by:
- Exiting before conditions deteriorate completely
- Converting potential losses into smaller wins
- Improving overall system statistics

---

## Status Messages You'll See

### ✓ Good Signals
```
🎯 TARGETS MET! Win Rate ≥ 50% AND Profit Factor ≥ 2.0

→ System is performing as designed
→ Execute all LONG signals
```

### ⚠️ Partial Performance
```
⚠️  PARTIAL SUCCESS: WR ✓ | PF ✗

→ Win rate good but PF needs work
→ Check if SELL signals are optimizing exits
```

### ❌ Below Targets
```
❌ TARGETS NOT MET - WR: 42% (target >50%) | PF: 1.8 (target ≥2.0)

→ Too many losing trades
→ Make sure you're using SELL signals properly
→ May need to adjust signal mode or parameters
```

---

## Summary

| Your Situation | Signal Shows | You Do |
|---|---|---|
| No position | 🟢 LONG | BUY now |
| In long | 🟡 WAIT | Hold the trade |
| In long | 🔴 SELL | Exit the trade |
| In long | ⚠️ DANGER | EXIT IMMEDIATELY |
| No position | 🟡 WAIT or 🔴 SELL | Do nothing, wait |

**That's it!** Your system now tells you when to buy AND when to sell. 🚀
