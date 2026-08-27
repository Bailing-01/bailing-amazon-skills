param(
    [Parameter(Mandatory = $true)][string]$Source,
    [string]$WorkDir = (Get-Location).Path,
    [ValidateSet("base", "small", "medium")][string]$Model = "small"
)
$ErrorActionPreference = "Stop"

$isUrl = $Source -match "^https?://"
$videos = Join-Path $WorkDir "videos"
$cache = Join-Path $WorkDir ".video-cache"
New-Item -ItemType Directory -Path $videos,$cache -Force | Out-Null

if ($isUrl) {
    $uri = [Uri]$Source
    if ($uri.Host -notmatch "(^|\.)tiktok\.com$") {
        throw "Only public TikTok links are supported. Use a local video file for other sources."
    }
    $python = Join-Path $env:LOCALAPPDATA "tianguo-video\python-env\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) { throw "The tianguo-video Python environment is missing. Run setup-windows.ps1 first." }
    & $python -c "import gallery_dl" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "gallery-dl is missing. Run setup-windows.ps1 first." }
    $videoId = if ($Source -match "/video/(\d+)") { $Matches[1] } else { throw "The TikTok video ID could not be parsed from the URL." }
    & $python -m gallery_dl --directory $videos --filename "{id}.{extension}" -- $Source
    $primaryExitCode = $LASTEXITCODE
    if ($primaryExitCode -ne 0) {
        [Console]::Error.WriteLine("[download] gallery-dl failed (exit $primaryExitCode); trying the public no-cookie fallback.")
        $partial = Join-Path $videos "$videoId.fallback.partial.mp4"
        try {
            $encodedSource = [Uri]::EscapeDataString($Source)
            $headers = @{ "User-Agent" = "tiangege-tiktok-workflow/4.0" }
            $response = Invoke-RestMethod -Uri "https://www.tikwm.com/api/?url=$encodedSource" -Method Get -Headers $headers -TimeoutSec 30
            if ($response.code -ne 0 -or -not $response.data.play) {
                throw "the fallback endpoint did not return a downloadable video"
            }
            if ([string]$response.data.id -ne $videoId) {
                throw "the fallback video ID does not match the requested TikTok video"
            }

            $downloadUri = [Uri][string]$response.data.play
            if ($downloadUri.Scheme -ne "https" -or $downloadUri.Host -notmatch "(^|\.)tiktokcdn(-us)?\.com$") {
                throw "the fallback returned an untrusted download host"
            }

            Invoke-WebRequest -Uri $downloadUri.AbsoluteUri -OutFile $partial -Headers $headers -UseBasicParsing -TimeoutSec 120
            if (-not (Test-Path -LiteralPath $partial) -or (Get-Item -LiteralPath $partial).Length -lt 1024) {
                throw "the fallback video file is missing or unexpectedly small"
            }

            $ffprobe = Join-Path $env:LOCALAPPDATA "tianguo-video\tools\ffmpeg\bin\ffprobe.exe"
            if (-not (Test-Path -LiteralPath $ffprobe)) {
                throw "FFprobe is missing; run setup-windows.ps1 first"
            }
            $streamTypes = @(& $ffprobe -v error -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1 $partial)
            if ($LASTEXITCODE -ne 0 -or $streamTypes -notcontains "video" -or $streamTypes -notcontains "audio") {
                throw "the fallback file did not pass FFprobe video/audio validation"
            }

            Move-Item -LiteralPath $partial -Destination (Join-Path $videos "$videoId.mp4") -Force
            [Console]::Error.WriteLine("[download] public fallback succeeded and passed ID, host, size and FFprobe checks.")
        }
        catch {
            if (Test-Path -LiteralPath $partial) {
                Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
            }
            throw "TikTok download failed: gallery-dl exit $primaryExitCode; public fallback failed: $($_.Exception.Message). Upload the local video."
        }
    }
    $video = Get-ChildItem -LiteralPath $videos -File |
        Where-Object { $_.BaseName -eq $videoId -and $_.Extension -match "^\.(mp4|mov|webm|m4v)$" } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $video) { throw "gallery-dl finished without a readable video file." }
    $sourceType = "tiktok"
} else {
    $video = (Resolve-Path -LiteralPath $Source).ProviderPath
    $sourceType = "local"
}

$analysis = & (Join-Path $PSScriptRoot "analyze-video.ps1") -Video $video -WorkDir $cache -Model $Model |
    ConvertFrom-Json
[ordered]@{
    pipeline_id = "tk-content-pipeline/v1"
    artifact_type = "prepared_media"
    source_type = $sourceType
    source = $Source
    video = $analysis.video
    cache = $analysis.cache
    transcript = $analysis.transcript
    frames = $analysis.frames
    frames_index = $analysis.frames_index
    manifest = $analysis.manifest
    frame_strategy = $analysis.frame_strategy
    frame_count = $analysis.frame_count
} | ConvertTo-Json
