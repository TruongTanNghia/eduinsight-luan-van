// Bảng dữ liệu: nằm trong Sticker p-0, đầu bảng nền vàng nhạt, viền dưới đầu bảng 2.5px đen, dòng kẻ màu line.
import { cn } from "./cn";

export type Column<R> = { key: string; header: string; align?: "left" | "right"; numeric?: boolean; render: (row: R) => React.ReactNode };

export function DataTable<R>({ columns, rows, rowKey, empty }: { columns: Column<R>[]; rows: R[]; rowKey: (r: R) => string; empty?: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[13.5px]">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={cn("whitespace-nowrap border-b-[2.5px] border-ink bg-table-head px-3 py-2.5 text-xs font-bold text-ink", c.align === "right" ? "text-right" : "text-left")}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={rowKey(r)} className="hover:bg-surface-soft">
              {columns.map((c) => (
                <td key={c.key} className={cn("whitespace-nowrap border-b-[1.5px] border-line px-3 py-2.5 align-middle", c.align === "right" && "text-right", c.numeric && "num")}>
                  {c.render(r)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (empty ?? <EmptyInline />)}
    </div>
  );
}

function EmptyInline() {
  return <div className="px-5 py-12 text-center font-bold">Không có dữ liệu phù hợp với bộ lọc.</div>;
}
