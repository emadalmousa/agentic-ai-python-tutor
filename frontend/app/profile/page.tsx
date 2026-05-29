"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

const LEARNED_TOPICS = ["Variablen", "Schleifen", "Bedingungen"]
const WEAKNESSES = ["Syntaxfehler", "Einrückung"]
const NEXT_GOAL = "Funktionen"
const PROGRESS_PERCENT = 45

export default function ProfilePage() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login")
    }
  }, [isAuthenticated, router])

  if (!isAuthenticated || !user) return null

  const levelColor = {
    "Anfänger": "bg-green-900/30 text-green-400 border-green-800/40",
    "Mittel": "bg-yellow-900/30 text-yellow-400 border-yellow-800/40",
    "Fortgeschritten": "bg-purple-900/30 text-purple-400 border-purple-800/40",
  }[user.level]

  return (
    <div className="min-h-screen bg-[#060e1c] text-white">
      {/* Navbar spacer - the Navbar is rendered in page.tsx / layout, profile uses its own back-nav */}
      <div className="sticky top-0 z-50 flex items-center justify-between px-6 py-3 border-b bg-[#080f1e]/95 border-[#1e2f45] backdrop-blur-sm">
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
          Zurück zum Tutor
        </button>
        <span className="text-xs text-gray-500">Profil</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Profile header */}
        <div className="flex items-center gap-5 mb-8">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-blue-500/20">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">{user.name}</h1>
            <p className="text-sm text-gray-400">{user.email}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <span className={`text-xs px-2.5 py-0.5 rounded-full border ${levelColor}`}>
                {user.level}
              </span>
              <span className="text-xs text-gray-500">
                Ziel: {user.goal}
              </span>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-1">Analysierte Codes</div>
            <div className="text-3xl font-bold text-white">{user.analyzedCount}</div>
          </div>
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-2">Lernfortschritt</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white">{PROGRESS_PERCENT}%</span>
            </div>
            <div className="mt-2 h-2 bg-[#0a1628] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-700"
                style={{ width: `${PROGRESS_PERCENT}%` }}
              />
            </div>
          </div>
        </div>

        {/* Info cards */}
        <div className="space-y-4">
          {/* Learned topics */}
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-400">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">Gelernte Themen</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {LEARNED_TOPICS.map((topic) => (
                <span
                  key={topic}
                  className="px-3 py-1 text-xs rounded-full bg-green-900/20 text-green-400 border border-green-800/30"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>

          {/* Weaknesses */}
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">Aktuelle Schwächen</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {WEAKNESSES.map((w) => (
                <span
                  key={w}
                  className="px-3 py-1 text-xs rounded-full bg-amber-900/20 text-amber-400 border border-amber-800/30"
                >
                  {w}
                </span>
              ))}
            </div>
          </div>

          {/* Next learning goal */}
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">Nächstes Lernziel</h3>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600/15 text-blue-300 border border-blue-500/30">
                {NEXT_GOAL}
              </span>
              <span className="text-xs text-gray-500">Empfohlen basierend auf deinem Fortschritt</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
