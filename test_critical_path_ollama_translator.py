import unittest
import threading
import time
import os
import json
from unittest.mock import patch, MagicMock
import tkinter as tk
from ollama_translator_gui import OllamaTranslatorApp

class TestCriticalPathOllamaTranslator(unittest.TestCase):
    def setUp(self):
        # Setup Tkinter root and app instance
        self.root = tk.Tk()
        self.app = OllamaTranslatorApp(self.root)
        # Patch messagebox to prevent actual dialogs during tests
        patcher = patch('ollama_translator_gui.messagebox')
        self.mock_messagebox = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.root.destroy()

    def test_start_ollama_server_already_running(self):
        with patch('ollama_translator_gui.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            self.app.start_ollama_server()
            # Should print "Ollama server already running."
            mock_get.assert_called()

    def test_start_ollama_server_not_running(self):
        with patch('ollama_translator_gui.requests.get', side_effect=Exception("Connection error")) as mock_get, \
             patch('ollama_translator_gui.subprocess.Popen') as mock_popen, \
             patch('ollama_translator_gui.time.sleep', return_value=None):
            mock_popen.return_value = None
            self.app.start_ollama_server()
            mock_popen.assert_called()

    def test_refresh_and_activate_models(self):
        # Mock API response for models
        models_response = {
            "models": [{"name": "model1"}, {"name": "model2"}]
        }
        with patch('ollama_translator_gui.requests.get') as mock_get, \
             patch.object(self.app.api_endpoint_var, 'get', return_value="http://localhost:11434/api"):
            mock_get.return_value.json.return_value = models_response
            mock_get.return_value.status_code = 200
            self.app._fetch_models_thread()
            # Wait for GUI update
            self.root.update()
            self.assertIn("model1", self.app.available_models_listbox.get(0, tk.END))
            self.assertIn("model2", self.app.available_models_listbox.get(0, tk.END))

        # Activate model
        self.app.available_models_listbox.selection_set(0)
        self.app.activate_model()
        self.assertEqual(self.app.active_model, "model1")
        self.assertEqual(self.app.active_model_label.cget("text"), "model1")

    def test_start_and_cancel_translation(self):
        # Setup active model and input text
        self.app.active_model = "model1"
        self.app.input_text.insert('1.0', "Test input")
        self.app.update_translate_button_state()

        # Patch requests.post to simulate streaming response
        def fake_iter_lines():
            yield json.dumps({"response": "Hello"}).encode('utf-8')
            yield json.dumps({"response": " World"}).encode('utf-8')
            yield json.dumps({"done": True}).encode('utf-8')

        mock_response = MagicMock()
        mock_response.iter_lines = fake_iter_lines
        mock_response.raise_for_status = lambda: None

        with patch('ollama_translator_gui.requests.post', return_value=mock_response):
            self.app.start_translation()
            # Allow some time for thread to process
            time.sleep(0.5)
            # Cancel translation
            self.app.cancel_translation()
            # Check that cancel button is disabled
            self.assertEqual(self.app.cancel_button['state'], 'disabled')

    def test_upload_and_save_txt(self):
        # Patch filedialog.askopenfilename and asksaveasfilename
        with patch('ollama_translator_gui.filedialog.askopenfilename', return_value='test_input.txt'), \
             patch('builtins.open', unittest.mock.mock_open(read_data="Hello world")) as mock_file:
            self.app.upload_txt()
            self.assertEqual(self.app.input_text.get('1.0', 'end-1c'), "Hello world")

        with patch('ollama_translator_gui.filedialog.asksaveasfilename', return_value='test_output.txt'), \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.app.output_text.config(state=tk.NORMAL)
            self.app.output_text.delete('1.0', tk.END)
            self.app.output_text.insert('1.0', "Translated text")
            self.app.output_text.config(state=tk.DISABLED)
            self.app.save_txt()
            mock_file.assert_called_with('test_output.txt', 'w', encoding='utf-8')

    def test_toggle_theme_and_config_persistence(self):
        # Test toggle theme changes current_theme
        initial_theme = self.app.current_theme
        self.app.toggle_theme()
        self.assertNotEqual(self.app.current_theme, initial_theme)

        # Test config save and load
        config_path = os.path.join(os.path.expanduser("~"), ".ollama_translator_config.json")
        test_config = {
            "theme": "dark",
            "api_endpoint": "http://test-endpoint",
            "direction": "en-de",
            "last_model": "model1"
        }
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))) as mock_open, \
             patch('json.load', return_value=test_config), \
             patch.object(self.app.api_endpoint_var, 'get', return_value="http://test-endpoint"):
            self.app._load_config()
            self.assertEqual(self.app.current_theme, "dark")
            self.assertEqual(self.app.api_endpoint_var.get(), "http://test-endpoint")
            self.assertEqual(self.app.direction_var.get(), "en-de")
            self.assertEqual(self.app.active_model, "model1")

        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.app._save_config()
            mock_file.assert_called_with(config_path, 'w', encoding='utf-8')

import tkinter as tk
from unittest.mock import patch, MagicMock
import json
import os

class TestThoroughOllamaTranslator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = OllamaTranslatorApp(self.root)
        patcher = patch('ollama_translator_gui.messagebox')
        self.mock_messagebox = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.root.destroy()

    def test_keyboard_shortcuts(self):
        # Insert some text to enable translate button
        self.app.active_model = "model1"
        self.app.input_text.insert('1.0', "Test")
        self.app.update_translate_button_state()

        # Simulate Ctrl+Return (translate)
        event = MagicMock()
        self.app._keyboard_translate()
        self.assertEqual(self.app.translate_button['state'], 'disabled')

        # Simulate Escape (cancel)
        self.app.translation_controller = {'abort': False}
        self.app._keyboard_cancel()
        self.assertTrue(self.app.translation_controller['abort'])

        # Simulate Ctrl+L (clear input)
        self.app._keyboard_clear_input()
        self.assertEqual(self.app.input_text.get('1.0', 'end-1c'), '')

        # Simulate Ctrl+T (toggle theme)
        current_theme = self.app.current_theme
        self.app._keyboard_toggle_theme()
        self.assertNotEqual(self.app.current_theme, current_theme)

        # Simulate Ctrl+R (refresh models)
        with patch.object(self.app, 'refresh_available_models') as mock_refresh:
            self.app._keyboard_refresh_models()
            mock_refresh.assert_called_once()

    def test_translation_edge_cases(self):
        # No active model
        self.app.active_model = None
        self.app.input_text.insert('1.0', "Test")
        with patch('ollama_translator_gui.messagebox.showerror') as mock_error:
            self.app.start_translation()
            mock_error.assert_called_with("Error", "No model selected for translation.")

        # Empty input
        self.app.active_model = "model1"
        self.app.input_text.delete('1.0', tk.END)
        with patch('ollama_translator_gui.messagebox.showerror') as mock_error:
            self.app.start_translation()
            mock_error.assert_called_with("Error", "Input text cannot be empty.")

    def test_activate_model_edge_cases(self):
        # No selection
        self.app.available_models_listbox.selection_clear(0, tk.END)
        with patch('ollama_translator_gui.messagebox.showwarning') as mock_warning:
            self.app.activate_model()
            mock_warning.assert_called_with("No Selection", "Please select a model from the 'Available Models' list.")

        # Invalid selection
        self.app.available_models_listbox.insert(tk.END, "Loading...")
        self.app.available_models_listbox.selection_set(tk.END)
        with patch('ollama_translator_gui.messagebox.showwarning') as mock_warning:
            self.app.activate_model()
            mock_warning.assert_called_with("Invalid Selection", "Please wait for models to load or select a valid model.")

    def test_error_handling_in_translation(self):
        self.app.active_model = "model1"
        self.app.input_text.insert('1.0', "Test")

        with patch('ollama_translator_gui.requests.post', side_effect=Exception("API failure")), \
             patch('ollama_translator_gui.messagebox.showerror') as mock_error:
            self.app.start_translation()
            time.sleep(0.5)
            mock_error.assert_called()

    def test_file_io_edge_cases(self):
        # Upload file cancel
        with patch('ollama_translator_gui.filedialog.askopenfilename', return_value=''), \
             patch('ollama_translator_gui.messagebox.showerror') as mock_error:
            self.app.upload_txt()
            mock_error.assert_not_called()

        # Save file cancel
        with patch('ollama_translator_gui.filedialog.asksaveasfilename', return_value=''), \
             patch('ollama_translator_gui.messagebox.showwarning') as mock_warning:
            self.app.output_text.config(state=tk.NORMAL)
            self.app.output_text.delete('1.0', tk.END)
            self.app.output_text.insert('1.0', "Some text")
            self.app.output_text.config(state=tk.DISABLED)
            self.app.save_txt()
            mock_warning.assert_not_called()

    def test_theme_application_effects(self):
        # Check that theme colors are applied to widgets
        self.app.current_theme = "light"
        self.app.apply_theme()
        self.assertEqual(self.app.root.cget("bg"), "#f0f0f0")

        self.app.current_theme = "dark"
        self.app.apply_theme()
        self.assertEqual(self.app.root.cget("bg"), "#333333")

if __name__ == "__main__":
    unittest.main()
