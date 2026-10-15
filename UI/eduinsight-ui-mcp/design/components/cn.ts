// Gộp className không cần thư viện. Có thể thay bằng clsx + tailwind-merge nếu dự án đã dùng.
export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}
