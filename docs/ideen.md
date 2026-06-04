# Sprint 3 — Ideen

## Vorschläge

| # | Idee | Vorteile | Nachteile | Priorität |
|---|---|---|---|---|
| 1 | **Adaptive Schwierigkeit** — LLM analysiert Fehlerhistory und passt automatisch den nächsten Skill vor (überspringen oder wiederholen) | Echte Personalisierung · nutzt bereits vorhandene `LearningEvent` History | LLM-Aufruf bei jedem Schritt · Erklärung für Schüler warum Sprung nötig | 🔴 Hoch |
| 2 | **Chat-Memory mit Zusammenfassung** — LangChain `ConversationSummaryMemory` fasst lange Chat-Verläufe zusammen statt alles zu senden | Kontext bleibt über viele Nachrichten erhalten · weniger Tokens | Zusammenfassung kann Details verlieren · Implementierung in bestehenden `/chat` Endpoint | 🔴 Hoch |
| 3 | **Code-Review Tool** — neues Agent-Tool das nicht nur Fehler sucht sondern Code-Qualität, Stil und Best Practices bewertet | Schüler lernt sauberen Code zu schreiben · differenzierter als `debug_tool` | Überschneidet sich teilweise mit `explain_tool` + `debug_tool` · Abgrenzung nötig | 🟡 Mittel |
| 4 | **Lernpfad-Generator** — LLM erstellt basierend auf Ziel (z.B. "Web-Scraping lernen") einen personalisierten Skill-Plan mit Reihenfolge | Schüler sieht konkreten Weg zum Ziel · nutzt bestehenden SKILL_TREE | Einmaliger Aufruf beim Onboarding · SKILL_TREE ist bereits fix geordnet | 🟡 Mittel |
| 5 | **Fehler-Cluster Analyse** — LLM aggregiert `LearningEvent.mistakes` wöchentlich und generiert eine Schwächen-Zusammenfassung für den Schüler | Macht Muster sichtbar die einzelne Analysen nicht zeigen · `mistakes` Daten bereits vorhanden | Braucht Cronjob oder Trigger · Mehrwert erst nach vielen Events sichtbar | 🟢 Niedrig |

## Empfehlung Sprint 3

Idee 1 + 2 zusammen — beide nutzen vorhandene Daten und LangChain-Komponenten, ohne neue DB-Tabellen zu brauchen.
