param(
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent $PSScriptRoot
$expectedDisplayName = -join @(
    [char]0x6700, [char]0x65B0, '1', '0', '6', [char]0xFF5C,
    'T', 'K', [char]0x65B0, [char]0x811A, [char]0x672C, [char]0x5E93
)
$requiredFiles = @(
    "SKILL.md",
    "agents\openai.yaml",
    "references\analysis-framework.md",
    "references\pipeline-contract.md",
    "references\breakdown-bundle.schema.json",
    "references\script-bundle.schema.json",
    "references\lark-script-config.json",
    "references\lark-script-mapping.json",
    "scripts\validate_bundle.py",
    "scripts\test_validate_bundle.py"
)

$errors = [System.Collections.Generic.List[string]]::new()
foreach ($relative in $requiredFiles) {
    $path = Join-Path $skillRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $errors.Add("Missing required file: $relative")
    }
}

if ($errors.Count -eq 0) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $skillRoot "SKILL.md")
    $openaiText = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $skillRoot "agents\openai.yaml")

    if ($skillText -notmatch "(?m)^name:\s*generate-tk-scripts\s*$") {
        $errors.Add("SKILL.md name is not generate-tk-scripts")
    }
    if ($skillText -match "\[TODO") {
        $errors.Add("SKILL.md still contains TODO placeholders")
    }
    $displayMatch = [regex]::Match($openaiText, "(?m)^\s*display_name:\s*`"([^`"]+)`"\s*$")
    if (-not $displayMatch.Success -or $displayMatch.Groups[1].Value -ne $expectedDisplayName) {
        $errors.Add("agents/openai.yaml display_name mismatch or unquoted")
    }
    $shortMatch = [regex]::Match($openaiText, "(?m)^\s*short_description:\s*`"([^`"]+)`"\s*$")
    if (-not $shortMatch.Success) {
        $errors.Add("agents/openai.yaml short_description missing or unquoted")
    } elseif ($shortMatch.Groups[1].Value.Length -lt 25 -or $shortMatch.Groups[1].Value.Length -gt 64) {
        $errors.Add("short_description length must be 25-64 characters")
    }
    $defaultMatch = [regex]::Match($openaiText, "(?m)^\s*default_prompt:\s*`"([^`"]+)`"\s*$")
    if (-not $defaultMatch.Success) {
        $errors.Add("agents/openai.yaml default_prompt missing or unquoted")
    } elseif (-not $defaultMatch.Groups[1].Value.Contains('$generate-tk-scripts')) {
        $errors.Add("default_prompt must contain `$generate-tk-scripts")
    }

    foreach ($relative in @(
        "references\breakdown-bundle.schema.json",
        "references\script-bundle.schema.json",
        "references\lark-script-config.json",
        "references\lark-script-mapping.json"
    )) {
        try {
            Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $skillRoot $relative) | ConvertFrom-Json | Out-Null
        } catch {
            $errors.Add("Invalid JSON in $relative`: $($_.Exception.Message)")
        }
    }
}

if (-not $PythonPath) {
    $pythonCandidates = @(
        "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
        "C:\Users\Administrator\AppData\Roaming\uv\python\cpython-3.11.15-windows-x86_64-none\python.exe",
        "C:\Users\Administrator\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"
    )
    $PythonPath = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $PythonPath) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCommand) {
            $PythonPath = $pythonCommand.Source
        }
    }
}

if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    $errors.Add("Python runtime not found")
} else {
    $savedErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $testOutput = & $PythonPath -X utf8 -m unittest discover -s $PSScriptRoot -p "test_*.py" -v 2>&1
    $testExitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedErrorPreference
    if ($testExitCode -ne 0) {
        $errors.Add("Validator unit tests failed:`n$($testOutput -join [Environment]::NewLine)")
    }

    $quickValidate = "C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $ErrorActionPreference = "Continue"
    if ($uvCommand) {
        $quickOutput = & $uvCommand.Source run --with pyyaml --python $PythonPath python -X utf8 $quickValidate $skillRoot 2>&1
    } else {
        $quickOutput = & $PythonPath -X utf8 $quickValidate $skillRoot 2>&1
    }
    $quickExitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedErrorPreference
    if ($quickExitCode -ne 0) {
        $errors.Add("skill-creator quick_validate failed:`n$($quickOutput -join [Environment]::NewLine)")
    }
}

$result = [ordered]@{
    valid = ($errors.Count -eq 0)
    skill_root = $skillRoot
    display_name = $expectedDisplayName
    errors = @($errors)
}
$result | ConvertTo-Json -Depth 5
if ($errors.Count -gt 0) {
    exit 1
}
