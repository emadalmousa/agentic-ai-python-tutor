"use client"

import type { TutorResponse } from "@/app/types/tutor"
import StatusBadge from "./StatusBadge"

interface Props {
  result: TutorResponse
  dark: boolean
}

export default function TutorResult({ result, dark }: Props) {
  const card = dark
    ? "bg-[#1e2a3a] border border-[#2d3f55] rounded-xl p-5"
    : "bg-white border border-gray-200 rounded-xl p-5 shadow-sm"

  const label = dark ? "text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-1" : "text-xs font-semibold uppercase tracking-widest text-indigo-500 mb-1"
  const text = dark ? "text-gray-200 text-sm leading-relaxed" : "text-gray-700 text-sm leading-relaxed"

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <StatusBadge errorFound={result.error_found} />
      </div>

      <div className={card}>
        <p className={label}>Erklärung</p>
        <p className={text}>{result.explanation}</p>
      </div>

      <div className={card}>
        <p className={label}>Hinweis</p>
        <p className={text}>{result.suggestion}</p>
      </div>

      {result.next_exercise && (
        <div className={dark ? "bg-indigo-900/30 border border-indigo-500/30 rounded-xl p-5" : "bg-indigo-50 border border-indigo-200 rounded-xl p-5"}>
          <p className={label}>Nächste Übung</p>
          <p className={text}>{result.next_exercise}</p>
        </div>
      )}
    </div>
  )
}
