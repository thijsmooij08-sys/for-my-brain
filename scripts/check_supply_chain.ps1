$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  $pipAuditPath = Join-Path $root 'backend/.venv/Scripts/pip-audit.exe'
  $pipAudit = if (Test-Path $pipAuditPath) { $pipAuditPath } else { (Get-Command pip-audit -ErrorAction SilentlyContinue).Source }
  if ([string]::IsNullOrWhiteSpace($pipAudit)) {
    Write-Output 'pip-audit is not installed; install it locally to run the Python vulnerability scan.'
  } else {
    & $pipAudit --strict
    if ($LASTEXITCODE -ne 0) { throw "pip-audit failed with exit code $LASTEXITCODE" }
  }

  $npm = Get-Command npm -ErrorAction SilentlyContinue
  if ($null -eq $npm) {
    Write-Output 'npm is not installed; frontend audit skipped.'
  } else {
    & $npm.Source --prefix frontend audit --omit=dev
    if ($LASTEXITCODE -ne 0) { throw "npm audit failed with exit code $LASTEXITCODE" }
  }
} finally { Pop-Location }
