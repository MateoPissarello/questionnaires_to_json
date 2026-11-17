import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Giunti Psychometrics · Instrument Digitization Workbench",
  description:
    "Extracción y estructuración estandarizada de cuestionarios psicométricos desde PDF, Word y Excel.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${jakarta.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen font-[family-name:var(--font-sans)] text-[#111827] antialiased">
        {children}
      </body>
    </html>
  );
}
