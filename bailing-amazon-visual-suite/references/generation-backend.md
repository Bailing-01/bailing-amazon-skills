# Generation Backend

Use this file before final image generation. The goal is to use `gsk img` + gpt-image-2 first, then a working fallback without hard-coding credentials or forcing one local environment.

## Route Priority

1. **Preferred: `gsk img` + gpt-image-2.** Call once per final image with `--args-file` JSON (`model`, `aspect_ratio`, `image_urls`, and the full `query` from the Prompt Contract in `SKILL.md`). Do not send abstract style-only prompts.
2. If the preferred route is unavailable or fails, explain the reason and get the user's approval, then use an existing Bailing deployment helper in the active workspace when present.
3. Or, after the same approval, use a fixed-interface generation script from a related Bailing skill when it is present and configured.
4. Built-in `image_gen` is the last fallback, and also requires the user approval in step 2. Do not switch to it just to save steps.

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

If the preferred `gsk img` + gpt-image-2 route is unavailable, fails, or cannot save/display the result, do not silently switch backends. Report the attempted route and a high-level failure reason, get the user's approval, then use a Bailing deployment helper, a fixed-interface script, or built-in `image_gen`.

When falling back, report:

- attempted route
- failure reason at a high level
- user approval to switch
- final route used
