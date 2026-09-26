param(
    [ValidateRange(1,100)][int]$Limit = 20,
    [ValidateRange(1,10)][int]$Pages = 1
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        throw 'Install the Python environment first; see README.md.'
    }
    & '.venv/Scripts/python.exe' -X utf8 -m land_discover.cli scrape hamrobazar --limit $Limit --pages $Pages --csv data/hamrobazar-listings.csv
    if ($LASTEXITCODE -ne 0) { throw 'Collection reported errors; inspect the output and run log.' }
} finally { Pop-Location }
