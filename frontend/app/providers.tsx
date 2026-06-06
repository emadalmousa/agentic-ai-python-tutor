"use client"

import { AuthProvider } from "@/context/AuthContext"
import { ThemeProvider } from "@/context/ThemeContext"
import { LangProvider } from "@/context/LangContext"
import HtmlDirSync from "@/components/HtmlDirSync"
import { ReactNode } from "react"

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <LangProvider>
      <ThemeProvider>
        <HtmlDirSync />
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </LangProvider>
  )
}
