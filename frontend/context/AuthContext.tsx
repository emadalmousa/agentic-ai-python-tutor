"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

export type Level = "Anfänger" | "Mittel" | "Fortgeschritten"

export interface User {
  id: string
  name: string
  email: string
  level: Level
  goal: string
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

const STORAGE_KEY = "python_tutor_auth"
const USERS_KEY = "python_tutor_users"

const DEFAULT_USER: User = {
  id: "1",
  name: "Anna Schmidt",
  email: "student@example.com",
  level: "Mittel",
  goal: "Prüfungsvorbereitung",
  analyzedCount: 12,
}

const DEFAULT_PASSWORD = "password123"

const GUEST_KEY = "python_tutor_guest"

function readStoredUser(): User | null {
  if (typeof window === "undefined") return null
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) return null
  try {
    return JSON.parse(stored) as User
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

function readStoredGuest(): boolean {
  if (typeof window === "undefined") return false
  return localStorage.getItem(GUEST_KEY) === "true"
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(readStoredUser)
  const [isGuest, setIsGuest] = useState<boolean>(readStoredGuest)
  const [mounted, setMounted] = useState(false)

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setMounted(true) }, [])

  const getUsers = (): Record<string, { user: User; password: string }> => {
    try {
      const raw = localStorage.getItem(USERS_KEY)
      if (raw) return JSON.parse(raw)
    } catch {}
    // Seed with default user
    const seed = {
      [DEFAULT_USER.email]: { user: DEFAULT_USER, password: DEFAULT_PASSWORD },
    }
    localStorage.setItem(USERS_KEY, JSON.stringify(seed))
    return seed
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    const users = getUsers()
    const entry = users[email.toLowerCase()]
    if (entry && entry.password === password) {
      setUser(entry.user)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(entry.user))
      return true
    }
    return false
  }

  const register = async (data: RegisterData): Promise<boolean> => {
    const users = getUsers()
    if (users[data.email.toLowerCase()]) {
      return false // already exists
    }
    const newUser: User = {
      id: crypto.randomUUID(),
      name: data.name,
      email: data.email.toLowerCase(),
      level: data.level,
      goal: data.goal,
      analyzedCount: 0,
    }
    users[newUser.email] = { user: newUser, password: data.password }
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
    setUser(newUser)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser))
    return true
  }

  const continueAsGuest = () => {
    setIsGuest(true)
    localStorage.setItem(GUEST_KEY, "true")
  }

  const updateUser = (updates: Partial<Pick<User, "name" | "level" | "goal">>) => {
    if (!user) return
    const updated = { ...user, ...updates }
    setUser(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    const users = getUsers()
    if (users[user.email]) {
      users[user.email].user = updated
      localStorage.setItem(USERS_KEY, JSON.stringify(users))
    }
  }

  const logout = () => {
    setUser(null)
    setIsGuest(false)
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(GUEST_KEY)
  }

  if (!mounted) {
    return null
  }

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user || isGuest, isGuest, login, register, logout, continueAsGuest, updateUser }}
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
