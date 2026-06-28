import tkinter as tk
# Kırmızı çizgiyi engellemek için daha net import:
from scapy.all import sniff
from scapy.layers.l2 import ARP
from scapy.config import conf
from tkinter import scrolledtext
import threading
from scapy.all import sniff
import os
import requests
import subprocess
import ctypes
import sys
import datetime

def arp_monitor_callback(pkt):
    if pkt.haslayer(ARP) and pkt[ARP].op == 2: # Sadece ARP yanıtlarını al
        # Eğer modemin (Gateway) MAC adresi değişiyorsa bu bir zehirlemedir
        # Buraya kendi modeminin IP'sini yaz (Örn: 192.168.1.1)
        gateway_ip = "192.168.1.1"
        if pkt[ARP].psrc == gateway_ip:
            # Gerçek MAC adresini buraya sabitlemelisin!
            # Bunu 'arp -a' komutuyla CMD'den öğrenebilirsin
            gercek_mac = "XX:XX:XX:XX:XX:XX"
            if pkt[ARP].hwsrc != gercek_mac:
                ekrana_yaz(f"[!!!] KRİTİK: ARP ZEHİRLENMESİ TESPİT EDİLDİ! Saldırgan: {pkt[ARP].hwsrc}")
                # Hızlıca kalkanı devreye sok
                kalkani_aktif_et(pkt[ARP].psrc)

# --- YETKİ KONTROLÜ ---
def admin_yetkisi_iste():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass


admin_yetkisi_iste()

# --- ARAYÜZ ---
root = tk.Tk()
root.title("ANONYCAT - 🇹🇷 Siber Paket Analizörü 🇹🇷 ")
root.geometry("800x650")
root.configure(bg="#1e1e1e")

traffic_log = scrolledtext.ScrolledText(root, width=90, height=20, bg="black", fg="lime", font=("Consolas", 10))
traffic_log.pack(padx=10, pady=10)

engellenenler = set()
paket_sayaci = {}
aktif = False
GUVENLI_PREFIXLER = {"172.217.", "216.239.", "192.178.", "142.251.", "52.", "35.", "172.253.", "13.", "192.168.1."}
# 192.168.1. ekledim ki kendi ev ağındaki cihazlarını engelleme!

if os.path.exists("kara_liste.txt"):
    with open("kara_liste.txt", "r") as f:
        for line in f:
            if line.strip():
                ip = line.split(" | ")[0]
                engellenenler.add(ip)


def ekrana_yaz(mesaj):
    zaman = datetime.datetime.now().strftime("%H:%M:%S")
    traffic_log.insert(tk.END, f"[{zaman}] {mesaj}\n")
    traffic_log.see(tk.END)


def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = response.json()
        return f"{data.get('country')} - {data.get('city')}" if data.get('status') == 'success' else "Bilinmiyor"
    except:
        return "Bilinmiyor"


def blok_analiz_ve_kilit(yeni_ip):
    blok = ".".join(yeni_ip.split('.')[:3])
    ayni_bloktan_kac_tane = sum(1 for ip in engellenenler if ip.startswith(blok))
    if ayni_bloktan_kac_tane >= 3:
        ekrana_yaz(f"[!!!] KRİTİK: {blok}.0/24 Bloğu tespit edildi. Engelleniyor!")
        komut = f'netsh advfirewall firewall add rule name="BLOCK_SUBNET_{blok}" dir=in action=block remoteip={blok}.0/24'
        subprocess.run(komut, shell=True)
        with open("kara_liste.txt", "a") as f:
            f.write(f"{blok}.0/24 | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (OTOMATİK)\n")


def kalkani_aktif_et(ip_adresi):
    if ip_adresi not in engellenenler:
        konum = get_ip_info(ip_adresi)
        zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ekrana_yaz(f"[!!!] ENGELLEME: {ip_adresi} ({konum})")
        komut = f'netsh advfirewall firewall add rule name="BLOCK_{ip_adresi}" dir=in action=block remoteip={ip_adresi}'
        try:
            subprocess.run(komut, shell=True)
            with open("kara_liste.txt", "a") as f:
                f.write(f"{ip_adresi} | {zaman}\n")
            engellenenler.add(ip_adresi)
            blok_analiz_ve_kilit(ip_adresi)
        except Exception as e:
            ekrana_yaz(f"[X] HATA: {e}")


def paket_yakalayici(paket):
    global paket_sayaci
    if not aktif or not paket.haslayer('IP'): return

    src_ip = paket['IP'].src
    dst_ip = paket['IP'].dst  # Hedef IP'yi alıyoruz

    # Güvenli IP'leri ve kendi kara listemizi kontrol et
    if src_ip in engellenenler or src_ip.startswith("192.168.") or any(src_ip.startswith(p) for p in GUVENLI_PREFIXLER):
        return

    paket_sayaci[src_ip] = paket_sayaci.get(src_ip, 0) + 1

    if paket_sayaci[src_ip] == 1:
        konum = get_ip_info(src_ip)
        port_bilgisi = str(paket['TCP'].dport) if paket.haslayer('TCP') else "N/A"

        # Burası kilit nokta: Kaynaktan hedefe geçişi logluyoruz
        ekrana_yaz(f"[!!!] TRAFİK: {src_ip} -> {dst_ip} | Konum: {konum} | Port: {port_bilgisi}")

    if paket_sayaci[src_ip] >= 50:
        kalkani_aktif_et(src_ip)


def sistemi_baslat():
    global aktif
    aktif = True
    ekrana_yaz("[!] Sistem Aktif: Savunma hatları kuruldu.")

    # Trafik izleme thread'i
    threading.Thread(target=lambda: sniff(filter="ip", prn=paket_yakalayici, store=0), daemon=True).start()

    # ARP Zehirleme izleme thread'i (Bu çok önemli!)
    threading.Thread(target=lambda: sniff(filter="arp", prn=arp_monitor_callback, store=0), daemon=True).start()


def kalkanlari_indir():
    subprocess.run('powershell -Command "Remove-NetFirewallRule -DisplayName \'BLOCK_*\'"', shell=True)
    if os.path.exists("kara_liste.txt"): os.remove("kara_liste.txt")
    engellenenler.clear()
    ekrana_yaz("[!!!] KALKANLAR İNDİRİLDİ.")


btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(pady=20)
tk.Button(btn_frame, text="BAŞLAT", command=sistemi_baslat, bg="green", fg="white", width=15).pack(side=tk.LEFT,
                                                                                                   padx=10)
tk.Button(btn_frame, text="KALKANLARI İNDİR", command=kalkanlari_indir, bg="orange", fg="black", width=20).pack(
    side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="DURDUR", command=lambda: globals().update(aktif=False) or ekrana_yaz("[!] DURDURULDU"),
          bg="red", fg="white", width=15).pack(side=tk.LEFT, padx=10)

root.mainloop()