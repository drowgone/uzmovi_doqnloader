#!/bin/bash
# Setup VDL Native Messaging Host

HOST_NAME="com.vdl"
JSON_FILE="../vdl_host/$HOST_NAME.json"

# Check for Chrome/Chromium config directories
CHROME_PATH="$HOME/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_PATH="$HOME/.config/chromium/NativeMessagingHosts"

mkdir -p "$CHROME_PATH"
mkdir -p "$CHROMIUM_PATH"

# Copy the JSON manifest
cp "$JSON_FILE" "$CHROME_PATH/$HOST_NAME.json"
cp "$JSON_FILE" "$CHROMIUM_PATH/$HOST_NAME.json"

echo "[+] Native Messaging Host manifesti nusxalandi."
echo "[!] Chrome kengaytmani yuklaganingizdan keyin ID raqamini ushbu fayllarga yozishimiz kerak bo'ladi."
