import type { Metadata } from "next";
import { Fraunces, Manrope } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display-loaded",
  display: "swap",
});

const body = Manrope({
  subsets: ["latin"],
  variable: "--font-body-loaded",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MARP — Multi-Agent Academic Research Platform",
  description:
    "Orchestrated academic literature reviews with agents that search, critique, and write.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable}`}>
        <SiteHeader />
        <main>{children}</main>
        <footer className="site-footer shell">
          MARP · Multi-Agent Academic Research Platform
        </footer>
      </body>
    </html>
  );
}
