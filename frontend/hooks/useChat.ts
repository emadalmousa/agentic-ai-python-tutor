"use client"

import { useState, useRef, useEffect } from "react"
import { sendChatMessage, analyzeCode, uploadMaterial } from "@/lib/api"
import type { ChatMessage, TutorResponse } from "@/types/tutor"
import { useAuth } from "@/context/AuthContext"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

async function saveSession(payload: {
  code: string
  topics: string[]
  errors: string[]
  chat_messages: { role: string; content: string }[]
}) {
  const token = localStorage.getItem("ki_tutor_token")
  if (!token) return
  try {
    await fetch(`${API_URL}/progress/session`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
  } catch {
    // network error — ignore silently, session tracking is non-critical
  }
}

export function useChat(code: string) {
  const { user } = useAuth()
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [materialName, setMaterialName] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

      if (user) {
        const lastTwo = data.history.slice(-2)
        await saveSession({
          code,
          topics: [],
          errors: [],
          chat_messages: lastTwo.map((m) => ({ role: m.role, content: m.content })),
        })
      }
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

      if (user) {
        const errors = data.error_found && data.error_type ? [data.error_type] : []
        await saveSession({
          code,
          topics: [],
          errors,
          chat_messages: [
            { role: "user", content: "🔍 Code analysieren" },
            { role: "assistant", content: formatted },
          ],
        })
      }
    } catch {
      setError("Analyse fehlgeschlagen. Ist das Backend erreichbar?")
      setHistory(prev => prev.slice(0, -1))
    } finally {
      setAnalyzing(false)
    }
  }

  async function uploadPdf(file: File) {
    if (uploading) return
    setError(null)
    setUploading(true)
    setMaterialName(file.name)
    try {
      const data = await uploadMaterial(file)
      const msg: ChatMessage = {
        role: "assistant",
        content: `📚 **Lernmaterial geladen:** ${file.name}\n\n${data.chunks} Abschnitte verarbeitet. Ab jetzt nutze ich dieses Material als Kontext bei der Code-Analyse.`,
      }
      setHistory(prev => [...prev, msg])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "PDF-Upload fehlgeschlagen.")
      setMaterialName(null)
    } finally {
      setUploading(false)
    }
  }

  function openFilePicker() {
    fileInputRef.current?.click()
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) uploadPdf(file)
    e.target.value = ""
  }

  function reset() {
    setHistory([])
    setInput("")
    setError(null)
    setMaterialName(null)
  }

  return {
    history, input, setInput,
    loading, analyzing, uploading, materialName,
    error,
    send, analyze, reset,
    openFilePicker, handleFileInput, fileInputRef,
    bottomRef,
  }
}
