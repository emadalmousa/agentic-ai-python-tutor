"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import CourseTransition from "@/components/CourseTransition"

const LEVEL_LABEL: Record<string, string> = {
  "Anfänger":        "Anfänger",
  "Mittel":          "Fortgeschritten",
  "Fortgeschritten": "Experte",
}

const LEVEL_COLOR: Record<string, string> = {
  "Anfänger":        "text-emerald-400",
  "Mittel":          "text-blue-400",
  "Fortgeschritten": "text-violet-400",
}

function ArrowRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
    </svg>
  )
}

function TutorIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function CourseIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  )
}

export default function DashboardView() {
  const { user, isAuthenticated } = useAuth()
  const { dark } = useTheme()
  const router = useRouter()
  const [showTransition, setShowTransition] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  if (showTransition) {
    return <CourseTransition onDone={() => setShowTransition(false)} />
  }

  const firstName = user?.name?.split(" ")[0] ?? "Gast"
  const levelLabel = LEVEL_LABEL[user?.level ?? "Anfänger"] ?? user?.level
  const levelColor = LEVEL_COLOR[user?.level ?? "Anfänger"] ?? "text-gray-400"

  const bg      = dark ? "bg-[#060e1c]"     : "bg-gray-50"
  const cardBg  = dark ? "bg-[#0d1b2e]"     : "bg-white"
  const textPri = dark ? "text-white"        : "text-gray-900"
  const textSub = dark ? "text-gray-400"     : "text-gray-500"
  const divider = dark ? "border-[#1e2f45]" : "border-gray-200"

  return (
    <div className={`${bg} flex-1 flex flex-col items-center justify-center px-6 py-16`}>

      {/* Ambient glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-160 h-96 bg-blue-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-2xl flex flex-col items-center gap-10">

        {/* Greeting */}
        <div className="text-center space-y-2">
          <p className={`text-sm font-medium ${textSub}`}>Willkommen zurück</p>
          <h1 className={`text-4xl font-bold tracking-tight ${textPri}`}>
            Hallo, {firstName} 👋
          </h1>
          {user && (
            <p className={`text-sm ${textSub}`}>
              Level: <span className={`font-semibold ${levelColor}`}>{levelLabel}</span>
              {user.goal && (
                <> &nbsp;·&nbsp; Ziel: <span className={dark ? "text-gray-300" : "text-gray-700"}>{user.goal}</span></>
              )}
            </p>
          )}
        </div>

        {/* Divider */}
        <div className={`w-16 border-t ${divider}`} />

        {/* Cards */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4">

          {/* KI Tutor — normal Link */}
          <Link
            href="/tutor"
            className={`${cardBg} border ${
              dark ? "border-[#1e2f45] hover:border-blue-500/40" : "border-gray-200 hover:border-blue-400/60"
            } rounded-2xl p-6 flex flex-col gap-4 shadow-lg ${
              dark ? "hover:shadow-blue-900/30" : "hover:shadow-blue-100"
            } transition-all duration-200 group`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              dark ? "bg-[#0a1628]" : "bg-gray-50"
            } border ${divider} ${dark ? "text-blue-400" : "text-blue-600"} group-hover:scale-105 transition-transform`}>
              <TutorIcon />
            </div>
            <div className="flex-1 space-y-1.5">
              <h2 className={`text-base font-bold ${textPri}`}>KI Tutor</h2>
              <p className={`text-sm leading-relaxed ${textSub}`}>
                Dein persönlicher KI-Begleiter für Python — stelle Fragen, lass Code erklären und lerne im Gespräch genau das, was du gerade brauchst.
              </p>
            </div>
            <div className={`flex items-center gap-1.5 text-sm font-semibold ${
              dark ? "text-blue-400" : "text-blue-600"
            } group-hover:gap-2.5 transition-all`}>
              Mit dem Tutor lernen
              <ArrowRight />
            </div>
          </Link>

          {/* Python Kurs — triggers rocket animation */}
          <button
            onClick={() => setShowTransition(true)}
            className={`${cardBg} border ${
              dark ? "border-[#1e2f45] hover:border-violet-500/40" : "border-gray-200 hover:border-violet-400/60"
            } rounded-2xl p-6 flex flex-col gap-4 shadow-lg ${
              dark ? "hover:shadow-violet-900/30" : "hover:shadow-violet-100"
            } transition-all duration-200 group text-left`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              dark ? "bg-[#0a1628]" : "bg-gray-50"
            } border ${divider} ${dark ? "text-violet-400" : "text-violet-600"} group-hover:scale-105 transition-transform`}>
              <CourseIcon />
            </div>
            <div className="flex-1 space-y-1.5">
              <h2 className={`text-base font-bold ${textPri}`}>Python Kurs</h2>
              <p className={`text-sm leading-relaxed ${textSub}`}>
                Lerne Python Schritt für Schritt — von den Grundlagen bis zu fortgeschrittenen Konzepten, mit Übungen die dich wirklich weiterbringen.
              </p>
            </div>
            <div className={`flex items-center gap-1.5 text-sm font-semibold ${
              dark ? "text-violet-400" : "text-violet-600"
            } group-hover:gap-2.5 transition-all`}>
              Kurs starten
              <ArrowRight />
            </div>
          </button>

        </div>

        {/* Quick link to profile */}
        <p className={`text-xs ${textSub}`}>
          Einstellungen & Profil findest du oben rechts im Avatar-Menü.
        </p>

      </div>
    </div>
  )
}
