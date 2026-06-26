from flask import Flask, request
import requests

app = Flask(__name__)

# Senin IPinfo panosundaki gizli anahtarın!
IPINFO_TOKEN = ""


def ip_analiz_et_ipinfo(ip_adresi):
    # Eğer lokalde test ediyorsak kendi dış IP'mizi sorgulasın
    if ip_adresi == "127.0.0.1":
        sorgu_url = f"https://ipinfo.io/json?token={IPINFO_TOKEN}"
    else:
        sorgu_url = f"https://ipinfo.io/{ip_adresi}/json?token={IPINFO_TOKEN}"

    try:
        # IPinfo servisine senin özel anahtarınla istek atıyoruz
        cevap = requests.get(sorgu_url).json()

        ulke = cevap.get("country", "Bilinmiyor")
        sehir = cevap.get("city", "Bilinmiyor")
        saglayici = cevap.get("org", "Bilinmiyor")
        konum_koordinat = cevap.get("loc", "Bilinmiyor")

        # VPN tespiti
        vpn_mi = "HAYIR (Doğal Bağlantı)"
        org_name = saglayici.lower()
        supheli_kelimeler = ["vpn", "proxy", "hosting", "server", "cloud", "m247", "ovh", "digitalocean", "mullvad",
                             "nord"]
        if any(kelime in org_name for kelime in supheli_kelimeler):
            vpn_mi = "EVET! (VPN veya Proxy)"

        return ulke, sehir, saglayici, konum_koordinat, vpn_mi
    except Exception as e:
        return "Hata", "Hata", f"Bilgiler alınamadı: {e}", "Hata", "Bilinmiyor"


@app.route('/')
def home():
    dolandirici_ip = request.remote_addr
    tarayici = request.headers.get('User-Agent')

    # Arka planda sessizce senin tokenınla sorguluyor
    ulke, sehir, saglayici, koordinat, vpn_durumu = ip_analiz_et_ipinfo(dolandirici_ip)

    # Kanıtları txt dosyasına kaydediyoruz
    with open("kanitlar.txt", "a", encoding="utf-8") as dosya:
        dosya.write("--- YENİ BALIK DÜŞTÜ (IPINFO) ---\n")
        dosya.write(f"IP: {dolandirici_ip}\n")
        dosya.write(f"Lokasyon: {sehir} / {ulke}\n")
        dosya.write(f"Koordinatlar: {koordinat}\n")
        dosya.write(f"Sağlayıcı: {saglayici}\n")
        dosya.write(f"VPN Kullanımı: {vpn_durumu}\n")
        dosya.write(f"Tarayıcı: {tarayici}\n")
        dosya.write("---------------------------------\n\n")

    # Dolandırıcının ekranında sadece bu karizma uyarı çıkıyor:
    return """
    <body style="background-color: black; color: #00FF00; text-align: center; font-family: monospace; padding-top: 150px;">
        <h1 style="font-size: 60px; margin-bottom: 20px;">🔴 OYUN BİTTİ 🔴</h1>
        <h2 style="font-size: 35px; color: white; letter-spacing: 2px;">ANONYCAT WINNER</h2>
        <p style="font-size: 20px; color: #00FF00; margin-top: 30px;">Siber suç faaliyetiniz tespit edilmiştir.</p>
        <p style="font-size: 16px; color: #888;">Tüm dijital ayak izleriniz güvenli bir şekilde loglanmıştır.</p>
    </body>
    """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
