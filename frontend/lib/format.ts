// Định dạng số kiểu Việt Nam: dấu phẩy thập phân, dấu chấm hàng nghìn.
export function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(digits).replace(".", ",");
}

export function sgn(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const s = fmt(Math.abs(v), digits);
  return v > 0 ? `+${s}` : v < 0 ? `−${s}` : `±${s}`;
}

export function int(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return new Intl.NumberFormat("vi-VN").format(v);
}

export function pct(v: number | null | undefined, digits = 1): string {
  return v === null || v === undefined ? "—" : `${fmt(v, digits)}%`;
}

export function dateVN(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("vi-VN");
}

export const deltaClass = (v: number | null | undefined, t = 0.3) => (v === null || v === undefined ? "text-muted" : v >= t ? "text-positive-text" : v <= -t ? "text-negative-text" : "text-ink");

export const LEVEL_TONE: Record<string, "cobalt" | "mint" | "yellow" | "tomato"> = { "Tốt": "cobalt", "Khá": "mint", "Đạt": "yellow", "Chưa đạt": "tomato" };
export const TREND_KIND: Record<string, "up" | "flat" | "down" | "insufficient"> = { up: "up", up_last: "up", flat: "flat", down: "down", down_last: "down", insufficient: "insufficient" };
