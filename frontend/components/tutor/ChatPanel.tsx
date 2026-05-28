"use client"

import { useRef, useEffect, KeyboardEvent } from "react"
import type { ChatMessage } from "@/types/tutor"
import MarkdownMessage from "./MarkdownMessage"

interface Props {
  history: ChatMessage[]
  input: string
  loading: boolean
  analyzing?: boolean
  error: string | null
  bottomRef: React.RefObject<HTMLDivElement | null>
  onInput: (v: string) => void
  onSend: () => void
  onReset: () => void
  onInsertCode?: (code: string) => void
  dark: boolean
}

export default function ChatPanel({
  history, input, loading, analyzing,
  error, bottomRef,
  onInput, onSend, onReset, onInsertCode, dark,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = Math.min(el.scrollHeight, 120) + "px"
  }, [input])

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const busy    = loading || analyzing
  const bg      = dark ? "bg-[#0a1628]"     : "bg-white"
  const border  = dark ? "border-[#1e2f45]" : "border-gray-200"
  const msgBg   = dark ? "bg-[#111e30]"     : "bg-gray-50"
  const userBg  = dark ? "bg-indigo-600"    : "bg-indigo-500"
  const inputBg = dark ? "bg-[#0d1b2a] border-[#2d3f55]" : "bg-white border-gray-200"
  const textCol = dark ? "text-gray-200"    : "text-gray-800"
  const subCol  = dark ? "text-gray-500"    : "text-gray-400"

  return (
    <div className={`flex flex-col h-full ${bg} border-l ${border}`}>

      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-3 border-b ${border}`}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-indigo-500" />
          <span className={`text-sm font-semibold ${textCol}`}>Python Tutor</span>
        </div>
        {history.length > 0 && (
          <button
            onClick={onReset}
            className={`text-xs ${subCol} hover:text-red-400 transition-colors`}
          >
            Neues Gespräch
          </button>
        )}
      </div>

      {/* Nachrichtenverlauf */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
        {history.length === 0 && !busy && (
          <div className={`text-center mt-12 ${subCol} text-sm`}>
            <div className="text-3xl mb-3">🤖</div>
            <p className="font-medium mb-1">Hallo! Ich bin dein Python-Tutor.</p>
            <p className="text-xs">Stell eine Frage oder analysiere deinen Code.</p>
          </div>
        )}

        {history.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-6 h-6 rounded-full bg-indigo-700 flex items-center justify-center text-xs mr-2 mt-0.5 flex-shrink-0">
                🤖
              </div>
            )}
            <div
              className={`max-w-[85%] px-4 py-2.5 rounded-2xl ${
                msg.role === "user"
                  ? `${userBg} text-white rounded-br-sm`
                  : `${msgBg} ${textCol} rounded-bl-sm`
              }`}
            >
              <MarkdownMessage
                content={msg.content}
                dark={dark}
                isUser={msg.role === "user"}
                onInsertCode={msg.role === "assistant" ? onInsertCode : undefined}
              />
            </div>
          </div>
        ))}

        {/* Typing-Indikator */}
        {busy && (
          <div className="flex justify-start">
            <div className="w-6 h-6 rounded-full bg-indigo-700 flex items-center justify-center text-xs mr-2 mt-0.5">
              🤖
            </div>
            <div className={`${msgBg} px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2`}>
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:"0ms"}} />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:"150ms"}} />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:"300ms"}} />
              </div>
              {analyzing && <span className={`text-xs ${subCol}`}>Analysiere Code…</span>}
            </div>
          </div>
        )}

        {error && (
          <div className="text-xs text-red-400 text-center py-2">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Eingabe */}
      <div className={`px-4 py-3 border-t ${border}`}>
        <div className={`flex gap-2 items-end rounded-2xl border ${inputBg} px-3 py-2`}>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => onInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Frage stellen… (Enter = senden)"
            rows={1}
            className={`flex-1 bg-transparent text-sm resize-none focus:outline-none ${dark ? "text-gray-200 placeholder-gray-500" : "text-gray-800 placeholder-gray-400"}`}
            style={{ maxHeight: 120 }}
            disabled={busy}
          />

          {/* Senden */}
          <button
            onClick={onSend}
            disabled={!input.trim() || busy}
            className="w-7 h-7 rounded-xl bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all flex-shrink-0 mb-0.5"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  )
}
