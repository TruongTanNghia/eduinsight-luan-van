"use client";
// 03 · Hồ sơ học sinh — /students/[id]
import { Download, Compass } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { buttonClass } from "@/components/ui/button";
import { C, TrendLineChart } from "@/components/ui/charts";
import { ToggleChips } from "@/components/ui/segmented";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { DemoBadge, Tag, TrendTag } from "@/components/ui/tag";
import { useApi } from "@/lib/api";
import { fmt, LEVEL_TONE, sgn } from "@/lib/format";

type Trend = { kind: string; label: string; streak: number; dir: number; deltas: { i: number; d: number }[] };
type SubjectRow = { key: string; name: string; short: string; values: (number | null)[]; cells: (number | null)[]; classAvg: number | null; trend: Trend; lastDelta: number | null };
type Profile = {
  id: string; name: string; initials: string; class: string; grade: number; year: string; level: string; conduct: string; absences: number;
  periods: { key: string; grade: number; ky: number; kind: string; label: string; short: string; year: string }[]; avgs: (number | null)[]; lastIndex: number; latestAvg: number; delta: number | null; unit: string;
  grid: { key: string; grade: number; ky: number; kind: string; label: string; short: string; avg: number | null; level: string | null }[];
  overall: "up" | "flat" | "down" | "insufficient"; threshold: number; subjects: SubjectRow[]; classAvgByPeriod: Record<string, Record<string, number | null>>;
  ranks: { Lớp: string; "Lớp học": string; Hạng: number; "Sĩ số": number; ĐTB: number; Mức: string }[];
  analysis: { k: string; v: string; d: string; tone: string }[]; remarks: string[]; evidence: string[]; levelsByPeriod: (string | null)[];
};
const TREND_TONE: Record<string, "mint" | "tomato" | "neutral" | "white"> = { up: "mint", up_last: "mint", down: "tomato", down_last: "tomato", flat: "neutral", insufficient: "white" };
const TONE_TEXT: Record<string, string> = { positive: "text-positive-text", negative: "text-negative-text", warning: "text-warning-text", ink: "text-ink" };
const OVERALL = { up: "Tiến bộ", flat: "Ổn định", down: "Sa sút", insufficient: "Chưa đủ dữ liệu" };

export default function StudentProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, loading, reload } = useApi<Profile>(`/students/${id}`);
  const [selected, setSelected] = useState<string[]>(["Toan", "Van", "NgoaiNgu"]);
  if (error) return <ErrorSticker message={error} onRetry={reload} />;
  if (loading || !data) return <LoadingSticker lines={6} />;
  const p = data;
  const li = p.lastIndex;
  const last = p.periods[li];
  const prevLabel = li > 0 ? p.periods[li - 1].label : null;
  const chartData = p.periods.map((per, i) => ({ semester: per.short, ...Object.fromEntries(p.subjects.map((s) => [s.key, s.values[i]])) }));
  const chips = p.subjects.map((s, i) => ({ key: s.key, label: s.name, color: C.series[i % C.series.length] }));
  const lines = p.subjects.map((s, i) => ({ key: s.key, name: s.name, color: C.series[i % C.series.length] })).filter((l) => selected.includes(l.key));
  const classAvg = p.classAvgByPeriod[last.key] ?? {};
  const grades = [...new Set(p.grid.map((c) => c.grade))];
  const edge = (j: number) => (j === 0 || p.grid[j - 1].grade !== p.grid[j].grade ? "border-l-[2.5px] border-l-ink" : "");
  const hb = (v: number | null) => (v === null ? 0 : Math.max(4, Math.round(((v - 4) / 6) * 180)));
  const all = p.subjects.flatMap((s) => s.values.filter((v): v is number => v !== null));
  const hmin = Math.floor(Math.min(...all)), hmax = 10;

  return (
    <>
      <nav aria-label="Đường dẫn" className="flex flex-wrap items-center gap-2 text-[13px] font-medium">
        <Link href="/students">Học sinh</Link><span aria-hidden="true">/</span><Link href={`/classes/${p.class}`}>{p.class}</Link><span aria-hidden="true">/</span><span className="font-bold text-ink">{p.name}</span>
        <DemoBadge label="Thực tế · tính từ dữ liệu" />
      </nav>

      <Sticker className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex flex-wrap items-center gap-[18px]">
          <span aria-hidden="true" className="flex size-[72px] items-center justify-center rounded-full border-[2.5px] border-ink bg-pink text-2xl font-extrabold">{p.initials}</span>
          <div className="flex flex-col gap-1.5">
            <h1 className="m-0 text-2xl font-extrabold tracking-[-0.02em]">{p.name}</h1>
            <div className="flex flex-wrap gap-x-[18px] gap-y-1.5 text-[13px] font-medium">
              <span>Mã HS <strong className="num">{p.id}</strong></span><span>Lớp <strong>{p.class}</strong></span><span>Khối <strong>{p.grade}</strong></span><span>Năm học <strong>{p.year}</strong></span>
              <span>Rèn luyện <strong>{p.conduct}</strong></span><span>Nghỉ <strong className="num">{p.absences}</strong> buổi</span>
            </div>
            <span className="text-xs font-medium text-muted">Ảnh đại diện: không có trong dữ liệu · Chỉ hiển thị trường có trong dataset</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="flex min-w-[150px] flex-col gap-1 rounded-lg border-[2.5px] border-ink px-4 py-3"><span className="text-xs font-bold">ĐTB {last.label}</span><span className="num text-[26px] font-extrabold leading-none">{fmt(p.latestAvg)}</span><Tag tone={LEVEL_TONE[p.level]} className="self-start">{p.level}</Tag></div>
          <div className="flex min-w-[210px] flex-col gap-1 rounded-lg border-[2.5px] border-ink px-4 py-3"><span className="text-xs font-bold">Xu hướng gần đây</span><TrendTag trend={p.overall} /><span className="num text-xs font-medium">ĐTB {sgn(p.delta)} so với {prevLabel ?? "kỳ trước"} · ngưỡng ±{fmt(p.threshold)}</span></div>
        </div>
        <div className="flex flex-wrap gap-2.5">
          <Link href={`/reports?scope=student&target=${p.id}`} className={buttonClass("outline")}><Download className="size-[18px]" strokeWidth={2.5} aria-hidden="true" />Xuất báo cáo</Link>
          <Link href={`/predictions?student=${p.id}`} className={buttonClass("primary")}><Compass className="size-[18px]" strokeWidth={2.5} aria-hidden="true" />Định hướng</Link>
        </div>
      </Sticker>

      <Sticker className="p-0">
        <div className="flex flex-wrap items-start justify-between gap-2.5 px-5 pb-3 pt-[18px]">
          <StickerHeader title="Bảng điểm theo môn, học kỳ và năm học" description={`Điểm trung bình môn từng học kỳ và cả năm, thang 10 · Xu hướng tính trên chuỗi ${p.periods.length} ${p.unit} liên tiếp (${p.periods[0]?.label} → ${last.label}), ngưỡng thay đổi có ý nghĩa ±${fmt(p.threshold)}`} />
          <Tag tone="cobalt" className="self-center">Thực tế · tính từ dữ liệu</Tag>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr>
                <th scope="col" rowSpan={2} className="border-b-[2.5px] border-ink bg-table-head px-3 py-2 text-left text-xs font-bold">Môn học</th>
                {grades.map((g) => <th key={g} scope="colgroup" colSpan={p.grid.filter((c) => c.grade === g).length} className="border-b-[1.5px] border-l-[2.5px] border-ink bg-table-head px-3 py-1.5 text-center text-xs font-extrabold">Lớp {g}</th>)}
                <th scope="col" rowSpan={2} className="whitespace-nowrap border-b-[2.5px] border-l-[2.5px] border-ink bg-table-head px-3 py-2 text-right text-xs font-bold">ĐTB lớp<br />{last.label}</th>
                <th scope="col" rowSpan={2} className="border-b-[2.5px] border-ink bg-table-head px-3 py-2 text-left text-xs font-bold">Xu hướng</th>
              </tr>
              <tr>
                {p.grid.map((c, j) => <th key={c.key} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-b-ink px-2.5 py-1.5 text-right text-[11.5px] font-bold ${c.kind === "year" ? "bg-yellow" : "bg-table-head"} ${edge(j)}`}>{c.ky === 0 ? "Cả năm" : `HK${c.ky}`}</th>)}
              </tr>
            </thead>
            <tbody>
              {p.subjects.map((s) => (
                <tr key={s.key} className="hover:bg-surface-soft">
                  <td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{s.name}</td>
                  {s.cells.map((v, j) => <td key={j} className={`num border-b-[1.5px] border-b-line px-2.5 py-2.5 text-right ${v === null ? "text-muted" : ""} ${p.grid[j].kind === "year" ? "bg-surface-soft font-bold" : ""} ${edge(j)}`}>{fmt(v, 1)}</td>)}
                  <td className="num border-b-[1.5px] border-l-[2.5px] border-b-line border-l-ink px-3 py-2.5 text-right text-muted">{fmt(s.classAvg, 1)}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone={TREND_TONE[s.trend.kind]}>{s.trend.label}</Tag></td>
                </tr>
              ))}
              <tr className="bg-surface-soft">
                <td className="px-3 py-2.5 font-extrabold">ĐTB các môn</td>
                {p.grid.map((c, j) => <td key={c.key} className={`num px-2.5 py-2.5 text-right font-extrabold ${edge(j)}`}>{fmt(c.avg)}</td>)}
                <td className="num border-l-[2.5px] border-l-ink px-3 py-2.5 text-right text-muted">{fmt(classAvg.dtb as number | null)}</td>
                <td className="px-3 py-2.5 text-xs font-medium text-muted">Trung bình các môn có điểm</td>
              </tr>
              <tr>
                <td className="px-3 py-2 text-xs font-bold text-muted">Mức (TT22)</td>
                {p.grid.map((c, j) => <td key={c.key} className={`px-2 py-2 text-right ${edge(j)}`}>{c.level ? <Tag tone={LEVEL_TONE[c.level]}>{c.level}</Tag> : <span className="text-muted">—</span>}</td>)}
                <td className="border-l-[2.5px] border-l-ink" />
                <td />
              </tr>
            </tbody>
          </table>
        </div>
      </Sticker>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6">
        <Sticker>
          <StickerHeader title={`Điểm từng môn qua các ${p.unit}`} description={`${p.periods[0]?.label} → ${last.label} · chọn một hoặc nhiều môn để so sánh`} />
          <div className="mt-3.5"><ToggleChips items={chips} selected={selected} onToggle={(k) => setSelected((s) => (s.includes(k) ? s.filter((x) => x !== k) : [...s, k]))} /></div>
          {lines.length ? (
            <div role="img" aria-label={`Biểu đồ đường điểm ${lines.map((l) => l.name).join(", ")} qua ${p.periods.length} ${p.unit}`} className="mt-2">
              <TrendLineChart data={chartData} lines={lines} domain={[Math.min(5, hmin), 10]} />
            </div>
          ) : <p className="mt-4 text-center text-[13px] font-medium text-muted">Chưa chọn môn nào. Chọn ít nhất một môn ở trên.</p>}
        </Sticker>

        <Sticker>
          <StickerHeader title={`Điểm các môn ${last.label} so với lớp`} description={`${last.label} ${last.year} · cá nhân và ĐTB lớp ${p.class}`}
            action={<div className="flex gap-3 text-xs font-bold"><span className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] border border-ink bg-cobalt" />{p.name}</span><span className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] border border-ink bg-pink" />ĐTB lớp</span></div>} />
          <div role="img" aria-label={`So sánh điểm từng môn ${last.label} của học sinh với ĐTB lớp`} className="mt-[18px] flex h-[220px] items-end gap-3 border-b-[2.5px] border-ink px-1">
            {p.subjects.map((s) => (
              <div key={s.key} title={`${s.name}: ${fmt(s.values[li], 1)} (lớp ${fmt(s.classAvg, 1)})`} className="flex h-full flex-1 items-end gap-[3px]">
                <div className="flex flex-1 flex-col items-center gap-1"><span className="num text-[10.5px] font-bold">{fmt(s.values[li], 1)}</span><span className="block w-full rounded-t-md border-2 border-b-0 border-ink bg-cobalt" style={{ height: hb(s.values[li]) }} /></div>
                <div className="flex flex-1 flex-col items-center gap-1"><span className="num text-[10.5px] text-muted">{fmt(s.classAvg, 1)}</span><span className="block w-full rounded-t-md border-2 border-b-0 border-ink bg-pink" style={{ height: hb(s.classAvg) }} /></div>
              </div>
            ))}
          </div>
          <div className="flex gap-3 px-1 pt-2">{p.subjects.map((s) => <span key={s.key} className="flex-1 text-center text-[11.5px] font-bold">{s.short}</span>)}</div>
          <p className="mt-2 text-[13px] font-medium text-muted">Trục bắt đầu từ 4,0.</p>
        </Sticker>

        <Sticker>
          <StickerHeader title="Mức tăng/giảm so với kỳ trước" description={prevLabel ? `${last.label} so với ${prevLabel} · vùng xám: dưới ngưỡng ±${fmt(p.threshold)}, coi là ổn định` : "Chưa có kỳ trước để so sánh"} />
          <div className="mt-4 flex flex-col gap-2.5">
            {p.subjects.map((s) => {
              const d = s.lastDelta;
              const w = d === null ? 0 : Math.min((Math.abs(d) / 1.5) * 100, 100);
              const band = (p.threshold / 1.5) * 100;
              return (
                <div key={s.key} className="grid grid-cols-[84px_1fr_1fr_60px] items-center">
                  <span className="text-[13px] font-bold">{s.short}</span>
                  <span className="relative flex h-[18px] justify-end border-r-2 border-ink"><span className="absolute right-0 top-0 h-full bg-neutral" style={{ width: `${band}%` }} /><span className="relative h-full rounded-l-[3px] bg-tomato" style={{ width: d !== null && d < 0 ? `${w}%` : 0 }} /></span>
                  <span className="relative flex h-[18px]"><span className="absolute left-0 top-0 h-full bg-neutral" style={{ width: `${band}%` }} /><span className="relative h-full rounded-r-[3px] bg-mint" style={{ width: d !== null && d > 0 ? `${w}%` : 0 }} /></span>
                  <span className={`num text-right text-[12.5px] font-bold ${d === null ? "text-muted" : d >= p.threshold ? "text-positive-text" : d <= -p.threshold ? "text-negative-text" : "text-ink"}`}>{sgn(d, 1)}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-1.5 grid grid-cols-[84px_1fr_1fr_60px]"><span /><span className="num text-[10.5px] text-muted">−1,5</span><span className="num text-right text-[10.5px] text-muted">+1,5</span><span /></div>
        </Sticker>

        <Sticker>
          <StickerHeader title={`Heatmap môn học theo ${p.unit}`} description="Màu đậm hơn = điểm cao hơn · ô gạch chéo: thiếu dữ liệu" />
          <div className="mt-3.5 overflow-x-auto">
            <div className="grid min-w-[420px] gap-1" style={{ gridTemplateColumns: `76px repeat(${p.periods.length}, minmax(52px, 1fr))` }}>
              <span />{p.periods.map((per) => <span key={per.key} className="pb-1 text-center text-[11px] font-bold text-muted">{per.short}</span>)}
              {p.subjects.map((s) => (
                <HeatRow key={s.key} s={s} min={hmin} max={hmax} periods={p.periods.map((x) => x.label)} />
              ))}
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2 text-[11px] font-medium text-muted"><span className="num">{fmt(hmin, 1)}</span><span className="flex h-2 w-40 overflow-hidden rounded border border-ink">{Array.from({ length: 10 }).map((_, i) => <span key={i} className="flex-1" style={{ background: heat(i / 9) }} />)}</span><span className="num">10,0</span></div>
        </Sticker>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2.5"><h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">Phân tích tự động</h2><span className="text-xs font-medium text-muted">Tất cả chỉ số tính trực tiếp từ bảng điểm; không phải dự báo mô hình</span></div>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-3">
          {p.analysis.map((a) => (
            <div key={a.k} className="flex flex-col gap-1.5 rounded-lg border-[2.5px] border-ink bg-white p-4"><span className="text-xs font-bold">{a.k}</span><span className={`text-lg font-extrabold ${TONE_TEXT[a.tone]}`}>{a.v}</span><span className="num text-xs text-muted">{a.d}</span></div>
          ))}
        </div>
      </section>

      <Sticker className="flex flex-col gap-3.5">
        <div className="flex flex-wrap justify-between gap-2.5">
          <StickerHeader title="Nhận xét" description="Sinh tự động từ các phép tính đã xác minh. Giáo viên có thể chỉnh sửa trước khi đưa vào báo cáo." />
          <Tag tone="cobalt" className="self-start">Thực tế · không dùng mô hình</Tag>
        </div>
        <div className="flex max-w-[80ch] flex-col gap-2 text-[14.5px] font-medium leading-[1.65]">{p.remarks.map((m, i) => <p key={i} className="m-0">{m}</p>)}</div>
        <div className="flex flex-wrap items-center gap-2 border-t-[1.5px] border-line pt-3"><span className="text-xs font-bold text-muted">Căn cứ:</span>{p.evidence.map((e) => <Tag key={e} tone="neutral" className="num font-medium">{e}</Tag>)}</div>
      </Sticker>

      <Sticker className="p-0">
        <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Thứ hạng trong lớp theo từng kỳ" description="Xếp theo ĐTB các môn trong lớp ở từng học kỳ và cả năm" /></div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[13.5px]">
            <thead><tr>{["Kỳ", "Lớp học", "Hạng", "Sĩ số", "ĐTB", "Mức"].map((h, i) => <th key={h} scope="col" className={`border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i >= 2 && i <= 4 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
            <tbody>{p.ranks.map((r) => (
              <tr key={r.Lớp} className="hover:bg-surface-soft">
                <td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{r.Lớp}</td><td className="border-b-[1.5px] border-line px-3 py-2.5">{r["Lớp học"]}</td>
                <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right font-bold">{r.Hạng}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{r["Sĩ số"]}</td>
                <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(r.ĐTB)}</td><td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone={LEVEL_TONE[r.Mức]}>{r.Mức}</Tag></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Sticker>
    </>
  );
}

function heat(k: number) {
  const lerp = (a: number, b: number) => Math.round(a + (b - a) * k);
  return `rgb(${lerp(255, 43)},${lerp(255, 89)},${lerp(255, 255)})`;
}

function HeatRow({ s, min, max, periods }: { s: SubjectRow; min: number; max: number; periods: string[] }) {
  return (
    <>
      <span className="flex items-center text-[12.5px] font-bold">{s.short}</span>
      {s.values.map((v, i) => {
        if (v === null) return <span key={i} title={`${s.name} · ${periods[i]}: thiếu dữ liệu`} className="num flex h-[34px] items-center justify-center rounded-[5px] border-2 border-dashed border-line-strong bg-neutral text-xs font-bold text-muted">—</span>;
        const k = Math.max(0, Math.min(1, (v - min) / (max - min)));
        return <span key={i} title={`${s.name} · ${periods[i]}: ${fmt(v, 1)}`} className={`num flex h-[34px] items-center justify-center rounded-[5px] text-xs font-bold ${k > 0.5 ? "text-white" : "text-ink"}`} style={{ background: heat(k) }}>{fmt(v, 1)}</span>;
      })}
    </>
  );
}

