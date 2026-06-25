"""Tutor-Router: Code-Analyse, Chat, Code-Ausführung und PDF-Upload.

Alle Chat-Anfragen werden auf Python-Relevanz geprüft bevor das LLM aufgerufen wird.
RAG-Kontext (vom hochgeladenen PDF) hat Vorrang vor dem Agent-Loop.
"""
import subprocess
import sys
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from models.schemas import CodeRequest, TutorResponse, ChatRequest, ChatResponse, ChatMessage, RunRequest, RunResponse, UploadResponse
from agent.tutor_agent import run_analysis, run_chat, run_chat_with_context
from agent.tools.code_review_chain import run_code_review
from services.memory_service import load_memory, update_memory
from agent.config import get_classifier_llm
from langchain_core.messages import SystemMessage, HumanMessage
from core.database import get_db
from routers.auth import get_current_user
from models.user import User
from models.skill_progress import StudentSkillProgress, SKILL_TREE

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
        sources=result.get("sources", []),
    )


@router.post("/upload-material", response_model=UploadResponse)
async def upload_material(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Lädt ein PDF als Lernmaterial hoch und speichert es als pgvector-Index für den eingeloggten User."""
    content_type = file.content_type or ""
    filename = file.filename or ""
    if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Die hochgeladene Datei ist leer.")

    try:
        from agent.rag.loader import extract_pages
        from agent.rag.splitter import split_pages
        from agent.rag.vectorstore import build_and_save

        pages = extract_pages(pdf_bytes)
        chunks = split_pages(pages)
        build_and_save(chunks, user_id=current_user.id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Verarbeiten der PDF: {e}")

    return UploadResponse(status="ok", chunks=len(chunks))


@router.post("/run", response_model=RunResponse)
def run_code(request: RunRequest) -> RunResponse:
    """Führt Schüler-Code in einer temporären Datei aus und gibt stdout/stderr zurück.

    Temporäre Datei statt -c wird verwendet damit Multi-Zeilen-Code und Syntaxfehler
    korrekt gemeldet werden (bessere Zeilennummern im Traceback).
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(request.code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10,  # Schutz gegen Endlosschleifen
        )
        return RunResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(stdout="", stderr="Timeout: Code lief länger als 10 Sekunden.", exit_code=1)
    finally:
        os.unlink(tmp_path)  # temporäre Datei immer löschen — auch bei Exceptions


import re as _re

_GREETING_PATTERN = _re.compile(
    r"^\s*(hi|hallo|hey|guten\s*(morgen|tag|abend)|servus|moin|grüß\s*(gott|dich)|was\s+geht|wie\s+geht'?s?)\W*\s*$",
    _re.IGNORECASE,
)

_CLASSIFY_SYSTEM = SystemMessage(content=(
    "Du klassifizierst Nachrichten im Kontext eines Python-Tutors. "
    "Der Schüler hat Python-Code im Editor und kann ein Lernmaterial (PDF) hochgeladen haben. "
    "Antworte NUR mit 'ja' wenn die Nachricht eine Frage zum Code, zur Programmierung, "
    "zu Python-Konzepten, zu Lernmaterial-Seiten oder zum Lernmaterial sein könnte. "
    "Antworte NUR mit 'nein' bei Fragen die eindeutig nichts mit Programmierung oder dem Lernmaterial zu tun haben (z.B. Wetter, Sport, Kochen). "
    "Kein weiterer Text."
))

OFF_TOPIC_REPLY = (
    "Ich bin dein Python-Tutor und kann nur bei Python, Programmierung und deinem Lernmaterial helfen. "
    "Hast du eine Frage zu deinem Code oder dem PDF? 🐍"
)

# Erkennt Muster wie "Seite 9", "page 9", "seite9", "s. 9"
_PAGE_PATTERN = _re.compile(r"\b(?:seite|page|s\.)\s*(\d+)\b", _re.IGNORECASE)


def _extract_page_number(message: str) -> int | None:
    match = _PAGE_PATTERN.search(message)
    return int(match.group(1)) if match else None


def _is_python_related(message: str, code: str) -> bool:
    """Klassifiziert ob eine Nachricht Python/Programmier-Bezug hat.

    Verwendet das günstige gpt-4o-mini Classifier-LLM für schnelle ja/nein-Entscheidung.
    Gibt bei Fehlern implizit True zurück (False würde legitime Fragen blockieren).
    """
    llm = get_classifier_llm()
    # Schüler-Code mitschicken — Kontext hilft bei mehrdeutigen Fragen ("was macht das hier?")
    context = f"Code des Schülers:\n```python\n{code}\n```\n\nFrage: {message}" if code.strip() else message
    response = llm.invoke([_CLASSIFY_SYSTEM, HumanMessage(content=context)])
    return str(response.content).strip().lower().startswith("ja") # type: ignore


def _get_rag_context(message: str, user_id: int) -> str:
    """Sucht im PDF-Index des Users nach relevanten Passagen.

    Strategie:
    1. Seitenzahl erkannt → alle Chunks dieser Seite (exakter Match)
    2. Immer zusätzlich semantische pgvector-Suche (top_k aus Env-Variable)
    Duplikate werden über seen-Set entfernt, Seiteninhalt steht zuerst.
    Gibt leeren String zurück wenn kein Index vorhanden oder Fehler aufgetreten.
    """
    try:
        from agent.rag.vectorstore import load, query_with_pages, get_page

        index_data = load(user_id)
        if index_data is None:
            return ""  # Kein PDF hochgeladen

        seen: set[str] = set()
        results: list[tuple[str, int]] = []

        # Schritt 1: Explizite Seitenreferenz → direkte Chunk-Abfrage
        page_num = _extract_page_number(message)
        if page_num is not None:
            page_chunks = get_page(index_data, page_num)
            if not page_chunks:
                results.append((f"Seite {page_num} wurde im Lernmaterial nicht gefunden.", 0))
            for item in page_chunks:
                if item[0] not in seen:
                    seen.add(item[0])
                    results.append(item)

        # Schritt 2: Semantische Suche immer ausführen (auch wenn Seite gefunden)
        top_k = int(os.getenv("RAG_TOP_K", "3"))
        for item in query_with_pages(index_data, message, top_k=top_k):
            if item[0] not in seen:  # Duplikate aus Seiten-Lookup überspringen
                seen.add(item[0])
                results.append(item)

        if not results:
            return ""

        # Ausgabe formatieren: Seitennummer als Referenz voranstellen
        parts = []
        for text, page in results:
            ref = f"[Seite {page}]" if page > 0 else ""
            parts.append(f"{ref}\n{text}" if ref else text)

        return "\n\n---\n\n".join(parts)
    except Exception:
        return ""  # Fehler im RAG → normalen Chat fortsetzen


@router.get("/memory")
def get_memory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Gibt den aktuellen Memory-Summary des Users zurück."""
    summary = load_memory(current_user.id, db)
    return {"summary": summary}


@router.post("/review", response_model=dict)
def review_code(
    request: CodeRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """3-stufige Code-Review-Chain: Syntax → Stil/PEP8 → Best Practices."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code darf nicht leer sein.")
    return run_code_review(request.code)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Chat-Endpunkt mit Off-Topic-Filter, RAG-Priorität und personalisiertem Agent.

    Ablauf:
    1. Off-Topic-Check: nicht-Python-Fragen werden mit Standardantwort abgelehnt
    2. RAG-Kontext laden: wenn PDF-Index vorhanden → direktes LLM-Gespräch mit Kontext
    3. Kein RAG → ReAct-Agent mit personalisierten Tools (basierend auf Skill-Fortschritt)
    """
    if _GREETING_PATTERN.match(request.message):
        greeting_reply = f"Hallo {current_user.name}! 👋 Schön, dass du wieder da bist! Hast du Lust, heute weiter Python zu lernen? 🐍"
        new_history = list(request.history) + [
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=greeting_reply),
        ]
        return ChatResponse(reply=greeting_reply, history=new_history)

    if not _is_python_related(request.message, request.code):
        # Off-Topic: History trotzdem aktualisieren damit Frontend konsistent bleibt
        new_history = list(request.history) + [
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=OFF_TOPIC_REPLY),
        ]
        return ChatResponse(reply=OFF_TOPIC_REPLY, history=new_history)

    # Skill-Fortschritt für personalisierte Tool-Auswahl laden
    progress_rows = db.query(StudentSkillProgress).filter_by(user_id=current_user.id).all()
    skill_map = {s["key"]: s for s in SKILL_TREE}
    skill_progress = [
        {
            "skill_key": row.skill_key,
            "skill_label": skill_map[row.skill_key]["label"] if row.skill_key in skill_map else row.skill_key,
            "status": row.status,
            "score": row.score,
            "completed_titles": "",  # wird aktuell nicht befüllt — Platzhalter für spätere Erweiterung
        }
        for row in progress_rows
        if row.skill_key in skill_map  # nur bekannte Skills übergeben
    ]

    # Gedächtnis laden — gibt None zurück wenn noch keine Sessions existieren
    memory_summary = load_memory(current_user.id, db)

    # RAG hat Vorrang: wenn PDF-Kontext gefunden → direktes LLM-Gespräch (kein Agent)
    rag_context = _get_rag_context(request.message, current_user.id)

    if rag_context:
        reply = run_chat_with_context(
            message=request.message,
            code=request.code,
            history=request.history,
            user_level=current_user.level,
            rag_context=rag_context,
        )
    else:
        # Kein RAG → ReAct-Agent mit Memory + dynamischen personalisierten Tools
        reply = run_chat(
            message=request.message,
            code=request.code,
            history=request.history,
            user_level=current_user.level,
            skill_progress=skill_progress,
            memory_summary=memory_summary,
        )

    # Gedächtnis nach Antwort asynchron aktualisieren (non-blocking für Response)
    update_memory(current_user.id, db, request.message, reply)

    # Neue Nachricht ans Ende der History hängen — Frontend nutzt dies für Anzeige
    new_history = list(request.history) + [
        ChatMessage(role="user", content=request.message),
        ChatMessage(role="assistant", content=reply),
    ]

    return ChatResponse(reply=reply, history=new_history)
