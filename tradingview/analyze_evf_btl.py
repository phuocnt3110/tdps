#!/usr/bin/env python3
"""
analyze_evf_btl.py - Phân tích EVF theo điều kiện BTL (12/01/2026 - 10/03/2026)
Sử dụng vnstock (VCI) để lấy dữ liệu OHLCV.
Tính toán tất cả BTL conditions theo ngày để tìm cơ hội cải thiện.
"""
import sys, os, warnings
warnings.filterwarnings('ignore')
_vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vnstock')
if os.path.exists(_vp): sys.path.insert(0, _vp)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from vnstock import Quote
except ImportError:
    print("ERROR: pip install vnstock"); sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
SYMBOL = "EVF"
ANALYSIS_START = "2026-01-12"
ANALYSIS_END = "2026-03-10"
# Need ~200 bars before analysis start for MA150 + RSI warm-up
DATA_START = "2025-04-01"  # ~9 months before for indicator warm-up
DATA_END = "2026-03-12"

# BTL Parameters (matching Pine Script)
MA150_LEN = 150
DARVAS_LEN = 20
DARVAS_MAX_WIDTH = 15.0  # %
DARVAS_MIN_WIDTH = 3.0   # %
VOL_MA_LEN = 20
VOL_CONFIRM_MULT = 1.5
RSI_OVERSOLD = 30
RSI_LOOKBACK = 100  # bars
EMA12_LEN = 12
EMA36_LEN = 36
MAX_STOP_PCT = 10.0
MIN_RR = 2.0

# ═══════════════════════════════════════════════════════════════
# FETCH DATA
# ═══════════════════════════════════════════════════════════════
print(f"Fetching {SYMBOL} data from {DATA_START} to {DATA_END}...")
q = Quote(source="vci", symbol=SYMBOL, show_log=False)
df = q.history(start=DATA_START, end=DATA_END, interval="1D")

if df is None or df.empty:
    print("ERROR: No data returned"); sys.exit(1)

# Normalize columns
df['date'] = pd.to_datetime(df['time']).dt.date
df = df.sort_values('date').reset_index(drop=True)
print(f"Got {len(df)} bars from {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

# ═══════════════════════════════════════════════════════════════
# CALCULATE INDICATORS
# ═══════════════════════════════════════════════════════════════

# Basic OHLCV
O = df['open'].values.astype(float)
H = df['high'].values.astype(float)
L = df['low'].values.astype(float)
C = df['close'].values.astype(float)
V = df['volume'].values.astype(float)

n = len(df)

# --- Moving Averages ---
def sma(arr, period):
    result = np.full(len(arr), np.nan)
    for i in range(period - 1, len(arr)):
        result[i] = np.mean(arr[i - period + 1:i + 1])
    return result

def ema(arr, period):
    result = np.full(len(arr), np.nan)
    k = 2.0 / (period + 1)
    # Find first valid
    for i in range(len(arr)):
        if not np.isnan(arr[i]):
            result[i] = arr[i]
            for j in range(i + 1, len(arr)):
                result[j] = arr[j] * k + result[j-1] * (1 - k)
            break
    return result

ma150 = sma(C, MA150_LEN)
ma20 = sma(C, 20)
vol_ma = sma(V, VOL_MA_LEN)
ema12 = ema(C, EMA12_LEN)
ema36 = ema(C, EMA36_LEN)

# --- MA150 Slope (10-bar) ---
ma150_slope = np.full(n, np.nan)
for i in range(10, n):
    if not np.isnan(ma150[i]) and not np.isnan(ma150[i-10]):
        ma150_slope[i] = ma150[i] - ma150[i-10]

# --- RSI (14-period) ---
def calc_rsi(close, period=14):
    result = np.full(len(close), np.nan)
    for i in range(period, len(close)):
        gains = []
        losses = []
        for j in range(i - period + 1, i + 1):
            delta = close[j] - close[j-1]
            gains.append(max(delta, 0))
            losses.append(max(-delta, 0))
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            result[i] = 100
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - 100 / (1 + rs)
    return result

rsi14 = calc_rsi(C, 14)

# --- Weekly RSI approximation (use 5-day aggregation) ---
# Approximate weekly bars from daily data
def calc_weekly_rsi(close, daily_period=5, rsi_period=14):
    """Approximate weekly RSI from daily data"""
    # Create weekly closes (every 5 bars)
    weekly_closes = []
    weekly_indices = []
    for i in range(daily_period - 1, len(close), daily_period):
        weekly_closes.append(close[i])
        weekly_indices.append(i)
    
    if len(weekly_closes) < rsi_period + 1:
        return np.full(len(close), np.nan)
    
    wc = np.array(weekly_closes)
    w_rsi = calc_rsi(wc, rsi_period)
    
    # Map back to daily
    result = np.full(len(close), np.nan)
    for wi, di in enumerate(weekly_indices):
        if not np.isnan(w_rsi[wi]):
            # Fill forward for 5 bars
            for d in range(max(0, di - daily_period + 1), min(len(close), di + 1)):
                result[d] = w_rsi[wi]
    # Forward fill
    last_val = np.nan
    for i in range(len(result)):
        if not np.isnan(result[i]):
            last_val = result[i]
        elif not np.isnan(last_val):
            result[i] = last_val
    return result

rsi_weekly = calc_weekly_rsi(C)

# --- Weinstein Stages ---
def calc_stages(close, ma150, slope, n):
    wStage1 = np.zeros(n, dtype=bool)
    wStage2Early = np.zeros(n, dtype=bool)
    wStage4 = np.zeros(n, dtype=bool)
    wStage1Breakout = np.zeros(n, dtype=bool)
    wStage3 = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        if np.isnan(ma150[i]) or np.isnan(slope[i]) or ma150[i] == 0:
            continue
        
        dist_pct = abs(close[i] - ma150[i]) / ma150[i] * 100
        slope_pct = abs(slope[i]) / ma150[i] * 100
        
        wStage1[i] = dist_pct < 5 and slope_pct < 1
        wStage2Early[i] = close[i] > ma150[i] and slope[i] > 0 and close[i] > ma150[i] * 1.02
        wStage4[i] = close[i] < ma150[i] and slope[i] < 0
        
        # Stage 1 Breakout: close crosses above MA150 with volume
        if i > 0 and not np.isnan(ma150[i-1]):
            wStage1Breakout[i] = (close[i] > ma150[i] and close[i-1] <= ma150[i-1] 
                                   and V[i] > (vol_ma[i] * 1.3 if not np.isnan(vol_ma[i]) else 0))
        
        # Stage 3: above MA but slope flattening, excludes others
        slope_flat = abs(slope[i]) / ma150[i] * 100 < 0.5
        wStage3[i] = (close[i] > ma150[i] and slope_flat 
                      and not wStage1[i] and not wStage2Early[i] and not wStage1Breakout[i])
    
    return wStage1, wStage2Early, wStage4, wStage1Breakout, wStage3

wStage1, wStage2Early, wStage4, wStage1Breakout, wStage3 = calc_stages(C, ma150, ma150_slope, n)

# Combined stage label
def stage_label(i):
    if wStage4[i]: return "Stage 4"
    if wStage1Breakout[i]: return "S1->2 BO"
    if wStage2Early[i]: return "Stage 2"
    if wStage3[i]: return "Stage 3"
    if wStage1[i]: return "Stage 1"
    return "Transition"

# --- Darvas Box (using [1] anti-repaint) ---
darvas_high = np.full(n, np.nan)
darvas_low = np.full(n, np.nan)
darvas_width = np.full(n, np.nan)
valid_darvas = np.zeros(n, dtype=bool)
darvas_breakout = np.zeros(n, dtype=bool)
darvas_vol_confirm = np.zeros(n, dtype=bool)

for i in range(DARVAS_LEN + 1, n):
    # Use [1] offset: highest/lowest of bars [i-DARVAS_LEN, i-1] (exclude current bar)
    dh = np.max(H[i - DARVAS_LEN:i])
    dl = np.min(L[i - DARVAS_LEN:i])
    darvas_high[i] = dh
    darvas_low[i] = dl
    if dl > 0:
        w = (dh - dl) / dl * 100
        darvas_width[i] = w
        valid_darvas[i] = DARVAS_MIN_WIDTH <= w <= DARVAS_MAX_WIDTH
    
    # Breakout: close > darvas_high AND prev close <= prev darvas_high
    if i > 0 and not np.isnan(darvas_high[i-1]):
        darvas_breakout[i] = C[i] > dh and C[i-1] <= darvas_high[i-1]
    
    # Volume confirmation
    if not np.isnan(vol_ma[i]) and vol_ma[i] > 0:
        darvas_vol_confirm[i] = V[i] > vol_ma[i] * VOL_CONFIRM_MULT

# --- EMA conditions ---
ema_cross_up = np.zeros(n, dtype=bool)
ema_above = np.zeros(n, dtype=bool)
for i in range(1, n):
    if not np.isnan(ema12[i]) and not np.isnan(ema36[i]):
        ema_above[i] = ema12[i] > ema36[i]
        if not np.isnan(ema12[i-1]) and not np.isnan(ema36[i-1]):
            ema_cross_up[i] = ema12[i] > ema36[i] and ema12[i-1] <= ema36[i-1]

# --- RSI oversold tracking ---
weekly_oversold = np.zeros(n, dtype=bool)
was_oversold_recently = np.zeros(n, dtype=bool)
bars_since_oversold = np.full(n, np.nan)

for i in range(n):
    if not np.isnan(rsi_weekly[i]):
        weekly_oversold[i] = rsi_weekly[i] < RSI_OVERSOLD

# Calculate bars since oversold
last_os_bar = -999
for i in range(n):
    if weekly_oversold[i]:
        last_os_bar = i
    if last_os_bar >= 0:
        bars_since_oversold[i] = i - last_os_bar
        was_oversold_recently[i] = (i - last_os_bar) <= RSI_LOOKBACK
    else:
        bars_since_oversold[i] = np.nan
        was_oversold_recently[i] = False

# --- BTL Stop & R:R ---
stop_pct = np.full(n, 99.0)
rr_ratio = np.full(n, 0.0)
stop_ok = np.zeros(n, dtype=bool)
rr_ok = np.zeros(n, dtype=bool)

for i in range(n):
    if not np.isnan(darvas_low[i]) and C[i] > darvas_low[i]:
        sp = (C[i] - darvas_low[i]) / C[i] * 100
        stop_pct[i] = sp
        stop_ok[i] = sp <= MAX_STOP_PCT
        rr_ratio[i] = 20.0 / sp if sp > 0 else 0
        rr_ok[i] = rr_ratio[i] >= MIN_RR

# --- isAboveTheLine / isBelowTheLine ---
is_atl = np.zeros(n, dtype=bool)
for i in range(n):
    if (not np.isnan(ma150[i]) and not np.isnan(sma(C, 200)[i] if i >= 199 else np.nan)):
        ma200 = sma(C, 200)
        ma50 = sma(C, 50)
        break

ma50 = sma(C, 50)
ma200 = sma(C, 200)

for i in range(n):
    if all(not np.isnan(x[i]) for x in [ma50, ma150, ma200]):
        is_atl[i] = C[i] > ma150[i] and C[i] > ma200[i] and ma50[i] > ma150[i] and ma50[i] > ma200[i]
is_btl = ~is_atl

# --- Unified BTL Buy Condition ---
btl_darvas_ok = valid_darvas & darvas_breakout & darvas_vol_confirm
btl_rsi_ok = was_oversold_recently
btl_ema_ok = ema_above
btl_buy = (is_btl & ~wStage4 & btl_darvas_ok & btl_rsi_ok & btl_ema_ok & stop_ok & rr_ok)

# ═══════════════════════════════════════════════════════════════
# ANALYSIS - Focus on 12/01/2026 - 10/03/2026
# ═══════════════════════════════════════════════════════════════
analysis_start = datetime.strptime(ANALYSIS_START, "%Y-%m-%d").date()
analysis_end = datetime.strptime(ANALYSIS_END, "%Y-%m-%d").date()
mask = (df['date'] >= analysis_start) & (df['date'] <= analysis_end)
idx_range = df[mask].index.tolist()

print(f"\n{'='*120}")
print(f"EVF BTL CONDITION ANALYSIS: {ANALYSIS_START} → {ANALYSIS_END}")
print(f"{'='*120}")

# Header
print(f"\n{'Date':>12} {'Close':>8} {'MA150':>8} {'Stage':>10} | {'Box':>4} {'DrvH':>8} {'DrvL':>8} {'Wid%':>5} {'BO':>3} {'Vol':>4} | {'RSIw':>5} {'WasOS':>5} {'OSD':>4} | {'EMA12':>8} {'EMA36':>8} {'E>36':>4} | {'Stp%':>5} {'R:R':>4} | {'BUY':>3}")
print("-" * 120)

for i in idx_range:
    dt = df['date'].iloc[i]
    stage = stage_label(i)
    
    box_status = "✓" if valid_darvas[i] else "✗"
    bo = "✓" if darvas_breakout[i] else " "
    vc = "✓" if darvas_vol_confirm[i] else " "
    
    wos = "✓" if was_oversold_recently[i] else "✗"
    osd = f"{int(bars_since_oversold[i])}" if not np.isnan(bars_since_oversold[i]) else "n/a"
    
    ea = "✓" if ema_above[i] else "✗"
    
    sp = f"{stop_pct[i]:.1f}" if stop_pct[i] < 90 else "n/a"
    rr = f"{rr_ratio[i]:.1f}" if rr_ratio[i] > 0 else "n/a"
    
    buy = "★" if btl_buy[i] else " "
    
    rsiw_str = f"{rsi_weekly[i]:.1f}" if not np.isnan(rsi_weekly[i]) else "n/a"
    e12 = f"{ema12[i]:.0f}" if not np.isnan(ema12[i]) else "n/a"
    e36 = f"{ema36[i]:.0f}" if not np.isnan(ema36[i]) else "n/a"
    dh = f"{darvas_high[i]:.0f}" if not np.isnan(darvas_high[i]) else "n/a"
    dl = f"{darvas_low[i]:.0f}" if not np.isnan(darvas_low[i]) else "n/a"
    dw = f"{darvas_width[i]:.1f}" if not np.isnan(darvas_width[i]) else "n/a"
    m150 = f"{ma150[i]:.0f}" if not np.isnan(ma150[i]) else "n/a"
    
    print(f"{dt!s:>12} {C[i]:>8.0f} {m150:>8} {stage:>10} | {box_status:>4} {dh:>8} {dl:>8} {dw:>5} {bo:>3} {vc:>4} | {rsiw_str:>5} {wos:>5} {osd:>4} | {e12:>8} {e36:>8} {ea:>4} | {sp:>5} {rr:>4} | {buy:>3}")

# ═══════════════════════════════════════════════════════════════
# SUMMARY: Why no BTL signal? Condition breakdown
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*120}")
print("CONDITION SUMMARY (% of days in analysis period where condition = TRUE)")
print(f"{'='*120}")

total_days = len(idx_range)
def pct_true(arr):
    return sum(1 for i in idx_range if arr[i]) / total_days * 100

conditions = [
    ("isBelowTheLine", is_btl),
    ("not wStage4", ~wStage4),
    ("wasOversoldRecently", was_oversold_recently),
    ("validDarvasBox", valid_darvas),
    ("darvasBreakout", darvas_breakout),
    ("darvasVolConfirm", darvas_vol_confirm),
    ("btlDarvasOK (all 3)", btl_darvas_ok),
    ("emaAbove (EMA12>EMA36)", ema_above),
    ("stopOK (<=10%)", stop_ok),
    ("rrOK (>=2:1)", rr_ok),
    ("FULL BTL BUY", btl_buy),
]

for name, arr in conditions:
    days_true = sum(1 for i in idx_range if arr[i])
    print(f"  {name:<30} : {days_true:>3}/{total_days} days ({pct_true(arr):>5.1f}%)")

# ═══════════════════════════════════════════════════════════════
# PRICE PERFORMANCE in analysis period
# ═══════════════════════════════════════════════════════════════
if idx_range:
    start_price = C[idx_range[0]]
    end_price = C[idx_range[-1]]
    max_price = max(C[i] for i in idx_range)
    min_price = min(C[i] for i in idx_range)
    max_gain = (max_price - start_price) / start_price * 100
    
    print(f"\n{'='*120}")
    print("PRICE PERFORMANCE")
    print(f"{'='*120}")
    print(f"  Start: {start_price:.0f} ({ANALYSIS_START})")
    print(f"  End:   {end_price:.0f} ({ANALYSIS_END})")
    print(f"  High:  {max_price:.0f} (Max gain: {max_gain:+.1f}%)")
    print(f"  Low:   {min_price:.0f}")
    print(f"  Return:{(end_price - start_price) / start_price * 100:+.1f}%")

# ═══════════════════════════════════════════════════════════════
# KEY EVENTS: EMA cross, Stage transitions, Darvas events
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*120}")
print("KEY EVENTS IN PERIOD")
print(f"{'='*120}")

for i in idx_range:
    events = []
    if ema_cross_up[i]:
        events.append("★ EMA12 crosses above EMA36")
    if i > 0 and ema_above[i] and not ema_above[i-1]:
        events.append("EMA12 > EMA36 (starts)")
    if i > 0 and not ema_above[i] and ema_above[i-1]:
        events.append("EMA12 < EMA36 (lost)")
    if wStage1Breakout[i]:
        events.append("★★ Stage 1→2 BREAKOUT")
    if i > 0 and stage_label(i) != stage_label(i-1):
        events.append(f"Stage change: {stage_label(i-1)} → {stage_label(i)}")
    if darvas_breakout[i]:
        events.append(f"Darvas Breakout (High={darvas_high[i]:.0f})")
    if i > 0 and valid_darvas[i] and not valid_darvas[i-1]:
        events.append(f"Darvas Box becomes VALID (width={darvas_width[i]:.1f}%)")
    if i > 0 and not valid_darvas[i] and valid_darvas[i-1]:
        events.append(f"Darvas Box becomes INVALID (width={darvas_width[i]:.1f}%)")
    
    if events:
        print(f"  {df['date'].iloc[i]} | Close: {C[i]:.0f} | {' | '.join(events)}")

# ═══════════════════════════════════════════════════════════════
# RELAXED SCENARIOS: What if we relaxed conditions?
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*120}")
print("RELAXED SCENARIO ANALYSIS")
print(f"{'='*120}")

# Scenario 1: Relax Darvas width to 20%
for i in idx_range:
    if not np.isnan(darvas_width[i]):
        relaxed_box = DARVAS_MIN_WIDTH <= darvas_width[i] <= 20.0
    else:
        relaxed_box = False
    if is_btl[i] and not wStage4[i] and relaxed_box and darvas_breakout[i] and darvas_vol_confirm[i] and was_oversold_recently[i] and ema_above[i] and stop_ok[i] and rr_ok[i]:
        print(f"  [Relax Box 20%] BUY on {df['date'].iloc[i]} at {C[i]:.0f}")

# Scenario 2: Relax Darvas width to 25%
for i in idx_range:
    if not np.isnan(darvas_width[i]):
        relaxed_box = DARVAS_MIN_WIDTH <= darvas_width[i] <= 25.0
    else:
        relaxed_box = False
    if is_btl[i] and not wStage4[i] and relaxed_box and darvas_breakout[i] and darvas_vol_confirm[i] and was_oversold_recently[i] and ema_above[i] and stop_ok[i] and rr_ok[i]:
        print(f"  [Relax Box 25%] BUY on {df['date'].iloc[i]} at {C[i]:.0f}")

# Scenario 3: Remove Darvas requirement, keep RSI+EMA
for i in idx_range:
    if is_btl[i] and not wStage4[i] and was_oversold_recently[i] and ema_above[i]:
        # Just check price momentum
        if i > 0 and C[i] > C[i-1] and V[i] > vol_ma[i] * 1.3 if not np.isnan(vol_ma[i]) else False:
            print(f"  [No Darvas, RSI+EMA+Vol] Signal on {df['date'].iloc[i]} at {C[i]:.0f} | Vol: {V[i]/vol_ma[i]:.1f}x")

# Scenario 4: EMA cross up as trigger (not just above)
for i in idx_range:
    if is_btl[i] and not wStage4[i] and was_oversold_recently[i] and ema_cross_up[i]:
        print(f"  [EMA Cross Up trigger] Signal on {df['date'].iloc[i]} at {C[i]:.0f} | RSIw: {rsi_weekly[i]:.1f}")

# Scenario 5: Relax RSI oversold to < 40 
was_os40 = np.zeros(n, dtype=bool)
last_os40_bar = -999
for i in range(n):
    if not np.isnan(rsi_weekly[i]) and rsi_weekly[i] < 40:
        last_os40_bar = i
    if last_os40_bar >= 0:
        was_os40[i] = (i - last_os40_bar) <= RSI_LOOKBACK

for i in idx_range:
    if is_btl[i] and not wStage4[i] and was_os40[i] and ema_cross_up[i]:
        print(f"  [RSI<40 + EMA Cross] Signal on {df['date'].iloc[i]} at {C[i]:.0f} | RSIw: {rsi_weekly[i]:.1f}")

# Scenario 6: Simple momentum: Price > MA150 + EMA12 > EMA36 + Volume surge
for i in idx_range:
    if not np.isnan(ma150[i]) and not np.isnan(vol_ma[i]):
        above_ma150 = C[i] > ma150[i]
        vol_surge = V[i] > vol_ma[i] * 1.5
        if is_btl[i] and above_ma150 and ema_above[i] and vol_surge and i > 0 and C[i] > C[i-1]:
            print(f"  [Above MA150+EMA+Vol] Signal on {df['date'].iloc[i]} at {C[i]:.0f} | Dist MA150: {(C[i]-ma150[i])/ma150[i]*100:.1f}%")

# ═══════════════════════════════════════════════════════════════
# IDEAL ENTRY ANALYSIS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*120}")
print("IDEAL ENTRY RETROSPECTIVE (What would have been the best buy?)")
print(f"{'='*120}")

# Find the peak price in period
if idx_range:
    peak_idx = max(idx_range, key=lambda i: C[i])
    peak_price = C[peak_idx]
    peak_date = df['date'].iloc[peak_idx]
    
    # For each day, calculate forward return to peak
    print(f"  Peak: {peak_price:.0f} on {peak_date}")
    print(f"\n  {'Date':>12} {'Close':>8} {'To Peak%':>8} {'Stage':>10} {'EMA>36':>6} {'WasOS':>5} {'Box':>4} {'StopOK':>6}")
    print(f"  {'-'*70}")
    
    for i in idx_range:
        if i <= peak_idx:
            fwd_return = (peak_price - C[i]) / C[i] * 100
            print(f"  {df['date'].iloc[i]!s:>12} {C[i]:>8.0f} {fwd_return:>+7.1f}% {stage_label(i):>10} {'✓' if ema_above[i] else '✗':>6} {'✓' if was_oversold_recently[i] else '✗':>5} {'✓' if valid_darvas[i] else '✗':>4} {'✓' if stop_ok[i] else '✗':>6}")

print(f"\n{'='*120}")
print("ANALYSIS COMPLETE")
print(f"{'='*120}")
