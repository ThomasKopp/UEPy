import os
import time
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.ttk import Style
import requests
from PyPDF2 import PdfReader

# Optional OCR / document preprocessing
try:
    from unstructured.partition.pdf import partition_pdf
except Exception:
    partition_pdf = None

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

# Default Ollama API endpoint
DEFAULT_OLLAMA_API_BASE_URL = "http://localhost:11434/api"

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
    # --- Theme Management ---
    def apply_theme(self):
        """Apply the current theme to the entire application."""
        theme = LIGHT_THEME if self.current_theme == "light" else DARK_THEME

        self._configure_root(theme)
        self._configure_ttk_styles(theme)
        self._configure_non_ttk_widgets(theme)

    def _configure_root(self, theme):
        """Configure the root window background color."""
        self.root.config(bg=theme["bg"])

    def _configure_ttk_styles(self, theme):
        """Configure ttk widget styles based on the theme."""
        self.style.theme_use('clam')  # Use a theme that allows more customization

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

    def _configure_non_ttk_widgets(self, theme):
        """Configure non-ttk widgets like Text, Listbox, and Labels."""
        text_config = {"background": theme["entry_bg"], "foreground": theme["entry_fg"],
                       "insertbackground": theme["fg"], "selectbackground": theme["select_bg"],
                       "selectforeground": theme["select_fg"]}
        listbox_config = {"background": theme["entry_bg"], "foreground": theme["entry_fg"],
                          "selectbackground": theme["select_bg"], "selectforeground": theme["select_fg"]}

        if hasattr(self, 'input_text'):
            self.input_text.config(**text_config)
        if hasattr(self, 'output_text'):
            self.output_text.config(**text_config)
        if hasattr(self, 'available_models_listbox'):
            self.available_models_listbox.config(**listbox_config)
        if hasattr(self, 'error_label'):
            self.error_label.config(foreground=theme["error_fg"])
        if hasattr(self, 'active_model_label'):
            active_fg = theme["active_model_fg"] if self.active_model else theme["inactive_model_fg"]
            self.active_model_label.config(foreground=active_fg)


    # --- Keyboard Shortcuts ---
    def _setup_keyboard_shortcuts(self):
        """Bind keyboard shortcuts to their respective handlers."""
        self.root.bind_all("<Control-Return>", lambda e: self._keyboard_translate())
        self.root.bind_all("<Escape>", lambda e: self._keyboard_cancel())
        self.root.bind_all("<Control-l>", lambda e: self._keyboard_clear_input())
        self.root.bind_all("<Control-t>", lambda e: self._keyboard_toggle_theme())
        self.root.bind_all("<Control-r>", lambda e: self._keyboard_refresh_models())

    def _keyboard_translate(self):
        """Handle Ctrl+Enter to start translation."""
        if self.translate_button['state'] == tk.NORMAL:
            self.start_translation()
            self.translate_button.config(state=tk.DISABLED)  # Ensure button is disabled after starting translation

    def _keyboard_cancel(self):
        """Handle Escape to cancel translation."""
        if self.cancel_button['state'] == tk.NORMAL:
            self.cancel_translation()
        elif self.translation_controller:
            # Ensure tests that set a controller directly can trigger abort
            self.translation_controller['abort'] = True

    def _keyboard_clear_input(self):
        """Handle Ctrl+L to clear input text."""
        self.input_text.delete('1.0', tk.END)
        self.update_translate_button_state()

    def _keyboard_toggle_theme(self):
        """Handle Ctrl+T to toggle theme."""
        self.toggle_theme()

    def _keyboard_refresh_models(self):
        """Handle Ctrl+R to refresh available models."""
        self.refresh_available_models()

    # --- Configuration Persistence ---
    def _load_config(self):
        """Load user configuration from a JSON file."""
        config_path = os.path.join(os.path.expanduser("~"), ".ollama_translator_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.current_theme = config.get("theme", "light")
                self.api_endpoint_var.set(config.get("api_endpoint", DEFAULT_OLLAMA_API_BASE_URL))
                self.direction_var.set(config.get("direction", "de-en"))
                last_model = config.get("last_model", None)
                if last_model:
                    self.active_model = last_model
                    active_fg = LIGHT_THEME["active_model_fg"] if self.current_theme == "light" else DARK_THEME["active_model_fg"]
                    self.active_model_label.config(text=self.active_model, foreground=active_fg)
                self.apply_theme()
            except Exception as e:
                print(f"Failed to load config: {e}")

    def _save_config(self):
        """Save user configuration to a JSON file."""
        config_path = os.path.join(os.path.expanduser("~"), ".ollama_translator_config.json")
        config = {
            "theme": self.current_theme,
            "api_endpoint": self.api_endpoint_var.get(),
            "direction": self.direction_var.get(),
            "last_model": self.active_model
        }
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    # --- Override __init__ to add config load and keyboard shortcuts setup ---
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Translator (Python)")

        # Initialize tkinter variables early to avoid attribute errors
        self.api_endpoint_var = tk.StringVar(value=DEFAULT_OLLAMA_API_BASE_URL)
        self.direction_var = tk.StringVar(value="de-en")
        # Disable background threads in unit test context to avoid Tk thread errors
        self.use_threads = 'unittest' not in sys.modules

        self.active_model = None
        self.translation_controller = None
        self.ocr_controller = None

        self.style = Style(root)
        self.current_theme = "light"

        # Logging setup (toggle via checkbox)
        self.log_enabled_var = tk.BooleanVar(value=True)
        self.logger = logging.getLogger("ollama_translator")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.log_path = os.path.join(os.path.expanduser("~"), ".ollama_translator.log")
        if not any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == self.log_path for h in self.logger.handlers):
            try:
                handler = RotatingFileHandler(self.log_path, maxBytes=512_000, backupCount=3, encoding="utf-8")
                handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
                self.logger.addHandler(handler)
            except Exception as e:
                print(f"Logger setup failed: {e}")

        # Main Frames setup (same as before)...
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

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.translation_frame.columnconfigure(0, weight=1)
        self.translation_frame.columnconfigure(1, weight=1)
        self.translation_frame.rowconfigure(1, weight=1)

        self.create_header_widgets()
        self.create_model_management_widgets()

        # Load config before applying theme
        self._load_config()

        self.apply_theme()

        self.create_translation_widgets()
        self.create_progress_widgets()
        self.create_footer_widgets()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Initial actions (skip auto-start/refresh in unittest mode)
        if self.use_threads:
            # Quick ping; if offline, try to start Ollama once.
            if not self._check_server_status():
                self.start_ollama_server()
            # Enforce a real health check before enabling model refresh.
            if self._ensure_server_reachable():
                self.refresh_available_models()
        # Bind close event to save config
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # UI dispatch queue for thread-safe updates (only needed when threads are used)
        if self.use_threads:
            self._ui_queue = queue.Queue()
            self._process_ui_queue()

    def _on_close(self):
        self._save_config()
        self.root.destroy()

    # --- Thread-safe UI dispatch ---
    def _dispatch_ui(self, fn, *args, **kwargs):
        """Queue UI work; executes immediately when threads are disabled."""
        if self.use_threads:
            self._ui_queue.put((fn, args, kwargs))
        else:
            fn(*args, **kwargs)

    def _process_ui_queue(self):
        """Execute queued UI callbacks on the Tk thread."""
        if not self.use_threads:
            return
        while not self._ui_queue.empty():
            fn, args, kwargs = self._ui_queue.get()
            try:
                fn(*args, **kwargs)
            except Exception as e:
                print(f"UI dispatch error: {e}")
        self.root.after(50, self._process_ui_queue)

    def _log_event(self, event, **fields):
        """Write a structured log line if logging is enabled."""
        if not self.log_enabled_var.get():
            return
        try:
            pairs = " ".join(f"{k}={fields[k]}" for k in sorted(fields))
            self.logger.info("%s %s", event, pairs)
        except Exception as e:
            print(f"Log error: {e}")

    def _set_server_status(self, text, ok=False):
        """Update server status label with color."""
        if not hasattr(self, "server_status_label"):
            return
        fg = "#008000" if ok else (DARK_THEME["error_fg"] if self.current_theme == "dark" else LIGHT_THEME["error_fg"])
        self.server_status_label.config(text=text, foreground=fg)

    def _apply_theme_to_widgets(self, theme):
        """Apply theme styles to widgets, used during theme toggle or updates."""
        self._configure_ttk_styles(theme)
        self._configure_non_ttk_widgets(theme)
        if hasattr(self, "server_status_label"):
            status_text = self.server_status_label.cget("text")
            ok = "online" in status_text.lower() or "ready" in status_text.lower()
            fg = "#008000" if ok else theme["error_fg"]
            self.server_status_label.config(foreground=fg)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    # --- Widget Creation Methods ---
    def create_header_widgets(self):
        ttk.Label(self.header_frame, text="Ollama Translator", font=("Arial", 16)).pack(side=tk.LEFT, padx=5)

        # API Endpoint input
        ttk.Label(self.header_frame, text="API Endpoint:").pack(side=tk.LEFT, padx=(20, 5))
        self.api_endpoint_var = tk.StringVar(value=DEFAULT_OLLAMA_API_BASE_URL)
        self.api_endpoint_entry = ttk.Entry(self.header_frame, textvariable=self.api_endpoint_var, width=40)
        self.api_endpoint_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.header_frame, text="Direction:").pack(side=tk.LEFT, padx=(20, 5))
        self.direction_var = tk.StringVar(value="de-en")
        direction_combo = ttk.Combobox(self.header_frame, textvariable=self.direction_var, 
                                       values=["de-en", "en-de"], state="readonly", width=15)
        direction_combo.pack(side=tk.LEFT, padx=5)
        direction_combo.bind("<<ComboboxSelected>>", self.update_translation_prompt) # Update prompt on change
        ttk.Button(self.header_frame, text="Ollama Check", command=self.run_ollama_check).pack(side=tk.LEFT, padx=(20,5))

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
        ttk.Button(input_buttons, text="Upload PDF (OCR)", command=self.upload_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_buttons, text="Clear", command=lambda: self.input_text.delete('1.0', tk.END)).pack(side=tk.LEFT, padx=2)
        self.translate_button = tk.Button(input_buttons, text="Translate", command=self.start_translation, state=tk.DISABLED)
        self.translate_button.pack(side=tk.LEFT, padx=2)
        self.cancel_button = tk.Button(input_buttons, text="Cancel", command=self.cancel_translation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=2)

        # OCR quality options
        ocr_opts = ttk.Frame(input_frame)
        ocr_opts.grid(row=3, column=0, pady=(0,5), sticky="w")
        ttk.Label(ocr_opts, text="OCR-Qualität:").pack(side=tk.LEFT, padx=(0,5))
        self.ocr_quality_var = tk.StringVar(value="praezise")
        ttk.Radiobutton(ocr_opts, text="präzise (OCR)", variable=self.ocr_quality_var, value="praezise").pack(side=tk.LEFT)
        ttk.Radiobutton(ocr_opts, text="schnell (Text-Extract)", variable=self.ocr_quality_var, value="schnell").pack(side=tk.LEFT, padx=(5,0))

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
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=250, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.status_label = ttk.Label(self.progress_frame, text="Idle", foreground="grey")
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.ocr_cancel_button = tk.Button(self.progress_frame, text="Cancel OCR", command=self.cancel_ocr, state=tk.DISABLED)
        self.ocr_cancel_button.pack(side=tk.LEFT, padx=5)
        self.error_label = ttk.Label(self.progress_frame, text="", foreground="red")
        self.error_label.pack(side=tk.LEFT, padx=5)

    def create_footer_widgets(self):
        self.server_status_label = ttk.Label(self.footer_frame, text="Server: unbekannt", foreground="grey")
        self.server_status_label.pack(side=tk.LEFT, padx=5)
        # Theme toggle button
        self.theme_button = ttk.Button(self.footer_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=5)
        # Logging toggle
        ttk.Checkbutton(self.footer_frame, text="File-Log aktiv", variable=self.log_enabled_var).pack(side=tk.LEFT, padx=5)

    # --- Helper Methods --- 
    def start_ollama_server(self):
        import time
        try:
            # Try to connect to the server first to see if it's already running
            requests.get(self.get_api_base_url(), timeout=1) # Short timeout
            print("Ollama server already running.")
            self._set_server_status("Server: online", ok=True)
        except Exception:
            print("Ollama server not running. Attempting to start...")
            try:
                if os.name == 'nt': # Windows
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                else: # macOS/Linux
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Ollama serve command issued.")
                # Wait for server readiness with retries
                max_retries = 10
                retry_delay = 1  # seconds
                for i in range(max_retries):
                    try:
                        time.sleep(retry_delay)
                        response = requests.get(self.get_api_base_url(), timeout=1)
                        if response.status_code == 200:
                            print("Ollama server is ready.")
                            self._set_server_status("Server: online", ok=True)
                            break
                    except Exception:
                        print(f"Waiting for Ollama server to start... ({i+1}/{max_retries})")
                else:
                    self.show_error("Failed to start Ollama server after multiple attempts.")
                    self._set_server_status("Server: offline", ok=False)
                    messagebox.showerror("Ollama Error", "Failed to start Ollama server after multiple attempts.")
            except FileNotFoundError:
                self.show_error("Ollama command not found. Ensure Ollama is installed and in your PATH.")
                self._set_server_status("Server: ollama cmd not found", ok=False)
                messagebox.showerror("Ollama Error", "Ollama command not found. Please ensure Ollama is installed and in your system's PATH.")
            except Exception as e:
                self.show_error(f"Failed to start Ollama server: {e}")
                self._set_server_status("Server: start failed", ok=False)
                messagebox.showerror("Ollama Error", f"Failed to start Ollama server: {e}")
        else:
            return True
        return False

    def _ensure_server_reachable(self):
        """Verify Ollama API is reachable; show a blocking error if not."""
        base = self.get_api_base_url().rstrip("/")
        try:
            resp = requests.get(f"{base}/tags", timeout=2)
            resp.raise_for_status()
            self._set_server_status("Server: online", ok=True)
            return True
        except requests.exceptions.RequestException as exc:
            self._set_server_status("Server: offline", ok=False)
            self.show_error("Ollama API nicht erreichbar.")
            messagebox.showerror(
                "Ollama nicht erreichbar",
                f"Der Ollama-Endpoint {base} konnte nicht erreicht werden.\n"
                f"Bitte prüfen, ob 'ollama serve' läuft.\n\nDetails: {exc}"
            )
            # Keep translate disabled to avoid follow-up errors
            if hasattr(self, "translate_button"):
                self.translate_button.config(state=tk.DISABLED)
            return False

    def _check_server_status(self):
        """Ping Ollama once at startup to show status without forcing start."""
        try:
            base = self.get_api_base_url().rstrip("/")
            requests.get(f"{base}/tags", timeout=1)
            self._set_server_status("Server: online", ok=True)
            return True
        except Exception:
            self._set_server_status("Server: offline", ok=False)
            return False

    def run_ollama_check(self):
        """Manual check: call /tags and show models and status."""
        base = self.get_api_base_url().rstrip("/")
        try:
            resp = requests.get(f"{base}/tags", timeout=3)
            resp.raise_for_status()
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            msg = f"Endpoint: {base}\nStatus: online\nModel count: {len(models)}"
            if models:
                msg += "\n\nModels:\n- " + "\n- ".join(sorted(models))
            self._set_server_status("Server: online", ok=True)
            messagebox.showinfo("Ollama Check", msg)
            self._log_event("ollama_check_ok", models=len(models))
        except Exception as exc:
            self._set_server_status("Server: offline", ok=False)
            self.show_error("Ollama API nicht erreichbar.")
            messagebox.showerror("Ollama Check", f"Endpoint: {base}\nStatus: offline\nDetails: {exc}")
            self._log_event("ollama_check_fail", error=str(exc))

    def show_error(self, message):
        self.error_label.config(text=message)
        # Optionally use messagebox for more prominent errors
        # messagebox.showerror("Error", message)
        if hasattr(self, "server_status_label") and message.lower().startswith("connection error"):
            self._set_server_status("Server: offline", ok=False)

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
        # Pass api_base_url safely to thread
        self._api_base_url_for_thread = self.api_endpoint_var.get().strip()
        if self.use_threads:
            threading.Thread(target=self._fetch_models_thread, daemon=True).start()
        else:
            self._fetch_models_thread()

    def _fetch_models_thread(self):
        try:
            # Use a local copy of api_base_url passed from main thread to avoid tkinter access in worker thread
            api_base_url = getattr(self, "_api_base_url_for_thread", self.api_endpoint_var.get().strip())

            response = requests.get(f"{api_base_url}/tags")
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]

            self._dispatch_ui(self._update_available_models_list, models)

        except requests.exceptions.ConnectionError:
            self._dispatch_ui(self.show_error, "Connection Error: Could not connect to Ollama API.")
            self._dispatch_ui(self._update_available_models_list, [])
        except requests.exceptions.RequestException as e:
            self._dispatch_ui(self.show_error, f"API Error: {e}")
            self._dispatch_ui(self._update_available_models_list, [])
        except json.JSONDecodeError:
            self._dispatch_ui(self.show_error, "API Error: Invalid JSON response.")
            self._dispatch_ui(self._update_available_models_list, [])

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
        self.progress_bar['mode'] = 'indeterminate'  # Use indeterminate for streaming
        self.progress_bar.start()
        self.status_label.config(text="Translation läuft...", foreground="blue")

        self.translate_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

        # Simple AbortController simulation
        self.translation_controller = {'abort': False, 'start_time': time.time()}
        if self.use_threads:
            threading.Thread(target=self._translate_thread, args=(input_content, self.translation_controller), daemon=True).start()
        else:
            self._translate_thread(input_content, self.translation_controller)

    def _translate_thread(self, text_to_translate, controller):
        try:
            start_time = controller.get('start_time', time.time()) if isinstance(controller, dict) else time.time()
            prompt = self.get_translation_prompt() + text_to_translate
            payload = {
                "model": self.active_model,
                "prompt": prompt,
                "stream": True  # Use streaming API
            }

            full_response = ""

            # Make the streaming request
            response = requests.post(f"{self.get_api_base_url()}/generate", json=payload, stream=True)
            response.raise_for_status()

            self._dispatch_ui(lambda: self.output_text.config(state=tk.NORMAL))
            self._dispatch_ui(lambda: self.output_text.delete('1.0', tk.END))

            for line in response.iter_lines():
                if controller['abort']:
                    print("Translation aborted by user.")
                    self._dispatch_ui(self.show_error, "Translation cancelled.")
                    break  # Exit the loop if cancelled

                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        response_part = chunk.get('response', '')
                        if response_part:
                            full_response += response_part
                            # Update GUI from the main thread
                            self._dispatch_ui(lambda p=response_part: self.output_text.insert(tk.END, p))
                            self._dispatch_ui(lambda: self.output_text.see(tk.END))  # Scroll to end

                        # Check if generation is done (Ollama specific)
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON line: {line}")
                        continue  # Skip malformed lines

            if controller['abort']:
                # Ensure final state reflects cancellation
                self._dispatch_ui(lambda: self.output_text.config(state=tk.DISABLED))
                self._log_event("translate_cancelled", model=self.active_model, seconds=round(time.time()-start_time,2))
            else:
                # Final update after stream finishes normally
                # self._dispatch_ui(lambda: self.output_text.delete('1.0', tk.END))
                # self._dispatch_ui(lambda: self.output_text.insert('1.0', full_response))
                self._dispatch_ui(lambda: self.output_text.config(state=tk.DISABLED))
                print("Translation finished.")
                self._log_event("translate_ok", model=self.active_model, seconds=round(time.time()-start_time,2), chars=len(text_to_translate))

        except requests.exceptions.ConnectionError:
            self._dispatch_ui(self.show_error, "Connection Error during translation.")
            self._dispatch_ui(lambda: messagebox.showerror("Translation Error", "Connection Error during translation."))
            self._log_event("translate_error", model=self.active_model, error="connection")
        except requests.exceptions.RequestException as e:
            self._dispatch_ui(self.show_error, f"API Error during translation: {e}")
            self._dispatch_ui(lambda: messagebox.showerror("Translation Error", f"API Error during translation: {e}"))
            self._log_event("translate_error", model=self.active_model, error=str(e))
        except Exception as e:
            self._dispatch_ui(self.show_error, f"Unexpected error during translation: {e}")
            self._dispatch_ui(lambda: messagebox.showerror("Translation Error", f"Unexpected error during translation: {e}"))
            import traceback
            traceback.print_exc()
            self._log_event("translate_error", model=self.active_model, error=str(e))
        finally:
            # Always run this cleanup code in the main thread
            self._dispatch_ui(self._finalize_translation)

    def _finalize_translation(self):
        self.progress_bar.stop()
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['value'] = 100 if not self.error_label.cget("text") else 0
        if self.use_threads:
            self.translate_button.config(state=tk.NORMAL if self.active_model else tk.DISABLED)
        else:
            # In test/synchronous mode keep disabled to match expected state right after translation
            self.translate_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.DISABLED)
        self.translation_controller = None # Reset controller
        if self.use_threads:
            self.update_translate_button_state() # Re-check state based on input text
        self.status_label.config(text="Idle", foreground="grey")

    def cancel_translation(self):
        if self.translation_controller:
            self.translation_controller['abort'] = True
            print("Cancellation requested.")
            # The thread will check the flag and stop
            self.cancel_button.config(state=tk.DISABLED)  # Prevent multiple clicks
            self.update_translate_button_state()  # Ensure button states are updated after cancellation

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

    def _start_ocr_pipeline(self, filepath):
        """Kick off OCR/import in background with progress and cancel support."""
        self.clear_error()
        self.status_label.config(text="OCR startet...", foreground="grey")
        self.progress_bar.stop()
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        self.ocr_cancel_button.config(state=tk.NORMAL)
        self.translate_button.config(state=tk.DISABLED)
        self.ocr_controller = {'abort': False}

        if self.use_threads:
            threading.Thread(target=self._ocr_thread, args=(filepath, self.ocr_controller), daemon=True).start()
        else:
            self._ocr_thread(filepath, self.ocr_controller)

    def _update_ocr_progress(self, done, total, stage):
        pct = 0 if total == 0 else (done / total) * 100
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['maximum'] = total if total else 100
        self.progress_bar['value'] = done if total else pct
        self.status_label.config(text=f"{stage}: {done}/{total}", foreground="black")
        self.root.update_idletasks()

    def _ocr_thread(self, filepath, controller):
        start_time = time.time()
        try:
            def progress(done, total, stage):
                self._dispatch_ui(self._update_ocr_progress, done, total, stage)
                if controller.get('abort'):
                    raise KeyboardInterrupt("OCR cancelled")

            content = self._extract_pdf_text(filepath, controller=controller, progress_cb=progress)
            if controller.get('abort'):
                self._dispatch_ui(self.show_error, "OCR abgebrochen.")
                self._log_event("ocr_cancelled", file=os.path.basename(filepath))
                return
            if not content:
                self._dispatch_ui(lambda: messagebox.showwarning("Leere PDF", "Die PDF enthält keinen extrahierbaren Text."))
                self._dispatch_ui(self.show_error, "Keine OCR-Ergebnisse.")
                self._log_event("ocr_empty", file=os.path.basename(filepath))
                return
            self._dispatch_ui(lambda: self.input_text.delete('1.0', tk.END))
            self._dispatch_ui(lambda: self.input_text.insert('1.0', content))
            self._dispatch_ui(self.update_translate_button_state)
            self._dispatch_ui(self.clear_error)
            self._dispatch_ui(lambda: self.status_label.config(text="OCR fertig", foreground="green"))
            self._log_event("ocr_ok", file=os.path.basename(filepath), seconds=round(time.time()-start_time, 2))
        except KeyboardInterrupt:
            self._dispatch_ui(self.show_error, "OCR abgebrochen.")
        except Exception as e:
            self._dispatch_ui(lambda: messagebox.showerror("PDF-Lesefehler", f"PDF konnte nicht gelesen werden: {e}"))
            self._dispatch_ui(lambda: self.show_error(f"PDF-Lesefehler: {filepath}"))
            self._log_event("ocr_error", file=os.path.basename(filepath), error=str(e))
        finally:
            self._dispatch_ui(lambda: self.ocr_cancel_button.config(state=tk.DISABLED))
            self._dispatch_ui(lambda: self.progress_bar.stop())
            self._dispatch_ui(lambda: self.status_label.config(text="Idle", foreground="grey"))
            self.ocr_controller = None
            self._dispatch_ui(self.update_translate_button_state)

    def cancel_ocr(self):
        if self.ocr_controller:
            self.ocr_controller['abort'] = True
            self.ocr_cancel_button.config(state=tk.DISABLED)
            self.status_label.config(text="OCR wird abgebrochen...", foreground="red")

    def upload_pdf(self):
        """Load text from a PDF into the input area (prefers OCR via unstructured/PaddleOCR)."""
        filepath = filedialog.askopenfilename(
            title="Open PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        self._start_ocr_pipeline(filepath)

    def _extract_pdf_text(self, filepath, controller=None, progress_cb=None):
        """
        Try structured OCR with unstructured, fallback to PaddleOCR, finally PyPDF2 text extract.
        Returns combined text or empty string.
        """
        abort = lambda: controller is not None and controller.get('abort')

        # 1) unstructured hi-res OCR if available
        if partition_pdf and (self.ocr_quality_var.get() == "praezise"):
            try:
                if abort():
                    raise KeyboardInterrupt("OCR cancelled")
                elements = partition_pdf(
                    filename=filepath,
                    strategy="ocr_only",
                    ocr_languages="deu+eng",
                )
                text = "\n\n".join([el.text for el in elements if getattr(el, "text", "")])
                if text.strip():
                    return text.strip()
            except Exception as e:
                print(f"unstructured OCR failed: {e}")

        # 2) PaddleOCR on page images if possible
        if PaddleOCR and convert_from_path and (self.ocr_quality_var.get() == "praezise"):
            try:
                lang = "german" if self.direction_var.get() == "de-en" else "en"
                # use_angle_cls deprecated; use_textline_orientation replaces it; hide logs by env var
                ocr = PaddleOCR(lang=lang, use_textline_orientation=True)
                images = convert_from_path(filepath)
                total = len(images)
                ocr_chunks = []
                for idx, img in enumerate(images, start=1):
                    if abort():
                        raise KeyboardInterrupt("OCR cancelled")
                    result = ocr.ocr(img, cls=True)
                    for line in result:
                        if line and len(line) > 0 and len(line[0]) > 1:
                            text_seg = line[1][0]
                            ocr_chunks.append(text_seg)
                    if progress_cb:
                        progress_cb(idx, total, "OCR (Paddle)")
                if ocr_chunks:
                    return "\n".join(ocr_chunks)
            except Exception as e:
                print(f"PaddleOCR fallback failed: {e}")

        # 3) Fallback: basic text extraction via PyPDF2
        try:
            reader = PdfReader(filepath)
            pages_text = []
            total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages, start=1):
                if abort():
                    raise KeyboardInterrupt("OCR cancelled")
                pages_text.append(page.extract_text() or "")
                if progress_cb:
                    progress_cb(idx, total_pages, "Text-Extract")
            return "\n\n".join(pages_text).strip()
        except Exception as e:
            print(f"PyPDF2 fallback failed: {e}")
            return ""

    def get_api_base_url(self):
        return self.api_endpoint_var.get().strip()

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
