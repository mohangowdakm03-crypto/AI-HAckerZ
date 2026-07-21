import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI-HackerZ | GraphRAG Brain",
  description: "Elite industrial GraphRAG dashboard. Fully offline, zero cloud dependencies.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body style={{ display: 'flex' }}>
        <Sidebar />
        <div style={{ flex: 1, minWidth: 0 }}>
          {children}
        </div>
      </body>
    </html>
  );
}
