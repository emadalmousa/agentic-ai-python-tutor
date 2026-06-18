"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import CodeModal from "@/components/tutor/CodeModal"
import ChatPanel from "@/components/tutor/ChatPanel"
import ChatSidebar from "@/components/tutor/ChatSidebar"
import { useChat } from "@/hooks/useChat"
import { useCodeRunner } from "@/hooks/useCodeRunner"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useLang } from "@/context/LangContext"
import { listChatHistory, loadChat } from "@/lib/api"
import type { ChatHistoryItem } from "@/types/tutor"

const LEVEL_COMPLEXITY: Record<string, string> = {
  beginner:     "Erkläre alles sehr einfach für absolute Anfänger. Verwende kurze, klare Sätze. Zeige einfache Beispiele mit print() und einfachen Werten.",
  intermediate: "Erkläre auf mittlerem Niveau. Zeige praxisnahe Beispiele mit realistischen Anwendungsfällen.",
  advanced:     "Erkläre tiefgehend mit komplexen Beispielen, Best Practices und typischen Fehlerquellen.",
}

const DEFAULT_CODE = "# Schreibe hier deinen Python-Code..."

function readExerciseRedirect(): { code: string; history: import("@/types/tutor").ChatMessage[] } {
  try {
    const topicRaw = localStorage.getItem("ki_tutor_explain_topic")
    if (topicRaw) {
      const { skill_label, level } = JSON.parse(topicRaw) as { skill_key: string; skill_label: string; level: string }
      localStorage.removeItem("ki_tutor_explain_topic")
      const complexity = LEVEL_COMPLEXITY[level] ?? LEVEL_COMPLEXITY.beginner
      const prompt = `Erkläre mir das Thema **${skill_label}** in Python vollständig.\n\n${complexity}\n\nStruktur deiner Erklärung:\n1. Was ist ${skill_label}? (kurze Definition)\n2. Warum braucht man das?\n3. Syntax / Grundstruktur\n4. Mindestens 3 Beispiele mit steigendem Schwierigkeitsgrad\n5. Häufige Fehler und wie man sie vermeidet\n6. Kurze Zusammenfassung`
      return { code: DEFAULT_CODE, history: [{ role: "user", content: prompt }] }
    }
  } catch {
    localStorage.removeItem("ki_tutor_explain_topic")
  }
  try {
    const raw = localStorage.getItem("ki_tutor_exercise_redirect")
    if (!raw) return { code: DEFAULT_CODE, history: [] }
    const { code, analysis, exercise_title } = JSON.parse(raw) as {
      code: string; analysis: string; exercise_title: string
    }
    localStorage.removeItem("ki_tutor_exercise_redirect")
    return {
      code,
      history: [{ role: "assistant", content: `**Aufgabe: ${exercise_title}**\n\n${analysis}` }],
    }
  } catch {
    localStorage.removeItem("ki_tutor_exercise_redirect")
    return { code: DEFAULT_CODE, history: [] }
  }
}

export default function TutorView() {
  const { dark } = useTheme()
  const { t } = useLang()
  const { isAuthenticated } = useAuth()
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""
  const router = useRouter()

  const [{ code: initialCode, history: initialHistory }] = useState(readExerciseRedirect)
  const [code, setCode] = useState(initialCode)
  const [showCode, setShowCode] = useState(false)
  const [activeChatId, setActiveChatId] = useState<number | null>(null)

  // Sidebar state
  const [sidebarItems, setSidebarItems] = useState<ChatHistoryItem[]>([])
  const [sidebarLoading, setSidebarLoading] = useState(false)

  const {
    history, input, setInput,
    loading, analyzing, uploading, materialName, hasPdf, openPdf,
    error,
    send, analyze, reset,
    saveCurrentChat, loadHistoryIntoChat,
    openFilePicker, handleFileInput, fileInputRef,
    bottomRef,
  } = useChat(code, t, initialHistory)

  const { output, loading: running, run } = useCodeRunner(t)

  // Load sidebar on mount
  useEffect(() => {
    if (!token) return
    setSidebarLoading(true)
    listChatHistory(token)
      .then(setSidebarItems)
      .catch(() => {/* sidebar is non-critical */})
      .finally(() => setSidebarLoading(false))
  }, [token])

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  // Save current chat before switching + refresh sidebar
  async function switchToChat(item: ChatHistoryItem) {
    if (history.length > 0 && activeChatId === null) {
      await saveCurrentChat(code)
      refreshSidebar()
    }
    try {
      const data = await loadChat(item.id, token)
      const restoredCode = loadHistoryIntoChat(data.messages, data.code)
      if (restoredCode) setCode(restoredCode)
      setActiveChatId(item.id)
    } catch {/* ignore */}
  }

  function handleNewChat() {
    if (history.length > 0) {
      saveCurrentChat(code).then(refreshSidebar)
    }
    reset()
    setCode(DEFAULT_CODE)
    setActiveChatId(null)
  }

  function refreshSidebar() {
    if (!token) return
    listChatHistory(token).then(setSidebarItems).catch(() => {})
  }

  // Wrap analyze: save chat to DB after analyze completes (sidebar updates)
  const handleAnalyze = useCallback(async () => {
    await analyze()
    if (token) refreshSidebar()
  }, [analyze, token])

  const bg = dark ? "bg-[#060e1c] text-white" : "bg-gray-100 text-gray-900"

  return (
    <div className={`${bg} flex-1 flex overflow-hidden`}>

      {/* LEFT: Chat history sidebar */}
      <ChatSidebar
        items={sidebarItems}
        activeId={activeChatId}
        onNewChat={handleNewChat}
        onSelect={switchToChat}
        loading={sidebarLoading}
      />

      {/* CENTER: Chat only */}
      <div className="flex-1 min-w-0 overflow-hidden flex flex-col">
        <ChatPanel
          history={history}
          input={input}
          loading={loading}
          analyzing={analyzing}
          uploading={uploading}
          materialName={materialName}
          hasPdf={hasPdf}
          onOpenPdf={openPdf}
          error={error}
          bottomRef={bottomRef}
          fileInputRef={fileInputRef}
          onInput={setInput}
          onSend={send}
          onReset={handleNewChat}
          onOpenFilePicker={openFilePicker}
          onFileInput={handleFileInput}
          onInsertCode={setCode}
          onOpenCode={() => setShowCode(true)}
          dark={dark}
        />
      </div>

      {/* Code Editor Modal */}
      {showCode && (
        <CodeModal
          code={code}
          onChange={setCode}
          dark={dark}
          running={running}
          analyzing={analyzing}
          output={output}
          onRun={() => run(code)}
          onAnalyze={handleAnalyze}
          onClose={() => setShowCode(false)}
        />
      )}

    </div>
  )
}
