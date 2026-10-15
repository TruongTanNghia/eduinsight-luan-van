"use client";
// 08 · Quản lý dữ liệu — /data-management
import { CircleAlert, CircleCheck, CircleX, FileSpreadsheet, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { apiSend, useApi, useMeta } from "@/lib/api";
import { dateVN, fmt, int } from "@/lib/format";

type Preview = { token: string; ok: boolean; file: string; size: number; sheets: number; rows: number; grade: number | null; year: string | null; valid: number; invalid: number; warnings: number;
  issues: { kind: string; title: string; detail: string }[]; schema: { col: string; type: string; required: boolean; found: boolean }[];
  preview: { row: number; sheet: string; id: string; name: string; class: string; toan: number | null; van: number | null; anh: number | null; muc: number | null; note: string; dup: boolean }[]; overwrite: number; newRecords: number };
type Schema = { schema: { col: string; type: string; required: boolean }[]; dictionary: { field: string; desc: string; missing: number }[]; version: { version: string; updated: string; records: number; students: number } };
type Hist = { version: string; file: string; valid: number; invalid: number; by: string; at: string; status: string; note: string };
const LEVEL = ["Chưa đạt", "Đạt", "Khá", "Tốt"];

export default function DataManagementPage() {
  const meta = useMeta();
  const schema = useApi<Schema>("/data/schema");
  const history = useApi<Hist[]>("/data/import/history");
  const [pv, setPv] = useState<Preview | null>(null);
  const [busy, setBusy] = useState<"preview" | "confirm" | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [agree, setAgree] = useState(false);
  const [done, setDone] = useState<{ version: string; students: number } | null>(null);
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const step = done ? 4 : pv ? 3 : 1;

  const upload = async (file: File) => {
    setBusy("preview"); setErr(null); setDone(null); setAgree(false);
    try { const fd = new FormData(); fd.append("file", file); setPv(await apiSend<Preview>("/data/import/preview", "POST", fd)); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  const confirm = async () => {
    if (!pv) return;
    setBusy("confirm"); setErr(null);
    try { setDone(await apiSend("/data/import/confirm", "POST", { token: pv.token, agree })); history.reload(); schema.reload(); meta.reload(); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  const v = schema.data?.version;

  return (
    <>
      <PageHeader title="Quản lý dữ liệu" badge="Thực tế · tính từ dữ liệu" subtitle={v ? <>Phiên bản đang dùng: <strong className="num">{v.version}</strong> · {int(v.records)} bản ghi điểm · {int(v.students)} học sinh · cập nhật {dateVN(v.updated)}</> : "Đang đọc phiên bản dữ liệu…"} />

      <Sticker className="flex flex-col gap-5">
        <ol className="m-0 flex list-none flex-wrap gap-3 p-0">
          {["Tải lên", "Kiểm tra cấu trúc", "Xem trước", "Xác nhận nhập"].map((s, i) => { const n = i + 1; const st = n < step ? "done" : n === step ? "cur" : "next"; return (
            <li key={s} aria-current={st === "cur" ? "step" : undefined} className="flex items-center gap-2 text-[13.5px] font-bold">
              <span className={`num flex size-7 items-center justify-center rounded-full border-2 border-ink text-xs ${st === "done" ? "bg-mint" : st === "cur" ? "bg-cobalt text-white" : "bg-neutral"}`}>{st === "done" ? <CircleCheck aria-hidden="true" className="size-4" strokeWidth={3} /> : n}</span>
              <span className={st === "next" ? "text-muted" : ""}>{s}</span>{i < 3 && <span aria-hidden="true" className="mx-1 text-muted">→</span>}
            </li>); })}
        </ol>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(380px,100%),1fr))] gap-4">
          <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) upload(f); }}
            className={`flex flex-col items-center gap-2.5 rounded-lg border-[2.5px] border-dashed border-cobalt px-5 py-7 text-center ${drag ? "bg-yellow" : "bg-surface-soft"}`}>
            <Upload aria-hidden="true" className="size-[30px] text-cobalt" strokeWidth={2.5} />
            <strong className="text-[15px]">Kéo thả tệp sổ điểm Excel vào đây</strong>
            <span className="text-[12.5px] font-medium text-muted">.xls, .xlsx xuất từ phần mềm sổ điểm · tối đa 20 MB · tên tệp dạng “KHOI 7-23-24.xls” · công thức trong ô được đọc như văn bản, không thực thi</span>
            <label className="press inline-flex min-h-11 cursor-pointer items-center justify-center rounded-md border-[2.5px] border-ink bg-white px-4 text-sm font-extrabold shadow-btn">Chọn tệp<input ref={inputRef} type="file" accept=".xls,.xlsx" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); }} /></label>
            <span className="text-[12.5px] font-bold">Mẫu đúng cấu trúc: 4 tệp trong data/raw/</span>
          </div>
          <div className="flex flex-col gap-3 rounded-lg border-[2.5px] border-ink p-4">
            {busy === "preview" && <LoadingSticker lines={2} title="Đang đọc tệp…" />}
            {!pv && busy !== "preview" && <span className="text-[13px] font-medium text-muted">Chưa chọn tệp. Sau khi tải lên, hệ thống kiểm tra cấu trúc, đếm dòng hợp lệ và hiển thị xem trước trước khi nhập.</span>}
            {pv && (
              <>
                <div className="flex items-center gap-3">
                  <span className="flex size-10 flex-none items-center justify-center rounded-md border-2 border-ink bg-mint"><FileSpreadsheet aria-hidden="true" className="size-5" strokeWidth={2.5} /></span>
                  <div className="flex min-w-0 flex-col"><strong className="num break-all text-[13.5px]">{pv.file}</strong><span className="text-xs font-medium text-muted">{fmt(pv.size / 1024 / 1024, 1)} MB · {pv.sheets} sheet · {int(pv.rows)} dòng · lớp {pv.grade ?? "?"} · {pv.year ?? "?"}</span></div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-md border-2 border-ink bg-mint p-3"><span className="text-[11.5px] font-bold">Hợp lệ</span><br /><strong className="num text-xl">{int(pv.valid)}</strong></div>
                  <div className="rounded-md border-2 border-ink bg-tomato p-3"><span className="text-[11.5px] font-bold">Không hợp lệ</span><br /><strong className="num text-xl">{int(pv.invalid)}</strong></div>
                  <div className="rounded-md border-2 border-ink bg-warning p-3"><span className="text-[11.5px] font-bold">Trùng khóa</span><br /><strong className="num text-xl">{int(pv.warnings)}</strong></div>
                </div>
                <span className="text-xs font-medium text-muted">Dòng không hợp lệ sẽ bị bỏ qua và được liệt kê trong bảng xem trước.</span>
              </>
            )}
            {err && <ErrorSticker message={err} />}
          </div>
        </div>
      </Sticker>

      {pv && (
        <>
          <section className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] gap-6">
            <Sticker className="p-0">
              <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Kiểm tra cấu trúc" description="So khớp cột với schema đã khai báo" /></div>
              <div className="overflow-x-auto"><table className="w-full border-collapse text-[13.5px]">
                <thead><tr>{["Cột", "Kiểu mong đợi", "Bắt buộc", "Kết quả"].map((h) => <th key={h} scope="col" className="border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-left text-xs font-bold">{h}</th>)}</tr></thead>
                <tbody>{pv.schema.map((c) => <tr key={c.col} className="hover:bg-surface-soft"><td className="num border-b-[1.5px] border-line px-3 py-2.5">{c.col}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{c.type}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{c.required ? "Có" : "Không"}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5">{c.found ? <span className="inline-flex items-center gap-1.5 font-bold text-positive-text"><CircleCheck aria-hidden="true" className="size-4" strokeWidth={2.5} />Có</span> : c.required ? <span className="inline-flex items-center gap-1.5 font-bold text-negative-text"><CircleX aria-hidden="true" className="size-4" strokeWidth={2.5} />Thiếu</span> : <span className="inline-flex items-center gap-1.5 font-bold text-warning-text"><CircleAlert aria-hidden="true" className="size-4" strokeWidth={2.5} />Không có (tùy chọn)</span>}</td></tr>)}</tbody>
              </table></div>
            </Sticker>
            <Sticker className="p-0">
              <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Lỗi và cảnh báo" description={`${pv.invalid} dòng không hợp lệ, ${pv.issues.length} vấn đề về cấu trúc`} /></div>
              {pv.issues.length === 0 ? <p className="px-5 pb-5 text-[13.5px] font-medium">Không có lỗi cấu trúc.</p> : (
                <ul className="m-0 flex list-none flex-col gap-2.5 px-5 pb-5">
                  {pv.issues.map((i, k) => <li key={k} className={`flex items-start gap-3 rounded-md border-2 border-ink p-3 ${i.kind === "Lỗi" ? "bg-tomato" : "bg-warning"}`}><Tag tone="white">{i.kind}</Tag><div className="flex flex-col gap-0.5 text-[13px]"><strong>{i.title}</strong><span className="font-medium">{i.detail}</span></div></li>)}
                </ul>
              )}
            </Sticker>
          </section>

          <Sticker className="p-0">
            <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Xem trước dữ liệu" description="8 dòng đầu và các dòng có lỗi · nền đỏ: dòng sẽ bị bỏ qua · họ tên không được lưu vào tập huấn luyện" /></div>
            <div className="overflow-x-auto"><table className="w-full border-collapse text-[13px]">
              <thead><tr>{["Dòng", "Sheet", "Mã (ẩn danh)", "Họ tên", "Lớp", "Toán", "Văn", "Anh", "Mức", "Ghi chú"].map((h, i) => <th key={h} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i >= 5 && i <= 7 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
              <tbody>{pv.preview.map((r) => (
                <tr key={`${r.sheet}-${r.row}`} className={r.note ? "bg-[#FEF3F2]" : "hover:bg-surface-soft"}>
                  <td className="num border-b-[1.5px] border-line px-3 py-2 text-muted">{r.row}</td><td className="border-b-[1.5px] border-line px-3 py-2">{r.sheet}</td><td className="num border-b-[1.5px] border-line px-3 py-2">{r.id}</td><td className="border-b-[1.5px] border-line px-3 py-2">{r.name}</td><td className="border-b-[1.5px] border-line px-3 py-2">{r.class}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.toan, 1)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.van, 1)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.anh, 1)}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2">{r.muc === null ? "—" : LEVEL[r.muc]}</td><td className="border-b-[1.5px] border-line px-3 py-2 text-[12.5px] font-bold text-negative-text">{r.note}{r.dup && !r.note && <span className="text-warning-text">trùng khóa → ghi đè</span>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          </Sticker>

          <Sticker className={`flex flex-col gap-3.5 ${pv.ok ? "" : "border-tomato"}`}>
            <StickerHeader title="Xác nhận nhập dữ liệu" description="Tạo phiên bản mới; tệp cũ cùng tên được sao lưu vào outputs/backup/ để có thể khôi phục" />
            <div className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-3 text-[13px]">
              <div><span className="text-muted">Phiên bản mới</span><br /><strong className="num">tự tăng từ {v?.version ?? "…"}</strong></div>
              <div><span className="text-muted">Bản ghi thêm mới</span><br /><strong className="num">{int(pv.newRecords)}</strong></div>
              <div><span className="text-muted">Bản ghi trùng khóa sẽ ghi đè</span><br /><strong className="num text-warning-text">{int(pv.overwrite)}</strong></div>
              <div><span className="text-muted">Mô hình bị ảnh hưởng</span><br /><strong>Cần huấn luyện lại (scripts/train.bat)</strong></div>
            </div>
            <div className="flex flex-col gap-2.5 rounded-md border-2 border-ink bg-warning px-3.5 py-3">
              <span className="text-[13px] font-medium leading-relaxed"><strong>{int(pv.overwrite)} bản ghi đã tồn tại</strong> (cùng mã học sinh và lớp) sẽ được thay bằng giá trị trong tệp. Thao tác được ghi vào lịch sử nhập.</span>
              <label className="flex min-h-9 items-center gap-2.5 text-[13.5px] font-bold"><input type="checkbox" className="size-[18px] accent-cobalt" checked={agree} onChange={(e) => setAgree(e.target.checked)} />Tôi đã xem trước dữ liệu và đồng ý ghi đè {int(pv.overwrite)} bản ghi</label>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <Button variant="outline" onClick={() => { setPv(null); setDone(null); setAgree(false); if (inputRef.current) inputRef.current.value = ""; }}>Hủy</Button>
              <Button disabled={!agree || !pv.ok || busy !== null} onClick={confirm}>{busy === "confirm" ? "Đang nhập và tính lại…" : `Xác nhận nhập ${int(pv.valid)} dòng`}</Button>
            </div>
            {!pv.ok && <span role="alert" className="text-[13px] font-bold text-negative-text">Tệp còn lỗi cấu trúc; sửa tên tệp hoặc cột rồi tải lại.</span>}
            {done && <div role="status" className="flex items-center gap-2.5 rounded-md border-2 border-ink bg-mint px-3.5 py-3 text-[13.5px] font-bold"><CircleCheck aria-hidden="true" className="size-5" strokeWidth={2.5} />Đã tạo phiên bản {done.version} · {int(done.students)} học sinh. Hãy chạy lại huấn luyện để cập nhật mô hình.</div>}
          </Sticker>
        </>
      )}

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(480px,100%),1fr))] gap-6">
        <Sticker className="p-0">
          <div className="px-5 pb-2.5 pt-[18px]"><h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Lịch sử nhập dữ liệu</h2></div>
          <div className="overflow-x-auto"><table className="w-full border-collapse text-[13.5px]">
            <thead><tr>{["Phiên bản", "Tệp nguồn", "Hợp lệ", "Lỗi", "Người nhập", "Ngày", "Trạng thái"].map((h, i) => <th key={h} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i === 2 || i === 3 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
            <tbody>{(history.data ?? []).map((h) => <tr key={h.version + h.at} className="hover:bg-surface-soft"><td className="num border-b-[1.5px] border-line px-3 py-2.5 font-bold">{h.version}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-xs">{h.file}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{int(h.valid)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{int(h.invalid)}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{h.by}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-xs">{dateVN(h.at)}</td><td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone="mint">{h.status}</Tag></td></tr>)}</tbody>
          </table>{history.data && history.data.length === 0 && <div className="px-5 py-8 text-center text-[13.5px] font-bold">Chưa có lần nhập nào qua ứng dụng. Dữ liệu hiện tại được nạp bằng scripts/prepare_data.bat.</div>}</div>
        </Sticker>
        <Sticker className="p-0">
          <div className="px-5 pb-2.5 pt-[18px]"><h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Data dictionary</h2></div>
          <div className="overflow-x-auto"><table className="w-full border-collapse text-[13.5px]">
            <thead><tr>{["Trường", "Mô tả", "% thiếu"].map((h, i) => <th key={h} scope="col" className={`border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i === 2 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
            <tbody>{(schema.data?.dictionary ?? []).map((d) => <tr key={d.field} className="hover:bg-surface-soft"><td className="num border-b-[1.5px] border-line px-3 py-2.5">{d.field}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{d.desc}</td><td className={`num border-b-[1.5px] border-line px-3 py-2.5 text-right ${d.missing >= 100 ? "font-bold text-negative-text" : ""}`}>{fmt(d.missing, 1)}%</td></tr>)}</tbody>
          </table></div>
        </Sticker>
      </section>
    </>
  );
}
