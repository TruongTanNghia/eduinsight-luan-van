// Thẻ số liệu lớn (KPI). Nghiêng nhẹ xen kẽ theo tokens.rotation.stickerTilt.
import { Sticker } from "./sticker";

export function StatSticker({ label, value, hint, tone, tilt = 0 }: { label: string; value: string; hint?: string; tone: "cobalt" | "mint" | "tomato" | "lilac" | "yellow" | "pink" | "white"; tilt?: number }) {
  return (
    <Sticker tone={tone} tilt={tilt} as="div" className="flex min-h-[140px] flex-col justify-between gap-1 px-5 py-[18px]">
      <span className="text-sm font-bold">{label}</span>
      <span className="text-[52px] font-extrabold leading-none tracking-[-0.04em]">{value}</span>
      {hint && <span className="text-[12.5px] font-medium">{hint}</span>}
    </Sticker>
  );
}
// Dùng: const TILT = [-1.5, 1.2, 1, -1.2]; stats.map((s, i) => <StatSticker key={s.label} {...s} tilt={TILT[i % 4]} />)
