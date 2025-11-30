# Ollama Translator GUI (Tkinter)

Grafische Übersetzungsoberfläche für lokale Ollama-Modelle. Die App sucht bei Bedarf den Ollama‑Daemon, holt verfügbare Modelle ab, streamt Übersetzungen und bietet Dark/Light‑Theme, Datei‑I/O sowie Tastenkürzel.

## Funktionen
- Modellverwaltung: Liste laden, Modell aktivieren/deaktivieren.
- Übersetzung DE↔EN per Streaming; Abbrechen möglich.
- Datei‑Import/Export (`.txt`), Kopieren in die Zwischenablage.
- Themes umschalten, Einstellungen (API‑Endpoint, Richtung, letztes Modell, Theme) werden im Home-Verzeichnis gespeichert.
- Tastenkürzel: `Ctrl+Enter` Übersetzen, `Esc` Abbrechen, `Ctrl+L` Eingabe löschen, `Ctrl+T` Theme, `Ctrl+R` Modelle neu laden.

## Voraussetzungen
- Python ≥3.10 (Tkinter muss installiert sein; unter Windows üblicherweise enthalten).
- Ollama installiert und in `PATH` (`ollama serve` muss starten können).
- Abhängigkeiten: `requests` (GUI nutzt außerdem Standardbibliothek/Tkinter).  
  Installation: `pip install -r requirements.txt`

## Start
```bash
python ollama_translator_gui.py
```
Die App versucht automatisch `ollama serve` zu starten. Läuft Ollama nicht oder ist nicht im `PATH`, erscheint eine Fehlermeldung.

## Nutzung
1) Endpoint und Übersetzungsrichtung wählen (Standard: `http://localhost:11434/api`, DE→EN).  
2) „Refresh“ lädt Modelle, „Activate Model“ setzt das aktive Modell.  
3) Text eingeben oder `Upload TXT`.  
4) „Translate“ oder `Ctrl+Enter` starten; Ausgabe erscheint gestreamt.  
5) Mit „Cancel“ bzw. `Esc` abbrechen, „Save TXT“ speichern, „Copy“ kopieren.  
6) Theme via Button oder `Ctrl+T` wechseln.

## Tests
Unittests:  
```bash
python -m unittest test_critical_path_ollama_translator.py
```  
Hinweis: Die Tests erzeugen Tkinter-Fenster und mocken Netzwerk/Messageboxen; sie benötigen eine funktionierende Python/Tkinter-Installation.

## Build (optional)
Ein Windows-Executable kann mit PyInstaller erstellt werden:  
```bash
pyinstaller --onefile --windowed ollama_translator_gui.py
```  
Ergebnis liegt im Verzeichnis `dist/`.

## Bekannte Stolpersteine
- Kein Python/Tkinter im System-PATH → Programm/Tests starten nicht.  
- Ollama nicht installiert oder nicht im `PATH` → Start des Daemons schlägt fehl.  
- Models leer → API-Endpunkt prüfen (`/api/tags` muss erreichbar sein).

## Lizenz
Im Repository liegt keine Lizenzdatei; vor Weitergabe/Nutzung bitte klären.
