#!/usr/bin/env python3
import sys
import os
import urllib.request
import re
import subprocess
import time
import json
import signal
import threading
import select
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- PLATFORM DETECTION ---
IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

# --- DEPENDENCY AUTOLOADER ---
def check_dependencies():
    try:
        import rich
        import questionary
        return True
    except ImportError:
        return False

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

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.panel import Panel
import questionary

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
    """Dastur haqida batafsil yordam ma'lumotlarini ko'rsatish"""
    download_base = load_config()
    print_banner()
    
    os_info = "Linux"
    if IS_WINDOWS: os_info = "Windows"
    if IS_TERMUX: os_info = "Termux (Android)"
    
    help_text = f"""
[bold cyan]Sizning tizimingiz:[/bold cyan] [white]{os_info}[/white]
[bold yellow]📂 Joriy yuklash papkasi:[/bold yellow] [cyan]{download_base}[/cyan]

[bold yellow]Dastur haqida:[/bold yellow]
Ushbu dastur istalgan video manzilidan (YouTube, Instagram, Uzmovi va h.k.) videolarni [bold]yt-dlp[/bold] yordamida yuklab olish uchun mo'ljallangan.

[bold green]Buyruqlar:[/bold green]
  [bold]kino[/bold]          - Dasturni interaktiv menyu bilan ochish
  [bold]kino --help[/bold]   - Ushbu yordam oynasini ko'rsatish

[bold magenta]Sizning tizimingizdagi manzillar:[/bold magenta]
  - [cyan]Konfiguratsiya:[/cyan] {CONFIG_FILE}
  - [cyan]Global buyruq:[/cyan]  kino

[bold blue]Imkoniyatlar:[/bold blue]
  1. Istalgan video URL manzilidan yuklash (Universal).
  2. .txt fayldagi ko'plab linklarni ommaviy yuklash.
  3. Uzmovi.tv dagi yashirin serial va filmlarni topish.

[bold magenta]🌐 CHROME INTEGRATSIYASI (KENGAYTMA):[/bold magenta]
Brauzerda o'ng tugmani bosish orqali yuklashni xohlasangiz:
1. Chrome'da [cyan]chrome://extensions/[/cyan] ga kiring.
2. [white]Developer mode[/white] ni yoqing va [white]Load unpacked[/white] tugmasini bosing.
3. Papkani tanlang: [yellow]{os.path.dirname(os.path.realpath(__file__))}/vdl_extension[/yellow]
4. Kengaytmaning [white]ID[/white] raqamini nusxalang.
5. [yellow]{os.path.dirname(os.path.realpath(__file__))}/vdl_host/com.antigravity.vdl.json[/yellow]
   faylini ochib, [white]PLACEHOLDER_ID[/white] o'rniga ID ni qo'ying.
6. Sozlamalardan [green]Kino'ni qayta o'rnating[/green] (Install).
"""
    console.print(Panel(help_text, title="YO'RIQNOMA", border_style="blue"))
    sys.exit(0)

def print_banner():
    console.clear()
    banner = r"""[bold cyan]
  _   _ ________  ________     _______  _____  _      
 | | | |__  /  \/  |  _ \ \   / /_   _||  __ \| |     
 | | | | / /| \  / | | | \ \ / /  | |  | |  | | |     
 | |_| |/ /_| |\/| | |_| |\ V /   | |  | |  | | |___  
  \___//____|_|  |_|____/  \_/    |_|  | |__|_|_____| 
                                       |_____/        
[/bold cyan]
[bold white]Universal Video Downloader (Any URL) & Uzmovi TV[/bold white]"""
    console.print(Panel(banner, border_style="cyan", expand=False))

def get_uzmovi_info(url, retries=3):
    """Uzmovi urldan ma'lumotlarni tortib olish"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')

            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1).split('-')[0].strip() if title_match else "Kino"
            title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
            title_clean = title_clean.replace("(", "").replace(")", "").strip()
            
            folder_name = title_clean

            iframe_match = re.search(r'src="(https://uzdown\.(?:live|net|com|org|pw)/embed/[^"]+)"', html)
            if not iframe_match:
                return url, None, "Iframe topilmadi."
            
            iframe_url = iframe_match.group(1)
            
            ep_match = re.search(r'episode=(\d+)', iframe_url)
            if ep_match:
                title_clean = f"{title_clean} - {ep_match.group(1)}-qism"
                
            req2 = urllib.request.Request(iframe_url, headers={'User-Agent': 'Mozilla/5.0'})
            iframe_html = urllib.request.urlopen(req2, timeout=10).read().decode('utf-8')

            m3u8_match = re.search(r"file:\s*'([^']+)'", iframe_html)
            if not m3u8_match:
                return url, None, "m3u8 manba ssilkasi topilmadi."

            return url, {"title": title_clean, "folder": os.path.join("uzmovi", folder_name), "source_url": m3u8_match.group(1)}, None
        except Exception as e:
            if attempt == retries - 1:
                return url, None, str(e)
            time.sleep(1)
    
    return url, None, "Xatolik ro'y berdi"

def get_universal_info(url):
    """yt-dlp yordamida istalgan urldan ma'lumotlarni olish"""
    try:
        cmd = ["yt-dlp", "-j", "--no-playlist", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return url, None, result.stderr.strip() or "yt-dlp ma'lumot ololmadi"
        
        info = json.loads(result.stdout)
        title = info.get("title", "Video")
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        title_clean = title_clean.replace("(", "").replace(")", "").strip() # Qavslarni ham olib tashlaymiz xavfsizlik uchun
        
        # Folder nomi sifatida sayt nomini ishlatamiz yoki 'Downloads'
        folder_name = info.get("extractor_key", "General")
        
        return url, {"title": title_clean, "folder": os.path.join(folder_name, title_clean), "source_url": url}, None
    except Exception as e:
        return url, None, str(e)

def get_video_info(url):
    """Urlni tekshirib tegishli parserga yuborish"""
    if "uzmovi.tv" in url:
        return get_uzmovi_info(url)
    else:
        return get_universal_info(url)

def get_available_qualities(url):
    """yt-dlp yordamida mavjud sifatlarni aniqlash"""
    try:
        cmd = ["yt-dlp", "-j", "--no-playlist", url]
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

def get_single_key():
    """Tugma bosilishini blokirovka qilmasdan o'qish"""
    if IS_WINDOWS:
        if msvcrt.kbhit():
            try:
                return msvcrt.getch().decode('utf-8').lower()
            except:
                return None
        return None
    else:
        # Linux/Termux uchun non-blocking stdin
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return None
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            # select yordamida stdin'da ma'lumot borligini tekshirish
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

def download_with_progress(command, file_name):
    # yt-dlp ni qator-ma-qator matn chiqaradigan rejimda ishga tushirish
    cmd = command + ["--newline", "--no-colors"]
    
    # Process group yaratish (Linuxda barcha bolalarini ham to'xtatish uchun)
    popen_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1
    }
    if not IS_WINDOWS:
        popen_kwargs["preexec_fn"] = os.setsid

    process = subprocess.Popen(cmd, **popen_kwargs)

    paused = False
    stop_listener = threading.Event()
    
    paused = False
    stop_listener = threading.Event()
    
    # Terminal kengligidan qat'i nazar barqaror turishi uchun xavfsiz o'lchamlar
    # Kino nomini 15-20 belgida cheklaymiz, shunda bar qisqarib-cho'zilishga joy qoladi
    desc_limit = 18
    original_desc = file_name[:desc_limit] + "..." if len(file_name) > desc_limit else file_name

    # Eng barqaror va xavfsiz ustunlar
    columns = [
        TextColumn("[cyan]{task.description}"),          # Tavsif (pad qilingan)
        BarColumn(bar_width=None),                       # Moslashuvchan bar
        TaskProgressColumn(),                            # %
        TextColumn("[blue]{task.fields[total_size]:>10}"),# Umumiy hajm
        TextColumn("[magenta]{task.fields[speed]:>11}"), # Tezlik
        TextColumn("[yellow]{task.fields[eta]:>8}"),     # Qolgan vaqt
    ]

    # Tavsif qat'iy 20 belgidan oshmasligi va kam bo'lsa bo'shliq bilan to'ldirilishini ta'minlaymiz
    formatted_desc = original_desc.ljust(20)

    with Progress(*columns, console=console, transient=False, refresh_per_second=10) as progress:
        task = progress.add_task(f"{formatted_desc}", total=100.0, speed="0 B/s", eta="--:--", total_size="-- MiB")
        
        def input_listener():
            nonlocal paused
            if not IS_WINDOWS:
                fd = sys.stdin.fileno()
                if not os.isatty(fd): return
                old_settings = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            
            try:
                while not stop_listener.is_set() and process.poll() is None:
                    if IS_WINDOWS:
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode('utf-8').lower()
                            if key == 'p':
                                paused = not paused
                                # Windowsda faqat UI'da pauza qilamiz (SIGSTOP yo'q)
                                progress.update(task, description=f"[bold yellow][PAUZA][/bold yellow] {original_desc}" if paused else original_desc)
                        time.sleep(0.1)
                    else:
                        # select bilan input kutish (0.1 soniya timeout)
                        r, _, _ = select.select([sys.stdin], [], [], 0.1)
                        if r:
                            key = sys.stdin.read(1).lower()
                            if key == 'p':
                                paused = not paused
                                if paused:
                                    os.killpg(process.pid, signal.SIGSTOP)
                                    progress.update(task, description=f"[bold yellow][PAUZA][/bold yellow] {original_desc}")
                                else:
                                    os.killpg(process.pid, signal.SIGCONT)
                                    progress.update(task, description=f"{original_desc}")
            except:
                pass
            finally:
                if not IS_WINDOWS:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        listener_thread = threading.Thread(target=input_listener, daemon=True)
        listener_thread.start()

        try:
            error_log = []
            for line in iter(process.stdout.readline, ''):
                if not line: break
                error_log.append(line.strip())
                if len(error_log) > 20: error_log.pop(0)
                
                # Agar pauzada bo'lsa, readline to'xtab qoladi (chunki process ham to'xtagan)
                match = re.search(r'\[download\]\s+(\d+\.\d+)%', line)
                size_match = re.search(r'of\s+([~\d\.\w]+)', line)
                speed_match = re.search(r'at\s+([~\d\.\w]+/s)', line)
                eta_match = re.search(r'ETA\s+([\d:]+)', line)
                
                if match:
                    percent = float(match.group(1))
                    total_size = size_match.group(1) if size_match else "-- MiB"
                    speed = speed_match.group(1) if speed_match else ""
                    eta = eta_match.group(1) if eta_match else ""
                    progress.update(task, completed=percent, speed=speed, eta=eta, total_size=total_size)
        except KeyboardInterrupt:
            stop_listener.set()
            if not IS_WINDOWS:
                try: 
                    os.killpg(process.pid, signal.SIGCONT)
                    os.killpg(process.pid, signal.SIGTERM)
                except: pass
            process.terminate()
            raise KeyboardInterrupt
        finally:
            stop_listener.set()
                
    process.stdout.close()
    return_code = process.wait()
    if return_code != 0 and return_code != -15: # -15 is SIGTERM
        if not IS_WINDOWS:
            try: os.killpg(process.pid, signal.SIGCONT)
            except: pass
        error_msg = "\n".join(error_log[-5:]) if error_log else "Noma'lum xatolik"
        raise Exception(f"Yuklash xatolik bilan to'xtadi (kod={return_code}).\nXatolik tafsiloti:\n{error_msg}")

def is_installed():
    """Dastur tizimga o'rnatilganligini tekshirish"""
    if IS_WINDOWS:
        link_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'kino.cmd')
    else:
        link_path = os.path.expanduser("~/.local/bin/kino")
    return os.path.exists(link_path)

def install_chrome_bridge():
    """Chrome uchun Native Messaging Host'ni avtomatik sozlash"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    host_json_path = os.path.join(script_dir, "vdl_host", "com.antigravity.vdl.json")
    
    if not os.path.exists(host_json_path):
        return

    host_name = "com.antigravity.vdl"

    # Tayyorlash: Manifest tarkibini o'qish va moslashtirish
    try:
        with open(host_json_path, 'r') as f:
            manifest = json.load(f)
        
        # OS ga qarab host yo'lini aniqlash
        host_script_path = os.path.join(script_dir, "vdl_host", "vdl_host.py")
        
        if IS_WINDOWS:
            # Windowsda .bat wrapper yaratamiz, chunki Chrome .py ni to'g'ridan-to'g'ri ishga tushirishi qiyin
            host_cmd_path = os.path.join(script_dir, "vdl_host", "vdl_host.bat")
            with open(host_cmd_path, 'w') as f:
                f.write(f'@echo off\n"{sys.executable}" "{host_script_path}" %*')
        else:
            host_cmd_path = host_script_path
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
            
            # Yangilangan manifestni source joyiga saqlab qo'yamiz (yoki vaqtinchalik)
            # Lekin registry manifestning O'ZIGA emas, uning JOYLASHGAN JOYIGA qarashi kerak
            # Shuning uchun source manifestni o'zini yangilaymiz
            with open(host_json_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key_path)
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, host_json_path)
            winreg.CloseKey(key)
            
            for browser in ["Chromium", "Microsoft\\Edge"]:
                reg_key_path = f"Software\\{browser}\\NativeMessagingHosts\\{host_name}"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key_path)
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, host_json_path)
                winreg.CloseKey(key)

            console.print("[bold green][+] Chrome/Edge integratsiyasi (Windows Registry) muvaffaqiyatli sozlandi.[/bold green]")
        except Exception as e:
            console.print(f"[bold yellow][!] Windowsda integratsiyani o'rnatib bo'lmadi: {e}[/bold yellow]")
    else:
        # Linux
        paths = [
            os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts"),
            os.path.expanduser("~/.config/chromium/NativeMessagingHosts"),
            os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts")
        ]
        
        try:
            for p in paths:
                os.makedirs(p, exist_ok=True)
                target = os.path.join(p, f"{host_name}.json")
                with open(target, 'w') as f:
                    json.dump(manifest, f, indent=2)
            console.print("[bold green][+] Chrome integratsiyasi (Native Host) muvaffaqiyatli sozlandi.[/bold green]")
        except Exception as e:
            console.print(f"[bold yellow][!] Linuxda integratsiyani o'rnatib bo'lmadi: {e}[/bold yellow]")

def install_kino():
    """Dasturni 'kino' buyrug'i orqali ishga tushadigan qilish (Install)"""
    script_path = os.path.realpath(__file__)
    
    if IS_WINDOWS:
        # Windowsda WindowsApps papkasi PATHda bor
        bin_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps')
        link_path = os.path.join(bin_dir, "kino.cmd")
        wrapper_content = f'@echo off\npython "{script_path}" %*'
    else:
        bin_dir = os.path.expanduser("~/.local/bin")
        link_path = os.path.join(bin_dir, "kino")
    
    try:
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir, exist_ok=True)
            
        if os.path.exists(link_path):
            if os.path.islink(link_path) or os.path.isfile(link_path):
                os.remove(link_path)
            
        if IS_WINDOWS:
            with open(link_path, 'w') as f:
                f.write(wrapper_content)
        else:
            os.symlink(script_path, link_path)
            os.chmod(script_path, 0o755)
        
        # Chrome integratsiyasini ham o'rnatamiz
        install_chrome_bridge()
        
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
    """Sozlamalar sub-menyusi"""
    installed = is_installed()
    
    choices = [
        questionary.Choice(
            title=[('class:folder', "Yuklash papkasini o'zgartirish")], 
            value="folder"
        )
    ]
    
    if not installed:
        choices.append(questionary.Choice(
            title=[('class:install', "Dasturni tizimga o'rnatish ('kino' buyrug'i)")], 
            value="install"
        ))
    else:
        choices.append(questionary.Choice(
            title=[('class:uninstall', "Dasturni tizimdan o'chirish")], 
            value="uninstall"
        ))
        
    choices.append(questionary.Choice(
        title=[('class:back', "Orqaga")], 
        value="back"
    ))

    action = questionary.select(
        "Sozlamalar menyusi:",
        choices=choices,
        style=questionary.Style([
            ('highlighted', 'fg:cyan bold'),
            ('pointer', 'fg:cyan bold'),
            ('folder', 'fg:blue'),
            ('install', 'fg:green'),
            ('uninstall', 'fg:red'),
            ('back', 'fg:yellow'),
        ])
    ).ask()

    if not action or action == "back":
        return True

    if action == "folder":
        new_path = questionary.path("Yangi yuklash papkasini tanlang:", default=download_base, only_directories=True).ask()
        if new_path:
            save_config(new_path)
            console.print(f"[bold green][+] Yuklash papkasi '{new_path}' ga o'zgartirildi.[/bold green]")
    elif action == "install":
        install_kino()
    elif action == "uninstall":
        uninstall_kino()
    
    return True

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
                future_to_url = {executor.submit(get_video_info, url): url for url in urls}
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
    if download_confirm:
        for idx, info in enumerate(results, 1):
            # Global yuklash papkasini ham inobatga olamiz
            target_folder = os.path.join(download_base, info['folder'])
            os.makedirs(target_folder, exist_ok=True)
            
            file_name = f"{info['title']}.mp4"
            file_path = os.path.join(target_folder, file_name)
            
            console.print(f"\n[bold green]=== [{idx}/{len(results)}] {file_name} ===[/bold green]")
            console.print(f"[cyan]📁 Saqlash joyi: {target_folder}/[/cyan]")
            
            if os.path.exists(file_path):
                console.print(f"[bold yellow][!] Bu kino mavjud, o'tkazib yuborilmoqda: {file_path}[/bold yellow]")
                continue
                
            command = [
                "yt-dlp", 
                info['source_url'], 
                "--no-playlist",
                "-f", quality_str,
                "--merge-output-format", "mp4",
                "--concurrent-fragments", "4",
                "-o", file_path
            ]
            try:
                download_with_progress(command, file_name)
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
    
    original_url, info, error = get_video_info(url)
    if not info:
        console.print(f"[bold red][!] Ma'lumot olib bo'lmadi: {error}[/bold red]")
        sys.exit(1)
    
    # Sifatlarni tekshirish
    console.print("[cyan]🔍 Mavjud sifatlar tekshirilmoqda...[/cyan]")
    heights = get_available_qualities(info['source_url'])
    
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
    
    target_folder = os.path.join(download_base, info['folder'])
    os.makedirs(target_folder, exist_ok=True)
    
    file_name = f"{info['title']}.mp4"
    file_path = os.path.join(target_folder, file_name)
    
    console.print(f"[bold green]=== [1/1] {file_name} ===[/bold green]")
    console.print(f"[cyan]📁 Saqlash joyi: {target_folder}/[/cyan]")
    
    if os.path.exists(file_path):
        console.print(f"[bold yellow][!] Bu video mavjud: {file_path}[/bold yellow]")
        sys.exit(0)
    
    command = [
        "yt-dlp", 
        info['source_url'], 
        "--no-playlist",
        "-f", quality_str,
        "--merge-output-format", "mp4",
        "--concurrent-fragments", "4",
        "-o", file_path
    ]
    try:
        download_with_progress(command, file_name)
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
