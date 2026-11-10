#!/bin/sh
# usage: webframe.sh <page-402x791@2x.png> <out.png> — the page screenshot inside an iPhone 17 Pro Safari frame (status bar + bottom bar), 402×874 @2x
D=$(cd "$(dirname "$0")" && pwd); PAGE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); sed "s#PAGE#file://$PAGE#" "$D/webframe.html" > "${TMPDIR:-/tmp}/webframe-run.html"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=old --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=402,874 --timeout=30000 --screenshot="$2" "file://${TMPDIR:-/tmp}/webframe-run.html" >/dev/null 2>&1
