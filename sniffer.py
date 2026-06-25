from scapy.all import sniff


def raporla(paket):
    # Eğer paket hem IP hem de TCP katmanına sahipse
    if paket.haslayer('IP') and paket.haslayer('TCP'):
        src_ip = paket['IP'].src
        dst_port = paket['TCP'].dport  # Hedef portu alıyoruz

        # Sadece 80 veya 443 (Web trafiği) gibi portlara bak
        if dst_port in [80, 443]:
            log = f"[!] WEB TRAFİĞİ: {src_ip} -> Hedef Port: {dst_port}\n"
            with open("ag_raporu.txt", "a") as dosya:
                dosya.write(log)

def raporla(paket):
    if paket.haslayer('IP'):
        log_metni = f"[+] Paket: {paket['IP'].src} -> {paket['IP'].dst}\n"
        print(log_metni.strip())  # Ekrana da bas ki çalıştığını gör

        # Dosyayı "append" (ekleme) modunda açıyoruz
        with open("ag_raporu.txt", "a") as dosya:
            dosya.write(log_metni)


print("Ağ dinleniyor... Raporlar 'ag_raporu.txt' dosyasına yazılıyor.")
print("Durdurmak için CTRL+C yapabilirsin.")

# Sonsuz döngü: count yok, program sen durdurana kadar devam eder
sniff(filter="ip", prn=raporla, store=0)