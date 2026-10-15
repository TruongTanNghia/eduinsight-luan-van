"use client";
// 04 · Phân tích lớp học — /classes/[id]
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { SelectField } from "@/components/ui/field";
import { PeriodSelect } from "@/components/ui/period-select";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { Tag, TrendTag } from "@/components/ui/tag";
import { useApi, useMeta } from "@/lib/api";
import { deltaClass, fmt, int, pct, sgn } from "@/lib/format";

type Data = {
  class: string; period: { key: string; grade: number; label: string; year: string }; prevLabel: string | null; n: number;
  kpi: { avg: number; prevAvg: number | null; cohortAvg: number; delta: number | null; deltaLabel: string; goodPct: number; good: number; watch: number };
  subjects: { subject: string; name: string; prev: number | null; cur: number; cohort: number }[];
  distribution: { period: string; parts: { name: string; n: number }[] }[];
  groups: Record<"up" | "flat" | "down" | "insufficient", number>;
  drops: { key: string; name: string; n: number }[];
  students: { id: string; name: string; prev: number | null; avg: number; delta: number | null; group: "up" | "flat" | "down" | "insufficient"; drops: string[]; dropKeys: string[]; level: string }[];
  threshold: number;
};
const GROUP_LABEL = { up: "Tiến bộ", flat: "Ổn định", down: "Sa sút", insufficient: "Chưa đủ dữ liệu" } as const;
const GROUP_BG = { up: "bg-mint", flat: "bg-neutral", down: "bg-tomato", insufficient: "bg-white" } as const;
const LEVEL_BG: Record<string, string> = { "Tốt": "bg-cobalt text-white", "Khá": "bg-mint", "Đạt": "bg-yellow", "Chưa đạt": "bg-tomato" };

export default function ClassPage() {
  return <Suspense fallback={<LoadingSticker />}><ClassAnalysis /></Suspense>;
}

function ClassAnalysis() {
  const { id } = useParams<{ id: string }>();
  const sp = useSearchParams();
  const router = useRouter();
  const period0 = sp.get("period") ?? "";
  const meta = useMeta();
  const period = period0 || meta.data?.defaultPeriod || "";
  const { data, error, loading, reload } = useApi<Data>(period ? `/classes/${id}?period=${period}` : null);
  const [group, setGroup] = useState<keyof typeof GROUP_LABEL | null>(null);
  const [subj, setSubj] = useState<string | null>(null);
  const classes = meta.data?.classesByPeriod[period] ?? [];

  const right = (
    <>
      <SelectField label="Lớp" value={id} onChange={(e) => router.replace(`/classes/${e.target.value}?period=${period}`)}>{(classes.length ? classes : [id]).map((c) => <option key={c} value={c}>{c}</option>)}</SelectField>
      <PeriodSelect periods={meta.data?.periods ?? []} value={period} onChange={(v) => router.replace(`/classes/${id}?period=${v}`)} />
    </>
  );
  if (error) return <><PageHeader title={`Phân tích lớp ${id}`} right={right} /><ErrorSticker message={error} onRetry={reload} /></>;
  if (loading || !data) return <><PageHeader title={`Phân tích lớp ${id}`} right={right} /><LoadingSticker lines={5} /></>;
  const d = data;
  const total = d.n || 1;
  const maxDrop = Math.max(...d.drops.map((x) => x.n), 1);
  const rows = d.students.filter((s) => (!group || s.group === group) && (!subj || s.dropKeys.includes(subj)));
  const filterLabel = group ? GROUP_LABEL[group] : subj ? d.drops.find((x) => x.key === subj)?.name : null;
  const groupKeys = ["up", "flat", "down"] as const;
  const hb = (v: number | null) => (v === null ? 0 : Math.max(4, Math.round(((v - 5) / 5) * 180)));

  return (
    <>
      <PageHeader title={`Phân tích lớp ${d.class}`} badge="Thực tế · tính từ dữ liệu" right={right}
        subtitle={<>{int(d.n)} học sinh · GVCN: [Tên giáo viên] · So sánh {d.period.label} ({d.period.year}) với {d.prevLabel ?? "kỳ trước (chưa có)"}</>} />

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-3.5">
        <Kpi label={`ĐTB lớp ${d.period.label}`} value={fmt(d.kpi.avg)} hint={`${d.prevLabel ?? "kỳ trước"}: ${fmt(d.kpi.prevAvg)} · khối: ${fmt(d.kpi.cohortAvg)}`} />
        <Kpi label={`Thay đổi so với ${d.prevLabel ?? "kỳ trước"}`} value={sgn(d.kpi.delta)} hint={d.kpi.delta === null ? "chưa có kỳ trước" : Math.abs(d.kpi.delta) < d.threshold ? `dưới ngưỡng ±${fmt(d.threshold, 1)} → lớp ổn định` : d.kpi.delta > 0 ? "lớp tiến bộ" : "lớp sa sút"} className={deltaClass(d.kpi.delta, d.threshold)} />
        <Kpi label="Mức Tốt + Khá" value={pct(d.kpi.goodPct)} hint={`${d.kpi.good} / ${d.n} học sinh`} />
        <Kpi label="Cần giáo viên theo dõi" value={int(d.kpi.watch)} hint="thỏa ≥ 1 tiêu chí cảnh báo" className="text-warning-text" />
      </section>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6">
        <Sticker>
          <StickerHeader title={`ĐTB môn: ${d.prevLabel ?? "—"} và ${d.period.label}`} description={`Lớp ${d.class} · trục từ 5,0`}
            action={<div className="flex gap-3 text-xs font-bold"><span className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] border border-ink bg-pink" />{d.prevLabel ?? "Kỳ trước"}</span><span className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] border border-ink bg-cobalt" />{d.period.label}</span></div>} />
          <div role="img" aria-label={`ĐTB từng môn của lớp ở hai năm học`} className="mt-[18px] flex h-[210px] items-end gap-3 border-b-[2.5px] border-ink px-1">
            {d.subjects.map((s) => (
              <div key={s.subject} title={`${s.name}: ${fmt(s.prev, 1)} → ${fmt(s.cur, 1)}`} className="flex h-full flex-1 items-end gap-[3px]">
                <div className="flex flex-1 flex-col items-center gap-1"><span className="num text-[10.5px] text-muted">{fmt(s.prev, 1)}</span><span className="block w-full rounded-t-md border-2 border-b-0 border-ink bg-pink" style={{ height: hb(s.prev) }} /></div>
                <div className="flex flex-1 flex-col items-center gap-1"><span className="num text-[10.5px] font-bold">{fmt(s.cur, 1)}</span><span className="block w-full rounded-t-md border-2 border-b-0 border-ink bg-cobalt" style={{ height: hb(s.cur) }} /></div>
              </div>
            ))}
          </div>
          <div className="flex gap-3 px-1 pt-2">{d.subjects.map((s) => <span key={s.subject} className="flex-1 text-center text-[11.5px] font-bold">{s.subject}</span>)}</div>
        </Sticker>
        <Sticker>
          <StickerHeader title="Phân bố mức kết quả học tập" description="Số học sinh theo mức, TT22"
            action={<div className="flex flex-wrap gap-3 text-xs font-bold">{Object.entries(LEVEL_BG).map(([k, v]) => <span key={k} className="flex items-center gap-1.5"><span className={`size-2.5 rounded-[3px] border border-ink ${v}`} />{k}</span>)}</div>} />
          <div className="mt-6 flex flex-col gap-[18px]">
            {d.distribution.map((row) => {
              const tot = row.parts.reduce((a, p) => a + p.n, 0) || 1;
              return (
                <div key={row.period} className="grid grid-cols-[70px_1fr] items-center gap-3">
                  <span className="text-[13px] font-bold">{row.period}</span>
                  <span role="img" aria-label={`${row.period}: ${row.parts.map((p) => `${p.name} ${p.n}`).join(", ")}`} className="flex h-9 overflow-hidden rounded-md border-[2.5px] border-ink">
                    {row.parts.filter((p) => p.n > 0).map((p) => <span key={p.name} title={`${p.name}: ${p.n}`} className={`num flex items-center justify-center border-r-2 border-ink text-xs font-bold last:border-r-0 ${LEVEL_BG[p.name]}`} style={{ width: `${(p.n / tot) * 100}%` }}>{p.n}</span>)}
                  </span>
                </div>
              );
            })}
          </div>
          {d.distribution.length === 2 && <p className="mt-[18px] text-[13px] font-medium text-muted">{d.period.label}: Tốt từ {d.distribution[0].parts[0].n} thành {d.distribution[1].parts[0].n}, Đạt từ {d.distribution[0].parts[2].n} thành {d.distribution[1].parts[2].n}.</p>}
        </Sticker>
      </section>

      <Sticker>
        <div className="flex flex-wrap items-start justify-between gap-2.5">
          <StickerHeader title="Tiến bộ, ổn định và sa sút" description={`Nhấn một nhóm hoặc một môn để lọc danh sách học sinh bên dưới · ngưỡng ±${fmt(d.threshold, 1)}`} />
          {filterLabel && <Button variant="outline" onClick={() => { setGroup(null); setSubj(null); }}>Bỏ lọc: {filterLabel}</Button>}
        </div>
        <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(min(320px,100%),1fr))] gap-6">
          <div className="flex flex-col gap-3">
            <div aria-hidden="true" className="flex h-3.5 overflow-hidden rounded border-2 border-ink">{groupKeys.map((g) => <span key={g} className={GROUP_BG[g]} style={{ width: `${(d.groups[g] / total) * 100}%` }} />)}</div>
            <div className="grid grid-cols-3 gap-2.5">
              {groupKeys.map((g) => {
                const on = group === g;
                return (
                  <button key={g} type="button" aria-pressed={on} onClick={() => { setGroup(on ? null : g); setSubj(null); }}
                    className={`press flex min-h-11 flex-col gap-1 rounded-lg border-[2.5px] border-ink p-3 text-left ${on ? "bg-yellow shadow-selected" : "bg-white"}`}>
                    <span className="flex items-center gap-1.5 text-xs font-bold"><span className={`size-2.5 rounded-[3px] border border-ink ${GROUP_BG[g]}`} />{GROUP_LABEL[g]}</span>
                    <span className="num text-2xl font-extrabold">{d.groups[g]}</span>
                    <span className="num text-xs text-muted">{pct((100 * d.groups[g]) / total)}</span>
                  </button>
                );
              })}
            </div>
            {d.groups.insufficient > 0 && <span className="text-xs font-medium text-muted">{d.groups.insufficient} em chưa đủ dữ liệu (không có điểm kỳ trước).</span>}
          </div>
          <div className="flex flex-col gap-1">
            <span className="px-2 pb-1.5 text-[12.5px] font-bold">Số học sinh giảm ≥ {fmt(d.threshold, 1)} theo môn</span>
            {d.drops.map((x) => {
              const on = subj === x.key;
              return (
                <button key={x.key} type="button" aria-pressed={on} onClick={() => { setSubj(on ? null : x.key); setGroup(null); }}
                  className={`grid min-h-10 grid-cols-[120px_1fr_40px] items-center gap-2.5 rounded-md px-2 text-left ${on ? "bg-yellow" : "hover:bg-surface-soft"}`}>
                  <span className="text-[13px] font-bold">{x.name}</span>
                  <span className="block h-3 overflow-hidden rounded border border-ink bg-neutral"><span className={`block h-full ${x.n >= 9 ? "bg-amber" : "bg-cobalt"}`} style={{ width: `${(x.n / maxDrop) * 100}%` }} /></span>
                  <span className="num text-right text-[12.5px] font-bold">{x.n}</span>
                </button>
              );
            })}
          </div>
        </div>
      </Sticker>

      <Sticker className="p-0">
        <div className="px-5 pb-3 pt-[18px]"><StickerHeader title={`Học sinh${filterLabel ? ` · ${filterLabel}` : ""}`} description={`${rows.length} học sinh hiển thị · nhấn để mở hồ sơ`} /></div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[13.5px]">
            <thead><tr>
              {[["Học sinh", "left"], [`ĐTB ${d.prevLabel ?? "trước"}`, "right"], [`ĐTB ${d.period.label}`, "right"], ["Δ", "right"], ["Nhóm", "left"], [`Môn giảm ≥ ${fmt(d.threshold, 1)}`, "left"], ["", "left"]].map(([h, a], i) => (
                <th key={i} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${a === "right" ? "text-right" : "text-left"}`}>{h || <span className="sr-only">Thao tác</span>}</th>
              ))}
            </tr></thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id} className="hover:bg-surface-soft">
                  <td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{s.name}<span className="num ml-2 text-xs font-medium text-muted">{s.id}</span></td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right text-muted">{fmt(s.prev)}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(s.avg)}</td>
                  <td className={`num border-b-[1.5px] border-line px-3 py-2.5 text-right font-bold ${deltaClass(s.delta, d.threshold)}`}>{sgn(s.delta)}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5"><TrendTag trend={s.group} /></td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5">{s.drops.length ? s.drops.join(", ") : "—"}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5 text-right"><Link href={`/students/${s.id}`} className="inline-flex min-h-11 items-center text-[13px] font-bold">Xem hồ sơ</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <div className="px-5 py-12 text-center font-bold">Không có học sinh nào trong nhóm đã chọn.</div>}
        </div>
      </Sticker>
    </>
  );
}

function Kpi({ label, value, hint, className }: { label: string; value: string; hint: string; className?: string }) {
  return (
    <Sticker className="flex flex-col gap-1.5 px-[18px] py-4">
      <span className="text-[12.5px] font-bold">{label}</span>
      <span className={`num text-[28px] font-extrabold leading-none ${className ?? ""}`}>{value}</span>
      <span className="text-xs font-medium text-muted">{hint}</span>
    </Sticker>
  );
}
