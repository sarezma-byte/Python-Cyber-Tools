from scapy.all import sniff
import os
import platform

engellenenler = set()

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


def kalkani_aktif_et(ip_adresi):
    if ip_adresi in engellenenler:
        return
    print(f"\n[!!!] GÜVENLİK ALARMI: {ip_adresi} engelleniyor...")
    komut = f'netsh advfirewall firewall add rule name="BLOCK_{ip_adresi}" dir=in action=block remoteip={ip_adresi}'
    os.system(komut)
    with open("kara_liste.txt", "a") as kara_liste:
        kara_liste.write(f"{ip_adresi} - Tarih: 2026\n")
    engellenenler.add(ip_adresi)
    print(f"[!] BAŞARILI: {ip_adresi} bloklandı.")

# 1. HAFIZA YÜKLEYİCİ: Dosya varsa, daha önce engellediklerini hatırla
engellenenler = set()
if os.path.exists("kara_liste.txt"):
    with open("kara_liste.txt", "r") as dosya:
        for satir in dosya:
            ip = satir.split(" - ")[0] # Sadece IP kısmını al
            engellenenler.add(ip.strip())

# Artık kodun "Daha önce bu adamı engellemiştim, bir daha uğraşmayayım" diyecek.

paket_sayaci = {}


def paket_yakalayici(paket):
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].src
        dst_ip = paket['IP'].dst
        dst_port = paket['TCP'].dport

        baglanti_id = f"{src_ip} -> {dst_ip} (Port: {dst_port})"

        # AG RAPORU (Dosya yazma işlemi burada)
        with open("ag_raporu.txt", "a") as rapor:
            rapor.write(f"{baglanti_id}\n")

        paket_sayaci[baglanti_id] = paket_sayaci.get(baglanti_id, 0) + 1

        print(f"[+] Trafik: {baglanti_id} | Sayı: {paket_sayaci[baglanti_id]}")

        if dst_port not in [443, 80, 8080, 21, 22] and paket_sayaci[baglanti_id] > 10:
            print(f"[!!!] ŞÜPHELİ YÜKSEK TRAFİK: {baglanti_id}")

        if paket_sayaci[baglanti_id] > 50 and src_ip != "192.168.1.63":
            kalkani_aktif_et(src_ip)


print("Sistem tarama modunda... (CTRL+C ile durdur)")
sniff(filter="ip or tcp", prn=paket_yakalayici, store=0)