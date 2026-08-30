# Generation Tools

Read this file for direct image generation. Unless the user explicitly asks for prompts only, do not stop at a prompt pack.

## Priority

1. First attempt the deployment helper written by the installer for the actual image generation call.
2. Resolve the helper from `BAILING_IMAGE_GENERATOR` first, then `%LOCALAPPDATA%\ApiCodexOneClick\tools\generate-image.ps1`.
3. The helper owns the endpoint, model, key selection, request shape, output saving, and Markdown preview behavior. Do not ask the user for an API key.
4. The helper routes reference-image requests to `https://__BAILING_DOMAIN_KEEP__/v1/images/edits` and text-only requests to `https://__BAILING_DOMAIN_KEEP__/v1/images/generations`.
5. Use the fixed model configured by the helper: `gpt-image-2`.
6. If the helper is missing, unavailable, fails, or cannot save/display the generated image, use built-in Codex `image_gen` as the final fallback.
7. Do not call built-in `image_gen` before resolving and attempting the helper.
8. Default scene-image size is square `1:1`; use helper size `1024x1024` unless the user specifies another size.
9. Final images must be generated directly by the helper or built-in `image_gen`. Do not use local scripts to stitch, composite, replace backgrounds, overlay final text, or create placeholder images.

## Helper Command

Resolve the helper at runtime:

```powershell
$helper = $env:BAILING_IMAGE_GENERATOR
if (-not $helper) { $helper = Join-Path $env:LOCALAPPDATA 'ApiCodexOneClick\tools\generate-image.ps1' }
```

For text-only generation:

```powershell
$promptFile = "<absolute prompt file path>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper `
  -PromptFile $promptFile `
  -OutputDir "<absolute output directory>" `
  -Size "1024x1024" `
  -FileName "scene-01.png"
```

For product or style reference images, join every reference path with semicolons and pass the joined string to `-ReferenceImage`. Do not pass a PowerShell array or comma-separated list directly.

```powershell
$promptFile = "<absolute prompt file path>"
$referenceImages = @("C:\path\to\product-front.png", "C:\path\to\style-reference.png")
$referenceImageArg = ($referenceImages -join ';')
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper `
  -PromptFile $promptFile `
  -ReferenceImage $referenceImageArg `
  -OutputDir "<absolute output directory>" `
  -Size "1024x1024" `
  -FileName "scene-01.png"
```

## Multi-Image Calls

For more than one final image, use staggered concurrency:

- Create one prompt file and one output filename per image.
- Submit the first helper call as a background job.
- Wait 3 seconds.
- Submit the next helper call without waiting for the first output file.
- After all jobs are submitted, wait for all jobs, collect helper output, and verify saved files.
- If staggered concurrency fails, times out, or rate limits, retry failed images one by one with the same helper arguments.

## Save And Deliver

- After every successful generation, confirm the local file exists.
- The final response must list the local path for each image and show Markdown previews when supported.
- If helper output returns a URL or base64 data instead of a path, save it to the local output directory before delivery.
- If both helper and built-in `image_gen` fail, explain both failure reasons where available and deliver the prompt pack as a fallback, clearly stating that images were not generated.

## No Automatic Regeneration

- Once generation succeeds and files are saved, proceed to delivery.
- Do not automatically rewrite prompts or regenerate because of text errors, weak design, product drift, imperfect dimensions, or repeated composition.
- If potential issues are noticed, list them only as optional review items. Regenerate only when the user explicitly asks to redo, fix, replace, or regenerate specific images.
