#!/usr/bin/env python3
import sys
import json
import struct
import subprocess
import os

if sys.platform == "win32":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

# Chrome Native Messaging Host logic
def send_message(message):
    encoded_message = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()

def read_message():
    text_length_bytes = sys.stdin.buffer.read(4)
    if not text_length_bytes:
        return None
    text_length = struct.unpack('I', text_length_bytes)[0]
    message = sys.stdin.buffer.read(text_length).decode('utf-8')
    return json.loads(message)

def main():
    while True:
        try:
            message = read_message()
            if message:
                url = message.get('url')
                if url:
                    # URL xavfsizligini tekshirish (Command injection va boshqa xavflarni oldini olish uchun)
                    if not isinstance(url, str):
                        continue
                    from urllib.parse import urlparse
                    try:
                        parsed = urlparse(url.strip())
                        if parsed.scheme not in ("http", "https") or not parsed.netloc:
                            continue
                        url = url.strip()
                    except Exception:
                        continue

                    # Launch the opener script in a new terminal
                    # Using absolute path for safety
                    script_dir = os.path.dirname(os.path.realpath(__file__))
                    # opener is now a python script in the parent directory
                    opener_path = os.path.join(os.path.dirname(script_dir), "kino_opener.py")
                    
                    is_windows = os.name == 'nt'

                    if is_windows:
                        # Windows: Use CREATE_NEW_CONSOLE for a clean separate terminal
                        # This avoids shell quoting issues with 'start' and correctly handles URLs with '&'
                        # We do not use shell=True to prevent command injection!
                        CREATE_NEW_CONSOLE = 0x00000010
                        subprocess.Popen([sys.executable, opener_path, url], creationflags=CREATE_NEW_CONSOLE)
                    elif sys.platform == "darwin":
                        # macOS: Use AppleScript to open Terminal and run the python opener securely
                        launched = False
                        try:
                            cmd_str = f'"{sys.executable}" "{opener_path}" "{url}"'
                            apple_script = f'tell application "Terminal" to do script {json.dumps(cmd_str)}'
                            subprocess.Popen(['osascript', '-e', apple_script])
                            launched = True
                        except Exception:
                            pass

                        if not launched:
                            subprocess.Popen([sys.executable, opener_path, url])
                    else:
                        # Linux: Use available terminal emulators dynamically
                        import shutil
                        terminals = [
                            ('gnome-terminal', ['gnome-terminal', '--app-id', 'org.gnome.Terminal', '--tab', '--active', '--', sys.executable, opener_path, url]),
                            ('konsole', ['konsole', '--new-tab', '-e', sys.executable, opener_path, url]),
                            ('xfce4-terminal', ['xfce4-terminal', '--tab', '-e', f'{sys.executable} "{opener_path}" "{url}"']),
                            ('mate-terminal', ['mate-terminal', '--', sys.executable, opener_path, url]),
                            ('kitty', ['kitty', '--', sys.executable, opener_path, url]),
                            ('alacritty', ['alacritty', '-e', sys.executable, opener_path, url]),
                            ('lxterminal', ['lxterminal', '-e', sys.executable, opener_path, url]),
                            ('x-terminal-emulator', ['x-terminal-emulator', '-e', sys.executable, opener_path, url]),
                            ('xterm', ['xterm', '-e', sys.executable, opener_path, url])
                        ]

                        launched = False
                        for term_name, cmd in terminals:
                            if shutil.which(term_name):
                                try:
                                    subprocess.Popen(cmd)
                                    launched = True
                                    break
                                except Exception:
                                    pass

                        if not launched:
                            # Fallback if no terminal found, run it directly in background (or log)
                            subprocess.Popen([sys.executable, opener_path, url])
                    
                    send_message({"status": "launched", "url": url})
            else:
                break
        except Exception as e:
            # We can log to a file for debugging since stdout is used for messaging
            try:
                script_dir = os.path.dirname(os.path.realpath(__file__))
                log_path = os.path.join(script_dir, "vdl_host_error.log")
                with open(log_path, "a") as f:
                    f.write(str(e) + "\n")
            except:
                pass
            break

if __name__ == '__main__':
    main()
