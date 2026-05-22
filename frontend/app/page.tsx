"use client"

import { useState } from "react"
import CodeEditor from "@/components/tutor/CodeEditor"
import TutorResult from "@/components/tutor/TutorResult"
import { useTutorAnalysis } from "@/hooks/useTutorAnalysis"

export default function Home() {
  const [dark, setDark] = useState(true)
  const { code, setCode, question, setQuestion, result, loading, error, analyze } = useTutorAnalysis()

  const bg = dark ? "min-h-screen bg-[#0a1628] text-white" : "min-h-screen bg-gray-50 text-gray-900"
  const card = dark
    ? "bg-[#111e30] border border-[#1e2f45] rounded-2xl p-6 shadow-xl"
    : "bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
  const labelCls = dark
    ? "block text-sm font-medium text-gray-300 mb-2"
    : "block text-sm font-medium text-gray-600 mb-2"
  const inputCls = dark
    ? "w-full rounded-xl border border-[#2d3f55] bg-[#0d1b2a] px-4 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    : "w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400"

  return (
    <div className={bg}>
      <div className="max-w-2xl mx-auto px-4 py-12">

        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h1 className={`text-2xl font-bold ${dark ? "text-white" : "text-gray-900"}`}>
              🤖 Python Tutor
            </h1>
            <p className={`text-sm mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
              Agentic AI — Phase 1
            </p>
          </div>
          <button
            onClick={() => setDark(!dark)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${dark
              ? "border-[#2d3f55] text-gray-300 hover:bg-[#1e2f45]"
              : "border-gray-200 text-gray-600 hover:bg-gray-100"}`}
          >
            {dark ? "☀ Hell" : "🌙 Dunkel"}
          </button>
        </div>

        {/* Input Card */}
        <div className={`${card} mb-6`}>
          <div className="mb-5">
            <label className={labelCls}>Dein Python-Code</label>
            <CodeEditor code={code} onChange={setCode} dark={dark} />
          </div>

          <div className="mb-5">
            <label className={labelCls}>Frage (optional)</label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="z.B. Warum funktioniert meine for-Schleife nicht?"
              className={inputCls}
            />
          </div>

          <button
            onClick={analyze}
            disabled={loading || !code.trim()}
            className="w-full py-3 rounded-xl font-semibold text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Analysiere..." : "Analysieren"}
          </button>
        </div>

        {/* Fehler */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Ergebnis */}
        {result && (
          <div className={card}>
            <TutorResult result={result} dark={dark} />
          </div>
        )}

      </div>
    </div>
  )
}
