#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import re
import signal
import threading
import time

# --- PLATFORM DETECTION ---
IS_WINDOWS = os.name == 'nt'
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty
    import select

def check_ffmpeg():
    """Tizimda ffmpeg borligini tekshirish"""
    return shutil.which("ffmpeg") is not None

def show_ffmpeg_warning(console, Panel):
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

def is_safe_path(base_dir, path):
    """Path target directory ichida ekanligini tekshirish (Directory traversal himoyasi)"""
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(path)
    return real_base == real_path or real_path.startswith(real_base + os.sep)

def download_with_progress(command, file_name, console, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn):
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
                                console.print("[yellow]\n[!] Windows operatsion tizimida yuklashni to'xtatib turish (Pause) qo'llab-quvvatlanmaydi.[/yellow]\n")
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
