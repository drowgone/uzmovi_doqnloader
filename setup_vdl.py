#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

# --- CONFIGURATION ---
REQUIRED_PACKAGES = ["rich", "questionary", "yt-dlp"]

def is_windows():
    return os.name == 'nt'

def is_termux():
    return "com.termux" in os.environ.get("PREFIX", "")

def get_os_name():
    if is_windows(): return "Windows"
    if is_termux(): return "Termux (Android)"
    return "Linux/Unix"

def check_ffmpeg():
    """Tizimda ffmpeg borligini tekshirish"""
    return shutil.which("ffmpeg") is not None

def install_packages():
    """Pip orqali kerakli kutubxonalarni o'rnatish"""
    print("--- 1. Kutubxonalarni tekshirish va o'rnatish ---")
    
    # Pip mavjudligini tekshirish
    try:
        import pip
    except ImportError:
        print("[!] XATOLIK: Tizimda 'pip' moduli topilmadi.")
        if is_windows():
            print("    -> Windowsda: Pythonni qayta o'rnating va 'Add to PATH' belgisini qo'ying.")
        elif is_termux():
            print("    -> Termuxda: pkg install python")
        else:
            print("    -> Linuxda: sudo apt install python3-pip")
        return False

    try:
        # pip orqali o'rnatish
        print(f"[*] {', '.join(REQUIRED_PACKAGES)} o'rnatilmoqda...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U"] + REQUIRED_PACKAGES)
        print("[+] Kutubxonalar muvaffaqiyatli tayyorlandi.\n")
        return True
    except Exception as e:
        print(f"[!] Xatolik: Kutubxonalarni o'rnatib bo'lmadi: {e}")
        return False

def main():
    print("="*60)
    print("🎬 VDL (Universal Video Downloader) - Universal Setup")
    print("="*60)
    print(f"Tizim: {get_os_name()}")
    
    # 1. Install pip packages
    if not install_packages():
        sys.exit(1)

    # 2. Check FFmpeg
    print("--- 2. Tizim vositalarini tekshirish (FFmpeg) ---")
    if check_ffmpeg():
        print("[+] FFmpeg topildi. Videolar birlashtirishga tayyor.")
    else:
        print("[!] OGOHLANTIRISH: FFmpeg topilmadi!")
        if is_windows():
            print("    -> Yuklab oling: https://ffmpeg.org/download.html")
        elif is_termux():
            print("    -> O'rnating: pkg install ffmpeg")
        else:
            print("    -> O'rnating: sudo apt install ffmpeg")
    print("")

    # 3. Setup Global Command and Chrome Bridge
    print("--- 3. Tizimga integratsiya ---")
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(script_dir)
        import uzmovi_dl
        
        if uzmovi_dl.install_kino():
            print(f"[+] Integratsiya yakunlandi ({get_os_name()}).")
        else:
            print("[!] Integratsiya jarayonida ogohlantirish (Manual setup talab qilinishi mumkin).")
    except Exception as e:
        print(f"[!] Xatolik integratsiyada: {e}")

    print("\n" + "="*60)
    print("🎉 O'rnatish yakunlandi!")
    print("Endi terminalda 'kino' deb yozib dasturni ishga tushirishingiz mumkin.")
    print("="*60 + "\n")

    # 4. Run the app
    try:
        import uzmovi_dl
        uzmovi_dl.run_app()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] Dasturni boshlashda xato: {e}")

if __name__ == "__main__":
    main()
