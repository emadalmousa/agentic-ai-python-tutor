# Code-Review Chain

## Was ist das?

Die Code-Review Chain ist ein mehrstufiger LLM-Workflow, der Python-Code in drei unabhängigen LLM-Aufrufen analysiert. Jeder Schritt liefert strukturiertes Feedback und reicht sein Ergebnis als Kontext an den nächsten Schritt weiter.

## Wie funktioniert es technisch?

```
Code
 │
 ▼
Schritt 1 — Syntax-Analyse (LLM #1)
 │  → erkennt: fehlende Doppelpunkte, falsche Einrückung, nicht geschlossene Strings
 │
 ▼
Schritt 2 — Stil / PEP8 (LLM #2)  ← kennt Syntax-Ergebnis
 │  → erkennt: snake_case, Zeilenlänge >79, fehlende Leerzeichen, Magic Numbers
 │
 ▼
Schritt 3 — Best Practices (LLM #3)  ← kennt Syntax + Stil
    → erkennt: range(len()) statt enumerate, bare except, mutable Defaults, global-Variablen
```

Implementiert als LangChain `RunnableSequence` via `|`-Operator zwischen `RunnableLambda`-Funktionen. Das `inputs`-Dict wird von Stufe zu Stufe weitergereicht und um das jeweilige Ergebnis ergänzt.

## Was sieht der Nutzer?

Im Code-Editor-Modal gibt es einen violetten **"Code Review"**-Button in der Aktionsleiste. Nach dem Klick:

1. Button wechselt zu "Prüfe..." mit Lade-Animation
2. 3 LLM-Aufrufe laufen sequenziell durch (ca. 5–10 Sekunden)
3. Ein Panel öffnet sich unterhalb des Editors mit drei Abschnitten:
   - 🔴 **Schritt 1 — Syntax** (Fehler/Warnungen)
   - 🟡 **Schritt 2 — Stil / PEP8** (Warnungen)
   - 🔵 **Schritt 3 — Best Practices** (Hinweise)
4. Jedes Problem zeigt: Zeilennummer · Schweregrad-Badge · Beschreibung
5. Header zeigt Gesamtzahl der Probleme (grün = 0, gelb = 1–3, rot = 4+)
6. "✕ Schließen" schließt nur das Panel, nicht den Editor

### Schweregrade

| Badge | Farbe | Bedeutung |
|-------|-------|-----------|
| Fehler | Rot | Syntax-Fehler, Code läuft nicht |
| Warnung | Gelb | Stil-Problem, sollte behoben werden |
| Hinweis | Blau | Verbesserungsvorschlag (Best Practice) |

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `backend/agent/tools/code_review_chain.py` | 3-stufige LangChain-Chain + `run_code_review()` |
| `backend/routers/tutor.py` | `POST /tutor/review` Endpunkt |
| `frontend/components/tutor/CodeReviewPanel.tsx` | Panel-Komponente mit Issue-Darstellung |
| `frontend/components/tutor/CodeModal.tsx` | Button + Panel-Integration |
| `frontend/components/tutor/TutorView.tsx` | Review-State + `handleReview()` |
| `frontend/types/tutor.ts` | `CodeReviewIssue`, `CodeReviewSection`, `CodeReviewResult` |
| `frontend/lib/api.ts` | `reviewCode(code, token)` |

## API

```
POST /tutor/review
Authorization: Bearer <token>
{ "code": "..." }

→ {
  "syntax":         { "issues": [...], "summary": "..." },
  "style":          { "issues": [...], "summary": "..." },
  "best_practices": { "issues": [...], "summary": "..." },
  "total_issues":   3
}
```

Issue-Struktur: `{ "line": int, "severity": "error"|"warning"|"info", "message": string }`

## Fehlerverhalten

- Leerer Code → HTTP 400 vom Backend
- LLM-Fehler in einer Stufe → leere Issues, Fehlermeldung als Summary
- API-Fehler im Frontend → Panel öffnet sich nicht (silent catch)
