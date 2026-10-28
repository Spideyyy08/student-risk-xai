# Start the MySQL container
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
docker compose up -d db
docker compose ps