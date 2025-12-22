# Contributing

## Setup
- Python ≥ 3.10 (mit Tkinter)
- Optional für PDF→Image OCR: Poppler (`pdfinfo`) + `pdf2image`
- Optional für OCR: `unstructured`, `paddleocr`

Install:
```bash
pip install -r requirements.txt
```

## Run
```bash
python ollama_translator_gui.py
```
Ollama muss erreichbar sein (Default: `http://localhost:11434/api`).

## Tests
```bash
python -m unittest
```
Hinweis: Tests initialisieren Tkinter; auf Linux kann ein X-Server nötig sein (CI nutzt `xvfb`).

## Code Style / Lint
CI nutzt `ruff` (minimal: Syntax/Undefined). Lokal:
```bash
ruff check .
```

## Packaging
- Build via `pyinstaller ollama_translator_gui.spec`
- Windows Convenience: `.\tools\build.ps1`

## Pull Request Checklist
- [ ] Tests laufen lokal (`python -m unittest`)
- [ ] Keine Secrets/PII im Log oder in Testdaten
- [ ] README/Changelog aktualisiert (wenn user-facing Änderungen)

