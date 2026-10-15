// Khối nội dung chuẩn. Mọi card/panel/biểu đồ/bảng đều nằm trong Sticker.
import { cn } from "./cn";

type Tone = "white" | "yellow" | "cobalt" | "mint" | "tomato" | "pink" | "lilac";
const TONE: Record<Tone, string> = {
  white: "bg-white text-ink",
  yellow: "bg-yellow text-ink",
  cobalt: "bg-cobalt text-white",
  mint: "bg-mint text-ink",
  tomato: "bg-tomato text-ink",
  pink: "bg-pink text-ink",
  lilac: "bg-lilac text-ink",
};

export function Sticker({ tone = "white", tilt = 0, className, children, as: Tag = "section", ...rest }: React.HTMLAttributes<HTMLElement> & { tone?: Tone; tilt?: number; as?: React.ElementType }) {
  return (
    <Tag
      className={cn("rounded-xl border-[2.5px] border-ink shadow-sticker p-6 min-w-0", TONE[tone], className)}
      style={tilt ? { transform: `rotate(${tilt}deg)` } : undefined}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function StickerHeader({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2.5">
      <div>
        <h2 className="m-0 text-[22px] font-extrabold tracking-[-0.02em]">{title}</h2>
        {description && <p className="mt-1 text-[13px] font-medium text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
