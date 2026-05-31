"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { getLearningProgress, analyzeSkill, deleteAnalysisEvents } from "@/lib/api"
import type { ProgressResponse, SkillAnalyzeResponse, SkillProgress } from "@/types/tutor"

const TOKEN_KEY = "ki_tutor_token"
function getToken(): string {
  if (typeof window === "undefined") return ""
  return localStorage.getItem(TOKEN_KEY) ?? ""
}

// Status-Konfiguration
const STATUS_CONFIG = {
  understood:     { label: "Verstanden",           color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",  bar: "bg-emerald-500" },
  partial:        { label: "Teilweise verstanden",  color: "bg-amber-500/20 text-amber-400 border-amber-500/30",       bar: "bg-amber-500"   },
  not_understood: { label: "Nicht verstanden",      color: "bg-red-500/20 text-red-400 border-red-500/30",             bar: "bg-red-500"     },
}
const STATUS_CONFIG_LIGHT = {
  understood:     { label: "Verstanden",           color: "bg-emerald-100 text-emerald-700 border-emerald-200",  bar: "bg-emerald-500" },
  partial:        { label: "Teilweise verstanden",  color: "bg-amber-100 text-amber-700 border-amber-200",       bar: "bg-amber-500"   },
  not_understood: { label: "Nicht verstanden",      color: "bg-red-100 text-red-700 border-red-200",             bar: "bg-red-500"     },
}

// User-Status-Konfiguration
const USER_STATUS_CONFIG = {
  "Anfänger":      { color: "bg-orange-500/20 text-orange-400 border-orange-500/30",     colorLight: "bg-orange-100 text-orange-700 border-orange-200"     },
  "Fortgeschritten": { color: "bg-blue-500/20 text-blue-400 border-blue-500/30",         colorLight: "bg-blue-100 text-blue-700 border-blue-200"           },
  "Profi":         { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",  colorLight: "bg-emerald-100 text-emerald-700 border-emerald-200"  },
}

function StatusBadge({ status, dark }: { status: string; dark: boolean }) {
  const cfg = (dark ? STATUS_CONFIG : STATUS_CONFIG_LIGHT)[status as keyof typeof STATUS_CONFIG]
    ?? (dark ? STATUS_CONFIG.not_understood : STATUS_CONFIG_LIGHT.not_understood)
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}

function UserStatusBadge({ status, dark }: { status: "Anfänger" | "Fortgeschritten" | "Profi"; dark: boolean }) {
  const cfg = USER_STATUS_CONFIG[status]
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${dark ? cfg.color : cfg.colorLight}`}>
      {status}
    </span>
  )
}

function SkillBar({ score, status, dark }: { score: number; status: string; dark: boolean }) {
  const cfg = (dark ? STATUS_CONFIG : STATUS_CONFIG_LIGHT)[status as keyof typeof STATUS_CONFIG]
    ?? (dark ? STATUS_CONFIG.not_understood : STATUS_CONFIG_LIGHT.not_understood)
  return (
    <div className={`w-full h-2 rounded-full ${dark ? "bg-[#1e2f45]" : "bg-gray-200"} overflow-hidden`}>
      <div
        className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`}
        style={{ width: `${score}%` }}
      />
    </div>
  )
}

function OverallRing({ score, dark }: { score: number; dark: boolean }) {
  const radius = 36
  const circ   = 2 * Math.PI * radius
  const dash   = circ * (score / 100)
  const color  = score >= 75 ? "#10b981" : score >= 40 ? "#f59e0b" : "#ef4444"

  return (
    <svg width="96" height="96" className="rotate-[-90deg]">
      <circle cx="48" cy="48" r={radius} fill="none" strokeWidth="8"
        stroke={dark ? "#1e2f45" : "#e5e7eb"} />
      <circle cx="48" cy="48" r={radius} fill="none" strokeWidth="8"
        stroke={color} strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        style={{ transition: "stroke-dasharray 0.8s ease" }} />
      <text x="48" y="52" textAnchor="middle" fontSize="18" fontWeight="bold"
        fill={dark ? "#fff" : "#111"} className="rotate-90 origin-center"
        style={{ transform: "rotate(90deg)", transformOrigin: "48px 48px" }}>
        {score}
      </text>
    </svg>
  )
}

const LEVEL_GROUPS: Array<{
  key: "beginner" | "intermediate" | "advanced"
  label: string
  alwaysShow: boolean
}> = [
  { key: "beginner",     label: "Grundlagen (Anfänger)", alwaysShow: true  },
  { key: "intermediate", label: "Fortgeschritten",        alwaysShow: false },
  { key: "advanced",     label: "Profi",                  alwaysShow: false },
]

function SkillCard({
  skill,
  dark,
  onClick,
}: {
  skill: SkillProgress
  dark: boolean
  onClick: () => void
}) {
  const isLocked = !skill.is_unlocked
  const cardBase = dark
    ? "rounded-xl border border-[#1e2f45] p-4 transition-colors"
    : "rounded-xl border border-gray-200 p-4 transition-colors"

  const interactiveClass = isLocked
    ? `${cardBase} opacity-50 ${dark ? "bg-[#0a1525]" : "bg-gray-50"}`
    : `${cardBase} cursor-pointer hover:border-blue-500/50 ${dark ? "bg-[#0a1525] hover:bg-[#0d1f35]" : "bg-white hover:bg-blue-50/50"}`

  return (
    <div
      className={interactiveClass}
      onClick={isLocked ? undefined : onClick}
      role={isLocked ? undefined : "button"}
      tabIndex={isLocked ? undefined : 0}
      onKeyDown={isLocked ? undefined : (e) => { if (e.key === "Enter" || e.key === " ") onClick() }}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className={`text-sm font-medium flex items-center gap-1.5 ${dark ? "text-gray-200" : "text-gray-700"}`}>
          {isLocked && <span title="Gesperrt">🔒</span>}
          {skill.skill_label}
        </span>
        {!isLocked && (
          <div className="flex items-center gap-2">
            <span className={`text-xs tabular-nums ${dark ? "text-gray-400" : "text-gray-500"}`}>
              {skill.score}/100
            </span>
            <StatusBadge status={skill.status} dark={dark} />
          </div>
        )}
        {isLocked && (
          <span className={`text-xs ${dark ? "text-gray-600" : "text-gray-400"}`}>Gesperrt</span>
        )}
      </div>
      {!isLocked && (
        <SkillBar score={skill.score} status={skill.status} dark={dark} />
      )}
    </div>
  )
}

export default function LearningProgressView() {
  const { user } = useAuth()
  const { dark } = useTheme()

  const [progress, setProgress]         = useState<ProgressResponse | null>(null)
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState<string | null>(null)
  const [selectedSkill, setSelectedSkill] = useState<SkillProgress | null>(null)
  const [refreshTick, setRefreshTick]   = useState(0)

  // Analyse-Panel
  const [inputText, setInputText]       = useState("")
  const [inputType, setInputType]       = useState<"code" | "frage">("frage")
  const [analyzing, setAnalyzing]       = useState(false)
  const [lastResult, setLastResult]     = useState<SkillAnalyzeResponse | null>(null)

  // Delete events state
  const [deleting, setDeleting]         = useState(false)
  const [deleteSuccess, setDeleteSuccess] = useState(false)

  // Collapsible section state
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    beginner: true,
    intermediate: false,
    advanced: false,
  })

  const bg       = dark ? "bg-[#060e1c] text-white"    : "bg-gray-50 text-gray-900"
  const card     = dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"
  const inputCls = dark
    ? "w-full bg-[#0a1525] border border-[#1e2f45] text-white placeholder-gray-500 rounded-xl p-3 text-sm resize-none focus:outline-none focus:border-blue-500/60"
    : "w-full bg-white border border-gray-300 text-gray-900 placeholder-gray-400 rounded-xl p-3 text-sm resize-none focus:outline-none focus:border-blue-500"

  const refreshProgress = useCallback(() => {
    setRefreshTick((t) => t + 1)
  }, [])

  useEffect(() => {
    if (!user) return
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    getLearningProgress(Number(user.id), getToken())
      .then((data) => { if (!cancelled) setProgress(data) })
      .catch(() => { if (!cancelled) setError("Fortschritt konnte nicht geladen werden.") })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [user, refreshTick])

  async function handleAnalyze() {
    if (!inputText.trim() || analyzing) return
    setAnalyzing(true)
    setLastResult(null)
    try {
      const result = await analyzeSkill(
        inputType === "code" ? { code: inputText } : { question: inputText },
        getToken(),
      )
      setLastResult(result)
      setProgress(result.updated_progress)
    } catch {
      setError("Analyse fehlgeschlagen.")
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleDeleteEvents() {
    const confirmed = window.confirm(
      "Alle letzten Analysen löschen? Diese Aktion kann nicht rückgängig gemacht werden."
    )
    if (!confirmed) return
    setDeleting(true)
    try {
      await deleteAnalysisEvents(getToken())
      setDeleteSuccess(true)
      refreshProgress()
      setTimeout(() => setDeleteSuccess(false), 3000)
    } catch {
      setError("Löschen fehlgeschlagen.")
    } finally {
      setDeleting(false)
    }
  }

  function toggleGroup(key: string) {
    setOpenGroups((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  if (loading) {
    return (
      <div className={`${bg} flex-1 flex items-center justify-center`}>
        <div className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>Laden…</div>
      </div>
    )
  }

  // Unused state log suppression — selectedSkill will be wired to modal in Phase 6
  void selectedSkill

  return (
    <div className={`${bg} flex-1 overflow-y-auto`}>
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

        {/* Header */}
        <div className="flex items-center gap-4 flex-wrap">
          <div>
            <h1 className={`text-xl font-bold ${dark ? "text-white" : "text-gray-900"}`}>
              Lernfortschritt
            </h1>
            <p className={`text-sm mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
              Dein aktueller Stand in den Python-Grundlagen
            </p>
          </div>
          {progress && (
            <UserStatusBadge status={progress.user_status} dark={dark} />
          )}
        </div>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Gesamtfortschritt */}
        {progress && (
          <div className={`rounded-2xl border p-6 ${card} flex items-center gap-6`}>
            <OverallRing score={progress.overall_score} dark={dark} />
            <div>
              <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                Gesamtfortschritt
              </p>
              <p className={`text-3xl font-bold ${dark ? "text-white" : "text-gray-900"}`}>
                {progress.overall_score}%
              </p>
              <p className={`text-sm mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                Durchschnitt über alle Skills
              </p>
            </div>
          </div>
        )}

        {/* Skill-Fortschrittsbalken — grouped by level */}
        {progress && (
          <div className={`rounded-2xl border p-6 ${card} space-y-4`}>
            <h2 className={`text-sm font-semibold ${dark ? "text-white" : "text-gray-900"}`}>
              Skills im Detail
            </h2>

            {LEVEL_GROUPS.map(({ key, label, alwaysShow }) => {
              const groupSkills = progress.skills
                .filter((s) => s.level === key)
                .sort((a, b) => a.order - b.order)

              const hasUnlocked = groupSkills.some((s) => s.is_unlocked)
              if (!alwaysShow && !hasUnlocked) return null

              const isOpen = openGroups[key] ?? false

              return (
                <div key={key}>
                  <button
                    className={`w-full flex items-center justify-between py-2 text-left transition-colors ${
                      dark
                        ? "text-gray-300 hover:text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                    onClick={() => toggleGroup(key)}
                  >
                    <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
                    <span className={`text-xs ${dark ? "text-gray-500" : "text-gray-400"}`}>
                      {isOpen ? "▲" : "▼"}
                    </span>
                  </button>

                  {isOpen && (
                    <div className="space-y-2 mt-2">
                      {groupSkills.map((skill) => (
                        <SkillCard
                          key={skill.skill_key}
                          skill={skill}
                          dark={dark}
                          onClick={() => setSelectedSkill(skill)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Analyse-Panel */}
        <div className={`rounded-2xl border p-6 ${card}`}>
          <h2 className={`text-sm font-semibold mb-1 ${dark ? "text-white" : "text-gray-900"}`}>
            Code oder Frage analysieren
          </h2>
          <p className={`text-xs mb-4 ${dark ? "text-gray-500" : "text-gray-400"}`}>
            Gib Python-Code oder eine Frage ein — das System erkennt den Skill und bewertet deinen Stand.
          </p>
          <div className="flex gap-2 mb-2">
            <button
              onClick={() => setInputType("code")}
              className={inputType === "code" ? "px-3 py-1 rounded bg-blue-600 text-white text-sm" : "px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-sm"}
            >
              Code
            </button>
            <button
              onClick={() => setInputType("frage")}
              className={inputType === "frage" ? "px-3 py-1 rounded bg-blue-600 text-white text-sm" : "px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-sm"}
            >
              Frage
            </button>
          </div>
          <textarea
            rows={5}
            placeholder={inputType === "code" ? "# Beispiel:\nfor i in range(5)\n    print(i)" : "z.B. Was ist eine for-Schleife?"}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className={inputCls}
          />
          <button
            onClick={handleAnalyze}
            disabled={!inputText.trim() || analyzing}
            className="mt-3 px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {analyzing ? "Analysiere…" : "Analysieren"}
          </button>

          {/* Analyse-Ergebnis */}
          {lastResult && (
            <div className={`mt-5 rounded-xl border p-5 space-y-4 ${dark ? "border-[#1e2f45] bg-[#060e1c]" : "border-gray-200 bg-gray-50"}`}>
              {/* Score + Status */}
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`text-2xl font-bold ${dark ? "text-white" : "text-gray-900"}`}>
                  {lastResult.score}/100
                </span>
                <StatusBadge status={lastResult.status} dark={dark} />
                <span className={`text-xs px-2 py-0.5 rounded-full border ${dark ? "border-blue-500/30 bg-blue-500/10 text-blue-400" : "border-blue-200 bg-blue-50 text-blue-700"}`}>
                  Skill: {lastResult.main_skill}
                </span>
              </div>

              {/* Feedback */}
              <div>
                <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                  Feedback
                </p>
                <p className={`text-sm ${dark ? "text-gray-300" : "text-gray-700"}`}>
                  {lastResult.feedback}
                </p>
              </div>

              {/* Typische Fehler */}
              {lastResult.mistakes.length > 0 && (
                <div>
                  <p className={`text-xs font-medium uppercase tracking-wider mb-2 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                    Typische Fehler
                  </p>
                  <ul className="space-y-1">
                    {lastResult.mistakes.map((m, i) => (
                      <li key={i} className={`flex items-start gap-2 text-sm ${dark ? "text-amber-300" : "text-amber-700"}`}>
                        <span className="mt-0.5">⚠</span>
                        {m}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Empfohlene Übung */}
              {lastResult.recommended_next_exercise && (
                <div className={`rounded-xl p-4 ${dark ? "bg-blue-600/10 border border-blue-500/20" : "bg-blue-50 border border-blue-200"}`}>
                  <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${dark ? "text-blue-400" : "text-blue-700"}`}>
                    Empfohlene nächste Übung
                  </p>
                  <p className={`text-sm ${dark ? "text-blue-200" : "text-blue-800"}`}>
                    {lastResult.recommended_next_exercise}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Letzte Analysen */}
        {progress && progress.recent_events.length > 0 && (
          <div className={`rounded-2xl border p-6 ${card}`}>
            <h2 className={`text-sm font-semibold mb-4 ${dark ? "text-white" : "text-gray-900"}`}>
              Letzte Analysen
            </h2>
            <div className="space-y-3">
              {progress.recent_events.map((ev, i) => (
                <div key={i} className={`rounded-xl border p-4 ${dark ? "border-[#1e2f45] bg-[#0a1525]" : "border-gray-100 bg-gray-50"}`}>
                  <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-700"}`}>
                        {ev.skill_label}
                      </span>
                      <span className={`text-xs tabular-nums ${dark ? "text-gray-500" : "text-gray-400"}`}>
                        Score: {ev.score}
                      </span>
                    </div>
                    {ev.created_at && (
                      <span className={`text-xs ${dark ? "text-gray-600" : "text-gray-400"}`}>
                        {new Date(ev.created_at).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" })}
                      </span>
                    )}
                  </div>
                  {ev.feedback && (
                    <p className={`text-xs ${dark ? "text-gray-400" : "text-gray-600"}`}>{ev.feedback}</p>
                  )}
                  {ev.mistakes.length > 0 && (
                    <p className={`text-xs mt-1 ${dark ? "text-amber-400/70" : "text-amber-700"}`}>
                      ⚠ {ev.mistakes.join(" · ")}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Letzte Analysen löschen */}
            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={handleDeleteEvents}
                disabled={deleting}
                className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                  dark
                    ? "border-red-500/30 text-red-400 hover:bg-red-500/10"
                    : "border-red-200 text-red-600 hover:bg-red-50"
                }`}
              >
                {deleting ? "Lösche…" : "Letzte Analysen löschen"}
              </button>
              {deleteSuccess && (
                <span className={`text-xs ${dark ? "text-emerald-400" : "text-emerald-600"}`}>
                  Analysen wurden gelöscht.
                </span>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
