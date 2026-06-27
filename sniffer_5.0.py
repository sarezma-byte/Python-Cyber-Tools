import tkinter as tk
from tkinter import scrolledtext
import threading
from scapy.all import sniff
import os
import platform
import requests
import subprocess
import ctypes
import os
import sys

def admin_yetkisi_iste():
    try:
        # Eğer zaten yönetici ise devam et
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            # Yönetici değilse, programı yönetici olarak yeniden başlat
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit() # Normal (yetkisiz) olanı kapat
    except:
        return False

# Programın en başına (arayüzden önce) bunu çağır:
admin_yetkisi_iste()

# --- GÜVENLİK AYARLARI ---
engellenenler = set()
paket_sayaci = {}
aktif = False  # Operasyonu durdurup başlatmak için

# --- DOSYA YÜKLEME ---
if os.path.exists("kara_liste.txt"):
    with open("kara_liste.txt", "r") as dosya:
        for satir in dosya:
            engellenenler.add(satir.split(" - ")[0].strip())


# --- LOKASYON BULMA ---
def get_ip_info(ip):
    try:
        # Yerel IP'leri geç
        if ip.startswith("192.168.") or ip.startswith("10."): return "Yerel Ağ"
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = response.json()
        return f"{data.get('country', 'Bilinmiyor')} - {data.get('city', 'Bilinmiyor')}"
    except:
        return "Konum Belirsiz"

admin_yetkisi_iste()

# --- ARAYÜZ KURULUMU ---
root = tk.Tk()
root.title("ANONYCAT - Cyber Command Center")
root.geometry("800x650")
root.configure(bg="#1e1e1e")

label = tk.Label(root, text="[ANONYCAT] CANLI OPERASYON PANELİ", font=("Consolas", 14, "bold"), bg="#1e1e1e", fg="red")
label.pack(pady=10)

traffic_log = scrolledtext.ScrolledText(root, width=90, height=20, bg="black", fg="lime", font=("Consolas", 10))
traffic_log.pack(padx=10, pady=10)


def ekrana_yaz(mesaj):
    traffic_log.insert(tk.END, mesaj + "\n")
    traffic_log.see(tk.END)


def kalkanlari_indir():
    # PowerShell üzerinden yönetici yetkisiyle doğrudan silme komutu
    # Bu komut Windows'un kural listesini daha doğrudan etkiler
    powershell_komut = 'powershell -Command "Remove-NetFirewallRule -DisplayName \'BLOCK_*\' -ErrorAction SilentlyContinue"'

    # Komutu çalıştır
    sonuc = subprocess.run(powershell_komut, shell=True)

    # Dosya ve liste temizliği
    if os.path.exists("kara_liste.txt"):
        os.remove("kara_liste.txt")

    engellenenler.clear()
    ekrana_yaz("[!!!] KALKANLAR İNDİRİLDİ (PowerShell Modu).")

# --- MANTIK SALDIRI VE SAVUNMA ---
def kalkani_aktif_et(ip_adresi):
    if ip_adresi not in engellenenler:
        ekrana_yaz(f"[!!!] GÜVENLİK ALARMI: {ip_adresi} engelleniyor...")
        # Windows firewall komutu
        komut = f'netsh advfirewall firewall add rule name="BLOCK_{ip_adresi}" dir=in action=block remoteip={ip_adresi}'
        os.system(komut)
        with open("kara_liste.txt", "a") as kara_liste:
            kara_liste.write(f"{ip_adresi} - Tarih: 2026\n")
        engellenenler.add(ip_adresi)
        ekrana_yaz(f"[!] BAŞARILI: {ip_adresi} bloklandı.")


def paket_yakalayici(paket):
    if not aktif: return
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].src
        dst_port = paket['TCP'].dport
        baglanti_id = f"{src_ip} -> {paket['IP'].dst} (Port: {dst_port})"

        paket_sayaci[baglanti_id] = paket_sayaci.get(baglanti_id, 0) + 1

        # Lokasyon ve trafik bilgisi
        if paket_sayaci[baglanti_id] % 20 == 0:  # Her 20 pakette bir lokasyon sorgula (sistemi yormamak için)
            konum = get_ip_info(src_ip)
            ekrana_yaz(f"[+] Trafik: {src_ip} | Konum: {konum} | Sayı: {paket_sayaci[baglanti_id]}")

        # Şüpheli trafik kontrolü
        if paket_sayaci[baglanti_id] > 50 and src_ip != "192.168.1.63":
            kalkani_aktif_et(src_ip)




def sistemi_baslat():
    global aktif
    aktif = True
    ekrana_yaz("[!] Sistem Aktif: Dinleme başlatıldı...")
    t = threading.Thread(target=lambda: sniff(filter="ip or tcp", prn=paket_yakalayici, store=0), daemon=True)
    t.start()


def sistemi_durdur():
    global aktif
    aktif = False
    ekrana_yaz("[!] OPERASYON DURDURULDU.")


# --- BUTONLAR ---
btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(pady=20)

tk.Button(btn_frame, text="BAŞLAT", command=sistemi_baslat, bg="green", fg="white", width=15).pack(side=tk.LEFT,
                                                                                                   padx=10)
tk.Button(btn_frame, text="DURDUR", command=sistemi_durdur, bg="red", fg="white", width=15).pack(side=tk.RIGHT, padx=10)

# Mevcut BAŞLAT ve DURDUR butonlarının yanına bunu ekle
tk.Button(btn_frame, text="KALKANLARI İNDİR", command=kalkanlari_indir, bg="orange", fg="black", width=20).pack(side=tk.LEFT, padx=10)

root.mainloop()