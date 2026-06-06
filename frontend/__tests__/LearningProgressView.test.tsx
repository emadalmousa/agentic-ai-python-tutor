import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import type { ProgressResponse } from "@/types/tutor"

// --- Module mocks ---

vi.mock("@/context/AuthContext", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/context/ThemeContext", () => ({
  useTheme: vi.fn(),
}))

vi.mock("@/context/LangContext", () => ({
  useLang: vi.fn(),
}))

vi.mock("@/lib/api", () => ({
  getLearningProgress: vi.fn(),
  analyzeSkill: vi.fn(),
  deleteAnalysisEvents: vi.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useLang } from "@/context/LangContext"
import { getLearningProgress, deleteAnalysisEvents } from "@/lib/api"
import LearningProgressView from "@/components/LearningProgressView"
import de from "@/i18n/de"

// --- Test data factory ---

function makeProgress(overrides: Partial<ProgressResponse> = {}): ProgressResponse {
  return {
    student_id: 1,
    overall_score: 42,
    user_status: "Anfänger",
    skills: [
      {
        skill_key: "variables",
        skill_label: "Variablen",
        score: 60,
        status: "partial",
        updated_at: null,
        level: "beginner",
        is_unlocked: true,
        order: 1,
      },
      {
        skill_key: "loops",
        skill_label: "Schleifen",
        score: 0,
        status: "not_understood",
        updated_at: null,
        level: "beginner",
        is_unlocked: false,
        order: 2,
      },
    ],
    recent_events: [],
    ...overrides,
  }
}

// --- Setup helpers ---

function setupMocks(progressData: ProgressResponse = makeProgress()) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: "1", name: "Test", email: "t@t.de", level: "Anfänger", goal: "", role: "user", analyzedCount: 0 },
    isAuthenticated: true,
    isGuest: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    continueAsGuest: vi.fn(),
    updateUser: vi.fn(),
  })
  vi.mocked(useTheme).mockReturnValue({ dark: true, toggleDark: vi.fn() })
  vi.mocked(useLang).mockReturnValue({
    locale: "de" as const,
    setLocale: vi.fn(),
    t: ((key: string, vars?: Record<string, string | number>) => {
      let str = (de as Record<string, string>)[key] ?? key
      if (vars) {
        str = str.replace(/\{(\w+)\}/g, (_, k) => vars[k] !== undefined ? String(vars[k]) : `{${k}}`)
      }
      return str
    }) as ReturnType<typeof useLang>["t"],
  })
  vi.mocked(getLearningProgress).mockResolvedValue(progressData)
}

// -----------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------

describe("LearningProgressView", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // localStorage stub
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue("mock-token"),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    })
  })

  // 1. User status badge --------------------------------------------------
  it("renders Anfänger status badge", async () => {
    setupMocks(makeProgress({ user_status: "Anfänger" }))
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Anfänger")).toBeInTheDocument())
  })

  it("renders Fortgeschritten status badge", async () => {
    setupMocks(makeProgress({ user_status: "Fortgeschritten", overall_score: 60 }))
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Fortgeschritten")).toBeInTheDocument())
  })

  it("renders Profi status badge", async () => {
    setupMocks(makeProgress({ user_status: "Profi", overall_score: 90 }))
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Profi")).toBeInTheDocument())
  })

  // 2. Locked skills show lock emoji, no role="button" --------------------
  it("locked skill shows lock emoji and is not a button", async () => {
    setupMocks()
    render(<LearningProgressView />)

    // The beginner group starts open (openGroups: { beginner: true, ... })
    // Skills render as soon as the API resolves — no click needed
    await waitFor(() => expect(screen.getByText("Schleifen")).toBeInTheDocument())

    // The locked card has no role="button"
    const lockedLabel = screen.getByText("Schleifen")
    const lockedCard = lockedLabel.closest("div[class*='rounded-xl']")
    expect(lockedCard).not.toBeNull()
    expect(lockedCard!.getAttribute("role")).toBeNull()
  })

  it("locked skill shows Gesperrt text", async () => {
    setupMocks()
    render(<LearningProgressView />)
    // beginner group is open by default, Gesperrt appears for locked skills
    await waitFor(() => expect(screen.getByText("Gesperrt")).toBeInTheDocument())
  })

  // 3. Unlocked skills are clickable (have role="button") -----------------
  it("unlocked skill has role button", async () => {
    setupMocks()
    render(<LearningProgressView />)
    // beginner group is open by default
    await waitFor(() => expect(screen.getByText("Variablen")).toBeInTheDocument())
    const unlockedLabel = screen.getByText("Variablen")
    const unlockedCard = unlockedLabel.closest("[role='button']")
    expect(unlockedCard).not.toBeNull()
  })

  // 4. "Letzte Analysen löschen" button appears when events exist ----------
  it("shows delete button when recent events are present", async () => {
    const progressWithEvents = makeProgress({
      recent_events: [
        {
          skill_key: "variables",
          skill_label: "Variablen",
          score: 55,
          mistakes: [],
          feedback: "Gut gemacht",
          recommended_exercise: "Übung 1",
          created_at: "2026-05-31T10:00:00",
        },
      ],
    })
    setupMocks(progressWithEvents)
    render(<LearningProgressView />)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /letzte analysen löschen/i })).toBeInTheDocument()
    )
  })

  it("does not show delete button when no recent events", async () => {
    setupMocks(makeProgress({ recent_events: [] }))
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Lernfortschritt")).toBeInTheDocument())
    expect(screen.queryByRole("button", { name: /letzte analysen löschen/i })).toBeNull()
  })

  // 5. Code/Frage toggle renders correctly --------------------------------
  it("renders Code and Frage toggle buttons", async () => {
    setupMocks()
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Code")).toBeInTheDocument())
    expect(screen.getByText("Frage")).toBeInTheDocument()
  })

  it("Code toggle is active when clicked", async () => {
    setupMocks()
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Code")).toBeInTheDocument())

    const codeBtn = screen.getByRole("button", { name: "Code" })
    fireEvent.click(codeBtn)

    // After clicking Code, the textarea placeholder should change to code example
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement
    expect(textarea.placeholder).toContain("for i in range")
  })

  it("Frage toggle sets textarea placeholder to question example", async () => {
    setupMocks()
    render(<LearningProgressView />)
    await waitFor(() => expect(screen.getByText("Frage")).toBeInTheDocument())

    // Default is "frage", so placeholder should be the question example already
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement
    expect(textarea.placeholder).toContain("Was ist eine for-Schleife")
  })

  // 6. Overall progress score renders -------------------------------------
  it("renders overall score", async () => {
    setupMocks(makeProgress({ overall_score: 42 }))
    render(<LearningProgressView />)
    // Score appears twice: in the SVG text and in the large number
    await waitFor(() => {
      const matches = screen.getAllByText("42")
      expect(matches.length).toBeGreaterThanOrEqual(1)
    })
  })

  // 7. Delete events calls API and shows success message ------------------
  it("delete events calls deleteAnalysisEvents and shows success message", async () => {
    vi.mocked(deleteAnalysisEvents).mockResolvedValue({ deleted_count: 3 })
    window.confirm = vi.fn().mockReturnValue(true)

    const progressWithEvents = makeProgress({
      recent_events: [
        {
          skill_key: "variables",
          skill_label: "Variablen",
          score: 55,
          mistakes: [],
          feedback: "Gut gemacht",
          recommended_exercise: "Übung 1",
          created_at: "2026-05-31T10:00:00",
        },
      ],
    })
    setupMocks(progressWithEvents)
    render(<LearningProgressView />)

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /letzte analysen löschen/i })).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole("button", { name: /letzte analysen löschen/i }))

    await waitFor(() =>
      expect(screen.getByText(/analysen wurden gelöscht/i)).toBeInTheDocument()
    )
    expect(deleteAnalysisEvents).toHaveBeenCalledOnce()
  })

  // 8. Shows loading state initially, then resolves -----------------------
  it("shows loading indicator while fetching", () => {
    // Never resolve during this assertion
    vi.mocked(getLearningProgress).mockReturnValue(new Promise(() => {}))
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", name: "Test", email: "t@t.de", level: "Anfänger", goal: "", role: "user", analyzedCount: 0 },
      isAuthenticated: true,
      isGuest: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      continueAsGuest: vi.fn(),
      updateUser: vi.fn(),
    })
    vi.mocked(useTheme).mockReturnValue({ dark: true, toggleDark: vi.fn() })
    vi.mocked(useLang).mockReturnValue({
      locale: "de" as const,
      setLocale: vi.fn(),
      t: ((key: string, vars?: Record<string, string | number>) => {
        let str = (de as Record<string, string>)[key] ?? key
        if (vars) {
          str = str.replace(/\{(\w+)\}/g, (_, k) => vars[k] !== undefined ? String(vars[k]) : `{${k}}`)
        }
        return str
      }) as ReturnType<typeof useLang>["t"],
    })

    render(<LearningProgressView />)
    expect(screen.getByText("Laden…")).toBeInTheDocument()
  })

  // 9. Shows error message on API failure ---------------------------------
  it("shows error message when API call fails", async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", name: "Test", email: "t@t.de", level: "Anfänger", goal: "", role: "user", analyzedCount: 0 },
      isAuthenticated: true,
      isGuest: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      continueAsGuest: vi.fn(),
      updateUser: vi.fn(),
    })
    vi.mocked(useTheme).mockReturnValue({ dark: true, toggleDark: vi.fn() })
    vi.mocked(useLang).mockReturnValue({
      locale: "de" as const,
      setLocale: vi.fn(),
      t: ((key: string, vars?: Record<string, string | number>) => {
        let str = (de as Record<string, string>)[key] ?? key
        if (vars) {
          str = str.replace(/\{(\w+)\}/g, (_, k) => vars[k] !== undefined ? String(vars[k]) : `{${k}}`)
        }
        return str
      }) as ReturnType<typeof useLang>["t"],
    })
    vi.mocked(getLearningProgress).mockRejectedValue(new Error("Network error"))

    render(<LearningProgressView />)
    await waitFor(() =>
      expect(screen.getByText("Fortschritt konnte nicht geladen werden.")).toBeInTheDocument()
    )
  })

  // 10. No user — stays in loading (no fetch attempted) ------------------
  it("does not render progress when user is null", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isGuest: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      continueAsGuest: vi.fn(),
      updateUser: vi.fn(),
    })
    vi.mocked(useTheme).mockReturnValue({ dark: true, toggleDark: vi.fn() })
    vi.mocked(useLang).mockReturnValue({
      locale: "de" as const,
      setLocale: vi.fn(),
      t: ((key: string, vars?: Record<string, string | number>) => {
        let str = (de as Record<string, string>)[key] ?? key
        if (vars) {
          str = str.replace(/\{(\w+)\}/g, (_, k) => vars[k] !== undefined ? String(vars[k]) : `{${k}}`)
        }
        return str
      }) as ReturnType<typeof useLang>["t"],
    })

    render(<LearningProgressView />)
    // Component shows loading because setLoading is true but fetch is never called
    // (the useEffect returns early when !user)
    expect(getLearningProgress).not.toHaveBeenCalled()
  })
})
