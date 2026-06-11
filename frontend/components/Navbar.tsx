"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useLang } from "@/context/LangContext"
import LanguageSwitcher from "@/components/LanguageSwitcher"

export default function Navbar() {
  const { user, isGuest, logout } = useAuth()
  const { dark, toggleDark } = useTheme()
  const { t } = useLang()
  const router = useRouter()
  const pathname = usePathname()
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    function onFsChange() {
      setIsFullscreen(document.fullscreenElement !== null)
    }
    document.addEventListener("fullscreenchange", onFsChange)
    return () => document.removeEventListener("fullscreenchange", onFsChange)
  }, [])

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  }
  const onTutor    = pathname === "/tutor"
  const onProfile  = pathname === "/profile"
  const onProgress = pathname === "/progress"

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <header
      className={`sticky top-0 z-50 flex items-center justify-between px-6 py-3 border-b flex-shrink-0 ${
        dark
          ? "bg-[#080f1e]/95 border-[#1e2f45] backdrop-blur-sm"
          : "bg-white/95 border-gray-200 backdrop-blur-sm"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="text-lg">🤖</span>
        <div>
          <span className={`font-bold text-sm ${dark ? "text-white" : "text-gray-900"}`}>
            Python Tutor
          </span>
          <span className={`ml-2 text-xs ${dark ? "text-gray-500" : "text-gray-400"}`}>
            Agentic AI
          </span>
        </div>
      </div>

      <nav className="flex items-center gap-2">
        {user ? (
          <>
            {!onTutor && (
              <Link
                href="/tutor"
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  dark
                    ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                }`}
              >
                {t("nav.tutor")}
              </Link>
            )}
            {!onProgress && (
              <Link
                href="/progress"
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  dark
                    ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                }`}
              >
                {t("nav.progress")}
              </Link>
            )}
            {!onProfile && (
              <Link
                href="/profile"
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  dark
                    ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                }`}
              >
                {t("nav.profile")}
              </Link>
            )}
            <button
              onClick={handleLogout}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                dark
                  ? "text-gray-400 hover:bg-red-900/30 hover:text-red-300"
                  : "text-gray-500 hover:bg-red-50 hover:text-red-600"
              }`}
            >
              {t("nav.logout")}
            </button>
            <div
              className={`ml-2 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                dark ? "bg-blue-600/20 text-blue-400" : "bg-blue-100 text-blue-700"
              }`}
            >
              {user.name.charAt(0).toUpperCase()}
            </div>
          </>
        ) : isGuest ? (
          <>
            {!onTutor && (
              <Link
                href="/tutor"
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  dark
                    ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                }`}
              >
                {t("nav.tutor")}
              </Link>
            )}
            <Link
              href="/login"
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                dark
                  ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                  : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              }`}
            >
              {t("nav.login")}
            </Link>
          </>
        ) : (
          <>
            <Link
              href="/login"
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                dark
                  ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
                  : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              }`}
            >
              {t("nav.login")}
            </Link>
            <Link
              href="/register"
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                dark
                  ? "border-blue-500/40 text-blue-400 hover:bg-blue-600/10 hover:text-blue-300"
                  : "border-blue-300 text-blue-600 hover:bg-blue-50"
              }`}
            >
              {t("nav.register")}
            </Link>
          </>
        )}

        <div className={`ml-2 w-px h-5 ${dark ? "bg-[#1e2f45]" : "bg-gray-200"}`} />

        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Vollbild beenden" : "Vollbild"}
          className={`flex items-center justify-center w-7 h-7 rounded-lg transition-all ${
            dark
              ? "text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
              : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          }`}
        >
          {isFullscreen ? (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 3v3a2 2 0 0 1-2 2H3"/><path d="M21 8h-3a2 2 0 0 1-2-2V3"/>
              <path d="M3 16h3a2 2 0 0 1 2 2v3"/><path d="M16 21v-3a2 2 0 0 1 2-2h3"/>
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
              <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
            </svg>
          )}
        </button>

        <LanguageSwitcher />

        <button
          onClick={toggleDark}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
            dark
              ? "border-[#2d3f55] text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
              : "border-gray-200 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          }`}
        >
          {dark ? (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
              {t("nav.themeLight")}
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
              {t("nav.themeDark")}
            </>
          )}
        </button>
      </nav>
    </header>
  )
}
