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

$opsReadiness = Invoke-RestMethod "$BaseUrl/api/ops/readiness"
Show-Json "ops-readiness" $opsReadiness

$opsRuntime = Invoke-RestMethod "$BaseUrl/api/ops/runtime"
Show-Json "ops-runtime" $opsRuntime

$runtimeAudit = Invoke-RestMethod "$BaseUrl/api/ops/runtime-audit"
Show-Json "runtime-audit" $runtimeAudit

$acceptance = Invoke-RestMethod "$BaseUrl/api/ops/acceptance"
Show-Json "acceptance" $acceptance

$p0Summary = Invoke-RestMethod "$BaseUrl/api/ops/p0-summary"
Show-Json "p0-summary" $p0Summary

$sourceConfig = Invoke-RestMethod "$BaseUrl/api/source/config"
Show-Json "source-config" $sourceConfig

$alertCoverage = Invoke-RestMethod "$BaseUrl/api/alerts/coverage"
Show-Json "alert-coverage" $alertCoverage

$monitor = Invoke-RestMethod "$BaseUrl/api/monitor"
Show-Json "monitor" @{ count = $monitor.Count }

$monitorCoverage = Invoke-RestMethod "$BaseUrl/api/monitor/coverage"
Show-Json "monitor-coverage" $monitorCoverage

$nameIdTodo = Invoke-RestMethod "$BaseUrl/api/steam-nameids/todo"
Show-Json "steam-nameid-todo" $nameIdTodo

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
