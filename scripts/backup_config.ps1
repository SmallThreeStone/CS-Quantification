param(
  [string]$BackupDir = "./backups/config",
  [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$root = Resolve-Path -LiteralPath "."
$resolvedBackupDir = Join-Path $root $BackupDir
$stagingDir = Join-Path $resolvedBackupDir "config_$timestamp"
$archivePath = Join-Path $resolvedBackupDir "config_$timestamp.zip"

New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

$files = @(
  ".env",
  ".env.example",
  "docker-compose.yml",
  "README.md",
  "CLAUDE.md"
)

foreach ($file in $files) {
  if (Test-Path -LiteralPath $file) {
    Copy-Item -LiteralPath $file -Destination $stagingDir -Force
  } else {
    Write-Host "skip missing file: $file"
  }
}

if (Test-Path -LiteralPath "scripts") {
  Copy-Item -LiteralPath "scripts" -Destination (Join-Path $stagingDir "scripts") -Recurse -Force
}

Compress-Archive -LiteralPath (Join-Path $stagingDir "*") -DestinationPath $archivePath -Force
Remove-Item -LiteralPath $stagingDir -Recurse -Force

$file = Get-Item -LiteralPath $archivePath
if ($file.Length -le 0) {
  throw "config backup file is empty: $archivePath"
}

if ($RetentionDays -gt 0) {
  $cutoff = (Get-Date).AddDays(-$RetentionDays)
  Get-ChildItem -LiteralPath $resolvedBackupDir -Filter "*.zip" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force
}

Write-Host "== config backup complete =="
Write-Host "path=$archivePath"
Write-Host "size=$($file.Length)"
