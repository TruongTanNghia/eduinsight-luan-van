# 01 · Tổng quan — `/dashboard`
Tham chiếu thiết kế: `reference/Main.dc.html`

**Mục đích:** nhìn toàn trường trong 10 giây: điểm tăng/giảm, môn yếu, ai cần chú ý.
**API:** `GET /api/v1/analytics/overview`, `/analytics/grades-by-semester`, `/analytics/subject-comparison`, `/analytics/class-comparison`, `/analytics/student-risk` (đều nhận query `year, grade, class, semester, subject`).

## Bố cục (trên → dưới)
1. **FilterBar**: Năm học · Khối · Lớp · Học kỳ · Môn học; bên phải `num` "Nguồn: {datasetVersion} · cập nhật {date}". Bộ lọc đổi query string (URL là nguồn state) và refetch.
2. **Hero + KPI** (grid 2 cột ≥ 520px):
   - Trái `Sticker tone="yellow"` p-9: `DemoBadge` nghiêng; h1 54px "Trường mình tăng [+0,07] điểm học kỳ này" (cụm số trong span `bg-ink text-yellow rounded-[10px] px-2.5 -rotate-[1.5deg] inline-block`); đoạn tóm tắt 18px sinh từ số liệu thật; 2 nút: `dark` "Xem N bạn cần chú ý" → /students?status=watch, `outline` "Xuất báo cáo" → /reports.
   - Phải lưới 2×2 `StatSticker`: ĐTB (cobalt), Bạn tiến bộ (mint), Bạn đi xuống (tomato), Cần xem lại (lilac). `hint` = định nghĩa KPI (VD "ĐTB tăng ≥ 0,3 · 23,3%").
3. **Hàng biểu đồ 1** (2 cột): `TrendLineChart` "Điểm trung bình qua 4 kỳ" (toàn trường cobalt + khối pink, tag chú giải góc phải); `SubjectBarChart` "Môn nào mạnh, môn nào cần đỡ?" + `Tag tone="tomato"` "Cam = dưới ĐTB chung ≥ 0,3".
4. **Hàng biểu đồ 2** (3 cột ≥ 380px): Histogram "Điểm của N bạn" (cột viền đen, khoảng < 5,5 tô tomato); "Xếp loại theo TT22" (thanh xếp chồng cao 52px viền đen, chú giải lưới 2 cột với số mono); "8 lớp, ai dẫn đầu?" (ô lớp viền đen: tên, ĐTB 24px/800, `▲tiến ▼sa sút` mono; màu ô theo ĐTB: ≥7,3 mint, ≥7 trắng, ≥6,85 #FFE9A8, còn lại #FFC2B3; bấm → /classes/{id}).
5. **Các bạn cần thầy cô xem lại**: h2 30px + câu miễn trừ; lưới thẻ ≥ 250px, mỗi thẻ `Sticker p-[18px]`: avatar chữ cái 46px viền đen màu xoay vòng, tên + lớp·mã (mono), `Tag` lý do (tomato nếu giảm/ dưới ngưỡng, yellow nếu cảnh báo môn, white nếu thiếu dữ liệu), ĐTB 26px/800 + Δ mono màu theo dấu, nút `outline` "Mở hồ sơ" → /students/{id}.

## Trạng thái
- Loading: `LoadingSticker` thay từng khối, giữ bố cục lưới.
- Không có dữ liệu cho bộ lọc: `EmptySticker` "Chưa có dữ liệu cho bộ lọc này" + nút "Xóa bộ lọc".
- Lỗi API: `ErrorSticker` có nút Thử lại; các khối khác vẫn hiển thị.

## Quy tắc dữ liệu
- KPI tiến bộ/sa sút: |Δ ĐTB| ≥ ngưỡng cấu hình (mặc định 0,3) so với kỳ trước. Hiển thị ngưỡng trong `hint`.
- Không kết luận tâm lý/gia đình; tiêu chí "cần xem lại" lấy từ cấu hình.
