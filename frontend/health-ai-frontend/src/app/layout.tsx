import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans", // We'll reuse the variable name for compatibility
  display: "swap",
});

export const metadata: Metadata = {
  title: "HealthAI - Your Advanced Health Assistant",
  description: "An AI-powered health assistant to help you understand and improve your health",
  keywords: ["health", "AI", "assistant", "medical", "healthcare", "wellness"],
  authors: [{ name: "HealthAI Team" }],
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" }
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.variable} antialiased h-full`}>
        {children}
      </body>
    </html>
  );
}
