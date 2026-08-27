#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "未找到 Homebrew。请先从 https://brew.sh 安装 Homebrew，再重新运行本脚本。" >&2
  exit 2
fi

brew install ffmpeg python

# Install one consistent scripted backend in an isolated environment on every supported Mac.
env_root="$HOME/Library/Caches/tianguo-video/python-env"
env_python="$env_root/bin/python"
if [[ ! -x "$env_python" ]]; then
  mkdir -p "$(dirname "$env_root")"
  python3 -m venv "$env_root"
fi
"$env_python" -m pip install --upgrade pip faster-whisper gallery-dl

model_root="$HOME/Library/Caches/tianguo-video/models"
backend_marker="$HOME/Library/Caches/tianguo-video/backend-verified.json"
"$env_python" "$(cd "$(dirname "$0")" && pwd)/verify-transcription-backend.py" \
  --download-root "$model_root" --marker "$backend_marker"

echo "初始化和转写后端自测完成。请运行 check-environment.sh 验证环境。"
