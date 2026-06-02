"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth, Level } from "@/context/AuthContext"
import { useLang } from "@/context/LangContext"
import type { TranslationKey } from "@/i18n"

const LEVELS: { value: Level; labelKey: TranslationKey }[] = [
  { value: "Anfänger", labelKey: "auth.register.levelBeginner" },
  { value: "Mittel", labelKey: "auth.register.levelIntermediate" },
  { value: "Fortgeschritten", labelKey: "auth.register.levelAdvanced" },
]

const GOALS: { value: string; labelKey: TranslationKey }[] = [
  { value: "Python Grundlagen", labelKey: "auth.register.goalBasics" },
  { value: "Debugging", labelKey: "auth.register.goalDebugging" },
  { value: "Prüfungsvorbereitung", labelKey: "auth.register.goalExam" },
  { value: "Objektorientierung", labelKey: "auth.register.goalOOP" },
  { value: "Datenstrukturen", labelKey: "auth.register.goalDataStructures" },
]

export default function RegisterForm() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [level, setLevel] = useState<Level>("Anfänger")
  const [goal, setGoal] = useState(GOALS[0].value)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { register, user } = useAuth()
  const { t } = useLang()
  const router = useRouter()

  useEffect(() => {
    if (user) router.push("/tutor")
  }, [user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!name || !email || !password || !confirmPassword) {
      setError(t("auth.register.errorEmpty"))
      return
    }
    if (password !== confirmPassword) {
      setError(t("auth.register.errorMismatch"))
      return
    }
    if (password.length < 6) {
      setError(t("auth.register.errorShort"))
      return
    }

    setLoading(true)
    const success = await register({ name, email, password, level, goal })
    if (success) {
      router.push("/login")
    } else {
      setError(t("auth.register.errorExists"))
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
          <p className="text-gray-500 text-sm">{t("auth.register.subtitle")}</p>
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
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.name")}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("auth.register.namePlaceholder")}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.email")}</label>
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
              <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.password")}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.register.passwordPlaceholder")}
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.confirm")}</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t("auth.register.confirmPlaceholder")}
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.level")}</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value as Level)}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
            >
              {LEVELS.map((l) => <option key={l.value} value={l.value}>{t(l.labelKey)}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.register.goal")}</label>
            <select
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
            >
              {GOALS.map((g) => <option key={g.value} value={g.value}>{t(g.labelKey)}</option>)}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg px-4 py-3 transition-all"
          >
            {loading ? t("auth.register.submitting") : t("auth.register.submit")}
          </button>

          <p className="text-center text-sm text-gray-500">
            {t("auth.register.hasAccount")}{" "}
            <Link href="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
              {t("auth.register.login")}
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
