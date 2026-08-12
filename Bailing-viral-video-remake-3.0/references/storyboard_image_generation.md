# Storyboard Image Generation

Use this file when a visual director storyboard sheet is required.

## Priority

1. Use `scripts/generate_storyboard_image.py` for normal storyboard image generation.
2. The script first tries the deployment helper written by the installer:
   `%LOCALAPPDATA%\ApiCodexOneClick\tools\generate-image.ps1`
3. The helper routes reference-image requests to `https://xinghe.xin/v1/images/edits` and text-only requests to `https://xinghe.xin/v1/images/generations`.
4. If the helper is missing or fails, the script falls back to direct OpenAI-compatible HTTP calls with model `gpt-image-2`.
5. Use built-in Codex `image_gen` only as the final fallback when the helper/script/API path is unavailable, fails, or cannot save a local storyboard sheet.

## Defaults

- Model: `gpt-image-2`
- Size: `auto`, choosing `2048x1536` for landscape/grid-heavy sheets or `1536x2048` for portrait/tall sheets
- Output filename: `storyboard_sheet.png`
- Output type: one single director storyboard sheet, not separate panels
- Reference images: product images, reference contact sheets, or style boards may be passed through `--reference-image`

## Command

```powershell
python "<skill>/scripts/generate_storyboard_image.py" `
  --storyboard-json "C:/path/storyboard.json" `
  --reference-image "C:/path/product.png" `
  --size "auto" `
  --output-dir "C:/path/storyboard-image"
```

Use a prompt file when the storyboard prompt was already created:

```powershell
python "<skill>/scripts/generate_storyboard_image.py" `
  --prompt-file "C:/path/storyboard_sheet_prompt.txt" `
  --reference-image "C:/path/product.png" `
  --size "2048x1536" `
  --output-dir "C:/path/storyboard-image"
```

For prompt-file mode, `auto` falls back to `2048x1536` because panel count is unavailable. Use `1536x2048` manually when the storyboard sheet should be portrait/tall.

## Environment Fallback

Direct HTTP fallback reads these variables:

- API key: `IMG_API_KEY`, `OPENAI_API_KEY`, or `API_KEY`
- Base URL: `OPENAI_BASE_URL`, `OPENAI_API_BASE`, `IMG_BASE_URL`, or `BASE_URL`
- Model: `OPENAI_IMAGE_MODEL`, `IMG_MODEL`, `OPENAI_MODEL`, or `IMAGE_MODEL`
- Generations URL: `OPENAI_IMAGE_GENERATIONS_URL` or `IMG_GENERATIONS_URL`
- Edits URL: `OPENAI_IMAGE_EDITS_URL` or `IMG_EDITS_URL`

If no base URL is configured, the script defaults to:

- `https://xinghe.xin/v1/images/generations`
- `https://xinghe.xin/v1/images/edits`

## Save Rule

After generation succeeds, the output image path must exist locally. The script writes:

- `storyboard_sheet.png`
- `storyboard-image-manifest.json`
- `storyboard-image-result.json`
- `storyboard_sheet_prompt.txt`

If generation fails, keep the prompt file and result JSON so the user can inspect or retry.

## Face Marker Rule

If the storyboard has a visible person face, the prompt should use the red 5x6 face-marker rule. The final Seedance prompt must state that the red face grid is only a storyboard marker and must not appear in the final video.
