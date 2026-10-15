import { cn } from "./cn";

const control = "h-11 rounded-md border-[2.5px] border-ink bg-white px-3 text-sm font-semibold text-ink min-w-[120px] focus-visible:outline-3 focus-visible:outline-cobalt";

export function SelectField({ label, className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className={cn("flex flex-col gap-1 text-xs font-bold", className)}>
      {label}
      <select className={control} {...props}>{children}</select>
    </label>
  );
}

export function TextField({ label, className, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className={cn("flex flex-col gap-1 text-xs font-bold", className)}>
      {label}
      <input className={cn(control, "w-full")} {...props} />
    </label>
  );
}

// Hàng bộ lọc chuẩn (Tổng quan, Học sinh, Lớp): flex-wrap, gap-3, items-end.
export function FilterBar({ children, source }: { children: React.ReactNode; source?: string }) {
  return (
    <form aria-label="Bộ lọc" className="flex flex-wrap items-end gap-3" onSubmit={(e) => e.preventDefault()}>
      {children}
      {source && <span className="num ml-auto self-center text-xs">{source}</span>}
    </form>
  );
}
