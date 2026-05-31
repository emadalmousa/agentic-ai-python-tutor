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

// --- Exercise types ---

export interface Exercise {
  id: string
  order: number
  title: string
  description: string
  /** Static hint from exercise data. Dynamic hints available via getExerciseHint API. */
  hint: string
  /** True when the exercise is visible to the user (prev exercise completed). */
  is_unlocked: boolean
  /** True when the exercise is fully completed (score_granted=20) and blocks re-submission. */
  is_locked: boolean
  score_granted: number
}

export interface ExercisesResponse {
  skill_key: string
  exercises: Exercise[]
}

export interface SubmitExerciseRequest {
  skill_key: string
  exercise_id: string
  code: string
}

export interface SubmitExerciseResponse {
  result: "richtig" | "teilweise" | "falsch"
  score_change: number
  new_skill_score: number
  what_was_good: string
  what_went_wrong: string
  hint: string
  stdout: string
  stderr: string
  redirect_to_tutor: boolean
  analysis: string
}

export interface HintRequest {
  skill_key: string
  exercise_id: string
  code: string
  hint_level: number
}

export interface HintResponse {
  hint: string
}

// --- Skill test types ---

export interface SkillTestGenerateResponse {
  test_session_id: number
  test_data: {
    multiple_choice: Array<{
      question: string
      options: { A: string; B: string; C: string; D: string }
      correct: string
      explanation: string
    }>
    code_reading: {
      code: string
      question: string
      correct_answer: string
    }
    mini_task: {
      description: string
      expected_output: string
    }
  }
}

export interface SkillTestSubmitRequest {
  skill_key: string
  test_session_id: number
  mc_answers: Record<string, string>
  code_reading_answer: string
  mini_task_code: string
}

export interface SkillTestResult {
  total_score: number
  passed: boolean
  mc_score: number
  code_reading_score: number
  mini_task_score: number
  per_question_feedback: Array<{
    question_type: string
    index?: number
    correct: boolean
    explanation: string
  }>
  attempt_number: number
}

// --- Level test types ---

export type LevelKey = "beginner" | "intermediate" | "advanced"

export interface LevelTestGenerateResponse {
  test_session_id: number
  level: LevelKey
  test_data: {
    multiple_choice: Array<{
      question: string
      options: { A: string; B: string; C: string; D: string }
      correct: string
      explanation: string
    }>
    code_reading: {
      code: string
      question: string
      correct_answer: string
    }
    mini_task: {
      description: string
      expected_output: string
    }
  }
}

export interface LevelTestSubmitRequest {
  test_session_id: number
  level: LevelKey
  mc_answers: Record<string, string>
  code_reading_answer: string
  mini_task_code: string
}

export interface LevelTestResult {
  total_score: number
  passed: boolean
  mc_score: number
  code_reading_score: number
  mini_task_score: number
  per_question_feedback: Array<{
    question_type: string
    index?: number
    correct: boolean
    explanation: string
  }>
  attempt_number: number
}
