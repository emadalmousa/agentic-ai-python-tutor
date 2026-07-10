"use client"

import { useTheme } from "@/context/ThemeContext"
import type { LearningPlanResponse, LearningPlanSkill, LearningPlanTask, SkillProgress } from "@/types/tutor"

interface Props {
  plan: LearningPlanResponse
  progressSkills: SkillProgress[]
  savedAt?: number | null
  onClose: () => void
  onStartSkill: (skillKey: string) => void
  onRefresh: () => void
}

function scoreDot(score: number) {
  if (score < 40) return "bg-red-500"
  if (score < 80) return "bg-amber-500"
  return "bg-emerald-500"
}

const TASK_STYLES: Record<string, { icon: string; bg: string; bgLight: string; text: string; textLight: string }> = {
  review:    { icon: "📖", bg: "bg-indigo-500/10 border-indigo-500/20",   bgLight: "bg-indigo-50 border-indigo-100",   text: "text-indigo-300", textLight: "text-indigo-700" },
  practice:  { icon: "✏️",  bg: "bg-blue-500/10 border-blue-500/20",       bgLight: "bg-blue-50 border-blue-100",       text: "text-blue-300",   textLight: "text-blue-700"   },
  challenge: { icon: "🎯", bg: "bg-emerald-500/10 border-emerald-500/20", bgLight: "bg-emerald-50 border-emerald-100", text: "text-emerald-300", textLight: "text-emerald-700" },
}

function TaskPill({ task, dark }: { task: LearningPlanTask; dark: boolean }) {
  const s = TASK_STYLES[task.type] ?? TASK_STYLES.practice
  return (
    <div className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs ${dark ? `${s.bg} ${s.text}` : `${s.bgLight} ${s.textLight}`}`}>
      <span>{s.icon}</span>
      <span className="font-medium">{task.label}</span>
      <span className={`ml-auto pl-2 font-mono tabular-nums ${dark ? "text-gray-500" : "text-gray-400"}`}>~{task.hours}h</span>
    </div>
  )
}

function SkillRow({ skill, dark, locked, onStart }: { skill: LearningPlanSkill; dark: boolean; locked: boolean; onStart: () => void }) {
  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const cardBg = dark ? "bg-[#0a1628]" : "bg-gray-50"
  const sub = dark ? "text-gray-500" : "text-gray-400"

  return (
    <div className={`rounded-xl border ${border} overflow-hidden ${locked ? "opacity-60" : ""}`}>
      {/* Skill header row */}
      <div className={`flex items-center gap-3 px-3 py-2.5 ${cardBg}`}>
        {locked
          ? <span className="text-sm shrink-0">🔒</span>
          : <span className={`w-2 h-2 rounded-full shrink-0 ${scoreDot(skill.score)}`} />
        }
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold truncate ${dark ? "text-white" : "text-gray-900"}`}>
            {skill.skill_label}
          </p>
          <p className={`text-xs ${sub}`}>
            {locked
              ? "Vorherige Skills abschließen"
              : `${skill.score}% erreicht · ~${skill.hours}h gesamt`
            }
          </p>
        </div>
        <button
          onClick={locked ? undefined : onStart}
          disabled={locked}
          className={`shrink-0 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            locked
              ? `cursor-default ${dark ? "bg-[#1e2f45] text-gray-600" : "bg-gray-200 text-gray-400"}`
              : "bg-blue-600 hover:bg-blue-500 text-white active:scale-95"
          }`}
        >
          {locked ? "Gesperrt" : "Starten →"}
        </button>
      </div>

      {/* Task list */}
      {!locked && skill.tasks && skill.tasks.length > 0 && (
        <div className={`px-3 py-2.5 space-y-1.5 border-t ${border} ${dark ? "bg-[#060e1c]" : "bg-white"}`}>
          {skill.tasks.map((task, i) => (
            <TaskPill key={i} task={task} dark={dark} />
          ))}
        </div>
      )}
    </div>
  )
}

function formatSavedAt(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" }) +
    " " + d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })
}

export default function LearningPlanModal({ plan, progressSkills, savedAt, onClose, onStartSkill, onRefresh }: Props) {
  const { dark } = useTheme()

  const overlay = "fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
  const card = dark
    ? "bg-[#0d1929] border border-[#1e2f45] text-white"
    : "bg-white border border-gray-200 text-gray-900"
  const sub = dark ? "text-gray-400" : "text-gray-500"
  const weekBg = dark ? "bg-[#060e1c] border-[#1e2f45]" : "bg-gray-50 border-gray-200"

  const totalHours = plan.weeks
    .flatMap((w) => w.skills)
    .reduce((acc, s) => acc + (s.hours ?? 0), 0)

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
              <p className={`text-xs ${sub}`}>
                {plan.weeks.length} Woche{plan.weeks.length !== 1 ? "n" : ""}
                {totalHours > 0 && ` · ~${totalHours.toFixed(1)}h gesamt`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              title="Plan neu generieren"
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all active:scale-95 ${
                dark
                  ? "border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10"
                  : "border-indigo-200 text-indigo-600 hover:bg-indigo-50"
              }`}
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/>
              </svg>
              {savedAt ? formatSavedAt(savedAt) : "Neu generieren"}
            </button>
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
            plan.weeks.map((week) => {
              const weekHours = week.skills.reduce((acc, s) => acc + (s.hours ?? 0), 0)
              return (
                <div key={week.week} className={`rounded-xl border p-4 space-y-2.5 ${weekBg}`}>
                  <div className="flex items-center justify-between">
                    <p className={`text-xs font-bold uppercase tracking-wider ${sub}`}>
                      Woche {week.week}
                    </p>
                    <span className={`text-xs font-mono ${sub}`}>~{weekHours.toFixed(1)}h</span>
                  </div>
                  {week.skills.map((skill) => {
                    const progress = progressSkills.find((s) => s.skill_key === skill.skill_key)
                    const locked = progress ? !progress.is_unlocked : false
                    return (
                      <SkillRow
                        key={skill.skill_key}
                        skill={skill}
                        dark={dark}
                        locked={locked}
                        onStart={() => onStartSkill(skill.skill_key)}
                      />
                    )
                  })}
                </div>
              )
            })
          )}
        </div>

        {/* Legend */}
        <div className={`px-5 py-3 border-t flex items-center gap-4 ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
          {[
            { icon: "📖", label: "Wiederholen" },
            { icon: "✏️",  label: "Üben" },
            { icon: "🎯", label: "Herausforderung" },
          ].map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="text-sm">{icon}</span>
              <span className={`text-xs ${sub}`}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
