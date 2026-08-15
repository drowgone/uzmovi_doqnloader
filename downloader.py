#!/usr/bin/env python3
import sys
import os
import re
import time
import signal
import threading
import select
import shutil
import subprocess

IS_WINDOWS = os.name == 'nt'

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

def check_ffmpeg():
    """Tizimda ffmpeg borligini tekshirish"""
    return shutil.which("ffmpeg") is not None

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

def download_with_progress(command, file_name, console=None):
    """Download video with interactive progress bar"""
    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
    if console is None:
        from rich.console import Console
        console = Console()

    cmd = command + ["--newline", "--no-colors"]

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

    desc_limit = 18
    original_desc = file_name[:desc_limit] + "..." if len(file_name) > desc_limit else file_name

    columns = [
        TextColumn("[cyan]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TextColumn("[blue]{task.fields[total_size]:>10}"),
        TextColumn("[magenta]{task.fields[speed]:>11}"),
        TextColumn("[yellow]{task.fields[eta]:>8}"),
    ]

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
    if return_code != 0 and return_code != -15:
        if not IS_WINDOWS:
            try: os.killpg(process.pid, signal.SIGCONT)
            except: pass
        error_msg = "\n".join(error_log[-5:]) if error_log else "Noma'lum xatolik"
        raise Exception(f"Yuklash xatolik bilan to'xtadi (kod={return_code}).\nXatolik tafsiloti:\n{error_msg}")
