# Feature: Lernplan-Generator

## Was ist das?

Das LLM analysiert alle 37 Skill-Scores des Nutzers und erstellt einen personalisierten Wochenlernplan. Nur Skills mit Score < 80 kommen in den Plan. Der Plan wird als Modal auf der `/progress`-Seite angezeigt — mit Wocheneinteilung, Zeitschätzung pro Skill und einem motivierenden Tipp. Von jedem Skill aus kann der Nutzer direkt zum Tutor springen.

## Datenfluss

```
Nutzer klickt "Lernplan" Button (Progress-Seite)
         │
         ▼
Frontend → POST /learning-progress/learning-plan
         │
         ▼
learning_progress.py → get_learning_plan()
         │
         ├── _build_progress_response(user_id, db)
         │       → alle 37 Skill-Scores aus DB laden
         │
         └── generate_learning_plan(skills, goal)     ← LLM-AUFRUF
                 agent/tools/learning_plan_tool.py
                 │
                 ├── Filtert Skills mit score < 80
                 ├── Sortiert nach Score aufsteigend (dringendste zuerst)
                 │
                 └── LLM-Prompt:
                       Input:  Skill-Liste + Lernziel des Nutzers
                       Output: JSON { weeks: [...], tip: "..." }
                 │
                 Bei LLM-Fehler → Fallback: erste 3 schwächste Skills in Woche 1
         │
         ▼
Response: { weeks: [{ week, skills: [{ skill_key, skill_label, score, hours }] }], tip }
         │
         ▼
Frontend → LearningPlanModal öffnet sich
         │
         ├── Wochenblöcke mit Skill-Zeilen (Farbe nach Score)
         ├── Motivations-Tipp oben
         └── "Starten →" Button → navigiert zum Skill in der Skill-Liste
```

## Datenbankmodell

Kein neues Modell — nutzt bestehende `student_skill_progress`-Tabelle.

## Schlüsseldateien

| Datei | Funktion |
|---|---|
| `backend/agent/tools/learning_plan_tool.py` | LLM generiert Wochenlernplan als JSON |
| `backend/routers/learning_progress.py` | `POST /learning-progress/learning-plan` Endpoint |
| `frontend/components/LearningPlanModal.tsx` | Modal-UI: Wochen, Skills, Tipp, Start-Button |
| `frontend/components/LearningProgressView.tsx` | Button + State + Modal-Integration |
| `frontend/lib/api.ts` | `getLearningPlan()` API-Funktion |
| `frontend/types/tutor.ts` | `LearningPlanResponse`, `LearningPlanWeek`, `LearningPlanSkill` |

## LLM-Aufruf

| Aufruf | Modell | Zweck |
|---|---|---|
| `generate_learning_plan()` | `get_llm()` (gpt-4o / Ollama) | Wochenplan + Tipp generieren |

## JSON-Struktur (LLM-Output)

```json
{
  "weeks": [
    {
      "week": 1,
      "skills": [
        { "skill_key": "for_loop", "skill_label": "For-Schleifen", "score": 35, "hours": 2.0 },
        { "skill_key": "functions", "skill_label": "Funktionen",   "score": 50, "hours": 1.5 }
      ]
    },
    {
      "week": 2,
      "skills": [
        { "skill_key": "lists", "skill_label": "Listen", "score": 60, "hours": 1.5 }
      ]
    }
  ],
  "tip": "Starte mit For-Schleifen — dort besteht der größte Nachholbedarf."
}
```

## Regeln für den LLM-Prompt

- Maximal 3 Skills pro Woche
- Skills mit niedrigstem Score zuerst
- Zeitschätzung: score < 40 → 2–3h, score 40–79 → 1–2h
- Maximal 4 Wochen
- Skills mit Score ≥ 80 kommen nicht in den Plan

## Farbkodierung im Modal

| Farbe | Bedeutung |
|---|---|
| 🔴 Rot | Score < 40% |
| 🟡 Amber | Score 40–79% |

## Fehlerbehandlung

Bei LLM-Fehler greift ein Fallback: die ersten 3 schwächsten Skills werden automatisch in Woche 1 eingetragen ohne LLM-Aufruf.
