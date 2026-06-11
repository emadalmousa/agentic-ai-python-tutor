# Schwierigkeiten & TODOs

## TODOs

- [x] Per-User PDF-Index: jeder User hat seine eigene pgvector-Collection `user_{user_id}` in PostgreSQL
- [x] Upload-Endpoint JWT-geschützt: `get_current_user` Dependency
- [x] Chat-History und materialName persistieren in localStorage (useChat.ts)
- [x] PDF-Badge im Chat klickbar: öffnet PDF im neuen Tab via Blob-URL
- [ ] Chat-Filter anpassen: Nachrichten filtern/sortieren
- [ ] PDF: Seitenbereich-Auswahl beim Upload (z.B. "Seite 1-50") für große PDFs

---

## PDF: Ganze Datei vs. einzelne Seite senden

### Option A: Nur eine Seite senden

**Vorteile:**
- Kleinere Datei → schnellerer Upload
- Weniger Backend-Arbeit

**Nachteile:**
- Frontend muss PDF parsen (braucht Library wie `pdf.js`)
- Nutzer muss wissen welche Seite relevant ist
- Kein Kontext zwischen Seiten (Seite 10 referenziert vielleicht Seite 5)
- Komplexerer Frontend-Code

### Option B: Ganzes PDF senden (aktuelles System)

**Vorteile:**
- Frontend bleibt einfach — kein PDF-Parsing
- pgvector sucht automatisch die relevanteste Seite
- Zusammenhänge zwischen Seiten bleiben erhalten
- Nutzer muss sich um nichts kümmern

**Nachteile:**
- Bei 1000 Seiten → langer Upload + viel Speicher
- Alle Seiten werden zu Vektoren → dauert lange

### Fazit
Option B bleibt besser für ein Lernmaterial-System. Optimierung: Seitenbereich beim Upload wählbar machen (z.B. "Seite 1-50") statt immer das komplette PDF zu verarbeiten.

---

## Hinweis: Server-RAM vs. Browser-RAM

`await file.read()` lädt die PDF-Bytes in den Arbeitsspeicher des laufenden uvicorn/Python-Prozesses — das ist Server-RAM, nicht der RAM des Computers auf dem der Browser läuft. Der Browser schickt die Datei nur über HTTP und hält danach keine Kopie mehr.
