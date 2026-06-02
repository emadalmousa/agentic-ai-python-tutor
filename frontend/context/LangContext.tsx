"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from "react"
import type { Locale, TranslationKey } from "@/i18n"
import { translations, interpolate } from "@/i18n"

interface LangContextType {
  locale: Locale
  setLocale: (l: Locale) => void
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string
}

const STORAGE_KEY = "ki_tutor_lang"

function getInitialLocale(): Locale {
  if (typeof window === "undefined") return "de"
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === "de" || stored === "en" || stored === "ar") return stored
  return "de"
}

const LangContext = createContext<LangContextType>({
  locale: "de",
  setLocale: () => {},
  t: (key) => key,
})

export function LangProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale)

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l)
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, l)
    }
  }, [])

  const t = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>): string => {
      const str = translations[locale][key] ?? key
      return interpolate(str, vars)
    },
    [locale],
  )

  return (
    <LangContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LangContext.Provider>
  )
}

export function useLang(): LangContextType {
  return useContext(LangContext)
}
