import os
import json
import glob
import base64
import markdown
import jsonschema
import re
import io  
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image 

load_dotenv() 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

def resize_image_and_encode_base64(image_source, max_size=(512, 512), quality=85):
    """
    Mengambil sumber gambar (path file atau objek file bytes), pengecil ukuran,
    konversi ke JPEG, dan mengembalikan string base64.
    
    Args:
        image_source: Path string ke file atau objek BytesIO (hasil upload form).
        max_size: Tuple (width, height) maksimal. Mencoba mempertahankan aspect ratio.
        quality: Kualitas kompresi JPEG (1-100).
    Returns:
        String base64 gambar yang sudah dikecilkan, atau None jika gagal.
    """
    try:
        if isinstance(image_source, bytes):
            img = Image.open(io.BytesIO(image_source))
        else:
            # Jika sumber adalah path string
            if not os.path.exists(image_source):
                return None
            img = Image.open(image_source)

        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1]) 
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=quality, optimize=True)
        
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_str

    except Exception as e:
        print(f"Error saat resizing/encoding gambar: {e}")
        return None

def auto_load_product_images(products):
    image_folder = os.path.join('static', 'data', 'Product')
    for product in products:
        if product.get('image') and not product['image'].startswith('static/'):
            continue
        product_name = product['name'].lower()
        image_files = glob.glob(os.path.join(image_folder, '*'))
        for img in image_files:
            filename = os.path.basename(img).lower()
            if product_name.split() in filename:
                relative_path = os.path.relpath(img, 'static').replace("\\", "/")
                product['image'] = relative_path
                break
        if not product.get('image'):
            product['image'] = 'data/no-image.png'
    return products

def clean_and_preprocess(raw_data):
    processed_products = []
    for product in raw_data:
        item = product.copy()
        price_str = item.get('price', '0')
        cleaned_price = price_str.replace("Rp.", "").replace(".", "").replace(" ", "").strip()
        try:
            item['price_numeric'] = int(cleaned_price)
        except ValueError:
            item['price_numeric'] = 0
            
        item['rating_numeric'] = item.get('rating', 0.0)
        
        if item.get('image') and item['image'].startswith('static/'):
            item['image'] = item['image'].replace('static/', '', 1)
        processed_products.append(item)
    return auto_load_product_images(processed_products)

def clean_text(raw_text):
    if not raw_text:
        return ""
    bersih = re.sub(r'<[^>]+>', '', raw_text)
    bersih = re.sub(r'[^\w\s.,?!%\'"-]', '', bersih)
    bersih = re.sub(r'\s+', ' ', bersih).strip()
    return bersih

def load_products(filepath="products.json", schema_path="product_schema.json"):
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            
        try:
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as schema_file:
                    schema = json.load(schema_file)
                # Mengecek apakah 'data' sesuai dengan 'schema'
                jsonschema.validate(instance=data, schema=schema)
                print("✅ Data JSON valid sesuai schema!")
            else:
                print("⚠️ File schema tidak ditemukan, melewati proses validasi.")
        except jsonschema.exceptions.ValidationError as ve:
            print(f"❌ Peringatan Validasi JSON! Ada data yang tidak sesuai format:\n{ve.message}")
            
        return clean_and_preprocess(data)
    except Exception as e:
        print(f"Error baca JSON: {e}")
        return []

def extract_image_features(image_base64):
    """
    Fungsi baru untuk mengekstrak fitur visual dari gambar menjadi data JSON terstruktur.
    """
    if not client or not image_base64:
        return None
        
    try:
        print("🔍 Memulai proses Image Feature Extraction...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}, 
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah sistem ekstraksi fitur visual. Analisis gambar yang diberikan dan keluarkan HANYA format JSON dengan key berikut: 'kategori' (misal: laptop, tas, jam tangan, sepatu), 'warna_dominan', 'merek' (isi dengan nama merek jika terlihat, jika tidak isi null), dan 'kondisi'."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            max_tokens=150,
            temperature=0.1
        )
        features = json.loads(response.choices[0].message.content)
        return features
    except Exception as e:
        print(f"⚠️ Error saat ekstraksi fitur gambar: {e}")
        return None

def extract_text_preferences(user_query):
    """
    Fungsi untuk mengekstrak preferensi (merek, kategori, budget, BAHASA) dari teks chat user menggunakan AI.
    """
    if not client or not user_query:
        return None
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}, 
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah sistem ekstraksi data belanja. Analisis kalimat pengguna dan keluarkan HANYA format JSON dengan key: 'merek' (nama merek jika ada, jika tidak null), 'kategori' (jenis produk atau kata kunci pencarian seperti laptop, SSD, portable, gaming, wireless dll. Jika tidak ada null), 'budget' (isi dengan 'Murah / Terjangkau', 'Premium', atau null), dan 'bahasa_dominan' (deteksi bahasa apa yang digunakan user dalam prompt, contoh: 'Indonesia', 'Inggris', 'Sunda', 'Jawa', dll)."
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            max_tokens=100,
            temperature=0.1
        )
        features = json.loads(response.choices[0].message.content)
        return features
    except Exception as e:
        print(f"⚠️ Error saat ekstraksi preferensi teks: {e}")
        return None

def ask_ai(user_query, product_data, history, user_image_bytes, summary_algo, preferences, file_text_content=""):
    if not client:
        return "Sistem belum terintegrasi dengan API Key OpenAI.", True

    optimized_products = []
    for p in product_data:
        if p.get('hidden') == True:
            continue
            
        optimized_products.append({
            "name": p.get('name'),
            "price": p.get('price'),
            "desc": p.get('description'), 
            "img": p.get('image'),        
            "rating": p.get('rating')
        })
        
    context_text = json.dumps(optimized_products, separators=(',', ':'))
    recent_history = history[-3:] if len(history) > 3 else history
    history_text = "\n".join([f"U:{chat['user']}\nA:{chat['ai']}" for chat in recent_history])

    algo_instruction = ""
    if summary_algo == 'extractive':
        algo_instruction = "TUGAS: Extractive Summarization. Ekstrak spesifikasi teknis mentah. Wajib format bullet points (<ul><li>) atau TABEL HTML (<table>) jika data spesifikasi cukup padat.."
    elif summary_algo == 'abstractive':
        algo_instruction = "TUGAS: Abstractive Summarization. Buat ringkasan naratif SANGAT SINGKAT. Maksimal 2 kalimat."
    elif summary_algo == 'comparative':
        algo_instruction = "TUGAS: Comparative Summarization. Bandingkan produk secara terstruktur. Soroti 'Kelebihan' & 'Kekurangan'. \n\nATURAN WAJIB PERBANDINGAN:\n1. FILTER DATA: Analisis permintaan pengguna (misal meminta 'laptop'), lalu HANYA cari dan bandingkan produk di [Data Produk] yang sesuai dengan kata kunci tersebut.\n2. JANGAN asal membandingkan produk dari urutan teratas jika tidak relevan dengan permintaan pengguna.\n3. Kamu SANGAT DISARANKAN menggunakan format TABEL HTML (<table>) untuk membandingkan spesifikasi, harga, kelebihan, atau kekurangan antar-produk yang RELEVAN agar terlihat rapi dan modular."
    elif summary_algo == 'recommendation':
        algo_instruction = "TUGAS: Recommendation. Berikan 2-3 rekomendasi produk yang PALING COCOK berdasarkan '[Preferensi User Saat Ini]' atau permintaan spesifiknya di prompt. WAJIB sertakan poin '💡 Mengapa cocok untukmu' pada setiap produk, 'Kelebihan', dan 'Kekurangan' menggunakan format list HTML (<ul><li>) yang rapi atau tabel perbandingan di akhir jika diperlukan."
    elif summary_algo == 'general':
        algo_instruction = "TUGAS: General Chat. Jawab sapaan atau pertanyaan umum pengguna dengan ramah, santai, dan natural. Jika pengguna tidak menanyakan produk, jangan paksakan format rekomendasi atau tabel. Cukup jawab layaknya asisten yang siap membantu."

    merek_str = ", ".join(preferences["merek_favorit"]) if preferences["merek_favorit"] else "Belum diketahui"
    minat_str = ", ".join(preferences["kategori_minat"]) if preferences["kategori_minat"] else "Belum diketahui"
    budget_str = preferences.get("budget", "Bebas")
    bahasa_str = preferences.get("bahasa_dominan", "Indonesia")

    text_prompt = f"""Kamu adalah 'ShopAssist', asisten belanja AI.

{algo_instruction}

ATURAN KETAT:
1. BAHASA UTAMA: Kamu WAJIB menerjemahkan dan menjawab SELURUH respons kamu menggunakan bahasa: {bahasa_str}. Jangan mencampur bahasa kecuali untuk istilah teknis atau nama produk.
2. FAKTA SAJA: Prioritaskan informasi dari "Data Produk". NAMUN, jika pengguna secara spesifik meminta untuk menjelaskan gambar (misal: "jelaskan gambar ini"), kamu WAJIB menganalisis dan menjelaskan teks, fitur, atau spesifikasi yang terlihat langsung pada gambar tersebut meskipun produknya mungkin tidak persis ada di Data Produk.
3. CARI ALTERNATIF: Jika produk persis yang diminta (baik dari teks maupun gambar) tidak ada di data, JANGAN langsung bilang tidak ada/tidak tahu. Tawarkan alternatif produk yang kategorinya paling mirip (misal: jika user mencari/mengirim gambar earphone merek X, tawarkan earphone merek Y yang ada di data).
4. FORMAT LISTING: Jika menyebutkan poin-poin seperti Kelebihan, Kekurangan, atau Alasan, JANGAN PERNAH menuliskannya menyambung dalam satu paragraf dengan tanda hubung (-). Kamu WAJIB menurunkannya menggunakan tag <ul> dan <li>.
5. FORMAT TABEL HTML (PANDUAN): Jika menggunakan tabel untuk perbandingan atau ringkasan data, buatlah struktur tabel HTML yang valid (<table>, <tr>, <th>, <td>). 
   Agar serasi dengan tampilan CSS Dark Mode, berikan inline style dasar pada tag tabelmu:
   - Pada tag <table> gunakan: style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;"
   - Pada tag <th> (Header) gunakan: style="background-color: var(--bg-sidebar); border: 1px solid var(--hover-bg); padding: 10px; text-align: left; color: var(--accent-color);"
   - Pada tag <td> (Isi baris) gunakan: style="border: 1px solid var(--hover-bg); padding: 10px; color: var(--text-primary);"
5. FORMAT TAMPILAN PRODUK WAJIB: 
   Kamu WAJIB menggunakan struktur tag HTML (ul dan li) di bawah ini persis untuk setiap produk. Gunakan teks tebal (bold) dengan menambahkan tanda bintang ganda (**) pada nomor urut dan nama produk agar format penomoran tidak rusak (contoh: ""1. Nama Produk""):

   "[Nomor Urut]. [Nama Produk]"
   <ul>
       <li>Harga: [Harga Produk]</li>
       <li>Rating: [Rating Produk]</li>
       <li>Deskripsi: [Deskripsi singkat Produk]</li>
   </ul>
   <img src="[URL_GAMBAR]" alt="[Nama Produk]" style="max-width: 250px; border-radius: 8px; display: block; margin: 15px 0 30px 0; border: 1px solid #ddd;">

   Aturan [URL_GAMBAR]:
   - Jika 'img' berawalan 'http': Tulis apa adanya. (Cth: <img src="http://web.com/1.jpg" alt="...">)
   - Jika BUKAN link internet: Tambahkan '/static/'. (Cth: <img src="/static/data/Product/x.jpg" alt="...">)
   - Gunakan style ini: style="max-width: 150px; border-radius: 8px; display: block; margin: 10px 0; border: 1px solid #ddd;"

--- KONTEKS ---
[Data Produk]:
{context_text}

[Riwayat]:
{history_text}

[Preferensi User Saat Ini]:
- Merek Disukai: {merek_str}
- Kategori Diminati: {minat_str}
- Preferensi Budget: {budget_str}
- Bahasa Dominan: {bahasa_str}
[Pertanyaan User]:
"{user_query}"
"""

    content_array = [
        {"type": "text", "text": text_prompt}
    ]

    extracted_text_info = ""
    if user_image_bytes:
        user_img_b64_resized = resize_image_and_encode_base64(user_image_bytes, max_size=(512, 512))
        
        if user_img_b64_resized:
            img_features = extract_image_features(user_img_b64_resized)
            
            if img_features:
                print(f"✅ Hasil Ekstraksi Fitur Gambar: {img_features}")
                if img_features.get('merek') and img_features['merek'] != 'null':
                    merek = str(img_features['merek']).title()
                    if merek not in preferences["merek_favorit"]:
                        preferences["merek_favorit"].append(merek)
                        
                if img_features.get('kategori') and img_features['kategori'] != 'null':
                    kategori = str(img_features['kategori']).title()
                    if kategori not in preferences["kategori_minat"]:
                        preferences["kategori_minat"].append(kategori)
                    
                extracted_text_info = f"\n[INFO SISTEM: Dari gambar yang dikirim user, sistem telah mengekstrak fitur berikut: Kategori={img_features.get('kategori')}, Warna={img_features.get('warna_dominan')}, Merek={img_features.get('merek')}, Teks Terbaca={img_features.get('teks_terbaca')}]. Jika user meminta penjelasan gambar, jelaskan secara detail berdasarkan 'Teks Terbaca' dan penglihatan visualmu pada gambar tersebut."
            
            content_array.append({"type": "text", "text": "Ini gambar referensi dari user:" + extracted_text_info})
            content_array.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{user_img_b64_resized}"}})
        
    content_array.append({"type": "text", "text": "Ini gambar produk toko yang relevan sebagai referensi visual:"})
    for product in product_data[:3]: 
        if product.get('image') and product['image'] != 'data/no-image.png' and not product['image'].startswith('http'):
            image_path = os.path.join('static', product['image'])
            prod_img_b64_resized = resize_image_and_encode_base64(image_path, max_size=(400, 400))
            
            if prod_img_b64_resized:
                content_array.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{prod_img_b64_resized}"}})
                
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": content_array}],
            max_tokens=3500,
            temperature=0.3 
        )
        response_text = response.choices[0].message.content
        html_response = markdown.markdown(response_text)
        
        usage = response.usage
        eval_data = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
        
        return html_response, False, eval_data 

    except Exception as e:
        print(f"Error OpenAI: {e}")
        return "Maaf, kendala teknis AI saat memproses. Pastikan API Key valid.", True, None