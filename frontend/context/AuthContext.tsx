"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

export type Level = "Anfänger" | "Mittel" | "Fortgeschritten"

export type Role = "admin" | "user"

export interface User {
  id: string
  name: string
  email: string
  level: Level
  goal: string
  role: Role
  analyzedCount: number
}

export interface RegisterData {
  name: string
  email: string
  password: string
  level: Level
  goal: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isGuest: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (data: RegisterData) => Promise<boolean>
  logout: () => void
  continueAsGuest: () => void
  updateUser: (updates: Partial<Pick<User, "name" | "level" | "goal">>) => void
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY = "ki_tutor_token"
const GUEST_KEY = "ki_tutor_guest"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

function readStoredGuest(): boolean {
  if (typeof window === "undefined") return false
  return localStorage.getItem(GUEST_KEY) === "true"
}

async function fetchMe(token: string): Promise<User | null> {
  try {
    const res = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return null
    const data = await res.json()
    return {
      id: String(data.id),
      name: data.name,
      email: data.email,
      level: data.level as Level,
      goal: data.goal,
      role: (data.role ?? "user") as Role,
      analyzedCount: data.analyzed_count ?? 0,
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isGuest, setIsGuest] = useState<boolean>(readStoredGuest)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const token = getToken()

    const init = token
      ? fetchMe(token).then((resolved) => {
          if (resolved) {
            setUser(resolved)
          } else {
            localStorage.removeItem(TOKEN_KEY)
          }
        })
      : Promise.resolve()

    init.then(() => setMounted(true))
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) return false
      const { access_token } = await res.json()
      localStorage.setItem(TOKEN_KEY, access_token)
      const resolved = await fetchMe(access_token)
      if (resolved) {
        setUser(resolved)
        return true
      }
      return false
    } catch {
      return false
    }
  }

  const register = async (data: RegisterData): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          email: data.email,
          password: data.password,
          level: data.level,
          goal: data.goal,
        }),
      })
      return res.ok
    } catch {
      return false
    }
  }

  const continueAsGuest = () => {
    setIsGuest(true)
    localStorage.setItem(GUEST_KEY, "true")
  }

  const updateUser = async (updates: Partial<Pick<User, "name" | "level" | "goal">>) => {
    const token = getToken()
    if (!user || !token) return
    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      })
      if (!res.ok) return
      const data = await res.json()
      setUser({
        id: String(data.id),
        name: data.name,
        email: data.email,
        level: data.level as Level,
        goal: data.goal,
        role: (data.role ?? "user") as Role,
        analyzedCount: data.analyzed_count ?? 0,
      })
    } catch {
      // network error — ignore silently
    }
  }

  const logout = () => {
    setUser(null)
    setIsGuest(false)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(GUEST_KEY)
    sessionStorage.removeItem("ki_tutor_chat_history")
    sessionStorage.removeItem("ki_tutor_material_name")
  }

  if (!mounted) {
    return null
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user || isGuest,
        isGuest,
        login,
        register,
        logout,
        continueAsGuest,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
