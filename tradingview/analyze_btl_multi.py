#!/usr/bin/env python3
"""
analyze_btl_multi.py - Multi-stock BTL Signal Analysis & Optimization
=====================================================================
Phân tích toàn diện BTL buy signals trên nhiều mã để tối ưu:
- Forward returns: T+2, T+7, T+14, T+30
- Win rate theo từng điều kiện & tổ hợp
- Chase filter (không mua đuổi >3% so với pivot)
- Parameter sensitivity analysis
- Cross-stock correlation & statistics
"""
import sys, os, warnings, time, io
warnings.filterwarnings('ignore')

# Fix encoding for Windows pipe/redirect
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

_vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vnstock')
if os.path.exists(_vp): sys.path.insert(0, _vp)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from vnstock import Quote
except ImportError:
    print("ERROR: pip install vnstock"); sys.exit(1)

# Tee output to file
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "btl_output.txt")
class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            try: s.write(data); s.flush()
            except: pass
    def flush(self):
        for s in self.streams:
            try: s.flush()
            except: pass

_log_file = open(OUTPUT_FILE, "w", encoding="utf-8")
sys.stdout = Tee(sys.stdout, _log_file)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
STOCKS = [
    # (symbol, analysis_start, analysis_end)
    ("EVF", "2026-01-06", "2026-03-10"),
    ("GSP", "2026-01-06", "2026-03-10"),
    ("PVC", "2025-12-22", "2026-03-10"),
    ("STB", "2025-12-22", "2026-03-10"),
    ("G36", "2025-05-01", "2026-03-10"),
    ("PLX", "2025-12-03", "2026-03-10"),
    ("DPM", "2025-06-06", "2026-03-10"),
    ("PHR", "2025-05-26", "2026-03-10"),
    ("DGW", "2025-05-16", "2026-03-10"),
    ("VHC", "2025-12-24", "2026-03-10"),
    ("HPG", "2025-06-19", "2025-09-17"),
    ("BFC", "2026-01-06", "2026-03-10"),
]

# BTL Parameters (matching Pine Script defaults)
MA150_LEN = 150
DARVAS_LEN = 20
DARVAS_MAX_WIDTH = 15.0
DARVAS_MIN_WIDTH = 3.0
VOL_MA_LEN = 20
VOL_CONFIRM_MULT = 1.5
RSI_OVERSOLD = 30
RSI_LOOKBACK = 100
EMA12_LEN = 12
EMA36_LEN = 36
MAX_STOP_PCT = 10.0
MIN_RR = 2.0
CHASE_MAX_PCT = 3.0  # Max % above Darvas High to avoid chasing

# Forward return horizons (trading days)
FWD_HORIZONS = {"T+2": 2, "T+7": 7, "T+14": 14, "T+30": 30}

# API throttle
API_SLEEP = 1.5

# ═══════════════════════════════════════════════════════════════
# INDICATOR FUNCTIONS (matching Pine Script exactly)
# ═══════════════════════════════════════════════════════════════

def sma(arr, period):
    result = np.full(len(arr), np.nan)
    for i in range(period - 1, len(arr)):
        result[i] = np.mean(arr[i - period + 1:i + 1])
    return result

def ema(arr, period):
    result = np.full(len(arr), np.nan)
    k = 2.0 / (period + 1)
    for i in range(len(arr)):
        if not np.isnan(arr[i]):
            result[i] = arr[i]
            for j in range(i + 1, len(arr)):
                result[j] = arr[j] * k + result[j-1] * (1 - k)
            break
    return result

def calc_rsi(close, period=14):
    result = np.full(len(close), np.nan)
    for i in range(period, len(close)):
        gains, losses = [], []
        for j in range(i - period + 1, i + 1):
            d = close[j] - close[j-1]
            gains.append(max(d, 0))
            losses.append(max(-d, 0))
        avg_g = np.mean(gains)
        avg_l = np.mean(losses)
        result[i] = 100 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    return result

def calc_weekly_rsi(close, daily_period=5, rsi_period=14):
    wc, wi = [], []
    for i in range(daily_period - 1, len(close), daily_period):
        wc.append(close[i]); wi.append(i)
    if len(wc) < rsi_period + 1:
        return np.full(len(close), np.nan)
    w_rsi = calc_rsi(np.array(wc), rsi_period)
    result = np.full(len(close), np.nan)
    for idx, di in enumerate(wi):
        if not np.isnan(w_rsi[idx]):
            for d in range(max(0, di - daily_period + 1), min(len(close), di + 1)):
                result[d] = w_rsi[idx]
    last = np.nan
    for i in range(len(result)):
        if not np.isnan(result[i]): last = result[i]
        elif not np.isnan(last): result[i] = last
    return result

# ═══════════════════════════════════════════════════════════════
# STOCK ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════

def analyze_stock(symbol, analysis_start_str, analysis_end_str):
    """Full BTL analysis for one stock. Returns dict with signals & metrics."""
    
    a_start = datetime.strptime(analysis_start_str, "%Y-%m-%d").date()
    a_end = datetime.strptime(analysis_end_str, "%Y-%m-%d").date()
    # Need ~250 bars before analysis_start for MA150 + RSI warm-up
    data_start = (a_start - timedelta(days=400)).strftime("%Y-%m-%d")
    # Need 30 bars after analysis_end for T+30 forward return
    data_end = (a_end + timedelta(days=50)).strftime("%Y-%m-%d")
    
    print(f"\n  Fetching {symbol}...", end=" ", flush=True)
    try:
        q = Quote(source="vci", symbol=symbol, show_log=False)
        df = q.history(start=data_start, end=data_end, interval="1D")
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    
    if df is None or df.empty:
        print("NO DATA")
        return None
    
    df['date'] = pd.to_datetime(df['time']).dt.date
    df = df.sort_values('date').reset_index(drop=True)
    print(f"{len(df)} bars [{df['date'].iloc[0]} → {df['date'].iloc[-1]}]")
    
    O = df['open'].values.astype(float)
    H = df['high'].values.astype(float)
    L = df['low'].values.astype(float)
    C = df['close'].values.astype(float)
    V = df['volume'].values.astype(float)
    n = len(df)
    
    # --- Indicators ---
    ma50  = sma(C, 50)
    ma150 = sma(C, MA150_LEN)
    ma200 = sma(C, 200)
    vol_ma = sma(V, VOL_MA_LEN)
    vol_ma50 = sma(V, 50)
    _ema12 = ema(C, EMA12_LEN)
    _ema36 = ema(C, EMA36_LEN)
    
    # MA150 slope
    ma150_slope = np.full(n, np.nan)
    for i in range(10, n):
        if not np.isnan(ma150[i]) and not np.isnan(ma150[i-10]):
            ma150_slope[i] = ma150[i] - ma150[i-10]
    
    # RSI
    rsi_weekly = calc_weekly_rsi(C)
    rsi14 = calc_rsi(C, 14)
    
    # ATR(14)
    atr14 = np.full(n, np.nan)
    for i in range(1, n):
        tr = max(H[i] - L[i], abs(H[i] - C[i-1]), abs(L[i] - C[i-1]))
        if i == 1:
            atr14[i] = tr
        elif not np.isnan(atr14[i-1]):
            atr14[i] = (atr14[i-1] * 13 + tr) / 14
    
    # Weinstein Stages
    wStage1 = np.zeros(n, dtype=bool)
    wStage2 = np.zeros(n, dtype=bool)
    wStage4 = np.zeros(n, dtype=bool)
    wStage1BO = np.zeros(n, dtype=bool)
    wStage3 = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        if np.isnan(ma150[i]) or np.isnan(ma150_slope[i]) or ma150[i] == 0:
            continue
        dist = abs(C[i] - ma150[i]) / ma150[i] * 100
        slp = abs(ma150_slope[i]) / ma150[i] * 100
        wStage1[i] = dist < 5 and slp < 1
        wStage2[i] = C[i] > ma150[i] and ma150_slope[i] > 0 and C[i] > ma150[i] * 1.02
        wStage4[i] = C[i] < ma150[i] and ma150_slope[i] < 0
        if i > 0 and not np.isnan(ma150[i-1]):
            vol_ok = V[i] > (vol_ma[i] * 1.3 if not np.isnan(vol_ma[i]) else 0)
            wStage1BO[i] = C[i] > ma150[i] and C[i-1] <= ma150[i-1] and vol_ok
        slp_flat = abs(ma150_slope[i]) / ma150[i] * 100 < 0.5
        wStage3[i] = C[i] > ma150[i] and slp_flat and not wStage1[i] and not wStage2[i] and not wStage1BO[i]
    
    def stage_label(i):
        if wStage4[i]: return "S4"
        if wStage1BO[i]: return "S1→2"
        if wStage2[i]: return "S2"
        if wStage3[i]: return "S3"
        if wStage1[i]: return "S1"
        return "Trans"
    
    # isAboveTheLine / isBelowTheLine
    is_atl = np.zeros(n, dtype=bool)
    for i in range(n):
        if all(not np.isnan(x[i]) for x in [ma50, ma150, ma200]):
            is_atl[i] = C[i] > ma150[i] and C[i] > ma200[i] and ma50[i] > ma150[i] and ma50[i] > ma200[i]
    is_btl = ~is_atl
    
    # Darvas Box (anti-repaint: [1] offset)
    darvas_high = np.full(n, np.nan)
    darvas_low = np.full(n, np.nan)
    darvas_width = np.full(n, np.nan)
    valid_darvas = np.zeros(n, dtype=bool)
    
    for i in range(DARVAS_LEN + 1, n):
        dh = np.max(H[i - DARVAS_LEN:i])
        dl = np.min(L[i - DARVAS_LEN:i])
        darvas_high[i] = dh
        darvas_low[i] = dl
        if dl > 0:
            w = (dh - dl) / dl * 100
            darvas_width[i] = w
            valid_darvas[i] = DARVAS_MIN_WIDTH <= w <= DARVAS_MAX_WIDTH
    
    # Darvas Breakout with var anti-repaint (matching Pine Script exactly)
    darvas_breakout = np.zeros(n, dtype=bool)
    darvas_bo_condition = np.zeros(n, dtype=bool)
    darvas_bo_triggered = False
    darvas_bo_bar = -1
    
    for i in range(DARVAS_LEN + 2, n):
        if np.isnan(darvas_high[i]) or np.isnan(darvas_high[i-1]):
            continue
        cond = C[i] > darvas_high[i] and C[i-1] <= darvas_high[i-1]
        darvas_bo_condition[i] = cond
        prev_cond = darvas_bo_condition[i-1] if i > 0 else False
        # Edge detection (var mechanism)
        if cond and not prev_cond:
            darvas_bo_triggered = True
            darvas_bo_bar = i
        # Reset
        if C[i] < darvas_high[i] * 0.95:
            darvas_bo_triggered = False
            darvas_bo_bar = -1
        darvas_breakout[i] = (darvas_bo_bar == i)
    
    darvas_vol_confirm = np.zeros(n, dtype=bool)
    for i in range(n):
        if not np.isnan(vol_ma[i]) and vol_ma[i] > 0:
            darvas_vol_confirm[i] = V[i] > vol_ma[i] * VOL_CONFIRM_MULT
    
    # EMA conditions
    ema_above = np.zeros(n, dtype=bool)
    ema_cross_up = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if not np.isnan(_ema12[i]) and not np.isnan(_ema36[i]):
            ema_above[i] = _ema12[i] > _ema36[i]
            if not np.isnan(_ema12[i-1]) and not np.isnan(_ema36[i-1]):
                ema_cross_up[i] = _ema12[i] > _ema36[i] and _ema12[i-1] <= _ema36[i-1]
    
    # Weekly RSI oversold tracking
    weekly_oversold = np.zeros(n, dtype=bool)
    was_os = np.zeros(n, dtype=bool)
    bars_since_os = np.full(n, np.nan)
    last_os = -999
    for i in range(n):
        if not np.isnan(rsi_weekly[i]):
            weekly_oversold[i] = rsi_weekly[i] < RSI_OVERSOLD
        if weekly_oversold[i]:
            last_os = i
        if last_os >= 0:
            bars_since_os[i] = i - last_os
            was_os[i] = (i - last_os) <= RSI_LOOKBACK
    
    # Stop & R:R
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
    
    # Market Stage (use VNINDEX as proxy - simplified: just check stock's own stage)
    market_ok = ~wStage4  # Simplified: not Stage 4
    
    # BTL Exit Signals (for var reset)
    btl_stop_hit = np.zeros(n, dtype=bool)
    btl_enter_s4 = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if not np.isnan(darvas_low[i]):
            btl_stop_hit[i] = C[i] < darvas_low[i] * 0.98
        if not np.isnan(ma150[i]) and not np.isnan(ma150[i-1]):
            btl_enter_s4[i] = C[i] < ma150[i] and C[i-1] >= ma150[i-1]
    
    # --- BTL BUY with var anti-repaint (matching Pine) ---
    btl_darvas_ok = valid_darvas & darvas_breakout & darvas_vol_confirm
    btl_rsi_ok = was_os
    btl_ema_ok = ema_above
    btl_buy_condition = is_btl & market_ok & btl_darvas_ok & btl_rsi_ok & btl_ema_ok & stop_ok & rr_ok & ~wStage4
    
    # Var edge detection + reset for btlBuySignal
    btl_buy = np.zeros(n, dtype=bool)
    btl_triggered = False
    btl_bar = -1
    for i in range(1, n):
        cond = btl_buy_condition[i]
        prev = btl_buy_condition[i-1]
        if cond and not prev:
            btl_triggered = True
            btl_bar = i
        # Reset
        if btl_stop_hit[i] or btl_enter_s4[i] or (not np.isnan(darvas_low[i]) and C[i] < darvas_low[i] * 0.95):
            btl_triggered = False
            btl_bar = -1
        btl_buy[i] = (btl_bar == i)
    
    # Chase distance: how far above Darvas High at entry
    chase_pct = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(darvas_high[i]) and darvas_high[i] > 0:
            chase_pct[i] = (C[i] - darvas_high[i]) / darvas_high[i] * 100
    
    # --- Intraday drawdown proxy (using Low of next bars) ---
    
    # --- COLLECT SIGNALS & FORWARD RETURNS ---
    mask = (df['date'] >= a_start) & (df['date'] <= a_end)
    idx_range = df[mask].index.tolist()
    
    signals = []
    
    # Also track "relaxed" signals for parameter sensitivity
    for i in idx_range:
        # Current BTL conditions detail
        conds = {
            "is_btl": bool(is_btl[i]),
            "not_s4": bool(not wStage4[i]),
            "darvas_valid": bool(valid_darvas[i]),
            "darvas_bo": bool(darvas_breakout[i]),
            "darvas_vol": bool(darvas_vol_confirm[i]),
            "darvas_ok": bool(btl_darvas_ok[i]),
            "rsi_ok": bool(was_os[i]),
            "ema_ok": bool(ema_above[i]),
            "stop_ok": bool(stop_ok[i]),
            "rr_ok": bool(rr_ok[i]),
            "buy_signal": bool(btl_buy[i]),
        }
        
        # Forward returns
        fwd = {}
        for label, bars in FWD_HORIZONS.items():
            fi = i + bars
            if fi < n:
                fwd[label] = (C[fi] - C[i]) / C[i] * 100
                # Max drawdown from entry to T+bars
                if fi < n:
                    min_low = np.min(L[i+1:fi+1]) if fi > i else L[i]
                    fwd[f"{label}_dd"] = (min_low - C[i]) / C[i] * 100
            else:
                fwd[label] = np.nan
                fwd[f"{label}_dd"] = np.nan
        
        # Volume profile
        vol_ratio = V[i] / vol_ma[i] if not np.isnan(vol_ma[i]) and vol_ma[i] > 0 else np.nan
        vol_ratio_50 = V[i] / vol_ma50[i] if not np.isnan(vol_ma50[i]) and vol_ma50[i] > 0 else np.nan
        
        # Price momentum
        mom_5d = (C[i] - C[i-5]) / C[i-5] * 100 if i >= 5 else np.nan
        mom_10d = (C[i] - C[i-10]) / C[i-10] * 100 if i >= 10 else np.nan
        mom_20d = (C[i] - C[i-20]) / C[i-20] * 100 if i >= 20 else np.nan
        
        # Distance from MA150
        dist_ma150 = (C[i] - ma150[i]) / ma150[i] * 100 if not np.isnan(ma150[i]) and ma150[i] > 0 else np.nan
        
        # Forward price path for realistic SL/TP simulation (next 30 bars)
        max_fwd = 30
        fwd_highs = []
        fwd_lows = []
        fwd_closes = []
        for j in range(1, max_fwd + 1):
            fi = i + j
            if fi < n:
                fwd_highs.append(float(H[fi]))
                fwd_lows.append(float(L[fi]))
                fwd_closes.append(float(C[fi]))
            else:
                fwd_highs.append(np.nan)
                fwd_lows.append(np.nan)
                fwd_closes.append(np.nan)
        
        signals.append({
            "symbol": symbol,
            "date": df['date'].iloc[i],
            "open": O[i], "high": H[i], "low": L[i], "close": C[i],
            "volume": V[i],
            "stage": stage_label(i),
            "ma150": ma150[i] if not np.isnan(ma150[i]) else None,
            "darvas_high": darvas_high[i] if not np.isnan(darvas_high[i]) else None,
            "darvas_low": darvas_low[i] if not np.isnan(darvas_low[i]) else None,
            "darvas_width": darvas_width[i] if not np.isnan(darvas_width[i]) else None,
            "rsi_weekly": rsi_weekly[i] if not np.isnan(rsi_weekly[i]) else None,
            "rsi14": rsi14[i] if not np.isnan(rsi14[i]) else None,
            "ema12": _ema12[i] if not np.isnan(_ema12[i]) else None,
            "ema36": _ema36[i] if not np.isnan(_ema36[i]) else None,
            "bars_since_os": bars_since_os[i] if not np.isnan(bars_since_os[i]) else None,
            "stop_pct": stop_pct[i] if stop_pct[i] < 90 else None,
            "rr_ratio": rr_ratio[i] if rr_ratio[i] > 0 else None,
            "chase_pct": chase_pct[i] if not np.isnan(chase_pct[i]) else None,
            "vol_ratio_20d": vol_ratio if not np.isnan(vol_ratio) else None,
            "vol_ratio_50d": vol_ratio_50 if not np.isnan(vol_ratio_50) else None,
            "mom_5d": mom_5d, "mom_10d": mom_10d, "mom_20d": mom_20d,
            "dist_ma150": dist_ma150,
            "atr_pct": (atr14[i] / C[i] * 100) if not np.isnan(atr14[i]) else None,
            "fwd_highs": fwd_highs,
            "fwd_lows": fwd_lows,
            "fwd_closes": fwd_closes,
            **conds,
            **fwd,
        })
    
    return signals

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

print("=" * 130)
print("MULTI-STOCK BTL SIGNAL ANALYSIS & OPTIMIZATION")
print(f"Stocks: {len(STOCKS)} | Chase filter: ≤{CHASE_MAX_PCT}% above pivot")
print("=" * 130)

all_signals = []
for sym, a_start, a_end in STOCKS:
    result = analyze_stock(sym, a_start, a_end)
    if result:
        all_signals.extend(result)
    time.sleep(API_SLEEP)

df_all = pd.DataFrame(all_signals)
print(f"\nTotal data points: {len(df_all)} across {df_all['symbol'].nunique()} stocks")

# ═══════════════════════════════════════════════════════════════
# PART 1: BTL BUY SIGNALS DETECTED
# ═══════════════════════════════════════════════════════════════
buy_df = df_all[df_all['buy_signal'] == True].copy()

print(f"\n{'='*130}")
print(f"PART 1: BTL BUY SIGNALS DETECTED ({len(buy_df)} signals)")
print(f"{'='*130}")

if len(buy_df) > 0:
    cols = ['symbol', 'date', 'close', 'stage', 'darvas_high', 'darvas_width', 
            'chase_pct', 'stop_pct', 'rr_ratio', 'vol_ratio_20d', 'rsi_weekly',
            'T+2', 'T+7', 'T+14', 'T+30', 'T+2_dd']
    show = buy_df[[c for c in cols if c in buy_df.columns]].copy()
    for c in ['close', 'darvas_high']:
        if c in show.columns:
            show[c] = show[c].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "n/a")
    for c in ['chase_pct', 'stop_pct', 'darvas_width', 'T+2', 'T+7', 'T+14', 'T+30', 'T+2_dd']:
        if c in show.columns:
            show[c] = show[c].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "n/a")
    for c in ['rr_ratio', 'vol_ratio_20d', 'rsi_weekly']:
        if c in show.columns:
            show[c] = show[c].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "n/a")
    print(show.to_string(index=False))
    
    # Win rates
    for h in FWD_HORIZONS:
        valid = buy_df[h].dropna()
        if len(valid) > 0:
            wins = (valid > 0).sum()
            avg = valid.mean()
            med = valid.median()
            worst = valid.min()
            best = valid.max()
            print(f"  {h}: Win {wins}/{len(valid)} ({wins/len(valid)*100:.0f}%) | "
                  f"Avg {avg:+.2f}% | Med {med:+.2f}% | Best {best:+.2f}% | Worst {worst:+.2f}%")
else:
    print("  No BTL buy signals detected with current parameters!")

# ═══════════════════════════════════════════════════════════════
# PART 2: CHASE FILTER ANALYSIS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print(f"PART 2: CHASE FILTER ANALYSIS (max {CHASE_MAX_PCT}% above pivot)")
print(f"{'='*130}")

if len(buy_df) > 0:
    no_chase = buy_df[buy_df['chase_pct'].notna() & (buy_df['chase_pct'] <= CHASE_MAX_PCT)]
    chased = buy_df[buy_df['chase_pct'].notna() & (buy_df['chase_pct'] > CHASE_MAX_PCT)]
    
    print(f"\n  Signals ≤{CHASE_MAX_PCT}% above pivot: {len(no_chase)}")
    if len(no_chase) > 0:
        for h in FWD_HORIZONS:
            v = no_chase[h].dropna()
            if len(v) > 0:
                print(f"    {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")
    
    print(f"\n  Signals >{CHASE_MAX_PCT}% above pivot (CHASED): {len(chased)}")
    if len(chased) > 0:
        for h in FWD_HORIZONS:
            v = chased[h].dropna()
            if len(v) > 0:
                print(f"    {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 3: CONDITION BREAKDOWN - WHY SIGNALS MISSED
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 3: PER-STOCK CONDITION BREAKDOWN (% of analysis days TRUE)")
print(f"{'='*130}")

cond_cols = ['is_btl', 'not_s4', 'darvas_valid', 'darvas_bo', 'darvas_vol', 
             'darvas_ok', 'rsi_ok', 'ema_ok', 'stop_ok', 'rr_ok', 'buy_signal']

for sym in df_all['symbol'].unique():
    sdf = df_all[df_all['symbol'] == sym]
    total = len(sdf)
    print(f"\n  {sym} ({total} days):")
    for c in cond_cols:
        cnt = sdf[c].sum()
        print(f"    {c:<20}: {cnt:>3}/{total} ({cnt/total*100:>5.1f}%)")

# ═══════════════════════════════════════════════════════════════
# PART 4: RELAXED SIGNAL SCENARIOS (expanding conditions)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 4: RELAXED/ALTERNATIVE SIGNAL SCENARIOS")
print(f"{'='*130}")

# Helper: find "near-miss" signals where only 1-2 conditions fail
def near_miss_analysis(df):
    """Find days where most BTL conditions are met but signal doesn't fire."""
    results = []
    for _, row in df.iterrows():
        if row['buy_signal']:
            continue
        fails = []
        if not row['is_btl']: fails.append("ATL(not BTL)")
        if not row['not_s4']: fails.append("Stage4")
        if not row['darvas_valid']: fails.append("Box invalid")
        if not row['darvas_bo']: fails.append("No breakout")
        if not row['darvas_vol']: fails.append("Vol low")
        if not row['rsi_ok']: fails.append("RSI not OS")
        if not row['ema_ok']: fails.append("EMA below")
        if not row['stop_ok']: fails.append("Stop>10%")
        if not row['rr_ok']: fails.append("R:R<2")
        
        n_pass = len(cond_cols) - 1 - len(fails)  # -1 for buy_signal itself
        if n_pass >= 7:  # At least 7/9 conditions met
            results.append({
                "symbol": row['symbol'], "date": row['date'],
                "close": row['close'], "stage": row['stage'],
                "pass": n_pass, "fails": ", ".join(fails),
                "T+2": row.get('T+2', np.nan), "T+7": row.get('T+7', np.nan),
                "T+14": row.get('T+14', np.nan),
                "chase_pct": row.get('chase_pct', np.nan),
            })
    return pd.DataFrame(results)

near_miss = near_miss_analysis(df_all)
if len(near_miss) > 0:
    print(f"\n  Near-miss signals (≥7/9 conditions met, {len(near_miss)} found):")
    print(f"  {'Symbol':>6} {'Date':>12} {'Close':>8} {'Stage':>6} {'Pass':>4} {'Fails':<30} {'T+2':>6} {'T+7':>6} {'T+14':>7}")
    print(f"  {'-'*100}")
    for _, r in near_miss.sort_values(['symbol', 'date']).iterrows():
        t2 = f"{r['T+2']:+.1f}%" if pd.notna(r['T+2']) else "n/a"
        t7 = f"{r['T+7']:+.1f}%" if pd.notna(r['T+7']) else "n/a"
        t14 = f"{r['T+14']:+.1f}%" if pd.notna(r['T+14']) else "n/a"
        print(f"  {r['symbol']:>6} {str(r['date']):>12} {r['close']:>8.0f} {r['stage']:>6} {r['pass']:>4} {r['fails']:<30} {t2:>6} {t7:>6} {t14:>7}")

# ═══════════════════════════════════════════════════════════════
# PART 5: DARVAS BREAKOUT DAYS - ALL (even without full signal)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 5: ALL DARVAS BREAKOUT DAYS (regardless of other conditions)")
print(f"{'='*130}")

bo_df = df_all[df_all['darvas_bo'] == True].copy()
if len(bo_df) > 0:
    print(f"\n  Total Darvas breakouts: {len(bo_df)}")
    print(f"\n  {'Sym':>5} {'Date':>12} {'Close':>8} {'DrvH':>8} {'Chase%':>7} {'Vol':>5} "
          f"{'Stage':>6} {'RSI':>5} {'EMA':>4} {'StpOK':>5} "
          f"{'T+2':>7} {'T+7':>7} {'T+14':>7} {'T+2dd':>7} {'Full':>4}")
    print(f"  {'-'*115}")
    for _, r in bo_df.sort_values(['symbol', 'date']).iterrows():
        chase = f"{r['chase_pct']:+.1f}" if pd.notna(r['chase_pct']) else "n/a"
        vol = f"{r['vol_ratio_20d']:.1f}" if pd.notna(r['vol_ratio_20d']) else "n/a"
        rsiw = f"{r['rsi_weekly']:.0f}" if pd.notna(r['rsi_weekly']) else "n/a"
        ea = "✓" if r['ema_ok'] else "✗"
        sok = "✓" if r['stop_ok'] else "✗"
        t2 = f"{r['T+2']:+.1f}%" if pd.notna(r['T+2']) else "n/a"
        t7 = f"{r['T+7']:+.1f}%" if pd.notna(r['T+7']) else "n/a"
        t14 = f"{r['T+14']:+.1f}%" if pd.notna(r['T+14']) else "n/a"
        t2dd = f"{r['T+2_dd']:+.1f}%" if pd.notna(r['T+2_dd']) else "n/a"
        full = "★" if r['buy_signal'] else " "
        dh = f"{r['darvas_high']:.0f}" if pd.notna(r['darvas_high']) else "n/a"
        print(f"  {r['symbol']:>5} {str(r['date']):>12} {r['close']:>8.0f} {dh:>8} {chase:>7} {vol:>5} "
              f"{r['stage']:>6} {rsiw:>5} {ea:>4} {sok:>5} "
              f"{t2:>7} {t7:>7} {t14:>7} {t2dd:>7} {full:>4}")
    
    # Breakout quality stats
    print(f"\n  Breakout T+2 statistics:")
    valid_t2 = bo_df['T+2'].dropna()
    if len(valid_t2) > 0:
        print(f"    All breakouts: Win {(valid_t2>0).sum()}/{len(valid_t2)} ({(valid_t2>0).sum()/len(valid_t2)*100:.0f}%) | Avg {valid_t2.mean():+.2f}%")
    
    # With vol confirm
    bo_vol = bo_df[bo_df['darvas_vol'] == True]
    if len(bo_vol) > 0:
        v = bo_vol['T+2'].dropna()
        if len(v) > 0:
            print(f"    + Vol confirm:  Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")
    
    # With vol + EMA
    bo_ve = bo_df[(bo_df['darvas_vol'] == True) & (bo_df['ema_ok'] == True)]
    if len(bo_ve) > 0:
        v = bo_ve['T+2'].dropna()
        if len(v) > 0:
            print(f"    + Vol + EMA:    Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")
    
    # With vol + EMA + RSI
    bo_ver = bo_df[(bo_df['darvas_vol'] == True) & (bo_df['ema_ok'] == True) & (bo_df['rsi_ok'] == True)]
    if len(bo_ver) > 0:
        v = bo_ver['T+2'].dropna()
        if len(v) > 0:
            print(f"    + Vol+EMA+RSI:  Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")
    
    # Chase filter
    bo_nc = bo_df[(bo_df['chase_pct'].notna()) & (bo_df['chase_pct'] <= CHASE_MAX_PCT)]
    if len(bo_nc) > 0:
        v = bo_nc['T+2'].dropna()
        if len(v) > 0:
            print(f"    No chase ≤{CHASE_MAX_PCT}%: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 6: PARAMETER SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 6: PARAMETER SENSITIVITY (how T+2 win rate changes with thresholds)")
print(f"{'='*130}")

# 6a. Darvas Max Width sensitivity
print("\n  6a. Darvas Max Width threshold:")
for max_w in [10, 12, 15, 18, 20, 25]:
    subset = df_all[(df_all['darvas_bo'] == True) & (df_all['darvas_vol'] == True) & 
                     (df_all['darvas_width'].notna()) & (df_all['darvas_width'] <= max_w) &
                     (df_all['darvas_width'] >= DARVAS_MIN_WIDTH)]
    v = subset['T+2'].dropna()
    if len(v) > 0:
        print(f"    Width ≤{max_w:>2}%: Signals {len(v):>3} | Win {(v>0).sum():>3} ({(v>0).sum()/len(v)*100:>5.1f}%) | Avg T+2 {v.mean():+.2f}%")
    else:
        print(f"    Width ≤{max_w:>2}%: Signals   0")

# 6b. Volume multiplier sensitivity
print("\n  6b. Volume confirmation multiplier:")
for mult in [1.0, 1.2, 1.5, 2.0, 2.5]:
    subset = df_all[(df_all['darvas_bo'] == True) & 
                     (df_all['vol_ratio_20d'].notna()) & (df_all['vol_ratio_20d'] >= mult)]
    v = subset['T+2'].dropna()
    if len(v) > 0:
        print(f"    Vol ≥{mult:.1f}x: Signals {len(v):>3} | Win {(v>0).sum():>3} ({(v>0).sum()/len(v)*100:>5.1f}%) | Avg T+2 {v.mean():+.2f}%")
    else:
        print(f"    Vol ≥{mult:.1f}x: Signals   0")

# 6c. Chase threshold sensitivity
print("\n  6c. Chase threshold (max % above pivot):")
for chase_th in [1, 2, 3, 5, 7, 10]:
    subset = df_all[(df_all['darvas_bo'] == True) & (df_all['darvas_vol'] == True) &
                     (df_all['chase_pct'].notna()) & (df_all['chase_pct'] <= chase_th)]
    v = subset['T+2'].dropna()
    if len(v) > 0:
        print(f"    Chase ≤{chase_th:>2}%: Signals {len(v):>3} | Win {(v>0).sum():>3} ({(v>0).sum()/len(v)*100:>5.1f}%) | Avg T+2 {v.mean():+.2f}%")
    else:
        print(f"    Chase ≤{chase_th:>2}%: Signals   0")

# 6d. Stop % sensitivity
print("\n  6d. Max Stop % threshold:")
for max_stp in [5, 7, 8, 10, 12, 15]:
    subset = df_all[(df_all['darvas_bo'] == True) & (df_all['darvas_vol'] == True) &
                     (df_all['stop_pct'].notna()) & (df_all['stop_pct'] <= max_stp)]
    v = subset['T+2'].dropna()
    if len(v) > 0:
        print(f"    Stop ≤{max_stp:>2}%: Signals {len(v):>3} | Win {(v>0).sum():>3} ({(v>0).sum()/len(v)*100:>5.1f}%) | Avg T+2 {v.mean():+.2f}%")
    else:
        print(f"    Stop ≤{max_stp:>2}%: Signals   0")

# 6e. RSI oversold lookback
print("\n  6e. RSI Oversold Lookback (bars):")
for lk in [50, 75, 100, 150, 200]:
    subset = df_all[(df_all['darvas_bo'] == True) & (df_all['darvas_vol'] == True) &
                     (df_all['bars_since_os'].notna()) & (df_all['bars_since_os'] <= lk)]
    v = subset['T+2'].dropna()
    if len(v) > 0:
        print(f"    Lookback ≤{lk:>3}: Signals {len(v):>3} | Win {(v>0).sum():>3} ({(v>0).sum()/len(v)*100:>5.1f}%) | Avg T+2 {v.mean():+.2f}%")
    else:
        print(f"    Lookback ≤{lk:>3}: Signals   0")

# ═══════════════════════════════════════════════════════════════
# PART 7: MOMENTUM & CONTEXT AT ENTRY
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 7: ENTRY CONTEXT ANALYSIS (momentum, distance, volume patterns)")
print(f"{'='*130}")

bo_signals = df_all[df_all['darvas_bo'] == True].copy()
if len(bo_signals) > 0:
    # Correlation of features with T+2 return
    print("\n  7a. Feature correlation with T+2 return:")
    feat_cols = ['chase_pct', 'stop_pct', 'vol_ratio_20d', 'vol_ratio_50d', 
                 'mom_5d', 'mom_10d', 'mom_20d', 'dist_ma150', 'darvas_width',
                 'rsi_weekly', 'rsi14', 'atr_pct', 'rr_ratio']
    for fc in feat_cols:
        valid = bo_signals[[fc, 'T+2']].dropna()
        if len(valid) >= 3:
            corr = valid[fc].corr(valid['T+2'])
            print(f"    {fc:<18}: r = {corr:+.3f} (n={len(valid)})")
    
    # 7b. Stage at entry vs T+2
    print("\n  7b. Stage at breakout vs T+2:")
    for stg in bo_signals['stage'].unique():
        sub = bo_signals[bo_signals['stage'] == stg]['T+2'].dropna()
        if len(sub) > 0:
            print(f"    {stg:<8}: n={len(sub):>3} | Win {(sub>0).sum()}/{len(sub)} ({(sub>0).sum()/len(sub)*100:.0f}%) | Avg {sub.mean():+.2f}%")
    
    # 7c. 5-day momentum buckets
    print("\n  7c. 5-day momentum at entry vs T+2:")
    mom_bins = [(-99, -5), (-5, 0), (0, 3), (3, 7), (7, 15), (15, 99)]
    for lo, hi in mom_bins:
        sub = bo_signals[(bo_signals['mom_5d'] >= lo) & (bo_signals['mom_5d'] < hi)]['T+2'].dropna()
        if len(sub) > 0:
            print(f"    Mom5d [{lo:>3},{hi:>3}): n={len(sub):>3} | Win {(sub>0).sum()}/{len(sub)} ({(sub>0).sum()/len(sub)*100:.0f}%) | Avg {sub.mean():+.2f}%")
    
    # 7d. Daily RSI14 at entry
    print("\n  7d. Daily RSI(14) at entry vs T+2:")
    rsi_bins = [(0, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 100)]
    for lo, hi in rsi_bins:
        sub = bo_signals[(bo_signals['rsi14'] >= lo) & (bo_signals['rsi14'] < hi)]['T+2'].dropna()
        if len(sub) > 0:
            print(f"    RSI14 [{lo:>3},{hi:>3}): n={len(sub):>3} | Win {(sub>0).sum()}/{len(sub)} ({(sub>0).sum()/len(sub)*100:.0f}%) | Avg {sub.mean():+.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 8: T+2 DRAWDOWN ANALYSIS (max pain during holding)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 8: T+2 DRAWDOWN ANALYSIS (max intraday pain from entry)")
print(f"{'='*130}")

if len(bo_signals) > 0 and 'T+2_dd' in bo_signals.columns:
    dd = bo_signals['T+2_dd'].dropna()
    if len(dd) > 0:
        print(f"\n  All breakouts T+2 max drawdown:")
        print(f"    Mean: {dd.mean():.2f}% | Median: {dd.median():.2f}% | Worst: {dd.min():.2f}%")
        print(f"    % with dd > -3%: {(dd < -3).sum()}/{len(dd)} ({(dd < -3).sum()/len(dd)*100:.0f}%)")
        print(f"    % with dd > -5%: {(dd < -5).sum()}/{len(dd)} ({(dd < -5).sum()/len(dd)*100:.0f}%)")
    
    # With chase filter
    nc = bo_signals[(bo_signals['chase_pct'].notna()) & (bo_signals['chase_pct'] <= CHASE_MAX_PCT)]
    if len(nc) > 0:
        dd_nc = nc['T+2_dd'].dropna()
        if len(dd_nc) > 0:
            print(f"\n  No-chase (≤{CHASE_MAX_PCT}%) breakouts T+2 max drawdown:")
            print(f"    Mean: {dd_nc.mean():.2f}% | Median: {dd_nc.median():.2f}% | Worst: {dd_nc.min():.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 9: OPTIMAL CONDITION COMBINATION (maximize T+2 win rate)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 9: OPTIMAL CONDITION COMBINATIONS (finding T+2 ≥ 0% recipe)")
print(f"{'='*130}")

# Test various condition combinations
combos = [
    ("Darvas BO only", lambda r: r['darvas_bo']),
    ("Darvas BO + Vol", lambda r: r['darvas_bo'] and r['darvas_vol']),
    ("Darvas BO + Vol + EMA", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok']),
    ("Darvas BO + Vol + RSI", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['rsi_ok']),
    ("Darvas BO + Vol + EMA + RSI", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and r['rsi_ok']),
    ("Full BTL (current)", lambda r: r['buy_signal']),
    ("Full BTL + Chase≤3%", lambda r: r['buy_signal'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 3),
    ("Full BTL + Chase≤2%", lambda r: r['buy_signal'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 2),
    ("Darvas BO+Vol+EMA + Chase≤3%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 3),
    ("Darvas BO+Vol+EMA + Mom5d<7%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and pd.notna(r.get('mom_5d')) and r['mom_5d'] < 7),
    ("Darvas BO+Vol+EMA + RSI14<70", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and pd.notna(r.get('rsi14')) and r['rsi14'] < 70),
    ("Darvas BO+Vol+EMA+RSI + Stop≤8%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and r['rsi_ok'] and pd.notna(r.get('stop_pct')) and r['stop_pct'] <= 8),
    ("BO+Vol+EMA+RSI+Chase≤3%+Stp≤8%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and r['rsi_ok'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 3 and pd.notna(r.get('stop_pct')) and r['stop_pct'] <= 8),
]

print(f"\n  {'Combination':<45} {'Sigs':>5}", end="")
for h in ['T+2', 'T+7', 'T+14', 'T+30']:
    print(f"  {'Win':>12} {'Avg':>8}", end="")
print(f"  {'T+2Worst':>9}")
print(f"  {'-'*130}")

for name, cond_fn in combos:
    try:
        mask_series = df_all.apply(cond_fn, axis=1)
        subset = df_all[mask_series]
        n_sig = len(subset)
        if n_sig == 0:
            print(f"  {name:<45} {0:>5}")
            continue
        
        line = f"  {name:<45} {n_sig:>5}"
        for h in ['T+2', 'T+7', 'T+14', 'T+30']:
            hv = subset[h].dropna()
            if len(hv) > 0:
                w_str = f"{(hv>0).sum()}/{len(hv)}({(hv>0).sum()/len(hv)*100:.0f}%)"
                a_str = f"{hv.mean():+.1f}%"
            else:
                w_str = "n/a"
                a_str = "n/a"
            line += f"  {w_str:>12} {a_str:>8}"
        t2v = subset['T+2'].dropna()
        t2w = f"{t2v.min():+.1f}%" if len(t2v) > 0 else "n/a"
        line += f"  {t2w:>9}"
        print(line)
    except Exception as e:
        print(f"  {name:<45} ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# PART 10: PER-STOCK PERFORMANCE SUMMARY
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 10: PER-STOCK PRICE PERFORMANCE IN ANALYSIS PERIOD")
print(f"{'='*130}")

print(f"\n  {'Symbol':>6} {'Start':>12} {'End':>12} {'Period':>8} {'Open':>8} {'Close':>8} {'High':>8} {'Low':>8} {'Return':>8} {'MaxGain':>8} {'MaxDD':>8} {'Signals':>7}")
print(f"  {'-'*115}")

for sym in df_all['symbol'].unique():
    sdf = df_all[df_all['symbol'] == sym].sort_values('date')
    if len(sdf) == 0: continue
    start_p = sdf.iloc[0]['close']
    end_p = sdf.iloc[-1]['close']
    hi_p = sdf['high'].max()
    lo_p = sdf['low'].min()
    ret = (end_p - start_p) / start_p * 100
    max_gain = (hi_p - start_p) / start_p * 100
    max_dd = (lo_p - start_p) / start_p * 100
    n_sig = sdf['buy_signal'].sum()
    n_days = len(sdf)
    
    print(f"  {sym:>6} {str(sdf.iloc[0]['date']):>12} {str(sdf.iloc[-1]['date']):>12} {n_days:>6}d "
          f"{start_p:>8.0f} {end_p:>8.0f} {hi_p:>8.0f} {lo_p:>8.0f} "
          f"{ret:>+7.1f}% {max_gain:>+7.1f}% {max_dd:>+7.1f}% {n_sig:>7}")

# ═══════════════════════════════════════════════════════════════
# PART 12: REALISTIC TRADE SIMULATION (SL/TP path tracking)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 12: REALISTIC TRADE SIMULATION - SL HIT / TP HIT / HOLD TO HORIZON")
print("  Entry = Close on signal day | SL = -10% from entry | TP = +20% from entry")
print("  Track bar-by-bar: does Low hit SL first, or High hit TP first, or hold to horizon?")
print(f"{'='*130}")

def simulate_trade(row, sl_pct=-10.0, tp_pct=20.0, horizons=[7, 14, 30]):
    """
    Simulate a trade from entry (close) with SL/TP.
    Returns dict with outcome for each horizon.
    - For each horizon T+N: track if SL or TP is hit before day N.
    - If SL hit first → return = sl_pct
    - If TP hit first → return = tp_pct
    - If neither hit → return = close-to-close at T+N
    """
    entry = row['close']
    sl_price = entry * (1 + sl_pct / 100.0)
    tp_price = entry * (1 + tp_pct / 100.0)
    
    fwd_h = row.get('fwd_highs', [])
    fwd_l = row.get('fwd_lows', [])
    fwd_c = row.get('fwd_closes', [])
    
    if not fwd_h or len(fwd_h) == 0:
        return {}
    
    results = {}
    for hz in horizons:
        sl_day = None
        tp_day = None
        max_dd = 0.0
        max_gain = 0.0
        
        for d in range(min(hz, len(fwd_l))):
            lo = fwd_l[d]
            hi = fwd_h[d]
            if np.isnan(lo) or np.isnan(hi):
                break
            
            dd_pct = (lo - entry) / entry * 100
            gain_pct = (hi - entry) / entry * 100
            if dd_pct < max_dd:
                max_dd = dd_pct
            if gain_pct > max_gain:
                max_gain = gain_pct
            
            if sl_day is None and lo <= sl_price:
                sl_day = d + 1  # 1-indexed day
            if tp_day is None and hi >= tp_price:
                tp_day = d + 1
        
        # Determine outcome
        if sl_day is not None and tp_day is not None:
            # Both hit - which first?
            if sl_day <= tp_day:
                outcome = "SL"
                ret = sl_pct
                exit_day = sl_day
            else:
                outcome = "TP"
                ret = tp_pct
                exit_day = tp_day
        elif sl_day is not None:
            outcome = "SL"
            ret = sl_pct
            exit_day = sl_day
        elif tp_day is not None:
            outcome = "TP"
            ret = tp_pct
            exit_day = tp_day
        else:
            # Hold to horizon
            idx = hz - 1
            if idx < len(fwd_c) and not np.isnan(fwd_c[idx]):
                ret = (fwd_c[idx] - entry) / entry * 100
                outcome = "HOLD"
                exit_day = hz
            else:
                ret = np.nan
                outcome = "N/A"
                exit_day = None
        
        results[f"T{hz}_outcome"] = outcome
        results[f"T{hz}_ret"] = ret
        results[f"T{hz}_exit_day"] = exit_day
        results[f"T{hz}_maxdd"] = max_dd
        results[f"T{hz}_maxgain"] = max_gain
    
    return results

# Run simulation on all Darvas breakouts
SL_PCT = -10.0
TP_PCT = 20.0
SIM_HORIZONS = [7, 14, 30]

bo_sim = df_all[df_all['darvas_bo'] == True].copy()

if len(bo_sim) > 0:
    sim_results = []
    for idx, row in bo_sim.iterrows():
        res = simulate_trade(row, sl_pct=SL_PCT, tp_pct=TP_PCT, horizons=SIM_HORIZONS)
        sim_results.append(res)
    sim_df = pd.DataFrame(sim_results, index=bo_sim.index)
    bo_sim = pd.concat([bo_sim, sim_df], axis=1)
    
    # --- 12a: Per-signal detail table ---
    print(f"\n  12a. ALL DARVAS BREAKOUT TRADES (SL={SL_PCT}% / TP={TP_PCT}%)")
    print(f"\n  {'Sym':>5} {'Date':>12} {'Entry':>6} {'SL@':>6} {'TP@':>6} {'Chase%':>7} | "
          f"{'T7Out':>5} {'T7Ret':>7} {'T7Day':>5} | "
          f"{'T14Out':>6} {'T14Ret':>7} {'T14Day':>6} | "
          f"{'T30Out':>6} {'T30Ret':>7} {'T30Day':>6} | {'MaxDD':>7} {'MaxGn':>7}")
    print(f"  {'-'*155}")
    
    for _, r in bo_sim.sort_values(['symbol', 'date']).iterrows():
        entry = r['close']
        sl_p = entry * (1 + SL_PCT / 100)
        tp_p = entry * (1 + TP_PCT / 100)
        chase = f"{r['chase_pct']:+.1f}" if pd.notna(r.get('chase_pct')) else "n/a"
        
        parts = [f"  {r['symbol']:>5} {str(r['date']):>12} {entry:>6.0f} {sl_p:>6.0f} {tp_p:>6.0f} {chase:>7}"]
        
        for hz in SIM_HORIZONS:
            out = r.get(f'T{hz}_outcome', 'N/A')
            ret = r.get(f'T{hz}_ret', np.nan)
            day = r.get(f'T{hz}_exit_day', None)
            ret_s = f"{ret:+.1f}%" if pd.notna(ret) else "n/a"
            day_s = f"d{day}" if day is not None else "n/a"
            sep = "|"
            parts.append(f" {sep} {out:>5} {ret_s:>7} {day_s:>5}")
        
        # Max DD and max gain across full 30-day path
        mdd = r.get('T30_maxdd', np.nan)
        mgn = r.get('T30_maxgain', np.nan)
        mdd_s = f"{mdd:+.1f}%" if pd.notna(mdd) else "n/a"
        mgn_s = f"{mgn:+.1f}%" if pd.notna(mgn) else "n/a"
        parts.append(f" | {mdd_s:>7} {mgn_s:>7}")
        
        print("".join(parts))
    
    # --- 12b: Outcome summary per horizon ---
    print(f"\n  12b. OUTCOME SUMMARY BY HORIZON (all Darvas breakouts, n={len(bo_sim)})")
    for hz in SIM_HORIZONS:
        out_col = f'T{hz}_outcome'
        ret_col = f'T{hz}_ret'
        if out_col not in bo_sim.columns:
            continue
        
        valid = bo_sim[bo_sim[out_col] != 'N/A']
        n_valid = len(valid)
        if n_valid == 0:
            continue
        
        n_sl = (valid[out_col] == 'SL').sum()
        n_tp = (valid[out_col] == 'TP').sum()
        n_hold = (valid[out_col] == 'HOLD').sum()
        
        hold_rets = valid[valid[out_col] == 'HOLD'][ret_col].dropna()
        hold_win = (hold_rets > 0).sum() if len(hold_rets) > 0 else 0
        
        all_rets = valid[ret_col].dropna()
        avg_ret = all_rets.mean() if len(all_rets) > 0 else np.nan
        
        print(f"\n    T+{hz} ({n_valid} trades):")
        print(f"      SL hit (-10%):  {n_sl:>3} ({n_sl/n_valid*100:>5.1f}%)")
        print(f"      TP hit (+20%):  {n_tp:>3} ({n_tp/n_valid*100:>5.1f}%)")
        print(f"      HOLD to T+{hz}:  {n_hold:>3} ({n_hold/n_valid*100:>5.1f}%) | of which win: {hold_win}/{len(hold_rets)}")
        print(f"      Avg return:     {avg_ret:+.2f}%")
        
        # Breakdown: SL avg day, TP avg day
        sl_days = valid[valid[out_col] == 'SL'][f'T{hz}_exit_day'].dropna()
        tp_days = valid[valid[out_col] == 'TP'][f'T{hz}_exit_day'].dropna()
        if len(sl_days) > 0:
            print(f"      SL avg hit day: d{sl_days.mean():.1f} | median d{sl_days.median():.0f}")
        if len(tp_days) > 0:
            print(f"      TP avg hit day: d{tp_days.mean():.1f} | median d{tp_days.median():.0f}")
    
    # --- 12c: Simulation with different SL levels ---
    print(f"\n  12c. SL SENSITIVITY (TP fixed at +20%, T+30 horizon)")
    print(f"    {'SL':>5} {'Trades':>6} {'SL Hit':>8} {'TP Hit':>8} {'Hold':>8} {'Avg Ret':>8} {'Win%':>6}")
    print(f"    {'-'*60}")
    
    for sl in [-5, -7, -8, -10, -12, -15]:
        sim_res_sl = []
        for idx2, row in bo_sim.iterrows():
            res = simulate_trade(row, sl_pct=sl, tp_pct=TP_PCT, horizons=[30])
            sim_res_sl.append(res)
        sl_df = pd.DataFrame(sim_res_sl)
        valid_sl = sl_df[sl_df['T30_outcome'] != 'N/A']
        if len(valid_sl) == 0:
            continue
        n_v = len(valid_sl)
        n_sl2 = (valid_sl['T30_outcome'] == 'SL').sum()
        n_tp2 = (valid_sl['T30_outcome'] == 'TP').sum()
        n_hd2 = (valid_sl['T30_outcome'] == 'HOLD').sum()
        avg_r = valid_sl['T30_ret'].dropna().mean()
        win_r = (valid_sl['T30_ret'].dropna() > 0).sum()
        total_r = len(valid_sl['T30_ret'].dropna())
        print(f"    {sl:>4}% {n_v:>6} {n_sl2:>3}({n_sl2/n_v*100:>4.0f}%) {n_tp2:>3}({n_tp2/n_v*100:>4.0f}%) "
              f"{n_hd2:>3}({n_hd2/n_v*100:>4.0f}%) {avg_r:>+7.2f}% {win_r}/{total_r}")
    
    # --- 12d: Simulation per combo (best combos from Part 9) ---
    print(f"\n  12d. COMBO TRADE SIMULATION (SL={SL_PCT}%, TP={TP_PCT}%, T+30 horizon)")
    sim_combos = [
        ("All Darvas BO", lambda r: r['darvas_bo']),
        ("BO + Vol + EMA", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok']),
        ("BO+Vol+EMA+Chase≤3%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 3),
        ("BO+Vol+EMA+RSI14<70", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and pd.notna(r.get('rsi14')) and r['rsi14'] < 70),
        ("BO+Vol+EMA+RSI+Stop≤8%", lambda r: r['darvas_bo'] and r['darvas_vol'] and r['ema_ok'] and r['rsi_ok'] and pd.notna(r.get('stop_pct')) and r['stop_pct'] <= 8),
        ("Full BTL (current)", lambda r: r['buy_signal']),
    ]
    
    print(f"\n    {'Combo':<35}", end="")
    for hz in SIM_HORIZONS:
        print(f"  T+{hz}: {'SL':>3} {'TP':>3} {'HOLD':>4} {'AvgR':>7}", end="")
    print()
    print(f"    {'-'*120}")
    
    for cname, cfn in sim_combos:
        try:
            cmask = df_all.apply(cfn, axis=1)
            csub = df_all[cmask].copy()
            if len(csub) == 0:
                print(f"    {cname:<35}  (no signals)")
                continue
            
            c_sim = []
            for idx3, crow in csub.iterrows():
                res = simulate_trade(crow, sl_pct=SL_PCT, tp_pct=TP_PCT, horizons=SIM_HORIZONS)
                c_sim.append(res)
            c_sim_df = pd.DataFrame(c_sim)
            
            line = f"    {cname:<35}"
            for hz in SIM_HORIZONS:
                oc = f'T{hz}_outcome'
                rc = f'T{hz}_ret'
                if oc not in c_sim_df.columns:
                    line += f"  T+{hz}:  -   -   -      -"
                    continue
                vv = c_sim_df[c_sim_df[oc] != 'N/A']
                if len(vv) == 0:
                    line += f"  T+{hz}:  -   -   -      -"
                    continue
                ns = (vv[oc] == 'SL').sum()
                nt = (vv[oc] == 'TP').sum()
                nh = (vv[oc] == 'HOLD').sum()
                ar = vv[rc].dropna().mean()
                line += f"  T+{hz}: {ns:>3} {nt:>3} {nh:>4} {ar:>+6.1f}%"
            print(line)
        except Exception as e:
            print(f"    {cname:<35}  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# PART 13: MULTI-HORIZON DRAWDOWN ANALYSIS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 13: DRAWDOWN ANALYSIS BY HORIZON (max intraday pain from entry)")
print(f"{'='*130}")

if len(bo_sim) > 0:
    for hz in SIM_HORIZONS:
        dd_col = f'T{hz}_maxdd'
        gn_col = f'T{hz}_maxgain'
        if dd_col not in bo_sim.columns:
            continue
        dd = bo_sim[dd_col].dropna()
        gn = bo_sim[gn_col].dropna()
        if len(dd) == 0:
            continue
        print(f"\n  T+{hz} (n={len(dd)}):")
        print(f"    Max Drawdown:  Mean {dd.mean():+.2f}% | Med {dd.median():+.2f}% | Worst {dd.min():+.2f}%")
        print(f"    Max Gain:      Mean {gn.mean():+.2f}% | Med {gn.median():+.2f}% | Best {gn.max():+.2f}%")
        print(f"    DD > -5%:  {(dd < -5).sum()}/{len(dd)} ({(dd < -5).sum()/len(dd)*100:.0f}%)")
        print(f"    DD > -10%: {(dd < -10).sum()}/{len(dd)} ({(dd < -10).sum()/len(dd)*100:.0f}%)")
        print(f"    Gain > +10%: {(gn > 10).sum()}/{len(gn)} ({(gn > 10).sum()/len(gn)*100:.0f}%)")
        print(f"    Gain > +20%: {(gn > 20).sum()}/{len(gn)} ({(gn > 20).sum()/len(gn)*100:.0f}%)")

# ═══════════════════════════════════════════════════════════════
# PART 14: FINAL RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 14: ANALYSIS CONCLUSIONS & RECOMMENDATIONS")
print(f"{'='*130}")

total_signals = len(buy_df)
total_bo = len(bo_signals) if len(bo_signals) > 0 else 0

print(f"""
  Dataset: {len(STOCKS)} stocks, {len(df_all)} total bar-days
  Full BTL signals (current logic): {total_signals}
  Darvas breakouts (any): {total_bo}
  
  KEY METRICS:""")

if len(buy_df) > 0:
    for h in ['T+2', 'T+7', 'T+14', 'T+30']:
        hv = buy_df[h].dropna()
        if len(hv) > 0:
            print(f"  - Full BTL {h}: Win {(hv>0).sum()}/{len(hv)} ({(hv>0).sum()/len(hv)*100:.0f}%) | Avg {hv.mean():+.2f}%")

if len(bo_signals) > 0:
    for h in ['T+2', 'T+7', 'T+14', 'T+30']:
        hv = bo_signals[h].dropna()
        if len(hv) > 0:
            print(f"  - All BO {h}: Win {(hv>0).sum()}/{len(hv)} ({(hv>0).sum()/len(hv)*100:.0f}%) | Avg {hv.mean():+.2f}%")

print(f"""
  TRADE SIMULATION (SL={SL_PCT}%, TP={TP_PCT}%):
  - See Part 12b for outcome breakdown per horizon
  - See Part 12c for SL sensitivity analysis
  - See Part 12d for combo simulation results
  
  OPTIMIZATION SUGGESTIONS:
  1. Chase filter: Do NOT buy if close > Darvas High + {CHASE_MAX_PCT}%
  2. Check Part 6 for optimal parameter thresholds
  3. Check Part 9 for best condition combinations across ALL horizons
  4. Part 12 shows realistic SL/TP path outcomes
  5. Feature correlations (Part 7a) indicate which factors matter most
""")

print(f"{'='*130}")
print("ANALYSIS COMPLETE")
print(f"{'='*130}")
