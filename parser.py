#!/usr/bin/env python3
import os
import re
import sys
import json
import urllib.request
import subprocess

def sanitize_filename(name):
    """Filename yoki folder nomidan xavfli belgilarni olib tashlash"""
    # Windows/Linux tizimlari uchun taqiqlangan belgilar
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    # Directory traversal (..), absolute path va relative path sakrashlarini oldini olish
    cleaned = os.path.basename(cleaned)
    cleaned = cleaned.replace("..", "").replace("/", "").replace("\\", "").strip()
    return cleaned if cleaned else "Video"

def get_uzmovi_info(url, retries=3):
    """Uzmovi urldan ma'lumotlarni tortib olish"""
    for attempt in range(retries):
        try:
            # Modern browser user-agent to bypass basic blocks/Cloudflare filters
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'uz,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://uzmovi.tv/'
            }
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')

            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1).split('-')[0].strip() if title_match else "Kino"
            title_clean = sanitize_filename(title)
            folder_name = title_clean

            # Flexible regex for iframe domains (uzdown.* / and support various TLDs)
            iframe_match = re.search(r'src=["\'](https://uzdown\.[a-zA-Z0-9.-]+/embed/[^"\']+)["\']', html)
            if not iframe_match:
                return url, None, "Iframe topilmadi."

            iframe_url = iframe_match.group(1)

            ep_match = re.search(r'episode=(\d+)', iframe_url)
            if ep_match:
                title_clean = sanitize_filename(f"{title_clean} - {ep_match.group(1)}-qism")

            req2 = urllib.request.Request(iframe_url, headers=headers)
            iframe_html = urllib.request.urlopen(req2, timeout=10).read().decode('utf-8')

            # Robust regex supporting single/double quotes and other variations
            m3u8_match = re.search(r"file:\s*['\"]([^'\"]+)['\"]", iframe_html)
            if not m3u8_match:
                return url, None, "m3u8 manba ssilkasi topilmadi."

            return url, {"title": title_clean, "folder": os.path.join("uzmovi", folder_name), "source_url": m3u8_match.group(1)}, None
        except Exception as e:
            if attempt == retries - 1:
                return url, None, str(e)
            import time
            time.sleep(1)

    return url, None, "Xatolik ro'y berdi"

def get_universal_info(url):
    """yt-dlp yordamida istalgan urldan ma'lumotlarni olish"""
    try:
        cmd = [sys.executable, "-m", "yt_dlp", "-j", "--no-playlist", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return url, None, result.stderr.strip() or "yt-dlp ma'lumot ololmadi"

        info = json.loads(result.stdout)
        title = info.get("title", "Video")
        title_clean = sanitize_filename(title)

        # Folder nomi sifatida sayt nomini ishlatamiz yoki 'Downloads'
        extractor_key = info.get("extractor_key", "General")
        folder_name = sanitize_filename(extractor_key)

        return url, {"title": title_clean, "folder": os.path.join(folder_name, title_clean), "source_url": url}, None
    except Exception as e:
        return url, None, str(e)

def get_video_info(url):
    """Urlni tekshirib tegishli parserga yuborish"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return url, None, "Xavfsiz bo'lmagan yoki noto'g'ri URL!"
    except Exception as e:
        return url, None, f"Noto'g'ri URL: {str(e)}"

    url_str = url.strip()
    if "uzmovi.tv" in url_str:
        return get_uzmovi_info(url_str)
    else:
        return get_universal_info(url_str)

def get_available_qualities(url):
    """yt-dlp yordamida mavjud sifatlarni aniqlash"""
    try:
        cmd = [sys.executable, "-m", "yt_dlp", "-j", "--no-playlist", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return []

        info = json.loads(result.stdout)
        formats = info.get("formats", [])

        heights = set()
        for f in formats:
            h = f.get("height")
            if h and isinstance(h, int):
                heights.add(h)

        return sorted(list(heights), reverse=True)
    except:
        return []
