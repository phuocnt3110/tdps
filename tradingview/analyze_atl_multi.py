#!/usr/bin/env python3
"""
analyze_atl_multi.py - Multi-stock ATL/BTL Dual Mode Analysis v2
=====================================================================
Phân tích toàn diện ATL + BTL dual mode buy signals:
- 1 year data (10/03/2025 - 10/03/2026)
- ATL mode: Minervini SEPA for confirmed uptrends
- BTL mode: Weinstein-Darvas for recovery plays
- Gap zone analysis: breakouts missed by BOTH modes
- Big trend evaluation: stocks gaining 50%+
- SL/TP realistic trade simulation
"""
import sys, os, warnings, time, io
warnings.filterwarnings('ignore')

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
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atl_output_v2.txt")
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
ANALYSIS_START = "2025-03-10"
ANALYSIS_END   = "2026-03-10"

STOCKS = [
    "DPM", "DCM", "GSP", "GMD", "NAF", "EVF", "OIL", "POW", "BFC", "PAC",
    "PLX", "MSR", "MWG", "TD6", "PVT", "PVD", "BSR", "NT2", "PVS", "PVC",
    "BIG", "DGW", "HPG", "SZC", "CTD", "PSX", "BIC", "PVB", "VHC", "PNJ",
    "HHP", "DCL", "NDN", "BAF", "TTF", "FIT", "TCX", "G36", "HAG", "PHR",
    "CTG", "HDB", "STB", "MST",
]

# ATL Parameters (matching Pine Script)
BASE_LEN = 30
ATR_LEN = 14
VCP_SEG_LEN = 7
PIVOT_LOOK = 5
HTF_MIN_GAIN = 80.0
NEAR_HIGH_PCT = 25.0
BARS_52 = 252
VOL_SURGE_MIN = 150  # % of volMA20
MAX_STOP_PCT = 8.0   # Minervini stop

# Forward return horizons
FWD_HORIZONS = {"T+2": 2, "T+7": 7, "T+14": 14, "T+30": 30}

# Benchmark
BENCHMARK = "VNINDEX"

API_SLEEP = 1.2

# ═══════════════════════════════════════════════════════════════
# INDICATOR FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def sma(arr, period):
    result = np.full(len(arr), np.nan)
    for i in range(period - 1, len(arr)):
        result[i] = np.mean(arr[i - period + 1:i + 1])
    return result

def ema_calc(arr, period):
    result = np.full(len(arr), np.nan)
    k = 2.0 / (period + 1)
    for i in range(len(arr)):
        if not np.isnan(arr[i]):
            result[i] = arr[i]
            for j in range(i + 1, len(arr)):
                result[j] = arr[j] * k + result[j-1] * (1 - k)
            break
    return result

def calc_atr(H, L, C, period=14):
    n = len(C)
    tr = np.full(n, np.nan)
    for i in range(1, n):
        tr[i] = max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1]))
    atr = np.full(n, np.nan)
    # SMA seed then RMA
    start = period
    if start < n:
        atr[start] = np.nanmean(tr[1:start+1])
        for i in range(start+1, n):
            if not np.isnan(atr[i-1]) and not np.isnan(tr[i]):
                atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    return atr

# ═══════════════════════════════════════════════════════════════
# FETCH BENCHMARK
# ═══════════════════════════════════════════════════════════════
print("Fetching benchmark VNINDEX...", flush=True)
a_start_dt = datetime.strptime(ANALYSIS_START, "%Y-%m-%d").date()
data_start_bench = (a_start_dt - timedelta(days=600)).strftime("%Y-%m-%d")
data_end_bench = (datetime.strptime(ANALYSIS_END, "%Y-%m-%d").date() + timedelta(days=50)).strftime("%Y-%m-%d")

try:
    q_bench = Quote(source="vci", symbol=BENCHMARK, show_log=False)
    df_bench = q_bench.history(start=data_start_bench, end=data_end_bench, interval="1D")
    df_bench['date'] = pd.to_datetime(df_bench['time']).dt.date
    df_bench = df_bench.sort_values('date').reset_index(drop=True)
    bench_close_map = dict(zip(df_bench['date'], df_bench['close'].values))
    bench_ma50_arr = sma(df_bench['close'].values.astype(float), 50)
    bench_ma50_map = dict(zip(df_bench['date'], bench_ma50_arr))
    print(f"  VNINDEX: {len(df_bench)} bars")
except Exception as e:
    print(f"  ERROR fetching benchmark: {e}")
    bench_close_map = {}
    bench_ma50_map = {}

time.sleep(API_SLEEP)

# ═══════════════════════════════════════════════════════════════
# STOCK ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════

def analyze_stock_atl(symbol):
    a_start = datetime.strptime(ANALYSIS_START, "%Y-%m-%d").date()
    a_end   = datetime.strptime(ANALYSIS_END, "%Y-%m-%d").date()
    data_start = (a_start - timedelta(days=600)).strftime("%Y-%m-%d")
    data_end   = (a_end + timedelta(days=50)).strftime("%Y-%m-%d")

    print(f"\n  Fetching {symbol}...", end=" ", flush=True)
    try:
        q = Quote(source="vci", symbol=symbol, show_log=False)
        df = q.history(start=data_start, end=data_end, interval="1D")
    except Exception as e:
        print(f"ERROR: {e}")
        return None

    if df is None or df.empty:
        print("NO DATA"); return None

    df['date'] = pd.to_datetime(df['time']).dt.date
    df = df.sort_values('date').reset_index(drop=True)
    print(f"{len(df)} bars [{df['date'].iloc[0]} -> {df['date'].iloc[-1]}]")

    O = df['open'].values.astype(float)
    H = df['high'].values.astype(float)
    L = df['low'].values.astype(float)
    C = df['close'].values.astype(float)
    V = df['volume'].values.astype(float)
    n = len(df)

    if n < 260:
        print(f"    Skipping {symbol}: only {n} bars (need >=260)")
        return None

    # --- Moving Averages ---
    ma20  = sma(C, 20)
    ma50  = sma(C, 50)
    ma150 = sma(C, 150)
    ma200 = sma(C, 200)
    vol_ma20 = sma(V, 20)
    vol_ma50 = sma(V, 50)
    _ema10 = ema_calc(C, 10)
    _ema21 = ema_calc(C, 21)

    # --- Relative Strength vs VNINDEX ---
    rs_norm = np.full(n, np.nan)
    bench_arr = np.full(n, np.nan)
    for i in range(n):
        d = df['date'].iloc[i]
        if d in bench_close_map and bench_close_map[d] != 0:
            bench_arr[i] = bench_close_map[d]
    rs_raw = np.where(bench_arr > 0, C / bench_arr, np.nan)
    for i in range(n):
        lb = min(200, i + 1)
        if lb < 20: continue
        seg = rs_raw[max(0, i-lb+1):i+1]
        valid = seg[~np.isnan(seg)]
        if len(valid) < 10: continue
        rs_hi = np.max(valid)
        rs_lo = np.min(valid)
        rng = rs_hi - rs_lo
        if rng > 0 and not np.isnan(rs_raw[i]):
            rs_norm[i] = 100.0 * (rs_raw[i] - rs_lo) / rng

    rs_strong = np.array([not np.isnan(rs_norm[i]) and rs_norm[i] >= 80 for i in range(n)])
    rs_very_strong = np.array([not np.isnan(rs_norm[i]) and rs_norm[i] >= 90 for i in range(n)])
    rs_extreme = np.array([not np.isnan(rs_norm[i]) and rs_norm[i] >= 95 for i in range(n)])

    # --- 52-week metrics (anti-repaint: use [1]) ---
    hi52 = np.full(n, np.nan)
    lo52 = np.full(n, np.nan)
    for i in range(1, n):
        lb = min(BARS_52, i)
        hi52[i] = np.max(H[max(0,i-lb):i])  # exclude current bar
        lo52[i] = np.min(L[max(0,i-lb):i])
    dist_from_52h = np.where(hi52 > 0, (C - hi52) / hi52 * 100, np.nan)
    is_near_high = np.array([not np.isnan(dist_from_52h[i]) and dist_from_52h[i] >= -NEAR_HIGH_PCT for i in range(n)])
    above_low_30 = np.array([not np.isnan(lo52[i]) and C[i] >= lo52[i] * 1.3 for i in range(n)])

    # --- Trend Template (Minervini) ---
    cond_price_above = np.zeros(n, dtype=bool)
    cond_ma_stacked  = np.zeros(n, dtype=bool)
    cond_ma_slope    = np.zeros(n, dtype=bool)
    cond_rs_up       = np.zeros(n, dtype=bool)
    cond_vol_strong  = np.zeros(n, dtype=bool)

    for i in range(5, n):
        if any(np.isnan(x[i]) for x in [ma50, ma150, ma200]): continue
        cond_price_above[i] = C[i] > ma50[i] and C[i] > ma150[i] and C[i] > ma200[i]
        cond_ma_stacked[i]  = ma50[i] > ma150[i] and ma150[i] > ma200[i]
        if not np.isnan(ma50[i-5]) and not np.isnan(ma150[i-5]) and not np.isnan(ma200[i-5]):
            cond_ma_slope[i] = ma50[i] > ma50[i-5] and ma150[i] >= ma150[i-5] and ma200[i] >= ma200[i-5]
        if not np.isnan(rs_norm[i]) and not np.isnan(rs_norm[i-5]):
            cond_rs_up[i] = rs_norm[i] > rs_norm[i-5]
        if not np.isnan(vol_ma20[i]) and vol_ma20[i] > 0:
            cond_vol_strong[i] = V[i] > vol_ma20[i]

    trend_score = (cond_price_above.astype(int) * 2 + cond_ma_stacked.astype(int) * 2 +
                   cond_ma_slope.astype(int) * 2 + is_near_high.astype(int) * 2 +
                   cond_rs_up.astype(int) * 1 + cond_vol_strong.astype(int) * 1)

    is_stage2    = trend_score >= 8
    is_stage2_ok = (trend_score >= 5) & (trend_score < 8)

    # --- isAboveTheLine ---
    is_atl = np.zeros(n, dtype=bool)
    for i in range(n):
        if all(not np.isnan(x[i]) for x in [ma50, ma150, ma200]):
            is_atl[i] = C[i] > ma150[i] and C[i] > ma200[i] and ma50[i] > ma150[i] and ma50[i] > ma200[i]

    # --- ATR ---
    atr14 = calc_atr(H, L, C, ATR_LEN)
    atr_pct = np.where(C > 0, atr14 / C * 100, np.nan)

    # --- Base / Setup Detection ---
    base_high = np.full(n, np.nan)
    base_low  = np.full(n, np.nan)
    base_depth = np.full(n, np.nan)
    price_pos  = np.full(n, np.nan)
    pivot_dist = np.full(n, np.nan)
    prior_gain = np.full(n, np.nan)

    for i in range(BASE_LEN + 1, n):
        bh = np.max(H[i-BASE_LEN:i])  # exclude current bar [1]
        bl = np.min(L[i-BASE_LEN:i])
        base_high[i] = bh
        base_low[i]  = bl
        if bh > 0:
            base_depth[i] = (bh - bl) / bh * 100
            price_pos[i]  = (C[i] - bl) / (bh - bl) * 100 if bh != bl else 100
            pivot_dist[i] = (bh - C[i]) / bh * 100
        # Prior gain
        if i >= BASE_LEN * 2:
            prior_low = np.min(L[i-BASE_LEN*2:i-BASE_LEN])
            if prior_low > 0:
                prior_gain[i] = (bh - prior_low) / prior_low * 100

    # --- VCP T-Count ---
    atr_t1 = sma(atr_pct, VCP_SEG_LEN * 4)
    atr_t2 = sma(atr_pct, VCP_SEG_LEN * 3)
    atr_t3 = sma(atr_pct, VCP_SEG_LEN * 2)
    atr_t4 = sma(atr_pct, VCP_SEG_LEN)

    t_count = np.zeros(n, dtype=int)
    for i in range(n):
        if all(not np.isnan(x[i]) for x in [atr_t1, atr_t2, atr_t3, atr_t4]):
            t_count[i] = int(atr_t1[i] > atr_t2[i]) + int(atr_t2[i] > atr_t3[i]) + int(atr_t3[i] > atr_t4[i])
    has_vcp_char = t_count >= 2

    # --- Volume Analysis ---
    up_vol   = np.where(C > np.roll(C, 1), V, 0)
    down_vol = np.where(C < np.roll(C, 1), V, 0)
    up_vol[0] = 0; down_vol[0] = 0
    up_vol_ma10   = sma(up_vol, 10)
    down_vol_ma10 = sma(down_vol, 10)
    vol_healthy = np.array([up_vol_ma10[i] >= down_vol_ma10[i] if not np.isnan(up_vol_ma10[i]) else False for i in range(n)])
    vol_dry_up = np.array([not np.isnan(vol_ma20[i]) and not np.isnan(vol_ma50[i]) and vol_ma50[i] > 0 and vol_ma20[i] < vol_ma50[i] * 0.8 for i in range(n)])
    accum_ratio = np.where(down_vol_ma10 > 0, up_vol_ma10 / down_vol_ma10, 1.0)

    # --- Tightness ---
    range_pct = np.where(C > 0, (H - L) / C * 100, np.nan)
    range_ma5  = sma(range_pct, 5)
    range_ma20 = sma(range_pct, 20)
    tightness = np.where(range_ma20 > 0, range_ma5 / range_ma20, np.nan)

    higher_lows = np.zeros(n, dtype=bool)
    for i in range(PIVOT_LOOK * 2, n):
        hl1 = np.min(L[i-PIVOT_LOOK+1:i+1])
        hl2 = np.min(L[i-PIVOT_LOOK*2+1:i-PIVOT_LOOK+1])
        higher_lows[i] = hl1 >= hl2
    is_tight = np.array([not np.isnan(tightness[i]) and tightness[i] < 0.9 and higher_lows[i] for i in range(n)])

    # --- Pattern Detection ---
    pattern_name  = ["NO SETUP"] * n
    pattern_score = np.zeros(n, dtype=int)

    for i in range(BASE_LEN * 2, n):
        bd = base_depth[i] if not np.isnan(base_depth[i]) else 99
        pp = price_pos[i] if not np.isnan(price_pos[i]) else 0
        pg = prior_gain[i] if not np.isnan(prior_gain[i]) else 0
        tr_val = tightness[i] if not np.isnan(tightness[i]) else 99
        tc = t_count[i]
        vd = vol_dry_up[i]
        vh = vol_healthy[i]
        pd_val = pivot_dist[i] if not np.isnan(pivot_dist[i]) else 99
        tight = is_tight[i]
        vcp = has_vcp_char[i]

        # Priority order (matching Pine)
        is_pp = pd_val <= 3 and tr_val < 0.5 and vd and vcp
        is_htf = pg >= HTF_MIN_GAIN and 10 <= bd <= 25 and tr_val < 0.6 and pp >= 70
        is_vcp_pat = vcp and bd <= 35 and pp >= 70 and tight and vd
        is_cup = 15 <= bd <= 65 and pp >= 70 and tr_val < 0.85 and tc >= 1 and vd
        # Double bottom (simplified)
        if i >= BASE_LEN:
            half = BASE_LEN // 2
            low1 = np.min(L[i-half+1:i+1])
            low2 = np.min(L[i-BASE_LEN+1:i-half+1])
            has_w = abs(low1 - low2) / max(low1, 1) * 100 < 5
        else:
            has_w = False
        is_db = has_w and 15 <= bd <= 50 and pp >= 60 and vcp
        is_flat = bd <= 15 and pp >= 80 and vh
        # Ascending
        if i >= PIVOT_LOOK * 3:
            pl1 = np.min(L[i-PIVOT_LOOK+1:i+1])
            pl2 = np.min(L[i-PIVOT_LOOK*2+1:i-PIVOT_LOOK+1])
            pl3 = np.min(L[i-PIVOT_LOOK*3+1:i-PIVOT_LOOK*2+1])
            is_asc = pl1 > pl2 and pl2 > pl3 and bd <= 35 and pp >= 50
        else:
            is_asc = False

        # RS Bonus
        rs_bon = 10 if rs_very_strong[i] else (5 if rs_strong[i] else 0)

        if is_pp:
            pattern_name[i] = "POWER PLAY"; pattern_score[i] = 95 + rs_bon
        elif is_htf:
            pattern_name[i] = "HTF"; pattern_score[i] = 90 + rs_bon
        elif is_vcp_pat:
            pattern_name[i] = f"VCP({tc}T)"; pattern_score[i] = 85 + rs_bon
        elif is_cup:
            pattern_name[i] = "CUP"; pattern_score[i] = 80 + rs_bon
        elif is_db:
            pattern_name[i] = "DOUBLE BTM"; pattern_score[i] = 75 + rs_bon
        elif is_flat:
            pattern_name[i] = "FLAT BASE"; pattern_score[i] = 70 + rs_bon
        elif is_asc:
            pattern_name[i] = "ASCENDING"; pattern_score[i] = 72 + rs_bon
        elif vcp and pp >= 50:
            pattern_name[i] = "FORMING"; pattern_score[i] = 40 + rs_bon
        else:
            pattern_score[i] = 0 + rs_bon

    # --- Qualification ---
    tier12_qualified = is_stage2 & (np.array(pattern_score) >= 77)
    # Super stock
    super_stock = rs_very_strong & is_stage2_ok & cond_price_above & (cond_ma_stacked | rs_extreme)
    rs_based_qualified = super_stock & (np.array(pattern_score) >= 50)
    is_qualified = tier12_qualified | rs_based_qualified

    # --- Stop Loss (Minervini method, simplified: use base_low with 1% buffer) ---
    # Method 4 simplified: max(vcpTightStop, fixed7%)
    stop_level = np.full(n, np.nan)
    stop_pct   = np.full(n, 99.0)
    stop_ok    = np.zeros(n, dtype=bool)

    for i in range(VCP_SEG_LEN, n):
        if np.isnan(base_high[i]) or base_high[i] <= 0: continue
        vcp_tight = np.min(L[max(0,i-VCP_SEG_LEN+1):i+1]) * 0.99
        fixed_7   = base_high[i] * 0.93
        sl = max(vcp_tight, fixed_7)
        stop_level[i] = sl
        sp = (base_high[i] - sl) / base_high[i] * 100
        stop_pct[i] = sp
        stop_ok[i] = sp <= MAX_STOP_PCT

    # --- Market Bullish ---
    market_bullish = np.zeros(n, dtype=bool)
    for i in range(n):
        d = df['date'].iloc[i]
        bc = bench_close_map.get(d, np.nan)
        bm = bench_ma50_map.get(d, np.nan)
        if not np.isnan(bc) and not np.isnan(bm):
            market_bullish[i] = bc > bm

    # --- Volume Surge ---
    vol_surge_pct = np.where(vol_ma20 > 0, V / vol_ma20 * 100, 0)
    has_vol_surge = vol_surge_pct >= VOL_SURGE_MIN

    # --- ATL Breakout Detection (var anti-repaint) ---
    prior_pivot = base_high.copy()  # Already [1] offset

    regular_bo_cond = np.zeros(n, dtype=bool)
    gap_bo_cond     = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if np.isnan(prior_pivot[i]) or np.isnan(prior_pivot[i]): continue
        regular_bo_cond[i] = C[i] > prior_pivot[i] and C[i-1] <= prior_pivot[i]
        gap_pct_val = (O[i] - C[i-1]) / C[i-1] * 100 if C[i-1] > 0 else 0
        gap_bo_cond[i] = O[i] > prior_pivot[i] and C[i-1] <= prior_pivot[i] and gap_pct_val >= 2

    # Var anti-repaint for ATL breakout
    atl_bo_triggered = False
    atl_bo_bar = -1
    atl_bo_pivot = 0.0
    is_breakout = np.zeros(n, dtype=bool)

    for i in range(1, n):
        if np.isnan(prior_pivot[i]): continue
        any_bo = regular_bo_cond[i] or gap_bo_cond[i]
        is_new_higher_pivot = prior_pivot[i] > atl_bo_pivot * 1.005
        is_first = (not atl_bo_triggered) and any_bo
        is_new_pivot_bo = atl_bo_triggered and is_new_higher_pivot and any_bo

        if is_first or is_new_pivot_bo:
            atl_bo_triggered = True
            atl_bo_bar = i
            atl_bo_pivot = prior_pivot[i]

        # Reset
        if not np.isnan(prior_pivot[i]) and C[i] < prior_pivot[i] * 0.97:
            atl_bo_triggered = False
            atl_bo_bar = -1
            atl_bo_pivot = 0.0

        is_breakout[i] = (atl_bo_bar == i)

    # --- freshBreakout = isBreakout AND volSurge AND marketBullish AND stopOK ---
    fresh_breakout = is_breakout & has_vol_surge & market_bullish & stop_ok

    # --- ATL BUY SIGNAL = isATL AND isQualified AND freshBreakout AND rsStrong ---
    atl_buy = is_atl & is_qualified & fresh_breakout & rs_strong

    # --- Also detect "relaxed" breakout (without some conditions) for missed signal analysis ---
    # Breakout with volume only (no qualification)
    bo_with_vol = is_breakout & has_vol_surge

    # ═══════════════════════════════════════════════════════════════
    # BTL (Below The Line) BUY LOGIC - Weinstein-Darvas Method
    # ═══════════════════════════════════════════════════════════════
    is_btl = ~is_atl  # BTL = not ATL (no gap by definition)

    # --- Darvas Box Detection ---
    DARVAS_LEN = 20
    darvas_high = np.full(n, np.nan)
    darvas_low  = np.full(n, np.nan)
    for i in range(DARVAS_LEN + 1, n):
        darvas_high[i] = np.max(H[i-DARVAS_LEN:i])  # exclude current bar
        darvas_low[i]  = np.min(L[i-DARVAS_LEN:i])
    darvas_range = np.where(darvas_low > 0, (darvas_high - darvas_low) / darvas_low * 100, np.nan)
    valid_darvas = np.array([not np.isnan(darvas_range[i]) and 5 <= darvas_range[i] <= 50 for i in range(n)])

    # Darvas Breakout (var anti-repaint)
    darvas_bo_triggered = False
    darvas_bo_bar = -1
    darvas_breakout = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if np.isnan(darvas_high[i]): continue
        cond = C[i] > darvas_high[i] and C[i-1] <= darvas_high[i]
        if cond and not darvas_bo_triggered:
            darvas_bo_triggered = True
            darvas_bo_bar = i
        if C[i] < darvas_high[i] * 0.95:
            darvas_bo_triggered = False
            darvas_bo_bar = -1
        darvas_breakout[i] = (darvas_bo_bar == i)

    darvas_vol_confirm = darvas_breakout & (vol_surge_pct >= 130)

    # --- RSI Weekly Approximation (RSI 70-bar ≈ weekly RSI 14) ---
    def calc_rsi(arr, period=14):
        n2 = len(arr)
        rsi = np.full(n2, np.nan)
        delta = np.diff(arr, prepend=arr[0])
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = np.full(n2, np.nan)
        avg_loss = np.full(n2, np.nan)
        if period < n2:
            avg_gain[period] = np.mean(gain[1:period+1])
            avg_loss[period] = np.mean(loss[1:period+1])
            for j in range(period+1, n2):
                avg_gain[j] = (avg_gain[j-1] * (period-1) + gain[j]) / period
                avg_loss[j] = (avg_loss[j-1] * (period-1) + loss[j]) / period
            for j in range(period, n2):
                if avg_loss[j] == 0: rsi[j] = 100.0
                elif not np.isnan(avg_gain[j]) and not np.isnan(avg_loss[j]):
                    rsi[j] = 100.0 - 100.0 / (1.0 + avg_gain[j] / avg_loss[j])
        return rsi

    rsi_weekly = calc_rsi(C, 70)  # 70-bar ≈ 14-week RSI
    weekly_oversold = np.array([not np.isnan(rsi_weekly[i]) and rsi_weekly[i] < 30 for i in range(n)])
    # Was oversold recently (within 20 bars)
    was_oversold_recently = np.zeros(n, dtype=bool)
    for i in range(n):
        lb = min(20, i + 1)
        was_oversold_recently[i] = any(weekly_oversold[max(0,i-lb+1):i+1])

    # --- EMA12/EMA36 ---
    _ema12 = ema_calc(C, 12)
    _ema36 = ema_calc(C, 36)
    ema_above = np.array([not np.isnan(_ema12[i]) and not np.isnan(_ema36[i]) and _ema12[i] > _ema36[i] for i in range(n)])

    # --- Weinstein Stages ---
    ma30w = ma150.copy()  # 150-bar ≈ 30-week MA
    ma30w_slope = np.full(n, 0.0)
    for i in range(10, n):
        if not np.isnan(ma30w[i]) and not np.isnan(ma30w[i-10]):
            ma30w_slope[i] = ma30w[i] - ma30w[i-10]
    w_stage4 = np.array([not np.isnan(ma30w[i]) and C[i] < ma30w[i] and ma30w_slope[i] < 0 for i in range(n)])

    # Market OK for BTL (not market Stage 4)
    bench_ma150_arr = sma(df_bench['close'].values.astype(float), 150) if len(df_bench) > 0 else np.array([])
    bench_ma150_map = dict(zip(df_bench['date'], bench_ma150_arr)) if len(bench_ma150_arr) > 0 else {}
    market_ok_btl = np.zeros(n, dtype=bool)
    for i in range(n):
        d = df['date'].iloc[i]
        bc = bench_close_map.get(d, np.nan)
        bm150 = bench_ma150_map.get(d, np.nan)
        if not np.isnan(bc) and not np.isnan(bm150):
            bslope = 0
            # approximate slope
            market_ok_btl[i] = not (bc < bm150 and bslope < 0)  # simplified: just not below MA150
        else:
            market_ok_btl[i] = True

    # --- BTL Stop & R:R ---
    btl_stop_pct = np.full(n, 99.0)
    btl_stop_ok  = np.zeros(n, dtype=bool)
    btl_rr_ok    = np.zeros(n, dtype=bool)
    for i in range(n):
        if not np.isnan(darvas_low[i]) and C[i] > darvas_low[i]:
            sp = (C[i] - darvas_low[i]) / C[i] * 100
            btl_stop_pct[i] = sp
            btl_stop_ok[i] = sp <= 10.0  # BTL max 10%
            btl_rr_ok[i] = sp > 0 and (20.0 / sp) >= 2.0  # min 2:1 R:R

    # --- BTL BUY SIGNAL ---
    btl_darvas_ok = valid_darvas & darvas_breakout & darvas_vol_confirm
    btl_rsi_ok = was_oversold_recently
    btl_ema_ok = ema_above
    btl_buy_cond = is_btl & market_ok_btl & btl_stop_ok & btl_rr_ok & btl_darvas_ok & btl_rsi_ok & btl_ema_ok & ~w_stage4

    # Anti-repaint for BTL buy
    btl_buy_triggered = False
    btl_buy_bar_idx = -1
    btl_buy = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if btl_buy_cond[i] and not btl_buy_cond[i-1]:
            btl_buy_triggered = True
            btl_buy_bar_idx = i
        # Reset conditions
        if not np.isnan(darvas_low[i]) and C[i] < darvas_low[i] * 0.98:
            btl_buy_triggered = False
            btl_buy_bar_idx = -1
        if not np.isnan(ma30w[i]) and C[i] < ma30w[i] and (i > 0 and C[i-1] >= ma30w[i-1] if not np.isnan(ma30w[i-1]) else False):
            btl_buy_triggered = False
            btl_buy_bar_idx = -1
        btl_buy[i] = (btl_buy_bar_idx == i)

    # --- ANY BUY = ATL or BTL ---
    any_buy = atl_buy | btl_buy

    # --- GAP ZONE = breakout detected but neither ATL buy nor BTL buy fires ---
    gap_breakout = is_breakout & ~atl_buy & ~btl_buy  # breakouts in "gap"

    # --- COLLECT SIGNALS ---
    mask = (df['date'] >= a_start) & (df['date'] <= a_end)
    idx_range = df[mask].index.tolist()

    signals = []
    for i in idx_range:
        # Chase
        chase_pct_val = (C[i] - prior_pivot[i]) / prior_pivot[i] * 100 if not np.isnan(prior_pivot[i]) and prior_pivot[i] > 0 else np.nan

        # Forward returns & path
        fwd = {}
        fwd_highs, fwd_lows, fwd_closes = [], [], []
        for label, bars in FWD_HORIZONS.items():
            fi = i + bars
            if fi < n:
                fwd[label] = (C[fi] - C[i]) / C[i] * 100
                min_low = np.min(L[i+1:fi+1]) if fi > i else L[i]
                fwd[f"{label}_dd"] = (min_low - C[i]) / C[i] * 100
            else:
                fwd[label] = np.nan
                fwd[f"{label}_dd"] = np.nan
        for j in range(1, 31):
            fi = i + j
            if fi < n:
                fwd_highs.append(float(H[fi])); fwd_lows.append(float(L[fi])); fwd_closes.append(float(C[fi]))
            else:
                fwd_highs.append(np.nan); fwd_lows.append(np.nan); fwd_closes.append(np.nan)

        signals.append({
            "symbol": symbol, "date": df['date'].iloc[i],
            "open": O[i], "high": H[i], "low": L[i], "close": C[i], "volume": V[i],
            "ma50": ma50[i], "ma150": ma150[i], "ma200": ma200[i],
            "rs_norm": rs_norm[i] if not np.isnan(rs_norm[i]) else None,
            "trend_score": int(trend_score[i]),
            "is_stage2": bool(is_stage2[i]),
            "is_stage2_ok": bool(is_stage2_ok[i]),
            "is_atl": bool(is_atl[i]),
            "pattern": pattern_name[i],
            "pattern_score": int(pattern_score[i]),
            "t_count": int(t_count[i]),
            "base_depth": base_depth[i] if not np.isnan(base_depth[i]) else None,
            "price_pos": price_pos[i] if not np.isnan(price_pos[i]) else None,
            "pivot_dist": pivot_dist[i] if not np.isnan(pivot_dist[i]) else None,
            "prior_pivot": prior_pivot[i] if not np.isnan(prior_pivot[i]) else None,
            "stop_pct": stop_pct[i] if stop_pct[i] < 90 else None,
            "stop_ok": bool(stop_ok[i]),
            "vol_surge": vol_surge_pct[i] if not np.isnan(vol_surge_pct[i]) else None,
            "has_vol_surge": bool(has_vol_surge[i]),
            "market_bullish": bool(market_bullish[i]),
            "rs_strong": bool(rs_strong[i]),
            "rs_very_strong": bool(rs_very_strong[i]),
            "tier12_qualified": bool(tier12_qualified[i]),
            "rs_qualified": bool(rs_based_qualified[i]),
            "is_qualified": bool(is_qualified[i]),
            "is_breakout": bool(is_breakout[i]),
            "fresh_breakout": bool(fresh_breakout[i]),
            "atl_buy": bool(atl_buy[i]),
            "bo_with_vol": bool(bo_with_vol[i]),
            "chase_pct": chase_pct_val,
            "vol_dry_up": bool(vol_dry_up[i]),
            "vol_healthy": bool(vol_healthy[i]),
            "tightness": tightness[i] if not np.isnan(tightness[i]) else None,
            "is_tight": bool(is_tight[i]),
            "higher_lows": bool(higher_lows[i]),
            "dist_52h": dist_from_52h[i] if not np.isnan(dist_from_52h[i]) else None,
            # BTL fields
            "is_btl": bool(is_btl[i]),
            "mode": "ATL" if is_atl[i] else "BTL",
            "btl_buy": bool(btl_buy[i]),
            "btl_darvas_ok": bool(btl_darvas_ok[i]),
            "btl_rsi_ok": bool(btl_rsi_ok[i]),
            "btl_ema_ok": bool(btl_ema_ok[i]),
            "btl_stop_ok": bool(btl_stop_ok[i]),
            "btl_rr_ok": bool(btl_rr_ok[i]),
            "w_stage4": bool(w_stage4[i]),
            "darvas_breakout": bool(darvas_breakout[i]),
            "any_buy": bool(any_buy[i]),
            "gap_breakout": bool(gap_breakout[i]),
            "fwd_highs": fwd_highs, "fwd_lows": fwd_lows, "fwd_closes": fwd_closes,
            **fwd,
        })

    return signals

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════
print("=" * 130)
print("MULTI-STOCK ATL/BTL DUAL MODE ANALYSIS v2")
print(f"Stocks: {len(STOCKS)} | Period: {ANALYSIS_START} -> {ANALYSIS_END} (1 year)")
print("=" * 130)

all_signals = []
for sym in STOCKS:
    result = analyze_stock_atl(sym)
    if result:
        all_signals.extend(result)
    time.sleep(API_SLEEP)

df_all = pd.DataFrame(all_signals)
print(f"\nTotal data points: {len(df_all)} across {df_all['symbol'].nunique()} stocks")

# ═══════════════════════════════════════════════════════════════
# PART 1: MODE OVERVIEW (ATL vs BTL distribution)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 1: ATL/BTL MODE DISTRIBUTION")
print(f"{'='*130}")

n_total = len(df_all)
n_atl_days = (df_all['is_atl'] == True).sum()
n_btl_days = (df_all['is_btl'] == True).sum()
n_atl_buy = (df_all['atl_buy'] == True).sum()
n_btl_buy = (df_all['btl_buy'] == True).sum()
n_any_buy = (df_all['any_buy'] == True).sum()
n_bo_all  = (df_all['is_breakout'] == True).sum()
n_gap_bo  = (df_all['gap_breakout'] == True).sum()
n_darvas_bo = (df_all['darvas_breakout'] == True).sum()

print(f"""
  Total bar-days: {n_total} across {df_all['symbol'].nunique()} stocks
  ATL mode days: {n_atl_days} ({n_atl_days/n_total*100:.0f}%)
  BTL mode days: {n_btl_days} ({n_btl_days/n_total*100:.0f}%)
  
  ATL pivot breakouts: {n_bo_all}
  Darvas breakouts (BTL): {n_darvas_bo}
  
  ATL buy signals: {n_atl_buy}
  BTL buy signals: {n_btl_buy}
  Combined (any buy): {n_any_buy}
  
  GAP breakouts (pivot BO but neither ATL nor BTL buy fires): {n_gap_bo}
""")

# Per-mode breakdown on breakout bars
bo_df = df_all[df_all['is_breakout'] == True].copy()
if len(bo_df) > 0:
    bo_atl_mode = bo_df[bo_df['is_atl'] == True]
    bo_btl_mode = bo_df[bo_df['is_btl'] == True]
    print(f"  Pivot breakouts in ATL mode: {len(bo_atl_mode)} | ATL buy fired: {bo_atl_mode['atl_buy'].sum()}")
    print(f"  Pivot breakouts in BTL mode: {len(bo_btl_mode)} | BTL buy fired: {bo_btl_mode['btl_buy'].sum()}")
    print(f"  Gap (breakout, no buy signal): {n_gap_bo} ({n_gap_bo/len(bo_df)*100:.0f}% of all breakouts)")

# ═══════════════════════════════════════════════════════════════
# PART 2: ATL BUY SIGNALS
# ═══════════════════════════════════════════════════════════════
buy_df = df_all[df_all['atl_buy'] == True].copy()

print(f"\n{'='*130}")
print(f"PART 2: ATL BUY SIGNALS ({len(buy_df)} signals)")
print(f"{'='*130}")

def print_signal_table(sdf, show_mode=False):
    if len(sdf) == 0:
        print("  (no signals)"); return
    hdr = f"  {'Sym':>5} {'Date':>12} {'Close':>7} {'Pivot':>7} {'Chase%':>7} {'Pattern':>12} {'PS':>3} {'RS':>4} {'TS':>3} {'Vol%':>5}"
    if show_mode: hdr += f" {'Mode':>4}"
    hdr += f" {'T+2':>7} {'T+7':>7} {'T+14':>7} {'T+30':>7}"
    print(hdr)
    print(f"  {'-'*130}")
    for _, r in sdf.sort_values(['symbol', 'date']).iterrows():
        chase = f"{r['chase_pct']:+.1f}" if pd.notna(r.get('chase_pct')) else "n/a"
        rs = f"{r['rs_norm']:.0f}" if pd.notna(r.get('rs_norm')) else "n/a"
        vs = f"{r['vol_surge']:.0f}" if pd.notna(r.get('vol_surge')) else "n/a"
        pvt = f"{r['prior_pivot']:.0f}" if pd.notna(r.get('prior_pivot')) else "n/a"
        t2 = f"{r['T+2']:+.1f}%" if pd.notna(r.get('T+2')) else "n/a"
        t7 = f"{r['T+7']:+.1f}%" if pd.notna(r.get('T+7')) else "n/a"
        t14 = f"{r['T+14']:+.1f}%" if pd.notna(r.get('T+14')) else "n/a"
        t30 = f"{r['T+30']:+.1f}%" if pd.notna(r.get('T+30')) else "n/a"
        line = f"  {r['symbol']:>5} {str(r['date']):>12} {r['close']:>7.0f} {pvt:>7} {chase:>7} {r['pattern']:>12} {r['pattern_score']:>3} {rs:>4} {r['trend_score']:>3} {vs:>5}"
        if show_mode: line += f" {r['mode']:>4}"
        line += f" {t2:>7} {t7:>7} {t14:>7} {t30:>7}"
        print(line)

print_signal_table(buy_df)
print(f"\n  ATL Win rates:")
for h in FWD_HORIZONS:
    v = buy_df[h].dropna()
    if len(v) > 0:
        print(f"    {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}% | Med {v.median():+.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 3: BTL BUY SIGNALS
# ═══════════════════════════════════════════════════════════════
btl_buy_df = df_all[df_all['btl_buy'] == True].copy()

print(f"\n{'='*130}")
print(f"PART 3: BTL BUY SIGNALS ({len(btl_buy_df)} signals)")
print(f"{'='*130}")

if len(btl_buy_df) > 0:
    print_signal_table(btl_buy_df, show_mode=True)
    print(f"\n  BTL Win rates:")
    for h in FWD_HORIZONS:
        v = btl_buy_df[h].dropna()
        if len(v) > 0:
            print(f"    {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}% | Med {v.median():+.2f}%")
else:
    print("  No BTL buy signals fired!")
    # Diagnose why
    btl_mode = df_all[df_all['is_btl'] == True]
    print(f"\n  BTL mode days: {len(btl_mode)}")
    btl_darvas = btl_mode[btl_mode['darvas_breakout'] == True]
    print(f"  Darvas breakouts in BTL mode: {len(btl_darvas)}")
    if len(btl_darvas) > 0:
        print(f"    btl_rsi_ok: {btl_darvas['btl_rsi_ok'].sum()}")
        print(f"    btl_ema_ok: {btl_darvas['btl_ema_ok'].sum()}")
        print(f"    btl_stop_ok: {btl_darvas['btl_stop_ok'].sum()}")
        print(f"    btl_rr_ok: {btl_darvas['btl_rr_ok'].sum()}")
        print(f"    w_stage4: {btl_darvas['w_stage4'].sum()}")

# ═══════════════════════════════════════════════════════════════
# PART 4: GAP ZONE ANALYSIS - breakouts missed by BOTH modes
# ═══════════════════════════════════════════════════════════════
gap_df = df_all[df_all['gap_breakout'] == True].copy()

print(f"\n{'='*130}")
print(f"PART 4: GAP ZONE ANALYSIS ({len(gap_df)} breakouts, no buy signal from either mode)")
print(f"{'='*130}")

if len(gap_df) > 0:
    # Breakdown by mode at time of breakout
    gap_atl = gap_df[gap_df['is_atl'] == True]
    gap_btl = gap_df[gap_df['is_btl'] == True]
    print(f"\n  Gap breakouts in ATL mode: {len(gap_atl)} (had ATL structure but buy didn't fire)")
    print(f"  Gap breakouts in BTL mode: {len(gap_btl)} (BTL mode, BTL buy didn't fire either)")

    # Why ATL buy didn't fire for ATL-mode gap breakouts
    if len(gap_atl) > 0:
        print(f"\n  ATL-mode gap breakouts - why ATL buy failed:")
        atl_reasons = {}
        for _, r in gap_atl.iterrows():
            fails = []
            if not r['is_qualified']: fails.append("not_qualified")
            if not r['has_vol_surge']: fails.append("no_vol_surge")
            if not r['market_bullish']: fails.append("mkt_bearish")
            if not r['stop_ok']: fails.append("stop>8%")
            if not r['rs_strong']: fails.append("RS<80")
            for f in fails:
                atl_reasons[f] = atl_reasons.get(f, 0) + 1
        for reason, cnt in sorted(atl_reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason:<20}: {cnt:>4} ({cnt/len(gap_atl)*100:.0f}%)")

    # Why BTL buy didn't fire for BTL-mode gap breakouts
    if len(gap_btl) > 0:
        print(f"\n  BTL-mode gap breakouts - why BTL buy failed:")
        btl_reasons = {}
        for _, r in gap_btl.iterrows():
            fails = []
            if not r['darvas_breakout']: fails.append("no_darvas_bo")
            if not r['btl_rsi_ok']: fails.append("no_rsi_oversold")
            if not r['btl_ema_ok']: fails.append("ema12<ema36")
            if not r['btl_stop_ok']: fails.append("stop>10%")
            if not r['btl_rr_ok']: fails.append("R:R<2:1")
            if r['w_stage4']: fails.append("stage4")
            for f in fails:
                btl_reasons[f] = btl_reasons.get(f, 0) + 1
        for reason, cnt in sorted(btl_reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason:<20}: {cnt:>4} ({cnt/len(gap_btl)*100:.0f}%)")

    # Gap breakouts with good returns = real missed opportunities
    gap_good = gap_df[(gap_df['T+30'].notna()) & (gap_df['T+30'] > 20)].sort_values('T+30', ascending=False)
    if len(gap_good) > 0:
        print(f"\n  TOP GAP OPPORTUNITIES (T+30 > +20%, {len(gap_good)} signals):")
        print(f"    {'Sym':>5} {'Date':>12} {'Close':>7} {'Mode':>4} {'Pattern':>12} {'RS':>4} {'TS':>3} {'Vol%':>5} "
              f"{'T+7':>7} {'T+14':>7} {'T+30':>7} Why-ATL-fail | Why-BTL-fail")
        print(f"    {'-'*140}")
        for _, r in gap_good.head(30).iterrows():
            atl_f = []
            if not r['is_atl']: atl_f.append("!ATL")
            elif not r['is_qualified']: atl_f.append("!Qual")
            if not r['has_vol_surge']: atl_f.append("!Vol")
            if not r['rs_strong']: atl_f.append("!RS")
            if not r['market_bullish']: atl_f.append("!Mkt")
            btl_f = []
            if not r['is_btl']: btl_f.append("ATLmode")
            elif not r['darvas_breakout']: btl_f.append("!Darv")
            if not r['btl_rsi_ok']: btl_f.append("!RSI")
            if not r['btl_ema_ok']: btl_f.append("!EMA")
            rs = f"{r['rs_norm']:.0f}" if pd.notna(r.get('rs_norm')) else "n/a"
            vs = f"{r['vol_surge']:.0f}" if pd.notna(r.get('vol_surge')) else "n/a"
            t7 = f"{r['T+7']:+.1f}%" if pd.notna(r.get('T+7')) else "n/a"
            t14 = f"{r['T+14']:+.1f}%" if pd.notna(r.get('T+14')) else "n/a"
            t30 = f"{r['T+30']:+.1f}%" if pd.notna(r.get('T+30')) else "n/a"
            print(f"    {r['symbol']:>5} {str(r['date']):>12} {r['close']:>7.0f} {r['mode']:>4} {r['pattern']:>12} {rs:>4} {r['trend_score']:>3} {vs:>5} "
                  f"{t7:>7} {t14:>7} {t30:>7} {','.join(atl_f):<15} {','.join(btl_f)}")

    # Win rate comparison: gap vs bought signals
    print(f"\n  Forward returns comparison (gap breakouts vs bought signals):")
    for label, sub in [("ATL buy", buy_df), ("BTL buy", btl_buy_df), ("Gap (no buy)", gap_df)]:
        if len(sub) == 0: continue
        print(f"    {label} ({len(sub)} signals):")
        for h in FWD_HORIZONS:
            v = sub[h].dropna()
            if len(v) > 0:
                print(f"      {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | Avg {v.mean():+.2f}%")

# ═══════════════════════════════════════════════════════════════
# PART 5: BIG TREND EVALUATION (Minervini: ATL should catch 50%+ moves)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 5: BIG TREND EVALUATION (stocks with 50%+ gain in period)")
print(f"{'='*130}")

print(f"\n  {'Sym':>5} {'Return':>7} {'MaxGn':>7} {'ATLd':>5} {'BTLd':>5} {'ATLbuy':>6} {'BTLbuy':>6} {'AnyBuy':>6} {'GapBO':>5} {'1stBO':>12} {'1stBuyDt':>12} {'1stBuyMode':>10}")
print(f"  {'-'*120}")

for sym in sorted(df_all['symbol'].unique()):
    sdf = df_all[df_all['symbol'] == sym].sort_values('date')
    if len(sdf) == 0: continue
    start_p = sdf.iloc[0]['close']
    end_p = sdf.iloc[-1]['close']
    ret = (end_p - start_p) / start_p * 100
    mg = (sdf['high'].max() - start_p) / start_p * 100
    if mg < 50: continue  # Only big movers

    n_atl_d = sdf['is_atl'].sum()
    n_btl_d = sdf['is_btl'].sum()
    n_atl_b = sdf['atl_buy'].sum()
    n_btl_b = sdf['btl_buy'].sum()
    n_any_b = sdf['any_buy'].sum()
    n_gap_b = sdf['gap_breakout'].sum()

    # First breakout date
    first_bo = sdf[sdf['is_breakout'] == True]
    first_bo_dt = str(first_bo.iloc[0]['date']) if len(first_bo) > 0 else "n/a"

    # First buy signal (ATL or BTL)
    first_buy = sdf[sdf['any_buy'] == True]
    if len(first_buy) > 0:
        fb = first_buy.iloc[0]
        first_buy_dt = str(fb['date'])
        first_buy_mode = "ATL" if fb['atl_buy'] else "BTL"
    else:
        first_buy_dt = "NONE"
        first_buy_mode = "MISSED"

    print(f"  {sym:>5} {ret:>+6.1f}% {mg:>+6.1f}% {n_atl_d:>5} {n_btl_d:>5} {n_atl_b:>6} {n_btl_b:>6} {n_any_b:>6} {n_gap_b:>5} {first_bo_dt:>12} {first_buy_dt:>12} {first_buy_mode:>10}")

# ═══════════════════════════════════════════════════════════════
# PART 6: CONDITION COMBOS + SL/TP SIMULATION
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 6: CONDITION COMBINATIONS - ALL HORIZONS")
print(f"{'='*130}")

combos = [
    ("All pivot breakouts", lambda r: r['is_breakout']),
    ("BO + VolSurge", lambda r: r['is_breakout'] and r['has_vol_surge']),
    ("BO+Vol (ATL mode only)", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['is_atl']),
    ("BO+Vol+ATL+Mkt", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['is_atl'] and r['market_bullish']),
    ("BO+Vol+ATL+Mkt+RS>=80", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['is_atl'] and r['market_bullish'] and r['rs_strong']),
    ("Full ATL BUY (current)", lambda r: r['atl_buy']),
    ("Full ATL + Chase<=3%", lambda r: r['atl_buy'] and pd.notna(r.get('chase_pct')) and r['chase_pct'] <= 3),
    ("BTL BUY", lambda r: r['btl_buy']),
    ("Any BUY (ATL or BTL)", lambda r: r['any_buy']),
    ("Gap breakouts (missed)", lambda r: r['gap_breakout']),
    ("Gap + VolSurge (missed w/vol)", lambda r: r['gap_breakout'] and r['has_vol_surge']),
    ("BO+Vol+ATL+Mkt+StopOK (no RS/Qual)", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['is_atl'] and r['market_bullish'] and r['stop_ok']),
]

print(f"\n  {'Combination':<45} {'Sigs':>5}", end="")
for h in ['T+2', 'T+7', 'T+14', 'T+30']:
    print(f"  {'Win':>12} {'Avg':>8}", end="")
print()
print(f"  {'-'*130}")

for name, cond_fn in combos:
    try:
        mask_s = df_all.apply(cond_fn, axis=1)
        subset = df_all[mask_s]
        n_sig = len(subset)
        if n_sig == 0:
            print(f"  {name:<45} {0:>5}"); continue
        line = f"  {name:<45} {n_sig:>5}"
        for h in ['T+2', 'T+7', 'T+14', 'T+30']:
            hv = subset[h].dropna()
            if len(hv) > 0:
                w_str = f"{(hv>0).sum()}/{len(hv)}({(hv>0).sum()/len(hv)*100:.0f}%)"
                a_str = f"{hv.mean():+.1f}%"
            else:
                w_str = "n/a"; a_str = "n/a"
            line += f"  {w_str:>12} {a_str:>8}"
        print(line)
    except Exception as e:
        print(f"  {name:<45} ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# PART 7: SL/TP TRADE SIMULATION
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 7: REALISTIC TRADE SIMULATION (ATL: SL=-8%/TP=+20%, BTL: SL=-10%/TP=+20%)")
print(f"{'='*130}")

SL_PCT_ATL = -8.0
SL_PCT_BTL = -10.0
TP_PCT = 20.0
SIM_HORIZONS = [7, 14, 30]

def simulate_trade(row, sl_pct=-8.0, tp_pct=TP_PCT, horizons=SIM_HORIZONS):
    entry = row['close']
    sl_price = entry * (1 + sl_pct / 100.0)
    tp_price = entry * (1 + tp_pct / 100.0)
    fwd_h = row.get('fwd_highs', [])
    fwd_l = row.get('fwd_lows', [])
    fwd_c = row.get('fwd_closes', [])
    if not fwd_h or len(fwd_h) == 0: return {}
    results = {}
    for hz in horizons:
        sl_day = tp_day = None
        max_dd = max_gain = 0.0
        for d in range(min(hz, len(fwd_l))):
            lo, hi = fwd_l[d], fwd_h[d]
            if np.isnan(lo) or np.isnan(hi): break
            dd_p = (lo - entry) / entry * 100
            gn_p = (hi - entry) / entry * 100
            if dd_p < max_dd: max_dd = dd_p
            if gn_p > max_gain: max_gain = gn_p
            if sl_day is None and lo <= sl_price: sl_day = d + 1
            if tp_day is None and hi >= tp_price: tp_day = d + 1
        if sl_day and tp_day:
            if sl_day <= tp_day: outcome, ret, exit_d = "SL", sl_pct, sl_day
            else: outcome, ret, exit_d = "TP", tp_pct, tp_day
        elif sl_day: outcome, ret, exit_d = "SL", sl_pct, sl_day
        elif tp_day: outcome, ret, exit_d = "TP", tp_pct, tp_day
        else:
            idx2 = hz - 1
            if idx2 < len(fwd_c) and not np.isnan(fwd_c[idx2]):
                ret = (fwd_c[idx2] - entry) / entry * 100
                outcome, exit_d = "HOLD", hz
            else:
                ret, outcome, exit_d = np.nan, "N/A", None
        results[f"T{hz}_outcome"] = outcome
        results[f"T{hz}_ret"] = ret
        results[f"T{hz}_exit_day"] = exit_d
    return results

sim_combos = [
    ("ATL BUY (SL=-8%)", lambda r: r['atl_buy'], SL_PCT_ATL),
    ("BTL BUY (SL=-10%)", lambda r: r['btl_buy'], SL_PCT_BTL),
    ("Any BUY (ATL/BTL)", lambda r: r['any_buy'], SL_PCT_ATL),
    ("Gap BO+Vol (SL=-8%)", lambda r: r['gap_breakout'] and r['has_vol_surge'], SL_PCT_ATL),
    ("BO+Vol+ATL+Mkt (SL=-8%)", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['is_atl'] and r['market_bullish'], SL_PCT_ATL),
    ("All BO+Vol (SL=-8%)", lambda r: r['is_breakout'] and r['has_vol_surge'], SL_PCT_ATL),
]

for cname, cfn, sl in sim_combos:
    try:
        cmask = df_all.apply(cfn, axis=1)
        csub = df_all[cmask].copy()
        if len(csub) == 0:
            print(f"\n  {cname}: (no signals)"); continue
        c_sim = [simulate_trade(crow, sl_pct=sl) for _, crow in csub.iterrows()]
        c_sim_df = pd.DataFrame(c_sim)
        print(f"\n  {cname} ({len(csub)} signals):")
        for hz in SIM_HORIZONS:
            oc = f'T{hz}_outcome'; rc = f'T{hz}_ret'
            if oc not in c_sim_df.columns: continue
            vv = c_sim_df[c_sim_df[oc] != 'N/A']
            if len(vv) == 0: continue
            ns = (vv[oc] == 'SL').sum(); nt = (vv[oc] == 'TP').sum(); nh = (vv[oc] == 'HOLD').sum()
            ar = vv[rc].dropna().mean(); nv = len(vv)
            print(f"    T+{hz}: SL={ns}({ns/nv*100:.0f}%) TP={nt}({nt/nv*100:.0f}%) HOLD={nh}({nh/nv*100:.0f}%) | Avg={ar:+.1f}%")
    except Exception as e:
        print(f"\n  {cname}: ERROR {e}")

# ═══════════════════════════════════════════════════════════════
# PART 8: PER-STOCK SUMMARY (with mode info)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 8: PER-STOCK SUMMARY (ATL/BTL mode & signals)")
print(f"{'='*130}")

print(f"\n  {'Sym':>5} {'Days':>5} {'ATLd':>5} {'BTLd':>5} {'BO':>3} {'ATLb':>4} {'BTLb':>4} {'GapBO':>5} {'RS_avg':>6} {'Return':>7} {'MaxGn':>7} {'MaxDD':>7}")
print(f"  {'-'*95}")

for sym in sorted(df_all['symbol'].unique()):
    sdf = df_all[df_all['symbol'] == sym].sort_values('date')
    if len(sdf) == 0: continue
    n_days = len(sdf)
    n_atl_d = sdf['is_atl'].sum()
    n_btl_d = sdf['is_btl'].sum()
    n_bo = sdf['is_breakout'].sum()
    n_atl_b = sdf['atl_buy'].sum()
    n_btl_b = sdf['btl_buy'].sum()
    n_gap = sdf['gap_breakout'].sum()
    rs_avg = sdf['rs_norm'].dropna().mean() if len(sdf['rs_norm'].dropna()) > 0 else np.nan
    start_p = sdf.iloc[0]['close']
    end_p = sdf.iloc[-1]['close']
    ret = (end_p - start_p) / start_p * 100
    mg = (sdf['high'].max() - start_p) / start_p * 100
    mdd = (sdf['low'].min() - start_p) / start_p * 100
    rs_s = f"{rs_avg:.0f}" if not np.isnan(rs_avg) else "n/a"
    print(f"  {sym:>5} {n_days:>5} {n_atl_d:>5} {n_btl_d:>5} {n_bo:>3} {n_atl_b:>4} {n_btl_b:>4} {n_gap:>5} {rs_s:>6} {ret:>+6.1f}% {mg:>+6.1f}% {mdd:>+6.1f}%")

# ═══════════════════════════════════════════════════════════════
# PART 9: CONCLUSIONS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 9: CONCLUSIONS & HYPOTHESIS TESTING")
print(f"{'='*130}")

print(f"""
  DATASET: {df_all['symbol'].nunique()} stocks, {n_total} bar-days, {ANALYSIS_START} -> {ANALYSIS_END} (1 year)
  
  MODE DISTRIBUTION:
    ATL mode: {n_atl_days} days ({n_atl_days/n_total*100:.0f}%)
    BTL mode: {n_btl_days} days ({n_btl_days/n_total*100:.0f}%)
  
  SIGNALS:
    ATL buy: {n_atl_buy} | BTL buy: {n_btl_buy} | Combined: {n_any_buy}
    Gap breakouts (neither mode fires): {n_gap_bo}
  
  HYPOTHESIS 1 (Timeframe):
    With 1-year data, we can now see whether ATL logic catches long-term 50%+ trends.
    See Part 5 for big trend evaluation.
    
  HYPOTHESIS 2 (ATL/BTL Gap):
    Gap breakouts: {n_gap_bo} ({n_gap_bo/max(n_bo_all,1)*100:.0f}% of all breakouts)
    These are breakouts where NEITHER ATL nor BTL logic fires a buy signal.
    See Part 4 for detailed gap zone analysis and failure reasons.
""")

print(f"{'='*130}")
print("ANALYSIS COMPLETE")
print(f"{'='*130}")
