# Schwierigkeiten & TODOs

## TODOs

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
- FAISS sucht automatisch die relevanteste Seite
- Zusammenhänge zwischen Seiten bleiben erhalten
- Nutzer muss sich um nichts kümmern

**Nachteile:**
- Bei 1000 Seiten → langer Upload + viel Speicher
- Alle Seiten werden zu Vektoren → dauert lange

### Fazit
Option B bleibt besser für ein Lernmaterial-System. Optimierung: Seitenbereich beim Upload wählbar machen (z.B. "Seite 1-50") statt immer das komplette PDF zu verarbeiten.
