"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import CourseTransition from "@/components/CourseTransition"
import TutorTransition from "@/components/TutorTransition"

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


export default function DashboardView() {
  const { user, isAuthenticated } = useAuth()
  const { dark } = useTheme()
  const router = useRouter()
  const [showTransition, setShowTransition] = useState(false)
  const [showTutorTransition, setShowTutorTransition] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  if (showTransition) {
    return <CourseTransition onDone={() => setShowTransition(false)} />
  }

  if (showTutorTransition) {
    return <TutorTransition onDone={() => setShowTutorTransition(false)} />
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
        </div>

        {/* Divider */}
        <div className={`w-16 border-t ${divider}`} />

        {/* Cards */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4">

          {/* KI Tutor */}
          <button
            onClick={() => setShowTutorTransition(true)}
            className={`${cardBg} border ${
              dark ? "border-[#1e2f45] hover:border-blue-500/40" : "border-gray-200 hover:border-blue-400/60"
            } rounded-2xl p-8 flex flex-col items-center justify-between gap-6 shadow-lg ${
              dark ? "hover:shadow-blue-900/30" : "hover:shadow-blue-100"
            } transition-all duration-200 group text-left aspect-square`}
          >
            {/* Big robot emoji */}
            <div className="flex-1 flex items-center justify-center">
              <span
                className="text-8xl select-none transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"
                role="img" aria-label="Roboter"
              >
                🤖
              </span>
            </div>

            {/* Title + button */}
            <div className="w-full space-y-3">
              <h2 className={`text-lg font-bold text-center ${textPri}`}>KI Tutor</h2>
              <div className={`w-full py-2.5 rounded-xl text-sm font-semibold text-center ${
                dark ? "bg-blue-600/20 text-blue-400 group-hover:bg-blue-600/35" : "bg-blue-50 text-blue-600 group-hover:bg-blue-100"
              } transition-colors`}>
                Mit dem Tutor lernen
              </div>
            </div>
          </button>

          {/* Python Kurs */}
          <button
            onClick={() => setShowTransition(true)}
            className={`${cardBg} border ${
              dark ? "border-[#1e2f45] hover:border-violet-500/40" : "border-gray-200 hover:border-violet-400/60"
            } rounded-2xl p-8 flex flex-col items-center justify-between gap-6 shadow-lg ${
              dark ? "hover:shadow-violet-900/30" : "hover:shadow-violet-100"
            } transition-all duration-200 group text-left aspect-square`}
          >
            {/* Big rocket emoji */}
            <div className="flex-1 flex items-center justify-center">
              <span
                className="text-8xl select-none transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12 group-hover:-translate-y-2"
                role="img" aria-label="Rakete"
              >
                🚀
              </span>
            </div>

            {/* Title + button */}
            <div className="w-full space-y-3">
              <h2 className={`text-lg font-bold text-center ${textPri}`}>Python Kurs</h2>
              <div className={`w-full py-2.5 rounded-xl text-sm font-semibold text-center ${
                dark ? "bg-violet-600/20 text-violet-400 group-hover:bg-violet-600/35" : "bg-violet-50 text-violet-600 group-hover:bg-violet-100"
              } transition-colors`}>
                Kurs starten
              </div>
            </div>
          </button>

        </div>


      </div>
    </div>
  )
}
