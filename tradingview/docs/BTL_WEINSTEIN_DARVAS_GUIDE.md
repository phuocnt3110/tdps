# BTL Mode - Hướng dẫn Weinstein-Darvas

## Tổng quan

**BTL (Below The Line)** là chế độ phân tích dành cho cổ phiếu **chưa đạt tiêu chuẩn Minervini** (giá chưa nằm trên các đường MA quan trọng). Thay vì bỏ qua những cổ phiếu này, BTL sử dụng phương pháp **Weinstein Stage Analysis** kết hợp **Darvas Box** để tìm điểm vào sớm khi cổ phiếu đang trong giai đoạn tích lũy hoặc chuẩn bị breakout.

---

## 1. WEINSTEIN STAGE ANALYSIS

### Stage là gì?

Stan Weinstein chia chu kỳ giá cổ phiếu thành 4 giai đoạn:

| Stage | Tên gọi | Đặc điểm | Hành động |
|-------|---------|----------|-----------|
| **Stage 1** | Basing (Tích lũy) | Giá đi ngang, MA30W phẳng | WATCH - Chờ đợi |
| **Stage 1→2** | Breakout | Giá vượt MA30W với volume | **BUY** |
| **Stage 2** | Advancing (Tăng) | Giá > MA30W, MA30W dốc lên | HOLD/ADD |
| **Stage 3** | Top (Đỉnh) | MA30W phẳng lại sau khi tăng | SELL |
| **Stage 4** | Decline (Giảm) | Giá < MA30W, MA30W dốc xuống | AVOID |

### Các chỉ báo Stage trong Panel

| Thuật ngữ | Ý nghĩa |
|-----------|---------|
| **MA30W (150d)** | Đường MA 30 tuần ≈ 150 ngày - đường quan trọng nhất của Weinstein |
| **Price: Above/Below** | Giá hiện tại so với MA30W |
| **Slope: Rising/Falling/Flat** | Độ dốc MA30W - xác định xu hướng |
| **Stage 1 Breakout** | Giá vừa vượt MA30W từ dưới lên với volume mạnh |

### Điểm Weinstein Score (0-100)

| Điều kiện | Điểm |
|-----------|------|
| Stage 1 (Basing) | +20 |
| Stage 2 (Advancing) | +30 |
| Stage 1→2 Breakout | +40 |
| Momentum ngắn hạn (Close > MA20, MA20 tăng) | +20 |
| Volume > Average | +10 |

**Grade:**
- A: ≥70 điểm
- B: ≥50 điểm  
- C: ≥30 điểm
- F: <30 điểm

---

## 2. DARVAS BOX

### Darvas Box là gì?

Nicolas Darvas phát triển phương pháp "box" để xác định vùng tích lũy và điểm breakout:

```
┌─────────────────────────┐
│      BOX HIGH           │ ← Kháng cự (Resistance)
│                         │
│    ████ PRICE ████      │ ← Giá dao động trong box
│                         │
│      BOX LOW            │ ← Hỗ trợ (Support)  
└─────────────────────────┘
```

### Các chỉ báo Darvas trong Panel

| Thuật ngữ | Ý nghĩa |
|-----------|---------|
| **Box High** | Đỉnh cao nhất trong 20 phiên gần nhất |
| **Box Low** | Đáy thấp nhất trong 20 phiên gần nhất |
| **Width** | Biên độ box = (High - Low) / Low × 100% |
| **Box Status** | Trạng thái: No Valid Box / Box Formed / In Breakout Zone / BOX BREAKOUT! |
| **Price Position** | Vị trí giá trong box (% từ đáy) |

### Box hợp lệ

- **Width 3% - 15%**: Box không quá rộng (biến động lớn) cũng không quá hẹp
- **✓**: Box hợp lệ
- **✗**: Box quá rộng hoặc quá hẹp

### Điểm Darvas Score (0-100)

| Điều kiện | Điểm |
|-----------|------|
| Valid Box (box hợp lệ) | +30 |
| Breakout + Volume confirm | +50 |
| Đang trong breakout zone (≤5% từ đỉnh box) | +30 |
| Giá ở 70% trên của box | +20 |

---

## 3. RSI/EMA SCORE (MỚI)

### Weekly RSI

**RSI Weekly** là RSI tính trên khung tuần - dùng để phát hiện trạng thái quá bán:

| Giá trị RSI | Trạng thái | Ý nghĩa |
|-------------|------------|---------|
| < 30 | **Oversold (OS)** | Quá bán - cơ hội mean reversion |
| 30-40 | Low | RSI thấp - có thể đang tích lũy |
| > 40 | Normal | Bình thường |

**Rec✓** = Recovering: RSI vừa vượt lên trên 30 (hồi phục từ quá bán)

### EMA Cross

**EMA12/36** là hệ thống 2 đường EMA:
- **EMA12**: EMA nhanh (12 ngày)
- **EMA36**: EMA chậm (36 ngày)

| Trạng thái | Ý nghĩa | Tín hiệu |
|------------|---------|----------|
| **Cross✓** | EMA12 vừa cắt lên EMA36 | Bullish crossover - MUA |
| **Above** | EMA12 > EMA36 | Xu hướng tăng |
| **Below** | EMA12 < EMA36 | Xu hướng giảm |

### Accumulation (Accum)

Tỷ lệ tích lũy = Volume ngày tăng / Volume ngày giảm

| Giá trị | Ý nghĩa |
|---------|---------|
| > 1.2x | **Yes✓** - Đang tích lũy (nhiều mua hơn bán) |
| ≤ 1.2x | No - Chưa có dấu hiệu tích lũy rõ |

### Điểm RSI/EMA Score (0-55)

| Điều kiện | Điểm |
|-----------|------|
| RSI Weekly < 30 (Oversold) | +15 |
| RSI Weekly < 40 (Low) | +5 |
| RSI đang hồi phục (vượt 30) | +10 |
| EMA Cross Up | +20 |
| EMA12 > EMA36 | +10 |
| Volume > 1.3x average | +10 |

**Grade:**
- A: ≥35 điểm
- B: ≥25 điểm
- C: ≥15 điểm
- F: <15 điểm

---

## 4. BTL COMBINED SCORE

**Công thức**: `BTL Score = (Weinstein + Darvas + RSI/EMA) / 3`

| Grade | Điểm | Ý nghĩa |
|-------|------|---------|
| **A** | ≥60 | Tín hiệu mạnh - Cân nhắc MUA |
| **B** | ≥45 | Tín hiệu tốt - Theo dõi sát |
| **C** | ≥30 | Tín hiệu trung bình - Chờ thêm |
| **F** | <30 | Chưa có tín hiệu - Bỏ qua |

**Display**: `BTL Score: A (65)  [W:70 D:60 R:35]`
- W = Weinstein Score
- D = Darvas Score  
- R = RSI/EMA Score

---

## 5. ENTRY SIGNALS

### Entry Type

| Type | Điều kiện | Mô tả |
|------|-----------|-------|
| **Darvas** | Darvas Breakout + Volume + Stage 1→2 hoặc Stage 2 | Entry cổ điển theo Darvas-Weinstein |
| **RSI+EMA** | RSI < 30 + EMA Cross Up + Volume | Entry mean reversion |
| **None** | Chưa có tín hiệu entry | Chờ đợi |

### Entry Status

| Status | Ý nghĩa | Hành động |
|--------|---------|-----------|
| **★★★ BTL BUY ★★★** | Tất cả điều kiện đã đủ | **MUA NGAY** |
| **★★ BTL READY ★★** | Setup gần hoàn chỉnh | Chuẩn bị mua |
| **○ BTL WATCH ○** | Đang trong stage thuận lợi | Theo dõi |
| **◆ BTL FORMING ◆** | Setup đang hình thành | Chờ đợi |
| **-- STAGE 4 SKIP --** | Stage 4 - Tránh xa | KHÔNG MUA |

---

## 6. EXIT SIGNALS

### Stop Loss

**Darvas Box Low** được sử dụng làm mức stop loss:
- Stop = Box Low × 0.98 (buffer 2%)
- Nếu giá phá vỡ box low → **CẮT LỖ**

### Exit Warnings

| Signal | Điều kiện | Hành động |
|--------|-----------|-----------|
| **🔴 STOP HIT** | Giá < Box Low × 0.98 | Bán ngay |
| **🔴 STAGE 4** | Giá vừa phá vỡ MA30W xuống | Bán ngay |
| **⚠️ FAILED BO** | Breakout thất bại - giá quay vào box | Cân nhắc bán |
| **🟡 STAGE 3 WARN** | MA30W bắt đầu phẳng sau khi tăng | Chuẩn bị bán |
| **🟢 HOLD** | Không có tín hiệu exit | Giữ vị thế |

---

## 7. MARKET STAGE CHECK

Weinstein nhấn mạnh: **KHÔNG MUA khi thị trường trong Stage 4**

| Indicator | Ý nghĩa |
|-----------|---------|
| **MARKET: OK ✓** | Thị trường không trong Stage 4 - Có thể mua BTL |
| **MARKET: Stage4⚠** | Thị trường trong Stage 4 - TRÁNH mua BTL |
| **Index vs MA150** | So sánh chỉ số benchmark với MA150 của nó |

---

## 8. QUY TẮC GIAO DỊCH BTL

### Khi nào MUA?

1. ✅ BTL Score ≥ B (≥45)
2. ✅ Entry Type = Darvas hoặc RSI+EMA  
3. ✅ Market = OK (không Stage 4)
4. ✅ Stop Loss < 10% (relaxed vs ATL 8%)
5. ✅ R:R ≥ 2:1
6. ✅ **Gap% < 1%** tại ATO (data: Win gap = -0.2%, Lose gap = 1.2%)
7. ✅ **Pre-7d < 7%** giá chưa tăng quá 7% so với 7 ngày trước (data: Win = 7.2%, Lose = 12.1%)
8. ✅ **Vol/7d ≤ 0.7x** volume thấp so với trung bình 7 ngày (data: Win = 0.62x, Lose = 1.27x)
9. ✅ **Distribution Days < 7** trong 25 phiên gần nhất
10. ✅ **Nến đỏ** (ưu tiên mua ngày giảm - data: 100% winners mua ngày nến đỏ)

### Khi nào BÁN?

1. 🔴 Stop Hit - Bán ngay
2. 🔴 Stage 4 - Bán ngay
3. 🔴 **T+1 Return < -2%** - Cắt lỗ sớm (data: Win T+1 = +3.6%, Lose T+1 = -2.5%)
4. ⚠️ Failed Breakout - Cân nhắc bán
5. 🟡 Stage 3 Warning - Bắt đầu giảm vị thế
6. ✅ Đạt target (+20% hoặc +35%)

### Position Sizing

- Risk mỗi trade: 1-2% tài khoản
- Position size = Risk Amount / (Entry - Stop)
- BTL trades thường rủi ro hơn ATL → size nhỏ hơn (win rate chỉ ~22%)

---

## 9. BTL REFERENCE INDICATORS (Mới v3.1)

Các chỉ báo tham khảo hiển thị trong BTL Entry panel - **chỉ tham khảo, không phải điều kiện mua tự động**:

| Chỉ báo | Công thức | Tốt | Cảnh báo |
|-----------|----------|------|----------|
| **Vol/7d** | Volume / SMA(Volume,7) | ≤ 0.7x ✓quiet | > 1.3x ⚠high |
| **Pre-7d** | (Close - Close[7]) / Close[7] × 100 | ≤ 7% ✓ | > 10% ⚠extended |
| **Candle** | Close vs Open | RED ✓ | GREEN |

> **Lưu ý**: Các chỉ báo này dựa trên phân tích 18 BTL trades thực tế (vnstock VCI). Winners mua trong yên lặng (vol thấp, không đuổi giá, nến đỏ). Losers mua khi đám đông hưng phấn (vol cao, gap up, giá đã extended).

---

## 10. ICONS REFERENCE

| Icon | Ý nghĩa |
|------|---------|
| 🟢 | Tín hiệu tốt / Xác nhận |
| 🟡 | Cảnh báo / Trung lập |
| 🔴 | Tín hiệu xấu / Từ chối |
| ⚪ | Không có tín hiệu |
| ✓ | Điều kiện đạt |
| ✗ | Điều kiện không đạt |
| ⚠ | Cảnh báo |
| ★ | Tín hiệu mạnh |

---

## 11. VÍ DỤ THỰC TẾ

### Case 1: Darvas Entry
```
BTL Score: A (68)  [W:70 D:80 R:35]
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 STAGE (Weinstein)  A  (70/100)
Current Stage:  Stage 1→2 Breakout
MA30W: 25000   |   Price: Above ✓   |   Slope: Rising ✓
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 SETUP (Darvas Box)  A  (80/100)
Box Status:  BOX BREAKOUT!
→ ACTION: BUY [Darvas Entry]
```

### Case 2: RSI+EMA Entry
```
BTL Score: B (48)  [W:30 D:30 R:45]
━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 STAGE (Weinstein)  C  (30/100)
Current Stage:  Stage 1 (Basing)
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 RSI/EMA  A  (45/55)
RSI Wkly: 28.5 OS✓   |   EMA: Cross✓
→ ACTION: BUY [RSI+EMA Entry] - Mean reversion play
```

### Case 3: Avoid
```
BTL Score: F (20)  [W:10 D:20 R:15]
MARKET: Stage4⚠
→ ACTION: NO TRADE - Market và stock đều yếu
```

---

## 12. PHÂN TÍCH DỮ LIỆU THỰC TẾ (vnstock)

Dựa trên phân tích 18 BTL trades (12/2025 - 03/2026) bằng vnstock VCI:

### Kết quả tổng quan

| Metric | Giá trị |
|--------|--------|
| Win Rate | **22%** (4/18) |
| Avg PnL | -3.71% |
| Win Avg | +6.45% |
| Lose Avg | -6.62% |

### Chỉ số phân biệt Win vs Lose (★★ = rất có ý nghĩa)

| Metric | WIN | LOSE | Sig |
|--------|-----|------|-----|
| Gap% | -0.2% | 1.2% | ★★ |
| ATO premium | -0.5% | 0.4% | ★★ |
| VolRatio | 0.6x | 1.3x | ★★ |
| PreChg% | 7.2% | 12.1% | ★★ |
| MaxGain% | 12.9% | 3.1% | ★★ |
| MaxDD% | -5.4% | -8.3% | ★★ |
| T+1 Ret% | +3.6% | -2.5% | ★★ |
| 7dRet% | -1.9% | -3.9% | ★★ |

### Nhận xét quan trọng

1. **Gap-up = nguy hiểm**: BTL thắng khi entry không gap hoặc gap nhẹ xuống
2. **Volume ratio thấp lại tốt hơn**: Winning BTL trades có vol = 0.6x (chưa breakout mạnh). Vol cao (>1.3x) có thể là distribution
3. **Pre-signal run-up > 10% = red flag**: Giá đã chạy quá nhiều trước khi signal
4. **T+1 return là predictor mạnh**: Nếu ngày sau mua bị âm > 2%, nên cắt lỗ sớm

### BTL Winning Trades

| Code | PnL | Gap | VolRatio | 7d Ret |
|------|-----|-----|----------|--------|
| PVC | +15.8% | 0.0% | 0.6x | +6.1% |
| G36 | +7.0% | 0.0% | 0.3x | +1.7% |
| BIC | +2.7% | -0.2% | 0.6x | -8.1% |
| VHC | +0.3% | -0.5% | 0.9x | -7.3% |

> **Kết luận**: BTL win rate rất thấp (22%). Cần thêm filter chặt (gap, pre-change, T+1 cut) để cải thiện.

---

*Tài liệu này được tạo cho Minervini Indicator v3.1 - BTL Mode (cập nhật 03/2026)*

**Changelog v3.1:**
- Thêm **BTL Reference Indicators** (Vol/7d, Pre-7d, Candle) hiển thị trong panel
- Cập nhật quy tắc giao dịch với data-driven thresholds
- Đồng bộ backtest script với main indicator (btlStopOK + btlRRok)
