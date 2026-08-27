$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$skillPath = Join-Path $root "SKILL.md"
$openaiPath = Join-Path $root "agents\openai.yaml"
$skill = Get-Content -LiteralPath $skillPath -Raw -Encoding UTF8
$openai = Get-Content -LiteralPath $openaiPath -Raw -Encoding UTF8
$displayName = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("5pyA5pawMTA0772cVEvop4bpopHmi4bop6M="))
$noNineScripts = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("5LiN55Sf5oiQ5Lmd54mI6ISa5pys"))
$noLarkTools = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("5LiN6LCD55So6aOe5Lmm5bel5YW3"))

$requiredFiles = @(
    "SKILL.md",
    "agents\openai.yaml",
    "references\runtime.md",
    "references\breakdown-framework.md",
    "references\output-schema.md",
    "scripts\prepare-video.ps1",
    "scripts\prepare-video.sh",
    "scripts\prepare-account-manifest.py",
    "scripts\cluster-transcripts.py",
    "scripts\validate-breakdown-bundle.py",
    "scripts\extract-semantic-frames.py"
)
$requiredTokens = @(
    "tk-content-pipeline/v1",
    "account-manifest",
    "step1-batch-confirm",
    "step2-ten-part",
    "hook-comparison",
    "duplicate-clustering",
    "candidate-elements",
    "breakdown_bundle.json",
    $noNineScripts,
    $noLarkTools
)
$checks = [ordered]@{}
foreach ($relative in $requiredFiles) {
    $checks["file:$relative"] = Test-Path -LiteralPath (Join-Path $root $relative)
}
foreach ($token in $requiredTokens) {
    $checks["token:$token"] = $skill.Contains($token)
}
$checks["internal-name"] = $skill -match "(?m)^name: deconstruct-tk-video\r?$"
$checks["display-name"] = $openai.Contains(('display_name: "' + $displayName + '"'))
$checks["default-prompt"] = $openai.Contains('$deconstruct-tk-video')
$checks["quoted-openai-strings"] = @(
    $openai -split "`r?`n" |
        Where-Object { $_ -match '^\s+[a-z_]+:\s+' } |
        Where-Object { $_ -notmatch '^\s+[a-z_]+:\s+".*"\s*$' }
).Count -eq 0
$checks["no-lark-config"] = -not (Test-Path -LiteralPath (Join-Path $root "references\lark-base-config.json"))
$checks["no-nine-script-framework"] = -not (Test-Path -LiteralPath (Join-Path $root "references\analysis-framework.md"))

$checks | ConvertTo-Json -Depth 3
if (@($checks.Values | Where-Object { -not $_ }).Count -gt 0) {
    exit 1
}
