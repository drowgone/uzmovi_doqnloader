#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

# --- CONFIGURATION ---
REQUIRED_PACKAGES = ["rich", "questionary", "yt-dlp"]

def is_windows():
    return os.name == 'nt'

def check_ffmpeg():
    """Tizimda ffmpeg borligini tekshirish"""
    return shutil.which("ffmpeg") is not None

def install_packages():
    """Pip orqali kerakli kutubxonalarni o'rnatish"""
    print("--- 1. Kutubxonalarni tekshirish va o'rnatish ---")
    try:
        # pip orqali o'rnatish
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + REQUIRED_PACKAGES)
        print("[+] Kutubxonalar muvaffaqiyatli tayyorlandi.\n")
        return True
    except Exception as e:
        print(f"[!] Xatolik: Kutubxonalarni o'rnatib bo'lmadi: {e}")
        return False

def main():
    print("="*60)
    print("🎬 VDL (Universal Video Downloader) - O'rnatish va Sozlash")
    print("="*60)
    print(f"Joriy OS: {'Windows' if is_windows() else 'Linux/Unix'}")
    
    # 1. Install pip packages
    if not install_packages():
        sys.exit(1)

    # 2. Check FFmpeg
    print("--- 2. Tizim vositalarini tekshirish ---")
    if check_ffmpeg():
        print("[+] FFmpeg topildi. Videolar birlashtirishga tayyor.")
    else:
        print("[!] OGOHLANTIRISH: FFmpeg topilmadi!")
        if is_windows():
            print("    -> Iltimos, ffmpeg.org saytidan yuklab oling va PATH'ga qo'shing.")
        else:
            print("    -> Iltimos, o'rnating: sudo apt install ffmpeg")
    print("")

    # 3. Setup Global Command and Chrome Bridge
    print("--- 3. Tizimga integratsiya qilish ---")
    try:
        # Endi kutubxonalar bor, uzmovi_dl ni import qilamiz
        script_dir = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(script_dir)
        
        import uzmovi_dl
        
        # Install global command
        if uzmovi_dl.install_kino():
            print("[+] 'kino' buyrug'i va Chrome integratsiyasi tayyor.")
        else:
            print("[!] Integratsiyada qandaydir muammo bo'ldi, lekin dastur ishlashi kerak.")
    except Exception as e:
        print(f"[!] Xatolik: Integratsiya jarayonida xato: {e}")

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
