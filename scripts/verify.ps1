$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  function Invoke-Checked([scriptblock]$command) {
    & $command
    if ($LASTEXITCODE -ne 0) { throw "Verification command failed with exit code $LASTEXITCODE" }
  }
  Invoke-Checked { & .\backend\.venv\Scripts\python -m ruff check backend }
  Invoke-Checked { & .\backend\.venv\Scripts\python -m pytest backend\tests }
  Push-Location backend
  try {
    Invoke-Checked { & .\.venv\Scripts\pyright.exe }
    Invoke-Checked { & .\.venv\Scripts\alembic.exe upgrade head }
  } finally { Pop-Location }
  Invoke-Checked { & 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build }
  $matches = rg -n --glob '!**/node_modules/**' --glob '!**/.venv/**' '(PRIVATE_KEY|POLYMARKET_API_SECRET|ALPACA_SECRET_KEY)\s*=' .
  if ($LASTEXITCODE -eq 0) { throw "Potential committed secret assignment found: $matches" }
  if ($LASTEXITCODE -ne 1) { throw 'Secret scan failed unexpectedly.' }
  Write-Output 'PolyTrader Phase 1 quality gate completed.'
} finally { Pop-Location }
