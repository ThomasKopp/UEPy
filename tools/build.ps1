param(
  [switch]$OneFile = $true,
  [switch]$Windowed = $true
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { Write-Host $msg }
function Write-Warn([string]$msg) { Write-Warning $msg }

function Get-PythonCmd {
  foreach ($c in @("python", "py", "python3")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { return $c }
  }
  return $null
}

function Test-PopplerAvailable {
  $popplerPath = $env:POPPLER_PATH
  if ($popplerPath) {
    $candidate = $popplerPath
    if (Test-Path -LiteralPath $candidate) {
      if ((Test-Path -LiteralPath (Join-Path $candidate "pdfinfo.exe")) -or (Test-Path -LiteralPath (Join-Path $candidate "pdfinfo"))) {
        return $true
      }
      $bin = Join-Path $candidate "bin"
      if ((Test-Path -LiteralPath (Join-Path $bin "pdfinfo.exe")) -or (Test-Path -LiteralPath (Join-Path $bin "pdfinfo"))) {
        return $true
      }
    }
  }

  if (Get-Command pdfinfo -ErrorAction SilentlyContinue) { return $true }
  if (Get-Command pdfinfo.exe -ErrorAction SilentlyContinue) { return $true }
  return $false
}

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
  $py = Get-PythonCmd
  if (-not $py) {
    throw "Python wurde nicht gefunden (python/py/python3). Bitte Python 3.10+ installieren und sicherstellen, dass es im PATH ist."
  }

  Write-Info "Python: $py"

  if (-not (Test-PopplerAvailable)) {
    Write-Warn "Poppler (pdfinfo) wurde nicht gefunden. PDF->Image OCR (pdf2image) wird ohne Poppler nicht funktionieren."
    Write-Info "Windows Download: https://github.com/oschwartz10612/poppler-windows"
    Write-Info "Tipp: POPPLER_PATH auf das Poppler bin-Verzeichnis setzen (oder pdfinfo.exe in PATH)."
  }

  & $py -m pip install --upgrade pip
  & $py -m pip install -r requirements.txt
  & $py -m pip install pyinstaller

  $spec = "ollama_translator_gui.spec"
  if (-not (Test-Path -LiteralPath $spec)) { throw "Spec nicht gefunden: $spec" }

  # The .spec controls onefile/windowed; keep flags for compatibility with future expansions.
  # Current spec builds a windowed executable (console=False). For console builds, adjust the spec.
  & $py -m PyInstaller $spec

  Write-Info "Build fertig. Ausgabe unter: dist\\"
} finally {
  Pop-Location
}

