#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Xatolik: URL manzili kiritilmadi.")
        input("\nChiqish uchun ENTER bosing...")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL schema and format
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            print(f"Xatolik: Xavfsiz bo'lmagan yoki noto'g'ri URL manzil: {url}")
            input("\nChiqish uchun ENTER bosing...")
            sys.exit(1)
        url = url.strip()
    except Exception as e:
        print(f"Xatolik: URL parsing xatosi: {e}")
        input("\nChiqish uchun ENTER bosing...")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    downloader_path = os.path.join(script_dir, "uzmovi_dl.py")

    if not os.path.exists(downloader_path):
        print(f"Xatolik: Downloader topilmadi: {downloader_path}")
        input("\nChiqish uchun ENTER bosing...")
        sys.exit(1)

    print(f"Yuklash boshlanmoqda: {url}")
    
    # Run the downloader
    # We use the same python interpreter
    cmd = [sys.executable, downloader_path, "--url", url]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nYuklash bekor qilindi.")
    except Exception as e:
        print(f"\n\nXatolik yuz berdi: {e}")

    print("\n" + "="*50)
    print("Ish tugadi. Chiqish uchun ENTER bosing...")
    input()

if __name__ == "__main__":
    main()
