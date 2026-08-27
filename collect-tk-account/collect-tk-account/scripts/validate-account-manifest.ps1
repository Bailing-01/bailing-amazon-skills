param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [switch]$SkipFileChecks
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Assert-ExactProperties {
    param([object]$Object, [string[]]$Expected, [string]$Context)
    if ($null -eq $Object) { throw "$Context is null." }
    $actual = @($Object.PSObject.Properties.Name)
    $missing = @($Expected | Where-Object { $actual -notcontains $_ })
    $extra = @($actual | Where-Object { $Expected -notcontains $_ })
    if ($missing.Count -gt 0) { throw "$Context is missing: $($missing -join ', ')." }
    if ($extra.Count -gt 0) { throw "$Context has non-contract fields: $($extra -join ', ')." }
}

function Assert-NullableNonnegativeInteger {
    param([object]$Value, [string]$Context)
    if ($null -eq $Value) { return }
    if ($Value -isnot [int] -and $Value -isnot [long]) { throw "$Context must be an integer or null." }
    if ([long]$Value -lt 0) { throw "$Context must not be negative." }
}

$resolved = (Resolve-Path -LiteralPath $ManifestPath).ProviderPath
$manifest = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-ExactProperties $manifest @("pipeline_id", "artifact_type", "generated_at", "account", "selection", "videos") "manifest"
if ($manifest.pipeline_id -ne "tk-content-pipeline/v1") { throw "pipeline_id must be tk-content-pipeline/v1." }
if ($manifest.artifact_type -ne "account_manifest") { throw "artifact_type must be account_manifest." }
Assert-ExactProperties $manifest.account @("platform", "handle", "profile_url") "account"
if ($manifest.account.platform -ne "tiktok") { throw "account.platform must be tiktok." }
Assert-ExactProperties $manifest.selection @("days", "top", "metric", "cache_status") "selection"
if ($manifest.selection.metric -ne "plays") { throw "selection.metric must be plays." }
if ($manifest.selection.cache_status -notin @("hit", "miss", "refresh", "scan_failed")) { throw "Invalid selection.cache_status." }

$videos = @($manifest.videos)
$ids = @{}
$expectedRank = 1
foreach ($video in ($videos | Sort-Object rank)) {
    Assert-ExactProperties $video @("video_id", "source_url", "local_path", "published_at", "metrics", "rank", "account", "acquisition") "video"
    Assert-ExactProperties $video.metrics @("plays", "likes", "comments", "shares") "video.metrics"
    foreach ($metricName in @("plays", "likes", "comments", "shares")) {
        Assert-NullableNonnegativeInteger $video.metrics.$metricName "video.metrics.$metricName"
    }
    Assert-ExactProperties $video.account @("platform", "handle", "profile_url") "video.account"
    Assert-ExactProperties $video.acquisition @("status", "error") "video.acquisition"
    if ($video.account.platform -ne "tiktok" -or $video.account.handle -ne $manifest.account.handle -or $video.account.profile_url -ne $manifest.account.profile_url) {
        throw "Video account does not match the manifest account: $($video.video_id)"
    }
    if ($ids.ContainsKey([string]$video.video_id)) { throw "Duplicate video_id: $($video.video_id)" }
    $ids[[string]$video.video_id] = $true
    if ([int]$video.rank -ne $expectedRank) { throw "Ranks must be continuous from 1; expected $expectedRank but found $($video.rank)." }
    $expectedRank++
    if ($video.acquisition.status -notin @("downloaded", "cached", "failed")) { throw "Invalid acquisition status for $($video.video_id)." }
    if ($video.acquisition.status -eq "failed") {
        if ([string]::IsNullOrWhiteSpace([string]$video.acquisition.error)) { throw "Failed item $($video.video_id) must include acquisition.error." }
        if ($null -ne $video.local_path) { throw "Failed item $($video.video_id) must use local_path=null." }
    } else {
        if ([string]::IsNullOrWhiteSpace([string]$video.local_path)) { throw "Successful item $($video.video_id) must include local_path." }
        if (-not $SkipFileChecks) {
            if (-not (Test-Path -LiteralPath $video.local_path -PathType Leaf)) { throw "Local video is missing: $($video.local_path)" }
            if ((Get-Item -LiteralPath $video.local_path).Length -lt 1024) { throw "Local video is too small: $($video.local_path)" }
        }
        if ($null -ne $video.acquisition.error) { throw "Successful item $($video.video_id) must use acquisition.error=null." }
    }
}
if ($videos.Count -gt [int]$manifest.selection.top) { throw "videos count exceeds selection.top." }

[pscustomobject][ordered]@{
    valid = $true
    manifest = $resolved
    pipeline_id = $manifest.pipeline_id
    artifact_type = $manifest.artifact_type
    selected = $videos.Count
    downloaded = @($videos | Where-Object { $_.acquisition.status -eq "downloaded" }).Count
    cached = @($videos | Where-Object { $_.acquisition.status -eq "cached" }).Count
    failed = @($videos | Where-Object { $_.acquisition.status -eq "failed" }).Count
} | ConvertTo-Json -Depth 3
