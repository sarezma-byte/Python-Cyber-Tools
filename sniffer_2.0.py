from scapy.all import sniff
import os
import platform

# Ekranı temizle
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")


print("""
################################################
#                                              #
#  __________________________________________  #
# |                                          | #
# |  🇹🇷       CYBER OPERATION - 2026       🇹🇷 | #
# |__________________________________________| #                        
# ============================================#                
#           * * * * *  #
#         * * * #
#        * * #
#        * *  #
#         * ** #
#           * * * *  #
#                                              #
#      🇹🇷 HACKER İMZASI: [ANONYCAT] 🇹🇷      #
#                                           #
################################################
""")

def raporla(paket):
    # Eğer paket hem IP hem de TCP katmanına sahipse
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].fields
        dst_port = paket['TCP'].dport  # Hedef portu alıyoruz

        # Sadece 80 veya 443 (Web trafiği) gibi portlara bak
        if dst_port in [80, 443, 22, 8080]:
            log = f"[!] WEB TRAFİĞİ: {src_ip} -> Hedef Port: {dst_port}\n"
            with open("ag_raporu.txt", "a") as dosya:
                dosya.write(log)

def raporla(paket):
    if paket.haslayer('IP'):
        log_metni = f"[+] Paket: {paket['IP'].fields} -> {paket['IP'].dst}\n"
        print(log_metni.strip())  # Ekrana da bas ki çalıştığını gör

        # Dosyayı "append" (ekleme) modunda açıyoruz
        with open("ag_raporu.txt", "a") as dosya:
            dosya.write(log_metni)




# Sonsuz döngü: count yok, program sen durdurana kadar devam eder
sniff(filter="ip", prn=raporla, store=0)