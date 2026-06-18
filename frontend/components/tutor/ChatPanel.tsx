"use client"

import { useRef, useEffect, useState, KeyboardEvent } from "react"
import type { ChatMessage } from "@/types/tutor"
import type { TranslationKey } from "@/i18n"
import { useLang } from "@/context/LangContext"
import MarkdownMessage from "./MarkdownMessage"

const THINKING_KEYS: { after: number; key: TranslationKey }[] = [
  { after: 0,  key: "tutor.thinking0" },
  { after: 2,  key: "tutor.thinking1" },
  { after: 5,  key: "tutor.thinking2" },
  { after: 9,  key: "tutor.thinking3" },
  { after: 14, key: "tutor.thinking4" },
  { after: 20, key: "tutor.thinking5" },
  { after: 28, key: "tutor.thinking6" },
]

function ThinkingIndicator({ dark, subCol }: { dark: boolean; subCol: string }) {
  const { t } = useLang()
  const [msgIndex, setMsgIndex] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    setMsgIndex(0)
    setElapsed(0)
    const interval = setInterval(() => {
      setElapsed((prev) => {
        const next = prev + 1
        const nextIdx = THINKING_KEYS.findLastIndex((m) => m.after <= next)
        setMsgIndex(nextIdx >= 0 ? nextIdx : 0)
        return next
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const msg = THINKING_KEYS[msgIndex]

  return (
    <div className={`px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-3 ${dark ? "bg-[#111e30]" : "bg-gray-50"}`}>
      <div className="flex gap-1 items-center shrink-0">
        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span className={`text-xs transition-all duration-500 ${subCol}`}>{t(msg.key)}</span>
    </div>
  )
}

interface Props {
  history: ChatMessage[]
  input: string
  loading: boolean
  analyzing?: boolean
  uploading?: boolean
  materialName?: string | null
  hasPdf?: boolean
  onOpenPdf?: () => void
  error: string | null
  bottomRef: React.RefObject<HTMLDivElement | null>
  fileInputRef: React.RefObject<HTMLInputElement | null>
  onInput: (v: string) => void
  onSend: () => void
  onReset: () => void
  onOpenFilePicker: () => void
  onFileInput: (e: React.ChangeEvent<HTMLInputElement>) => void
  onInsertCode?: (code: string) => void
  onOpenCode?: () => void
  dark: boolean
}

export default function ChatPanel({
  history, input, loading, analyzing, uploading, materialName, hasPdf, onOpenPdf,
  error, bottomRef, fileInputRef,
  onInput, onSend, onReset, onOpenFilePicker, onFileInput, onInsertCode, onOpenCode, dark,
}: Props) {
  const { t } = useLang()
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

  const busy    = loading || analyzing || uploading
  const bg      = dark ? "bg-[#0a1628]"     : "bg-white"
  const border  = dark ? "border-[#1e2f45]" : "border-gray-200"
  const msgBg   = dark ? "bg-[#111e30]"     : "bg-gray-50"
  const userBg  = dark ? "bg-indigo-600"    : "bg-indigo-500"
  const inputBg = dark ? "bg-[#0d1b2a] border-[#2d3f55]" : "bg-white border-gray-200"
  const textCol = dark ? "text-gray-200"    : "text-gray-800"
  const subCol  = dark ? "text-gray-500"    : "text-gray-400"

  return (
    <div className={`flex flex-col min-h-full ${bg} border-l ${border}`}>

      {/* Header */}
      <div className={`sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b ${border} ${bg}`}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-indigo-500" />
          <span className={`text-sm font-semibold ${textCol}`}>Python Tutor</span>
          {materialName && (
            <button
              onClick={hasPdf ? onOpenPdf : undefined}
              title={hasPdf ? "PDF öffnen" : undefined}
              className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border transition-opacity ${hasPdf ? "cursor-pointer hover:opacity-75" : "cursor-default"} ${dark ? "bg-amber-500/15 text-amber-400 border-amber-500/30" : "bg-amber-50 text-amber-700 border-amber-200"}`}
            >
              📚 {materialName}
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Code-Editor öffnen */}
          {onOpenCode && (
            <button
              onClick={onOpenCode}
              title="Code-Editor öffnen"
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                dark
                  ? "border-[#2d3f55] text-gray-400 hover:text-emerald-400 hover:border-emerald-500/40 hover:bg-emerald-500/10"
                  : "border-gray-200 text-gray-500 hover:text-emerald-600 hover:border-emerald-300 hover:bg-emerald-50"
              }`}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              Python
            </button>
          )}
        </div>
      </div>

      {/* Message history */}
      <div className="flex-1 px-4 py-4 flex flex-col gap-3">
        {history.length === 0 && !busy && (
          <div className={`text-center mt-12 ${subCol} text-sm`}>
            <div className="text-3xl mb-3">🤖</div>
            <p className="font-medium mb-1">{t("tutor.greeting")}</p>
            <p className="text-xs">{t("tutor.greetingSub")}</p>
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

        {/* Typing indicator */}
        {busy && (
          <div className="flex justify-start">
            <div className="w-6 h-6 rounded-full bg-indigo-700 flex items-center justify-center text-xs mr-2 mt-0.5 shrink-0">
              🤖
            </div>
            {analyzing ? (
              <div className={`${msgBg} px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2`}>
                <div className="flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className={`text-xs ${subCol}`}>{t("tutor.analyzing")}</span>
              </div>
            ) : uploading ? (
              <div className={`${msgBg} px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2`}>
                <div className="flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className={`text-xs ${subCol}`}>{t("tutor.uploading")}</span>
              </div>
            ) : (
              <ThinkingIndicator dark={dark} subCol={subCol} />
            )}
          </div>
        )}

        {error && (
          <div className="text-xs text-red-400 text-center py-2">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className={`sticky bottom-0 px-4 py-3 border-t ${border} ${bg}`}>
        <div className={`flex gap-2 items-end rounded-2xl border ${inputBg} px-3 py-2`}>

          {/* Paperclip: PDF upload */}
          <button
            onClick={onOpenFilePicker}
            disabled={busy}
            title={t("tutor.uploadTitle")}
            className={`w-7 h-7 flex items-center justify-center rounded-lg transition-all flex-shrink-0 mb-0.5 disabled:opacity-30 disabled:cursor-not-allowed ${
              dark
                ? "text-gray-500 hover:text-amber-400 hover:bg-amber-500/10"
                : "text-gray-400 hover:text-amber-600 hover:bg-amber-50"
            }`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => onInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={t("tutor.inputPlaceholder")}
            rows={1}
            className={`flex-1 bg-transparent text-sm resize-none focus:outline-none ${dark ? "text-gray-200 placeholder-gray-500" : "text-gray-800 placeholder-gray-400"}`}
            style={{ maxHeight: 120 }}
            disabled={busy}
          />

          {/* Send */}
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

        <p className={`text-center text-xs mt-1.5 ${subCol}`}>
          {t("tutor.uploadHint")}
        </p>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={onFileInput}
      />
    </div>
  )
}
