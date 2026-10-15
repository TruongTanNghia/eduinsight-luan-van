// Trạng thái bắt buộc cho mọi trang/khối: loading, empty, error.
import { Sticker } from "./sticker";
import { Button } from "./button";

export function LoadingSticker({ lines = 3, title = "Đang tải dữ liệu…" }: { lines?: number; title?: string }) {
  return (
    <Sticker aria-busy="true" aria-live="polite">
      <span className="sr-only">{title}</span>
      <div className="mb-4 h-6 w-1/3 rounded-md border-2 border-ink bg-yellow motion-safe:animate-pulse" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="mb-2.5 h-4 rounded-sm bg-neutral motion-safe:animate-pulse" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </Sticker>
  );
}

export function EmptySticker({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <Sticker className="flex flex-col items-center gap-2.5 border-dashed px-5 py-10 text-center shadow-none">
      <strong className="text-base font-extrabold">{title}</strong>
      {description && <p className="m-0 max-w-[46ch] text-[13.5px] font-medium text-muted">{description}</p>}
      {action}
    </Sticker>
  );
}

export function ErrorSticker({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Sticker tone="tomato" role="alert" className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <strong className="text-base font-extrabold">Không tải được dữ liệu</strong>
        <p className="m-0 mt-1 text-[13.5px] font-medium">{message}</p>
      </div>
      {onRetry && <Button variant="outline" onClick={onRetry}>Thử lại</Button>}
    </Sticker>
  );
}
