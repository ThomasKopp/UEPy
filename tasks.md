# Aufgaben & Fortschritt (Stand 01.12.2025)

## Sofort angehen
- [x] README in UTF-8 speichern und fehlerhafte Umlaute bereinigen.
- [x] Abschnitt "Getting started" ergaenzen: Python 3.10+, `pip install -r requirements.txt`, Poppler-Installationshinweis fuer Windows/macOS/Linux.
- [x] Hinweis aufnehmen, dass `ollama serve` erreichbar sein muss; Healthcheck vor UI-Start einbauen und klare Fehlermeldung anzeigen.
- [x] Kurzes Demo-GIF/Screenshot der GUI in README verlinken. (Platzhalter: `docs/screenshot.png`)

## Funktionale Verbesserungen
- [x] Schaltflaeche "Ollama check": `/api/tags` abrufen, Modelle und Laufzeitstatus anzeigen.
- [x] Fortschrittsanzeige fuer OCR-Pipeline (mehrseitige PDFs) und Abbruchknopf fuer lang laufende OCR.
- [x] OCR-Qualitaetsoptionen: "schnell" (nur Text-Extract) vs. "praezise" (unstructured + PaddleOCR).
- [x] Optionales Logging in Datei (Timestamp, Modell, Dauer, Quelle, Fehler) mit Log-Rotation.
- [ ] Batch-Übersetzung: mehrere Dateien/Absätze in Warteschlange und gesammelt exportieren.
- [ ] Glossar/Terminologie: benutzerdefiniertes Wörterbuch (CSV/JSON) für erzwungene Übersetzungen / Do-not-translate.
- [ ] Prompt-Profile: vordefinierte Übersetzungsstile (wörtlich, frei, formal, kreativ) pro Richtung.
- [ ] Qualitätsrückmeldung: Button „Bewerten“ mit Logging, optional Revisions-Prompt.
- [ ] Auto-Detect Language: Sprache erkennen und Richtung automatisch setzen (mit Rückfrage).
- [ ] Kontext-History: letzte N Übersetzungen anzeigen, Copy/Retry.
- [ ] Benutzerdefinierte Shortcuts: Hotkeys im Einstellungsdialog speichern.
- [ ] Modell-Settings: Temperature/Top‑p/Max tokens im UI, pro Modell persistent.
- [ ] Offline-Fallback: wenn Ollama nicht erreichbar, Text lokal speichern und später senden.
- [ ] Fortschrittsdetails Übersetzung: Zeit-/Seitencounter, geschätzte Restzeit bei Streams.
- [ ] Theme-Auto: Dark/Light anhand System oder Tageszeit.
- [ ] Export-Formate: zusätzlich `.md` / `.docx`, bei PDF Export optional Seitenreferenzen.
- [ ] Sicherheitsmodus: sensible Daten maskieren (E-Mail, Telefonnummern) vor dem Senden.

## Stabilitaet & Tests
- [ ] Unittests fuer OCR-Fallback-Kette (ohne echte OCR mittels Mocks).
- [ ] Tests fuer Cancel-Flow im Streaming-Modus.
- [ ] Lint/Unit-CI z.B. via GitHub Actions (Windows + Linux Matrix).

## Packaging
- [ ] Poppler-Check in Build-Skripten dokumentieren; Download-Link fuer Windows beilegen.
- [ ] PyInstaller-Config auf Abhaengigkeiten pruefen (paddleocr, unstructured) und README-Abschnitt "Build/Release" erweitern.

## Dokumentation & Meta
- [ ] Lizenz klaeren und Datei hinzufuegen.
- [ ] Roadmap-Abschnitt im README mit naechsten Milestones verlinken.
