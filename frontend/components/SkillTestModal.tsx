"use client"

import { useState, useEffect } from "react"
import { useTheme } from "@/context/ThemeContext"
import { useAuth } from "@/context/AuthContext"
import { useLang } from "@/context/LangContext"
import { generateSkillTest, submitSkillTest } from "@/lib/api"
import type { SkillProgress, SkillTestGenerateResponse, SkillTestResult } from "@/types/tutor"

interface SkillTestModalProps {
  skill: SkillProgress
  onClose: () => void
  onTestPassed: (skillKey: string) => void
  inline?: boolean
}

type Step = 1 | 2 | 3

export default function SkillTestModal({ skill, onClose, onTestPassed, inline = false }: SkillTestModalProps) {
  const { dark } = useTheme()
  const { t } = useLang()
  useAuth() // ensure we are inside an authenticated context
  const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""

  const STEP_LABELS = [t("skillTest.stepMC"), t("skillTest.stepCodeReading"), t("skillTest.stepMiniTask")] as const

  const [testData, setTestData] = useState<SkillTestGenerateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Wizard state
  const [step, setStep] = useState<Step>(1)

  // MC answers: keyed by question index "0", "1", "2"
  const [mcAnswers, setMcAnswers] = useState<Record<string, string>>({})

  // Code reading answer
  const [codeReadingAnswer, setCodeReadingAnswer] = useState("")

  // Mini task code
  const [miniTaskCode, setMiniTaskCode] = useState("")

  // Submission state
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<SkillTestResult | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await generateSkillTest(skill.skill_key, token)
        setTestData(data)
      } catch {
        setError(t("skillTest.generateError"))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [skill.skill_key])

  // Escape key
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", handleKey)
    return () => document.removeEventListener("keydown", handleKey)
  }, [onClose])

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  async function handleSubmitTest() {
    if (!testData || submitting) return
    setSubmitting(true)
    try {
      const res = await submitSkillTest(
        {
          skill_key: skill.skill_key,
          test_session_id: testData.test_session_id,
          mc_answers: mcAnswers,
          code_reading_answer: codeReadingAnswer,
          mini_task_code: miniTaskCode,
        },
        token,
      )
      setResult(res)
      if (res.passed) {
        onTestPassed(skill.skill_key)
      }
    } catch {
      setError(t("skillTest.submitError"))
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
    setError(null)
    generateSkillTest(skill.skill_key, token)
      .then((data) => setTestData(data))
      .catch(() => setError(t("skillTest.generateError")))
      .finally(() => setLoading(false))
  }

  const overlayClass = "fixed inset-0 z-50 flex items-center justify-center p-4 animate-[fadeIn_200ms_ease-out]"
  const backdropClass = dark ? "bg-black/70 backdrop-blur-sm" : "bg-black/40 backdrop-blur-sm"
  const modalClass = dark
    ? "bg-[#0d1929] border border-[#1e2f45] text-white rounded-2xl shadow-2xl shadow-black/40"
    : "bg-white border border-gray-200 text-gray-900 rounded-2xl shadow-2xl shadow-black/10"

  const codeAreaClass = dark
    ? "w-full min-h-[160px] bg-[#1e1e1e] text-gray-100 border border-[#2d3f55] rounded-xl p-4 font-mono text-sm resize-y focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all placeholder-gray-600"
    : "w-full min-h-[160px] bg-gray-900 text-gray-100 border border-gray-300 rounded-xl p-4 font-mono text-sm resize-y focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all placeholder-gray-500"

  const inputClass = dark
    ? "w-full bg-[#0a1525] border border-[#1e2f45] text-white placeholder-gray-500 rounded-xl p-3 text-sm focus:outline-none focus:border-blue-500/60 transition-colors"
    : "w-full bg-white border border-gray-300 text-gray-900 placeholder-gray-400 rounded-xl p-3 text-sm focus:outline-none focus:border-blue-500 transition-colors"

  const content = (
    <>
        {/* Header */}
        <div className={`sticky top-0 z-10 px-6 py-4 border-b ${dark ? "border-[#1e2f45] bg-[#0d1929]" : "border-gray-100 bg-white"} rounded-t-2xl`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className={`text-base font-semibold ${dark ? "text-white" : "text-gray-900"}`}>
                {t("skillTest.title", { label: skill.skill_label })}
              </h2>
              {!result && !loading && (
                <p className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                  {t("skillTest.step", { step })} &mdash; {STEP_LABELS[step - 1]}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${dark ? "hover:bg-[#1e2f45] text-gray-400 hover:text-white" : "hover:bg-gray-100 text-gray-400 hover:text-gray-700"}`}
              aria-label={t("skillTest.close")}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>

          {/* Progress bar */}
          {!result && !loading && (
            <div className="flex gap-1.5 mt-3">
              {[1, 2, 3].map((s) => (
                <div
                  key={s}
                  className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                    s <= step
                      ? "bg-blue-500"
                      : dark
                        ? "bg-[#1e2f45]"
                        : "bg-gray-200"
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className={`w-6 h-6 border-2 border-t-transparent rounded-full animate-spin ${dark ? "border-blue-400" : "border-blue-600"}`} />
              <p className={`text-sm ${dark ? "text-gray-400" : "text-gray-500"}`}>{t("skillTest.generating")}</p>
            </div>
          )}

          {error && (
            <div className={`px-4 py-3 rounded-xl text-sm ${dark ? "bg-red-500/10 border border-red-500/20 text-red-400" : "bg-red-50 border border-red-200 text-red-600"}`}>
              {error}
            </div>
          )}

          {/* Result screen */}
          {result && (
            <div className="space-y-5 animate-[fadeIn_300ms_ease-out]">
              {/* Score display */}
              <div className="text-center py-4">
                <div className={`text-5xl font-bold mb-2 ${result.passed ? "text-emerald-500" : "text-red-500"}`}>
                  {result.total_score}%
                </div>
                <p className={`text-lg font-semibold ${result.passed ? (dark ? "text-emerald-400" : "text-emerald-600") : (dark ? "text-red-400" : "text-red-600")}`}>
                  {result.passed ? t("skillTest.passed") : t("skillTest.failed")}
                </p>
                {result.passed && (
                  <p className={`text-sm mt-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                    {t("skillTest.nextUnlocked")}
                  </p>
                )}
              </div>

              {/* Score breakdown */}
              <div className={`rounded-xl border p-4 space-y-3 ${dark ? "border-[#1e2f45] bg-[#0a1525]" : "border-gray-200 bg-gray-50"}`}>
                <h4 className={`text-xs font-medium uppercase tracking-wider ${dark ? "text-gray-500" : "text-gray-400"}`}>
                  {t("skillTest.detailResults")}
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <ScoreBox label="MC" score={result.mc_score} max={30} dark={dark} />
                  <ScoreBox label={t("skillTest.stepCodeReading")} score={result.code_reading_score} max={30} dark={dark} />
                  <ScoreBox label={t("skillTest.stepMiniTask")} score={result.mini_task_score} max={40} dark={dark} />
                </div>
              </div>

              {/* Per-question feedback (only on failure) */}
              {!result.passed && result.per_question_feedback.length > 0 && (
                <div className="space-y-2">
                  <h4 className={`text-xs font-medium uppercase tracking-wider ${dark ? "text-gray-500" : "text-gray-400"}`}>
                    {t("skillTest.feedback")}
                  </h4>
                  {result.per_question_feedback.map((fb, i) => (
                    <div
                      key={i}
                      className={`rounded-lg p-3 text-sm border-s-4 ${
                        fb.correct
                          ? dark ? "bg-emerald-500/5 border-s-emerald-500/50 text-emerald-300" : "bg-emerald-50 border-s-emerald-500 text-emerald-800"
                          : dark ? "bg-red-500/5 border-s-red-500/50 text-red-300" : "bg-red-50 border-s-red-500 text-red-800"
                      }`}
                    >
                      <span className="font-medium">
                        {fb.question_type}{fb.index !== undefined ? ` ${fb.index + 1}` : ""}:
                      </span>{" "}
                      {fb.explanation}
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-center gap-3 pt-2">
                {!result.passed && (
                  <button
                    onClick={handleRetry}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    {t("skillTest.retry")}
                  </button>
                )}
                <button
                  onClick={onClose}
                  className={`px-5 py-2 rounded-xl text-sm font-medium border transition-colors ${dark
                    ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45]"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {t("skillTest.close")}
                </button>
              </div>
            </div>
          )}

          {/* Step content */}
          {!loading && !result && testData && (
            <>
              {/* Step 1: Multiple Choice */}
              {step === 1 && (
                <div className="space-y-5">
                  {testData.test_data.multiple_choice.map((q, idx) => (
                    <div key={idx} className={`rounded-xl border p-4 space-y-3 ${dark ? "border-[#1e2f45] bg-[#0a1525]" : "border-gray-100 bg-gray-50"}`}>
                      <p className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-700"}`}>
                        {idx + 1}. {q.question}
                      </p>
                      <div className="space-y-2">
                        {(["A", "B", "C", "D"] as const).map((opt) => {
                          const selected = mcAnswers[String(idx)] === opt
                          return (
                            <label
                              key={opt}
                              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-all ${
                                selected
                                  ? dark
                                    ? "border-blue-500/50 bg-blue-500/10"
                                    : "border-blue-500 bg-blue-50"
                                  : dark
                                    ? "border-[#1e2f45] hover:border-[#2d3f55] bg-transparent"
                                    : "border-gray-200 hover:border-gray-300 bg-white"
                              }`}
                            >
                              <span
                                className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                                  selected
                                    ? "border-blue-500 bg-blue-500"
                                    : dark
                                      ? "border-gray-600"
                                      : "border-gray-300"
                                }`}
                              >
                                {selected && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                                )}
                              </span>
                              <span className={`text-sm ${dark ? "text-gray-300" : "text-gray-700"}`}>
                                <span className="font-medium">{opt}.</span> {q.options[opt]}
                              </span>
                              <input
                                type="radio"
                                name={`mc-${idx}`}
                                value={opt}
                                checked={selected}
                                onChange={() => setMcAnswers((prev) => ({ ...prev, [String(idx)]: opt }))}
                                className="sr-only"
                              />
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
                  <div>
                    <h3 className={`text-sm font-semibold mb-2 ${dark ? "text-gray-200" : "text-gray-700"}`}>
                      {t("skillTest.codeReadingInstruction")}
                    </h3>
                    <pre className={`rounded-xl p-4 font-mono text-sm overflow-x-auto ${dark ? "bg-[#1e1e1e] text-gray-200 border border-[#2d3f55]" : "bg-gray-900 text-gray-200 border border-gray-300"}`}>
                      {testData.test_data.code_reading.code}
                    </pre>
                  </div>
                  <div>
                    <p className={`text-sm font-medium mb-2 ${dark ? "text-gray-300" : "text-gray-700"}`}>
                      {testData.test_data.code_reading.question}
                    </p>
                    <textarea
                      value={codeReadingAnswer}
                      onChange={(e) => setCodeReadingAnswer(e.target.value)}
                      className={inputClass}
                      rows={4}
                      placeholder={t("skillTest.yourAnswer")}
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Mini Task */}
              {step === 3 && (
                <div className="space-y-4">
                  <div>
                    <h3 className={`text-sm font-semibold mb-2 ${dark ? "text-gray-200" : "text-gray-700"}`}>
                      {t("skillTest.miniTaskTitle")}
                    </h3>
                    <p className={`text-sm leading-relaxed ${dark ? "text-gray-400" : "text-gray-600"}`}>
                      {testData.test_data.mini_task.description}
                    </p>
                  </div>
                  {testData.test_data.mini_task.expected_output && (
                    <div className={`rounded-xl p-3 ${dark ? "bg-[#0a1525] border border-[#1e2f45]" : "bg-gray-50 border border-gray-200"}`}>
                      <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                        {t("skillTest.expectedOutput")}
                      </p>
                      <pre className={`font-mono text-sm ${dark ? "text-emerald-400" : "text-emerald-700"}`}>
                        {testData.test_data.mini_task.expected_output}
                      </pre>
                    </div>
                  )}
                  <div>
                    <label className={`block text-xs font-medium uppercase tracking-wider mb-2 ${dark ? "text-gray-500" : "text-gray-400"}`}>
                      {t("skillTest.yourCode")}
                    </label>
                    <textarea
                      value={miniTaskCode}
                      onChange={(e) => setMiniTaskCode(e.target.value)}
                      className={codeAreaClass}
                      rows={8}
                      placeholder={t("skillTest.codePlaceholder")}
                      spellCheck={false}
                    />
                  </div>
                </div>
              )}

              {/* Navigation buttons */}
              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => setStep((s) => (s > 1 ? (s - 1) as Step : s))}
                  disabled={step === 1}
                  className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${dark
                    ? "border-[#1e2f45] text-gray-300 hover:bg-[#1e2f45]"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {t("skillTest.back")}
                </button>
                {step < 3 ? (
                  <button
                    onClick={() => setStep((s) => (s < 3 ? (s + 1) as Step : s))}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    {t("skillTest.next")}
                  </button>
                ) : (
                  <button
                    onClick={handleSubmitTest}
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {submitting ? t("skillTest.submitting") : t("skillTest.submitBtn")}
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </>
  )

  if (inline) {
    return (
      <div className={`flex-1 overflow-y-auto p-5 ${dark ? "bg-[#060e1c]" : "bg-gray-50"}`}>
        <div className={`rounded-2xl overflow-hidden ${modalClass}`}>
          {content}
        </div>
      </div>
    )
  }

  return (
    <div className={`${overlayClass} ${backdropClass}`} onClick={handleBackdropClick}>
      <div className={`${modalClass} w-full max-w-[700px] max-h-[90vh] overflow-y-auto animate-[slideUp_250ms_ease-out]`}>
        {content}
      </div>
    </div>
  )
}

function ScoreBox({ label, score, max, dark }: { label: string; score: number; max: number; dark: boolean }) {
  const percent = Math.round((score / max) * 100)
  const color = percent >= 70 ? "text-emerald-500" : percent >= 40 ? "text-amber-500" : "text-red-500"
  return (
    <div className={`text-center rounded-lg p-3 ${dark ? "bg-[#0d1929] border border-[#1e2f45]" : "bg-white border border-gray-200"}`}>
      <div className={`text-lg font-bold ${color}`}>{score}/{max}</div>
      <div className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>{label}</div>
    </div>
  )
}
