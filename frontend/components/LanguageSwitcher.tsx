"use client"

import { useLang } from "@/context/LangContext"
import { useTheme } from "@/context/ThemeContext"
import type { Locale } from "@/i18n"

const OPTIONS: { locale: Locale; label: string }[] = [
  { locale: "de", label: "DE" },
  { locale: "en", label: "EN" },
  { locale: "ar", label: "ع" },
]

export default function LanguageSwitcher() {
  const { locale, setLocale } = useLang()
  const { dark } = useTheme()

  return (
    <div className="flex items-center gap-0.5">
      {OPTIONS.map(({ locale: l, label }, i) => (
        <span key={l} className="flex items-center">
          <button
            onClick={() => setLocale(l)}
            className={`px-1.5 py-0.5 rounded text-xs font-medium transition-colors ${
              locale === l
                ? dark
                  ? "text-blue-400"
                  : "text-blue-600"
                : dark
                  ? "text-gray-500 hover:text-gray-300"
                  : "text-gray-400 hover:text-gray-600"
            }`}
          >
            {label}
          </button>
          {i < OPTIONS.length - 1 && (
            <span className={`text-xs ${dark ? "text-gray-600" : "text-gray-300"}`}>|</span>
          )}
        </span>
      ))}
    </div>
  )
}
