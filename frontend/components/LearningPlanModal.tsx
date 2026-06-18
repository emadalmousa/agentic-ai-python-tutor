"use client"

import { useTheme } from "@/context/ThemeContext"
import type { LearningPlanResponse, LearningPlanSkill } from "@/types/tutor"

interface Props {
  plan: LearningPlanResponse
  onClose: () => void
  onStartSkill: (skillKey: string) => void
}

function scoreColor(score: number) {
  if (score < 40) return "text-red-400"
  if (score < 80) return "text-amber-400"
  return "text-emerald-400"
}

function scoreDot(score: number) {
  if (score < 40) return "bg-red-500"
  if (score < 80) return "bg-amber-500"
  return "bg-emerald-500"
}

function SkillRow({ skill, dark, onStart }: { skill: LearningPlanSkill; dark: boolean; onStart: () => void }) {
  return (
    <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl ${dark ? "bg-[#0a1628]" : "bg-gray-50"}`}>
      <span className={`w-2 h-2 rounded-full shrink-0 ${scoreDot(skill.score)}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${dark ? "text-white" : "text-gray-900"}`}>
          {skill.skill_label}
        </p>
        <p className={`text-xs ${dark ? "text-gray-500" : "text-gray-400"}`}>
          aktuell {skill.score}% · ~{skill.hours}h
        </p>
      </div>
      <button
        onClick={onStart}
        className="shrink-0 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all active:scale-95"
      >
        Starten →
      </button>
    </div>
  )
}

export default function LearningPlanModal({ plan, onClose, onStartSkill }: Props) {
  const { dark } = useTheme()

  const overlay = "fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
  const card = dark
    ? "bg-[#0d1929] border border-[#1e2f45] text-white"
    : "bg-white border border-gray-200 text-gray-900"
  const sub = dark ? "text-gray-400" : "text-gray-500"
  const weekBg = dark ? "bg-[#060e1c] border-[#1e2f45]" : "bg-gray-50 border-gray-200"

  return (
    <div className={overlay} onClick={onClose}>
      <div
        className={`${card} rounded-2xl shadow-2xl w-full max-w-lg flex flex-col`}
        style={{ maxHeight: "85vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-center justify-between px-5 py-4 border-b ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
          <div className="flex items-center gap-2.5">
            <span className="text-xl">📅</span>
            <div>
              <p className="text-base font-bold">Dein persönlicher Lernplan</p>
              <p className={`text-xs ${sub}`}>{plan.weeks.length} Woche{plan.weeks.length !== 1 ? "n" : ""} geplant</p>
            </div>
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

        {/* Tip */}
        {plan.tip && (
          <div className={`mx-5 mt-4 px-4 py-3 rounded-xl flex items-start gap-2.5 ${dark ? "bg-blue-500/10 border border-blue-500/20" : "bg-blue-50 border border-blue-100"}`}>
            <span className="text-base shrink-0">💡</span>
            <p className={`text-sm leading-relaxed ${dark ? "text-blue-200" : "text-blue-700"}`}>{plan.tip}</p>
          </div>
        )}

        {/* Weeks */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {plan.weeks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2">
              <span className="text-4xl">🎉</span>
              <p className={`text-sm font-medium ${dark ? "text-white" : "text-gray-900"}`}>Alle Skills abgeschlossen!</p>
              <p className={`text-xs ${sub}`}>Du hast bei allen Skills einen Score ≥ 80%.</p>
            </div>
          ) : (
            plan.weeks.map((week) => (
              <div key={week.week} className={`rounded-xl border p-4 space-y-2.5 ${weekBg}`}>
                <p className={`text-xs font-bold uppercase tracking-wider ${sub}`}>
                  Woche {week.week}
                </p>
                {week.skills.map((skill) => (
                  <SkillRow
                    key={skill.skill_key}
                    skill={skill}
                    dark={dark}
                    onStart={() => onStartSkill(skill.skill_key)}
                  />
                ))}
              </div>
            ))
          )}
        </div>

        {/* Legend */}
        <div className={`px-5 py-3 border-t flex items-center gap-4 ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
          {[
            { dot: "bg-red-500",     label: "Score < 40%" },
            { dot: "bg-amber-500",   label: "Score 40–79%" },
          ].map(({ dot, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${dot}`} />
              <span className={`text-xs ${sub}`}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
