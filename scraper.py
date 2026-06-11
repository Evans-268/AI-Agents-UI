import requests
from bs4 import BeautifulSoup
import urllib.parse

def scrape_toko_online(url):
    print(f"🔍 Memulai scraping dari: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Gagal mengakses website! Status: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error koneksi: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    hasil_produk = []
    
    items = soup.find_all('article', class_='product_pod') 
    
    if not items:
        print("⚠️ Produk tidak ditemukan! Cek kembali tag HTML atau mungkin web menggunakan JavaScript.")
        return []

    for item in items:
        name_tag = item.find('h3')
        if name_tag and name_tag.find('a'):
            nama_produk = name_tag.find('a').get('title') or name_tag.find('a').text.strip()
        else:
            nama_produk = "Nama tidak ditemukan"
        
        price_tag = item.find('p', class_='price_color')
        harga_produk = price_tag.text.strip() if price_tag else "Harga tidak ditemukan"
        
        img_tag = item.find('img')
        url_gambar = ""
        if img_tag:
            src_mentah = img_tag.get('src') or img_tag.get('data-src') or ""
            url_gambar = urllib.parse.urljoin(url, src_mentah)
        
        hasil_produk.append({
            "name": nama_produk,
            "price": harga_produk,
            "image": url_gambar 
        })
        
    print(f"✅ Berhasil mengambil {len(hasil_produk)} produk!")
    return hasil_produk