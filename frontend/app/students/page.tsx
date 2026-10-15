"use client";
// 02 · Danh sách học sinh — /students
import { ChevronLeft, ChevronRight, ChevronsUpDown, Search } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Button, buttonClass } from "@/components/ui/button";
import { SelectField } from "@/components/ui/field";
import { PeriodSelect } from "@/components/ui/period-select";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { useApi, useMeta } from "@/lib/api";
import { deltaClass, fmt, int, sgn } from "@/lib/format";

type Row = { id: string; name: string; class: string; grade: number; avg: number; delta: number | null; level: string; strong: string; weak: string | null; weakReason: string; status: string; reasons: string[]; nPeriods: number };
type Page = { total: number; page: number; size: number; pages: number; items: Row[]; counts: Record<string, number>; period: { key: string; label: string; year: string }; prevPeriod: { key: string; label: string } | null };
const STATUS_TONE: Record<string, "warning" | "mint" | "neutral"> = { "Theo dõi": "warning", "Bình thường": "mint", "Thiếu dữ liệu": "neutral" };

export default function StudentsPage() {
  return <Suspense fallback={<LoadingSticker />}><Students /></Suspense>;
}

function Students() {
  const sp = useSearchParams();
  const router = useRouter();
  const meta = useMeta();
  const q = sp.get("q") ?? "";
  const cls = sp.get("class") ?? "all";
  const period = sp.get("period") ?? "";
  const status = sp.get("status") ?? "all";
  const sort = sp.get("sort") ?? "name";
  const dir = sp.get("dir") ?? "asc";
  const page = Number(sp.get("page") ?? "1");
  const [qInput, setQInput] = useState(q);
  const set = (patch: Record<string, string | null>) => {
    const n = new URLSearchParams(sp.toString());
    for (const [k, v] of Object.entries(patch)) { if (v === null || v === "" || v === "all") n.delete(k); else n.set(k, v); }
    if (!("page" in patch)) n.delete("page");
    router.replace(`/students?${n.toString()}`);
  };
  useEffect(() => {
    const t = setTimeout(() => { if (qInput !== q) set({ q: qInput }); }, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qInput]);
  const path = `/students?q=${encodeURIComponent(q)}&class=${cls === "all" ? "" : cls}&status=${status === "all" ? "" : status}&sort=${sort}&dir=${dir}&page=${page}&size=20&period=${period}`;
  const { data, error, loading, reload } = useApi<Page>(path);
  const pkey = period || data?.period.key || meta.data?.defaultPeriod || "";
  const classes = meta.data?.classesByPeriod[pkey] ?? [];
  const toggleSort = (k: string) => set({ sort: k, dir: sort === k && dir === "asc" ? "desc" : "asc" });
  const sortLabel = { name: "họ tên", avg: "ĐTB gần nhất", delta: "Δ kỳ trước" }[sort] ?? sort;

  return (
    <>
      <PageHeader title="Danh sách học sinh" badge="Thực tế · tính từ dữ liệu"
        subtitle={<>Bạn đang xem học sinh thuộc phạm vi được phân quyền · Kỳ: <strong>{data?.period.label ?? "…"}</strong> ({data?.period.year ?? "…"}) · Δ so với {data?.prevPeriod?.label ?? "kỳ trước"}</>} />
      <Sticker className="px-5 py-4">
        <form aria-label="Bộ lọc" className="flex flex-wrap items-end gap-3" onSubmit={(e) => e.preventDefault()}>
          <label className="flex flex-1 basis-[280px] flex-col gap-1 text-xs font-bold">Tìm theo tên hoặc mã học sinh
            <span className="relative block">
              <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3 size-[18px] text-muted" strokeWidth={2.5} />
              <input type="search" value={qInput} onChange={(e) => setQInput(e.target.value)} placeholder="VD: Minh Anh hoặc HS-05C" className="h-11 w-full rounded-md border-[2.5px] border-ink bg-white pl-[38px] pr-3 text-sm font-semibold" />
            </span>
          </label>
          <PeriodSelect periods={meta.data?.periods ?? []} value={pkey} onChange={(v) => set({ period: v, class: null })} />
          <SelectField label="Lớp" value={cls} onChange={(e) => set({ class: e.target.value })}>
            <option value="all">Tất cả lớp</option>{classes.map((c) => <option key={c} value={c}>{c}</option>)}
          </SelectField>
          <SelectField label="Trạng thái" value={status} onChange={(e) => set({ status: e.target.value })}>
            <option value="all">Tất cả</option><option>Theo dõi</option><option>Bình thường</option><option>Thiếu dữ liệu</option>
          </SelectField>
        </form>
      </Sticker>

      {error && <ErrorSticker message={error} onRetry={reload} />}
      {loading && !data && <LoadingSticker lines={6} />}
      {data && (
        <Sticker className="p-0">
          <div className="flex flex-wrap items-center justify-between gap-2.5 border-b-[1.5px] border-line px-5 py-3.5">
            <span className="text-[13.5px] font-medium"><strong className="num">{int(data.total)}</strong> học sinh khớp bộ lọc · sắp xếp: <strong>{sortLabel}</strong></span>
            <span className="text-xs font-medium text-muted">Δ: chênh lệch ĐTB so với kỳ trước · “—” khi kỳ trước thiếu dữ liệu</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[13.5px]">
              <thead>
                <tr>
                  <Th>Mã HS</Th>
                  <Th sort="name" cur={sort} dir={dir} onSort={toggleSort}>Họ tên</Th>
                  <Th>Lớp</Th>
                  <Th right sort="avg" cur={sort} dir={dir} onSort={toggleSort}>ĐTB gần nhất</Th>
                  <Th right sort="delta" cur={sort} dir={dir} onSort={toggleSort}>Δ kỳ trước</Th>
                  <Th title="Môn có điểm cao hơn ĐTB lớp của môn đó nhiều nhất, kỳ gần nhất">Môn mạnh nhất</Th>
                  <Th title="Môn giảm ≥ 0,5 trong kỳ gần nhất hoặc dưới 6,5 hai kỳ liền">Môn cần chú ý</Th>
                  <Th>Trạng thái</Th>
                  <Th><span className="sr-only">Thao tác</span></Th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id} className="hover:bg-surface-soft">
                    <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-[12.5px]">{r.id}</td>
                    <td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{r.name}</td>
                    <td className="border-b-[1.5px] border-line px-3 py-2.5">{r.class}</td>
                    <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(r.avg)}</td>
                    <td className={`num border-b-[1.5px] border-line px-3 py-2.5 text-right font-bold ${deltaClass(r.delta)}`}>{sgn(r.delta)}</td>
                    <td className="border-b-[1.5px] border-line px-3 py-2.5">{r.strong}</td>
                    <td className={`border-b-[1.5px] border-line px-3 py-2.5 ${r.weak ? "text-negative-text" : "text-muted"}`}>{r.weak ? `${r.weak} · ${r.weakReason}` : "—"}</td>
                    <td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone={STATUS_TONE[r.status]}>{r.status}</Tag></td>
                    <td className="border-b-[1.5px] border-line px-3 py-2.5 text-right"><Link href={`/students/${r.id}`} className="inline-flex min-h-11 items-center text-[13px] font-bold">Xem hồ sơ</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.items.length === 0 && (
              <div className="flex flex-col items-center gap-2 px-5 py-12 text-center">
                <Search aria-hidden="true" className="size-7 text-muted" />
                <strong className="text-[15px]">Không tìm thấy học sinh phù hợp</strong>
                <span className="text-[13px] font-medium text-muted">Thử từ khóa khác hoặc bỏ bớt bộ lọc.</span>
                <Button variant="outline" onClick={() => { setQInput(""); router.replace("/students"); }}>Xóa bộ lọc</Button>
              </div>
            )}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2.5 px-5 py-3.5">
            <span className="text-[13px] font-medium text-muted">Hiển thị {data.total ? (data.page - 1) * data.size + 1 : 0}–{Math.min(data.page * data.size, data.total)} trên tổng {int(data.total)} học sinh</span>
            <nav aria-label="Phân trang" className="flex items-center gap-1.5">
              <PgBtn aria-label="Trang trước" disabled={page <= 1} onClick={() => set({ page: String(page - 1) })}><ChevronLeft className="size-4" strokeWidth={2.5} /></PgBtn>
              {pageList(page, data.pages).map((p, i) => p === 0 ? <span key={`e${i}`} className="px-1 text-muted">…</span> : (
                <PgBtn key={p} on={p === page} aria-current={p === page ? "page" : undefined} onClick={() => set({ page: String(p) })}>{p}</PgBtn>
              ))}
              <PgBtn aria-label="Trang sau" disabled={page >= data.pages} onClick={() => set({ page: String(page + 1) })}><ChevronRight className="size-4" strokeWidth={2.5} /></PgBtn>
            </nav>
          </div>
        </Sticker>
      )}
      <p className="m-0 text-[13px] font-medium text-muted">Trạng thái “Theo dõi” chỉ dựa trên điểm số (biến động so với kỳ trước, số kỳ có dữ liệu), không dùng để đánh giá hoàn cảnh hay năng lực. <Link href="/dashboard" className={buttonClass("outline", "ml-2 min-h-9 px-3")}>Về tổng quan</Link></p>
    </>
  );
}

function Th({ children, right, sort, cur, dir, onSort, title }: { children: React.ReactNode; right?: boolean; sort?: string; cur?: string; dir?: string; onSort?: (k: string) => void; title?: string }) {
  const active = sort && sort === cur;
  return (
    <th scope="col" title={title} aria-sort={active ? (dir === "asc" ? "ascending" : "descending") : undefined}
      className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${right ? "text-right" : "text-left"}`}>
      {sort && onSort ? (
        <button type="button" onClick={() => onSort(sort)} className="inline-flex min-h-9 items-center gap-1 font-bold">{children}<ChevronsUpDown aria-hidden="true" className="size-3.5" strokeWidth={2.5} /></button>
      ) : children}
    </th>
  );
}

function PgBtn({ on, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { on?: boolean }) {
  return <button type="button" className={`inline-flex size-10 items-center justify-center rounded-md border-[2.5px] border-ink text-sm font-bold disabled:opacity-40 ${on ? "bg-ink text-yellow" : "bg-white"} ${className ?? ""}`} {...props} />;
}

function pageList(cur: number, pages: number): number[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
  const s = new Set([1, 2, pages - 1, pages, cur - 1, cur, cur + 1].filter((p) => p >= 1 && p <= pages));
  const arr = [...s].sort((a, b) => a - b);
  const out: number[] = [];
  arr.forEach((p, i) => { if (i && p - arr[i - 1] > 1) out.push(0); out.push(p); });
  return out;
}
