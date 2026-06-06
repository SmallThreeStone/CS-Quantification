param(
  [string]$BackupDir = "./backups/postgres",
  [int]$RetentionDays = 14,
  [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"

function Get-EnvValue($Name, $Default) {
  if (Test-Path ".env") {
    $line = Get-Content ".env" | Where-Object { $_ -match "^$Name=" } | Select-Object -First 1
    if ($line) {
      return ($line -replace "^$Name=", "").Trim()
    }
  }
  return $Default
}

$dbName = Get-EnvValue "POSTGRES_DB" "cs_quant"
$dbUser = Get-EnvValue "POSTGRES_USER" "cs_quant"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resolvedBackupDir = Resolve-Path -LiteralPath "." | ForEach-Object { Join-Path $_ $BackupDir }
New-Item -ItemType Directory -Force -Path $resolvedBackupDir | Out-Null
$backupPath = Join-Path $resolvedBackupDir "$($dbName)_$timestamp.dump"

Write-Host "== backup postgres =="
Write-Host "database=$dbName user=$dbUser output=$backupPath"

docker compose -f $ComposeFile exec -T postgres pg_dump -U $dbUser -d $dbName -F c -f "/tmp/$($dbName)_$timestamp.dump"
docker compose -f $ComposeFile cp "postgres:/tmp/$($dbName)_$timestamp.dump" $backupPath
docker compose -f $ComposeFile exec -T postgres rm "/tmp/$($dbName)_$timestamp.dump"

$file = Get-Item -LiteralPath $backupPath
if ($file.Length -le 0) {
  throw "backup file is empty: $backupPath"
}

if ($RetentionDays -gt 0) {
  $cutoff = (Get-Date).AddDays(-$RetentionDays)
  Get-ChildItem -LiteralPath $resolvedBackupDir -Filter "*.dump" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force
}

Write-Host "== backup complete =="
Write-Host "path=$backupPath"
Write-Host "size=$($file.Length)"
