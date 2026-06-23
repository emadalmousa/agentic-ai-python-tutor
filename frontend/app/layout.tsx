import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Providers from "./providers";
import Navbar from "@/components/Navbar";
import PageFadeIn from "@/components/PageFadeIn";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  preload: false,
});

export const metadata: Metadata = {
  title: "Python Tutor — Agentic AI",
  description: "KI-gestützter Python-Tutor: Code erklären, Fehler finden, Übungen generieren",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="h-full flex flex-col overflow-hidden">
        <Providers>
          <Navbar />
          <PageFadeIn>
            {children}
          </PageFadeIn>
        </Providers>
      </body>
    </html>
  );
}
