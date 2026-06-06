from pydantic import BaseModel


class CodeRequest(BaseModel):
    code: str


class TutorResponse(BaseModel):
    explanation: str
    error_found: bool
    error_type: str = "Kein Fehler"
    suggestion: str
    next_exercise: str | None = None


class ChatMessage(BaseModel):
    role: str        # "user" oder "assistant"
    content: str


class ChatRequest(BaseModel):
    code: str
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessage]


class RunRequest(BaseModel):
    code: str


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


