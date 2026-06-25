from scapy.all import sniff
import os
import platform

# Ekranı temizle
os.system('cls' if platform.system() == "Windows" else 'clear')

print("""
################################################
#                                              #
#  __________________________________________  #
# |                                          | #
# |  🇹🇷       CYBER OPERATION - 2026       🇹🇷 | #
# |__________________________________________| #                        
# ============================================ #                
#           * * * * * #
#         * * * #
#        * * #
#        * * #
#         * ** #
#           * * * * #
#                                              #
#      🇹🇷 HACKER İMZASI: [ANONYCAT] 🇹🇷        #
################################################
""")


def paket_yakalayici(paket):
    if paket.haslayer('IP'):
        src_ip = paket['IP'].src
        dst_ip = paket['IP'].dst

        # Eğer TCP katmanı varsa port bilgisini al
        if paket.haslayer('TCP'):
            dst_port = paket['TCP'].dport
            log = f"[!] TCP TRAFİĞİ: {src_ip} -> {dst_ip} (Port: {dst_port})\n"

            # Sadece şüpheli portları konsola ve dosyaya yaz
            if dst_port in [80, 443, 22, 8080]:
                print(log.strip())
                with open("ag_raporu.txt", "a") as dosya:
                    dosya.write(log)
        else:
            # TCP olmayan IP paketlerini de görelim
            log = f"[+] Paket: {src_ip} -> {dst_ip}\n"
            # İstersen buradaki print'i silebilirsin, sadece önemli portlara odaklanmak için
            # print(log.strip())


print("Sistem tarama modunda... (Çıkmak için CTRL+C)")
sniff(filter="ip", prn=paket_yakalayici, store=0)