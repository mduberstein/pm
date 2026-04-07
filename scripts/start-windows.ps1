$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$ImageName = "pm-mvp:local"
$ContainerName = "pm-mvp"
$HostPort = if ($env:PORT) { $env:PORT } else { "8000" }

Set-Location $RootDir

Write-Host "Building Docker image $ImageName..."
docker build -t $ImageName .

$exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $ContainerName }
if ($exists) {
  Write-Host "Removing existing container $ContainerName..."
  docker rm -f $ContainerName | Out-Null
}

Write-Host "Starting container $ContainerName on port $HostPort..."
docker run -d `
  --name $ContainerName `
  --env-file (Join-Path $RootDir ".env") `
  -p "${HostPort}:8000" `
  $ImageName | Out-Null

Write-Host "App is starting. Open http://localhost:$HostPort"
