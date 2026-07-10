"""Generiert einen personalisierten Wochenlernplan basierend auf den Skill-Scores des Nutzers."""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import get_llm

_SYSTEM_PROMPT = """Du bist ein erfahrener Python-Lerncoach.
Du erhältst eine Liste von Python-Skills mit vorberechneten Lernschritten (tasks), Scores und Lock-Status.
Erstelle einen strukturierten Wochenlernplan NUR für Skills mit Score < 80.
Übernimm die tasks GENAU wie angegeben — ändere sie NICHT.

Antworte NUR mit validem JSON in diesem Format:
{
  "weeks": [
    {
      "week": 1,
      "skills": [
        {
          "skill_key": "for_loop",
          "skill_label": "For-Schleifen",
          "score": 35,
          "hours": 2.5,
          "tasks": [
            {"type": "review",    "label": "Thema wiederholen",   "hours": 0.5},
            {"type": "practice",  "label": "Grundübungen lösen",  "hours": 1.5},
            {"type": "challenge", "label": "Schwerpunktübungen",  "hours": 0.5}
          ]
        }
      ]
    }
  ],
  "tip": "Ein motivierender Satz auf Deutsch (max. 20 Wörter) der auf die größte Schwäche eingeht."
}

Regeln:
- Maximal 3 Skills pro Woche
- Reihenfolge: ZUERST freigeschaltete Skills (is_unlocked=true) mit HÖCHSTEM Score (fast fertig), dann freigeschaltete mit niedrigem Score, ZULETZT gesperrte Skills (is_unlocked=false) — nie in Woche 1
- Maximal 4 Wochen
- Kein Markdown, kein Text außerhalb des JSON"""


def _make_tasks(score: int) -> list[dict]:
    """Erstellt sinnvolle Lernschritte basierend auf dem aktuellen Score."""
    if score < 30:
        return [
            {"type": "review",    "label": "Thema von Grund auf wiederholen", "hours": 1.0},
            {"type": "practice",  "label": "Grundübungen lösen",              "hours": 1.5},
            {"type": "challenge", "label": "Schwerpunktübungen",              "hours": 1.0},
        ]
    if score < 60:
        return [
            {"type": "review",   "label": "Thema wiederholen",  "hours": 0.5},
            {"type": "practice", "label": "Gezielt üben",       "hours": 1.5},
        ]
    # score 60-79: fast fertig
    return [
        {"type": "review",   "label": "Konzept kurz auffrischen", "hours": 0.5},
        {"type": "practice", "label": "Lücken schließen",         "hours": 1.0},
    ]


def generate_learning_plan(
    skills: list[dict],
    goal: str,
) -> dict:
    """Gibt einen Wochenlernplan als dict zurück.

    skills: Liste von {skill_key, skill_label, score, level}
    goal: Lernziel des Nutzers (z.B. "Prüfungsvorbereitung")
    Bei LLM-Fehler → einfacher Fallback-Plan.
    """
    todo = [s for s in skills if s["score"] < 80]
    if not todo:
        return {"weeks": [], "tip": "Super! Du hast alle Skills gemeistert."}

    # Reihenfolge: 1) freigeschaltet + hoher Score (fast fertig)  2) freigeschaltet + niedriger Score  3) gesperrt
    todo_sorted = sorted(
        todo,
        key=lambda s: (
            0 if s.get("is_unlocked", True) else 1,  # gesperrte zuletzt
            -s["score"],                               # innerhalb: höchster Score zuerst
        ),
    )

    # Tasks vorberechnen — deterministisch, nicht vom LLM
    todo_with_tasks = [
        {**s, "tasks": _make_tasks(s["score"]), "hours": sum(t["hours"] for t in _make_tasks(s["score"]))}
        for s in todo_sorted
    ]

    skills_text = "\n".join(
        f"- {s['skill_label']} (key: {s['skill_key']}, score: {s['score']}, level: {s['level']}, "
        f"is_unlocked: {s.get('is_unlocked', True)}, hours: {s['hours']}, "
        f"tasks: {[t['label'] for t in s['tasks']]})"
        for s in todo_with_tasks
    )

    prompt = (
        f"Lernziel des Studenten: {goal}\n\n"
        f"Skills die noch nicht abgeschlossen sind (score < 80), bereits mit Lernschritten:\n{skills_text}\n\n"
        "Verteile diese Skills auf Wochen (max 3 Skills/Woche, max 4 Wochen). "
        "Übernimm tasks und hours GENAU aus der Liste. Erstelle das JSON."
    )

    try:
        llm = get_llm()
        result = llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        text = result.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        plan = json.loads(text)
        # Sicherheitsnetz: tasks aus LLM-Antwort mit vorberechneten überschreiben
        skill_lookup = {s["skill_key"]: s for s in todo_with_tasks}
        for week in plan.get("weeks", []):
            for skill in week.get("skills", []):
                key = skill.get("skill_key")
                if key in skill_lookup:
                    skill["tasks"] = skill_lookup[key]["tasks"]
                    skill["hours"] = skill_lookup[key]["hours"]
        return plan
    except Exception:
        first_three = [s for s in todo_with_tasks if s.get("is_unlocked", True)][:3] or todo_with_tasks[:3]
        return {
            "weeks": [
                {
                    "week": 1,
                    "skills": [
                        {
                            "skill_key":   s["skill_key"],
                            "skill_label": s["skill_label"],
                            "score":       s["score"],
                            "hours":       s["hours"],
                            "tasks":       s["tasks"],
                        }
                        for s in first_three
                    ],
                }
            ],
            "tip": f"Starte mit {first_three[0]['skill_label']} — dort besteht der größte Nachholbedarf.",
        }
