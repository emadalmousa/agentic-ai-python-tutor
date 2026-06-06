"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useTheme } from "@/context/ThemeContext"
import { useAuth } from "@/context/AuthContext"
import { getExercises, submitExercise, getExerciseHint } from "@/lib/api"
import type { SkillProgress, Exercise, SubmitExerciseResponse } from "@/types/tutor"
import MarkdownMessage from "@/components/tutor/MarkdownMessage"
import CodeEditor from "@/components/tutor/CodeEditor"

interface ExercisePanelProps {
  skill: SkillProgress
  onSkillScoreUpdate: (skillKey: string, newScore: number) => void
  onStartSkillTest: () => void
}

function ExerciseCard({
  exercise,
  index,
  skillKey,
  token,
  dark,
  onScoreUpdate,
}: {
  exercise: Exercise
  index: number
  skillKey: string
  token: string
  dark: boolean
  onScoreUpdate: (newScore: number) => void
}) {
  const router = useRouter()
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const [code, setCode] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<SubmitExerciseResponse | null>(null)
  const [hintLevel, setHintLevel] = useState(1)
  const [hint, setHint] = useState<string | null>(null)
  const [hintLoading, setHintLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  async function handleSubmit() {
    if (!code.trim() || submitting) return
    setSubmitting(true)
    setResult(null)
    setErr(null)
    try {
      const res = await submitExercise({ skill_key: skillKey, exercise_id: exercise.id, code }, token)
      setResult(res)
      onScoreUpdate(res.new_skill_score)
      if (res.result === "falsch" && res.redirect_to_tutor) {
        localStorage.setItem("ki_tutor_exercise_redirect", JSON.stringify({
          code, analysis: res.analysis, exercise_title: exercise.title,
        }))
        timerRef.current = setTimeout(() => router.push("/tutor"), 1200)
      }
    } catch {
      setErr("Abgabe fehlgeschlagen.")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleHint() {
    if (hintLevel > 3 || hintLoading) return
    setHintLoading(true)
    try {
      const res = await getExerciseHint({ skill_key: skillKey, exercise_id: exercise.id, code, hint_level: hintLevel }, token)
      setHint(res.hint)
      setHintLevel((p) => p + 1)
    } catch {
      setErr("Tipp nicht verfügbar.")
    } finally {
      setHintLoading(false)
    }
  }

  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const cardBg = dark ? "bg-[#0d1929]" : "bg-white"
  const labelCls = `text-xs font-semibold uppercase tracking-wider ${dark ? "text-gray-500" : "text-gray-400"}`

  return (
    <div className={`rounded-2xl border ${border} ${cardBg} overflow-hidden`}>
      {/* Header */}
      <div className={`px-5 py-3 border-b ${border} flex items-center gap-3`}>
        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          exercise.is_locked
            ? "bg-emerald-500/20 text-emerald-400"
            : "bg-blue-600/20 text-blue-400"
        }`}>
          {exercise.is_locked ? "✓" : index + 1}
        </span>
        <h3 className={`text-sm font-semibold ${dark ? "text-white" : "text-gray-800"}`}>
          {exercise.title}
        </h3>
        {exercise.is_locked && (
          <span className="ml-auto text-xs text-emerald-400 font-medium">+2 Punkte</span>
        )}
      </div>

      {/* Body */}
      <div className="px-5 py-4 space-y-4">
        {/* Description */}
        <p className={`text-sm leading-relaxed ${dark ? "text-gray-300" : "text-gray-600"}`}>
          {exercise.description}
        </p>

        {/* Code editor — always visible, locked ones are read-only */}
        <div>
          <label className={`block mb-2 ${labelCls}`}>Dein Code</label>
          {exercise.is_locked ? (
            <div className="opacity-50 cursor-default">
              <CodeEditor code={code || "# Abgeschlossen"} onChange={() => {}} dark={dark} />
            </div>
          ) : (
            <CodeEditor code={code} onChange={setCode} dark={dark} />
          )}
        </div>

        {!exercise.is_locked && (
          <>
            {/* Hint */}
            {hint && (
              <div className={`rounded-xl p-4 border-l-4 ${dark ? "bg-blue-500/5 border-l-blue-500/50" : "bg-blue-50 border-l-blue-400"}`}>
                <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${dark ? "text-blue-400" : "text-blue-600"}`}>
                  Tipp {hintLevel - 1}
                </p>
                <MarkdownMessage content={hint} dark={dark} />
              </div>
            )}

            {err && (
              <p className="text-xs text-red-400">{err}</p>
            )}

            {/* Result */}
            {result && (
              <div className={`rounded-xl p-4 border-l-4 text-sm space-y-1 ${
                result.result === "richtig"
                  ? dark ? "bg-emerald-500/10 border-l-emerald-500 text-emerald-300" : "bg-emerald-50 border-l-emerald-500 text-emerald-800"
                  : result.result === "teilweise"
                    ? dark ? "bg-amber-500/10 border-l-amber-500 text-amber-300" : "bg-amber-50 border-l-amber-500 text-amber-800"
                    : dark ? "bg-red-500/10 border-l-red-500 text-red-300" : "bg-red-50 border-l-red-500 text-red-800"
              }`}>
                <p className="font-semibold text-sm mb-2">
                  {result.result === "richtig" && `✓ Richtig! +${result.score_change / 10} Punkte`}
                  {result.result === "teilweise" && `◐ Teilweise! +${result.score_change / 10} Punkte`}
                  {result.result === "falsch" && "✗ Falsch"}
                </p>
                {result.what_was_good && (
                  <MarkdownMessage content={result.what_was_good} dark={dark} />
                )}
                {result.what_went_wrong && (
                  <div className="mt-1 opacity-90">
                    <MarkdownMessage content={result.what_went_wrong} dark={dark} />
                  </div>
                )}
                {result.result === "falsch" && result.redirect_to_tutor && (
                  <p className="text-xs opacity-60">Weiterleitung zum Tutor...</p>
                )}
                {result.result === "falsch" && !result.redirect_to_tutor && (
                  <p className="text-xs opacity-60">Versuche es nochmal!</p>
                )}
                {(result.stdout || result.stderr) && (
                  <pre className={`mt-2 text-xs font-mono rounded-lg p-2 ${dark ? "bg-black/30" : "bg-white/60"} whitespace-pre-wrap`}>
                    {result.stdout}{result.stderr && <span className="text-red-400">{result.stderr}</span>}
                  </pre>
                )}
              </div>
            )}

            {/* Buttons */}
            <div className="flex items-center justify-between gap-3 pt-1">
              <button
                onClick={handleHint}
                disabled={hintLevel > 3 || hintLoading}
                className={`px-4 py-2 rounded-xl text-xs font-medium border transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${
                  dark ? "border-[#1e2f45] text-gray-400 hover:bg-[#1e2f45]" : "border-gray-200 text-gray-500 hover:bg-gray-50"
                }`}
              >
                {hintLoading ? "Lädt..." : hintLevel > 3 ? "Kein weiterer Tipp" : `💡 Tipp ${hintLevel}`}
              </button>
              <button
                onClick={handleSubmit}
                disabled={!code.trim() || submitting}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? "Prüfe..." : "▶ Ausführen"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function ExercisePanel({ skill, onSkillScoreUpdate, onStartSkillTest }: ExercisePanelProps) {
  const { dark } = useTheme()
  useAuth()
  const router = useRouter()
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""

  const [exercises, setExercises] = useState<Exercise[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshTick, setRefreshTick] = useState(0)

  function handleExplainTopic() {
    localStorage.setItem("ki_tutor_explain_topic", JSON.stringify({
      skill_key: skill.skill_key,
      skill_label: skill.skill_label,
      level: skill.level,
    }))
    router.push("/tutor")
  }

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    getExercises(skill.skill_key, token)
      .then((data) => { if (!cancelled) setExercises(data.exercises) })
      .catch(() => { if (!cancelled) setError("Übungen konnten nicht geladen werden.") })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [skill.skill_key, refreshTick])

  function handleScoreUpdate(newScore: number) {
    onSkillScoreUpdate(skill.skill_key, newScore)
    // reload exercises to update lock states
    setRefreshTick((t) => t + 1)
  }

  const allDone = exercises.length > 0 && exercises.every((ex) => ex.is_locked)
  const visibleExercises = exercises.filter((ex) => ex.is_locked || ex.is_unlocked)

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className={`w-6 h-6 border-2 border-t-transparent rounded-full animate-spin ${dark ? "border-blue-400" : "border-blue-600"}`} />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-4">

      {/* Skill header */}
      <div className="flex items-center justify-between gap-3">
        <h2 className={`text-base font-bold ${dark ? "text-white" : "text-gray-900"}`}>
          {skill.skill_label} — Übungen
        </h2>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs tabular-nums font-mono px-2 py-0.5 rounded-full ${dark ? "bg-[#1e2f45] text-gray-400" : "bg-gray-100 text-gray-500"}`}>
            {exercises.filter((e) => e.is_locked).length} / {exercises.length} gelöst
          </span>
          <button
            onClick={handleExplainTopic}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-colors ${
              dark
                ? "border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10"
                : "border-indigo-200 text-indigo-600 hover:bg-indigo-50"
            }`}
            title="Lass dir dieses Thema vom Tutor erklären"
          >
            <span>💡</span> Thema erklären
          </button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {/* Exercises stacked */}
      {visibleExercises.map((ex, i) => (
        <ExerciseCard
          key={ex.id}
          exercise={ex}
          index={i}
          skillKey={skill.skill_key}
          token={token}
          dark={dark}
          onScoreUpdate={handleScoreUpdate}
        />
      ))}

      {/* All done */}
      {allDone && (
        <div className={`rounded-2xl border p-6 text-center space-y-2 ${dark ? "bg-emerald-500/5 border-emerald-500/20" : "bg-emerald-50 border-emerald-200"}`}>
          <div className="text-4xl">🎉</div>
          <p className={`text-sm font-semibold ${dark ? "text-emerald-300" : "text-emerald-700"}`}>
            Alle Übungen abgeschlossen! Score: {skill.score}/100
          </p>
          <p className={`text-xs ${dark ? "text-emerald-400/70" : "text-emerald-600/70"}`}>
            Wenn alle Skills dieses Levels ≥ 80% — Level-Test freischalten!
          </p>
        </div>
      )}
    </div>
  )
}
