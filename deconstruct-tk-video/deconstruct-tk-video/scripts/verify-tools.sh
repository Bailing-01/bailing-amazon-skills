#!/bin/sh
set -eu

python="$HOME/Library/Caches/tianguo-video/python-env/bin/python"
if [ ! -x "$python" ]; then
  echo "缺少专用 Python 环境：$python" >&2
  exit 1
fi

version=$("$python" -c 'import gallery_dl; print(gallery_dl.__version__)')
echo "gallery-dl macOS：$version"
echo "Python：$python"
