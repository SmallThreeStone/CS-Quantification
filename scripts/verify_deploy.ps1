param(
  [string]$BaseUrl = "http://localhost",
  [switch]$Collect
)

$ErrorActionPreference = "Stop"

function Show-Json($Label, $Value) {
  Write-Host "== $Label =="
  $Value | ConvertTo-Json -Depth 8
}

Write-Host "== docker compose ps =="
docker compose ps

$health = Invoke-RestMethod "$BaseUrl/api/health"
Show-Json "health" $health

$opsHealth = Invoke-RestMethod "$BaseUrl/api/ops/health"
Show-Json "ops-health" $opsHealth

$monitor = Invoke-RestMethod "$BaseUrl/api/monitor"
Show-Json "monitor" @{ count = $monitor.Count }

$runs = Invoke-RestMethod "$BaseUrl/api/collect-runs"
Show-Json "collect-runs" @{ count = $runs.Count; latest = if ($runs.Count) { $runs[0] } else { $null } }

if ($Collect) {
  $alerts = Invoke-RestMethod -Method Post "$BaseUrl/api/collect"
  Show-Json "collect" @{ alert_count = $alerts.Count }
  $runsAfter = Invoke-RestMethod "$BaseUrl/api/collect-runs"
  Show-Json "collect-runs-after" @{ count = $runsAfter.Count; latest = if ($runsAfter.Count) { $runsAfter[0] } else { $null } }
}

$page = Invoke-WebRequest $BaseUrl -UseBasicParsing
Write-Host "== frontend =="
Write-Host "status=$($page.StatusCode)"
