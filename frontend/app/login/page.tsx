"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/")
    }
  }, [isAuthenticated, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    if (!email || !password) {
      setError("Bitte alle Felder ausfüllen.")
      setLoading(false)
      return
    }

    const success = await login(email, password)
    if (success) {
      router.push("/")
    } else {
      setError("Ungültige E-Mail oder Passwort.")
    }
    setLoading(false)
  }

  if (isAuthenticated) return null

  return (
    <div className="min-h-screen bg-[#060e1c] flex items-center justify-center px-4">
      {/* Subtle radial glow behind the card */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <span className="text-2xl">🤖</span>
            <span className="text-white font-bold text-lg">Python Tutor</span>
          </div>
          <p className="text-gray-500 text-sm">Melde dich an, um weiterzulernen</p>
        </div>

        {/* Card */}
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
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              E-Mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Passwort
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Passwort eingeben"
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg px-4 py-3 transition-all"
          >
            {loading ? "Wird angemeldet..." : "Einloggen"}
          </button>

          <p className="text-center text-sm text-gray-500">
            Noch kein Konto?{" "}
            <Link href="/register" className="text-blue-400 hover:text-blue-300 transition-colors">
              Registrieren
            </Link>
          </p>
        </form>

        {/* Demo hint */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-600">
            Demo: student@example.com / password123
          </p>
        </div>
      </div>
    </div>
  )
}
