# Aufgaben & Fortschritt (Stand 01.12.2025)

## Sofort angehen
- [x] README in UTF-8 speichern und fehlerhafte Umlaute bereinigen.
- [x] Abschnitt "Getting started" ergaenzen: Python 3.10+, `pip install -r requirements.txt`, Poppler-Installationshinweis fuer Windows/macOS/Linux.
- [x] Hinweis aufnehmen, dass `ollama serve` erreichbar sein muss; Healthcheck vor UI-Start einbauen und klare Fehlermeldung anzeigen.
- [x] Kurzes Demo-GIF/Screenshot der GUI in README verlinken. (Platzhalter: `docs/screenshot.png`)

## Funktionale Verbesserungen PRIO
- [x] Export-Formate: zusätzlich `.md` / `.docx`, bei PDF Export optional Seitenreferenzen.
- [x] Prompt-Profile: vordefinierte Übersetzungsstile (wörtlich, frei, formal, kreativ) pro Richtung.

## Funktionale Verbesserungen
- [x] Schaltflaeche "Ollama check": `/api/tags` abrufen, Modelle und Laufzeitstatus anzeigen.
- [x] Fortschrittsanzeige fuer OCR-Pipeline (mehrseitige PDFs) und Abbruchknopf fuer lang laufende OCR.
- [x] OCR-Qualitaetsoptionen: "schnell" (nur Text-Extract) vs. "praezise" (unstructured + PaddleOCR).
- [x] Optionales Logging in Datei (Timestamp, Modell, Dauer, Quelle, Fehler) mit Log-Rotation.
- [x] Batch-uebersetzung: mehrere Dateien/Absaetze in Warteschlange und gesammelt exportieren.
- [x] Glossar/Terminologie: benutzerdefiniertes Woerterbuch (CSV/JSON) fuer erzwungene Uebersetzungen / Do-not-translate.
- [x] Qualitaetsrueckmeldung: Button "Bewerten" mit Logging, optional Revisions-Prompt.
- [x] Auto-Detect Language: Sprache erkennen und Richtung automatisch setzen (mit Rueckfrage).
- [x] Kontext-History: letzte N Uebersetzungen anzeigen, Copy/Retry.
- [x] Benutzerdefinierte Shortcuts: Hotkeys im Einstellungsdialog speichern.
- [x] Modell-Settings: Temperature/Top-p/Max tokens im UI, pro Modell persistent.
- [x] Offline-Fallback: wenn Ollama nicht erreichbar, Text lokal speichern und spaeter senden.
- [x] Fortschrittsdetails Uebersetzung: Zeit-/Seitencounter, geschaetzte Restzeit bei Streams.
- [x] Theme-Auto: Dark/Light anhand System oder Tageszeit.
- [x] Sicherheitsmodus: sensible Daten maskieren (E-Mail, Telefonnummern) vor dem Senden.

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

