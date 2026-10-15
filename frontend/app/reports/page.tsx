"use client";
// 07 · Báo cáo — /reports
import { Download } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { SelectField } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { apiSend, useApi, useMeta } from "@/lib/api";
import { dateVN, fmt, int, sgn } from "@/lib/format";

type Scope = "student" | "class" | "period" | "all";
type Profile = { id: string; name: string; class: string; year: string; periods: { key: string; label: string }[]; avgs: (number | null)[]; latestAvg: number; overall: string; delta: number | null;
  subjects: { key: string; name: string; values: (number | null)[]; trend: { label: string }; classAvg: number | null; lastDelta: number | null }[]; remarks: string[]; strengths: { mon: string; diem: number }[]; threshold: number };
type ClassData = { class: string; period: { label: string; year: string }; prevLabel: string | null; n: number; kpi: { avg: number; prevAvg: number | null; delta: number | null; goodPct: number; watch: number }; subjects: { name: string; prev: number | null; cur: number }[]; groups: Record<string, number>; students: { id: string; name: string; prev: number | null; avg: number; delta: number | null; group: string }[] };
type Overview = { period: { label: string; year: string }; n: number; kpi: { avg: number; delta: number | null; up: number; down: number; watch: number }; subjects: { name: string; value: number }[]; groups: { name: string; n: number }[]; classes: { name: string; avg: number; up: number; down: number }[] };
type ReportRow = { id: string; scope: string; target: string; format: string; createdBy: string; createdAt: string; datasetVersion: string };
const SCOPES: { v: Scope; name: string; desc: string }[] = [{ v: "student", name: "Một học sinh", desc: "Bảng điểm, tiến bộ, nhận xét" }, { v: "class", name: "Một lớp", desc: "ĐTB, nhóm tiến bộ/sa sút" }, { v: "period", name: "Một năm học", desc: "Toàn khối ở một năm" }, { v: "all", name: "Toàn khóa", desc: "Tổng quan hiện tại" }];
const OVERALL: Record<string, string> = { up: "Tiến bộ", flat: "Ổn định", down: "Sa sút", insufficient: "Chưa đủ dữ liệu" };

export default function ReportsPage() {
  return <Suspense fallback={<LoadingSticker />}><Reports /></Suspense>;
}

function Reports() {
  const sp = useSearchParams();
  const router = useRouter();
  const meta = useMeta();
  const [scope, setScope] = useState<Scope>((sp.get("scope") as Scope) ?? "student");
  const [target, setTarget] = useState(sp.get("target") ?? "");
  const [cls, setCls] = useState("9A1");
  const [fmtOut, setFmtOut] = useState<"pdf" | "excel">("pdf");
  const [sec, setSec] = useState({ grades: true, chart: true, strengths: true, remarks: true, prediction: false });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [made, setMade] = useState<string | null>(null);
  const students = useApi<{ items: { id: string; name: string; class: string }[] }>(scope === "student" ? `/students?grade=9&class=${cls}&size=200&sort=name` : null);
  const history = useApi<ReportRow[]>("/reports");
  const classes = meta.data?.classesByPeriod["L9"] ?? [];
  const periods = meta.data?.periods ?? [];
  useEffect(() => {
    if (scope === "student" && !target && students.data?.items[0]) setTarget(students.data.items[0].id);
    if (scope === "class" && !classes.includes(target)) setTarget(classes[0] ?? "9A1");
    if (scope === "period" && !periods.some((p) => p.key === target)) setTarget(meta.data?.defaultPeriod ?? "L9");
    if (scope === "all") setTarget("all");
  }, [scope, target, students.data, classes, periods]);
  const previewPath = useMemo(() => {
    if (!target) return null;
    if (scope === "student") return `/students/${target}`;
    if (scope === "class") return `/classes/${target}?period=${meta.data?.defaultPeriod ?? "L9"}`;
    if (scope === "period") return `/analytics/overview?period=${target}`;
    return `/analytics/overview?period=${meta.data?.defaultPeriod ?? "L9"}`;
  }, [scope, target, meta.data]);
  const data = useApi<Profile | ClassData | Overview>(previewPath);

  const create = async () => {
    setBusy(true); setErr(null);
    try {
      const r = await apiSend<{ id: string }>("/reports", "POST", { scope, target, sections: sec, format: fmtOut });
      setMade(r.id); history.reload();
      if (fmtOut === "pdf") setTimeout(() => window.print(), 300);
      else downloadCsv(scope, target, data.data, r.id);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Báo cáo" badge="Thực tế · tính từ dữ liệu" subtitle="Mọi báo cáo ghi rõ nguồn dữ liệu, thời điểm dữ liệu và tách số liệu thực tế khỏi kết quả dự đoán." />
      <div className="flex flex-wrap items-start gap-5">
        <Sticker className="flex flex-1 basis-[340px] flex-col gap-[18px]">
          <h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Thiết lập báo cáo</h2>
          <div className="flex flex-col gap-1 text-xs font-bold">Phạm vi
            <div role="group" aria-label="Phạm vi báo cáo" className="grid grid-cols-2 gap-2">
              {SCOPES.map((s) => <button key={s.v} type="button" aria-pressed={scope === s.v} onClick={() => { setScope(s.v); setTarget(""); setMade(null); }} className={`press flex min-h-11 flex-col rounded-md border-[2.5px] border-ink px-3 py-2 text-left ${scope === s.v ? "bg-yellow shadow-selected" : "bg-white"}`}><strong className="text-[13.5px]">{s.name}</strong><span className="text-[11.5px] font-medium text-muted">{s.desc}</span></button>)}
            </div>
          </div>
          {scope === "student" && <>
            <SelectField label="Lớp" value={cls} onChange={(e) => { setCls(e.target.value); setTarget(""); }}>{(classes.length ? classes : [cls]).map((c) => <option key={c}>{c}</option>)}</SelectField>
            <SelectField label="Học sinh" value={target} onChange={(e) => setTarget(e.target.value)}>{(students.data?.items ?? []).map((s) => <option key={s.id} value={s.id}>{s.name} · {s.id}</option>)}</SelectField>
          </>}
          {scope === "class" && <SelectField label="Lớp" value={target} onChange={(e) => setTarget(e.target.value)}>{classes.map((c) => <option key={c}>{c}</option>)}</SelectField>}
          {scope === "period" && <SelectField label="Năm học" value={target} onChange={(e) => setTarget(e.target.value)}>{periods.map((p) => <option key={p.key} value={p.key}>{p.label} · {p.year}</option>)}</SelectField>}
          <fieldset className="m-0 flex flex-col gap-1 border-0 p-0">
            <legend className="pb-1.5 text-xs font-bold">Nội dung</legend>
            {([["grades", "Bảng điểm"], ["chart", "Biểu đồ tiến bộ"], ["strengths", "Môn mạnh / cần chú ý"], ["remarks", "Nhận xét"], ["prediction", "Kết quả dự đoán lớp 9 (mô hình)"]] as const).map(([k, label]) => (
              <label key={k} className="flex min-h-9 items-center gap-2.5 text-[13.5px] font-semibold"><input type="checkbox" className="size-[18px] accent-cobalt" checked={sec[k]} onChange={(e) => setSec({ ...sec, [k]: e.target.checked })} />{label}{k === "prediction" && <Tag tone="neutral">chỉ cho một học sinh</Tag>}</label>
            ))}
          </fieldset>
          <div className="flex flex-col gap-1 text-xs font-bold">Định dạng
            <div role="group" aria-label="Định dạng" className="grid grid-cols-2 gap-2">
              {([["pdf", "PDF", "in / lưu từ trình duyệt"], ["excel", "Excel (CSV)", "bảng số liệu"]] as const).map(([v, n, d]) => <button key={v} type="button" aria-pressed={fmtOut === v} onClick={() => setFmtOut(v)} className={`press flex min-h-11 flex-col rounded-md border-[2.5px] border-ink px-3 py-2 text-left ${fmtOut === v ? "bg-yellow shadow-selected" : "bg-white"}`}><strong className="text-[13.5px]">{n}</strong><span className="text-[11.5px] font-medium text-muted">{d}</span></button>)}
            </div>
          </div>
          {err && <span role="alert" className="text-[13px] font-bold text-negative-text">{err}</span>}
          <Button disabled={busy || !data.data} onClick={create}><Download className="size-[18px]" strokeWidth={2.5} aria-hidden="true" />{busy ? "Đang tạo…" : `Tạo và tải ${fmtOut === "pdf" ? "PDF" : "CSV"}`}</Button>
          {made && <span role="status" className="text-[13px] font-bold text-positive-text">Đã lưu báo cáo {made}.</span>}
        </Sticker>

        <section className="flex min-w-0 flex-[999] basis-[560px] flex-col gap-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Xem trước</h2><span className="text-xs font-medium text-muted">khổ A4 · in bằng nút “Tạo và tải PDF”</span></div>
          <div className="flex justify-center rounded-lg bg-[#E8DDBE] p-6">
            {data.error && <ErrorSticker message={data.error} onRetry={data.reload} />}
            {data.loading && !data.data && <LoadingSticker lines={6} />}
            {data.data && <Preview scope={scope} data={data.data} sec={sec} meta={meta.data} id={made} />}
          </div>
        </section>
      </div>

      <Sticker className="p-0">
        <div className="px-5 pb-2.5 pt-[18px]"><h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Lịch sử báo cáo</h2></div>
        <div className="overflow-x-auto"><table className="w-full border-collapse text-[13.5px]">
          <thead><tr>{["Mã", "Phạm vi", "Đối tượng", "Định dạng", "Dữ liệu", "Người tạo", "Ngày tạo", ""].map((h, i) => <th key={i} scope="col" className="whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-left text-xs font-bold">{h || <span className="sr-only">Mở lại</span>}</th>)}</tr></thead>
          <tbody>{(history.data ?? []).map((r) => (
            <tr key={r.id} className="hover:bg-surface-soft">
              <td className="num border-b-[1.5px] border-line px-3 py-2.5 font-bold">{r.id}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{SCOPES.find((s) => s.v === r.scope)?.name ?? r.scope}</td>
              <td className="num border-b-[1.5px] border-line px-3 py-2.5">{r.target}</td><td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone="white">{r.format.toUpperCase()}</Tag></td>
              <td className="num border-b-[1.5px] border-line px-3 py-2.5">{r.datasetVersion}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{r.createdBy}</td>
              <td className="num border-b-[1.5px] border-line px-3 py-2.5">{dateVN(r.createdAt)}</td>
              <td className="border-b-[1.5px] border-line px-3 py-2.5"><button type="button" className="inline-flex min-h-9 items-center font-bold" onClick={() => { setScope(r.scope as Scope); setTarget(r.target); setMade(r.id); router.replace(`/reports?scope=${r.scope}&target=${r.target}`); }}>Mở lại</button></td>
            </tr>
          ))}</tbody>
        </table>{history.data && history.data.length === 0 && <div className="px-5 py-10 text-center font-bold">Chưa có báo cáo nào được tạo.</div>}</div>
      </Sticker>
    </>
  );
}

function Preview({ scope, data, sec, meta, id }: { scope: Scope; data: Profile | ClassData | Overview; sec: Record<string, boolean>; meta: { datasetVersion: string; updated: string; school: string } | null; id: string | null }) {
  const head = (title: string, sub: string, k: string, v: string) => (
    <>
      <div className="flex flex-wrap justify-between gap-3 border-b-2 border-ink pb-2.5">
        <div className="flex flex-col"><strong className="text-[11px] tracking-[0.04em]">{(meta?.school ?? "TRƯỜNG THCS [TÊN TRƯỜNG]").toUpperCase()}</strong><span className="text-[10.5px] font-medium text-muted">EduInsight AI · báo cáo nội bộ</span></div>
        <div className="num text-right text-[10.5px] font-medium">Ngày tạo: {new Date().toLocaleDateString("vi-VN")}<br />Mã: {id ?? "(chưa lưu)"}</div>
      </div>
      <div><h3 className="m-0 text-[17px] font-extrabold">{title}</h3><p className="m-0 mt-0.5 font-medium">{sub}</p></div>
      <div className="grid grid-cols-3 gap-2 rounded-md bg-surface-soft p-2.5 text-[10.5px]">
        <div><span className="text-muted">Nguồn dữ liệu</span><br /><strong className="num">{meta?.datasetVersion ?? "—"}</strong></div>
        <div><span className="text-muted">Thời điểm dữ liệu</span><br /><strong className="num">{dateVN(meta?.updated)}</strong></div>
        <div><span className="text-muted">{k}</span><br /><strong className="num">{v}</strong></div>
      </div>
    </>
  );
  const foot = <div className="mt-1.5 flex flex-wrap justify-between gap-2 border-t border-line pt-2 text-[10px] font-medium text-muted"><span>Số liệu thực tế: tính trực tiếp từ bảng điểm. Dự đoán: đầu ra mô hình, chỉ mang tính tham khảo.</span><span className="num">1/1</span></div>;
  const th = "border-b border-ink px-1.5 py-1 text-left text-[10.5px] font-bold";
  const td = "border-b border-line px-1.5 py-1";

  if (scope === "student") {
    const p = data as Profile;
    return (
      <article className="print-area flex w-full max-w-[640px] flex-col gap-4 rounded-sm border-[2.5px] border-ink bg-white px-11 py-10 text-xs leading-[1.55]">
        {head(`Báo cáo kết quả học tập · ${p.name}`, `Lớp ${p.class} · Năm học ${p.year} · Mã ${p.id}`, "ĐTB gần nhất", `${fmt(p.latestAvg)} · ${OVERALL[p.overall]}`)}
        {sec.grades && <div className="flex flex-col gap-1.5"><strong className="text-[12.5px]">1. Bảng điểm <span className="font-medium text-cobalt-text">· Số liệu thực tế</span></strong>
          <table className="w-full border-collapse"><thead><tr><th className={th}>Môn</th>{p.periods.map((x) => <th key={x.key} className={`${th} text-right`}>{x.label}</th>)}<th className={th}>Xu hướng</th></tr></thead>
            <tbody>{p.subjects.map((s) => <tr key={s.key}><td className={td}>{s.name}</td>{s.values.map((v, i) => <td key={i} className={`${td} num text-right`}>{fmt(v, 1)}</td>)}<td className={td}>{s.trend.label}</td></tr>)}
              <tr><td className={`${td} font-bold`}>ĐTB</td>{p.avgs.map((v, i) => <td key={i} className={`${td} num text-right font-bold`}>{fmt(v)}</td>)}<td className={td} /></tr></tbody></table></div>}
        {sec.chart && <div className="flex flex-col gap-1.5"><strong className="text-[12.5px]">2. Biểu đồ tiến bộ (ĐTB theo năm)</strong><MiniLine periods={p.periods.map((x) => x.label)} series={[{ name: "ĐTB", values: p.avgs, color: "#2B59FF" }, ...p.subjects.filter((s) => ["Toan", "Van", "NgoaiNgu"].includes(s.key)).map((s, i) => ({ name: s.name, values: s.values, color: ["#FF8FC7", "#3DDC97", "#B8A4FF"][i] }))]} /></div>}
        {sec.strengths && <div className="grid grid-cols-2 gap-2.5"><div><strong>3. Môn mạnh</strong><br />{p.strengths.map((s) => `${s.mon} (${fmt(s.diem, 1)})`).join(", ")}</div><div><strong>Môn cần chú ý</strong><br />{p.subjects.filter((s) => s.lastDelta !== null && s.lastDelta <= -p.threshold).map((s) => `${s.name}: ${sgn(s.lastDelta, 1)}`).join(", ") || "Không có môn giảm vượt ngưỡng"}</div></div>}
        {sec.remarks && <div><strong>4. Nhận xét (sinh từ số liệu, giáo viên có thể sửa)</strong>{p.remarks.map((r, i) => <p key={i} className="m-0 mt-1">{r}</p>)}</div>}
        {sec.prediction && <div className="rounded-md border-[1.5px] border-dashed border-tomato p-2.5"><strong>5. Kết quả dự đoán <span className="text-negative-text">· Dự đoán mô hình</span></strong><p className="m-0 mt-1">Điểm lớp 9 dự đoán từ lớp 6–8 kèm khoảng tin cậy 90% được lưu trong tệp báo cáo (reports JSON). Dự đoán tuyển sinh THPT chưa kích hoạt do chưa có nhãn kết quả thi; mục này để trống có chủ đích.</p></div>}
        {foot}
      </article>
    );
  }
  if (scope === "class") {
    const c = data as ClassData;
    return (
      <article className="print-area flex w-full max-w-[640px] flex-col gap-4 rounded-sm border-[2.5px] border-ink bg-white px-11 py-10 text-xs leading-[1.55]">
        {head(`Báo cáo lớp ${c.class}`, `${c.period.label} · ${c.period.year} · ${c.n} học sinh`, "ĐTB lớp", `${fmt(c.kpi.avg)} (${sgn(c.kpi.delta)} so với ${c.prevLabel ?? "kỳ trước"})`)}
        {sec.grades && <div className="flex flex-col gap-1.5"><strong className="text-[12.5px]">1. ĐTB từng môn <span className="font-medium text-cobalt-text">· Số liệu thực tế</span></strong>
          <table className="w-full border-collapse"><thead><tr><th className={th}>Môn</th><th className={`${th} text-right`}>{c.prevLabel ?? "Trước"}</th><th className={`${th} text-right`}>{c.period.label}</th></tr></thead><tbody>{c.subjects.map((s) => <tr key={s.name}><td className={td}>{s.name}</td><td className={`${td} num text-right`}>{fmt(s.prev, 1)}</td><td className={`${td} num text-right`}>{fmt(s.cur, 1)}</td></tr>)}</tbody></table></div>}
        {sec.strengths && <div><strong>2. Nhóm tiến bộ / ổn định / sa sút</strong><br />Tiến bộ {c.groups.up} · Ổn định {c.groups.flat} · Sa sút {c.groups.down} · Tốt + Khá {fmt(c.kpi.goodPct, 1)}% · Cần theo dõi {c.kpi.watch}</div>}
        {sec.remarks && <div className="flex flex-col gap-1.5"><strong>3. Danh sách học sinh</strong>
          <table className="w-full border-collapse"><thead><tr><th className={th}>Học sinh</th><th className={`${th} text-right`}>ĐTB trước</th><th className={`${th} text-right`}>ĐTB nay</th><th className={`${th} text-right`}>Δ</th><th className={th}>Nhóm</th></tr></thead>
            <tbody>{c.students.map((s) => <tr key={s.id}><td className={td}>{s.name}</td><td className={`${td} num text-right`}>{fmt(s.prev)}</td><td className={`${td} num text-right`}>{fmt(s.avg)}</td><td className={`${td} num text-right`}>{sgn(s.delta)}</td><td className={td}>{OVERALL[s.group]}</td></tr>)}</tbody></table></div>}
        {foot}
      </article>
    );
  }
  const o = data as Overview;
  return (
    <article className="print-area flex w-full max-w-[640px] flex-col gap-4 rounded-sm border-[2.5px] border-ink bg-white px-11 py-10 text-xs leading-[1.55]">
      {head(`Báo cáo toàn khối · ${o.period.label}`, `Năm học ${o.period.year} · ${o.n} học sinh`, "ĐTB khối", `${fmt(o.kpi.avg)} (${sgn(o.kpi.delta)})`)}
      <div><strong>1. Tổng quan</strong><br />Tiến bộ {o.kpi.up} · Đi xuống {o.kpi.down} · Cần xem lại {o.kpi.watch} · Xếp loại: {o.groups.map((g) => `${g.name} ${g.n}`).join(", ")}</div>
      {sec.grades && <div className="flex flex-col gap-1.5"><strong>2. ĐTB từng môn</strong><table className="w-full border-collapse"><tbody>{o.subjects.map((s) => <tr key={s.name}><td className={td}>{s.name}</td><td className={`${td} num text-right`}>{fmt(s.value)}</td></tr>)}</tbody></table></div>}
      {sec.strengths && <div className="flex flex-col gap-1.5"><strong>3. Theo lớp</strong><table className="w-full border-collapse"><thead><tr><th className={th}>Lớp</th><th className={`${th} text-right`}>ĐTB</th><th className={`${th} text-right`}>Tiến bộ</th><th className={`${th} text-right`}>Sa sút</th></tr></thead><tbody>{o.classes.map((c) => <tr key={c.name}><td className={td}>{c.name}</td><td className={`${td} num text-right`}>{fmt(c.avg)}</td><td className={`${td} num text-right`}>{c.up}</td><td className={`${td} num text-right`}>{c.down}</td></tr>)}</tbody></table></div>}
      {foot}
    </article>
  );
}

function MiniLine({ periods, series }: { periods: string[]; series: { name: string; values: (number | null)[]; color: string }[] }) {
  const W = 520, H = 120, L = 30, R = 70, T = 10, B = 24;
  const vals = series.flatMap((s) => s.values.filter((v): v is number => v !== null));
  const mn = Math.floor(Math.min(...vals, 10)), mx = 10;
  const X = (i: number) => L + ((W - L - R) * i) / Math.max(periods.length - 1, 1);
  const Y = (v: number) => T + (H - T - B) * (1 - (v - mn) / (mx - mn));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={`Diễn biến ${series.map((s) => s.name).join(", ")} qua ${periods.length} năm`}>
      <line x1={L} x2={W - R} y1={H - B} y2={H - B} stroke="#EADFC3" strokeWidth={1.5} />
      {periods.map((p, i) => <text key={p} x={X(i)} y={H - 8} textAnchor="middle" fontSize={9} fill="#111111">{p}</text>)}
      {series.map((s) => {
        const pts = s.values.map((v, i) => (v === null ? null : `${X(i)},${Y(v)}`)).filter(Boolean).join(" ");
        const last = [...s.values].reverse().find((v) => v !== null);
        return <g key={s.name}><polyline points={pts} fill="none" stroke={s.color} strokeWidth={2} /><text x={W - R + 4} y={last !== undefined && last !== null ? Y(last) + 3 : H / 2} fontSize={9} fill="#111111">{s.name}</text></g>;
      })}
    </svg>
  );
}

function downloadCsv(scope: Scope, target: string, data: Profile | ClassData | Overview | null, id: string) {
  if (!data) return;
  let rows: (string | number | null)[][] = [];
  if (scope === "student") { const p = data as Profile; rows = [["Môn", ...p.periods.map((x) => x.label), "ĐTB lớp", "Xu hướng"], ...p.subjects.map((s) => [s.name, ...s.values, s.classAvg, s.trend.label]), ["ĐTB", ...p.avgs]]; }
  else if (scope === "class") { const c = data as ClassData; rows = [["Học sinh", "Mã", "ĐTB trước", "ĐTB nay", "Δ", "Nhóm"], ...c.students.map((s) => [s.name, s.id, s.prev, s.avg, s.delta, OVERALL[s.group]])]; }
  else { const o = data as Overview; rows = [["Lớp", "ĐTB", "Tiến bộ", "Sa sút"], ...o.classes.map((c) => [c.name, c.avg, c.up, c.down])]; }
  const csv = rows.map((r) => r.map((v) => (v === null || v === undefined ? "" : typeof v === "number" ? String(v).replace(".", ",") : `"${String(v).replace(/"/g, '""')}"`)).join(";")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
  a.download = `${id}-${target}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}


