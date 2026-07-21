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
        {/* SVG filter for photorealistic liquid glass refraction & dispersion */}
        <svg style={{ width: 0, height: 0, position: 'absolute' }} aria-hidden="true" focusable="false">
          <defs>
            <filter id="apple-glass-dispersion" x="-20%" y="-20%" width="140%" height="140%">
              {/* Generate microscopic organic noise for frosted glass texture */}
              <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="3" result="noise" />
              {/* Soften the noise impact */}
              <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.15 0" in="noise" result="coloredNoise" />
              {/* Physically displace (refract) the pixels behind the element based on the noise map */}
              <feDisplacementMap in="SourceGraphic" in2="coloredNoise" scale="5" xChannelSelector="R" yChannelSelector="G" result="displacement" />
            </filter>
          </defs>
        </svg>
        <Sidebar />
        <div style={{ flex: 1, minWidth: 0 }}>
          {children}
        </div>
      </body>
    </html>
  );
}
