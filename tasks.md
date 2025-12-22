# Aufgaben & Fortschritt (Stand 22.12.2025)

## Sofort angehen
- [x] README in UTF-8 speichern und fehlerhafte Umlaute bereinigen.
- [x] Abschnitt "Getting started" ergänzen: Python 3.10+, `pip install -r requirements.txt`, Poppler-Installationshinweis für Windows/macOS/Linux.
- [x] Hinweis aufnehmen, dass `ollama serve` erreichbar sein muss; Healthcheck vor UI-Start einbauen und klare Fehlermeldung anzeigen.
- [x] Screenshot-Link in README ergänzen (aktuell Platzhalter: `docs/screenshot.png`).
- [ ] Tatsächlichen Screenshot/Demo-GIF unter `docs/` hinzufügen.

## Funktionale Verbesserungen (Prio)
- [x] Export-Formate: zusätzlich `.md` / `.docx`; beim PDF-Export optional Seitenreferenzen.
- [x] Prompt-Profile: vordefinierte Übersetzungsstile (wörtlich, frei, formal, kreativ) pro Richtung.

## Funktionale Verbesserungen
- [x] Schaltfläche "Ollama check": `/api/tags` abrufen, Modelle und Laufzeitstatus anzeigen.
- [x] Fortschrittsanzeige für OCR-Pipeline (mehrseitige PDFs) und Abbruchknopf für lang laufende OCR.
- [x] OCR-Qualitätsoptionen: "schnell" (nur Text-Extract) vs. "präzise" (unstructured + PaddleOCR).
- [x] Optionales Logging in Datei (Timestamp, Modell, Dauer, Quelle, Fehler) mit Log-Rotation.
- [x] Batch-Übersetzung: mehrere Dateien/Absätze in Warteschlange und gesammelt exportieren.
- [x] Glossar/Terminologie: benutzerdefiniertes Wörterbuch (CSV/JSON) für erzwungene Übersetzungen / Do-not-translate.
- [x] Qualitätsrückmeldung: Button "Bewerten" mit Logging, optional Revisions-Prompt.
- [x] Auto-Detect Language: Sprache erkennen und Richtung automatisch setzen (mit Rückfrage).
- [x] Kontext-History: letzte N Übersetzungen anzeigen, Copy/Retry.
- [x] Benutzerdefinierte Shortcuts: Hotkeys im Einstellungsdialog speichern.
- [x] Modell-Settings: Temperature/Top-p/Max tokens im UI, pro Modell persistent.
- [x] Offline-Fallback: wenn Ollama nicht erreichbar, Text lokal speichern und später senden.
- [x] Fortschrittsdetails Übersetzung: Zeit-/Seitencounter, geschätzte Restzeit bei Streams.
- [x] Theme-Auto: Dark/Light anhand System oder Tageszeit.
- [x] Sicherheitsmodus: sensible Daten maskieren (E-Mail, Telefonnummern) vor dem Senden.

## Stabilität & Tests
- [x] Unittests für OCR-Fallback-Kette (ohne echte OCR mittels Mocks).
- [x] Tests für Cancel-Flow im Streaming-Modus.
- [x] Lint/Unit-CI z.B. via GitHub Actions (Windows + Linux Matrix).
- [ ] Tests: Batch-Queue (Add/Remove/Clear/Run) ohne Netzwerk (Mocks für `requests.post`).
- [ ] Tests: Glossar/Do-not-translate (Platzhalter-Logik, Roundtrip, Edge-Cases wie Overlaps).
- [ ] Tests: Export (MD/DOCX/PDF) – zumindest Smoke-Tests (Dateien erzeugt, nicht leer).
- [ ] Test: Offline-Queue (Store/Load/Process) ohne echte Ollama-Instanz.

## Packaging
- [x] Poppler-Check in Build-Skripten dokumentieren; Download-Link für Windows beilegen.
- [x] PyInstaller-Config auf Abhängigkeiten prüfen (paddleocr, unstructured) und README-Abschnitt "Build/Release" erweitern.
- [ ] `tools/build.ps1`: Option `-Clean` (PyInstaller `--clean`) und Ausgabe-Ordner optional timestamped.
- [ ] `tools/build.ps1`: Erkennen, ob venv aktiv ist; ggf. Warnung/Anleitung.
- [ ] Release-Artefakte: `dist/` mit `LICENSE`, `README.md` und Beispiel-Konfig (optional) bundlen.

## Dokumentation & Meta
- [x] README: Abhängigkeiten konsistent benennen (z.B. `pypdf` statt `PyPDF2`).
- [x] Lizenz klären und Datei hinzufügen.
- [x] Roadmap-Abschnitt im README mit nächsten Milestones verlinken.
- [x] `CHANGELOG.md` einführen (SemVer + Release-Notes pro Version).
- [x] `CONTRIBUTING.md` (Setup, Tests, Code-Style, PR-Checkliste).
- [x] Kurzer Datenschutz-/Sicherheits-Hinweis in README (welche Daten an Ollama gesendet werden; Masking-Optionen).
- [x] Screenshot/Demo aktualisieren (aktuell Platzhalter unter `docs/screenshot.png`).

## Erweiterungen (Vorschläge)
### UX / Bedienung
- [ ] Drag & Drop für `.txt`/`.pdf` in Input (Windows + Linux).
- [ ] Fenstergröße/Position persistent speichern.
- [ ] Schriftgröße (UI + Output) als Setting; optional „Monospace Output“ Toggle.
- [ ] Output-Tools: „Suchen/Ersetzen“, „Copy as Markdown“, Wort-/Zeichen-/Token-Schätzung.

### Übersetzen / Prompting
- [ ] Mehr Sprachpaare (nicht nur DE↔EN): Dropdown für `source_lang`/`target_lang`, Auto-Detect beibehalten.
- [ ] Prompt-Profile editierbar (User-defined Profile speichern/teilen).
- [ ] „Terminologie prüfen“: Warnung, wenn Glossar-Einträge im Output fehlen.

### OCR / Dokumente
- [ ] OCR: Sprache manuell auswählbar (deu/eng/deu+eng) als Override.
- [ ] OCR: Pre-/Postprocessing UI-Toggles sichtbar machen (Cleanup, Preprocess, DPI), inkl. „Reset defaults“.
- [ ] PDF: Option „Nur erste N Seiten“ für schnelle Vorschau/OCR.

### Performance / Robustheit
- [ ] Streaming: robustere JSON-Line-Parsing-Fehlerbehandlung (Teilchunks/Keepalive).
- [ ] Chunking: smartere Segmentierung (Absatz-/Satzgrenzen), stabile Kontext-Übergabe.
- [ ] Telemetrie lokal: „Bug-Report erstellen“ (Log + anonymisierte Config + Systeminfo als ZIP).

## Hinweis
- Wenn Umlaute in PowerShell kaputt aussehen: Datei ist UTF‑8; in Windows PowerShell 5 z.B. `Get-Content -Encoding utf8 tasks.md` verwenden.
