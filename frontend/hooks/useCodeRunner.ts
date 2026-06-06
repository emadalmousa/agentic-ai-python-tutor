"use client"

import { useState } from "react"
import { runCode } from "@/lib/api"
import type { RunResponse } from "@/types/tutor"
import type { TranslationKey } from "@/i18n"

type TFn = (key: TranslationKey, vars?: Record<string, string | number>) => string

export function useCodeRunner(t: TFn) {
  const [output, setOutput] = useState<RunResponse | null>(null)
  const [loading, setLoading] = useState(false)

  async function run(code: string) {
    if (!code.trim()) return
    setLoading(true)
    setOutput(null)
    try {
      const data = await runCode({ code })
      setOutput(data)
    } catch {
      setOutput({ stdout: "", stderr: t("tutor.backendError"), exit_code: 1 })
    } finally {
      setLoading(false)
    }
  }

  return { output, loading, run }
}
