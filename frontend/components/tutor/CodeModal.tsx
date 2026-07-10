"use client"

import CodeEditor from "./CodeEditor"
import CodeReviewPanel from "./CodeReviewPanel"
import type { RunResponse, CodeReviewResult } from "@/types/tutor"
import { useLang } from "@/context/LangContext"

interface Props {
  code: string
  onChange: (code: string) => void
  dark: boolean
  running: boolean
  analyzing: boolean
  reviewing: boolean
  output: RunResponse | null
  reviewResult: CodeReviewResult | null
  onRun: () => void
  onAnalyze: () => void
  onReview: () => void
  onClearReview: () => void
  onClose: () => void
  onReset: () => void
}

export default function CodeModal({
  code, onChange, dark, running, analyzing, reviewing, output, reviewResult,
  onRun, onAnalyze, onReview, onClearReview, onClose, onReset,
}: Props) {
  const { t } = useLang()
  const busy = running || analyzing || reviewing


  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const bg     = dark ? "bg-[#0a1628]"     : "bg-white"
  const subCol = dark ? "text-gray-500"    : "text-gray-400"

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <div className={`${bg} rounded-2xl border ${border} shadow-2xl w-full max-w-5xl flex flex-col`}
        style={{ height: "90vh" }}>

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

        {/* Code Review Panel */}
        {reviewing && (
          <div className={`border-t ${border} flex items-center justify-center gap-3 py-6 ${dark ? "bg-[#0a1628]" : "bg-white"}`}>
            <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
              style={{ color: dark ? "#818cf8" : "#6366f1" }}>
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            <span className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>Code wird analysiert…</span>
          </div>
        )}
        {!reviewing && reviewResult && (
          <CodeReviewPanel
            result={reviewResult}
            dark={dark}
            onClose={onClearReview}
          />
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
            onClick={onReview}
            disabled={busy || !code.trim()}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-violet-600 hover:bg-violet-500 text-white"
          >
            {reviewing ? (
              <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
            )}
            {reviewing ? "Prüfe..." : "Code Review"}
          </button>

          <button
            onClick={onReset}
            disabled={busy}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
              dark ? "bg-[#1e2f45] hover:bg-red-900/40 hover:text-red-400 text-gray-400" : "bg-gray-100 hover:bg-red-50 hover:text-red-500 text-gray-500"
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/>
            </svg>
            Zurücksetzen
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
