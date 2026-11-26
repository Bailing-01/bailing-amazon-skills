#!/bin/bash
# youtube.sh — download subtitles from YouTube / Bilibili / other yt-dlp-supported platforms.
#
# Usage:
#   ./youtube.sh <URL> [output_dir]
#
# Tries (in order):
#   1) Manual zh-Hans / zh-CN / zh / zh-TW
#   2) Manual en / en-US / en-GB
#   3) Manual ja / ko (locale-dependent)
#   4) Auto-generated zh-Hans / en
#
# Output: one .srt file (or .vtt fallback) per request, named `{title}.{lang}.srt`.
# Pipe to `srt_to_transcript.py` for clean text.
#
# Requires: yt-dlp. Install: brew install yt-dlp.

set -e

URL="$1"
OUTPUT_DIR="${2:-.}"

if [ -z "$URL" ]; then
    echo "Usage: $0 <URL> [output_dir]" >&2
    echo "" >&2
    echo "Supported platforms: YouTube / Bilibili / Vimeo / many more (see yt-dlp docs)" >&2
    exit 1
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
    echo "ERROR: yt-dlp not installed. Install with:" >&2
    echo "  brew install yt-dlp" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"

# Marker for finding new files
touch /tmp/.master-skill-ytdlp-marker

echo ">>> Listing available subtitles..."
yt-dlp --list-subs --no-download "$URL" 2>/dev/null | tail -25 || true
echo ""

attempt() {
    local label="$1"; shift
    echo ">>> Trying: $label"
    if yt-dlp "$@" --sub-format srt --skip-download \
        -o "$OUTPUT_DIR/%(title).80s.%(id)s" "$URL" 2>&1 | tail -5; then
        local found
        found=$(find "$OUTPUT_DIR" -name "*.srt" -newer /tmp/.master-skill-ytdlp-marker 2>/dev/null | head -1)
        if [ -z "$found" ]; then
            found=$(find "$OUTPUT_DIR" -name "*.vtt" -newer /tmp/.master-skill-ytdlp-marker 2>/dev/null | head -1)
        fi
        if [ -n "$found" ]; then
            echo "OK: $found"
            exit 0
        fi
    fi
}

# 1) Manual Chinese
attempt "manual Chinese subs" \
    --write-subs --sub-langs "zh-Hans,zh-CN,zh,zh-TW,zh-Hant"

# 2) Manual English
attempt "manual English subs" \
    --write-subs --sub-langs "en,en-US,en-GB"

# 3) Manual Japanese / Korean (cheap try, useful for ja/ko locales)
attempt "manual Japanese subs" \
    --write-subs --sub-langs "ja"
attempt "manual Korean subs" \
    --write-subs --sub-langs "ko"

# 4) Auto-generated (last resort)
attempt "auto-generated zh + en" \
    --write-auto-subs --sub-langs "zh-Hans,zh,en"

echo "FAIL: no subs found for $URL" >&2
echo "" >&2
echo "Suggestion: download the video locally (yt-dlp <URL> -o video.mp4) then" >&2
echo "transcribe with: ./local_video.sh video.mp4   (uses faster-whisper, lazy install)" >&2
echo "Or search for a transcript on the web (e.g. podcastnotes.org for podcasts)." >&2
exit 3
