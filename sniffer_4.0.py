from scapy.all import sniff
import os
import platform

# Ekranı temizle
os.system('cls' if platform.system() == "Windows" else 'clear')

print("""
################################################
################################################
#  __________________________________________  #
# |                                          | #
# |  🇹🇷     - CYBER OPERATION - 2026 -     🇹🇷 | #
# |__________________________________________| #                        
# ============================================ #     
#                      
#           * * * * * *    
#         * * * *     * *           **
#        * * *                   ********
#        * * *                     ****
#         * * * *     * *         **  **
#           * * * * * *
#                                              #
#      🇹🇷 HACKER İMZASI: [ANONYCAT] 🇹🇷        #
################################################
""")

# Paket sayılarını tutacak bir sözlük
paket_sayaci = {}

# 1. Kalkan fonksiyonu EN DIŞARIDA olmalı
def kalkani_aktif_et(ip_adresi):
    print(f"\n[!!!] GÜVENLİK ALARMI: {ip_adresi} engelleniyor...")
    komut = f'netsh advfirewall firewall add rule name="BLOCK_{ip_adresi}" dir=in action=block remoteip={ip_adresi}'
    os.system(komut)
    print(f"[!] BAŞARILI: {ip_adresi} bloklandı.")

def paket_yakalayici(paket):
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].src
        dst_ip = paket['IP'].dst
        dst_port = paket['TCP'].dport

        baglanti_id = f"{src_ip} -> {dst_ip} (Port: {dst_port})"
        paket_sayaci[baglanti_id] = paket_sayaci.get(baglanti_id, 0) + 1

        # HER paketi ekrana basmak yerine, bilgi amaçlı her pakette bir işaret koyabilirsin
        # Ama ekranın akması için şunu açabilirsin:
        print(f"[+] Trafik: {baglanti_id} | Sayı: {paket_sayaci[baglanti_id]}")

        # 2. Şüpheli Trafik Kontrolü
        if dst_port not in [443, 80, 8080, 21, 22] and paket_sayaci[baglanti_id] > 10:
            print(f"[!!!] ŞÜPHELİ YÜKSEK TRAFİK: {baglanti_id}")

        # 3. Kalkanı Çağırma (Sadece 50'yi geçerse engelle, IP'ni engellememek için kontrol ekle)
        if paket_sayaci[baglanti_id] > 100 and src_ip != "192.168.1.63":
            kalkani_aktif_et(src_ip)

print("Sistem tarama modunda... (CTRL+C ile durdur)")
sniff(filter="ip or tcp", prn=paket_yakalayici, store=0)