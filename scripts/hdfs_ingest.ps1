param(
  [string]$Source = 'Geolife Trajectories 1.3/Data',
  [string]$Target = 'hdfs:///geotrack/raw/Data'
)

if (-not (Get-Command hdfs -ErrorAction SilentlyContinue)) {
  throw 'hdfs command not found. Run this script inside the Hadoop client container.'
}

hdfs dfs -mkdir -p $Target
hdfs dfs -put -f $Source/* $Target/
Write-Output "GeoLife raw files uploaded to $Target"
