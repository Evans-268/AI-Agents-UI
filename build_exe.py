# build_exe.py
import os
import sys
import subprocess

def build():
    print("🚀 Memulai proses pembungkusan (bundling) ke file .exe...")
    
    # Pastikan pyinstaller sudah terinstal
    try:
        import PyInstaller
    except ImportError:
        print("📦 PyInstaller belum terinstal. Menginstal sekarang...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Tentukan nama file utama Anda
    main_script = "server_flask.py"
    
    if not os.path.exists(main_script):
        print(f"❌ Error: File '{main_script}' tidak ditemukan di folder ini!")
        return

    # Menyusun perintah PyInstaller
    # --onedir atau --onefile. Kita gunakan --onedir (folder) agar file JSON database (users.json, chat_history.json)
    # tetap bisa dibaca dan ditulis dengan aman di sebelah file .exe tanpa hilang saat aplikasi ditutup.
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir", # Membuat folder berisi .exe + aset pendukung
        "--name=ShopAssistApp",
        "--add-data=templates;templates", # Memasukkan folder HTML
        "--add-data=static;static",       # Memasukkan folder CSS/JS/Gambar
    ]
    
    # Tambahkan file JSON jika diperlukan sebagai data awal
    for json_file in ["products.json", "product_schema.json"]:
        if os.path.exists(json_file):
            cmd.append(f"--add-data={json_file};.")

    cmd.append(main_script)
    
    print(f"🛠️ Menjalankan perintah: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ BERHASIL! Aplikasi Anda telah dibuat.")
        print("📁 Silakan cek folder 'dist/ShopAssistApp'.")
        print("👉 Di dalamnya terdapat file 'ShopAssistApp.exe' yang bisa langsung dijalankan!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Gagal membuat file .exe. Error: {e}")

if __name__ == "__main__":
    build()
