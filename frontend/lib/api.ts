import type {
  CodeRequest, TutorResponse, ChatRequest, ChatResponse,
  RunRequest, RunResponse, UploadResponse,
  ProgressResponse, SkillAnalyzeRequest, SkillAnalyzeResponse, SkillInfo,
  ExercisesResponse, SubmitExerciseRequest, SubmitExerciseResponse,
  HintRequest, HintResponse,
  SkillTestGenerateResponse, SkillTestSubmitRequest, SkillTestResult,
} from "@/types/tutor"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

export async function analyzeCode(payload: CodeRequest): Promise<TutorResponse> {
  const res = await fetch(`${API_URL}/tutor/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/tutor/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function runCode(payload: RunRequest): Promise<RunResponse> {
  const res = await fetch(`${API_URL}/tutor/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

// --- Authenticated fetch helper ---
function authHeaders(token: string) {
  return { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
}

export async function getLearningProgress(studentId: number, token: string): Promise<ProgressResponse> {
  const res = await fetch(`${API_URL}/learning-progress/${studentId}`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function analyzeSkill(payload: SkillAnalyzeRequest, token: string): Promise<SkillAnalyzeResponse> {
  const res = await fetch(`${API_URL}/learning-progress/analyze`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function getSkills(token: string): Promise<SkillInfo[]> {
  const res = await fetch(`${API_URL}/learning-progress/skills`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function uploadMaterial(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(`${API_URL}/tutor/upload-material`, {
    method: "POST",
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Upload-Fehler: ${res.status}`)
  }
  return res.json()
}

// --- Exercise API ---

export async function getExercises(skillKey: string, token: string): Promise<ExercisesResponse> {
  const res = await fetch(`${API_URL}/exercises/${skillKey}`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function submitExercise(payload: SubmitExerciseRequest, token: string): Promise<SubmitExerciseResponse> {
  const res = await fetch(`${API_URL}/exercises/submit`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function getExerciseHint(payload: HintRequest, token: string): Promise<HintResponse> {
  const res = await fetch(`${API_URL}/exercises/hint`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

// --- Skill test API ---

export async function generateSkillTest(skillKey: string, token: string): Promise<SkillTestGenerateResponse> {
  const res = await fetch(`${API_URL}/skill-tests/generate`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ skill_key: skillKey }),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

export async function submitSkillTest(payload: SkillTestSubmitRequest, token: string): Promise<SkillTestResult> {
  const res = await fetch(`${API_URL}/skill-tests/submit`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}

// --- Learning progress events ---

export async function deleteAnalysisEvents(token: string): Promise<{ deleted_count: number }> {
  const res = await fetch(`${API_URL}/learning-progress/events`, {
    method: "DELETE",
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  return res.json()
}
