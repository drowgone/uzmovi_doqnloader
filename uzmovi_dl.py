#!/usr/bin/env python3
import sys
import os
import json

# --- PLATFORM DETECTION ---
IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

# --- WINDOWS HARDENING ---
if IS_WINDOWS:
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# --- DEPENDENCY CHECK ---
def check_dependencies():
    """Check if required libraries (rich, questionary, yt-dlp) are installed"""
    import importlib
    for lib in ["rich", "questionary", "yt_dlp"]:
        try:
            importlib.import_module(lib)
        except ImportError:
            return False
    return True

if not check_dependencies():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, '.venv')
    
    if IS_WINDOWS:
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python3')

    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("-" * 50)
        print(" [!] XATOLIK: Kerakli kutubxonalar topilmadi.")
        print("-" * 50)
        print("Iltimos, kutubxonalarni o'rnating:")
        if IS_TERMUX:
            print(" -> pkg install python ffmpeg")
            print(" -> pip install rich questionary yt-dlp")
        elif IS_WINDOWS:
            print(" -> pip install rich questionary yt-dlp")
        else:
            print(" -> sudo apt install python3-rich python3-questionary yt-dlp")
            print(" Yoki: pip install rich questionary yt-dlp")
        print("-" * 50)
        sys.exit(1)

from rich.console import Console
from parser import sanitize_filename, is_safe_path, get_video_info, get_available_qualities
from downloader import check_ffmpeg, show_ffmpeg_warning, direct_download, download_with_progress
from ui import print_banner, show_help, get_single_key, run_settings, run_app

console = Console()

# --- CONFIGURATION PATHS ---
def get_config_dir():
    if IS_WINDOWS:
        base = os.getenv('APPDATA') or os.path.expanduser('~/AppData/Roaming')
    else:
        base = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, 'uzmovi')

CONFIG_DIR = get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    """Konfiguratsiyani o'qish (yuklash papkasi va h.k.)"""
    default_dir = os.getcwd()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                d_dir = config.get("download_dir", default_dir)
                if os.path.exists(d_dir):
                    return d_dir
        except:
            pass
    return default_dir

def save_config(download_dir):
    """Konfiguratsiyani saqlash"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"download_dir": download_dir}, f)
        return True
    except:
        return False

def is_installed():
    """Dastur tizimga o'rnatilganligini tekshirish"""
    if IS_WINDOWS:
        link_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'kino.cmd')
    else:
        link_path = os.path.expanduser("~/.local/bin/kino")
    return os.path.exists(link_path)

def install_chrome_bridge(python_exe=None):
    """Chrome uchun Native Messaging Host'ni avtomatik sozlash"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    host_json_template_path = os.path.join(script_dir, "vdl_host", "com.chrome_ex.vdl.json")
    
    if not os.path.exists(host_json_template_path):
        return

    host_name = "com.chrome_ex.vdl"

    config_dir = get_config_dir()
    os.makedirs(config_dir, exist_ok=True)
    host_json_path = os.path.join(config_dir, "com.chrome_ex.vdl.json")

    try:
        with open(host_json_template_path, 'r') as f:
            manifest = json.load(f)
        
        host_script_path = os.path.join(script_dir, "vdl_host", "vdl_host.py")

        if not python_exe:
            python_exe = sys.executable
            venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe") if IS_WINDOWS else os.path.join(script_dir, ".venv", "bin", "python3")
            if os.path.exists(venv_python):
                python_exe = venv_python

        if IS_WINDOWS:
            host_cmd_path = os.path.join(config_dir, "vdl_host.bat")
            with open(host_cmd_path, 'w') as f:
                f.write(f'@echo off\n"{python_exe}" "{host_script_path}" %*')
        else:
            host_cmd_path = os.path.join(config_dir, "vdl_host_wrapper.sh")
            with open(host_cmd_path, 'w') as f:
                f.write(f'#!/bin/bash\n"{python_exe}" "{host_script_path}" "$@"')
            os.chmod(host_cmd_path, 0o755)
            os.chmod(host_script_path, 0o755)

        manifest["path"] = host_cmd_path
    except Exception as e:
        console.print(f"[bold yellow][!] Manifest tayyorlashda xato: {e}[/bold yellow]")
        return

    if IS_WINDOWS:
        try:
            import winreg
            reg_key_path = f"Software\\Google\\Chrome\\NativeMessagingHosts\\{host_name}"

            with open(host_json_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key_path)
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, host_json_path)
            winreg.CloseKey(key)

            for browser in ["Chromium", "Microsoft\\Edge", "BraveSoftware\\Brave-Browser"]:
                reg_key_path = f"Software\\{browser}\\NativeMessagingHosts\\{host_name}"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key_path)
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, host_json_path)
                winreg.CloseKey(key)

            console.print("[bold green][+] Chrome/Edge integratsiyasi (Windows Registry) muvaffaqiyatli sozlandi.[/bold green]")
        except Exception as e:
            console.print(f"[bold yellow][!] Windowsda integratsiyani o'rnatib bo'lmadi: {e}[/bold yellow]")
    else:
        paths = [
            os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts"),
            os.path.expanduser("~/.config/chromium/NativeMessagingHosts"),
            os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"),
            os.path.expanduser("~/.config/microsoft-edge/NativeMessagingHosts"),
            os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts"),
            os.path.expanduser("~/Library/Application Support/Chromium/NativeMessagingHosts"),
            os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"),
            os.path.expanduser("~/Library/Application Support/Microsoft Edge/NativeMessagingHosts")
        ]

        try:
            with open(host_json_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            for p in paths:
                try:
                    os.makedirs(p, exist_ok=True)
                    target = os.path.join(p, f"{host_name}.json")
                    with open(target, 'w') as f:
                        json.dump(manifest, f, indent=2)
                except:
                    pass
            console.print("[bold green][+] Chrome integratsiyasi (Native Host) muvaffaqiyatli sozlandi.[/bold green]")
        except Exception as e:
            console.print(f"[bold yellow][!] Unix/Linux/macOS tizimlarida integratsiyani o'rnatib bo'lmadi: {e}[/bold yellow]")

def install_kino(venv_python=None):
    """Dasturni 'kino' buyrug'i orqali ishga tushadigan qilish (Install)"""
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    
    python_exe = venv_python if venv_python else sys.executable
    if not venv_python:
        auto_venv = os.path.join(script_dir, ".venv", "Scripts", "python.exe") if IS_WINDOWS else os.path.join(script_dir, ".venv", "bin", "python3")
        if os.path.exists(auto_venv):
            python_exe = auto_venv

    if IS_WINDOWS:
        bin_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps')
        link_path = os.path.join(bin_dir, "kino.cmd")
        wrapper_content = f'@echo off\n"{python_exe}" "{script_path}" %*'
    else:
        bin_dir = os.path.expanduser("~/.local/bin")
        link_path = os.path.join(bin_dir, "kino")
        wrapper_content = f'#!/bin/bash\n"{python_exe}" "{script_path}" "$@"'
    
    try:
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir, exist_ok=True)
            
        if os.path.exists(link_path):
            if os.path.islink(link_path) or os.path.isfile(link_path):
                os.remove(link_path)
            
        with open(link_path, 'w') as f:
            f.write(wrapper_content)
        
        if not IS_WINDOWS:
            os.chmod(link_path, 0o755)
            os.chmod(script_path, 0o755)
        
        install_chrome_bridge(python_exe=python_exe)
        
        console.print(f"\n[bold green][+] Tabriklaymiz! Dastur muvaffaqiyatli o'rnatildi.[/bold green]")
        console.print(f"[cyan][!] Endi terminalning istalgan joyida shunchaki [bold]kino[/bold] deb yozsangiz dastur ishga tushadi.[/cyan]")
        return True
    except Exception as e:
        console.print(f"\n[bold red][!] O'rnatishda xatolik: {e}[/bold red]")
        return False

def uninstall_kino():
    """'kino' buyrug'ini tizimdan o'chirish (Uninstall)"""
    if IS_WINDOWS:
        link_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'kino.cmd')
    else:
        link_path = os.path.expanduser("~/.local/bin/kino")
        
    try:
        if os.path.exists(link_path):
            os.remove(link_path)
            console.print(f"\n[bold yellow][+] 'kino' buyrug'i tizimdan o'chirildi.[/bold yellow]")
        else:
            console.print(f"\n[bold red][!] Dastur tizimga o'rnatilmagan ekan.[/bold red]")
        return True
    except Exception as e:
        console.print(f"\n[bold red][!] O'chirishda xatolik: {e}[/bold red]")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_help(load_config(), CONFIG_FILE)
        
        for i, arg in enumerate(sys.argv):
            if arg == '--url' and i + 1 < len(sys.argv):
                direct_download(sys.argv[i+1], load_config)
                sys.exit(0)
            elif arg.startswith('http'):
                direct_download(arg, load_config)
                sys.exit(0)

    try:
        while True:
            is_active = run_app(load_config, save_config, install_kino, uninstall_kino, is_installed)
            if not is_active:
                console.print(f"\n[bold green]Dasturdan muvaffaqiyatli chiqildi. Xizmatingizga doim tayyormiz![/bold green]")
                break
            input("\n=> Asosiy menyuga qaytish uchun ENTER tugmasini bosing...")
    except KeyboardInterrupt:
        console.print(f"\n[bold red][-] Dastur jarayoni to'xtatildi.[/bold red]")
        sys.exit(0)
