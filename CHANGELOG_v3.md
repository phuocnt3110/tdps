# TDPS v3 — VN Market Calibration & Parabolic Launch

## Summary
v3 calibrates pattern detection thresholds for the Vietnamese market based on empirical analysis of 44 stocks over 1 year (2025-03–2026-03). Adds a new **PARABOLIC LAUNCH** pattern for explosive momentum stocks.

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

### D. Component Score Updates

- `baseScore`: Adjusted breakpoints for VN depths (20/30/40/50)
- `volScore`: Added `volSuperDry` bonus tier (15 pts vs 10 for regular volDryUp)
- `tightScore`: Adjusted breakpoints (0.7/1.0/1.3) matching new thresholds

### E. Files Modified

- `minervini_complete_vnstock.pine` — Main indicator (all changes)
- `minervini_backtest_vnstock.pine` — Backtest (synced pattern detection + thresholds)

## Data Source

Calibration based on `calibrate_vn_patterns.py` analyzing 44 Vietnamese stocks:
DPM, DCM, GSP, GMD, NAF, EVF, OIL, POW, BFC, PAC, PLX, MSR, MWG, PVT, PVD, BSR, NT2, PVS, PVC, BIG, DGW, HPG, SZC, CTD, BIC, PVB, VHC, PNJ, HHP, DCL, NDN, BAF, TTF, FIT, G36, HAG, PHR, CTG, HDB, STB, MST, GTD, TIN, CET

**Key findings:**
- 682 breakouts analyzed, 198 good (>10% T+30), 106 great (>20% T+30)
- v2 pattern detection: 81% classified as FLAT/ASC, only 0.6% as VCP/HTF/Cup
- FORMING + NONE categories (missed by v2) had 3-5x higher returns than detected patterns
- Deep bases (35-65%) showed best forward returns despite being penalized in v2
