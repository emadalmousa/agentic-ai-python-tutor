import subprocess
import sys
import tempfile
import os
from fastapi import APIRouter, HTTPException
from models.schemas import CodeRequest, TutorResponse, ChatRequest, ChatResponse, ChatMessage, RunRequest, RunResponse
from agent.tutor_agent import run_analysis
from agent.config import get_llm, get_classifier_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

router = APIRouter(prefix="/tutor", tags=["Tutor"])


@router.post("/analyze", response_model=TutorResponse)
def analyze_code(request: CodeRequest) -> TutorResponse:
    result = run_analysis(request.code)
    return TutorResponse(
        explanation=result["explanation"],
        error_found=result["error_found"],
        error_type=result.get("error_type", "Kein Fehler"),
        suggestion=result["suggestion"],
        next_exercise=result["next_exercise"],
    )



@router.post("/run", response_model=RunResponse)
def run_code(request: RunRequest) -> RunResponse:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(request.code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return RunResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(stdout="", stderr="Timeout: Code lief länger als 10 Sekunden.", exit_code=1)
    finally:
        os.unlink(tmp_path)


_CLASSIFY_SYSTEM = SystemMessage(content=(
    "Du klassifizierst Nachrichten im Kontext eines Python-Tutors. "
    "Antworte NUR mit 'ja' wenn die Nachricht eine Frage zum Code, zur Programmierung oder "
    "zu Python-Konzepten sein könnte. "
    "Antworte NUR mit 'nein' bei Fragen die eindeutig nichts mit Programmierung zu tun haben (z.B. Wetter, Sport, Kochen). "
    "Kein weiterer Text."
))

OFF_TOPIC_REPLY = (
    "Ich bin dein Python-Tutor und kann nur bei Python und Programmierung helfen. "
    "Hast du eine Frage zu deinem Code? 🐍"
)


def _is_python_related(message: str, code: str) -> bool:
    llm = get_classifier_llm()
    context = f"Code des Schülers:\n```python\n{code}\n```\n\nFrage: {message}" if code.strip() else message
    response = llm.invoke([_CLASSIFY_SYSTEM, HumanMessage(content=context)])
    return response.content.strip().lower().startswith("ja")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not _is_python_related(request.message, request.code):
        new_history = list(request.history) + [
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=OFF_TOPIC_REPLY),
        ]
        return ChatResponse(reply=OFF_TOPIC_REPLY, history=new_history)

    llm = get_llm()

    system_text = (
        "Du bist ein freundlicher Python-Tutor für Anfänger. "
        "Antworte klar, geduldig und auf Deutsch. Gib bei Bedarf Codebeispiele.\n"
        f"Aktueller Code des Schülers:\n```python\n{request.code}\n```"
    )

    messages = [SystemMessage(content=system_text)]
    for msg in request.history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    messages.append(HumanMessage(content=request.message))

    response = llm.invoke(messages)
    reply = response.content

    new_history = list(request.history) + [
        ChatMessage(role="user", content=request.message),
        ChatMessage(role="assistant", content=reply),
    ]

    return ChatResponse(reply=reply, history=new_history)
