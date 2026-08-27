param(
    [Parameter(Mandatory = $true)][string]$ProfileUrl,
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [ValidateRange(1, 100)][int]$Top = 10,
    [ValidateRange(1, 3650)][int]$Days = 30,
    [ValidateRange(0, 168)][int]$CacheHours = 20,
    [switch]$Refresh
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Convert-ToNullableInt64 {
    param([object]$Value)
    $parsed = [long]0
    if ($null -ne $Value -and [long]::TryParse(([string]$Value), [ref]$parsed)) { return $parsed }
    return $null
}

function Get-MetricSortValue {
    param([object]$Value)
    if ($null -eq $Value) { return [long]::MinValue }
    return [long]$Value
}

function Convert-EpochToIso {
    param([long]$Epoch)
    return [DateTimeOffset]::FromUnixTimeSeconds($Epoch).UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Invoke-GalleryDl {
    param([string[]]$Arguments)
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    if ($script:GalleryExe) {
        $output = @(& $script:GalleryExe @Arguments 2>&1)
    } else {
        $pythonArguments = @("-m", "gallery_dl") + $Arguments
        $output = @(& $script:PythonExe @pythonArguments 2>&1)
    }
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = @($output | ForEach-Object { $_.ToString() })
    }
}

function New-ContractManifest {
    param(
        [string]$GeneratedAt,
        [object]$Account,
        [int]$WindowDays,
        [int]$TopCount,
        [string]$CacheStatus,
        [array]$Videos
    )
    return [ordered]@{
        pipeline_id = "tk-content-pipeline/v1"
        artifact_type = "account_manifest"
        generated_at = $GeneratedAt
        account = $Account
        selection = [ordered]@{
            days = $WindowDays
            top = $TopCount
            metric = "plays"
            cache_status = $CacheStatus
        }
        videos = @($Videos)
    }
}

$uri = $null
try { $uri = [Uri]$ProfileUrl } catch { throw "ProfileUrl is not a valid URL." }
if ($uri.Scheme -notin @("http", "https") -or $uri.Host -notmatch "(^|\.)tiktok\.com$" -or $uri.AbsolutePath -notmatch "^/@[^/]+/?$") {
    throw "ProfileUrl must be a public TikTok profile URL such as https://www.tiktok.com/@name"
}

$handle = ($uri.AbsolutePath.Trim('/') -replace '^@', '')
$canonicalProfile = "https://www.tiktok.com/@$handle"
$accountObject = [ordered]@{ platform = "tiktok"; handle = $handle; profile_url = $canonicalProfile }
$safeHandle = $handle -replace '[^A-Za-z0-9._-]', '_'
$resolvedWorkDir = [System.IO.Path]::GetFullPath($WorkDir)
$profileDir = Join-Path $resolvedWorkDir "profile-cache"
$videoDir = Join-Path $resolvedWorkDir "videos"
New-Item -ItemType Directory -Path $resolvedWorkDir,$profileDir,$videoDir -Force | Out-Null

$allPath = Join-Path $profileDir "$safeHandle-all-video-posts.json"
$rankingPath = Join-Path $profileDir "$safeHandle-${Days}d-top$Top.json"
$manifestPath = Join-Path $resolvedWorkDir "account_manifest.json"
$cutoffEpoch = [DateTimeOffset]::UtcNow.AddDays(-$Days).ToUnixTimeSeconds()
$generatedAt = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")

$pythonRoot = Join-Path $env:LOCALAPPDATA "tianguo-video\python-env"
$script:GalleryExe = Join-Path $pythonRoot "Scripts\gallery-dl.exe"
$script:PythonExe = Join-Path $pythonRoot "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $script:GalleryExe)) { $script:GalleryExe = $null }
if (-not $script:GalleryExe) {
    if (-not (Test-Path -LiteralPath $script:PythonExe)) {
        throw "gallery-dl is missing. Expected the dedicated environment under %LOCALAPPDATA%\tianguo-video\python-env."
    }
    & $script:PythonExe -c "import gallery_dl" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "gallery-dl is missing from the dedicated tianguo-video Python environment." }
}

$cacheFresh = $false
if (Test-Path -LiteralPath $allPath) {
    $cacheAgeHours = ([DateTime]::UtcNow - (Get-Item -LiteralPath $allPath).LastWriteTimeUtc).TotalHours
    $cacheFresh = ($cacheAgeHours -le $CacheHours)
}

$allVideos = @()
$cacheStatus = if ($Refresh) { "refresh" } elseif ($cacheFresh) { "hit" } else { "miss" }
if ((-not $Refresh) -and $cacheFresh) {
    try {
        $cached = Get-Content -LiteralPath $allPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $allVideos = @($cached)
    } catch {
        $cacheFresh = $false
        $cacheStatus = "miss"
    }
}

if (-not $cacheFresh -or $Refresh) {
    $format = "{id}|{stats[playCount]}|{stats[diggCount]}|{stats[commentCount]}|{stats[shareCount]}|{createTime}|{type}|{extension}"
    $scan = Invoke-GalleryDl -Arguments @("--print", $format, ($canonicalProfile + "/posts"))
    if ($scan.ExitCode -ne 0) {
        $failure = New-ContractManifest -GeneratedAt $generatedAt -Account $accountObject -WindowDays $Days -TopCount $Top -CacheStatus "scan_failed" -Videos @()
        $failure | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
        $failure | ConvertTo-Json -Depth 8
        $diagnostic = ($scan.Output | Select-Object -Last 5) -join " | "
        [Console]::Error.WriteLine("TikTok profile scan failed. Check login, region, CAPTCHA, privacy, or risk-control restrictions. $diagnostic")
        exit 2
    }

    $records = @()
    foreach ($line in $scan.Output) {
        if ($line -notmatch '^\d+\|') { continue }
        $parts = $line -split '\|', 8
        if ($parts.Count -lt 8 -or $parts[6] -ne "video" -or $parts[7] -ne "mp4") { continue }
        $createdEpoch = Convert-ToNullableInt64 $parts[5]
        if ($null -eq $createdEpoch -or $createdEpoch -le 0) { continue }
        $records += [pscustomobject][ordered]@{
            video_id = [string]$parts[0]
            source_url = "https://www.tiktok.com/@$handle/video/$($parts[0])"
            published_at = Convert-EpochToIso $createdEpoch
            created_epoch = $createdEpoch
            metrics = [ordered]@{
                plays = Convert-ToNullableInt64 $parts[1]
                likes = Convert-ToNullableInt64 $parts[2]
                comments = Convert-ToNullableInt64 $parts[3]
                shares = Convert-ToNullableInt64 $parts[4]
            }
        }
    }
    $allVideos = @($records | Group-Object video_id | ForEach-Object {
        $_.Group | Sort-Object @{Expression = { Get-MetricSortValue $_.metrics.plays }; Descending = $true}, @{Expression = { $_.created_epoch }; Descending = $true} | Select-Object -First 1
    } | Sort-Object @{Expression = { Get-MetricSortValue $_.metrics.plays }; Descending = $true}, @{Expression = { $_.created_epoch }; Descending = $true}, @{Expression = { $_.video_id }; Descending = $false})
    ConvertTo-Json -InputObject @($allVideos) -Depth 6 | Set-Content -LiteralPath $allPath -Encoding UTF8
}

$recent = @($allVideos | Where-Object { [long]$_.created_epoch -ge $cutoffEpoch })
$selected = @($recent | Sort-Object @{Expression = { Get-MetricSortValue $_.metrics.plays }; Descending = $true}, @{Expression = { [long]$_.created_epoch }; Descending = $true}, @{Expression = { [string]$_.video_id }; Descending = $false} | Select-Object -First $Top)

$rankedCache = @()
$rank = 0
foreach ($item in $selected) {
    $rank++
    $rankedCache += [pscustomobject][ordered]@{
        rank = $rank
        video_id = [string]$item.video_id
        source_url = [string]$item.source_url
        published_at = [string]$item.published_at
        metrics = $item.metrics
    }
}
ConvertTo-Json -InputObject @($rankedCache) -Depth 6 | Set-Content -LiteralPath $rankingPath -Encoding UTF8

$manifestVideos = @()
$rank = 0
foreach ($item in $selected) {
    $rank++
    $videoPath = Join-Path $videoDir ("{0}.mp4" -f $item.video_id)
    $status = "failed"
    $errorMessage = $null
    if ((Test-Path -LiteralPath $videoPath) -and (Get-Item -LiteralPath $videoPath).Length -ge 1024) {
        $status = "cached"
    } else {
        $download = Invoke-GalleryDl -Arguments @("--filter", "type == 'video' and extension == 'mp4'", "--directory", $videoDir, "--filename", "{id}.{extension}", "--", [string]$item.source_url)
        if ($download.ExitCode -eq 0 -and (Test-Path -LiteralPath $videoPath) -and (Get-Item -LiteralPath $videoPath).Length -ge 1024) {
            $status = "downloaded"
        } else {
            $diagnostic = ($download.Output | Select-Object -Last 5) -join " | "
            if (-not $diagnostic) { $diagnostic = "Downloader returned no diagnostic." }
            $errorMessage = "Video download failed: $diagnostic"
        }
    }

    $manifestVideos += [pscustomobject][ordered]@{
        video_id = [string]$item.video_id
        source_url = [string]$item.source_url
        local_path = if ($status -eq "failed") { $null } else { [System.IO.Path]::GetFullPath($videoPath) }
        published_at = [string]$item.published_at
        metrics = [ordered]@{
            plays = $item.metrics.plays
            likes = $item.metrics.likes
            comments = $item.metrics.comments
            shares = $item.metrics.shares
        }
        rank = $rank
        account = $accountObject
        acquisition = [ordered]@{ status = $status; error = $errorMessage }
    }
}

$manifest = New-ContractManifest -GeneratedAt $generatedAt -Account $accountObject -WindowDays $Days -TopCount $Top -CacheStatus $cacheStatus -Videos $manifestVideos
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifest | ConvertTo-Json -Depth 8
