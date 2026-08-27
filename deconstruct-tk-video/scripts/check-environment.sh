#!/usr/bin/env bash
set -u

command_path() { command -v "$1" 2>/dev/null || true; }

ffmpeg_path="$(command_path ffmpeg)"
ffprobe_path="$(command_path ffprobe)"
env_python="$HOME/Library/Caches/tianguo-video/python-env/bin/python"
backend_marker="$HOME/Library/Caches/tianguo-video/backend-verified.json"
if [[ -x "$env_python" ]]; then
  python_path="$env_python"
else
  python_path="$(command_path python3)"
fi
whisper_path="$(command_path whisper-cli)"
if [[ -z "$whisper_path" ]]; then whisper_path="$(command_path whisper-cpp)"; fi

faster_whisper=false
gallery_dl=false
backend_verified=false
if [[ -n "$python_path" ]] && "$python_path" -c "import faster_whisper" >/dev/null 2>&1; then
  faster_whisper=true
fi
if [[ -n "$python_path" ]] && "$python_path" -c "import gallery_dl" >/dev/null 2>&1; then
  gallery_dl=true
fi
if [[ "$faster_whisper" == true && -s "$backend_marker" ]]; then
  if "$python_path" - "$backend_marker" <<'PY' >/dev/null 2>&1
import json, sys
raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("verified") is True else 1)
PY
  then
    backend_verified=true
  fi
fi

arch="$(uname -m)"
local_ready=false
link_ready=false
if [[ -n "$ffmpeg_path" && -n "$ffprobe_path" && -n "$python_path" && "$faster_whisper" == true && "$backend_verified" == true ]]; then
  local_ready=true
  if [[ "$gallery_dl" == true ]]; then link_ready=true; fi
fi

cat <<EOF
{"platform":"macos","architecture":"$arch","ffmpeg":"$ffmpeg_path","ffprobe":"$ffprobe_path","gallery_dl":$gallery_dl,"python":"$python_path","whisper_cli":"$whisper_path","faster_whisper":$faster_whisper,"transcription_backend_verified":$backend_verified,"metal_candidate":$([[ "$arch" == "arm64" ]] && echo true || echo false),"local_video_ready":$local_ready,"tiktok_link_ready":$link_ready,"ready":$local_ready}
EOF

[[ "$local_ready" == true ]]
