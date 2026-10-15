# 05 · Dự đoán & định hướng — `/predictions?student=`
Tham chiếu: `reference/Prediction.dc.html`

**API:** `GET /api/v1/students/{id}/predictions`, `GET /api/v1/ai/models`, `POST /api/v1/ai/predict`. Trường/điểm chuẩn: `GET/POST /api/v1/schools`, `/admission-requirements`.

## Nguyên tắc tối thượng
Công cụ hỗ trợ quyết định, **không phải phán quyết**. Khi dataset chưa có nhãn kết quả thi vào 10: **không hiển thị xác suất đỗ/trượt**. Mọi số giả lập gắn `Tag tone="yellow"` "DEMO".

## Bố cục
1. h1 + `DemoBadge` + câu "Công cụ hỗ trợ quyết định…". Phải: `SelectField` học sinh (rộng 240px) và `Segmented` trạng thái dữ liệu (chỉ hiện ở môi trường demo; production đọc từ `models[].status`).
2. **Khi chưa có nhãn** (`status = "awaiting_labels"`): `Sticker tone="yellow"` cảnh báo (icon TriangleAlert) "Dự đoán tuyển sinh THPT chưa được kích hoạt" + 4 bước pipeline dạng ô viền đen đánh số: Thu thập nhãn (Đang chờ) · Ghép hồ sơ (Đang chờ) · Huấn luyện & đánh giá (Pipeline sẵn sàng, mint) · Kích hoạt (Đang khóa, neutral). Link "Nhập dữ liệu kết quả tuyển sinh" → /data-management.
3. **Khi DEMO / có nhãn**: `Sticker` viền nét đứt 2.5px tomato + Tag "DEMO" giải thích số liệu giả lập; khi có nhãn thật thay bằng phiên bản mô hình, khoảng tin cậy, độ hiệu chỉnh.
4. 2 cột:
   - "Kiến trúc mô hình chuỗi học kỳ": 4 token học kỳ (ô `bg-surface-soft` viền đen, vector mono) → mũi tên → "Embedding + mã hóa vị trí" → khối `bg-cobalt text-white` "Transformer Encoder × 2" → 2 ô đầu ra (A đang dùng / B chờ nhãn, viền nét đứt).
   - "Đặc trưng đầu vào ánh xạ từ schema": bảng Đặc trưng · Cột nguồn (mono) · Trạng thái (`Tag`: Có trong dataset mint / Dẫn xuất cobalt / Không có neutral) + ô kết quả đầu ra A cho học sinh (ghi rõ "chưa hiệu chỉnh", link Đánh giá mô hình).
5. **Gợi ý trường THPT**:
   - Chưa có điểm chuẩn → `EmptySticker` + form thêm trường (Tên, Năm, Phương thức, Điểm chuẩn, Loại hình, **Nguồn tham chiếu bắt buộc**).
   - Có dữ liệu → bảng: Trường · Phương thức · Điểm chuẩn · **Chênh lệch điểm** (cột riêng) · **Xác suất mô hình** (cột riêng, thanh + số + Tag DEMO nếu chưa kiểm chứng) · Nhóm (Mục tiêu cobalt / Phù hợp mint / Dự phòng neutral). Giải thích công thức chênh lệch bên dưới. Khối "Môn cần cải thiện để tiến gần {trường}" (thanh tomato, ghi "Tính từ dữ liệu, không dùng mô hình").
6. **Các phương án học tập sau THCS**: 4 ô (THPT công lập, ngoài công lập, GDTX, GDNN), mỗi ô liệt kê yếu tố với icon trạng thái: Đã xác minh (mint) / Chưa có dữ liệu (amber) / Cần trao đổi (muted). Ô nhập "Nguyện vọng của học sinh" và "Ghi chú tư vấn". Câu chốt: "Quyết định cuối cùng thuộc về học sinh và gia đình". Không tự xếp học sinh vào phương án nào.
