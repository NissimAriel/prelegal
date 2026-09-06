# Start Prelegal (Windows).
#requires -Version 5.1
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '_common.ps1')

Assert-Docker
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    Write-Host 'Building and starting Prelegal...'
    docker compose up --build --detach
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }

    # Generous: the first run builds the frontend and installs both toolchains.
    $timeoutSeconds = 300
    $waited = 0
    Write-Host -NoNewline 'Waiting for http://localhost:8000 to come up'
    while (-not (Test-Health)) {
        if ($waited -ge $timeoutSeconds) {
            Write-Host ''
            Write-Warning "Gave up after $timeoutSeconds seconds. Recent logs:"
            docker compose logs --tail 40
            exit 1
        }
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host -NoNewline '.'
    }

    Write-Host ''
    Write-Host 'Prelegal is running at http://localhost:8000'
}
finally {
    Pop-Location
}
