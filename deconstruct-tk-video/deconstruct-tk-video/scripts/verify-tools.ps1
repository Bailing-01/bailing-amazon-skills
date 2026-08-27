$ErrorActionPreference = 'Stop'

$python = Join-Path $env:LOCALAPPDATA 'tianguo-video\python-env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Dedicated Python environment is missing: $python"
}

$version = & $python -c "import gallery_dl; print(gallery_dl.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error 'gallery-dl could not be imported from the dedicated Python environment.'
}

Write-Host "gallery-dl Windows version: $version"
Write-Host "Python: $python"
