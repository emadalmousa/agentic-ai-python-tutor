import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import type { SkillTestGenerateResponse, SkillTestResult } from "@/types/tutor"

// --- Module mocks (hoisted before imports) ---

vi.mock("@/context/AuthContext", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/context/ThemeContext", () => ({
  useTheme: vi.fn(),
}))

vi.mock("@/lib/api", () => ({
  generateSkillTest: vi.fn(),
  submitSkillTest: vi.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { generateSkillTest, submitSkillTest } from "@/lib/api"
import SkillTestModal from "@/components/SkillTestModal"
import type { SkillProgress } from "@/types/tutor"

// --- Mock data ---

const mockSkill: SkillProgress = {
  skill_key: "variables",
  skill_label: "Variablen",
  score: 60,
  status: "partial",
  updated_at: null,
  level: "beginner",
  is_unlocked: true,
  order: 1,
}

const mockTestData: SkillTestGenerateResponse = {
  test_session_id: 1,
  test_data: {
    multiple_choice: [
      {
        question: "Was ist eine Variable?",
        options: { A: "Ein Wert", B: "Eine Funktion", C: "Eine Klasse", D: "Ein Modul" },
        correct: "A",
        explanation: "Eine Variable speichert einen Wert.",
      },
      {
        question: "Welches Zeichen weist einen Wert zu?",
        options: { A: "==", B: "=", C: "!=", D: "+" },
        correct: "B",
        explanation: "= ist der Zuweisungsoperator.",
      },
      {
        question: "Was ist der Typ von x = 5?",
        options: { A: "str", B: "float", C: "int", D: "bool" },
        correct: "C",
        explanation: "5 ist ein Integer.",
      },
    ],
    code_reading: {
      code: "x = 5\nprint(x)",
      question: "Was ist der Wert von x?",
      correct_answer: "5",
    },
    mini_task: {
      description: "Schreibe Python-Code der x = 5 setzt und ausgibt.",
      expected_output: "5",
    },
  },
}

const passedResult: SkillTestResult = {
  total_score: 80,
  passed: true,
  mc_score: 30,
  code_reading_score: 20,
  mini_task_score: 30,
  per_question_feedback: [],
  attempt_number: 1,
}

const failedResult: SkillTestResult = {
  total_score: 40,
  passed: false,
  mc_score: 10,
  code_reading_score: 10,
  mini_task_score: 20,
  per_question_feedback: [
    { question_type: "MC", index: 0, correct: false, explanation: "Falsche Antwort." },
  ],
  attempt_number: 1,
}

// --- Setup helpers ---

function setupMocks() {
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
}

const defaultProps = {
  skill: mockSkill,
  onClose: vi.fn(),
  onTestPassed: vi.fn(),
}

/**
 * Render SkillTestModal with pre-loaded test data and wait for the MC step to appear.
 * The MC questions render as "{idx+1}. {question}" so we search for the full string.
 */
async function renderAndAwaitStep1() {
  render(<SkillTestModal {...defaultProps} />)
  // The first MC question renders as "1. Was ist eine Variable?"
  await waitFor(
    () => expect(screen.getByText(/1\. Was ist eine Variable\?/)).toBeInTheDocument(),
    { timeout: 3000 },
  )
}

/**
 * Navigate from step 1 to step 2 (Code Reading).
 */
async function goToStep2() {
  fireEvent.click(screen.getByRole("button", { name: /weiter/i }))
  await waitFor(
    () => expect(screen.getByText("Was ist der Wert von x?")).toBeInTheDocument(),
    { timeout: 3000 },
  )
}

/**
 * Navigate from step 1 to step 3 (Mini Task).
 */
async function goToStep3() {
  await goToStep2()
  fireEvent.click(screen.getByRole("button", { name: /weiter/i }))
  await waitFor(
    () => expect(screen.getByText("Schreibe Python-Code der x = 5 setzt und ausgibt.")).toBeInTheDocument(),
    { timeout: 3000 },
  )
}

// -----------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------

describe("SkillTestModal", () => {
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

  // 1. Shows loading state initially ----------------------------------------
  it("shows loading state initially", () => {
    vi.mocked(generateSkillTest).mockReturnValue(new Promise(() => {}))
    render(<SkillTestModal {...defaultProps} />)
    expect(screen.getByText("Test wird generiert...")).toBeInTheDocument()
    // MC questions must not yet be visible
    expect(screen.queryByText(/Was ist eine Variable\?/)).toBeNull()
  })

  // 2. Renders MC questions on step 1 ---------------------------------------
  it("renders multiple choice questions on step 1 after load", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    await renderAndAwaitStep1()

    // All 3 MC questions appear in order
    expect(screen.getByText(/2\. Welches Zeichen weist einen Wert zu\?/)).toBeInTheDocument()
    expect(screen.getByText(/3\. Was ist der Typ von x = 5\?/)).toBeInTheDocument()
  })

  // 3. "Weiter" button advances to step 2 (Code Reading) -------------------
  it("Weiter button advances to step 2 showing Code Reading content", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    await renderAndAwaitStep1()
    await goToStep2()

    // The step indicator in the header shows "Code-Lesen"
    expect(screen.getByText(/Code-Lesen/i)).toBeInTheDocument()
    // Code reading question is shown
    expect(screen.getByText("Was ist der Wert von x?")).toBeInTheDocument()
  })

  // 4. "Weiter" button advances to step 3 (Mini Task) ----------------------
  it("Weiter button on step 2 advances to step 3 showing Mini Task", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    await renderAndAwaitStep1()
    await goToStep3()

    // Mini-Aufgabe header is displayed
    expect(screen.getByText("Mini-Aufgabe")).toBeInTheDocument()
    // Task description
    expect(screen.getByText("Schreibe Python-Code der x = 5 setzt und ausgibt.")).toBeInTheDocument()
  })

  // 5. "Zurück" button goes back to previous step --------------------------
  it("Zurück button goes back from step 2 to step 1", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    await renderAndAwaitStep1()
    await goToStep2()

    // Go back to step 1
    fireEvent.click(screen.getByRole("button", { name: /zurück/i }))
    await waitFor(
      () => expect(screen.getByText(/1\. Was ist eine Variable\?/)).toBeInTheDocument(),
      { timeout: 3000 },
    )
  })

  // 6. "Absenden" submits all answers ---------------------------------------
  it("Absenden button submits and calls submitSkillTest with correct payload", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    vi.mocked(submitSkillTest).mockResolvedValue(passedResult)

    await renderAndAwaitStep1()
    await goToStep3()

    fireEvent.click(screen.getByRole("button", { name: /absenden/i }))

    await waitFor(() => expect(submitSkillTest).toHaveBeenCalledOnce(), { timeout: 3000 })
    expect(submitSkillTest).toHaveBeenCalledWith(
      expect.objectContaining({
        skill_key: "variables",
        test_session_id: 1,
      }),
      "mock-token",
    )
  })

  // 7. Shows "Bestanden!" when score >= 60 ----------------------------------
  it("shows Bestanden when score is >= 60", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    vi.mocked(submitSkillTest).mockResolvedValue(passedResult)

    await renderAndAwaitStep1()
    await goToStep3()
    fireEvent.click(screen.getByRole("button", { name: /absenden/i }))

    await waitFor(() => expect(screen.getByText(/Bestanden/i)).toBeInTheDocument(), {
      timeout: 3000,
    })
    expect(screen.getByText("80%")).toBeInTheDocument()
  })

  // 8. Shows "Nicht bestanden" when score < 60 ------------------------------
  it("shows Nicht bestanden when score is < 60", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    vi.mocked(submitSkillTest).mockResolvedValue(failedResult)

    await renderAndAwaitStep1()
    await goToStep3()
    fireEvent.click(screen.getByRole("button", { name: /absenden/i }))

    await waitFor(() => expect(screen.getByText("Nicht bestanden")).toBeInTheDocument(), {
      timeout: 3000,
    })
    expect(screen.getByText("40%")).toBeInTheDocument()
  })

  // 9. Shows score breakdown (MC/Code-Lesen/Mini-Aufgabe) ------------------
  it("shows score breakdown after submission", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    vi.mocked(submitSkillTest).mockResolvedValue(passedResult)

    await renderAndAwaitStep1()
    await goToStep3()
    fireEvent.click(screen.getByRole("button", { name: /absenden/i }))

    await waitFor(() => expect(screen.getByText(/Bestanden/i)).toBeInTheDocument(), {
      timeout: 3000,
    })

    // Score breakdown labels (in the ScoreBox components)
    expect(screen.getByText("MC")).toBeInTheDocument()
    expect(screen.getByText("Code-Lesen")).toBeInTheDocument()
    // "Mini-Aufgabe" label appears in the ScoreBox
    const miniLabels = screen.getAllByText("Mini-Aufgabe")
    expect(miniLabels.length).toBeGreaterThanOrEqual(1)

    // Scores displayed as fractions per ScoreBox
    expect(screen.getByText("30/30")).toBeInTheDocument()
    expect(screen.getByText("20/30")).toBeInTheDocument()
    expect(screen.getByText("30/40")).toBeInTheDocument()
  })

  // 10. "Nochmal versuchen" button resets the test on failure ---------------
  it("Nochmal versuchen button resets test on failure", async () => {
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)
    vi.mocked(submitSkillTest).mockResolvedValue(failedResult)

    await renderAndAwaitStep1()
    await goToStep3()
    fireEvent.click(screen.getByRole("button", { name: /absenden/i }))

    await waitFor(() => expect(screen.getByText("Nicht bestanden")).toBeInTheDocument(), {
      timeout: 3000,
    })

    // Set up the retry call to also resolve with test data
    vi.mocked(generateSkillTest).mockResolvedValue(mockTestData)

    fireEvent.click(screen.getByRole("button", { name: /nochmal versuchen/i }))

    // Result screen disappears
    await waitFor(() => expect(screen.queryByText("Nicht bestanden")).toBeNull(), {
      timeout: 3000,
    })

    // generateSkillTest was called twice: once on mount, once on retry
    expect(generateSkillTest).toHaveBeenCalledTimes(2)
  })
})
