# Sprint 3 — Was ich bei jeder Slide sage

---

## Slide 1 — Titelfolie

> 1. "So, willkommen zu Sprint 3."
> 2. "Heute zeig ich euch drei neue Features die wir gebaut haben — Agent-Gedächtnis, Code-Review Chain und Lernplan-Generator."
> 3. "Ich geh das Ganze nicht als Technik-Liste durch, sondern ich zeig euch wie das alles zusammen für eine echte Nutzerin funktioniert."
> 4. "Danach machen wir ne kurze Live Demo."

---

## Slide 2 — Agenda

> 1. "Kurz zur Agenda."
> 2. "Wir starten mit Lisa — das ist unsere fiktive Studentin, durch die ich alle Features erkläre."
> 3. "Dann geh ich technisch rein: wie funktioniert das Gedächtnis, wie funktioniert die Review Chain und der Lernplan."
> 4. "Dann schauen wir was im Sprint 4 kommt, und am Ende gibt's die Live Demo."

---

## Slide 3 — Lisa's Lernstunde

> 0. "Also, das hier ist Lisa. Zweites Semester, Python-Anfängerin. Letzte Woche hat sie Loops gelernt, heute will sie ihren Code reviewen lassen."
> 1. "Sie meldet sich an, sieht das Dashboard — zwei klare Optionen, KI Tutor oder Python Kurs. Sie klickt auf den Tutor."
> 2. "Der Tutor startet mit einer kleinen Animation — Der Roboter begrüßt Lisa persönlich. Das wirkt freundlich und persönlich."
> 3. "Jetzt kommt das erste neue Feature: Der Agent erinnert sich. Er sagt ihr direkt 'Letzte Woche haben wir Loops besprochen — willst du da weitermachen?' Lisa muss gar nichts erklären."
> 4. "Sie schickt ihren Loop-Code rein, kriegt direkt Feedback auf drei Ebenen — was ist ein echter Fehler, was ist nur Stil, was könnte sie langfristig besser machen."
> 5. "Danach fragt sie nach einem Lernplan. Sie kriegt einen personalisierten Wochenplan — nicht irgendwas generisches, sondern basierend auf ihren echten Schwächen."
> 6. "Und nächste Woche, wenn sie wiederkommt — der Tutor weiß noch alles. Kein Neustart, kein 'Wer bist du nochmal'."

---

## Slide 4 — Agent-Gedächtnis (technisch)

> 1. "Kurz wie das technisch funktioniert — komplett selbst gebaut, kein LangChain-Memory-Modul. Das steckt in `memory_service.py`."
> 2. "Wenn Lisa eine Nachricht schickt, passieren zwei Sachen."
> 3. "Schon bevor Lisa etwas schreibt: GET /tutor/memory lädt den Summary aus der DB und zeigt ihn als lila 🧠-Karte oben im Chat. Kein Warten — sie sieht sofort, was der Tutor über sie weiß."
> 4. "Erst wenn Lisa eine Nachricht schickt: `load_memory()` packt den Summary als Kontext in den System-Prompt. Das ist LLM-Aufruf Nummer eins — `run_chat()` antwortet mit dem Wissen über vergangene Sessions."
> 5. "Nach der Antwort: `update_memory()` wird aufgerufen. Alter Summary plus neue Nachricht rein — neuer, kompakter Summary raus. Format: max. 2 Sätze, max. 40 Wörter, nur Schlüsselwörter. Das ist Aufruf Nummer zwei."
> 6. "Wir speichern nicht den rohen Chat-Verlauf — nur den Summary. Jeder User hat seinen eigenen Eintrag in der DB."

---

## Slide 5 — Code-Review Chain (technisch)

> 1. "Die Code-Review Chain — steckt in `code_review_chain.py`. Lisa schickt Code rein, eine `RunnableSequence` läuft durch — drei Schritte, drei separate LLM-Aufrufe."
> 2. "Jeder Schritt hat einen eigenen System-Prompt und fokussiert auf genau eine Dimension. Der Button ist direkt in jeder Übungskarte verfügbar — kein Wechsel zur Tutor-Seite nötig."
> 3. "Schritt 1 — Syntax: Nur echte Fehler — fehlende Doppelpunkte, falsche Einrückung, undefinierte Variablen — mit Zeilennummer und Schweregrad error/warning."
> 4. "Schritt 2 — Stil / PEP8: Anderer Prompt — Naming, Zeilenlänge, Magic Numbers, fehlende Docstrings. Bekommt den Syntax-Summary als Kontext aus Schritt 1."
> 5. "Schritt 3 — Best Practices: Pythonische Muster — range(len()) statt enumerate, redundante Vergleiche wie == True, bare except. Jedes Issue bekommt ein 'Besser:'-Feld mit verbessertem Code-Snippet."
> 6. "Im Frontend: drei aufklappbare Bereiche — rot, gelb, blau. Lisa weiß sofort was zuerst zu fixen ist."

---

## Slide 6 — Lernplan-Generator (technisch)

> 1. "Der Lernplan-Generator — `learning_plan_tool.py`. Lisa klickt auf 'Lernplan' und sieht ihren personalisierten Plan, basierend auf echten Skill-Scores."
> 2. "Sortierreihenfolge ist fest: Erstens freigeschaltete Skills mit hohem Score — die sind fast fertig, leicht auf 100% zu bringen. Zweitens freigeschaltete mit niedrigem Score. Drittens gesperrte Skills — die kommen nie in Woche 1."
> 3. "Jeder Skill wird in 2–3 konkrete Lernschritte aufgeteilt — deterministisch nach Score. Score unter 30: Wiederholen plus Grundübungen plus Schwerpunkt. Score 30 bis 59: Wiederholen plus Üben. Score 60 bis 79: Auffrischen plus Lücken schließen. Mit Zeitschätzung pro Schritt."
> 4. "Der Plan wird im localStorage gecacht — ki_tutor_plan_userId. Beim nächsten Öffnen erscheint er sofort, kein LLM-Call. Datum der letzten Generierung ist sichtbar, ein Refresh-Button erlaubt einen neuen Plan nach Fortschritt. Cache-Ablauf nach 4 Wochen."

---

## Slide 7 — Nächster Sprint

> 1. "Was kommt als nächstes. Drei Sachen haben wir für Sprint 4 geplant."
> 2. "Erstens: Adaptiver Hinweis-Dialog. Wenn der Tutor merkt dass Lisa feststeckt, bietet er Hinweise in drei Stufen an — ohne die Lösung direkt zu verraten. Pädagogisch sinnvoller."
> 3. "Zweitens: Fehlermeldungen auf Deutsch. Python-Tracebacks sind auf Englisch und für Anfänger total kryptisch. Wir übersetzen die automatisch und erklären sie verständlich."
> 4. "Drittens: Inline Thema-Erklärung. Direkt in der Übungsansicht gibt es ein aufklappbares Panel — Lisa klickt drauf, das AI erklärt das Thema level-spezifisch, und sie bleibt dabei in der Übung. Kein Seitenwechsel mehr zum Tutor."

---

## Slide 8 — Live Demo

> 1. "Alright, das war die Theorie — jetzt schauen wir's uns live an."
> 2. *(Browser öffnen, Demo starten)*
> 3. "Ich zeig euch Dashboard, Tutor-Start, Memory in Aktion, Code Review und Lernplan-Generator."
