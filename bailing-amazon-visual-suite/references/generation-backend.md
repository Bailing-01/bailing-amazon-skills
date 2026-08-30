# Generation Backend

Use this file before final image generation. The goal is to choose a working route without hard-coding credentials or forcing one local environment.

## Route Priority

1. Use an existing Bailing deployment helper in the active workspace when present.
2. Use a fixed-interface generation script from a related Bailing skill when it is present and configured.
3. Use built-in `image_gen` as the final fallback.

## Discovery

Search locally before choosing the backend:

```powershell
Get-ChildItem -Recurse -File -Include *generate*.py,*generate*.js,*image*.py,*image*.js,*fallback-generation.md
```

Prioritize files whose names or parent folders indicate:

- `bailing`
- `deployment`
- `generate_image`
- `generate_batch`
- `fallback-generation`
- `image helper`

If a related skill provides `references/fallback-generation.md`, read it before using that route.

## Reference Image Argument Rule

When using a PowerShell deployment helper that accepts product images, reference images, competitor images, or style references through `-ReferenceImage`, always pass exactly one string argument:

```powershell
$referenceImages = @(
  "C:\path\to\product.jpg",
  "C:\path\to\style-reference.png"
)
$referenceImageArg = ($referenceImages -join ';')

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper `
  -PromptFile $promptFile `
  -ReferenceImage $referenceImageArg `
  -OutputDir $outputDir `
  -Size $size `
  -FileName $fileName
```

For a single reference image, still use the same pattern or pass the single path as one string. For text-only generation, omit `-ReferenceImage`.

Never pass a PowerShell array, comma-separated argument list, or splatted multi-value path list directly to `-ReferenceImage`. On some Windows/PowerShell versions, later paths can be mis-bound to following parameters such as `TimeoutSec`.

## Multi-Image Helper Calls

For the 21-image Amazon suite, when using a PowerShell deployment helper and more than one image is ready to generate, prefer staggered concurrency:

- Submit the first image as a background job.
- Wait 3 seconds.
- Submit the second image without waiting for the first image to finish or land on disk.
- Continue until every ready image is submitted.
- After submission, wait for all jobs, collect helper output, and verify saved files.
- If `Start-Job`, `Wait-Job`, or `Receive-Job` fails on the customer's computer, stop and clean up background jobs, then retry missing outputs one by one with the same helper arguments.

Each task must have its own prompt file, output folder, final filename, target size, and optional semicolon-joined `ReferenceImageArg`.

```powershell
$serialFallback = $false
$jobs = @()
try {
  foreach ($task in $imageTasks) {
    $jobs += Start-Job -ScriptBlock {
      param($helper, $promptFile, $referenceImageArg, $outputDir, $size, $fileName)
      if ($referenceImageArg) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PromptFile $promptFile -ReferenceImage $referenceImageArg -OutputDir $outputDir -Size $size -FileName $fileName
      } else {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PromptFile $promptFile -OutputDir $outputDir -Size $size -FileName $fileName
      }
    } -ArgumentList $helper, $task.PromptFile, $task.ReferenceImageArg, $task.OutputDir, $task.Size, $task.FileName
    Start-Sleep -Seconds 3
  }
  $jobs | Wait-Job | Out-Null
  $results = $jobs | Receive-Job -ErrorAction Stop
} catch {
  $serialFallback = $true
} finally {
  if ($jobs.Count -gt 0) {
    if ($serialFallback) { $jobs | Stop-Job -ErrorAction SilentlyContinue }
    $jobs | Remove-Job -Force -ErrorAction SilentlyContinue
  }
}
if ($serialFallback) {
  $results = @()
  foreach ($task in $imageTasks) {
    $outPath = Join-Path $task.OutputDir $task.FileName
    if (Test-Path -LiteralPath $outPath) { continue }
    if ($task.ReferenceImageArg) {
      $results += & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PromptFile $task.PromptFile -ReferenceImage $task.ReferenceImageArg -OutputDir $task.OutputDir -Size $task.Size -FileName $task.FileName
    } else {
      $results += & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PromptFile $task.PromptFile -OutputDir $task.OutputDir -Size $task.Size -FileName $task.FileName
    }
  }
}
```

For a single image, use the normal synchronous helper call.

## Backend Contract

For each generated asset, preserve:

- one image per call
- requested asset type and final role
- Product Master Description
- product consistency and physics locks
- marketplace language
- output file path

Do not use local stitching, collage assembly, or piece-by-piece compositing as a generation route. Generate each final image as one standalone image through the selected backend.

Do not write credentials into files. Use existing `.env`, environment variables, or the current tool configuration only.

## Fallback Rules

If no fixed route is available, fails, or cannot save/display the result, use built-in `image_gen`.

When falling back, report:

- attempted route
- failure reason at a high level
- final route used
