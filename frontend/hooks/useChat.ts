"use client"

import { useState, useRef, useEffect } from "react"
import { sendChatMessage } from "@/lib/api"
import type { ChatMessage } from "@/types/tutor"

export function useChat(code: string) {
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history, loading])

  async function send() {
    const msg = input.trim()
    if (!msg || loading) return
    setInput("")
    setError(null)
    // User-Nachricht sofort anzeigen
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

  function reset() {
    setHistory([])
    setInput("")
    setError(null)
  }

  return { history, input, setInput, loading, error, send, reset, bottomRef }
}
