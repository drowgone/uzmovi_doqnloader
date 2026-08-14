#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import time
import json
import signal
import threading
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- PLATFORM DETECTION ---
IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

# --- WINDOWS HARDENING ---
if IS_WINDOWS:
    try:
        # Windowsda terminal kodirovkasini UTF-8 ga o'tkazish (Emoji va maxsus belgilar uchun)
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
    # Try local .venv relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, '.venv')
    
    if IS_WINDOWS:
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python3')

    if os.path.exists(venv_python) and sys.executable != venv_python:
        # Restart using venv
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        # Still missing? Show help
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

# Now we can import Rich, Questionary, and our helper modules safely
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
import questionary

# Dynamic imports of extracted modules
import parser
import downloader
import ui

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
                # Agar papka o'chib ketgan bo'lsa, joriy papkaga qaytaramiz
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

def show_help():
    ui.show_help(console, Panel, IS_WINDOWS, IS_TERMUX, CONFIG_FILE, load_config)

def print_banner():
    ui.print_banner(console, Panel)

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

    # Tayyorlash: Manifest and CONFIG_DIR paths
    config_dir = get_config_dir()
    os.makedirs(config_dir, exist_ok=True)
    host_json_path = os.path.join(config_dir, "com.chrome_ex.vdl.json")

    try:
        with open(host_json_template_path, 'r') as f:
            manifest = json.load(f)
        
        # OS ga qarab host yo'lini aniqlash
        host_script_path = os.path.join(script_dir, "vdl_host", "vdl_host.py")

        # Python interpreterini aniqlash (agar berilmagan bo'lsa)
        if not python_exe:
            python_exe = sys.executable
            venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe") if IS_WINDOWS else os.path.join(script_dir, ".venv", "bin", "python3")
            if os.path.exists(venv_python):
                python_exe = venv_python

        if IS_WINDOWS:
            # Windowsda .bat wrapper yaratamiz, chunki Chrome .py ni to'g'ridan-to'g'ri ishga tushirishi qiyin
            host_cmd_path = os.path.join(config_dir, "vdl_host.bat")
            with open(host_cmd_path, 'w') as f:
                f.write(f'@echo off\n"{python_exe}" "{host_script_path}" %*')
        else:
            # Linuxda ham wrapper orqali venv pythonni ishlatamiz
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
            # Registry path calculation
            reg_key_path = f"Software\\Google\\Chrome\\NativeMessagingHosts\\{host_name}"

            # Yangilangan manifestni safe config_dir ichiga saqlab qo'yamiz (template o'zgarishsiz qoladi!)
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
        # Linux va macOS
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
            # Yangilangan manifestni safe config_dir ichiga saqlab qo'yamiz (template o'zgarishsiz qoladi!)
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
    
    # Python interpreterini aniqlash
    python_exe = venv_python if venv_python else sys.executable
    if not venv_python:
        # Avtomatik .venv ni tekshirish
        auto_venv = os.path.join(script_dir, ".venv", "Scripts", "python.exe") if IS_WINDOWS else os.path.join(script_dir, ".venv", "bin", "python3")
        if os.path.exists(auto_venv):
            python_exe = auto_venv

    if IS_WINDOWS:
        # Windowsda WindowsApps papkasi PATHda bor
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
            
        # Wrapper yaratish (Linuxda ham, Windowsda ham)
        with open(link_path, 'w') as f:
            f.write(wrapper_content)
        
        if not IS_WINDOWS:
            os.chmod(link_path, 0o755)
            os.chmod(script_path, 0o755)
        
        # Chrome integratsiyasini ham o'rnatamiz
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
        link_path = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'WindowsApps', 'kino.cmd')
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

def run_settings(download_base):
    return ui.run_settings(console, questionary, is_installed, save_config, install_kino, uninstall_kino, download_base)

def run_app():
    download_base = load_config()
    print_banner()
    console.print(f"[bold yellow]📂 Joriy yuklash papkasi: [cyan]{download_base}[/cyan][/bold yellow]\n")
    
    action = questionary.select(
        "Nima qilmoqchisiz?",
        choices=[
            questionary.Choice(
                title=[('class:single', "Yagona sahifa ssilkasini kiritish")], 
                value="single"
            ),
            questionary.Choice(
                title=[('class:list', "Ssilkalar ro'yxati matn fayli (.txt) ni o'qish")], 
                value="list"
            ),
            questionary.Choice(
                title=[('class:settings', "Sozlamalar (Settings)")], 
                value="Settings"
            ),
            questionary.Choice(
                title=[('class:exit', "Chiqish")], 
                value="exit"
            )
        ],
        style=questionary.Style([
            ('highlighted', 'fg:cyan bold'),
            ('pointer', 'fg:cyan bold'),
            ('single', 'fg:green'),
            ('list', 'fg:blue'),
            ('settings', 'fg:red bold'),
            ('exit', 'fg:red'),
        ])
    ).ask()

    urls = []
    results = []
    failed = []
    is_pre_parsed = False
    
    if not action or action == "exit":
        return False
    elif action == "Settings":
        run_settings(download_base)
        return True
    elif action == "single":
        url = questionary.text("Video URL manzilini kiriting (YouTube, Uzmovi va h.k.):").ask()
        if not url: return True
        urls.append(url.strip())
    elif action == "list":
        file_path = questionary.path("Ro'yxat matn faylini tanlang (masalan: topilgan_kinolar.txt):").ask()
        if not file_path or not os.path.isfile(file_path):
            console.print(f"[bold red][!] Bunday yuklash fayli topilmadi.[/bold red]")
            return True
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Faylda bizning maxsus keshimiz belgilari bormi?
        if any(line.startswith("Kino: ") for line in lines):
            is_pre_parsed = True
            for i, line in enumerate(lines):
                if line.startswith("Kino: "):
                    title = line.replace("Kino: ", "").strip()
                    url_line = lines[i+1] if i+1 < len(lines) else ""
                    if url_line.startswith("URL: "):
                        source_url = url_line.replace("URL: ", "").strip()
                        # Extract folder from title (strip out episode suffixes)
                        folder = title.split(' - ')[0].strip() if ' - ' in title else title
                        results.append({"title": title, "folder": folder, "source_url": source_url})
            console.print(f"\n[bold green][+] Tizim o'rnatishga tayyor tarzdagi '{file_path}' zaxira arxiv ma'lumotlarini tanidi![/bold green]")
        else:
            urls = [line.strip() for line in lines if line.strip() and line.startswith('http')]

    if not is_pre_parsed:
        total = len(urls)
        if total == 0:
            console.print("[bold red][!] Birorta ham havola topilmadi![/bold red]")
            return True
            
        console.print(f"\n[bold green][+] Jami {total} ta havola tekshirish uchun qabul qilindi.[/bold green]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Kino ma'lumotlari qidirilmoqda...", total=total)
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(parser.get_video_info, url): url for url in urls}
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        original_url, info, error = future.result()
                        if info:
                            results.append(info)
                        else:
                            failed.append((original_url, error))
                    except Exception as exc:
                        failed.append((url, str(exc)))
                    progress.advance(task)

        console.print("\n[bold]--- TAYYOR ---[/bold]")
        console.print(f"[bold green][+] Muvaffaqiyatli tortib olindi: {len(results)} ta[/bold green]")
        if failed:
            console.print(f"[bold yellow][!] Xato deb topildi: {len(failed)} ta (Uzmovi ushbu filmlarni o'chirgan bo'lishi mumkin)[/bold yellow]")
            for err_url, err_msg in failed:
                console.print(f"   [yellow]->[/yellow] {err_url[:60]}... (Xato: [red]{err_msg}[/red])")

    if not results:
        return True

    quality_choice = questionary.select(
        "\nQaysi sifatda yuklab olishni xohlaysiz?",
        choices=[
            "1080p | Eng yaxshi sifat (Katta hajm)",
            "720p  | O'rtacha (Kompuyter va telefon uchun mos)",
            "480p  | Past sifat (Tez tortish, joyni tejash uchun)"
        ],
        style=questionary.Style([('highlighted', 'fg:green bold')])
    ).ask()

    if not quality_choice: return True
    
    if "1080p" in quality_choice:
        quality_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    elif "720p" in quality_choice:
        quality_str = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best"
    else:
        quality_str = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]/best"

    download_confirm = questionary.confirm("Kinolarni hozirning o'zida yuklashni boshlaymizmi?").ask()

    save_path = "topilgan_kinolar.txt"
    
    # FFmpeg tekshiruvi (YouTube va h.k. uchun juda muhim)
    is_ffmpeg_ok = downloader.check_ffmpeg()

    if download_confirm:
        # Agar FFmpeg yo'q bo'lsa va bu ehtimol YouTube bo'lsa, ogohlantirish
        if not is_ffmpeg_ok:
            downloader.show_ffmpeg_warning(console, Panel)
            console.print("[bold yellow][!] Ogohlantirish: Videolar alohida (audio/video) bo'lib qolishi mumkin.[/bold yellow]")
            if not questionary.confirm("Baribir davom etamizmi?").ask():
                return True
                
        for idx, info in enumerate(results, 1):
            # Global yuklash papkasini ham inobatga olamiz
            target_folder = os.path.join(download_base, info['folder'])
            file_name = f"{info['title']}.mp4"
            file_path = os.path.join(target_folder, file_name)
            
            # Xavfsizlik tekshiruvi: path traversal hujumini to'liq bloklash
            if not downloader.is_safe_path(download_base, file_path):
                console.print(f"[bold red][!] XAVFSIZLIK XATOLIGI: {file_name} yuklash papkasidan tashqarida joylashgan! O'tkazib yuborilmoqda.[/bold red]")
                continue

            os.makedirs(target_folder, exist_ok=True)

            console.print(f"\n[bold green]=== [{idx}/{len(results)}] {file_name} ===[/bold green]")
            console.print(f"[cyan]📁 Saqlash joyi: {target_folder}/[/cyan]")
            
            if os.path.exists(file_path):
                console.print(f"[bold yellow][!] Bu kino mavjud, o'tkazib yuborilmoqda: {file_path}[/bold yellow]")
                continue
                
            command = [
                sys.executable, "-m", "yt_dlp", 
                info['source_url'], 
                "--no-playlist",
                "-f", quality_str,
                "--merge-output-format", "mp4",
                "--concurrent-fragments", "4",
                "-o", file_path
            ]
            if IS_WINDOWS:
                # Windowsda path length va noqonuniy belgilar muammosini oldini olish
                command.extend(["--windows-filenames", "--restrict-filenames", "--trim-filenames", "160"])
            try:
                downloader.download_with_progress(
                    command, file_name, console, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
                )
                console.print(f"[bold cyan][+] Muvaffaqiyatli saqlandi: {file_path}[/bold cyan]")
            except KeyboardInterrupt:
                console.print(f"\n[bold red][-] Yuklash bekor qilindi.[/bold red]")
                break
            except Exception as e:
                console.print(f"[bold red][!] Xatolik kuzatildi: {e}[/bold red]")
                
    with open(save_path, 'w', encoding='utf-8') as f:
        for info in results:
            f.write(f"Kino: {info['title']}\nURL: {info['source_url']}\n{'-'*50}\n")
            
    if not download_confirm:
        console.print(f"\n[bold yellow][!] Yuklash bekor qilindi.[/bold yellow]")
    console.print(f"[bold green][+] Topilgan barcha m3u8 ma'lumotlari maxsus zaxira sifatida '{save_path}' ga yozib qo'yildi.[/bold green]\n")
    
    return True

def direct_download(url):
    """URL orqali to'g'ridan-to'g'ri yuklash (interaktiv menyusiz)"""
    download_base = load_config()
    print_banner()
    console.print(f"[bold yellow]🔗 To'g'ridan-to'g'ri yuklash manzil:[/bold yellow] [cyan]{url}[/cyan]\n")
    
    original_url, info, error = parser.get_video_info(url)
    if not info:
        console.print(f"[bold red][!] Ma'lumot olib bo'lmadi: {error}[/bold red]")
        sys.exit(1)
    
    # Sifatlarni tekshirish
    console.print("[cyan]🔍 Mavjud sifatlar tekshirilmoqda...[/cyan]")
    heights = parser.get_available_qualities(info['source_url'])
    
    quality_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" # Default
    
    if len(heights) > 1:
        choices = []
        for h in heights:
            choices.append(f"{h}p")
        choices.append("Eng yaxshi (Auto)")
        
        selected = questionary.select(
            "Video sifati kiritilgan ssilkada bir nechta ekan. Qaysi birini yuklaymiz?",
            choices=choices,
            style=questionary.Style([('highlighted', 'fg:green bold')])
        ).ask()
        
        if not selected or selected == "Eng yaxshi (Auto)":
            quality_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            h_val = selected.replace("p", "")
            quality_str = f"bestvideo[height<={h_val}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_val}][ext=mp4]/best[height<={h_val}]/best"
    elif len(heights) == 1:
        console.print(f"[green][+] Faqat bitta sifat topildi: {heights[0]}p. Shu sifatda yuklanadi.[/green]")
        quality_str = f"bestvideo[height<={heights[0]}][ext=mp4]+bestaudio[ext=m4a]/best[height<={heights[0]}][ext=mp4]/best[height<={heights[0]}]/best"
    else:
        console.print("[yellow][!] Sifatlarni aniqlab bo'lmadi, eng yaxshi sifat tanlanadi.[/yellow]")
    
    # FFmpeg check for direct download
    if not downloader.check_ffmpeg():
        downloader.show_ffmpeg_warning(console, Panel)
        if not questionary.confirm("Baribir davom etamizmi?").ask():
            return True
    
    target_folder = os.path.join(download_base, info['folder'])
    file_name = f"{info['title']}.mp4"
    file_path = os.path.join(target_folder, file_name)

    # Xavfsizlik tekshiruvi: path traversal hujumini to'liq bloklash
    if not downloader.is_safe_path(download_base, file_path):
        console.print(f"[bold red][!] XAVFSIZLIK XATOLIGI: {file_name} yuklash papkasidan tashqarida joylashgan! Chiqilmoqda.[/bold red]")
        sys.exit(1)

    os.makedirs(target_folder, exist_ok=True)
    
    console.print(f"[bold green]=== [1/1] {file_name} ===[/bold green]")
    console.print(f"[cyan]📁 Saqlash joyi: {target_folder}/[/cyan]")
    
    if os.path.exists(file_path):
        console.print(f"[bold yellow][!] Bu video mavjud: {file_path}[/bold yellow]")
        sys.exit(0)
    
    command = [
        sys.executable, "-m", "yt_dlp", 
        info['source_url'], 
        "--no-playlist",
        "-f", quality_str,
        "--merge-output-format", "mp4",
        "--concurrent-fragments", "4",
        "-o", file_path
    ]
    if IS_WINDOWS:
        command.extend(["--windows-filenames", "--restrict-filenames", "--trim-filenames", "160"])
    try:
        downloader.download_with_progress(
            command, file_name, console, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        )
        console.print(f"[bold cyan][+] Muvaffaqiyatli saqlandi: {file_path}[/bold cyan]")
    except Exception as e:
        console.print(f"[bold red][!] Xatolik: {e}[/bold red]")
        sys.exit(1)

if __name__ == '__main__':
    # Argumentlarni tekshirish
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_help()
        
        # URL argumentini qidirish
        for i, arg in enumerate(sys.argv):
            if arg == '--url' and i + 1 < len(sys.argv):
                direct_download(sys.argv[i+1])
                sys.exit(0)
            elif arg.startswith('http'):
                direct_download(arg)
                sys.exit(0)

    try:
        while True:
            is_active = run_app()
            if not is_active:
                console.print(f"\n[bold green]Dasturdan muvaffaqiyatli chiqildi. Xizmatingizga doim tayyormiz![/bold green]")
                break
            # Resultatlarni o'qib bo'lgach ENTER bosishini kutish
            input("\n=> Asosiy menyuga qaytish uchun ENTER tugmasini bosing...")
    except KeyboardInterrupt:
        console.print(f"\n[bold red][-] Dastur jarayoni to'xtatildi.[/bold red]")
        sys.exit(0)
