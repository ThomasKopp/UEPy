import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import json
import subprocess
import os

# Import Style
from tkinter.ttk import Style

# Default Ollama API endpoint
OLLAMA_API_BASE_URL = "http://localhost:11434/api"

# --- Theme Definitions ---
LIGHT_THEME = {
    "bg": "#f0f0f0",
    "fg": "#000000",
    "select_bg": "#c3c3c3",
    "select_fg": "#000000",
    "button_bg": "#e1e1e1",
    "button_fg": "#000000",
    "entry_bg": "#ffffff",
    "entry_fg": "#000000",
    "disabled_fg": "#a3a3a3",
    "error_fg": "red",
    "active_model_fg": "black",
    "inactive_model_fg": "grey"
}

DARK_THEME = {
    "bg": "#333333",
    "fg": "#ffffff",
    "select_bg": "#555555",
    "select_fg": "#ffffff",
    "button_bg": "#555555",
    "button_fg": "#ffffff",
    "entry_bg": "#444444",
    "entry_fg": "#ffffff",
    "disabled_fg": "#888888",
    "error_fg": "#ff8080", # Lighter red for dark bg
    "active_model_fg": "white",
    "inactive_model_fg": "#aaaaaa"
}

class OllamaTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Translator (Python)")
        # self.root.geometry("800x600") # Optional: Set initial size

        self.active_model = None
        self.translation_controller = None # To hold the AbortController equivalent

        # --- Theme Setup ---
        self.style = Style(root)
        self.current_theme = "light" # Start with light theme
        self.apply_theme()

        # --- Main Frames ---
        self.header_frame = ttk.Frame(root, padding="10")
        self.header_frame.grid(row=0, column=0, sticky="ew")

        self.model_mgmt_frame = ttk.LabelFrame(root, text="Model Management", padding="10")
        self.model_mgmt_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.translation_frame = ttk.LabelFrame(root, text="Translation", padding="10")
        self.translation_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        self.progress_frame = ttk.Frame(root, padding="10")
        self.progress_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.footer_frame = ttk.Frame(root, padding="10")
        self.footer_frame.grid(row=4, column=0, sticky="ew")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1) # Allow translation frame to expand vertically
        self.translation_frame.columnconfigure(0, weight=1)
        self.translation_frame.columnconfigure(1, weight=1)
        self.translation_frame.rowconfigure(1, weight=1) # Allow text areas to expand

        self.create_header_widgets()
        self.create_model_management_widgets()
        self.create_translation_widgets()
        self.create_progress_widgets()
        self.create_footer_widgets()

        # Initial actions
        self.start_ollama_server()
        self.refresh_available_models()

    # --- Theme Management ---
    def apply_theme(self):
        theme = LIGHT_THEME if self.current_theme == "light" else DARK_THEME

        # Configure root window background
        self.root.config(bg=theme["bg"])

        # Configure ttk styles
        self.style.theme_use('clam') # Use a theme that allows more customization

        self.style.configure('.', background=theme["bg"], foreground=theme["fg"],
                             fieldbackground=theme["entry_bg"], selectbackground=theme["select_bg"],
                             selectforeground=theme["select_fg"])
        self.style.map('.', background=[('active', theme["select_bg"])])

        self.style.configure('TButton', background=theme["button_bg"], foreground=theme["button_fg"])
        self.style.map('TButton', background=[('active', theme["select_bg"]), ('disabled', theme["bg"])],
                                  foreground=[('disabled', theme["disabled_fg"])])

        self.style.configure('TLabel', background=theme["bg"], foreground=theme["fg"])
        self.style.configure('TFrame', background=theme["bg"])
        self.style.configure('TLabelframe', background=theme["bg"], foreground=theme["fg"])
        self.style.configure('TLabelframe.Label', background=theme["bg"], foreground=theme["fg"])
        self.style.configure('TCombobox', fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"],
                             selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
        self.style.map('TCombobox', fieldbackground=[('readonly', theme["entry_bg"])],
                                  selectbackground=[('readonly', theme["select_bg"])],
                                  selectforeground=[('readonly', theme["select_fg"])])
        # Removed attempt to style TCombobox.downarrow as it was unreliable
        self.style.configure('TProgressbar', background=theme["button_bg"], troughcolor=theme["entry_bg"]) 

        # Configure non-ttk widgets (Text, Listbox)
        # Note: tk.Text does not support 'disabledbackground'
        text_config = {"background": theme["entry_bg"], "foreground": theme["entry_fg"],
                       "insertbackground": theme["fg"], "selectbackground": theme["select_bg"],
                       "selectforeground": theme["select_fg"]}
        listbox_config = {"background": theme["entry_bg"], "foreground": theme["entry_fg"],
                          "selectbackground": theme["select_bg"], "selectforeground": theme["select_fg"]}

        # Apply to existing widgets if they exist
        if hasattr(self, 'input_text'): self.input_text.config(**text_config)
        if hasattr(self, 'output_text'): self.output_text.config(**text_config)
        if hasattr(self, 'available_models_listbox'): self.available_models_listbox.config(**listbox_config)

        # Apply specific foreground colors
        if hasattr(self, 'error_label'): self.error_label.config(foreground=theme["error_fg"])
        if hasattr(self, 'active_model_label'):
            active_fg = theme["active_model_fg"] if self.active_model else theme["inactive_model_fg"]
            self.active_model_label.config(foreground=active_fg)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    # --- Widget Creation Methods ---
    def create_header_widgets(self):
        ttk.Label(self.header_frame, text="Ollama Translator", font=("Arial", 16)).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.header_frame, text="Direction:").pack(side=tk.LEFT, padx=(20, 5))
        self.direction_var = tk.StringVar(value="de-en")
        direction_combo = ttk.Combobox(self.header_frame, textvariable=self.direction_var, 
                                       values=["de-en", "en-de"], state="readonly", width=15)
        direction_combo.pack(side=tk.LEFT, padx=5)
        direction_combo.bind("<<ComboboxSelected>>", self.update_translation_prompt) # Update prompt on change

    def create_model_management_widgets(self):
        # Available Models Section
        available_frame = ttk.Frame(self.model_mgmt_frame)
        available_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ns")
        ttk.Label(available_frame, text="Available Models").pack()
        self.available_models_listbox = tk.Listbox(available_frame, height=5, exportselection=False)
        self.available_models_listbox.pack(fill=tk.X, expand=True)
        available_buttons = ttk.Frame(available_frame)
        available_buttons.pack(pady=5)
        ttk.Button(available_buttons, text="Refresh", command=self.refresh_available_models).pack(side=tk.LEFT, padx=2)
        ttk.Button(available_buttons, text="Activate Model", command=self.activate_model).pack(side=tk.LEFT, padx=2)

        # Active Model Section
        active_frame = ttk.Frame(self.model_mgmt_frame)
        active_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")
        ttk.Label(active_frame, text="Active Model for Translation").pack()
        self.active_model_label = ttk.Label(active_frame, text="None selected", foreground="grey", width=30, anchor="center")
        self.active_model_label.pack(pady=5)
        # Note: No listbox for active models needed, just display the selected one.
        # Adding a deactivate button
        ttk.Button(active_frame, text="Deactivate Model", command=self.deactivate_model).pack(pady=5)

        self.model_mgmt_frame.columnconfigure(0, weight=1)
        self.model_mgmt_frame.columnconfigure(1, weight=1)

    def create_translation_widgets(self):
        # Input Section
        input_frame = ttk.Frame(self.translation_frame)
        input_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky="nsew")
        ttk.Label(input_frame, text="Input").grid(row=0, column=0, sticky="w")
        self.input_text = tk.Text(input_frame, wrap=tk.WORD, height=10, width=40)
        self.input_text.grid(row=1, column=0, sticky="nsew")
        input_buttons = ttk.Frame(input_frame)
        input_buttons.grid(row=2, column=0, pady=5, sticky="ew")

        ttk.Button(input_buttons, text="Upload TXT", command=self.upload_txt).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_buttons, text="Clear", command=lambda: self.input_text.delete('1.0', tk.END)).pack(side=tk.LEFT, padx=2)
        self.translate_button = ttk.Button(input_buttons, text="Translate", command=self.start_translation, state=tk.DISABLED)
        self.translate_button.pack(side=tk.LEFT, padx=2)
        self.cancel_button = ttk.Button(input_buttons, text="Cancel", command=self.cancel_translation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=2)

        # Output Section
        output_frame = ttk.Frame(self.translation_frame)
        output_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")
        ttk.Label(output_frame, text="Output").grid(row=0, column=0, sticky="w")
        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=10, width=40, state=tk.DISABLED)
        self.output_text.grid(row=1, column=0, sticky="nsew")
        output_buttons = ttk.Frame(output_frame)
        output_buttons.grid(row=2, column=0, pady=5, sticky="ew")

        ttk.Button(output_buttons, text="Save TXT", command=self.save_txt).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_buttons, text="Copy", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=2)

        input_frame.rowconfigure(1, weight=1)
        input_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)

    def create_progress_widgets(self):
        ttk.Label(self.progress_frame, text="Progress:").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.error_label = ttk.Label(self.progress_frame, text="", foreground="red")
        self.error_label.pack(side=tk.LEFT, padx=5)

    def create_footer_widgets(self):
        # Theme toggle button
        self.theme_button = ttk.Button(self.footer_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=5)
        # pass # Remove pass

    # --- Helper Methods --- 
    def start_ollama_server(self):
        try:
            # Try to connect to the server first to see if it's already running
            requests.get(OLLAMA_API_BASE_URL, timeout=1) # Short timeout
            print("Ollama server already running.")
        except requests.exceptions.RequestException:
            print("Ollama server not running. Attempting to start...")
            try:
                # For Windows, use CREATE_NO_WINDOW to hide the console
                # Adjust the command if 'ollama' is not in PATH or has a specific path
                if os.name == 'nt': # Windows
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                else: # macOS/Linux
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Ollama serve command issued.")
                # It might take a few seconds for the server to start
                # Consider adding a small delay or a more robust check here if needed
            except FileNotFoundError:
                self.show_error("Ollama command not found. Ensure Ollama is installed and in your PATH.")
                messagebox.showerror("Ollama Error", "Ollama command not found. Please ensure Ollama is installed and in your system's PATH.")
            except Exception as e:
                self.show_error(f"Failed to start Ollama server: {e}")
                messagebox.showerror("Ollama Error", f"Failed to start Ollama server: {e}")

    def show_error(self, message):
        self.error_label.config(text=message)
        # Optionally use messagebox for more prominent errors
        # messagebox.showerror("Error", message)

    def clear_error(self):
        self.error_label.config(text="")

    def update_translate_button_state(self):
        if self.active_model and self.input_text.get("1.0", "end-1c").strip():
            self.translate_button.config(state=tk.NORMAL)
        else:
            self.translate_button.config(state=tk.DISABLED)

    # --- Model Management Methods --- 
    def refresh_available_models(self):
        self.clear_error()
        self.available_models_listbox.delete(0, tk.END)
        self.available_models_listbox.insert(tk.END, "Loading...")
        threading.Thread(target=self._fetch_models_thread, daemon=True).start()

    def _fetch_models_thread(self):
        try:
            response = requests.get(f"{OLLAMA_API_BASE_URL}/tags")
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            self.root.after(0, self._update_available_models_list, models)

        except requests.exceptions.ConnectionError:
            self.root.after(0, self.show_error, "Connection Error: Could not connect to Ollama API.")
            self.root.after(0, self._update_available_models_list, [])
        except requests.exceptions.RequestException as e:
            self.root.after(0, self.show_error, f"API Error: {e}")
            self.root.after(0, self._update_available_models_list, [])
        except json.JSONDecodeError:
             self.root.after(0, self.show_error, "API Error: Invalid JSON response.")
             self.root.after(0, self._update_available_models_list, [])

    def _update_available_models_list(self, models):
        self.available_models_listbox.delete(0, tk.END)
        if models:
            for model in sorted(models):
                self.available_models_listbox.insert(tk.END, model)
        else:
            self.available_models_listbox.insert(tk.END, "No models found.")
            if not self.error_label.cget("text"): # Show error only if not already shown by fetch
                 self.show_error("No models available or API error.")

    def activate_model(self):
        selection = self.available_models_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model from the 'Available Models' list.")
            return
        
        selected_model = self.available_models_listbox.get(selection[0])
        if selected_model in ["Loading...", "No models found."]:
             messagebox.showwarning("Invalid Selection", "Please wait for models to load or select a valid model.")
             return

        # If a different model is already active and a translation might be running, cancel it.
        if self.active_model and self.active_model != selected_model and self.translation_controller:
            print(f"Switching model from {self.active_model} to {selected_model}. Cancelling ongoing translation if any.")
            self.cancel_translation()

        self.active_model = selected_model
        active_fg = LIGHT_THEME["active_model_fg"] if self.current_theme == "light" else DARK_THEME["active_model_fg"]
        self.active_model_label.config(text=self.active_model, foreground=active_fg)
        self.update_translate_button_state()
        self.update_translation_prompt() # Update prompt when model changes
        print(f"Activated model: {self.active_model}")

    def deactivate_model(self):
        self.active_model = None
        inactive_fg = LIGHT_THEME["inactive_model_fg"] if self.current_theme == "light" else DARK_THEME["inactive_model_fg"]
        self.active_model_label.config(text="None selected", foreground=inactive_fg)
        self.update_translate_button_state()
        self.update_translation_prompt()
        print("Deactivated model")

    # --- Translation Methods --- 
    def get_translation_prompt(self):
        direction = self.direction_var.get()
        source_lang = "German" if direction == "de-en" else "English"
        target_lang = "English" if direction == "de-en" else "German"
        # Basic prompt - can be refined
        return f"Translate the following text from {source_lang} to {target_lang}. Output only the translation, without any introductory phrases or explanations:\n\n"

    def update_translation_prompt(self, event=None): # event=None allows calling it directly
        # This method could potentially update a label showing the prompt, 
        # but for now, it just ensures the prompt is ready when needed.
        # We also re-check button state as direction change might affect logic later.
        self.update_translate_button_state()
        pass

    def start_translation(self):
        if not self.active_model:
            messagebox.showerror("Error", "No model selected for translation.")
            return
            
        input_content = self.input_text.get("1.0", "end-1c").strip()
        if not input_content:
            messagebox.showerror("Error", "Input text cannot be empty.")
            return

        self.clear_error()
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', "Translating...")
        self.output_text.config(state=tk.DISABLED)
        
        self.progress_bar['value'] = 0
        self.progress_bar['mode'] = 'indeterminate' # Use indeterminate for streaming
        self.progress_bar.start()
        
        self.translate_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

        # Use threading to avoid blocking the GUI
        # Simple AbortController simulation
        self.translation_controller = {'abort': False}
        threading.Thread(target=self._translate_thread, args=(input_content, self.translation_controller), daemon=True).start()

    def _translate_thread(self, text_to_translate, controller):
        try:
            prompt = self.get_translation_prompt() + text_to_translate
            payload = {
                "model": self.active_model,
                "prompt": prompt,
                "stream": True # Use streaming API
            }
            
            full_response = ""
            
            # Make the streaming request
            response = requests.post(f"{OLLAMA_API_BASE_URL}/generate", json=payload, stream=True)
            response.raise_for_status()

            self.root.after(0, lambda: self.output_text.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.output_text.delete('1.0', tk.END))

            for line in response.iter_lines():
                if controller['abort']:
                    print("Translation aborted by user.")
                    self.root.after(0, self.show_error, "Translation cancelled.")
                    break # Exit the loop if cancelled

                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        response_part = chunk.get('response', '')
                        if response_part:
                            full_response += response_part
                            # Update GUI from the main thread
                            self.root.after(0, lambda p=response_part: self.output_text.insert(tk.END, p))
                            self.root.after(0, lambda: self.output_text.see(tk.END)) # Scroll to end
                        
                        # Check if generation is done (Ollama specific)
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON line: {line}")
                        continue # Skip malformed lines
            
            if controller['abort']:
                 # Ensure final state reflects cancellation
                 self.root.after(0, lambda: self.output_text.config(state=tk.DISABLED))
            else:
                # Final update after stream finishes normally
                # self.root.after(0, lambda: self.output_text.delete('1.0', tk.END))
                # self.root.after(0, lambda: self.output_text.insert('1.0', full_response))
                self.root.after(0, lambda: self.output_text.config(state=tk.DISABLED))
                print("Translation finished.")

        except requests.exceptions.ConnectionError:
            self.root.after(0, self.show_error, "Connection Error during translation.")
        except requests.exceptions.RequestException as e:
            self.root.after(0, self.show_error, f"API Error during translation: {e}")
        except Exception as e:
            self.root.after(0, self.show_error, f"Unexpected error during translation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always run this cleanup code in the main thread
            self.root.after(0, self._finalize_translation)

    def _finalize_translation(self):
        self.progress_bar.stop()
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['value'] = 100 if not self.error_label.cget("text") else 0
        self.translate_button.config(state=tk.NORMAL if self.active_model else tk.DISABLED)
        self.cancel_button.config(state=tk.DISABLED)
        self.translation_controller = None # Reset controller
        self.update_translate_button_state() # Re-check state based on input text

    def cancel_translation(self):
        if self.translation_controller:
            self.translation_controller['abort'] = True
            print("Cancellation requested.")
            # The thread will check the flag and stop
            self.cancel_button.config(state=tk.DISABLED) # Prevent multiple clicks

    # --- File I/O Methods --- 
    def upload_txt(self):
        filepath = filedialog.askopenfilename(
            title="Open TXT File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.delete('1.0', tk.END)
            self.input_text.insert('1.0', content)
            self.update_translate_button_state()
            self.clear_error()
        except Exception as e:
            messagebox.showerror("File Read Error", f"Could not read file: {e}")
            self.show_error(f"Error reading file: {filepath}")

    def save_txt(self):
        output_content = self.output_text.get("1.0", "end-1c").strip()
        if not output_content or output_content == "Translating...":
            messagebox.showwarning("No Output", "There is no translated text to save.")
            return
            
        filepath = filedialog.asksaveasfilename(
            title="Save Translation As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output_content)
            self.clear_error()
        except Exception as e:
            messagebox.showerror("File Save Error", f"Could not save file: {e}")
            self.show_error(f"Error saving file: {filepath}")

    def copy_to_clipboard(self):
        output_content = self.output_text.get("1.0", "end-1c").strip()
        if not output_content or output_content == "Translating...":
            messagebox.showwarning("No Output", "There is no translated text to copy.")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_content)
            messagebox.showinfo("Copied", "Output copied to clipboard.")
            self.clear_error()
        except tk.TclError:
             messagebox.showwarning("Clipboard Error", "Could not access clipboard.")
             self.show_error("Clipboard access error.")

# --- Main Execution --- 
if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaTranslatorApp(root)
    root.mainloop()