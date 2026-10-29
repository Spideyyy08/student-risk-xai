# Start Docker MySQL 8.0 Container on Port 3307
$ErrorActionPreference = "Stop"

Write-Host "Starting MySQL 8.0 Docker container on port 3307..."
docker-compose up -d
