#!/bin/bash
# local_video.sh — transcribe a local video / audio file to SRT + plain text.
#
# Pipeline:
#   1. ffmpeg → 16 kHz mono WAV (Whisper-friendly)
#   2. faster-whisper → SRT
#   3. srt_to_transcript.py → clean .txt
#
# Lazy install: ffmpeg + faster-whisper get checked here, **only at the moment
# the user actually runs this script**. Not at master-skill setup time. The
# script prompts before installing; pass `AUTO_YES=1` to skip prompts.
#
# Usage:
#   ./local_video.sh <input.mp4|input.mov|...|input.wav> [output_dir]
#
# Env vars:
#   AUTO_YES=1                skip y/N prompts, install missing deps
#   WHISPER_MODEL=<name>      tiny / base / small / medium / large-v3 (default: medium)
#   WHISPER_LANG=<code>       zh / en / ja / ... (default: auto-detect)
#   KEEP_AUDIO=1              don't delete intermediate WAV after transcription
#
# Exit codes:
#   0 OK
#   1 usage error
#   2 input file missing
#   3 user declined to install ffmpeg
#   4 user declined to install faster-whisper
#   5 ffmpeg failed (extraction)
#   6 whisper failed (transcription)
#   7 srt_to_transcript failed

set -e

INPUT="$1"
OUTPUT_DIR="${2:-.}"
AUTO_YES="${AUTO_YES:-0}"
MODEL="${WHISPER_MODEL:-medium}"
LANG="${WHISPER_LANG:-}"
KEEP_AUDIO="${KEEP_AUDIO:-0}"

if [ -z "$INPUT" ]; then
    cat <<EOF >&2
Usage: $0 <input.mp4|input.mov|...> [output_dir]

Supported inputs:
  Video: .mp4 .mov .mkv .webm .avi .flv .ts ...
  Audio: .wav .mp3 .m4a .flac .ogg .opus ...

Env vars:
  AUTO_YES=1                skip prompts, auto-install missing deps
  WHISPER_MODEL=medium      tiny / base / small / medium / large-v3
  WHISPER_LANG=zh           force language (default: auto-detect)
  KEEP_AUDIO=1              keep intermediate WAV file

Output:
  <output_dir>/<stem>.srt              raw whisper subtitles
  <output_dir>/<stem>_transcript.txt   cleaned plain text (paragraph-grouped)
EOF
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "ERROR: input file not found: $INPUT" >&2
    exit 2
fi

# ---------- Lazy-install helpers ----------

confirm() {
    # $1 = prompt text. Returns 0 if user says yes.
    if [ "$AUTO_YES" = "1" ]; then
        echo "$1 [auto-yes]" >&2
        return 0
    fi
    if [ ! -t 0 ]; then
        # No tty — refuse to silently install
        echo "ERROR: stdin not a tty, can't prompt. Set AUTO_YES=1 to skip." >&2
        return 1
    fi
    local ans
    read -p "$1 [y/N] " ans </dev/tty
    [[ "$ans" =~ ^[Yy] ]]
}

ensure_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1; then
        return 0
    fi
    echo "" >&2
    echo "[lazy-install] ffmpeg is required (audio extraction)." >&2
    echo "             will install via:  brew install ffmpeg" >&2
    if ! confirm "Proceed with brew install ffmpeg?"; then
        echo "ABORT: ffmpeg required. Run manually:  brew install ffmpeg" >&2
        exit 3
    fi
    if ! command -v brew >/dev/null 2>&1; then
        echo "ERROR: Homebrew not installed. Install brew first:" >&2
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" >&2
        exit 3
    fi
    # Redirect installer chatter to stderr so stdout stays the transcript path.
    brew install ffmpeg >&2
}

ensure_whisper() {
    if python3 -c "import faster_whisper" 2>/dev/null; then
        return 0
    fi
    echo "" >&2
    echo "[lazy-install] faster-whisper Python package is required (transcription)." >&2
    echo "             will install via:  python3 -m pip install faster-whisper" >&2
    if ! confirm "Proceed with python3 -m pip install faster-whisper?"; then
        echo "ABORT: faster-whisper required. Run manually:  python3 -m pip install faster-whisper" >&2
        exit 4
    fi
    # Use python3 -m pip (not bare pip3) to guarantee the package lands in the
    # interpreter that whisper_transcribe.py will actually run with. Stdout
    # → stderr so we don't pollute the transcript-path stdout contract.
    python3 -m pip install faster-whisper >&2
}

# ---------- Pipeline ----------

ensure_ffmpeg
ensure_whisper

mkdir -p "$OUTPUT_DIR"
STEM=$(basename "$INPUT" | sed 's/\.[^.]*$//')
WAV_PATH="$OUTPUT_DIR/$STEM.master-skill.wav"
SRT_PATH="$OUTPUT_DIR/$STEM.srt"
TRANSCRIPT_PATH="$OUTPUT_DIR/${STEM}_transcript.txt"

echo "" >&2
echo ">>> Step 1/3: ffmpeg → 16 kHz mono WAV" >&2
if ! ffmpeg -y -loglevel error -i "$INPUT" -ac 1 -ar 16000 -f wav "$WAV_PATH" 2>&1; then
    echo "ERROR: ffmpeg failed to extract audio from $INPUT" >&2
    exit 5
fi
echo "    → $WAV_PATH" >&2

echo "" >&2
echo ">>> Step 2/3: faster-whisper transcribe (model=$MODEL${LANG:+, lang=$LANG})" >&2
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHISPER_ARGS=(--input "$WAV_PATH" --output "$SRT_PATH" --model "$MODEL")
if [ -n "$LANG" ]; then
    WHISPER_ARGS+=(--language "$LANG")
fi
if ! python3 "$SCRIPT_DIR/whisper_transcribe.py" "${WHISPER_ARGS[@]}"; then
    echo "ERROR: whisper transcription failed" >&2
    exit 6
fi
echo "    → $SRT_PATH" >&2

echo "" >&2
echo ">>> Step 3/3: srt_to_transcript → cleaned text" >&2
if ! python3 "$SCRIPT_DIR/srt_to_transcript.py" "$SRT_PATH" "$TRANSCRIPT_PATH"; then
    echo "ERROR: srt_to_transcript failed" >&2
    exit 7
fi
echo "    → $TRANSCRIPT_PATH" >&2

# Cleanup intermediate WAV unless user asked to keep
if [ "$KEEP_AUDIO" != "1" ]; then
    rm -f "$WAV_PATH"
fi

echo "" >&2
echo "OK:" >&2
echo "  srt:        $SRT_PATH" >&2
echo "  transcript: $TRANSCRIPT_PATH" >&2

# Print transcript path on stdout so callers can chain
echo "$TRANSCRIPT_PATH"
