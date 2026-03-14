# 🔎 Volume Profile (Nâng cao) — Cảnh báo đảo chiều/giảm và tích hợp với Trend Health

Tài liệu này hướng dẫn cách dùng Volume Profile để nhận biết sớm rủi ro “phân phối/đảo chiều” của từng cổ phiếu và cách kết hợp với Trend Health của panel. Đây là tài liệu độc lập, không ảnh hưởng đến cơ chế panel hiện đang áp dụng.

---

## Định nghĩa nhanh

- **POC (Point of Control)**: Mức giá có khối lượng giao dịch lớn nhất trong vùng chọn.
- **Value Area (VA)**: Vùng chứa ~70% khối lượng (mặc định). Biên trên/dưới là **VAH/VAL**.
- **HVN (High Volume Node)**: Cụm vùng giá có volume dày (khu vực được thị trường “chấp nhận”).
- **LVN (Low Volume Node)**: Vùng giá ít volume (khe thanh khoản). Giá đi qua nhanh khi bị thủng.

---

## Dấu hiệu cảnh báo đảo chiều từ Volume Profile

- **[Failed Acceptance ở vùng cao]**
  - Mô tả: Giá vượt VAH/đỉnh nhưng không tạo được HVN mới phía trên, sớm đóng cửa lại dưới VAH.
  - Hệ quả: Breakout thiếu “chấp nhận”, dễ đảo chiều/bull trap.
  - Hành động: Tránh mua đuổi; nếu đang nắm giữ, siết trailing hoặc chốt bớt.

- **[POC Shift đi ngang/đi xuống trong khi giá còn cao]**
  - Mô tả: POC không trôi lên theo giá, thậm chí dịch xuống.
  - Hệ quả: Dòng tiền lớn không chấp nhận vùng giá cao; rủi ro phân phối tăng.
  - Hành động: Hạn chế add-on; dời stop lên sát nến/ATR; quan sát lower high.

- **[Thủng LVN → trượt nhanh về HVN kế tiếp]**
  - Mô tả: Đóng cửa dưới LVN với volume tăng.
  - Hệ quả: Thiếu hỗ trợ, giá thường “trượt” nhanh tới HVN kế tiếp.
  - Hành động: Đặt stop kỹ thuật dưới LVN hoặc thoát phần lớn khi bị thủng.

- **[Supply Overhang (HVN dày ở phía trên)]**
  - Mô tả: Trên đầu giá hiện tại có các HVN lớn (vùng “kẹt hàng”).
  - Hệ quả: Giá hồi lên dễ bị xả, khó vượt nếu không có acceptance rõ.
  - Hành động: Tránh mua ngay dưới cụm HVN; nếu giữ vị thế, cân nhắc chốt bớt khi tiếp cận.

- **[Break VAH rồi mất lại (Bull Trap)]**
  - Mô tả: Vượt VAH nhưng 1–2 phiên sau đóng cửa lại dưới VAH.
  - Hệ quả: Bẫy tăng; rủi ro đảo chiều ngắn hạn.
  - Hành động: Chốt 1/2 và kéo stop phần còn lại về entry/ATR trail.

---

## Tích hợp với Trend Health (Panel)

- **Churning = YES** + không tạo HVN mới phía trên → Phân phối rất rõ.
- **Failed Breakout / Pivot rejected** + mất VAH/POC → Bull trap/đảo chiều.
- **Lower High xuất hiện** + POC dịch xuống → Xu hướng suy yếu sớm.
- **Dist day (cổ phiếu)** + thủng LVN → Dễ rơi nhanh về HVN kế tiếp.

---

## Quy tắc vào lệnh (Entry Filters)

- **Không mua** nếu phía trên có **HVN dày** (supply overhang) trừ khi đã có acceptance rõ ràng phía trên HVN (giá đóng cửa trên HVN 1–2 phiên + POC/mini-HVN hình thành).
- Sau khi **vượt VAH/box high**, ưu tiên đợi **1–2 nến acceptance** (POC trôi lên/mini-HVN xuất hiện) trước khi vào vị thế chính.
- Tránh vào khi **POC không đi cùng chiều giá** (đi ngang/đi xuống) hoặc **break VAH rồi đóng dưới lại** trong 1–2 phiên gần nhất.

---

## Quy tắc thoát lệnh (Exit/SL/Trailing)

- Đặt **stop dưới LVN/hỗ trợ HVN gần nhất** thay vì chỉ % cứng; nếu đóng cửa thủng LVN với vol tăng → thoát phần lớn.
- Nếu **break VAH rồi mất lại** trong 1–2 phiên: **chốt 1/2**, phần còn lại kéo stop về entry hoặc theo **ATR trail**/MA20.
- **POC shift xuống liên tiếp** trong khi giá tạo **lower high**: giảm 25–50% vị thế, siết trailing dưới đáy nến gần nhất.

---

## Thiết lập & Thực hành

- **Fixed Range**: quét theo nền/base hoặc đoạn tăng gần nhất để đo acceptance đúng bối cảnh.
- **Visible Range**: tham khảo cấu trúc tổng thể; kết hợp Fixed Range để ra quyết định.
- **Timeframe**: bám cùng timeframe của tín hiệu (ví dụ Daily cho ATL/BTL Daily).

---

## Mức độ cảnh báo (Severity)

| Mức | Tổ hợp tín hiệu | Gợi ý hành động |
|-----|------------------|------------------|
| Nhẹ | 1 trong các dấu hiệu ở trên, vol bình thường | Quan sát, chưa cần hành động |
| Vừa | 2 dấu hiệu kết hợp hoặc có Dist day | Giảm size, siết trailing |
| Nặng | Failed acceptance + POC xuống + thủng LVN | Chốt phần lớn/thoát lệnh |

---

## Checklist nhanh

- **[entry]** Có **overhead HVN** gần không? Có acceptance rõ phía trên chưa?
- **[entry]** POC có **trôi lên theo giá** không?
- **[hold]** Có **Churning/Dist day** và **mất VAH/POC** không?
- **[risk]** LVN gần nhất phía dưới ở đâu? Kế hoạch stop?
