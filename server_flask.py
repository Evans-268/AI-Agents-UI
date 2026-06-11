from flask import Flask, render_template, request, redirect, jsonify, session, url_for
from functools import wraps
import base64
import webbrowser
from threading import Timer
import app
import scraper
import time
import uuid 
import json 
import os   
from dotenv import load_dotenv 
from pyngrok import ngrok 

server = Flask(__name__)

load_dotenv()

server.secret_key = uuid.uuid4().hex
USERS_FILE = "users.json" 

def load_users():
    """Fungsi untuk membaca data user dari file users.json"""
    if not os.path.exists(USERS_FILE):
        users_json = {}
        with open(USERS_FILE, 'w') as f:
            json.dump(users_json, f, indent=4)
        return users_json
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users_data):
    """Fungsi untuk menyimpan data user baru ke dalam file users.json"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)

CHAT_FILE = "chat_history.json"

def load_chat_sessions():
    """Fungsi untuk membaca riwayat obrolan dari file JSON."""
    if not os.path.exists(CHAT_FILE):
        return []
    try:
        with open(CHAT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_chat_sessions(sessions):
    """Fungsi untuk menyimpan seluruh obrolan secara permanen ke file JSON."""
    with open(CHAT_FILE, 'w') as f:
        json.dump(sessions, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

chat_sessions = load_chat_sessions()
active_session_id = str(uuid.uuid4())

@server.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/chat')
        
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        users_db = load_users()
        
        if email in users_db:
            user_data = users_db[email]
            
            # Mendukung format data lama (string) dan format baru (dict)
            if isinstance(user_data, dict):
                stored_password = user_data.get('password')
                stored_name = user_data.get('name', email.split('@')[0].capitalize())
            else:
                stored_password = user_data
                stored_name = email.split('@')[0].capitalize()
        
            if stored_password == password:
                session['logged_in'] = True
                session['user_email'] = email
                session['user_name'] = stored_name  # Mengambil nama dari database
                return redirect('/chat')
            else:
                error = "Email atau password salah. Silakan coba lagi."
        else:
            error = "Email atau password salah. Silakan coba lagi."
            
    return render_template('login.html', error=error)

@server.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        users = load_users()

        if email in users:
            return render_template('register.html', error="Email sudah terdaftar! Silakan gunakan email lain.")

        users[email] = {
            "password": password,
            "name": name
        }
        save_users(users)

        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = name 

        return redirect('/chat')

    return render_template('register.html')

@server.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@server.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    message = None
    old_email = session.get('user_email')
    users_db = load_users()
    
    if request.method == 'POST':
        new_name = request.form.get('new_name')
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')
        
        if old_email in users_db:
            users_db.pop(old_email)
            
        users_db[new_email] = {
            "password": new_password,
            "name": new_name
        }
        
        save_users(users_db)
        
        session['user_email'] = new_email
        session['user_name'] = new_name
        
        message = "Data akun berhasil diperbarui secara permanen!"
        
    return render_template('settings.html', 
                           message=message, 
                           current_email=session.get('user_email'),
                           current_name=session.get('user_name'))

@server.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_email = session.get('user_email')
    
    users_db = load_users()
    
    if user_email in users_db:
        users_db.pop(user_email)
        save_users(users_db) 
        print(f"🗑️ Akun {user_email} telah berhasil dihapus secara permanen.")
        
    session.clear()
    
    return redirect('/login')

@server.route('/')
@login_required
def shop_home():
    products = app.load_products("products.json")
    return render_template('shop.html', products=products)

@server.route('/chat', methods=['GET', 'POST'])
@login_required
def home():
    global chat_sessions, active_session_id
    error_msg = None
    products = []
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    
    if request.method == 'POST':
        if not current_session:
            current_session = {
                "id": active_session_id, 
                "title": "Obrolan Baru", 
                "messages": [],
                "preferences": {
                    "merek_favorit": [],
                    "kategori_minat": [],
                    "budget": "Bebas",
                    "bahasa_dominan": "Indonesia"
                }
            }
            chat_sessions.insert(0, current_session)
            
        chat_memory = current_session.get("messages", [])
        session_prefs = current_session.get("preferences", {
            "merek_favorit": [],
            "kategori_minat": [],
            "budget": "Bebas",
            "bahasa_dominan": "Indonesia"
        })

        current_session["messages"] = chat_memory
        current_session["preferences"] = session_prefs
        
        raw_query = request.form.get('message', '')
        user_query = app.clean_text(raw_query)
        user_image_file = request.files.get('user_image')
        query_huruf_kecil = user_query.lower()

        extracted_prefs = app.extract_text_preferences(user_query)
        
        if extracted_prefs:
            print(f"✅ Preferensi terdeteksi dari teks: {extracted_prefs}")
            
            if extracted_prefs.get('merek') and str(extracted_prefs['merek']).lower() != 'null':
                merek = str(extracted_prefs['merek']).title()
                if merek not in session_prefs["merek_favorit"]:
                    session_prefs["merek_favorit"].append(merek)
                
            if extracted_prefs.get('kategori') and str(extracted_prefs['kategori']).lower() != 'null':
                kategori = str(extracted_prefs['kategori']).title()
                if kategori not in session_prefs["kategori_minat"]:
                    session_prefs["kategori_minat"].append(kategori)
                
            if extracted_prefs.get('budget') and str(extracted_prefs['budget']).lower() != 'null':
                session_prefs["budget"] = str(extracted_prefs['budget']).title()
            if extracted_prefs.get('bahasa_dominan') and str(extracted_prefs['bahasa_dominan']).lower() != 'null':
                session_prefs["bahasa_dominan"] = str(extracted_prefs['bahasa_dominan']).title()

        manual_algo = request.form.get('manual_algo', 'auto')
        manual_source = request.form.get('manual_source', 'auto')

        if manual_algo != 'auto':
            summary_algo = manual_algo
        else:
            if any(kata in query_huruf_kecil for kata in ['bandingkan', 'perbandingan', 'beda', 'vs', 'mending mana', 'pilih mana']):
                summary_algo = 'comparative'
            elif any(kata in query_huruf_kecil for kata in ['singkat', 'ringkas', 'padat', 'kesimpulan', 'intinya']):
                summary_algo = 'abstractive'
            elif any(kata in query_huruf_kecil for kata in ['spesifikasi', 'spek', 'detail', 'poin penting', 'teknis']):
                summary_algo = 'extractive'
            elif any(kata in query_huruf_kecil for kata in [
                'rekomendasi', 'saran', 'cocok', 'rekomendasikan', 'pilihan terbaik', 'bagusnya',
                'laptop', 'hp', 'smartphone', 'jam', 'watch', 'smartwatch', 'earphone', 'tws', 
                'headset', 'ssd', 'penyimpanan', 'hardisk', 'tas', 'dompet', 'brankas',
                'samsung', 'apple', 'asus', 'acer', 'huawei', 'realme', 'mac', 'ipad', 'galaxy'
            ]):
                summary_algo = 'recommendation'
            else:
                summary_algo = 'general'
            
        if manual_source != 'auto':
             data_source = manual_source
        else:
             data_source = 'json_lokal'
             if any(kata in query_huruf_kecil for kata in ['buku', 'web', 'internet', 'online', 'live', 'luar']):
                 data_source = 'web_scraping'
        
        if data_source == 'json_lokal':
            products = app.load_products("products.json")
        elif data_source == 'web_scraping':
            url_target = "https://books.toscrape.com/"
            products = scraper.scrape_toko_online(url_target)
            if not products:
                error_msg = "Gagal mengambil data dari website. Pastikan koneksi aman."

        user_image_bytes = None
        image_mime = ""

        if user_image_file and user_image_file.filename != '':
            image_mime = user_image_file.mimetype
            user_image_bytes = user_image_file.read() 

        if user_query and not error_msg:
            start_time = time.time()
            ai_response, has_error, eval_data = app.ask_ai(
                user_query, products, chat_memory, user_image_bytes, summary_algo, session_prefs
            )
            latency = round(time.time() - start_time, 2) 

            display_base64 = ""
            if user_image_bytes:
                display_base64 = base64.b64encode(user_image_bytes).decode('utf-8')

            chat_memory.append({
                "user": user_query,
                "ai": ai_response,
                "image": display_base64,
                "image_mime": image_mime,
                "algo": summary_algo,   
                "latency": latency,     
                "eval": eval_data       
            })
            
            if len(chat_memory) == 1:
                new_title = user_query[:25] + "..." if len(user_query) > 25 else user_query
                current_session["title"] = new_title
                save_chat_sessions(chat_sessions)
                
    else:
        if current_session:
            chat_memory = current_session.get("messages", [])
            session_prefs = current_session.get("preferences", {
                "merek_favorit": [], 
                "kategori_minat": [], 
                "budget": "Bebas", 
                "bahasa_dominan": "Indonesia"
            })
        else:
            chat_memory = []
            session_prefs = {"merek_favorit": [], "kategori_minat": [], "budget": "Bebas", "bahasa_dominan": "Indonesia"}

    prefs_for_html = {
        "merek_favorit": session_prefs.get("merek_favorit", []),
        "kategori_minat": session_prefs.get("kategori_minat", []),
        "budget": session_prefs.get("budget", "Bebas"),
        "bahasa_dominan": session_prefs.get("bahasa_dominan", "Indonesia")
    }

    user_name = session.get('user_name', 'User')

    return render_template('index.html', 
                           chat_history=chat_memory, 
                           error_msg=error_msg, 
                           prefs=prefs_for_html, 
                           sessions=chat_sessions, 
                           active_session_id=active_session_id,
                           user_name=user_name)

@server.route('/switch_chat/<session_id>')
@login_required
def switch_chat(session_id):
    global active_session_id
    active_session_id = session_id
    return redirect('/chat')

@server.route('/new_chat')
@login_required
def new_chat():
    global active_session_id
    active_session_id = str(uuid.uuid4())
    return redirect('/chat')

@server.route('/delete_multiple', methods=['POST'])
@login_required
def delete_multiple_chats():
    global chat_sessions, active_session_id
    selected_ids = request.form.getlist('selected_chats')
    
    chat_sessions = [s for s in chat_sessions if s["id"] not in selected_ids]
    
    if not chat_sessions or active_session_id in selected_ids:
        active_session_id = str(uuid.uuid4())

    save_chat_sessions(chat_sessions)    
    return redirect('/chat')

@server.route('/api/products', methods=['GET'])
def api_get_products():
    try:
        products = app.load_products("products.json")
        return jsonify({"status": "success", "total_products": len(products), "data": products}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@server.route('/api/preferences', methods=['GET'])
def api_get_preferences():
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if current_session:
        prefs = current_session["preferences"]
    else:
        prefs = {"merek_favorit": [], "kategori_minat": [], "budget": "Bebas", "bahasa_dominan": "Indonesia"}
        
    prefs_for_json = {
        "merek_favorit": list(prefs["merek_favorit"]),
        "kategori_minat": list(prefs["kategori_minat"]),
        "budget": prefs["budget"],
        "bahasa_dominan": prefs["bahasa_dominan"]
    }
    return jsonify({"status": "success", "preferences": prefs_for_json}), 200

@server.route('/api/chat', methods=['POST'])
def api_chat():
    global chat_sessions, active_session_id
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"status": "error", "message": "Format JSON salah."}), 400
        
    raw_query = data.get('message', '')
    user_query = app.clean_text(raw_query)
    
    if not user_query.strip():
        return jsonify({"status": "error", "message": "Pesan tidak boleh kosong."}), 400
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if not current_session:
        current_session = {
            "id": active_session_id, 
            "title": user_query[:25] + "...", 
            "messages": [],
            "preferences": {"merek_favorit": [], "kategori_minat": [], "budget": "Bebas", "bahasa_dominan": "Indonesia"}
        }
        chat_sessions.insert(0, current_session)
        
    chat_memory = current_session["messages"]
    session_prefs = current_session["preferences"]
    
    summary_algo = 'recommendation' 
    products = app.load_products("products.json")
    start_time = time.time()
    
    ai_response, has_error, eval_data = app.ask_ai(
        user_query, products, chat_memory, None, summary_algo, session_prefs
    )
    
    latency = round(time.time() - start_time, 2)
    if has_error:
        return jsonify({"status": "error", "message": ai_response}), 500
        
    chat_memory.append({
        "user": user_query,
        "ai": ai_response,
        "image": "", "image_mime": "", "algo": summary_algo,
        "latency": latency, "eval": eval_data
    })

    save_chat_sessions(chat_sessions)
    
    return jsonify({
        "status": "success",
        "data": {
            "user_query": user_query,
            "ai_response_html": ai_response,
            "latency": latency
        }
    }), 200

@server.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    global chat_sessions, active_session_id
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Tidak ada data"}), 400
        
    chat_idx = data.get('chat_index')
    feedback_type = data.get('feedback')
    
    current_session = next((s for s in chat_sessions if s["id"] == active_session_id), None)
    if current_session and chat_idx is not None and 0 <= chat_idx < len(current_session["messages"]):
        current_session["messages"][chat_idx]['usability_feedback'] = feedback_type
        save_chat_sessions(chat_sessions)
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "message": "Indeks tidak valid"}), 400

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

@server.route('/api/comparison_accuracy', methods=['GET'])
@login_required
def get_comparison_accuracy():
    global chat_sessions
    
    total_comparative_chats = 0
    positive_feedback = 0
    negative_feedback = 0

    for session_chat in chat_sessions:
        for message in session_chat.get("messages", []):
            if message.get("algo") == "comparative":
                feedback = message.get("usability_feedback")
                if feedback == "up":
                    positive_feedback += 1
                elif feedback == "down":
                    negative_feedback += 1

    total_feedback = positive_feedback + negative_feedback

    if total_feedback > 0:
        accuracy_percentage = round((positive_feedback / total_feedback) * 100, 2)
    else:
        accuracy_percentage = 0.0

    return jsonify({
        "status": "success",
        "metric_name": "Product Comparison Accuracy",
        "total_comparative_with_feedback": total_feedback,
        "positive_votes": positive_feedback,
        "negative_votes": negative_feedback,
        "accuracy_score": f"{accuracy_percentage}%"
    }), 200

from pyngrok import ngrok 

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not server.debug:
        try:
            print("⏳ Sedang menyiapkan tautan publik via Ngrok...")
            
            ngrok_token = os.getenv("NGROK_AUTHTOKEN")
            
            if ngrok_token:
                ngrok.set_auth_token(ngrok_token)
                print("✅ AuthToken Ngrok berhasil dipasang!")
            else:
                print("⚠️ AuthToken tidak ditemukan di file .env, menggunakan mode tamu.")
                
            public_url = ngrok.connect(5000).public_url
            
            print("=" * 60)
            print("🚀 APLIKASI BERHASIL DIDEPLOY SEMENTARA!")
            print(f"🌍 Link Public: {public_url}")
            print("=" * 60)
        except Exception as e:
            print(f"⚠️ Gagal menjalankan Ngrok: {e}")

    server.run(host='0.0.0.0', port=5000, debug=True)