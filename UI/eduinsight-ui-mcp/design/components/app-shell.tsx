"use client";
// Thanh điều hướng trên cùng: logo sticker nghiêng + nav dạng nút tròn viền đen. KHÔNG dùng sidebar.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "./cn";

export const NAV = [
  { href: "/dashboard", label: "Tổng quan" },
  { href: "/students", label: "Học sinh" },
  { href: "/classes", label: "Lớp học" },
  { href: "/predictions", label: "Dự đoán" },
  { href: "/model-evaluation", label: "Mô hình" },
  { href: "/reports", label: "Báo cáo" },
  { href: "/data-management", label: "Dữ liệu" },
] as const;

export function AppShell({ children, userInitials = "GV" }: { children: React.ReactNode; userInitials?: string }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-dots flex flex-col">
      <header className="mx-auto w-full max-w-[1400px] px-4 sm:px-8 pt-5 flex flex-wrap items-center justify-between gap-3.5">
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/dashboard" className="inline-block -rotate-[2.5deg] rounded-md bg-ink px-3.5 py-1.5 text-[22px] font-extrabold tracking-[-0.02em] text-yellow no-underline hover:text-yellow">
            EduInsight<span className="text-tomato">!</span>
          </Link>
          <nav aria-label="Điều hướng chính" className="flex flex-wrap gap-2">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex min-h-11 items-center rounded-full border-[2.5px] border-ink px-4 text-sm font-bold no-underline transition-shadow",
                    active ? "bg-cobalt text-white shadow-btn hover:text-white" : "bg-white text-ink hover:text-ink hover:shadow-btn"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <span aria-label="Tài khoản" className="flex size-[46px] items-center justify-center rounded-full border-[2.5px] border-ink bg-pink font-extrabold">{userInitials}</span>
      </header>
      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 sm:px-8 pt-6 pb-16 flex flex-col gap-7">{children}</main>
    </div>
  );
}
