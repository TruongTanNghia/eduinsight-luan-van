// Tiêu đề trang chuẩn: h1 30px + nhãn + dòng phụ; vùng bên phải cho bộ lọc.
import { DemoBadge } from "./tag";

export function PageHeader({ title, badge, subtitle, right }: { title: string; badge?: string | null; subtitle?: React.ReactNode; right?: React.ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <h1 className="m-0 text-[30px] font-extrabold tracking-[-0.03em]">{title}</h1>
          {badge && <DemoBadge label={badge} />}
        </div>
        {subtitle && <p className="m-0 text-[13.5px] font-medium text-muted">{subtitle}</p>}
      </div>
      {right && <div className="flex flex-wrap items-end gap-3">{right}</div>}
    </header>
  );
}

export function SectionTitle({ title, note }: { title: string; note?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2.5">
      <h2 className="m-0 text-[30px] font-extrabold tracking-[-0.03em]">{title}</h2>
      {note && <span className="text-[13.5px] font-medium">{note}</span>}
    </div>
  );
}
