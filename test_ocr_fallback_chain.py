import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import ollama_translator_gui as mod


class _Var:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def _make_app(direction="de-en", quality="praezise"):
    """
    Create an OllamaTranslatorApp instance without running its Tkinter-heavy __init__.
    Only the attributes used by _extract_pdf_text are provided.
    """
    app = mod.OllamaTranslatorApp.__new__(mod.OllamaTranslatorApp)
    app.direction_var = _Var(direction)
    app.ocr_quality_var = _Var(quality)

    app._lazy_import_unstructured = MagicMock(return_value=None)
    app._lazy_import_pdf2image = MagicMock(return_value=None)
    app._lazy_import_paddleocr = MagicMock(return_value=None)

    app._get_poppler_path = MagicMock(return_value="C:\\poppler\\bin")
    app._create_paddleocr = MagicMock(return_value=None)
    app._pdf_to_images = MagicMock(return_value=[])
    app._preprocess_ocr_image = MagicMock(side_effect=lambda img: img)
    app._paddleocr_text_segments = MagicMock(return_value=[])
    app._postprocess_ocr_text = MagicMock(side_effect=lambda text: text)

    app._log_event = MagicMock()
    app.show_error = MagicMock()
    app._dispatch_ui = MagicMock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))

    return app


class TestOcrFallbackChain(unittest.TestCase):
    def test_unstructured_used_when_available_and_precise(self):
        app = _make_app(direction="de-en", quality="praezise")

        el1 = SimpleNamespace(text="Hallo")
        el2 = SimpleNamespace(text="Welt")
        partition_pdf_fn = MagicMock(return_value=[el1, el2])
        app._lazy_import_unstructured.return_value = partition_pdf_fn

        text = app._extract_pdf_text("dummy.pdf")

        self.assertIn("Hallo", text)
        self.assertIn("Welt", text)
        app._lazy_import_pdf2image.assert_not_called()
        app._lazy_import_paddleocr.assert_not_called()

    def test_paddleocr_used_when_unstructured_fails(self):
        app = _make_app(direction="en-de", quality="praezise")

        # unstructured present but returns empty => should fall back
        el_empty = SimpleNamespace(text="   ")
        app._lazy_import_unstructured.return_value = MagicMock(return_value=[el_empty])

        convert_fn = MagicMock()
        app._lazy_import_pdf2image.return_value = convert_fn

        app._lazy_import_paddleocr.return_value = object()

        ocr = MagicMock()
        ocr.predict.return_value = object()
        app._create_paddleocr.return_value = ocr
        app._pdf_to_images.return_value = ["img1", "img2"]
        app._paddleocr_text_segments.side_effect = lambda _result: ["Hello", "World"]

        text = app._extract_pdf_text("dummy.pdf")

        self.assertIn("Hello", text)
        self.assertIn("World", text)

    def test_pypdf_used_when_ocr_unavailable(self):
        app = _make_app(direction="de-en", quality="praezise")
        app._lazy_import_unstructured.return_value = None
        app._lazy_import_pdf2image.return_value = None
        app._lazy_import_paddleocr.return_value = None

        page1 = SimpleNamespace(extract_text=lambda: "P1")
        page2 = SimpleNamespace(extract_text=lambda: "P2")
        reader = SimpleNamespace(pages=[page1, page2])

        progress = MagicMock()
        with patch.object(mod, "PdfReader", return_value=reader):
            text = app._extract_pdf_text("dummy.pdf", progress_cb=progress)

        self.assertIn("P1", text)
        self.assertIn("P2", text)
        progress.assert_any_call(1, 2, "Text-Extract")
        progress.assert_any_call(2, 2, "Text-Extract")

    def test_abort_raises_keyboardinterrupt(self):
        app = _make_app(direction="de-en", quality="praezise")
        app._lazy_import_unstructured.return_value = None
        app._lazy_import_pdf2image.return_value = None
        app._lazy_import_paddleocr.return_value = None

        page = SimpleNamespace(extract_text=lambda: "P1")
        reader = SimpleNamespace(pages=[page])

        with patch.object(mod, "PdfReader", return_value=reader):
            with self.assertRaises(KeyboardInterrupt):
                app._extract_pdf_text("dummy.pdf", controller={"abort": True})


if __name__ == "__main__":
    unittest.main()

