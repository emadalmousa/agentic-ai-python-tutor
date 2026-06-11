# Sprint 2 — Präsentation Spickzettel

---

## Slide 1 — Titelfolie

> "So, willkommen. Heute zeig ich euch was wir in Sprint 2 gebaut haben.
> Das Projekt ist ein KI-gestützter Python-Tutor — der Student chattet, stellt Fragen, schreibt Code, und der Agent reagiert drauf.
> Die drei großen Themen heute: PDF-Upload mit RAG, Lernfortschritt mit Skill-System, und fünf neue Agent-Tools.
> Fangen wir an."

---

## Slide 2 — Agenda

> "Kurz der Überblick — wir haben sechs Punkte.
> Erst schauen wir uns die neuen Backend-Endpoints an, dann das PDF-Feature mit der RAG-Pipeline dahinter.
> Dann die fünf neuen Tools die der Agent jetzt nutzen kann, und das Skill-System — also wie der Tutor den Lernfortschritt tracked.
> Am Ende kurz was kommt nächsten Sprint, und dann machen wir Live-Demo."

---

## Slide 3 — Endpoints & Architektur

> "Hier seht ihr alle Endpoints — aber ich will nicht einfach eine Liste runterrattern, sondern zeigen *wie* die aufgebaut sind.
> Die vier Karten zeigen vier verschiedene Wege wie ein Request durchs System geht.

> Die **erste Karte** — die ausgegraut ist — ist der alte Chat ohne PDF. Da geht alles durch den LangChain-Agenten, der entscheidet selbst welches Tool er aufruft. Nicht deterministisch, bisschen chaotisch. Den haben wir nicht geändert, zeig ich trotzdem damit's klar ist.

> Die **grüne Karte** ist neu — das sind die Übungs- und Skill-Test-Endpoints. Die rufen direkt ein Tool auf, kein Agent-Loop drumrum. Wir sagen dem System explizit 'ruf dieses Tool auf', das LLM läuft *innerhalb* des Tools, nicht außen rum.

> Die **gelbe Karte** ist auch neu — das ist der Chat *wenn ein PDF hochgeladen ist*, und der Lernfortschritt-Endpoint. Die rufen das LLM direkt auf mit `llm.invoke()`. Kein Tool, kein Agent. Einfach: hier ist der Prompt, gib mir eine Antwort.

> Die **lila Karte** unten rechts — kein LLM, kein LangChain. Auth-Login, Registrierung, Skills aus der Datenbank holen. Reines Python."

---

## Slide 4 — PDF Feature & RAG

> "Ok, jetzt das PDF-Feature. Das ist technisch das interessanteste in diesem Sprint.

> **Obere Reihe — Upload-Pipeline:**
> Student lädt ein PDF hoch. Wir zerlegen das in Chunks, ungefähr 500 Zeichen pro Stück. Dann kommt der erste LLM-Aufruf — die Chunks werden in Vektoren umgewandelt, das nennt sich Embedding. Die Vektoren landen in PostgreSQL, in der pgvector-Extension. Pro User isoliert, also meine PDFs überschreiben nicht deine.

> **Untere Reihe — Chat-Pipeline:**
> Student fragt was. Wir suchen in seinem pgvector-Bereich nach ähnlichen Chunks — semantische Suche. Wenn er 'Erkläre Seite 5' schreibt checken wir auch per Regex ob er eine Seitenzahl meint. Die gefundenen Chunks kommen als Kontext in den Prompt, dann zweiter LLM-Aufruf — direkt, kein Agent drumrum.

> Das heißt: der LLM antwortet mit dem Wissen aus dem PDF, nicht nur aus seinen Trainingsdaten. Das ist RAG."

---

## Slide 5 — Lernfortschritt & Skills

> "Das Skill-System. Jedes Mal wenn der Student Code einschickt, analysiert das System was er gerade geübt hat.

> **Obere Pipeline:**
> Code kommt rein, geht in `analyze_skill()`. Das Ding versucht erstmal das LLM — gibt ihm den Code, fragt 'welchen Skill sehe ich hier, wie gut, welche Fehler?'. Antwort kommt als JSON zurück mit `main_skill`, `score`, `mistakes`. Wenn das LLM nicht erreichbar ist, fällt es auf Keyword-Matching zurück — sucht nach `for ` + `range(` und sagt 'aha, for-loop'.
> Der neue Score wird mit dem alten gemischt: 70% alter Score, 30% neuer. So springt das nicht rum.

> **Untere Reihe — 37 Skills:**
> Wir haben 37 Skills in drei Level: Beginner, Intermediate, Advanced. Man fängt bei Beginner an, kommt nur weiter wenn man einen Skill auf 80% hat. Am Ende wenn man alles auf 100% hat — Profi-Status.

> Die Score-Regeln rechts: 75-100 ist 'understood', 40-74 'partial', darunter 'not_understood'."

---

## Slide 6 — Probleme & Schwierigkeiten

> "Jetzt zur ehrlichen Seite. Was hat nicht funktioniert wie gedacht.

> **Erstes Problem:** Der Classifier-Filter soll erkennen ob eine Frage Python-bezogen ist. Aber das LLM ist nicht deterministisch — 'Was ist eine Liste?' wird manchmal als Python-Frage eingestuft, manchmal als Allgemeinwissen. Das ist noch offen, wir haben noch keine gute Lösung.

> **Zweites Problem:** PDFs die eingescannt sind funktionieren nicht. pypdf liest nur den Text-Layer, keine Pixel. Wer eine fotografierte Vorlesungsfolie hochlädt bekommt leere Chunks. Workaround: nur digital erstellte PDFs, also Word-Export, LaTeX, das läuft.

> **Drittes Problem:** Das Punkte-System ist noch unklar. Wie viel zählt eine gelöste Übung? Wie viel eine Chat-Frage? Wann wird der Score gesenkt? Das fühlt sich momentan etwas willkürlich an, das müssen wir noch klarer definieren."

---

## Slide 7 — Nächster Sprint

> "Was kommt nächsten Sprint — drei Sachen.

> **Agent-Gedächtnis:** Gerade vergisst der Agent alles wenn man die Seite neu lädt. Nächsten Sprint kommt persistente Chat-History — der Tutor erinnert sich an deine Fehler aus der letzten Session, passt seine Erklärungen an.

> **Code-Review Chain:** Eine echte LangChain-Chain — drei Schritte, drei LLM-Aufrufe hintereinander. Schritt 1 Syntax, Schritt 2 Stil, Schritt 3 Best Practices. Das ist dann wirklich 'Chaining' im LangChain-Sinne, nicht nur einzelne Tool-Aufrufe.

> **Mehrere Chats:** Jedes Gespräch in seiner eigenen Session. Sidebar mit alten Chats, kann man jederzeit wieder aufmachen. Klingt simpel, aber gerade gibt's nur einen globalen Chat."

---

## Slide 8 — Live Demo

> "Ok, genug Theorie. Ich zeig das jetzt kurz live."

**Was zeigen:**
- Login / Registrierung
- Chat ohne PDF (normaler Agent-Modus)
- PDF hochladen → Chat mit Kontext aus dem PDF
- Übung generieren und lösen (evaluate_exercise)
- Skill-Test starten
- Lernfortschritt-Page mit den 37 Skills

---

## Timing

| Slide | Zeit |
|-------|------|
| 1–2 | ~2 min |
| 3 | ~4 min |
| 4 | ~4 min |
| 5 | ~3 min |
| 6 | ~3 min |
| 7 | ~2 min |
| 8 Demo | ~7 min |
| **Gesamt** | **~25 min** |
