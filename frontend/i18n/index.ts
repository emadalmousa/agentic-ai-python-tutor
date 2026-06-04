export type Locale = "de" | "en"

export { default as de } from "./de"
export type { TranslationKey } from "./de"
export { default as en } from "./en"

import deStrings from "./de"
import enStrings from "./en"
import type { TranslationKey } from "./de"

export const translations: Record<Locale, Record<TranslationKey, string>> = {
  de: deStrings,
  en: enStrings,
}

/**
 * Interpolate `{placeholder}` patterns in a translated string.
 * Example: interpolate("Übung {n} von {total}", { n: 1, total: 5 }) => "Übung 1 von 5"
 */
export function interpolate(
  template: string,
  vars?: Record<string, string | number>,
): string {
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const val = vars[key]
    return val !== undefined ? String(val) : `{${key}}`
  })
}
