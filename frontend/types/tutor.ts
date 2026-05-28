export interface CodeRequest {
  code: string
}

export interface TutorResponse {
  explanation: string
  error_found: boolean
  error_type: string
  suggestion: string
  next_exercise: string | null
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface ChatRequest {
  code: string
  message: string
  history: ChatMessage[]
}

export interface ChatResponse {
  reply: string
  history: ChatMessage[]
}

export interface RunRequest {
  code: string
}

export interface RunResponse {
  stdout: string
  stderr: string
  exit_code: number
}
