#!/usr/bin/env node
// EduInsight UI MCP — cung cấp design system "Sticker lớp học" cho agent lập trình.
// Chạy qua stdio: node server.mjs
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "design");
const read = (...p) => readFileSync(join(ROOT, ...p), "utf8");
const tokens = JSON.parse(read("tokens.json"));

const SCREENS = {
  dashboard: { file: "dashboard.md", ref: "Main.dc.html", route: "/dashboard", title: "Tổng quan" },
  students: { file: "students.md", ref: "Students.dc.html", route: "/students", title: "Danh sách học sinh" },
  "student-profile": { file: "student-profile.md", ref: "StudentProfile.dc.html", route: "/students/[id]", title: "Hồ sơ học sinh" },
  "class-analysis": { file: "class-analysis.md", ref: "ClassAnalysis.dc.html", route: "/classes/[id]", title: "Phân tích lớp học" },
  prediction: { file: "prediction.md", ref: "Prediction.dc.html", route: "/predictions", title: "Dự đoán & định hướng" },
  "model-evaluation": { file: "model-evaluation.md", ref: "ModelEval.dc.html", route: "/model-evaluation", title: "Đánh giá mô hình" },
  reports: { file: "reports.md", ref: "Reports.dc.html", route: "/reports", title: "Báo cáo" },
  "data-management": { file: "data-management.md", ref: "DataManagement.dc.html", route: "/data-management", title: "Quản lý dữ liệu" },
};
const SCREEN_IDS = Object.keys(SCREENS);

const COMPONENTS = {
  cn: { file: "cn.ts", path: "components/ui/cn.ts", desc: "Helper gộp className" },
  layout: { file: "layout.tsx", path: "app/layout.tsx", desc: "Root layout: next/font Bricolage + JetBrains Mono (subset vietnamese) + AppShell" },
  "app-shell": { file: "app-shell.tsx", path: "components/ui/app-shell.tsx", desc: "Thanh trên cùng: logo sticker nghiêng + nav nút tròn; khung trang max-w 1400px" },
  sticker: { file: "sticker.tsx", path: "components/ui/sticker.tsx", desc: "Sticker (khối nội dung chuẩn, 7 tone, nghiêng tùy chọn) + StickerHeader" },
  button: { file: "button.tsx", path: "components/ui/button.tsx", desc: "Button + buttonClass: primary / dark / outline / danger, bóng cứng" },
  tag: { file: "tag.tsx", path: "components/ui/tag.tsx", desc: "Tag, DemoBadge (bắt buộc với dữ liệu giả lập), TrendTag" },
  "stat-sticker": { file: "stat-sticker.tsx", path: "components/ui/stat-sticker.tsx", desc: "Thẻ KPI số lớn, nghiêng xen kẽ" },
  field: { file: "field.tsx", path: "components/ui/field.tsx", desc: "SelectField, TextField, FilterBar" },
  segmented: { file: "segmented.tsx", path: "components/ui/segmented.tsx", desc: "Segmented (chọn 1) và ToggleChips (chọn nhiều)" },
  "data-table": { file: "data-table.tsx", path: "components/ui/data-table.tsx", desc: "DataTable có đầu bảng vàng nhạt, empty state" },
  states: { file: "states.tsx", path: "components/ui/states.tsx", desc: "LoadingSticker, EmptySticker, ErrorSticker" },
  charts: { file: "charts.tsx", path: "components/ui/charts.tsx", desc: "Theme Recharts + TrendLineChart, SubjectBarChart, StickerTooltip" },
};
const COMPONENT_IDS = Object.keys(COMPONENTS);

const text = (t) => ({ content: [{ type: "text", text: t }] });

// ---------- Kiểm tra UI ----------
const ALLOWED_HEX = new Set(
  [
    ...Object.values(tokens.color),
    ...Object.values(tokens.semantic).flatMap((s) => [s.bg, s.fg, s.text].filter(Boolean)),
    ...tokens.chart.series,
    "#FFC2B3", "#FEF3F2", "#E8DDBE", "#F6EFD9", "#0A7A4B", "#C2290F", "#B54708", "#FFFFFF", "#000000",
  ].map((h) => h.toUpperCase())
);

function audit(code) {
  const findings = [];
  const add = (level, rule, message, fix, sample) => findings.push({ level, rule, message, fix, sample });
  const lines = code.split("\n");
  const find = (re) => {
    const out = [];
    lines.forEach((l, i) => { if (re.test(l)) out.push(`L${i + 1}: ${l.trim().slice(0, 140)}`); re.lastIndex = 0; });
    return out;
  };

  const grad = find(/linear-gradient|conic-gradient|bg-gradient-|\bfrom-[a-z]+-\d{2,3}\b.*\bto-[a-z]+-\d{2,3}\b/);
  if (grad.length) add("error", "no-gradient", "Phong cách C không dùng gradient (chỉ nền chấm bi radial-gradient của body).", "Thay bằng màu khối đặc trong tokens: bg-cobalt / bg-yellow / bg-mint…", grad.slice(0, 5));

  const blur = find(/\bshadow-(sm|md|lg|xl|2xl|inner)\b|drop-shadow|backdrop-blur|\bblur-|box-shadow:\s*[^;]*\d+px\s+\d+px\s+[1-9]\d*px/);
  if (blur.length) add("error", "hard-shadow-only", "Chỉ dùng bóng cứng không blur.", "Dùng shadow-sticker (5px 5px 0 #111), shadow-btn (3px 3px 0) hoặc shadow-selected (4px 4px 0).", blur.slice(0, 5));

  const fonts = find(/\b(Inter|Roboto|Arial|Poppins|Geist|Helvetica|Montserrat)\b/);
  if (fonts.length) add("error", "font", "Font không thuộc design system.", "Dùng font-sans (Bricolage Grotesque) cho chữ và font-mono / class num (JetBrains Mono) cho số.", fonts.slice(0, 5));

  const twPalette = find(/\b(?:bg|text|border|from|to|via|ring|fill|stroke|outline|divide|accent|decoration)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/);
  if (twPalette.length) add("error", "palette", "Dùng màu Tailwind mặc định thay vì token.", "Thay bằng token: ink, paper, surface, yellow, cobalt, tomato, mint, pink, lilac, muted, line, table-head, positive-text, negative-text…", twPalette.slice(0, 6));

  const hexes = [...new Set((code.match(/#[0-9a-fA-F]{6}\b/g) || []).map((h) => h.toUpperCase()))].filter((h) => !ALLOWED_HEX.has(h));
  if (hexes.length) add("warning", "hex-outside-palette", `Màu ngoài bảng: ${hexes.join(", ")}`, "Ánh xạ về màu gần nhất trong tokens.json (get_design_tokens).");

  const side = find(/<aside\b|[Ss]idebar/);
  if (side.length) add("error", "no-sidebar", "Phong cách C không có sidebar.", "Dùng AppShell (thanh trên cùng với nav dạng nút tròn).", side.slice(0, 3));

  const emoji = find(/\p{Extended_Pictographic}/u);
  if (emoji.length) add("error", "no-emoji", "Không dùng emoji thay icon.", "Dùng lucide-react, stroke 2–2.5, màu currentColor.", emoji.slice(0, 3));

  const whiteOnLight = find(/text-white[^"'`]*\bbg-(yellow|mint|pink|lilac|tomato|amber|warning|neutral)\b|\bbg-(yellow|mint|pink|lilac|tomato|amber|warning|neutral)\b[^"'`]*text-white/);
  if (whiteOnLight.length) add("error", "contrast", "Chữ trắng trên nền sáng không đủ tương phản 4.5:1.", "Chữ trắng chỉ trên bg-cobalt hoặc bg-ink; còn lại dùng text-ink.", whiteOnLight.slice(0, 4));

  const thinCard = find(/\brounded-(lg|xl|2xl|3xl)\b(?![^"'`]*border-\[2(\.5)?px\])[^"'`]*\bborder\b(?!-)/);
  if (thinCard.length) add("warning", "thick-border", "Khối bo góc với viền 1px — phong cách C dùng viền đen 2.5px.", "Dùng <Sticker> hoặc thêm border-[2.5px] border-ink shadow-sticker.", thinCard.slice(0, 4));

  const sideAccent = find(/\bborder-l-(4|8|\[\d+px\])\b/);
  if (sideAccent.length) add("warning", "no-side-accent", "Tránh card có viền màu một bên.", "Dùng Tag màu hoặc tone của Sticker.", sideAccent.slice(0, 3));

  const dot = find(/toFixed\(\d\)(?!\s*\.replace)/);
  if (dot.length) add("warning", "vi-decimal", "Số thập phân tiếng Việt dùng dấu phẩy.", 'Dùng v.toFixed(2).replace(".", ",") hoặc Intl.NumberFormat("vi-VN").', dot.slice(0, 4));

  const imgs = find(/<img\b(?![^>]*\balt=)/);
  if (imgs.length) add("error", "a11y-img-alt", "Ảnh thiếu alt.", "Thêm alt mô tả, hoặc alt=\"\" nếu chỉ trang trí.", imgs.slice(0, 3));

  const iconBtn = find(/<button\b(?![^>]*aria-label)[^>]*>\s*<[A-Z][A-Za-z]+\s[^>]*\/>\s*<\/button>/);
  if (iconBtn.length) add("error", "a11y-icon-button", "Nút chỉ có icon thiếu aria-label.", "Thêm aria-label tiếng Việt.", iconBtn.slice(0, 3));

  const clickDiv = find(/<(div|span)\b[^>]*onClick=/);
  if (clickDiv.length) add("error", "a11y-real-controls", "Dùng div/span có onClick thay cho nút.", "Dùng <button type=\"button\"> hoặc <Link>.", clickDiv.slice(0, 3));

  if (/\b(mock|faker|demoData|sample(Data|Students)|seed)\b/i.test(code) && !/DemoBadge|DEMO|Dữ liệu minh họa/.test(code))
    add("warning", "demo-label", "Có dấu hiệu dữ liệu giả lập nhưng thiếu nhãn.", "Thêm <DemoBadge /> ở tiêu đề trang hoặc Tag \"DEMO\" cạnh số liệu mô hình.");

  if (/(predict|probab|xác suất)/i.test(code) && !/DEMO|calibrat|hiệu chỉnh|khoảng tin cậy|confidence/i.test(code))
    add("warning", "honest-ai", "Hiển thị xác suất/dự đoán mà không ghi trạng thái kiểm chứng.", "Ghi DEMO nếu chưa có nhãn thật, hoặc kèm phiên bản mô hình + độ hiệu chỉnh/khoảng tin cậy.");

  if (/useEffect\([^)]*fetch|useQuery|fetch\(/.test(code) && !/Loading|Skeleton|aria-busy/.test(code))
    add("warning", "states", "Gọi API nhưng không thấy trạng thái loading.", "Dùng LoadingSticker / EmptySticker / ErrorSticker (get_component states).");

  if (/<(main|section|div)[^>]*>/.test(code) && !/Sticker|sticker|shadow-sticker/.test(code) && code.length > 400)
    add("info", "use-sticker", "Không thấy Sticker trong đoạn mã giao diện.", "Mọi khối nội dung nên bọc trong <Sticker>.");

  const errors = findings.filter((f) => f.level === "error").length;
  const warnings = findings.filter((f) => f.level === "warning").length;
  const score = Math.max(0, 100 - errors * 15 - warnings * 5);
  return { score, verdict: errors ? "CHƯA ĐẠT — sửa các lỗi error rồi chạy lại audit_ui" : warnings ? "ĐẠT CÓ ĐIỀU KIỆN — xem warning" : "ĐẠT chuẩn Sticker lớp học", errors, warnings, findings };
}

// ---------- Server ----------
const server = new McpServer(
  { name: "eduinsight-ui", version: "1.0.0" },
  {
    instructions:
      "Design system 'Sticker lớp học' của EduInsight AI (Next.js 16 + Tailwind v4 + Recharts). Trước khi viết UI: gọi get_design_rules, rồi get_screen cho màn cần làm, get_component cho các component cần dùng. Sau khi viết: gọi audit_ui với mã nguồn và sửa đến khi không còn lỗi error. Không tự chế màu, font, bóng đổ ngoài tokens.",
  }
);

server.registerTool(
  "get_design_rules",
  { title: "Luật UI bắt buộc", description: "Toàn bộ luật thiết kế phong cách Sticker lớp học: bản sắc, điều cấm, bảng component, màu theo ý nghĩa, bố cục, nội dung, truy cập. Gọi đầu tiên.", inputSchema: {} },
  async () => text(read("RULES.md"))
);

server.registerTool(
  "get_design_tokens",
  {
    title: "Design tokens",
    description: "Lấy token màu, font, viền, bo góc, bóng đổ, biểu đồ. format=json (tokens.json) hoặc css (globals.css Tailwind v4 @theme dán thẳng vào app/globals.css).",
    inputSchema: { format: z.enum(["json", "css"]).default("json").describe("json hoặc css") },
  },
  async ({ format }) => text(format === "css" ? read("globals.css") : JSON.stringify(tokens, null, 2))
);

server.registerTool(
  "list_components",
  { title: "Danh sách component", description: "Liệt kê component React/Tailwind có sẵn và đường dẫn nên đặt trong dự án Next.js.", inputSchema: {} },
  async () => text(COMPONENT_IDS.map((id) => `- ${id} → ${COMPONENTS[id].path}: ${COMPONENTS[id].desc}`).join("\n"))
);

server.registerTool(
  "get_component",
  {
    title: "Lấy mã component",
    description: "Trả về mã nguồn TSX của component. Dùng name='all' để lấy toàn bộ thư viện (kèm đường dẫn file đích).",
    inputSchema: { name: z.enum([...COMPONENT_IDS, "all"]).describe("Tên component hoặc 'all'") },
  },
  async ({ name }) => {
    const ids = name === "all" ? COMPONENT_IDS : [name];
    return text(ids.map((id) => `// ===== ${COMPONENTS[id].path} =====\n${read("components", COMPONENTS[id].file)}`).join("\n\n"));
  }
);

server.registerTool(
  "list_screens",
  { title: "Danh sách màn hình", description: "8 màn hình của EduInsight AI với route Next.js.", inputSchema: {} },
  async () => text(SCREEN_IDS.map((id) => `- ${id} → ${SCREENS[id].route} · ${SCREENS[id].title}`).join("\n"))
);

server.registerTool(
  "get_screen",
  {
    title: "Đặc tả màn hình",
    description: "Đặc tả chi tiết một màn hình: API, bố cục từng khối, component, trạng thái, quy tắc dữ liệu. include_reference=true để kèm HTML thiết kế gốc (định dạng .dc.html: <sc-for>/<sc-if> là vòng lặp/điều kiện, {{x}} là dữ liệu; dùng làm chuẩn thị giác, KHÔNG copy nguyên).",
    inputSchema: {
      screen: z.enum(SCREEN_IDS).describe("Mã màn hình"),
      include_reference: z.boolean().default(false).describe("Kèm HTML thiết kế gốc (dài)"),
    },
  },
  async ({ screen, include_reference }) => {
    const s = SCREENS[screen];
    let out = read("screens", s.file);
    if (include_reference) out += `\n\n---\n## HTML thiết kế gốc (${s.ref})\n\`\`\`html\n${read("reference", s.ref)}\n\`\`\``;
    return text(out);
  }
);

server.registerTool(
  "get_setup_guide",
  { title: "Hướng dẫn cài vào dự án", description: "Các bước đưa design system vào dự án Next.js 16 (frontend/ của EduInsight AI).", inputSchema: {} },
  async () =>
    text(`# Cài design system vào frontend Next.js 16
1. Cài thư viện: \`npm i recharts lucide-react\` (Tailwind v4 đã có sẵn khi tạo app bằng create-next-app).
2. Gọi get_design_tokens format=css → ghi đè app/globals.css.
3. Gọi get_component name=all → tạo từng file theo đường dẫn ghi ở đầu mỗi khối (components/ui/*, app/layout.tsx).
4. Đảm bảo tsconfig có alias "@/*": ["./*"].
5. Tạo route theo list_screens (app/dashboard/page.tsx, app/students/page.tsx, app/students/[id]/page.tsx, app/classes/[id]/page.tsx, app/predictions/page.tsx, app/model-evaluation/page.tsx, app/reports/page.tsx, app/data-management/page.tsx). app/page.tsx redirect('/dashboard').
6. Với mỗi màn: get_screen → dựng UI bằng component có sẵn → gọi API backend /api/v1 (không hardcode khi đã có API) → audit_ui → sửa đến khi verdict ĐẠT.
7. Định dạng số: Intl.NumberFormat("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).`)
);

server.registerTool(
  "audit_ui",
  {
    title: "Kiểm tra UI theo chuẩn",
    description: "Quét mã TSX/JSX/CSS/HTML để phát hiện vi phạm phong cách Sticker lớp học (gradient, bóng mờ, font lạ, màu Tailwind mặc định, sidebar, emoji, tương phản, viền mỏng, a11y, nhãn DEMO, trạng thái loading). Trả về điểm, verdict và cách sửa.",
    inputSchema: {
      code: z.string().min(1).describe("Mã nguồn cần kiểm tra"),
      filename: z.string().optional().describe("Tên file (để báo cáo)"),
    },
  },
  async ({ code, filename }) => {
    const r = audit(code);
    return text(JSON.stringify({ file: filename ?? null, ...r }, null, 2));
  }
);

// Prompt dựng màn hình (cho client hỗ trợ prompts, VD Claude Code: /mcp__eduinsight-ui__build_screen)
server.registerPrompt(
  "build_screen",
  {
    title: "Dựng một màn hình theo chuẩn",
    description: "Nạp luật + đặc tả màn hình + danh sách component để dựng đúng chuẩn.",
    argsSchema: { screen: z.enum(SCREEN_IDS).describe("Mã màn hình") },
  },
  ({ screen }) => {
    const s = SCREENS[screen];
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Dựng màn hình "${s.title}" tại route ${s.route} cho EduInsight AI (Next.js 16, TypeScript, Tailwind v4, Recharts, lucide-react).

Bắt buộc tuân thủ design system dưới đây. Chỉ dùng component trong components/ui (nếu chưa có thì tạo từ get_component). Gọi API backend thật; có loading/empty/error. Xong thì chạy audit_ui với từng file và sửa đến khi không còn lỗi error.

=== LUẬT ===
${read("RULES.md")}

=== ĐẶC TẢ MÀN HÌNH ===
${read("screens", s.file)}

=== COMPONENT CÓ SẴN ===
${COMPONENT_IDS.map((id) => `- ${id} (${COMPONENTS[id].path}): ${COMPONENTS[id].desc}`).join("\n")}`,
          },
        },
      ],
    };
  }
);

// Resources cho client hỗ trợ đọc tài nguyên
server.registerResource("rules", "eduinsight://rules", { title: "Luật UI", mimeType: "text/markdown" }, async (uri) => ({ contents: [{ uri: uri.href, text: read("RULES.md") }] }));
server.registerResource("tokens", "eduinsight://tokens.json", { title: "Design tokens", mimeType: "application/json" }, async (uri) => ({ contents: [{ uri: uri.href, text: read("tokens.json") }] }));
server.registerResource("globals-css", "eduinsight://globals.css", { title: "Tailwind v4 theme", mimeType: "text/css" }, async (uri) => ({ contents: [{ uri: uri.href, text: read("globals.css") }] }));
for (const id of SCREEN_IDS) {
  server.registerResource(`screen-${id}`, `eduinsight://screens/${id}`, { title: `Màn hình · ${SCREENS[id].title}`, mimeType: "text/markdown" }, async (uri) => ({ contents: [{ uri: uri.href, text: read("screens", SCREENS[id].file) }] }));
}

// Kiểm tra toàn vẹn file khi khởi động
for (const f of readdirSync(join(ROOT, "reference"))) if (!f.endsWith(".dc.html")) console.error(`[eduinsight-ui] bỏ qua file lạ: ${f}`);

await server.connect(new StdioServerTransport());
console.error("[eduinsight-ui] MCP server đang chạy (stdio)");
