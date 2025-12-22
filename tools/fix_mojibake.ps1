param(
  [Parameter(Mandatory = $true)]
  [string]$Path
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Path)) {
  throw "File not found: $Path"
}

$bytes = [System.IO.File]::ReadAllBytes($Path)

function Has-Utf8Bom([byte[]]$b) {
  return ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
}

function Decode-Utf8Strict([byte[]]$b, [int]$offset = 0) {
  $utf8Strict = [System.Text.UTF8Encoding]::new($false, $true) # throwOnInvalidBytes
  return $utf8Strict.GetString($b, $offset, $b.Length - $offset)
}

$latin1 = [System.Text.Encoding]::GetEncoding("ISO-8859-1")

try {
  if (Has-Utf8Bom $bytes) {
    $text = Decode-Utf8Strict $bytes 3
  } else {
    $text = Decode-Utf8Strict $bytes 0
  }
} catch {
  # Fallback: treat as ISO-8859-1 so we can still see/replace stray bytes.
  $text = $latin1.GetString($bytes)
}

function Fix-MojibakeSegments([string]$s) {
  # Convert only runs of U+0000..U+00FF characters by interpreting them as Latin-1 bytes
  # and decoding them as UTF-8. This avoids failures when the file also contains real
  # Unicode characters outside Latin-1 (e.g. curly quotes).
  $sb = New-Object System.Text.StringBuilder
  $buf = New-Object System.Text.StringBuilder

  $flush = {
    if ($buf.Length -eq 0) { return }
    $chunk = $buf.ToString()
    $buf.Clear() | Out-Null

    if (-not ($chunk.Contains([char]0x00C3) -or ($chunk -match "[\u0080-\u009F]"))) {
      $null = $sb.Append($chunk)
      return
    }

    try {
      $fixed = Decode-Utf8Strict ($latin1.GetBytes($chunk)) 0
      $null = $sb.Append($fixed)
    } catch {
      $null = $sb.Append($chunk)
    }
  }.GetNewClosure()

  foreach ($ch in $s.ToCharArray()) {
    if ([int]$ch -le 0xFF) {
      $null = $buf.Append($ch)
    } else {
      & $flush
      $null = $sb.Append($ch)
    }
  }
  & $flush
  return $sb.ToString()
}

# If the text was UTF-8 bytes decoded as Latin-1 at some point (classic "Ãœ" style),
# this converts it back to proper Unicode, without breaking real Unicode runs.
$text = Fix-MojibakeSegments $text

$c81 = [char]0x81
$ldquoLow = [char]0x201E   # „
$aAcute = [char]0x00E1     # á

$replacements = [ordered]@{
  # Control-byte fallout
  ("hinzuf${c81}gen") = "hinzufügen"
  ("anf${c81}gen")    = "anfügen"
  ("ausf${c81}hren")  = "ausführen"

  # Common mojibake patterns observed in `ollama_translator_gui.py`
  ("Qualit${ldquoLow}t") = "Qualität"
  ("pr${ldquoLow}zise")  = "präzise"
  ("l${ldquoLow}uft")    = "läuft"
  ("enth${ldquoLow}lt")  = "enthält"
  "Eintr,ge"             = "Einträge"
  "w,hlen"               = "wählen"
  "f?r"                  = "für"

  "?bersetzung"          = "Übersetzung"
  "?berspringen"         = "Überspringen"
  "?bertragen"           = "übertragen"

  ("Fu${aAcute}zeile")   = "Fußzeile"
}

foreach ($k in $replacements.Keys) {
  $text = $text.Replace([string]$k, [string]$replacements[$k])
}

# Replace the broken German direction note (contains embedded quote-junk) with a clean version.
$badDirectionNeedle = "Schreibe nat?rlich klingendes, idiomatisches Deutsch."
if ($text.Contains($badDirectionNeedle)) {
  $pattern = [regex]::Escape($badDirectionNeedle) + ".*?gehalten\\."
  $deOpen = [char]0x201E  # „
  $deClose = [char]0x201C # “
  $replacement = (
    "Schreibe nat" + [char]0x00FC + "rlich klingendes, idiomatisches Deutsch. " +
    "Verwende standardm" + [char]0x00E4 + [char]0x00DF + "ig die H" + [char]0x00F6 + "flichkeitsform " +
    $deOpen + "Sie" + $deClose + ", es sei denn, der Eingangstext ist eindeutig informell und " +
    "durchg" + [char]0x00E4 + "ngig mit " + $deOpen + "du" + $deClose + " gehalten."
  )
  $text = [regex]::Replace($text, $pattern, $replacement, [System.Text.RegularExpressions.RegexOptions]::Singleline)
}

# Write back as UTF-8 (no BOM).
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($Path, $text, $utf8NoBom)

Write-Host "Fixed mojibake and wrote UTF-8: $Path"
