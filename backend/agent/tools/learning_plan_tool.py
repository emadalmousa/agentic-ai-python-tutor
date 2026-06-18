"""Generiert einen personalisierten Wochenlernplan basierend auf den Skill-Scores des Nutzers."""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import get_llm

_SYSTEM_PROMPT = """Du bist ein erfahrener Python-Lerncoach.
Du erhältst eine Liste von Python-Skills mit ihren aktuellen Scores (0-100) und dem Lernziel des Studenten.
Erstelle einen strukturierten Wochenlernplan NUR für Skills mit Score < 80.
Skills mit Score >= 80 gelten als abgeschlossen und kommen NICHT in den Plan.

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
          "hours": 2.0
        }
      ]
    }
  ],
  "tip": "Ein motivierender Satz auf Deutsch (max. 20 Wörter) der auf die größte Schwäche eingeht."
}

Regeln:
- Maximal 3 Skills pro Woche
- Skills mit niedrigstem Score zuerst (dringendste Schwächen)
- Zeitschätzung: score < 40 → 2-3h, score 40-79 → 1-2h
- Maximal 4 Wochen
- Kein Markdown, kein Text außerhalb des JSON"""


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

    todo_sorted = sorted(todo, key=lambda s: s["score"])

    skills_text = "\n".join(
        f"- {s['skill_label']} (key: {s['skill_key']}, score: {s['score']}, level: {s['level']})"
        for s in todo_sorted
    )

    prompt = (
        f"Lernziel des Studenten: {goal}\n\n"
        f"Skills die noch nicht abgeschlossen sind (score < 80):\n{skills_text}\n\n"
        "Erstelle jetzt den Wochenlernplan als JSON."
    )

    try:
        llm = get_llm()
        result = llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        text = result.content.strip()
        # JSON aus Markdown-Wrappern befreien
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception:
        # Fallback: ersten 3 schwächsten Skills in Woche 1
        return {
            "weeks": [
                {
                    "week": 1,
                    "skills": [
                        {
                            "skill_key":   s["skill_key"],
                            "skill_label": s["skill_label"],
                            "score":       s["score"],
                            "hours":       2.0 if s["score"] < 40 else 1.5,
                        }
                        for s in todo_sorted[:3]
                    ],
                }
            ],
            "tip": f"Starte mit {todo_sorted[0]['skill_label']} — dort besteht der größte Nachholbedarf.",
        }
