// app/layout.tsx — nạp font có subset tiếng Việt và khung AppShell.
import type { Metadata } from "next";
import { Bricolage_Grotesque, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/ui/app-shell";

const bricolage = Bricolage_Grotesque({ subsets: ["latin", "vietnamese"], variable: "--font-bricolage", weight: ["400", "500", "600", "700", "800"] });
const jetbrains = JetBrains_Mono({ subsets: ["latin", "vietnamese"], variable: "--font-jetbrains", weight: ["400", "500", "700"] });

export const metadata: Metadata = { title: "EduInsight AI", description: "Phân tích kết quả học tập và định hướng cho học sinh THCS" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${bricolage.variable} ${jetbrains.variable}`}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
