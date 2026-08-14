#!/usr/bin/env python3
import os
import sys

def print_banner(console, Panel):
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

def show_help(console, Panel, IS_WINDOWS, IS_TERMUX, CONFIG_FILE, load_config):
    """Dastur haqida batafsil yordam ma'lumotlarini ko'rsatish"""
    download_base = load_config()
    print_banner(console, Panel)

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
2. [white]Developer mode[/white] ni yoqing va [white]Load unpacked[/white] ya'ni kengaytmani yuklash tugmasini bosing.
3. Papkani tanlang: [yellow]{os.path.dirname(os.path.realpath(__file__))}/vdl_extension[/yellow]
4. Kengaytmaning [white]ID[/white] raqamini nusxalang.
  5. [yellow]{os.path.dirname(os.path.realpath(__file__))}/vdl_host/com.chrome_ex.vdl.json[/yellow]
   faylini ochib, [white]PLACEHOLDER_ID[/white] o'rniga ID ni qo'ying.
6. Sozlamalardan [green]Kino'ni qayta o'rnating[/green] (Install).
"""
    console.print(Panel(help_text, title="YO'RIQNOMA", border_style="blue"))
    sys.exit(0)

def run_settings(console, questionary, is_installed, save_config, install_kino, uninstall_kino, download_base):
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
