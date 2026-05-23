"use client"

import { useState } from "react"
import Header from "@/components/tutor/Header"
import CodeEditor from "@/components/tutor/CodeEditor"
import EditorFooter from "@/components/tutor/EditorFooter"
import TutorResult from "@/components/tutor/TutorResult"
import ChatPanel from "@/components/tutor/ChatPanel"
import { useTutorAnalysis } from "@/hooks/useTutorAnalysis"
import { useChat } from "@/hooks/useChat"
import { useCodeRunner } from "@/hooks/useCodeRunner"

export default function Home() {
  const [dark, setDark] = useState(true)
  const [activeTab, setActiveTab] = useState<"analyze" | "chat">("chat")

  const { code, setCode, result, loading: analyzing, error: analyzeError, analyze } = useTutorAnalysis()
  const { history, input, setInput, loading: chatLoading, error: chatError, send, reset, bottomRef } = useChat(code)
  const { output, loading: running, run } = useCodeRunner()

  const bg         = dark ? "bg-[#060e1c] text-white"        : "bg-gray-100 text-gray-900"
  const border     = dark ? "border-[#1e2f45]"               : "border-gray-200"
  const tabBase    = "px-4 py-2 text-xs font-semibold rounded-lg transition-all"
  const tabActive  = dark ? "bg-[#1e2f45] text-white"        : "bg-indigo-100 text-indigo-700"
  const tabInactive = dark ? "text-gray-500 hover:text-gray-300" : "text-gray-400 hover:text-gray-600"
  const labelCls   = dark ? "block text-xs font-medium text-gray-400 mb-1.5" : "block text-xs font-medium text-gray-500 mb-1.5"

  return (
    <div className={`${bg} h-screen flex flex-col overflow-hidden`}>

      <Header dark={dark} onToggleDark={() => setDark(!dark)} />

      {/* ── Split Layout ── */}
      <div className="flex flex-1 min-h-0">

        {/* ════ LINKE SEITE: Code-Editor ════ */}
        <div className={`w-[480px] flex-shrink-0 flex flex-col border-r ${border}`}>

          {/* Editor scrollt */}
          <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
            <label className={labelCls}>Python-Code</label>
            <CodeEditor code={code} onChange={setCode} dark={dark} />
          </div>

          {/* Footer bleibt immer sichtbar */}
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

        {/* ════ RECHTE SEITE: Tabs (Chat / Analyse) ════ */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Tab-Leiste */}
          <div className={`flex items-center gap-1 px-4 py-2 border-b ${border} ${dark ? "bg-[#080f1e]" : "bg-gray-50"} flex-shrink-0`}>
            <button
              onClick={() => setActiveTab("chat")}
              className={`${tabBase} ${activeTab === "chat" ? tabActive : tabInactive}`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveTab("analyze")}
              className={`${tabBase} ${activeTab === "analyze" ? tabActive : tabInactive}`}
            >
              🔍 Analyse
            </button>
          </div>

          {/* Tab-Inhalt */}
          <div className="flex-1 min-h-0">

            {activeTab === "chat" && (
              <ChatPanel
                history={history}
                input={input}
                loading={chatLoading}
                error={chatError}
                bottomRef={bottomRef}
                onInput={setInput}
                onSend={send}
                onReset={reset}
                dark={dark}
              />
            )}

            {activeTab === "analyze" && (
              <div className="h-full overflow-y-auto px-4 py-4">
                {analyzeError && (
                  <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                    {analyzeError}
                  </div>
                )}
                {result ? (
                  <TutorResult result={result} dark={dark} />
                ) : (
                  <div className={`text-center mt-16 text-sm ${dark ? "text-gray-600" : "text-gray-400"}`}>
                    <div className="text-3xl mb-3">🔍</div>
                    <p>Klicke auf <strong>Analysieren</strong> um eine vollständige Code-Analyse zu starten.</p>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </div>

    </div>
  )
}
