$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

function Invoke-CheckedNative {
  param(
    [Parameter(Mandatory = $true)][string]$Command,
    [Parameter(Mandatory = $true)][string[]]$Arguments
  )
  & $Command @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "命令失败（退出码 $LASTEXITCODE）：$Command $($Arguments -join ' ')"
  }
}

Write-Host '[1/4] Python tests'
Invoke-CheckedNative python @('-m', 'unittest', 'discover', '-s', 'tests', '-v')

Write-Host '[2/4] Serving payload dry-run'
Invoke-CheckedNative python @('jobs/check_serving_payload.py', '--input', 'data/processed/demo.json')
Invoke-CheckedNative python @('jobs/load_serving_tables.py', '--input', 'data/processed/demo.json', '--dry-run')

Write-Host '[3/4] Compose config'
docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "命令失败（退出码 $LASTEXITCODE）：docker compose config" }

Write-Host '[4/4] Frontend production build'
Invoke-CheckedNative npm @('--prefix', 'frontend', 'run', 'build')

Write-Host 'GeoTrack acceptance checks passed.'
