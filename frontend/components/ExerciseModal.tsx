"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useTheme } from "@/context/ThemeContext"
import { useAuth } from "@/context/AuthContext"
import { useLang } from "@/context/LangContext"
import { getExercises, submitExercise, getExerciseHint } from "@/lib/api"
import type { SkillProgress, Exercise, SubmitExerciseResponse, HintResponse } from "@/types/tutor"

interface ExerciseModalProps {
  skill: SkillProgress
  onClose: () => void
  onSkillScoreUpdate: (skillKey: string, newScore: number) => void
  onStartSkillTest?: () => void
}

export default function ExerciseModal({ skill, onClose, onSkillScoreUpdate, onStartSkillTest }: ExerciseModalProps) {
  const { dark } = useTheme()
  const { t } = useLang()
  useAuth() // ensure we are inside an authenticated context
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""
  const router = useRouter()
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const [exercises, setExercises] = useState<Exercise[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Current exercise state
  const [code, setCode] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<SubmitExerciseResponse | null>(null)

  // Hint state
  const [hintLevel, setHintLevel] = useState(1)
  const [currentHint, setCurrentHint] = useState<string | null>(null)
  const [hintLoading, setHintLoading] = useState(false)

  const [loadTick, setLoadTick] = useState(0)

  useEffect(() => {
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [])

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    getExercises(skill.skill_key, token)
      .then((data) => { if (!cancelled) setExercises(data.exercises) })
      .catch(() => { if (!cancelled) setError(t("exercise.loadError")) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [skill.skill_key, loadTick])

  // Find the current exercise: first one that is unlocked and not locked
  const currentExercise = exercises.find((ex) => ex.is_unlocked && !ex.is_locked) ?? null
  // is_locked means score_granted=20 (fully completed), not "blocked by admin"
  const allDone = exercises.length > 0 && exercises.every((ex) => ex.is_locked)
  const totalExercises = exercises.length
  const currentIndex = currentExercise
    ? exercises.findIndex((ex) => ex.id === currentExercise.id) + 1
    : totalExercises

  async function handleSubmit() {
    if (!currentExercise || !code.trim() || submitting) return
    setSubmitting(true)
    setResult(null)
    try {
      const res = await submitExercise(
        { skill_key: skill.skill_key, exercise_id: currentExercise.id, code },
        token,
      )
      setResult(res)
      onSkillScoreUpdate(skill.skill_key, res.new_skill_score)

      if (res.result === "richtig") {
        // After correct answer, reload exercises to advance
        timerRef.current = setTimeout(() => {
          setResult(null)
          setCode("")
          setCurrentHint(null)
          setHintLevel(1)
          setLoadTick((t) => t + 1)
        }, 1500)
      } else if (res.result === "falsch" && res.redirect_to_tutor) {
        // Save redirect data and navigate to tutor
        localStorage.setItem(
          "ki_tutor_exercise_redirect",
          JSON.stringify({
            code,
            analysis: res.analysis,
            exercise_title: currentExercise.title,
          }),
        )
        timerRef.current = setTimeout(() => {
          router.push("/tutor")
        }, 1200)
      }
    } catch {
      setError(t("exercise.submitError"))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleHint() {
    if (!currentExercise || hintLevel > 3 || hintLoading) return
    setHintLoading(true)
    try {
      const res: HintResponse = await getExerciseHint(
        { skill_key: skill.skill_key, exercise_id: currentExercise.id, code, hint_level: hintLevel },
        token,
      )
      setCurrentHint(res.hint)
      setHintLevel((prev) => prev + 1)
    } catch {
      setError(t("exercise.hintError"))
    } finally {
      setHintLoading(false)
    }
  }

  function getHintButtonLabel(): string {
    if (hintLevel > 3) return t("exercise.hintNone")
    return t("exercise.hintLabel", { level: hintLevel })
  }

  // Backdrop click handler
  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  // Key handler for Escape
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", handleKey)
    return () => document.removeEventListener("keydown", handleKey)
  }, [onClose])

  const overlayClass = "fixed inset-0 z-50 flex items-center justify-center p-4 animate-[fadeIn_200ms_ease-out]"
  const backdropClass = dark
    ? "bg-black/70 backdrop-blur-sm"
    : "bg-black/40 backdrop-blur-sm"

  const modalClass = dark
    ? "bg-[#0d1929] border border-[#1e2f45] text-white rounded-2xl shadow-2xl shadow-black/40"
    : "bg-white border border-gray-200 text-gray-900 rounded-2xl shadow-2xl shadow-black/10"

  const codeAreaClass = dark
    ? "w-full min-h-[200px] bg-[#1e1e1e] text-gray-100 border border-[#2d3f55] rounded-xl p-4 font-mono text-sm resize-y focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all placeholder-gray-600"
    : "w-full min-h-[200px] bg-gray-900 text-gray-100 border border-gray-300 rounded-xl p-4 font-mono text-sm resize-y focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all placeholder-gray-500"

  return (
    <div className={`${overlayClass} ${backdropClass}`} onClick={handleBackdropClick}>
      <div
        className={`${modalClass} w-full max-w-[700px] max-h-[90vh] overflow-y-auto animate-[slideUp_250ms_ease-out]`}
      >
        {/* Header */}
        <div className={`sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b ${dark ? "border-[#1e2f45] bg-[#0d1929]" : "border-gray-100 bg-white"} rounded-t-2xl`}>
          <div>
            <h2 className={`text-base font-semibold ${dark ? "text-white" : "text-gray-900"}`}>
              {skill.skill_label}
            </h2>
            {!allDone && currentExercise && (
              <p className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                {t("exercise.exerciseOf", { current: currentIndex, total: totalExercises })}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${dark ? "hover:bg-[#1e2f45] text-gray-400 hover:text-white" : "hover:bg-gray-100 text-gray-400 hover:text-gray-700"}`}
            aria-label={t("exercise.close")}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className={`w-6 h-6 border-2 border-t-transparent rounded-full animate-spin ${dark ? "border-blue-400" : "border-blue-600"}`} />
            </div>
          )}

          {error && (
            <div className={`px-4 py-3 rounded-xl text-sm ${dark ? "bg-red-500/10 border border-red-500/20 text-red-400" : "bg-red-50 border border-red-200 text-red-600"}`}>
              {error}
            </div>
          )}

          {/* All exercises completed */}
          {!loading && allDone && (
            <div className="text-center py-8 space-y-4">
              <div className="text-4xl">&#127881;</div>
              <h3 className={`text-lg font-semibold ${dark ? "text-white" : "text-gray-900"}`}>
                {t("exercise.allDone")}
              </h3>
              <p className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>
                {t("exercise.currentScore", { score: skill.score })}
              </p>
              <button
                onClick={() => {
                  if (onStartSkillTest) onStartSkillTest()
                }}
                className="mt-4 px-6 py-2.5 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                {t("exercise.startSkillTest")}
              </button>
            </div>
          )}

          {/* Current exercise */}
          {!loading && !allDone && currentExercise && (
            <>
              {/* Exercise title and description */}
              <div>
                <h3 className={`text-base font-semibold mb-2 ${dark ? "text-gray-100" : "text-gray-800"}`}>
                  {currentExercise.title}
                </h3>
                <p className={`text-sm leading-relaxed ${dark ? "text-gray-400" : "text-gray-600"}`}>
                  {currentExercise.description}
                </p>
              </div>

              {/* Code editor */}
              <div>
                <label className={`block text-xs font-medium uppercase tracking-wider mb-2 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                  {t("exercise.yourCode")}
                </label>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className={codeAreaClass}
                  rows={8}
                  placeholder={t("exercise.codePlaceholder")}
                  spellCheck={false}
                />
              </div>

              {/* Hint display */}
              {currentHint && (
                <div className={`rounded-xl p-4 border-s-4 ${dark ? "bg-blue-500/5 border-s-blue-500/50 text-blue-200" : "bg-blue-50 border-s-blue-500 text-blue-800"}`}>
                  <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${dark ? "text-blue-400" : "text-blue-600"}`}>
                    {t("exercise.hintLabel", { level: hintLevel - 1 })}
                  </p>
                  <p className="text-sm leading-relaxed">{currentHint}</p>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center justify-between gap-3">
                <button
                  onClick={handleHint}
                  disabled={hintLevel > 3 || hintLoading}
                  className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${dark
                    ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45] hover:text-white"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  {hintLoading ? t("exercise.hintLoading") : getHintButtonLabel()}
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!code.trim() || submitting}
                  className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting ? t("exercise.submitting") : t("exercise.submit")}
                </button>
              </div>

              {/* Result display */}
              {result && (
                <div className="space-y-3 animate-[fadeIn_300ms_ease-out]">
                  {result.result === "richtig" && (
                    <div className={`rounded-xl p-4 border-s-4 ${dark ? "bg-emerald-500/10 border-s-emerald-500 text-emerald-300" : "bg-emerald-50 border-s-emerald-500 text-emerald-800"}`}>
                      <p className="font-semibold text-sm mb-1">&#10003; {t("exercise.correct", { points: result.score_change / 10 })}</p>
                      {result.what_was_good && (
                        <p className={`text-sm ${dark ? "text-emerald-200/80" : "text-emerald-700"}`}>{result.what_was_good}</p>
                      )}
                    </div>
                  )}

                  {result.result === "teilweise" && (
                    <div className={`rounded-xl p-4 border-s-4 ${dark ? "bg-amber-500/10 border-s-amber-500 text-amber-300" : "bg-amber-50 border-s-amber-500 text-amber-800"}`}>
                      <p className="font-semibold text-sm mb-1">&#9684; {t("exercise.partial", { points: result.score_change / 10 })}</p>
                      {result.what_was_good && (
                        <p className={`text-sm mb-2 ${dark ? "text-amber-200/80" : "text-amber-700"}`}>{result.what_was_good}</p>
                      )}
                      {result.what_went_wrong && (
                        <p className={`text-sm ${dark ? "text-amber-300/70" : "text-amber-600"}`}>{result.what_went_wrong}</p>
                      )}
                    </div>
                  )}

                  {result.result === "falsch" && (
                    <div className={`rounded-xl p-4 border-s-4 ${dark ? "bg-red-500/10 border-s-red-500 text-red-300" : "bg-red-50 border-s-red-500 text-red-800"}`}>
                      <p className="font-semibold text-sm mb-1">&#10007; {t("exercise.wrong")}</p>
                      {result.what_went_wrong && (
                        <p className={`text-sm ${dark ? "text-red-200/80" : "text-red-700"}`}>{result.what_went_wrong}</p>
                      )}
                      {result.redirect_to_tutor ? (
                        <p className={`text-xs mt-2 ${dark ? "text-red-400/60" : "text-red-500"}`}>
                          {t("exercise.redirecting")}
                        </p>
                      ) : (
                        <p className={`text-xs mt-2 ${dark ? "text-red-400/60" : "text-red-500"}`}>
                          {t("exercise.tryAgain")}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Stdout/Stderr output */}
                  {(result.stdout || result.stderr) && (
                    <div className={`rounded-xl p-3 font-mono text-xs ${dark ? "bg-[#1e1e1e] border border-[#2d3f55]" : "bg-gray-900 border border-gray-300"}`}>
                      {result.stdout && (
                        <pre className="text-gray-300 whitespace-pre-wrap">{result.stdout}</pre>
                      )}
                      {result.stderr && (
                        <pre className="text-red-400 whitespace-pre-wrap">{result.stderr}</pre>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Keyframe animations */}
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
