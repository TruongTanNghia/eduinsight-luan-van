"use client";
// Theme Recharts cho phong cách Sticker. Đường dày, chấm vàng viền đen, cột viền đen bo trên.
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";

export const C = {
  ink: "#111111", cobalt: "#2B59FF", pink: "#FF8FC7", mint: "#3DDC97", yellow: "#FFD23F", tomato: "#FF5A36", lilac: "#B8A4FF", grid: "#EADFC3",
  series: ["#2B59FF", "#3DDC97", "#FF8FC7", "#B8A4FF", "#FFD23F", "#FF5A36", "#06AED4", "#CA8504"],
};
export const axisProps = { stroke: C.ink, tick: { fill: C.ink, fontSize: 12, fontFamily: "var(--font-jetbrains)" }, tickLine: false } as const;

export function StickerTooltip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border-[2.5px] border-ink bg-white px-3 py-2 shadow-btn">
      <div className="text-xs font-extrabold">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="num flex items-center gap-2 text-[12.5px]"><span className="size-2.5 border border-ink" style={{ background: p.color }} />{p.name}: {p.value.toFixed(2).replace(".", ",")}</div>
      ))}
    </div>
  );
}

// Biểu đồ đường ĐTB theo học kỳ (dashboard, hồ sơ, lớp)
export function TrendLineChart({ data, lines, domain = [6, 9] }: { data: Record<string, number | string | null>[]; lines: { key: string; name: string; color?: string; dashed?: boolean }[]; domain?: [number, number] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 24, right: 16, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={C.grid} strokeWidth={1.5} vertical={false} />
        <XAxis dataKey="semester" {...axisProps} />
        <YAxis domain={domain} {...axisProps} tickFormatter={(v) => String(v).replace(".", ",")} />
        <Tooltip content={<StickerTooltip />} />
        {lines.map((l, i) => (
          <Line key={l.key} type="linear" dataKey={l.key} name={l.name} connectNulls={false}
            stroke={l.color ?? C.series[i]} strokeWidth={i === 0 ? 6 : 5} strokeLinecap="round" strokeDasharray={l.dashed ? "8 6" : undefined}
            dot={i === 0 ? { r: 9, fill: C.yellow, stroke: C.ink, strokeWidth: 2.5 } : false} activeDot={{ r: 10, fill: C.yellow, stroke: C.ink, strokeWidth: 2.5 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// Cột môn học: môn dưới ngưỡng tô tomato, còn lại xoay vòng màu series. Viền đen 2.5px.
export function SubjectBarChart({ data, average, lowGap = 0.3 }: { data: { subject: string; value: number }[]; average: number; lowGap?: number }) {
  let k = 0;
  const cyc = [C.cobalt, C.mint, C.pink, C.lilac, C.yellow];
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 20, right: 8, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={C.grid} strokeWidth={1.5} vertical={false} />
        <XAxis dataKey="subject" {...axisProps} tick={{ ...axisProps.tick, fontFamily: "var(--font-bricolage)", fontWeight: 700 }} />
        <YAxis domain={[5, 9]} {...axisProps} />
        <Tooltip content={<StickerTooltip />} cursor={{ fill: "rgba(17,17,17,.05)" }} />
        <ReferenceLine y={average} stroke={C.ink} strokeDasharray="6 4" strokeWidth={1.5} />
        <Bar dataKey="value" name="ĐTB" stroke={C.ink} strokeWidth={2.5} radius={[10, 10, 0, 0]}>
          {data.map((d) => <Cell key={d.subject} fill={d.value <= average - lowGap ? C.tomato : cyc[k++ % cyc.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
