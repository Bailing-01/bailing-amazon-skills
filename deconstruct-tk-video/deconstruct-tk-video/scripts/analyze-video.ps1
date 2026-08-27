param(
    [Parameter(Mandatory = $true)][string]$Video,
    [string]$WorkDir,
    [ValidateSet("base", "small", "medium")][string]$Model = "small"
)
$ErrorActionPreference = "Stop"

$portableBin = Join-Path $env:LOCALAPPDATA "tianguo-video\tools\ffmpeg\bin"
$ffmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
$ffprobeCommand = Get-Command ffprobe -ErrorAction SilentlyContinue
if (-not $ffmpegCommand -and (Test-Path -LiteralPath (Join-Path $portableBin "ffmpeg.exe"))) {
    $ffmpegCommand = Get-Item -LiteralPath (Join-Path $portableBin "ffmpeg.exe")
}
if (-not $ffprobeCommand -and (Test-Path -LiteralPath (Join-Path $portableBin "ffprobe.exe"))) {
    $ffprobeCommand = Get-Item -LiteralPath (Join-Path $portableBin "ffprobe.exe")
}
if (-not $ffmpegCommand -or -not $ffprobeCommand) {
    throw "FFmpeg is missing. Run setup-windows.ps1 first."
}
$ffmpegExe = $ffmpegCommand.Source
if (-not $ffmpegExe) { $ffmpegExe = $ffmpegCommand.FullName }
$ffprobeExe = $ffprobeCommand.Source
if (-not $ffprobeExe) { $ffprobeExe = $ffprobeCommand.FullName }

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

$resolvedVideo = (Resolve-Path -LiteralPath $Video).ProviderPath
if (-not $WorkDir) { $WorkDir = Join-Path (Get-Location) ".video-cache" }
$hash = (Get-FileHash -LiteralPath $resolvedVideo -Algorithm SHA256).Hash.ToLowerInvariant()
$cache = Join-Path $WorkDir $hash
$frames = Join-Path $cache "frames"
New-Item -ItemType Directory -Path $frames -Force | Out-Null

$audio = Join-Path $cache "audio.wav"
$transcript = Join-Path $cache "transcript.json"
$metadata = Join-Path $cache "metadata.json"
$manifest = Join-Path $cache "manifest.json"
$frameIndex = Join-Path $cache "frames.json"

if (-not (Test-Path -LiteralPath $metadata) -or (Get-Item -LiteralPath $metadata).Length -lt 10) {
    & $ffprobeExe -v quiet -print_format json -show_format -show_streams -- $resolvedVideo |
        Set-Content -LiteralPath $metadata -Encoding utf8
}
if (-not (Test-Path -LiteralPath $audio) -or (Get-Item -LiteralPath $audio).Length -lt 44) {
    & $ffmpegExe -y -hide_banner -loglevel error -i $resolvedVideo -vn -ac 1 -ar 16000 -c:a pcm_s16le $audio
}
$transcriptValid = $false
$python = Find-CompatiblePython
if (-not $python) { throw "Compatible Python 3.10-3.12 is missing." }
if (Test-Path -LiteralPath $transcript) {
    try {
        $cachedTranscript = Get-Content -LiteralPath $transcript -Raw -Encoding utf8 | ConvertFrom-Json
        $transcriptValid = ($cachedTranscript.model -eq $Model -and $null -ne $cachedTranscript.segments)
    } catch {}
}
if (-not $transcriptValid) {
    $script = Join-Path $PSScriptRoot "transcribe_faster_whisper.py"
    $modelRoot = Join-Path $env:LOCALAPPDATA "tianguo-video\models"
    & $python $script $audio $transcript --model $Model --download-root $modelRoot
    if ($LASTEXITCODE -ne 0) { throw "Transcription failed. Dense full-video frame extraction was not started." }
}

$frameIndexValid = $false
if (Test-Path -LiteralPath $frameIndex) {
    try {
        $cachedFrames = Get-Content -LiteralPath $frameIndex -Raw -Encoding utf8 | ConvertFrom-Json
        $frameIndexValid = ($cachedFrames.strategy -in @("semantic-scene-v1", "semantic-scene-v2") -and $cachedFrames.frame_count -gt 0)
    } catch {}
}
if (-not $frameIndexValid) {
    $extractor = Join-Path $PSScriptRoot "extract-semantic-frames.py"
    & $python $extractor $resolvedVideo $frames --transcript $transcript --ffmpeg $ffmpegExe --ffprobe $ffprobeExe --max-frames 30 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Semantic frame extraction failed." }
}
$frameData = Get-Content -LiteralPath $frameIndex -Raw -Encoding utf8 | ConvertFrom-Json
$frameCount = [int]$frameData.frame_count
$duration = [math]::Ceiling([double]$frameData.duration_seconds)

[ordered]@{
    schema_version = 2
    video_sha256 = $hash
    model = $Model
    duration_seconds = $duration
    frame_strategy = $frameData.strategy
    frame_count = $frameCount
    updated_at = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -LiteralPath $manifest -Encoding utf8

[ordered]@{
    video = $resolvedVideo
    cache = $cache
    metadata = $metadata
    audio = $audio
    transcript = $transcript
    frames = $frames
    frames_index = $frameIndex
    manifest = $manifest
    frame_strategy = $frameData.strategy
    frame_count = $frameCount
} | ConvertTo-Json
