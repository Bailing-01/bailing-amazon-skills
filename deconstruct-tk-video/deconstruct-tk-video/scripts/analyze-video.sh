#!/usr/bin/env bash
set -euo pipefail

video="${1:?用法: analyze-video.sh <video> [work-dir] [model]}"
work_dir="${2:-$PWD/.video-cache}"
model="${3:-small}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
env_python="$HOME/Library/Caches/tianguo-video/python-env/bin/python"
if [[ -x "$env_python" ]]; then
  python_cmd="$env_python"
else
  python_cmd="$(command -v python3 || true)"
fi

video_abs="$(cd "$(dirname "$video")" && pwd)/$(basename "$video")"
if command -v shasum >/dev/null 2>&1; then
  hash="$(shasum -a 256 "$video_abs" | awk '{print $1}')"
else
  hash="$(openssl dgst -sha256 "$video_abs" | awk '{print $NF}')"
fi
cache="$work_dir/$hash"
frames="$cache/frames"
frame_index="$cache/frames.json"
mkdir -p "$frames"

[[ -s "$cache/metadata.json" ]] || ffprobe -v quiet -print_format json -show_format -show_streams "$video_abs" > "$cache/metadata.json"
[[ -s "$cache/audio.wav" ]] || ffmpeg -y -hide_banner -loglevel error -i "$video_abs" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$cache/audio.wav"

transcript_valid=false
if [[ -s "$cache/transcript.json" ]] && [[ -n "$python_cmd" ]]; then
  if "$python_cmd" - "$cache/transcript.json" "$model" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if data.get("model") == sys.argv[2] and isinstance(data.get("segments"), list) else 1)
PY
  then
    transcript_valid=true
  fi
fi

if [[ "$transcript_valid" != true ]]; then
  if [[ -n "$python_cmd" ]] && "$python_cmd" -c "import faster_whisper" >/dev/null 2>&1; then
    "$python_cmd" "$script_dir/transcribe_faster_whisper.py" "$cache/audio.wav" "$cache/transcript.json" \
      --model "$model" --download-root "$HOME/Library/Caches/tianguo-video/models"
  else
    echo "未找到可脚本化的 faster-whisper 后端；停止，未进入整片密集抽帧兜底。" >&2
    exit 3
  fi
fi

frame_index_valid=false
if [[ -s "$frame_index" ]] && "$python_cmd" - "$frame_index" <<'PY' >/dev/null 2>&1
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if data.get("strategy") in {"semantic-scene-v1", "semantic-scene-v2"} and data.get("frame_count", 0) > 0 else 1)
PY
then
  frame_index_valid=true
fi
if [[ "$frame_index_valid" != true ]]; then
  "$python_cmd" "$script_dir/extract-semantic-frames.py" "$video_abs" "$frames" \
    --transcript "$cache/transcript.json" --ffmpeg "$(command -v ffmpeg)" \
    --ffprobe "$(command -v ffprobe)" --max-frames 30 >/dev/null
fi
frame_count="$("$python_cmd" - "$frame_index" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["frame_count"])
PY
)"
duration="$("$python_cmd" - "$frame_index" <<'PY'
import json, math, sys
print(math.ceil(json.load(open(sys.argv[1], encoding="utf-8"))["duration_seconds"]))
PY
)"
updated_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
cat > "$cache/manifest.json" <<EOF
{"schema_version":2,"video_sha256":"$hash","model":"$model","duration_seconds":${duration%.*},"frame_strategy":"semantic-scene-v2","frame_count":$frame_count,"updated_at":"$updated_at"}
EOF

printf '{"video":"%s","cache":"%s","transcript":"%s","frames":"%s","frames_index":"%s","manifest":"%s","frame_strategy":"semantic-scene-v2","frame_count":%s}\n' \
  "$video_abs" "$cache" "$cache/transcript.json" "$frames" "$frame_index" "$cache/manifest.json" "$frame_count"
