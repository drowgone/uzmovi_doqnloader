#!/usr/bin/env python3
import os
import sys
import json
from rich.console import Console
from rich.panel import Panel
from downloader import check_ffmpeg

IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

console = Console()

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

def show_ffmpeg_warning():
    """FFmpeg yo'qligi haqida chiroyli ogohlantirish ko'rsatish"""
    if check_ffmpeg():
        return True

    warning_text = """
[bold red]⚠️  DIQQAT: FFmpeg topilmadi (Missing FFmpeg)![/bold red]

YouTube va boshqa saytlardan [bold]1080p+[/bold] sifatda video yuklashda
video va audio [bold]aylanib (merging)[/bold] qolmasligi uchun [bold]FFmpeg[/bold] shart!

[bold yellow]Yechim (O'rnatish):[/bold yellow]
  [green]• Windows:[/green]   Terminalda shunchaki: [bold blue]winget install ffmpeg[/bold blue]
  [green]• Linux:[/green]     [bold blue]sudo apt install ffmpeg[/bold blue]
  [green]• Termux:[/green]    [bold blue]pkg install ffmpeg[/bold blue]

[cyan]FFmpeg o'rnatilgandan so'ng dasturni qaytadan ishga tushiring.[/cyan]
"""
    console.print(Panel(warning_text, title="TIZIM XATOLIGI", border_style="red"))
    return False

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
5. [yellow]{os.path.dirname(os.path.realpath(__file__))}/vdl_host/com.chrome_ex.vdl.json[/yellow]
   faylini ochib, [white]PLACEHOLDER_ID[/white] o'rniga ID ni qo'ying.
6. Sozlamalardan [green]Kino'ni qayta o'rnating[/green] (Install).
"""
    console.print(Panel(help_text, title="YO'RIQNOMA", border_style="blue"))
    sys.exit(0)
