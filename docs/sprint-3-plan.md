# Sprint 3 — Feature-Plan

| # | Feature | Beschreibung | Priorität | LangChain / LLM |
|---|---|---|---|---|
| 1 | **Lernplan-Generator** | LLM analysiert alle 37 Skill-Scores des Nutzers und erstellt einen personalisierten Wochenplan: welche Skills in welcher Reihenfolge, mit Zeitschätzung pro Skill | Hoch | LLM — `generate_learning_plan_tool` |
| 2 | **Code-Review mit Stil-Feedback** | Über die reine Fehlererkennung hinaus: LLM bewertet Code-Qualität (Lesbarkeit, Benennung, PEP8, Redundanz) und gibt konkrete Verbesserungsvorschläge als Inline-Kommentare | Hoch | LLM — neues `code_review_tool` |
| 3 | **Adaptiver Hinweis-Dialog** | Statt fixer Hint-Level 1–3 führt das LLM einen echten Dialog: stellt Gegenfragen um zu prüfen ob der Schüler den Fehler selbst findet, bevor es die Lösung verrät | Hoch | LangChain — Conversational Chain mit Memory |
| 4 | **Fehler-Erklärung auf Deutsch** | LLM übersetzt und erklärt Python-Fehlermeldungen (`TypeError`, `IndexError` etc.) kindsgerecht auf Deutsch, mit Beispiel was schiefgelaufen ist und wie man es behebt | Hoch | LLM — erweitertes `debug_tool` |
| 5 | **Quiz-Generator aus Chat-Verlauf** | LLM analysiert die letzten N Chat-Nachrichten und generiert daraus ein kurzes Quiz (3–5 Fragen) um zu prüfen ob der Schüler das Erklärte verstanden hat | Mittel | LLM — `quiz_from_history_tool` |
| 6 | **Code-Umschreibungs-Tool** | Schüler gibt schlechten aber funktionierenden Code ein — LLM schreibt ihn in 3 Varianten um: pythonisch, lesbar, effizient — und erklärt den Unterschied | Mittel | LLM — `refactor_tool` |
| 7 | **Lernfortschritt-Zusammenfassung** | LLM generiert wöchentlich eine narrative Zusammenfassung: "Diese Woche hast du X gelernt, deine stärkste Verbesserung war Y, nächste Woche solltest du Z angehen" | Mittel | LLM — `progress_summary_tool` |
| 8 | **Themen-Verknüpfungs-Agent** | Wenn ein Schüler ein Konzept fragt (z.B. List Comprehension), erkennt das LLM automatisch welche Vorkenntnisse nötig sind und verlinkt auf die relevanten Skills im Skill-Baum | Mittel | LangChain — ReAct-Agent mit Skill-Tree-Tool |
| 9 | **Plagiat-/Hardcode-Detektor** | LLM erkennt ob ein Schüler die erwartete Ausgabe direkt hardcodiert hat (z.B. `print(120)` statt Fakultät berechnen) — geht über den bestehenden einfachen Check hinaus | Mittel | LLM — Erweiterung `exercise_evaluator_tool` |
| 10 | **Lernziel-Abgleich** | LLM vergleicht das vom Nutzer gesetzte Lernziel (z.B. "Prüfungsvorbereitung") mit dem aktuellen Skill-Score und gibt konkrete Empfehlungen was noch fehlt um das Ziel zu erreichen | Niedrig | LLM — `goal_alignment_tool` |
