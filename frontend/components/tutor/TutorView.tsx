"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import CodeEditor from "@/components/tutor/CodeEditor"
import EditorFooter from "@/components/tutor/EditorFooter"
import ChatPanel from "@/components/tutor/ChatPanel"
import { useChat } from "@/hooks/useChat"
import { useCodeRunner } from "@/hooks/useCodeRunner"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"

function readExerciseRedirect(): { code: string; history: import("@/types/tutor").ChatMessage[] } {
  const DEFAULT_CODE = "for i in range(5)\n    print(i)"
  try {
    const raw = localStorage.getItem("ki_tutor_exercise_redirect")
    if (!raw) return { code: DEFAULT_CODE, history: [] }
    const { code, analysis, exercise_title } = JSON.parse(raw) as {
      code: string
      analysis: string
      exercise_title: string
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
  const [{ code: initialCode, history: initialHistory }] = useState(readExerciseRedirect)
  const [code, setCode] = useState(initialCode)
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const {
    history, input, setInput,
    loading, analyzing, uploading, materialName,
    error,
    send, analyze, reset,
    openFilePicker, handleFileInput, fileInputRef,
    bottomRef,
  } = useChat(code, initialHistory)
  const { output, loading: running, run } = useCodeRunner()

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  const bg = dark ? "bg-[#060e1c] text-white" : "bg-gray-100 text-gray-900"
  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const labelCls = dark
    ? "block text-xs font-medium text-gray-400 mb-1.5"
    : "block text-xs font-medium text-gray-500 mb-1.5"

  return (
    <div className={`${bg} flex-1 flex flex-col overflow-hidden`}>
      <div className="flex flex-1 min-h-0">

        <div className={`w-[480px] flex-shrink-0 flex flex-col border-r ${border}`}>
          <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
            <label className={labelCls}>Python-Code</label>
            <CodeEditor code={code} onChange={setCode} dark={dark} />
          </div>
          <EditorFooter
            dark={dark}
            code={code}
            running={running}
            analyzing={analyzing}
            output={output}
            onRun={() => run(code)}
            onAnalyze={analyze}
          />
        </div>

        <div className="flex-1 min-w-0">
          <ChatPanel
            history={history}
            input={input}
            loading={loading}
            analyzing={analyzing}
            uploading={uploading}
            materialName={materialName}
            error={error}
            bottomRef={bottomRef}
            fileInputRef={fileInputRef}
            onInput={setInput}
            onSend={send}
            onReset={reset}
            onOpenFilePicker={openFilePicker}
            onFileInput={handleFileInput}
            onInsertCode={setCode}
            dark={dark}
          />
        </div>

      </div>
    </div>
  )
}
