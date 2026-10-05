$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  & .\backend\.venv\Scripts\python scripts\smoke_polymarket_stream.py
  if ($LASTEXITCODE -ne 0) { throw "Public stream smoke failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
