$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $root '.env'
$contact = Read-Host 'Enter an email address you control for the SEC User-Agent'
if ([string]::IsNullOrWhiteSpace($contact) -or $contact -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') {
  throw 'A valid contact email is required; nothing was written.'
}
$value = "POLYTRADER_SEC_USER_AGENT=PolyTrader/0.1 (research; contact: $contact)"
$lines = if (Test-Path $envPath) { @(Get-Content $envPath) } else { @() }
$updated = $false
$lines = @($lines | ForEach-Object {
  if ($_ -match '^POLYTRADER_SEC_USER_AGENT=') { $script:updated = $true; $value } else { $_ }
})
if (-not $updated) { $lines += $value }
Set-Content -Path $envPath -Value $lines -Encoding utf8
Write-Output "Saved SEC User-Agent to .env (contact address not displayed)."
