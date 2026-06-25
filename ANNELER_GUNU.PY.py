import requests
import json

base_url = "https://www.usom.gov.tr/api/address/index?page=1"

try:
    response = requests.get(base_url)

    if response.status_code == 200:
        data = response.json()

        # 1. Ekrana yazdıralım
        for item in data['models']:
            print(f"Zararlı IP/URL: {item['url']} - Kritiklik Seviyesi: {item['criticality_level']}")

        # 2. Dosyaya güvenli bir şekilde kaydedelim
        with open("zararli_listesi.json", "w", encoding='utf-8') as f:
            # indent=4 verinin okunabilir (okunaklı) olmasını sağlar
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("\n[+] Başarılı: Veriler 'zararli_listesi.json' dosyasına yazıldı.")

    else:
        print(f"Hata oluştu: {response.status_code}")

except Exception as e:
    print(f"Bağlantı hatası: {e}")