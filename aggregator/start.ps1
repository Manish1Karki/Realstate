$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        throw 'Create the virtual environment and install requirements first. See README.md.'
    }
    if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) {
        throw 'Build the frontend first: cd frontend; npm ci; npm run build.'
    }
    & '.venv/Scripts/python.exe' -m uvicorn land_discover.api:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
