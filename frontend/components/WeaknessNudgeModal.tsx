"use client"

import { useTheme } from "@/context/ThemeContext"

interface Props {
  skillLabel: string
  score: number
  nudgeText: string
  onPractice: () => void
  onDismiss: () => void
}

export default function WeaknessNudgeModal({ skillLabel, score, nudgeText, onPractice, onDismiss }: Props) {
  const { dark } = useTheme()

  const overlay = "fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
  const card = dark
    ? "bg-[#0d1929] border border-[#1e2f45] text-white"
    : "bg-white border border-gray-200 text-gray-900"

  const scoreColor = score < 40 ? "text-red-400" : "text-amber-400"

  return (
    <div className={overlay} onClick={onDismiss}>
      <div
        className={`${card} rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <p className={`text-xs font-semibold uppercase tracking-wider ${dark ? "text-gray-400" : "text-gray-500"}`}>
              Schwachstelle erkannt
            </p>
            <p className="text-base font-bold">{skillLabel}</p>
          </div>
          <span className={`ml-auto text-lg font-bold tabular-nums ${scoreColor}`}>
            {score}%
          </span>
        </div>

        {/* Nudge text */}
        <p className={`text-sm leading-relaxed ${dark ? "text-gray-300" : "text-gray-600"}`}>
          {nudgeText}
        </p>

        {/* Score bar */}
        <div className={`w-full h-2 rounded-full overflow-hidden ${dark ? "bg-[#1e2f45]" : "bg-gray-200"}`}>
          <div
            className={`h-full rounded-full transition-all duration-700 ${score < 40 ? "bg-red-500" : "bg-amber-500"}`}
            style={{ width: `${score}%` }}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-1">
          <button
            onClick={onPractice}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white transition-all"
          >
            Jetzt üben
          </button>
          <button
            onClick={onDismiss}
            className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              dark
                ? "bg-[#1e2f45] hover:bg-[#243a56] text-gray-300"
                : "bg-gray-100 hover:bg-gray-200 text-gray-600"
            }`}
          >
            Später
          </button>
        </div>
      </div>
    </div>
  )
}
