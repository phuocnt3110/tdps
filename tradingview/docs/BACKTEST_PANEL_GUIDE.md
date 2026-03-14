# Backtest Panel - Hướng dẫn sử dụng

## Tổng quan

**Backtest Panel** là bảng thống kê hiệu suất của các tín hiệu BUY được tạo bởi indicator. Panel này giúp bạn đánh giá chất lượng tín hiệu trước khi áp dụng vào giao dịch thực.

**Phiên bản**: v3.1 (1-share basis + Trade History + Pullback Buy + Low-Cheat Pivot)

---

## 1. CẤU TRÚC BẢNG THỐNG KÊ (Top-right)

```
┌──────┬───────┬───────┬─────┬──────┬──────┬──────┬──────┐
│ Exit │ Total │ Valid │ Win │ Win% │ Avg% │ Max% │ Min% │
├──────┼───────┼───────┼─────┼──────┼──────┼──────┼──────┤
│  T+2 │   17  │   17  │  10 │ 58.8 │ +1.8 │+13.4 │-11.7 │
│  T+7 │   17  │   17  │  12 │ 70.6 │ +3.7 │+24.8 │-11.9 │
│ T+14 │   17  │   16  │  10 │ 62.5 │ +4.8 │+33.3 │-12.5 │
│ T+30 │   17  │   16  │  10 │ 62.5 │ +7.8 │+36.8 │ -6.7 │
│  6M  │   17  │   14  │  11 │ 78.6 │+26.3 │+77.3 │ -2.7 │
│  1Y  │   17  │   12  │   4 │ 33.3 │+15.3 │+163.2│-60.7 │
├──────┼───────┼───────┼─────┼──────┴──────┴──────┴──────┤
│SUMMARY│ATL:8 │BTL:9 │ LGL │      5Y | 1-share basis   │
├──────┴───────┴───────┴─────┴───────────────────────────┤
│ ATL=Breakout|PB=Pullback|LC=LowCheat|BTL=Weinstein-Darvas │
└────────────────────────────────────────────────────┘────┘
```

## 2. BẢNG TRADE HISTORY (Bottom-right)

```
┌──────┬────────────┬─────────────────────┬────────────┬─────────────────────┬───────┬───────┬──────┐
│ T+2  │    Buy     │       B.OHLC        │    Exit    │       E.OHLC        │  P&L  │   %   │ Type │
├──────┼────────────┼─────────────────────┼────────────┼─────────────────────┼───────┼───────┼──────┤
│   1  │ 2025/06/18 │ 3200/3390/3200/3390 │ 2025/12/15 │ 5700/6010/5330/6010 │ +2620 │+77.3% │ ATL  │
│   2  │ 2025/02/06 │ 2550/2720/2550/2720 │ 2025/08/07 │ 4220/4300/4170/4220 │ +1500 │+55.1% │ BTL  │
│  ... │    ...     │        ...          │    ...     │        ...          │  ...  │  ...  │ ...  │
├──────┴────────────┴─────────────────────┴────────────┴─────────────────────┴───────┴───────┴──────┤
│ Total: 14 trades | Showing last 14                                         │ 1 share basis       │
└─────────────────────────────────────────────────────────────────────────────┴─────────────────────┘
```

---

## 3. GIẢI THÍCH CÁC CỘT - BẢNG THỐNG KÊ

### Exit (Thời điểm chốt lời)

| Exit | Mô tả | Số bars |
|------|-------|---------|
| **T+2** | Bán sau 2 ngày | 2 |
| **T+7** | Bán sau 1 tuần | 7 |
| **T+14** | Bán sau 2 tuần | 14 |
| **T+30** | Bán sau 1 tháng | 30 |
| **6M** | Bán sau 6 tháng | 126 |
| **1Y** | Bán sau 1 năm | 252 |

### Total (Tổng tín hiệu)

- **Ý nghĩa**: Tổng số tín hiệu BUY (ATL + BTL) trong khoảng lookback
- Giá trị này giống nhau cho tất cả các dòng

### Valid (Tín hiệu hợp lệ)

- **Ý nghĩa**: Số tín hiệu có đủ dữ liệu để tính return
- Valid < Total khi có tín hiệu gần đây chưa đủ thời gian
- Ví dụ: T+30 cần ít nhất 30 ngày sau tín hiệu mới tính được

### Win (Số lần thắng)

- **Ý nghĩa**: Số tín hiệu có return > 0%
- Dùng để tính Win Rate

### Win% (Tỷ lệ thắng)

- **Công thức**: `Win / Valid × 100%`
- **Màu sắc**:
  - 🟢 Xanh: ≥ 60%
  - 🟡 Vàng: 50-60%
  - 🔴 Đỏ: < 50%

### Avg% (Return trung bình - 1-share basis)

- **Ý nghĩa**: % lãi/lỗ trung bình nếu mua 1 cổ phiếu mỗi signal
- **Công thức**: `Σ(return%) / Valid`
- **Màu sắc**:
  - 🟢 Xanh: > 0% (lãi)
  - 🔴 Đỏ: < 0% (lỗ)

### Max% (Return cao nhất)

- **Ý nghĩa**: Lợi nhuận cao nhất trong các tín hiệu
- Luôn hiển thị màu xanh

### Min% (Return thấp nhất)

- **Ý nghĩa**: Lợi nhuận thấp nhất (có thể âm = thua lỗ)
- Luôn hiển thị màu đỏ
- Cho biết worst-case drawdown

---

## 4. GIẢI THÍCH CÁC CỘT - BẢNG TRADE HISTORY

| Cột | Ý nghĩa |
|-----|---------|
| **#** | Số thứ tự (1 = gần nhất) |
| **Buy** | Ngày mua (YYYY/MM/DD) |
| **B.OHLC** | Open/High/Low/Close ngày mua |
| **Exit** | Ngày exit |
| **E.OHLC** | Open/High/Low/Close ngày exit |
| **P&L** | Lãi/lỗ tuyệt đối (Exit Close - Buy Close) |
| **%** | % lãi/lỗ |
| **Type** | ATL (xanh lá) / ATL-PB (teal) / ATL-LC (xanh dương) / BTL (aqua) |

**Lưu ý**: Bảng hiển thị tối đa 15 trades gần nhất

---

## 5. ĐÁNH GIÁ KẾT QUẢ THEO TIMEFRAME

### T+2 (Momentum ngắn hạn)

| Avg% | Chất lượng |
|------|------------|
| > +2% | Tốt - Timing chuẩn |
| 0% - +2% | Trung bình |
| < 0% | Kém - Timing sai |

### T+7 / T+14 (Swing ngắn)

| Avg% | Chất lượng |
|------|------------|
| > +5% | Xuất sắc |
| +2% - +5% | Tốt |
| 0% - +2% | Trung bình |
| < 0% | Kém |

### T+30 (Swing trading)

| Avg% | Chất lượng |
|------|------------|
| > +8% | Xuất sắc |
| +4% - +8% | Tốt |
| 0% - +4% | Trung bình |
| < 0% | Kém |

### 6M (Position trading)

| Avg% | Chất lượng |
|------|------------|
| > +25% | Xuất sắc |
| +15% - +25% | Tốt |
| +5% - +15% | Trung bình |
| < +5% | Kém |

### 1Y (Long-term)

| Avg% | Chất lượng |
|------|------------|
| > +40% | Xuất sắc |
| +25% - +40% | Tốt |
| +10% - +25% | Trung bình |
| < +10% | Kém |

### Độ tin cậy theo Valid count

| Valid | Độ tin cậy |
|-------|------------|
| > 20 | Cao |
| 10-20 | Trung bình |
| 5-10 | Thấp |
| < 5 | Rất thấp |

---

## 4. CÁCH ĐỌC KẾT QUẢ

### Ví dụ 1: Tín hiệu tốt
```
│ Exit │ Total │ Valid │ Win │ Win% │  Inv │  Now  │ P&L% │
├──────┼───────┼───────┼─────┼──────┼──────┼───────┼──────┤
│  T+2 │  25   │  25   │  18 │ 72.0 │ 2500 │ 2581  │ +3.2 │
│ T+30 │  25   │  22   │  17 │ 77.3 │ 2200 │ 2548  │+15.8 │
```
**Phân tích:**
- Valid = 25/22: Hầu hết tín hiệu đủ dữ liệu
- Win% = 72-77%: Tỷ lệ thắng cao (xanh)
- P&L% = +3.2/+15.8: Lãi tốt
- **Kết luận**: Tín hiệu chất lượng cao

### Ví dụ 2: Tín hiệu kém
```
│ Exit │ Total │ Valid │ Win │ Win% │  Inv │  Now  │ P&L% │
├──────┼───────┼───────┼─────┼──────┼──────┼───────┼──────┤
│  T+2 │   4   │   4   │   1 │ 25.0 │  400 │  394  │ -1.5 │
│ T+30 │   4   │   3   │   1 │ 33.3 │  300 │  307  │ +2.4 │
```
**Phân tích:**
- Valid = 4/3: Mẫu quá nhỏ
- Win% = 25-33%: Tỷ lệ thắng thấp (đỏ)
- P&L% = -1.5/+2.4: Return kém
- **Kết luận**: Tín hiệu không hiệu quả hoặc mẫu chưa đủ

### Ví dụ 3: Giá trị "oor"
```
│  6M  │  12   │   5   │   4 │ 80.0 │  500 │  oor  │  oor │
│  1Y  │  12   │   2   │   2 │  oor │  200 │  oor  │  oor │
```
**Giải thích:**
- **oor** = "Out Of Range" - Chưa đủ data để tính
- Valid = 5/2: Chỉ có 5 tín hiệu đủ 6 tháng, 2 tín hiệu đủ 1 năm
- Các tín hiệu gần đây chưa có đủ thời gian để tính return
- Đây là bình thường, không phải lỗi

---

## 5. PHƯƠNG PHÁP TÍNH TOÁN

### Reverse Lookup

Do Pine Script không cho phép truy cập dữ liệu tương lai trực tiếp, backtest sử dụng phương pháp **Reverse Lookup**:

1. Tại mỗi bar hiện tại, nhìn lại N bars trước
2. Kiểm tra xem tại bar đó có tín hiệu BUY không
3. Nếu có, tính return = (Close hiện tại - Close lúc signal) / Close lúc signal

```
Ví dụ tính T+30:
- Bar hiện tại: #100
- Nhìn lại bar #70 (30 bars trước)
- Nếu bar #70 có ATL BUY signal:
  - Return = (Close[0] - Close[30]) / Close[30] × 100%
  - Thêm vào mảng atlReturnsT30
```

### Thống kê

| Metric | Công thức |
|--------|-----------|
| Win Rate | Count(Returns > 0) / Count(Valid Returns) |
| Portfolio | Σ(100 × (1 + return%/100)) cho mỗi signal |
| P&L% | (Portfolio - Invested) / Invested × 100% |

---

## 6. CÁC TRƯỜNG HỢP ĐẶC BIỆT

### Không có tín hiệu (Total = 0)

```
│  T+2 │   0   │   0   │   0 │  n/a │   0  │  n/a  │  n/a │
```
- **n/a** = Không có tín hiệu nào được tạo
- Cổ phiếu chưa bao giờ đạt điều kiện BUY

### Dữ liệu không đủ (Valid < Total)

```
│  1Y  │   8   │   2   │   1 │ 50.0 │  200 │  210  │ +5.2 │
```
- Total = 8, Valid = 2: Chỉ 2/8 tín hiệu đủ 1 năm dữ liệu
- 6 tín hiệu còn lại quá mới

### Mixed Results

```
│  T+2 │  18   │  18   │  14 │ 77.8 │ 1800 │ 1881  │ +4.5 │
│ T+30 │  18   │  15   │   6 │ 40.0 │ 1500 │ 1465  │ -2.4 │
```
- T+2 tốt (Win 77.8%, P&L +4.5%) nhưng T+30 kém (Win 40%, P&L -2.4%)
- Timing tốt nhưng không giữ được lợi nhuận
- Có thể do volatility hoặc thị trường đảo chiều

---

## 7. SỬ DỤNG BACKTEST HIỆU QUẢ

### Đánh giá qua SUMMARY row

Dùng SUMMARY row để xem tổng quan:

```
│SUMMARY│ATL:15│BTL: 8│Tot:23│ VIC  │  5Y | 100đ/sig   │
```
- ATL: 15 tín hiệu Above The Line (Minervini)
- BTL: 8 tín hiệu Below The Line (Weinstein-Darvas)
- Tot: 23 tổng cộng
- VIC: Mã cổ phiếu
- 5Y | 100đ/sig: Lookback 5 năm, đầu tư 100đ/signal

### Đánh giá theo timeframe

| Mục tiêu | Xem cột |
|----------|---------|
| Swing trading (2-5 ngày) | T+2 |
| Position trading (1 tháng) | T+30 |
| Medium term (6 tháng) | 6M |
| Long term (1 năm+) | 1Y |

### Kết hợp với phân tích hiện tại

1. **Bước 1**: Xem tín hiệu hiện tại trên Main Panel
2. **Bước 2**: Kiểm tra lịch sử hiệu suất trên Backtest Panel
3. **Bước 3**: Nếu lịch sử tốt → Tăng confidence
4. **Bước 4**: Nếu lịch sử kém → Giảm size hoặc skip

---

## 8. HẠN CHẾ

### Không phải là guarantee

- Hiệu suất quá khứ **KHÔNG** đảm bảo kết quả tương lai
- Thị trường có thể thay đổi, pattern có thể không còn hiệu quả

### Sample size matters

- Count < 10: Thống kê không đáng tin cậy
- Cần ít nhất 20+ signals để có kết luận có ý nghĩa

### Survivorship bias

- Backtest chỉ tính trên cổ phiếu còn tồn tại
- Không bao gồm cổ phiếu đã bị hủy niêm yết

### Look-ahead bias (Đã được xử lý)

- Script sử dụng Reverse Lookup để tránh look-ahead bias
- Tín hiệu được xác định tại thời điểm phát sinh, không sử dụng dữ liệu tương lai

---

## 9. SETTINGS

### Show Signal Markers on Chart

- **On**: Hiển thị markers trên chart tại vị trí tín hiệu (A=ATL, B=BTL)
- **Off**: Chỉ hiển thị bảng thống kê

### Lookback Period (Years)

- Mặc định: `5` năm
- Chỉ quét tín hiệu trong khoảng thời gian này
- Giá trị: 1-20 năm

### Show Trade History Panel

- **On**: Hiển thị bảng chi tiết các lệnh giao dịch (bottom-right)
- **Off**: Ẩn bảng Trade History

### Exit Timeframe for History

- Mặc định: `T+2`
- Lựa chọn: T+2, T+7, T+14, T+30, 6M, 1Y
- Chọn timeframe để hiển thị trong bảng Trade History

### Benchmark Symbol

- Mặc định: `HOSE:VNINDEX`
- Dùng để tính Relative Strength
- Có thể đổi sang HNX:HNXINDEX nếu phân tích sàn HNX

---

## 10. ICONS VÀ MARKERS

### Trên Chart

| Marker | Màu | Ý nghĩa |
|--------|-----|--------|
| **A** | Lime | ATL Breakout BUY |
| **P** | Teal | ATL Pullback BUY |
| **L** | Blue | ATL Low-Cheat Pivot |
| **B** | Aqua | BTL BUY |

### Trong Bảng

| Format | Ý nghĩa |
|--------|---------|
| +XX.X% | Return dương (màu xanh) |
| -XX.X% | Return âm (màu đỏ) |
| n/a | Không có dữ liệu |
| oor | Out of range - chưa đủ thời gian |

---

## 11. BEST PRACTICES

### Khi nào nên tin tưởng backtest?

✅ **Tin tưởng cao:**
- Count > 20
- Returns nhất quán qua các timeframe
- Win rate > 60%

⚠️ **Cẩn thận:**
- Count < 10
- T+2 âm nhưng long-term dương (timing issue)
- Volatility cao giữa các signals

❌ **Không nên tin:**
- Count < 5
- Returns toàn negative
- Thị trường đã thay đổi fundamentally

### Workflow đề xuất

```
1. Mở chart cổ phiếu
2. Thêm indicator "Minervini Complete"
3. Thêm indicator "Minervini Backtest"
4. Đọc Main Panel → Xác định tín hiệu hiện tại
5. Đọc Backtest Panel → Đánh giá chất lượng lịch sử
6. Quyết định trade dựa trên cả hai thông tin
```

---

## 12. FAQ

**Q: Tại sao return hiển thị "oor"?**
A: Tín hiệu quá mới, chưa đủ thời gian để tính return cho timeframe đó.

**Q: Tại sao count = 0?**
A: Cổ phiếu chưa bao giờ đạt điều kiện BUY trong lịch sử có sẵn.

**Q: Backtest có tính fees/slippage không?**
A: Không. Returns là gross returns, chưa trừ chi phí giao dịch.

**Q: Có thể export dữ liệu không?**
A: Pine Script không hỗ trợ export. Có thể chụp screenshot hoặc ghi chép thủ công.

**Q: Backtest panel nằm ở đâu?**
A: Panel hiển thị ở góc trên phải của chart, nằm cạnh Main Panel.

---

*Tài liệu này được tạo cho Minervini Backtest Indicator v3.1 (cập nhật 03/2026)*

**Changelog v3.1:**
- Thêm **Pullback Buy** signal (ATL-PB) - post-breakout pullback entry
- Thêm **Low-Cheat Pivot** signal (ATL-LC) - pre-breakout VCP contraction entry
- **4 loại tín hiệu**: ATL (breakout), ATL-PB (pullback), ATL-LC (low-cheat), BTL
- Cập nhật breakout state tracking đồng bộ với main indicator
- Thêm chart markers: A (lime), P (teal), L (blue), B (aqua)
- VCP tightening: pricePosPct ≥ 70% (từ 60%)
- Trade History hiển thị chi tiết loại tín hiệu với màu riêng

**Changelog v3.0:**
- Thay đổi từ Investment-based sang **1-share basis**
- Thêm cột **Avg%** (thay thế Inv/Now/P&L%)
- Thêm timeframes **T+7** và **T+14**
- Thêm **Trade History Panel** với chi tiết từng lệnh
- Hiển thị OHLC của ngày mua và ngày exit
- Tính P&L trên cơ sở 1 cổ phiếu
