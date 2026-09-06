$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host '[1/4] Python tests'
python -m unittest discover -s tests -v

Write-Host '[2/4] Serving payload dry-run'
python jobs/check_serving_payload.py --input data/processed/demo.json
python jobs/load_serving_tables.py --input data/processed/demo.json --dry-run

Write-Host '[3/4] Compose config'
docker compose config | Out-Null

Write-Host '[4/4] Frontend production build'
npm --prefix frontend run build

Write-Host 'GeoTrack acceptance checks passed.'
