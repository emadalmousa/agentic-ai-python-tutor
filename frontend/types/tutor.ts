export interface CodeRequest {
  code: string
}

export interface TutorResponse {
  explanation: string
  error_found: boolean
  error_type: string
  suggestion: string
  next_exercise: string | null
  sources: string[]
}

export interface UploadResponse {
  status: string
  chunks: number
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

// --- Learning Progress ---

export interface SkillInfo {
  key: string
  label: string
}

export interface SkillProgress {
  skill_key: string
  skill_label: string
  score: number
  status: "understood" | "partial" | "not_understood"
  updated_at: string | null
  level: "beginner" | "intermediate" | "advanced"
  is_unlocked: boolean
  order: number
}

export interface LearningEvent {
  skill_key: string
  skill_label: string
  score: number
  mistakes: string[]
  feedback: string
  recommended_exercise: string
  created_at: string | null
}

export interface ProgressResponse {
  student_id: number
  overall_score: number
  skills: SkillProgress[]
  recent_events: LearningEvent[]
  user_status: "Anfänger" | "Fortgeschritten" | "Profi"
}

export interface SkillAnalyzeRequest {
  code?: string
  question?: string
}

export interface SkillAnalyzeResponse {
  detected_skills: string[]
  main_skill: string
  score: number
  status: "understood" | "partial" | "not_understood"
  mistakes: string[]
  feedback: string
  recommended_next_exercise: string
  updated_progress: ProgressResponse
}
