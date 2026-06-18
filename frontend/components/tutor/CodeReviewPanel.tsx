"use client"

import type { CodeReviewResult, CodeReviewIssue } from "@/types/tutor"

interface Props {
  result: CodeReviewResult
  dark: boolean
  onClose: () => void
}

const SEVERITY_STYLES = {
  error:   { dot: "bg-red-500",    text: "text-red-400",    badge: "bg-red-500/10 border-red-500/20",    label: "Fehler"    },
  warning: { dot: "bg-amber-500",  text: "text-amber-400",  badge: "bg-amber-500/10 border-amber-500/20", label: "Warnung"   },
  info:    { dot: "bg-blue-500",   text: "text-blue-400",   badge: "bg-blue-500/10 border-blue-500/20",   label: "Hinweis"   },
}

const SECTIONS = [
  { key: "syntax",         icon: "🔴", title: "Schritt 1 — Syntax",           step: "1/3" },
  { key: "style",          icon: "🟡", title: "Schritt 2 — Stil / PEP8",      step: "2/3" },
  { key: "best_practices", icon: "🔵", title: "Schritt 3 — Best Practices",   step: "3/3" },
] as const

function IssueRow({ issue, dark }: { issue: CodeReviewIssue; dark: boolean }) {
  const s = SEVERITY_STYLES[issue.severity] ?? SEVERITY_STYLES.info
  return (
    <div className={`flex items-start gap-2.5 px-3 py-2 rounded-lg border ${s.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${s.dot}`} />
      <div className="flex-1 min-w-0">
        <span className={`text-xs font-mono ${s.text}`}>Zeile {issue.line}</span>
        <span className={`ml-2 text-xs ${dark ? "text-gray-300" : "text-gray-700"}`}>{issue.message}</span>
      </div>
      <span className={`text-xs font-semibold shrink-0 ${s.text}`}>{s.label}</span>
    </div>
  )
}

function Section({
  icon, title, step, data, dark,
}: {
  icon: string; title: string; step: string
  data: { issues: CodeReviewIssue[]; summary: string }
  dark: boolean
}) {
  const sub = dark ? "text-gray-500" : "text-gray-400"
  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const sectionBg = dark ? "bg-[#060e1c]" : "bg-gray-50"
  const ok = data.issues.length === 0

  return (
    <div className={`rounded-xl border ${border} overflow-hidden`}>
      {/* Section header */}
      <div className={`flex items-center gap-2.5 px-4 py-2.5 ${sectionBg} border-b ${border}`}>
        <span className="text-base">{icon}</span>
        <div className="flex-1">
          <p className={`text-xs font-bold ${dark ? "text-white" : "text-gray-900"}`}>{title}</p>
          <p className={`text-xs ${sub}`}>{data.summary}</p>
        </div>
        <span className={`text-xs font-mono ${sub}`}>{step}</span>
        {ok && <span className="text-emerald-400 text-xs font-semibold">✓</span>}
      </div>
      {/* Issues */}
      {data.issues.length > 0 && (
        <div className="p-3 space-y-1.5">
          {data.issues.map((issue, i) => (
            <IssueRow key={i} issue={issue} dark={dark} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CodeReviewPanel({ result, dark, onClose }: Props) {
  const border = dark ? "border-[#1e2f45]" : "border-gray-200"
  const bg     = dark ? "bg-[#0a1628]"     : "bg-white"
  const sub    = dark ? "text-gray-500"    : "text-gray-400"

  const totalColor = result.total_issues === 0
    ? "text-emerald-400"
    : result.total_issues <= 3 ? "text-amber-400" : "text-red-400"

  return (
    <div className={`${bg} border-t ${border} flex flex-col`} style={{ maxHeight: "55%" }}>

      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${border} ${dark ? "bg-[#080f1e]" : "bg-gray-50"}`}>
        <div className="flex items-center gap-2">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            className={dark ? "text-violet-400" : "text-violet-600"}>
            <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          <span className={`text-xs font-bold ${dark ? "text-white" : "text-gray-900"}`}>Code Review</span>
          <span className={`text-xs font-mono font-bold ${totalColor}`}>
            {result.total_issues === 0 ? "Kein Problem" : `${result.total_issues} Problem${result.total_issues !== 1 ? "e" : ""}`}
          </span>
        </div>
        <button
          onClick={onClose}
          className={`text-xs ${sub} hover:${dark ? "text-white" : "text-gray-900"} transition-colors`}
        >
          ✕ Schließen
        </button>
      </div>

      {/* Sections */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {SECTIONS.map((s) => (
          <Section
            key={s.key}
            icon={s.icon}
            title={s.title}
            step={s.step}
            data={result[s.key]}
            dark={dark}
          />
        ))}
      </div>
    </div>
  )
}
