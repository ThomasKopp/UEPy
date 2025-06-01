# Ollama Translator GUI

A user-friendly desktop application for translating text using Ollama's local language models. This application provides a simple graphical interface to interact with Ollama's API for translation tasks.

## Features

- **Local Translation**: Utilizes Ollama's local language models for private, offline-capable translations
- **Dark/Light Theme**: Toggle between light and dark themes for comfortable usage in any environment
- **Model Management**: Easily switch between different Ollama models
- **File Support**: Translate text directly from files
- **Clipboard Integration**: Copy translations to clipboard with a single click
- **Responsive UI**: Clean and intuitive interface built with Tkinter

## Prerequisites

- Python 3.6 or higher
- Ollama installed and running locally (default: http://localhost:11434)
- Required Python packages (install via `pip install -r requirements.txt`)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure Ollama is running on your system

## Usage

1. Run the application:
   ```
   python ollama_translator_gui.py
   ```
2. Select your preferred Ollama model from the dropdown
3. Enter the text you want to translate in the input area
4. Click the "Translate" button
5. View the translation in the output area

### File Translation

1. Click the "Open File" button
2. Select a text file to translate
3. The content will be loaded into the input area
4. Click "Translate" to process the content

## Building the Application

To create a standalone executable:

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   pyinstaller --onefile --windowed ollama_translator_gui.py
   ```
3. The executable will be in the `dist` directory

## Requirements

- requests
- tkinter (usually comes with Python)

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please open an issue in the repository or contact the maintainers.

---

*Note: This application requires Ollama to be installed and running locally. For more information about Ollama, visit [ollama.ai](https://ollama.ai/).*
