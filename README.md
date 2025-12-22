# Ollama Translator GUI (Tkinter)

Grafische Oberfläche für Übersetzungen mit lokalen Ollama-Modellen. Die App kann PDF-Dateien per OCR (PaddleOCR + unstructured) vorbereiten und den erkannten Text an das ausgewählte LLM senden.

![GUI Screenshot](docs/screenshot.png) <!-- Platzhalter: durch echten Screenshot/Demo ersetzen -->

## Funktionen
- Modellverwaltung: Modelle laden, aktivieren/deaktivieren.
- Übersetzung DE↔EN im Streaming-Modus; Abbrechen möglich.
- Datei-Import/Export: `.txt`, `.md`, `.docx`, `.pdf` (PDF mit OCR), Kopieren in die Zwischenablage.
- OCR-Qualität umschaltbar: „präzise“ (unstructured + PaddleOCR) oder „schnell“ (reines Textextrahieren).
- Fortschrittsanzeige inkl. Abbrechen für mehrseitige PDF-OCR.
- Manueller „Ollama Check“-Button prüft `/api/tags` und listet Modelle.
- Optionales Datei-Logging mit Rotations-Log unter `~/.ollama_translator.log`.
- Themes (hell/dunkel), speichert Einstellungen (Endpoint, Richtung, letztes Modell, Theme) im Home-Verzeichnis.
- Tastenkürzel: `Ctrl+Enter` Übersetzen, `Esc` Abbrechen, `Ctrl+L` Eingabe löschen, `Ctrl+T` Theme, `Ctrl+R` Modelle neu laden.

## Voraussetzungen
- Python ≥ 3.10 mit Tkinter.
- Ollama installiert und in `PATH`; der Dienst `ollama serve` muss erreichbar sein.
- Abhängigkeiten: siehe `requirements.txt` (u.a. `requests`, `pypdf`, `pdf2image`, `Pillow`, `unstructured`, `paddleocr`, `python-docx`, `fpdf2`).
- Poppler wird für `pdf2image` benötigt (systemweit installiert).

## Getting Started
1) Abhängigkeiten installieren
   ```bash
   pip install -r requirements.txt
   ```
2) Poppler installieren (für PDF→Image OCR)
   - Windows: https://github.com/oschwartz10612/poppler-windows (bin-Verzeichnis zu `PATH` hinzufügen)
     - Alternativ: `POPPLER_PATH` auf das Poppler `bin`-Verzeichnis setzen.
   - macOS: `brew install poppler`
   - Linux: Paket `poppler-utils`
3) Ollama-Dienst sicherstellen
   ```bash
   ollama serve
   ```
   Die GUI prüft beim Start per Healthcheck (`/api/tags`), ob der Endpoint (Standard `http://localhost:11434/api`) erreichbar ist.
4) App starten
   ```bash
   python ollama_translator_gui.py
   ```

## Tests
```bash
python -m unittest
```
Die Tests mocken Netzwerk und Dialoge, benötigen aber eine lauffähige Python/Tkinter-Umgebung. Auf Linux kann für Tkinter-Tests ein X-Server nötig sein (CI nutzt `xvfb`).

## Build / Release
- Standard:
  ```bash
  pyinstaller ollama_translator_gui.spec
  ```
- Windows (PowerShell):
  ```powershell
  .\tools\build.ps1
  ```

Hinweise:
- Poppler ist zur Laufzeit für PDF→Image OCR (`pdf2image`) erforderlich. Entweder `pdfinfo(.exe)` in `PATH` oder `POPPLER_PATH` setzen.
- Optionale Features (OCR via `unstructured`/`paddleocr`) werden nur mitgebaut, wenn die Pakete beim Build installiert sind.

## Datenschutz & Sicherheit
- Die Anwendung sendet den eingegebenen Text an den konfigurierten Ollama-Endpoint (standardmäßig lokal: `http://localhost:11434/api`).
- Optionaler *Sicherheitsmodus* maskiert E-Mail-Adressen und Telefonnummern vor dem Senden.
- Optionales Datei-Logging schreibt Metadaten (z.B. Dauer/Fehler) lokal unter `~/.ollama_translator.log`.
- *Offline-Queue* speichert Anfragen lokal, falls Ollama nicht erreichbar ist (Datei im Home-Verzeichnis).

## Bekannte Stolpersteine
- Poppler fehlt: `pdf2image` kann keine Seiten rendern → Poppler installieren und `PATH`/`POPPLER_PATH` setzen.
- PaddleOCR bzw. unstructured nicht installiert: PDF-OCR fällt auf einfaches Text-Extract zurück.
- Ollama nicht im `PATH` oder nicht laufend: Healthcheck schlägt fehl; im Fehlerdialog wird der Endpoint angezeigt.

## Lizenz
Siehe `LICENSE`.

## Roadmap
Siehe `tasks.md`.

