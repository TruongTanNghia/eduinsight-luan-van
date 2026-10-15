# 03 · Hồ sơ học sinh — `/students/[id]` (phân hệ quan trọng nhất)
Tham chiếu: `reference/StudentProfile.dc.html`

**API:** `GET /api/v1/students/{id}`, `/students/{id}/grades`, `/students/{id}/trends`, `/students/{id}/analysis`.

## Bố cục
1. Breadcrumb "Học sinh / {lớp} / {tên}" + `DemoBadge`.
2. `Sticker` thông tin: avatar chữ cái 72px tròn `bg-pink border-[2.5px]` (chỉ dùng ảnh nếu dataset có); tên h1 24px/800; dòng Mã HS (mono) · Lớp · Khối · Năm học; ghi chú "Chỉ hiển thị trường có trong dataset". Hai ô stat viền đen: "ĐTB {kỳ}" (mono 26px) và "Xu hướng gần đây" (Tiến bộ/Ổn định/Sa sút + "ĐTB ±x so với kỳ trước · ngưỡng ±0,3"). Nút `outline` "Xuất báo cáo", `primary` "Định hướng".
3. `Sticker p-0` **Bảng điểm theo môn và học kỳ**: chip "Thực tế · tính từ dữ liệu"; cột Môn · mỗi kỳ (mono, phải; thiếu = "—" màu muted) · ĐTB lớp · Xu hướng (`Tag`: "Tăng N kỳ liên tiếp" mint, "Giảm N kỳ liên tiếp" tomato, "Tăng/Giảm kỳ gần nhất" nhạt hơn, "Ổn định" neutral, "Chưa đủ dữ liệu" white). Dòng cuối "ĐTB kỳ" nền surface-soft.
4. Lưới 2 cột biểu đồ:
   - "Điểm từng môn qua các kỳ": `ToggleChips` chọn nhiều môn (mặc định Toán, Văn, Anh) + `TrendLineChart` nhiều series (màu `tokens.chart.series`). Không chọn môn nào → thông báo.
   - "Điểm các môn kỳ gần nhất so với lớp": cột đôi cá nhân (cobalt) / ĐTB lớp (pink), viền đen.
   - "Mức tăng/giảm so với kỳ trước": thanh phân kỳ quanh trục 0 (âm tomato trái, dương mint phải), vùng ±ngưỡng tô neutral.
   - "Heatmap môn × học kỳ": ô 34px bo 5px, thang trắng → cobalt, chữ trắng khi đậm > 50%; ô thiếu dữ liệu gạch chéo.
5. **Phân tích tự động** (lưới ô stat ≥ 200px): môn tăng nhiều nhất · môn giảm nhiều nhất · ĐTB theo kỳ · môn biến động nhất (độ lệch chuẩn) · số kỳ giảm liên tiếp · môn thiếu dữ liệu. Ghi rõ "không phải dự báo mô hình".
6. **Nhận xét**: đoạn văn sinh từ phép tính đã xác minh (≤ 80ch), dòng "Căn cứ:" chứa các `Tag` neutral mono (VD "Toán: +0,4, +0,4, +0,5", "Ngưỡng ±0,30"). Giáo viên có thể sửa trước khi đưa vào báo cáo.

## Logic xu hướng (đặt ở backend, trả về sẵn)
- Δ chỉ tính giữa hai kỳ liên tiếp đều có điểm; streak đếm từ kỳ gần nhất lùi lại, cùng dấu và |Δ| ≥ ngưỡng.
- < 3 kỳ có điểm → "Chưa đủ dữ liệu". Không đưa nhận xét khi thiếu căn cứ.
