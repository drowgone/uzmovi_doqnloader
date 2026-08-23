#!/bin/bash
# Setup VDL Native Messaging Host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_NAME="com.chrome_ex.vdl"
JSON_FILE="$SCRIPT_DIR/$HOST_NAME.json"

# Check for Chrome/Chromium config directories
CHROME_PATH="$HOME/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_PATH="$HOME/.config/chromium/NativeMessagingHosts"

mkdir -p "$CHROME_PATH"
mkdir -p "$CHROMIUM_PATH"

# Use python installer to safely generate wrappers and install manifest in user config dirs
if command -v python3 &>/dev/null; then
    python3 -c "import sys; sys.path.append('$SCRIPT_DIR/..'); import uzmovi_dl; uzmovi_dl.install_chrome_bridge()"
else
    # Fallback copy manifest
    if [ -f "$JSON_FILE" ]; then
        cp "$JSON_FILE" "$CHROME_PATH/$HOST_NAME.json"
        cp "$JSON_FILE" "$CHROMIUM_PATH/$HOST_NAME.json"
    fi
fi

echo "[+] Native Messaging Host manifesti va sozlamalari muvaffaqiyatli o'rnatildi."
