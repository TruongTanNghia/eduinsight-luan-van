"use client";
// 05 · Dự đoán & định hướng — /predictions?student=
import { CircleAlert, CircleCheck, CircleDashed, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { SelectField, TextField } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { EmptySticker, ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { apiSend, useApi, useMeta } from "@/lib/api";
import { fmt, LEVEL_TONE, sgn } from "@/lib/format";

type Pred = {
  id: string; available: boolean; reason?: string; model: string; models: string[]; latestGrade: number; latestLabel?: string;
  predicted: { key: string; name: string; short: string; value: number; lo: number; hi: number; latest: number; actual: number | null }[];
  levelProba: Record<string, number> | null; actualLevel: string | null; hasActual9: boolean; floor: number; floorSource: string; intervalNote: string;
  facts: Record<string, unknown> & { tong_3_mon: number; diem_3_mon_thi: Record<string, number>; nhom_dinh_huong: string; muc_ket_qua_hoc_tap_du_doan_lop_9: string; diem_trung_binh_du_doan_lop_9: number;
    diem_sang: { mon: string; diem: number; lop: number }[]; muc_tieu_tiep_theo?: { muc: string; kha_thi: boolean; can_cu: string; can_cai_thien: { mon: string; tu: number; len: number }[] };
    tuyen_sinh_lop_10: { diem_san: number; tong_3_mon: number; chenh_lech: number; nhan_dinh: string; khoang_tong_3_mon_90?: [number, number] }; xu_huong?: Record<string, { xu_huong: string; thay_doi: number }> };
  occlusion: ({ feature: string; period: string } & Record<string, number>)[]; attention: ({ feature: string } & Record<string, number | null>)[] | null; inputPeriods: string[];
};
type School = { id: string; name: string; year: string; method: string; cut: number; type: string; source: string };
type Student = { id: string; name: string; class: string };
type Models = { items: { id: string; name: string; served: boolean; rmse: number; proposed: boolean; best: boolean }[]; llm: string[]; status: string };
const AUD = ["Học sinh", "Phụ huynh", "Giáo viên chủ nhiệm"] as const;

export default function PredictionsPage() {
  return <Suspense fallback={<LoadingSticker />}><Predictions /></Suspense>;
}

function Predictions() {
  const sp = useSearchParams();
  const router = useRouter();
  const meta = useMeta();
  const student = sp.get("student") ?? "";
  const [cls, setCls] = useState(sp.get("class") ?? "9A1");
  const [model, setModel] = useState(sp.get("model") ?? "XEdu-KANFormer");
  const list = useApi<{ items: Student[] }>(`/students?grade=9&class=${cls}&size=200&sort=name`);
  const models = useApi<Models>("/ai/models");
  const schools = useApi<School[]>("/schools");
  useEffect(() => {
    if (!student && list.data?.items.length) router.replace(`/predictions?student=${list.data.items[0].id}&class=${cls}`);
  }, [student, list.data, cls, router]);
  const pred = useApi<Pred>(student ? `/students/${student}/predictions?model=${model}` : null);
  const classes = meta.data?.classesByPeriod["L9"] ?? [];
  const chosen = list.data?.items.find((s) => s.id === student);
  const noLabel = (models.data?.status ?? "awaiting_labels") === "awaiting_labels";

  return (
    <>
      <PageHeader title="Dự đoán & định hướng" badge="Dự đoán mô hình · đã đánh giá chéo" subtitle="Công cụ hỗ trợ quyết định. Không phải phán quyết về tương lai của học sinh."
        right={<>
          <SelectField label="Lớp" value={cls} onChange={(e) => { setCls(e.target.value); router.replace(`/predictions?class=${e.target.value}`); }}>{(classes.length ? classes : [cls]).map((c) => <option key={c}>{c}</option>)}</SelectField>
          <SelectField label="Học sinh" className="min-w-[240px]" value={student} onChange={(e) => router.replace(`/predictions?student=${e.target.value}&class=${cls}`)}>{(list.data?.items ?? []).map((s) => <option key={s.id} value={s.id}>{s.name} · {s.class} · {s.id}</option>)}</SelectField>
          <SelectField label="Mô hình" value={model} onChange={(e) => setModel(e.target.value)}>{(models.data?.items.filter((m) => m.served) ?? [{ id: model, name: model }]).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</SelectField>
        </>} />

      {noLabel && (
        <Sticker tone="yellow" className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <TriangleAlert aria-hidden="true" className="mt-0.5 size-[22px] flex-none" strokeWidth={2.5} />
            <div className="flex flex-col gap-1">
              <h2 className="m-0 text-base font-extrabold">Dự đoán kết quả tuyển sinh THPT chưa được kích hoạt</h2>
              <p className="m-0 max-w-[90ch] text-[13.5px] font-medium leading-relaxed">Bộ dữ liệu hiện tại ({meta.data?.datasetVersion ?? "…"}) chưa có nhãn kết quả thi vào lớp 10 theo từng trường. Hệ thống <strong>không hiển thị xác suất đỗ/trượt</strong>. Phần dưới chỉ gồm: dự đoán điểm cả năm lớp 9 (đã đánh giá chéo trên khóa này) và phép so sánh chênh lệch điểm với điểm chuẩn do nhà trường nhập.</p>
            </div>
          </div>
          <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-2.5 p-0">
            {[["1", "Thu thập nhãn", "Kết quả thi vào 10 của khóa đã tốt nghiệp", "Đang chờ", "neutral"], ["2", "Ghép hồ sơ", "Nối nhãn với mã học sinh ẩn danh", "Đang chờ", "neutral"], ["3", "Huấn luyện & đánh giá", "Pipeline cửa sổ lớp 6–8 → lớp 9 đã chạy", "Pipeline sẵn sàng", "mint"], ["4", "Kích hoạt đầu ra B", "Chỉ bật khi có nhãn thật", "Đang khóa", "neutral"]].map(([n, t, dsc, st, tone]) => (
              <li key={n} className={`flex flex-col gap-1 rounded-lg border-[2.5px] border-ink p-3 ${tone === "mint" ? "bg-mint" : "bg-white"}`}>
                <span className="flex items-center gap-2 text-xs font-bold"><span className="num flex size-[22px] items-center justify-center rounded-full border-2 border-ink bg-white text-[11.5px]">{n}</span>{st}</span>
                <strong className="text-[13.5px]">{t}</strong><span className="text-xs font-medium">{dsc}</span>
              </li>
            ))}
          </ol>
          <Link href="/data-management" className="self-start text-[13.5px] font-bold">Nhập dữ liệu kết quả tuyển sinh</Link>
        </Sticker>
      )}

      {pred.error && <ErrorSticker message={pred.error} onRetry={pred.reload} />}
      {pred.loading && !pred.data && <LoadingSticker lines={5} title="Đang tính dự đoán…" />}
      {pred.data && !pred.data.available && <EmptySticker title="Chưa dự đoán được" description={pred.data.reason} />}
      {pred.data?.available && chosen && <Body p={pred.data} student={chosen} schools={schools} llms={models.data?.llm ?? []} />}
    </>
  );
}

function Body({ p, student, schools, llms }: { p: Pred; student: Student; schools: ReturnType<typeof useApi<School[]>>; llms: string[] }) {
  const f = p.facts;
  const ts = f.tuyen_sinh_lop_10;
  const exam = Object.entries(f.diem_3_mon_thi);
  const total = f.tong_3_mon;
  const groupTone: Record<string, "tomato" | "yellow" | "mint"> = { "Định hướng nghề nghiệp": "tomato", "Cần bứt phá": "yellow", "Vững vàng thi THPT": "mint" };
  const hb = (v: number) => Math.max(4, Math.round(((v - 3) / 7) * 190));

  return (
    <>
      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(520px,100%),1fr))] gap-6">
        <Sticker className="flex flex-col gap-3.5">
          <StickerHeader title="Dự đoán điểm cả năm lớp 9 (đầu ra A)" description={`Từ ${p.inputPeriods.length} mốc (${p.inputPeriods[0]} → ${p.inputPeriods[p.inputPeriods.length - 1]}) của ${student.name} · mô hình ${p.model} · thanh sai số = khoảng tin cậy 90%`}
            action={<Tag tone="cobalt">Dự đoán mô hình</Tag>} />
          <div role="img" aria-label={`Điểm dự đoán 8 môn lớp 9, ĐTB dự đoán ${fmt(f.diem_trung_binh_du_doan_lop_9)}`} className="flex h-[230px] items-end gap-2.5 border-b-[2.5px] border-ink px-1">
            {p.predicted.map((s) => (
              <div key={s.key} title={`${s.name}: dự đoán ${fmt(s.value, 1)} (${fmt(s.lo, 1)}–${fmt(s.hi, 1)}); ${p.latestLabel ?? `lớp ${p.latestGrade}`}: ${fmt(s.latest, 1)}${s.actual !== null ? `; thực tế lớp 9: ${fmt(s.actual, 1)}` : ""}`} className="relative flex h-full flex-1 flex-col items-center justify-end gap-1">
                <span className="num text-[11px] font-bold" style={{ marginBottom: Math.max(0, hb(s.hi) - hb(s.value)) }}>{fmt(s.value, 1)}</span>
                <span className="relative block w-full rounded-t-[10px] border-[2.5px] border-b-0 border-ink bg-cobalt" style={{ height: hb(s.value) }}>
                  <span aria-hidden="true" className="absolute left-1/2 w-0.5 -translate-x-1/2 bg-ink" style={{ bottom: `${hb(s.lo)}px`, height: `${hb(s.hi) - hb(s.lo)}px` }} />
                  {s.actual !== null && <span aria-hidden="true" className="absolute left-1/2 size-3 -translate-x-1/2 rotate-45 border-2 border-ink bg-tomato" style={{ bottom: `${hb(s.actual) - 6}px` }} />}
                </span>
              </div>
            ))}
          </div>
          <div className="flex gap-2.5 px-1">{p.predicted.map((s) => <span key={s.key} className="flex-1 text-center text-[11.5px] font-bold">{s.short}</span>)}</div>
          <div className="flex flex-wrap gap-2 text-xs font-bold"><span className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] border border-ink bg-cobalt" />Dự đoán lớp 9</span>{p.hasActual9 && <span className="flex items-center gap-1.5"><span className="size-2.5 rotate-45 border border-ink bg-tomato" />Thực tế lớp 9 (đã có trong sổ)</span>}<span className="text-muted">· {p.intervalNote}</span></div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] gap-2.5">
            <Kv k="ĐTB lớp 9 dự đoán" v={fmt(f.diem_trung_binh_du_doan_lop_9, 1)} />
            <Kv k="Mức dự đoán (TT22)" v={<Tag tone={LEVEL_TONE[f.muc_ket_qua_hoc_tap_du_doan_lop_9]}>{f.muc_ket_qua_hoc_tap_du_doan_lop_9}</Tag>} />
            {p.levelProba && <Kv k="Xác suất mức (đầu phân mức)" v={<span className="num text-[13px]">{Object.entries(p.levelProba).filter(([, v]) => v >= 0.05).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${fmt(v)}`).join(" · ")}</span>} />}
            {p.actualLevel && <Kv k="Mức thực tế lớp 9" v={<Tag tone={LEVEL_TONE[p.actualLevel]}>{p.actualLevel}</Tag>} />}
          </div>
          <p className="m-0 text-xs font-medium text-muted">Xác suất mức chưa hiệu chỉnh (calibration). Độ tin cậy của mô hình xem tại <Link href={`/model-evaluation?model=${p.model}`}>Đánh giá mô hình</Link>.</p>
        </Sticker>

        <Sticker className="flex flex-col gap-3.5">
          <StickerHeader title="Mô hình đọc gì từ lưới môn × năm" description={`Ô nào kéo dự đoán lên (xanh) hay xuống (cam) nếu bị che · ${p.inputPeriods.length} mốc đầu vào · tính bằng che ô (occlusion)`} />
          <OcclusionGrid rows={p.occlusion} subjects={p.predicted.map((s) => ({ key: s.key, short: s.short }))} />
          {p.attention && <p className="m-0 text-xs font-medium text-muted">Mô hình {p.model} có trọng số chú ý trên lưới; giá trị cao nhất: {attnTop(p.attention)}.</p>}
        </Sticker>
      </section>

      <Sticker className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-2.5">
          <StickerHeader title="Ba môn thi và điểm sàn trường THPT" description="Điểm chuẩn do nhà trường nhập kèm nguồn. Hệ thống không tự điền điểm chuẩn." />
          <Tag tone={groupTone[f.nhom_dinh_huong]}>{f.nhom_dinh_huong}</Tag>
        </div>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] gap-2.5">
          {exam.map(([k, v]) => <Kv key={k} k={`${k} (dự đoán lớp 9)`} v={fmt(v, 1)} />)}
          <Kv k="Tổng 3 môn" v={<>{fmt(total, 1)}{ts.khoang_tong_3_mon_90 && <span className="num ml-2 text-xs font-medium text-muted">90%: {fmt(ts.khoang_tong_3_mon_90[0], 1)}–{fmt(ts.khoang_tong_3_mon_90[1], 1)}</span>}</>} />
          <Kv k="Điểm sàn đang so" v={<>{fmt(p.floor, 1)}<span className="ml-2 text-xs font-medium text-muted">{p.floorSource}</span></>} />
          <Kv k="Chênh lệch" v={<span className={ts.chenh_lech >= 0 ? "text-positive-text" : "text-negative-text"}>{sgn(ts.chenh_lech, 1)} · {ts.nhan_dinh}</span>} />
        </div>
        {f.xu_huong && <p className="m-0 text-[13px] font-medium">Xu hướng điểm cả năm các lớp trước: ĐTB <strong>{f.xu_huong.diem_trung_binh?.xu_huong.toLowerCase()}</strong> ({sgn(f.xu_huong.diem_trung_binh?.thay_doi, 1)}), tổng 3 môn thi <strong>{f.xu_huong.tong_3_mon_thi?.xu_huong.toLowerCase()}</strong> ({sgn(f.xu_huong.tong_3_mon_thi?.thay_doi, 1)}).</p>}
        <SchoolsBlock schools={schools} total={total} />
      </Sticker>

      <section className="grid grid-cols-[repeat(auto-fit,minmax(min(380px,100%),1fr))] gap-6">
        <Sticker className="flex flex-col gap-3">
          <StickerHeader title="Điểm sáng" description={`Môn nổi bật nhất so với bạn cùng khối ở ${p.latestLabel ?? `lớp ${p.latestGrade}`} · thực tế, không dùng mô hình`} />
          {f.diem_sang.map((s) => <div key={s.mon} className="flex items-center justify-between rounded-lg border-[2.5px] border-ink bg-mint px-4 py-2.5"><strong>{s.mon}</strong><span className="num font-bold">{fmt(s.diem, 1)} · {p.latestLabel ?? `lớp ${s.lop}`}</span></div>)}
        </Sticker>
        <Sticker className="flex flex-col gap-3">
          <StickerHeader title="Mục tiêu khả thi cho lớp 9" description={f.muc_tieu_tiep_theo ? `Để đạt mức ${f.muc_tieu_tiep_theo.muc} theo Thông tư 22 · căn cứ ${f.muc_tieu_tiep_theo.can_cu}` : "Dự kiến ở mức Tốt: duy trì kết quả hiện tại"} />
          {f.muc_tieu_tiep_theo?.can_cai_thien.map((c) => (
            <div key={c.mon} className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-lg border-[2.5px] border-ink px-4 py-2.5"><strong>{c.mon}</strong><span className="num text-[13px] font-bold">{fmt(c.tu, 1)} → {fmt(c.len, 1)} <span className="text-positive-text">({sgn(c.len - c.tu, 1)})</span></span></div>
          ))}
          {f.muc_tieu_tiep_theo && !f.muc_tieu_tiep_theo.kha_thi && <span className="text-xs font-medium text-warning-text">Có môn cần tăng hơn 1,5 điểm: nên đặt mục tiêu theo từng chặng.</span>}
        </Sticker>
      </section>

      <Paths f={f} />
      <MessageBlock sid={p.id} llms={llms} />
    </>
  );
}

function attnTop(att: NonNullable<Pred["attention"]>) {
  let best = { f: "", c: "", v: -1 };
  for (const r of att) for (const [c, v] of Object.entries(r)) if (c !== "feature" && typeof v === "number" && v > best.v) best = { f: r.feature, c, v };
  return `${best.f} · ${best.c} (${fmt(best.v, 3)})`;
}

function Kv({ k, v }: { k: string; v: React.ReactNode }) {
  return <div className="flex flex-col gap-1 rounded-lg border-[2.5px] border-ink bg-white px-3.5 py-2.5"><span className="text-xs font-bold text-muted">{k}</span><span className="num text-lg font-extrabold">{v}</span></div>;
}

function OcclusionGrid({ rows, subjects }: { rows: Pred["occlusion"]; subjects: { key: string; short: string }[] }) {
  const [target, setTarget] = useState(subjects[0]?.key ?? "Toan");
  const grades = [...new Set(rows.map((r) => r.period))];
  const feats = [...new Set(rows.map((r) => r.feature))];
  const max = Math.max(...rows.map((r) => Math.abs(r[target] ?? 0)), 0.01);
  return (
    <div className="flex flex-col gap-3">
      <Segmented label="Môn được dự đoán" value={target} onChange={setTarget} options={subjects.map((s) => ({ value: s.key, label: s.short }))} tone="yellow" />
      <div className="overflow-x-auto">
        <div className="grid min-w-[360px] gap-1" style={{ gridTemplateColumns: `130px repeat(${grades.length}, minmax(64px, 1fr))` }}>
          <span />{grades.map((g) => <span key={g} className="pb-1 text-center text-[11.5px] font-bold text-muted">{g}</span>)}
          {feats.map((fe) => (
            <RowCells key={fe} fe={fe} grades={grades} rows={rows} target={target} max={max} />
          ))}
        </div>
      </div>
      <span className="text-xs font-medium text-muted">Giá trị = thay đổi của điểm dự đoán nếu coi ô đó là khuyết. Xanh: ô đang kéo dự đoán lên; cam: kéo xuống.</span>
    </div>
  );
}

function RowCells({ fe, grades, rows, target, max }: { fe: string; grades: string[]; rows: Pred["occlusion"]; target: string; max: number }) {
  return (
    <>
      <span className="flex items-center text-[12.5px] font-bold">{fe}</span>
      {grades.map((g) => {
        const r = rows.find((x) => x.feature === fe && x.period === g);
        const v = r ? r[target] : null;
        if (v === null || v === undefined) return <span key={g} className="num flex h-8 items-center justify-center rounded-[5px] border border-line text-xs text-muted">—</span>;
        const k = Math.min(1, Math.abs(v) / max);
        return <span key={g} title={`${fe} · ${g}: ${sgn(v)}`} className={`num flex h-8 items-center justify-center rounded-[5px] border border-ink text-xs font-bold ${v >= 0 ? "bg-mint" : "bg-tomato"}`} style={{ opacity: 0.35 + 0.65 * k }}>{sgn(v)}</span>;
      })}
    </>
  );
}

function SchoolsBlock({ schools, total }: { schools: ReturnType<typeof useApi<School[]>>; total: number }) {
  const [form, setForm] = useState({ name: "", year: String(new Date().getFullYear()), method: "Thi tuyển 3 môn", cut: "", type: "Công lập", source: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const add = async () => {
    setBusy(true); setErr(null);
    try { await apiSend("/schools", "POST", { ...form, cut: Number(form.cut.replace(",", ".")) }); setForm({ ...form, name: "", cut: "", source: "" }); schools.reload(); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };
  const del = async (id: string) => { await apiSend(`/schools/${id}`, "DELETE"); schools.reload(); };
  const group = (gap: number) => (gap < -1 ? ["Mục tiêu", "cobalt"] : gap <= 1 ? ["Phù hợp", "mint"] : ["Dự phòng", "neutral"]) as [string, "cobalt" | "mint" | "neutral"];
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(380px,100%),1fr))] gap-5">
      {schools.loading && !schools.data ? <LoadingSticker lines={2} /> : schools.data && schools.data.length ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[13.5px]">
            <thead><tr>{["Trường (nhập tay)", "Phương thức", "Điểm chuẩn", "Chênh lệch điểm", "Xác suất mô hình", "Nhóm", ""].map((h, i) => <th key={i} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i === 2 || i === 3 ? "text-right" : "text-left"}`}>{h || <span className="sr-only">Xóa</span>}</th>)}</tr></thead>
            <tbody>{schools.data.map((s) => { const gap = total - s.cut; const [g, tone] = group(gap); return (
              <tr key={s.id} className="hover:bg-surface-soft">
                <td className="border-b-[1.5px] border-line px-3 py-2.5"><div className="flex flex-col"><strong>{s.name}</strong><span className="text-[11.5px] font-medium text-muted">{s.year} · {s.source}</span></div></td>
                <td className="border-b-[1.5px] border-line px-3 py-2.5">{s.method}</td>
                <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(s.cut, 1)}</td>
                <td className={`num border-b-[1.5px] border-line px-3 py-2.5 text-right font-bold ${gap >= 0 ? "text-positive-text" : "text-negative-text"}`}>{sgn(gap, 1)}</td>
                <td className="border-b-[1.5px] border-line px-3 py-2.5 text-muted">Chưa có nhãn · không hiển thị</td>
                <td className="border-b-[1.5px] border-line px-3 py-2.5"><Tag tone={tone}>{g}</Tag></td>
                <td className="border-b-[1.5px] border-line px-3 py-2.5 text-right"><Button variant="outline" className="min-h-9 px-3" onClick={() => del(s.id)}>Xóa</Button></td>
              </tr>); })}</tbody>
          </table>
          <p className="mt-2 text-[12.5px] font-medium text-muted">Chênh lệch điểm = tổng điểm dự đoán lớp 9 của Toán + Ngữ văn + Tiếng Anh ({fmt(total, 1)}) − điểm chuẩn. Đây là phép so sánh tham khảo, không phải điểm thi dự kiến. Mục tiêu: thấp hơn điểm chuẩn trên 1 điểm · Phù hợp: trong ±1 · Dự phòng: cao hơn trên 1 điểm.</p>
        </div>
      ) : (
        <EmptySticker title="Chưa có dữ liệu điểm chuẩn" description="Thêm các trường mục tiêu cùng điểm chuẩn và nguồn tham chiếu để so sánh. Chênh lệch điểm sẽ được tính; xác suất chỉ hiển thị khi có nhãn tuyển sinh thật." />
      )}
      <form aria-label="Thêm trường THPT" className="grid content-start grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-3" onSubmit={(e) => { e.preventDefault(); add(); }}>
        <TextField label="Tên trường" className="col-span-full" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="VD: THPT [tên trường]" />
        <TextField label="Năm tuyển sinh" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} />
        <SelectField label="Phương thức" value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })}><option>Thi tuyển 3 môn</option><option>Xét tuyển học bạ</option><option>Kết hợp</option></SelectField>
        <TextField label="Điểm chuẩn (thang 30)" required inputMode="decimal" value={form.cut} onChange={(e) => setForm({ ...form, cut: e.target.value })} placeholder="[điểm chuẩn]" />
        <SelectField label="Loại hình" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}><option>Công lập</option><option>Ngoài công lập</option></SelectField>
        <TextField label="Nguồn tham chiếu (bắt buộc)" className="col-span-full" required value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} placeholder="Quyết định / thông báo của Sở GD&ĐT, đường dẫn" />
        {err && <span role="alert" className="col-span-full text-[13px] font-bold text-negative-text">{err}</span>}
        <Button type="submit" disabled={busy} className="justify-self-start">Thêm trường</Button>
      </form>
    </div>
  );
}

function Paths({ f }: { f: Pred["facts"] }) {
  const ok = (t: string) => ({ st: "Đã xác minh", text: t, Icon: CircleCheck, cls: "text-positive-text" });
  const na = (t: string) => ({ st: "Chưa có dữ liệu", text: t, Icon: CircleAlert, cls: "text-warning-text" });
  const talk = (t: string) => ({ st: "Cần trao đổi", text: t, Icon: CircleDashed, cls: "text-muted" });
  const lv = f.muc_ket_qua_hoc_tap_du_doan_lop_9;
  const paths = [
    { title: "THPT công lập", desc: "Thi tuyển 3 môn Toán, Ngữ văn, Tiếng Anh", facts: [ok(`Tổng 3 môn dự đoán ${fmt(f.tong_3_mon, 1)} / 30`), na("Điểm chuẩn thật của trường mục tiêu"), talk("Nguyện vọng và khả năng đi lại")] },
    { title: "THPT ngoài công lập", desc: "Xét tuyển học bạ hoặc kết hợp", facts: [ok(`Mức dự đoán lớp 9: ${lv}`), na("Điều kiện xét tuyển của từng trường"), talk("Học phí và điều kiện gia đình")] },
    { title: "Giáo dục thường xuyên", desc: "Học văn hóa THPT kết hợp nghề", facts: [ok("Điều kiện: tốt nghiệp THCS"), talk("Định hướng nghề song song")] },
    { title: "Giáo dục nghề nghiệp", desc: "Trung cấp / cao đẳng nghề", facts: [ok(`Điểm sáng: ${f.diem_sang.map((s) => s.mon).join(", ")}`), ok("Điều kiện: kết quả học tập và rèn luyện lớp 9 từ mức Đạt"), talk("Ngành nghề phù hợp sở thích")] },
  ];
  const [wish, setWish] = useState("");
  const [note, setNote] = useState("");
  return (
    <Sticker className="flex flex-col gap-4">
      <StickerHeader title="Các phương án học tập sau THCS" description="Trình bày các yếu tố liên quan để giáo viên, học sinh và gia đình cùng cân nhắc. Hệ thống không tự xếp học sinh vào phương án nào." />
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(250px,100%),1fr))] gap-3">
        {paths.map((p) => (
          <div key={p.title} className="flex flex-col gap-2.5 rounded-lg border-[2.5px] border-ink bg-white p-4">
            <strong className="text-[14.5px]">{p.title}</strong><span className="text-[12.5px] font-medium text-muted">{p.desc}</span>
            <div className="flex flex-col gap-1.5 border-t-[1.5px] border-line pt-2">
              {p.facts.map((x) => <span key={x.text} className="flex items-start gap-2 text-[12.5px] font-medium"><x.Icon aria-hidden="true" className={`mt-0.5 size-4 flex-none ${x.cls}`} strokeWidth={2.5} /><span><strong className={x.cls}>{x.st}</strong> · {x.text}</span></span>)}
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(300px,100%),1fr))] gap-3">
        <TextField label="Nguyện vọng của học sinh (giáo viên ghi nhận sau trao đổi)" value={wish} onChange={(e) => setWish(e.target.value)} placeholder="[chưa ghi nhận]" />
        <TextField label="Ghi chú tư vấn" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Nội dung trao đổi với gia đình" />
      </div>
      <p className="m-0 rounded-md bg-surface-soft px-3.5 py-3 text-[12.5px] font-medium leading-relaxed">Hệ thống không thu thập hoàn cảnh gia đình hay điều kiện kinh tế. Các yếu tố này cần được trao đổi trực tiếp. Quyết định cuối cùng thuộc về học sinh và gia đình.</p>
    </Sticker>
  );
}

function MessageBlock({ sid, llms }: { sid: string; llms: string[] }) {
  const [aud, setAud] = useState<(typeof AUD)[number]>("Học sinh");
  const [llm, setLlm] = useState(llms[0] ?? "");
  const [msg, setMsg] = useState<{ text: string; issues: string[]; source: string } | null>(null);
  const [busy, setBusy] = useState<"template" | "llm" | "save" | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => { if (!llm && llms[0]) setLlm(llms[0]); }, [llms, llm]);
  const gen = async (useLlm: boolean) => {
    setBusy(useLlm ? "llm" : "template"); setErr(null); setSaved(false);
    try { setMsg(await apiSend(`/students/${sid}/message`, "POST", { audience: aud, use_llm: useLlm, llm_model: useLlm ? llm : null })); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  const save = async () => {
    if (!msg) return;
    setBusy("save");
    try { await apiSend(`/students/${sid}/message/approve`, "POST", { audience: aud, text: msg.text, source: msg.source }); setSaved(true); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  return (
    <Sticker className="flex flex-col gap-4">
      <StickerHeader title="Thông điệp gửi học sinh, phụ huynh hoặc giáo viên chủ nhiệm" description="LLM chạy trên máy nhà trường chỉ diễn đạt lại dữ kiện đã tính ở trên; không nhận họ tên. Giáo viên duyệt rồi mới lưu."
        action={<Tag tone="lilac">Hỗ trợ · cần giáo viên duyệt</Tag>} />
      <div className="flex flex-wrap items-end gap-3">
        <Segmented label="Người nhận" value={aud} onChange={setAud} options={AUD.map((a) => ({ value: a, label: a }))} />
        {llms.length > 0 && <SelectField label="LLM cục bộ (Ollama)" value={llm} onChange={(e) => setLlm(e.target.value)}>{llms.map((m) => <option key={m}>{m}</option>)}</SelectField>}
        <Button variant="outline" disabled={busy !== null} onClick={() => gen(false)}>{busy === "template" ? "Đang tạo…" : "Thông điệp mẫu theo luật"}</Button>
        <Button disabled={busy !== null || !llm} onClick={() => gen(true)}>{busy === "llm" ? "LLM đang viết (1–3 phút)…" : "Viết bằng LLM"}</Button>
      </div>
      {!llms.length && <span className="text-xs font-medium text-warning-text">Không kết nối được Ollama; chỉ dùng được thông điệp mẫu theo luật.</span>}
      {err && <ErrorSticker message={err} />}
      {busy === "llm" && <LoadingSticker lines={3} title="LLM đang viết" />}
      {msg && (
        <>
          <label className="flex flex-col gap-1 text-xs font-bold">Nguồn: {msg.source} — giáo viên có thể sửa trước khi duyệt
            <textarea value={msg.text} onChange={(e) => setMsg({ ...msg, text: e.target.value })} rows={7} className="rounded-md border-[2.5px] border-ink bg-white px-3 py-2 text-[14px] font-medium leading-relaxed" />
          </label>
          {msg.issues.length ? <span role="alert" className="text-[13px] font-bold text-warning-text">Hàng rào kiểm soát: {msg.issues.join("; ")}</span> : <span className="text-xs font-medium text-positive-text">Hàng rào kiểm soát: không có từ ngữ tiêu cực, số liệu khớp dữ kiện, đúng câu mở đầu.</span>}
          <div className="flex items-center gap-3"><Button variant="dark" disabled={busy !== null || msg.issues.length > 0} onClick={save}>Giáo viên duyệt và lưu</Button>{saved && <span role="status" className="text-[13px] font-bold text-positive-text">Đã lưu vào outputs/thong_diep_da_duyet.csv</span>}</div>
        </>
      )}
    </Sticker>
  );
}
