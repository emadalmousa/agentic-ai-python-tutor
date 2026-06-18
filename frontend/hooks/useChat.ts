"use client"

import { useState, useRef, useEffect } from "react"
import { sendChatMessage, analyzeCode, uploadMaterial, saveChatHistory, updateChatHistory } from "@/lib/api"
import type { ChatMessage, TutorResponse } from "@/types/tutor"
import type { TranslationKey } from "@/i18n"

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

type TFn = (key: TranslationKey, vars?: Record<string, string | number>) => string

const _HISTORY_KEY = "ki_tutor_chat_history"
const _MATERIAL_KEY = "ki_tutor_material_name"

// PDF blob survives SPA navigation (module scope), lost on hard reload
let _pdfBlob: Blob | null = null

export function useChat(code: string, t: TFn, initialHistory: ChatMessage[] = []) {
  // If initialHistory starts with a user message, treat it as a pending auto-send
  const pendingMsg = initialHistory.length === 1 && initialHistory[0].role === "user"
    ? initialHistory[0].content : null
  const hasRedirect = initialHistory.length > 0

  const [history, setHistory] = useState<ChatMessage[]>(() => {
    if (hasRedirect) return pendingMsg ? [] : initialHistory
    try {
      const raw = typeof window !== "undefined" ? sessionStorage.getItem(_HISTORY_KEY) : null
      return raw ? (JSON.parse(raw) as ChatMessage[]) : []
    } catch { return [] }
  })
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [materialName, setMaterialName] = useState<string | null>(() => {
    try {
      return typeof window !== "undefined" ? sessionStorage.getItem(_MATERIAL_KEY) : null
    } catch { return null }
  })
  // true = blob is available (can open PDF), false = no blob (e.g. after hard reload)
  const [hasPdf, setHasPdf] = useState<boolean>(() => _pdfBlob !== null)
  const [error, setError] = useState<string | null>(null)
  const [activeChatId, setActiveChatId] = useState<number | null>(null)
  const activeChatIdRef = useRef<number | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function persistToDb(msgs: ChatMessage[], currentCode: string) {
    const token = getToken()
    if (!token || !msgs.length) return
    try {
      const payload = msgs.map((m) => ({ role: m.role, content: m.content }))
      if (activeChatIdRef.current !== null) {
        await updateChatHistory(activeChatIdRef.current, payload, currentCode, token)
      } else {
        const item = await saveChatHistory(payload, currentCode, token)
        activeChatIdRef.current = item.id
        setActiveChatId(item.id)
      }
    } catch {
      // non-critical — history is still in sessionStorage
    }
  }

  function persistHistory(next: ChatMessage[]) {
    setHistory(next)
    try { sessionStorage.setItem(_HISTORY_KEY, JSON.stringify(next)) } catch { /* ignore */ }
  }

  function persistMaterialName(name: string | null, blob: Blob | null = null) {
    setMaterialName(name)
    setHasPdf(blob !== null)
    _pdfBlob = blob
    try {
      if (name) sessionStorage.setItem(_MATERIAL_KEY, name)
      else sessionStorage.removeItem(_MATERIAL_KEY)
    } catch { /* ignore */ }
  }

  function openPdf() {
    if (!_pdfBlob) return
    const url = URL.createObjectURL(_pdfBlob)
    window.open(url, "_blank", "noopener")
    // revoke after a short delay so the browser has time to load it
    setTimeout(() => URL.revokeObjectURL(url), 10_000)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history, loading, analyzing])

  function getToken(): string | undefined {
    return localStorage.getItem("ki_tutor_token") ?? undefined
  }

  // Auto-send pending topic explanation on mount
  useEffect(() => {
    if (!pendingMsg) return
    setLoading(true)
    const userMsg: ChatMessage = { role: "user", content: pendingMsg }
    persistHistory([userMsg])
    sendChatMessage({ code, message: pendingMsg, history: [] }, getToken())
      .then((data) => persistHistory(data.history))
      .catch(() => setError(t("tutor.backendError")))
      .finally(() => setLoading(false))
  }, [])

  async function send() {
    const msg = input.trim()
    if (!msg || loading || analyzing) return
    setInput("")
    setError(null)
    const optimistic: ChatMessage[] = [...history, { role: "user", content: msg }]
    persistHistory(optimistic)
    setLoading(true)
    try {
      const data = await sendChatMessage({ code, message: msg, history }, getToken())
      persistHistory(data.history)
      await persistToDb(data.history, code)
    } catch {
      setError(t("tutor.backendError"))
      persistHistory(history)
    } finally {
      setLoading(false)
    }
  }

  async function analyze() {
    if (loading || analyzing) return
    setError(null)
    const trigger: ChatMessage = { role: "user", content: `🔍 ${t("tutor.analyzeAction")}` }
    persistHistory([...history, trigger])
    setAnalyzing(true)
    try {
      const data = await analyzeCode({ code })
      const formatted = formatAnalysis(data)
      const next: ChatMessage[] = [...history, trigger, { role: "assistant", content: formatted }]
      persistHistory(next)
      await persistToDb(next, code)
    } catch {
      setError(t("tutor.analyzeError"))
      persistHistory(history)
    } finally {
      setAnalyzing(false)
    }
  }

  async function uploadPdf(file: File) {
    if (uploading) return
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError(t("tutor.uploadError"))
      return
    }
    setError(null)
    setUploading(true)
    persistMaterialName(file.name, file)
    try {
      const data = await uploadMaterial(file, getToken())
      const msg: ChatMessage = {
        role: "assistant",
        content: `📚 **${t("tutor.materialLoaded", { name: file.name })}**\n\n${t("tutor.materialChunks", { chunks: data.chunks })}`,
      }
      persistHistory([...history, msg])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : t("tutor.uploadError"))
      persistMaterialName(null)
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
    persistHistory([])
    setInput("")
    setError(null)
    persistMaterialName(null)
    activeChatIdRef.current = null
    setActiveChatId(null)
  }

  async function saveCurrentChat(currentCode: string): Promise<number | null> {
    if (!history.length) return null
    const token = getToken()
    if (!token) return null
    try {
      const item = await saveChatHistory(
        history.map((m) => ({ role: m.role, content: m.content })),
        currentCode,
        token,
      )
      return item.id
    } catch {
      return null
    }
  }

  function loadHistoryIntoChat(messages: ChatMessage[], currentCode?: string | null, chatId?: number | null) {
    persistHistory(messages)
    setInput("")
    setError(null)
    activeChatIdRef.current = chatId ?? null
    setActiveChatId(chatId ?? null)
    return currentCode ?? null
  }

  return {
    history, input, setInput,
    loading, analyzing, uploading, materialName, hasPdf, openPdf,
    error,
    activeChatId,
    send, analyze, reset,
    saveCurrentChat, loadHistoryIntoChat,
    openFilePicker, handleFileInput, fileInputRef,
    bottomRef,
  }
}
