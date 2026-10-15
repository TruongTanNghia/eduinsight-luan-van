# 08 · Quản lý dữ liệu — `/data-management` (quyền nhập dữ liệu)
Tham chiếu: `reference/DataManagement.dc.html`

**API:** `POST /api/v1/data/import/preview` (multipart), `POST /api/v1/data/import/confirm`, `GET /api/v1/data/import/history`, `GET /api/v1/data/schema`.

## Bố cục
1. h1 + `DemoBadge`; dòng "Phiên bản đang dùng: **{ver}** · N bản ghi · N học sinh · nhập ngày …".
2. `Sticker` stepper 4 bước (Tải lên → Kiểm tra cấu trúc → Xem trước → Xác nhận nhập): chấm 28px, bước xong mint dấu ✓, bước hiện tại cobalt, bước sau neutral; `aria-current="step"`.
   - Dropzone viền nét đứt 2.5px cobalt nhạt: icon Upload, "Kéo thả file CSV hoặc Excel vào đây", ".csv, .xlsx · tối đa 20 MB · công thức trong ô được đọc như văn bản, không thực thi", nút chọn file, link "Tải file mẫu đúng cấu trúc".
   - Ô file đã chọn: tên (mono), dung lượng, số dòng; 3 ô số Hợp lệ (mint nhạt) / Không hợp lệ (tomato nhạt) / Cảnh báo (warning).
3. 2 cột: bảng "Kiểm tra cấu trúc" (Cột mono · Kiểu mong đợi · Bắt buộc · Kết quả với icon CircleCheck/CircleAlert/CircleX + chữ) · danh sách "Lỗi và cảnh báo" (Tag Lỗi/Cảnh báo + tiêu đề + chi tiết số dòng).
4. `Sticker p-0` "Xem trước dữ liệu": dòng lỗi nền `#FEF3F2`, ô sai đậm, cột Ghi chú màu `#C2290F`.
5. `Sticker` "Xác nhận nhập dữ liệu": Phiên bản mới · Bản ghi thêm mới · Bản ghi trùng khóa sẽ ghi đè (amber) · Mô hình bị ảnh hưởng; khối cảnh báo warning với checkbox "Tôi đã xem trước dữ liệu và đồng ý ghi đè N bản ghi"; nút `primary` chỉ bật khi tick; sau khi nhập: thông báo `role="status"` mint.
6. 2 cột: "Lịch sử nhập dữ liệu" (Phiên bản · File · Hợp lệ · Lỗi · Người nhập · Ngày · Trạng thái Tag) · "Data dictionary" (Trường mono · Mô tả · % thiếu; trường nhãn tuyển sinh thiếu 100% ghi rõ).

## Bảo mật
- Không bao giờ ghi đè khi chưa xác nhận; ghi audit log. Không thực thi công thức/macro trong file.
