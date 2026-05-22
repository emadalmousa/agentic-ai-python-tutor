export interface CodeRequest {
  code: string
  question?: string
}

export interface TutorResponse {
  explanation: string
  error_found: boolean
  suggestion: string
  next_exercise: string | null
}
