// Ô chọn kỳ: nhóm theo lớp (Lớp 6: HK1, HK2, Cả năm …). Dùng chung cho Tổng quan, Học sinh, Lớp học, Báo cáo.
import { SelectField } from "./field";

export type PeriodOption = { key: string; grade: number; ky: number; kind: string; label: string; year: string };

export function PeriodSelect({ periods, value, onChange, label = "Kỳ" }: { periods: PeriodOption[]; value: string; onChange: (key: string) => void; label?: string }) {
  const grades = [...new Set(periods.map((p) => p.grade))];
  return (
    <SelectField label={label} value={value} onChange={(e) => onChange(e.target.value)}>
      {grades.map((g) => {
        const ps = periods.filter((p) => p.grade === g);
        return (
          <optgroup key={g} label={`Lớp ${g} · ${ps[0]?.year ?? ""}`}>
            {ps.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
          </optgroup>
        );
      })}
    </SelectField>
  );
}
