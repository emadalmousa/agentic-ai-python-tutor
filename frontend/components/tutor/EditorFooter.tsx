"use client"

import type { RunResponse } from "@/types/tutor"

interface Props {
  dark: boolean
  code: string
  running: boolean
  analyzing: boolean
  output: RunResponse | null
  onRun: () => void
  onAnalyze: () => void
}

export default function EditorFooter({ dark, code, running, analyzing, output, onRun, onAnalyze }: Props) {
  const border = dark ? "border-[#1e2f45]" : "border-gray-200"

  return (
    <div className={`flex-shrink-0 border-t ${border}`}>

      {/* Output-Panel */}
      {(output || running) && (
        <div className={`border-b ${border}`}>
          <div className={`flex items-center justify-between px-4 py-1.5 ${dark ? "bg-[#080f1e]" : "bg-gray-50"}`}>
            <div className="flex items-center gap-2">
              {output && (
                <span className={`w-2 h-2 rounded-full ${output.exit_code === 0 ? "bg-emerald-400" : "bg-red-400"}`} />
              )}
              <span className={`text-xs font-mono font-semibold ${dark ? "text-gray-400" : "text-gray-500"}`}>
                Output
              </span>
            </div>
            {output && (
              <span className={`text-xs font-mono ${output.exit_code === 0 ? "text-emerald-400" : "text-red-400"}`}>
                exit {output.exit_code}
              </span>
            )}
          </div>
          <pre className={`px-4 py-3 text-xs font-mono leading-relaxed overflow-x-auto max-h-36 ${
            dark ? "bg-[#060e1c] text-gray-300" : "bg-gray-900 text-gray-100"
          }`}>
            {running && <span className="text-gray-500">Ausführen…</span>}
            {output?.stdout && <span>{output.stdout}</span>}
            {output?.stderr && <span className="text-red-400">{output.stderr}</span>}
            {output && !output.stdout && !output.stderr && (
              <span className="text-gray-500">(kein Output)</span>
            )}
          </pre>
        </div>
      )}

      {/* Action-Bar */}
      <div className={`px-4 py-3 flex gap-2 ${dark ? "bg-[#080f1e]" : "bg-white"}`}>
        <button
          onClick={onRun}
          disabled={running || !code.trim()}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
            dark
              ? "bg-emerald-700 hover:bg-emerald-600 text-white"
              : "bg-emerald-600 hover:bg-emerald-500 text-white"
          }`}
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
          {running ? "Läuft…" : "Ausführen"}
        </button>

        <button
          onClick={onAnalyze}
          disabled={analyzing || !code.trim()}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
            dark
              ? "bg-indigo-600 hover:bg-indigo-500 text-white"
              : "bg-indigo-600 hover:bg-indigo-500 text-white"
          }`}
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
          {analyzing ? "Analysiere…" : "Code analysieren"}
        </button>
      </div>

    </div>
  )
}
