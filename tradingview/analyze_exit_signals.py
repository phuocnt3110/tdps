#!/usr/bin/env python3
"""
analyze_exit_signals.py - Multi-dimensional Exit Signal Prediction
==================================================================
Phân tích đa chiều dự báo điểm thoát:
  Vi mô: 12 exit signals nội tại mã (MA breaks, volume, RS, pattern)
  Vĩ mô: VNINDEX health, distribution days, sector strength
  Chỉ sử dụng dữ liệu quá khứ tại mỗi bar (no lookahead)
  Kết hợp nhật ký giao dịch thực tế để đánh giá accuracy

Chạy: python analyze_exit_signals.py
"""
import sys, os, io, time, warnings
warnings.filterwarnings('ignore')
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
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

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_CSV = os.path.join(SCRIPT_DIR, "trade_analysis_results.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "exit_signal_report.txt")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "exit_signal_detail.csv")

LOOKBACK_DAYS = 730     # ~2 years of calendar days for fetch buffer
FWD_BARS = 60           # Track 60 bars forward from entry
API_SLEEP = 0.8
BENCHMARK = "VNINDEX"
BARS_52 = 252

# Sector mapping for peer group analysis
SECTORS = {
    "Energy":       ["PVD","PVS","PVB","BSR","OIL","PLX","POW","NT2","DPM","DCM","GSP","NAF","MSR"],
    "Retail":       ["MWG","PNJ","DGW"],
    "Banking":      ["CTG","STB"],
    "Construction": ["CTD","PVC","G36","SZC"],
    "Steel":        ["HPG"],
    "Logistics":    ["GMD","PAC"],
    "Agriculture":  ["BAF"],
    "Misc":         ["FIT","TTF","NDN","PHR","VHC","BIG","BIC"],
}
STOCK_SECTOR = {}
for _sec, _syms in SECTORS.items():
    for _s in _syms:
        STOCK_SECTOR[_s] = _sec

# Tee output
class Tee:
    def __init__(self, *s):
        self.s = s
    def write(self, d):
        for x in self.s:
            try: x.write(d); x.flush()
            except: pass
    def flush(self):
        for x in self.s:
            try: x.flush()
            except: pass

# ═══════════════════════════════════════════════════════════════
# HELPERS (mirrored from analyze_3zone.py — past-only)
# ═══════════════════════════════════════════════════════════════
def sma(a, p):
    r = np.full(len(a), np.nan)
    for i in range(p-1, len(a)):
        r[i] = np.mean(a[i-p+1:i+1])
    return r

def ema_c(a, p):
    r = np.full(len(a), np.nan); k = 2.0/(p+1)
    for i in range(len(a)):
        if not np.isnan(a[i]):
            r[i] = a[i]
            for j in range(i+1, len(a)):
                r[j] = a[j]*k + r[j-1]*(1-k)
            break
    return r

def calc_atr(H, L, C, p=14):
    n = len(C); tr = np.full(n, np.nan)
    for i in range(1, n):
        tr[i] = max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1]))
    atr = np.full(n, np.nan)
    if p+1 < n:
        atr[p] = np.nanmean(tr[1:p+1])
        for j in range(p+1, n):
            if not np.isnan(atr[j-1]) and not np.isnan(tr[j]):
                atr[j] = (atr[j-1]*(p-1)+tr[j])/p
    return atr

def calc_rs_norm(C, bc_aligned, bars_52=252):
    """RS Norm (0-100) vs benchmark. Both arrays must be date-aligned."""
    n = len(C)
    perf = np.full(n, np.nan); bp = np.full(n, np.nan)
    for i in range(bars_52, n):
        if C[i-bars_52] > 0: perf[i] = (C[i]-C[i-bars_52])/C[i-bars_52]*100
        if not np.isnan(bc_aligned[i-bars_52]) and bc_aligned[i-bars_52] > 0:
            bp[i] = (bc_aligned[i]-bc_aligned[i-bars_52])/bc_aligned[i-bars_52]*100
    rs_raw = perf - bp
    rs_norm = np.full(n, np.nan)
    for i in range(bars_52, n):
        w = rs_raw[max(0, i-bars_52+1):i+1]; v = w[~np.isnan(w)]
        if len(v) > 0:
            rn = v.max()-v.min()
            rs_norm[i] = 100*(rs_raw[i]-v.min())/rn if rn > 0 else 50
    return rs_norm

# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════
def fetch(symbol, start, end):
    try:
        q = Quote(source="vci", symbol=symbol, show_log=False)
        df = q.history(start=start, end=end, interval="1D")
        if df is None or df.empty: return None
        df['date'] = pd.to_datetime(df['time']).dt.date
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"  ERR {symbol}: {e}"); return None

def align_bc(stock_dates, bc_map):
    """Align benchmark closes to stock trading dates."""
    sorted_bd = sorted(bc_map.keys())
    out = []
    for d in stock_dates:
        if d in bc_map:
            out.append(bc_map[d])
        else:
            prev = np.nan
            for bd in sorted_bd:
                if bd <= d: prev = bc_map[bd]
                else: break
            out.append(prev)
    return np.array(out, dtype=float)

# ═══════════════════════════════════════════════════════════════
# VNINDEX MACRO SIGNALS (computed once for all dates)
# ═══════════════════════════════════════════════════════════════
def compute_vni_signals(bc_df):
    """Compute macro signals from VNINDEX data. Returns date->dict map."""
    C = bc_df['close'].values.astype(float)
    V = bc_df['volume'].values.astype(float)
    dates = bc_df['date'].tolist()
    n = len(C)
    ma50 = sma(C, 50); ma150 = sma(C, 150)
    vol_ma = sma(V, 50)

    # Distribution days count (trailing 25 bars)
    dist_count = np.zeros(n, dtype=int)
    for i in range(25, n):
        dc = 0
        for j in range(i-24, i+1):
            if j >= 1 and C[j] < C[j-1]*0.998 and V[j] > V[j-1]:
                dc += 1
        dist_count[i] = dc

    vni_map = {}
    for i in range(n):
        d = dates[i]
        vni_map[d] = {
            'vni_close': C[i],
            'vni_ma50': ma50[i] if not np.isnan(ma50[i]) else None,
            'vni_ma150': ma150[i] if not np.isnan(ma150[i]) else None,
            'vni_breakMA50': bool(C[i] < ma50[i]) if not np.isnan(ma50[i]) else False,
            'vni_breakMA150': bool(C[i] < ma150[i]) if not np.isnan(ma150[i]) else False,
            'vni_dist25': int(dist_count[i]),
            'vni_dist5': bool(dist_count[i] >= 5),
            'vni_dist8': bool(dist_count[i] >= 8),
            'vni_ret20': float((C[i]-C[i-20])/C[i-20]*100) if i >= 20 and C[i-20] > 0 else 0.0,
        }
    return vni_map

# ═══════════════════════════════════════════════════════════════
# MICRO EXIT SIGNALS (12 signals, past-only)
# ═══════════════════════════════════════════════════════════════
SIGNAL_NAMES = [
    'breakMA10', 'breakMA20', 'breakMA50',
    'failedBO', 'lowerHigh', 'lowerLow',
    'volClimax', 'climaxTop', 'churning',
    'rsDiverg', 'breakATR', 'lateBase',
]
MACRO_NAMES = ['vni_dist5', 'vni_dist8', 'vni_breakMA50', 'sector_weak']
ALL_SIGNAL_NAMES = SIGNAL_NAMES + MACRO_NAMES

def compute_micro_signals(O, H, L, C, V, rs_norm):
    """Compute 12 micro exit signals. Returns dict of bool arrays (len=n)."""
    n = len(C)
    ma10 = sma(C, 10); ma20 = sma(C, 20); ma50 = sma(C, 50)
    vol_ma20 = sma(V, 20)
    atr14 = calc_atr(H, L, C, 14); atr10 = calc_atr(H, L, C, 10)

    sig = {}

    # 1. breakMA10
    sig['breakMA10'] = np.array([C[i] < ma10[i] if not np.isnan(ma10[i]) else False for i in range(n)])
    # 2. breakMA20
    sig['breakMA20'] = np.array([C[i] < ma20[i] if not np.isnan(ma20[i]) else False for i in range(n)])
    # 3. breakMA50
    sig['breakMA50'] = np.array([C[i] < ma50[i] if not np.isnan(ma50[i]) else False for i in range(n)])

    # 4. failedBreakout: close drops below 30-bar high (proxy for pivot rejection)
    fb = np.zeros(n, dtype=bool)
    for i in range(31, n):
        bh = np.max(H[i-30:i])  # past 30 bars high (anti-repaint: excludes bar i)
        fb[i] = C[i] < bh and C[i-1] >= bh
    sig['failedBO'] = fb

    # 5. lowerHigh: high < highest(high, 5)[1]  — using past 5 bars excluding current
    lh = np.zeros(n, dtype=bool)
    for i in range(6, n):
        lh[i] = H[i] < np.max(H[i-5:i])
    sig['lowerHigh'] = lh

    # 6. lowerLow: low < lowest(low, 5)[1]
    ll = np.zeros(n, dtype=bool)
    for i in range(6, n):
        ll[i] = L[i] < np.min(L[i-5:i])
    sig['lowerLow'] = ll

    # 7. volClimax: vol > 3×volMA20 AND close < open (distribution candle)
    vc = np.zeros(n, dtype=bool)
    for i in range(n):
        if not np.isnan(vol_ma20[i]) and vol_ma20[i] > 0:
            vc[i] = V[i] > vol_ma20[i]*3 and C[i] < O[i]
    sig['volClimax'] = vc

    # 8. climaxTop: vol >= 4×volMA20 + (extended OR wide bar)
    ct = np.zeros(n, dtype=bool)
    for i in range(n):
        if np.isnan(vol_ma20[i]) or np.isnan(ma20[i]) or np.isnan(atr14[i]): continue
        if vol_ma20[i] <= 0 or ma20[i] <= 0 or C[i] <= 0: continue
        vol4x = V[i] >= vol_ma20[i]*4
        extended = (C[i]-ma20[i])/ma20[i]*100 >= 7.0
        wide = (H[i]-L[i])/L[i]*100 > atr14[i]/C[i]*100*1.5 if L[i] > 0 else False
        ct[i] = vol4x and (extended or wide)
    sig['climaxTop'] = ct

    # 9. churning: high avg vol 5d but little price progress
    ch = np.zeros(n, dtype=bool)
    for i in range(5, n):
        if np.isnan(vol_ma20[i]) or vol_ma20[i] <= 0 or C[i-5] <= 0: continue
        avg5 = np.mean(V[i-4:i+1])
        ch[i] = (avg5 > vol_ma20[i]*1.5 and
                 abs((C[i]-C[i-5])/C[i-5]*100) < 3 and
                 (C[i] > ma50[i] if not np.isnan(ma50[i]) else False))
    sig['churning'] = ch

    # 10. rsDivergence: price up 5d but RS dropped >5 points
    rd = np.zeros(n, dtype=bool)
    for i in range(5, n):
        if np.isnan(rs_norm[i]) or np.isnan(rs_norm[i-5]): continue
        rd[i] = C[i] > C[i-5] and (rs_norm[i]-rs_norm[i-5]) < -5
    sig['rsDiverg'] = rd

    # 11. breakTrailATR: close < highest(H, 10)[past] - ATR(10)*2
    ba = np.zeros(n, dtype=bool)
    for i in range(11, n):
        if np.isnan(atr10[i]): continue
        trail = np.max(H[i-10:i]) - atr10[i]*2
        ba[i] = C[i] < trail
    sig['breakATR'] = ba

    # 12. lateStageBase: base pullback count >= 3
    bc2 = 0
    lsb = np.zeros(n, dtype=bool)
    for i in range(51, n):
        hh50 = np.max(H[max(0, i-50):i])
        if hh50 > 0:
            pb = (hh50-L[i])/hh50*100
            hh50_prev = np.max(H[max(0, i-51):i-1])
            pb_prev = (hh50_prev-L[i-1])/hh50_prev*100 if hh50_prev > 0 else 0
            if pb >= 10 and pb_prev < 10:
                bc2 += 1
        if not np.isnan(ma50[i]) and C[i] < ma50[i]*0.9:
            bc2 = 0
        lsb[i] = bc2 >= 3
    sig['lateBase'] = lsb

    return sig

# ═══════════════════════════════════════════════════════════════
# SECTOR RELATIVE STRENGTH (peer group proxy)
# ═══════════════════════════════════════════════════════════════
def compute_sector_weakness(stock_sym, stock_dates, stock_C, all_stock_data, bc_map):
    """Sector weakness: sector 20d return < VNI 20d return by >3%."""
    sector = STOCK_SECTOR.get(stock_sym, "Misc")
    peers = [s for s in SECTORS.get(sector, []) if s != stock_sym and s in all_stock_data]
    n = len(stock_C)
    weak = np.zeros(n, dtype=bool)

    if len(peers) == 0:
        return weak

    for i in range(20, n):
        d = stock_dates[i]; d20 = stock_dates[i-20]
        # Sector 20d return (equal-weighted peers)
        peer_rets = []
        for p in peers:
            pdf = all_stock_data[p]
            dm = pdf['date_map']
            if d in dm and d20 in dm:
                c_now = pdf['C'][dm[d]]; c_20 = pdf['C'][dm[d20]]
                if c_20 > 0: peer_rets.append((c_now-c_20)/c_20*100)
        if len(peer_rets) == 0: continue
        sec_ret = np.mean(peer_rets)

        # VNI 20d return
        bc_now = bc_map.get(d); bc_20 = bc_map.get(d20)
        if bc_now is None or bc_20 is None or bc_20 == 0: continue
        vni_ret = (bc_now-bc_20)/bc_20*100

        weak[i] = (sec_ret - vni_ret) < -3.0

    return weak

# ═══════════════════════════════════════════════════════════════
# FORWARD TRACKING: from entry, track signals + DD + gain
# ═══════════════════════════════════════════════════════════════
def track_trade(entry_bar, C, H, L, micro_sig, macro_dates_sig, stock_dates, sector_weak, fwd=FWD_BARS):
    """Track forward from entry_bar. Returns dict with signal timelines."""
    n = len(C)
    avail = min(fwd, n - entry_bar - 1)
    if avail <= 0:
        return None

    entry_price = C[entry_bar]
    result = {
        'entry_price': entry_price,
        'bars_avail': avail,
        'max_gain': 0.0, 'max_dd': 0.0,
        'day_max_gain': 0, 'day_max_dd': 0,
        'dd_curve': [],  # DD at each forward bar
    }

    # Per-signal: first fire day, DD at fire, gain at fire
    for sn in ALL_SIGNAL_NAMES:
        result[f'{sn}_day'] = -1      # day it first fired (-1=never)
        result[f'{sn}_dd'] = np.nan   # DD when it fired
        result[f'{sn}_gain'] = np.nan # gain when it fired

    mg = 0.0; md = 0.0
    for j in range(1, avail+1):
        bi = entry_bar + j
        cur_gain = (C[bi]-entry_price)/entry_price*100
        cur_dd = (min(L[entry_bar+1:bi+1].min() if j > 0 else L[bi], L[bi])-entry_price)/entry_price*100
        cur_mg = (max(H[entry_bar+1:bi+1].max() if j > 0 else H[bi], H[bi])-entry_price)/entry_price*100

        if cur_mg > mg: mg = cur_mg; result['day_max_gain'] = j
        if cur_dd < md: md = cur_dd; result['day_max_dd'] = j

        result['dd_curve'].append(round(cur_dd, 2))

        # Check micro signals
        for sn in SIGNAL_NAMES:
            if result[f'{sn}_day'] == -1 and micro_sig[sn][bi]:
                result[f'{sn}_day'] = j
                result[f'{sn}_dd'] = round(cur_dd, 2)
                result[f'{sn}_gain'] = round(cur_gain, 2)

        # Check macro signals (by date lookup)
        d = stock_dates[bi]
        macro = macro_dates_sig.get(d, {})
        for mn in ['vni_dist5', 'vni_dist8', 'vni_breakMA50']:
            if result[f'{mn}_day'] == -1 and macro.get(mn, False):
                result[f'{mn}_day'] = j
                result[f'{mn}_dd'] = round(cur_dd, 2)
                result[f'{mn}_gain'] = round(cur_gain, 2)

        # Sector weakness
        if result['sector_weak_day'] == -1 and sector_weak[bi]:
            result['sector_weak_day'] = j
            result['sector_weak_dd'] = round(cur_dd, 2)
            result['sector_weak_gain'] = round(cur_gain, 2)

    result['max_gain'] = round(mg, 2)
    result['max_dd'] = round(md, 2)
    return result

# ═══════════════════════════════════════════════════════════════
# STATISTICS & SCORING
# ═══════════════════════════════════════════════════════════════
def compute_statistics(trades_results):
    """Aggregate signal statistics across all trades."""
    stats = {}
    for sn in ALL_SIGNAL_NAMES:
        fired = [(t, t['track']) for t in trades_results if t['track'] and t['track'][f'{sn}_day'] > 0]
        not_fired = [(t, t['track']) for t in trades_results if t['track'] and t['track'][f'{sn}_day'] == -1]
        n_total = len([t for t in trades_results if t['track']])
        n_fired = len(fired)

        if n_fired == 0:
            stats[sn] = {'fire_rate': 0, 'n_fired': 0, 'avg_day': 0, 'accuracy': 0,
                         'avg_dd_at_fire': 0, 'avg_avoidable_dd': 0, 'score': 0}
            continue

        avg_day = np.mean([tr[f'{sn}_day'] for _, tr in fired])
        # Accuracy: % of fired trades that are actual losers
        n_correct = sum(1 for t, tr in fired if t['result'] == 'lose')
        accuracy = n_correct / n_fired * 100 if n_fired > 0 else 0

        # Avoidable DD: for losers where signal fired, how much more DD happened after signal
        avoidable = []
        for t, tr in fired:
            if t['result'] == 'lose':
                dd_at_fire = tr[f'{sn}_dd']
                actual_dd = tr['max_dd']
                if not np.isnan(dd_at_fire):
                    avoidable.append(actual_dd - dd_at_fire)  # negative = more DD after signal
        avg_avoidable = np.mean(avoidable) if avoidable else 0

        # DD at fire
        dd_at = [tr[f'{sn}_dd'] for _, tr in fired if not np.isnan(tr[f'{sn}_dd'])]
        avg_dd_at = np.mean(dd_at) if dd_at else 0

        # Composite score: higher = better exit signal
        # Weight: accuracy (40%) + early detection (30%) + avoidable DD (30%)
        early_score = max(0, 100 - avg_day * 5)  # Earlier = better, 0 at day 20+
        avoid_score = min(100, abs(avg_avoidable) * 10) if avg_avoidable < 0 else 0
        score = accuracy * 0.4 + early_score * 0.3 + avoid_score * 0.3

        stats[sn] = {
            'fire_rate': n_fired / n_total * 100 if n_total > 0 else 0,
            'n_fired': n_fired,
            'avg_day': round(avg_day, 1),
            'accuracy': round(accuracy, 1),
            'avg_dd_at_fire': round(avg_dd_at, 2),
            'avg_avoidable_dd': round(avg_avoidable, 2),
            'score': round(score, 1),
        }
    return stats

def compute_zone_stats(trades_results, zone):
    """Stats for a specific zone (atl/btl)."""
    filtered = [t for t in trades_results if t['type'] == zone]
    if not filtered: return None
    return compute_statistics(filtered)

# ═══════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════
S = '═' * 100
S2 = '─' * 100

def print_signal_table(stats, title):
    print(f"\n{S}\n  {title}\n{S}")
    print(f"  {'Signal':<15} {'Fire%':>6} {'#Fire':>5} {'AvgDay':>7} {'Accur%':>7} {'DD@Fire':>8} {'AvoidDD':>8} {'Score':>6}")
    print(f"  {S2}")
    ranked = sorted(stats.items(), key=lambda x: -x[1]['score'])
    for sn, st in ranked:
        if st['n_fired'] == 0: continue
        print(f"  {sn:<15} {st['fire_rate']:>5.0f}% {st['n_fired']:>5} {st['avg_day']:>6.1f}d {st['accuracy']:>6.1f}% "
              f"{st['avg_dd_at_fire']:>7.2f}% {st['avg_avoidable_dd']:>7.2f}% {st['score']:>6.1f}")
    # Signals that never fired
    never = [sn for sn, st in stats.items() if st['n_fired'] == 0]
    if never:
        print(f"  {'(never fired)':.<15} {', '.join(never)}")

def print_trade_timeline(t, track):
    code = t['code']; sym = t['symbol']; zone = t['type'].upper()
    res = '✓WIN' if t['result'] == 'win' else '✗LOSE'
    pnl = t['pnl']
    print(f"\n  {code} ({sym}) {zone} {res} PnL={pnl:+.1f}%  MxGain={track['max_gain']:+.1f}% @d{track['day_max_gain']}  MxDD={track['max_dd']:+.1f}% @d{track['day_max_dd']}")
    # Signals timeline (sorted by day)
    events = []
    for sn in ALL_SIGNAL_NAMES:
        day = track[f'{sn}_day']
        if day > 0:
            dd = track[f'{sn}_dd']
            events.append((day, sn, dd))
    events.sort(key=lambda x: x[0])
    if events:
        tl = "    Timeline: "
        parts = [f"d{day}:{sn}({dd:+.1f}%)" for day, sn, dd in events[:8]]
        tl += " → ".join(parts)
        if len(events) > 8: tl += f" ... (+{len(events)-8} more)"
        print(tl)
    else:
        print("    Timeline: (no exit signals fired)")
    # DD curve (compact: show d1, d3, d5, d7, d10, d14, d20, d30)
    curve = track['dd_curve']
    checkpoints = [1, 3, 5, 7, 10, 14, 20, 30]
    dd_str = "    DD curve: "
    for cp in checkpoints:
        if cp <= len(curve):
            dd_str += f"d{cp}:{curve[cp-1]:+.1f}% "
    print(dd_str)

def print_best_combos(trades_results):
    """Find best 2-signal combinations."""
    print(f"\n{S}\n  BEST 2-SIGNAL COMBOS (both fire within 10 days → exit)\n{S}")
    valid = [t for t in trades_results if t['track']]
    combos = []
    for i, s1 in enumerate(ALL_SIGNAL_NAMES):
        for s2 in ALL_SIGNAL_NAMES[i+1:]:
            both_fired = []
            for t in valid:
                tr = t['track']
                d1 = tr[f'{s1}_day']; d2 = tr[f'{s2}_day']
                if 0 < d1 <= 10 and 0 < d2 <= 10:
                    both_fired.append(t)
            if len(both_fired) < 3: continue
            n_lose = sum(1 for t in both_fired if t['result'] == 'lose')
            accuracy = n_lose / len(both_fired) * 100
            avg_exit_day = np.mean([min(t['track'][f'{s1}_day'], t['track'][f'{s2}_day']) for t in both_fired])
            combos.append((s1, s2, len(both_fired), accuracy, avg_exit_day))

    combos.sort(key=lambda x: (-x[3], x[4]))
    print(f"  {'Combo':<35} {'#Trades':>7} {'LoseRate':>9} {'AvgDay':>7}")
    print(f"  {S2}")
    for s1, s2, n, acc, day in combos[:15]:
        print(f"  {s1}+{s2:<20} {n:>7} {acc:>8.0f}% {day:>6.1f}d")

def print_dd_probability(trades_results):
    """DD probability curve by day."""
    print(f"\n{S}\n  DRAWDOWN PROBABILITY BY DAY (P(DD > threshold) at day N)\n{S}")
    valid = [t for t in trades_results if t['track']]
    print(f"  {'Day':>4}", end='')
    thresholds = [-3, -5, -7, -10, -15]
    for th in thresholds:
        print(f"  {'DD>'+str(th)+'%':>8}", end='')
    print(f"  {'AvgDD':>8}")
    print(f"  {S2}")
    for day in [1, 2, 3, 5, 7, 10, 14, 20, 30]:
        probs = []
        dds = []
        for t in valid:
            curve = t['track']['dd_curve']
            if day <= len(curve):
                # Min DD up to this day
                min_dd = min(curve[:day])
                dds.append(min_dd)
        if not dds: continue
        print(f"  d{day:>3}", end='')
        for th in thresholds:
            p = sum(1 for d in dds if d < th) / len(dds) * 100
            probs.append(p)
            print(f"  {p:>7.0f}%", end='')
        avg = np.mean(dds)
        print(f"  {avg:>7.1f}%")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    _lf = open(OUTPUT_FILE, "w", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, _lf)

    print(f"{S}\n  EXIT SIGNAL PREDICTION — Multi-dimensional Analysis\n{S}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Data: {LOOKBACK_DAYS} days lookback, {FWD_BARS} bars forward tracking\n")

    # 1. Read trade journal
    tdf = pd.read_csv(TRADE_CSV)
    symbols = sorted(tdf['symbol'].unique())
    print(f"  Trades: {len(tdf)} | Symbols: {len(symbols)} | {', '.join(symbols)}")

    # Date range for fetching
    earliest = pd.to_datetime(tdf['buy_date']).min()
    latest = pd.to_datetime(tdf['buy_date']).max()
    fetch_start = (earliest - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    fetch_end = (latest + timedelta(days=120)).strftime("%Y-%m-%d")
    print(f"  Fetch range: {fetch_start} → {fetch_end}\n")

    # 2. Fetch VNINDEX
    print("  Fetching VNINDEX...", end=' ', flush=True)
    bc_df = fetch(BENCHMARK, fetch_start, fetch_end)
    if bc_df is None:
        print("FAILED"); return
    bc_map = dict(zip(bc_df['date'], bc_df['close'].values.astype(float)))
    vni_signals = compute_vni_signals(bc_df)
    print(f"OK ({len(bc_df)} bars)")
    time.sleep(API_SLEEP)

    # 3. Fetch all stocks
    all_stock_data = {}
    for sym in symbols:
        print(f"  Fetching {sym}...", end=' ', flush=True)
        df = fetch(sym, fetch_start, fetch_end)
        if df is None or len(df) < 260:
            print(f"SKIP ({len(df) if df is not None else 0} bars)")
            time.sleep(API_SLEEP); continue
        O = df['open'].values.astype(float); H = df['high'].values.astype(float)
        L = df['low'].values.astype(float); C = df['close'].values.astype(float)
        V = df['volume'].values.astype(float)
        dates = df['date'].tolist()
        date_map = {d: i for i, d in enumerate(dates)}

        # Align benchmark + compute RS
        bc_aligned = align_bc(dates, bc_map)
        rs_norm = calc_rs_norm(C, bc_aligned)

        # Compute micro signals
        micro_sig = compute_micro_signals(O, H, L, C, V, rs_norm)

        all_stock_data[sym] = {
            'df': df, 'O': O, 'H': H, 'L': L, 'C': C, 'V': V,
            'dates': dates, 'date_map': date_map,
            'rs_norm': rs_norm, 'micro_sig': micro_sig,
        }
        print(f"OK ({len(df)} bars, RS range: {np.nanmin(rs_norm):.0f}-{np.nanmax(rs_norm):.0f})")
        time.sleep(API_SLEEP)

    # 4. Compute sector weakness for each stock
    for sym, sd in all_stock_data.items():
        sd['sector_weak'] = compute_sector_weakness(
            sym, sd['dates'], sd['C'], all_stock_data, bc_map)

    # 5. Track each trade forward
    print(f"\n{S}\n  FORWARD TRACKING ({FWD_BARS} bars per trade)\n{S}")
    trades_results = []
    for _, row in tdf.iterrows():
        sym = row['symbol']; buy_date_str = row['buy_date']
        buy_date = datetime.strptime(buy_date_str[:10], "%Y-%m-%d").date()

        if sym not in all_stock_data:
            trades_results.append({
                'code': row['code'], 'symbol': sym, 'type': row['type'],
                'result': row['result'], 'pnl': row['pnl'], 'buy_date': buy_date_str,
                'track': None
            })
            continue

        sd = all_stock_data[sym]
        dm = sd['date_map']
        # Find entry bar (exact date or next available)
        entry_bar = None
        for d in sd['dates']:
            if d >= buy_date:
                entry_bar = dm[d]; break
        if entry_bar is None:
            trades_results.append({
                'code': row['code'], 'symbol': sym, 'type': row['type'],
                'result': row['result'], 'pnl': row['pnl'], 'buy_date': buy_date_str,
                'track': None
            })
            continue

        track = track_trade(
            entry_bar, sd['C'], sd['H'], sd['L'],
            sd['micro_sig'], vni_signals, sd['dates'],
            sd['sector_weak']
        )
        trades_results.append({
            'code': row['code'], 'symbol': sym, 'type': row['type'],
            'result': row['result'], 'pnl': row['pnl'], 'buy_date': buy_date_str,
            'sector': STOCK_SECTOR.get(sym, 'Misc'),
            'track': track
        })

    # 6. Signal statistics
    all_stats = compute_statistics(trades_results)
    print_signal_table(all_stats, "OVERALL EXIT SIGNAL STATISTICS (all 34 trades)")

    for zone in ['atl', 'btl']:
        zs = compute_zone_stats(trades_results, zone)
        if zs:
            n_zone = len([t for t in trades_results if t['type'] == zone])
            print_signal_table(zs, f"{zone.upper()} ZONE ({n_zone} trades)")

    # 7. Best combos
    print_best_combos(trades_results)

    # 8. DD probability curve
    print_dd_probability(trades_results)

    # Per-zone DD probability
    for zone in ['atl', 'btl']:
        filtered = [t for t in trades_results if t['type'] == zone and t['track']]
        if filtered:
            print(f"\n  {zone.upper()} zone ({len(filtered)} trades):")
            for day in [1, 3, 5, 7, 10, 14, 20]:
                dds = []
                for t in filtered:
                    curve = t['track']['dd_curve']
                    if day <= len(curve): dds.append(min(curve[:day]))
                if dds:
                    p5 = sum(1 for d in dds if d < -5)/len(dds)*100
                    p10 = sum(1 for d in dds if d < -10)/len(dds)*100
                    print(f"    d{day:>2}: P(DD>5%)={p5:.0f}%  P(DD>10%)={p10:.0f}%  AvgDD={np.mean(dds):.1f}%")

    # 9. Trade timelines
    print(f"\n{S}\n  DETAILED TRADE TIMELINES\n{S}")

    # Sort: losers first (most negative PnL), then winners
    sorted_trades = sorted(trades_results, key=lambda t: t['pnl'])
    for t in sorted_trades:
        if t['track']:
            print_trade_timeline(t, t['track'])

    # 10. Recommendations
    print(f"\n{S}\n  KHUYẾN NGHỊ EXIT STRATEGY\n{S}")
    ranked = sorted(all_stats.items(), key=lambda x: -x[1]['score'])
    top3 = [sn for sn, st in ranked if st['score'] > 0][:3]
    print(f"  Top 3 signals (by composite score): {', '.join(top3)}")
    for sn in top3:
        st = all_stats[sn]
        print(f"    {sn}: accuracy={st['accuracy']:.0f}%, avg fire day={st['avg_day']:.1f}, "
              f"DD at fire={st['avg_dd_at_fire']:.1f}%, avoidable DD={st['avg_avoidable_dd']:.1f}%")

    # Zone-specific recommendations
    for zone in ['atl', 'btl']:
        zs = compute_zone_stats(trades_results, zone)
        if zs:
            zr = sorted(zs.items(), key=lambda x: -x[1]['score'])
            zt = [sn for sn, st in zr if st['score'] > 0][:3]
            print(f"\n  {zone.upper()} best: {', '.join(zt)}")
            for sn in zt:
                st = zs[sn]
                print(f"    {sn}: accuracy={st['accuracy']:.0f}%, day={st['avg_day']:.1f}, "
                      f"DD@fire={st['avg_dd_at_fire']:.1f}%")

    # VNI distribution days insight
    d9_trades = [t for t in trades_results if t['track'] and t.get('sector')]
    d9_vni = []
    for t in d9_trades:
        bd = datetime.strptime(t['buy_date'][:10], "%Y-%m-%d").date()
        vs = vni_signals.get(bd, {})
        d9_vni.append((t, vs.get('vni_dist25', 0)))
    if d9_vni:
        hi_dist = [t for t, d in d9_vni if d >= 8]
        lo_dist = [t for t, d in d9_vni if d < 5]
        if hi_dist:
            lr = sum(1 for t in hi_dist if t['result'] == 'lose') / len(hi_dist) * 100
            print(f"\n  ⚠ VNI DistDays≥8 at entry: {len(hi_dist)} trades, {lr:.0f}% lose rate")
        if lo_dist:
            lr = sum(1 for t in lo_dist if t['result'] == 'lose') / len(lo_dist) * 100
            print(f"  ✓ VNI DistDays<5 at entry: {len(lo_dist)} trades, {lr:.0f}% lose rate")

    # 11. Export CSV
    rows = []
    for t in trades_results:
        r = {'code': t['code'], 'symbol': t['symbol'], 'type': t['type'],
             'result': t['result'], 'pnl': t['pnl'], 'buy_date': t['buy_date'],
             'sector': t.get('sector', '')}
        if t['track']:
            tr = t['track']
            r['max_gain'] = tr['max_gain']; r['max_dd'] = tr['max_dd']
            r['day_max_gain'] = tr['day_max_gain']; r['day_max_dd'] = tr['day_max_dd']
            for sn in ALL_SIGNAL_NAMES:
                r[f'{sn}_day'] = tr[f'{sn}_day']
                r[f'{sn}_dd'] = tr[f'{sn}_dd']
        rows.append(r)
    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Saved: {OUTPUT_CSV}")
    print(f"  Report: {OUTPUT_FILE}")
    print(f"\n{S}\n  DONE\n{S}")

    _lf.close()
    sys.stdout = sys.__stdout__
    print(f"Exit signal analysis complete. See {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
