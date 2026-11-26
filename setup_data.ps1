param(
    [ValidateSet('complete','data-only','db-only','verify','load-mariadb','load-postgis','load-fuseki','load-qdrant')]
    [string]$Mode = 'complete',
    [string]$Archive,
    [string]$ArchiveSha256,
    [string]$ArchiveUrl,
    [string]$Project = 'dalila-data2-local',
    [switch]$WithRedis,
    [switch]$SkipDependencies
)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction Stop
$arguments = @('scripts/setup_data.py', '--mode', $Mode, '--project', $Project)
if ($Archive) { $arguments += @('--archive', $Archive) }
if ($ArchiveSha256) { $arguments += @('--archive-sha256', $ArchiveSha256) }
if ($ArchiveUrl) { $arguments += @('--archive-url', $ArchiveUrl) }
if ($WithRedis) { $arguments += '--with-redis' }
if ($SkipDependencies) { $arguments += '--skip-dependencies' }
Push-Location $PSScriptRoot
try {
    & $python.Source @arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
