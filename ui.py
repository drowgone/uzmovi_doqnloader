import os
import sys
import select
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
import questionary

from parser import is_safe_path, get_video_info
from downloader import check_ffmpeg, show_ffmpeg_warning, download_with_progress

IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

console = Console()

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

def show_help(download_base, config_file):
    """Dastur haqida batafsil yordam ma'lumotlarini ko'rsatish"""
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
  - [cyan]Konfiguratsiya:[/cyan] {config_file}
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
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return None
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

def run_settings(download_base, save_config_func, install_kino_func, uninstall_kino_func, is_installed_func):
    """Sozlamalar sub-menyusi"""
    installed = is_installed_func()

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
            save_config_func(new_path)
            console.print(f"[bold green][+] Yuklash papkasi '{new_path}' ga o'zgartirildi.[/bold green]")
    elif action == "install":
        install_kino_func()
    elif action == "uninstall":
        uninstall_kino_func()

    return True

def run_app(load_config_func, save_config_func, install_kino_func, uninstall_kino_func, is_installed_func):
    download_base = load_config_func()
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
        run_settings(download_base, save_config_func, install_kino_func, uninstall_kino_func, is_installed_func)
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

        if any(line.startswith("Kino: ") for line in lines):
            is_pre_parsed = True
            for i, line in enumerate(lines):
                if line.startswith("Kino: "):
                    title = line.replace("Kino: ", "").strip()
                    url_line = lines[i+1] if i+1 < len(lines) else ""
                    if url_line.startswith("URL: "):
                        source_url = url_line.replace("URL: ", "").strip()
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
    is_ffmpeg_ok = check_ffmpeg()

    if download_confirm:
        if not is_ffmpeg_ok:
            show_ffmpeg_warning()
            console.print("[bold yellow][!] Ogohlantirish: Videolar alohida (audio/video) bo'lib qolishi mumkin.[/bold yellow]")
            if not questionary.confirm("Baribir davom etamizmi?").ask():
                return True

        for idx, info in enumerate(results, 1):
            target_folder = os.path.join(download_base, info['folder'])
            file_name = f"{info['title']}.mp4"
            file_path = os.path.join(target_folder, file_name)

            if not is_safe_path(download_base, file_path):
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
                command.extend(["--windows-filenames", "--restrict-filenames", "--trim-filenames", "160"])
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
