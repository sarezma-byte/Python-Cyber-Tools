from flask import Flask, jsonify, render_template, request
import requests
from bs4 import BeautifulSoup
import yfinance as yf

app = Flask(__name__)

# --- HABER MOTORU ---
def get_news(url, count):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        haberler = []
        for link in soup.find_all('a', href=True):
            title = link.get('title') or link.text.strip()
            href = link['href']
            # Linkin tam adres olduğundan emin olalım
            full_link = href if href.startswith('http') else "https://www.haberturk.com" + href

            if len(title) > 20 and {"title": title, "link": full_link} not in haberler:
                haberler.append({"title": title, "link": full_link})

        return haberler[:count]
    except:
        return []

# --- FİNANS MOTORU ---
# app.py içindeki get_finance_data fonksiyonunu bununla değiştir
def get_finance_data():
    # Sadece çalışan sembolleri bırakıyoruz
    tickers = {
        "USD": "USDTRY=X",
        "EUR": "EURTRY=X",
        "BIST100": "XU100.IS"
    }
    prices = {}

    # Kurları çek
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            prices[name] = round(t.fast_info['last_price'], 2)
        except:
            prices[name] = 0.0

    # Altın için hata payını kaldır, hata alırsa "Kapalı" yazsın
    try:
        ons_altin = yf.Ticker("XAU=X").fast_info['last_price']
        prices["ALTIN"] = round((ons_altin / 31.1035) * prices["USD"], 2)
    except:
        prices["ALTIN"] = "Piyasa Kapalı"

    return prices
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def news_api():
    return jsonify({
        "finans": get_news("https://www.haberturk.com/ekonomi", 15),
        "dunya": get_news("https://www.haberturk.com/dunya", 10),
        "teknoloji": get_news("https://www.haberturk.com/teknoloji", 10),
        "spor": get_news("https://www.haberturk.com/spor", 5)
    })

@app.route('/api/prices')
def prices_api():
    return jsonify(get_finance_data())

@app.route('/api/brief')
def brief_api():
    data = get_finance_data()
    return jsonify({"text": f"Piyasalar bugün hareketli. Dolar şu an {data['USD']} TL, BIST100 ise {data['BIST100']} seviyesinde seyrediyor."})

if __name__ == '__main__':
    app.run(debug=True)