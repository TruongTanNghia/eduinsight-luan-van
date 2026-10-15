"use client";
// Lớp học — danh sách lớp theo kỳ (HK1 / HK2 / Cả năm), dẫn tới /classes/[id]
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { FilterBar } from "@/components/ui/field";
import { PeriodSelect } from "@/components/ui/period-select";
import { PageHeader } from "@/components/ui/page-header";
import { EmptySticker, ErrorSticker, LoadingSticker } from "@/components/ui/states";
import { Sticker } from "@/components/ui/sticker";
import { Tag } from "@/components/ui/tag";
import { useApi, useMeta } from "@/lib/api";
import { fmt, int } from "@/lib/format";

type Cls = { id: string; name: string; avg: number; up: number; down: number; n: number };

export default function ClassesPage() {
  return <Suspense fallback={<LoadingSticker />}><Classes /></Suspense>;
}

function Classes() {
  const sp = useSearchParams();
  const router = useRouter();
  const period = sp.get("period") ?? "";
  const meta = useMeta();
  const pkey = period || meta.data?.defaultPeriod || "";
  const { data, error, loading, reload } = useApi<Cls[]>(pkey ? `/classes?period=${pkey}` : null);
  const pl = meta.data?.periods.find((p) => p.key === pkey);
  return (
    <>
      <PageHeader title="Lớp học" badge="Thực tế · tính từ dữ liệu" subtitle={<>Chọn một lớp để xem tiến bộ, ổn định và sa sút của từng em · ▲ số em ĐTB tăng ≥ 0,3 · ▼ số em giảm ≥ 0,3 so với kỳ trước</>}
        right={<FilterBar><PeriodSelect periods={meta.data?.periods ?? []} value={pkey} onChange={(v) => router.replace(`/classes?period=${v}`)} /></FilterBar>} />
      {error && <ErrorSticker message={error} onRetry={reload} />}
      {loading && !data && <LoadingSticker lines={4} />}
      {data && data.length === 0 && <EmptySticker title="Chưa có lớp nào ở kỳ này" />}
      {data && data.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(250px,100%),1fr))] gap-[18px]">
          {data.map((c) => (
            <Sticker key={c.id} as="article" className="flex flex-col gap-2.5 p-[18px]">
              <div className="flex items-center justify-between"><strong className="text-xl font-extrabold">{c.name}</strong><Tag tone="white">{pl?.label ?? pkey}</Tag></div>
              <span className="num text-[44px] font-extrabold leading-none tracking-[-0.04em]">{fmt(c.avg)}</span>
              <span className="text-[12.5px] font-medium">ĐTB lớp · {int(c.n)} học sinh</span>
              <div className="flex gap-2"><Tag tone="mint">▲ {c.up} tiến bộ</Tag><Tag tone="tomato">▼ {c.down} sa sút</Tag></div>
              <Link href={`/classes/${c.id}?period=${pkey}`} className="press mt-1 inline-flex min-h-11 items-center justify-center rounded-md border-[2.5px] border-ink bg-white text-sm font-extrabold text-ink no-underline shadow-btn hover:text-ink">Phân tích lớp</Link>
            </Sticker>
          ))}
        </div>
      )}
    </>
  );
}
