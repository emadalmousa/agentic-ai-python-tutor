"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth, Level } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useLang } from "@/context/LangContext"
import { getLearningProgress } from "@/lib/api"
import type { SkillProgress } from "@/types/tutor"
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

export default function ProfileView() {
  const { user, updateUser } = useAuth()
  const { dark } = useTheme()
  const { t } = useLang()
  const router = useRouter()

  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState("")
  const [editLevel, setEditLevel] = useState<Level>("Anfänger")
  const [editGoal, setEditGoal] = useState("")

  const [skills, setSkills] = useState<SkillProgress[]>([])
  const [overallScore, setOverallScore] = useState<number | null>(null)

  useEffect(() => {
    if (!user) router.push("/login")
  }, [user, router])

  useEffect(() => {
    if (!user) return
    const token = typeof window !== "undefined" ? localStorage.getItem("ki_tutor_token") ?? "" : ""
    if (!token) return
    getLearningProgress(Number(user.id), token)
      .then((data) => {
        setSkills(data.skills)
        setOverallScore(data.overall_score)
      })
      .catch(() => {/* ignore — show no data */})
  }, [user])

  if (!user) return null

  const learnedTopics = skills
    .filter((s) => s.score >= 80)
    .map((s) => s.skill_label)

  const weaknesses = skills
    .filter((s) => s.is_unlocked && s.score < 40)
    .sort((a, b) => a.score - b.score)
    .slice(0, 5)
    .map((s) => s.skill_label)

  const nextGoal = skills.find((s) => s.is_unlocked && s.score < 80)?.skill_label ?? null

  const progressPercent = overallScore ?? 0

  const levelColor = {
    "Anfänger": "bg-green-900/30 text-green-400 border-green-800/40",
    "Mittel": "bg-yellow-900/30 text-yellow-400 border-yellow-800/40",
    "Fortgeschritten": "bg-purple-900/30 text-purple-400 border-purple-800/40",
  }[user.level]

  const handleEditOpen = () => {
    setEditName(user.name)
    setEditLevel(user.level)
    setEditGoal(user.goal)
    setIsEditing(true)
  }

  const handleEditSave = () => {
    updateUser({ name: editName, level: editLevel, goal: editGoal })
    setIsEditing(false)
  }

  const bg = dark ? "bg-[#060e1c] text-white" : "bg-gray-100 text-gray-900"

  return (
    <div className={`flex-1 ${bg}`}>
      <div className="max-w-2xl mx-auto px-6 py-10">
        <div className="flex items-center gap-5 mb-8">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-blue-500/20">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">{user.name}</h1>
              {!isEditing && (
                <button
                  onClick={handleEditOpen}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium border border-[#1e2f45] text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200 transition-all"
                >
                  {t("profile.edit")}
                </button>
              )}
            </div>
            <p className="text-sm text-gray-400">{user.email}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <span className={`text-xs px-2.5 py-0.5 rounded-full border ${levelColor}`}>
                {user.level}
              </span>
              <span className="text-xs text-gray-500">{t("profile.goalPrefix", { goal: user.goal })}</span>
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-6 mb-6 space-y-4">
            <h2 className="text-sm font-medium text-gray-300">{t("profile.editTitle")}</h2>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("profile.name")}</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("profile.level")}</label>
              <select
                value={editLevel}
                onChange={(e) => setEditLevel(e.target.value as Level)}
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
              >
                {LEVELS.map((l) => <option key={l.value} value={l.value}>{t(l.labelKey)}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">{t("profile.goal")}</label>
              <select
                value={editGoal}
                onChange={(e) => setEditGoal(e.target.value)}
                className="w-full bg-[#0a1628] border border-[#1e2f45] rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all appearance-none"
              >
                {GOALS.map((g) => <option key={g.value} value={g.value}>{t(g.labelKey)}</option>)}
              </select>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={handleEditSave}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-all"
              >
                {t("profile.save")}
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium border border-[#1e2f45] text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200 transition-all"
              >
                {t("profile.cancel")}
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-1">{t("profile.analyzedCodes")}</div>
            <div className="text-3xl font-bold text-white">{user.analyzedCount}</div>
          </div>
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="text-xs text-gray-500 mb-2">{t("profile.progressLabel")}</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white">{progressPercent}%</span>
            </div>
            <div className="mt-2 h-2 bg-[#0a1628] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-700"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-400">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">{t("profile.learnedTopics")}</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {learnedTopics.length > 0
                ? learnedTopics.map((topic) => (
                    <span key={topic} className="px-3 py-1 text-xs rounded-full bg-green-900/20 text-green-400 border border-green-800/30">
                      {topic}
                    </span>
                  ))
                : <span className="text-xs text-gray-500">—</span>
              }
            </div>
          </div>

          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">{t("profile.weaknesses")}</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {weaknesses.length > 0
                ? weaknesses.map((w) => (
                    <span key={w} className="px-3 py-1 text-xs rounded-full bg-amber-900/20 text-amber-400 border border-amber-800/30">
                      {w}
                    </span>
                  ))
                : <span className="text-xs text-gray-500">—</span>
              }
            </div>
          </div>

          <div className="bg-[#0d1b2e] border border-[#1e2f45] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <h3 className="text-sm font-medium text-gray-300">{t("profile.nextGoal")}</h3>
            </div>
            <div className="flex items-center gap-3">
              {nextGoal
                ? <>
                    <span className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600/15 text-blue-300 border border-blue-500/30">
                      {nextGoal}
                    </span>
                    <span className="text-xs text-gray-500">{t("profile.recommended")}</span>
                  </>
                : <span className="text-xs text-gray-500">—</span>
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
