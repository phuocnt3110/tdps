# TDPS v3 — Multi-Market Calibration & Parabolic Launch

## Summary
v3 calibrates pattern detection thresholds for 3 markets (VN, US, Crypto) based on Minervini SEPA philosophy adapted to each market's characteristics. Adds **PARABOLIC LAUNCH** pattern, ETL bar coloring fix, and dead code cleanup.

## Changes Applied

### A. VN-Calibrated Thresholds

| Metric | v2 (US default) | v3 (VN calibrated) | Rationale |
|---|---|---|---|
| **Tightness (isTight)** | < 0.9 | < 1.3 | Median VN breakout = 1.2; only 11% met old threshold |
| **Tightness (Cup)** | < 0.85 | < 1.2 | Enable Cup pattern detection in VN |
| **Tightness (HTF)** | < 0.6 | < 0.8 | Still tight, but achievable in VN |
| **Tightness (Power Play)** | < 0.5 | < 0.7 | Slightly relaxed for VN volatility |
| **Volume Dry-up** | MA20/MA50 < 0.8 | < 1.0 | Only 7.4% of breakouts met old threshold |
| **Volume Super Dry** | N/A | < 0.7 | New bonus tier for true supply exhaustion |
| **HTF Min Prior Gain** | 80% | 40% | P75 of good breakouts = 48%; 80% virtually impossible in VN |
| **Flat Base max depth** | 15% | 20% | Median VN base depth = 18.5% |
| **VCP/Ascending depth** | 35% | 40% | Good breakouts P75 = 27%, but 30-40% still valid |

### B. VCP Redesign (Hybrid)

- **New input**: `vcpBaseLen = 60` (separate from `baseLen = 30`)
- VCP pattern now uses 60-bar lookback for base depth measurement
- Allows multi-stage VCP contractions that don't fit in 30 bars
- T-Count (SMA proxy) kept as primary detection method
- Other patterns still use `baseLen = 30`

### C. PARABOLIC LAUNCH Pattern (New)

Designed for stocks like GTD, CET, TIN with explosive moves from deep bases.

**Conditions (all must be true):**

| Condition | Threshold | Validated |
|---|---|---|
| RS Ranking | >= 90 | Filters out weak momentum |
| RS Acceleration | >= 30 pts in 10 bars | GTD: 15→100, CET: 12→100 |
| Volume Explosion | >= 200% of MA20 (any of 3 recent bars) | GTD: 682%, CET: 588% |
| Price Momentum | >= 3 up days in last 5 | GTD: 8 consecutive up |
| Consecutive 5%+ gains | >= 2 consecutive days with >= 5% gain | Reduces false positives (BIG, TTF) |
| Zone | ATL (barsSinceATL <= 15) or ETL | GTD: ATL, CET: ETL→ATL |
| Trend Score | >= 7 | Filters weak trend structure |
| Deep Base | vcpBaseDepth >= 35% (60-bar lookback) | GTD: 52%, CET: 50% |

**Pattern Score**: 75 base + 10 RS bonus (RS>=90 always true) = **85 final**
- Exceeds `tier12Qualified` threshold (77)
- Exceeds `rsBasedQualified` threshold (50)

### D. PL + Climax Top Conflict Resolution

**Problem**: PARABOLIC LAUNCH fires every day during a parabolic move, but CLIMAX TOP also fires from Day 2+. This creates conflicting BUY + exhaustion warnings.

**Analysis (BIG & GTD)**:

| Entry | Climax? | Crash low vs stop | Result |
|---|---|---|---|
| GTD Day 1 (no Climax) | No | 48,800 > 36,828 | **+23% even at crash low** |
| GTD Day 2 (Climax) | Yes | 48,800 > 42,315 | Risky but OK |
| GTD Day 3 (Climax) | Yes | 48,800 ≈ 48,546 | 0.5% margin! |
| GTD Day 4 (Climax) | Yes | 48,800 < 55,242 | **Stop hit, loss** |
| GTD Day 5 (Climax) | Yes | 48,800 < 62,310 | **Stop hit, big loss** |

**Solution**: When `isParabolicLaunch AND climaxTop` both true → suppress `freshBreakout`:
- Day 1 PL (no Climax Top) → BUY fires normally
- Day 2+ PL with Climax Top → BUY suppressed, shows "PARABOLIC CLIMAX" warning
- Entry conclusion: `"🔴 PARABOLIC CLIMAX - BUY suppressed! Vol X% = exhaustion risk"`

### E. Component Score Updates

- `baseScore`: Adjusted breakpoints for VN depths (20/30/40/50)
- `volScore`: Added `volSuperDry` bonus tier (15 pts vs 10 for regular volDryUp)
- `tightScore`: Adjusted breakpoints (0.7/1.0/1.3) matching new thresholds

### F. ETL Bar Coloring Fix

**Bug**: ETL BUY shows in panel but bars not colored green.

**Root cause**: `etlBuySignal` (confirmed) only fires on first bar via anti-repaint guard, but `etlBuySignal_RT` (panel) fires every bar where conditions persist.

**Fix**: Added `etlBuyTriggered` as aqua bar color for active ETL positions (mirrors ATL's `isAddHold`):
- ETL breakout bar → Lime
- ETL position active → Aqua
- ETL base → Yellow (60% transparent)

### G. Dead Code Cleanup

Removed 10 unused variables (~30 lines per file):
`sellVol`, `buyVolMA5`, `sellVolMA5`, `aboveLow30pct`, `patternColor` (12 assignments), `priceChange`, `rsChange10`, `rsAccelerating`, `regularBreakout`, `gapBreakout`

### H. File Renaming Convention

| Folder | Old Name | New Name |
|---|---|---|
| VN/ | `minervini_complete_vnstock.pine` | `vn_minervini_main.pine` |
| VN/ | `minervini_backtest_vnstock.pine` | `vn_minervini_backtest.pine` |
| VN/ | `rsline_vnstock.pine` | `vn_rsline.pine` |
| US/ | `minervini_complete_vnstock.pine` | `us_minervini_main.pine` |
| US/ | `minervini_backtest_vnstock.pine` | `us_minervini_backtest.pine` |
| US/ | `rsline_vnstock.pine` | `us_rsline.pine` |
| Crypto/ | `minervini_complete_vnstock copy.pine` | `crypto_minervini_main.pine` |
| Crypto/ | `minervini_backtest_vnstock copy.pine` | `crypto_minervini_backtest.pine` |
| Crypto/ | `rsline_vnstock copy.pine` | `crypto_rsline.pine` |

### I. US Market Calibration (Minervini Original)

US = Minervini's home market. Restored original thresholds from his books.

| Parameter | VN | US | Rationale |
|---|---|---|---|
| Benchmark | `HOSE:VNINDEX` | `SP:SPX` | S&P 500 standard for RS |
| HTF Min Gain | 40% | **80%** | Minervini original |
| Tightness (isTight) | < 1.3 | **< 0.9** | US bases are tighter |
| Vol Dry-up | < 1.0 | **< 0.8** | Deep US liquidity |
| HTF tightness | < 0.8 | **< 0.6** | Original |
| Cup tightness | < 1.2 | **< 0.85** | Original |
| PowerPlay tightness | < 0.7 | **< 0.5** | Original |
| Flat Base depth | ≤ 20% | **≤ 15%** | Minervini: 10-15% |
| Ascending depth | ≤ 40% | **≤ 35%** | Original |
| VCP depth | ≤ 40% | **≤ 35%** | Original |
| Base scoring | 20/30/40/50 | **12/20/30/40** | Tighter US bases |
| Tight scoring | 0.7/1.0/1.3 | **0.5/0.7/0.9** | Match original |
| Fundamentals | OFF | **ON** | US has best EPS data |

### J. Crypto Market Calibration

Crypto = extreme volatility, 24/7 market, no fundamentals. Thresholds expanded.

| Parameter | VN | Crypto | Rationale |
|---|---|---|---|
| Benchmark | `HOSE:VNINDEX` | `CRYPTOCAP:TOTAL` | Total crypto market cap |
| 52W Bars | 252 | **365** | 24/7 trading |
| HTF Min Gain | 40% | **100%** | Crypto super-cycles |
| Tightness (isTight) | < 1.3 | **< 1.5** | Higher daily volatility |
| Vol Dry-up | < 1.0 | **< 1.2** | Inconsistent volume |
| HTF tightness | < 0.8 | **< 1.0** | Wider range |
| Cup tightness | < 1.2 | **< 1.4** | Deeper cups normal |
| PowerPlay tightness | < 0.7 | **< 0.8** | Relaxed |
| Flat Base depth | ≤ 20% | **≤ 25%** | Crypto dips deeper |
| Ascending depth | ≤ 40% | **≤ 45%** | Wider ascending |
| VCP depth | ≤ 40% | **≤ 50%** | Wider contractions |
| Base scoring | 20/30/40/50 | **25/40/55/70** | Deep corrections normal |
| Tight scoring | 0.7/1.0/1.3 | **0.8/1.2/1.5** | Higher vol tolerance |
| Climax Top vol | 400% | **600%** | Crypto spikes bigger |
| Extended from MA20 | 7% | **12%** | Crypto trends farther |
| Distribution Day | -0.2% | **-1.0%** | Daily vol much higher |
| Follow-through Day | +1.25% | **+3.0%** | Needs bigger move |
| Darvas Max Width | 15% | **25%** | Wider boxes |
| RSI Oversold Lookback | 100 | **150** | Longer bear markets |
| Fundamentals | OFF | OFF | No EPS for crypto |

### K. Files Modified (Final)

**VN/** — `vn_minervini_main.pine`, `vn_minervini_backtest.pine`, `vn_rsline.pine`
**US/** — `us_minervini_main.pine`, `us_minervini_backtest.pine`, `us_rsline.pine`
**Crypto/** — `crypto_minervini_main.pine`, `crypto_minervini_backtest.pine`, `crypto_rsline.pine`

## Data Source

Calibration based on `calibrate_vn_patterns.py` analyzing 44 Vietnamese stocks:
DPM, DCM, GSP, GMD, NAF, EVF, OIL, POW, BFC, PAC, PLX, MSR, MWG, PVT, PVD, BSR, NT2, PVS, PVC, BIG, DGW, HPG, SZC, CTD, BIC, PVB, VHC, PNJ, HHP, DCL, NDN, BAF, TTF, FIT, G36, HAG, PHR, CTG, HDB, STB, MST, GTD, TIN, CET

**Key findings:**
- 682 breakouts analyzed, 198 good (>10% T+30), 106 great (>20% T+30)
- v2 pattern detection: 81% classified as FLAT/ASC, only 0.6% as VCP/HTF/Cup
- FORMING + NONE categories (missed by v2) had 3-5x higher returns than detected patterns
- Deep bases (35-65%) showed best forward returns despite being penalized in v2
