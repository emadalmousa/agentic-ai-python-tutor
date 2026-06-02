"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"
import { useLang } from "@/context/LangContext"

export default function LoginForm() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login, user, continueAsGuest } = useAuth()
  const { t } = useLang()
  const router = useRouter()

  const handleGuest = useCallback(() => {
    continueAsGuest()
    router.push("/tutor")
  }, [continueAsGuest, router])

  useEffect(() => {
    if (user) router.push("/tutor")
  }, [user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    if (!email || !password) {
      setError(t("auth.login.errorEmpty"))
      setLoading(false)
      return
    }

    const success = await login(email, password)
    if (success) {
      router.push("/tutor")
    } else {
      setError(t("auth.login.errorInvalid"))
    }
    setLoading(false)
  }

  if (user) return null

  return (
    <div className="flex-1 bg-[#060e1c] flex items-center justify-center px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <span className="text-2xl">🤖</span>
            <span className="text-white font-bold text-lg">Python Tutor</span>
          </div>
          <p className="text-gray-500 text-sm">{t("auth.login.subtitle")}</p>
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
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.login.email")}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("auth.login.password")}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("auth.login.passwordPlaceholder")}
              className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg px-4 py-3 transition-all"
          >
            {loading ? t("auth.login.submitting") : t("auth.login.submit")}
          </button>

          <p className="text-center text-sm text-gray-500">
            {t("auth.login.noAccount")}{" "}
            <Link href="/register" className="text-blue-400 hover:text-blue-300 transition-colors">
              {t("auth.login.register")}
            </Link>
          </p>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#1e2f45]" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-[#0d1b2e] px-3 text-gray-600">{t("auth.login.or")}</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGuest}
            className="w-full border border-[#1e2f45] hover:border-[#2d4a6b] hover:bg-[#0a1628] text-gray-400 hover:text-gray-200 font-medium text-sm rounded-lg px-4 py-3 transition-all"
          >
            {t("auth.login.guest")}
          </button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-xs text-gray-600">{t("auth.login.demo")}</p>
        </div>
      </div>
    </div>
  )
}
