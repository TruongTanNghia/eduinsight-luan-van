"use client";
// 06 · Đánh giá mô hình — /model-evaluation
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { SelectField } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker, StickerHeader } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { useApi, useMeta } from "@/lib/api";
import { fmt, int } from "@/lib/format";

type ModelRow = { id: string; name: string; group: string; served: boolean; proposed: boolean; best: boolean; rmse: number; rmseStd: number; mae: number; r2: number; macroF1: number; acc: number; picp: number; mpiw: number; examRmse: number; seconds: number };
type Metrics = {
  id: string; task: string; card: { inputs: string; split: string; selection: string; datasetVersion: string; checkpoint: string | null; seeds: string; evalWindows: number; trainWindows: number };
  perSubject: { subject: string; short: string; rmse: number; mae: number; picp: number }[]; perRun: { run: string; rmse: number; mae: number; macroF1: number | null; picp: number }[];
  avgRank: number | null; friedman: { friedman_chi2: number; friedman_p: number; nemenyi_cd: number; n_blocks: number };
  wilcoxon: { vs: string; maeProposed: number; maeOther: number; diff: number; pStudent: number | string; pBlock: number | null }[];
  nemenyi: { models: string[]; rows: (string | number)[][] } | null; importance: { feature: string; period: string; value: number }[] | null; hidden: { metric: string; reason: string }[];
};

export default function ModelEvalPage() {
  return <Suspense fallback={<LoadingSticker />}><ModelEval /></Suspense>;
}

function ModelEval() {
  const sp = useSearchParams();
  const router = useRouter();
  const meta = useMeta();
  const models = useApi<{ items: ModelRow[] }>("/ai/models");
  const id = sp.get("model") ?? "XEdu-KANFormer";
  const m = useApi<Metrics>(`/ai/models/${encodeURIComponent(id)}/metrics`);
  const items = models.data?.items ?? [];
  const cur = items.find((x) => x.id === id);
  const proposed = items.find((x) => x.proposed);
  const best = items.find((x) => x.best);
  const main = items.filter((x) => x.group !== "ablation");
  const rankOf = (mid: string) => main.findIndex((x) => x.id === mid) + 1;

  return (
    <>
      <PageHeader title="Đánh giá mô hình" badge={models.data ? "Số liệu thực nghiệm · reports/" : null}
        subtitle={<>Mọi chỉ số đọc từ báo cáo đánh giá đã lưu (reports/metrics_runs.csv, summary.csv, wilcoxon.csv, nemenyi_p.csv). Chỉ số không phù hợp với nhãn bị ẩn kèm lý do.</>}
        right={<SelectField label="Mô hình" className="min-w-[260px]" value={id} onChange={(e) => router.replace(`/model-evaluation?model=${encodeURIComponent(e.target.value)}`)}>{(items.length ? items : [{ id, name: id }]).map((x) => <option key={x.id} value={x.id}>{x.name}{"proposed" in x && x.proposed ? " · đề xuất" : ""}</option>)}</SelectField>} />

      {models.error && <ErrorSticker message={models.error} onRetry={models.reload} />}
      {models.data && (
        <Sticker className="p-0">
          <div className="flex flex-wrap items-start justify-between gap-2.5 px-5 pb-3 pt-[18px]">
            <StickerHeader title="So sánh với các mô hình cơ sở" description={`Trung bình 8 môn lớp 9 trên ${items.length ? "15 lần chạy (5 lần gập × 3 hạt giống)" : "…"} · ± độ lệch chuẩn · xếp theo RMSE tăng dần`} />
            <div className="flex gap-2"><Tag tone="yellow">Đề xuất: {proposed?.name ?? "—"}</Tag><Tag tone="mint">Tốt nhất: {best?.name ?? "—"}</Tag></div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[13.5px]">
              <thead><tr>{["#", "Mô hình", "RMSE", "MAE", "R²", "Macro-F1", "Acc", "PICP", "MPIW", "RMSE 3 môn thi", "Thời gian (s)"].map((h, i) => <th key={h} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i >= 2 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
              <tbody>{items.map((x) => (
                <tr key={x.id} className={`hover:bg-surface-soft ${x.id === id ? "bg-surface-soft" : ""}`}>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5">{x.group === "ablation" ? "—" : rankOf(x.id)}</td>
                  <td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{x.name} {x.proposed && <Tag tone="yellow">đề xuất</Tag>} {x.served && <Tag tone="cobalt">đang phục vụ</Tag>} {x.group === "ablation" && <Tag tone="neutral">biến thể</Tag>} {x.group === "reference" && <Tag tone="white">tham chiếu</Tag>}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.rmse, 3)} ± {fmt(x.rmseStd, 3)}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.mae, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.r2, 3)}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.macroF1, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.acc, 3)}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.picp, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.mpiw)}</td>
                  <td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.examRmse, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(x.seconds, 1)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </Sticker>
      )}

      {m.error && <ErrorSticker message={m.error} onRetry={m.reload} />}
      {m.loading && !m.data && <LoadingSticker lines={5} />}
      {m.data && cur && (
        <>
          <Sticker className="grid grid-cols-[repeat(auto-fit,minmax(min(220px,100%),1fr))] gap-x-6 gap-y-[18px]">
            <Kv k="Bài toán" v={m.data.task} />
            <Kv k="Mô hình" v={<>{m.data.id} · {cur.group === "ablation" ? "biến thể loại bỏ thành phần" : `hạng ${rankOf(m.data.id)}/${main.length} theo RMSE`}</>} />
            <Kv k="Phiên bản dữ liệu" v={<span className="num">{m.data.card.datasetVersion}</span>} />
            <Kv k="Checkpoint" v={<span className="num text-[12.5px]">{m.data.card.checkpoint ?? "chưa xuất (chỉ đánh giá chéo)"}</span>} />
            <Kv k="Hạt giống" v={<span className="num">{m.data.card.seeds}</span>} />
            <Kv k="Cửa sổ huấn luyện / đánh giá" v={<span className="num">{int(m.data.card.trainWindows)} / {int(m.data.card.evalWindows)}</span>} />
            <Kv k="Tiêu chí chọn mô hình" v={m.data.card.selection} />
            <Kv k="Thời gian huấn luyện" v={<span className="num">{fmt(cur.seconds, 1)} s / lần chạy</span>} />
            <Kv k="Đặc trưng đầu vào" v={m.data.card.inputs} />
            <Kv k="Chia dữ liệu" v={m.data.card.split} />
          </Sticker>

          <section className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] gap-6">
            <Sticker className="p-0">
              <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Sai số theo từng môn" description="Trung bình các lần chạy · PICP là độ phủ của khoảng 90%" /></div>
              <div className="overflow-x-auto"><table className="w-full border-collapse text-[13.5px]">
                <thead><tr>{["Môn", "RMSE", "MAE", "PICP"].map((h, i) => <th key={h} scope="col" className={`border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold ${i ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
                <tbody>{m.data.perSubject.map((s) => <tr key={s.subject} className="hover:bg-surface-soft"><td className="border-b-[1.5px] border-line px-3 py-2.5 font-bold">{s.subject}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(s.rmse, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(s.mae, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2.5 text-right">{fmt(s.picp, 3)}</td></tr>)}</tbody>
              </table></div>
            </Sticker>
            <Sticker className="p-0">
              <div className="px-5 pb-2.5 pt-[18px]"><StickerHeader title="Từng lần chạy" description="cv{k}_s{h}: lần gập k, hạt giống h · đánh giá trên cửa sổ lớp 9 ngoài tập huấn luyện" /></div>
              <div className="max-h-[360px] overflow-auto"><table className="w-full border-collapse text-[13px]">
                <thead><tr>{["Lần chạy", "RMSE", "MAE", "Macro-F1", "PICP"].map((h, i) => <th key={h} scope="col" className={`sticky top-0 border-b-[2.5px] border-ink bg-table-head px-3 py-2 text-xs font-bold ${i ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
                <tbody>{m.data.perRun.map((r) => <tr key={r.run} className="hover:bg-surface-soft"><td className="num border-b-[1.5px] border-line px-3 py-2">{r.run}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.rmse, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.mae, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.macroF1, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(r.picp, 3)}</td></tr>)}</tbody>
              </table></div>
            </Sticker>
          </section>

          <section className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] gap-6">
            <Sticker className="flex flex-col gap-3.5">
              <StickerHeader title="Kiểm định thống kê" description={`Friedman trên ${m.data.friedman.n_blocks} khối (lần chạy × môn) · hậu kiểm Nemenyi · Wilcoxon theo học sinh`} />
              <div className="grid grid-cols-[repeat(auto-fit,minmax(min(140px,100%),1fr))] gap-2.5">
                <Kv k="Friedman χ²" v={<span className="num">{fmt(m.data.friedman.friedman_chi2)}</span>} />
                <Kv k="p-value" v={<span className="num">{m.data.friedman.friedman_p < 0.0001 ? "< 0,0001" : fmt(m.data.friedman.friedman_p, 4)}</span>} />
                <Kv k="CD Nemenyi (α = 0,05)" v={<span className="num">{fmt(m.data.friedman.nemenyi_cd)}</span>} />
                <Kv k="Hạng trung bình của mô hình" v={<span className="num">{fmt(m.data.avgRank)}</span>} />
              </div>
              {m.data.wilcoxon.length > 0 && (
                <div className="overflow-x-auto"><table className="w-full border-collapse text-[13px]">
                  <thead><tr>{["Đề xuất so với", "MAE đề xuất", "MAE đối thủ", "Chênh lệch", "p (học sinh)", "p (khối)"].map((h, i) => <th key={h} scope="col" className={`whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2 text-xs font-bold ${i ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
                  <tbody>{m.data.wilcoxon.map((w) => <tr key={w.vs} className="hover:bg-surface-soft"><td className="border-b-[1.5px] border-line px-3 py-2 font-bold">{w.vs}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(w.maeProposed, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(w.maeOther, 3)}</td><td className={`num border-b-[1.5px] border-line px-3 py-2 text-right font-bold ${w.diff < 0 ? "text-positive-text" : "text-negative-text"}`}>{w.diff > 0 ? "+" : ""}{fmt(w.diff, 3)}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{typeof w.pStudent === "number" ? fmt(w.pStudent, 4) : w.pStudent}</td><td className="num border-b-[1.5px] border-line px-3 py-2 text-right">{fmt(w.pBlock, 4)}</td></tr>)}</tbody>
                </table><p className="mt-2 text-xs font-medium text-muted">Chênh lệch âm: mô hình đề xuất sai số thấp hơn. Bảng Wilcoxon luôn so mô hình đề xuất ({proposed?.name}) với từng mô hình.</p></div>
              )}
            </Sticker>
            <Sticker tone="yellow" className="flex flex-col gap-3">
              <StickerHeader title="Kết luận thận trọng" />
              <Conclusion items={items} proposed={proposed} best={best} friedmanP={m.data.friedman.friedman_p} />
              <div className="flex flex-col gap-1.5 border-t-[2.5px] border-ink pt-3">
                {m.data.hidden.map((h) => <span key={h.metric} className="text-[12.5px] font-medium"><strong>Ẩn: {h.metric}.</strong> {h.reason}</span>)}
              </div>
            </Sticker>
          </section>

          {m.data.importance && <Importance rows={m.data.importance} />}
        </>
      )}
    </>
  );
}

function Conclusion({ items: all, proposed, best, friedmanP }: { items: ModelRow[]; proposed?: ModelRow; best?: ModelRow; friedmanP: number }) {
  if (!proposed || !best) return null;
  const items = all.filter((x) => x.group !== "ablation");
  const rank = items.findIndex((x) => x.id === proposed.id) + 1;
  const overlap = Math.abs(proposed.rmse - best.rmse) <= proposed.rmseStd;
  return (
    <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-[13.5px] font-medium leading-relaxed">
      <li>Mô hình đề xuất {proposed.name} xếp hạng {rank}/{items.length} theo RMSE ({fmt(proposed.rmse, 3)} ± {fmt(proposed.rmseStd, 3)}); mô hình tốt nhất là {best.name} ({fmt(best.rmse, 3)}).</li>
      <li>{overlap ? "Chênh lệch với mô hình tốt nhất nằm trong một độ lệch chuẩn giữa các lần chạy, nên chưa thể kết luận mô hình nào vượt trội." : "Chênh lệch với mô hình tốt nhất vượt một độ lệch chuẩn giữa các lần chạy; mô hình đề xuất chưa đạt mục tiêu vượt mô hình cơ sở tốt nhất."}</li>
      <li>Kiểm định Friedman {friedmanP < 0.05 ? "cho thấy các mô hình khác nhau có ý nghĩa thống kê" : "chưa cho thấy khác biệt có ý nghĩa"}; cặp nào có hạng trung bình cách nhau dưới CD Nemenyi thì chưa khác biệt.</li>
      <li>Macro-F1 của đầu phân mức chỉ phản ánh 3 lớp (khóa này không có mức Chưa đạt). Không mặc định Transformer tốt hơn baseline.</li>
    </ul>
  );
}

function Kv({ k, v }: { k: string; v: React.ReactNode }) {
  return <div className="flex flex-col gap-1"><span className="text-xs font-bold text-muted">{k}</span><span className="text-[13.5px] font-bold leading-snug">{v}</span></div>;
}

function Importance({ rows }: { rows: { feature: string; period: string; value: number }[] }) {
  const feats = [...new Set(rows.map((r) => r.feature))];
  const grades = [...new Set(rows.map((r) => r.period))];
  const max = Math.max(...rows.map((r) => r.value), 0.001);
  const order = feats.sort((a, b) => rows.filter((r) => r.feature === b).reduce((s, r) => s + r.value, 0) - rows.filter((r) => r.feature === a).reduce((s, r) => s + r.value, 0));
  return (
    <Sticker className="flex flex-col gap-3.5">
      <StickerHeader title="Ô nào quan trọng với mô hình (toàn cục)" description="Độ quan trọng hoán vị trên lần gập đầu tiên: RMSE trung bình 8 môn tăng bao nhiêu khi xáo trộn một ô (đặc trưng × mốc thời gian) giữa các học sinh" />
      <div className="overflow-x-auto">
        <div className="grid min-w-[420px] gap-1" style={{ gridTemplateColumns: `170px repeat(${grades.length}, minmax(80px, 1fr))` }}>
          <span />{grades.map((g) => <span key={g} className="pb-1 text-center text-[11.5px] font-bold text-muted">{g}</span>)}
          {order.map((fe) => (
            <ImpRow key={fe} fe={fe} grades={grades} rows={rows} max={max} />
          ))}
        </div>
      </div>
    </Sticker>
  );
}

function ImpRow({ fe, grades, rows, max }: { fe: string; grades: string[]; rows: { feature: string; period: string; value: number }[]; max: number }) {
  return (
    <>
      <span className="flex items-center text-[12.5px] font-bold">{fe}</span>
      {grades.map((g) => {
        const r = rows.find((x) => x.feature === fe && x.period === g);
        const k = r ? Math.max(0, r.value) / max : 0;
        const lerp = (a: number, b: number) => Math.round(a + (b - a) * k);
        return <span key={g} title={`${fe} · ${g}: ${fmt(r?.value, 3)}`} className={`num flex h-8 items-center justify-center rounded-[5px] border border-ink text-xs font-bold ${k > 0.5 ? "text-white" : "text-ink"}`} style={{ background: `rgb(${lerp(255, 43)},${lerp(255, 89)},${lerp(255, 255)})` }}>{r ? fmt(r.value, 3) : "—"}</span>;
      })}
    </>
  );
}
