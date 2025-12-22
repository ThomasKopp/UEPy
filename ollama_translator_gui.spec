# -*- mode: python ; coding: utf-8 -*-

import importlib.util


def _opt(modname: str):
    return [modname] if importlib.util.find_spec(modname) is not None else []


a = Analysis(
    ['ollama_translator_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # Optional features rely on lazy imports; include them only if they are installed at build time.
    hiddenimports=(
        _opt("pdf2image")
        + _opt("PIL")
        + _opt("pypdf")
        + _opt("fpdf")
        + _opt("docx")
        + _opt("unstructured")
        + _opt("paddleocr")
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ollama_translator_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
