# Ollama Translator GUI (Tkinter)

Grafische Oberfläche für Übersetzungen mit lokalen Ollama‑Modellen. Die App kann PDF-Dateien per OCR (PaddleOCR + unstructured) vorbereiten und den erkannten Text an das gewählte LLM senden.

## Funktionen
- Modellverwaltung: Modelle laden, aktivieren/deaktivieren.
- Übersetzung DE↔EN im Streaming-Modus; Abbrechen möglich.
- Datei-Import/Export: `.txt` und `.pdf` (PDF mit OCR), Kopieren in die Zwischenablage.
- Themes (hell/dunkel), speichert Einstellungen (Endpoint, Richtung, letztes Modell, Theme) im Home-Verzeichnis.
- Tastenkürzel: `Ctrl+Enter` Übersetzen, `Esc` Abbrechen, `Ctrl+L` Eingabe löschen, `Ctrl+T` Theme, `Ctrl+R` Modelle neu laden.

## Voraussetzungen
- Python ≥3.10 mit Tkinter.
- Ollama installiert und in `PATH` (`ollama serve` muss startbar sein).
- Abhängigkeiten: `requests`, `PyPDF2`, `unstructured`, `paddleocr`, `pdf2image`, `Pillow`.
  Installation: `pip install -r requirements.txt`
  Hinweis: Für `pdf2image` wird systemweit Poppler benötigt.

## Start
```bash
python ollama_translator_gui.py
```
Die App versucht automatisch `ollama serve` zu starten. Falls nicht im `PATH`, erscheint eine Fehlermeldung.

## Nutzung
1) Endpoint und Übersetzungsrichtung wählen (Standard: `http://localhost:11434/api`, DE→EN).  
2) „Refresh“ lädt Modelle, „Activate Model“ setzt das aktive Modell.  
3) Text eingeben oder `Upload TXT` / `Upload PDF (OCR)` wählen. Bei PDF wird zuerst unstructured (OCR-only) genutzt, danach PaddleOCR, zuletzt schlichtes Text-Extract.  
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
Ergebnis liegt in `dist/`.

## Bekannte Stolpersteine
- Poppler fehlt: `pdf2image` kann keine Seiten rendern → bitte Poppler installieren.  
- PaddleOCR bzw. unstructured nicht installiert: PDF-OCR fällt auf einfaches Text-Extract zurück.  
- Ollama nicht im `PATH`: automatischer Start scheitert.

## Lizenz
Keine Lizenzdatei im Repo hinterlegt; vor Weitergabe/Nutzung klären.
