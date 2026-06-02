"use client"

import { useEffect } from "react"
import { useLang } from "@/context/LangContext"

export default function HtmlDirSync() {
  const { locale } = useLang()

  useEffect(() => {
    document.documentElement.lang = locale
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr"
  }, [locale])

  return null
}
