"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth, Level } from "@/context/AuthContext"

const LEVELS: Level[] = ["Anfänger", "Mittel", "Fortgeschritten"]
const GOALS = [
  "Python Grundlagen",
  "Debugging",
  "Prüfungsvorbereitung",
  "Objektorientierung",
  "Datenstrukturen",
]

export default function RegisterForm() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [level, setLevel] = useState<Level>("Anfänger")
  const [goal, setGoal] = useState(GOALS[0])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { register, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user) router.push("/tutor")
  }, [user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!name || !email || !password || !confirmPassword) {
      setError("Bitte alle Felder ausfüllen.")
      return
    }
    if (password !== confirmPassword) {
      setError("Passwörter stimmen nicht überein.")
      return
    }
    if (password.length < 6) {
      setError("Passwort muss mindestens 6 Zeichen lang sein.")
      return
    }

    setLoading(true)
    const success = await register({ name, email, password, level, goal })
    if (success) {
      router.push("/login")
    } else {
      setError("Ein Konto mit dieser E-Mail existiert bereits.")
    }
    setLoading(false)
  }

  if (user) return null

  return (
    <div className="flex-1 bg-[#060e1c] flex items-center justify-center px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-blue-600/4 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <span className="text-2xl">🤖</span>
            <span className="text-white font-bold text-lg">Python Tutor</span>
          </div>
          <p className="text-gray-500 text-sm">Erstelle dein Lernkonto</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-8 space-y-5"
        >
          {error && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Dein Name"
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">E-Mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Passwort</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 6 Zeichen"
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Bestätigen</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Wiederholen"
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Erfahrungslevel</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value as Level)}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
            >
              {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Lernziel</label>
            <select
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
            >
              {GOALS.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg px-4 py-3 transition-all"
          >
            {loading ? "Wird registriert..." : "Konto erstellen"}
          </button>

          <p className="text-center text-sm text-gray-500">
            Bereits registriert?{" "}
            <Link href="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
              Einloggen
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
