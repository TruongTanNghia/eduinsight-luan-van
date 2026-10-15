"use client";
// 01 · Tổng quan — /dashboard
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { buttonClass } from "@/components/ui/button";
import { SubjectBarChart, TrendLineChart } from "@/components/ui/charts";
import { FilterBar, SelectField } from "@/components/ui/field";
import { PeriodSelect } from "@/components/ui/period-select";
import { SectionTitle } from "@/components/ui/page-header";
import { StatSticker } from "@/components/ui/stat-sticker";
import { EmptySticker, ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { DemoBadge, Tag } from "@/components/ui/tag";
import { useApi, useMeta } from "@/lib/api";
import { dateVN, fmt, int, pct, sgn } from "@/lib/format";

type Overview = {
  period: { key: string; grade: number; label: string; short: string; kind: string; year: string }; prevPeriod: { key: string; label: string } | null; class: string; n: number;
  kpi: { avg: number; delta: number | null; up: number; upPct: number; down: number; downPct: number; watch: number; compared: number };
  summary: string; series: { semester: string; all: number; class?: number | null }[];
  subjects: { subject: string; name: string; value: number }[]; subjectAverage: number;
  histogram: { label: string; n: number; low: boolean }[]; lowCount: number; groups: { name: string; n: number }[];
  classes: { id: string; name: string; avg: number; up: number; down: number; n: number }[];
  risk: { id: string; name: string; initials: string; class: string; avg: number; delta: number | null; reasons: string[]; status: string }[]; threshold: number;
};

const TILT = [-1.5, 1.2, 1, -1.2];
const GROUP_COLOR: Record<string, string> = { "Tốt": "bg-cobalt text-white", "Khá": "bg-mint", "Đạt": "bg-yellow", "Chưa đạt": "bg-tomato" };
const AVATAR = ["bg-pink", "bg-mint", "bg-lilac", "bg-yellow", "bg-cobalt text-white"];

export default function DashboardPage() {
  return (
    <Suspense fallback={<LoadingSticker />}>
      <Dashboard />
    </Suspense>
  );
}

function Dashboard() {
  const sp = useSearchParams();
  const router = useRouter();
  const period = sp.get("period") ?? "";
  const cls = sp.get("class") ?? "all";
  const meta = useMeta();
  const { data, error, loading, reload } = useApi<Overview>(`/analytics/overview?period=${period}&class=${cls}`);
  const set = (k: string, v: string) => {
    const q = new URLSearchParams(sp.toString());
    if (v === "all" || !v) q.delete(k); else q.set(k, v);
    if (k === "period") q.delete("class");
    router.replace(`/dashboard?${q.toString()}`);
  };
  const pkey = period || meta.data?.defaultPeriod || "";
  const classes = meta.data?.classesByPeriod[pkey] ?? [];

  return (
    <>
      <FilterBar source={meta.data ? `Nguồn: ${meta.data.datasetVersion} · cập nhật ${dateVN(meta.data.updated)}` : undefined}>
        <PeriodSelect periods={meta.data?.periods ?? []} value={pkey} onChange={(v) => set("period", v)} />
        <SelectField label="Lớp" value={cls} onChange={(e) => set("class", e.target.value)}>
          <option value="all">Tất cả lớp</option>
          {classes.map((c) => <option key={c} value={c}>{c}</option>)}
        </SelectField>
      </FilterBar>

      {error && <ErrorSticker message={error} onRetry={reload} />}
      {loading && !data && <LoadingSticker lines={4} />}
      {data && data.n === 0 && <EmptySticker title="Chưa có dữ liệu cho bộ lọc này" action={<Link href="/dashboard" className={buttonClass("outline")}>Xóa bộ lọc</Link>} />}
      {data && data.n > 0 && <Content d={data} period={data.period.key} cls={cls} />}
    </>
  );
}

function Content({ d, period, cls }: { d: Overview; period: string; cls: string }) {
  const k = d.kpi;
  const scope = cls === "all" ? "Toàn khối" : `Lớp ${cls}`;
  const hero = k.delta === null ? `${scope} đạt ĐTB ${fmt(k.avg)} ở ${d.period.label}` : `${scope} ${k.delta >= 0 ? "tăng" : "giảm"} `;
  const maxH = Math.max(...d.histogram.map((h) => h.n), 1);
  const total = d.groups.reduce((a, g) => a + g.n, 0) || 1;
  const good = d.groups.filter((g) => g.name === "Tốt" || g.name === "Khá").reduce((a, g) => a + g.n, 0);
  const stats = [
    { label: "Điểm trung bình", value: fmt(k.avg), hint: `${scope.toLowerCase()}, thang 10 · ${d.n} học sinh`, tone: "cobalt" as const },
    { label: "Bạn tiến bộ", value: int(k.up), hint: `ĐTB tăng ≥ ${fmt(d.threshold, 1)} · ${pct(k.upPct)}`, tone: "mint" as const },
    { label: "Bạn đi xuống", value: int(k.down), hint: `ĐTB giảm ≥ ${fmt(d.threshold, 1)} · ${pct(k.downPct)}`, tone: "tomato" as const },
    { label: "Cần xem lại", value: int(k.watch), hint: "≥ 1 tiêu chí cảnh báo", tone: "lilac" as const },
  ];

  return (
    <>
      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6 items-stretch">
        <Sticker tone="yellow" className="flex flex-col justify-center gap-4 p-9">
          <DemoBadge label={`Thực tế · tính từ dữ liệu · ${d.period.label} ${d.period.year}`} />
          <h1 className="m-0 text-[54px] font-extrabold leading-[1.02] tracking-[-0.035em] text-balance">
            {hero}
            {k.delta !== null && (
              <>
                <span className="inline-block -rotate-[1.5deg] rounded-[10px] bg-ink px-2.5 text-yellow">{sgn(k.delta)}</span> điểm so với {d.prevPeriod?.label}
              </>
            )}
          </h1>
          <p className="m-0 max-w-[52ch] text-lg font-medium leading-normal">{d.summary}</p>
          <div className="flex flex-wrap gap-2.5">
            <Link href={`/students?status=Theo dõi&period=${d.period.key}${cls !== "all" ? `&class=${cls}` : ""}`} className={buttonClass("dark")}>Xem {k.watch} bạn cần chú ý</Link>
            <Link href="/reports" className={buttonClass("outline")}>Xuất báo cáo</Link>
          </div>
        </Sticker>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-[18px]">
          {stats.map((s, i) => <StatSticker key={s.label} {...s} tilt={TILT[i % 4]} />)}
        </div>
      </section>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6">
        <Sticker>
          <StickerHeader title={d.period.kind === "semester" ? "Điểm trung bình qua các học kỳ" : "Điểm trung bình qua các năm"} action={<div className="flex gap-2"><Tag tone="cobalt">Toàn khối</Tag>{cls !== "all" && <Tag tone="pink">Lớp {cls}</Tag>}</div>} />
          <div role="img" aria-label={`ĐTB toàn khối ${fmt(d.series[0]?.all)} → ${fmt(d.series[d.series.length - 1]?.all)}`} className="mt-3.5">
            <TrendLineChart data={d.series} lines={[{ key: "all", name: "Toàn khối" }, ...(cls !== "all" ? [{ key: "class", name: `Lớp ${cls}`, color: "#FF8FC7" }] : [])]} domain={[6, 9.5]} />
          </div>
        </Sticker>
        <Sticker>
          <StickerHeader title="Môn nào mạnh, môn nào cần đỡ?" action={<Tag tone="tomato">Cam = dưới ĐTB chung ≥ {fmt(d.threshold, 1)}</Tag>} />
          <div role="img" aria-label={`ĐTB từng môn ${d.period.label}; đường nét đứt là ĐTB chung ${fmt(d.subjectAverage)}`} className="mt-3.5">
            <SubjectBarChart data={d.subjects} average={d.subjectAverage} lowGap={d.threshold} />
          </div>
        </Sticker>
      </section>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(380px,100%),1fr))] gap-6">
        <Sticker className="flex flex-col gap-3.5">
          <h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Điểm của {d.n} bạn</h2>
          <div role="img" aria-label={`Phân bố ĐTB; ${d.lowCount} bạn dưới 5,5`} className="flex h-[170px] items-end gap-1.5 border-b-[2.5px] border-ink">
            {d.histogram.map((h, i) => (
              <div key={h.label} title={`ĐTB ${h.label}: ${h.n} bạn`} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
                <span className="num text-[11px] font-bold">{h.n}</span>
                <span className={`block w-full rounded-t-md border-2 border-b-0 border-ink ${h.low ? "bg-tomato" : i % 2 ? "bg-yellow" : "bg-cobalt"}`} style={{ height: `${Math.round((h.n / maxH) * 130)}px` }} />
              </div>
            ))}
          </div>
          <div className="flex gap-1.5">{d.histogram.map((h) => <span key={h.label} className="num flex-1 text-center text-[10.5px] font-bold">{h.label}</span>)}</div>
          <span className="text-[13px] font-medium">Cột cam: ĐTB dưới 5,5 ({d.lowCount} bạn)</span>
        </Sticker>
        <Sticker className="flex flex-col gap-4">
          <h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Xếp loại theo TT22</h2>
          <div role="img" aria-label={d.groups.map((g) => `${g.name} ${g.n}`).join(", ")} className="flex h-[52px] overflow-hidden rounded-lg border-[2.5px] border-ink">
            {d.groups.filter((g) => g.n > 0).map((g) => <span key={g.name} title={`${g.name}: ${g.n}`} className={`border-r-[2.5px] border-ink last:border-r-0 ${GROUP_COLOR[g.name]}`} style={{ width: `${(g.n / total) * 100}%` }} />)}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {d.groups.map((g) => (
              <div key={g.name} className="flex items-center gap-2.5">
                <span className={`size-[18px] flex-none rounded-md border-2 border-ink ${GROUP_COLOR[g.name]}`} />
                <span className="text-[15px] font-bold">{g.name}</span>
                <span className="num ml-auto text-[15px] font-bold">{int(g.n)}</span>
              </div>
            ))}
          </div>
          <span className="text-[13px] font-medium">Tốt + Khá: {int(good)} bạn ({pct((100 * good) / total)})</span>
        </Sticker>
        <Sticker className="flex flex-col gap-3.5">
          <StickerHeader title={`${d.classes.length} lớp, ai dẫn đầu?`} action={<Tag tone="white">▲ tiến bộ ▼ sa sút</Tag>} />
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(96px,100%),1fr))] gap-2.5">
            {d.classes.map((c) => (
              <Link key={c.id} href={`/classes/${c.id}?period=${period}`} className={`press flex min-h-11 flex-col gap-0.5 rounded-lg border-[2.5px] border-ink px-3 py-2.5 text-ink no-underline hover:text-ink ${c.avg >= 7.3 ? "bg-mint" : c.avg >= 7 ? "bg-white" : c.avg >= 6.85 ? "bg-warning" : "bg-[#FFC2B3]"}`}>
                <span className="text-[13px] font-bold">{c.name}</span>
                <span className="text-2xl font-extrabold tracking-[-0.03em]">{fmt(c.avg)}</span>
                <span className="num text-[11.5px] font-bold">▲{c.up} ▼{c.down}</span>
              </Link>
            ))}
          </div>
        </Sticker>
      </section>

      <section className="flex flex-col gap-4">
        <SectionTitle title="Các bạn cần thầy cô xem lại" note="Chỉ dựa trên điểm số, không dùng để đánh giá hoàn cảnh hay năng lực" />
        {d.risk.length === 0 ? (
          <EmptySticker title="Không có bạn nào vượt tiêu chí cảnh báo" description={`Tiêu chí: ĐTB giảm ≥ ${fmt(d.threshold, 1)}, ≥ 2 môn giảm ≥ 1,0, một môn giảm ≥ 2,0, hoặc ĐTB dưới 5,5.`} />
        ) : (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(250px,100%),1fr))] gap-[18px]">
            {d.risk.map((r, i) => (
              <Sticker key={r.id} as="article" className="flex flex-col gap-3 p-[18px]">
                <div className="flex items-center gap-3">
                  <span aria-hidden="true" className={`flex size-[46px] flex-none items-center justify-center rounded-lg border-[2.5px] border-ink text-base font-extrabold ${AVATAR[i % AVATAR.length]}`}>{r.initials}</span>
                  <div className="flex min-w-0 flex-col"><strong className="text-base">{r.name}</strong><span className="num text-xs">{r.class} · {r.id}</span></div>
                </div>
                <Tag tone={r.reasons[0]?.startsWith("ĐTB") || r.reasons[0]?.includes("giảm") ? "tomato" : "yellow"} className="self-start">{r.reasons[0] ?? "Cần xem lại"}</Tag>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] font-medium">ĐTB {d.period.label}</span>
                  <span className="flex items-baseline gap-2"><span className="text-[26px] font-extrabold">{fmt(r.avg)}</span><span className={`num text-[13px] font-bold ${r.delta === null ? "text-muted" : r.delta < 0 ? "text-negative-text" : "text-positive-text"}`}>{sgn(r.delta)}</span></span>
                </div>
                <Link href={`/students/${r.id}`} className={buttonClass("outline", "min-h-10")}>Mở hồ sơ</Link>
              </Sticker>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
