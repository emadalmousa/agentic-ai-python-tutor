"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useLang } from "@/context/LangContext"
import { getLearningProgress } from "@/lib/api"
import type { ProgressResponse, SkillProgress } from "@/types/tutor"
import ExercisePanel from "@/components/ExercisePanel"
import SkillTestModal from "@/components/SkillTestModal"
import LevelTestModal from "@/components/LevelTestModal"
import type { LevelKey } from "@/types/tutor"
import type { TranslationKey } from "@/i18n"

// ─── Config ────────────────────────────────────────────────────────────────

const STATUS_BAR_COLORS = {
  understood:     "bg-emerald-500",
  partial:        "bg-amber-500",
  not_understood: "bg-red-500",
}

const STATUS_BADGE_COLORS = {
  dark: {
    understood:     "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    partial:        "bg-amber-500/20 text-amber-400 border-amber-500/30",
    not_understood: "bg-red-500/20 text-red-400 border-red-500/30",
  },
  light: {
    understood:     "bg-emerald-100 text-emerald-700 border-emerald-200",
    partial:        "bg-amber-100 text-amber-700 border-amber-200",
    not_understood: "bg-red-100 text-red-700 border-red-200",
  },
}

const STATUS_LABEL_KEYS: Record<string, TranslationKey> = {
  understood:     "status.understood",
  partial:        "status.partial",
  not_understood: "status.not_understood",
}

const LEVEL_META: Record<string, { labelKey: TranslationKey; icon: string; accent: string }> = {
  beginner:     { labelKey: "levels.beginner",       icon: "🌱", accent: "blue" },
  intermediate: { labelKey: "levels.intermediate", icon: "⚡", accent: "purple" },
  advanced:     { labelKey: "levels.advanced",           icon: "🔥", accent: "orange" },
}

const USER_STATUS_STYLES = {
  "Anfänger":      "bg-orange-500/20 text-orange-400 border-orange-500/40",
  "Fortgeschritten": "bg-blue-500/20 text-blue-400 border-blue-500/40",
  "Profi":         "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
}
const USER_STATUS_STYLES_LIGHT = {
  "Anfänger":      "bg-orange-100 text-orange-700 border-orange-200",
  "Fortgeschritten": "bg-blue-100 text-blue-700 border-blue-200",
  "Profi":         "bg-emerald-100 text-emerald-700 border-emerald-200",
}

// ─── Small helpers ─────────────────────────────────────────────────────────

function statusBarColor(status: string) {
  return STATUS_BAR_COLORS[status as keyof typeof STATUS_BAR_COLORS] ?? STATUS_BAR_COLORS.not_understood
}

function statusBadgeColor(status: string, dark: boolean) {
  const map = dark ? STATUS_BADGE_COLORS.dark : STATUS_BADGE_COLORS.light
  return map[status as keyof typeof map] ?? map.not_understood
}

function Ring({ score, size = 80, dark }: { score: number; size?: number; dark: boolean }) {
  const r = size / 2 - 7
  const c = 2 * Math.PI * r
  const color = score >= 75 ? "#10b981" : score >= 40 ? "#f59e0b" : "#ef4444"
  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth="7" stroke={dark ? "#1e2f45" : "#e5e7eb"} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth="7" stroke={color}
        strokeLinecap="round" strokeDasharray={`${c * score / 100} ${c}`}
        style={{ transition: "stroke-dasharray 0.9s ease" }} />
      <text x={size / 2} y={size / 2 + 6} textAnchor="middle" fontSize={size / 5} fontWeight="bold"
        fill={dark ? "#fff" : "#111"}
        style={{ transform: `rotate(90deg)`, transformOrigin: `${size / 2}px ${size / 2}px` }}>
        {score}
      </text>
    </svg>
  )
}

function Bar({ score, status, dark }: { score: number; status: string; dark: boolean }) {
  return (
    <div className={`w-full h-1.5 rounded-full ${dark ? "bg-[#1e2f45]" : "bg-gray-200"} overflow-hidden`}>
      <div className={`h-full rounded-full transition-all duration-700 ${statusBarColor(status)}`} style={{ width: `${score}%` }} />
    </div>
  )
}

// ─── Left panel: skill list ─────────────────────────────────────────────────

function SkillListItem({
  skill, selected, dark, onClick,
}: { skill: SkillProgress; selected: boolean; dark: boolean; onClick: () => void }) {
  const locked = !skill.is_unlocked

  const base = `flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all text-sm`
  const bg = locked
    ? `opacity-40 cursor-default ${dark ? "text-gray-500" : "text-gray-400"}`
    : selected
      ? dark ? "bg-blue-600/25 border border-blue-500/40 text-white" : "bg-blue-50 border border-blue-200 text-blue-900"
      : dark
        ? "hover:bg-[#0d1f35] text-gray-300 border border-transparent hover:border-[#1e2f45]"
        : "hover:bg-gray-100 text-gray-700 border border-transparent"

  return (
    <div className={`${base} ${bg}`} onClick={locked ? undefined : onClick}>
      <span className="text-base leading-none">
        {locked ? "🔒" : skill.score === 100 ? "✅" : skill.score >= 80 ? "⭐" : "📖"}
      </span>
      <div className="flex-1 min-w-0">
        <p className="truncate text-xs font-medium leading-tight">{skill.skill_label}</p>
        {!locked && (
          <Bar score={skill.score} status={skill.status} dark={dark} />
        )}
      </div>
      {!locked && (
        <span className={`text-xs tabular-nums font-mono shrink-0 ${dark ? "text-gray-500" : "text-gray-400"}`}>
          {skill.score}%
        </span>
      )}
    </div>
  )
}

// ─── Right panel: skill detail ──────────────────────────────────────────────

function EmptyState({ dark }: { dark: boolean }) {
  const { t } = useLang()
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 opacity-50 select-none">
      <span className="text-6xl">👈</span>
      <p className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>
        {t("progress.selectSkill")}
      </p>
    </div>
  )
}

function SkillDetail({
  skill, dark, onStartExercise,
}: { skill: SkillProgress; dark: boolean; onStartExercise: () => void }) {
  const { t } = useLang()
  const statusLabel = t(STATUS_LABEL_KEYS[skill.status] ?? "status.not_understood")
  const meta = LEVEL_META[skill.level] ?? LEVEL_META.beginner

  const exercisesDone = Math.floor(skill.score / 20)
  const allExercisesDone = skill.score >= 100

  const accentColors: Record<string, string> = {
    blue:   dark ? "from-blue-600/20 to-transparent border-blue-500/20" : "from-blue-50 to-transparent border-blue-100",
    purple: dark ? "from-purple-600/20 to-transparent border-purple-500/20" : "from-purple-50 to-transparent border-purple-100",
    orange: dark ? "from-orange-600/20 to-transparent border-orange-500/20" : "from-orange-50 to-transparent border-orange-100",
  }
  const accentText: Record<string, string> = {
    blue:   dark ? "text-blue-400" : "text-blue-700",
    purple: dark ? "text-purple-400" : "text-purple-700",
    orange: dark ? "text-orange-400" : "text-orange-700",
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-5">

      {/* Hero card */}
      <div className={`rounded-2xl border bg-gradient-to-br p-6 ${accentColors[meta.accent]}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-2xl">{meta.icon}</span>
              <span className={`text-xs font-semibold uppercase tracking-widest ${accentText[meta.accent]}`}>
                {t(meta.labelKey)}
              </span>
            </div>
            <h2 className={`text-2xl font-bold mt-1 ${dark ? "text-white" : "text-gray-900"}`}>
              {skill.skill_label}
            </h2>
            <span className={`inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadgeColor(skill.status, dark)}`}>
              {statusLabel}
            </span>
          </div>
          <Ring score={skill.score} size={88} dark={dark} />
        </div>
      </div>

      {/* Progress breakdown */}
      <div className={`rounded-2xl border p-5 ${dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"}`}>
        <h3 className={`text-xs font-semibold uppercase tracking-wider mb-4 ${dark ? "text-gray-400" : "text-gray-500"}`}>
          {t("progress.progressLabel")}
        </h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          {[1, 2, 3, 4, 5].slice(0, 3).concat([4, 5]).map((n) => {
            const done = n <= exercisesDone
            const current = n === exercisesDone + 1 && !allExercisesDone
            return (
              <div key={n} className={`rounded-xl p-3 text-center border transition-all ${
                done
                  ? dark ? "bg-emerald-500/15 border-emerald-500/30" : "bg-emerald-50 border-emerald-200"
                  : current
                    ? dark ? "bg-blue-500/15 border-blue-500/40 ring-1 ring-blue-500/30" : "bg-blue-50 border-blue-300 ring-1 ring-blue-200"
                    : dark ? "bg-[#0a1525] border-[#1e2f45] opacity-40" : "bg-gray-50 border-gray-200 opacity-50"
              }`}>
                <div className="text-xl mb-1">{done ? "✅" : current ? "📝" : "🔒"}</div>
                <div className={`text-xs font-medium ${dark ? "text-gray-400" : "text-gray-500"}`}>
                  {t("progress.exerciseN", { n })}
                </div>
                <div className={`text-xs mt-0.5 ${done ? (dark ? "text-emerald-400" : "text-emerald-600") : current ? (dark ? "text-blue-400" : "text-blue-600") : (dark ? "text-gray-600" : "text-gray-400")}`}>
                  {done ? t("progress.done") : current ? t("progress.open") : t("progress.locked")}
                </div>
              </div>
            )
          })}
        </div>
        <div className={`flex justify-between text-xs mb-1.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>
          <span>{t("progress.exercisesCompleted", { done: exercisesDone, total: 5 })}</span>
          <span>{skill.score}%</span>
        </div>
        <div className={`w-full h-2.5 rounded-full ${dark ? "bg-[#1e2f45]" : "bg-gray-200"} overflow-hidden`}>
          <div
            className={`h-full rounded-full transition-all duration-700 ${statusBarColor(skill.status)}`}
            style={{ width: `${skill.score}%` }}
          />
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className={`rounded-xl border p-4 ${dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"}`}>
          <p className={`text-xs uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>{t("progress.nextGoal")}</p>
          <p className={`text-sm font-medium ${dark ? "text-white" : "text-gray-800"}`}>
            {allExercisesDone ? t("progress.passSkillTest") : t("progress.solveExercise", { n: exercisesDone + 1 })}
          </p>
        </div>
        <div className={`rounded-xl border p-4 ${dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"}`}>
          <p className={`text-xs uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>{t("progress.toNextSkill")}</p>
          <p className={`text-sm font-medium ${dark ? "text-white" : "text-gray-800"}`}>
            {skill.score >= 80 ? t("progress.reached") : t("progress.remaining", { n: 80 - skill.score })}
          </p>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onStartExercise}
        className="w-full py-3 rounded-2xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white transition-all shadow-lg shadow-blue-600/20"
      >
        {allExercisesDone ? t("progress.startSkillTest") : t("progress.startExercise", { n: exercisesDone + 1 })}
      </button>

    </div>
  )
}

// ─── Main component ─────────────────────────────────────────────────────────

export default function LearningProgressView() {
  const { user } = useAuth()
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""
  const { dark } = useTheme()
  const { t } = useLang()

  const [progress, setProgress]           = useState<ProgressResponse | null>(null)
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState<string | null>(null)
  const [selectedSkill, setSelectedSkill] = useState<SkillProgress | null>(null)
  const [skillTestSkill, setSkillTestSkill] = useState<SkillProgress | null>(null)
  const [showLevelTest, setShowLevelTest] = useState<LevelKey | null>(null)
  const [refreshTick, setRefreshTick]     = useState(0)
  const [activeLevel, setActiveLevel]     = useState<LevelKey>("beginner")

  const refreshProgress = useCallback(() => setRefreshTick((t) => t + 1), [])

  useEffect(() => {
    if (!user) return
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    getLearningProgress(Number(user.id), token)
      .then((data) => { if (!cancelled) setProgress(data) })
      .catch(() => { if (!cancelled) setError(t("progress.loadError")) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [user, refreshTick])

  function handleSkillScoreUpdate(skillKey: string, newScore: number) {
    setProgress((prev) => {
      if (!prev) return prev
      return { ...prev, skills: prev.skills.map((s) => s.skill_key === skillKey ? { ...s, score: newScore } : s) }
    })
    setSelectedSkill((prev) => prev?.skill_key === skillKey ? { ...prev, score: newScore } : prev)
  }

  function handleTestPassed(_skillKey: string) {
    setSkillTestSkill(null)
    refreshProgress()
  }

  const bg   = dark ? "bg-[#060e1c] text-white" : "bg-gray-50 text-gray-900"
  const side = dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"

  if (loading) {
    return (
      <div className={`${bg} flex-1 flex items-center justify-center`}>
        <div className={`text-sm animate-pulse ${dark ? "text-gray-400" : "text-gray-500"}`}>{t("progress.loading")}</div>
      </div>
    )
  }

  const levelSkills = (level: string) =>
    (progress?.skills ?? []).filter((s) => s.level === level).sort((a, b) => a.order - b.order)

  const unlockedLevels = (["beginner", "intermediate", "advanced"] as const).filter(
    (l) => l === "beginner" || levelSkills(l).some((s) => s.is_unlocked)
  )

  return (
    <div className={`${bg} flex-1 flex flex-col overflow-hidden`}>

      {/* Top bar */}
      <div className={`border-b px-6 py-4 flex items-center justify-between gap-4 shrink-0 ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
        <div className="flex items-center gap-3">
          <h1 className={`text-lg font-bold ${dark ? "text-white" : "text-gray-900"}`}>{t("progress.title")}</h1>
          {progress && (
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${dark ? USER_STATUS_STYLES[progress.user_status] : USER_STATUS_STYLES_LIGHT[progress.user_status]}`}>
              {progress.user_status}
            </span>
          )}
        </div>
        {progress && (
          <div className="flex items-center gap-2">
            <Ring score={progress.overall_score} size={44} dark={dark} />
            <div>
              <p className={`text-xs ${dark ? "text-gray-500" : "text-gray-400"}`}>{t("progress.total")}</p>
              <p className={`text-sm font-bold ${dark ? "text-white" : "text-gray-900"}`}>{progress.overall_score}%</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Split layout */}
      <div className="flex-1 flex overflow-hidden">

        {/* LEFT — skill list */}
        <div className={`w-64 shrink-0 border-r flex flex-col overflow-hidden ${side}`}>

          {/* Level tabs */}
          <div className={`flex border-b ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
            {unlockedLevels.map((lvl) => {
              const meta = LEVEL_META[lvl]
              const active = activeLevel === lvl
              return (
                <button
                  key={lvl}
                  onClick={() => setActiveLevel(lvl)}
                  className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
                    active
                      ? dark ? "border-b-2 border-blue-500 text-blue-400" : "border-b-2 border-blue-500 text-blue-600"
                      : dark ? "text-gray-500 hover:text-gray-300" : "text-gray-400 hover:text-gray-600"
                  }`}
                  title={t(meta.labelKey)}
                >
                  {meta.icon}
                </button>
              )
            })}
          </div>

          {/* Skill items */}
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {levelSkills(activeLevel).map((skill) => (
              <SkillListItem
                key={skill.skill_key}
                skill={skill}
                selected={selectedSkill?.skill_key === skill.skill_key}
                dark={dark}
                onClick={() => setSelectedSkill(skill)}
              />
            ))}
          </div>

          {/* Level stats footer + Level-Test Button */}
          {progress && (() => {
            const skills = levelSkills(activeLevel)
            const ready = skills.length > 0 && skills.every((s) => s.score >= 80)
            return (
              <div className={`p-3 border-t space-y-2 ${dark ? "border-[#1e2f45]" : "border-gray-200"}`}>
                <p className={`text-xs text-center ${dark ? "text-gray-500" : "text-gray-400"}`}>
                  {t("progress.skillsAbove80", { done: skills.filter((s) => s.score >= 80).length, total: skills.length })}
                </p>
                {ready && (
                  <button
                    onClick={() => { setSelectedSkill(null); setShowLevelTest(activeLevel) }}
                    className="w-full py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                  >
                    {t("progress.startLevelTest")}
                  </button>
                )}
              </div>
            )
          })()}
        </div>

        {/* RIGHT — detail panel */}
        <div className="flex-1 flex overflow-hidden">
          {showLevelTest ? (
            <LevelTestModal
              level={showLevelTest}
              onClose={() => setShowLevelTest(null)}
              onTestResult={() => { setShowLevelTest(null); refreshProgress() }}
            />
          ) : !selectedSkill || !selectedSkill.is_unlocked ? (
            <EmptyState dark={dark} />
          ) : skillTestSkill ? (
            <SkillTestModal
              skill={skillTestSkill}
              onClose={() => setSkillTestSkill(null)}
              onTestPassed={handleTestPassed}
              inline
            />
          ) : (
            <ExercisePanel
              skill={selectedSkill}
              onSkillScoreUpdate={handleSkillScoreUpdate}
              onStartSkillTest={() => setSkillTestSkill(selectedSkill)}
            />
          )}
        </div>

      </div>
    </div>
  )
}
