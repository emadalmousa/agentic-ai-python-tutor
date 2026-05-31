"use client"

import { useState, useEffect } from "react"
import { useTheme } from "@/context/ThemeContext"
import { useAuth } from "@/context/AuthContext"
import { generateLevelTest, submitLevelTest } from "@/lib/api"
import type { LevelKey, LevelTestGenerateResponse, LevelTestResult } from "@/types/tutor"
import CodeEditor from "@/components/tutor/CodeEditor"

const LEVEL_LABELS: Record<LevelKey, string> = {
  beginner:     "Anfänger",
  intermediate: "Fortgeschritten",
  advanced:     "Profi",
}

const STEP_LABELS = ["Multiple Choice", "Code-Lesen", "Mini-Aufgabe"] as const
type Step = 1 | 2 | 3

interface Props {
  level: LevelKey
  onClose: () => void
  onTestResult?: (passed: boolean) => void
}

function ScoreBox({ label, score, max, dark }: { label: string; score: number; max: number; dark: boolean }) {
  const pct = Math.round((score / max) * 100)
  const color = pct >= 70 ? "text-emerald-500" : pct >= 40 ? "text-amber-500" : "text-red-500"
  return (
    <div className={`text-center rounded-xl p-3 border ${dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"}`}>
      <div className={`text-lg font-bold ${color}`}>{score}/{max}</div>
      <div className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>{label}</div>
    </div>
  )
}

export default function LevelTestModal({ level, onClose, onTestResult }: Props) {
  const { dark } = useTheme()
  useAuth()
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""

  const [testData, setTestData] = useState<LevelTestGenerateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [step, setStep] = useState<Step>(1)
  const [mcAnswers, setMcAnswers] = useState<Record<string, string>>({})
  const [codeReadingAnswer, setCodeReadingAnswer] = useState("")
  const [miniTaskCode, setMiniTaskCode] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<LevelTestResult | null>(null)

  useEffect(() => {
    generateLevelTest(level, token)
      .then((data) => setTestData(data))
      .catch(() => setError("Level-Test konnte nicht generiert werden."))
      .finally(() => setLoading(false))
  }, [])

  async function handleSubmit() {
    if (!testData || submitting) return
    setSubmitting(true)
    try {
      const res = await submitLevelTest({
        test_session_id: testData.test_session_id,
        level,
        mc_answers: mcAnswers,
        code_reading_answer: codeReadingAnswer,
        mini_task_code: miniTaskCode,
      }, token)
      setResult(res)
      onTestResult?.(res.passed)
    } catch {
      setError("Abgabe fehlgeschlagen.")
    } finally {
      setSubmitting(false)
    }
  }

  function handleRetry() {
    setResult(null)
    setStep(1)
    setMcAnswers({})
    setCodeReadingAnswer("")
    setMiniTaskCode("")
    setLoading(true)
    generateLevelTest(level, token)
      .then((data) => setTestData(data))
      .catch(() => setError("Fehler beim Neuladen."))
      .finally(() => setLoading(false))
  }

  const card = dark ? "bg-[#0d1929] border-[#1e2f45]" : "bg-white border-gray-200"
  const inputCls = dark
    ? "w-full bg-[#0a1525] border border-[#1e2f45] text-white placeholder-gray-500 rounded-xl p-3 text-sm focus:outline-none focus:border-blue-500/60"
    : "w-full bg-white border border-gray-300 text-gray-900 placeholder-gray-400 rounded-xl p-3 text-sm focus:outline-none focus:border-blue-500"

  return (
    <div className={`flex-1 overflow-y-auto p-5 ${dark ? "bg-[#060e1c]" : "bg-gray-50"}`}>
      <div className={`rounded-2xl border overflow-hidden ${card}`}>

        {/* Header */}
        <div className={`px-6 py-4 border-b flex items-center justify-between ${dark ? "border-[#1e2f45] bg-[#0d1929]" : "border-gray-100 bg-white"}`}>
          <div>
            <h2 className={`text-base font-bold ${dark ? "text-white" : "text-gray-900"}`}>
              Level-Test: {LEVEL_LABELS[level]}
            </h2>
            {!result && !loading && (
              <p className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                Schritt {step} von 3 — {STEP_LABELS[step - 1]}
              </p>
            )}
          </div>
          <button onClick={onClose}
            className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${dark ? "hover:bg-[#1e2f45] text-gray-400 hover:text-white" : "hover:bg-gray-100 text-gray-400 hover:text-gray-700"}`}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>

        {/* Progress bar */}
        {!result && !loading && (
          <div className={`flex gap-1.5 px-6 pt-3 ${dark ? "bg-[#0d1929]" : "bg-white"}`}>
            {[1, 2, 3].map((s) => (
              <div key={s} className={`h-1.5 flex-1 rounded-full transition-all ${s <= step ? "bg-blue-500" : dark ? "bg-[#1e2f45]" : "bg-gray-200"}`} />
            ))}
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-5 space-y-5">

          {loading && (
            <div className="flex flex-col items-center py-12 gap-3">
              <div className={`w-6 h-6 border-2 border-t-transparent rounded-full animate-spin ${dark ? "border-blue-400" : "border-blue-600"}`} />
              <p className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>Level-Test wird generiert...</p>
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          {/* Result */}
          {result && (
            <div className="space-y-5">
              <div className="text-center py-4">
                <div className={`text-5xl font-bold mb-2 ${result.passed ? "text-emerald-500" : "text-red-500"}`}>
                  {result.total_score}%
                </div>
                <p className={`text-lg font-semibold ${result.passed ? (dark ? "text-emerald-400" : "text-emerald-600") : (dark ? "text-red-400" : "text-red-600")}`}>
                  {result.passed ? "Bestanden! 🎓" : "Nicht bestanden"}
                </p>
                <p className={`text-sm mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                  {result.passed ? "Glückwunsch! Du hast dieses Level abgeschlossen." : "Versuch es nochmal — du schaffst das!"}
                </p>
              </div>

              <div className={`rounded-xl border p-4 ${dark ? "border-[#1e2f45] bg-[#0a1525]" : "border-gray-200 bg-gray-50"}`}>
                <p className={`text-xs font-medium uppercase tracking-wider mb-3 ${dark ? "text-gray-500" : "text-gray-400"}`}>Ergebnisse</p>
                <div className="grid grid-cols-3 gap-3">
                  <ScoreBox label="MC" score={result.mc_score} max={30} dark={dark} />
                  <ScoreBox label="Code-Lesen" score={result.code_reading_score} max={30} dark={dark} />
                  <ScoreBox label="Mini-Aufgabe" score={result.mini_task_score} max={40} dark={dark} />
                </div>
              </div>

              {!result.passed && result.per_question_feedback.length > 0 && (
                <div className="space-y-2">
                  {result.per_question_feedback.map((fb, i) => (
                    <div key={i} className={`rounded-lg p-3 text-sm border-l-4 ${fb.correct
                      ? dark ? "bg-emerald-500/5 border-l-emerald-500/50 text-emerald-300" : "bg-emerald-50 border-l-emerald-500 text-emerald-800"
                      : dark ? "bg-red-500/5 border-l-red-500/50 text-red-300" : "bg-red-50 border-l-red-500 text-red-800"}`}>
                      <span className="font-medium">{fb.question_type}{fb.index !== undefined ? ` ${fb.index + 1}` : ""}:</span>{" "}{fb.explanation}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex justify-center gap-3 pt-2">
                {!result.passed && (
                  <button onClick={handleRetry}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors">
                    Nochmal versuchen
                  </button>
                )}
                <button onClick={onClose}
                  className={`px-5 py-2 rounded-xl text-sm font-medium border transition-colors ${dark ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45]" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
                  Schließen
                </button>
              </div>
            </div>
          )}

          {/* Steps */}
          {!loading && !result && testData && (
            <>
              {/* Step 1: MC */}
              {step === 1 && (
                <div className="space-y-4">
                  {testData.test_data.multiple_choice.map((q, idx) => (
                    <div key={idx} className={`rounded-xl border p-4 space-y-3 ${dark ? "border-[#1e2f45] bg-[#0a1525]" : "border-gray-100 bg-gray-50"}`}>
                      <p className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-700"}`}>{idx + 1}. {q.question}</p>
                      <div className="space-y-2">
                        {(["A", "B", "C", "D"] as const).map((opt) => {
                          const selected = mcAnswers[String(idx)] === opt
                          return (
                            <label key={opt} className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-all ${selected
                              ? dark ? "border-blue-500/50 bg-blue-500/10" : "border-blue-500 bg-blue-50"
                              : dark ? "border-[#1e2f45] hover:border-[#2d3f55]" : "border-gray-200 hover:border-gray-300 bg-white"}`}>
                              <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${selected ? "border-blue-500 bg-blue-500" : dark ? "border-gray-600" : "border-gray-300"}`}>
                                {selected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                              </span>
                              <span className={`text-sm ${dark ? "text-gray-300" : "text-gray-700"}`}>
                                <span className="font-medium">{opt}.</span> {q.options[opt]}
                              </span>
                              <input type="radio" name={`mc-${idx}`} value={opt} checked={selected}
                                onChange={() => setMcAnswers((p) => ({ ...p, [String(idx)]: opt }))} className="sr-only" />
                            </label>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Step 2: Code Reading */}
              {step === 2 && (
                <div className="space-y-4">
                  <p className={`text-sm font-semibold ${dark ? "text-gray-200" : "text-gray-700"}`}>Lies den Code und beantworte die Frage:</p>
                  <pre className={`rounded-xl p-4 font-mono text-sm overflow-x-auto ${dark ? "bg-[#1e1e1e] text-gray-200 border border-[#2d3f55]" : "bg-gray-900 text-gray-200"}`}>
                    {testData.test_data.code_reading.code}
                  </pre>
                  <p className={`text-sm font-medium ${dark ? "text-gray-300" : "text-gray-700"}`}>{testData.test_data.code_reading.question}</p>
                  <textarea value={codeReadingAnswer} onChange={(e) => setCodeReadingAnswer(e.target.value)}
                    className={inputCls} rows={3} placeholder="Deine Antwort..." />
                </div>
              )}

              {/* Step 3: Mini Task */}
              {step === 3 && (
                <div className="space-y-4">
                  <p className={`text-sm font-semibold ${dark ? "text-gray-200" : "text-gray-700"}`}>Mini-Aufgabe</p>
                  <p className={`text-sm ${dark ? "text-gray-400" : "text-gray-600"}`}>{testData.test_data.mini_task.description}</p>
                  {testData.test_data.mini_task.expected_output && (
                    <div className={`rounded-xl p-3 ${dark ? "bg-[#0a1525] border border-[#1e2f45]" : "bg-gray-50 border border-gray-200"}`}>
                      <p className={`text-xs uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>Erwartete Ausgabe</p>
                      <pre className={`font-mono text-sm ${dark ? "text-emerald-400" : "text-emerald-700"}`}>{testData.test_data.mini_task.expected_output}</pre>
                    </div>
                  )}
                  <CodeEditor code={miniTaskCode} onChange={setMiniTaskCode} dark={dark} />
                </div>
              )}

              {/* Navigation */}
              <div className="flex items-center justify-between pt-2">
                <button onClick={() => setStep((s) => (s > 1 ? (s - 1) as Step : s))} disabled={step === 1}
                  className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors disabled:opacity-30 ${dark ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45]" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
                  Zurück
                </button>
                {step < 3 ? (
                  <button onClick={() => setStep((s) => (s < 3 ? (s + 1) as Step : s))}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors">
                    Weiter
                  </button>
                ) : (
                  <button onClick={handleSubmit} disabled={submitting}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 transition-colors">
                    {submitting ? "Prüfe..." : "Absenden"}
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
