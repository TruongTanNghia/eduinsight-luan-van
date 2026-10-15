# 02 · Danh sách học sinh — `/students`
Tham chiếu: `reference/Students.dc.html`

**API:** `GET /api/v1/students?q=&class=&year=&status=&sort=avg|delta|name&dir=asc|desc&page=&size=20`

## Bố cục
1. Tiêu đề h1 30px "Danh sách học sinh" + `DemoBadge`; dòng phụ "Bạn đang xem học sinh thuộc phạm vi được phân quyền · Năm học … · Kỳ gần nhất …".
2. `Sticker` bộ lọc: `TextField` tìm kiếm có icon Search (lucide) chiếm rộng, `SelectField` Lớp, Năm học, Trạng thái (Theo dõi / Bình thường / Thiếu dữ liệu). Gõ tìm debounce 300ms, đồng bộ URL.
3. `Sticker className="p-0"`:
   - Dải trên: "**N** học sinh khớp bộ lọc · sắp xếp: …" và chú thích "Δ: chênh lệch ĐTB so với kỳ trước · “—” khi kỳ trước thiếu dữ liệu".
   - `DataTable` cột: Mã HS (mono) · Họ tên (bold, nút sắp xếp) · Lớp · ĐTB gần nhất (mono, phải, sắp xếp) · Δ kỳ trước (mono, màu ≥+0,3 xanh `#0A7A4B`, ≤−0,3 đỏ `#C2290F`) · Môn mạnh nhất (title giải thích tiêu chí) · Môn cần chú ý · Trạng thái (`Tag`: Theo dõi=warning, Bình thường=mint, Thiếu dữ liệu=neutral) · "Xem hồ sơ".
   - Nút sắp xếp trong `<th>` là `<button>` có icon ChevronsUpDown và `aria-sort` trên th.
   - Phân trang: nút 40px viền đen; trang hiện tại `bg-ink text-yellow`.
4. Empty: icon Search + "Không tìm thấy học sinh phù hợp" + nút "Xóa bộ lọc".

## Quy tắc
- Không gắn "sa sút" chỉ vì điểm thấp — dùng trạng thái từ API (xét biến động + số kỳ).
