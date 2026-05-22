import type { CodeRequest, TutorResponse } from "@/types/tutor"

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
