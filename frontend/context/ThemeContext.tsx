"use client"

import { createContext, useContext, useState } from "react"

interface ThemeContextType {
  dark: boolean
  toggleDark: () => void
}

const ThemeContext = createContext<ThemeContextType>({ dark: true, toggleDark: () => {} })

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [dark, setDark] = useState(true)
  return (
    <ThemeContext.Provider value={{ dark, toggleDark: () => setDark(d => !d) }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
