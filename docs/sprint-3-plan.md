# Sprint 3 — Feature-Plan

| # | Feature | Beschreibung | Priorität | LangChain / LLM |
|---|---|---|---|---|
| 1 | **Agent-Gedächtnis** | `ConversationSummaryMemory` — Agent fasst frühere Sessions per LLM zusammen und speichert sie in der DB. Bei neuem Chat werden vergangene Fehler und Erklärungen automatisch als Kontext eingebunden | Hoch | LangChain — `ConversationSummaryMemory` + DB-persistent |
| 2 | **Lernplan-Generator** | LLM analysiert alle 37 Skill-Scores des Nutzers und erstellt einen personalisierten Wochenplan: welche Skills in welcher Reihenfolge, mit Zeitschätzung pro Skill | Hoch | LLM — `generate_learning_plan_tool` |
| 3 | **Code-Review Chain** | Mehrstufige `RunnableSequence`: Schritt 1 Syntax → Schritt 2 Stil/PEP8 → Schritt 3 Best Practices. Jeder Schritt ein eigener LLM-Aufruf, Ergebnis als strukturiertes Inline-Feedback | Hoch | LangChain — `RunnableSequence`, 3 LLM-Aufrufe |
| 4 | **Adaptiver Hinweis-Dialog** | Statt fixer Hint-Level 1–3 führt das LLM einen echten Dialog: stellt Gegenfragen um zu prüfen ob der Schüler den Fehler selbst findet, bevor es die Lösung verrät | Hoch | LangChain — Conversational Chain mit Memory |
| 5 | **Fehler-Erklärung auf Deutsch** | LLM übersetzt und erklärt Python-Fehlermeldungen (`TypeError`, `IndexError` etc.) kindsgerecht auf Deutsch, mit Beispiel was schiefgelaufen ist und wie man es behebt | Hoch | LLM — erweitertes `debug_tool` |
| 6 | **Quiz-Generator aus Chat-Verlauf** | LLM analysiert die letzten N Chat-Nachrichten und generiert daraus ein kurzes Quiz (3–5 Fragen) um zu prüfen ob der Schüler das Erklärte verstanden hat | Mittel | LLM — `quiz_from_history_tool` |
| 7 | **Code-Umschreibungs-Tool** | Schüler gibt schlechten aber funktionierenden Code ein — LLM schreibt ihn in 3 Varianten um: pythonisch, lesbar, effizient — und erklärt den Unterschied | Mittel | LLM — `refactor_tool` |
| 8 | **Lernfortschritt-Zusammenfassung** | LLM generiert wöchentlich eine narrative Zusammenfassung: "Diese Woche hast du X gelernt, deine stärkste Verbesserung war Y, nächste Woche solltest du Z angehen" | Mittel | LLM — `progress_summary_tool` |
| 9 | **Themen-Verknüpfungs-Agent** | Wenn ein Schüler ein Konzept fragt (z.B. List Comprehension), erkennt das LLM automatisch welche Vorkenntnisse nötig sind und verlinkt auf die relevanten Skills im Skill-Baum | Mittel | LangChain — ReAct-Agent mit Skill-Tree-Tool |
| 10 | **Plagiat-/Hardcode-Detektor** | LLM erkennt ob ein Schüler die erwartete Ausgabe direkt hardcodiert hat (z.B. `print(120)` statt Fakultät berechnen) — geht über den bestehenden einfachen Check hinaus | Mittel | LLM — Erweiterung `exercise_evaluator_tool` |
| 11 | **Lernziel-Abgleich** | LLM vergleicht das vom Nutzer gesetzte Lernziel (z.B. "Prüfungsvorbereitung") mit dem aktuellen Skill-Score und gibt konkrete Empfehlungen was noch fehlt um das Ziel zu erreichen | Niedrig | LLM — `goal_alignment_tool` |
