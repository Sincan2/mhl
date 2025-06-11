#!/bin/bash

# =================================================================
# Sincan2 Interactive Runner
# Author: MHL TEAM
# Version: 1.3 (Duck Banner Integration)
# Deskripsi: Skrip Bash untuk menjalankan sincan2.py dengan menu.
# =================================================================

# --- Definisi Warna ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Fungsi untuk menampilkan menu utama ---
function show_menu() {
    # PERUBAHAN: Fungsi banner dihapus, sekarang hanya membersihkan layar
    clear
    echo -e "${YELLOW}================= SINCAN2 RUNNER MENU ===================${NC}"
    echo -e ""
    echo -e "  ${CYAN}[1]${NC} 🎯  Pindai Target Tunggal"
    echo -e "  ${CYAN}[2]${NC} 📂  Pindai Massal dari File (dengan state)"
    echo -e ""
    echo -e "  ${RED}[3]${NC} 🚪  Keluar"
    echo -e ""
    echo -e "${YELLOW}===========================================================${NC}"
}

# --- Fungsi untuk menjalankan pemindaian tunggal ---
function run_single_scan() {
    local command_to_run=$1
    # Menjalankan skrip python yang akan menampilkan bannernya sendiri
    eval "$command_to_run"
    echo -e "\n${GREEN}✅ Pemindaian selesai. Tekan [ENTER] untuk kembali ke menu.${NC}"
    read
}

# --- Fungsi untuk opsi 1: Target Tunggal ---
function scan_single_target() {
    local target_host
    local timeout=2
    local extra_flags=""
    echo -e "\n--- 🎯 Pindai Target Tunggal ---"
    read -p "  Masukkan IP:PORT target: " target_host
    if [[ -z "$target_host" ]]; then echo -e "${RED}Error: Input tidak boleh kosong!${NC}"; sleep 2; return; fi
    if ! [[ "$target_host" =~ ^https?:// ]]; then target_host="http://$target_host"; fi
    read -p "  ⏱️  Berapa lama timeout? (default: 2 detik, tekan enter): " user_timeout
    timeout=${user_timeout:-2}
    read -p "  💥  Coba eksploitasi otomatis? (y/n, default: n): " auto_exploit
    if [[ "$auto_exploit" =~ ^[Yy]$ ]]; then extra_flags+=" --auto-exploit"; fi
    read -p "  🔬  Aktifkan pemindaian modern (CVE)? (y/n, default: n): " modern_scan
    if [[ "$modern_scan" =~ ^[Yy]$ ]]; then extra_flags+=" -M"; fi
    local final_command="python ./sincan2.py -u $target_host --timeout $timeout$extra_flags"
    run_single_scan "$final_command"
}

# --- Fungsi untuk opsi 2: Target Massal ---
function scan_mass_target() {
    local filename port timeout=2 extra_flags="" success_file="berhasil.txt"
    echo -e "\n--- 📂 Pindai Massal dari File ---"
    read -p "  Masukkan nama file list IP (contoh: koped.txt): " filename
    if [[ -z "$filename" ]]; then echo -e "${RED}Error: Nama file tidak boleh kosong!${NC}"; sleep 2; return; fi
    if [ ! -f "$filename" ]; then echo -e "${RED}Error: File '$filename' tidak ditemukan!${NC}"; sleep 2; return; fi
    read -p "  Masukkan port yang akan digunakan untuk semua IP: " port
    if [[ -z "$port" ]]; then echo -e "${RED}Error: Port tidak boleh kosong!${NC}"; sleep 2; return; fi
    read -p "  ⏱️  Berapa lama timeout? (default: 2 detik, tekan enter): " user_timeout
    timeout=${user_timeout:-2}
    read -p "  💥  Coba eksploitasi otomatis? (y/n, default: y): " auto_exploit
    if [[ ! "$auto_exploit" =~ ^[Nn]$ ]]; then extra_flags+=" --auto-exploit"; fi
    read -p "  🔬  Aktifkan pemindaian modern (CVE)? (y/n, default: y): " modern_scan
    if [[ ! "$modern_scan" =~ ^[Nn]$ ]]; then extra_flags+=" -M"; fi

    mapfile -t all_ips < "$filename"
    total_ips=${#all_ips[@]}
    
    if [ "$total_ips" -eq 0 ]; then
        echo -e "\n${YELLOW}⚠️  File '$filename' kosong. Tidak ada yang dipindai.${NC}"
        sleep 2
        return
    fi
    
    # Jalankan banner bebek satu kali sebelum loop
    python ./sincan2.py --help > /dev/null 2>&1 & # Trik untuk menjalankan banner tanpa memproses argumen
    sleep 4 # Beri waktu animasi selesai
    
    local processed_count=0
    for ip in "${all_ips[@]}"; do
        ((processed_count++))
        target_url="http://$ip:$port"

        echo -e "\n${BLUE}===========================================================${NC}"
        echo -e "${CYAN}[$processed_count/$total_ips] Memindai target: $target_url${NC}"
        echo -e "${BLUE}===========================================================${NC}"
        
        local final_command="python ./sincan2.py -u $target_url --timeout $timeout$extra_flags"
        
        # Hapus banner dari output utama agar tidak berulang
        scan_output=$(eval "$final_command" | sed '1,2d' | tee /dev/tty)
        
        if echo "$scan_output" | grep -q "\[ SUCCESS \]"; then
            echo -e "\n${GREEN}🎉 SUKSES! Target berhasil dieksploitasi. Menyimpan ke '$success_file'...${NC}"
            echo "$target_url" >> "$success_file"
        fi

        sed -i "/^${ip}$/d" "$filename"
        echo -e "${YELLOW}🧹 IP '$ip' telah diproses dan dihapus dari '$filename'.${NC}"
    done

    echo -e "\n${GREEN}✅ Semua target dalam file telah selesai dipindai. Tekan [ENTER] untuk kembali ke menu.${NC}"
    read
}

# --- Loop Utama Skrip ---
if [ ! -f "sincan2.py" ]; then
    echo -e "${RED}Error: File 'sincan2.py' tidak ditemukan di direktori ini.${NC}"
    echo -e "Pastikan skrip ini dijalankan di lokasi yang sama dengan sincan2.py.${NC}"
    exit 1
fi

while true; do
    show_menu
    read -p "  Pilih opsi [1-3]: " choice
    case $choice in
        1) scan_single_target ;;
        2) scan_mass_target ;;
        3) echo -e "\n${GREEN}Terima kasih telah menggunakan Sincan2 Runner! Sampai jumpa!${NC}\n"; exit 0 ;;
        *) echo -e "\n${RED}Pilihan tidak valid. Silakan coba lagi.${NC}"; sleep 1 ;;
    esac
done
