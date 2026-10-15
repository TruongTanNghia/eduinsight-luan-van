# eduinsight-ui-mcp

MCP server chứa toàn bộ design system **"Sticker lớp học"** của EduInsight AI. Cắm vào Claude Code, Cursor, Claude Desktop, VS Code hay Windsurf để agent dựng UI Next.js đúng chuẩn đã chốt:
- nền vàng bơ chấm bi
- viền đen 2.5px, bóng đổ cứng
- màu khối rực
- font Bricolage Grotesque

## Cài nhanh 3 bước (Windows + Claude Code)

1. Giải nén zip vào thư mục cố định, ví dụ `D:\tools\eduinsight-ui-mcp` (không để trong Downloads rồi xóa đi).
2. Mở terminal:
   ```bash
   cd D:\tools\eduinsight-ui-mcp
   npm install
   npm test
   ```
   Thấy dòng `TOOLS: get_design_rules, get_design_tokens, …, audit_ui` và `GOOD: 100 ĐẠT chuẩn` là cài đúng.
3. Mở terminal ở thư mục dự án EduInsight:
   ```bash
   claude mcp add --scope project eduinsight-ui -- node D:\tools\eduinsight-ui-mcp\server.mjs
   ```
   Chép file `CLAUDE.md` trong gói này vào thư mục gốc dự án. Mở Claude Code, gõ `/mcp`, thấy `eduinsight-ui ✔ connected` là xong.
   Thử ngay: `/mcp__eduinsight-ui__build_screen dashboard`

macOS/Linux: làm y hệt, chỉ thay đường dẫn kiểu `/Users/ten/tools/eduinsight-ui-mcp/server.mjs`.

## Có gì bên trong

| Tool | Dùng để |
|---|---|
| `get_design_rules` | Luật UI bắt buộc (bản sắc, điều cấm, màu theo ý nghĩa, bố cục, a11y, quy tắc dữ liệu của đề tài) |
| `get_design_tokens` | `format=json`: token đầy đủ · `format=css`: `globals.css` Tailwind v4 `@theme` dán thẳng vào dự án |
| `list_components` / `get_component` | 12 file React/TSX có sẵn: AppShell, Sticker, Button, Tag/DemoBadge/TrendTag, StatSticker, Field/FilterBar, Segmented/ToggleChips, DataTable, Loading/Empty/Error, Recharts theme |
| `list_screens` / `get_screen` | Đặc tả 8 màn hình (route, API, bố cục từng khối, trạng thái, quy tắc dữ liệu); `include_reference=true` kèm HTML thiết kế gốc |
| `get_setup_guide` | Các bước đưa vào `frontend/` Next.js 16 |
| `audit_ui` | Quét mã vừa viết, chấm điểm, chỉ ra vi phạm và cách sửa: gradient, bóng mờ, font lạ, màu Tailwind mặc định, sidebar, emoji, chữ trắng trên nền sáng, viền mỏng, thiếu alt/aria, div bấm được, thiếu nhãn DEMO, thiếu loading, số thập phân dấu chấm |

Ngoài ra có **prompt `build_screen`** và **resources** `eduinsight://rules`, `eduinsight://tokens.json`, `eduinsight://globals.css`, `eduinsight://screens/{id}`.

## Cài đặt

Yêu cầu Node.js 18 trở lên.

```bash
cd eduinsight-ui-mcp
npm install
npm test        # tự khởi động server và gọi thử toàn bộ tool
```

Trong các ví dụ dưới, thay `/ĐƯỜNG/DẪN/eduinsight-ui-mcp` bằng đường dẫn tuyệt đối thật trên máy anh. Trên Windows viết dạng `C:\\Users\\...\\eduinsight-ui-mcp\\server.mjs`.

### Claude Code
```bash
claude mcp add eduinsight-ui -- node /ĐƯỜNG/DẪN/eduinsight-ui-mcp/server.mjs
# dùng chung cho cả repo (ghi vào .mcp.json):
claude mcp add --scope project eduinsight-ui -- node /ĐƯỜNG/DẪN/eduinsight-ui-mcp/server.mjs
```
Kiểm tra bằng lệnh `/mcp` trong Claude Code. Dựng nhanh một màn: `/mcp__eduinsight-ui__build_screen dashboard`.

### Cursor: `.cursor/mcp.json` trong repo (hoặc `~/.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "eduinsight-ui": { "command": "node", "args": ["/ĐƯỜNG/DẪN/eduinsight-ui-mcp/server.mjs"] }
  }
}
```

### Claude Desktop
Mở Settings → Developer → Edit Config, rồi thêm khối giống Cursor vào `mcpServers` và khởi động lại app.

### VS Code (Copilot agent): `.vscode/mcp.json`
```json
{ "servers": { "eduinsight-ui": { "type": "stdio", "command": "node", "args": ["/ĐƯỜNG/DẪN/eduinsight-ui-mcp/server.mjs"] } } }
```

### Windsurf: `~/.codeium/windsurf/mcp_config.json`
Dùng cùng định dạng `mcpServers` như Cursor.

## Quy trình vibe chuẩn

Dán đoạn này vào agent ở lần đầu (hoặc đưa vào `CLAUDE.md` / `.cursorrules` của repo):

```
Dự án EduInsight AI dùng design system "Sticker lớp học" từ MCP eduinsight-ui.
1. Lần đầu: gọi get_setup_guide, rồi get_design_tokens format=css và get_component name=all để tạo đủ file nền.
2. Mỗi màn hình: gọi get_design_rules + get_screen <mã màn>; chỉ dùng component trong components/ui; gọi API /api/v1 thật; có loading/empty/error.
3. Sau mỗi file UI: gọi audit_ui với nội dung file, sửa đến khi verdict "ĐẠT". Không tự thêm màu, font, gradient, bóng mờ, sidebar.
4. Dữ liệu giả lập phải có DemoBadge; xác suất mô hình chưa có nhãn thật phải ghi DEMO.
```

Thứ tự nên làm: `dashboard` → `students` → `student-profile` → `class-analysis` → `prediction` → `model-evaluation` → `reports` → `data-management`.

## Cấu trúc thư mục

```
eduinsight-ui-mcp/
├── server.mjs              # MCP server (stdio)
├── CLAUDE.md               # chép vào gốc dự án để agent luôn theo chuẩn
├── test-client.mjs         # kiểm thử
├── design/
│   ├── RULES.md            # luật UI
│   ├── tokens.json         # design tokens
│   ├── globals.css         # Tailwind v4 theme
│   ├── components/*.tsx    # thư viện component React
│   ├── screens/*.md        # đặc tả 8 màn hình
│   └── reference/*.dc.html # HTML thiết kế gốc từ canvas
└── package.json
```

## Chỉnh sửa design system

Sửa trực tiếp các file trong `design/` rồi khởi động lại MCP trong client. `audit_ui` lấy danh sách màu hợp lệ từ `tokens.json`, nên thêm màu mới vào đó trước.

## Gỡ lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `node` không phải lệnh hợp lệ | Cài Node.js 18 trở lên từ nodejs.org, mở lại terminal |
| `/mcp` báo `failed` hoặc không thấy server | Kiểm tra đường dẫn tới `server.mjs` là đường dẫn tuyệt đối và tồn tại; chạy thử `node <đường dẫn>/server.mjs`, thấy dòng "MCP server đang chạy" (Ctrl+C để thoát) |
| `Cannot find package '@modelcontextprotocol/sdk'` | Chưa chạy `npm install` trong thư mục `eduinsight-ui-mcp` |
| Windows báo lỗi đường dẫn trong file JSON | Trong JSON phải viết `\\`: `"D:\\tools\\eduinsight-ui-mcp\\server.mjs"` (hoặc dùng `/`) |
| Agent vẫn tự chế màu/gradient | Kiểm tra đã có `CLAUDE.md` ở gốc dự án; nhắc agent "gọi audit_ui cho file vừa sửa" |
| Sửa luật/tokens nhưng agent không thấy | Khởi động lại MCP: thoát Claude Code mở lại, hoặc tắt/bật server trong `/mcp` |
| Muốn gỡ | `claude mcp remove eduinsight-ui` |

## Lưu ý

- Component viết cho **Next.js App Router + Tailwind CSS v4 + Recharts 2 + lucide-react**, đã kiểm tra kiểu với TypeScript strict.
- `audit_ui` là bộ kiểm tra tĩnh theo mẫu (regex), giúp bắt lỗi phổ biến nhanh. Nó không thay được việc mở trình duyệt xem lại giao diện.
- Số liệu trong file `reference/` là dữ liệu minh họa từ bản thiết kế, không dùng làm dữ liệu thật.
