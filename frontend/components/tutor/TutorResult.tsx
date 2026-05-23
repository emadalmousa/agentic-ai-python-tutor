"use client"

import type { TutorResponse } from "@/types/tutor"
import MarkdownMessage from "./MarkdownMessage"

interface Props {
  result: TutorResponse
  dark: boolean
}

export default function TutorResult({ result, dark }: Props) {
  const text  = dark ? "text-gray-200" : "text-gray-800"
  const sub   = dark ? "text-gray-400" : "text-gray-500"
  const card  = dark ? "bg-[#0d1b2a] border-[#1e2f45]" : "bg-white border-gray-200"
  const divider = dark ? "border-[#1e2f45]" : "border-gray-100"

  const errorColor = result.error_found
    ? dark ? "bg-red-500/10 border-red-500/30 text-red-400" : "bg-red-50 border-red-200 text-red-600"
    : dark ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : "bg-emerald-50 border-emerald-200 text-emerald-600"

  const errorIcon = result.error_found ? "🔴" : "🟢"
  const errorLabel = result.error_found ? result.error_type : "Kein Fehler"

  return (
    <div className="flex flex-col gap-4">

      {/* ── Status-Banner ── */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${errorColor}`}>
        <span className="text-lg">{errorIcon}</span>
        <div>
          <div className="font-bold text-sm">{errorLabel}</div>
          <div className="text-xs opacity-75">Code-Analyse abgeschlossen</div>
        </div>
      </div>

      {/* ── Erklärung ── */}
      <div className={`rounded-xl border ${card} overflow-hidden`}>
        <div className={`flex items-center gap-2 px-4 py-3 border-b ${divider}`}>
          <span>📖</span>
          <span className={`text-xs font-bold uppercase tracking-widest ${dark ? "text-indigo-400" : "text-indigo-500"}`}>
            Code-Erklärung
          </span>
        </div>
        <div className="px-4 py-4">
          <MarkdownMessage content={result.explanation} dark={dark} />
        </div>
      </div>

      {/* ── Fehler / Hinweis ── */}
      <div className={`rounded-xl border ${card} overflow-hidden`}>
        <div className={`flex items-center gap-2 px-4 py-3 border-b ${divider}`}>
          <span>{result.error_found ? "🐛" : "💡"}</span>
          <span className={`text-xs font-bold uppercase tracking-widest ${dark ? "text-amber-400" : "text-amber-600"}`}>
            {result.error_found ? "Fehler & Lösung" : "Hinweis"}
          </span>
        </div>
        <div className="px-4 py-4">
          <MarkdownMessage content={result.suggestion} dark={dark} />
        </div>
      </div>

      {/* ── Übung ── */}
      {result.next_exercise && (
        <div className={`rounded-xl border overflow-hidden ${dark ? "bg-indigo-950/40 border-indigo-500/20" : "bg-indigo-50 border-indigo-200"}`}>
          <div className={`flex items-center gap-2 px-4 py-3 border-b ${dark ? "border-indigo-500/20" : "border-indigo-200"}`}>
            <span>🎯</span>
            <span className={`text-xs font-bold uppercase tracking-widest ${dark ? "text-indigo-400" : "text-indigo-600"}`}>
              Deine nächste Übung
            </span>
          </div>
          <div className="px-4 py-4">
            <MarkdownMessage content={result.next_exercise!} dark={dark} />
          </div>
          <div className={`px-4 py-3 border-t ${dark ? "border-indigo-500/20" : "border-indigo-200"}`}>
            <p className={`text-xs ${sub}`}>
              💬 Hast du Fragen zur Übung? Frag den Tutor im Chat!
            </p>
          </div>
        </div>
      )}

    </div>
  )
}
