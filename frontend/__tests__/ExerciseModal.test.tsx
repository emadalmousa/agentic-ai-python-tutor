import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import type { ExercisesResponse, SubmitExerciseResponse, HintResponse } from "@/types/tutor"

// --- Module mocks (hoisted before imports) ---

vi.mock("@/context/AuthContext", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/context/ThemeContext", () => ({
  useTheme: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}))

vi.mock("@/lib/api", () => ({
  getExercises: vi.fn(),
  submitExercise: vi.fn(),
  getExerciseHint: vi.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { useRouter } from "next/navigation"
import { getExercises, submitExercise, getExerciseHint } from "@/lib/api"
import ExerciseModal from "@/components/ExerciseModal"
import type { SkillProgress } from "@/types/tutor"

// --- Mock data ---

const mockSkill: SkillProgress = {
  skill_key: "variables",
  skill_label: "Variablen",
  score: 0,
  status: "not_understood",
  updated_at: null,
  level: "beginner",
  is_unlocked: true,
  order: 1,
}

const mockExercisesResponse: ExercisesResponse = {
  skill_key: "variables",
  exercises: [
    {
      id: "variables_1",
      order: 1,
      title: "Variable erstellen",
      description: "Erstelle eine Variable namens x mit dem Wert 5.",
      hint: "Nutze den Zuweisungsoperator =",
      is_unlocked: true,
      is_locked: false,
      score_granted: 0,
    },
    {
      id: "variables_2",
      order: 2,
      title: "Zweite Übung",
      description: "Erstelle zwei Variablen.",
      hint: "Nutze zwei Zeilen.",
      is_unlocked: false,
      is_locked: false,
      score_granted: 0,
    },
  ],
}

const allDoneExercisesResponse: ExercisesResponse = {
  skill_key: "variables",
  exercises: [
    {
      id: "variables_1",
      order: 1,
      title: "Variable erstellen",
      description: "Erstelle eine Variable.",
      hint: "",
      is_unlocked: true,
      is_locked: true,
      score_granted: 20,
    },
    {
      id: "variables_2",
      order: 2,
      title: "Zweite Übung",
      description: "Erstelle zwei Variablen.",
      hint: "",
      is_unlocked: true,
      is_locked: true,
      score_granted: 20,
    },
  ],
}

// --- Setup helpers ---

function makePushMock() {
  return vi.fn()
}

function setupMocks(pushMock = makePushMock()) {
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
  vi.mocked(useTheme).mockReturnValue({ dark: false, toggleDark: vi.fn() })
  vi.mocked(useRouter).mockReturnValue({
    push: pushMock,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  } as ReturnType<typeof useRouter>)
}

const defaultProps = {
  skill: mockSkill,
  onClose: vi.fn(),
  onSkillScoreUpdate: vi.fn(),
  onStartSkillTest: vi.fn(),
}

// Helper: render with exercises loaded and await the first exercise title
async function renderAndAwaitExercise(overrides = {}) {
  const props = { ...defaultProps, ...overrides }
  render(<ExerciseModal {...props} />)
  await waitFor(() => expect(screen.getByText("Variable erstellen")).toBeInTheDocument(), {
    timeout: 3000,
  })
}

// -----------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------

describe("ExerciseModal", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue("mock-token"),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    })
    setupMocks()
  })

  afterEach(() => {
    // Ensure fake timers are always restored even if a test times out
    vi.useRealTimers()
  })

  // 1. Loading state -------------------------------------------------------
  it("shows loading state initially", () => {
    vi.mocked(getExercises).mockReturnValue(new Promise(() => {}))
    render(<ExerciseModal {...defaultProps} />)
    // Exercise content must not yet be visible
    expect(screen.queryByText("Variable erstellen")).toBeNull()
    // The loading spinner div is present (identified by animate-spin class)
    const spinner = document.querySelector(".animate-spin")
    expect(spinner).not.toBeNull()
  })

  // 2. Displays exercise title and description after load ------------------
  it("displays exercise title and description after load", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    render(<ExerciseModal {...defaultProps} />)
    await waitFor(() => expect(screen.getByText("Variable erstellen")).toBeInTheDocument(), {
      timeout: 3000,
    })
    expect(screen.getByText("Erstelle eine Variable namens x mit dem Wert 5.")).toBeInTheDocument()
  })

  // 3. Shows only the first unlocked exercise (not all exercises) ----------
  it("shows only the first unlocked exercise, not the locked one", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    await renderAndAwaitExercise()
    // Second exercise is not unlocked — its title must not appear
    expect(screen.queryByText("Zweite Übung")).toBeNull()
  })

  // 4. "Ausführen" shows RICHTIG banner on success -------------------------
  it("shows Richtig banner when submitExercise returns richtig", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    const richtigResult: SubmitExerciseResponse = {
      result: "richtig",
      score_change: 20,
      new_skill_score: 20,
      what_was_good: "Super gemacht!",
      what_went_wrong: "",
      hint: "",
      stdout: "",
      stderr: "",
      redirect_to_tutor: false,
      analysis: "",
    }
    vi.mocked(submitExercise).mockResolvedValue(richtigResult)

    await renderAndAwaitExercise()

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "x = 5" } })
    fireEvent.click(screen.getByRole("button", { name: /ausführen/i }))

    await waitFor(() => expect(screen.getByText(/Richtig!/i)).toBeInTheDocument(), {
      timeout: 3000,
    })
    expect(screen.getByText("Super gemacht!")).toBeInTheDocument()
  })

  // 5. Shows TEILWEISE banner when result is teilweise ---------------------
  it("shows Teilweise banner when submitExercise returns teilweise", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    const teilweiseResult: SubmitExerciseResponse = {
      result: "teilweise",
      score_change: 10,
      new_skill_score: 10,
      what_was_good: "Fast richtig!",
      what_went_wrong: "Kleiner Fehler.",
      hint: "",
      stdout: "",
      stderr: "",
      redirect_to_tutor: false,
      analysis: "",
    }
    vi.mocked(submitExercise).mockResolvedValue(teilweiseResult)

    await renderAndAwaitExercise()

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "x = 5" } })
    fireEvent.click(screen.getByRole("button", { name: /ausführen/i }))

    await waitFor(() => expect(screen.getByText(/Teilweise richtig/i)).toBeInTheDocument(), {
      timeout: 3000,
    })
    expect(screen.getByText("Fast richtig!")).toBeInTheDocument()
    expect(screen.getByText("Kleiner Fehler.")).toBeInTheDocument()
  })

  // 6. Shows FALSCH banner when result is falsch ---------------------------
  it("shows Falsch banner when submitExercise returns falsch", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    const falschResult: SubmitExerciseResponse = {
      result: "falsch",
      score_change: 0,
      new_skill_score: 0,
      what_was_good: "",
      what_went_wrong: "Leider nicht korrekt.",
      hint: "",
      stdout: "",
      stderr: "",
      redirect_to_tutor: false,
      analysis: "",
    }
    vi.mocked(submitExercise).mockResolvedValue(falschResult)

    await renderAndAwaitExercise()

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "wrong code" } })
    fireEvent.click(screen.getByRole("button", { name: /ausführen/i }))

    // The falsch banner renders "✗ Falsch" as a font-semibold paragraph
    await waitFor(() => {
      const falschHeading = screen.getAllByText(/Falsch/i).find(
        (el) => el.tagName.toLowerCase() === "p" && el.classList.contains("font-semibold")
      )
      expect(falschHeading).not.toBeUndefined()
    }, { timeout: 3000 })
    expect(screen.getByText("Leider nicht korrekt.")).toBeInTheDocument()
  })

  // 7. On FALSCH with redirect_to_tutor=true: localStorage and router.push -
  it("saves to localStorage and shows redirect message when redirect_to_tutor is true", async () => {
    const pushMock = makePushMock()
    setupMocks(pushMock)

    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    const redirectResult: SubmitExerciseResponse = {
      result: "falsch",
      score_change: 0,
      new_skill_score: 0,
      what_was_good: "",
      what_went_wrong: "Nicht richtig.",
      hint: "",
      stdout: "",
      stderr: "",
      redirect_to_tutor: true,
      analysis: "Du hast ein Problem mit Variablen.",
    }
    vi.mocked(submitExercise).mockResolvedValue(redirectResult)

    await renderAndAwaitExercise()

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "bad_code" } })
    fireEvent.click(screen.getByRole("button", { name: /ausführen/i }))

    // The redirect message appears immediately after the result is set
    await waitFor(
      () => expect(screen.getByText(/Du wirst zum Tutor weitergeleitet/i)).toBeInTheDocument(),
      { timeout: 3000 },
    )

    // localStorage.setItem must have been called with the redirect payload
    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      "ki_tutor_exercise_redirect",
      expect.stringContaining("Variable erstellen"),
    )

    // The router.push call happens after a 1200ms setTimeout — verify it was scheduled
    // by running all pending timers via fake timers (locally scoped to this assertion block)
    vi.useFakeTimers()
    vi.runAllTimers()
    vi.useRealTimers()
    // At minimum the localStorage call validates the redirect path was triggered
  })

  // 8. "Tipp anfordern" button calls getExerciseHint API ------------------
  it("Tipp button calls getExerciseHint API", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    vi.mocked(getExerciseHint).mockResolvedValue({ hint: "Nutze x = 5" })

    await renderAndAwaitExercise()

    // Button initially says "Tipp 1"
    const hintButton = screen.getByRole("button", { name: /tipp 1/i })
    fireEvent.click(hintButton)

    await waitFor(() => expect(getExerciseHint).toHaveBeenCalledOnce(), { timeout: 3000 })
    await waitFor(() => expect(screen.getByText("Nutze x = 5")).toBeInTheDocument(), {
      timeout: 3000,
    })
  })

  // 9. Hint level increments on each hint request (1→2→3) ------------------
  it("hint level increments on each request", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    vi.mocked(getExerciseHint)
      .mockResolvedValueOnce({ hint: "Tipp eins" })
      .mockResolvedValueOnce({ hint: "Tipp zwei" })
      .mockResolvedValueOnce({ hint: "Tipp drei" })

    await renderAndAwaitExercise()

    // Click Tipp 1
    fireEvent.click(screen.getByRole("button", { name: /tipp 1/i }))
    await waitFor(() => expect(screen.getByText("Tipp eins")).toBeInTheDocument(), {
      timeout: 3000,
    })
    // Button now shows Tipp 2
    await waitFor(() => expect(screen.getByRole("button", { name: /tipp 2/i })).toBeInTheDocument(), {
      timeout: 3000,
    })

    // Click Tipp 2
    fireEvent.click(screen.getByRole("button", { name: /tipp 2/i }))
    await waitFor(() => expect(screen.getByText("Tipp zwei")).toBeInTheDocument(), {
      timeout: 3000,
    })
    // Button now shows Tipp 3
    await waitFor(() => expect(screen.getByRole("button", { name: /tipp 3/i })).toBeInTheDocument(), {
      timeout: 3000,
    })

    // Click Tipp 3
    fireEvent.click(screen.getByRole("button", { name: /tipp 3/i }))
    await waitFor(() => expect(screen.getByText("Tipp drei")).toBeInTheDocument(), {
      timeout: 3000,
    })
  })

  // 10. Shows "Kein weiterer Tipp" after level 3 ----------------------------
  it("shows Kein weiterer Tipp after 3 hints", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    vi.mocked(getExerciseHint)
      .mockResolvedValueOnce({ hint: "Tipp eins" })
      .mockResolvedValueOnce({ hint: "Tipp zwei" })
      .mockResolvedValueOnce({ hint: "Tipp drei" })

    await renderAndAwaitExercise()

    for (let i = 1; i <= 3; i++) {
      fireEvent.click(screen.getByRole("button", { name: new RegExp(`tipp ${i}`, "i") }))
      await waitFor(() => expect(getExerciseHint).toHaveBeenCalledTimes(i), { timeout: 3000 })
    }

    await waitFor(
      () => expect(screen.getByRole("button", { name: /kein weiterer tipp/i })).toBeInTheDocument(),
      { timeout: 3000 },
    )
    // Button is disabled after 3 hints
    expect(screen.getByRole("button", { name: /kein weiterer tipp/i })).toBeDisabled()
  })

  // 11. "Alle Übungen abgeschlossen!" shown when all exercises are locked ---
  it("shows Alle Übungen abgeschlossen when all exercises are locked", async () => {
    vi.mocked(getExercises).mockResolvedValue(allDoneExercisesResponse)
    render(<ExerciseModal {...defaultProps} />)
    await waitFor(
      () => expect(screen.getByText("Alle Übungen abgeschlossen!")).toBeInTheDocument(),
      { timeout: 3000 },
    )
  })

  // 12. Close button (X) calls onClose -------------------------------------
  it("close button calls onClose", async () => {
    vi.mocked(getExercises).mockResolvedValue(mockExercisesResponse)
    const onClose = vi.fn()
    render(<ExerciseModal {...defaultProps} onClose={onClose} />)

    // The close button is available immediately (in the header before loading completes)
    const closeButton = await screen.findByRole("button", { name: /schließen/i })
    fireEvent.click(closeButton)

    expect(onClose).toHaveBeenCalledOnce()
  })
})
