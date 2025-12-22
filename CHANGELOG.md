# Changelog

Das Format basiert auf "Keep a Changelog" und orientiert sich grob an SemVer.

## [Unreleased]

## [0.1.0] - 2025-12-22
### Added
- Tkinter GUI für Übersetzungen über lokale Ollama-Modelle (Streaming + Abbruch).
- PDF-Import mit OCR-Fallback-Kette (unstructured → PaddleOCR → pypdf Text-Extract) inkl. Fortschritt und Abbruch.
- Export: TXT, Markdown, DOCX, PDF (inkl. optionaler Seitenreferenzen).
- Prompt-Profile (Übersetzungsstile) pro Richtung, Auto-Detect Language, History, Batch-Queue.
- Optionales Logging (Rotationslog), Sicherheitsmodus (Masking von E-Mail/Telefon), Offline-Queue.
- CI via GitHub Actions (Lint + Unit-Tests).

