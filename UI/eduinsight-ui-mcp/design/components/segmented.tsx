"use client";
// Nhóm lựa chọn (tab trạng thái, chọn môn, phạm vi báo cáo). Mục chọn: nền vàng hoặc cobalt + bóng cứng.
import { cn } from "./cn";

export function Segmented<T extends string>({ value, onChange, options, label, tone = "cobalt" }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; label: string; tone?: "cobalt" | "yellow" }) {
  return (
    <div role="group" aria-label={label} className="inline-flex flex-wrap gap-2">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(o.value)}
            className={cn(
              "min-h-10 rounded-full border-[2.5px] border-ink px-3.5 text-[13px] font-bold transition-shadow",
              on ? (tone === "cobalt" ? "bg-cobalt text-white shadow-btn" : "bg-yellow text-ink shadow-btn") : "bg-white text-ink hover:shadow-btn"
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

// Toggle nhiều lựa chọn (chọn môn trên biểu đồ hồ sơ học sinh)
export function ToggleChips({ items, selected, onToggle }: { items: { key: string; label: string; color: string }[]; selected: string[]; onToggle: (key: string) => void }) {
  return (
    <div role="group" aria-label="Chọn môn hiển thị" className="flex flex-wrap gap-2">
      {items.map((it) => {
        const on = selected.includes(it.key);
        return (
          <button key={it.key} type="button" aria-pressed={on} onClick={() => onToggle(it.key)}
            className={cn("inline-flex min-h-9 items-center gap-2 rounded-full border-[2.5px] border-ink px-3 text-[12.5px] font-bold", on ? "bg-cobalt text-white shadow-btn" : "bg-white text-ink")}>
            <span className="size-2.5 rounded-[3px] border border-ink" style={{ background: it.color }} />
            {it.label}
          </button>
        );
      })}
    </div>
  );
}
