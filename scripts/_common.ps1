# Shared by start-windows.ps1 and stop-windows.ps1.

function Assert-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error 'Docker is required but was not found on PATH. Install Docker Desktop: https://docs.docker.com/get-docker/'
    }

    docker compose version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "This needs Docker Compose v2 ('docker compose', not 'docker-compose')."
    }

    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Docker is installed but not running. Start it and try again.'
    }
}

function Test-Health {
    try {
        # -UseBasicParsing keeps this working on Windows PowerShell where
        # Internet Explorer's engine may be unavailable.
        $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' `
            -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}
