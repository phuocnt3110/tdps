# Minervini Complete System - Hướng dẫn Panel

## Tổng quan

Indicator này dựa trên phương pháp của **Mark Minervini** - nhà vô địch US Investing Championship. Panel hiển thị đánh giá theo 3 tầng (Tier) và 1 phần phụ cho quản lý vị thế.

---

## 📋 CẤU TRÚC PANEL

```
VIC  |  D  |  2025/3/18          ← Header (Symbol, Timeframe, Date)
O:25.3 H:26.1 L:25.0 C:25.8  |  Vol:1234K  B/S:62/38%  Avg:890K
                                ← OHLC + Volume + Chaikin Buy/Sell %
★★ READY ★★                      ← Verdict (Kết luận tổng hợp)
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 TREND  A+  (10/10)            ← TIER 1: Trend Template
...
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 SETUP:  VCP                   ← TIER 2: Setup Quality
...
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 ENTRY:  BUY!  (A+)            ← TIER 3: Entry Timing
...
┌─ PULLBACK BUY ──────            ← (hiển thị khi có pullback buy)
│ Support: EMA10=X  Pivot=Y
└────────────────────────────
┌─ LOW-CHEAT PIVOT ──────        ← (hiển thị khi có low-cheat)
│ Contraction: X ~ Y (Z%)
└────────────────────────────
┌─ STOP REF (3/4 methods ≤8%)    ← Stop Loss Reference
...
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TREND HEALTH (If Holding)     ← Phụ: Quản lý vị thế
...
```

---

## 🎯 VERDICT (Kết luận tổng hợp)

| Verdict | Code | Điều kiện | Hành động |
|---------|------|-----------|-----------|
| **★★★ ATL BUY ★★★** | `anyBuyNow_RT` | Breakout + Volume + RS + Stop OK | MUA NGAY |
| **★★★ ATL PULLBACK BUY ★★★** | `isPullbackBuyNow_RT` | Post-breakout pullback to support | 🟢 MUA - Pullback |
| **★★★ ATL LOW-CHEAT ★★★** | `isLowCheatNow_RT` | Buy at VCP contraction low | 🟢 MUA - Low-Cheat |
| **★★ ATL HOLD ★★** | `isAddHold` | Đã breakout, trong buy zone | GIỮ hoặc THÊM |
| **★★ ATL READY ★★** | `isReadyToBuy` | Gần pivot + Chờ breakout | SẴN SÀNG, chờ tín hiệu |
| **○ ATL WATCH ○** | `isQualified` | Tier 1+2 qualified, chờ entry | THEO DÕI |
| **◆ ATL FORMING ◆** | `isSuperStockWatch OR isWatchlist` | Setup đang hình thành | THEO DÕI |
| **-- SKIP --** | None of above | Không đạt | BỎ QUA |

### SUPER STOCK - Định nghĩa chi tiết

#### Super Stock Candidate (◇ SUPER STOCK? ◇)
```pine
superStockCandidate = rsVeryStrong AND isStage2OK AND condPriceAboveAll AND (condMaStacked OR rsExtreme)
```

| Điều kiện | Code | Giá trị |
|-----------|------|---------|
| RS Very Strong | `rsNorm >= 90` | Top 10% RS |
| Stage 2 OK | `trendScore >= 5` | Trend score ≥5/10 |
| Price Above All | `close > ma50 AND close > ma150 AND close > ma200` | Giá trên tất cả MA |
| MA Stacked | `ma50 > ma150 > ma200` | MA xếp chồng đúng |
| OR RS Extreme | `rsNorm >= 95` | Top 5% RS (nới lỏng MA stacking) |

#### RS-Based Qualified (★★★ BUY NOW [RS] ★★★)
```pine
rsBasedQualified = superStockCandidate AND patternScore >= 50
```
> **Ý nghĩa:** Khi RS ≥90 + setup OK (score ≥50), có thể override strict Tier 1+2 requirements. Đây là triết lý của Minervini: RS ranking là yếu tố quan trọng nhất.

### RS Weak - Điều kiện chặn Entry

```pine
rsWeak = rsNorm < 70  // Bottom 30% RS - BLOCK ENTRY
```

| Điều kiện | Code | Hậu quả |
|-----------|------|----------|
| RS Weak | `rsNorm < 70` | **CHẶN BUY NOW và ADD/HOLD** |
| RS Strong | `rsNorm >= 80` | Đủ điều kiện cơ bản |
| RS Very Strong | `rsNorm >= 90` | Super Stock candidate |

> **Minervini:** "I want to buy stocks that are **leaders**, not laggards. RS ranking should be at least 80, preferably 90+."

---

## 🏛️ MARKET TIMING (Mới)

Phần này giúp đánh giá **sức khỏe thị trường chung** theo triết lý của William O'Neil và Mark Minervini.

### Distribution Day (Ngày phân phối)

| Điều kiện | Code | Giá trị |
|-----------|------|----------|
| Index giảm | `benchChange <= -0.2%` | Index giảm ≥0.2% |
| Volume tăng | `benchVolume > benchVolume[1]` | Volume cao hơn ngày trước |
| **Kết luận** | `benchChange <= -0.2 AND volume up` | |

> **Ý nghĩa:** Smart money đang bán ra. Đếm số ngày phân phối trong 25 ngày gần nhất.

### Distribution Day Count

| Số lượng | Trạng thái | Hành động |
|----------|-----------|------------|
| 0-2 | **HEALTHY** | An toàn để mua |
| 3-4 | **CAUTION** | Cẩn thận, giảm size |
| 5+ | **HIGH RISK** | Giảm exposure, chờ correction |

### Follow-through Day (Ngày xác nhận rally)

| Điều kiện | Code | Giá trị |
|-----------|------|----------|
| Ngày 4-10 | `rallyDayCount >= 4 AND <= 10` | Sau đáy correction |
| Index tăng | `benchChange >= 1.25%` | Tăng ≥1.25% |
| Volume tăng | `benchVolume > benchVolume[1]` | Volume cao hơn ngày trước |
| **Kết luận** | Tất cả điều kiện trên | |

> **Ý nghĩa:** Tín hiệu xác nhận uptrend mới sau correction. Mọi bull market đều bắt đầu bằng FTD.

---

## 📊 FUNDAMENTALS (Mới)

Phần này độc lập với phân tích kỹ thuật, dựa trên triết lý của Minervini:
> *"Earnings are the most important fundamental factor."*

### Các chỉ số

| Chỉ số | Định nghĩa | Minervini Target |
|--------|-----------|------------------|
| **EPS** | Earnings Per Share (lợi nhuận trên cổ phiếu) | > 0 (dương) |
| **EPS Growth** | Tăng trưởng EPS so với quý trước | ≥25% QoQ |
| **Revenue (Rev)** | Doanh thu | Tăng trưởng |
| **Rev Growth** | Tăng trưởng doanh thu | ≥20% QoQ |
| **P/E Ratio** | Price / Earnings TTM | Tham khảo |
| **PEG Ratio** | P/E / EPS Growth Rate | < 1.5 (lý tưởng < 1) |
| **Surprise** | (Actual - Estimate) / Estimate * 100% | > 0% (Beat) |

### PEG Ratio - Chi tiết

**Công thức:** `PEG = P/E Ratio / EPS Growth Rate`

| PEG | Đánh giá | Điểm | Ký hiệu |
|-----|----------|------|----------|
| < 1.0 | **Undervalued** - Lý tưởng | 15 | ✓✓ |
| < 1.5 | Acceptable | 10 | ✓ |
| < 2.0 | Fair | 0 | |
| ≥ 2.0 | **Overvalued** - Cảnh báo | 0 | ⚠ |

> **Minervini:** "PEG < 1 means you're getting growth at a reasonable price."

### Earnings Surprise - Chi tiết

**Công thức:** `Surprise = (EPS Actual - EPS Estimate) / |EPS Estimate| * 100%`

| Surprise | Đánh giá | Ký hiệu |
|----------|----------|----------|
| > 0% | **Beat** - Vượt kỳ vọng | ✓Beat |
| = 0% | Meet - Đúng kỳ vọng | |
| < 0% | **Miss** - Dưới kỳ vọng | ⚠ |

> **Ý nghĩa:** Cổ phiếu beat earnings thường có momentum tốt hơn. Minervini ưu tiên mua cổ phiếu liên tục beat kỳ vọng.

### Fundamental Score

| Tiêu chí | Điều kiện | Điểm |
|----------|-----------|------|
| EPS dương | `epsQ > 0` | 20 |
| EPS Growth ≥25% | `epsGrowthQoQ >= 25` | 25 |
| EPS Accelerating | `epsGrowthQoQ >= 40` | 10 |
| Rev Growth ≥20% | `revGrowthQoQ >= 20` | 20 |
| Rev Accelerating | `revGrowthQoQ >= 30` | 10 |
| PEG < 1 | `pegRatio < 1` | 15 |
| PEG < 1.5 | `pegRatio < 1.5` | 10 |
| **Tổng tối đa** | | **100** |

### Fundamental Grade

| Grade | Score | Đánh giá |
|-------|-------|----------|
| **A+** | ≥80 | EXCELLENT |
| **A** | ≥60 | GOOD |
| **B** | ≥40 | FAIR |
| **C** | ≥20 | WEAK |
| **F** | <20 | N/A |

> **Lưu ý:** Dữ liệu fundamental có thể không khả dụng cho tất cả mã chứng khoán Việt Nam.

---

## ⚙️ INPUT SETTINGS

| Setting | Default | Ghi chú |
|---------|---------|---------|
| **Benchmark (RS)** | HOSE:VNINDEX | Chỉ số để tính RS |
| **Near 52W High Threshold %** | 25 | Ngưỡng "gần đỉnh" |
| **Bars for 52 weeks** | 252 | Số phiên trong 1 năm |
| **Base Length (bars)** | 30 | Độ dài base |
| **ATR Length** | 14 | Chu kỳ ATR |
| **T-Segment Length** | 7 | Độ dài segment cho T-count |
| **Pivot Lookback** | 5 | Lookback cho pivot |
| **HTF Min Prior Gain %** | 80 | Gain tối thiểu cho HTF |
| **Show MA20** | ✅ | Hiển thị MA20 |
| **Show MA50** | ✅ | Hiển thị MA50 |
| **Show MA150** | ❌ | Hiển thị MA150 (có thể nén chart) |
| **Show MA200** | ❌ | Hiển thị MA200 (có thể nén chart) |
| **Show Entry/Pivot** | ✅ | Hiển thị điểm pivot |
| **Show Stop/TP levels** | ❌ | Hiển thị stop/TP (có thể nén chart) |

---

## ⚠️ ÁP DỤNG CHO THỊ TRƯỜNG KHÁC (Crypto, Forex, etc.)

### Triết lý Minervini có áp dụng được không?

**CÓ THỂ**, nhưng cần hiểu các hạn chế:

| Yếu tố | Stock (Tối ưu) | Crypto | Vấn đề khi dùng với Crypto |
|--------|----------------|--------|----------------------------|
| **Benchmark** | VNINDEX, S&P500 | BTC.D, Total Market Cap | ⚠️ Hiện tại dùng VNINDEX → RS không chính xác |
| **RS Calculation** | So với index | Cần so với BTC hoặc Total MC | Market: Weak dù BTC rally |
| **Volatility** | 1-3% daily | 5-15% daily | Các ngưỡng % cần điều chỉnh |
| **Base patterns** | 3-8 tuần | 1-2 tuần | VCP, Cup khó nhận diện |
| **52W metrics** | Ổn định | Biến động cực mạnh | Đỉnh/đáy 52W ít relevant |

### Vấn đề thường gặp với Crypto

| Hiện tượng | Nguyên nhân | Giải pháp |
|------------|-------------|-----------|
| **Market: Weak** dù coin rally | Benchmark là VNINDEX | Đổi benchmark sang BTC.D hoặc ignore |
| **NO SETUP** với Score thấp | Parabolic moves không match VCP | Chấp nhận - pattern detection không phù hợp |
| **SUPER STOCK?** không chuyển BUY | Pattern score < 50 | Dựa vào RS và price action thay vì indicator |

### Khuyến nghị khi dùng với Crypto

1. **Tập trung vào TREND (Tier 1):** MA structure vẫn hoạt động
2. **Bỏ qua SETUP score:** Pattern detection cho stock, không cho crypto
3. **RS không chính xác:** Ignore hoặc đổi benchmark
4. **Exit signals vẫn hữu ích:** Climax Top, RS Divergence vẫn có giá trị

> **Kết luận:** Indicator được tối ưu cho **Vietnam Stock Market**. Với crypto, chỉ nên tham khảo TREND và EXIT signals, không nên dựa vào SETUP và ENTRY scoring.

---

## 📚 THAM KHẢO

- **Mark Minervini**: "Trade Like a Stock Market Wizard"
- **Mark Minervini**: "Think & Trade Like a Champion"
- **SEPA Method**: Specific Entry Point Analysis
- **VCP**: Volatility Contraction Pattern

---

## 📈 PHÂN TÍCH DỮ LIỆU THỰC TẾ (vnstock)

Dựa trên phân tích 16 ATL trades (01/2026 - 03/2026) bằng vnstock VCI:

### Kết quả tổng quan

| Metric | Giá trị |
|--------|--------|
| Win Rate | **50%** (8/16) |
| Avg PnL | +0.31% |
| Win Avg | +8.97% |
| Lose Avg | -8.34% |

### Chỉ số phân biệt Win vs Lose

| Metric | WIN | LOSE | Sig |
|--------|-----|------|-----|
| Gap% | 0.5% | 1.3% | ★★ |
| MaxGain% | 14.4% | 4.4% | ★★ |
| MaxDD% | -4.6% | -12.1% | ★★ |
| 7dRet% | +2.8% | -8.0% | ★★ |
| T+1 Ret% | +3.8% | -2.7% | ★★ |
| DistDays/25 | 5.4 | 6.8 | ★ |

### Quy tắc rút ra từ data

1. **KHÔNG MUA** nếu Gap% > 2% (POW 4.8%, CTG 3.1% - cả hai thua)
2. **Volume ratio > 3x** cũng là dấu hiệu tiêu cực (PVB 4.2x, POW 3.4x - thua)
3. **Distribution Days ≥ 7** → tránh entry mới
4. **CắT LỖ** nếu MaxDD > 8% trong tuần đầu
5. **T+1 âm > 2%** → cân nhắc cắt sớm

---

## 📉 VOLUME MỚI: Chaikin Buy/Sell

### Công thức

```
Buy Volume  = Volume × (Close - Low)  / (High - Low)
Sell Volume = Volume × (High - Close) / (High - Low)
Buy%  = Buy Volume / Total Volume × 100
Sell% = 100 - Buy%
```

### Hiển thị trên Panel Header

```
VIC | D | 2025/3/18
O:25.3 H:26.1 L:25.0 C:25.8  |  Vol:1234K  B/S:62/38%  Avg:890K
```

- **B/S**: Buy%/Sell% theo Chaikin approximation
- **Avg**: Volume trung bình 20 phiên (MA20)
- Buy% > 60% = áp lực mua mạnh
- Buy% < 40% = áp lực bán mạnh

---

## 🆕 PULLBACK BUY & LOW-CHEAT PIVOT

### Pullback Buy (Minervini: first normal pullback after breakout)

| Điều kiện | Giá trị |
|-----------|--------|
| Breakout đã xảy ra | 2-10 bars trước |
| Giá pullback về pivot | ≤ pivot +3% |
| Giữ trên support | ≥ EMA10 hoặc pivot -3% |
| Volume dry-up | < 70% vol MA50 |
| Nến bounce | Close > Open, Close > Close[1] |
| Market bullish | Benchmark > MA50 |
| **Stop max** | **5%** (chặt hơn breakout 8%) |

### Low-Cheat Pivot (Minervini: buy at bottom of last VCP contraction)

| Điều kiện | Giá trị |
|-----------|--------|
| VCP confirmed | T-count ≥ 2 |
| Giá tại contraction low | ≤ contraction low +2% |
| Volume dry-up | volMA20 < volMA50 × 0.8 |
| Tight action | tightnessRatio < 0.9 |
| Contraction range | ≤ 8% |
| **Stop max** | **4%** (rất chặt, best R:R) |

### So sánh 3 loại Entry

| | Breakout | Pullback Buy | Low-Cheat Pivot |
|--|----------|-------------|----------------|
| **Timing** | Tại breakout | Sau breakout 2-10 bars | Trước breakout |
| **Stop** | ≤8% | ≤5% | ≤4% |
| **Grade** | A+ | A | A- |
| **R:R** | Tốt | Tốt hơn | Tốt nhất |
| **Win Rate** | Cao nhất | Cao | Trung bình (cần breakout xác nhận) |
| **Bar Color** | Lime | Teal | Blue |

---

## 🔍 BTL REFERENCE INDICATORS (Mới v3.1)

Các chỉ báo tham khảo hiển thị trong BTL Entry section - **chỉ tham khảo, không phải điều kiện mua**:

### Vol/7d (Volume Ratio so với trung bình 7 ngày)

**Công thức**: `Volume hôm nay / SMA(Volume, 7)`

| Giá trị | Đánh giá | Ký hiệu |
|---------|----------|----------|
| ≤ 0.7x | **Quiet accumulation** - Winners BTL thường mua ở volume thấp | ✓quiet |
| 0.7x - 1.3x | Bình thường | (trống) |
| > 1.3x | **Volume cao** - Có thể là distribution trong downtrend | ⚠high |

> **Data**: BTL winners có Vol/7d = 0.62x, losers = 1.27x

### Pre-7d (Pre-Momentum 7 ngày)

**Công thức**: `(Close - Close[7]) / Close[7] × 100`

| Giá trị | Đánh giá | Ký hiệu |
|---------|----------|----------|
| ≤ 7% | **Chưa extended** - Còn room to run | ✓ |
| 7% - 10% | Tạm chấp nhận | ~OK |
| > 10% | **Extended** - Giá đã chạy xa, dễ bị pullback | ⚠extended |

> **Data**: BTL winners có Pre-7d = 7.2%, losers = 12.1%

### Candle (Màu nến ngày mua)

| Giá trị | Đánh giá | Ký hiệu |
|---------|----------|----------|
| RED | Mua ngày giảm - quiet accumulation | ✓ |
| GREEN | Mua ngày tăng | (trống) |

> **Data**: 100% BTL winners mua ngày nến đỏ

---

*Tài liệu này được tạo cho Minervini Complete System v3.1 (cập nhật 03/2026)*
