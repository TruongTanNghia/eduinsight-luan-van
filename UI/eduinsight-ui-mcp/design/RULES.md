# EduInsight · Sticker lớp học — Luật UI bắt buộc

Đọc toàn bộ trước khi viết bất kỳ component hay trang nào. Sau khi viết xong, gọi tool `audit_ui` với mã nguồn để tự kiểm tra.

## 1. Bản sắc
- Phong cách neo-brutalist vui tươi cho trường THCS: **nền vàng bơ chấm bi, viền đen 2.5px, bóng đổ cứng `5px 5px 0 #111` (không blur), khối màu rực**.
- Font duy nhất cho chữ: **Bricolage Grotesque** (800 cho tiêu đề, 500–700 cho thân). Số liệu: **JetBrains Mono** + `tabular-nums`. Nạp bằng `next/font/google` với `subsets: ["latin","vietnamese"]`.
- Bảng màu đóng: ink `#111111`, paper `#FFF4D6`, yellow `#FFD23F`, cobalt `#2B59FF`, tomato `#FF5A36`, mint `#3DDC97`, pink `#FF8FC7`, lilac `#B8A4FF`, cùng các tông phụ trong `tokens.json`. **Không thêm màu ngoài bảng.**

## 2. Cấm tuyệt đối
- Gradient nền/chữ/nút (`bg-gradient-*`, `linear-gradient`, `from-* to-*`), trừ nền chấm bi `radial-gradient` của body.
- Bóng mờ (`shadow-md/lg/xl/2xl`, `box-shadow` có blur), glow, glassmorphism, `backdrop-blur`.
- Sidebar điều hướng. Điều hướng là **thanh trên cùng** với logo sticker nghiêng + nút tròn viền đen (`AppShell`).
- Font Inter, Roboto, Arial, Poppins, Geist làm font hiển thị.
- Màu tím/indigo/violet kiểu Tailwind mặc định (`indigo-*`, `violet-*`, `purple-*`), xám slate/gray mặc định cho chữ.
- Emoji thay icon. Dùng `lucide-react` (stroke 2–2.5, màu `currentColor`).
- Card bo góc kèm viền màu một bên (left-border accent).
- KPI/biểu đồ không có định nghĩa hoặc nguồn dữ liệu.

## 3. Thành phần
| Việc | Dùng | Ghi chú |
|---|---|---|
| Khung trang | `AppShell` | max-w 1400px, px-8 (mobile px-4), gap-7 giữa section |
| Mọi khối nội dung | `Sticker` | `rounded-xl border-[2.5px] border-ink shadow-sticker p-6` |
| Khối hero / tóm tắt | `Sticker tone="yellow"` | tiêu đề 54px/800, có 1 cụm số nổi bật đảo màu đen–vàng nghiêng -1.5° |
| KPI | `StatSticker` | tối đa 4–6 thẻ, nghiêng xen kẽ `[-1.5, 1.2, 1, -1.2]`, số 52px/800 |
| Nút | `Button` / `buttonClass` | primary cobalt, dark (đen chữ vàng), outline, danger; luôn `shadow-btn` |
| Nhãn | `Tag`, `TrendTag`, `DemoBadge` | viền 2px, chữ 12px/700 |
| Form | `SelectField`, `TextField`, `FilterBar` | cao 44px, viền 2.5px, bo 12px |
| Lựa chọn | `Segmented`, `ToggleChips` | mục chọn: cobalt chữ trắng hoặc vàng, có `shadow-btn` |
| Bảng | `DataTable` trong `Sticker className="p-0"` | đầu bảng `bg-table-head`, viền dưới 2.5px đen |
| Biểu đồ | `TrendLineChart`, `SubjectBarChart` (Recharts) | đường 6px, chấm vàng viền đen r=9; cột viền đen 2.5px, bo trên 10px |
| Trạng thái | `LoadingSticker`, `EmptySticker`, `ErrorSticker` | bắt buộc cho mọi khối gọi API |

## 4. Màu theo ý nghĩa (luôn kèm chữ, không chỉ màu)
- Tiến bộ / hợp lệ: mint `#3DDC97` (chữ trên nền trắng: `#0A7A4B`).
- Sa sút / lỗi / dưới ngưỡng: tomato `#FF5A36` (chữ: `#C2290F`).
- Cảnh báo / cần xem lại: lilac `#B8A4FF` hoặc warning `#FFE9A8` (chữ `#B54708`).
- Ổn định / thiếu dữ liệu: neutral `#F6EFD9`.
- Dữ liệu chính: cobalt `#2B59FF`. Lựa chọn đang bật / nhấn mạnh: yellow `#FFD23F`.
- Mức TT22: Tốt cobalt · Khá mint · Đạt yellow · Chưa đạt tomato.

## 5. Bố cục
- Grid responsive: `grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6` cho cặp biểu đồ; `minmax(min(250px,100%),1fr)` cho lưới thẻ.
- Chỉ nghiêng: logo, thẻ KPI, nhãn nổi bật trong hero. **Không nghiêng bảng, biểu đồ, form.**
- Mỗi màn có một trọng tâm. Không nhồi quá 6 khối trên một màn hình đầu.
- Mobile: nav tự xuống dòng; bảng rộng nằm trong `overflow-x-auto`; lưới về 1 cột.

## 6. Nội dung và dữ liệu (theo đề tài)
- Ngôn ngữ: tiếng Việt, xưng hô thân thiện ("các bạn", "thầy cô") nhưng không suồng sã.
- Số thập phân dùng dấu phẩy: `7,12`. Định dạng: `v.toFixed(2).replace(".", ",")`.
- Mọi trang có dữ liệu giả lập phải có `DemoBadge`. Kết quả mô hình chưa có nhãn thật: ghi **DEMO**, không trình bày như kết quả khoa học.
- Danh sách "cần chú ý": luôn kèm câu "Chỉ dựa trên điểm số, không dùng để đánh giá hoàn cảnh hay năng lực".
- Phân biệt rõ chip **"Thực tế · tính từ dữ liệu"** và **"Dự đoán mô hình"**.
- Không bịa điểm chuẩn, không bịa thông tin cá nhân. Chỗ thiếu: placeholder `[Tên trường]`.

## 7. Truy cập
- Vùng bấm ≥ 44px. Dùng `<button>`, `<a>`, `<label>` + `<input>` thật.
- Nút chỉ có icon phải có `aria-label`. Biểu đồ SVG có `role="img"` + `aria-label` mô tả xu hướng.
- Tương phản chữ ≥ 4.5:1: chữ trắng chỉ đặt trên cobalt hoặc ink; trên mint/yellow/pink/lilac/tomato dùng chữ đen.
- `focus-visible` viền cobalt 3px (đã có trong globals.css).
