"use client"

import { useState } from "react"
import { analyzeCode } from "@/lib/api"
import type { TutorResponse } from "@/types/tutor"

// Gesamter State und Logik für die Tutor-Analyse — getrennt von der UI
export function useTutorAnalysis() {
  const [code, setCode] = useState("for i in range(5)\n    print(i)")
  const [question, setQuestion] = useState("")
  const [result, setResult] = useState<TutorResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function analyze() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeCode({ code, question: question || undefined })
      setResult(data)
    } catch {
      setError("Backend nicht erreichbar. Ist das FastAPI-Backend gestartet?")
    } finally {
      setLoading(false)
    }
  }

  return { code, setCode, question, setQuestion, result, loading, error, analyze }
}
