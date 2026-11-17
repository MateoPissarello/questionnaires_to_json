import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Giunti Psychometrics · Digitalizador de Cuestionarios",
  description:
    "Extracción y estructuración estandarizada de cuestionarios psicométricos desde PDF, Word y Excel.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen font-[family-name:var(--font-sans)] text-[#111827] antialiased">
        {children}
      </body>
    </html>
  );
}
