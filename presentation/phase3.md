# Sprint 3 — Was ich bei jeder Slide sage

---

## Slide 1 — Titelfolie

> "So, willkommen zu Sprint 3. Heute zeig ich euch drei neue Features die wir gebaut haben — Agent-Gedächtnis, Code-Review Chain und Lernplan-Generator. Ich geh das Ganze nicht als Technik-Liste durch, sondern ich zeig euch wie das alles zusammen für eine echte Nutzerin funktioniert. Danach machen wir ne kurze Live Demo."

---

## Slide 2 — Agenda

> "Kurz zur Agenda. Wir starten mit Lisa — das ist unsere fiktive Studentin, durch die ich alle Features erkläre. Dann geh ich kurz technisch rein: wie funktioniert das Gedächtnis, wie funktioniert die Review Chain. Dann schauen wir was als nächstes kommt, und am Ende gibt's die Live Demo wo ihr das alles selbst sehen könnt."

---

## Slide 3 — Lisa's Lernstunde

> "Also, das hier ist Lisa. Zweites Semester, Python-Anfängerin. Letzte Woche hat sie Loops gelernt, heute will sie ihren Code reviewen lassen."

> "Sie loggt sich ein, sieht das Dashboard — zwei klare Optionen, KI Tutor oder Python Kurs. Sie klickt auf den Tutor."

> "Der Tutor startet mit einer kleinen Animation — Roboter begrüßt sie, fühlt sich persönlich an."

> "Jetzt kommt das erste neue Feature: Der Agent erinnert sich. Er sagt ihr direkt 'Letzte Woche haben wir Loops besprochen — willst du da weitermachen?' Lisa muss gar nichts erklären."

> "Sie schickt ihren Loop-Code rein, kriegt direkt Feedback auf drei Ebenen — was ist ein echter Fehler, was ist nur Stil, was könnte sie langfristig besser machen."

> "Danach fragt sie nach einem Lernplan. Sie kriegt einen personalisierten Wochenplan — nicht irgendwas generisches, sondern basierend auf ihren echten Schwächen."

> "Und nächste Woche, wenn sie wiederkommt — der Tutor weiß noch alles. Kein Neustart, kein 'Wer bist du nochmal'."

---

## Slide 4 — Agent-Gedächtnis (technisch)

> "Kurz wie das technisch funktioniert — wir haben das komplett selbst gebaut, kein LangChain-Memory-Modul. Das steckt in unserem eigenen `memory_service.py`."

> "Wenn Lisa eine Nachricht schickt, passieren zwei Sachen."

> "Erstens: `load_memory()` holt ihren Summary aus der Datenbank und packt ihn als Kontext in den System-Prompt. Das ist LLM-Aufruf Nummer eins — `run_chat()` antwortet mit dem Wissen über vergangene Sessions."

> "Zweitens, nach der Antwort: `update_memory()` wird aufgerufen. Alter Summary plus neue Nachricht rein, LLM macht draus einen neuen, kompakten Summary. Das ist Aufruf Nummer zwei."

> "Wichtig: wir speichern nicht den rohen Chat-Verlauf. Nur den Summary. Das skaliert viel besser, und jeder User hat seinen eigenen Eintrag in der DB."

> "Also zwei LLM-Aufrufe pro Nachricht — einer für die Antwort in `run_chat()`, einer für das Gedächtnis-Update in `update_memory()`."

---

## Slide 5 — Code-Review Chain (technisch)

> "Die Code-Review Chain. Lisa schickt ihren Code rein, und dann läuft eine RunnableSequence durch — drei Schritte, drei separate LLM-Aufrufe."

> "Schritt eins: Syntax. Das LLM sucht nur nach echten Fehlern — SyntaxError, NameError, mit Zeilennummer."

> "Schritt zwei: Stil. Anderer Prompt, anderes LLM — schaut nur auf PEP8, Naming, Lesbarkeit."

> "Schritt drei: Best Practices. Architektur, Effizienz, ob der Code pythonisch ist."

> "Der Output von Schritt eins geht als Input in Schritt zwei — echte Chain, nicht nur drei separate Aufrufe hintereinander."

> "Im Frontend sieht Lisa dann drei aufklappbare Bereiche — rot für Fehler, gelb für Stil, blau für Best Practices. Sie weiß sofort was sie zuerst fixen muss."

---

## Slide 6 — Nächster Sprint

> "Was kommt als nächstes. Drei Sachen haben wir für Sprint 4 geplant."

> "Erstens: Adaptiver Hinweis-Dialog. Wenn der Tutor merkt dass Lisa feststeckt, bietet er Hinweise in drei Stufen an — ohne die Lösung direkt zu verraten. Pädagogisch sinnvoller."

> "Zweitens: Fehlermeldungen auf Deutsch. Python-Tracebacks sind auf Englisch und für Anfänger total kryptisch. Wir übersetzen die automatisch und erklären sie verständlich."

> "Drittens: Code-Umschreibungs-Tool. Lisa gibt funktionierenden aber hässlichen Code rein, kriegt sauberen pythonischen Code raus — mit Erklärung was verbessert wurde. Als Lernmaterial."

---

## Slide 7 — Live Demo

> "Alright, das war die Theorie — jetzt schauen wir's uns live an."

> *(Browser öffnen, Demo starten)*

> "Ich zeig euch Dashboard, Tutor-Start, Memory in Aktion, Code Review und Lernplan-Generator."
