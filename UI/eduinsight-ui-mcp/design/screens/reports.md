# 07 · Báo cáo — `/reports`
Tham chiếu: `reference/Reports.dc.html`

**API:** `POST /api/v1/reports/student`, `POST /api/v1/reports/class`, `GET /api/v1/reports/{id}`, lịch sử `GET /api/v1/reports`.

## Bố cục
1. h1 + `DemoBadge`; phụ đề "Mọi báo cáo ghi rõ nguồn dữ liệu, thời điểm dữ liệu và tách số liệu thực tế khỏi kết quả dự đoán".
2. Hàng 2 cột (flex-wrap):
   - Trái `Sticker` "Thiết lập báo cáo" (≥ 340px): Phạm vi (4 nút ô `aria-pressed`: Một học sinh / Một lớp / Một học kỳ / Toàn nhóm; chọn = yellow + shadow-selected) · Đối tượng · Học kỳ · checkbox Nội dung (Bảng điểm, Biểu đồ tiến bộ, Môn mạnh/cần chú ý, Nhận xét, Kết quả dự đoán — kèm Tag "mô hình chưa sẵn sàng" khi chưa có) · Định dạng PDF/Excel · nút `primary` "Tạo và tải {định dạng}".
   - Phải: "Xem trước" — khung nền `#E8DDBE` chứa trang A4 trắng (max-w 640px) phản ánh tùy chọn trực tiếp: đầu trang tên trường + ngày tạo + mã báo cáo; tiêu đề; ô meta Nguồn dữ liệu · Thời điểm dữ liệu · ĐTB; các mục đánh số; mục dự đoán viền nét đứt tomato; chân trang phân biệt "Số liệu thực tế" và "Dự đoán".
3. `Sticker p-0` "Lịch sử báo cáo": Mã (mono) · Phạm vi · Đối tượng · Định dạng (Tag) · Dữ liệu (phiên bản) · Người tạo · Ngày tạo · "Tải lại".
