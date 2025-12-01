# Ollama Translator GUI (Tkinter)

Grafische Oberfläche für Übersetzungen mit lokalen Ollama-Modellen. Die App kann PDF-Dateien per OCR (PaddleOCR + unstructured) vorbereiten und den erkannten Text an das ausgewählte LLM senden.

![GUI Screenshot](docs/screenshot.png) <!-- Platzhalter: Bild/GIF später ergänzen -->

## Funktionen
- Modellverwaltung: Modelle laden, aktivieren/deaktivieren.
- Übersetzung DE⇄EN im Streaming-Modus; Abbrechen möglich.
- Datei-Import/Export: `.txt` und `.pdf` (PDF mit OCR), Kopieren in die Zwischenablage.
- OCR-Qualität umschaltbar: „präzise“ (unstructured + PaddleOCR) oder „schnell“ (reines Textextrahieren).
- Fortschrittsanzeige inkl. Abbrechen für mehrseitige PDF-OCR.
- Manueller „Ollama Check“-Button prüft `/api/tags` und listet Modelle.
- Optionales Datei-Logging mit Rotations-Log unter `~/.ollama_translator.log`.
- Themes (hell/dunkel), speichert Einstellungen (Endpoint, Richtung, letztes Modell, Theme) im Home-Verzeichnis.
- Tastenkürzel: `Ctrl+Enter` Übersetzen, `Esc` Abbrechen, `Ctrl+L` Eingabe löschen, `Ctrl+T` Theme, `Ctrl+R` Modelle neu laden.

## Voraussetzungen
- Python ≥ 3.10 mit Tkinter.
- Ollama installiert und in `PATH`; der Dienst `ollama serve` muss erreichbar sein.
- Abhängigkeiten: `requests`, `PyPDF2`, `unstructured`, `paddleocr`, `pdf2image`, `Pillow`.
- Poppler wird für `pdf2image` benötigt (systemweit installiert).

## Getting Started
1) Abhängigkeiten installieren  
   ```bash
   pip install -r requirements.txt
   ```
   Poppler-Installation:
   - Windows: https://github.com/oschwartz10612/poppler-windows (bin-Verzeichnis zum `PATH` hinzufügen)
   - macOS: `brew install poppler`
   - Linux: Paket `poppler-utils`
2) Ollama-Dienst sicherstellen  
   ```bash
   ollama serve
   ```
   Die GUI prüft beim Start per Healthcheck (`/api/tags`), ob der Endpoint (Standard `http://localhost:11434/api`) erreichbar ist. Bei Fehler erscheint eine klare Fehlermeldung.
3) App starten  
   ```bash
   python ollama_translator_gui.py
   ```

## Nutzung
1) Endpoint und Übersetzungsrichtung wählen (Standard: `http://localhost:11434/api`, DE→EN).  
2) „Refresh“ lädt Modelle, „Activate Model“ setzt das aktive Modell.  
3) Text eingeben oder `Upload TXT` / `Upload PDF (OCR)` wählen. Bei PDF: zuerst unstructured (OCR-only), dann PaddleOCR, zuletzt reines Text-Extract.  
4) „Translate“ oder `Ctrl+Enter` starten; Ausgabe wird gestreamt.  
5) Mit „Cancel“ bzw. `Esc` abbrechen, „Save TXT“ speichern, „Copy“ kopieren.  
6) Theme via Button oder `Ctrl+T` wechseln.

## Tests
```bash
python -m unittest test_critical_path_ollama_translator.py
```
Die Tests mocken Netzwerk und Dialoge, benötigen aber eine lauffähige Python/Tkinter-Umgebung.

## Build (optional)
```bash
pyinstaller --onefile --windowed ollama_translator_gui.py
```
Das Ergebnis liegt in `dist/`. Poppler muss zur Laufzeit vorhanden sein, OCR-Abhängigkeiten müssen in der Umgebung installiert sein.

## Bekannte Stolpersteine
- Poppler fehlt: `pdf2image` kann keine Seiten rendern → Poppler installieren und `PATH` setzen.
- PaddleOCR bzw. unstructured nicht installiert: PDF-OCR fällt auf einfaches Text-Extract zurück.
- Ollama nicht im `PATH` oder nicht laufend: Healthcheck schlägt fehl; im Fehlerdialog wird der Endpoint angezeigt.

## Lizenz
Keine Lizenzdatei im Repo hinterlegt; vor Weitergabe/Nutzung klären.
