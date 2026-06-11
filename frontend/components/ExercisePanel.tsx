"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useTheme } from "@/context/ThemeContext"
import { useAuth } from "@/context/AuthContext"
import { getExercises, submitExercise, getExerciseHint } from "@/lib/api"
import type { SkillProgress, Exercise, SubmitExerciseResponse } from "@/types/tutor"
import MarkdownMessage from "@/components/tutor/MarkdownMessage"
import CodeEditor from "@/components/tutor/CodeEditor"

function ResultPopup({
  result,
  onClose,
  onGoToTutor,
  dark,
}: {
  result: SubmitExerciseResponse
  onClose: () => void
  onGoToTutor: () => void
  dark: boolean
}) {
  const isRichtig = result.result === "richtig"
  const isTeilweise = result.result === "teilweise"
  const isFalsch = result.result === "falsch"

  const cardBg = dark ? "bg-[#0d1929]" : "bg-white"
  const textBase = dark ? "text-gray-300" : "text-gray-700"

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className={`${cardBg} max-w-md w-full mx-4 rounded-2xl shadow-2xl overflow-hidden`}>

        {/* Coloured top band */}
        {isRichtig && (
          <div className="bg-emerald-500/15 px-6 pt-8 pb-6 flex flex-col items-center gap-3 border-b border-emerald-500/20">
            <span className="text-8xl leading-none select-none">🎉</span>
            <h2 className="text-2xl font-bold text-emerald-400">Richtig! 🎉</h2>
            {result.score_change > 0 && (
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-sm font-semibold">
                +{result.score_change / 10} Punkte
              </span>
            )}
          </div>
        )}

        {isTeilweise && (
          <div className="bg-amber-500/15 px-6 pt-8 pb-6 flex flex-col items-center gap-3 border-b border-amber-500/20">
            <span className="text-8xl leading-none select-none">⚡</span>
            <h2 className="text-2xl font-bold text-amber-400">Fast! Noch ein Versuch ⚡</h2>
            {result.score_change > 0 && (
              <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-sm font-semibold">
                +{result.score_change / 10} Punkte
              </span>
            )}
          </div>
        )}

        {isFalsch && (
          <div className="bg-red-500/15 px-6 pt-8 pb-6 flex flex-col items-center gap-3 border-b border-red-500/20">
            <span className="text-8xl leading-none select-none">💡</span>
            <h2 className="text-2xl font-bold text-red-400">Noch nicht ganz...</h2>
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* what_was_good */}
          {result.what_was_good && (
            <div className={`text-sm ${isRichtig ? (dark ? "text-emerald-300" : "text-emerald-800") : isTeilweise ? (dark ? "text-amber-200" : "text-amber-900") : textBase}`}>
              <MarkdownMessage content={result.what_was_good} dark={dark} />
            </div>
          )}

          {/* what_went_wrong — shown for teilweise and falsch */}
          {(isTeilweise || isFalsch) && result.what_went_wrong && (
            <div className={`text-sm rounded-xl p-3 ${dark ? "bg-white/5" : "bg-gray-50"} ${textBase}`}>
              <MarkdownMessage content={result.what_went_wrong} dark={dark} />
            </div>
          )}

          {/* hint — shown for teilweise if present */}
          {isTeilweise && result.hint && (
            <div className={`rounded-xl p-3 border-l-4 ${dark ? "bg-blue-500/5 border-l-blue-500/50" : "bg-blue-50 border-l-blue-400"}`}>
              <p className={`text-xs font-semibold uppercase tracking-wider mb-1 ${dark ? "text-blue-400" : "text-blue-600"}`}>Hinweis</p>
              <div className={`text-sm ${textBase}`}>
                <MarkdownMessage content={result.hint} dark={dark} />
              </div>
            </div>
          )}

          {/* stdout / stderr — shown for falsch */}
          {isFalsch && (result.stdout || result.stderr) && (
            <pre className={`text-xs font-mono rounded-xl p-3 whitespace-pre-wrap ${dark ? "bg-black/30 text-gray-400" : "bg-gray-100 text-gray-600"}`}>
              {result.stdout}
              {result.stderr && <span className="text-red-400">{result.stderr}</span>}
            </pre>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-1">
            {isFalsch && result.redirect_to_tutor ? (
              <>
                <button
                  onClick={onGoToTutor}
                  className="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold bg-red-500 hover:bg-red-600 text-white transition-colors"
                >
                  Zum Tutor →
                </button>
                <button
                  onClick={onClose}
                  className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold border transition-colors ${
                    dark ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45]" : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  Hier bleiben
                </button>
              </>
            ) : isRichtig ? (
              <button
                onClick={onClose}
                className="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-emerald-500 hover:bg-emerald-600 text-white transition-colors"
              >
                Weiter →
              </button>
            ) : isTeilweise ? (
              <button
                onClick={onClose}
                className="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-white transition-colors"
              >
                Nochmal versuchen
              </button>
            ) : (
              <button
                onClick={onClose}
                className="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-red-500 hover:bg-red-600 text-white transition-colors"
              >
                Nochmal versuchen
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

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

  const [code, setCode] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<SubmitExerciseResponse | null>(null)
  const [showPopup, setShowPopup] = useState(false)
  const [pendingScore, setPendingScore] = useState<number | null>(null)
  const [hintLevel, setHintLevel] = useState(1)
  const [hint, setHint] = useState<string | null>(null)
  const [hintLoading, setHintLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function handleSubmit() {
    if (!code.trim() || submitting) return
    setSubmitting(true)
    setResult(null)
    setErr(null)
    try {
      const res = await submitExercise({ skill_key: skillKey, exercise_id: exercise.id, code }, token)
      setResult(res)
      setPendingScore(res.new_skill_score)
      setShowPopup(true)
      if (res.result === "falsch" && res.redirect_to_tutor) {
        localStorage.setItem("ki_tutor_exercise_redirect", JSON.stringify({
          code, analysis: res.analysis, exercise_title: exercise.title,
        }))
      }
    } catch {
      setErr("Abgabe fehlgeschlagen.")
    } finally {
      setSubmitting(false)
    }
  }

  function handleClosePopup() {
    setShowPopup(false)
    if (pendingScore !== null) {
      onScoreUpdate(pendingScore)
      setPendingScore(null)
    }
  }

  function handleGoToTutor() {
    router.push("/tutor")
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

            {showPopup && result && (
              <ResultPopup
                result={result}
                onClose={handleClosePopup}
                onGoToTutor={handleGoToTutor}
                dark={dark}
              />
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
        <div className="flex items-center gap-2 min-w-0">
          <h2 className={`text-base font-bold ${dark ? "text-white" : "text-gray-900"}`}>
            {skill.skill_label} — Übungen
          </h2>
          {skill.score >= 100 && (
            <button
              onClick={onStartSkillTest}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-sm font-bold bg-emerald-500 hover:bg-emerald-600 active:scale-[0.97] text-white transition-all shadow-md shadow-emerald-500/30"
            >
              🎯 Skill testen
            </button>
          )}
        </div>
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
