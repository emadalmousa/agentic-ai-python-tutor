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

> 1. "Kurz wie das technisch funktioniert — wir haben das komplett selbst gebaut, kein LangChain-Memory-Modul. Das steckt in unserem eigenen `memory_service.py`."
> 2. "Wenn Lisa eine Nachricht schickt, passieren zwei Sachen."
> 3. "Erstens: `load_memory()` holt ihren Summary aus der Datenbank und packt ihn als Kontext in den System-Prompt. Das ist LLM-Aufruf Nummer eins — `run_chat()` antwortet mit dem Wissen über vergangene Sessions."
> 4. "Zweitens, nach der Antwort: `update_memory()` wird aufgerufen. Alter Summary plus neue Nachricht rein, LLM macht draus einen neuen, kompakten Summary. Das ist Aufruf Nummer zwei."
> 5. "Wichtig: wir speichern nicht den rohen Chat-Verlauf. Nur den Summary. Das skaliert viel besser, und jeder User hat seinen eigenen Eintrag in der DB."

---

## Slide 5 — Code-Review Chain (technisch)

> 1. "Die Code-Review Chain. Lisa schickt ihren Code rein, und dann läuft eine RunnableSequence durch — drei Schritte, drei separate LLM-Aufrufe."
> 2. "Schritt eins: Syntax. Das LLM sucht nur nach echten Fehlern — SyntaxError, NameError, mit Zeilennummer."
> 3. "Schritt zwei: Stil. Anderer Prompt, anderes LLM — schaut nur auf PEP8, Naming, Lesbarkeit."
> 4. "Schritt drei: Best Practices. Architektur, Effizienz, ob der Code pythonisch ist."
> 5. "Der Output von Schritt eins geht als Input in Schritt zwei — echte Chain, nicht nur drei separate Aufrufe hintereinander."
> 6. "Im Frontend sieht Lisa dann drei aufklappbare Bereiche — rot für Fehler, gelb für Stil, blau für Best Practices. Sie weiß sofort was sie zuerst fixen muss."

---

## Slide 6 — Lernplan-Generator (technisch)

> 1. "Der Lernplan-Generator. Lisa fragt nach einem Lernplan — und kriegt keinen generischen Wochenplan, sondern einen der auf ihren echten Skill-Scores basiert. Schwache Themen kommen zuerst, max. drei Skills pro Woche."
> 2. "Der Endpunkt POST /learning-plan liest die gespeicherten Scores aus der DB und übergibt sie dem LLM — das LLM entscheidet dann, in welcher Reihenfolge und welchem Tempo Lisa die Themen angehen soll."
> 3. "Der Plan ist kein statisches Dokument — er ändert sich, wenn Lisa neue Themen bearbeitet und ihre Scores sich verbessern. Nächste Woche sieht der Plan automatisch anders aus."

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
