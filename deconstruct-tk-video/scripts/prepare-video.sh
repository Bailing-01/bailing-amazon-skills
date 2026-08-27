#!/usr/bin/env bash
set -euo pipefail

source_value="${1:?用法: prepare-video.sh <本地视频或公开TikTok链接> [工作目录] [模型]}"
work_dir="${2:-$PWD}"
model="${3:-small}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
videos="$work_dir/videos"
cache="$work_dir/.video-cache"
mkdir -p "$videos" "$cache"

if [[ "$source_value" =~ ^https?:// ]]; then
  if [[ ! "$source_value" =~ ^https?://([^/]+\.)?tiktok\.com/ ]]; then
    echo "只支持公开 TikTok 链接；其他来源请上传本地视频文件。" >&2
    exit 2
  fi
  env_python="$HOME/Library/Caches/tianguo-video/python-env/bin/python"
  [[ -x "$env_python" ]] || { echo "缺少专用 Python 环境，请先运行 setup-macos.sh。" >&2; exit 3; }
  "$env_python" -c "import gallery_dl" >/dev/null 2>&1 || { echo "缺少 gallery-dl，请先运行 setup-macos.sh。" >&2; exit 3; }
  [[ "$source_value" =~ /video/([0-9]+) ]] || { echo "无法从链接解析 TikTok 视频 ID。" >&2; exit 4; }
  video_id="${BASH_REMATCH[1]}"
  "$env_python" -m gallery_dl --directory "$videos" --filename "{id}.{extension}" -- "$source_value"
  video="$(find "$videos" -maxdepth 1 -type f \( -name "$video_id.mp4" -o -name "$video_id.mov" -o -name "$video_id.webm" -o -name "$video_id.m4v" \) -print -quit)"
  [[ -f "$video" ]] || { echo "gallery-dl 未返回可读取的视频。遇到登录、地区、验证码或风控时请上传本地文件。" >&2; exit 4; }
  source_type="tiktok"
else
  [[ -f "$source_value" ]] || { echo "本地视频不存在：$source_value" >&2; exit 2; }
  video="$source_value"
  source_type="local"
fi

analysis="$("$script_dir/analyze-video.sh" "$video" "$cache" "$model")"
printf '{"pipeline_id":"tk-content-pipeline/v1","artifact_type":"prepared_media","source_type":"%s","source":"%s","analysis":%s}\n' "$source_type" "$source_value" "$analysis"
