import { cn } from "./cn";

type Tone = "yellow" | "cobalt" | "mint" | "tomato" | "pink" | "lilac" | "white" | "neutral" | "warning";
const T: Record<Tone, string> = {
  yellow: "bg-yellow text-ink", cobalt: "bg-cobalt text-white", mint: "bg-mint text-ink", tomato: "bg-tomato text-ink",
  pink: "bg-pink text-ink", lilac: "bg-lilac text-ink", white: "bg-white text-ink", neutral: "bg-neutral text-muted-strong", warning: "bg-warning text-ink",
};

export function Tag({ tone = "white", tilt, className, children }: { tone?: Tone; tilt?: boolean; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border-2 border-ink px-2.5 py-0.5 text-xs font-bold", T[tone], tilt && "-rotate-2", className)}>
      {children}
    </span>
  );
}

// Nhãn bắt buộc khi trang hiển thị dữ liệu giả lập hoặc kết quả mô hình chưa kiểm chứng.
export function DemoBadge({ label = "Dữ liệu minh họa" }: { label?: string }) {
  return <Tag tone="yellow" tilt>{label}</Tag>;
}

// Xu hướng: luôn có chữ, không chỉ dựa vào màu.
export function TrendTag({ trend }: { trend: "up" | "flat" | "down" | "insufficient" }) {
  const map = {
    up: { tone: "mint", text: "Tiến bộ" },
    flat: { tone: "neutral", text: "Ổn định" },
    down: { tone: "tomato", text: "Sa sút" },
    insufficient: { tone: "white", text: "Chưa đủ dữ liệu" },
  } as const;
  const m = map[trend];
  return <Tag tone={m.tone}>{m.text}</Tag>;
}
