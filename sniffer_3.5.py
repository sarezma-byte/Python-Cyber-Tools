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


def paket_yakalayici(paket):
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].src
        dst_ip = paket['IP'].dst
        dst_port = paket['TCP'].dport

        baglanti_id = f"{src_ip} -> {dst_ip} (Port: {dst_port})"

        # Sayacı güncelle
        paket_sayaci[baglanti_id] = paket_sayaci.get(baglanti_id, 0) + 1

        # Eğer paket sayısı 50'nin katıysa raporla (böylece ekran akmaz ama sayı artar)
        if paket_sayaci[baglanti_id] % 50 == 0:
            print(f"[!] DİKKAT: {baglanti_id} üzerinden {paket_sayaci[baglanti_id]} paket geçti!")

        # Eğer çok şüpheli bir portsa ve paket sayısı yüksekse anında bas
        if dst_port not in [443, 80, 8080, 21, 22] and paket_sayaci[baglanti_id] > 10:
            print(f"[!!!] ŞÜPHELİ YÜKSEK TRAFİK: {baglanti_id} (Toplam: {paket_sayaci[baglanti_id]})")

            # Dosyaya sadece yeni bağlantıları kaydet
            with open("ag_raporu.txt", "a") as dosya:
                dosya.write(f"{baglanti_id}\n")


print("Sistem tarama modunda... (Çıkmak için CTRL+C)")
sniff(filter="ip or tcp", prn=paket_yakalayici, store=0)