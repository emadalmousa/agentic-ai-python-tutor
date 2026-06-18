# Sprint 3 — Feature-Plan

| # | Feature | Beschreibung | Priorität | LangChain / LLM? |
|---|---|---|---|---|
| 1 | **Profil: Mock-Daten ersetzen** | `ProfileView.tsx` zeigt hardcodierte Weaknesses, Topics, Progress — durch echte `/learning-progress` API-Daten ersetzen | Hoch | Nein |
| 2 | **Chat-History persistieren (Backend)** | Chat-Verlauf aktuell nur in `sessionStorage` — in DB speichern + `ChatSidebar` mit echten Sessions befüllen | Hoch | Nein |
| 3 | **Weakness-Nudge vollständig integrieren** | `nudge_tool.py` + `WeaknessNudgeModal.tsx` sind angelegt aber noch nicht im Flow verdrahtet — beim Login / Progress-Laden automatisch triggern | Hoch | Ja — LLM (Motivationstext) |
| 4 | **PDF: Seitenbereich-Auswahl beim Upload** | Steht als TODO in `schwierigkeiten.md` — Frontend-Eingabe "Seite von–bis", Backend schneidet Chunks entsprechend | Mittel | Nein (nur Filter-Logik) |
| 5 | **Adaptive Übungsreihenfolge** | Skills mit niedrigstem Score bevorzugt als nächste Übung vorschlagen — statt fixer Reihenfolge | Mittel | Optional (LLM oder Score-basierte Heuristik) |
| 6 | **Lernstreak & Gamification** | Tägliche Login-Strähne tracken (DB-Feld), Streak-Badge im Profil + Toast-Notification | Mittel | Nein |
| 7 | **Chat-Filter / Suche** | TODO in `schwierigkeiten.md` — Chat-History in `ChatSidebar` durchsuchbar + nach Datum filterbar | Mittel | Nein |
| 8 | **Level-Test: Detailliertes Feedback** | Nach Level-Test nur Pass/Fail — erweitern um per-Skill-Aufschlüsselung wo Punkte verloren gingen | Mittel | Ja — LLM (Feedback-Text) |
| 9 | **Admin-Dashboard: Schüler-Übersicht** | `/admin` Router existiert — Frontend-Seite bauen mit Skill-Heatmap aller Nutzer, häufigste Fehler | Niedrig | Nein |
| 10 | **LLM-Cache / Rate-Limit-Schutz** | Wiederholte identische LLM-Anfragen (gleiche Übung, gleicher Code) cachen — Redis oder DB-basiert — senkt Kosten | Niedrig | Nein (Infra) |
