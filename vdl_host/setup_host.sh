#!/bin/bash
# Setup VDL Native Messaging Host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_NAME="com.chrome_ex.vdl"
JSON_FILE="$SCRIPT_DIR/$HOST_NAME.json"

# Check for Chrome/Chromium/Brave/Edge config directories
CHROME_PATH="$HOME/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_PATH="$HOME/.config/chromium/NativeMessagingHosts"
BRAVE_PATH="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
EDGE_PATH="$HOME/.config/microsoft-edge/NativeMessagingHosts"

mkdir -p "$CHROME_PATH"
mkdir -p "$CHROMIUM_PATH"
mkdir -p "$BRAVE_PATH"
mkdir -p "$EDGE_PATH"

# Copy the JSON manifest if template exists
if [ -f "$JSON_FILE" ]; then
    cp "$JSON_FILE" "$CHROME_PATH/$HOST_NAME.json" 2>/dev/null || true
    cp "$JSON_FILE" "$CHROMIUM_PATH/$HOST_NAME.json" 2>/dev/null || true
    cp "$JSON_FILE" "$BRAVE_PATH/$HOST_NAME.json" 2>/dev/null || true
    cp "$JSON_FILE" "$EDGE_PATH/$HOST_NAME.json" 2>/dev/null || true
    echo "[+] Native Messaging Host manifesti nusxalandi."
else
    echo "[!] Manifest shabloni topilmadi: $JSON_FILE"
fi

echo "[!] Chrome kengaytmani yuklaganingizdan keyin ID raqamini ushbu fayllarga yozishimiz kerak bo'ladi."
