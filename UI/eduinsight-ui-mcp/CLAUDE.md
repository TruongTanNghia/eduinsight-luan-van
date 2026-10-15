# EduInsight AI — hướng dẫn cho agent

Chép file này vào thư mục gốc dự án EduInsight AI (cạnh `frontend/` và `backend/`). Cursor: đổi tên thành `.cursorrules` hoặc đưa vào `.cursor/rules/`.

## Giao diện: bắt buộc dùng MCP `eduinsight-ui`
Dự án dùng design system **"Sticker lớp học"**: nền vàng bơ chấm bi, viền đen 2.5px, bóng đổ cứng, màu khối rực, font Bricolage Grotesque + JetBrains Mono.

1. **Lần đầu dựng frontend:** gọi `get_setup_guide`, rồi `get_design_tokens` (format=css) → `frontend/app/globals.css`, và `get_component` (name=all) → tạo đủ file trong `frontend/components/ui/` và `frontend/app/layout.tsx`.
2. **Trước mỗi màn hình:** gọi `get_design_rules` và `get_screen <mã màn>` (dashboard, students, student-profile, class-analysis, prediction, model-evaluation, reports, data-management). Cần đối chiếu thị giác thì dùng `include_reference=true`.
3. **Khi viết UI:**
   - Chỉ dùng component trong `components/ui`.
   - Không tự thêm màu, font, gradient, bóng mờ, sidebar, emoji.
   - Gọi API backend `/api/v1` thật, có loading/empty/error.
4. **Sau mỗi file UI:** gọi `audit_ui` với toàn bộ nội dung file, sửa đến khi verdict là "ĐẠT". Báo lại điểm audit khi xong mỗi màn.

## Quy tắc dữ liệu của đề tài
- Dữ liệu giả lập phải có `DemoBadge`. Xác suất mô hình chưa có nhãn tuyển sinh thật phải ghi **DEMO**, không trình bày như kết quả khoa học.
- Không bịa điểm chuẩn hay thông tin cá nhân. Thiếu dữ liệu thì hiển thị trạng thái trống và cho phép nhập.
- Danh sách học sinh cần chú ý luôn kèm câu: "Chỉ dựa trên điểm số, không dùng để đánh giá hoàn cảnh hay năng lực".
- Số thập phân dùng dấu phẩy (`7,12`).

## Thứ tự làm
dashboard → students → student-profile → class-analysis → prediction → model-evaluation → reports → data-management.
