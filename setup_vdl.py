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

def check_termux_storage(path):
    """Termuxda shared storage (SDCard) cheklovini tekshirish"""
    if is_termux():
        # Termuxda /storage/ yoki /sdcard/ bilan boshlangan yo'llarda venv ishlamaydi
        abs_path = os.path.abspath(path)
        if abs_path.startswith("/storage/") or abs_path.startswith("/sdcard"):
            script_dir = os.path.dirname(abs_path)
            folder_name = os.path.basename(script_dir)
            print("\n" + "!" * 60)
            print("⚠️  DIQQAT: Termuxda Shared Storage Cheklovi!")
            print("-" * 60)
            print("Android tizimi '/storage/emulated/0' (shared storage) ichida")
            print("virtual muhit (symlink) yaratishga ruxsat bermaydi.")
            print("\nYechim: Loyihani Termuxning asosiy papkasiga ko'chiring:")
            print(f"\n   cp -r {script_dir} ~/")
            print(f"   cd ~/{folder_name}")
            print("   python setup_vdl.py")
            print("-" * 60 + "\n")
            return False
    return True

def install_packages():
    """Pip orqali kerakli kutubxonalarni o'rnatish (Virtual Environment ichida)"""
    print("--- 1. Kutubxonalarni tekshirish va o'rnatish ---")
    
    script_dir = os.path.dirname(os.path.realpath(__file__))
    venv_dir = os.path.join(script_dir, ".venv")
    
    # 1.0 Permission Check
    try:
        test_file = os.path.join(script_dir, ".permission_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        print(f"\n[!] XATOLIK: Papkaga yozish uchun ruxsat yo'q: {script_dir}")
        print("    -> Iltimos, loyihani yozishga ruxsati bor papkaga ko'chiring (masalan: Desktop yoki Documents).")
        return False
    
    # 1.1 Venv yaratish
    if not os.path.exists(venv_dir):
        if not check_termux_storage(venv_dir):
            return False
            
        print("[*] Virtual muhit (.venv) yaratilmoqda...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
            print("[+] .venv yaratildi.")
        except Exception as e:
            print(f"[!] Xatolik: Virtual muhitni yaratib bo'lmadi: {e}")
            if not is_windows() and not is_termux():
                print("    -> Debian/Ubuntu: sudo apt install python3-venv")
                print("    -> Arch Linux: sudo pacman -S python")
                print("    -> Fedora: sudo dnf install python3-virtualenv")
                print("    -> openSUSE: sudo zypper install python3-virtualenv")
            return False

    # 1.2 Venv python va pip yo'lini aniqlash
    if is_windows():
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python3")

    if not os.path.exists(venv_python):
        print(f"[!] Xatolik: Venv python topilmadi: {venv_python}")
        return False

    try:
        # venv ichidagi pip orqali o'rnatish
        print(f"[*] {', '.join(REQUIRED_PACKAGES)} o'rnatilmoqda...")
        # Upgrade pip inside venv first
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([venv_python, "-m", "pip", "install", "-U"] + REQUIRED_PACKAGES)
        print("[+] Kutubxonalar muvaffaqiyatli tayyorlandi.\n")
        return venv_python
    except Exception as e:
        print(f"[!] Xatolik: Kutubxonalarni o'rnatib bo'lmadi: {e}")
        return False

def main():
    print("="*60)
    print("🎬 VDL (Universal Video Downloader) - Universal Setup & Venv")
    print("="*60)
    print(f"Tizim: {get_os_name()}")
    
    # 1. Install pip packages in venv
    venv_python = install_packages()
    if not venv_python:
        sys.exit(1)

    # 2. Check FFmpeg
    print("--- 2. Tizim vositalarini tekshirish (FFmpeg) ---")
    if check_ffmpeg():
        print("[+] FFmpeg topildi. Videolar birlashtirishga tayyor.")
    else:
        print("[!] OGOHLANTIRISH: FFmpeg topilmadi!")
        if is_windows():
            print("    -> O'rnating (Eng oson): winget install ffmpeg")
            print("    -> Yoki yuklab oling: https://ffmpeg.org/download.html")
        elif is_termux():
            print("    -> O'rnating: pkg install ffmpeg")
        else:
            print("    -> Debian/Ubuntu: sudo apt install ffmpeg")
            print("    -> Arch Linux: sudo pacman -S ffmpeg")
            print("    -> Fedora: sudo dnf install ffmpeg")
            print("    -> openSUSE: sudo zypper install ffmpeg")
    print("")

    # 3. Setup Global Command and Chrome Bridge
    print("--- 3. Tizimga integratsiya ---")
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(script_dir)
        import uzmovi_dl
        
        # O'rnatishda venv python manzilini ko'rsatamiz
        if uzmovi_dl.install_kino(venv_python=venv_python):
            print(f"[+] Integratsiya yakunlandi ({get_os_name()}).")
        else:
            print("[!] Integratsiya jarayonida ogohlantirish (Manual setup talab qilinishi mumkin).")
    except Exception as e:
        print(f"[!] Xatolik integratsiyada: {e}")

    print("\n" + "="*60)
    print("🎉 O'rnatish yakunlandi!")
    print("Endi terminalda 'kino' deb yozib dasturni ishga tushirishingiz mumkin.")
    print("="*60 + "\n")

    # 4. Run the app using the venv python
    try:
        cmd = [venv_python, os.path.join(script_dir, "uzmovi_dl.py")]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] Dasturni boshlashda xato: {e}")

if __name__ == "__main__":
    main()
