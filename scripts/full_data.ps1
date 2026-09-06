param(
  [ValidateSet('summary','spark')]
  [string]$Mode = 'summary',
  [string]$DataRoot = 'Geolife Trajectories 1.3/Data',
  [string]$Manifest = 'data/processed/full-manifest.json'
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path -LiteralPath $DataRoot)) {
  throw "GeoLife data root not found: $DataRoot"
}

if ($Mode -eq 'summary') {
  python jobs/full_summary.py --data-root $DataRoot --output $Manifest
  exit $LASTEXITCODE
}

python jobs/spark_distributed.py `
  --input "$DataRoot/*/Trajectory/*.plt" `
  --output 'data/processed/full-points' `
  --quality-output 'data/processed/full-quality'
exit $LASTEXITCODE
