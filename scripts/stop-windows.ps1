# Stop Prelegal (Windows).
#requires -Version 5.1
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

Assert-Docker
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    Write-Host 'Stopping Prelegal...'
    docker compose down
    Write-Host 'Stopped.'
}
finally {
    Pop-Location
}
