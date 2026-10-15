# 04 · Phân tích lớp học — `/classes/[id]`
Tham chiếu: `reference/ClassAnalysis.dc.html`

**API:** `GET /api/v1/analytics/class-comparison?class=`, `/analytics/student-risk?class=`, `/students?class=`.

## Bố cục
1. h1 "Phân tích lớp {tên}" + `DemoBadge`; phụ đề sĩ số · GVCN · kỳ so sánh. Bên phải `SelectField` Lớp và So sánh (HK2 với HK1 …).
2. 4 ô KPI `Sticker p-4`: ĐTB lớp · Thay đổi so với kỳ trước (kèm "dưới ngưỡng ±0,3 → lớp ổn định") · Mức Tốt + Khá · Cần giáo viên theo dõi.
3. 2 cột: cột đôi "ĐTB môn: HK1 và HK2" (HK1 pink, HK2 cobalt) · "Phân bố mức kết quả học tập" (2 thanh xếp chồng HK1/HK2, số trong đoạn, chữ trắng chỉ trên cobalt).
4. `Sticker` **Tiến bộ, ổn định và sa sút** (drill-down):
   - Trái: thanh tỷ lệ 14px + 3 nút lớn (`aria-pressed`) Tiến bộ / Ổn định / Sa sút; nút đang chọn nền yellow + `shadow-selected`.
   - Phải: "Số học sinh giảm ≥ 0,3 theo môn" — mỗi môn là một `<button>` hàng ngang (tên · thanh · số), môn ≥ 9 HS tô amber; đang chọn nền yellow.
   - Bấm nhóm hoặc môn → lọc bảng bên dưới; nút "Bỏ lọc: …" xuất hiện góc phải.
5. `Sticker p-0` bảng học sinh: Học sinh · ĐTB kỳ trước · ĐTB kỳ này · Δ · Nhóm (`TrendTag`) · Môn giảm ≥ 0,3 · "Xem hồ sơ".
