import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Academic Copilot",
  description: "Read research papers like a professor explains them.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
