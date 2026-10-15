import { cn } from "./cn";

type Variant = "primary" | "dark" | "outline" | "danger";
const V: Record<Variant, string> = {
  primary: "bg-cobalt text-white hover:text-white",
  dark: "bg-ink text-yellow hover:text-white",
  outline: "bg-white text-ink hover:text-ink",
  danger: "bg-tomato text-ink hover:text-ink",
};

export function buttonClass(variant: Variant = "primary", className?: string) {
  return cn(
    "press inline-flex min-h-11 items-center justify-center gap-2 rounded-md border-[2.5px] border-ink px-4 text-sm font-extrabold no-underline shadow-btn",
    "disabled:cursor-not-allowed disabled:opacity-45 disabled:shadow-none disabled:transform-none",
    V[variant],
    className
  );
}

export function Button({ variant = "primary", className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={buttonClass(variant, className)} {...props} />;
}
// Link dạng nút: <Link href="/reports" className={buttonClass("dark")}>Xuất báo cáo</Link>
