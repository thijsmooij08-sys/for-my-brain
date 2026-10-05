$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  & .\backend\.venv\Scripts\python.exe .\scripts\smoke_polymarket.py
  if ($LASTEXITCODE -ne 0) { throw "Public Polymarket smoke failed with exit code $LASTEXITCODE" }
} finally {
  Pop-Location
}
