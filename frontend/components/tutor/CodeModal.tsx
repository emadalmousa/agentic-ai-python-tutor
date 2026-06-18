"use client"

import { useEffect, useRef, useCallback } from "react"
import CodeEditor from "./CodeEditor"
import type { RunResponse } from "@/types/tutor"
import { useLang } from "@/context/LangContext"

interface Props {
  code: string
  onChange: (code: string) => void
  dark: boolean
  running: boolean
  analyzing: boolean
  output: RunResponse | null
  onRun: () => void
  onAnalyze: () => void
  onClose: () => void
}

export default function CodeModal({
  code, onChange, dark, running, analyzing, output, onRun, onAnalyze, onClose,
}: Props) {
  const { t } = useLang()
  const busy = running || analyzing
  const overlayRef = useRef<HTMLDivElement>(null)

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose()
  }, [onClose])

  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const bg     = dark ? "bg-[#0a1628]"     : "bg-white"
  const subCol = dark ? "text-gray-500"    : "text-gray-400"

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <div className={`${bg} rounded-2xl border ${border} shadow-2xl w-full max-w-2xl flex flex-col`}
        style={{ maxHeight: "85vh" }}>

        {/* Header */}
        <div className={`flex items-center justify-between px-5 py-3.5 border-b ${border}`}>
          <div className="flex items-center gap-2">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              className={dark ? "text-emerald-400" : "text-emerald-600"}>
              <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
            </svg>
            <span className={`text-sm font-semibold ${dark ? "text-white" : "text-gray-900"}`}>
              {t("tutor.pythonCode")}
            </span>
          </div>
          <button
            onClick={onClose}
            className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors ${
              dark ? "text-gray-500 hover:text-white hover:bg-[#1e2f45]" : "text-gray-400 hover:text-gray-700 hover:bg-gray-100"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Editor */}
        <div className="flex-1 overflow-y-auto p-4 min-h-0">
          <CodeEditor code={code} onChange={onChange} dark={dark} />
        </div>

        {/* Output panel */}
        {(output || running) && (
          <div className={`border-t ${border}`}>
            <div className={`flex items-center justify-between px-4 py-1.5 ${dark ? "bg-[#080f1e]" : "bg-gray-50"}`}>
              <div className="flex items-center gap-2">
                {output && (
                  <span className={`w-2 h-2 rounded-full ${output.exit_code === 0 ? "bg-emerald-400" : "bg-red-400"}`} />
                )}
                <span className={`text-xs font-mono font-semibold ${subCol}`}>{t("tutor.output")}</span>
              </div>
              {output && (
                <span className={`text-xs font-mono ${output.exit_code === 0 ? "text-emerald-400" : "text-red-400"}`}>
                  exit {output.exit_code}
                </span>
              )}
            </div>
            <pre className={`px-4 py-3 text-xs font-mono leading-relaxed overflow-y-auto max-h-40 ${
              dark ? "bg-[#060e1c] text-gray-300" : "bg-gray-900 text-gray-100"
            }`}>
              {running && <span className="text-gray-500">{t("tutor.running")}</span>}
              {output?.stdout && <span>{output.stdout}</span>}
              {output?.stderr && <span className="text-red-400">{output.stderr}</span>}
              {output && !output.stdout && !output.stderr && (
                <span className="text-gray-500">{t("tutor.noOutput")}</span>
              )}
            </pre>
          </div>
        )}

        {/* Action bar */}
        <div className={`flex gap-2 px-4 py-3 border-t ${border} ${dark ? "bg-[#080f1e]" : "bg-gray-50"}`}>
          <button
            onClick={onRun}
            disabled={busy || !code.trim()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            {running ? (
              <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            )}
            {running ? t("tutor.runRunning") : t("tutor.run")}
          </button>

          <button
            onClick={onAnalyze}
            disabled={busy || !code.trim()}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            {analyzing ? (
              <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            )}
            {analyzing ? t("tutor.analyzeRunning") : t("tutor.analyze")}
          </button>

          <button
            onClick={onClose}
            className={`px-4 py-2.5 rounded-xl font-semibold text-sm transition-all ${
              dark ? "bg-[#1e2f45] hover:bg-[#243a56] text-gray-300" : "bg-gray-100 hover:bg-gray-200 text-gray-600"
            }`}
          >
            Schließen
          </button>
        </div>

      </div>
    </div>
  )
}
