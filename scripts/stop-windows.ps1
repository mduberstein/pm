$ErrorActionPreference = "Stop"

$ContainerName = "pm-mvp"
$exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $ContainerName }

if ($exists) {
  Write-Host "Stopping and removing $ContainerName..."
  docker rm -f $ContainerName | Out-Null
  Write-Host "Stopped."
} else {
  Write-Host "No container named $ContainerName found."
}
