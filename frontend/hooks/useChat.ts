"use client"

import { useState, useRef, useEffect } from "react"
import { sendChatMessage, analyzeCode } from "@/lib/api"
import type { ChatMessage, TutorResponse } from "@/types/tutor"

function formatAnalysis(r: TutorResponse): string {
  const status = r.error_found ? `🔴 **${r.error_type}**` : "🟢 **Kein Fehler gefunden**"
  let md = `## 🔍 Code-Analyse\n\n${status}\n\n${r.explanation}`

  const sectionTitle = r.error_found ? "🐛 Fehler & Lösung" : "💡 Hinweis"
  md += `\n\n---\n\n**${sectionTitle}**\n\n${r.suggestion}`

  if (r.next_exercise) {
    md += `\n\n**🎯 Nächste Übung**\n\n${r.next_exercise}`
  }

  return md
}

export function useChat(code: string) {
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history, loading, analyzing])

  async function send() {
    const msg = input.trim()
    if (!msg || loading || analyzing) return
    setInput("")
    setError(null)
    const optimistic: ChatMessage[] = [...history, { role: "user", content: msg }]
    setHistory(optimistic)
    setLoading(true)
    try {
      const data = await sendChatMessage({ code, message: msg, history })
      setHistory(data.history)
    } catch {
      setError("Backend nicht erreichbar.")
      setHistory(history)
    } finally {
      setLoading(false)
    }
  }

  async function analyze() {
    if (loading || analyzing) return
    setError(null)
    const trigger: ChatMessage = { role: "user", content: "🔍 Code analysieren" }
    setHistory(prev => [...prev, trigger])
    setAnalyzing(true)
    try {
      const data = await analyzeCode({ code })
      const formatted = formatAnalysis(data)
      setHistory(prev => [...prev, { role: "assistant", content: formatted }])
    } catch {
      setError("Analyse fehlgeschlagen. Ist das Backend erreichbar?")
      setHistory(prev => prev.slice(0, -1))
    } finally {
      setAnalyzing(false)
    }
  }

  function reset() {
    setHistory([])
    setInput("")
    setError(null)
  }

  return {
    history, input, setInput,
    loading, analyzing,
    error,
    send, analyze, reset,
    bottomRef,
  }
}
