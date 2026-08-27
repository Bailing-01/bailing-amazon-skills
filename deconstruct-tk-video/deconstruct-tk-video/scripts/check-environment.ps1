$ErrorActionPreference = "Stop"

function Find-Command([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
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
    return $null
}

$ffmpeg = Find-Command "ffmpeg"
$ffprobe = Find-Command "ffprobe"
$python = Find-CompatiblePython
$nvidia = Find-Command "nvidia-smi"
$backendMarker = Join-Path $env:LOCALAPPDATA "tianguo-video\backend-verified.json"

$portableBin = Join-Path $env:LOCALAPPDATA "tianguo-video\tools\ffmpeg\bin"
if (-not $ffmpeg) {
    $candidate = Join-Path $portableBin "ffmpeg.exe"
    if (Test-Path -LiteralPath $candidate) { $ffmpeg = $candidate }
}
if (-not $ffprobe) {
    $candidate = Join-Path $portableBin "ffprobe.exe"
    if (Test-Path -LiteralPath $candidate) { $ffprobe = $candidate }
}

$fasterWhisper = $false
$galleryDl = $false
$backendVerified = $false
if ($python) {
    try {
        & $python -c "import faster_whisper" 2>$null
        $fasterWhisper = ($LASTEXITCODE -eq 0)
    } catch {}
    try {
        & $python -c "import gallery_dl" 2>$null
        $galleryDl = ($LASTEXITCODE -eq 0)
    } catch {}
}
if ($fasterWhisper -and (Test-Path -LiteralPath $backendMarker)) {
    try {
        $markerData = Get-Content -LiteralPath $backendMarker -Raw -Encoding utf8 | ConvertFrom-Json
        $backendVerified = [bool]$markerData.verified
    } catch {}
}

$result = [ordered]@{
    platform = "windows"
    architecture = $env:PROCESSOR_ARCHITECTURE
    ffmpeg = $ffmpeg
    ffprobe = $ffprobe
    gallery_dl = $galleryDl
    python = $python
    faster_whisper = $fasterWhisper
    transcription_backend_verified = $backendVerified
    nvidia_cuda_candidate = [bool]$nvidia
    local_video_ready = [bool]($ffmpeg -and $ffprobe -and $python -and $fasterWhisper -and $backendVerified)
    tiktok_link_ready = [bool]($ffmpeg -and $ffprobe -and $python -and $fasterWhisper -and $backendVerified -and $galleryDl)
    ready = [bool]($ffmpeg -and $ffprobe -and $python -and $fasterWhisper -and $backendVerified)
}

$result | ConvertTo-Json -Depth 3
if (-not $result.ready) { exit 2 }
