# 06 · Đánh giá mô hình — `/model-evaluation` (vai trò quản trị / nghiên cứu)
Tham chiếu: `reference/ModelEval.dc.html`

**API:** `GET /api/v1/ai/models`, `GET /api/v1/ai/models/{id}/metrics` (đọc từ `evaluation_report.json` lưu cùng checkpoint).

## Bố cục
1. h1 + `Tag tone="yellow"` "DEMO · số liệu bố cục" nếu chưa có báo cáo thật; `SelectField` chọn mô hình/phiên bản.
2. `Sticker` model card dạng lưới key–value: Bài toán · Phiên bản + hash cấu hình · Thời gian huấn luyện · Phiên bản dữ liệu · Seed · Checkpoint (mono) · Tiêu chí chọn mô hình · Thời gian suy luận.
3. 2 cột: "Chia dữ liệu" (thanh Train cobalt / Val pink / Test tomato, chữ đen trên pink/tomato; bảng phân bố nhãn theo tập; cảnh báo lớp ít mẫu) · "Đặc trưng đầu vào" (Tag mono) + khối cấu hình `bg-ink text-yellow` font mono.
4. 2 cột: "Loss theo epoch" (train cobalt, val tomato, vạch dừng sớm nét đứt) · "Confusion matrix · tập test" (ô 52px, thang trắng→cobalt, ô đúng có viền đen 2px).
5. 2 cột: bảng Precision/Recall/F1/Support theo lớp + Macro + Accuracy (tính từ confusion matrix) · bảng so sánh với baseline (Macro F1 kèm CI 95%, ROC-AUC, PR-AUC, ECE, thời gian suy luận; dòng Transformer nền surface-soft) + khối `Sticker tone="yellow"` "Kết luận thận trọng".

## Quy tắc
- Chỉ hiển thị chỉ số có trong báo cáo đánh giá thật; chỉ số không phù hợp → ẩn và ghi lý do.
- Không mặc định Transformer tốt hơn baseline; ghi rõ khi CI chồng nhau.
