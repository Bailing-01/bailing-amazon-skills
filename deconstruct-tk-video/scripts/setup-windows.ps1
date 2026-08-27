$ErrorActionPreference = "Stop"

function Ensure-WingetPackage([string]$Command, [string]$PackageId) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        & winget install --id $PackageId --exact --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "Package installation failed: $PackageId" }
    }
}

function Find-CompatiblePython {
    $environmentPython = Join-Path $env:LOCALAPPDATA "tianguo-video\python-env\Scripts\python.exe"
    if (Test-Path -LiteralPath $environmentPython) {
        return $environmentPython
    }
    $direct = Get-Command python -ErrorAction SilentlyContinue
    if ($direct) {
        try {
            $minor = & $direct.Source -c "import sys; print(sys.version_info.minor)"
            if ($LASTEXITCODE -eq 0 -and [int]$minor -ge 10 -and [int]$minor -le 12) {
                return $direct.Source
            }
        } catch {}
    }
    $uvRoot = Join-Path $env:APPDATA "uv\python"
    if (Test-Path -LiteralPath $uvRoot) {
        $candidate = Get-ChildItem -LiteralPath $uvRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "^cpython-3\.(10|11|12)\." } |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }
    $programsRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path -LiteralPath $programsRoot) {
        $candidate = Get-ChildItem -LiteralPath $programsRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "^Python3(10|11|12)$" } |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }
    return $null
}

$winget = Get-Command winget -ErrorAction SilentlyContinue
$portableFfmpeg = Join-Path $env:LOCALAPPDATA "tianguo-video\tools\ffmpeg\bin\ffmpeg.exe"
if ($winget) {
    Ensure-WingetPackage "ffmpeg" "Gyan.FFmpeg"
    if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) {
        Ensure-WingetPackage "python" "Python.Python.3.12"
    }
} elseif (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $portableFfmpeg)) {
    $toolRoot = Join-Path $env:LOCALAPPDATA "tianguo-video\tools"
    $installRoot = Join-Path $toolRoot "ffmpeg"
    $archive = Join-Path $toolRoot "ffmpeg-release-essentials.zip"
    $extractRoot = Join-Path $toolRoot "ffmpeg-extract"
    New-Item -ItemType Directory -Path $toolRoot -Force | Out-Null
    $archiveComplete = $false
    if (Test-Path -LiteralPath $archive) {
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip = [IO.Compression.ZipFile]::OpenRead($archive)
            $zip.Dispose()
            $archiveComplete = $true
        } catch {}
    }
    if (-not $archiveComplete) {
        if (Test-Path -LiteralPath $archive) {
            Remove-Item -LiteralPath $archive -Force
        }
        $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
        if ($curl) {
            & $curl.Source -L --fail --connect-timeout 15 --max-time 1200 --retry 2 `
                --output $archive "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            if ($LASTEXITCODE -ne 0) { throw "Portable FFmpeg download failed or timed out." }
        } else {
            $request = @{
                Uri = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                OutFile = $archive
                TimeoutSec = 300
            }
            Invoke-WebRequest @request
        }
    }
    if (-not (Test-Path -LiteralPath $archive) -or (Get-Item -LiteralPath $archive).Length -lt 1000000) {
        throw "Portable FFmpeg download is incomplete."
    }
    $archiveReady = $false
    for ($attempt = 1; $attempt -le 10; $attempt++) {
        try {
            $stream = [IO.File]::Open($archive, "Open", "Read", "None")
            $stream.Dispose()
            $archiveReady = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $archiveReady) { throw "Portable FFmpeg archive remained locked after download." }
    if (Test-Path -LiteralPath $extractRoot) {
        Remove-Item -LiteralPath $extractRoot -Recurse -Force
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot -Force
    $ffmpegExe = Get-ChildItem -LiteralPath $extractRoot -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if (-not $ffmpegExe) { throw "Portable FFmpeg archive did not contain ffmpeg.exe." }
    $sourceRoot = Split-Path (Split-Path $ffmpegExe.FullName -Parent) -Parent
    if (Test-Path -LiteralPath $installRoot) {
        Remove-Item -LiteralPath $installRoot -Recurse -Force
    }
    Move-Item -LiteralPath $sourceRoot -Destination $installRoot
    Remove-Item -LiteralPath $extractRoot -Recurse -Force
    Remove-Item -LiteralPath $archive -Force
}

$python = Find-CompatiblePython
if (-not $python) {
    throw "Compatible Python was not found. Install Python 3.10-3.12, then run this script again."
}

$environmentRoot = Join-Path $env:LOCALAPPDATA "tianguo-video\python-env"
$environmentPython = Join-Path $environmentRoot "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $environmentPython)) {
    New-Item -ItemType Directory -Path (Split-Path $environmentRoot -Parent) -Force | Out-Null
    & $python -m venv $environmentRoot
    if ($LASTEXITCODE -ne 0) { throw "Python virtual environment creation failed." }
}

& $environmentPython -m pip install --upgrade pip faster-whisper gallery-dl
if ($LASTEXITCODE -ne 0) { throw "faster-whisper installation failed." }

$modelRoot = Join-Path $env:LOCALAPPDATA "tianguo-video\models"
$backendMarker = Join-Path $env:LOCALAPPDATA "tianguo-video\backend-verified.json"
$backendCheck = Join-Path $PSScriptRoot "verify-transcription-backend.py"
& $environmentPython $backendCheck --download-root $modelRoot --marker $backendMarker
if ($LASTEXITCODE -ne 0) {
    throw "The transcription runtime could not load a model. Update the latest Microsoft Visual C++ x64 runtime from https://aka.ms/vc14/vc_redist.x64.exe, restart Windows, then rerun setup-windows.ps1."
}

Write-Host "Setup and transcription backend verification completed. Run check-environment.ps1."
